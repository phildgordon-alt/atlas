"""review_v14c: key-resealed malformed-numerics tests against the PRODUCTION libzfast.v14c (no sanitizer; crash = negative rc).
Targeted extremes + random mutations.  vn = 0 so that accepted forged values reach the merge and the Z / row evaluation.
usage: fuzz_rv.py OUTDIR SEED NRANDOM"""
import json, os, random, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rvlib import *

OUT = sys.argv[1]; SEED = int(sys.argv[2]); NR = int(sys.argv[3])
os.makedirs(OUT); KD = os.path.join(OUT, 'keys'); os.makedirs(KD, mode=0o700)
T0, H, DL, D = '100000000000000', '61.0', '0.012', 2
def P(n): return os.path.join(OUT, n)
def K(n): return os.path.join(KD, n)
ref = probe(L14C, 'v14c', T0, '50.0', H, DL, D, 1, grid=100)
A = probe(L14C, 'v14c', T0, '50.0', H, DL, D, 1, P('A.txt'), key=K('A.key'), grid=100)
assert kk(A) == kk(ref)
LA = read_lines(P('A.txt')); hh = hh_of(LA[0]); N = len(LA) - 1
res = []; n = 0
def run(name, x, tokfn, raw=None):
    global n
    n += 1
    b = body(LA[x]); t = b.split(' ')
    nb = raw if raw is not None else ' '.join(tokfn(t[:]))
    xs = int(nb.split(' ')[1]) if nb.split(' ')[1].isdigit() and len(nb.split(' ')[1]) < 20 else x
    try:
        line = seal_item(nb, K('A.key'), hh, xs)
    except Exception:
        line = nb + ' #' + '0' * 64
    L = LA[:]; L[x] = line
    fn = P(f'c{n}.txt'); write_lines(fn, L); copykey(K('A.key'), K(f'c{n}.key'))
    t0 = time.time()
    try:
        r = probe(L14C, 'v14c', T0, '50.0', H, DL, D, 1, fn, key=K(f'c{n}.key'), vn=0, grid=100, timeout=180)
    except Exception as e:
        r = dict(rc='exc ' + repr(e)[:80])
    cls = 'watchdog' if 'WATCHDOG' in (r.get('stderr') or '') else 'crash' if isinstance(r['rc'], int) and r['rc'] < 0 else ('timeout' if r['rc'] == 'timeout' else ('refused' if r['rc'] == 3 else ('accepted_honest' if kk(r) == kk(ref) else ('accepted_changed' if r['rc'] == 0 else f'rc{r["rc"]}'))))
    row = dict(name=name, x=x, cls=cls, rc=r['rc'], wall=round(time.time() - t0, 1), reason=(r.get('reason') or '')[:120], rej=(r.get('info') or {}).get('lines_rejected'),
               loaded=(r.get('info') or {}).get('items_loaded'), Z0=(r.get('Z') or [None])[0], stderr=(r.get('stderr') or '')[-200:] if cls in ('crash', 'timeout') or str(cls).startswith('rc') else '')
    res.append(row); print(json.dumps(row)[:400], flush=True)

def setk(i, v):
    def f(t): t[i] = v; return t
    return f
X = 7
big = '1' + '0' * 30000 + '1'
targeted = [
    ('mid_man_huge_odd', 8, big), ('mid_exp_huge_pos', 9, '1' + '0' * 30000), ('mid_exp_huge_neg', 9, '-1' + '0' * 30000),
    ('rad_man_huge_odd', 10, big), ('rad_man_huge_exp0', 10, 'f' * 5000), ('mid_exp_2^70', 9, '4' + '0' * 17), ('mid_man_even', 8, 'a'), ('mid_zero_exp5', 8, '0'), ('rad_7fffffff', 10, '7fffffff'),
    ('rad_3fffffff', 10, '3fffffff'), ('rad_man_31bit_odd', 10, '7ffffffd'), ('rad_neg', 10, '-1'), ('rad_exp_2^80', 11, '1' + '0' * 20),
    ('rad_exp_2^36', 11, '1' + '0' * 9), ('rad_exp_-2^39', 11, '-8' + '0' * 9), ('mid_upper', 8, '-27C8AE05460BA312B'), ('mid_plus', 8, '+27c8ae05460ba312b'),
    ('mid_0x', 8, '0x27c8ae05460ba312b'), ('mid_leading0', 8, '-027c8ae05460ba312b'), ('mid_minus0_exp', 9, '-0'), ('rad_exp_minus0', 11, '-0'),
    ('mag_0:5', 168, '0:5'), ('mag_16f', 168, 'ffffffffffffffff:0'), ('mag_17hex', 168, '1ffffffffffffffff:0'), ('mag_2^29', 168, '20000000:0'),
    ('mag_below', 168, '1fffffff:0'), ('mag_exp40', 168, '20000000:ffffffffff'), ('mag_exp41', 168, '20000000:10000000000'),
    ('mag_exp_neg40', 168, '20000000:-ffffffffff'), ('mag_nocolon', 168, '20000000'), ('mag_2colon', 168, '20000000:1:2'), ('mag_exp_empty', 168, '20000000:'),
    ('mag_exp_huge', 168, '20000000:' + 'f' * 79), ('mag_exp_80', 168, '20000000:' + 'f' * 80), ('mag_leading0', 168, '020000000:0'),
    ('V_huge', 188, '20000000:ffffffffff'), ('V_tiny', 188, '20000000:-ffffffffff'),
    ('nbk_negzero', 6, '-0x0p+0'), ('nbk_inf', 6, 'inf'), ('nbk_nan', 6, 'nan'), ('nbk_max', 6, '0x1.fffffffffffffp+1023'), ('nbk_upper', 6, '0X1P+2'),
    ('nbk_dec', 6, '5'), ('nbk_noncanon', 6, '0x1.0p+2'), ('nbk_neg', 6, '-0x1p+2'), ('mph_huge', 7, '0x1p+1000'), ('mph_denorm', 7, '0x0.0000000000001p-1022'),
    ('lo_2^64', 4, '18446744073709551616'), ('lo_max', 4, '18446744073709551615'), ('b_max', 2, '18446744073709551615'), ('i_big', 3, '4294967296'),
    ('i_neg', 3, '-1'), ('b_leading0', 2, '0' + '940'),
]
for name, i, v in targeted:
    run(name, X if i < 8 or i >= 168 else X, setk(i, v))
b = body(LA[X])
run('extra_token', X, None, raw=b + ' 0')
run('missing_token', X, None, raw=' '.join(b.split(' ')[:-1]))
run('double_space', X, None, raw=b.replace(' ', '  ', 1).replace('I  ', 'I ', 1) if False else ' '.join(b.split(' ')[:10]) + '  ' + ' '.join(b.split(' ')[10:]))
run('tab', X, None, raw=' '.join(b.split(' ')[:10]) + '\t' + ' '.join(b.split(' ')[10:]))
run('nul_then_junk', X, None, raw=b + '\0junk junk')
run('nul_mid', X, None, raw=' '.join(b.split(' ')[:30]) + '\0' + ' '.join(b.split(' ')[30:]))
run('x_21digits', X, None, raw='I 0' + b.split(' ', 1)[1].split(' ', 1)[0].rjust(20, '0') + ' ' + b.split(' ', 2)[2])
run('x_leading0', X, None, raw='I 0' + b.split(' ', 2)[1] + ' ' + b.split(' ', 2)[2])
run('x_plus', X, None, raw='I +' + b.split(' ', 2)[1] + ' ' + b.split(' ', 2)[2])
# random mutations
rng = random.Random(SEED)
alph = '0123456789abcdef-:xpP.+ AF\0'
for k in range(NR):
    x = 1 + rng.randrange(N); t = body(LA[x]).split(' '); i = rng.randrange(1, len(t)); s = t[i]
    op = rng.randrange(7)
    if op == 0 and s: j = rng.randrange(len(s)); s = s[:j] + rng.choice(alph) + s[j + 1:]
    elif op == 1: j = rng.randrange(len(s) + 1); s = s[:j] + rng.choice(alph) + s[j:]
    elif op == 2 and s: j = rng.randrange(len(s)); s = s[:j] + s[j + 1:]
    elif op == 3: s = rng.choice(['0', '-0', '1', '-1', '7fffffff', 'ffffffffffffffff', '0:0', '0:1', '20000000:0', '1' * rng.randrange(1, 3000), '-' + 'f' * rng.randrange(1, 200)])
    elif op == 4: s = s + rng.choice(['0', 'f', '1' * 50, ':0'])
    elif op == 5: s = str(rng.randrange(2 ** 64 + 2))
    else: s = s.replace('-', '') if '-' in s else '-' + s
    t[i] = s
    run(f'rand{k}_op{op}_t{i}', x, None, raw=' '.join(t))
summ = {}
for r in res: summ[r['cls']] = summ.get(r['cls'], 0) + 1
json.dump(dict(summary=summ, cases=res), open(os.path.join(OUT, 'fuzz_results.json'), 'w'), indent=1)
print(json.dumps(dict(summary=summ)))
