"""Build tahanan.kicad_pcb: outline, mounting holes, placed footprints with nets, keep-outs.
Run with KiCad's bundled Python (see Makefile). Placement only: the board is NOT routed.
"""
import json, os, sys, uuid, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__)); HW = os.path.join(HERE, '..')
STOCK = os.environ.get('KICAD_FOOTPRINT_DIR', '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
NS = uuid.UUID('6f1d1c5e-7a0b-4f0e-9d53-7461686e616e')
def uid(*a): return str(uuid.uuid5(NS, '/'.join(map(str, a))))
MM = pcbnew.FromMM
W, H, OX, OY = 160.0, 105.0, 40.0, 40.0          # board size and page offset (mm)
def P(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))

D = json.load(open(os.path.join(HERE, 'design.json')))['parts']
BY = {p['ref']: p for p in D}
TITLES = json.load(open(os.path.join(HERE, 'design.json')))['sheets']
def V(prefix): return [p['ref'] for p in D if p['value'].startswith(prefix)][0]
CM5X, CM5Y = 97.0, 8.0                           # top-left corner of the CM5 outline, antenna edge at x+55
# ref: (x, y, rotation, side)
FIXED = {
    'J2': (20.0, 0.0, 180, 'F'),                 # RJ45, opening on the rear edge
    'J5': (44.8, 10.0, 180, 'F'),                # dual USB 3.0
    'J1': (60.0, 3.2, 180, 'F'),                 # USB-C power
    'SW1': (71.5, 4.0, 0, 'F'), 'SW3': (81.5, 4.0, 0, 'F'), 'SW2': (91.5, 4.0, 0, 'F'),
    'J13': (CM5X + 30, CM5Y + 3, 0, 'F'), 'J3': (CM5X + 30, CM5Y + 37, 0, 'F'),
    'H1': (CM5X + 3.5, CM5Y + 3.5, 0, 'F'), 'H2': (CM5X + 51.5, CM5Y + 3.5, 0, 'F'),
    'H3': (CM5X + 3.5, CM5Y + 36.5, 0, 'F'), 'H4': (CM5X + 51.5, CM5Y + 36.5, 0, 'F'),
    'H5': (4.0, 4.0, 0, 'F'), 'H6': (156.0, 4.0, 0, 'F'), 'H7': (4.0, 101.0, 0, 'F'), 'H8': (156.0, 101.0, 0, 'F'),
    V('Ag5810'): (38.0, 67.0, 0, 'F'),                 # Ag5810, input pins on the left
    V('MGM240P Thread'): (17.0, 97.2, 180, 'F'),               # Thread module, antenna on the front edge
    V('MGM240P Zigbee'): (37.0, 95.0, 0, 'F'),                 # Zigbee module, RF pin
    V('Z-Wave module socket'): (58.0, 88.0, 0, 'F'),                 # Z-Wave socket
    'J4': (146.0, 92.0, None, 'B'),              # M.2 on the bottom, SSD extends towards -x
    'H9': (146.0 - 78.0, 92.0, 0, 'B'), 'H10': (146.0 - 40.0, 92.0, 0, 'B'),   # card edge assumed 2.0mm behind the pad centre line: verify against TE 114-115006
    'MK1': (155.0, 72.0, 0, 'B'),                # microphone, bottom side, port through the board
    'SW4': (126.0, 100.2, 180, 'F'),
    V('LTV-817S'): (29.5, 45.0, 0, 'F'),          # optocoupler straddles the isolation barrier
    'D16': (6.3, 11.0, 90, 'F'), 'D17': (6.3, 15.0, 90, 'F'),
    'FID1': (26.5, 91.5, 0, 'F'), 'FID2': (150.0, 3.0, 0, 'F'), 'FID3': (152.0, 62.0, 0, 'B'), 'FID4': (5.0, 88.0, 0, 'B'),
}
# region name: (x0, y0, x1, y1); parts are shelf-packed inside in definition order
REGIONS = {'poe_pri': (1.5, 35.0, 22.0, 51.0), 'poe_out': (75.0, 52.0, 97.0, 83.0), 'eth': (31.0, 27.0, 53.5, 33.5), 'usb': (31.0, 17.5, 53.5, 26.6),
           'pwr_a': (54.0, 9.0, 96.0, 50.5), 'pwr_b': (38.5, 36.5, 53.5, 50.5), 'cm5misc': (98.0, 50.0, 156.0, 57.5), 'audio': (99.0, 58.5, 150.0, 82.5),
           'radio': (26.0, 84.0, 54.0, 86.6), 'radio2': (46.0, 88.0, 54.0, 104.0), 'misc': (73.0, 84.5, 150.0, 92.0), 'front': (66.0, 100.0, 118.0, 104.0)}
def region_of(p):
    r, s, n = p['ref'], p['sheet'], set(p['net'].values())
    if s == 'ethernet_poe':
        if n & {'VPOE_P', 'VPOE_N', 'POE_VIN_P', 'POE_VIN_N', 'POE_OPTO_A', 'POE_T4DET'}: return 'poe_pri'
        if 'V12_POE' in n or 'POE_BT_N' in n: return 'poe_out'
        return 'eth'
    if s == 'storage_usb': return 'cm5misc' if '+3V3_NVME' in n or 'M2_LED_N' in n else 'usb'
    if s == 'power_in': return 'pwr_a'
    if s == 'power_rails': return 'pwr_b' if n & {'+3V3', '+1V8', 'SW_3V3', 'BST_3V3'} and not n & {'VIN'} and r[0] != 'T' else 'pwr_a'
    if s == 'cm5':
        if r.startswith(('TP', 'BT', 'J')): return 'misc' if not r.startswith(('BT', 'J7')) or r == 'J6' else 'audio'
        return 'front' if r[0] == 'D' or 'LED' in ''.join(n) else 'cm5misc'
    if s == 'radios': return 'radio2' if r.startswith('J') else 'radio'
    return 'audio'

def load(fpid):
    l, n = fpid.split(':')
    return pcbnew.FootprintLoad(os.path.join(HW, l + '.pretty') if l == 'tahanan' else '%s/%s.pretty' % (STOCK, l), n)

def crt(fp):
    b = None
    for g in fp.GraphicalItems():
        if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            bb = g.GetBoundingBox()
            if b is None: b = bb
            else: b.Merge(bb)
    if b is None: b = fp.GetBoundingBox(False)
    return [pcbnew.ToMM(v) for v in (b.GetLeft(), b.GetTop(), b.GetRight(), b.GetBottom())]

def flip(fp):
    try: fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    except Exception: fp.Flip(fp.GetPosition(), True)

def main():
    board = pcbnew.NewBoard(os.path.join(HW, 'tahanan.kicad_pcb'))
    board.SetCopperLayerCount(4)
    for layer, name in ((pcbnew.In1_Cu, 'In1.GND'), (pcbnew.In2_Cu, 'In2.PWR')): board.SetLayerName(layer, name)
    ds = board.GetDesignSettings(); ds.SetBoardThickness(MM(1.6))
    # outline with 3 mm corner radius
    r = 3.0
    def seg(a, b):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(P(*a)); s.SetEnd(P(*b)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); board.Add(s)
    def arc(c, start, ang):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetCenter(P(*c)); s.SetStart(P(*start)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); board.Add(s)
    seg((r, 0), (W - r, 0)); seg((W, r), (W, H - r)); seg((W - r, H), (r, H)); seg((0, H - r), (0, r))
    arc((r, r), (0, r), 90); arc((W - r, r), (W - r, 0), 90); arc((W - r, H - r), (W, H - r), 90); arc((r, H - r), (r, H), 90)
    # nets
    # Net names come from the netlist KiCad exported from the schematic (gen/tahanan.net), so
    # the board matches the schematic exactly, including KiCad's names for unconnected pins.
    sys.path.insert(0, HERE)
    from sexp import parse, find, get
    t = parse(open(os.path.join(HERE, 'tahanan.net')).read())
    padnet = {}; nets = {}
    for n in find(get(t, 'nets'), 'net'):
        name = get(n, 'name')[1]
        name = name[1:] if name.startswith('/') else name
        ni = pcbnew.NETINFO_ITEM(board, name); board.Add(ni); nets[name] = ni
        for node in find(n, 'node'): padnet[(get(node, 'ref')[1], get(node, 'pin')[1])] = ni
    sheets = {}
    placed = {}; boxes = []
    def add(p, x, y, rot, side):
        fp = load(p['fp']); fp.SetReference(p['ref']); fp.SetValue(p['value']); fp.SetFPIDAsString(p['fp']); board.Add(fp)
        for k, v in (('MPN', p['mpn']), ('Manufacturer', p['mfr']), ('Alternate', p['alt'])):
            fp.SetField(k, v); fp.GetField(k).SetVisible(False)
        for k, v in (('Datasheet', p['datasheet']), ('Description', p['desc'])):
            try: fp.GetField(k).SetText(v)
            except Exception: fp.SetField(k, v); fp.GetField(k).SetVisible(False)
        fp.SetSheetname('/' + TITLES[p['sheet']] + '/'); fp.SetSheetfile(p['sheet'] + '.kicad_sch')
        fp.SetPosition(P(x, y))
        if side == 'B': flip(fp)
        if rot is not None: fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            ni = padnet.get((p['ref'], pad.GetNumber()))
            if ni: pad.SetNet(ni)
        try:
            fp.SetPath(pcbnew.KIID_PATH('/%s/%s' % (uid('sheet', p['sheet']), uid(p['ref'], 1))))
            if p['dnp']: fp.SetDNP(True)
            if not p['mpn']: fp.SetExcludedFromBOM(True)
        except Exception: pass
        if p['ref'][0] in 'RCLDT' or p['ref'][:2] in ('FB', 'FI'): fp.Reference().SetVisible(False)   # refs of small parts live on the Fab layer only
        placed[p['ref']] = fp
        return fp
    for ref, (x, y, rot, side) in FIXED.items():
        fp = add(BY[ref], x, y, rot, side)
        if ref == 'J4':        # choose the rotation that sends the SSD (rear row -> front row) towards -x
            for a in (0, 90, 180, 270):
                fp.SetOrientationDegrees(a)
                pos = {pad.GetNumber(): pad.GetPosition() for pad in fp.Pads()}
                if pos['2'].x < pos['1'].x - MM(5): break
        c = crt(fp); boxes.append((ref, side, c[0] - OX, c[1] - OY, c[2] - OX, c[3] - OY))
    # shelf packing of everything else
    groups = {}
    for p in D:
        if p['ref'] not in FIXED: groups.setdefault(region_of(p), []).append(p)
    report = []
    for name, parts in groups.items():
        x0, y0, x1, y1 = REGIONS[name]; x, y, rowh = x0, y0, 0.0; gap = 0.25
        sized = []
        for p in parts:
            fp = load(p['fp']); c = crt(fp); sized.append((p, c))
        sized.sort(key=lambda t: -(t[1][3] - t[1][1]))
        for p, c in sized:
            w, h = c[2] - c[0], c[3] - c[1]
            if x + w > x1: x = x0; y += rowh + gap; rowh = 0.0
            if y + h > y1: report.append('region %s overflow at %s' % (name, p['ref']))
            fp = add(p, x - c[0], y - c[1], 0, 'F')
            boxes.append((p['ref'], 'F', x, y, x + w, y + h)); x += w + gap; rowh = max(rowh, h)
        report.append('%-8s %3d parts, used to y=%.1f of %.1f' % (name, len(parts), y + rowh, y1))
    # rule areas
    def area(name, x0, y0, x1, y1, tracks):
        z = pcbnew.ZONE(board); z.SetIsRuleArea(True); z.SetZoneName(name); z.SetLayerSet(pcbnew.LSET.AllCuMask())
        z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowVias(tracks); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        o = z.Outline(); o.NewOutline()
        for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)): o.Append(MM(OX + px), MM(OY + py))
        board.Add(z)
    area('CM5 antenna keep-out', CM5X + 46.0, CM5Y + 17.0, W, CM5Y + 34.0, True)
    area('Thread antenna keep-out', 17.0 - 4.4, 97.2 + 2.7, 17.0 + 4.4, H, True)
    area('PoE primary: no planes', 0.0, 0.0, 31.5, 51.5, False)
    area('PoE primary under module input', 0.0, 51.5, 21.8, 83.0, False)
    # ground plane on inner layer 1 (planes are placed now so the split is defined before routing)
    z = pcbnew.ZONE(board); z.SetNet(nets['GND']); z.SetLayer(pcbnew.In1_Cu); z.SetZoneName('GND plane'); z.SetLocalClearance(MM(0.25))
    o = z.Outline(); o.NewOutline()
    for px, py in ((0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)): o.Append(MM(OX + px), MM(OY + py))
    board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(os.path.join(HW, 'tahanan.kicad_pcb'), board)
    json.dump({'board': [W, H], 'boxes': boxes, 'cm5': [CM5X, CM5Y]}, open(os.path.join(HERE, 'placement.json'), 'w'))
    print('\n'.join(report)); print('footprints:', len(board.GetFootprints()))

if __name__ == '__main__':
    main()
