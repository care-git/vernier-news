from __future__ import annotations

import httpx


class AdminError(Exception):
    """Raised when an admin API call fails. Carries a user-facing message."""

    def __init__(self, user_message: str) -> None:
        super().__init__(user_message)
        self.user_message = user_message


class AdminClient:
    """Thin async wrapper over the Vernier ``/api/v1/admin/*`` endpoints."""

    def __init__(
        self,
        base_url: str,
        admin_key: str | None,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {"X-Admin-Key": admin_key or ""}
        self._timeout = timeout
        self._transport = transport

    async def _request(self, method: str, path: str) -> dict:
        url = f"{self._base_url}{path}"
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.request(method, url, headers=self._headers)
        except httpx.RequestError as exc:
            raise AdminError("⚠️ API unreachable") from exc

        if response.status_code == 403:
            raise AdminError("⚠️ Admin key rejected")
        if response.status_code >= 400:
            raise AdminError(f"⚠️ API error {response.status_code}")
        return response.json()

    async def health(self) -> dict:
        return await self._request("GET", "/api/v1/admin/health")

    async def ingest(self) -> dict:
        return await self._request("POST", "/api/v1/admin/ingest")

    async def cluster_stats(self) -> dict:
        return await self._request("GET", "/api/v1/admin/clusters/stats")

    async def sources(self) -> dict:
        return await self._request("GET", "/api/v1/admin/sources")
