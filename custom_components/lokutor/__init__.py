"""The Lokutor integration: text-to-speech and speech-to-text."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LokutorAuthError, LokutorClient, LokutorError

PLATFORMS: list[Platform] = [Platform.STT, Platform.TTS]

type LokutorConfigEntry = ConfigEntry[LokutorClient]


async def async_setup_entry(hass: HomeAssistant, entry: LokutorConfigEntry) -> bool:
    """Set up Lokutor from a config entry."""
    client = LokutorClient(async_get_clientsession(hass), entry.data[CONF_API_KEY])
    try:
        await client.async_validate()
    except LokutorAuthError as err:
        raise ConfigEntryAuthFailed("The Lokutor API key was rejected") from err
    except LokutorError as err:
        raise ConfigEntryNotReady("Cannot reach the Lokutor API") from err

    entry.runtime_data = client
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: LokutorConfigEntry) -> None:
    """Reload when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: LokutorConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
