"""Media player entities for Sony Audio output zones."""

from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SonyAudioConfigEntry
from .const import DOMAIN
from .coordinator import SonyAudioCoordinator
from .models import ha_to_sony_volume, sony_to_ha_volume


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SonyAudioConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create one entity for each receiver output zone."""
    coordinator = entry.runtime_data
    async_add_entities(
        SonyAudioZoneEntity(coordinator, zone_uri)
        for zone_uri in coordinator.data.zones
    )


class SonyAudioZoneEntity(
    CoordinatorEntity[SonyAudioCoordinator], MediaPlayerEntity
):
    """Representation of one Sony receiver output zone."""

    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_has_entity_name = True

    def __init__(self, coordinator: SonyAudioCoordinator, zone_uri: str) -> None:
        """Initialize a zone entity."""
        super().__init__(coordinator)
        self._zone_uri = zone_uri
        zone = coordinator.zone(zone_uri)
        self._attr_name = None if zone.is_main else zone.title
        self._attr_unique_id = f"{coordinator.hardware_id}_{zone_uri}"

    @property
    def zone(self):
        """Return the latest zone state."""
        return self.coordinator.zone(self._zone_uri)

    @property
    def device_info(self) -> DeviceInfo:
        """Return receiver device information."""
        system_info = self.coordinator.system_info
        interface_info = self.coordinator.interface_info
        connections = set()
        if system_info.macAddr:
            connections.add((CONNECTION_NETWORK_MAC, system_info.macAddr))
        if system_info.wirelessMacAddr:
            connections.add((CONNECTION_NETWORK_MAC, system_info.wirelessMacAddr))
        return DeviceInfo(
            connections=connections,
            identifiers={(DOMAIN, self.coordinator.hardware_id)},
            manufacturer="Sony Corporation",
            model=interface_info.modelName,
            name=interface_info.productName or interface_info.modelName,
            sw_version=system_info.version,
        )

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Return features supported by this output."""
        features = (
            MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
        )
        if self.zone.volume_native is not None:
            features |= (
                MediaPlayerEntityFeature.VOLUME_SET
                | MediaPlayerEntityFeature.VOLUME_STEP
                | MediaPlayerEntityFeature.VOLUME_MUTE
            )
        if self.zone.sources:
            features |= MediaPlayerEntityFeature.SELECT_SOURCE
        if self.zone.is_main and self.coordinator.data.sound_modes:
            features |= MediaPlayerEntityFeature.SELECT_SOUND_MODE
        return features

    @property
    def state(self) -> MediaPlayerState:
        """Return zone state."""
        active = (
            self.coordinator.data.power if self.zone.is_main else self.zone.active
        )
        return MediaPlayerState.ON if active else MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        """Return normalized output volume."""
        zone = self.zone
        if (
            zone.volume is None
            or zone.volume_min is None
            or zone.volume_max is None
        ):
            return None
        return sony_to_ha_volume(zone.volume, zone.volume_min, zone.volume_max)

    @property
    def is_volume_muted(self) -> bool | None:
        """Return output mute state."""
        return self.zone.muted

    @property
    def source(self) -> str | None:
        """Return active source title for this output."""
        source = next(
            (item for item in self.zone.sources if item.uri == self.zone.source_uri),
            None,
        )
        return source.title if source else None

    @property
    def source_list(self) -> list[str]:
        """Return sources valid for this output."""
        return [source.title for source in self.zone.sources]

    @property
    def sound_mode(self) -> str | None:
        """Return active receiver sound mode title."""
        if not self.zone.is_main:
            return None
        active_value = self.coordinator.data.sound_mode
        return next(
            (
                title
                for title, value in self.coordinator.data.sound_modes.items()
                if value == active_value
            ),
            None,
        )

    @property
    def sound_mode_list(self) -> list[str] | None:
        """Return receiver sound modes for Main Zone."""
        if not self.zone.is_main:
            return None
        return list(self.coordinator.data.sound_modes)

    @property
    def volume_step(self) -> float | None:
        """Return normalized volume step."""
        zone = self.zone
        if (
            zone.volume_step is None
            or zone.volume_min is None
            or zone.volume_max is None
            or zone.volume_max <= zone.volume_min
        ):
            return None
        return zone.volume_step / (zone.volume_max - zone.volume_min)

    async def async_turn_on(self) -> None:
        """Turn on this output."""
        await self.coordinator.async_set_zone_power(self._zone_uri, True)

    async def async_turn_off(self) -> None:
        """Turn off this output."""
        await self.coordinator.async_set_zone_power(self._zone_uri, False)

    async def async_set_volume_level(self, volume: float) -> None:
        """Set normalized output volume."""
        zone = self.zone
        assert zone.volume_min is not None and zone.volume_max is not None
        native_volume = ha_to_sony_volume(
            volume, zone.volume_min, zone.volume_max, zone.volume_step
        )
        await self.coordinator.async_set_volume(self._zone_uri, native_volume)

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute this output."""
        await self.coordinator.async_set_mute(self._zone_uri, mute)

    async def async_select_source(self, source: str) -> None:
        """Select a source for this output."""
        await self.coordinator.async_select_source(self._zone_uri, source)

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        """Select the receiver-wide sound field."""
        await self.coordinator.async_select_sound_mode(sound_mode)
