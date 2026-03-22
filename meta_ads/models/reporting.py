from enum import Enum
from pydantic import BaseModel, Field


class DatePreset(str, Enum):
    TODAY = "today"
    YESTERDAY = "yesterday"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_QUARTER = "this_quarter"
    LAST_3D = "last_3d"
    LAST_7D = "last_7d"
    LAST_14D = "last_14d"
    LAST_28D = "last_28d"
    LAST_30D = "last_30d"
    LAST_90D = "last_90d"
    MAXIMUM = "maximum"


class Breakdown(str, Enum):
    AGE = "age"
    GENDER = "gender"
    COUNTRY = "country"
    REGION = "region"
    PUBLISHER_PLATFORM = "publisher_platform"
    PLATFORM_POSITION = "platform_position"
    DEVICE_PLATFORM = "device_platform"
    IMPRESSION_DEVICE = "impression_device"


class InsightLevel(str, Enum):
    ACCOUNT = "account"
    CAMPAIGN = "campaign"
    ADSET = "adset"
    AD = "ad"


DEFAULT_METRICS = [
    "impressions",
    "reach",
    "clicks",
    "cpc",
    "cpm",
    "ctr",
    "spend",
    "actions",
    "cost_per_action_type",
    "frequency",
]


class ReportRequest(BaseModel):
    level: InsightLevel = InsightLevel.CAMPAIGN
    date_preset: DatePreset | None = DatePreset.LAST_7D
    time_range: dict | None = Field(
        None,
        description='Custom date range: {"since": "2026-03-01", "until": "2026-03-22"}',
    )
    metrics: list[str] = Field(default_factory=lambda: list(DEFAULT_METRICS))
    breakdowns: list[Breakdown] = Field(default_factory=list)
    filtering: list[dict] | None = None
    campaign_id: str | None = None
    adset_id: str | None = None
    ad_id: str | None = None
    limit: int = 100


class InsightRow(BaseModel):
    date_start: str | None = None
    date_stop: str | None = None
    campaign_id: str | None = None
    campaign_name: str | None = None
    adset_id: str | None = None
    adset_name: str | None = None
    ad_id: str | None = None
    ad_name: str | None = None
    impressions: str | None = None
    reach: str | None = None
    clicks: str | None = None
    cpc: str | None = None
    cpm: str | None = None
    ctr: str | None = None
    spend: str | None = None
    frequency: str | None = None
    actions: list[dict] | None = None
    cost_per_action_type: list[dict] | None = None
    # Breakdown fields
    age: str | None = None
    gender: str | None = None
    country: str | None = None


class ReportResponse(BaseModel):
    data: list[InsightRow]
    total_count: int
    summary: dict | None = None
