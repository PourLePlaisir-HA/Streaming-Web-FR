from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CARD_RESOURCE_PATH, CONF_PLAYERS, CONF_PROVIDERS, DOMAIN, VERSION
from .lovelace_resource import async_register_lovelace_resource, async_remove_lovelace_resource
from .playback import async_launch_vlc
from .providers import ProviderManager
from .settings import async_load_yaml_config, config_path, fallback_from_entry

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    hass.data.setdefault(DOMAIN, {})
    return True


async def _async_effective_config(hass, entry):
    yaml_config = await async_load_yaml_config(hass)
    if yaml_config is not None:
        return yaml_config, "yaml"
    return fallback_from_entry(entry), "config_entry"


async def _async_apply_runtime_config(hass, runtime):
    config, source = await _async_effective_config(hass, runtime["entry"])
    session = async_get_clientsession(hass)
    runtime["manager"] = ProviderManager(session, config.get(CONF_PROVIDERS) or [])
    runtime["players"] = list(config.get(CONF_PLAYERS) or [])
    runtime["config_source"] = source
    runtime["config_path"] = config_path(hass)
    runtime["config_issues"] = list(config.get("_issues") or [])
    _LOGGER.info(
        "Streaming Web FR config: source=%s providers=%s players=%s ids=%s issues=%s",
        source,
        len(config.get(CONF_PROVIDERS) or []),
        len(config.get(CONF_PLAYERS) or []),
        [str(player.get("id")) for player in (config.get(CONF_PLAYERS) or [])],
        runtime["config_issues"],
    )
    return source


async def async_setup_entry(hass, entry):
    hass.data.setdefault(DOMAIN, {})
    runtime = {
        "manager": None,
        "players": [],
        "entry": entry,
        "config_source": None,
        "config_path": config_path(hass),
        "config_issues": [],
    }
    hass.data[DOMAIN][entry.entry_id] = runtime
    await _async_apply_runtime_config(hass, runtime)

    await _register_frontend(hass)
    await async_register_lovelace_resource(hass)
    _register_ws(hass)
    _register_services(hass)
    return True


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


def _register_services(hass):
    if hass.data[DOMAIN].get("_services_registered"):
        return

    async def _reload_config(call):
        runtimes = [
            value
            for key, value in hass.data.get(DOMAIN, {}).items()
            if not str(key).startswith("_") and isinstance(value, dict)
        ]
        for runtime in runtimes:
            try:
                source = await _async_apply_runtime_config(hass, runtime)
                _LOGGER.info(
                    "Streaming Web FR configuration reloaded from %s (%s)",
                    source,
                    runtime.get("config_path"),
                )
            except Exception:
                _LOGGER.exception("Unable to reload Streaming Web FR configuration")
                raise

    hass.services.async_register(DOMAIN, "reload_config", _reload_config)
    hass.data[DOMAIN]["_services_registered"] = True


def _register_ws(hass):
    if hass.data[DOMAIN].get("_ws_registered"):
        return

    @websocket_api.websocket_command(
        {
            vol.Required("type"): f"{DOMAIN}/runtime",
            vol.Optional("entry_id"): str,
        }
    )
    @websocket_api.async_response
    async def runtime_info(hass, connection, msg):
        data = _entry_data(hass, msg.get("entry_id"))
        if not data:
            connection.send_error(msg["id"], "not_loaded", "Streaming Web FR not loaded")
            return
        connection.send_result(
            msg["id"],
            {
                "providers": data["manager"].public_providers(),
                "players": _public_players(data["players"]),
                "config_source": data.get("config_source"),
                "config_path": data.get("config_path"),
                "config_issues": list(data.get("config_issues") or []),
                "version": VERSION,
            },
        )

    @websocket_api.websocket_command(
        {
            vol.Required("type"): f"{DOMAIN}/catalog",
            vol.Optional("entry_id"): str,
            vol.Optional("provider_id"): str,
            vol.Optional("query"): str,
            vol.Optional("category"): str,
            vol.Optional("cursor"): str,
            vol.Optional("limit", default=24): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
        }
    )
    @websocket_api.async_response
    async def catalog(hass, connection, msg):
        data = _entry_data(hass, msg.get("entry_id"))
        if not data:
            connection.send_error(msg["id"], "not_loaded", "Streaming Web FR not loaded")
            return
        try:
            if not msg.get("category") and not msg.get("query") and not msg.get("cursor"):
                items = await data["manager"].catalog(
                    provider_id=msg.get("provider_id") or None,
                )
                page = None
            else:
                page = await data["manager"].catalog_page(
                    provider_id=msg.get("provider_id") or None,
                    query=msg.get("query") or None,
                    category=msg.get("category") or None,
                    cursor=msg.get("cursor") or None,
                    limit=msg.get("limit") or 24,
                )
                items = page.items
            connection.send_result(
                msg["id"],
                {
                    "providers": data["manager"].public_providers(),
                    "players": _public_players(data["players"]),
                    "items": [item.as_dict() for item in items],
                    "config_source": data.get("config_source"),
                    "config_path": data.get("config_path"),
                    "config_issues": list(data.get("config_issues") or []),
                    "version": VERSION,
                    "has_more": page.has_more if page else False,
                    "next_cursor": page.next_cursor if page else None,
                    "page": page.page if page else 0,
                    "search_mode": page.search_mode if page else "home",
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
            vol.Optional("page_url"): str,
            vol.Optional("page_referer"): str,
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
                page_url=msg.get("page_url") or None,
                page_referer=msg.get("page_referer") or None,
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
            vol.Optional("page_url"): str,
            vol.Optional("page_referer"): str,
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
                page_url=msg.get("page_url") or None,
                page_referer=msg.get("page_referer") or None,
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
            vol.Optional("page_url"): str,
            vol.Optional("page_referer"): str,
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
                page_url=msg.get("page_url") or None,
                page_referer=msg.get("page_referer") or None,
            )
            connection.send_result(msg["id"], stream.as_dict())
        except Exception as err:
            connection.send_error(msg["id"], "resolve_error", str(err))

    websocket_api.async_register_command(hass, runtime_info)
    websocket_api.async_register_command(hass, catalog)
    websocket_api.async_register_command(hass, details)
    websocket_api.async_register_command(hass, play)
    websocket_api.async_register_command(hass, resolve)

    hass.data[DOMAIN]["_ws_registered"] = True
