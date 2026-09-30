from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MediaItem:
    provider_id: str
    provider_item_id: str
    title: str
    year: int | None = None
    media_type: str = "movie"
    poster: str | None = None
    overview: str | None = None
    genres: list[str] = field(default_factory=list)
    page_url: str | None = None
    playable: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def uid(self) -> str:
        return f"{self.provider_id}:{self.provider_item_id}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "provider_id": self.provider_id,
            "provider_item_id": self.provider_item_id,
            "title": self.title,
            "year": self.year,
            "media_type": self.media_type,
            "poster": self.poster,
            "overview": self.overview,
            "genres": list(self.genres),
            "page_url": self.page_url,
            "playable": self.playable,
            "extra": dict(self.extra),
        }


@dataclass(slots=True)
class CatalogPage:
    items: list[MediaItem] = field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False
    page: int = 0
    search_mode: str = "local"


@dataclass(slots=True)
class ResolvedStream:
    provider_id: str
    provider_item_id: str
    url: str
    stream_type: str = "hls"
    referer: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_item_id": self.provider_item_id,
            "url": self.url,
            "stream_type": self.stream_type,
            "referer": self.referer,
        }
