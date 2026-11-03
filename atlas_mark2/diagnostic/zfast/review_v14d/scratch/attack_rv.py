"""review_v14c adversarial tests on the PRODUCTION libzfast.v14c (test-hooks dylib only where noted).  Own v3 sealer (rvlib).
Light sessions: 10^14, H 61, Delta 0.012, D 2, W 1.  usage: attack_rv.py OUTDIR"""
import json, os, random, shutil, subprocess, sys, time, signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rvlib import *

OUT = sys.argv[1]; os.makedirs(OUT); KD = os.path.join(OUT, 'keys'); os.makedirs(KD, mode=0o700)
T0, H, DL, D = '100000000000000', '61.0', '0.012', 2
R = {}
def P(n): return os.path.join(OUT, n)
def K(n): return os.path.join(KD, n)
def pr(ck='-', key='-', U0='50.0', vn=8, role='gen', nonce='a' * 32, lib=L14C, env=None, W=1, timeout=600):
    try:
        return probe(lib, 'v14c', T0, U0, H, DL, D, W, ck, role=role, nonce=nonce, key=key, vn=vn, env=env, grid=100, timeout=timeout)
    except subprocess.TimeoutExpired:
        return dict(rc='timeout')
def info(r): return r.get('info') or {}
def rec(name, ok, **d):
    R[name] = dict(ok=bool(ok), **d); print(('OK   ' if ok else 'FAIL ') + name, json.dumps(d, default=str)[:600], flush=True)
def rs(r): return (r.get('reason') or '')[:200]

refA = pr(); refB = pr(U0='50.5')
A = pr(P('A.txt'), K('A.key'))
rec('A_fresh_identical', kk(A) == kk(refA) and info(A).get('key_created') == 1)
LA = read_lines(P('A.txt')); N = len(LA) - 1; hhA = hh_of(LA[0])

# ---------------- MJ1: cross-session splice under one key ----------------
copykey(K('A.key'), K('B.key'))
B = pr(P('B.txt'), K('B.key'), U0='50.5')
rec('B_new_header_existing_key_reported', B['rc'] == 0 and info(B).get('key_reused_new_header') == 1 and info(B).get('key_created') == 0 and kk(B) == kk(refB),
    note='stderr has EXISTING key note' if 'EXISTING' in B['stderr'] else 'no stderr note')
LB = read_lines(P('B.txt')); hhB = hh_of(LB[0])
same_idx = sum(1 for a, b in zip(LA[1:], LB[1:]) if a.split(' ')[1:6] == b.split(' ')[1:6])
diff_content = sum(1 for a, b in zip(LA[1:], LB[1:]) if body(a) != body(b))
rec('A_B_items_comparable', same_idx == N, same_index_tokens=same_idx, differing_bodies=diff_content)
# (a) B header + ALL of A's lines first + all of B's
for trial in range(3):
    rng = random.Random(trial); sel = rng.sample(LA[1:], 40)
    write_lines(P(f'spl{trial}.txt'), [LB[0]] + sel + LB[1:]); copykey(K('A.key'), K(f'spl{trial}.key'))
    r = pr(P(f'spl{trial}.txt'), K(f'spl{trial}.key'), U0='50.5', vn=8)
    rec(f'splice_A_into_B_{trial}', r['rc'] == 0 and kk(r) == kk(refB) and info(r).get('lines_rejected') == 40, rejected=info(r).get('lines_rejected'), loaded=info(r).get('items_loaded'))
# (b) B header + ONLY A's lines (all), nothing of B: A's lines must all be rejected -> everything recomputed
write_lines(P('splall.txt'), [LB[0]] + LA[1:]); copykey(K('A.key'), K('splall.key'))
r = pr(P('splall.txt'), K('splall.key'), U0='50.5')
rec('splice_only_A_lines_under_B_header', r['rc'] == 0 and kk(r) == kk(refB) and info(r).get('items_loaded') == 0, rejected=info(r).get('lines_rejected'))
# (c) A2 = second checkpoint of the SAME session parameters as A under A's key: identical item content, different hnonce
copykey(K('A.key'), K('A2.key')); A2 = pr(P('A2.txt'), K('A2.key'))
LA2 = read_lines(P('A2.txt'))
rec('A2_same_params_header_differs_only_in_hnonce', LA2[0].split(' hnonce=')[0] == LA[0].split(' hnonce=')[0] and LA2[0] != LA[0])
write_lines(P('splA2.txt'), [LA2[0]] + LA[1:]); copykey(K('A.key'), K('splA2.key'))
r = pr(P('splA2.txt'), K('splA2.key'))
rec('splice_same_params_other_file_rejected', r['rc'] == 0 and info(r).get('items_loaded') == 0 and info(r).get('lines_rejected') == N and kk(r) == kk(refA))
# (d) header transplant: A's lines under A2's header => rejected; A2's lines under A's header => rejected
write_lines(P('trans.txt'), [LA[0]] + LA2[1:]); copykey(K('A.key'), K('trans.key'))
r = pr(P('trans.txt'), K('trans.key'))
rec('transplant_lines_other_hnonce_rejected', r['rc'] == 0 and info(r).get('items_loaded') == 0 and kk(r) == kk(refA))
# (e) key-holder: A's content resealed for B's header (forgery) and mixed with B's own lines => conflicting duplicate
forged = [seal_item(body(l), K('A.key'), hhB) for l in LA[1:]]
write_lines(P('forge_dup.txt'), [LB[0]] + forged[:5] + LB[1:]); copykey(K('A.key'), K('forge_dup.key'))
r = pr(P('forge_dup.txt'), K('forge_dup.key'), U0='50.5')
rec('keyholder_conflicting_duplicate_refused', r['rc'] == 3 and 'conflicting duplicate' in rs(r), reason=rs(r))
# (f) key-holder: ONLY forged lines (all items) => the verify sample must catch it
write_lines(P('forge_all.txt'), [LB[0]] + forged); copykey(K('A.key'), K('forge_all.key'))
r = pr(P('forge_all.txt'), K('forge_all.key'), U0='50.5', vn=8)
rec('keyholder_forgery_all_items_caught_by_verify', r['rc'] == 3 and 'verification FAILED' in rs(r), reason=rs(r))
# (g) key-holder: ONE forged item among honest ones, verify 8 of 480: detection is probabilistic (8/480); record, not judged
cnt = 0
for t in range(10):
    x = 1 + random.Random(100 + t).randrange(N)
    Lf = LB[:]; Lf[x] = forged[x - 1]
    if body(Lf[x]) == body(LB[x]): continue
    write_lines(P(f'forge1_{t}.txt'), Lf); copykey(K('A.key'), K(f'forge1_{t}.key'))
    r = pr(P(f'forge1_{t}.txt'), K(f'forge1_{t}.key'), U0='50.5', vn=8); cnt += r['rc'] == 3
rec('keyholder_single_forgery_detect_rate_vn8 (info)', True, detected_of_10=cnt, expected=round(10 * 8 / N, 2))

# ---------------- index tampering ----------------
Lx = LA[:]; t = Lx[10].split(' '); t[1] = str(int(t[1]) + 1); Lx[10] = ' '.join(t)
write_lines(P('idx.txt'), Lx); copykey(K('A.key'), K('idx.key')); r = pr(P('idx.txt'), K('idx.key'))
rec('index_token_changed_rejected', r['rc'] == 0 and info(r).get('lines_rejected') == 1 and kk(r) == kk(refA))
# move line 10's content to position x=11 by key holder (x token AND seal changed, b/i/lo/hi of item 10)
b10 = body(LA[10]).split(' '); b10[1] = str(int(b10[1]) + 1)
Lx = LA[:]; Lx[12] = seal_item(' '.join(b10), K('A.key'), hhA); del Lx[11]
write_lines(P('idx2.txt'), Lx); copykey(K('A.key'), K('idx2.key')); r = pr(P('idx2.txt'), K('idx2.key'))
rec('keyholder_x_mismatch_first_b_plus_i_refused', r['rc'] == 3, reason=rs(r))
# key holder: item at position x claims (b, i) of another item AND its x -> lo/hi mismatch fatal or duplicate
b10 = body(LA[10]).split(' '); b11 = body(LA[11]).split(' '); bb = b10[:]; bb[1:4] = b11[1:4]
Lx = LA[:]; del Lx[11]; Lx.append(seal_item(' '.join(bb), K('A.key'), hhA))
write_lines(P('idx3.txt'), Lx); copykey(K('A.key'), K('idx3.key')); r = pr(P('idx3.txt'), K('idx3.key'))
rec('keyholder_item_relabelled_refused', r['rc'] == 3 or (r['rc'] == 0 and kk(r) == kk(refA)), rc=r['rc'], reason=rs(r))

# ---------------- duplicates, reordering, truncation, removal (no key needed) ----------------
Ld = LA + [LA[7]]; write_lines(P('dup.txt'), Ld); copykey(K('A.key'), K('dup.key')); r = pr(P('dup.txt'), K('dup.key'))
rec('nokey_identical_duplicate_makes_ckpt_unresumable', r['rc'] == 3 and 'identical duplicate' in rs(r), reason=rs(r))
Ld = LA[:1] + [LA[7]] + LA[1:]; write_lines(P('dup2.txt'), Ld); copykey(K('A.key'), K('dup2.key')); r = pr(P('dup2.txt'), K('dup2.key'))
rec('nokey_identical_duplicate_before_original', r['rc'] == 3, reason=rs(r))
Lr = LA[1:]; random.Random(5).shuffle(Lr); write_lines(P('shuf.txt'), [LA[0]] + Lr); copykey(K('A.key'), K('shuf.key')); r = pr(P('shuf.txt'), K('shuf.key'), vn=1000000)
rec('shuffled_identical_full_verify', r['rc'] == 0 and kk(r) == kk(refA) and info(r).get('items_loaded') == N)
Lr = [LA[0]] + [l for i, l in enumerate(LA[1:]) if random.Random(i).random() > 0.3]; write_lines(P('rm.txt'), Lr); copykey(K('A.key'), K('rm.key')); r = pr(P('rm.txt'), K('rm.key'))
rec('removed_30pct_identical', r['rc'] == 0 and kk(r) == kk(refA))
data = open(P('A.txt'), 'rb').read(); hl = data.index(b'\n') + 1
offs = [1, hl - 1, hl, hl + 1] + sorted(random.Random(77).sample(range(hl + 2, len(data)), 12))
for o in offs:
    fn = P(f'torn_{o}.txt'); open(fn, 'wb').write(data[:o]); copykey(K('A.key'), K(f'torn_{o}.key'))
    r = pr(fn, K(f'torn_{o}.key')); r2 = pr(fn, K(f'torn_{o}.key')) if r['rc'] == 0 else r
    ok = (r['rc'] == 0 and kk(r) == kk(refA) and kk(r2) == kk(refA) and r2['rc'] == 0 and info(r2).get('lines_written') == 0) or (r['rc'] == 3 and o < hl)
    rec(f'torn_{o}', ok, rc=r['rc'], loaded=info(r).get('items_loaded'), loaded2=info(r2).get('items_loaded'), w2=info(r2).get('lines_written'), reason=rs(r)[:80])
# torn line + NUL padding (power-loss style) + later appends
fn = P('nulpad.txt'); open(fn, 'wb').write(data[:hl + 3000] + b'\0' * 4096); copykey(K('A.key'), K('nulpad.key'))
r = pr(fn, K('nulpad.key')); r2 = pr(fn, K('nulpad.key'))
rec('nul_padded_tail_then_resume_twice', r['rc'] == 0 and r2['rc'] == 0 and kk(r) == kk(refA) and kk(r2) == kk(refA), rej2=info(r2).get('lines_rejected'))
# CRLF line endings
fn = P('crlf.txt'); open(fn, 'wb').write(data.replace(b'\n', b'\r\n')); copykey(K('A.key'), K('crlf.key')); r = pr(fn, K('crlf.key'))
rec('crlf_file_refused_header', r['rc'] == 3, reason=rs(r))
# leading blank line (no key): header no longer first
fn = P('blank.txt'); open(fn, 'wb').write(b'\n' + data); copykey(K('A.key'), K('blank.key')); r = pr(fn, K('blank.key'))
rec('leading_blank_line_refused (DoS, no key)', r['rc'] == 3, reason=rs(r))

# ---------------- header tampering ----------------
hdr = body(LA[0])
for name, new in [('hnonce_changed', hdr[:-1] + ('0' if hdr[-1] != '0' else '1')), ('hnonce_dropped', hdr.split(' hnonce=')[0]),
                  ('hnonce_upper', hdr.split(' hnonce=')[0] + ' hnonce=' + hdr.split(' hnonce=')[1].upper()),
                  ('hnonce_twice', hdr + ' hnonce=' + 'b' * 32), ('dyld_changed', hdr.replace('dyld_cache_uuid=e', 'dyld_cache_uuid=f')),
                  ('hw_changed', hdr.replace('hw_model=', 'hw_model=X')), ('extra_field', hdr.replace(' hooks=0', ' foo=1 hooks=0')),
                  ('wp_changed', hdr.replace(' wp=', ' wp=1')), ('nitems_changed', hdr.replace(' nitems=480', ' nitems=479')),
                  ('double_space', hdr.replace(' K=18', '  K=18'))]:
    Lh = [seal_hdr(new, K('A.key'))] + LA[1:]
    write_lines(P(f'h_{name}.txt'), Lh); copykey(K('A.key'), K(f'h_{name}.key')); r = pr(P(f'h_{name}.txt'), K(f'h_{name}.key'))
    if name == 'hnonce_changed':
        ok = r['rc'] == 0 and info(r).get('items_loaded') == 0 and kk(r) == kk(refA)
    elif name == 'double_space':
        ok = (r['rc'] == 0 and info(r).get('items_loaded') == 0 and kk(r) == kk(refA)) or r['rc'] == 3
    else:
        ok = r['rc'] == 3
    rec(f'keyholder_header_{name}', ok, rc=r['rc'], loaded=info(r).get('items_loaded'), reason=rs(r)[:140])
Lh = [LA[0].replace('hw_model=M', 'hw_model=N')] + LA[1:]
write_lines(P('h_nokey.txt'), Lh); copykey(K('A.key'), K('h_nokey.key')); r = pr(P('h_nokey.txt'), K('h_nokey.key'))
rec('nokey_header_tamper_refused', r['rc'] == 3 and 'not authenticated' in rs(r))

# ---------------- role / nonce / format crossover ----------------
shutil.copy(P('A.txt'), P('Arep.txt')); copykey(K('A.key'), K('Arep.key'))
r = pr(P('Arep.txt'), K('Arep.key'), role='replay'); rec('gen_file_as_replay_with_gen_key_refused', r['rc'] == 3 and 'role' in rs(r), reason=rs(r))
r = pr(P('Arep.txt'), K('Arep.key'), nonce='b' * 32); rec('other_nonce_refused', r['rc'] == 3 and 'nonce' in rs(r), reason=rs(r))
shutil.copy(P('A.txt'), P('Arep2.txt')); r = pr(P('Arep2.txt'), K('nokey_here.key'), role='replay'); rec('existing_ckpt_missing_key_refused', r['rc'] == 3, reason=rs(r))
v14b_ck = ZF + 'review_v14b/scratch/out_attack/A.txt'
if os.path.exists(v14b_ck):
    shutil.copy(v14b_ck, P('v14b.txt')); copykey(K('A.key'), K('v14b.key')); r = pr(P('v14b.txt'), K('v14b.key'))
    rec('v14b_format_refused', r['rc'] == 3, reason=rs(r))
# test-hooks checkpoint loaded by production
T = pr(P('T.txt'), K('T.key'), lib=L14CT); r = pr(P('T.txt'), K('T.key'))
rec('testhooks_ckpt_refused_by_production', T['rc'] == 0 and r['rc'] == 3, reason=rs(r))
r = pr(P('A.txt'), K('A.key'), lib=L14CT); rec('production_ckpt_refused_by_testhooks', r['rc'] == 3, reason=rs(r))

# ---------------- key file attacks ----------------
def keycase(name, mk):
    ck = P(f'k_{name}.txt'); kf = K(f'k_{name}.key'); mk(ck, kf)
    r = pr(ck, kf, timeout=20); return r
r = keycase('sym', lambda ck, kf: (shutil.copy(P('A.txt'), ck), os.symlink(K('A.key'), kf))); rec('key_symlink_refused', r['rc'] == 3, reason=rs(r))
r = keycase('m644', lambda ck, kf: (shutil.copy(P('A.txt'), ck), copykey(K('A.key'), kf), os.chmod(kf, 0o644))); rec('key_0644_refused', r['rc'] == 3, reason=rs(r))
r = keycase('m400', lambda ck, kf: (shutil.copy(P('A.txt'), ck), copykey(K('A.key'), kf), os.chmod(kf, 0o400))); rec('key_0400_ok', r['rc'] == 0 and kk(r) == kk(refA))
r = keycase('zero', lambda ck, kf: open(kf, 'wb').close() or os.chmod(kf, 0o600)); rec('key_0byte_empty_ckpt_refused', r['rc'] == 3 and '0-byte' in rs(r), reason=rs(r))
r = keycase('k33', lambda ck, kf: (shutil.copy(P('A.txt'), ck), open(kf, 'wb').write(keyb(K('A.key')) + b'x'), os.chmod(kf, 0o600))); rec('key_33byte_refused', r['rc'] == 3, reason=rs(r))
r = keycase('dir', lambda ck, kf: (shutil.copy(P('A.txt'), ck), os.mkdir(kf, 0o700))); rec('key_is_dir_refused', r['rc'] == 3, reason=rs(r))
r = keycase('hard', lambda ck, kf: (shutil.copy(P('A.txt'), ck), os.link(K('A.key'), kf))); rec('key_hardlink_accepted (same user; info)', True, rc=r['rc'])
r = keycase('fifo', lambda ck, kf: (shutil.copy(P('A.txt'), ck), os.mkfifo(kf, 0o600))); rec('key_fifo (hang?)', r['rc'] == 3, rc=r['rc'], reason=rs(r) if isinstance(r, dict) else '')
# key crash (test hooks) then rerun with production
r = pr(P('kc.txt'), K('kc.key'), lib=L14CT, env=dict(ZFAST14C_TEST_KEYCRASH='1'))
stray = [f for f in os.listdir(KD) if f.startswith('kc.key.tmp')]; kex = os.path.exists(K('kc.key')); cks = os.path.getsize(P('kc.txt')) if os.path.exists(P('kc.txt')) else None
r2 = pr(P('kc.txt'), K('kc.key'))
rec('keycrash_then_rerun', r['rc'] == 78 and not kex and len(stray) == 1 and r2['rc'] == 0 and kk(r2) == kk(refA), rc=r['rc'], stray=stray, rc2=r2['rc'], ckpt_size_after_crash=cks)

# ---------------- overlong ----------------
Lo = LA[:]; Lo.insert(50, 'I ' + 'x' * (64 << 20)); write_lines(P('over.txt'), Lo); copykey(K('A.key'), K('over.key'))
r = pr(P('over.txt'), K('over.key')); base = pr(P('A.txt'), K('A.key'))
rec('overlong_64MiB_line', r['rc'] == 0 and kk(r) == kk(refA) and info(r).get('lines_overlong') == 1, maxrss=r.get('maxrss_mb'), base_maxrss=base.get('maxrss_mb'))

# ---------------- provider / driver env pin ----------------
for var in ('ZFAST14C_TEST_ENVFAIL', 'ZFAST14C_TEST_KEYCRASH', 'ZFAST14_TEST_EXIT_AFTER', 'ZFAST14B_TEST_LBSHIFT', 'ZFAST14_GENERIC_KERNEL', 'ZFAST14D_TEST_WFAIL_AT', 'ZFAST14D_TEST_SYNCFAIL', 'ZFAST14D_TEST_RADIUS'):
    e = dict(os.environ, **{var: '1'}); e.pop('ZFAST_CKPT', None)
    p = subprocess.run(['nice', '-n', '19', PY, '-B', '-c', 'import sys; sys.path.insert(0, "' + ZF + 'atlas_v5za/lib"); import zfast_provider'], env=e, capture_output=True, text=True)
    rec(f'provider_refuses_{var}', p.returncode != 0 and 'test-hook' in p.stderr, rc=p.returncode)
# provider: verify 0 refused
e = dict(os.environ, ZFAST_CKPT=P('pv.txt'), ZFAST_CKPT_ROLE='gen', ZFAST_CKPT_NONCE='a' * 32, ZFAST_CKPT_KEY=K('pv.key'), ZFAST_CKPT_VERIFY='0')
p = subprocess.run(['nice', '-n', '19', PY, '-B', '-c', 'import sys; sys.path.insert(0, "' + ZF + 'atlas_v5za/lib"); import zfast_provider'], env=e, capture_output=True, text=True)
rec('provider_refuses_verify0', p.returncode != 0, tail=p.stderr[-160:])

json.dump(R, open(os.path.join(OUT, 'attack_results.json'), 'w'), indent=1)
print(json.dumps(dict(total=len(R), fail=[k for k, v in R.items() if not v['ok']])))
