from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.db.session import get_session
from src.main import app


async def fake_session() -> object:
    mock = AsyncMock()
    mock.execute = AsyncMock(return_value=MagicMock())
    yield mock


@pytest.mark.asyncio
async def test_health_check() -> None:
    app.dependency_overrides[get_session] = fake_session
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["database"] == "ok"
    finally:
        app.dependency_overrides.clear()
