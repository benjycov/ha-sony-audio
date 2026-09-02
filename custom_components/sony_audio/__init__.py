"""Sony Audio integration."""

from __future__ import annotations

from songpal import SongpalException

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_ENDPOINT
from .coordinator import SonyAudioCoordinator

PLATFORMS = (Platform.MEDIA_PLAYER,)

type SonyAudioConfigEntry = ConfigEntry[SonyAudioCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: SonyAudioConfigEntry
) -> bool:
    """Set up Sony Audio from a config entry."""
    coordinator = SonyAudioCoordinator(hass, entry.data[CONF_ENDPOINT])
    try:
        await coordinator.async_initialize()
        await coordinator.async_config_entry_first_refresh()
    except (SongpalException, TimeoutError) as ex:
        raise ConfigEntryNotReady from ex

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: SonyAudioConfigEntry
) -> bool:
    """Unload a Sony Audio config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
