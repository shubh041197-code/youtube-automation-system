from enum import Enum
from pydantic import BaseModel, Field


class CreativeFormat(str, Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    CAROUSEL = "CAROUSEL"


class CallToAction(str, Enum):
    LEARN_MORE = "LEARN_MORE"
    SHOP_NOW = "SHOP_NOW"
    SIGN_UP = "SIGN_UP"
    BOOK_NOW = "BOOK_NOW"
    CONTACT_US = "CONTACT_US"
    DOWNLOAD = "DOWNLOAD"
    GET_OFFER = "GET_OFFER"
    SUBSCRIBE = "SUBSCRIBE"
    WATCH_MORE = "WATCH_MORE"
    APPLY_NOW = "APPLY_NOW"


class CarouselCard(BaseModel):
    image_hash: str | None = None
    image_url: str | None = None
    link: str
    name: str | None = None
    description: str | None = None


class CreativeCreate(BaseModel):
    name: str
    format: CreativeFormat = CreativeFormat.IMAGE
    page_id: str = Field(..., description="Facebook Page ID to use for the ad")
    link: str | None = Field(None, description="Destination URL")
    message: str | None = Field(None, description="Ad copy / primary text")
    headline: str | None = None
    description: str | None = None
    call_to_action: CallToAction = CallToAction.LEARN_MORE
    image_hash: str | None = Field(None, description="Image hash from uploaded image")
    image_url: str | None = Field(None, description="Image URL (auto-uploaded)")
    video_id: str | None = Field(None, description="Video ID for video ads")
    thumbnail_url: str | None = None
    carousel_cards: list[CarouselCard] | None = Field(None, description="Cards for carousel ads")
    instagram_actor_id: str | None = Field(None, description="Instagram account ID")


class CreativeResponse(BaseModel):
    id: str
    name: str | None = None
    status: str | None = None
    title: str | None = None
    body: str | None = None
    image_url: str | None = None
    thumbnail_url: str | None = None
    object_story_spec: dict | None = None
    created_time: str | None = None


class ImageUploadResponse(BaseModel):
    hash: str
    url: str | None = None
