from __future__ import annotations

import html as html_lib
import hashlib
import re
import unicodedata
from urllib.parse import urljoin, urlsplit, urlunsplit

from ..models import CatalogPage, MediaItem, ResolvedStream
from .base import ProviderError, StreamingProvider


_LINK_RE = re.compile(
    r'<a[^>]+href=["\'](?P<href>[^"\']*/b/drabam/(?P<id>\d+)[^"\']*)["\'][^>]*>(?P<body>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_IMG_RE = re.compile(r'<img[^>]+(?:src|data-src)=["\']([^"\']+)["\']', re.IGNORECASE)
_TITLE_ATTR_RE = re.compile(r'(?:title|alt)=["\']([^"\']+)["\']', re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
_IFRAME_RE = re.compile(r'<iframe[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
_M3U8_ABS_RE = re.compile(
    r'https?:(?:\\/\\/|//)[^"\'<>\s]+?\.m3u8(?:\?[^"\'<>\s]+)?',
    re.IGNORECASE,
)
_M3U8_REL_RE = re.compile(r'["\']([^"\']+\.m3u8(?:\?[^"\']*)?)["\']', re.IGNORECASE)
_META_DESC_RE = re.compile(
    r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
_HEADING_RE = re.compile(r"<h[1-6][^>]*>(.*?)</h[1-6]>", re.IGNORECASE | re.DOTALL)
_ANCHOR_RE = re.compile(r"<a[^>]+href=['\"](?P<href>[^'\"]+)['\"][^>]*>(?P<body>.*?)</a>", re.IGNORECASE | re.DOTALL)
_OG_IMAGE_RE = re.compile(
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_CURSOR_RE = re.compile(r"^(?P<page>\d+)(?::(?P<fingerprint>[0-9a-f]{12}))?$")


def _clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(_TAG_RE.sub(" ", value or ""))).strip()


def _norm(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", _clean(value)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text).strip().casefold()


def _section_key(value: str | None) -> str | None:
    text = _norm(value)
    if "dernier" in text and "ajout" in text:
        return "latest"
    if "affiche" in text:
        return "featured"
    if "animation" in text:
        return "animation"
    if "doc" in text or "spectacle" in text:
        return "docs_shows"
    return None


class DrabamProvider(StreamingProvider):
    provider_type = "drabam"

    def _home_url(self) -> str:
        if not self.base_url:
            raise ProviderError("Base URL manquante")
        path = urlsplit(self.base_url).path.rstrip("/")
        if path.endswith("/home/drabam"):
            return self.base_url
        return f"{self.base_url}/home/drabam"

    def _detail_url(self, provider_item_id: str) -> str:
        base = self.base_url
        if base.endswith("/home/drabam"):
            base = base[: -len("/home/drabam")]
        return f"{base.rstrip('/')}/b/drabam/{provider_item_id}"

    def _catalog_url(self, source: str, final_url: str) -> str | None:
        fallback = None
        for match in _ANCHOR_RE.finditer(source):
            href = match.group("href")
            if "/c/drabam/" not in href:
                continue
            label = _norm(match.group("body"))
            url = urljoin(final_url, href)
            if label == "tout" or "explorer le catalogue" in label:
                return url
            fallback = fallback or url
        return fallback

    @staticmethod
    def _page_url(catalog_url: str, page: int) -> str:
        parts = urlsplit(catalog_url)
        path = parts.path.rstrip("/")
        if re.search(r"/\d+$", path):
            path = re.sub(r"/\d+$", f"/{page}", path)
        elif page:
            path = f"{path}/{page}"
        return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))

    @staticmethod
    def _fingerprint(items: list[MediaItem]) -> str:
        raw = "|".join(item.provider_item_id for item in items).encode()
        return hashlib.sha1(raw).hexdigest()[:12]

    @staticmethod
    def _next_catalog_index(source: str, catalog_url: str, current: int) -> int:
        """Read an embedded next offset/page, with sequential fallback."""
        path = urlsplit(catalog_url).path.rstrip("/")
        prefix = re.sub(r"/\d+$", "", path)
        pattern = re.compile(rf"{re.escape(prefix)}/(?P<index>\d+)")
        candidates = {
            int(match.group("index"))
            for match in pattern.finditer(html_lib.unescape(source).replace("\\/", "/"))
            if int(match.group("index")) > current
        }
        return min(candidates) if candidates else current + 1

    @staticmethod
    def _decode_cursor(cursor: str | None) -> tuple[int, str | None]:
        if not cursor:
            return 0, None
        match = _CURSOR_RE.fullmatch(str(cursor))
        if not match:
            raise ProviderError("Curseur catalogue invalide")
        return int(match.group("page")), match.group("fingerprint")

    async def _catalog_page(
        self,
        catalog_url: str,
        page: int,
        previous_fingerprint: str | None,
    ) -> tuple[list[MediaItem], str | None, bool]:
        page_url = self._page_url(catalog_url, page)
        source, final_url, status, _ = await self._get_text(page_url)
        if status >= 400:
            if page > 0 and status in {404, 410}:
                return [], None, False
            raise ProviderError(f"Provider catalogue HTTP {status}")

        items = self._extract_items(source, final_url)
        if not items:
            return [], None, False

        fingerprint = self._fingerprint(items)
        # Some providers redirect an unknown page to page zero. Comparing the
        # payload fingerprint prevents an endless sequence of duplicate pages.
        if previous_fingerprint and fingerprint == previous_fingerprint:
            return [], None, False
        next_page = self._next_catalog_index(source, catalog_url, page)
        return items, f"{next_page}:{fingerprint}", True

    def _extract_items(self, source: str, final_url: str) -> list[MediaItem]:
        headings: list[tuple[int, str, str]] = []
        for heading in _HEADING_RE.finditer(source):
            label = _clean(heading.group(1))
            key = _section_key(label)
            if key:
                headings.append((heading.start(), key, label))

        out: list[MediaItem] = []
        seen: set[str] = set()
        section_ranks: dict[str, int] = {}
        for match in _LINK_RE.finditer(source):
            item_id = match.group("id")
            if item_id in seen:
                continue
            seen.add(item_id)
            body = match.group("body")
            img_match = _IMG_RE.search(body)
            poster = urljoin(final_url, img_match.group(1)) if img_match else None

            title_match = _TITLE_ATTR_RE.search(body)
            title = _clean(title_match.group(1) if title_match else body)
            if not title:
                title = f"Drabam {item_id}"

            year_match = _YEAR_RE.search(title)
            year = int(year_match.group(1)) if year_match else None
            clean_title = _YEAR_RE.sub("", title).strip(" -–—()") or title

            section_key = None
            section_label = None
            for position, key, label in headings:
                if position > match.start():
                    break
                section_key = key
                section_label = label

            extra = {}
            if section_key:
                rank = section_ranks.get(section_key, 0)
                section_ranks[section_key] = rank + 1
                extra = {
                    "home_section": section_key,
                    "home_section_label": section_label,
                    "home_rank": rank,
                }

            out.append(
                MediaItem(
                    provider_id=self.id,
                    provider_item_id=item_id,
                    title=clean_title,
                    year=year,
                    poster=poster,
                    page_url=urljoin(final_url, match.group("href")),
                    extra=extra,
                )
            )
        return out

    async def browse(self, *, category: str | None = None) -> list[MediaItem]:
        source, final_url, status, _ = await self._get_text(self._home_url())
        if status >= 400:
            raise ProviderError(f"Drabam HTTP {status}")

        home_items = self._extract_items(source, final_url)
        wanted = str(category or "").strip().casefold()

        if wanted in {"latest", "featured", "animation", "docs_shows"}:
            return [
                item
                for item in home_items
                if str(item.extra.get("home_section") or "") == wanted
            ]

        if wanted in {"all", "catalog", "catalogue"}:
            catalog_url = self._catalog_url(source, final_url)
            if catalog_url:
                catalog_source, catalog_final_url, catalog_status, _ = await self._get_text(catalog_url)
                if catalog_status < 400:
                    return self._extract_items(catalog_source, catalog_final_url)

        return home_items

    async def browse_page(
        self,
        *,
        category: str | None = None,
        cursor: str | None = None,
        query: str | None = None,
        limit: int = 24,
    ) -> CatalogPage:
        wanted = str(category or "all").strip().casefold()
        needle = str(query or "").strip().casefold()

        if wanted not in {"all", "catalog", "catalogue"}:
            items = await self.browse(category=wanted)
            if needle:
                items = [item for item in items if needle in item.title.casefold()]
            return CatalogPage(items=items, search_mode="section")

        home_source, home_final_url, status, _ = await self._get_text(self._home_url())
        if status >= 400:
            raise ProviderError(f"Provider HTTP {status}")
        catalog_url = self._catalog_url(home_source, home_final_url)
        if not catalog_url:
            items = self._extract_items(home_source, home_final_url)
            if needle:
                items = [item for item in items if needle in item.title.casefold()]
            return CatalogPage(items=items, search_mode="local")

        page, previous_fingerprint = self._decode_cursor(cursor)
        if not needle:
            items, next_cursor, has_more = await self._catalog_page(
                catalog_url, page, previous_fingerprint
            )
            return CatalogPage(
                items=items,
                next_cursor=next_cursor,
                has_more=has_more,
                page=page,
                search_mode="catalog",
            )

        # No stable public search endpoint is assumed. Search walks the remote
        # catalog in bounded chunks and returns a continuation cursor when more
        # pages remain. Already fetched provider pages are therefore searchable,
        # while the card can keep requesting the rest until the search is global.
        matches: list[MediaItem] = []
        has_more = True
        next_cursor: str | None = cursor
        scanned = 0
        max_scan = max(1, min(int(self.config.get("search_pages_per_request") or 25), 100))
        while has_more and scanned < max_scan and len(matches) < max(1, limit):
            batch, next_cursor, has_more = await self._catalog_page(
                catalog_url, page, previous_fingerprint
            )
            matches.extend(item for item in batch if needle in item.title.casefold())
            scanned += 1
            if not has_more or not next_cursor:
                break
            page, previous_fingerprint = self._decode_cursor(next_cursor)

        return CatalogPage(
            items=matches,
            next_cursor=next_cursor if has_more else None,
            has_more=has_more,
            page=page,
            search_mode="provider_scan",
        )

    async def details(self, provider_item_id: str) -> MediaItem:
        page_url = self._detail_url(provider_item_id)
        source, final_url, status, _ = await self._get_text(page_url)
        if status >= 400:
            raise ProviderError(f"Drabam fiche HTTP {status}")

        h1 = _H1_RE.search(source)
        title = _clean(h1.group(1)) if h1 else f"Drabam {provider_item_id}"
        year_match = _YEAR_RE.search(title)
        year = int(year_match.group(1)) if year_match else None
        title = _YEAR_RE.sub("", title).strip(" -–—()") or title

        desc = _META_DESC_RE.search(source)
        image = _OG_IMAGE_RE.search(source)
        if not image:
            image = _IMG_RE.search(source)
        iframe = _IFRAME_RE.search(source)

        return MediaItem(
            provider_id=self.id,
            provider_item_id=str(provider_item_id),
            title=title,
            year=year,
            poster=urljoin(final_url, image.group(1)) if image else None,
            overview=_clean(desc.group(1)) if desc else None,
            page_url=final_url,
            extra={
                "player_url": urljoin(final_url, iframe.group(1)) if iframe else None,
            },
        )

    async def _validate_manifest(self, url: str, referer: str | None) -> bool:
        try:
            body, _, status, content_type = await self._get_text(url, referer=referer)
        except Exception:
            return False
        return status < 400 and (
            body.lstrip().startswith("#EXTM3U")
            or "mpegurl" in content_type.casefold()
        )

    async def resolve(self, provider_item_id: str) -> ResolvedStream:
        item = await self.details(provider_item_id)
        player_url = str(item.extra.get("player_url") or "")
        if not player_url:
            raise ProviderError("Player iframe introuvable")

        source, final_url, status, _ = await self._get_text(
            player_url,
            referer=item.page_url,
        )
        if status >= 400:
            raise ProviderError(f"Player HTTP {status}")

        normalized = html_lib.unescape(source).replace("\\/", "/")
        candidates: list[str] = []

        for match in _M3U8_ABS_RE.finditer(normalized):
            candidates.append(match.group(0))
        for match in _M3U8_REL_RE.finditer(normalized):
            candidates.append(urljoin(final_url, match.group(1)))

        unique: list[str] = []
        for candidate in candidates:
            candidate = candidate.replace("https:///", "https://").replace("http:///", "http://")
            if candidate not in unique:
                unique.append(candidate)

        for candidate in unique:
            if await self._validate_manifest(candidate, final_url):
                return ResolvedStream(
                    provider_id=self.id,
                    provider_item_id=str(provider_item_id),
                    url=candidate,
                    referer=final_url,
                )

        raise ProviderError(
            "Manifest HLS non trouvé dans le HTML du player. "
            "Le provider nécessite peut-être un resolver réseau dynamique."
        )
