"""Project-specific symbols and footprints (parts with no stock KiCad library entry).

Every dimension below is transcribed from the manufacturer document named in the
comment next to it. See docs/hardware/verification-ledger.md for the status of each.
"""
import json, os
from sexp import parse, dump

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.join(HERE, '..')
LIB = 'tahanan'

# ---------------------------------------------------------------- symbols
def box_symbol(name, ref, left, right, descr='', datasheet='', fp=''):
    """left/right: lists of (number, name, electrical_type) or None for a gap."""
    rows = max(len(left), len(right))
    lw = max([len(p[1]) for p in left if p] + [1]); rw = max([len(p[1]) for p in right if p] + [1])
    half = max(7.62, round(((lw + rw) * 1.1 + 6) / 2 / 2.54 + 0.5) * 2.54)
    top = (rows // 2 + 1) * 2.54
    s = [f'(symbol "{name}" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)',
         f'(property "Reference" "{ref}" (at {-half} {top + 1.27} 0) (effects (font (size 1.27 1.27)) (justify left)))',
         f'(property "Value" "{name}" (at 0 {top + 1.27} 0) (effects (font (size 1.27 1.27)) (justify left)))',
         f'(property "Footprint" "{fp}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'(property "Datasheet" "{datasheet}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'(property "Description" "{descr}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         f'(symbol "{name}_0_1" (rectangle (start {-half} {top}) (end {half} {top - (rows + 1) * 2.54}) (stroke (width 0.254) (type default)) (fill (type background))))',
         f'(symbol "{name}_1_1"']
    for side, pins in (('L', left), ('R', right)):
        for i, p in enumerate(pins):
            if not p:
                continue
            y = top - (i + 1) * 2.54
            x, ang = (-half - 2.54, 0) if side == 'L' else (half + 2.54, 180)
            s.append(f'(pin {p[2]} line (at {x} {y} {ang}) (length 2.54) (name "{p[1]}" (effects (font (size 1.27 1.27)))) (number "{p[0]}" (effects (font (size 1.27 1.27)))))')
    s.append('))')
    return parse('\n'.join(s))

def cm5_type(name):
    if name == 'GND': return 'power_in'
    if name == '5V': return 'power_in'
    if name in ('CM5_3.3V', 'CM5_1.8V'): return 'passive'
    if name == 'VBAT' or name == 'GPIO_VREF': return 'power_in'
    return 'bidirectional'

def symbols():
    pins = {int(k): v[0] for k, v in json.load(open(os.path.join(HERE, 'cm5_pins.json'))).items()}
    out = {}
    for half, base in (('A', 0), ('B', 100)):
        # Connector pad n of half B carries module pin 100+n (CM5 datasheet table 4).
        odd = [(str(n), pins[base + n], cm5_type(pins[base + n])) for n in range(1, 101, 2)]
        even = [(str(n), pins[base + n], cm5_type(pins[base + n])) for n in range(2, 101, 2)]
        out[f'CM5_{half}'] = box_symbol(f'CM5_{half}', 'J', odd, even,
            descr=f'Raspberry Pi Compute Module 5 board-to-board connector, module pins {base + 1}-{base + 100}',
            datasheet='https://datasheets.raspberrypi.com/cm5/cm5-datasheet.pdf',
            fp='Connector_Hirose_DF40:Hirose_DF40HC(3.0)-100DS-0.4V_2x50_P0.4mm')
    # Silvertel Ag5810 datasheet V1.2 section 1.2
    out['Ag5810'] = box_symbol('Ag5810', 'U',
        [('1', 'VIN+', 'power_in'), ('2', 'VIN-', 'power_in'), None, ('3', 'TYP2-DET', 'open_collector'),
         ('4', 'TYP4-DET', 'open_collector'), None, ('5', 'SA1', 'passive'), ('6', 'SA2', 'passive')],
        [('7', 'VOUT1', 'power_out'), ('8', 'VOUT1', 'passive'), ('10', 'VOUT2', 'passive'), None,
         ('13', 'ADJ', 'passive'), None, ('9', '0V1', 'passive'), ('11', '0V2', 'passive'), ('12', '0V2', 'passive')],
        descr='60 W IEEE 802.3bt Type 4 isolated PoE PD module, 12 V out',
        datasheet='https://silvertel.com/images/datasheets/Ag5810-datasheet-IEEE802_3bt-Power-over-Ethernet-4-pair-PD.pdf',
        fp=f'{LIB}:Silvertel_Ag5810')
    # Wuerth 7499511001A datasheet rev 004.000 page 2 schematic
    out['RJ45_WE_7499511001A'] = box_symbol('RJ45_WE_7499511001A', 'J',
        [('11', 'D1+', 'passive'), ('10', 'D1-', 'passive'), ('12', 'CD1', 'passive'), ('4', 'D2+', 'passive'),
         ('5', 'D2-', 'passive'), ('6', 'CD2', 'passive'), ('3', 'D3+', 'passive'), ('2', 'D3-', 'passive'),
         ('1', 'CD3', 'passive'), ('8', 'D4+', 'passive'), ('9', 'D4-', 'passive'), ('7', 'CD4', 'passive')],
        [('13', 'V1', 'passive'), ('14', 'V2', 'passive'), ('15', 'V3', 'passive'), ('16', 'V4', 'passive'),
         None, ('SH', 'SHIELD', 'passive')],
        descr='RJ45 1000BASE-T with magnetics, four cable-side centre taps for PoE, 600 mA per tap',
        datasheet='https://www.we-online.com/components/products/datasheet/7499511001A.pdf',
        fp=f'{LIB}:RJ45_Wuerth_7499511001A')
    # Silicon Labs MGM240P datasheet rev 1.0 table 6.1
    L = ['GND', 'PB04', 'PB03', 'PB02', 'PB01', 'PB00', 'PA00', 'PA01', 'PA02', 'PA03', 'PA04', 'PA05', 'PA06', 'GND',
         'VDD', 'PA07', 'PA08', 'PD03', 'PD02', 'PD01', 'PD00', 'PC00', 'GND', 'PC01', 'PC02', 'PC03', 'PC04', 'PC05',
         'PC06', 'PC07', 'RESETn', 'GND', 'RFOUT', 'GND', 'GND', 'GND']
    def mt(n): return 'power_in' if n in ('GND', 'VDD') else ('input' if n == 'RESETn' else ('passive' if n == 'RFOUT' else 'bidirectional'))
    allp = [(str(i + 1), n, mt(n)) for i, n in enumerate(L)]
    out['MGM240P'] = box_symbol('MGM240P', 'U', allp[:18], allp[18:],
        descr='Silicon Labs MGM240P EFR32MG24 multiprotocol 2.4 GHz module (Zigbee, Thread, BLE)',
        datasheet='https://www.silabs.com/documents/public/data-sheets/mgm240p-datasheet.pdf',
        fp=f'{LIB}:SiliconLabs_MGM240P')
    return out

def write_symbol_lib(extra=None):
    body = '\n'.join(dump(s, 1) for s in list(symbols().values()) + list((extra or {}).values()))
    open(os.path.join(HW, f'{LIB}.kicad_sym'), 'w').write(
        f'(kicad_symbol_lib (version 20241209) (generator "tahanan_gen") (generator_version "9.0")\n{body}\n)\n')

# ---------------------------------------------------------------- footprints
def _fp(name, descr, attr, body):
    hdr = (f'(footprint "{name}" (version 20241229) (generator "tahanan_gen") (generator_version "9.0") (layer "F.Cu")\n'
           f' (descr "{descr}")\n (attr {attr})\n')
    open(os.path.join(HW, f'{LIB}.pretty', name + '.kicad_mod'), 'w').write(hdr + '\n'.join(' ' + b for b in body) + '\n)\n')

def _txt(x0, y0, x1, y1):
    return [f'(property "Reference" "REF**" (at {(x0 + x1) / 2} {y0 - 1.2} 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
            f'(property "Value" "VAL**" (at {(x0 + x1) / 2} {y1 + 1.2} 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))']

def _rect(x0, y0, x1, y1, layer, w):
    return f'(fp_rect (start {x0} {y0}) (end {x1} {y1}) (stroke (width {w}) (type solid)) (fill no) (layer "{layer}"))'

def _th(n, x, y, drill, pad, shape='circle'):
    return f'(pad "{n}" thru_hole {shape} (at {round(x, 3)} {round(y, 3)}) (size {pad} {pad}) (drill {drill}) (layers "*.Cu" "*.Mask"))'

def _npth(x, y, d):
    return f'(pad "" np_thru_hole circle (at {round(x, 3)} {round(y, 3)}) (size {d} {d}) (drill {d}) (layers "*.Cu" "*.Mask"))'

def write_footprints():
    os.makedirs(os.path.join(HW, f'{LIB}.pretty'), exist_ok=True)
    # --- Silvertel Ag5810, datasheet V1.2 figure 16. Origin = body centre, body 69.98 x 30.
    W, H = 69.98, 30.0
    b = _txt(-W / 2, -H / 2, W / 2, H / 2)
    xl = -W / 2 + 2.0; xr = xl + 66.04
    for n in range(1, 7):                       # input pins 1..6, pin 1 is 9.86 below top edge
        b.append(_th(n, xl, -H / 2 + 9.86 + (n - 1) * 2.54, 1.1, 1.9, 'rect' if n == 1 else 'circle'))
    for n in range(7, 14):                      # output pins 13 (top, 7.32 below edge) .. 7
        b.append(_th(n, xr, -H / 2 + 7.32 + (13 - n) * 2.54, 1.1, 1.9))
    b += [_npth(-W / 2 + 2.49, -H / 2 + 2.49, 3.2), _npth(-W / 2 + 2.49 + 65, H / 2 - 2.49, 3.2)]  # two fixing holes
    b += [_rect(-W / 2, -H / 2, W / 2, H / 2, 'F.Fab', 0.1), _rect(-W / 2 - .12, -H / 2 - .12, W / 2 + .12, H / 2 + .12, 'F.SilkS', 0.12),
          _rect(-W / 2 - .5, -H / 2 - .5, W / 2 + .5, H / 2 + .5, 'F.CrtYd', 0.05)]
    _fp('Silvertel_Ag5810', 'Silvertel Ag5810 60W 802.3bt PD module, 70x30mm DIL, datasheet V1.2 fig.16. Keep copper and parts clear under the isolation barrier (fig.14).', 'through_hole', b)

    # --- Wuerth 7499511001A, datasheet 004.000 "Recommended Hole Pattern" (top view).
    # Origin = centre of the jack front face; the jack opening faces +Y. yf = distance behind the front face.
    b = _txt(-8.3, -32.8, 8.3, 0)
    P = lambda x, yf: (x, -yf)
    post = 10.9
    rowA = post + 15.24          # pins 1..6, pitch 2.03, pin 6 at left
    rowB = post + 17.78          # pins 7..12, 12 at left, 4.06 gap in the middle
    for i, n in enumerate(range(6, 0, -1)):
        b.append(_th(n, *P(-5.075 + i * 2.03, rowA), 0.9, 1.5, 'rect' if n == 1 else 'circle'))
    for n, x in zip((12, 11, 10, 9, 8, 7), (-6.09, -4.06, -2.03, 2.03, 4.06, 6.09)):
        b.append(_th(n, *P(x, rowB), 0.9, 1.5))
    for n, x, d in ((14, -5.59, 8.12), (16, -5.59, 6.66), (13, 5.59, 8.12), (15, 5.59, 6.66)):
        b.append(_th(n, *P(x, post + d), 0.9, 1.2))
    b += [_npth(*P(-6.35, post), 2.8), _npth(*P(6.35, post), 2.8)]
    for x in (-8.065, 8.065):
        b.append(_th('SH', *P(x, post - 3.18), 1.6, 2.6))
    b += [_rect(-8.3, -32.8, 8.3, 0, 'F.Fab', 0.1), _rect(-8.42, -32.92, 8.42, 0.12, 'F.SilkS', 0.12), _rect(-9.6, -33.3, 9.6, 0.5, 'F.CrtYd', 0.05)]
    _fp('RJ45_Wuerth_7499511001A', 'Wuerth WE-RJ45LAN HPLE 7499511001A, 1000BASE-T, PoE 600mA per centre tap, THT, tab down', 'through_hole', b)

    # --- Silicon Labs MGM240P, datasheet rev 1.0 figure 8.3; cross-checked against the
    # SparkFun Thing Plus MGM240P production footprint. Origin = module centre, antenna end at -Y.
    b = _txt(-6.45, -7.5, 6.45, 7.5)
    smd = lambda n, x, y, sx, sy: f'(pad "{n}" smd roundrect (at {round(x, 3)} {round(y, 3)}) (size {sx} {sy}) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25))'
    for n in range(1, 15):
        b.append(smd(n, -5.65, -6.8 + (n - 1), 2.4, 0.6))
    for n in range(15, 23):
        b.append(smd(n, -3.5 + (n - 15), 6.7, 0.6, 2.4))
    for n in range(23, 37):
        b.append(smd(n, 5.65, 6.2 - (n - 23), 2.4, 0.6))
    b += [_rect(-6.45, -7.5, 6.45, 7.5, 'F.Fab', 0.1), _rect(-7.35, -8.0, 7.35, 8.4, 'F.CrtYd', 0.05),
          '(fp_circle (center -7.9 -7.6) (end -7.75 -7.6) (stroke (width 0.3) (type solid)) (fill no) (layer "F.SilkS"))']
    _fp('SiliconLabs_MGM240P', 'Silicon Labs MGM240P module 12.9x15.0mm, 36 pads, datasheet fig 8.3. Built-in antenna variants need the 8.8x4.8mm copper keep-out at the antenna end.', 'smd', b)

if __name__ == '__main__':
    write_symbol_lib(); write_footprints(); print('custom library written')
