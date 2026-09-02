# Sony Audio for Home Assistant

Home Assistant custom integration for Sony receivers implementing the Sony Audio
Control API (formerly branded SongPal), with first-class multi-zone support.

The initial target is the Sony STR-DN1080. Each physical receiver is represented
as one Home Assistant device with one `media_player` entity per reported zone.

## Current status

Early development build. It provides:

- UI configuration using the receiver's Scalar API endpoint
- one Home Assistant device per receiver
- separate media players for Main Zone, Zone 2, Zone 3 and HDMI Zone when reported
- zone power, volume, mute and source control
- Main Zone sound-field control
- correct conversion between Sony's dB volume range and Home Assistant's 0–100%
- shared polling so several zone entities do not independently hammer the receiver

Push notifications and migration/upstream work are planned after live STR-DN1080
validation.

## Installation

### HACS

1. In HACS, open the menu and choose **Custom repositories**.
2. Add `https://github.com/benjycov/ha-sony-audio` as an **Integration**.
3. Install **Sony Audio**, then restart Home Assistant.
4. Add **Sony Audio** from Settings > Devices & services.

### Manual

Copy `custom_components/sony_audio` into the Home Assistant configuration directory,
restart Home Assistant, then add **Sony Audio** from Settings > Devices & services.

The endpoint is normally:

```text
http://RECEIVER_IP:10000/sony
```

Keep any existing Node-RED control in place during initial read-only validation.
Do not configure automations to write through both systems until behaviour has been
verified.

## Development phases

1. Validate discovery and read-only zone state on an STR-DN1080.
2. Validate commands zone by zone, starting with volume and mute.
3. Add Sony websocket push notifications and reconnect handling.
4. Remove the Node-RED workaround after feature parity and soak testing.
5. Prepare changes for upstream Home Assistant and `python-songpal` where useful.

## Licence

Apache License 2.0. `python-songpal` is a separate GPL-3.0-licensed runtime
dependency.
