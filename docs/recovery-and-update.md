# Software, recovery and updates

Nothing in this document has been run on Tahanan hardware. It records the intended configuration.

## Boot chain

1. CM5 EEPROM bootloader, configured by `software/boot/eeprom-boot.conf`.
2. Boot order: NVMe first, then USB mass storage, then retry.
3. Home Assistant OS for Raspberry Pi 5 class boards, which already supports CM5, with:
   - `software/boot/config.txt.tahanan` appended to `config.txt`,
   - `software/dts/tahanan-overlay.dts` compiled to `overlays/tahanan.dtbo`,
   - the kernel options in `software/haos-board/kernel-tahanan.config`,
   - the files under `software/rootfs/`.

## Getting an image

**Bring-up path.** Flash the stock Home Assistant OS image for Raspberry Pi 5 to the SSD. Mount the
boot partition, append the config block and copy in the compiled overlay. Everything except audio
works this way. The stock kernel configuration (`bcm2712_defconfig`) does not build the TLV320AIC31xx
codec driver, so audio needs the reproducible path.

**Reproducible path.** Run `software/haos-board/build.sh` on a Linux host with Docker. It clones Home
Assistant OS (18.5 unless `HAOS_TAG` names another release), adds the kernel fragment, the overlay, the
config block and the root file system files, patches the image hook so the overlay is compiled during
the build, and prints the build command. The tree preparation was checked against the 18.5 board
files. The image build itself has not been run.

## Hardware support expected from the operating system

| Hardware | Driver or mechanism | Expected state |
|---|---|---|
| NVMe on PCIe | `nvme`, `dtparam=pciex1` | supported upstream |
| Ethernet | CM5 PHY and MAC | supported upstream |
| Wi-Fi and Bluetooth | CM5 radio | supported upstream |
| USB 3.0 and 2.0 | RP1 xHCI, dwc2 | supported upstream |
| Zigbee | ZHA or Zigbee2MQTT over `/dev/tahanan-zigbee` | needs board-specific radio firmware |
| Thread and Matter | OpenThread Border Router add-on over `/dev/tahanan-thread` | needs board-specific radio firmware |
| Z-Wave | Z-Wave JS over `/dev/tahanan-zwave` | depends on the plug-in module |
| Audio codec | `snd-soc-tlv320aic31xx` with `simple-audio-card` | overlay written. Driver is added by the kernel fragment, it is not in the stock image |
| Fan and RTC | CM5 firmware and kernel | supported upstream |
| User button, LED, mute and PoE sense | `gpio-keys`, `gpio-leds` | overlay written. The overlay disables the CM5 camera regulator, which otherwise owns the PoE sense pin |
| USB-PD controller | none | no kernel driver bound. Status readable over I2C from user space |
| PoE power class | none | only the Type 4 flag reaches Linux |

Echo cancellation and noise suppression are done in software by the voice pipeline. The hardware
provides a sample-synchronous playback reference. There is one microphone, so no beamforming.

## Recovery

| Situation | Procedure |
|---|---|
| SSD will not boot | Insert a USB drive holding a Home Assistant OS image. The bootloader falls through to USB. Restore the latest backup |
| Replace or re-image the SSD | Boot from USB as above, or image the SSD in a USB enclosure on another computer |
| Bootloader configuration lost or corrupt | Power the hub from **PoE**. Hold RPIBOOT (SW2) while applying power. Connect J1 to a computer and run Raspberry Pi `usbboot` with the recovery image and `eeprom-boot.conf` |
| Zigbee or Thread radio firmware corrupt | Reflash over UART with the bootloader GPIOs, see `firmware/radios/README.md`. If the bootloader is gone, use the SWD pads J8 or J10 |
| Service console | 3.3 V serial on J7, 115200 baud, `/dev/ttyAMA4` |

The USB-C port will not power the hub from a computer's 5 V port. That is why bootloader recovery
needs PoE, or 12 V on the V12_POE test pad, as the power source.

## Updates

- Operating system: Home Assistant OS A/B updates, with automatic rollback if the new slot fails.
- Bootloader EEPROM: `rpi-eeprom-update` from a maintenance image, or `usbboot` as above.
- Radio firmware: `universal-silabs-flasher` over UART.
- USB-PD controller: programmed once at factory test, see `firmware/stusb4500/nvm-config.md`.
