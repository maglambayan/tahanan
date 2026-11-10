"""Summarise DRC as JSON and gate fabrication output on a clean, fully routed board."""
import collections, json, os, subprocess, sys, tempfile
HW = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
tmp = os.path.join(tempfile.mkdtemp(), 'drc.json')
subprocess.run(['kicad-cli', 'pcb', 'drc', '--severity-all', '--schematic-parity', '--format', 'json', '-o', tmp, os.path.join(HW, 'tahanan.kicad_pcb')],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
d = json.load(open(tmp))
c = collections.Counter((v['severity'], v['type']) for v in d.get('violations', []))
errors = sum(n for (s, _), n in c.items() if s == 'error')
unconnected = len(d.get('unconnected_items', [])); parity = len(d.get('schematic_parity', []))
print('DRC: %d errors, %d warnings, %d unconnected, %d schematic parity issues' % (errors, sum(c.values()) - errors, unconnected, parity))
for (s, t), n in c.most_common(): print('  %4d %-7s %s' % (n, s, t))
if '--verbose' in sys.argv:
    for v in d.get('violations', []):
        if v['severity'] == 'error': print('   ', v['description'][:110], '::', ' | '.join(i['description'] for i in v['items'])[:150])
    for p in d.get('schematic_parity', [])[:15]: print('   parity:', p['description'][:110], '::', ' | '.join(i['description'] for i in p['items'])[:100])
if '--require-clean' in sys.argv and (errors or unconnected or parity):
    sys.exit('Refusing to generate fabrication files: the board is not routed and DRC-clean.')
