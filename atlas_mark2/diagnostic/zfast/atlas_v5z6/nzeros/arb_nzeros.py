"""Arb's rigorous zero count N(t) (acb_dirichlet_zeta_nzeros, FLINT 3.6.0 bundled with python-flint 0.9.0), via ctypes.
Diagnostic cross-check only (not part of the Atlas trust base).  N(t) = number of zeros with 0 < gamma <= t (Arb's convention;
it is exact when the returned ball is an exact integer).  CLI: arb_nzeros.py T [T ...]  (decimal integers) -> JSON lines."""
import ctypes, sys, time, os, json, flint
L = ctypes.CDLL(os.path.join(os.path.dirname(flint.__file__), '.dylibs', 'libflint.24.0.dylib'))
L.arb_get_str.restype = ctypes.c_char_p


def nzeros(t, prec=None):
    t = str(int(t)); prec = prec or (64 + len(bin(int(t))))
    a = ctypes.create_string_buffer(256); r = ctypes.create_string_buffer(256)
    L.arb_init(a); L.arb_init(r)
    assert L.arb_set_str(a, t.encode(), ctypes.c_long(prec)) == 0
    t0 = time.time(); L.acb_dirichlet_zeta_nzeros(r, a, ctypes.c_long(prec)); dt = time.time() - t0
    s = L.arb_get_str(r, ctypes.c_long(40), ctypes.c_ulong(0)).decode()
    L.arb_clear(a); L.arb_clear(r)
    return dict(t=t, N=s, exact=('+/-' not in s), seconds=round(dt, 2), prec=prec)


if __name__ == '__main__':
    for t in sys.argv[1:]:
        print(json.dumps(nzeros(t)), flush=True)
