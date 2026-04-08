from __future__ import annotations

from typing import Any


class ApiError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        message: str,
        payload: dict[str, Any] | str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class NyxApiClient:
    def __init__(self, session, base_url: str, default_headers: dict[str, str]) -> None:
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.default_headers = default_headers

    async def post(
        self,
        path: str,
        *,
        json_body: dict[str, Any],
        token: str | None = None,
    ) -> dict[str, Any]:
        headers = {"Content-Type": "application/json", **self.default_headers}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        async with self.session.post(f"{self.base_url}{path}", json=json_body, headers=headers) as response:
            payload = await self._read_payload(response)
            if 200 <= response.status < 300:
                return payload
            raise ApiError(
                status_code=response.status,
                message=self._extract_error_message(payload),
                payload=payload,
            )

    async def _read_payload(self, response) -> dict[str, Any]:
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return await response.json()
        return {"raw": await response.text()}

    @staticmethod
    def _extract_error_message(payload: dict[str, Any] | str | None) -> str:
        if isinstance(payload, dict):
            return str(
                payload.get("error_message")
                or payload.get("message")
                or payload.get("raw")
                or "request failed"
            )
        if isinstance(payload, str):
            return payload
        return "request failed"
