from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from .const import CONF_PLAYERS, CONF_PROVIDERS

CONFIG_FILENAME = "streaming_web_fr.yaml"

DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    CONF_PROVIDERS: [],
    CONF_PLAYERS: [],
    "_issues": [],
}


def _section_items(raw: Any):
    """Yield (label, mapping) from either YAML list or id-keyed mapping."""
    if isinstance(raw, list):
        for index, item in enumerate(raw):
            yield str(index), item
        return
    if isinstance(raw, dict):
        for key, item in raw.items():
            if isinstance(item, dict):
                item = dict(item)
                item.setdefault("id", str(key))
            yield str(key), item


def _normalize_provider(raw: Any) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(raw, dict):
        return None, "provider must be a mapping"
    provider_id = str(raw.get("id") or "").strip()
    provider_type = str(raw.get("type") or "").strip().casefold()
    base_url = str(raw.get("base_url") or "").strip().rstrip("/")
    missing = [
        key
        for key, value in (
            ("id", provider_id),
            ("type", provider_type),
            ("base_url", base_url),
        )
        if not value
    ]
    if missing:
        return None, f"missing {', '.join(missing)}"
    auth = raw.get("auth") if isinstance(raw.get("auth"), dict) else {}
    return {
        "id": provider_id,
        "name": str(raw.get("name") or provider_id).strip(),
        "type": provider_type,
        "enabled": bool(raw.get("enabled", True)),
        "priority": int(raw.get("priority") or 100),
        "base_url": base_url,
        "auth": dict(auth or {}),
        "request_interval_seconds": max(
            0.5, min(float(raw.get("request_interval_seconds") or 1.25), 10.0)
        ),
        "cache_ttl_seconds": max(
            60, min(int(raw.get("cache_ttl_seconds") or 600), 3600)
        ),
        "circuit_breaker_seconds": max(
            60, min(int(raw.get("circuit_breaker_seconds") or 900), 3600)
        ),
        "search_pages_per_request": max(
            1, min(int(raw.get("search_pages_per_request") or 2), 5)
        ),
    }, None


def _normalize_player(raw: Any) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(raw, dict):
        return None, "player must be a mapping"
    player_id = str(raw.get("id") or "").strip()
    remote = str(raw.get("remote") or "").strip()
    adb_player = str(raw.get("adb_player") or "").strip()
    missing = [
        key
        for key, value in (
            ("id", player_id),
            ("remote", remote),
            ("adb_player", adb_player),
        )
        if not value
    ]
    if missing:
        return None, f"missing {', '.join(missing)}"
    return {
        "id": player_id,
        "name": str(raw.get("name") or player_id).strip(),
        "type": str(raw.get("type") or "android_tv").strip().casefold(),
        "media_player": str(raw.get("media_player") or "").strip(),
        "remote": remote,
        "adb_player": adb_player,
    }, None


def normalize_config(raw: Any) -> dict[str, Any]:
    data = raw if isinstance(raw, dict) else {}
    issues: list[str] = []

    providers = []
    for label, item in _section_items(data.get(CONF_PROVIDERS) or []):
        provider, issue = _normalize_provider(item)
        if provider:
            providers.append(provider)
        elif issue:
            issues.append(f"providers.{label}: {issue}")

    players = []
    for label, item in _section_items(data.get(CONF_PLAYERS) or []):
        player, issue = _normalize_player(item)
        if player:
            players.append(player)
        elif issue:
            issues.append(f"players.{label}: {issue}")

    return {
        "version": int(data.get("version") or 1),
        CONF_PROVIDERS: providers,
        CONF_PLAYERS: players,
        "_issues": issues,
    }


def _load_yaml(path: str) -> dict[str, Any] | None:
    file_path = Path(path)
    if not file_path.exists():
        return None
    with file_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    return normalize_config(raw)


async def async_load_yaml_config(hass) -> dict[str, Any] | None:
    path = hass.config.path(CONFIG_FILENAME)
    return await hass.async_add_executor_job(_load_yaml, path)


def config_path(hass) -> str:
    return hass.config.path(CONFIG_FILENAME)


def fallback_from_entry(entry) -> dict[str, Any]:
    providers = entry.options.get(
        CONF_PROVIDERS,
        entry.data.get(CONF_PROVIDERS, []),
    )
    players = entry.options.get(
        CONF_PLAYERS,
        entry.data.get(CONF_PLAYERS, []),
    )
    return normalize_config(
        {
            "version": 1,
            CONF_PROVIDERS: deepcopy(list(providers or [])),
            CONF_PLAYERS: deepcopy(list(players or [])),
        }
    )
