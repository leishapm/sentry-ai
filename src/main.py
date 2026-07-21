from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import api_router
from src.core.config import Environment, settings
from src.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "SENTRY API starting",
        extra={"environment": settings.environment, "version": settings.app_version},
    )
    yield


def create_app() -> FastAPI:
    app_kwargs = {
        "title": settings.app_name,
        "version": settings.app_version,
        "description": "Backend foundation for the SENTRY AI Execution Firewall.",
        "lifespan": lifespan,
    }

    if settings.environment == Environment.PRODUCTION:
        app_kwargs["openapi_url"] = None
        app_kwargs["docs_url"] = None
        app_kwargs["redoc_url"] = None

    app = FastAPI(**app_kwargs)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    return app


app = create_app()
