"""review_v14c: reviewer's own helpers (independent of runs/m13/neg/ck14c.py).
v3 sealing as read from bin/src_v14c/zfast_sched14c.inc:
  header tag = HMAC-SHA256(K, b"ZF14C-HDR\\0" + body)
  item tag   = HMAC-SHA256(K, b"ZF14C-ITEM\\0" + SHA256(stored header body incl. hnonce) + u64be(x) + body)
  line = body + " #" + hex(tag)"""
import hashlib, hmac, json, os, struct, subprocess

ZF = '/Users/kiosk/atlas_mark2/diagnostic/zfast/'
PY = '/Users/kiosk/projects/atlas-rerun/.venv/bin/python'
PROBE = ZF + 'review_v14d/scratch/probe_rv.py'
L14 = ZF + 'bin/libzfast.v14.dylib'
L14C = ZF + 'bin/libzfast.v14d.dylib'
L14CT = ZF + 'bin/libzfast.v14d_testhooks.dylib'
L14B = ZF + 'bin/libzfast.v14b.dylib'


def probe(lib, mode, T0, U0, H, DL, D, W, ck='-', role='gen', nonce='c' * 32, key='-', vn=8, env=None, grid=200, timeout=3600, K='18', J='12'):
    e = {k: v for k, v in os.environ.items() if not k.startswith('ZFAST')}
    e.update(env or {})
    cmd = ['nice', '-n', '19', PY, '-B', PROBE, lib, mode, str(T0), str(U0), str(H), str(DL), K, J, str(D), str(W), ck,
           str(float(U0) - 3), '0.004', str(grid), role, nonce, key, str(vn)]
    p = run_watched(cmd, e, timeout)
    lines = p.stdout.strip().splitlines()
    try:
        r = json.loads(lines[-1])
    except Exception:
        r = dict(ok=False, error='no json')
    r['rc'] = p.returncode
    r['stderr'] = p.stderr[-600:]
    return r


class _R: pass


def run_watched(cmd, env, timeout, lim_kb=2_500_000):
    """subprocess with a footprint watchdog (RSS > 2.5 GB => SIGKILL, reported as rc -9 and stderr WATCHDOG) and a wall timeout."""
    import tempfile, time as _t
    d = os.path.dirname(os.path.abspath(__file__)); fo, fe = tempfile.TemporaryFile(dir=d), tempfile.TemporaryFile(dir=d)
    p = subprocess.Popen(cmd, stdout=fo, stderr=fe, env=env); t0 = _t.time(); note = ''
    while p.poll() is None:
        _t.sleep(0.1)
        try:
            rss = int(subprocess.run(['ps', '-o', 'rss=', '-p', str(p.pid)], capture_output=True, text=True).stdout.strip() or 0)
        except ValueError:
            rss = 0
        if rss > lim_kb: p.kill(); note = f'WATCHDOG rss {rss} kB'; break
        if _t.time() - t0 > timeout: p.kill(); note = 'WATCHDOG timeout'; break
    p.wait(); fo.seek(0); fe.seek(0)
    r = _R(); r.stdout = fo.read().decode(errors='replace'); r.stderr = fe.read().decode(errors='replace') + note; r.returncode = p.returncode
    if note == 'WATCHDOG timeout': r.returncode = 'timeout'
    return r


def kk(r):
    return (r.get('state_sha256'), (r.get('grid') or {}).get('sha256'), r.get('rows_sha256'), tuple(r.get('Z') or ()))


def body(l):
    return l[:l.rindex(' #')]


def keyb(kf):
    return open(kf, 'rb').read()


def seal_hdr(b, kf):
    return b + ' #' + hmac.new(keyb(kf), b'ZF14C-HDR\x00' + b.encode(), hashlib.sha256).hexdigest()


def hh_of(hdr_line):
    return hashlib.sha256(body(hdr_line).encode()).digest()


def seal_item(b, kf, hh, x=None):
    if x is None:
        x = int(b.split(' ')[1])
    return b + ' #' + hmac.new(keyb(kf), b'ZF14C-ITEM\x00' + hh + struct.pack('>Q', x) + b.encode(), hashlib.sha256).hexdigest()


def read_lines(p):
    t = open(p).read()
    assert t.endswith('\n')
    return t[:-1].split('\n')


def write_lines(p, L, mode=0o644):
    with open(p, 'w') as f:
        f.write('\n'.join(L) + '\n')
    os.chmod(p, mode)


def copykey(src, dst):
    d = open(src, 'rb').read()
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.write(fd, d)
    os.close(fd)
