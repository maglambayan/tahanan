"""Write tahanan.kicad_pro: net classes, design rules and class assignment patterns."""
import json, os
HW = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
def cls(name, **kw):
    d = dict(name=name, clearance=0.127, track_width=0.15, via_diameter=0.6, via_drill=0.3, microvia_diameter=0.3, microvia_drill=0.1,
             diff_pair_width=0.15, diff_pair_gap=0.15, diff_pair_via_gap=0.25, bus_width=12, wire_width=6, line_style=0,
             pcb_color='rgba(0, 0, 0, 0.000)', schematic_color='rgba(0, 0, 0, 0.000)', priority=0)
    d.update(kw); return d
classes = [cls('Default', priority=2147483647),
           # JLC04161H-7628 4-layer stack, see docs/hardware/pcb-design-rules.md for the impedance calculation
           cls('Diff90', track_width=0.2, diff_pair_width=0.2, diff_pair_gap=0.15, clearance=0.2),
           cls('Diff100', track_width=0.17, diff_pair_width=0.17, diff_pair_gap=0.18, clearance=0.2),
           cls('RF50', track_width=0.35, clearance=0.3),
           cls('Power', track_width=0.5, clearance=0.2, via_diameter=0.8, via_drill=0.4),
           cls('PowerHigh', track_width=1.2, clearance=0.127, via_diameter=0.8, via_drill=0.4),
           cls('PoE_Primary', track_width=0.6, clearance=0.2, via_diameter=0.8, via_drill=0.4)]
patterns = [('PCIE_*_[PN]', 'Diff90'), ('USB3_*', 'Diff90'), ('USB2_D[PM]', 'Diff90'), ('ETH_P?_[PN]', 'Diff100'), ('ZB_RF_*', 'RF50'),
            ('POE_V?', 'PoE_Primary'), ('VPOE_*', 'PoE_Primary'), ('POE_VIN_*', 'PoE_Primary'), ('POE_T4DET', 'PoE_Primary'), ('POE_OPTO_A', 'PoE_Primary'),
            ('unconnected-(*-TYP2-DET-*', 'PoE_Primary'), ('unconnected-(*-SA?-Pad*', 'PoE_Primary'),   # unused pins on the primary side of the PoE module
            ('VIN', 'PowerHigh'), ('VBUS*', 'PowerHigh'), ('V12_POE', 'PowerHigh'), ('+5V*', 'PowerHigh'), ('+3V3_NVME', 'PowerHigh'), ('SW_*', 'PowerHigh'),
            ('USB_VBUS?', 'Power'), ('+3V3*', 'Power'), ('+1V8', 'Power'), ('CM5_3V3', 'Power'), ('SPK_*', 'Power')]
pro = {'meta': {'filename': 'tahanan.kicad_pro', 'version': 3},
       'board': {'design_settings': {'rules': {'min_clearance': 0.127, 'min_track_width': 0.127, 'min_via_diameter': 0.45, 'min_through_hole_diameter': 0.2,
                                               'min_via_annular_width': 0.1, 'min_copper_edge_clearance': 0.3, 'min_hole_to_hole': 0.25, 'min_hole_clearance': 0.25,
                                               'min_silk_clearance': 0.0, 'min_microvia_diameter': 0.2, 'min_microvia_drill': 0.1, 'solder_mask_to_copper_clearance': 0.0}}},
       'net_settings': {'classes': classes, 'meta': {'version': 4}, 'net_colors': None, 'netclass_assignments': None,
                        'netclass_patterns': [{'netclass': c, 'pattern': p} for p, c in patterns]},
       'schematic': {'meta': {'version': 1}}, 'sheets': [], 'text_variables': {}}
json.dump(pro, open(os.path.join(HW, 'tahanan.kicad_pro'), 'w'), indent=2)
print('project file written')

# Custom DRC rules. The isolation barrier is a rule between classes, so primary nets may sit at
# normal spacing to each other while staying 2.5 mm from everything on the secondary side.
open(os.path.join(HW, 'tahanan.kicad_dru'), 'w').write("""(version 1)

(rule "PoE isolation barrier"
  (condition "A.NetClass == 'PoE_Primary' && B.NetClass != 'PoE_Primary' && B.NetName != ''")
  (constraint clearance (min 2.5mm)))

(rule "PoE primary to planes"
  (condition "A.NetClass == 'PoE_Primary' && B.Type == 'Zone'")
  (constraint clearance (min 2.5mm)))

# Stock library footprints whose own pad sits closer to its own hole than the board-level 0.25 mm.
(rule "SMT spacers: pad surrounds its own hole"
  (condition "A.Type == 'Pad' && A.Fabrication_Property == 'Heatsink pad' || A.memberOfFootprint('H*')")
  (constraint hole_clearance (min 0mm)))

(rule "USB-C and microphone locating holes"
  (condition "A.memberOfFootprint('J1') || A.memberOfFootprint('MK1')")
  (constraint hole_clearance (min 0.15mm)))

(rule "Diff90 intra-pair skew"
  (condition "A.NetClass == 'Diff90'")
  (constraint skew (max 0.1mm)))

(rule "Diff100 intra-pair skew"
  (condition "A.NetClass == 'Diff100'")
  (constraint skew (max 0.15mm)))

(rule "RF feed length"
  (condition "A.NetClass == 'RF50'")
  (constraint length (max 12mm)))
""")
