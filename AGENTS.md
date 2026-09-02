# Development guidance

## Scope

This repository contains a Home Assistant custom integration for Sony Audio Control
API receivers. The first hardware target is the STR-DN1080 with Main Zone and Zone 2.

## Architecture

- Keep the integration domain as `sony_audio`; do not collide with HA Core's
  `songpal` domain.
- Use `python-songpal` for the protocol. Do not add Node-RED or JavaScript runtime
  dependencies.
- Model one physical receiver as one HA device and each Sony output zone as a
  separate `media_player` entity.
- All entities share one `SonyAudioCoordinator` and one `songpal.Device` instance.
- Route all zone operations using Sony output URIs, never display names alone.
- Main Zone may use receiver-wide power and sound-field APIs. Secondary zones use
  `setActiveTerminal` through `Zone.activate()`.
- Preserve Sony volume minimum, maximum and step. HA levels are normalized over the
  complete `[minVolume, maxVolume]` range; never divide a dB value by `maxVolume`.

## Safety

- Live hardware work begins read-only.
- Do not remove or rewrite existing Node-RED flows until explicitly requested.
- Do not issue power, input or high-volume commands during diagnostics.
- After adding write support, test mute and small volume changes before source or
  power changes.

## Quality

- Target current Home Assistant APIs and Python 3.13+.
- Keep protocol quirks in the coordinator, not in entities.
- Add fixtures/tests for every observed receiver payload before fixing a quirk.
- Run Ruff and Home Assistant validation before merging.
