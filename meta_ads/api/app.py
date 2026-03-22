from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from facebook_business.exceptions import FacebookRequestError
import logging

from meta_ads.api.routes import campaigns, creatives, audiences, reporting, budget


def create_app() -> FastAPI:
    app = FastAPI(
        title="Meta Ads Automation API",
        description="Full automation for Meta (Facebook/Instagram) advertising — campaigns, creatives, audiences, reporting, and budget optimization.",
        version="1.0.0",
    )

    # Register routes
    app.include_router(campaigns.router, prefix="/api/v1")
    app.include_router(creatives.router, prefix="/api/v1")
    app.include_router(audiences.router, prefix="/api/v1")
    app.include_router(reporting.router, prefix="/api/v1")
    app.include_router(budget.router, prefix="/api/v1")

    @app.exception_handler(FacebookRequestError)
    async def meta_api_error_handler(request: Request, exc: FacebookRequestError):
        logging.error(f"Meta API error: {exc.api_error_message()}")
        return JSONResponse(
            status_code=exc.http_status(),
            content={
                "error": "meta_api_error",
                "message": exc.api_error_message(),
                "code": exc.api_error_code(),
                "subcode": exc.api_error_subcode(),
            },
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        logging.exception("Unhandled error")
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": str(exc)},
        )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
