from __future__ import annotations

import asyncio
import shlex
from typing import Any

from homeassistant.core import HomeAssistant

from .const import VLC_ANDROID_ACTIVITY


def _require(player: dict[str, Any], key: str) -> str:
    value = str(player.get(key) or "").strip()
    if not value:
        raise ValueError(f"Destination incomplète : {key} manquant")
    return value


async def _call(
    hass: HomeAssistant,
    domain: str,
    service: str,
    data: dict[str, Any],
) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)


def build_vlc_http_command(url: str) -> str:
    media_url = str(url or "").strip()
    if not media_url.lower().startswith(("http://", "https://")):
        raise ValueError("URL média HTTP/HTTPS invalide")
    return (
        "am start "
        "-a android.intent.action.VIEW "
        f"-d {shlex.quote(media_url)} "
        f"-n {shlex.quote(VLC_ANDROID_ACTIVITY)}"
    )


async def async_launch_vlc(
    hass: HomeAssistant,
    player: dict[str, Any],
    media_url: str,
) -> None:
    remote = _require(player, "remote")
    adb_player = _require(player, "adb_player")
    command = build_vlc_http_command(media_url)

    await _call(hass, "remote", "turn_on", {"entity_id": remote})
    await asyncio.sleep(2)
    await _call(
        hass,
        "androidtv",
        "adb_command",
        {"entity_id": adb_player, "command": command},
    )
