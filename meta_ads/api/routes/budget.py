from fastapi import APIRouter, Depends, Query

from meta_ads.api.deps import get_budget_service
from meta_ads.services.budget_service import BudgetService

router = APIRouter(tags=["Budget Optimization"])


@router.get("/budget/recommendations/{campaign_id}")
def get_budget_recommendations(
    campaign_id: str,
    days: int = Query(7, description="Number of days to analyze"),
    svc: BudgetService = Depends(get_budget_service),
):
    """Analyze campaign performance and get budget recommendations."""
    return svc.get_budget_recommendations(campaign_id, days=days)


@router.post("/budget/set/{campaign_id}")
def set_campaign_budget(
    campaign_id: str,
    daily_budget_cents: int = Query(..., description="Daily budget in cents (e.g., 5000 = $50.00)"),
    svc: BudgetService = Depends(get_budget_service),
):
    """Set daily budget for a campaign."""
    return svc.set_campaign_budget(campaign_id, daily_budget_cents)


@router.post("/budget/pause-underperforming/{campaign_id}")
def pause_underperforming_ads(
    campaign_id: str,
    ctr_threshold: float = Query(0.5, description="Pause ads with CTR below this (%)"),
    min_impressions: int = Query(1000, description="Minimum impressions before evaluating"),
    svc: BudgetService = Depends(get_budget_service),
):
    """Auto-pause ads with poor CTR after sufficient impressions."""
    return svc.pause_underperforming_ads(campaign_id, ctr_threshold=ctr_threshold, min_impressions=min_impressions)


@router.post("/budget/scale-winners/{campaign_id}")
def scale_winning_adsets(
    campaign_id: str,
    ctr_threshold: float = Query(2.0, description="Scale ad sets with CTR above this (%)"),
    budget_increase: float = Query(0.2, description="Budget increase ratio (0.2 = 20%)"),
    svc: BudgetService = Depends(get_budget_service),
):
    """Increase budget for high-performing ad sets."""
    return svc.scale_winning_adsets(campaign_id, ctr_threshold=ctr_threshold, budget_increase=budget_increase)
