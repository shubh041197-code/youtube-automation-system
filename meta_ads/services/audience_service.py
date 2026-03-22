from facebook_business.adobjects.customaudience import CustomAudience

from meta_ads.meta_client import get_ad_account
from meta_ads.models.audiences import (
    CustomAudienceCreate,
    LookalikeAudienceCreate,
    AudienceResponse,
)

AUDIENCE_FIELDS = [
    CustomAudience.Field.id,
    CustomAudience.Field.name,
    CustomAudience.Field.description,
    CustomAudience.Field.subtype,
    CustomAudience.Field.approximate_count_lower_bound,
    CustomAudience.Field.time_created,
    CustomAudience.Field.time_updated,
    CustomAudience.Field.delivery_status,
]


class AudienceService:
    """Manages custom and lookalike audiences."""

    def create_custom_audience(self, data: CustomAudienceCreate) -> AudienceResponse:
        account = get_ad_account()
        params = {
            CustomAudience.Field.name: data.name,
            CustomAudience.Field.subtype: data.subtype.value,
        }
        if data.description:
            params[CustomAudience.Field.description] = data.description
        if data.customer_file_source:
            params[CustomAudience.Field.customer_file_source] = data.customer_file_source
        if data.rule:
            params[CustomAudience.Field.rule] = data.rule
        if data.retention_days:
            params["retention_days"] = data.retention_days
        if data.pixel_id:
            params[CustomAudience.Field.pixel_id] = data.pixel_id

        result = account.create_custom_audience(params=params)
        return self.get_audience(result["id"])

    def create_lookalike_audience(self, data: LookalikeAudienceCreate) -> AudienceResponse:
        account = get_ad_account()
        params = {
            CustomAudience.Field.name: data.name,
            CustomAudience.Field.subtype: "LOOKALIKE",
            "origin_audience_id": data.source_audience_id,
            "lookalike_spec": {
                "type": "similarity",
                "country": data.country,
                "ratio": data.ratio,
            },
        }
        if data.description:
            params[CustomAudience.Field.description] = data.description

        result = account.create_custom_audience(params=params)
        return self.get_audience(result["id"])

    def list_audiences(self) -> list[AudienceResponse]:
        account = get_ad_account()
        audiences = account.get_custom_audiences(fields=AUDIENCE_FIELDS)
        return [AudienceResponse(**{k: a.get(k) for k in a}) for a in audiences]

    def get_audience(self, audience_id: str) -> AudienceResponse:
        audience = CustomAudience(audience_id).api_get(fields=AUDIENCE_FIELDS)
        return AudienceResponse(**{k: audience.get(k) for k in audience})

    def delete_audience(self, audience_id: str) -> dict:
        CustomAudience(audience_id).api_delete()
        return {"id": audience_id, "deleted": True}
