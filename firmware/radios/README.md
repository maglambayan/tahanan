# Radio firmware

| Radio | Part | Firmware | Host port | Baud | Flow control |
|---|---|---|---|---|---|
| Zigbee (U19) | MGM240PA32VNN3 | Silicon Labs EmberZNet NCP (EZSP over UART) | /dev/tahanan-zigbee | 460800 | RTS/CTS |
| Thread (U20) | MGM240PA32VNA3 | OpenThread RCP (Spinel over UART) | /dev/tahanan-thread | 460800 | RTS/CTS |
| Z-Wave (J11) | plug-in 800-series module | vendor Serial API | /dev/tahanan-zwave | 115200 | none |

Module pin use (same on both MGM240P): PC00 TX to host, PC01 RX from host, PC02 RTS, PC03 CTS,
PB00 bootloader entry (hold low through reset), PA01 SWCLK, PA02 SWDIO.

## Building

`manifests/tahanan/` holds four manifests for the Home Assistant
[silabs-firmware-builder](https://github.com/NabuCasa/silabs-firmware-builder): a Gecko bootloader and an
application for each radio. They were derived from the upstream Home Assistant Yellow manifests (same
USART-with-flow-control arrangement) and change the device, the UART pins, the baud rate and the board
name. The activity LED and the MGM210 clock workaround were removed.

```
git clone https://github.com/NabuCasa/silabs-firmware-builder && cd silabs-firmware-builder
cp -r /path/to/tahanan/firmware/radios/manifests/tahanan manifests/
# then follow the builder README (Docker image) for each manifests/tahanan/*.yaml
```

The manifests pin `simplicity_sdk:2026.6.1` and toolchain 14.2.1, the versions upstream used on
2026-11-11. When upstream moves, re-derive from the then-current Yellow manifests instead of editing
versions by hand, because extension and patch names change with the SDK.

Points to check on the first build, none of which could be checked without the SDK:

- `device:` uses the SDK names `MGM240PA32VNN` and `MGM240PA32VNA` (orderable parts carry a trailing 3).
- USART0 routed to PC00 to PC03. The MGM240P allows USART0 on every port.
- Neither manifest sets a transmit power limit. Confirm the default the module applies against the
  regional limits in its certification before any radiated test.

First programming is over SWD (J8, J10 pads) with the Gecko bootloader plus application. Field updates
use the bootloader over UART:

```
universal-silabs-flasher --device /dev/tahanan-zigbee --bootloader-reset gpio \
    --gpio-reset 22 --gpio-boot 23 flash --firmware zigbee_ncp.gbl
universal-silabs-flasher --device /dev/tahanan-thread --bootloader-reset gpio \
    --gpio-reset 24 --gpio-boot 25 flash --firmware ot_rcp.gbl
```

Flag names differ between flasher releases; check `--help` for the installed version.
Status: manifests are complete but unbuilt. No firmware has been built or flashed for this board.
