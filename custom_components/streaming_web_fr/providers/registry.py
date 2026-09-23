from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from ..models import MediaItem, ResolvedStream
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

    async def details(self, provider_id: str, provider_item_id: str) -> MediaItem:
        return await self.get(provider_id).details(provider_item_id)

    async def resolve(self, provider_id: str, provider_item_id: str) -> ResolvedStream:
        return await self.get(provider_id).resolve(provider_item_id)

    async def test_provider(self, provider_id: str) -> dict[str, Any]:
        return await self.get(provider_id).test_connection()
