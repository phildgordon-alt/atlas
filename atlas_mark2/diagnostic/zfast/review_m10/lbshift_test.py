#!/usr/bin/env python3
"""review_m10: does a checkpoint written under a different Lb[] (model: libm `log` change between interruption and resume) get
accepted by libzfast.v14, and are the resulting Z balls still enclosures?  usage: lbshift_test.py {gen|use|honest} T0 CKPT"""
import ctypes, json, sys, random, os
mode, T0, ck = sys.argv[1:4]
B = '/Users/kiosk/atlas_mark2/diagnostic/zfast/'
lib = B + ('review_m10/scratch/libzfast.lbshift.dylib' if mode == 'gen' else 'bin/libzfast.v14.dylib')
if mode == 'gen': os.environ['REVIEW_LBSHIFT'] = '1'
L = ctypes.CDLL(lib)
L.zfa14_new.restype = ctypes.c_void_p
L.zfa14_new.argtypes = [ctypes.c_char_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
L.zfa3_Z.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
L.zfa14_info.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
s = L.zfa14_new(T0.encode(), 50.0, 61.0, 0.012, 18, 12, 2, 1, (ck if mode != 'honest' else '').encode())
if not s: print(json.dumps(dict(session=None))); sys.exit(3)
buf = ctypes.create_string_buffer(1 << 16); L.zfa14_info(s, buf, 4096); info = json.loads(buf.value.decode())
r = random.Random(3); Z = []
for u in [50 + 60.9 * (2 * r.random() - 1) for _ in range(10)] + [-10.5, 110.5]:
    L.zfa3_Z(s, u, buf, 1 << 16); Z.append([u, json.loads(buf.value.decode())['Z']])
print(json.dumps(dict(info=info, Z=Z)))
