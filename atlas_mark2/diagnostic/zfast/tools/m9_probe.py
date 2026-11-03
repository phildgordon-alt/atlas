"""M9 probe (diagnostic; no certificate): ONE zfast kind-0 session in this process, then its state hash (where the library has one), Z on a
grid, a few Z balls and rows as the exact strings the provider parses.  Prints one JSON line.
usage: m9_probe.py LIB MODE T0 U0 H DELTA K J D W CKPT GRID_U0 GRID_STEP GRID_N
  LIB: path of the dylib.  MODE: v13b (frozen lib, zfa4_new, no hash) | ref13h (frozen v13b source + hash) | v14 (zfa14_new with W workers)
  D: decomposition (v13b 'threads').  W: workers (v14 only).  CKPT: checkpoint path or '-'."""
import ctypes, hashlib, json, os, sys, time, resource
if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'): raise SystemExit('refusing to run under -O / PYTHONOPTIMIZE')
LIB, MODE, T0 = sys.argv[1], sys.argv[2], sys.argv[3]
U0, H, DEL = float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]); K, J, D, W = (int(x) for x in sys.argv[7:11])
CK = sys.argv[11]; GU0, GST, GN = float(sys.argv[12]), float(sys.argv[13]), int(sys.argv[14])
if MODE not in ('v13b', 'ref13h', 'v14'): raise SystemExit('bad MODE')
L = ctypes.CDLL(LIB); BUF = ctypes.create_string_buffer(1 << 16)
P = ctypes.POINTER(ctypes.c_double)
L.zfa3_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
L.zfa3_Z.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
L.zfa4_row.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
L.zfa3_Zgrid.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_long, P, P, P]
t0 = time.time()
if MODE == 'v14':
    L.zfa14_new.restype = ctypes.c_void_p
    L.zfa14_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
    S = L.zfa14_new(T0.encode(), U0, H, DEL, K, J, D, W, (b'' if CK == '-' else CK.encode()))
else:
    L.zfa4_new.restype = ctypes.c_void_p
    L.zfa4_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    S = L.zfa4_new(T0.encode(), U0, H, DEL, K, J, D)
if not S: print(json.dumps(dict(ok=False, error='session NULL'))); sys.exit(3)
tb = time.time() - t0
(L.zfa14_info if MODE == 'v14' else L.zfa3_info)(S, BUF, len(BUF)) if MODE != 'v14' else None
if MODE == 'v14':
    L.zfa14_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]; L.zfa14_info(S, BUF, len(BUF))
info = json.loads(BUF.value.decode())
h = None
if MODE in ('ref13h', 'v14'):
    f = L.zfa13h_hash if MODE == 'ref13h' else L.zfa14_hash; f.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    if f(S, BUF, len(BUF)) != 0: raise SystemExit('hash failed')
    h = BUF.value.decode()
mid = (ctypes.c_double * GN)(); rad = (ctypes.c_double * GN)(); uu = (ctypes.c_double * GN)()
t1 = time.time()
if MODE == 'v14':
    L.zfa14_Zgrid.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_long, P, P, P, ctypes.c_int]
    if L.zfa14_Zgrid(S, GU0, GST, GN, mid, rad, uu, W) != 0: raise SystemExit('grid failed')
else: L.zfa3_Zgrid(S, GU0, GST, GN, mid, rad, uu)
tg = time.time() - t1
gh = hashlib.sha256(bytes(mid) + bytes(rad) + bytes(uu)).hexdigest()
pts = [U0 - 0.9 * H, U0 - 0.31 * H, U0 + 0.123456789, U0 + 0.77 * H]
zs, rows = [], []
for u in pts:
    if L.zfa3_Z(S, u, BUF, len(BUF)) != 0: raise SystemExit('Z failed')
    zs.append(json.loads(BUF.value.decode())['Z'])
    for a in (2.8, 1.6):
        r = L.zfa4_row(S, u, a, BUF, len(BUF)); d = json.loads(BUF.value.decode()); d.pop('sec', None); rows.append([r, d])
ru = resource.getrusage(resource.RUSAGE_SELF)
print(json.dumps(dict(ok=True, mode=MODE, lib=LIB, lib_sha256=hashlib.sha256(open(LIB, 'rb').read()).hexdigest(), T0=T0, u0=U0, H=H, Delta=DEL, K=K, J=J,
                      D=D, W=W if MODE == 'v14' else None, ckpt=CK, build_wall=round(tb, 3), grid_wall=round(tg, 3), info=info, state_sha256=h,
                      grid=dict(u0=GU0, step=GST, n=GN, sha256=gh, max_rad=max(rad[:GN])), Z=zs, rows_sha256=hashlib.sha256(json.dumps(rows).encode()).hexdigest(),
                      cpu_user=round(ru.ru_utime, 2), maxrss_mb=round(ru.ru_maxrss / 2**20, 1), load=os.getloadavg(),
                      env={k: os.environ.get(k) for k in ('ZFAST14_GENERIC_KERNEL', 'ZFAST14_TEST_EXIT_AFTER')})))
