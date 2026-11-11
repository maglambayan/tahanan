# Power and thermal design

All figures are design calculations from datasheet limits. None has been measured.

## Rails

| Rail | Source | Rating | Loads |
|---|---|---|---|
| VIN | USB-C 15/20 V or PoE 12 V through ideal diodes | 9-21 V, UVLO 8 V | all regulators |
| +5V | U5 LMR33640, 400 kHz, 6.8 uH | 4 A | CM5, speaker amplifier, fan, U8, Z-Wave socket |
| +5V_USB | U6 LMR33640 | 4 A | two USB 3.0 ports through U10 |
| +3V3_NVME | U7 LMR33630, 6.8 uH | 3 A | M.2 socket only |
| +3V3 | U8 AP63203 from +5V | 2 A | both MGM240P, codec I/O, oscillator, LEDs |
| +1V8 | U9 AP2112K-1.8 | 0.6 A | codec core |

## Sequencing

1. VIN rises above 8 V. U5 starts and +5V comes up.
2. PG_5V enables U6 (+5V_USB). The CM5 PMIC starts from +5V.
3. CM5_3V3 from the module enables U8 (+3V3), so no carrier device can drive a CM5 pin before the
   module is powered. This is the rule in CM5 datasheet section 3.1.
4. The CM5 raises PCIE_PWR_EN, which enables U7 (+3V3_NVME), and VBUS_EN, which enables the USB ports.

## Maximum power budget

| Load | Rail | Maximum | Basis |
|---|---|---|---|
| CM5 at full CPU load with Wi-Fi | +5V | 12.0 W | Raspberry Pi 5 class peak |
| Speaker amplifier at full output | +5V | 2.9 W | 2.5 W out at 88 % |
| Fan | +5V | 1.0 W | 40 mm, 5 V |
| +3V3 loads, through U8 at 90 % | +5V | 1.8 W | two radios transmitting at +20 dBm, codec |
| Z-Wave module | +5V | 0.2 W | |
| **+5V total** | | **17.9 W, 3.6 A** | U5 rated 4 A |
| USB ports, 2 x 0.9 A | +5V_USB | 9.0 W | USB 3.0 port limit |
| NVMe SSD peak | +3V3_NVME | 8.25 W | M.2 limit of 2.5 A |
| **Load total** | | **35.2 W** | |
| Regulator losses at 92 % | | 3.1 W | |
| **At VIN** | | **38.3 W** | |

| Source | Draw at maximum | Limit | Margin |
|---|---|---|---|
| USB-C at 20 V | 1.92 A | 2.25 A (45 W) | 15 % |
| USB-C at 15 V | 2.56 A | 3.0 A (45 W) | 15 % |
| PoE, at the PD interface | 44.6 W | 51 W (Class 6) | 13 % |
| PoE current per pairset at 42.5 V | 0.52 A | 0.60 A (jack rating) | 13 % |

PoE figure: 38.3 W divided by 88 % module efficiency, plus about 1 W in the bridge diodes.

Typical operation (idle Home Assistant, SSD idle, no USB loads) is estimated at 8 to 9 W from USB-C and
10 to 11 W from PoE.

## Known power limits

- **U5 runs at 90 % of its rating in the worst case.** If measurement shows the CM5 above 12 W, move the
  speaker supply to +5V_USB or fit the pin-compatible higher-current part.
- **A 25 W PoE source (802.3at) cannot run the full budget.** The Ag5810 reports only whether the
  source is Type 4. Software must assume 25 W unless that signal is active or the administrator
  declares a Type 3 source, and in that mode it must keep USB port power off. See `docs/status.md`.
- **A 5 V-only USB-C charger will not power the unit.** This is by design.

## Thermal

| Heat source | Typical | Maximum |
|---|---|---|
| CM5 | 4.5 W | 12 W |
| NVMe SSD | 1.5 W | 8 W |
| Ag5810, PoE only | 1.3 W | 5.2 W |
| Regulators, bridge, OR-ing | 1.0 W | 4.3 W |
| Audio, radios, other | 0.8 W | 4 W |
| **Inside the enclosure** | **about 9 W** | **about 34 W** |

USB port power leaves the enclosure and is not counted.

- Enclosure outer surface is about 0.055 m². With natural convection and radiation near 8 W/m²K, a
  sealed box rises about 20 K at 9 W. Vent slots above and below the CM5 and the PoE module are
  expected to lower this, but the gain is unmeasured.
- The CM5 carries a passive heat sink under the lid vents. The SSD is coupled to the base by a
  thermal pad. The Ag5810 sits over base intake slots.
- **Sustained maximum load cannot be cooled passively.** 34 W in this volume would exceed 70 K rise.
  The optional 40 mm fan on J6 is required for sustained loads above roughly 15 W. Fan mounting
  holes are in the lid.
- Design ambient target is 0 to 40 °C. The Ethernet jack is rated 0 to 70 °C and sets the lower limit.

Every number in this section is a prediction. Tests PWR-01 to PWR-09 and TH-01 to TH-05 in
`docs/validation-plan.md` replace them with measurements.
