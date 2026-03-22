from enum import Enum
from pydantic import BaseModel, Field


class CampaignObjective(str, Enum):
    OUTCOME_AWARENESS = "OUTCOME_AWARENESS"
    OUTCOME_ENGAGEMENT = "OUTCOME_ENGAGEMENT"
    OUTCOME_LEADS = "OUTCOME_LEADS"
    OUTCOME_SALES = "OUTCOME_SALES"
    OUTCOME_TRAFFIC = "OUTCOME_TRAFFIC"
    OUTCOME_APP_PROMOTION = "OUTCOME_APP_PROMOTION"


class CampaignStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class BidStrategy(str, Enum):
    LOWEST_COST_WITHOUT_CAP = "LOWEST_COST_WITHOUT_CAP"
    LOWEST_COST_WITH_BID_CAP = "LOWEST_COST_WITH_BID_CAP"
    COST_CAP = "COST_CAP"
    LOWEST_COST_WITH_MIN_ROAS = "LOWEST_COST_WITH_MIN_ROAS"


class OptimizationGoal(str, Enum):
    IMPRESSIONS = "IMPRESSIONS"
    REACH = "REACH"
    LINK_CLICKS = "LINK_CLICKS"
    LANDING_PAGE_VIEWS = "LANDING_PAGE_VIEWS"
    CONVERSIONS = "CONVERSIONS"
    LEAD_GENERATION = "LEAD_GENERATION"
    APP_INSTALLS = "APP_INSTALLS"
    VALUE = "VALUE"


# --- Campaign ---

class CampaignCreate(BaseModel):
    name: str
    objective: CampaignObjective
    status: CampaignStatus = CampaignStatus.PAUSED
    daily_budget: int | None = Field(None, description="Daily budget in cents")
    lifetime_budget: int | None = Field(None, description="Lifetime budget in cents")
    bid_strategy: BidStrategy = BidStrategy.LOWEST_COST_WITHOUT_CAP
    special_ad_categories: list[str] = Field(default_factory=list)


class CampaignUpdate(BaseModel):
    name: str | None = None
    status: CampaignStatus | None = None
    daily_budget: int | None = None
    lifetime_budget: int | None = None
    bid_strategy: BidStrategy | None = None


class CampaignResponse(BaseModel):
    id: str
    name: str
    objective: str | None = None
    status: str | None = None
    daily_budget: str | None = None
    lifetime_budget: str | None = None
    bid_strategy: str | None = None
    created_time: str | None = None
    updated_time: str | None = None


# --- Ad Set ---

class TargetingGeo(BaseModel):
    countries: list[str] = Field(default_factory=list)
    cities: list[dict] | None = None
    regions: list[dict] | None = None


class TargetingSpec(BaseModel):
    geo_locations: TargetingGeo
    age_min: int = 18
    age_max: int = 65
    genders: list[int] | None = Field(None, description="1=male, 2=female")
    interests: list[dict] | None = None
    custom_audiences: list[dict] | None = None
    excluded_custom_audiences: list[dict] | None = None


class AdSetCreate(BaseModel):
    name: str
    campaign_id: str
    daily_budget: int | None = Field(None, description="Daily budget in cents")
    lifetime_budget: int | None = Field(None, description="Lifetime budget in cents")
    optimization_goal: OptimizationGoal = OptimizationGoal.LINK_CLICKS
    billing_event: str = "IMPRESSIONS"
    bid_amount: int | None = Field(None, description="Bid amount in cents")
    targeting: TargetingSpec
    start_time: str | None = None
    end_time: str | None = None
    status: CampaignStatus = CampaignStatus.PAUSED


class AdSetUpdate(BaseModel):
    name: str | None = None
    status: CampaignStatus | None = None
    daily_budget: int | None = None
    lifetime_budget: int | None = None
    optimization_goal: OptimizationGoal | None = None
    bid_amount: int | None = None
    targeting: TargetingSpec | None = None


class AdSetResponse(BaseModel):
    id: str
    name: str
    campaign_id: str | None = None
    status: str | None = None
    daily_budget: str | None = None
    lifetime_budget: str | None = None
    optimization_goal: str | None = None
    billing_event: str | None = None
    targeting: dict | None = None
    created_time: str | None = None


# --- Ad ---

class AdCreate(BaseModel):
    name: str
    adset_id: str
    creative_id: str
    status: CampaignStatus = CampaignStatus.PAUSED


class AdUpdate(BaseModel):
    name: str | None = None
    status: CampaignStatus | None = None
    creative_id: str | None = None


class AdResponse(BaseModel):
    id: str
    name: str
    adset_id: str | None = None
    creative_id: str | None = None
    status: str | None = None
    created_time: str | None = None
