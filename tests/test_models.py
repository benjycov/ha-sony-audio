"""Tests for Sony Audio's protocol-independent helpers."""

from custom_components.sony_audio.models import (
    ha_to_sony_volume,
    is_main_zone,
    sony_to_ha_volume,
)


def test_negative_db_volume_range() -> None:
    """Sony negative dB ranges map across the full HA range."""
    assert sony_to_ha_volume(-80, -80, 10) == 0.0
    assert sony_to_ha_volume(10, -80, 10) == 1.0
    assert sony_to_ha_volume(-35, -80, 10) == 0.5
    assert ha_to_sony_volume(0.5, -80, 10, 1) == -35


def test_volume_clamps_and_steps() -> None:
    """Volume conversion clamps and honours receiver step."""
    assert ha_to_sony_volume(-1, -80, 10) == -80
    assert ha_to_sony_volume(2, -80, 10) == 10
    assert ha_to_sony_volume(0.51, -80, 10, 2) == -34


def test_main_zone_detection() -> None:
    """Common Sony Main Zone representations are detected."""
    assert is_main_zone("Main Zone", "extOutput:zone?zone=1", 0)
    assert not is_main_zone("Zone 2", "extOutput:zone?zone=2", 1)
