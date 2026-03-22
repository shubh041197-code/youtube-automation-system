from enum import Enum
from pydantic import BaseModel, Field


class AudienceSubtype(str, Enum):
    CUSTOM = "CUSTOM"
    WEBSITE = "WEBSITE"
    APP = "APP"
    OFFLINE = "OFFLINE"
    ENGAGEMENT = "ENGAGEMENT"
    LOOKALIKE = "LOOKALIKE"


class CustomAudienceCreate(BaseModel):
    name: str
    description: str | None = None
    subtype: AudienceSubtype = AudienceSubtype.CUSTOM
    customer_file_source: str | None = Field(
        None, description="Source: USER_PROVIDED_ONLY, PARTNER_PROVIDED_ONLY, BOTH_USER_AND_PARTNER_PROVIDED"
    )
    rule: dict | None = Field(None, description="Rule-based audience definition (for website/app audiences)")
    retention_days: int | None = Field(None, description="Days to retain users in the audience")
    pixel_id: str | None = Field(None, description="Meta Pixel ID for website audiences")


class LookalikeAudienceCreate(BaseModel):
    name: str
    source_audience_id: str = Field(..., description="Source custom audience ID")
    country: str = Field(..., description="Country code (e.g., 'US')")
    ratio: float = Field(0.01, ge=0.01, le=0.20, description="Lookalike ratio (1%-20%)")
    description: str | None = None


class AudienceResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    subtype: str | None = None
    approximate_count: int | None = None
    time_created: str | None = None
    time_updated: str | None = None
    delivery_status: dict | None = None
