# SoC evaluation

Five publicly available application processors were compared. Figures are from vendor datasheets and
published board measurements, rounded. They were not measured on Tahanan hardware.

| | Broadcom BCM2712 | Rockchip RK3588S | Rockchip RK3568 | NXP i.MX 8M Plus | Amlogic S905X3 |
|---|---|---|---|---|---|
| CPU | 4x Cortex-A76, 2.4 GHz | 4x A76 + 4x A55 | 4x Cortex-A55, 2.0 GHz | 4x Cortex-A53, 1.8 GHz | 4x Cortex-A55, 1.9 GHz |
| Relative CPU throughput | 1.0 (reference) | about 1.8 multi-core | about 0.35 | about 0.3 | about 0.35 |
| Board power, idle / full load | about 3 W / 8-12 W | about 3 W / 12-15 W | about 1.5 W / 5 W | about 1.5 W / 5 W | about 1.5 W / 4 W |
| How it is bought | Only on Raspberry Pi boards and modules | Chip or third-party module | Chip or third-party module | Chip or module, open distribution | Chip, limited distribution |
| Stated availability | CM5 in production until at least January 2036 | Vendor and module-maker programmes, typically 10 years | Same | NXP 15-year longevity programme | Not published |
| Linux support | Raspberry Pi kernel, upstreaming in progress | Mainline usable, some blocks still vendor-only | Good mainline support | Excellent mainline support | Good mainline support |
| PCIe | 1 lane, Gen 2 supported | 1 lane Gen 2 | 2 lanes Gen 3 plus 1 lane Gen 2 | 1 lane Gen 3 | none |
| Ethernet | GbE PHY on the module | GbE MAC, external PHY | 2x GbE MAC, external PHY | 2x GbE MAC, one with TSN | GbE MAC, external PHY |
| USB | 2x USB 3.0, 1x USB 2.0 | USB 3.x plus USB 2.0 | 2x USB 3.0, 2x USB 2.0 | 2x USB 3.0 | 1x USB 3.0 |
| Audio | I2S master and slave | I2S, PDM | I2S, PDM | SAI, PDM, audio DSP | I2S, PDM |
| Wi-Fi and Bluetooth | Certified 802.11ac and BLE 5.0 on the module | external module | external module | external module | external module |
| Home Assistant OS | Official image, covers CM5 | No official image | Official image for ODROID-M1 | No official image | Official image for ODROID-C4 |
| Design effort | 4-layer carrier, no DDR or PMIC design | 8+ layer SoC-down, or carrier for a module | 6+ layer SoC-down, or carrier | 6+ layer SoC-down, or carrier | 6-layer SoC-down |

## Decision

**Selected: BCM2712, used as the Raspberry Pi Compute Module 5.**

- It is the only candidate with all three of: an official Home Assistant OS image, a pre-certified
  dual-band Wi-Fi and BLE radio, and a published end-of-production date.
- The module contains the SoC, LPDDR4X, PMIC, Ethernet PHY and radio. The carrier is then a 4-layer board
  with no DDR routing, which is the largest single reduction in manufacturing and certification risk.
- CPU headroom is two to three times that of the A55 and A53 parts, which matters for local voice
  processing and add-ons.

**Runner-up: RK3568.** It has better PCIe (Gen 3, two lanes) and lower power, and Home Assistant OS
supports one RK3568 board. It was rejected because Tahanan would need its own board port, its own
radio module and certification, and a 6-layer SoC-down or third-party module design.

**Rejected:** RK3588S and i.MX 8M Plus have no Home Assistant OS image. S905X3 has no PCIe, so it cannot
meet the NVMe requirement.

## Consequences accepted with this choice

- PCIe is Gen 2, one lane. NVMe sequential throughput is capped near 450 MB/s.
- Ethernet is 1 Gb/s. 2.5 Gb/s would need the single PCIe lane, which the SSD uses.
- BCM2712 cannot be bought as a chip. The product depends on Raspberry Pi Ltd as sole source for the
  module. CM5 variants with other RAM sizes are drop-in alternates.
