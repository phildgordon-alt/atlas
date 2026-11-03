"""ctypes wrapper for libzfast.<ver>.dylib (v9+).  Z(T0, u) and row(T0, u, a) return python-flint arb balls parsed from Arb's own
printed enclosures (rigorous).  The library path is explicit and versioned."""
import ctypes, json
from flint import arb, ctx

class ZFast:
    def __init__(self, libpath, J=12, threads=1):
        self.lib = ctypes.CDLL(libpath); self.J = J; self.threads = threads
        for f in (self.lib.zfa_Z, self.lib.zfa_row):
            f.restype = ctypes.c_int
        self.lib.zfa_Z.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        self.lib.zfa_row.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        self.buf = ctypes.create_string_buffer(4096)

    def _parse(self, s):
        old = ctx.prec; ctx.prec = max(old, 256)
        try: return arb(s)
        finally: ctx.prec = old

    def Z(self, T0, u):
        """ball containing Z(T0 + u); T0 int >= 0, u binary64"""
        assert isinstance(T0, int) and T0 >= 0
        r = self.lib.zfa_Z(str(T0).encode(), float(u), self.J, self.threads, self.buf, 4096)
        if r != 0: raise RuntimeError(f'zfa_Z failed {r}')
        d = json.loads(self.buf.value.decode()); return self._parse(d['Z'])

    def row(self, T0, u, a):
        """ball containing Re(-zeta'/zeta)(1/2 + pi/(2a) + i(T0 + u))"""
        r = self.lib.zfa_row(str(T0).encode(), float(u), float(a), self.J, self.threads, self.buf, 4096)
        if r != 0: raise RuntimeError(f'zfa_row failed {r}')
        d = json.loads(self.buf.value.decode()); return self._parse(d['P'])
