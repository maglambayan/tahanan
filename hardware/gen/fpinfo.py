import json, os, sys, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
STOCK = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'
d = json.load(open(os.path.join(HERE, 'design.json')))
out = {}
for fp in sorted({p['fp'] for p in d['parts']}):
    l, n = fp.split(':')
    path = os.path.join(HERE, '..', l + '.pretty') if l == 'tahanan' else f'{STOCK}/{l}.pretty'
    f = pcbnew.FootprintLoad(path, n)
    def box(layer):
        xs = []; ys = []
        for g in f.GraphicalItems():
            if g.GetLayer() == layer:
                b = g.GetBoundingBox(); xs += [b.GetLeft(), b.GetRight()]; ys += [b.GetTop(), b.GetBottom()]
        return [round(pcbnew.ToMM(v), 2) for v in (min(xs), min(ys), max(xs), max(ys))] if xs else None
    px = [pcbnew.ToMM(p.GetPosition().x) for p in f.Pads()]; py = [pcbnew.ToMM(p.GetPosition().y) for p in f.Pads()]
    out[fp] = dict(crt=box(pcbnew.F_CrtYd), fab=box(pcbnew.F_Fab), pads=[round(min(px), 2), round(min(py), 2), round(max(px), 2), round(max(py), 2)], npads=len(px),
                   p1=[round(pcbnew.ToMM(v), 2) for v in f.Pads()[0].GetPosition()], tht=any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in f.Pads()))
json.dump(out, open(os.path.join(HERE, 'fpinfo.json'), 'w'), indent=1)
for k, v in out.items():
    if v['npads'] > 3 or 'Conn' in k or 'SW' in k or 'Batt' in k or 'L_' in k or 'CP_' in k: print(k.split(':')[1][:55].ljust(56), 'crt', v['crt'], 'fab', v['fab'], 'p1', v['p1'])
