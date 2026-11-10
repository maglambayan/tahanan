"""Generate the hierarchical KiCad schematic from design.py.

Style: every pin carries a global label with its net name (no drawn wires). Parts are
grouped per functional sheet in definition order, so an IC is followed by its passives.
verify.py exports the netlist with kicad-cli and compares it with design.py pin by pin.
"""
import os, uuid, math, json
import design, netlist, kisym, customlib
from sexp import dump, find, get, parse

HW = os.path.join(netlist.HERE, '..')
PROJECT = 'tahanan'
NS = uuid.UUID('6f1d1c5e-7a0b-4f0e-9d53-7461686e616e')
def uid(*a): return str(uuid.uuid5(NS, '/'.join(map(str, a))))
ROOT = uid('root')
PAPER = {'A3': (420, 297), 'A2': (594, 420), 'A1': (841, 594), 'A0': (1189, 841)}
def g(v): return round(round(v / 1.27) * 1.27, 4)
def q(s): return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'

def unit_pins(p):
    """{unit: [pin]} with common (unit 0) pins added to every unit; alternate body styles dropped."""
    units = {}
    for u in find(p.sx, 'symbol'):
        un, style = [int(x) for x in u[1].rsplit('_', 2)[1:]]
        if style > 1: continue
        for pin in find(u, 'pin'):
            at = get(pin, 'at')
            units.setdefault(un, []).append(dict(num=get(pin, 'number')[1], type=str(pin[1]), x=float(at[1]), y=float(at[2]), ang=int(float(at[3]))))
    real = sorted(k for k in units if k) or [1]
    return {k: units.get(k, []) + units.get(0, []) for k in real}

def xf(rot, px, py): return (px, -py) if rot == 0 else (-py, -px)
def outward(rot, ang):
    ox, oy = -round(math.cos(math.radians(ang))), -round(math.sin(math.radians(ang)))
    return (ox, -oy) if rot == 0 else (-oy, -ox)
LBL = {(1, 0): (0, 'left'), (-1, 0): (180, 'right'), (0, -1): (90, 'left'), (0, 1): (270, 'right')}

def layout(parts):
    """Return [(part, unit, X, Y, rot, pins)] and the paper size."""
    cells = []
    for p in parts:
        ups = unit_pins(p)
        for un, pins in ups.items():
            small = len(p.pins) <= 2 and len(ups) == 1
            rot = 90 if (small and len(p.pins) == 2) else 0
            m = {'l': 5.0, 'r': 5.0, 'u': 5.0, 'd': 5.0}; ext = [-3.0, -3.0, 3.0, 3.0]
            for pin in pins:
                sx, sy = xf(rot, pin['x'], pin['y']); ox, oy = outward(rot, pin['ang'])
                ln = len(p.net[pin['num']]) * 1.25 + 8 if p.net[pin['num']] != 'NC' else 4
                ext[0] = min(ext[0], sx + min(0, ox * ln)); ext[2] = max(ext[2], sx + max(0, ox * ln))
                ext[1] = min(ext[1], sy + min(0, oy * ln)); ext[3] = max(ext[3], sy + max(0, oy * ln))
            ext[1] -= 6; ext[3] += 3
            cells.append([p, un, rot, pins, ext, small])
    for paper in ('A3', 'A2', 'A1', 'A0'):
        W, H = PAPER[paper]; x = 15; y = 48; rowh = 0; out = []; ok = True; col = None
        for c in cells:
            p, un, rot, pins, e, small = c
            w, h = e[2] - e[0] + 4, e[3] - e[1] + 2
            if small and col and col[1] + h <= col[2] and abs(col[3] - w) < 40:
                X, Y = col[0], col[1]; col[1] += h; col[3] = max(col[3], w)
            else:
                if col: x = col[0] + col[3]; col = None
                if x + w > W - 12: x = 15; y += rowh; rowh = 0
                X, Y = x, y
                if small: col = [x, y + h, y + max(rowh, 110), w]; rowh = max(rowh, 110)
                else: x += w; rowh = max(rowh, h)
            if Y + h > H - 12: ok = False; break
            out.append((p, un, g(X - e[0]), g(Y - e[1]), rot, pins))
        if ok: return out, paper
    raise RuntimeError('sheet does not fit A0')

def sym_instance(p, un, X, Y, rot, sheet_uuid, lib_id):
    props = [('Reference', p.ref, False), ('Value', p.value, False), ('Footprint', p.fp, True), ('Datasheet', p.datasheet, True), ('Description', p.desc, True),
             ('MPN', p.mpn, True), ('Manufacturer', p.mfr, True), ('Alternate', p.alt, True)]
    s = [f'(symbol (lib_id {q(lib_id)}) (at {X} {Y} {rot}) (unit {un}) (exclude_from_sim no) (in_bom {"yes" if p.mpn else "no"}) (on_board yes) (dnp {"yes" if p.dnp else "no"}) (uuid {q(uid(p.ref, un))})']
    for i, (k, v, hide) in enumerate(props):
        yy = Y - 5.08 if k == 'Reference' else (Y - 3.3 if k == 'Value' else Y)
        if rot == 0 and k in ('Reference', 'Value'):
            ys = [-pin['y'] for pin in unit_pins(p)[un]] or [0]; yy = Y + min(ys) - (6.6 if k == 'Reference' else 4.6)
        s.append(f'(property {q(k)} {q(v)} (at {X} {round(yy, 3)} 0) (effects (font (size 1.27 1.27)){" (hide yes)" if hide else ""}))')
    for pin in p.pins:
        s.append(f'(pin {q(pin["num"])} (uuid {q(uid(p.ref, "pin", pin["num"], un))}))')
    s.append(f'(instances (project {q(PROJECT)} (path {q("/" + ROOT + "/" + sheet_uuid)} (reference {q(p.ref)}) (unit {un}))))')
    return '\n'.join(s) + ')'

def glabel(net, x, y, d, key):
    ang, just = LBL[d]
    return (f'(global_label {q(net)} (shape passive) (at {x} {y} {ang}) (effects (font (size 1.27 1.27)) (justify {just})) (uuid {q(uid("gl", *key))})'
            f' (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes))))')

def embedded(lib, sym, sx):
    import copy
    e = copy.deepcopy(sx); e[1] = f'{lib}:{sym}'
    return dump(e, 2)

def power_flag_nets():
    types = {}
    for p in design.PARTS:
        for pin in p.pins:
            n = p.net[pin['num']]
            if n != 'NC': types.setdefault(n, set()).add(pin['type'])
    return sorted(n for n, t in types.items() if 'power_in' in t and 'power_out' not in t)

def write_sheet(name, parts, sheet_uuid, page):
    title, note = design.NOTES[name]
    placed, paper = layout(parts)
    libs = {}; body = []
    for p, un, X, Y, rot, pins in placed:
        lib_id = f'{p.lib}:{p.sym}'; libs[lib_id] = embedded(p.lib, p.sym, p.sx)
        body.append(sym_instance(p, un, X, Y, rot, sheet_uuid, lib_id))
        seen = set()
        for pin in pins:
            sx, sy = xf(rot, pin['x'], pin['y']); x, y = round(X + sx, 4), round(Y + sy, 4)
            if (x, y) in seen: continue
            seen.add((x, y)); net = p.net[pin['num']]
            if net == 'NC':
                if pin['type'] != 'no_connect': body.append(f'(no_connect (at {x} {y}) (uuid {q(uid("nc", p.ref, pin["num"], un))}))')
            else:
                body.append(glabel(net, x, y, outward(rot, pin['ang']), (p.ref, pin['num'], un)))
    if name == 'power_rails':
        l, s, sx = netlist.symdef('power:PWR_FLAG'); libs['power:PWR_FLAG'] = embedded(l, s, sx)
        W, H = PAPER[paper]
        for i, n in enumerate(power_flag_nets()):
            X, Y = g(20 + i * 22), g(H - 30)
            body.append(f'(symbol (lib_id "power:PWR_FLAG") (at {X} {Y} 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no) (dnp no) (uuid {q(uid("flg", n))})'
                        f' (property "Reference" "#FLG{i + 1:02d}" (at {X} {Y - 5} 0) (effects (font (size 1.27 1.27)) (hide yes))) (property "Value" "PWR_FLAG" (at {X} {Y - 4} 0) (effects (font (size 1.27 1.27))))'
                        f' (property "Footprint" "" (at {X} {Y} 0) (effects (font (size 1.27 1.27)) (hide yes))) (property "Datasheet" "" (at {X} {Y} 0) (effects (font (size 1.27 1.27)) (hide yes)))'
                        f' (pin "1" (uuid {q(uid("flg", n, "p"))})) (instances (project {q(PROJECT)} (path {q("/" + ROOT + "/" + sheet_uuid)} (reference "#FLG{i + 1:02d}") (unit 1)))))')
            body.append(glabel(n, X, Y, (0, 1), ('flg', n)))
    txt = (f'(text {q(title)} (exclude_from_sim no) (at 15 14 0) (effects (font (size 3.5 3.5) (bold yes)) (justify left top)) (uuid {q(uid("t", name))}))\n'
           f'(text {q(note)} (exclude_from_sim no) (at 15 21 0) (effects (font (size 1.8 1.8)) (justify left top)) (uuid {q(uid("n", name))}))')
    out = (f'(kicad_sch (version 20250114) (generator "tahanan_gen") (generator_version "9.0") (uuid {q(sheet_uuid)}) (paper {q(paper)})\n'
           f'(title_block (title {q("Tahanan Hub - " + title)}) (rev "A") (company "Tahanan") (comment 1 "Generated from hardware/gen/design.py"))\n'
           f'(lib_symbols\n' + '\n'.join(libs.values()) + '\n)\n' + txt + '\n' + '\n'.join(body) + '\n)\n')
    open(os.path.join(HW, f'{name}.kicad_sch'), 'w').write(out)
    return paper

def main():
    customlib.write_symbol_lib(netlist.EXTRA); customlib.write_footprints()
    errs = netlist.check()
    if errs: raise SystemExit('\n'.join(errs))
    sheets = list(design.NOTES)
    boxes = []
    for i, name in enumerate(sheets):
        su = uid('sheet', name)
        paper = write_sheet(name, [p for p in design.PARTS if p.sheet == name], su, i + 2)
        x, y = 30 + (i % 4) * 65, 60 + (i // 4) * 45
        boxes.append(f'(sheet (at {x} {y}) (size 50 25) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0)) (uuid {q(su)})'
                     f' (property "Sheetname" {q(design.NOTES[name][0])} (at {x} {y - 0.8} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))'
                     f' (property "Sheetfile" {q(name + ".kicad_sch")} (at {x} {y + 26} 0) (effects (font (size 1.27 1.27)) (justify left top)))'
                     f' (instances (project {q(PROJECT)} (path {q("/" + ROOT)} (page {q(i + 2)})))))')
        print(f'  {name}: {paper}')
    root = (f'(kicad_sch (version 20250114) (generator "tahanan_gen") (generator_version "9.0") (uuid {q(ROOT)}) (paper "A3")\n'
            f'(title_block (title "Tahanan Hub - top level") (rev "A") (company "Tahanan"))\n(lib_symbols)\n'
            f'(text "Tahanan Hub rev A\\nHome Assistant hub: CM5, NVMe, GbE with 802.3bt PoE, USB-C PD, Zigbee, Thread, Z-Wave socket, voice audio.\\n'
            f'All inter-sheet connections are global labels." (exclude_from_sim no) (at 30 25 0) (effects (font (size 2.5 2.5)) (justify left top)) (uuid {q(uid("roottext"))}))\n'
            + '\n'.join(boxes) + '\n(sheet_instances (path "/" (page "1")))\n)\n')
    open(os.path.join(HW, f'{PROJECT}.kicad_sch'), 'w').write(root)
    # Project tables list the project library plus every stock library the design uses, so the
    # project opens and checks cleanly even where no global library table is configured.
    slibs = sorted({p.lib for p in design.PARTS} | {'power'}); flibs = sorted({p.fp.split(':')[0] for p in design.PARTS})
    row = lambda n, uri: f'  (lib (name "{n}")(type "KiCad")(uri "{uri}")(options "")(descr ""))\n'
    open(os.path.join(HW, 'sym-lib-table'), 'w').write('(sym_lib_table\n  (version 7)\n' + ''.join(
        row(n, '${KIPRJMOD}/tahanan.kicad_sym' if n == 'tahanan' else '${KICAD10_SYMBOL_DIR}/%s.kicad_sym' % n) for n in slibs) + ')\n')
    open(os.path.join(HW, 'fp-lib-table'), 'w').write('(fp_lib_table\n  (version 7)\n' + ''.join(
        row(n, '${KIPRJMOD}/tahanan.pretty' if n == 'tahanan' else '${KICAD10_FOOTPRINT_DIR}/%s.pretty' % n) for n in flibs) + ')\n')
    # machine-readable copy of the design for pcbgen.py (runs under KiCad's own Python) and the BOM
    json.dump({'sheets': {k: v[0] for k, v in design.NOTES.items()}, 'parts': [dict(ref=p.ref, value=p.value, fp=p.fp, mpn=p.mpn, mfr=p.mfr, desc=p.desc, alt=p.alt, dnp=p.dnp, sheet=p.sheet, datasheet=p.datasheet,
                              symbol=f'{p.lib}:{p.sym}', net=p.net) for p in design.PARTS]}, open(os.path.join(netlist.HERE, 'design.json'), 'w'), indent=1)
    print(len(design.PARTS), 'parts written')

if __name__ == '__main__':
    main()
