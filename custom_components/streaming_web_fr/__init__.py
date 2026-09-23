from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CARD_RESOURCE_PATH, CONF_PLAYERS, CONF_PROVIDERS, DOMAIN
from .lovelace_resource import async_register_lovelace_resource, async_remove_lovelace_resource
from .playback import async_launch_vlc
from .providers import ProviderManager

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    hass.data.setdefault(DOMAIN, {})
    return True


def _settings(entry) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    providers = entry.options.get(CONF_PROVIDERS, entry.data.get(CONF_PROVIDERS, []))
    players = entry.options.get(CONF_PLAYERS, entry.data.get(CONF_PLAYERS, []))
    return list(providers or []), list(players or [])


async def async_setup_entry(hass, entry):
    hass.data.setdefault(DOMAIN, {})
    providers, players = _settings(entry)
    session = async_get_clientsession(hass)
    hass.data[DOMAIN][entry.entry_id] = {
        "manager": ProviderManager(session, providers),
        "players": players,
        "entry": entry,
    }

    await _register_frontend(hass)
    await async_register_lovelace_resource(hass)
    _register_ws(hass)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True


async def async_remove_entry(hass, entry):
    await async_remove_lovelace_resource(hass)


async def _register_frontend(hass):
    if hass.data[DOMAIN].get("_static_registered"):
        return
    path = Path(__file__).parent / "www" / "streaming-web-fr-card.js"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_RESOURCE_PATH, str(path), False)]
    )
    hass.data[DOMAIN]["_static_registered"] = True


def _entry_data(hass, entry_id=None):
    entries = {
        key: value
        for key, value in hass.data.get(DOMAIN, {}).items()
        if not str(key).startswith("_") and isinstance(value, dict)
    }
    return entries.get(entry_id) if entry_id else next(iter(entries.values()), None)


def _public_players(players):
    result = []
    for player in players or []:
        if not isinstance(player, dict):
            continue
        if not player.get("id") or not player.get("remote") or not player.get("adb_player"):
            continue
        result.append(
            {
                "id": str(player["id"]),
                "name": str(player.get("name") or player["id"]),
                "type": str(player.get("type") or "android_tv"),
            }
        )
    return result


def _player(players, player_id):
    for player in players or []:
        if isinstance(player, dict) and str(player.get("id")) == str(player_id):
            return player
    raise ValueError(f"Destination inconnue : {player_id}")


def _register_ws(hass):
    if hass.data[DOMAIN].get("_ws_registered"):
        return

    @websocket_api.websocket_command(
        {
            vol.Required("type"): f"{DOMAIN}/catalog",
            vol.Optional("entry_id"): str,
            vol.Optional("provider_id"): str,
            vol.Optional("query"): str,
        }
    )
    @websocket_api.async_response
    async def catalog(hass, connection, msg):
        data = _entry_data(hass, msg.get("entry_id"))
        if not data:
            connection.send_error(msg["id"], "not_loaded", "Streaming Web FR not loaded")
            return
        try:
            items = await data["manager"].catalog(
                provider_id=msg.get("provider_id") or None,
                query=msg.get("query") or None,
            )
            connection.send_result(
                msg["id"],
                {
                    "providers": data["manager"].public_providers(),
                    "players": _public_players(data["players"]),
                    "items": [item.as_dict() for item in items],
                },
            )
        except Exception as err:
            connection.send_error(msg["id"], "catalog_error", str(err))

    @websocket_api.websocket_command(
        {
            vol.Required("type"): f"{DOMAIN}/details",
            vol.Optional("entry_id"): str,
            vol.Required("provider_id"): str,
            vol.Required("provider_item_id"): str,
        }
    )
    @websocket_api.async_response
    async def details(hass, connection, msg):
        data = _entry_data(hass, msg.get("entry_id"))
        if not data:
            connection.send_error(msg["id"], "not_loaded", "Streaming Web FR not loaded")
            return
        try:
            item = await data["manager"].details(
                msg["provider_id"],
                msg["provider_item_id"],
            )
            connection.send_result(msg["id"], item.as_dict())
        except Exception as err:
            connection.send_error(msg["id"], "details_error", str(err))

    @websocket_api.websocket_command(
        {
            vol.Required("type"): f"{DOMAIN}/play",
            vol.Optional("entry_id"): str,
            vol.Required("provider_id"): str,
            vol.Required("provider_item_id"): str,
            vol.Required("player_id"): str,
        }
    )
    @websocket_api.async_response
    async def play(hass, connection, msg):
        data = _entry_data(hass, msg.get("entry_id"))
        if not data:
            connection.send_error(msg["id"], "not_loaded", "Streaming Web FR not loaded")
            return
        try:
            stream = await data["manager"].resolve(
                msg["provider_id"],
                msg["provider_item_id"],
            )
            player = _player(data["players"], msg["player_id"])
            await async_launch_vlc(hass, player, stream.url)
            connection.send_result(
                msg["id"],
                {"ok": True, "stream_type": stream.stream_type},
            )
        except Exception as err:
            _LOGGER.warning("Streaming Web FR playback failed: %s", err)
            connection.send_error(msg["id"], "playback_error", str(err))

    @websocket_api.websocket_command(
        {
            vol.Required("type"): f"{DOMAIN}/resolve",
            vol.Optional("entry_id"): str,
            vol.Required("provider_id"): str,
            vol.Required("provider_item_id"): str,
        }
    )
    @websocket_api.async_response
    async def resolve(hass, connection, msg):
        data = _entry_data(hass, msg.get("entry_id"))
        if not data:
            connection.send_error(msg["id"], "not_loaded", "Streaming Web FR not loaded")
            return
        try:
            stream = await data["manager"].resolve(
                msg["provider_id"],
                msg["provider_item_id"],
            )
            connection.send_result(msg["id"], stream.as_dict())
        except Exception as err:
            connection.send_error(msg["id"], "resolve_error", str(err))

    websocket_api.async_register_command(hass, catalog)
    websocket_api.async_register_command(hass, details)
    websocket_api.async_register_command(hass, play)
    websocket_api.async_register_command(hass, resolve)

    hass.data[DOMAIN]["_ws_registered"] = True
