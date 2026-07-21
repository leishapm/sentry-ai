from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.session import get_session
from src.health.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns service metadata and verifies backend database connectivity.",
)
async def health_check(
    session: AsyncSession = Depends(get_session),
) -> HealthResponse:
    db_status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "unreachable"

    overall_status = "ok" if db_status == "ok" else "degraded"

    return HealthResponse(
        status=overall_status,
        service=settings.app_name,
        environment=settings.environment,
        version=settings.app_version,
        database=db_status,
    )
