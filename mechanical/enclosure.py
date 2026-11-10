"""Tahanan Hub enclosure, generated around the PCB placement (hardware/gen/placement.json).

Two printed/moulded shells split at the PCB top surface, so every rear connector drops into an
open notch in the lid. Four M3 screws pass through base pillars and the PCB into heat-set
inserts in the lid pillars, clamping the board. Run:  python enclosure.py   (needs cadquery)
"""
import json, os
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
PL = json.load(open(os.path.join(HERE, '..', 'hardware', 'gen', 'placement.json')))
BW, BH = PL['board']; BOX = {b[0]: b for b in PL['boxes']}
T = 1.6                       # PCB thickness
WALL, FLOOR, GAP = 2.4, 2.4, 1.0
UNDER = 6.5                   # PCB underside to floor: M.2 socket + SSD + 1.5 mm thermal pad
OVER = 18.0                   # PCB top to ceiling: PoE module 14.1, USB stack 15.7
Z_PCB = FLOOR + UNDER; Z_TOP = Z_PCB + T; Z_CEIL = Z_TOP + OVER; Z_OUT = Z_CEIL + WALL
HOLES = [(4, 4), (BW - 4, 4), (4, BH - 4), (BW - 4, BH - 4)]
def xy(x, y): return (x, -y)  # PCB coordinates (y towards the front) -> CAD
X0, X1, Y0, Y1 = -GAP - WALL, BW + GAP + WALL, -(BH + GAP + WALL), GAP + WALL
CX, CY = (X0 + X1) / 2, (Y0 + Y1) / 2; LX, LY = X1 - X0, Y1 - Y0

def shell(z0, z1, open_top):
    outer = cq.Workplane('XY').workplane(offset=z0).center(CX, CY).rect(LX, LY).extrude(z1 - z0).edges('|Z').fillet(6.0)
    zc0, zc1 = (z0 + FLOOR, z1 + 1) if open_top else (z0 - 1, z1 - WALL)
    inner = cq.Workplane('XY').workplane(offset=zc0).center(CX, CY).rect(LX - 2 * WALL, LY - 2 * WALL).extrude(zc1 - zc0).edges('|Z').fillet(3.6)
    return outer.cut(inner)
def cyl(x, y, z0, z1, d): return cq.Workplane('XY').workplane(offset=z0).center(*xy(x, y)).circle(d / 2).extrude(z1 - z0)
def box(x0, y0, x1, y1, z0, z1): return cq.Workplane('XY').workplane(offset=z0).center((x0 + x1) / 2, -(y0 + y1) / 2).rect(abs(x1 - x0), abs(y1 - y0)).extrude(z1 - z0)
def slots(x0, y0, x1, y1, z0, z1, pitch=5.0, w=2.0):
    s = None; x = x0
    while x + w <= x1:
        b = box(x, y0, x + w, y1, z0, z1).edges('|Z').fillet(0.9); s = b if s is None else s.union(b); x += pitch
    return s

def base():
    b = shell(0, Z_TOP, True)
    for x, y in HOLES:                                   # pillars carry the PCB; screw enters from below
        b = b.union(cyl(x, y, 0, Z_PCB, 8.0))
    for x, y in HOLES:
        b = b.cut(cyl(x, y, -1, Z_PCB + 1, 3.4)).cut(cyl(x, y, -1, 3.2, 6.4))
    for x, y in ((40, 30), (120, 30), (40, 75)):         # mid supports clear of bottom-side parts
        b = b.union(cyl(x, y, 0, Z_PCB, 5.0))
    b = b.cut(slots(8, 54, 70, 80, -1, FLOOR + 1))        # intake under the PoE module
    b = b.cut(slots(100, 12, 150, 44, -1, FLOOR + 1))     # intake under the CM5
    b = b.union(box(66, 81.5, 146, 102.5, FLOOR, FLOOR + 1.0))   # raised land for the SSD thermal pad
    for x, y in ((12, 12), (BW - 12, 12), (12, BH - 12), (BW - 12, BH - 12)):
        b = b.cut(cyl(x, y, -1, 1.0, 10.5))               # rubber foot recesses
    return b

def lid():
    l = shell(Z_TOP, Z_OUT, False)
    for x, y in HOLES:                                   # pillars press on the PCB, M3 heat-set insert at the tip
        l = l.union(cyl(x, y, Z_TOP, Z_CEIL, 8.0)).cut(cyl(x, y, Z_TOP - 1, Z_TOP + 7.0, 4.0))
    rear = lambda xa, xb, h: box(xa, -GAP - WALL - 1, xb, 1.5, Z_TOP - 1, Z_TOP + h)
    j2, j5, j1 = BOX['J2'], BOX['J5'], BOX['J1']
    l = l.cut(rear(20 - 8.8, 20 + 8.8, 14.3))             # RJ45, panel cut-out 17.55 x 14.25 (Wuerth drawing)
    l = l.cut(rear((j5[2] + j5[4]) / 2 - 7.9, (j5[2] + j5[4]) / 2 + 7.9, 16.3))   # dual USB 3.0
    l = l.cut(rear(60 - 4.9, 60 + 4.9, 3.9).edges('|Y').fillet(1.2))            # USB-C
    for ref in ('SW1', 'SW2', 'SW3'):                    # button plungers
        bx = BOX[ref]; l = l.cut(cyl((bx[2] + bx[4]) / 2, (bx[3] + bx[5]) / 2, Z_CEIL - 1, Z_OUT + 1, 6.0))
    l = l.cut(slots(100, 12, 150, 44, Z_CEIL - 1, Z_OUT + 1))        # exhaust over the CM5 heat sink
    l = l.cut(slots(8, 56, 70, 78, Z_CEIL - 1, Z_OUT + 1))           # exhaust over the PoE module
    for y in (52.0, 62.0):                               # RP-SMA bulkheads: Zigbee, optional Wi-Fi
        l = l.cut(cq.Workplane('YZ').workplane(offset=BW - 1).center(-y, Z_TOP + 10.0).circle(3.3).extrude(GAP + WALL + 3))
    mk = BOX['MK1']; mx, my = (mk[2] + mk[4]) / 2, (mk[3] + mk[5]) / 2
    l = l.union(cyl(mx, my, Z_TOP + 0.6, Z_CEIL, 6.0)).cut(cyl(mx, my, Z_TOP, Z_OUT + 1, 1.6))   # acoustic tube, 0.6 mm gasket at the PCB
    sx, sy = 122.0, 80.0                                 # 40 mm speaker firing upwards
    grille = None
    for i in range(-3, 4):
        for j in range(-3, 4):
            if i * i + j * j <= 10:
                h = cyl(sx + i * 5.0, sy + j * 5.0, Z_CEIL - 1, Z_OUT + 1, 2.6); grille = h if grille is None else grille.union(h)
    ring = cyl(sx, sy, Z_CEIL - 3.0, Z_CEIL, 44.0).cut(cyl(sx, sy, Z_CEIL - 4.0, Z_CEIL + 1, 40.4))
    l = l.union(ring).cut(grille)
    sw = BOX['SW4']; l = l.cut(box((sw[2] + sw[4]) / 2 - 5.5, (sw[3] + sw[5]) / 2 - 2.2, (sw[2] + sw[4]) / 2 + 5.5, (sw[3] + sw[5]) / 2 + 2.2, Z_CEIL - 1, Z_OUT + 1))
    for ref, b in BOX.items():                            # light holes above the front status LEDs
        if ref[0] == 'D' and b[3] > 95: l = l.cut(cyl((b[2] + b[4]) / 2, (b[3] + b[5]) / 2, Z_CEIL - 1, Z_OUT + 1, 2.4))
    for dx, dy in ((-16, -16), (16, -16), (-16, 16), (16, 16)):      # optional 40 mm fan, 32 mm hole pitch, over the CM5
        l = l.cut(cyl(125 + dx, 28 + dy, Z_CEIL - 1, Z_OUT + 1, 3.4))
    return l

def plunger():        # one per push button: sits on the tact switch (2.5 mm tall), flange keeps it captive
    return cq.Workplane('XY').circle(4.2).extrude(1.2).faces('>Z').workplane().circle(2.8).extrude(OVER - 2.5 - 1.2 + WALL + 0.8)
def slider():         # extends the mute slide switch through the lid
    return cq.Workplane('XY').rect(7.0, 3.6).extrude(OVER - 3.5 + WALL + 1.5).faces('<Z').workplane().rect(2.2, 1.6).cutBlind(-2.0)

def keepouts():
    """Coarse solids for the tall parts, used only for the interference check and the assembly view."""
    tall = {'J2': 13.6, 'J5': 15.7, 'J1': 3.3, 'J11': 13.0, 'BT1': 5.0, 'J12': 6.0, 'J7': 8.6, 'SW1': 2.5, 'SW2': 2.5, 'SW3': 2.5, 'SW4': 3.5}
    k = box(0, 0, BW, BH, Z_PCB, Z_TOP).edges('|Z').fillet(3.0)
    for x, y in HOLES: k = k.cut(cyl(x, y, Z_PCB - 1, Z_TOP + 1, 3.2))
    for ref, b in BOX.items():
        h = tall.get(ref, 14.1 if b[4] - b[2] > 60 else (10.5 if ref[0] == 'C' and b[4] - b[2] > 12 else (4.0 if ref[0] == 'L' else None)))
        shrink = 1.5 if ref in ('J2', 'J5', 'J1') else 0.0      # courtyard is wider than the connector body
        if h and b[1] == 'F': k = k.union(box(max(b[2], -3) + shrink, max(b[3], -1.9), b[4] - shrink, b[5], Z_TOP, Z_TOP + h))
    cx, cy = PL['cm5']; k = k.union(box(cx, cy, cx + 55, cy + 40, Z_TOP + 3.0, Z_TOP + 3.0 + 1.24 + 2.4 + 10.0))   # CM5 + 10 mm heat sink
    k = k.union(box(66, 81, 146, 103, Z_PCB - 5.0, Z_PCB - 1.4))                                               # M.2 2280 SSD on the bottom
    return k

if __name__ == '__main__':
    out = os.path.join(HERE, 'out'); os.makedirs(out, exist_ok=True)
    parts = {'tahanan-base': base(), 'tahanan-lid': lid(), 'tahanan-button-plunger': plunger(), 'tahanan-mute-slider': slider()}
    for name, p in parts.items():
        for ext in ('step', 'stl', '3mf'):
            cq.exporters.export(p, os.path.join(out, '%s.%s' % (name, ext)))
        bb = p.val().BoundingBox(); print('%-24s %.1f x %.1f x %.1f mm, volume %.1f cm3' % (name, bb.xlen, bb.ylen, bb.zlen, p.val().Volume() / 1000))
    k = keepouts()
    asm = cq.Assembly()
    asm.add(parts['tahanan-base'], name='base', color=cq.Color(0.85, 0.85, 0.82)); asm.add(parts['tahanan-lid'], name='lid', color=cq.Color(0.95, 0.95, 0.93, 0.5))
    asm.add(k, name='pcb_keepout', color=cq.Color(0.1, 0.45, 0.2)); asm.save(os.path.join(out, 'tahanan-assembly.step'))
    for name in ('tahanan-base', 'tahanan-lid'):
        v = parts[name].intersect(k).val().Volume()
        print('interference %s vs PCB assembly: %.1f mm3' % (name, v))
    print('outer size %.1f x %.1f x %.1f mm' % (LX, LY, Z_OUT))
    for name, view in (('tahanan-lid', (1, -1, 1.2)), ('tahanan-base', (1, -1, 1.2))):
        cq.exporters.export(parts[name], os.path.join(out, name + '.svg'), opt={'projectionDir': view, 'showAxes': False, 'width': 900, 'height': 600, 'showHidden': False})
