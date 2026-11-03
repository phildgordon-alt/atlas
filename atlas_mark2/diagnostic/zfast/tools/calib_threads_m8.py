"""M8 thread-scaling calibration (diagnostic; no certificate).  One kind-0 zfast session (libzfast.v13b, the v5z5 wide parameters
H = 61, Delta = 0.012, K = 18, J = 12, centre 50) at height T0 with THREADS threads, then Z on NPTS grid points (step 0.004 from u = 0).
usage: calib_threads_m8.py T0 THREADS NPTS OUTJSONL   (appends one JSON line; run each thread count in a fresh process)"""
import ctypes, json, os, sys, time, resource
if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'): raise SystemExit('refusing to run under -O / PYTHONOPTIMIZE')
LIB = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/libzfast.v13b.dylib'
T0 = int(sys.argv[1]); TH = int(sys.argv[2]); NP = int(sys.argv[3]); OUT = sys.argv[4]
L = ctypes.CDLL(LIB)
L.zfa4_new.restype = ctypes.c_void_p
L.zfa4_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int]
L.zfa3_Zgrid.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_long, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
L.zfa3_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
BUF = ctypes.create_string_buffer(4096)
t0 = time.time(); c0 = resource.getrusage(resource.RUSAGE_SELF)
S = L.zfa4_new(str(T0).encode(), 50.0, 61.0, 0.012, 18, 12, TH)
if not S: raise SystemExit('zfa4_new failed')
t1 = time.time(); L.zfa3_info(S, BUF, 4096); info = json.loads(BUF.value.decode())
mid = (ctypes.c_double * NP)(); rad = (ctypes.c_double * NP)(); uu = (ctypes.c_double * NP)()
L.zfa3_Zgrid(S, 0.0, 0.004, NP, mid, rad, uu); t2 = time.time(); c1 = resource.getrusage(resource.RUSAGE_SELF)
rec = dict(T0=str(T0), threads=TH, build_wall=round(t1 - t0, 2), grid_points=NP, grid_wall=round(t2 - t1, 2),
           cpu_user=round(c1.ru_utime - c0.ru_utime, 1), maxrss_mb=round(c1.ru_maxrss / 2**20, 1), session=info,
           max_rad=max(rad[:NP]), load=os.getloadavg(), when=time.strftime('%Y-%m-%d %H:%M:%S'))
open(OUT, 'a').write(json.dumps(rec) + '\n'); print(json.dumps(rec))
