from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

import aiohttp

from ..const import (
    AUTH_API_KEY,
    AUTH_BASIC,
    AUTH_BEARER,
    AUTH_COOKIE,
    AUTH_CUSTOM_HEADERS,
)
from ..models import MediaItem, ResolvedStream


class ProviderError(RuntimeError):
    pass


class StreamingProvider(ABC):
    provider_type = "base"

    def __init__(self, session: aiohttp.ClientSession, config: dict[str, Any]) -> None:
        self.session = session
        self.config = config
        self.id = str(config.get("id") or "").strip()
        self.name = str(config.get("name") or self.id or self.provider_type).strip()
        self.base_url = str(config.get("base_url") or "").strip().rstrip("/")
        self.priority = int(config.get("priority") or 100)
        self.enabled = bool(config.get("enabled", True))

    def _request_kwargs(self) -> dict[str, Any]:
        auth = self.config.get("auth") or {}
        mode = str(auth.get("mode") or "none")
        headers = {
            "User-Agent": "Mozilla/5.0 (Home Assistant; Streaming Web FR)",
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        }
        kwargs: dict[str, Any] = {"headers": headers}

        if mode == AUTH_BASIC:
            username = str(auth.get("username") or "")
            password = str(auth.get("password") or "")
            kwargs["auth"] = aiohttp.BasicAuth(username, password)
        elif mode == AUTH_API_KEY:
            header = str(auth.get("api_key_header") or "X-Api-Key")
            headers[header] = str(auth.get("api_key") or "")
        elif mode == AUTH_BEARER:
            headers["Authorization"] = f"Bearer {str(auth.get('bearer') or '')}"
        elif mode == AUTH_COOKIE:
            headers["Cookie"] = str(auth.get("cookie") or "")
        elif mode == AUTH_CUSTOM_HEADERS:
            raw = auth.get("custom_headers")
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except Exception:
                    raw = {}
            if isinstance(raw, dict):
                headers.update({str(k): str(v) for k, v in raw.items()})

        return kwargs

    async def _ensure_form_login(self) -> None:
        auth = self.config.get("auth") or {}
        if str(auth.get("mode") or "none") != AUTH_FORM_LOGIN or self._form_logged_in:
            return
        login_url = str(auth.get("login_url") or "").strip()
        if not login_url:
            raise ProviderError("URL de connexion manquante")
        username_field = str(auth.get("username_field") or "username")
        password_field = str(auth.get("password_field") or "password")
        payload = {
            username_field: str(auth.get("username") or ""),
            password_field: str(auth.get("password") or ""),
        }
        extra = auth.get("login_extra_fields")
        if isinstance(extra, str) and extra.strip():
            try:
                extra = json.loads(extra)
            except Exception:
                extra = {}
        if isinstance(extra, dict):
            payload.update({str(k): str(v) for k, v in extra.items()})
        async with self.session.post(
            login_url,
            data=payload,
            headers={"User-Agent": "Mozilla/5.0 (Home Assistant; Streaming Web FR)"},
            timeout=aiohttp.ClientTimeout(total=20),
            allow_redirects=True,
        ) as response:
            if response.status >= 400:
                raise ProviderError(f"Échec connexion provider HTTP {response.status}")
            await response.read()
        self._form_logged_in = True

    async def _get_text(
        self,
        url: str,
        *,
        referer: str | None = None,
    ) -> tuple[str, str, int, str]:
        await self._ensure_form_login()
        kwargs = self._request_kwargs()
        headers = dict(kwargs.pop("headers", {}))
        if referer:
            headers["Referer"] = referer
        async with self.session.get(
            url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=20),
            allow_redirects=True,
            **kwargs,
        ) as response:
            body = await response.text(errors="replace")
            return body, str(response.url), response.status, response.headers.get("Content-Type", "")

    @abstractmethod
    async def browse(self, *, category: str | None = None) -> list[MediaItem]:
        raise NotImplementedError

    async def search(self, query: str) -> list[MediaItem]:
        query = str(query or "").strip().casefold()
        items = await self.browse()
        if not query:
            return items
        return [item for item in items if query in item.title.casefold()]

    @abstractmethod
    async def details(self, provider_item_id: str) -> MediaItem:
        raise NotImplementedError

    @abstractmethod
    async def resolve(self, provider_item_id: str) -> ResolvedStream:
        raise NotImplementedError

    async def test_connection(self) -> dict[str, Any]:
        try:
            items = await self.browse()
            return {"ok": True, "items": len(items)}
        except Exception as err:
            return {"ok": False, "error": str(err)}