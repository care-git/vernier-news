import httpx
import pytest

from bot.admin_client import AdminClient, AdminError


def _client(handler) -> AdminClient:
    return AdminClient("http://api:8000", "secret", transport=httpx.MockTransport(handler))


async def test_health_sends_admin_key_and_returns_json():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Admin-Key"] == "secret"
        assert request.url.path == "/api/v1/admin/health"
        return httpx.Response(200, json={"database": {}, "redis": {}})

    data = await _client(handler).health()
    assert data == {"database": {}, "redis": {}}


async def test_ingest_uses_post():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        return httpx.Response(200, json={"task_id": "x", "status": "queued"})

    data = await _client(handler).ingest()
    assert data["task_id"] == "x"


async def test_forbidden_raises_admin_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"detail": "invalid admin key"})

    with pytest.raises(AdminError) as excinfo:
        await _client(handler).health()
    assert "Admin key rejected" in excinfo.value.user_message


async def test_connection_error_raises_admin_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    with pytest.raises(AdminError) as excinfo:
        await _client(handler).health()
    assert "unreachable" in excinfo.value.user_message
