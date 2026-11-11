# Status against the requirements

Date: 2026-11-11. Revision A. **The design is not complete and not validated.** Hardware has not been
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
| BOM | Done with part numbers and alternates. 37 part numbers checked on DigiKey on 2026-11-11. **Nine have no stock**, see below |
| Enclosure | Done in STEP, STL, 3MF. Fit-checked in CAD only |
| Software configuration | Written and checked against the kernel source Home Assistant OS 18.5 builds. **Not compiled or run** |
| Firmware | USB-PD programming script and radio firmware manifests written. **Not run, not built** |
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
| BOM with suppliers, pricing, alternates | Mostly | 41 of 86 lines carry a DigiKey price and stock figure from 2026-11-11. The other lines are passives and small parts, still estimated |
| Footprints verified against documentation | Partly | see the table below |
| ERC and DRC | Met for the current state | ERC clean. DRC clean except unrouted nets |
| No placeholders or incomplete circuits | Mostly | open values listed below |
| Home Assistant OS image or build process | Written | build recipe and overlay hook complete for release 18.5. Never built |
| Bootloader, device tree, drivers | Written | checked against kernel source. Not compiled, not run |
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

## Open values: what was checked on 2026-11-11

| Item | Result | Source |
|---|---|---|
| LMR33640 inductor | **Changed** from 10 uH to 6.8 uH, the datasheet value for 5 V at 400 kHz | TI LMR33640 datasheet, table 9-1 |
| LMR33640 and LMR33630 input capacitor | **Changed** from 100 nF to 220 nF | same table |
| LMR336x0 feedback dividers, boot and VCC capacitors | Confirmed: 100 k with 24.9 k or 43.2 k, 100 nF, 1 uF | same table |
| TPS2561 current limit, 47 kohm | Confirmed inside the 20 to 187 kohm range. About 1.19 A nominal, 1.05 to 1.33 A | TI TPS2561 datasheet. The limits are calculated from its equations |
| Fan connector pin order | Confirmed: +5 V, PWM, GND, tach | Raspberry Pi documentation |
| TLV320AIC3100 VOL/MICDET to ground, MICBIAS open | Accepted by TI support. An older TI reply advises against leaving VOL/MICDET open, which this design does not do | TI E2E forum |
| STUSB4500 470 ohm, 1 kohm, 100 kohm, 22 kohm, 100 nF | The values match ST's reference schematic. Which pin each one connects to could not be read from the search extract | ST datasheet figure 9 |
| Inductor part number | **Changed.** SRP1038C-6R8M is obsolete. Now SRP1038CC-6R8M | DigiKey |
| Oscillator part number | **Changed.** ECS-2520MV-122.8-BN-TR is not a listed part. Now ECS-2520MVLC-122.8-BN-TR, 12.288 MHz, 1.6 to 3.6 V, same package | DigiKey |

These were read through web search summaries and distributor pages, not from the PDFs directly,
because this machine has no PDF reader installed. Treat "confirmed" as "consistent with the source",
and read the two changed regulator values in the datasheet before ordering.

Still open:

- STUSB4500 pin-by-pin comparison with ST's figure 9, and the Q1 gate network.
- Ethernet centre-tap termination on the PHY side (100 nF each to ground).
- SRP1038CC body size. DigiKey lists 11.0 x 10.0 mm and the footprint used is named 10.0 x 10.0 mm.
- Part number strings for the capacitors, resistors and LEDs that were not looked up.

## Supply, as seen on DigiKey on 2026-11-11

A single distributor on a single day. Check Mouser, the manufacturers' own stores and LCSC before
concluding anything.

| Part | Stock | Note |
|---|---|---|
| LMR33640ADDAR (U5, U6) | 0 | 2,500 expected 2027-07-08, 26 week lead time. **The longest item.** The listed alternate LMR33640DDDAR is the 2.1 MHz version and needs a different inductor |
| LMR33630ADDAR (U7) | 0 | backorder |
| LM74700QDBVRQ1 (U3, U4) | 0 | backorder. Alternate LM74701-Q1 not checked |
| TPS2561DRCR (U10) | 0 | 3,000 expected 2026-12-01 |
| TLV320AIC3100IRHBR (U21) | 0 | 2,995 expected 2026-11-18 |
| TPD2EUSB30DRTR (U12, U14) | 0 | backorder |
| DF40HC(3.0)-100DS-0.4V(51) (J3, J13) | 0 | backorder |
| Wurth 7499511001A (J2) | 0 | 42 expected 2026-11-18 |
| SRP1038CC-6R8M (L1 to L3) | 0 | 500 expected 2027-01-18 |
| Ag5810 (U17) | 343 | about USD 17.50 at the top price tier, well under the earlier USD 31 estimate |

Parts cost for one board is now USD 97.93, of which USD 5.92 is still estimated.

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

1. Route the board. See "Routing" below.
2. Reach DRC clean, then run `make fab` for Gerber X2, drill, position and IPC-2581 files.
3. Resolve the supply gaps above, starting with the LMR33640.
4. Close the items under "Still open" and the mechanical checks in the footprint table.
5. Build the radio firmware and the Home Assistant OS image. Both need a Linux host with Docker.
6. Build five prototypes. Program the STUSB4500 with `firmware/stusb4500/program_nvm.py`, checking
   the first board against ST's own tool.
7. Run the validation plan and record results.

## Routing

Not done. The plan agreed on 2026-11-11 is a draft route: critical nets placed by script, the rest
by the Freerouting autorouter, and fabrication files marked as needing a layout review before any
order. That did not start, because downloading Freerouting was blocked on the machine used. Nothing
in the repository depends on the choice of router yet. `pcb-layout-guide.md` still describes the
rules any route has to meet, and its warning stands: a board that only passes DRC is not proven fit
to build.

## Found and fixed on 2026-11-11

- Overlay used `MICBIAS_OFF`, which the kernel binding header does not define. It would not compile.
- The PoE Type 4 sense pin, RP1 GPIO34, belongs to the camera regulator in the CM5 base device tree.
  The overlay now disables that regulator and `config.txt` turns camera and display probing off.
- The mixer script never closed the `Speaker` switch, no unit ran the script, and `amixer` is not in
  the Home Assistant OS host image. All three are fixed in the build recipe.
- `build.sh` assumed a board directory layout that Home Assistant OS 18.5 does not have.
- The stock Home Assistant OS kernel does not include the TLV320AIC31xx driver, so audio needs the
  custom image.
