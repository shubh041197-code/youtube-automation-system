from fastapi import APIRouter, Depends

from meta_ads.api.deps import get_audience_service
from meta_ads.services.audience_service import AudienceService
from meta_ads.models.audiences import (
    CustomAudienceCreate,
    LookalikeAudienceCreate,
    AudienceResponse,
)

router = APIRouter(tags=["Audiences"])


@router.post("/audiences/custom", response_model=AudienceResponse)
def create_custom_audience(
    data: CustomAudienceCreate,
    svc: AudienceService = Depends(get_audience_service),
):
    return svc.create_custom_audience(data)


@router.post("/audiences/lookalike", response_model=AudienceResponse)
def create_lookalike_audience(
    data: LookalikeAudienceCreate,
    svc: AudienceService = Depends(get_audience_service),
):
    return svc.create_lookalike_audience(data)


@router.get("/audiences", response_model=list[AudienceResponse])
def list_audiences(
    svc: AudienceService = Depends(get_audience_service),
):
    return svc.list_audiences()


@router.get("/audiences/{audience_id}", response_model=AudienceResponse)
def get_audience(
    audience_id: str,
    svc: AudienceService = Depends(get_audience_service),
):
    return svc.get_audience(audience_id)


@router.delete("/audiences/{audience_id}")
def delete_audience(
    audience_id: str,
    svc: AudienceService = Depends(get_audience_service),
):
    return svc.delete_audience(audience_id)
