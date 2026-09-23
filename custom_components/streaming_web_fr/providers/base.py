from __future__ import annotations

import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urljoin, urlsplit

import aiohttp
from yarl import URL

from ..const import (
    AUTH_API_KEY,
    AUTH_BASIC,
    AUTH_BEARER,
    AUTH_COOKIE,
    AUTH_CUSTOM_HEADERS,
    AUTH_FORM_LOGIN,
)
from ..models import CatalogPage, MediaItem, ResolvedStream


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
        self._form_logged_in = False
        # Home Assistant's shared ClientSession may intentionally use a dummy
        # cookie jar. Providers still need browser-like, domain-scoped cookies
        # across catalog, details and player requests.
        self._cookie_jar = aiohttp.CookieJar(unsafe=True)
        self._request_lock = asyncio.Lock()
        self._last_request_at = 0.0
        self._request_count = 0
        self._cache_hits = 0
        self._text_cache: dict[tuple[str, str], tuple[float, tuple[str, str, int, str]]] = {}
        self._circuit_open_until = 0.0

    def diagnostics(self) -> dict[str, Any]:
        return {
            "requests": self._request_count,
            "cache_hits": self._cache_hits,
            "circuit_open_seconds": max(
                0, int(self._circuit_open_until - time.monotonic())
            ),
        }

    async def _wait_for_request_slot(self) -> None:
        cooldown = self._circuit_open_until - time.monotonic()
        if cooldown > 0:
            raise ProviderError(
                f"Provider temporairement en pause ({max(1, int(cooldown))} s)"
            )

        interval = max(
            0.5,
            min(float(self.config.get("request_interval_seconds") or 1.25), 10.0),
        )
        async with self._request_lock:
            cooldown = self._circuit_open_until - time.monotonic()
            if cooldown > 0:
                raise ProviderError(
                    f"Provider temporairement en pause ({max(1, int(cooldown))} s)"
                )
            wait = interval - (time.monotonic() - self._last_request_at)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request_at = time.monotonic()
            self._request_count += 1

    def _open_circuit(self) -> None:
        cooldown = max(
            60.0,
            min(float(self.config.get("circuit_breaker_seconds") or 900), 3600.0),
        )
        self._circuit_open_until = time.monotonic() + cooldown

    def _request_kwargs(self) -> dict[str, Any]:
        auth = self.config.get("auth") or {}
        mode = str(auth.get("mode") or "none")
        headers = {
            "User-Agent": "Mozilla/5.0 (Home Assistant; Streaming Web FR)",
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.7",
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
        await self._wait_for_request_slot()
        async with self.session.post(
            login_url,
            data=payload,
            headers={"User-Agent": "Mozilla/5.0 (Home Assistant; Streaming Web FR)"},
            cookies=self._cookie_jar.filter_cookies(URL(login_url)),
            timeout=aiohttp.ClientTimeout(total=20),
            allow_redirects=True,
        ) as response:
            self._cookie_jar.update_cookies(response.cookies, response.url)
            if response.status in {403, 429}:
                self._open_circuit()
                await response.read()
                raise ProviderError(
                    f"Provider HTTP {response.status} : accès mis en pause 15 min"
                )
            if response.status >= 400:
                raise ProviderError(f"Échec connexion provider HTTP {response.status}")
            await response.read()
        self._form_logged_in = True

    async def _get_text(
        self,
        url: str,
        *,
        referer: str | None = None,
        cache_ttl: float | None = None,
    ) -> tuple[str, str, int, str]:
        ttl = (
            float(self.config.get("cache_ttl_seconds") or 600)
            if cache_ttl is None
            else float(cache_ttl)
        )
        cache_key = (str(url), str(referer or ""))
        cached = self._text_cache.get(cache_key)
        if ttl > 0 and cached and cached[0] > time.monotonic():
            self._cache_hits += 1
            return cached[1]

        await self._ensure_form_login()
        kwargs = self._request_kwargs()
        base_headers = dict(kwargs.pop("headers", {}))
        current_url = str(url)
        current_referer = referer
        seen = {current_url}
        redirect_trace: list[str] = []

        for _ in range(11):
            await self._wait_for_request_slot()
            headers = dict(base_headers)
            if current_referer:
                headers["Referer"] = current_referer
            async with self.session.get(
                current_url,
                headers=headers,
                cookies=self._cookie_jar.filter_cookies(URL(current_url)),
                timeout=aiohttp.ClientTimeout(total=20),
                allow_redirects=False,
                **kwargs,
            ) as response:
                self._cookie_jar.update_cookies(response.cookies, response.url)
                if response.status in {403, 429}:
                    self._open_circuit()
                    await response.read()
                    raise ProviderError(
                        f"Provider HTTP {response.status} : accès mis en pause 15 min"
                    )
                location = response.headers.get("Location")
                if response.status in {301, 302, 303, 307, 308} and location:
                    next_url = urljoin(str(response.url), location)
                    current_path = urlsplit(str(response.url)).path or "/"
                    next_path = urlsplit(next_url).path or "/"
                    redirect_trace.append(
                        f"{response.status} {current_path} → {next_path}"
                    )
                    await response.read()
                    if next_url in seen:
                        self._open_circuit()
                        raise ProviderError(
                            "Boucle de redirection HTTP : "
                            + " | ".join(redirect_trace[-6:])
                        )
                    seen.add(next_url)
                    current_referer = str(response.url)
                    current_url = next_url
                    continue

                body = await response.text(errors="replace")
                result = (
                    body,
                    str(response.url),
                    response.status,
                    response.headers.get("Content-Type", ""),
                )
                if ttl > 0 and response.status < 400:
                    self._text_cache[cache_key] = (time.monotonic() + ttl, result)
                return result

        self._open_circuit()
        raise ProviderError(
            "Trop de redirections HTTP : " + " | ".join(redirect_trace[-6:])
        )

    @abstractmethod
    async def browse(self, *, category: str | None = None) -> list[MediaItem]:
        raise NotImplementedError

    async def browse_page(
        self,
        *,
        category: str | None = None,
        cursor: str | None = None,
        query: str | None = None,
        limit: int = 24,
    ) -> CatalogPage:
        """Return one provider page.

        Providers without remote pagination keep the legacy browse contract.
        """
        items = await self.browse(category=category)
        needle = str(query or "").strip().casefold()
        if needle:
            items = [item for item in items if needle in item.title.casefold()]
        return CatalogPage(items=items, search_mode="local")

    async def search(self, query: str) -> list[MediaItem]:
        query = str(query or "").strip().casefold()
        items = await self.browse()
        if not query:
            return items
        return [item for item in items if query in item.title.casefold()]

    @abstractmethod
    async def details(
        self,
        provider_item_id: str,
        page_url: str | None = None,
        page_referer: str | None = None,
    ) -> MediaItem:
        raise NotImplementedError

    @abstractmethod
    async def resolve(
        self,
        provider_item_id: str,
        page_url: str | None = None,
        page_referer: str | None = None,
    ) -> ResolvedStream:
        raise NotImplementedError

    async def test_connection(self) -> dict[str, Any]:
        try:
            items = await self.browse()
            return {"ok": True, "items": len(items)}
        except Exception as err:
            return {"ok": False, "error": str(err)}
