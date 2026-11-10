"""Export the netlist from the generated schematic with kicad-cli and compare it,
pin by pin, with design.py. Any transform or labelling error in schgen.py shows up here."""
import os, subprocess, sys, tempfile
import design, netlist
from sexp import parse, find, get

HW = os.path.join(netlist.HERE, '..')
def main():
    tmp = os.path.join(tempfile.mkdtemp(), 'tahanan.net')
    subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', tmp, os.path.join(HW, 'tahanan.kicad_sch')],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t = parse(open(tmp).read())
    got = {}
    for n in find(get(t, 'nets'), 'net'):
        name = get(n, 'name')[1].lstrip('/')
        for node in find(n, 'node'):
            got[(get(node, 'ref')[1], get(node, 'pin')[1])] = name
    comps = {get(c, 'ref')[1]: get(c, 'footprint')[1] for c in find(get(t, 'components'), 'comp')}
    bad = 0
    for p in design.PARTS:
        if not p.pins: continue
        if comps.get(p.ref) != p.fp: print('footprint mismatch', p.ref, comps.get(p.ref), p.fp); bad += 1
        for num, net in p.net.items():
            k = got.get((p.ref, num), '')
            if net == 'NC':
                if k and not k.startswith('unconnected-'): print(f'{p.ref}.{num}: expected no-connect, schematic has {k}'); bad += 1
            elif k != net:
                print(f'{p.ref}.{num}: design {net}, schematic {k!r}'); bad += 1
    extra = set(r for r, _ in got) - {p.ref for p in design.PARTS}
    if extra: print('unexpected refs', sorted(extra)); bad += 1
    print(f'netlist check: {len(got)} pins in schematic, {sum(len(p.net) for p in design.PARTS)} in design, {bad} mismatches')
    return bad
if __name__ == '__main__':
    sys.exit(1 if main() else 0)
