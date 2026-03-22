from fastapi import APIRouter, Depends, Query

from meta_ads.api.deps import get_campaign_service
from meta_ads.services.campaign_service import CampaignService
from meta_ads.models.campaigns import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    AdSetCreate, AdSetUpdate, AdSetResponse,
    AdCreate, AdUpdate, AdResponse,
)

router = APIRouter(tags=["Campaigns"])


# --- Campaigns ---

@router.post("/campaigns", response_model=CampaignResponse)
def create_campaign(
    data: CampaignCreate,
    svc: CampaignService = Depends(get_campaign_service),
):
    return svc.create_campaign(data)


@router.get("/campaigns", response_model=list[CampaignResponse])
def list_campaigns(
    status: str | None = Query(None, description="Filter by status: ACTIVE, PAUSED, etc."),
    svc: CampaignService = Depends(get_campaign_service),
):
    return svc.list_campaigns(status=status)


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: str,
    svc: CampaignService = Depends(get_campaign_service),
):
    return svc.get_campaign(campaign_id)


@router.patch("/campaigns/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: str,
    data: CampaignUpdate,
    svc: CampaignService = Depends(get_campaign_service),
):
    return svc.update_campaign(campaign_id, data)


@router.post("/campaigns/{campaign_id}/pause", response_model=CampaignResponse)
def pause_campaign(
    campaign_id: str,
    svc: CampaignService = Depends(get_campaign_service),
):
    return svc.pause_campaign(campaign_id)


@router.post("/campaigns/{campaign_id}/resume", response_model=CampaignResponse)
def resume_campaign(
    campaign_id: str,
    svc: CampaignService = Depends(get_campaign_service),
):
    return svc.resume_campaign(campaign_id)


@router.delete("/campaigns/{campaign_id}")
def delete_campaign(
    campaign_id: str,
    svc: CampaignService = Depends(get_campaign_service),
):
    return svc.delete_campaign(campaign_id)


# --- Ad Sets ---

@router.post("/adsets", response_model=AdSetResponse)
def create_adset(
    data: AdSetCreate,
    svc: CampaignService = Depends(get_campaign_service),
):
    return svc.create_adset(data)


@router.get("/adsets", response_model=list[AdSetResponse])
def list_adsets(
    campaign_id: str | None = Query(None),
    svc: CampaignService = Depends(get_campaign_service),
):
    return svc.list_adsets(campaign_id=campaign_id)


@router.get("/adsets/{adset_id}", response_model=AdSetResponse)
def get_adset(
    adset_id: str,
    svc: CampaignService = Depends(get_campaign_service),
):
    return svc.get_adset(adset_id)


@router.patch("/adsets/{adset_id}", response_model=AdSetResponse)
def update_adset(
    adset_id: str,
    data: AdSetUpdate,
    svc: CampaignService = Depends(get_campaign_service),
):
    return svc.update_adset(adset_id, data)


@router.delete("/adsets/{adset_id}")
def delete_adset(
    adset_id: str,
    svc: CampaignService = Depends(get_campaign_service),
):
    return svc.delete_adset(adset_id)


# --- Ads ---

@router.post("/ads", response_model=AdResponse)
def create_ad(
    data: AdCreate,
    svc: CampaignService = Depends(get_campaign_service),
):
    return svc.create_ad(data)


@router.get("/ads", response_model=list[AdResponse])
def list_ads(
    adset_id: str | None = Query(None),
    svc: CampaignService = Depends(get_campaign_service),
):
    return svc.list_ads(adset_id=adset_id)


@router.get("/ads/{ad_id}", response_model=AdResponse)
def get_ad(
    ad_id: str,
    svc: CampaignService = Depends(get_campaign_service),
):
    return svc.get_ad(ad_id)


@router.patch("/ads/{ad_id}", response_model=AdResponse)
def update_ad(
    ad_id: str,
    data: AdUpdate,
    svc: CampaignService = Depends(get_campaign_service),
):
    return svc.update_ad(ad_id, data)


@router.delete("/ads/{ad_id}")
def delete_ad(
    ad_id: str,
    svc: CampaignService = Depends(get_campaign_service),
):
    return svc.delete_ad(ad_id)
