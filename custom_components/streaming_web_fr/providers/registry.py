from __future__ import annotations

import asyncio
import base64
import json
from typing import Any

import aiohttp

from ..models import CatalogPage, MediaItem, ResolvedStream
from .base import ProviderError, StreamingProvider
from .drabam import DrabamProvider


_PROVIDER_TYPES: dict[str, type[StreamingProvider]] = {
    "drabam": DrabamProvider,
}


class ProviderManager:
    def __init__(self, session: aiohttp.ClientSession, providers: list[dict[str, Any]]) -> None:
        self.session = session
        self._providers: dict[str, StreamingProvider] = {}
        for raw in providers:
            if not isinstance(raw, dict) or not bool(raw.get("enabled", True)):
                continue
            provider_type = str(raw.get("type") or "").strip().casefold()
            cls = _PROVIDER_TYPES.get(provider_type)
            if cls is None:
                continue
            provider = cls(session, dict(raw))
            if provider.id:
                self._providers[provider.id] = provider

    def public_providers(self) -> list[dict[str, Any]]:
        result = []
        for provider in sorted(
            self._providers.values(),
            key=lambda item: (item.priority, item.name.casefold()),
        ):
            result.append(
                {
                    "id": provider.id,
                    "name": provider.name,
                    "type": provider.provider_type,
                    "priority": provider.priority,
                    "enabled": provider.enabled,
                    "diagnostics": provider.diagnostics(),
                }
            )
        return result

    def get(self, provider_id: str) -> StreamingProvider:
        provider = self._providers.get(str(provider_id or ""))
        if provider is None:
            raise ProviderError(f"Provider inconnu : {provider_id}")
        return provider

    async def catalog(
        self,
        *,
        provider_id: str | None = None,
        query: str | None = None,
        category: str | None = None,
    ) -> list[MediaItem]:
        providers = [self.get(provider_id)] if provider_id else list(self._providers.values())
        providers.sort(key=lambda p: (p.priority, p.name.casefold()))

        async def load(provider: StreamingProvider) -> list[MediaItem]:
            try:
                items = await provider.browse(category=category)
                if query:
                    needle = str(query).strip().casefold()
                    items = [item for item in items if needle in item.title.casefold()]
                return items
            except Exception:
                return []

        batches = await asyncio.gather(*(load(provider) for provider in providers))
        items: list[MediaItem] = []
        seen: set[str] = set()
        for batch in batches:
            for item in batch:
                if item.uid in seen:
                    continue
                seen.add(item.uid)
                items.append(item)
        return items

    async def catalog_page(
        self,
        *,
        provider_id: str | None = None,
        query: str | None = None,
        category: str | None = None,
        cursor: str | None = None,
        limit: int = 24,
    ) -> CatalogPage:
        providers = [self.get(provider_id)] if provider_id else list(self._providers.values())
        providers.sort(key=lambda p: (p.priority, p.name.casefold()))
        if not providers:
            return CatalogPage()

        if provider_id or len(providers) == 1:
            return await providers[0].browse_page(
                category=category,
                cursor=cursor,
                query=query,
                limit=limit,
            )

        cursors: dict[str, str | None] = {}
        if cursor:
            try:
                prefix, encoded = str(cursor).split(":", 1)
                if prefix != "multi":
                    raise ValueError
                padding = "=" * (-len(encoded) % 4)
                decoded = json.loads(base64.urlsafe_b64decode(encoded + padding))
                if not isinstance(decoded, dict):
                    raise ValueError
                cursors = {str(key): str(value) for key, value in decoded.items()}
            except Exception as err:
                raise ProviderError("Curseur multi-provider invalide") from err

        active_providers = providers if not cursor else [
            provider for provider in providers if provider.id in cursors
        ]
        pages = await asyncio.gather(
            *(
                provider.browse_page(
                    category=category,
                    cursor=cursors.get(provider.id),
                    query=query,
                    limit=limit,
                )
                for provider in active_providers
            ),
            return_exceptions=True,
        )
        items: list[MediaItem] = []
        seen: set[str] = set()
        next_cursors: dict[str, str] = {}
        search_modes: set[str] = set()
        current_page = 0
        for provider, page in zip(active_providers, pages, strict=True):
            if isinstance(page, Exception):
                continue
            search_modes.add(page.search_mode)
            current_page = max(current_page, page.page)
            if page.has_more and page.next_cursor:
                next_cursors[provider.id] = page.next_cursor
            for item in page.items:
                if item.uid not in seen:
                    seen.add(item.uid)
                    items.append(item)
        next_cursor = None
        if next_cursors:
            encoded = base64.urlsafe_b64encode(
                json.dumps(next_cursors, separators=(",", ":")).encode()
            ).decode().rstrip("=")
            next_cursor = f"multi:{encoded}"
        return CatalogPage(
            items=items,
            next_cursor=next_cursor,
            has_more=bool(next_cursors),
            page=current_page,
            search_mode="+".join(sorted(search_modes)) or ("provider" if query else "local"),
        )

    async def details(
        self,
        provider_id: str,
        provider_item_id: str,
        page_url: str | None = None,
        page_referer: str | None = None,
    ) -> MediaItem:
        return await self.get(provider_id).details(
            provider_item_id,
            page_url=page_url,
            page_referer=page_referer,
        )

    async def resolve(
        self,
        provider_id: str,
        provider_item_id: str,
        page_url: str | None = None,
        page_referer: str | None = None,
    ) -> ResolvedStream:
        return await self.get(provider_id).resolve(
            provider_item_id,
            page_url=page_url,
            page_referer=page_referer,
        )

    async def test_provider(self, provider_id: str) -> dict[str, Any]:
        return await self.get(provider_id).test_connection()
