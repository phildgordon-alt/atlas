"""review_v14d: own attacks on the paths NEW in v14d (production libzfast.v14d unless noted; test-hooks dylib only where noted).
Light sessions 10^14 (H 61, Delta 0.012, D 2); the I/O-abort cases use W 2.  Own v3 sealer (rvlib).  usage: attack_v14d.py OUTDIR
Sections: DUP (identical-duplicate ignore), NUL, HDR (byte-exact header), PATH (FIFO / device / dir), IO (real partial writes via
RLIMIT_FSIZE + SIGXFSZ ignored; newline-repair failure; header-write failure), HOOK (test-hooks WFAIL/SYNCFAIL/RADIUS), RAD (production
resume of key-resealed nonzero radii of every width 1..30), PROV (provider/driver hook refusal)."""
import json, os, random, resource, shutil, signal, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rvlib import *

OUT = sys.argv[1]; os.makedirs(OUT); KD = os.path.join(OUT, 'keys'); os.makedirs(KD, mode=0o700)
T0, H, DL, D = '100000000000000', '61.0', '0.012', 2
L14C_OLD = ZF + 'bin/libzfast.v14c.dylib'
R = {}
def P(n): return os.path.join(OUT, n)
def K(n): return os.path.join(KD, n)
def pr(ck='-', key='-', U0='50.0', vn=8, role='gen', nonce='a' * 32, lib=L14C, env=None, W=1, timeout=600):
    return probe(lib, 'v14c', T0, U0, H, DL, D, W, ck, role=role, nonce=nonce, key=key, vn=vn, env=env, grid=100, timeout=timeout)
def info(r): return r.get('info') or {}
def rec(name, ok, **d):
    R[name] = dict(ok=bool(ok), **d); print(('OK   ' if ok else 'FAIL ') + name, json.dumps(d, default=str)[:700], flush=True)
def rs(r): return (r.get('reason') or '')[:300]
def raw(p): return open(p, 'rb').read()
def wraw(p, b): open(p, 'wb').write(b)

ref = pr(); ref8 = ref
A = pr(P('A.txt'), K('A.key'))
rec('A_fresh_identical_and_dir_synced', A['rc'] == 0 and kk(A) == kk(ref) and info(A).get('ckpt_dir_synced') == 1 and info(A).get('ckpt_io_policy') == 'abort',
    lines_nul=info(A).get('lines_nul'))
LA = read_lines(P('A.txt')); N = len(LA) - 1; hhA = hh_of(LA[0]); BA = raw(P('A.txt'))
def case(tag, lines=None, data=None, **kw):
    ck, kf = P(tag + '.txt'), K(tag + '.key'); copykey(K('A.key'), kf)
    if lines is not None: write_lines(ck, lines)
    else: wraw(ck, data)
    return pr(ck, kf, **kw), ck, kf

# ---------------- DUP ----------------
r, ck, kf = case('dup1', LA + [LA[5]])
rec('DUP_append_one_identical_ignored', r['rc'] == 0 and kk(r) == kk(ref) and info(r).get('lines_duplicate') == 1 and info(r).get('items_loaded') == N, dup=info(r).get('lines_duplicate'))
r, ck, kf = case('dup2', [LA[0], LA[7]] + LA[1:])
rec('DUP_before_original_ignored', r['rc'] == 0 and kk(r) == kk(ref) and info(r).get('lines_duplicate') == 1)
r, ck, kf = case('dup3', LA + LA[1:])
rec('DUP_whole_file_doubled', r['rc'] == 0 and kk(r) == kk(ref) and info(r).get('lines_duplicate') == N, dup=info(r).get('lines_duplicate'))
r, ck, kf = case('dup4', LA + [LA[9]] * 3, vn=1000000)
rec('DUP_triple_copy_verify_all', r['rc'] == 0 and kk(r) == kk(ref) and info(r).get('lines_duplicate') == 3 and info(r).get('verified') == N)
# torn prefix of line 9 (newline-terminated garbage) then a full copy
r, ck, kf = case('dup5', LA + [LA[9][:len(LA[9]) // 2], LA[9]])
rec('DUP_torn_prefix_then_full_copy', r['rc'] == 0 and kk(r) == kk(ref) and info(r).get('lines_duplicate') == 1 and info(r).get('lines_rejected') == 1)
# partial checkpoint + a duplicate of a loaded line, resumed twice (the second time the file is complete)
cut = BA[:int(len(BA) * 0.45)]; last_full = cut[:cut.rindex(b'\n') + 1]; copies = last_full.split(b'\n')[3] + b'\n'
r, ck, kf = case('dup6', data=cut + b'\n' + copies, W=2)
r2 = pr(ck, kf, vn=1000000)
rec('DUP_partial_plus_dup_then_resume_twice', r['rc'] == 0 and r2['rc'] == 0 and kk(r) == kk(ref) == kk(r2) and info(r).get('lines_duplicate') == 1
    and info(r2).get('lines_duplicate') == 1 and info(r2).get('items_loaded') == N, r_dup=info(r).get('lines_duplicate'), r2_loaded=info(r2).get('items_loaded'))
# key holder: conflicting duplicate (one token changed, resealed) still fatal; also when the conflicting copy comes FIRST
t = body(LA[11]).split(' '); t[6] = t[6].replace('p', 'p', 1); i = 8; t[i] = t[i] + '1' if not t[i].endswith('1') else t[i][:-1] + '3'
forged = seal_item(' '.join(t), K('A.key'), hhA)
r, ck, kf = case('dup7', LA + [forged]); rec('DUP_keyholder_conflicting_after_still_fatal', r['rc'] == 3 and 'conflicting duplicate' in rs(r), reason=rs(r))
r, ck, kf = case('dup8', [LA[0], forged] + LA[1:]); rec('DUP_keyholder_conflicting_before_still_fatal', r['rc'] == 3, reason=rs(r))
# a duplicate whose seal differs (bit flip in the tag) is NOT authenticated: rejected, not counted as duplicate
bad = LA[13][:-1] + ('0' if LA[13][-1] != '0' else '1')
r, ck, kf = case('dup9', LA + [bad]); rec('DUP_bad_tag_copy_rejected_not_dup', r['rc'] == 0 and info(r).get('lines_rejected') == 1 and info(r).get('lines_duplicate') == 0 and kk(r) == kk(ref))
# same body, other x token (key holder): x mismatch is fatal before the duplicate classification
tb = body(LA[13]).split(' '); x13 = int(tb[1]); tb[1] = str(x13 + 1); f2 = seal_item(' '.join(tb), K('A.key'), hhA, x13 + 1)
r, ck, kf = case('dup10', LA + [f2]); rec('DUP_keyholder_same_body_other_x_fatal', r['rc'] == 3 and 'first[b] + i' in rs(r) or r['rc'] == 3, reason=rs(r))

# ---------------- NUL ----------------
b = body(LA[20]); nb = b[:40] + '\x00' + b[41:]
r, ck, kf = case('nul1', LA[:20] + [seal_item(nb, K('A.key'), hhA)] + LA[21:])
rec('NUL_keyholder_sealed_line_with_nul_rejected', r['rc'] == 0 and kk(r) == kk(ref) and info(r).get('lines_nul') == 1 and info(r).get('items_loaded') == N - 1, nul=info(r).get('lines_nul'))
hb = body(LA[0]); hn = hb[:30] + '\x00' + hb[31:]
r, ck, kf = case('nul2', [seal_hdr(hn, K('A.key'))] + LA[1:]); rec('NUL_in_header_refused', r['rc'] == 3 and 'NUL' in rs(r), reason=rs(r))
r, ck, kf = case('nul3', data=BA + b'\x00' * 8192); r2 = pr(ck, kf, vn=1000000)
rec('NUL_padded_tail_8KiB_resume_twice', r['rc'] == 0 and r2['rc'] == 0 and kk(r) == kk(ref) == kk(r2) and info(r).get('lines_nul') == 1, nul=info(r).get('lines_nul'), nul2=info(r2).get('lines_nul'))
off = BA.index(b'\n', len(BA) // 3) + 1; z = BA[:off + 100] + b'\x00' * 4096 + BA[off + 4196:]
r, ck, kf = case('nul4', data=z); rec('NUL_zero_block_mid_file', r['rc'] == 0 and kk(r) == kk(ref), nul=info(r).get('lines_nul'), rej=info(r).get('lines_rejected'), loaded=info(r).get('items_loaded'))

# ---------------- HDR ----------------
for tag, f in (('hdr_dspace', lambda s: s.replace(' ', '  ', 1)), ('hdr_trail', lambda s: s.split(' hnonce=')[0] + '  hnonce=' + s.split(' hnonce=')[1]),
               ('hdr_tab', lambda s: s.replace(' ', '\t', 1))):
    r, ck, kf = case(tag, [seal_hdr(f(body(LA[0])), K('A.key'))] + LA[1:])
    rec(f'HDR_{tag}_resealed_refused', r['rc'] == 3, reason=rs(r))

# ---------------- PATH ----------------
def timed(ck, kf, timeout=60):
    t = time.time(); r = probe(L14C, 'v14c', T0, '50.0', H, DL, D, 1, ck, nonce='a' * 32, key=kf, grid=0, timeout=timeout); return r, round(time.time() - t, 1)
os.mkfifo(P('fifo.txt')); copykey(K('A.key'), K('fifo.key')); r, dt = timed(P('fifo.txt'), K('fifo.key'))
rec('PATH_ckpt_fifo_refused_no_hang', r['rc'] == 3 and 'regular' in rs(r), wall=dt, reason=rs(r))
shutil.copy(P('A.txt'), P('kf.txt')); os.mkfifo(K('kf.key'), 0o600); r, dt = timed(P('kf.txt'), K('kf.key'))
rec('PATH_key_fifo_refused_no_hang', r['rc'] == 3 and 'regular' in rs(r), wall=dt, reason=rs(r))
os.symlink('/dev/null', P('devnull.txt')); copykey(K('A.key'), K('dn.key')); r, dt = timed(P('devnull.txt'), K('dn.key'))
rec('PATH_ckpt_symlink_to_dev_null_refused', r['rc'] == 3, wall=dt, reason=rs(r))
os.mkdir(P('dir.txt')); copykey(K('A.key'), K('dir.key')); r, dt = timed(P('dir.txt'), K('dir.key'))
rec('PATH_ckpt_is_dir_refused', r['rc'] == 3, reason=rs(r))
os.symlink(P('A.txt'), P('symA.txt')); copykey(K('A.key'), K('symA.key')); r, dt = timed(P('symA.txt'), K('symA.key'))
rec('PATH_ckpt_symlink_to_regular_followed (info, unchanged from v14c)', r['rc'] == 0, loaded=info(r).get('items_loaded'))
os.symlink(P('nonexist_target.txt'), P('dangle.txt')); copykey(K('A.key'), K('dangle.key')); r, dt = timed(P('dangle.txt'), K('dangle.key'))
rec('PATH_dangling_symlink_creates_target (info, unchanged from v14c)', True, rc=r['rc'], target_created=os.path.exists(P('nonexist_target.txt')))

# ---------------- IO: real partial writes ----------------
def probe_lim(ck, kf, limit, W=2, lib=L14C, env=None, vn=8, timeout=900):
    def pre():
        signal.signal(signal.SIGXFSZ, signal.SIG_IGN); resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit))
    e = {k: v for k, v in os.environ.items() if not k.startswith('ZFAST')}; e.update(env or {})
    cmd = ['nice', '-n', '19', PY, '-B', PROBE, lib, 'v14c', T0, '50.0', H, DL, '18', '12', str(D), str(W), ck, '47.0', '0.004', '100', 'gen', 'a' * 32, kf, str(vn)]
    t = time.time(); p = subprocess.run(cmd, env=e, capture_output=True, text=True, timeout=timeout, preexec_fn=pre)
    try: r = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception: r = dict(ok=False, error='no json')
    r['rc'] = p.returncode; r['stderr'] = p.stderr[-400:]; r['wall'] = round(time.time() - t, 2); return r
hdr_len = BA.index(b'\n') + 1; ends = [i + 1 for i, c in enumerate(BA) if c == 10]
lims = [('mid_line_30pct', int(len(BA) * 0.30) + 17), ('mid_line_70pct', int(len(BA) * 0.70) + 3), ('exact_line_end_k40', ends[40]),
        ('exact_header_end', hdr_len), ('one_byte_after_header', hdr_len + 1), ('last_byte_missing', len(BA) - 1)]
for tag, lim in lims:
    ck, kf = P(f'io_{tag}.txt'), K(f'io_{tag}.key')
    r = probe_lim(ck, kf, lim, W=(2 if tag.startswith('mid') else 1))
    size = os.path.getsize(ck); data = raw(ck); full = data.count(b'\n')
    torn = not data.endswith(b'\n'); tail = data[data.rindex(b'\n') + 1:] if torn else b''
    torn_complete = torn and len(tail) > 66 and tail[-66:-64] == b' #'
    r2 = pr(ck, kf, W=1); r3 = pr(ck, kf, vn=1000000, W=2)
    ok = (r['rc'] == 3 and rs(r).startswith('CKPT-IO-ABORT') and size == lim and r2['rc'] == 0 and r3['rc'] == 0 and kk(r2) == kk(ref) == kk(r3)
          and info(r2).get('items_loaded') == full - 1 + torn_complete and info(r2).get('lines_rejected') == (1 if torn and not torn_complete else 0) and info(r3).get('items_loaded') == N)
    rec(f'IO_rlimit_{tag}', ok, limit=lim, size=size, torn=torn, torn_complete=torn_complete, abort_wall=r['wall'], reason=rs(r)[:200], r2_loaded=info(r2).get('items_loaded'),
        r2_rej=info(r2).get('lines_rejected'), r3_loaded=info(r3).get('items_loaded'))
# header write fails (limit inside the header): session refused; the file holds a torn header => a rerun refuses (needs a fresh name)
ck, kf = P('io_hdr.txt'), K('io_hdr.key'); r = probe_lim(ck, kf, 100); r2 = pr(ck, kf)
rec('IO_rlimit_inside_header (info: fresh name needed, 0 items lost)', r['rc'] == 3 and rs(r).startswith('CKPT-IO-ABORT') and r2['rc'] == 3, reason=rs(r)[:160], rerun_reason=rs(r2)[:200])
# newline repair fails: torn file, limit = its size
cutb = BA[:int(len(BA) * 0.5) + 11]; ck, kf = P('io_nl.txt'), K('io_nl.key'); wraw(ck, cutb); copykey(K('A.key'), kf)
r = probe_lim(ck, kf, len(cutb)); same_after = raw(ck) == cutb; r2 = pr(ck, kf, W=2)
rec('IO_newline_repair_fails_file_unchanged_then_resume', r['rc'] == 3 and 'newline repair' in rs(r) and same_after and r2['rc'] == 0 and kk(r2) == kk(ref), reason=rs(r)[:200])
# limit reached during a RESUME (after load): appends fail, file still resumable
ck, kf = P('io_res.txt'), K('io_res.key'); wraw(ck, BA[:ends[100]]); copykey(K('A.key'), kf)
r = probe_lim(ck, kf, ends[250] + 50); r2 = pr(ck, kf, vn=1000000)
rec('IO_rlimit_during_resume_then_resume', r['rc'] == 3 and rs(r).startswith('CKPT-IO-ABORT') and r2['rc'] == 0 and kk(r2) == kk(ref) and (info(r2).get('items_loaded') or 0) > 100,
    loaded=info(r2).get('items_loaded'), reason=rs(r)[:160])

# ---------------- HOOK (test-hooks dylib) ----------------
refT = pr(lib=L14CT)
rec('HOOK_testhooks_no_env_equals_v14', refT['rc'] == 0 and kk(refT) == kk(ref))
for tag, env in (('wfail1', dict(ZFAST14D_TEST_WFAIL_AT='1')), ('wfail200', dict(ZFAST14D_TEST_WFAIL_AT='200'))):
    ck, kf = P(f'h_{tag}.txt'), K(f'h_{tag}.key')
    r = pr(ck, kf, lib=L14CT, env=env, W=2); r2 = pr(ck, kf, lib=L14CT, W=2, vn=1000000)
    rec(f'HOOK_{tag}_abort_then_resume', r['rc'] == 3 and rs(r).startswith('CKPT-IO-ABORT') and r2['rc'] == 0 and kk(r2) == kk(ref),
        reason=rs(r)[:200], loaded=info(r2).get('items_loaded'), rejected=info(r2).get('lines_rejected'))
# SYNCFAIL needs a session longer than 1 s (the flusher's first sync): 10^18, D 2
T18 = ('1000000000000000000', '7.25', '40.0', '0.02'); ref18 = probe(L14, 'v14', T18[0], T18[1], T18[2], T18[3], 2, 1, grid=100)
for tag, env in (('syncfail1', dict(ZFAST14D_TEST_SYNCFAIL='1')), ('syncfail3', dict(ZFAST14D_TEST_SYNCFAIL='3'))):
    ck, kf = P(f'h_{tag}.txt'), K(f'h_{tag}.key')
    r = probe(L14CT, 'v14c', T18[0], T18[1], T18[2], T18[3], 2, 2, ck, nonce='a' * 32, key=kf, env=env, grid=100)
    r2 = probe(L14CT, 'v14c', T18[0], T18[1], T18[2], T18[3], 2, 2, ck, nonce='a' * 32, key=kf, vn=1000000, grid=100)
    rec(f'HOOK_{tag}_1e18_abort_then_resume', r['rc'] == 3 and rs(r).startswith('CKPT-IO-ABORT') and r2['rc'] == 0 and kk(r2) == kk(ref18),
        reason=rs(r)[:200], loaded=info(r2).get('items_loaded'), items=info(r2).get('items'), fsec=info(r).get('sec_fast'))
# TEST_RADIUS: fresh / partial resume / verify-all all identical among themselves; the radii really are nonzero in the file
envR = dict(ZFAST14D_TEST_RADIUS='1'); ck, kf = P('h_rad.txt'), K('h_rad.key')
a = pr(ck, kf, lib=L14CT, env=envR); a0 = pr(lib=L14CT, env=envR)
d = raw(ck); cutr = d[:int(len(d) * 0.4)]; ckp, kfp = P('h_radp.txt'), K('h_radp.key'); wraw(ckp, cutr); copykey(kf, kfp)
b2 = pr(ckp, kfp, lib=L14CT, env=envR, vn=1000000, W=2); c2 = pr(ck, kf, lib=L14CT, env=envR, vn=1000000)
nz = sum(1 for l in d.decode().split('\n')[1:] for q in [l.split(' ')] if len(q) > 12 and q[10] != '0')
rec('HOOK_radius_fresh_resume_verifyall_consistent', all(x['rc'] == 0 for x in (a, a0, b2, c2)) and kk(a) == kk(a0) == kk(b2) == kk(c2) and kk(a) != kk(ref)
    and info(c2).get('verified') == N, lines_with_nonzero_first_radius=nz, loaded_partial=info(b2).get('items_loaded'))

# ---------------- RAD: production resume of resealed nonzero radii (every width 1..30) ----------------
rng = random.Random(7); out = [LA[0]]; nforged = 0
for li, l in enumerate(LA[1:]):
    t = body(l).split(' ')
    if li % 3 == 0:
        k = 0; j = 8
        while j + 3 < len(t) and ':' not in t[j]:
            w = 1 + (li + k) % 30; m = 1 if w == 1 else ((1 << (w - 1)) | (rng.getrandbits(w - 1)) | 1)
            if t[j] != '0': t[j + 2] = format(m, 'x'); t[j + 3] = format(-(600 + k), 'x').replace('0x', '') if False else '-' + format(600 + k, 'x'); nforged += 1
            j += 4; k += 1
    out.append(seal_item(' '.join(t), K('A.key'), hhA) if li % 3 == 0 else l)
r, ck, kf = case('rad', out, vn=0)
rec('RAD_production_loads_resealed_radii_all_widths', r['rc'] == 0 and info(r).get('items_loaded') == N, forged_balls=nforged, reason=rs(r))
r30 = [LA[0]] + [seal_item(' '.join((lambda t: t[:10] + ['3fffffff', '-1f4'] + t[12:])(body(l).split(' '))), K('A.key'), hhA) if i == 0 else l for i, l in enumerate(LA[1:])]
r, ck, kf = case('rad30', r30, vn=0)
rec('RAD_production_30bit_radius_loads (v14c refused this)', r['rc'] == 0 and info(r).get('items_loaded') == N, reason=rs(r))
r31 = [LA[0]] + [seal_item(' '.join((lambda t: t[:10] + ['7fffffff', '-1f4'] + t[12:])(body(l).split(' '))), K('A.key'), hhA) if i == 0 else l for i, l in enumerate(LA[1:])]
r, ck, kf = case('rad31', r31, vn=0)
rec('RAD_production_31bit_radius_refused', r['rc'] == 3 and 'MJ-C1' in rs(r), reason=rs(r))
rev = [LA[0]] + [seal_item(' '.join((lambda t: t[:10] + ['2', '-1f4'] + t[12:])(body(l).split(' '))), K('A.key'), hhA) if i == 0 else l for i, l in enumerate(LA[1:])]
r, ck, kf = case('radeven', rev, vn=0)
rec('RAD_production_even_radius_mantissa_refused', r['rc'] == 3, reason=rs(r))
rbig = [LA[0]] + [seal_item(' '.join((lambda t: t[:10] + ['1', '10000000000'] + t[12:])(body(l).split(' '))), K('A.key'), hhA) if i == 0 else l for i, l in enumerate(LA[1:])]
r, ck, kf = case('radbig', rbig, vn=0)
rec('RAD_production_radius_exp_2^40_refused_no_crash', r['rc'] == 3, reason=rs(r))

# ---------------- PROV ----------------
for var in ('ZFAST14D_TEST_WFAIL_AT', 'ZFAST14D_TEST_SYNCFAIL', 'ZFAST14D_TEST_RADIUS', 'ZFAST14D_TEST_ANYTHING'):
    e = dict(os.environ, **{var: '1'}); e.pop('ZFAST_CKPT', None)
    p = subprocess.run(['nice', '-n', '19', PY, '-B', '-c', 'import sys; sys.path.insert(0, "' + ZF + 'atlas_v5za/lib"); import zfast_provider'], env=e, capture_output=True, text=True)
    q = subprocess.run(['nice', '-n', '19', PY, '-B', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'v5za_copy', 'atlas_v5.py'), '1', '1', '2', '--name', 'never'], env=e, capture_output=True, text=True, cwd=OUT)
    rec(f'PROV_provider_and_driver_refuse_{var}', p.returncode != 0 and 'test-hook' in p.stderr and q.returncode != 0 and 'test-hook' in q.stderr, prc=p.returncode, drc=q.returncode)

json.dump(R, open(os.path.join(OUT, 'attack_v14d_results.json'), 'w'), indent=1)
print(json.dumps(dict(total=len(R), fail=[k for k, v in R.items() if not v['ok']])))
