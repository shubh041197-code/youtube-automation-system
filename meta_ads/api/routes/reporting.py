from fastapi import APIRouter, Depends, Query

from meta_ads.api.deps import get_reporting_service
from meta_ads.services.reporting_service import ReportingService
from meta_ads.models.reporting import ReportRequest, ReportResponse, InsightRow

router = APIRouter(tags=["Reporting"])


@router.post("/reports/insights", response_model=ReportResponse)
def get_insights(
    request: ReportRequest,
    svc: ReportingService = Depends(get_reporting_service),
):
    """Get detailed ad insights with custom metrics, breakdowns, and filters."""
    return svc.get_insights(request)


@router.get("/reports/summary")
def get_account_summary(
    date_preset: str = Query("last_7d", description="Date preset: today, yesterday, last_7d, last_30d, etc."),
    svc: ReportingService = Depends(get_reporting_service),
):
    """Get high-level account KPIs."""
    return svc.get_account_summary(date_preset=date_preset)


@router.get("/reports/campaigns/{campaign_id}", response_model=list[InsightRow])
def get_campaign_performance(
    campaign_id: str,
    date_preset: str = Query("last_7d"),
    svc: ReportingService = Depends(get_reporting_service),
):
    """Get daily performance breakdown for a specific campaign."""
    return svc.get_campaign_performance(campaign_id, date_preset=date_preset)
