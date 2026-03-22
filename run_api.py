#!/usr/bin/env python3
"""Start the Meta Ads Automation API server."""

import uvicorn
from meta_ads.config import get_settings


def main():
    settings = get_settings()
    uvicorn.run(
        "meta_ads.api.app:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
