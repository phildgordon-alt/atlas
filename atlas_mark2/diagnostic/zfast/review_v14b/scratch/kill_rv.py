"""reviewer kill/resume + live-lock test at 10^18 (u0 7.25, H 40, Delta 0.02, D 2): SIGKILL a W=2 checkpointed session at random times,
check the flock is held mid-run (after the dup'd read fd was closed), resume (W varies) until complete; final state must equal the
uninterrupted v14 reference.  usage: kill_rv.py OUTDIR"""
import fcntl, json, os, random, signal, subprocess, sys, time
ZF = '/Users/kiosk/atlas_mark2/diagnostic/zfast/'
PY = '/Users/kiosk/projects/atlas-rerun/.venv/bin/python'; PROBE = ZF + 'tools/m12_probe.py'
L14, L14B = ZF + 'bin/libzfast.v14.dylib', ZF + 'bin/libzfast.v14b.dylib'
OUT = sys.argv[1]; os.makedirs(OUT); KD = os.path.join(OUT, 'keys'); os.makedirs(KD, mode=0o700)
T0, U0, H, DL, D = '1000000000000000000', '7.25', '40.0', '0.02', '2'
def cmd(lib, mode, W, ck='-', key='-', vn='8'):
    return ['nice', '-n', '19', PY, '-B', PROBE, lib, mode, T0, U0, H, DL, '18', '12', D, str(W), ck, '4.25', '0.004', '200', 'gen', 'd' * 32, key, vn]
env = {k: v for k, v in os.environ.items() if not k.startswith('ZFAST')}
def run(c):
    p = subprocess.run(c, capture_output=True, text=True, env=env); r = json.loads(p.stdout.strip().splitlines()[-1]); r['rc'] = p.returncode; return r
def kk(r): return (r.get('state_sha256'), (r.get('grid') or {}).get('sha256'), r.get('rows_sha256'), tuple(r.get('Z') or ()))
ref = run(cmd(L14, 'v14', 1))
rng = random.Random(7); results = []
for trial in range(3):
    ck = os.path.join(OUT, f'k{trial}.txt'); key = os.path.join(KD, f'k{trial}.key'); kills = 0; lock_held = []
    for attempt in range(3):
        p = subprocess.Popen(cmd(L14B, 'v14b', 2, ck, key), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        time.sleep(rng.uniform(1.0, 3.0))
        if p.poll() is None and os.path.exists(ck):
            fd = os.open(ck, os.O_RDONLY)
            try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB); lock_held.append(False); fcntl.flock(fd, fcntl.LOCK_UN)
            except BlockingIOError: lock_held.append(True)
            os.close(fd)
            p.send_signal(signal.SIGKILL); kills += 1
        p.wait()
    nl = sum(1 for _ in open(ck)) if os.path.exists(ck) else 0
    r = run(cmd(L14B, 'v14b', rng.choice((1, 3, 4)), ck, key))
    ok = r['rc'] == 0 and kk(r) == kk(ref)
    row = dict(trial=trial, kills=kills, lock_held_midrun=lock_held, lines_before_final=nl, final_loaded=r['info'].get('items_loaded'),
               items=r['info'].get('items'), rejected=r['info'].get('lines_rejected'), dup=r['info'].get('lines_duplicate'), verified=r['info'].get('verified'), identical=ok)
    results.append(row); print(json.dumps(row), flush=True)
print(json.dumps(dict(all_identical=all(x['identical'] for x in results), lock_always_held=all(all(x['lock_held_midrun']) for x in results))))
