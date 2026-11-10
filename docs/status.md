# Status against the requirements

Date: 2026-11-10. Revision A. **The design is not complete and not validated.** Hardware has not been
built. This page states what was delivered, what was checked and how, and what is still open.

## Summary

| Area | State |
|---|---|
| SoC evaluation and architecture | Done |
| Schematic | Done. ERC 0 errors, 0 warnings. Netlist verified pin by pin |
| Custom footprints | Done from manufacturer drawings. Not yet checked against physical parts |
| PCB placement, outline, rules | Done. DRC 0 errors |
| PCB routing | **Not done** |
| Gerber, drill, assembly, pick-and-place | **Not generated.** Pipeline exists and is gated on a routed board |
| BOM | Done with part numbers and alternates. **Prices and stock are not verified** |
| Enclosure | Done in STEP, STL, 3MF. Fit-checked in CAD only |
| Software configuration | Written. **Not compiled or run** |
| Validation plan | Written. **No test has been run** |

## Requirement by requirement

| Requirement | State | Evidence or gap |
|---|---|---|
| Evaluate three or more SoCs | Met | `soc-evaluation.md`, five candidates |
| System block diagram | Met | `architecture.md` |
| Public datasheets, available parts | Met | every BOM line has a manufacturer part number |
| Gigabit Ethernet | Designed | CM5 PHY, Würth jack |
| Wi-Fi 2.4 and 5 GHz, BLE | Designed | on the CM5 |
| Zigbee, Thread, Matter | Designed | two MGM240P modules |
| Z-Wave | Designed as an expansion socket | module is a separate purchase |
| External antenna connectors | Designed | Zigbee U.FL to RP-SMA, optional Wi-Fi |
| RF interference and antenna placement | Partly | keep-outs and separation in the placement. No simulation, not measured |
| MEMS microphone, codec, amplifier | Designed | one microphone, codec with integrated class-D |
| Noise suppression and echo cancellation | Partly | synchronous reference in hardware, processing left to software |
| USB-C PD and 802.3bt PoE | Designed | see the PoE limits below |
| Automatic input selection, reverse protection | Designed | ideal-diode OR-ing |
| Regulation and sequencing | Designed | `power-and-thermal.md` |
| Maximum power and thermal dissipation | Calculated | not measured |
| Stable at maximum load | **Unproven** | needs tests PWR-09 and TH-03 |
| PCB dimensions, holes, connector positions | Met | `pcb-layout-guide.md` |
| Enclosure, thermal management, access | Designed | `mechanical.md` |
| STEP, STL, 3MF | Met | `mechanical/out/` |
| Editable schematic and PCB sources | Met | KiCad 10 project plus the generator |
| Gerber X2, drill, assembly, pick-and-place | **Not met** | needs routing |
| BOM with suppliers, pricing, alternates | Partly | supplier links are searches, prices are estimates |
| Footprints verified against documentation | Partly | see the table below |
| ERC and DRC | Met for the current state | ERC clean. DRC clean except unrouted nets |
| No placeholders or incomplete circuits | Mostly | open values listed below |
| Home Assistant OS image or build process | Partly | process written, one hook missing, never built |
| Bootloader, device tree, drivers | Written | not compiled, not run |
| NVMe primary, USB alternate boot | Configured | `eeprom-boot.conf` |
| Recovery and update procedure | Written | untested |
| All validation testing | **Not done** | no hardware |

## How each footprint and pinout was verified

| Part | Source | Remaining check |
|---|---|---|
| All stock KiCad parts, about 95 % of placements | KiCad 10 standard library. The generator rejects any symbol pin without a matching pad | none before prototype |
| CM5 pinout, 200 pins | parsed from the CM5 datasheet pin table | none |
| CM5 connector spacing, 34.0 mm | CM5 datasheet drawing, agreed by one independent open design | **check against the official CM5 STEP model** |
| Würth 7499511001A | datasheet hole pattern and schematic, read from the drawing | which holes are plated. Confirm with the 3D model |
| Silvertel Ag5810 | datasheet V1.2 package drawing and pin table | none before prototype |
| Silicon Labs MGM240P | datasheet land pattern, matches a SparkFun production footprint | none before prototype |
| M.2 retention posts | estimated | **position and height unverified** |

## Values taken from memory, to confirm against the datasheet before ordering

- STUSB4500 support components: 470 ohm and 1 kohm discharge resistors, Q1 gate network.
- TPS2561 current-limit resistor, 47 kohm for about 1.2 A.
- LMR33630 and LMR33640 inductor and output capacitor values, and feedback dividers.
- TLV320AIC3100: treatment of the VOL/MICDET pin (tied to ground) and unused MICBIAS.
- Ethernet centre-tap termination on the PHY side (100 nF each to ground).
- Fan connector pin order, taken as the Raspberry Pi 5 fan pinout.
- Part number strings for the oscillator, several capacitors and the 3 mm spacers.

## Known limitations of the design

1. **PoE jack rating.** The jack is specified for 600 mA per centre tap and its datasheet claims
   802.3at only. Electrically that covers 802.3bt Type 3 current, and the design draws at most
   0.52 A per pairset. A jack with an explicit 802.3bt rating should replace it if one with a public
   datasheet is found.
2. **PoE class.** The Ag5810 always requests Class 7. The board never draws more than about 45 W.
3. **PoE source detection.** Linux sees only a Type 4 flag. It cannot tell an 802.3at source from an
   802.3bt Type 3 source without LLDP or operator configuration.
4. **One microphone.** No beamforming. The codec has a mono converter.
5. **PCIe Gen 2 and 1 Gb/s Ethernet**, both set by the CM5.
6. **No radio coexistence signalling** between Wi-Fi and the 802.15.4 radios.
7. **Z-Wave is not on the board.** It needs a plug-in module.
8. **No HDMI.** The unit is headless. Service access is the serial console.
9. **Sole source** for the compute module and for the PoE module.
10. **Fan needed** for sustained loads above roughly 15 W.
11. **Operating range 0 to 40 °C**, limited by the jack and the passive cooling.
12. **USB-C needs a 45 W PD charger.** The port does not accept 5 V-only supplies.

## Work remaining, in order

1. Confirm the open values and mechanical items listed above.
2. Refine placement and route the board by hand, following `pcb-layout-guide.md`.
3. Reach DRC clean, then run `make fab` for Gerber X2, drill, position and IPC-2581 files.
4. Verify BOM price and stock with distributors and fix alternates.
5. Build five prototypes. Write the STUSB4500 programming script and the radio firmware.
6. Finish the Home Assistant OS build hook and build the image.
7. Run the validation plan and record results.
