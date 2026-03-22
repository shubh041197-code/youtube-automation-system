from meta_ads.services.campaign_service import CampaignService
from meta_ads.services.creative_service import CreativeService
from meta_ads.services.audience_service import AudienceService
from meta_ads.services.reporting_service import ReportingService
from meta_ads.services.budget_service import BudgetService

_campaign_service: CampaignService | None = None
_creative_service: CreativeService | None = None
_audience_service: AudienceService | None = None
_reporting_service: ReportingService | None = None
_budget_service: BudgetService | None = None


def get_campaign_service() -> CampaignService:
    global _campaign_service
    if _campaign_service is None:
        _campaign_service = CampaignService()
    return _campaign_service


def get_creative_service() -> CreativeService:
    global _creative_service
    if _creative_service is None:
        _creative_service = CreativeService()
    return _creative_service


def get_audience_service() -> AudienceService:
    global _audience_service
    if _audience_service is None:
        _audience_service = AudienceService()
    return _audience_service


def get_reporting_service() -> ReportingService:
    global _reporting_service
    if _reporting_service is None:
        _reporting_service = ReportingService()
    return _reporting_service


def get_budget_service() -> BudgetService:
    global _budget_service
    if _budget_service is None:
        _budget_service = BudgetService()
    return _budget_service
