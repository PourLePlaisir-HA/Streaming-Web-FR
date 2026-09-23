from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import OptionsFlowWithReload
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    AUTH_MODES,
    AUTH_NONE,
    CONF_PLAYERS,
    CONF_PROVIDERS,
    DEFAULT_PROVIDER_TYPE,
    DOMAIN,
    SUPPORTED_PROVIDER_TYPES,
)


def _slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", str(value or "").casefold()).strip("_")
    return text or "provider"


def _auth_from_input(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": data.get("auth_mode") or AUTH_NONE,
        "username": data.get("username") or "",
        "password": data.get("password") or "",
        "api_key": data.get("api_key") or "",
        "api_key_header": data.get("api_key_header") or "X-Api-Key",
        "bearer": data.get("bearer") or "",
        "cookie": data.get("cookie") or "",
        "custom_headers": data.get("custom_headers") or "",
        "login_url": data.get("login_url") or "",
        "username_field": data.get("username_field") or "username",
        "password_field": data.get("password_field") or "password",
        "login_extra_fields": data.get("login_extra_fields") or "",
    }


def _provider_from_input(data: dict[str, Any], existing_ids: set[str]) -> dict[str, Any]:
    provider_id = _slug(data.get("provider_id") or data.get("provider_name") or "provider")
    base_id = provider_id
    index = 2
    while provider_id in existing_ids:
        provider_id = f"{base_id}_{index}"
        index += 1
    return {
        "id": provider_id,
        "name": str(data.get("provider_name") or provider_id).strip(),
        "type": str(data.get("provider_type") or DEFAULT_PROVIDER_TYPE).strip(),
        "base_url": str(data.get("base_url") or "").strip().rstrip("/"),
        "enabled": bool(data.get("enabled", True)),
        "priority": int(data.get("priority") or 100),
        "auth": _auth_from_input(data),
    }


def _provider_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    auth = defaults.get("auth") or {}
    return vol.Schema(
        {
            vol.Required("provider_name", default=defaults.get("name", "Provider")):
                selector.TextSelector(),
            vol.Optional("provider_id", default=defaults.get("id", "")):
                selector.TextSelector(),
            vol.Required(
                "provider_type",
                default=defaults.get("type", DEFAULT_PROVIDER_TYPE),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=list(SUPPORTED_PROVIDER_TYPES),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required("base_url", default=defaults.get("base_url", "")):
                selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.URL)),
            vol.Required("enabled", default=bool(defaults.get("enabled", True))):
                selector.BooleanSelector(),
            vol.Required("priority", default=int(defaults.get("priority", 100))):
                selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=999, step=1, mode=selector.NumberSelectorMode.BOX)
                ),
            vol.Required("auth_mode", default=auth.get("mode", AUTH_NONE)):
                selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=list(AUTH_MODES),
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            vol.Optional("username", default=auth.get("username", "")):
                selector.TextSelector(),
            vol.Optional("password", default=auth.get("password", "")):
                selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
            vol.Optional("api_key", default=auth.get("api_key", "")):
                selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
            vol.Optional("api_key_header", default=auth.get("api_key_header", "X-Api-Key")):
                selector.TextSelector(),
            vol.Optional("bearer", default=auth.get("bearer", "")):
                selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
            vol.Optional("cookie", default=auth.get("cookie", "")):
                selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
            vol.Optional("custom_headers", default=auth.get("custom_headers", "")):
                selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
            vol.Optional("login_url", default=auth.get("login_url", "")):
                selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.URL)),
            vol.Optional("username_field", default=auth.get("username_field", "username")):
                selector.TextSelector(),
            vol.Optional("password_field", default=auth.get("password_field", "password")):
                selector.TextSelector(),
            vol.Optional("login_extra_fields", default=auth.get("login_extra_fields", "")):
                selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
        }
    )


def _player_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("player_name", default="AndroidTV"):
                selector.TextSelector(),
            vol.Optional("player_id", default=""):
                selector.TextSelector(),
            vol.Optional("media_player", default=""):
                selector.EntitySelector(selector.EntitySelectorConfig(domain="media_player")),
            vol.Required("remote"):
                selector.EntitySelector(selector.EntitySelectorConfig(domain="remote")),
            vol.Required("adb_player"):
                selector.EntitySelector(selector.EntitySelectorConfig(domain="media_player")),
        }
    )


class StreamingWebFrConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            provider = _provider_from_input(user_input, set())
            return self.async_create_entry(
                title="Streaming Web FR",
                data={
                    CONF_PROVIDERS: [provider],
                    CONF_PLAYERS: [],
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_provider_schema(
                {
                    "name": "Drabam",
                    "type": "drabam",
                    "priority": 100,
                    "enabled": True,
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return StreamingWebFrOptionsFlow()


class StreamingWebFrOptionsFlow(OptionsFlowWithReload):

    def _providers(self) -> list[dict[str, Any]]:
        return [
            dict(item)
            for item in self.config_entry.options.get(
                CONF_PROVIDERS,
                self.config_entry.data.get(CONF_PROVIDERS, []),
            )
            if isinstance(item, dict)
        ]

    def _players(self) -> list[dict[str, Any]]:
        return [
            dict(item)
            for item in self.config_entry.options.get(
                CONF_PLAYERS,
                self.config_entry.data.get(CONF_PLAYERS, []),
            )
            if isinstance(item, dict)
        ]

    def _save(self, *, providers=None, players=None):
        options = dict(self.config_entry.options)
        options[CONF_PROVIDERS] = providers if providers is not None else self._providers()
        options[CONF_PLAYERS] = players if players is not None else self._players()
        return self.async_create_entry(title="", data=options)

    async def async_step_init(self, user_input=None):
        menu = ["add_provider", "add_player"]
        if self._providers():
            menu.append("remove_provider")
        if self._players():
            menu.append("remove_player")
        return self.async_show_menu(step_id="init", menu_options=menu)

    async def async_step_add_provider(self, user_input=None):
        if user_input is not None:
            providers = self._providers()
            ids = {str(item.get("id") or "") for item in providers}
            providers.append(_provider_from_input(user_input, ids))
            return self._save(providers=providers)
        return self.async_show_form(step_id="add_provider", data_schema=_provider_schema())

    async def async_step_remove_provider(self, user_input=None):
        providers = self._providers()
        choices = {
            str(item.get("id")): str(item.get("name") or item.get("id"))
            for item in providers
            if item.get("id")
        }
        if user_input is not None:
            selected = str(user_input["provider_id"])
            return self._save(
                providers=[item for item in providers if str(item.get("id")) != selected]
            )
        return self.async_show_form(
            step_id="remove_provider",
            data_schema=vol.Schema({vol.Required("provider_id"): vol.In(choices)}),
        )

    async def async_step_add_player(self, user_input=None):
        if user_input is not None:
            players = self._players()
            ids = {str(item.get("id") or "") for item in players}
            player_id = _slug(user_input.get("player_id") or user_input.get("player_name") or "androidtv")
            base = player_id
            idx = 2
            while player_id in ids:
                player_id = f"{base}_{idx}"
                idx += 1
            players.append(
                {
                    "id": player_id,
                    "name": str(user_input.get("player_name") or player_id),
                    "type": "android_tv",
                    "media_player": str(user_input.get("media_player") or ""),
                    "remote": str(user_input.get("remote") or ""),
                    "adb_player": str(user_input.get("adb_player") or ""),
                }
            )
            return self._save(players=players)
        return self.async_show_form(step_id="add_player", data_schema=_player_schema())

    async def async_step_remove_player(self, user_input=None):
        players = self._players()
        choices = {
            str(item.get("id")): str(item.get("name") or item.get("id"))
            for item in players
            if item.get("id")
        }
        if user_input is not None:
            selected = str(user_input["player_id"])
            return self._save(
                players=[item for item in players if str(item.get("id")) != selected]
            )
        return self.async_show_form(
            step_id="remove_player",
            data_schema=vol.Schema({vol.Required("player_id"): vol.In(choices)}),
        )