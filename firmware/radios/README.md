# Radio firmware

| Radio | Part | Firmware | Host port | Baud | Flow control |
|---|---|---|---|---|---|
| Zigbee (U19) | MGM240PA32VNN3 | Silicon Labs EmberZNet NCP (EZSP over UART) | /dev/tahanan-zigbee | 460800 | RTS/CTS |
| Thread (U20) | MGM240PA32VNA3 | OpenThread RCP (Spinel over UART) | /dev/tahanan-thread | 460800 | RTS/CTS |
| Z-Wave (J11) | plug-in 800-series module | vendor Serial API | /dev/tahanan-zwave | 115200 | none |

Module pin use (same on both MGM240P): PC00 TX to host, PC01 RX from host, PC02 RTS, PC03 CTS,
PB00 bootloader entry (hold low through reset), PA01 SWCLK, PA02 SWDIO.

Build with the Home Assistant `silabs-firmware-builder` using a manifest derived from an existing MGM240P
board, changing only the USART pin assignment, the bootloader button GPIO (PB00) and the device name.
`manifest-zigbee.yaml` and `manifest-thread.yaml` in this directory record those values.

First programming is over SWD (J8, J10 pads) with the Gecko bootloader plus application. Field updates
use the bootloader over UART:

```
universal-silabs-flasher --device /dev/tahanan-zigbee --bootloader-reset gpio \
    --gpio-reset 22 --gpio-boot 23 flash --firmware zigbee_ncp.gbl
universal-silabs-flasher --device /dev/tahanan-thread --bootloader-reset gpio \
    --gpio-reset 24 --gpio-boot 25 flash --firmware ot_rcp.gbl
```

Flag names differ between flasher releases; check `--help` for the installed version.
Status: manifests are pin records only. No firmware has been built or flashed for this board.
