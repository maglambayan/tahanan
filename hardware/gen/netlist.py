"""Tiny netlist DSL. design.py describes the circuit with it; schgen.py and pcbgen.py consume it."""
import json, os, re
import kisym, customlib

HERE = os.path.dirname(os.path.abspath(__file__))
IDX = None
def _index():
    global IDX
    if IDX is None:
        IDX = {}
        import glob
        for f in sorted(glob.glob(kisym.SYMDIR + '/*.kicad_sym')):
            l = os.path.basename(f)[:-10]
            for m in re.finditer(r'^\t\(symbol "([^"]+)"', open(f).read(), re.M):
                IDX.setdefault(m.group(1), l)
    return IDX

CUSTOM = customlib.symbols()
EXTRA = {}
PARTS = []; COUNT = {}; SHEET = ['root']; NOTES = {}

class Part:
    pass

def sheet(name, title, note=''):
    SHEET[0] = name; NOTES[name] = [title, note]

def symdef(symbol):
    if ':' in symbol:
        l, s = symbol.split(':')
    else:
        s = symbol; l = customlib.LIB if s in CUSTOM else _index()[s]
    sx = CUSTOM[s] if l == customlib.LIB else kisym.resolve(l, s)
    return l, s, sx

def part(prefix, symbol, nets, value=None, fp=None, mpn='', mfr='', desc='', dnp=False, alt='', types=None, ref=None):
    """nets: {pin name or number: net name or 'NC'}. Pins left out get a no-connect flag
    only if listed as 'NC'; otherwise that is an error, so nothing is left floating by accident."""
    l, s, sx = symdef(symbol)
    p = Part(); p.lib, p.sym, p.sx = l, s, sx
    if not ref: COUNT[prefix] = COUNT.get(prefix, 0) + 1
    p.ref = ref or f'{prefix}{COUNT[prefix]}'
    if p.ref in {x.ref for x in PARTS}: raise ValueError(f'duplicate reference {p.ref}')
    p.value = value or s; p.fp = fp or kisym.prop(sx, 'Footprint'); p.mpn = mpn; p.mfr = mfr
    p.desc = desc or kisym.prop(sx, 'Description'); p.dnp = dnp; p.alt = alt; p.sheet = SHEET[0]
    p.datasheet = kisym.prop(sx, 'Datasheet'); p.types = types or {}
    if types:
        # electrical-type corrections live in a project copy of the symbol, never in the stock library name
        for u in kisym.find(sx, 'symbol'):
            for pin in kisym.find(u, 'pin'):
                if kisym.get(pin, 'name')[1] in types: pin[1] = kisym.Sym(types[kisym.get(pin, 'name')[1]])
        p.lib = l = customlib.LIB; EXTRA[s] = sx
    p.pins = kisym.pins_of(sx); p.net = {}
    names = {}
    for pin in p.pins:
        names.setdefault(pin['name'], []).append(pin['num'])
    nums = {pin['num'] for pin in p.pins}
    for k, v in nets.items():
        k = str(k)
        if k in nums: targets = [k]
        elif k in names: targets = names[k]
        else: raise KeyError(f'{p.ref} {symbol}: no pin {k!r}; have {sorted(names)}')
        for t in targets:
            p.net[t] = v
    for pin in p.pins:
        if pin['num'] not in p.net:
            if pin['type'] == 'no_connect': p.net[pin['num']] = 'NC'
            else: raise KeyError(f"{p.ref} {symbol}: pin {pin['num']} ({pin['name']}) not assigned")
    if not p.fp: raise ValueError(f'{p.ref}: no footprint')
    pads = kisym.fp_pads(p.fp)
    missing = {n for n in nums if n not in pads}
    if missing: raise ValueError(f'{p.ref} {p.fp}: symbol pins without pads: {sorted(missing)}')
    PARTS.append(p)
    return p

SIZES = {'0402': 'Capacitor_SMD:C_0402_1005Metric', '0603': 'Capacitor_SMD:C_0603_1608Metric', '0805': 'Capacitor_SMD:C_0805_2012Metric',
         '1206': 'Capacitor_SMD:C_1206_3216Metric', '1210': 'Capacitor_SMD:C_1210_3225Metric', '1812': 'Capacitor_SMD:C_1812_4532Metric'}
def R(val, a, b, size='0402', mpn='', mfr='Yageo', dnp=False, desc=''):
    if not mpn:
        mpn = {'0402': 'RC0402FR-07', '0603': 'RC0603FR-07', '1206': 'RC1206FR-07'}[size] + rcode(val) + 'L'
    return part('R', 'Device:R', {1: a, 2: b}, val, SIZES[size].replace('Capacitor_SMD:C_', 'Resistor_SMD:R_'), mpn, mfr, desc or f'Resistor {val} 1% {size}', dnp)
def rcode(v):
    v = v.replace('Ω', '')
    if v in ('0', '0R'): return '0R'
    m = re.match(r'^([\d.]+)([RkM]?)$', v); n, u = m.group(1), m.group(2) or 'R'
    return n.replace('.', u) if '.' in n else n + u
def C(val, a, b, size='0402', volt='16V', mpn='', mfr='', dnp=False, diel='X7R'):
    return part('C', 'Device:C', {1: a, 2: b}, f'{val} {volt}', SIZES[size], mpn, mfr, f'MLCC {val} {volt} {diel} {size}', dnp)

def nets():
    """net -> [(ref, pin)], skipping NC."""
    out = {}
    for p in PARTS:
        for num, n in p.net.items():
            if n != 'NC': out.setdefault(n, []).append((p.ref, num))
    return out

def check():
    errs = []
    for n, nodes in nets().items():
        if len(nodes) < 2: errs.append(f'net {n} has a single pin {nodes}')
    return errs
