#!/usr/bin/env python3
"""review_m10 adversarial checkpoint tests for libzfast.v14 (scratch files only under review_m10/scratch)."""
import hashlib, json, os, subprocess, sys
D0 = os.path.dirname(os.path.abspath(sys.argv[0])); SC = os.path.join(D0, 'scratch'); os.makedirs(SC, exist_ok=True)
T0, U0, H, DL, D = '100262293031823', 50, 61, 0.012, 2
def run(ck, W=1, env=None, npts=4):
    e = dict(os.environ); e.update(env or {})
    p = subprocess.run(['nice', '-n', '19', 'python3', os.path.join(D0, 'run_one.py'), 'v14'] + [str(x) for x in (T0, U0, H, DL, D, W, ck, npts, 5)], capture_output=True, text=True, env=e)
    try: o = json.loads(p.stdout)
    except Exception: o = {}
    return p.returncode, o, p.stderr.strip()[-300:]
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def lines(ck): return open(ck).read().split('\n')
def write(ck, ls): open(ck, 'w').write('\n'.join(ls))
def seal(content): return f'{content} #{sha(content)}'
def fresh(name):
    ck = os.path.join(SC, name)
    if os.path.exists(ck): os.remove(ck)
    return ck
res = []
def rep(name, ok, detail=''):
    res.append((name, ok)); print(('PASS ' if ok else 'FAIL ') + name, detail, flush=True)
rc, base, _ = run('')
BH, BZ = base['hash'], base['Z']; NIT = base['info']['items']; print('baseline', BH[:16], 'items', NIT)
# B full run with checkpoint
ck = fresh('full.txt'); rc, o, _ = run(ck)
L = [l for l in lines(ck) if l]
rep('B full run with ckpt: identical, 1+items lines', o.get('hash') == BH and len(L) == 1 + NIT, f'lines={len(L)}')
FULL = L
# B2 resume from complete checkpoint loads everything
rc, o, _ = run(ck); rep('B2 resume of complete ckpt: identical, all loaded', o.get('hash') == BH and o.get('Z') == BZ and o['info']['items_loaded'] == NIT, f"loaded={o['info']['items_loaded']}")
# C kill after k, resume (W=1 and W=2)
for W in (1, 2):
    ck = fresh(f'kill{W}.txt'); rc, o, err = run(ck, W, {'ZFAST14_TEST_EXIT_AFTER': '137'})
    rc2, o2, _ = run(ck, W)
    rep(f'C kill@137 W={W} then resume: identical', rc == 77 and o2.get('hash') == BH and o2.get('Z') == BZ, f"rc={rc} loaded={o2.get('info', {}).get('items_loaded')}")
# D truncated last line (partial write)
ck = fresh('trunc.txt'); write(ck, FULL[:101] + [FULL[101][:len(FULL[101]) // 2]])
rc, o, _ = run(ck); rep('D truncated last line ignored, resume identical', o.get('hash') == BH and o['info']['items_loaded'] == 100, f"loaded={o['info']['items_loaded']}")
L2 = [l for l in lines(ck) if l]; rep('D2 file after resume: all lines valid sha', all(l.rsplit(' #', 1)[1] == sha(l.rsplit(' #', 1)[0]) for l in L2[:1] + L2[102:]) )
# E corrupted byte, hash not fixed
ck = fresh('corrupt.txt'); bad = list(FULL[:60]); x = bad[30]; i = x.index(' ', 40) + 3; bad[30] = x[:i] + ('0' if x[i] != '0' else '1') + x[i + 1:]
write(ck, bad + ['']); rc, o, _ = run(ck); rep('E corrupted line ignored (recomputed), identical', o.get('hash') == BH and o['info']['items_loaded'] == 58)
# F forged (hash recomputed): radius of item 40 moment 0 shrunk to 0 and midpoint perturbed -> accepted?
ck = fresh('forge.txt'); fg = list(FULL)
c = fg[40].rsplit(' #', 1)[0].split(' ')
# tokens: I b i lo hi nbk mph, then arb dumps (4 tokens each); midpoint mantissa is token 7
c[7] = format(int(c[7], 16) + 12345, 'x'); fg[40] = seal(' '.join(c))
write(ck, fg + ['']); rc, o, _ = run(ck)
rep('F forged-but-resealed line is ACCEPTED (expected by design: SHA is integrity, not authenticity)', o.get('hash') is not None and o.get('hash') != BH,
    f"loaded={o.get('info', {}).get('items_loaded')} Z0 {BZ[0]} -> {o.get('Z', ['?'])[0]}")
# F2 forged error radius: set all err mags of an item to zero
ck = fresh('forge_err.txt'); fg = list(FULL); c = fg[41].rsplit(' #', 1)[0].split(' ')
na = 20; nerr0 = 7 + 8 * na
for a in range(na): c[nerr0 + a] = '0:0'
fg[41] = seal(' '.join(c)); write(ck, fg + ['']); rc, o, _ = run(ck)
rep('F2 forged zero error-bound accepted (radius underestimation possible via file)', o.get('hash') not in (None, BH), f"rad Z0 {BZ[0]} -> {o.get('Z', ['?'])[0]}")
# F3 unnormalised mag mantissa accepted?
ck = fresh('forge_mag.txt'); fg = list(FULL); c = fg[42].rsplit(' #', 1)[0].split(' '); c[nerr0] = '1:5'
fg[42] = seal(' '.join(c)); write(ck, fg + ['']); rc, o, err = run(ck)
rep('F3 non-normalised mag mantissa accepted (no mag validation)', o.get('hash') not in (None, BH), f"rc={rc} {err[-80:]}")
# G foreign header (different T0) refused
ck = fresh('foreign.txt'); h = FULL[0].rsplit(' #', 1)[0].replace('T0=' + T0, 'T0=' + str(int(T0) + 1))
write(ck, [seal(h)] + FULL[1:] + ['']); rc, o, err = run(ck); rep('G foreign header refused', rc == 3 and 'refusing' in err, err[-90:])
# G2 different D in header refused
ck = fresh('foreignD.txt'); h = FULL[0].rsplit(' #', 1)[0].replace(' D=2 ', ' D=3 ')
write(ck, [seal(h)] + FULL[1:] + ['']); rc, o, err = run(ck); rep('G2 header with other D refused', rc == 3)
# G3 header missing -> refused
ck = fresh('nohdr.txt'); write(ck, FULL[1:] + ['']); rc, o, err = run(ck); rep('G3 file without header refused', rc == 3)
# G4 truncated header -> refused
ck = fresh('trhdr.txt'); write(ck, [FULL[0][:40]]); rc, o, err = run(ck); rep('G4 truncated header refused', rc == 3)
# L empty file accepted, header written
ck = fresh('empty.txt'); open(ck, 'w').close(); rc, o, _ = run(ck); rep('L empty file -> fresh session, identical', o.get('hash') == BH and lines(ck)[0] == FULL[0])
# I valid hash but missing trailing tokens -> recomputed
ck = fresh('short.txt'); fg = list(FULL[:50]); c = fg[45].rsplit(' #', 1)[0].split(' '); fg[45] = seal(' '.join(c[:-3]))
write(ck, fg + ['']); rc, o, _ = run(ck); rep('I short (resealed) line rejected, recomputed, identical', o.get('hash') == BH and o['info']['items_loaded'] == 48)
# I2 extra token -> rejected
ck = fresh('long.txt'); fg = list(FULL[:50]); c = fg[45].rsplit(' #', 1)[0]; fg[45] = seal(c + ' 0:0')
write(ck, fg + ['']); rc, o, _ = run(ck); rep('I2 extra-token (resealed) line rejected, identical', o.get('hash') == BH and o['info']['items_loaded'] == 48)
# N two lines run together (partial write then append)
ck = fresh('glued.txt'); fg = list(FULL[:50]); fg[30] = fg[30][:200] + fg[31]; del fg[31]
write(ck, fg + ['']); rc, o, _ = run(ck); rep('N glued partial+full line both dropped, identical', o.get('hash') == BH and o['info']['items_loaded'] == 47, f"loaded={o['info']['items_loaded']}")
# J duplicate item lines: first valid wins
ck = fresh('dup.txt'); fg = list(FULL[:50]) + [FULL[10]]; write(ck, fg + ['']); rc, o, _ = run(ck)
rep('J duplicate line harmless', o.get('hash') == BH and o['info']['items_loaded'] == 49)
# K item index overflow (resealed)
ck = fresh('ovf.txt'); fg = list(FULL[:5]); c = fg[3].rsplit(' #', 1)[0].split(' '); c[2] = '9223372036854775000'; fg[3] = seal(' '.join(c))
write(ck, fg + ['']); rc, o, err = run(ck); rep('K huge item index (resealed) handled without crash', rc == 0 and o.get('hash') == BH, f'rc={rc} {err[-100:]}')
# K2 wrong lo/hi -> ignored
ck = fresh('lohi.txt'); fg = list(FULL[:5]); c = fg[3].rsplit(' #', 1)[0].split(' '); c[3] = str(int(c[3]) + 1); fg[3] = seal(' '.join(c))
write(ck, fg + ['']); rc, o, err = run(ck); rep('K2 mismatched lo (resealed) ignored, identical', o.get('hash') == BH and o['info']['items_loaded'] == 3)
# M stale checkpoint of the generic kernel (ZFAST14_GENERIC_KERNEL=1) is accepted -- header does not record the kernel/lib
ck = fresh('generic.txt'); rc, o, _ = run(ck, 1, {'ZFAST14_GENERIC_KERNEL': '1'}); rep('M generic-kernel run identical', o.get('hash') == BH)
print('SUMMARY', sum(ok for _, ok in res), '/', len(res))
