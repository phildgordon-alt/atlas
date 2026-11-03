"""sess_points.py LIB T0 CENTRE INFILE OUTFILE [rows]: one production session (v12a: zfa4, H4 D0.15 K18; v10b: kind-0 H3 D0.2 K16),
Z at every 'T0 u' line of INFILE (only lines with this T0 and |u-c|<=H); optional rows a=2.8,1.6 at the same u.  Never overwrites."""
import sys, json, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zlib as Z
lib, T0, c, inf, outf = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4], sys.argv[5]
rows = len(sys.argv) > 6 and sys.argv[6] == 'rows'
L = Z.prod(lib)
pts = []
for l in open(inf):
    p = l.split()
    if len(p) >= 2 and int(p[0]) == T0: pts.append(float.fromhex(p[1]) if 'x' in p[1] else float(p[1]))
H = 4.0 if lib == 'v12a' else 3.0
pts = [u for u in pts if abs(u - c) <= H]
out = open(outf, 'x')
t = time.time()
if lib == 'v12a': s, info = L.sess4(T0, c)
else: s, info = L.sess(T0, c, 0)
info['sec_wall'] = time.time() - t
out.write(json.dumps(dict(session=info, lib=lib, T0=str(T0), c=c)) + '\n'); out.flush()
for u in pts:
    d = L.Z4(s, u) if lib == 'v12a' else L.Z(s, u)
    d.update(T0=str(T0), u=u.hex(), kind='Z'); out.write(json.dumps(d) + '\n')
    if rows and lib == 'v12a':
        for a in (2.8, 1.6):
            r = L.row4(s, u, a); r.update(T0=str(T0), u=u.hex(), a=a, kind='row'); out.write(json.dumps(r) + '\n')
    out.flush()
out.write(json.dumps(dict(done=True, sec=time.time() - t)) + '\n')
