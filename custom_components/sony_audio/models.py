"""Data models and protocol-independent helpers for Sony Audio."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .const import MAIN_ZONE_TITLES


def is_main_zone(title: str, uri: str, index: int) -> bool:
    """Return whether a reported output is the receiver's main zone."""
    normalized = title.strip().casefold()
    return (
        normalized in MAIN_ZONE_TITLES
        or "zone=1" in uri.casefold()
        or (index == 0 and "zone" not in normalized)
    )


def sony_to_ha_volume(value: int, minimum: int, maximum: int) -> float:
    """Normalize a Sony volume value to Home Assistant's 0..1 range."""
    if maximum <= minimum:
        return 0.0
    return max(0.0, min(1.0, (value - minimum) / (maximum - minimum)))


def ha_to_sony_volume(
    level: float, minimum: int, maximum: int, step: int | None = None
) -> int:
    """Convert a Home Assistant 0..1 level to a valid Sony volume value."""
    level = max(0.0, min(1.0, level))
    raw = minimum + level * (maximum - minimum)
    effective_step = step if step and step > 0 else 1
    stepped = minimum + round((raw - minimum) / effective_step) * effective_step
    return max(minimum, min(maximum, stepped))


@dataclass(frozen=True, slots=True)
class SonySource:
    """Source available to a Sony output zone."""

    title: str
    uri: str
    native: Any = field(repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class SonyZoneState:
    """Latest state for one Sony output zone."""

    title: str
    uri: str
    active: bool
    is_main: bool
    native: Any = field(repr=False, compare=False)
    volume_native: Any | None = field(default=None, repr=False, compare=False)
    volume: int | None = None
    volume_min: int | None = None
    volume_max: int | None = None
    volume_step: int | None = None
    muted: bool | None = None
    source_uri: str | None = None
    sources: tuple[SonySource, ...] = ()


@dataclass(frozen=True, slots=True)
class SonyAudioData:
    """Latest receiver state shared by all entities."""

    power: bool
    zones: dict[str, SonyZoneState]
    sound_mode: str | None = None
    sound_modes: dict[str, str] = field(default_factory=dict)
