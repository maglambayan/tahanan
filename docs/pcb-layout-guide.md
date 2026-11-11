# PCB status and layout guide

## What exists

`hardware/tahanan.kicad_pcb` is a **placed, unrouted** board.

| Item | State |
|---|---|
| Outline | 160 x 105 mm, 3 mm corner radius, 1.6 mm, 4 copper layers |
| Mounting holes | 4x M3 plated, 4 mm in from each corner |
| Footprints | 230, all with nets, references and BOM fields. Schematic parity: 0 issues |
| Connector positions | Fixed. Rear edge: RJ45, dual USB-A, USB-C. See the table below |
| Component placement | Functional floorplan. Passives are grouped by circuit but not yet placed pin-adjacent |
| Keep-outs | CM5 antenna, Thread antenna, PoE primary area with no planes |
| Net classes and rules | Defined in `tahanan.kicad_pro` and `tahanan.kicad_dru` |
| DRC | 0 errors. 35 silkscreen warnings. 499 unrouted connections |
| Routing | **Not done** |
| Fabrication files | **Not generated.** `make fab` refuses to run until DRC is clean and nothing is unrouted |

Routing was not attempted with an autorouter. This board carries PCIe, two USB 3.0 ports, Gigabit
Ethernet, a 2.4 GHz antenna feed and a 1500 V isolation barrier. An autorouted result would pass DRC
and still be unfit to build, so it would only look finished.

## Fixed positions

Origin is the top-left board corner, x to the right, y towards the front. Rear edge is y = 0.

| Part | Position (mm) | Side | Note |
|---|---|---|---|
| J2 RJ45 | x 20, front face at y 0 | top | body 16.6 wide, 32.8 deep |
| J5 dual USB-A | centre x 41.3 | top | face 1.5 mm beyond the board edge, to confirm against the Molex drawing |
| J1 USB-C | centre x 60 | top | edge position from the footprint's PCB-edge mark |
| SW1 Power, SW3 User, SW2 RPIBOOT | x 71.5, 81.5, 91.5, y 4 | top | top-actuated, enclosure plungers |
| CM5 outline | x 97-152, y 8-48 | top | antenna at the right edge, 3.0 mm stack |
| J13, J3 CM5 connectors | centre x 127, y 11 and y 45 | top | 34.0 mm apart |
| U17 Ag5810 | centre 38, 67 | top | input pins on the left |
| U20 Thread module | centre 17, 97.2 | top | antenna at the front edge |
| U19 Zigbee module | centre 37, 95 | top | |
| J11 Z-Wave socket | pin 1 at 58, 88 | top | plug-in module overhangs to the right |
| J4 M.2 socket | 146, 92 | bottom | SSD extends towards x = 66 |
| MK1 microphone | 155, 72 | bottom | sound port through the board |

## Stack-up

| Layer | Use |
|---|---|
| F.Cu | components, high-speed pairs, RF feed |
| In1 | solid ground, cut only at the PoE primary area and under the antennas |
| In2 | power planes: +5V, +5V_USB, +3V3_NVME, +3V3, VIN |
| B.Cu | M.2 socket, microphone, slow signals, ground fill |

Target a standard 1.6 mm, 4-layer controlled-impedance stack with about 0.2 mm prepreg between the
outer and inner layers, ENIG finish, 0.3 mm minimum drill.

## Net classes

| Class | Nets | Width / gap | Target |
|---|---|---|---|
| Diff90 | PCIe, USB 3.0, USB 2.0 | 0.20 / 0.15 mm | 90 ohm differential |
| Diff100 | Ethernet MDI pairs | 0.17 / 0.18 mm | 100 ohm differential |
| RF50 | Zigbee RF feed | 0.35 mm | 50 ohm, under 12 mm long |
| PowerHigh | VIN, VBUS, V12_POE, +5V, +5V_USB, +3V3_NVME, switch nodes | 1.2 mm minimum | use pours |
| Power | +3V3, +1V8, USB_VBUS, speaker | 0.5 mm minimum | |
| PoE_Primary | everything on the cable side of the Ag5810 | 0.6 mm | 2.5 mm to all other copper |

The width and gap values are starting points for a 0.2 mm prepreg. **Recompute them with the chosen
fabricator's impedance calculator before routing.**

## Routing rules, in priority order

1. **Isolation.** No copper of any other net and no plane within 2.5 mm of a PoE_Primary net, on every
   layer. Only the Ag5810 and the optocoupler U18 cross the barrier. Keep the area under the Ag5810
   isolation gap free of copper, as its datasheet figure 14 shows.
2. **PCIe.** Route on F.Cu over unbroken ground. Match within each pair to 0.1 mm. No capacitors on
   the carrier: TX capacitors are on the CM5 and RX capacitors on the SSD. The socket is on the
   bottom, so each pair needs one via pair with adjacent ground vias.
3. **USB 3.0.** Match within each pair to 0.1 mm. Place U11 to U14 ESD arrays at the connector.
4. **Ethernet.** Match within each pair to 0.15 mm. Pair-to-pair skew under 50 mm is acceptable.
5. **RF.** Shortest possible feed from U19 pad 33 to J9, coplanar ground with via fencing. Keep the pi
   network pads in line. Keep the CM5 and Thread antenna keep-outs free on all layers.
6. **Switching regulators.** For U5, U6 and U7 put the input capacitors and the switch-node loop first,
   then move each remaining passive next to the pin it serves. The current placement groups them by
   circuit only.
7. **Decoupling.** Move each 100 nF capacitor to within 2 mm of its supply pin before routing.
8. **Audio.** Keep the microphone pair away from the class-D outputs and the switch nodes. Join +3V3A
   to +3V3 only at the ferrite.

## Items to resolve during layout

- Confirm the Amphenol or Hirose CM5 connector land pattern and height against the mating drawing.
- Confirm the M.2 retention post positions (H9, H10) and post height against TE specification
  114-115006. The 2.0 mm card-edge offset used is an assumption.
- Confirm the board-edge overhang of J5 against the Molex 48406-0001 drawing.
- Confirm which jack holes are plated in the Würth 7499511001A drawing (the 1.6 mm pair is assumed to
  be the shield tabs).
- Confirm the SRP1038CC inductor body, listed as 11.0 x 10.0 mm, against the footprint used for L1 to L3.
- Re-run `make drc` until it reports 0 errors and 0 unconnected, then run `make fab`.
