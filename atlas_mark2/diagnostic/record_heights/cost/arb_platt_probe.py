"""Cost probe (diagnostic, not trusted): Arb/FLINT acb_dirichlet_platt_local_hardy_z_zeros(res, n, len, prec) via ctypes.
It isolates `len` consecutive zeros starting at zero number n by Platt's grid method + Turing's method (rigorous library route,
the comparator).  usage: arb_platt_probe.py N LEN [PREC]   (N decimal integer)  -> one JSON line (time, count, first/last zero)."""
import ctypes, sys, time, os, json, resource, flint
L = ctypes.CDLL(os.path.join(os.path.dirname(flint.__file__), '.dylibs', 'libflint.24.0.dylib'))
L.arb_get_str.restype = ctypes.c_char_p
L._arb_vec_init.restype = ctypes.c_void_p
L.acb_dirichlet_platt_local_hardy_z_zeros.restype = ctypes.c_long
ARB_SIZE = 48  # sizeof(arb_struct) on 64-bit: arf_struct (32) + mag_struct (16)

n = sys.argv[1]; ln = int(sys.argv[2]); prec = int(sys.argv[3]) if len(sys.argv) > 3 else 64 + 2 * len(bin(int(n)))
z = ctypes.create_string_buffer(64); L.fmpz_init(z); assert L.fmpz_set_str(z, n.encode(), 10) == 0
res = L._arb_vec_init(ctypes.c_long(ln))
t0 = time.time(); got = L.acb_dirichlet_platt_local_hardy_z_zeros(ctypes.c_void_p(res), z, ctypes.c_long(ln), ctypes.c_long(prec)); dt = time.time() - t0
zs = [L.arb_get_str(ctypes.c_void_p(res + i * ARB_SIZE), ctypes.c_long(30), ctypes.c_ulong(0)).decode() for i in range(max(got, 0))]
print(json.dumps(dict(n=n, len=ln, prec=prec, found=got, seconds=round(dt, 2), first=zs[:1], last=zs[-1:],
                      zeros=zs, maxrss_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 1))), flush=True)
