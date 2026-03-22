from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad

from meta_ads.meta_client import get_ad_account
from meta_ads.models.reporting import (
    ReportRequest,
    ReportResponse,
    InsightRow,
    InsightLevel,
    DEFAULT_METRICS,
)


class ReportingService:
    """Fetches ad insights and generates analytics reports."""

    def get_insights(self, request: ReportRequest) -> ReportResponse:
        """Get insights at any level (account/campaign/adset/ad)."""
        params = {
            "level": request.level.value,
            "fields": request.metrics,
            "limit": request.limit,
        }

        if request.time_range:
            params["time_range"] = request.time_range
        elif request.date_preset:
            params["date_preset"] = request.date_preset.value

        if request.breakdowns:
            params["breakdowns"] = [b.value for b in request.breakdowns]

        if request.filtering:
            params["filtering"] = request.filtering

        # Choose the right source object
        if request.ad_id:
            source = Ad(request.ad_id)
        elif request.adset_id:
            source = AdSet(request.adset_id)
        elif request.campaign_id:
            source = Campaign(request.campaign_id)
        else:
            source = get_ad_account()

        insights = source.get_insights(params=params)

        rows = []
        for row in insights:
            row_data = {}
            for key in row:
                row_data[key] = row[key]
            rows.append(InsightRow(**row_data))

        return ReportResponse(
            data=rows,
            total_count=len(rows),
        )

    def get_account_summary(self, date_preset: str = "last_7d") -> dict:
        """High-level account KPIs."""
        account = get_ad_account()
        insights = account.get_insights(params={
            "fields": DEFAULT_METRICS,
            "date_preset": date_preset,
        })

        if insights:
            return dict(insights[0])
        return {}

    def get_campaign_performance(self, campaign_id: str, date_preset: str = "last_7d") -> list[InsightRow]:
        """Get daily performance for a specific campaign."""
        campaign = Campaign(campaign_id)
        insights = campaign.get_insights(params={
            "fields": DEFAULT_METRICS,
            "date_preset": date_preset,
            "time_increment": 1,  # daily breakdown
        })
        return [InsightRow(**{k: row[k] for k in row}) for row in insights]
