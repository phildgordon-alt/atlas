"""tools/m14_rt/extract_balls.py -- READ-ONLY extraction of every moment ball (4 arb_dump_str tokens) from zfast checkpoints
(formats ZFAST14CKPT v1 (v14), ZFAST14B (v14b), ZFAST14C CKPT v3 (v14c/v14d)).  usage: extract_balls.py OUT CKPT... ; prints counts.
The checkpoint files are opened read-only and never modified."""
import json, sys
if sys.flags.optimize: raise SystemExit('refusing -O')
out = open(sys.argv[1], 'x'); stats = {}
for p in sys.argv[2:]:
    with open(p, 'r', encoding='latin-1') as f:
        hdr = f.readline(); fmt = hdr.split(' ')[0] + ' ' + hdr.split(' ')[1]
        first = 8 if hdr.startswith('ZFAST14C CKPT v3') else 7
        n = nz = lines = 0
        for line in f:
            if not line.endswith('\n') or not line.startswith('I '): continue
            t = line[:-1].split(' ')
            if '#' in t[-1]: t = t[:-1]
            # arbs are 4-token groups until the first mag token (contains ':')
            k = first
            while k + 3 < len(t) and ':' not in t[k]:
                out.write(' '.join(t[k:k + 4]) + '\n'); n += 1; nz += t[k + 2] != '0'; k += 4
            lines += 1
    stats[p] = dict(format=fmt, lines=lines, balls=n, nonzero_radius=nz)
print(json.dumps(stats, indent=1))
