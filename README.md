# Tahanan Hub

A Home Assistant hub built on the Raspberry Pi Compute Module 5: NVMe storage, Gigabit Ethernet with
802.3bt PoE, USB-C Power Delivery, Wi-Fi and Bluetooth, Zigbee, Thread and Matter, a Z-Wave module
socket, and a microphone, codec and speaker output for voice.

**Revision A is a design package, not a finished product.** The schematic is complete and passes ERC.
The board is placed but not routed, so there are no fabrication files yet. No hardware has been built
and nothing has been validated. Read [docs/status.md](docs/status.md) first.

Since the first commit the open component values and part numbers were checked, the BOM was priced
against DigiKey, and the firmware and Home Assistant OS build files were completed and corrected.
Routing, fabrication files, builds and all testing are still open.

## Layout of this repository

| Path | Contents |
|---|---|
| `docs/` | SoC evaluation, architecture, power and thermal, PCB guide, mechanical, software and recovery, validation plan, status |
| `hardware/` | KiCad 10 project: schematic sheets, board, project library, rules |
| `hardware/gen/` | Generator. `design.py` is the circuit. The KiCad files are built from it |
| `manufacturing/bom/` | Board BOM and system BOM as CSV |
| `mechanical/` | Parametric enclosure script and exported STEP, STL, 3MF |
| `software/` | Bootloader config, `config.txt` block, device tree overlay, Home Assistant OS build recipe |
| `firmware/` | USB-PD controller settings and programming script, radio firmware manifests |

## Building

Needs KiCad 10 and Python 3. From `hardware/`:

```
make sch erc     # schematic, netlist comparison, electrical rule check
make pcb drc     # placed board, design rule check
make docs        # schematic PDF, placement drawing, board STEP, BOM
make fab         # fabrication outputs. Refuses until the board is routed and DRC-clean
```

Enclosure, with CadQuery installed: `python mechanical/enclosure.py`.

The schematic sheets and the board are editable in KiCad. Edits made there are overwritten by the
generator, so either change `design.py` or stop using the generator once manual layout begins.
