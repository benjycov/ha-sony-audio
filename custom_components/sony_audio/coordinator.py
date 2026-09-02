"""Shared receiver coordinator for Sony Audio."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from songpal import Device, SongpalException

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .models import SonyAudioData, SonySource, SonyZoneState, is_main_zone

_LOGGER = logging.getLogger(__name__)


class SonyAudioCoordinator(DataUpdateCoordinator[SonyAudioData]):
    """Coordinate one Sony receiver and all its output zones."""

    def __init__(self, hass: HomeAssistant, endpoint: str) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}:{endpoint}",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.endpoint = endpoint
        self.device = Device(endpoint)
        self.system_info: Any | None = None
        self.interface_info: Any | None = None

    async def async_initialize(self) -> None:
        """Initialize protocol methods and stable receiver information."""
        await self.device.get_supported_methods()
        self.system_info, self.interface_info = await asyncio.gather(
            self.device.get_system_info(),
            self.device.get_interface_information(),
        )

    @property
    def hardware_id(self) -> str:
        """Return the best stable hardware identifier."""
        assert self.system_info is not None
        return (
            self.system_info.macAddr
            or self.system_info.wirelessMacAddr
            or self.endpoint
        )

    async def _async_update_data(self) -> SonyAudioData:
        """Fetch receiver and zone state."""
        try:
            power, zones, volumes, inputs, sound_settings = await asyncio.gather(
                self.device.get_power(),
                self.device.get_zones(),
                self.device.get_volume_information(),
                self.device.get_inputs(),
                self.device.get_sound_settings(),
            )

            playback_results = await asyncio.gather(
                *(self._async_current_source(zone.uri) for zone in zones)
            )
        except (SongpalException, TimeoutError) as ex:
            raise UpdateFailed(f"Unable to update Sony receiver: {ex}") from ex

        volumes_by_output = {volume.output: volume for volume in volumes}
        zone_states: dict[str, SonyZoneState] = {}

        for index, (zone, current_source) in enumerate(
            zip(zones, playback_results, strict=True)
        ):
            volume = volumes_by_output.get(zone.uri)
            allowed_sources = tuple(
                SonySource(source.title, source.uri, source)
                for source in inputs
                if source.outputs and zone.uri in source.outputs
            )
            zone_states[zone.uri] = SonyZoneState(
                title=zone.title,
                uri=zone.uri,
                active=bool(zone.active),
                is_main=is_main_zone(zone.title, zone.uri, index),
                native=zone,
                volume_native=volume,
                volume=volume.volume if volume else None,
                volume_min=volume.minVolume if volume else None,
                volume_max=volume.maxVolume if volume else None,
                volume_step=volume.step if volume else None,
                muted=volume.is_muted if volume else None,
                source_uri=current_source,
                sources=allowed_sources,
            )

        sound_mode: str | None = None
        sound_modes: dict[str, str] = {}
        for setting in sound_settings:
            if setting.target != "soundField":
                continue
            sound_mode = setting.currentValue
            sound_modes = {
                option.title: option.value
                for option in setting.candidate
                if option.isAvailable
            }
            break

        return SonyAudioData(
            power=bool(power.status),
            zones=zone_states,
            sound_mode=sound_mode,
            sound_modes=sound_modes,
        )

    async def _async_current_source(self, output: str) -> str | None:
        """Return the current source URI for an output when available."""
        try:
            functions = await self.device.get_available_playback_functions(output)
        except SongpalException as ex:
            _LOGGER.debug("Unable to read source for output %s: %s", output, ex)
            return None
        return functions[0].uri if functions else None

    def zone(self, uri: str) -> SonyZoneState:
        """Return the current state for a zone."""
        return self.data.zones[uri]

    async def async_set_zone_power(self, uri: str, active: bool) -> None:
        """Set power for a receiver output."""
        zone = self.zone(uri)
        if zone.is_main:
            await self.device.set_power(active)
        else:
            await zone.native.activate(active)
        await self.async_request_refresh()

    async def async_set_volume(self, uri: str, volume: int) -> None:
        """Set native Sony volume for an output."""
        control = self.zone(uri).volume_native
        if control is None:
            raise SongpalException(f"No volume control for output {uri}")
        await control.set_volume(volume)
        await self.async_request_refresh()

    async def async_set_mute(self, uri: str, muted: bool) -> None:
        """Set mute for an output."""
        control = self.zone(uri).volume_native
        if control is None:
            raise SongpalException(f"No mute control for output {uri}")
        await control.set_mute(muted)
        await self.async_request_refresh()

    async def async_select_source(self, uri: str, title: str) -> None:
        """Select an input for an output."""
        zone = self.zone(uri)
        source = next((item for item in zone.sources if item.title == title), None)
        if source is None:
            raise SongpalException(f"Source {title!r} is not valid for {zone.title}")
        await source.native.activate(zone.native)
        await self.async_request_refresh()

    async def async_select_sound_mode(self, title: str) -> None:
        """Select the receiver-wide sound field."""
        value = self.data.sound_modes.get(title)
        if value is None:
            raise SongpalException(f"Unknown sound mode {title!r}")
        await self.device.set_sound_settings("soundField", value)
        await self.async_request_refresh()
