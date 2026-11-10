"""Write the bill of materials (manufacturing/bom/). Prices are budgetary estimates entered by hand
on 2026-11-10 for 1k-piece quantities; they are NOT distributor quotes. Supplier columns are search
links built from the manufacturer part number so stock and price can be confirmed before ordering."""
import csv, json, os, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', '..', 'manufacturing', 'bom'); os.makedirs(OUT, exist_ok=True)
D = json.load(open(os.path.join(HERE, 'design.json')))['parts']
EST = {'Ag5810': 31.0, '7499511001A': 6.8, 'MGM240PA32VNN3': 9.2, 'MGM240PA32VNA3': 9.2, 'TLV320AIC3100IRHBR': 3.3, 'STUSB4500QTR': 2.3, 'LMR33640ADDAR': 2.1,
       'LMR33630ADDAR': 1.8, 'LM74700QDBVRQ1': 0.95, 'CSD17581Q3A': 0.48, 'DMP3013SFV-7': 0.46, 'AP63203WU-7': 0.36, 'AP2112K-1.8TRG1': 0.12, 'TPS2561DRCR': 1.35,
       'TPD4E05U06DQAR': 0.26, 'TPD2EUSB30DRTR': 0.30, 'USBLC6-2SC6': 0.20, 'IM73A135V01XTSA1': 1.65, 'LTV-817S': 0.12, 'ECS-2520MV-122.8-BN-TR': 0.95,
       'DF40HC(3.0)-100DS-0.4V(51)': 1.45, '2199119-4': 1.25, '48406-0001': 1.9, 'USB4105-GF-A': 0.72, 'SRP1038C-100M': 0.92, 'SRP1038C-6R8M': 0.92, 'SRN4018-4R7M': 0.28,
       'EEE-FT1C102AP': 0.62, 'EEE-FT1V101AP': 0.33, 'T520B157M006ATE070': 0.95, '9774030151R': 0.55, '9774025243R': 0.50, 'PMEG10020ELRX': 0.11, 'SMAJ58A': 0.12,
       'SMAJ22A': 0.12, 'BZT52C10S-7-F': 0.03, 'FBMH3225HM102NT': 0.14, 'BLM18PG221SN1D': 0.03, 'BLM21PG221SN1D': 0.04, 'PTS636SM25FSMTRLFS': 0.11, 'JS102011SAQN': 0.42,
       '3000': 0.55, 'SM04B-SRSS-TB': 0.22, '61300311121': 0.08, 'U.FL-R-SMT-1(80)': 0.38, 'SSW-105-01-G-D': 0.85, 'S2B-PH-K-S': 0.06, 'C1812C472KGRACTU': 0.38,
       'CL32B106KBJNNNE': 0.16, 'CL21A226MPQNNNE': 0.05, 'CL31B106KAHNNNE': 0.07}
def est(p):
    if p['mpn'] in EST: return EST[p['mpn']]
    r = p['ref'].rstrip('0123456789')
    return {'R': 0.003, 'C': 0.008, 'D': 0.03}.get(r, 0.05)
def links(mpn):
    q = urllib.parse.quote(mpn)
    return ('https://www.digikey.com/en/products/result?keywords=' + q, 'https://www.mouser.com/c/?q=' + q, 'https://www.lcsc.com/search?q=' + q)
groups = {}
for p in D:
    if not p['mpn'] and not p['dnp']: continue                       # test pads, mounting holes, fiducials: PCB features
    k = (p['mpn'], p['value'], p['fp'], p['dnp'])
    groups.setdefault(k, []).append(p)
def refkey(r):
    import re; m = re.match(r'([A-Z]+)(\d+)(.*)', r); return (m.group(1), int(m.group(2)), m.group(3))
rows = []; total = 0.0
for (mpn, value, fp, dnp), ps in sorted(groups.items(), key=lambda kv: refkey(sorted((p['ref'] for p in kv[1]), key=refkey)[0])):
    refs = sorted((p['ref'] for p in ps), key=refkey); p = ps[0]; u = 0.0 if dnp else est(p); total += u * len(ps)
    dk, mo, lc = links(mpn) if mpn else ('', '', '')
    rows.append([' '.join(refs), len(ps), value, p['desc'], p['mfr'], mpn, fp.split(':')[1], 'DNP' if dnp else 'fit', p['alt'], '%.3f' % u, '%.2f' % (u * len(ps)), dk, mo, lc, p['datasheet']])
hdr = ['References', 'Qty', 'Value', 'Description', 'Manufacturer', 'MPN', 'Footprint', 'Fit', 'Alternates', 'Est. unit USD @1k', 'Est. ext USD', 'DigiKey search', 'Mouser search', 'LCSC search', 'Datasheet']
with open(os.path.join(OUT, 'tahanan-pcba-bom.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(hdr); w.writerows(rows)
SYSTEM = [  # item, qty, manufacturer, MPN, description, est. USD, note
    ['Compute module', 1, 'Raspberry Pi', 'CM5104000', 'Compute Module 5, 4GB RAM, Lite (no eMMC), wireless', 60.0, 'CM5108000 (8GB) is a drop-in option'],
    ['NVMe SSD', 1, 'any', 'M.2 2280 or 2242 NVMe, single-sided preferred', 'Primary storage, PCIe Gen 2 x1', 30.0, 'not shipped in the base SKU if sold bare'],
    ['CM5 heat sink', 1, 'Raspberry Pi', 'SC1869 (CM5 passive cooler)', 'Aluminium passive cooler for CM5', 5.0, 'confirm height under 10 mm'],
    ['Thermal pad', 1, 'Bergquist / Laird', '1.5 mm, 3 W/mK, 20 x 70 mm', 'SSD to base thermal land', 0.8, ''],
    ['Speaker', 1, 'PUI Audio / CUI', '40 mm, 4 ohm, 3 W, depth <= 10 mm, JST PH lead', 'Voice response speaker', 2.5, 'select and confirm acoustically'],
    ['Zigbee antenna', 1, 'any', '2.4 GHz RP-SMA dipole, 2-3 dBi, antenna listed in the MGM240P grant', 'External Zigbee antenna', 1.2, 'certification depends on antenna type and gain'],
    ['RF pigtail', 1, 'any', 'U.FL to RP-SMA bulkhead, 1.13 mm coax, 150 mm', 'Zigbee antenna lead', 1.0, ''],
    ['Coin cell', 1, 'Panasonic', 'CR1220', 'RTC backup', 0.3, ''],
    ['Screw', 4, 'any', 'M3 x 25 pan head', 'Enclosure and PCB clamp', 0.03, ''],
    ['Heat-set insert', 4, 'any', 'M3 x 5.7, brass', 'Lid pillars', 0.05, ''],
    ['Screw', 4, 'any', 'M2.5 x 5', 'CM5 to spacers', 0.02, ''],
    ['Screw', 1, 'any', 'M2 x 3 wafer head', 'SSD retention', 0.02, ''],
    ['Rubber foot', 4, '3M', 'SJ5302 (10 mm)', 'Base feet', 0.05, ''],
    ['Enclosure base', 1, 'custom', 'mechanical/out/tahanan-base.step', 'PC/ABS V-0, moulded or printed', 2.5, ''],
    ['Enclosure lid', 1, 'custom', 'mechanical/out/tahanan-lid.step', 'PC/ABS V-0, moulded or printed', 3.0, ''],
    ['Button plunger', 3, 'custom', 'mechanical/out/tahanan-button-plunger.step', '', 0.1, ''],
    ['Mute slider', 1, 'custom', 'mechanical/out/tahanan-mute-slider.step', '', 0.1, ''],
    ['Bare PCB', 1, 'custom', 'tahanan rev A, 160 x 105 mm, 4 layer, 1.6 mm, ENIG', 'see docs/pcb-layout-guide.md', 4.5, 'after routing'],
    ['Z-Wave module (option)', 1, 'Aeotec / Zooz', 'Z-Pi 800 / ZAC93 800 GPIO', 'Region-specific Z-Wave 800 controller on J11', 30.0, 'optional SKU'],
    ['Fan (option)', 1, 'any', '40 x 40 x 10 mm, 5 V PWM, JST-SH 4-pin (Pi 5 pinout)', 'Needed for sustained full load', 3.0, 'optional SKU'],
]
with open(os.path.join(OUT, 'tahanan-system-bom.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Item', 'Qty', 'Manufacturer', 'MPN / specification', 'Description', 'Est. unit USD', 'Note']); w.writerows(SYSTEM)
sys_total = sum(r[1] * r[5] for r in SYSTEM if 'option' not in r[0] and r[0] != 'NVMe SSD')
print('PCBA BOM: %d lines, %d fitted parts, estimated parts cost USD %.2f' % (len(rows), sum(r[1] for r in rows if r[7] == 'fit'), total))
print('System items excluding SSD and options: USD %.2f' % sys_total)
