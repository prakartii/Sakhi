"""Smoke test for the /health endpoint — verifies the app boots and the
DB dependency resolves, nothing more."""

from httpx import AsyncClient


async def test_health_check_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "database" in body
