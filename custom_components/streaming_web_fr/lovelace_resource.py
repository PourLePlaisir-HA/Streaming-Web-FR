from __future__ import annotations

from urllib.parse import urlsplit

from homeassistant.components import frontend
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import CARD_RESOURCE_PATH, DOMAIN

CARD_RESOURCE_TYPE = "module"


def _resource_path(url: str | None) -> str:
    try:
        return urlsplit(str(url or "")).path.rstrip("/")
    except ValueError:
        return ""


def _matches(item: dict) -> bool:
    return _resource_path(item.get("url")) == CARD_RESOURCE_PATH


async def async_register_lovelace_resource(hass: HomeAssistant) -> bool:
    integration = await async_get_integration(hass, DOMAIN)
    target_url = f"{CARD_RESOURCE_PATH}?v={integration.version or '0'}"
    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None:
        return False

    resources = lovelace.resources
    await resources.async_get_info()
    matches = [
        item for item in resources.async_items()
        if isinstance(item, dict) and _matches(item)
    ]

    if isinstance(resources, ResourceStorageCollection):
        if not matches:
            await resources.async_create_item(
                {"res_type": CARD_RESOURCE_TYPE, "url": target_url}
            )
            return True

        primary = matches[0]
        updates = {}
        if str(primary.get("url") or "") != target_url:
            updates["url"] = target_url
        if str(primary.get("type") or "").casefold() != CARD_RESOURCE_TYPE:
            updates["res_type"] = CARD_RESOURCE_TYPE
        if updates:
            await resources.async_update_item(primary["id"], updates)

        for duplicate in matches[1:]:
            if duplicate.get("id"):
                await resources.async_delete_item(duplicate["id"])
        return bool(updates or len(matches) > 1)

    if not matches:
        frontend.add_extra_js_url(hass, target_url)
        return True
    return False


async def async_remove_lovelace_resource(hass: HomeAssistant) -> bool:
    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None:
        return False

    resources = lovelace.resources
    if not isinstance(resources, ResourceStorageCollection):
        return False

    await resources.async_get_info()
    changed = False
    for item in list(resources.async_items()):
        if isinstance(item, dict) and _matches(item) and item.get("id"):
            await resources.async_delete_item(item["id"])
            changed = True
    return changed
