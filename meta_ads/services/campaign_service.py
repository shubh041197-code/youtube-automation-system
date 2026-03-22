from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad

from meta_ads.meta_client import get_ad_account
from meta_ads.models.campaigns import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    AdSetCreate, AdSetUpdate, AdSetResponse,
    AdCreate, AdUpdate, AdResponse,
)

CAMPAIGN_FIELDS = [
    Campaign.Field.id,
    Campaign.Field.name,
    Campaign.Field.objective,
    Campaign.Field.status,
    Campaign.Field.daily_budget,
    Campaign.Field.lifetime_budget,
    Campaign.Field.bid_strategy,
    Campaign.Field.created_time,
    Campaign.Field.updated_time,
]

ADSET_FIELDS = [
    AdSet.Field.id,
    AdSet.Field.name,
    AdSet.Field.campaign_id,
    AdSet.Field.status,
    AdSet.Field.daily_budget,
    AdSet.Field.lifetime_budget,
    AdSet.Field.optimization_goal,
    AdSet.Field.billing_event,
    AdSet.Field.targeting,
    AdSet.Field.created_time,
]

AD_FIELDS = [
    Ad.Field.id,
    Ad.Field.name,
    Ad.Field.adset_id,
    Ad.Field.status,
    Ad.Field.created_time,
]


class CampaignService:
    """Manages campaigns, ad sets, and ads via Meta Marketing API."""

    # --- Campaigns ---

    def create_campaign(self, data: CampaignCreate) -> CampaignResponse:
        account = get_ad_account()
        params = {
            Campaign.Field.name: data.name,
            Campaign.Field.objective: data.objective.value,
            Campaign.Field.status: data.status.value,
            Campaign.Field.special_ad_categories: data.special_ad_categories,
        }
        if data.daily_budget is not None:
            params[Campaign.Field.daily_budget] = str(data.daily_budget)
        if data.lifetime_budget is not None:
            params[Campaign.Field.lifetime_budget] = str(data.lifetime_budget)
        if data.bid_strategy:
            params[Campaign.Field.bid_strategy] = data.bid_strategy.value

        result = account.create_campaign(params=params)
        return self.get_campaign(result["id"])

    def list_campaigns(self, status: str | None = None) -> list[CampaignResponse]:
        account = get_ad_account()
        params = {}
        if status:
            params["filtering"] = [{"field": "campaign.effective_status", "operator": "IN", "value": [status]}]
        campaigns = account.get_campaigns(fields=CAMPAIGN_FIELDS, params=params)
        return [CampaignResponse(**{k: c.get(k) for k in c}) for c in campaigns]

    def get_campaign(self, campaign_id: str) -> CampaignResponse:
        campaign = Campaign(campaign_id).api_get(fields=CAMPAIGN_FIELDS)
        return CampaignResponse(**{k: campaign.get(k) for k in campaign})

    def update_campaign(self, campaign_id: str, data: CampaignUpdate) -> CampaignResponse:
        params = {}
        if data.name is not None:
            params[Campaign.Field.name] = data.name
        if data.status is not None:
            params[Campaign.Field.status] = data.status.value
        if data.daily_budget is not None:
            params[Campaign.Field.daily_budget] = str(data.daily_budget)
        if data.lifetime_budget is not None:
            params[Campaign.Field.lifetime_budget] = str(data.lifetime_budget)
        if data.bid_strategy is not None:
            params[Campaign.Field.bid_strategy] = data.bid_strategy.value

        Campaign(campaign_id).api_update(params=params)
        return self.get_campaign(campaign_id)

    def pause_campaign(self, campaign_id: str) -> CampaignResponse:
        return self.update_campaign(campaign_id, CampaignUpdate(status="PAUSED"))

    def resume_campaign(self, campaign_id: str) -> CampaignResponse:
        return self.update_campaign(campaign_id, CampaignUpdate(status="ACTIVE"))

    def delete_campaign(self, campaign_id: str) -> dict:
        Campaign(campaign_id).api_delete()
        return {"id": campaign_id, "deleted": True}

    # --- Ad Sets ---

    def create_adset(self, data: AdSetCreate) -> AdSetResponse:
        account = get_ad_account()
        params = {
            AdSet.Field.name: data.name,
            AdSet.Field.campaign_id: data.campaign_id,
            AdSet.Field.optimization_goal: data.optimization_goal.value,
            AdSet.Field.billing_event: data.billing_event,
            AdSet.Field.targeting: data.targeting.model_dump(exclude_none=True),
            AdSet.Field.status: data.status.value,
        }
        if data.daily_budget is not None:
            params[AdSet.Field.daily_budget] = str(data.daily_budget)
        if data.lifetime_budget is not None:
            params[AdSet.Field.lifetime_budget] = str(data.lifetime_budget)
        if data.bid_amount is not None:
            params[AdSet.Field.bid_amount] = str(data.bid_amount)
        if data.start_time:
            params[AdSet.Field.start_time] = data.start_time
        if data.end_time:
            params[AdSet.Field.end_time] = data.end_time

        result = account.create_ad_set(params=params)
        return self.get_adset(result["id"])

    def list_adsets(self, campaign_id: str | None = None) -> list[AdSetResponse]:
        account = get_ad_account()
        params = {}
        if campaign_id:
            params["filtering"] = [{"field": "campaign.id", "operator": "EQUAL", "value": campaign_id}]
        adsets = account.get_ad_sets(fields=ADSET_FIELDS, params=params)
        return [AdSetResponse(**{k: a.get(k) for k in a}) for a in adsets]

    def get_adset(self, adset_id: str) -> AdSetResponse:
        adset = AdSet(adset_id).api_get(fields=ADSET_FIELDS)
        return AdSetResponse(**{k: adset.get(k) for k in adset})

    def update_adset(self, adset_id: str, data: AdSetUpdate) -> AdSetResponse:
        params = {}
        if data.name is not None:
            params[AdSet.Field.name] = data.name
        if data.status is not None:
            params[AdSet.Field.status] = data.status.value
        if data.daily_budget is not None:
            params[AdSet.Field.daily_budget] = str(data.daily_budget)
        if data.lifetime_budget is not None:
            params[AdSet.Field.lifetime_budget] = str(data.lifetime_budget)
        if data.optimization_goal is not None:
            params[AdSet.Field.optimization_goal] = data.optimization_goal.value
        if data.bid_amount is not None:
            params[AdSet.Field.bid_amount] = str(data.bid_amount)
        if data.targeting is not None:
            params[AdSet.Field.targeting] = data.targeting.model_dump(exclude_none=True)

        AdSet(adset_id).api_update(params=params)
        return self.get_adset(adset_id)

    def delete_adset(self, adset_id: str) -> dict:
        AdSet(adset_id).api_delete()
        return {"id": adset_id, "deleted": True}

    # --- Ads ---

    def create_ad(self, data: AdCreate) -> AdResponse:
        account = get_ad_account()
        params = {
            Ad.Field.name: data.name,
            Ad.Field.adset_id: data.adset_id,
            Ad.Field.creative: {"creative_id": data.creative_id},
            Ad.Field.status: data.status.value,
        }
        result = account.create_ad(params=params)
        return self.get_ad(result["id"])

    def list_ads(self, adset_id: str | None = None) -> list[AdResponse]:
        account = get_ad_account()
        params = {}
        if adset_id:
            params["filtering"] = [{"field": "adset.id", "operator": "EQUAL", "value": adset_id}]
        ads = account.get_ads(fields=AD_FIELDS, params=params)
        return [AdResponse(**{k: a.get(k) for k in a}) for a in ads]

    def get_ad(self, ad_id: str) -> AdResponse:
        ad = Ad(ad_id).api_get(fields=AD_FIELDS)
        return AdResponse(**{k: ad.get(k) for k in ad})

    def update_ad(self, ad_id: str, data: AdUpdate) -> AdResponse:
        params = {}
        if data.name is not None:
            params[Ad.Field.name] = data.name
        if data.status is not None:
            params[Ad.Field.status] = data.status.value
        if data.creative_id is not None:
            params[Ad.Field.creative] = {"creative_id": data.creative_id}

        Ad(ad_id).api_update(params=params)
        return self.get_ad(ad_id)

    def delete_ad(self, ad_id: str) -> dict:
        Ad(ad_id).api_delete()
        return {"id": ad_id, "deleted": True}
