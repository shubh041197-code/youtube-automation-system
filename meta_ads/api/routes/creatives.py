from fastapi import APIRouter, Depends, UploadFile, File
import tempfile
import os

from meta_ads.api.deps import get_creative_service
from meta_ads.services.creative_service import CreativeService
from meta_ads.models.creatives import CreativeCreate, CreativeResponse, ImageUploadResponse

router = APIRouter(tags=["Creatives"])


@router.post("/creatives", response_model=CreativeResponse)
def create_creative(
    data: CreativeCreate,
    svc: CreativeService = Depends(get_creative_service),
):
    return svc.create_creative(data)


@router.get("/creatives", response_model=list[CreativeResponse])
def list_creatives(
    svc: CreativeService = Depends(get_creative_service),
):
    return svc.list_creatives()


@router.get("/creatives/{creative_id}", response_model=CreativeResponse)
def get_creative(
    creative_id: str,
    svc: CreativeService = Depends(get_creative_service),
):
    return svc.get_creative(creative_id)


@router.delete("/creatives/{creative_id}")
def delete_creative(
    creative_id: str,
    svc: CreativeService = Depends(get_creative_service),
):
    return svc.delete_creative(creative_id)


@router.post("/creatives/upload-image", response_model=ImageUploadResponse)
def upload_image(
    file: UploadFile = File(...),
    svc: CreativeService = Depends(get_creative_service),
):
    """Upload an image file for use in ad creatives."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or ".jpg")[1]) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        return svc.upload_image(tmp_path)
    finally:
        os.unlink(tmp_path)
