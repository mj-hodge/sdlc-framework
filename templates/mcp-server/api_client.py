"""
Template API client — direct httpx calls with auto-pagination.

Don't use SDK wrappers — they're often broken or outdated.
Per F-1: instantiate per-request, never cache.

Usage:
    client = MyApiClient(credentials, rate_limiter)
    campaigns = await client.list_items(scope_id="123", limit=50)
"""

from __future__ import annotations

from typing import Any

import httpx

_BASE_URL = "https://api.example.com"  # TODO: Set your API base URL


class ApiClientTemplate:
    """Direct httpx API client with auto-pagination and graceful degradation."""

    def __init__(self, credentials: dict, rate_limiter: Any = None) -> None:
        self.credentials = credentials
        self.rate_limiter = rate_limiter

    def _build_headers(self, scope_id: str | None = None, content_type: str | None = None) -> dict:
        headers = {
            "Authorization": f"Bearer {self.credentials.get('access_token', '')}",
            "Content-Type": "application/json",
        }
        if scope_id:
            headers["X-Scope"] = scope_id  # TODO: Set your scope header name
        if content_type:
            headers["Content-Type"] = content_type
            headers["Accept"] = content_type
        return headers

    async def _get(self, url: str, headers: dict, params: dict | None = None) -> Any:
        """GET with graceful degradation — returns {} on error."""
        async with httpx.AsyncClient() as http:
            resp = await http.get(url, headers=headers, params=params, timeout=30.0)
            if resp.is_error:
                return {}
            return resp.json()

    async def _post(self, url: str, headers: dict, body: dict) -> dict:
        """POST with graceful degradation — returns {} on error."""
        async with httpx.AsyncClient() as http:
            resp = await http.post(url, headers=headers, json=body, timeout=30.0)
            if resp.is_error:
                return {}
            return resp.json()

    async def _paginated_list(
        self, url: str, headers: dict, body: dict, result_key: str, max_pages: int = 50
    ) -> list[dict]:
        """Auto-paginate a POST list endpoint using nextToken."""
        all_items: list[dict] = []
        for _ in range(max_pages):
            payload = await self._post(url, headers, body)
            items = payload.get(result_key, [])
            all_items.extend(items)
            next_token = payload.get("nextToken")
            if not next_token or not items:
                break
            body = {**body, "nextToken": next_token}
        return all_items
