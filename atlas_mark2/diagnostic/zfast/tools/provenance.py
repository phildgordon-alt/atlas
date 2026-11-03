"""Writes RUN/provenance.json (new file; refuses if it exists): the exact code that produced a v5z/v5z2 certificate window, for review.
Records: driver + lib file shas used by the run (from drive.jsonl), current shas of the provider and zfast library, the freeze file,
the zfast source snapshot directory and its SHA256 file, and the scan/Turing tool."""
import json, sys, hashlib, os, glob
run = os.path.abspath(sys.argv[1]); out = run + '/provenance.json'; assert not os.path.exists(out)
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
root = os.path.dirname(os.path.dirname(os.path.dirname(run)))          # atlas_v5z2/
d = [json.loads(l) for l in open(run + '/drive.jsonl')][0]
prov = open(root + '/lib/zfast_provider.py').read()
lib = [l for l in prov.splitlines() if l.startswith('LIBPATH')][0].split('=', 1)[1].strip().strip("'")
ver = os.path.basename(lib).split('.')[1]
Z = '/Users/kiosk/atlas_mark2/diagnostic/zfast/'
rec = dict(run=run, tree=root, freeze_file=root + '/' + [f for f in os.listdir(root) if f.endswith('FREEZE.sha256')][0],
           driver_sha_at_run=d['driver_sha'], replay_target_sha_at_run=d['replay_target_sha'], lib_sha_at_run=d['lib_sha'],
           provider=root + '/lib/zfast_provider.py', provider_sha=sha(root + '/lib/zfast_provider.py'),
           zfast_library=lib, zfast_library_sha=sha(lib), zfast_version=ver, zfast_sources=Z + 'bin/src_' + ver, zfast_sources_sha_file=Z + 'bin/SHA256.' + ver,
           theory=[Z + 'THEORY_ZFAST.md', Z + 'THEORY_M3.md', Z + 'THEORY_M5.md', Z + 'THEORY_M5b.md', root + '/THEORY_V5Z2.md', Z + 'atlas_v5z/THEORY_V5Z.md'],
           scan_turing_tool=Z + 'tools/scan_turing2.py', scan_turing_tool_sha=sha(Z + 'tools/scan_turing2.py'))
json.dump(rec, open(out, 'w'), indent=1); print(out)
