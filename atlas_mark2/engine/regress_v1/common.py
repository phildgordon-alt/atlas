"""engine/regress_v1 shared helpers: Atlas guards, hashing, canonical JSON, guarded subprocess (nice 19, footprint watchdog)."""
import hashlib, json, os, re, subprocess, sys, time
from pathlib import Path

ROOT = Path('/Users/kiosk/atlas_mark2')
DIAG = ROOT / 'diagnostic'
ENGINE = ROOT / 'engine'
HERE = ENGINE / 'regress_v1'
WORK = HERE / 'work'                     # every file this harness writes lives under engine/regress_v1/
PY = '/Users/kiosk/projects/atlas-rerun/.venv/bin/python'
PARI_PY = str(ROOT / 'tools' / 'paripy' / 'bin' / 'python')
LIM_GB = 3.0                             # footprint watchdog (Phil's rule: <= 3 GB)
DISK_FLOOR_GB = 2.0


class RegressError(RuntimeError):
    pass


def guard():
    if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'):
        raise RegressError('refusing to start: python -O / PYTHONOPTIMIZE strips Atlas safety checks')
    st = os.statvfs(str(ROOT))
    free = st.f_bavail * st.f_frsize / 1e9
    if free < DISK_FLOOR_GB:
        raise RegressError(f'refusing to start: free disk {free:.2f} GB below the {DISK_FLOOR_GB} GB floor')


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def canon(obj):
    """canonical JSON: sorted keys, no whitespace, floats as Python repr (shortest round-trip, bit-exact)."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=True)


def canon_sha(obj):
    return hashlib.sha256(canon(obj).encode()).hexdigest()


def strip_keys(obj, keys):
    """recursively drop volatile keys (timings, absolute paths) before a canonical comparison."""
    if isinstance(obj, dict):
        return {k: strip_keys(v, keys) for k, v in obj.items() if k not in keys}
    if isinstance(obj, list):
        return [strip_keys(v, keys) for v in obj]
    return obj


def _footprint_gb(pid):
    try:
        o = subprocess.run(['footprint', '-p', str(pid)], capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return 0.0
    m = re.search(r'phys_footprint:\s*([\d.]+)\s*(KB|MB|GB)', o)
    return float(m.group(1)) * {'KB': 1e-6, 'MB': 1e-3, 'GB': 1}[m.group(2)] if m else 0.0


def _rss_gb(pid):
    try:
        out = subprocess.run(['ps', '-o', 'rss=', '-p', str(pid)], capture_output=True, text=True).stdout.strip()
        return int(out or 0) / 1e6
    except Exception:
        return 0.0


def env_base(**extra):
    e = dict(os.environ)
    e.pop('PYTHONOPTIMIZE', None); e.pop('ZFAST_CENTER', None)   # set only from the recorded run env (A4)
    e.update(PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1',
             ZFAST_THREADS='2', SECH_TABLE=str(WORK / 'sech_prime_table.npz'))
    e.update({k: str(v) for k, v in extra.items()})
    return e


def guarded(cmd, cwd, log, env=None, timeout=3600, lim=LIM_GB):
    """fresh process at nice 19; killed if RSS or phys_footprint exceeds lim GB or wall time exceeds timeout (s)."""
    t0 = time.time(); peak = 0.0; killed = None; n = 0
    Path(log).parent.mkdir(parents=True, exist_ok=True)
    with open(log, 'a') as f:
        p = subprocess.Popen(['nice', '-n', '19'] + list(map(str, cmd)), cwd=str(cwd), env=env or env_base(),
                             stdout=f, stderr=subprocess.STDOUT)
        while p.poll() is None:
            g = _rss_gb(p.pid)
            if n % 8 == 0:
                g = max(g, _footprint_gb(p.pid))
            peak = max(peak, g); n += 1
            if g > lim:
                p.kill(); killed = 'memory'; break
            if timeout and time.time() - t0 > timeout:
                p.kill(); killed = 'timeout'; break
            time.sleep(0.25)
        p.wait()
    return dict(rc=p.returncode, killed=killed, peak_gb=round(peak, 3), seconds=round(time.time() - t0, 2))
