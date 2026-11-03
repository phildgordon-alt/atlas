"""m10_monitor.py ROOT_PID RUN_DIR LOG STOPFILE [--lim-gb 3.0] [--max-window-h 10] [--disk-floor-gb 2]   (M10, PREDICTIONS_M10 sec. 4)

Watchdog + progress monitor for the M10 1e25 window.  Enters no certificate; reads only the zfast checkpoint files and `ps`/`footprint`.
Every 30 s:
  - sums phys_footprint (macOS `footprint`, else RSS) over ROOT_PID and all its descendants; logs the peak;
    > lim-gb  -> kills the whole tree (SIGTERM, then SIGKILL), writes STOPFILE.
  - free disk < floor -> same.
  - progress of the generator (RUN/zfast_ckpt_gen.txt) and replay (RUN/zfast_ckpt_replay.txt) sessions: terms done / (Nw - nhead)
    from the checkpoint lines 'I idx b n_lo n_hi ...' (inclusive ranges); projected session time = elapsed / fraction.
    First projection (fraction >= 2% and >= 600 s into the session): projected window = 2 x session + 900 s.  If > max-window-h:
    kill the tree and write STOPFILE (the PREDICTIONS_M10 projection STOP).
Explicit raises, no asserts; refuses -O / PYTHONOPTIMIZE.  Never deletes anything."""
import json, os, re, shutil, signal, subprocess, sys, time

if sys.flags.optimize or os.environ.get('PYTHONOPTIMIZE'):
    raise SystemExit('refusing to run under python -O / PYTHONOPTIMIZE')


def descendants(root):
    out = subprocess.run(['ps', '-Ao', 'pid=,ppid='], capture_output=True, text=True).stdout.split('\n')
    kids = {}
    for line in out:
        p = line.split()
        if len(p) == 2: kids.setdefault(int(p[1]), []).append(int(p[0]))
    res, st = [], [root]
    while st:
        x = st.pop(); res.append(x); st.extend(kids.get(x, []))
    return res


def footprint_mb(pid):
    try:
        o = subprocess.run(['footprint', '-p', str(pid)], capture_output=True, text=True, timeout=20).stdout
        m = re.search(r'phys_footprint:\s+([\d.]+)\s+(KB|MB|GB)', o)
        if m:
            v = float(m.group(1)); return v / 1024 if m.group(2) == 'KB' else v * 1024 if m.group(2) == 'GB' else v
    except Exception:
        pass
    o = subprocess.run(['ps', '-o', 'rss=', '-p', str(pid)], capture_output=True, text=True).stdout.strip()
    return int(o) / 1024 if o.isdigit() else 0.0


def alive(pid):
    try:
        os.kill(pid, 0); return True
    except OSError:
        return False


def kill_tree(root, log, why, stopfile):
    open(stopfile, 'a').write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} {why}\n')
    pids = descendants(root)
    log(dict(event='KILL', why=why, pids=pids))
    for p in reversed(pids):
        try: os.kill(p, signal.SIGTERM)
        except OSError: pass
    time.sleep(10)
    for p in reversed(pids):
        if alive(p):
            try: os.kill(p, signal.SIGKILL)
            except OSError: pass


def ckpt_progress(path):
    if not os.path.exists(path): return None
    with open(path) as f:
        h = f.readline()
        m = re.search(r'Nw=(\d+) .*nhead=(\d+) nitems=(\d+)', h)
        if not m: return None
        nw, nhead, nitems = int(m.group(1)), int(m.group(2)), int(m.group(3))
        s = n = 0
        for line in f:
            p = line.split()
            if len(p) >= 5 and p[0] == 'I' and line.endswith('\n'):
                s += int(p[4]) - int(p[3]) + 1; n += 1
    return dict(Nw=nw, nhead=nhead, nitems=nitems, items=n, frac=s / (nw - nhead), mtime=os.path.getmtime(path),
                ctime_first=None)


def main():
    a = sys.argv[1:]
    if len(a) < 4: raise SystemExit(__doc__)
    root, run, logp, stopfile = int(a[0]), a[1], a[2], a[3]
    opt = dict(zip(a[4::2], a[5::2]))
    lim_mb = float(opt.get('--lim-gb', 3.0)) * 1024; max_win = float(opt.get('--max-window-h', 10)) * 3600
    floor = float(opt.get('--disk-floor-gb', 2.0))
    def log(d):
        d['t'] = time.strftime('%Y-%m-%d %H:%M:%S'); open(logp, 'a').write(json.dumps(d) + '\n')
    t_start = time.time(); peak = 0.0; first_seen = {}; projected_once = False; last_frac = {}
    log(dict(event='start', root=root, run=run, lim_mb=lim_mb, max_window_s=max_win, disk_floor_gb=floor))
    while alive(root):
        pids = descendants(root)
        mb = sum(footprint_mb(p) for p in pids)
        if mb > peak: peak = mb
        free = shutil.disk_usage('/Users/kiosk').free / 1e9
        rec = dict(event='poll', procs=len(pids), footprint_mb=round(mb, 1), peak_mb=round(peak, 1), disk_free_gb=round(free, 2))
        for role in ('gen', 'replay'):
            pr = ckpt_progress(os.path.join(run, f'zfast_ckpt_{role}.txt'))
            if pr is None: continue
            if role not in first_seen: first_seen[role] = time.time()
            # session start = first time the checkpoint file was seen (its header is written at session start)
            el = time.time() - first_seen[role]
            rec[role] = dict(items=pr['items'], nitems=pr['nitems'], frac=round(pr['frac'], 5), elapsed_s=round(el))
            if pr['frac'] > 0 and pr['frac'] < 1:
                rec[role]['proj_session_s'] = round(el / pr['frac'])
            if role == 'gen' and not projected_once and pr['frac'] >= 0.02 and el >= 600:
                projected_once = True
                proj_win = 2 * el / pr['frac'] + 900
                log(dict(event='first_projection', frac=pr['frac'], elapsed_s=round(el), proj_session_s=round(el / pr['frac']),
                         proj_window_s=round(proj_win), limit_s=max_win))
                if proj_win > max_win:
                    kill_tree(root, log, f'projected window {proj_win:.0f} s > {max_win:.0f} s', stopfile); break
        log(rec)
        if mb > lim_mb:
            kill_tree(root, log, f'footprint {mb:.0f} MB > {lim_mb:.0f} MB', stopfile); break
        if free < floor:
            kill_tree(root, log, f'disk free {free:.2f} GB < {floor} GB', stopfile); break
        time.sleep(30)
    log(dict(event='end', peak_mb=round(peak, 1), wall_s=round(time.time() - t_start)))


if __name__ == '__main__':
    main()
