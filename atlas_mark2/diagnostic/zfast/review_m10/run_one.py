#!/usr/bin/env python3
"""review_m10 differential harness: one session in one fresh process; prints JSON (hash, Z strings, grid).
usage: run_one.py LIB T0 u0 H Delta D W CKPT NPTS SEED [GRIDN]   LIB in {v13b, ref13h, v14, v14old}"""
import ctypes, json, sys, random
B = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/'
lib, T0, u0, H, Dl, D, W, ck, npts, seed = sys.argv[1:11]
gridn = int(sys.argv[11]) if len(sys.argv) > 11 else 0
u0 = float(u0); H = float(H); Dl = float(Dl); D = int(D); W = int(W); npts = int(npts)
L = ctypes.CDLL(B + {'v13b': 'libzfast.v13b.dylib', 'ref13h': 'libzfast.ref13h.dylib', 'v14': 'libzfast.v14.dylib', 'v14old': 'libzfast.v14.dylib'}[lib])
L.zfa4_new.restype = ctypes.c_void_p
L.zfa4_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int]
L.zfa3_Z.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
DP = ctypes.POINTER(ctypes.c_double)
L.zfa3_Zgrid.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_long, DP, DP, DP]
buf = ctypes.create_string_buffer(1 << 16)
out = dict(lib=lib, T0=T0, u0=u0, H=H, Delta=Dl, D=D, W=W)
if lib == 'v14':
    L.zfa14_new.restype = ctypes.c_void_p
    L.zfa14_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
    s = L.zfa14_new(T0.encode(), u0, H, Dl, 18, 12, D, W, ck.encode())
else:
    s = L.zfa4_new(T0.encode(), u0, H, Dl, 18, 12, D)
if not s:
    out['session'] = None; print(json.dumps(out)); sys.exit(3)
if lib in ('v14', 'v14old'):
    L.zfa14_hash.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]; L.zfa14_hash(s, buf, 4096); out['hash'] = buf.value.decode()
    L.zfa14_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]; L.zfa14_info(s, buf, 4096); out['info'] = json.loads(buf.value.decode())
elif lib == 'ref13h':
    L.zfa13h_hash.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]; L.zfa13h_hash(s, buf, 4096); out['hash'] = buf.value.decode()
rng = random.Random(int(seed)); zs = []
for _ in range(npts):
    u = u0 + rng.uniform(-H, H) * 0.999
    L.zfa3_Z(s, u, buf, 1 << 16); zs.append(json.loads(buf.value.decode())['Z'])
out['Z'] = zs
if gridn:
    st = (2 * H * 0.999) / gridn; a = u0 - H * 0.999
    m = (ctypes.c_double * gridn)(); r = (ctypes.c_double * gridn)(); uu = (ctypes.c_double * gridn)()
    if lib == 'v14':
        L.zfa14_Zgrid.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_long, DP, DP, DP, ctypes.c_int]
        L.zfa14_Zgrid(s, a, st, gridn, m, r, uu, W)
    else:
        L.zfa3_Zgrid(s, a, st, gridn, m, r, uu)
    out['grid'] = [m[:].hex() if False else [x.hex() for x in m[:]], [x.hex() for x in r[:]], [x.hex() for x in uu[:]]]
print(json.dumps(out))
