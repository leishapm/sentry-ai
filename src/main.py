from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import api_router
from src.core.config import Environment, settings
from src.core.exceptions import setup_exception_handlers
from src.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "SENTRY AI Execution Firewall API starting",
        extra={"environment": settings.environment, "version": settings.app_version},
    )
    yield
    logger.info("SENTRY AI Execution Firewall API shutting down")


def create_app() -> FastAPI:
    app_kwargs = {
        "title": settings.app_name,
        "version": settings.app_version,
        "description": (
            "SENTRY — AI Execution Firewall backend API. "
            "Provides real-time policy evaluation, risk engine scoring, AI reasoning, "
            "audit trail recording, and human-in-the-loop approval workflows for AI agents."
        ),
        "lifespan": lifespan,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }

    if settings.environment == Environment.PRODUCTION:
        app_kwargs["openapi_url"] = None
        app_kwargs["docs_url"] = None
        app_kwargs["redoc_url"] = None

    app = FastAPI(**app_kwargs)

    # Register custom exception handlers
    setup_exception_handlers(app)

    # Configure CORS
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
