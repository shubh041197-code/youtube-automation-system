from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

from meta_ads.config import get_settings

_api: FacebookAdsApi | None = None
_ad_account: AdAccount | None = None


def init_api() -> FacebookAdsApi:
    """Initialize the Meta Marketing API client."""
    global _api
    if _api is None:
        settings = get_settings()
        _api = FacebookAdsApi.init(
            app_id=settings.meta_app_id,
            app_secret=settings.meta_app_secret,
            access_token=settings.meta_access_token,
        )
    return _api


def get_ad_account() -> AdAccount:
    """Get the configured Ad Account instance."""
    global _ad_account
    if _ad_account is None:
        init_api()
        settings = get_settings()
        _ad_account = AdAccount(settings.meta_ad_account_id)
    return _ad_account
