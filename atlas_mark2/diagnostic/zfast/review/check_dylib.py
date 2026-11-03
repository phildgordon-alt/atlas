"""The sha-pinned production library itself (libzfast.v10b.dylib, via its ctypes API exactly as lib/zfast_provider.py calls it:
sessions H=3, Delta=0.2, K=16, J=12, threads=2) on the low point set vs stock Arb; also checks agreement with rv_drv.prod."""
import sys, json, ctypes, hashlib
sys.path.insert(0, '/Users/kiosk/atlas_mark2/diagnostic/zfast/review')
import rvlib as L
LIB = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v10b.dylib'
assert hashlib.sha256(open(LIB, 'rb').read()).hexdigest() == '3daa33d516c062364ff7b5a7cb078ae3b9921483d20646d8587c392c246ef6f8'
_L = ctypes.CDLL(LIB)
_L.zfa_sess_new.restype = ctypes.c_void_p
_L.zfa_sess_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int]
_L.zfa_sess_Z.restype = ctypes.c_int; _L.zfa_sess_Z.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
buf = ctypes.create_string_buffer(4096)
pts = [json.loads(l) for l in open(f'{L.R}/data/zfast_low.jsonl')]
th2 = {(d['T0'], d['u']): d['sess2'] for d in map(json.loads, open(f'{L.R}/data/threads2_low.jsonl'))}
refs = {(int(d['T0']), float.fromhex(d['u'])): d['Z'] for d in map(json.loads, open(f'{L.R}/data/ref_low_AZ.jsonl'))}
S = {}; n = ok = agree = 0
out = L.xopen(f'{L.R}/data/dylib_low.jsonl')
for p in pts:
    c = L.centre(p['u']); k = (p['T0'], c)
    if k not in S: S[k] = _L.zfa_sess_new(str(p['T0']).encode(), c, 3.0, 0, 0.0, 0.2, 16, 12, 2)
    assert _L.zfa_sess_Z(S[k], p['u'], buf, 4096) == 0
    z = json.loads(buf.value.decode())['Z']
    a = L.compare(z, refs[(p['T0'], p['u'])]); b = L.compare(z, th2[(p['T0'], p['u'])])
    n += 1; ok += a['contained']; agree += b['overlap'] and b['diff'] <= 1e-30 + 1e-40
    out.write(json.dumps(dict(T0=p['T0'], u=p['u'], dylib=z, cmp_ref=a, cmp_drv=b)) + '\n')
print('dylib sessions contain stock Arb:', ok, '/', n, '; midpoint identical (to print precision) with rv_drv.prod th=2:', agree, '/', n)
