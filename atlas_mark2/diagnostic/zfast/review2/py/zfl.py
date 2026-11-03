"""review2: ctypes access to the PRODUCTION zfast dylibs (sha-checked) and to review2 mutant dylibs.  Read-only use."""
import ctypes, hashlib, json
B = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin'
PROD = {'v12a': (f'{B}/libzfast.v12a.dylib', '70e1c31722478bd09e3677cb6001c5e4bb39cd121ff0da3d9a438d3773eba8c0'),
        'v10b': (f'{B}/libzfast.v10b.dylib', '3daa33d516c062364ff7b5a7cb078ae3b9921483d20646d8587c392c246ef6f8')}
_BUF = ctypes.create_string_buffer(8192)

class Lib:
    def __init__(self, path, sha=None):
        if sha: assert hashlib.sha256(open(path, 'rb').read()).hexdigest() == sha, path
        L = ctypes.CDLL(path); self.L = L; self.path = path
        self.has4 = hasattr(L, 'zfa4_new')
        if self.has4:
            L.zfa4_new.restype = ctypes.c_void_p
            L.zfa4_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int]
            L.zfa3_Z.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
            L.zfa4_row.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
            L.zfa3_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
            L.zfa3_free.argtypes = [ctypes.c_void_p]
        if hasattr(L, 'zfa_sess_new'):
            L.zfa_sess_new.restype = ctypes.c_void_p
            L.zfa_sess_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int]
            L.zfa_sess_Z.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
            L.zfa_sess_row.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
            L.zfa_sess_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        L.zf_cos2pi.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_uint64]
        L.zf_cos2pi.restype = None

    def cos2pi(self, v):
        c = ctypes.c_double(); s = ctypes.c_double(); self.L.zf_cos2pi(ctypes.byref(c), ctypes.byref(s), v); return c.value, s.value

    # v12a-style kind-0 session (Z + complex-shift rows)
    def sess4(self, T0, u0, H=4.0, Delta=0.15, K=18, J=12, threads=1):
        s = self.L.zfa4_new(str(T0).encode(), u0, H, Delta, K, J, threads); assert s
        self.L.zfa3_info(s, _BUF, 8192); return s, json.loads(_BUF.value.decode())
    def Z4(self, s, u):
        r = self.L.zfa3_Z(s, u, _BUF, 8192); assert r == 0, r; return json.loads(_BUF.value.decode())
    def row4(self, s, u, a):
        r = self.L.zfa4_row(s, u, a, _BUF, 8192); d = json.loads(_BUF.value.decode()); d['rc'] = r; return d
    def free4(self, s): self.L.zfa3_free(s)
    # v10b-style sessions (kind 0 = Z, kind 1 = rows at a)
    def sess(self, T0, u0, kind, a=0.0, H=3.0, Delta=0.2, K=16, J=12, threads=1):
        s = self.L.zfa_sess_new(str(T0).encode(), u0, H, kind, a, Delta, K, J, threads); assert s
        self.L.zfa_sess_info(s, _BUF, 8192); return s, json.loads(_BUF.value.decode())
    def Z(self, s, u):
        r = self.L.zfa_sess_Z(s, u, _BUF, 8192); assert r == 0, r; return json.loads(_BUF.value.decode())
    def row(self, s, u):
        r = self.L.zfa_sess_row(s, u, _BUF, 8192); d = json.loads(_BUF.value.decode()); d['rc'] = r; return d

def prod(v): p, h = PROD[v]; return Lib(p, h)
