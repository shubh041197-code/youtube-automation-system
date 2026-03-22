from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad

from meta_ads.meta_client import get_ad_account
from meta_ads.models.reporting import DEFAULT_METRICS


class BudgetService:
    """Budget optimization and automated rules for ad spend management."""

    def get_budget_recommendations(self, campaign_id: str, days: int = 7) -> dict:
        """Analyze campaign performance and recommend budget changes."""
        campaign = Campaign(campaign_id)

        # Get campaign details
        campaign_data = campaign.api_get(fields=[
            Campaign.Field.name,
            Campaign.Field.daily_budget,
            Campaign.Field.lifetime_budget,
            Campaign.Field.status,
        ])

        # Get performance insights
        insights = campaign.get_insights(params={
            "fields": DEFAULT_METRICS,
            "date_preset": f"last_{days}d" if days in [3, 7, 14, 28, 30, 90] else "last_7d",
        })

        if not insights:
            return {
                "campaign_id": campaign_id,
                "campaign_name": campaign_data.get("name"),
                "recommendation": "INSUFFICIENT_DATA",
                "message": "Not enough data to make recommendations. Run the campaign for at least a few days.",
            }

        data = dict(insights[0])
        spend = float(data.get("spend", 0))
        impressions = int(data.get("impressions", 0))
        clicks = int(data.get("clicks", 0))
        ctr = float(data.get("ctr", 0))
        cpc = float(data.get("cpc", 0))
        cpm = float(data.get("cpm", 0))

        current_budget = float(campaign_data.get("daily_budget", 0)) / 100  # cents to dollars

        recommendations = []

        # CTR analysis
        if ctr < 1.0:
            recommendations.append({
                "type": "CREATIVE",
                "action": "Review and improve ad creatives — CTR is below 1%",
                "priority": "HIGH",
            })
        elif ctr > 3.0:
            recommendations.append({
                "type": "SCALE",
                "action": f"Strong CTR ({ctr:.2f}%) — consider increasing budget by 20-30%",
                "priority": "MEDIUM",
            })

        # CPC analysis
        if cpc > 2.0:
            recommendations.append({
                "type": "TARGETING",
                "action": f"CPC is high (${cpc:.2f}) — refine audience targeting or test new creatives",
                "priority": "HIGH",
            })

        # Spend efficiency
        if current_budget > 0 and spend > 0:
            daily_spend = spend / days
            utilization = daily_spend / current_budget
            if utilization < 0.5:
                recommendations.append({
                    "type": "BUDGET",
                    "action": f"Only spending {utilization:.0%} of budget — consider lowering budget or broadening targeting",
                    "priority": "MEDIUM",
                })

        # Budget suggestion
        suggested_budget = current_budget
        if ctr > 2.0 and cpc < 1.5:
            suggested_budget = current_budget * 1.25
        elif ctr < 1.0 or cpc > 3.0:
            suggested_budget = current_budget * 0.75

        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign_data.get("name"),
            "current_daily_budget": current_budget,
            "suggested_daily_budget": round(suggested_budget, 2),
            "metrics": {
                "spend": spend,
                "impressions": impressions,
                "clicks": clicks,
                "ctr": ctr,
                "cpc": cpc,
                "cpm": cpm,
            },
            "recommendations": recommendations,
        }

    def set_campaign_budget(self, campaign_id: str, daily_budget_cents: int) -> dict:
        """Set daily budget for a campaign (in cents)."""
        Campaign(campaign_id).api_update(params={
            Campaign.Field.daily_budget: str(daily_budget_cents),
        })
        return {"campaign_id": campaign_id, "daily_budget_cents": daily_budget_cents, "updated": True}

    def pause_underperforming_ads(
        self, campaign_id: str, ctr_threshold: float = 0.5, min_impressions: int = 1000
    ) -> list[dict]:
        """Auto-pause ads with CTR below threshold (after sufficient impressions)."""
        account = get_ad_account()
        ads = account.get_ads(
            fields=[Ad.Field.id, Ad.Field.name, Ad.Field.status],
            params={
                "filtering": [
                    {"field": "campaign.id", "operator": "EQUAL", "value": campaign_id},
                    {"field": "ad.effective_status", "operator": "IN", "value": ["ACTIVE"]},
                ],
            },
        )

        paused = []
        for ad in ads:
            ad_obj = Ad(ad["id"])
            insights = ad_obj.get_insights(params={
                "fields": ["impressions", "ctr"],
                "date_preset": "last_7d",
            })
            if not insights:
                continue

            data = dict(insights[0])
            impressions = int(data.get("impressions", 0))
            ctr = float(data.get("ctr", 0))

            if impressions >= min_impressions and ctr < ctr_threshold:
                ad_obj.api_update(params={Ad.Field.status: "PAUSED"})
                paused.append({
                    "ad_id": ad["id"],
                    "ad_name": ad.get("name"),
                    "impressions": impressions,
                    "ctr": ctr,
                    "action": "PAUSED",
                })

        return paused

    def scale_winning_adsets(
        self, campaign_id: str, ctr_threshold: float = 2.0, budget_increase: float = 0.2
    ) -> list[dict]:
        """Increase budget for ad sets with strong performance."""
        account = get_ad_account()
        adsets = account.get_ad_sets(
            fields=[AdSet.Field.id, AdSet.Field.name, AdSet.Field.daily_budget, AdSet.Field.status],
            params={
                "filtering": [
                    {"field": "campaign.id", "operator": "EQUAL", "value": campaign_id},
                    {"field": "adset.effective_status", "operator": "IN", "value": ["ACTIVE"]},
                ],
            },
        )

        scaled = []
        for adset in adsets:
            adset_obj = AdSet(adset["id"])
            insights = adset_obj.get_insights(params={
                "fields": ["impressions", "ctr", "cpc"],
                "date_preset": "last_7d",
            })
            if not insights:
                continue

            data = dict(insights[0])
            ctr = float(data.get("ctr", 0))
            current_budget = int(adset.get("daily_budget", 0))

            if ctr >= ctr_threshold and current_budget > 0:
                new_budget = int(current_budget * (1 + budget_increase))
                adset_obj.api_update(params={AdSet.Field.daily_budget: str(new_budget)})
                scaled.append({
                    "adset_id": adset["id"],
                    "adset_name": adset.get("name"),
                    "old_budget_cents": current_budget,
                    "new_budget_cents": new_budget,
                    "ctr": ctr,
                    "action": "SCALED_UP",
                })

        return scaled
