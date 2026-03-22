from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adimage import AdImage

from meta_ads.meta_client import get_ad_account
from meta_ads.models.creatives import CreativeCreate, CreativeResponse, CreativeFormat, ImageUploadResponse

CREATIVE_FIELDS = [
    AdCreative.Field.id,
    AdCreative.Field.name,
    AdCreative.Field.status,
    AdCreative.Field.title,
    AdCreative.Field.body,
    AdCreative.Field.image_url,
    AdCreative.Field.thumbnail_url,
    AdCreative.Field.object_story_spec,
]


class CreativeService:
    """Manages ad creatives — images, videos, and carousel ads."""

    def upload_image(self, image_path: str) -> ImageUploadResponse:
        """Upload an image file and return its hash."""
        account = get_ad_account()
        image = AdImage(parent_id=account.get_id())
        image[AdImage.Field.filename] = image_path
        image.remote_create()
        return ImageUploadResponse(
            hash=image[AdImage.Field.hash],
            url=image.get(AdImage.Field.url),
        )

    def create_creative(self, data: CreativeCreate) -> CreativeResponse:
        account = get_ad_account()

        if data.format == CreativeFormat.CAROUSEL:
            story_spec = self._build_carousel_spec(data)
        elif data.format == CreativeFormat.VIDEO:
            story_spec = self._build_video_spec(data)
        else:
            story_spec = self._build_image_spec(data)

        params = {
            AdCreative.Field.name: data.name,
            AdCreative.Field.object_story_spec: story_spec,
        }

        result = account.create_ad_creative(params=params)
        return self.get_creative(result["id"])

    def _build_image_spec(self, data: CreativeCreate) -> dict:
        link_data = {
            "link": data.link or "",
            "message": data.message or "",
            "call_to_action": {"type": data.call_to_action.value, "value": {"link": data.link or ""}},
        }
        if data.headline:
            link_data["name"] = data.headline
        if data.description:
            link_data["description"] = data.description
        if data.image_hash:
            link_data["image_hash"] = data.image_hash
        elif data.image_url:
            link_data["picture"] = data.image_url

        spec = {"page_id": data.page_id, "link_data": link_data}
        if data.instagram_actor_id:
            spec["instagram_actor_id"] = data.instagram_actor_id
        return spec

    def _build_video_spec(self, data: CreativeCreate) -> dict:
        video_data = {
            "video_id": data.video_id,
            "message": data.message or "",
            "call_to_action": {
                "type": data.call_to_action.value,
                "value": {"link": data.link or ""},
            },
        }
        if data.headline:
            video_data["title"] = data.headline
        if data.description:
            video_data["link_description"] = data.description
        if data.thumbnail_url:
            video_data["image_url"] = data.thumbnail_url

        spec = {"page_id": data.page_id, "video_data": video_data}
        if data.instagram_actor_id:
            spec["instagram_actor_id"] = data.instagram_actor_id
        return spec

    def _build_carousel_spec(self, data: CreativeCreate) -> dict:
        child_attachments = []
        for card in (data.carousel_cards or []):
            child = {"link": card.link}
            if card.image_hash:
                child["image_hash"] = card.image_hash
            elif card.image_url:
                child["picture"] = card.image_url
            if card.name:
                child["name"] = card.name
            if card.description:
                child["description"] = card.description
            child_attachments.append(child)

        link_data = {
            "message": data.message or "",
            "link": data.link or "",
            "child_attachments": child_attachments,
        }

        spec = {"page_id": data.page_id, "link_data": link_data}
        if data.instagram_actor_id:
            spec["instagram_actor_id"] = data.instagram_actor_id
        return spec

    def list_creatives(self) -> list[CreativeResponse]:
        account = get_ad_account()
        creatives = account.get_ad_creatives(fields=CREATIVE_FIELDS)
        return [CreativeResponse(**{k: c.get(k) for k in c}) for c in creatives]

    def get_creative(self, creative_id: str) -> CreativeResponse:
        creative = AdCreative(creative_id).api_get(fields=CREATIVE_FIELDS)
        return CreativeResponse(**{k: creative.get(k) for k in creative})

    def delete_creative(self, creative_id: str) -> dict:
        AdCreative(creative_id).api_delete()
        return {"id": creative_id, "deleted": True}
