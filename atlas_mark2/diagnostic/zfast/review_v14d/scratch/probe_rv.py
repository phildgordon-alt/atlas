"""M13 probe (diagnostic; no certificate) = m12_probe.py plus: mode v14c (= the v14b ctypes API of libzfast.v14c), and the
library's last_error is recorded on success too (review_v14b mn5).  M12 probe docstring follows.
M12 probe (diagnostic; no certificate): ONE zfast kind-0 session in this process, then its state hash, Z on a grid, a few Z balls and
rows as the exact strings the provider parses.  Prints one JSON line.  = m9_probe.py plus a v14b mode (zfa14b_new with role / nonce /
key file / verify_n; refusal reason from zfa14b_last_error).
usage: m12_probe.py LIB MODE T0 U0 H DELTA K J D W CKPT GRID_U0 GRID_STEP GRID_N [ROLE NONCE KEYFILE VERIFY_N]
  MODE: v14 (zfa14_new) | v14b (zfa14b_new).  CKPT '-' = none.  GRID_N 0 = no grid.  Exit 3 if the session is refused."""
import ctypes, hashlib, json, os, sys, time, resource
if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'): raise SystemExit('refusing to run under -O / PYTHONOPTIMIZE')
LIB, MODE, T0 = sys.argv[1], sys.argv[2], sys.argv[3]
U0, H, DEL = float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]); K, J, D, W = (int(x) for x in sys.argv[7:11])
CK = sys.argv[11]; GU0, GST, GN = float(sys.argv[12]), float(sys.argv[13]), int(sys.argv[14])
ROLE, NONCE, KEY, VN = (sys.argv[15:19] + ['gen', '0' * 32, '-', '8'])[:4] if len(sys.argv) > 15 else ('gen', '0' * 32, '-', '8')
if MODE not in ('v14', 'v14b', 'v14c'): raise SystemExit('bad MODE')
API_B = MODE in ('v14b', 'v14c')
L = ctypes.CDLL(LIB); BUF = ctypes.create_string_buffer(1 << 16)
P = ctypes.POINTER(ctypes.c_double)
L.zfa3_Z.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
L.zfa4_row.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
L.zfa14_new.restype = ctypes.c_void_p
L.zfa14_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
L.zfa14_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
L.zfa14_hash.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
L.zfa14_Zgrid.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_long, P, P, P, ctypes.c_int]
ck = b'' if CK == '-' else CK.encode()
t0 = time.time()
if API_B:
    L.zfa14b_new.restype = ctypes.c_void_p
    L.zfa14b_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                             ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    L.zfa14b_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    L.zfa14b_last_error.argtypes = [ctypes.c_char_p, ctypes.c_int]
    S = L.zfa14b_new(T0.encode(), U0, H, DEL, K, J, D, W, ck, ROLE.encode(), NONCE.encode(), (b'' if KEY == '-' else KEY.encode()), int(VN))
else:
    S = L.zfa14_new(T0.encode(), U0, H, DEL, K, J, D, W, ck)
tb = time.time() - t0
if not S:
    err = None
    if hasattr(L, 'zfa14b_last_error'):
        L.zfa14b_last_error.argtypes = [ctypes.c_char_p, ctypes.c_int]; L.zfa14b_last_error(BUF, len(BUF)); err = BUF.value.decode()
    print(json.dumps(dict(ok=False, error='session NULL', reason=err, build_wall=round(tb, 3)))); sys.exit(3)
(L.zfa14b_info if API_B else L.zfa14_info)(S, BUF, len(BUF)); info = json.loads(BUF.value.decode())
last_error = None
if API_B:
    L.zfa14b_last_error(BUF, len(BUF)); last_error = BUF.value.decode()
if L.zfa14_hash(S, BUF, len(BUF)) != 0: raise SystemExit('hash failed')
h = BUF.value.decode()
grid = None
if GN > 0:
    mid = (ctypes.c_double * GN)(); rad = (ctypes.c_double * GN)(); uu = (ctypes.c_double * GN)()
    t1 = time.time()
    if L.zfa14_Zgrid(S, GU0, GST, GN, mid, rad, uu, W) != 0: raise SystemExit('grid failed')
    grid = dict(u0=GU0, step=GST, n=GN, sha256=hashlib.sha256(bytes(mid) + bytes(rad) + bytes(uu)).hexdigest(), max_rad=max(rad[:GN]), wall=round(time.time() - t1, 3))
pts = [U0 - 0.9 * H, U0 - 0.31 * H, U0 + 0.123456789, U0 + 0.77 * H]
zs, rows = [], []
for u in pts:
    if L.zfa3_Z(S, u, BUF, len(BUF)) != 0: raise SystemExit('Z failed')
    zs.append(json.loads(BUF.value.decode())['Z'])
    for a in (2.8, 1.6):
        r = L.zfa4_row(S, u, a, BUF, len(BUF)); d = json.loads(BUF.value.decode()); d.pop('sec', None); rows.append([r, d])
ru = resource.getrusage(resource.RUSAGE_SELF)
print(json.dumps(dict(ok=True, mode=MODE, lib=LIB, lib_sha256=hashlib.sha256(open(LIB, 'rb').read()).hexdigest(), T0=T0, u0=U0, H=H, Delta=DEL, K=K, J=J,
                      D=D, W=W, ckpt=CK, build_wall=round(tb, 3), info=info, last_error=last_error, state_sha256=h, grid=grid, Z=zs,
                      rows_sha256=hashlib.sha256(json.dumps(rows).encode()).hexdigest(), cpu_user=round(ru.ru_utime, 2),
                      maxrss_mb=round(ru.ru_maxrss / 2**20, 1), load=os.getloadavg())))
