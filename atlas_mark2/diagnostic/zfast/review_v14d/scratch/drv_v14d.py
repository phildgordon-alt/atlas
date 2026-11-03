"""review_v14d: own driver tests of atlas_v5za's new paths on a REVIEW COPY of the tree (scratch/v5za_copy; only KEYDIR changed so that
keys stay inside review_v14d).  10^16 window [T0, T0+10], H 91, Delta 0.008, --turing-grid, D 2, W 2, nice 19.  usage: drv_v14d.py
  D1 reference;  D2 generator SIGKILLed inside the Turing-grid stage (after gen_done) -> --resume;  D3 SIGKILLed during the certificate
  stage (certs non-empty, before gen_done) -> --resume;  D4 replay SIGKILLed during its session build -> --resume;  D5 replay I/O abort
  (RLIMIT_FSIZE on the resumed driver) -> rc 3, banner, then --resume;  D6 non-I/O generator refusal (tampered header) after an earlier
  I/O abort -> rc != 3;  D7 non-I/O replay refusal (replay checkpoint path is a FIFO) -> rc != 3;  D8 nonce file removed -> refused,
  no move;  D9 bogus cert planted in certs/ before a postbuild resume -> moved, never used.
Compares certs, zs.json, measurements and Turing grid with engine/regress_v1 zfast.compare_regenerated (read-only import)."""
import hashlib, json, os, resource, shutil, signal, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, '/Users/kiosk/atlas_mark2')
from engine.regress_v1 import zfast as ZR

HERE = Path(__file__).resolve().parent; DST = HERE / 'v5za_copy'; PY = '/Users/kiosk/projects/atlas-rerun/.venv/bin/python'
T0 = 10**16; LO, HI = str(T0), str(T0 + 10); BASE = DST / 'runs' / f'w{T0}'; LOGS = HERE / 'drv_logs'; LOGS.mkdir(exist_ok=True)
RES = {}
def env(extra=None):
    e = {k: v for k, v in os.environ.items() if not k.startswith(('ZFAST', 'PYTHONOPTIMIZE'))}
    e.update(ZFAST_THREADS='2', ZFAST_WORKERS='2', V4_LIM_GB='1.0', HOMEBREW_NO_AUTO_UPDATE='1'); e.update(extra or {}); return e
def cmd(name, resume=False):
    return ['nice', '-n', '19', PY, '-u', '-B', 'atlas_v5.py', str(T0), LO, HI, '--name', name, '--zs-step', '0.005', '--gen-timeout', '3000',
            '--wide', '--zfast-h', '91.0', '--zfast-delta', '0.008', '--turing-grid'] + (['--resume'] if resume else [])
def run(name, resume=False, pre=None, tag='x', extra=None):
    lf = open(LOGS / f'{name}_{tag}.log', 'a'); t = time.time()
    p = subprocess.run(cmd(name, resume), cwd=str(DST), env=env(extra), stdout=lf, stderr=subprocess.STDOUT, preexec_fn=pre, timeout=3600)
    return dict(rc=p.returncode, s=round(time.time() - t, 1), log=str(LOGS / f'{name}_{tag}.log'))
def popen(name, resume=False, tag='kill'):
    lf = open(LOGS / f'{name}_{tag}.log', 'a')
    return subprocess.Popen(cmd(name, resume), cwd=str(DST), env=env(), stdout=lf, stderr=subprocess.STDOUT)
def stages(run_, f='gen.jsonl'):
    p = run_ / f
    return [json.loads(l).get('stage') for l in open(p) if l.strip()] if p.exists() else []
def pid_of(pat):
    q = subprocess.run(['pgrep', '-f', pat], capture_output=True, text=True).stdout.split(); return [int(x) for x in q]
def kill_when(name, cond, pat, resume=False, limit=1800):
    run_ = BASE / name; p = popen(name, resume); t = time.time(); killed = None; st = None
    while p.poll() is None and time.time() - t < limit:
        if cond(run_):
            ps = pid_of(pat.format(run=run_))
            if ps:
                for q in ps: os.kill(q, signal.SIGKILL)
                killed = ps; st = stages(run_); break
        time.sleep(0.01)
    p.wait(); return dict(rc=p.returncode, killed=killed, stages=st)
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def gridsame(A, B): return all((A / 'turing_grid' / f).exists() and (B / 'turing_grid' / f).exists() and sha(A / 'turing_grid' / f) == sha(B / 'turing_grid' / f) for f in ('grid.npz', 'zeros_intervals.json'))
def sessions(run_, role='gen'):
    f = run_ / f'zfast_ckpt_{role}.txt.sessions.jsonl'; return [json.loads(l)['info'] for l in open(f)] if f.exists() else []
def drive(run_): return [json.loads(l) for l in open(run_ / 'drive.jsonl')] if (run_ / 'drive.jsonl').exists() else []
def replay_ok(run_):
    f = run_ / 'replay_check' / 'replay_check.json'
    if not f.exists(): return None
    j = json.load(open(f)); return dict(passed=j.get('passed'), zck=(j.get('zfast_ckpt') or {}).get('ok'))
def compare(A, B):
    c = ZR.compare_regenerated(dict(run=str(A)), B); return c['identical'] and gridsame(A, B), c
def rec(k, ok, **d):
    RES[k] = dict(ok=bool(ok), **d); print(('OK   ' if ok else 'FAIL ') + k, json.dumps(d, default=str)[:900], flush=True)
def banner(log): return 'CHECKPOINT I/O ERROR' in open(log, errors='replace').read()

# D1
r = run('ref'); A = BASE / 'ref'; rec('D1_reference', r['rc'] == 0 and replay_ok(A) == dict(passed=True, zck=True), **r)

# D2: kill inside the Turing grid stage (turing_grid dir exists, stage not yet logged)
k = kill_when('d2', lambda R: (R / 'turing_grid').exists() and 'turing_grid' not in stages(R), 'gen_target5.py {run}')
B = BASE / 'd2'; r = run('d2', resume=True, tag='resume'); same, c = compare(A, B)
moved = sorted(p.name for p in (B / 'gen_postbuild.attempt1').iterdir()) if (B / 'gen_postbuild.attempt1').exists() else []
ss = sessions(B)
rec('D2_kill_in_turing_grid_then_resume', k['killed'] and 'gen_done' in (k['stages'] or []) and r['rc'] == 0 and same and 'turing_grid' in moved
    and replay_ok(B) == dict(passed=True, zck=True) and len(ss) == 2 and ss[-1]['items_loaded'] == ss[-1]['items'] and ss[-1]['verified'] == 64,
    kill=k, resume=r, moved=moved, sessions=[(s['items_loaded'], s['items'], s['verified']) for s in ss])

# D3: kill during the certificate stage (certs non-empty, before gen_done)
k = kill_when('d3', lambda R: (R / 'certs').exists() and any((R / 'certs').glob('*.json')) and 'gen_done' not in stages(R), 'gen_target5.py {run}')
B = BASE / 'd3'; r = run('d3', resume=True, tag='resume'); same, c = compare(A, B)
moved = sorted(p.name for p in (B / 'gen_postbuild.attempt1').iterdir()) if (B / 'gen_postbuild.attempt1').exists() else []
oldc = sorted(p.name for p in (B / 'gen_postbuild.attempt1' / 'certs').glob('*')) if moved else []
rec('D3_kill_in_cert_stage_then_resume', k['killed'] and r['rc'] == 0 and same and 'certs' in moved and replay_ok(B) == dict(passed=True, zck=True),
    kill=k, resume=r, moved=moved, old_certs=len(oldc))

# D9: plant a bogus certificate after the kill; it must be moved and never reach the replay / summary
k = kill_when('d9', lambda R: (R / 'zs.json').exists(), 'gen_target5.py {run}')
B = BASE / 'd9'; (B / 'certs').mkdir(exist_ok=True); shutil.copy(next((A / 'certs').glob('*.json')), B / 'certs' / 'cert_BOGUS_PLANTED.json')
r = run('d9', resume=True, tag='resume'); same, c = compare(A, B)
rec('D9_planted_cert_moved_not_used', r['rc'] == 0 and same and not (B / 'certs' / 'cert_BOGUS_PLANTED.json').exists()
    and (B / 'gen_postbuild.attempt1' / 'certs' / 'cert_BOGUS_PLANTED.json').exists() and replay_ok(B) == dict(passed=True, zck=True), resume=r)

# D4: replay killed during its session build -> --resume (the replay resumes ITS checkpoint)
k = kill_when('d4', lambda R: (R / 'zfast_ckpt_replay.txt').exists() and os.path.getsize(R / 'zfast_ckpt_replay.txt') > 200000, 'replay_target5.py {run}')
B = BASE / 'd4'; r = run('d4', resume=True, tag='resume'); same, c = compare(A, B); rs = sessions(B, 'replay')
rec('D4_replay_killed_then_resume', k['killed'] and r['rc'] == 0 and same and replay_ok(B) == dict(passed=True, zck=True) and rs and rs[-1]['items_loaded'] > 0,
    kill=k, resume=r, replay_sessions=[(s['items_loaded'], s['items'], s['verified']) for s in rs])

# D5: replay I/O abort.  Kill the replay early, then resume the driver under RLIMIT_FSIZE (= current replay ckpt + 300 kB)
k = kill_when('d5', lambda R: (R / 'zfast_ckpt_replay.txt').exists() and os.path.getsize(R / 'zfast_ckpt_replay.txt') > 100000, 'replay_target5.py {run}')
B = BASE / 'd5'; lim = os.path.getsize(B / 'zfast_ckpt_replay.txt') + 300000
def pre():
    signal.signal(signal.SIGXFSZ, signal.SIG_IGN); resource.setrlimit(resource.RLIMIT_FSIZE, (lim, lim))
r1 = run('d5', resume=True, pre=pre, tag='limited'); dj = drive(B); ab = [x for x in dj if x.get('stage') == 'ckpt_io_abort']
r2 = run('d5', resume=True, tag='resume'); same, c = compare(A, B)
rec('D5_replay_io_abort_rc3_then_resume', k['killed'] and r1['rc'] == 3 and len(ab) == 1 and ab[0].get('role') == 'replay' and banner(r1['log']) and r2['rc'] == 0 and same
    and replay_ok(B) == dict(passed=True, zck=True), limited=r1, resume=r2, abort=(ab[0]['error'][:200] if ab else None))

# D6: generator I/O abort (rc 3), then a NON-I/O refusal (tampered checkpoint header) must not exit 3
B = BASE / 'd6'
def pre6():
    signal.signal(signal.SIGXFSZ, signal.SIG_IGN); resource.setrlimit(resource.RLIMIT_FSIZE, (900000, 900000))
r1 = run('d6', pre=pre6, tag='limited')
ck = B / 'zfast_ckpt_gen.txt'; d = open(ck, 'rb').read(); i = d.index(b' T0='); open(ck, 'wb').write(d[:i + 4] + (b'2' if d[i + 4:i + 5] != b'2' else b'3') + d[i + 5:])
r2 = run('d6', resume=True, tag='tampered'); dj = drive(B)
rec('D6_io_abort_rc3_then_nonio_refusal_not_rc3', r1['rc'] == 3 and r2['rc'] not in (0, 3) and sum(x.get('stage') == 'ckpt_io_abort' for x in dj) == 1, limited=r1, tampered=r2,
    tail=open(r2['log'], errors='replace').read()[-300:])

# D7: non-I/O refusal of the replay (its checkpoint path is a FIFO) must not exit 3
k = kill_when('d7', lambda R: 'turing_grid' in stages(R), 'atlas_v5.py {T0} .* --name d7'.replace('{T0}', str(T0)))
B = BASE / 'd7'
for q in pid_of(f'replay_target5.py {B}'): os.kill(q, signal.SIGKILL)
time.sleep(3); fifo_placed = False
if not (B / 'zfast_ckpt_replay.txt').exists() and not (B / 'replay_check').exists(): os.mkfifo(B / 'zfast_ckpt_replay.txt'); fifo_placed = True
r = run('d7', resume=True, tag='fifo'); dj = drive(B)
refs7 = [json.loads(l) for l in open(B / 'zfast_ckpt_replay.txt.refusals.jsonl')] if (B / 'zfast_ckpt_replay.txt.refusals.jsonl').exists() else []
rec('D7_replay_fifo_refusal_not_rc3', fifo_placed and r['rc'] != 3 and not any(x.get('stage') == 'ckpt_io_abort' for x in dj) and (replay_ok(B) or {}).get('passed') is not True
    and any('regular' in x.get('error', '') for x in refs7), fifo_placed=fifo_placed, kill=k, run=r, replay=replay_ok(B), refusals=[x.get('error', '')[:120] for x in refs7])

# D8: nonce file removed after a postbuild death -> refused, nothing moved
k = kill_when('d8', lambda R: (R / 'zs.json').exists(), 'gen_target5.py {run}')
B = BASE / 'd8'; (B / 'zfast_ckpt_nonce.txt').rename(B / 'zfast_ckpt_nonce.txt.moved_by_review')
r = run('d8', resume=True, tag='nononce')
rec('D8_nonce_removed_refused_no_move', r['rc'] != 0 and not (B / 'gen_postbuild.attempt1').exists() and (B / 'zs.json').exists(), run=r,
    tail=open(r['log'], errors='replace').read()[-300:], new_nonce_file_created=(B / 'zfast_ckpt_nonce.txt').exists())

json.dump(RES, open(HERE / 'drv_v14d_results.json', 'w'), indent=1, default=str)
print(json.dumps(dict(total=len(RES), fail=[k for k, v in RES.items() if not v['ok']])))
