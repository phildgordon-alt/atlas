"""review_v14d driver tests, second pass (fixes two test-design misses of drv_v14d.py at 10^16, where the sessions build in < 1 s):
D2b generator SIGKILLed after gen_done and before the turing_grid stage record -> --resume;  D5b replay I/O abort: a copy of the complete
run d5 with its replay checkpoint truncated to 30 % mid-line and replay_check/ moved aside (= a replay that died mid-build), resumed under
RLIMIT_FSIZE -> rc 3 + banner + ckpt_io_abort(role replay), then --resume -> identical, replay passed."""
import os, shutil, signal, resource, json, sys
sys.argv = [sys.argv[0]]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'drv_v14d.py')).read().split('# D1')[0])
A = BASE / 'ref'
k = kill_when('d2b', lambda R: 'gen_done' in stages(R) and 'turing_grid' not in stages(R), 'gen_target5.py {run}')
B = BASE / 'd2b'; r = run('d2b', resume=True, tag='resume'); same, c = compare(A, B)
moved = sorted(p.name for p in (B / 'gen_postbuild.attempt1').iterdir()) if (B / 'gen_postbuild.attempt1').exists() else []
ss = sessions(B)
rec('D2b_kill_after_gen_done_before_grid_then_resume', k['killed'] and r['rc'] == 0 and same and 'zs.json' in moved and replay_ok(B) == dict(passed=True, zck=True)
    and len(ss) == 2 and ss[-1]['items_loaded'] == ss[-1]['items'] and ss[-1]['verified'] == 64, kill=dict(k, stages=(k['stages'] or [])[-3:]), resume=r, moved=moved,
    sessions=[(s['items_loaded'], s['items'], s['verified']) for s in ss])
S5 = BASE / 'd5'; B = BASE / 'd5b'; shutil.copytree(S5, B, symlinks=True)
(B / 'replay_check').rename(B / 'replay_check.moved_by_review')
d = open(B / 'zfast_ckpt_replay.txt', 'rb').read(); cut = int(len(d) * 0.3) + 7; open(B / 'zfast_ckpt_replay.txt', 'wb').write(d[:cut])
lim = cut + 200000
def pre():
    signal.signal(signal.SIGXFSZ, signal.SIG_IGN); resource.setrlimit(resource.RLIMIT_FSIZE, (lim, lim))
r1 = run('d5b', resume=True, pre=pre, tag='limited'); ab = [x for x in drive(B) if x.get('stage') == 'ckpt_io_abort']
size_after = os.path.getsize(B / 'zfast_ckpt_replay.txt')
r2 = run('d5b', resume=True, tag='resume'); same, c = compare(A, B); rs = sessions(B, 'replay')
rec('D5b_replay_io_abort_rc3_then_resume', r1['rc'] == 3 and len(ab) == 1 and ab[0].get('role') == 'replay' and banner(r1['log']) and size_after == lim
    and r2['rc'] == 0 and same and replay_ok(B) == dict(passed=True, zck=True), limited=r1, resume=r2, abort=(ab[0]['error'][:200] if ab else None),
    replay_sessions=[(s['items_loaded'], s['items'], s['verified'], s['lines_written']) for s in rs[-3:]])
json.dump(RES, open(HERE / 'drv2_v14d_results.json', 'w'), indent=1, default=str)
print(json.dumps(dict(total=len(RES), fail=[k for k, v in RES.items() if not v['ok']])))
