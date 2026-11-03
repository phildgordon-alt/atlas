"""reviewer adversarial / resume tests on libzfast.v14b (production dylib; testhooks only for LBSHIFT).  usage: attack_rv.py OUTDIR
10^14, H 61, Delta 0.012, D 2, W 1 (each session < 1 s)."""
import hashlib, hmac, json, os, random, shutil, subprocess, sys
ZF = '/Users/kiosk/atlas_mark2/diagnostic/zfast/'
PY = '/Users/kiosk/projects/atlas-rerun/.venv/bin/python'
PROBE = ZF + 'tools/m12_probe.py'
LB, LT = ZF + 'bin/libzfast.v14b.dylib', ZF + 'bin/libzfast.v14b_testhooks.dylib'
OUT = sys.argv[1]; os.makedirs(OUT); KD = os.path.join(OUT, 'keys'); os.makedirs(KD, mode=0o700)
T0, H, DL, D = '100000000000000', '61.0', '0.012', '2'
NA = 'a' * 32
R = {}


def probe(ck='-', role='gen', nonce=NA, key='-', vn=8, U0='50.0', lib=LB, env=None, W='1'):
    e = {k: v for k, v in os.environ.items() if not k.startswith('ZFAST')}; e.update(env or {})
    cmd = ['nice', '-n', '19', PY, '-B', PROBE, lib, 'v14b', T0, U0, H, DL, '18', '12', D, W, ck, str(float(U0) - 3), '0.004', '100', role, nonce, key, str(vn)]
    p = subprocess.run(cmd, capture_output=True, text=True, env=e, timeout=600)
    r = json.loads(p.stdout.strip().splitlines()[-1]); r['rc'] = p.returncode
    return r


def kk(r): return (r.get('state_sha256'), (r.get('grid') or {}).get('sha256'), r.get('rows_sha256'), tuple(r.get('Z') or ()))
def P(n): return os.path.join(OUT, n)
def K(n): return os.path.join(KD, n)
def rec(name, ok, **d):
    R[name] = dict(ok=bool(ok), **d); print(('OK   ' if ok else 'FAIL ') + name, json.dumps(d)[:700], flush=True)
def body(l): return l[:l.rindex(' #')]
def seal(b, kf): return b + ' #' + hmac.new(open(kf, 'rb').read(), b.encode(), hashlib.sha256).hexdigest()


# baseline gen ckpt (session A, u0 50)
ref = probe()
a = probe(P('A.txt'), key=K('A.key'))
rec('baseline_fresh_ckpt_identical', kk(a) == kk(ref) and a['info']['created'] == 1, items=a['info']['items'])
A = open(P('A.txt')).read().split('\n'); assert A[-1] == ''; A = A[:-1]; N = len(A) - 1

# 1. gen file used by replay role: (a) copied with its own key path, (b) with the gen key copied to the replay key path
shutil.copy(P('A.txt'), P('A_as_replay.txt')); r1 = probe(P('A_as_replay.txt'), role='replay', key=K('A_replay.key'))
rec('gen_file_replay_role_newkey_refused', r1['rc'] == 3, reason=r1.get('reason'))
shutil.copy(P('A.txt'), P('A_as_replay2.txt')); shutil.copy(K('A.key'), K('A_replay2.key'))
r2 = probe(P('A_as_replay2.txt'), role='replay', key=K('A_replay2.key'))
rec('gen_file_replay_role_genkey_refused', r2['rc'] == 3 and 'role' in (r2.get('reason') or ''), reason=r2.get('reason'))
r3 = probe(P('A_as_replay2.txt'), role='gen', nonce='b' * 32, key=K('A_replay2.key'))
rec('other_nonce_refused', r3['rc'] == 3 and 'nonce' in (r3.get('reason') or ''), reason=r3.get('reason'))

# 2. torn tails / torn header at random byte offsets: refuse or bit-identical
data = open(P('A.txt'), 'rb').read(); hl = data.index(b'\n') + 1
rng = random.Random(12345); offs = [0, 10, hl - 30, hl - 1, hl, hl + 5] + sorted(rng.sample(range(hl + 1, len(data)), 10))
for o in offs:
    fn = P(f'torn_{o}.txt'); open(fn, 'wb').write(data[:o]); shutil.copy(K('A.key'), K(f'torn_{o}.key'))
    r = probe(fn, key=K(f'torn_{o}.key'))
    ok = (r['rc'] == 0 and kk(r) == kk(ref)) or (r['rc'] == 3 and o < hl and o > 0)
    # a second resume must also be identical and the file must end in a newline
    r2 = probe(fn, key=K(f'torn_{o}.key')) if r['rc'] == 0 else r
    ok = ok and (r2['rc'] == r['rc']) and (r['rc'] != 0 or kk(r2) == kk(ref))
    rec(f'torn_at_{o}', ok, rc=r['rc'], loaded=(r.get('info') or {}).get('items_loaded'), rejected=(r.get('info') or {}).get('lines_rejected'),
        loaded2=(r2.get('info') or {}).get('items_loaded'), reason=(r.get('reason') or '')[:120])

# 3. torn line followed by valid appended lines in the same physical line (no newline fix) -> must not be accepted as one line
fn = P('glued.txt'); L = A[:]; glued = L[5][:len(L[5]) // 2] + L[6]; open(fn, 'w').write('\n'.join(L[:5] + [glued] + L[7:]) + '\n'); shutil.copy(K('A.key'), K('glued.key'))
r = probe(fn, key=K('glued.key')); rec('glued_torn_line_ignored', r['rc'] == 0 and kk(r) == kk(ref) and r['info']['lines_rejected'] == 1, info=r.get('info'))

# 4. zero-length key with an empty checkpoint (crash between key creat and key write)
open(K('zero.key'), 'wb').close(); os.chmod(K('zero.key'), 0o600); open(P('zero.txt'), 'w').close()
r = probe(P('zero.txt'), key=K('zero.key')); rec('zero_length_key_refused (operational: needs manual cleanup)', r['rc'] == 3, reason=r.get('reason'))

# 5. empty checkpoint + EXISTING key: the library silently reuses the key for a new session (u0 different)
open(P('B.txt'), 'w').close(); shutil.copy(K('A.key'), K('B.key'))
b = probe(P('B.txt'), key=K('B.key'), U0='50.5'); bref = probe(U0='50.5')
rec('empty_ckpt_existing_key_reused (expected by design; enables splice below)', b['rc'] == 0 and b['info']['created'] == 1 and kk(b) == kk(bref))
B = open(P('B.txt')).read().split('\n')[:-1]
# 6. splice: session B's file + a few of session A's authenticated lines (same key) for items with the same (b,i,lo,hi), placed BEFORE B's lines
keyB = {tuple(l.split(' ')[1:5]): l for l in B[1:]}; keyA = {tuple(l.split(' ')[1:5]): l for l in A[1:]}
common = [k for k in keyA if k in keyB and keyA[k] != keyB[k]]
print('items common (b,i,lo,hi) with different content:', len(common), 'of', len(B) - 1, flush=True)
acc = 0; wrong = 0; trials = 6
for t in range(trials):
    pick = random.Random(t).sample(common, 2)
    fn = P(f'splice_{t}.txt'); shutil.copy(K('B.key'), K(f'splice_{t}.key'))
    open(fn, 'w').write('\n'.join([B[0]] + [keyA[k] for k in pick] + B[1:]) + '\n')
    r = probe(fn, key=K(f'splice_{t}.key'), U0='50.5')
    if r['rc'] == 0:
        acc += 1; wrong += kk(r) != kk(bref)
        if t == 0: print('splice accepted: dup=', r['info']['lines_duplicate'], 'Z ref', bref['Z'][2], 'Z spliced', r['Z'][2], flush=True)
rec('splice_same_key_cross_session', acc == 0, accepted=acc, trials=trials, accepted_and_wrong=wrong,
    note='lines are not bound to the header/session; duplicates with different content are silently ignored (first wins)')

# 7. strict parser: authenticated (re-sealed) mutations of one line of A; every one must be refused (fatal) or be a canonical no-op
def mut(i, f, name):
    L = A[:]; b0 = body(L[i]); b1 = f(b0)
    if b1 == b0: return
    L[i] = seal(b1, K('A.key')); fn = P(f'mut_{name}.txt'); open(fn, 'w').write('\n'.join(L) + '\n'); shutil.copy(K('A.key'), K(f'mut_{name}.key'))
    r = probe(fn, key=K(f'mut_{name}.key'), vn=0)
    return r
def tok(i, j, v):
    def f(b):
        t = b.split(' '); t[j] = v(t[j]); return ' '.join(t)
    return f
muts = {
    'b_eq_nb': tok(3, 1, lambda s: '946'), 'b_huge': tok(3, 1, lambda s: '18446744073709551615'), 'b_overflow': tok(3, 1, lambda s: '18446744073709551616'),
    'i_eq_T': tok(3, 2, lambda s: str(int(s) + 2)), 'i_neg': tok(3, 2, lambda s: '-1'), 'lo_plus1': tok(3, 3, lambda s: str(int(s) + 1)), 'lo_leading0': tok(3, 3, lambda s: '0' + s),
    'nbk_noncanon': tok(3, 5, lambda s: s.replace('p+', 'p+0')), 'nbk_dec': tok(3, 5, lambda s: '3.0'), 'nbk_neg': tok(3, 5, lambda s: '-' + s), 'mph_inf': tok(3, 6, lambda s: 'inf'),
    'mph_nan': tok(3, 6, lambda s: 'nan'), 'arb_upper': tok(3, 7, lambda s: s.upper()), 'arb_lead0': tok(3, 7, lambda s: s[0] + '0' + s[1:] if s[0] == '-' else '0' + s),
    'arb_plus': tok(3, 7, lambda s: '+' + s.lstrip('-')), 'arb_rad_unnorm': tok(3, 9, lambda s: '1'), 'arb_rad_neg': tok(3, 9, lambda s: '-20000000'),
    'mag_unnorm': tok(3, 7 + 8 * 20, lambda s: '1:' + s.split(':')[1]), 'mag_exp_huge': tok(3, 7 + 8 * 20, lambda s: s.split(':')[0] + ':10000000000'),
    'mag_exp_lead0': tok(3, 7 + 8 * 20, lambda s: s.split(':')[0] + ':0' + s.split(':')[1].lstrip('-')), 'mag_neg0': tok(3, 7 + 8 * 20, lambda s: '0:-0'),
    'double_space': lambda b: b.replace(' ', '  ', 1), 'trailing_space': lambda b: b + ' ', 'extra_token': lambda b: b + ' 0:0', 'missing_token': lambda b: b.rsplit(' ', 1)[0],
    'tab_sep': lambda b: b.replace(' ', '\t', 1), 'first_tok_J': lambda b: 'J' + b[1:], 'nul_inside': lambda b: b[:20] + '\x00' + b[21:],
}
bad = []
for name, f in muts.items():
    r = mut(3, f, name)
    if r is None: continue
    if r['rc'] != 3: bad.append((name, r['rc'], (r.get('info') or {}).get('items_loaded')))
    print('  mut', name, r['rc'], (r.get('reason') or '')[-90:], flush=True)
rec('strict_parser_mutations_refused', not bad, n=len(muts), not_refused=bad)
# canonical but semantically weakened line (error mags zeroed): accepted iff not sampled -- trust model, recorded not judged
def zero_errs(b):
    t = b.split(' '); n0 = 7 + 8 * 20
    for k in range(n0, n0 + 20): t[k] = '0:0'
    return ' '.join(t)
r = mut(3, zero_errs, 'zero_errs_vn0'); rec('authenticated_zeroed_errors_vn0_ACCEPTED (key holder trusted)', r['rc'] == 0, rc=r['rc'], same_as_ref=kk(r) == kk(ref))

# 8. header tamper re-sealed with the key: reorder / duplicate / extra field -> refuse
def hdr(f, name):
    L = A[:]; L[0] = seal(f(body(L[0])), K('A.key')); fn = P(f'hdr_{name}.txt'); open(fn, 'w').write('\n'.join(L) + '\n'); shutil.copy(K('A.key'), K(f'hdr_{name}.key'))
    return probe(fn, key=K(f'hdr_{name}.key'))
hb = []
for name, f in {'swap': lambda b: b.replace(' K=18 J=12', ' J=12 K=18'), 'dup': lambda b: b + ' os=' + b.split(' os=')[1].split(' ')[0],
                'extra': lambda b: b + ' x=1', 'drop_os': lambda b: b.replace(' os=' + b.split(' os=')[1].split(' ')[0], ''),
                'prefast': lambda b: b.replace('prefast=' + b.split('prefast=')[1][0], 'prefast=' + ('0' if b.split('prefast=')[1][0] != '0' else '1'), 1)}.items():
    r = hdr(f, name); hb.append((name, r['rc'], (r.get('reason') or '')[-80:]))
rec('header_tamper_resealed_refused', all(x[1] == 3 for x in hb), cases=hb)

# 9. M1: LBSHIFT (testhooks build) -> prefast mismatch
t1 = probe(P('LT.txt'), key=K('LT.key'), lib=LT)
t2 = probe(P('LT.txt'), key=K('LT.key'), lib=LT, env={'ZFAST14B_TEST_LBSHIFT': '1'})
rec('lbshift_refused_prefast', t1['rc'] == 0 and t2['rc'] == 3 and 'prefast' in (t2.get('reason') or ''), reason=t2.get('reason'))
t3 = probe(P('LT.txt'), key=K('LT.key'))
rec('testhooks_ckpt_refused_by_production', t3['rc'] == 3, reason=t3.get('reason'))

# 10. lock: a second process while the file is flocked
import fcntl
fd = os.open(P('A.txt'), os.O_RDONLY); fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
r = probe(P('A.txt'), key=K('A.key')); os.close(fd)
rec('flock_held_refused', r['rc'] == 3 and 'locked' in (r.get('reason') or ''), reason=r.get('reason'))

json.dump(R, open(P('attack_results.json'), 'w'), indent=1)
print(json.dumps(dict(n=len(R), fail=[k for k, v in R.items() if not v['ok']])))
