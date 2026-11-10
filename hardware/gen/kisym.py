"""Read symbols from the stock KiCad libraries (pin maps are taken from the
community-verified library instead of being retyped)."""
import os, re, glob, copy, json
from sexp import parse, find, get, Sym
SYMDIR = os.environ.get('KICAD_SYMBOL_DIR', '/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols')
FPDIR = os.environ.get('KICAD_FOOTPRINT_DIR', '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
_cache = {}

def lib(name):
    if name not in _cache:
        t = parse(open(f'{SYMDIR}/{name}.kicad_sym').read())
        _cache[name] = {s[1]: s for s in find(t, 'symbol')}
    return _cache[name]

def resolve(libname, sym):
    """Flattened symbol s-expression ('extends' resolved)."""
    s = lib(libname)[sym]
    e = get(s, 'extends')
    if not e:
        return copy.deepcopy(s)
    p = resolve(libname, e[1])
    p[1] = sym
    for u in find(p, 'symbol'):
        u[1] = u[1].replace(e[1], sym, 1)
    props = {q[1]: q for q in find(s, 'property')}
    have = set()
    for i, q in enumerate(p):
        if isinstance(q, list) and q[0] == 'property' and q[1] in props:
            p[i] = copy.deepcopy(props[q[1]]); have.add(q[1])
    last = max(i for i, q in enumerate(p) if isinstance(q, list) and q[0] == 'property')
    for k, v in props.items():
        if k not in have:
            last += 1; p.insert(last, copy.deepcopy(v))
    for q in s:                      # flags the derived symbol sets itself
        if isinstance(q, list) and q[0] in ('in_bom', 'on_board', 'exclude_from_sim', 'embedded_fonts', 'pin_names', 'pin_numbers'):
            for i, o in enumerate(p):
                if isinstance(o, list) and o[0] == q[0]: p[i] = copy.deepcopy(q)
    return p

def pins_of(symsexp):
    out = []
    for u in find(symsexp, 'symbol'):
        unit = int(u[1].rsplit('_', 2)[1])
        for p in find(u, 'pin'):
            at = get(p, 'at')
            out.append(dict(unit=unit, num=get(p, 'number')[1], name=get(p, 'name')[1], type=str(p[1]),
                            x=float(at[1]), y=float(at[2]), ang=int(float(at[3])) if len(at) > 3 else 0))
    return out

def prop(symsexp, name):
    for q in find(symsexp, 'property'):
        if q[1] == name:
            return q[2]
    return ''

def fp_pads(fpid):
    """Pad names of a footprint 'Lib:Name' (stock library or project library)."""
    l, n = fpid.split(':')
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    for base in (os.path.join(here, f'{l}.pretty'), f'{FPDIR}/{l}.pretty'):
        f = os.path.join(base, n + '.kicad_mod')
        if os.path.exists(f):
            return set(re.findall(r'\(pad "([^"]*)"', open(f).read()))
    raise FileNotFoundError(fpid)
