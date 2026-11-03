"""Compare zfast (single + session) against independent references.  usage: compare_points.py ZFASTFILE REFFILE[,REFFILE] OUTJSON
Prints/stores per point: overlap/contained/diff/ratio for single and session vs each reference, and the reference-vs-reference
agreement when two references exist.  Containment = the reference ball lies inside the zfast ball (the M2 criterion)."""
import sys, json
sys.path.insert(0, '/Users/kiosk/atlas_mark2/diagnostic/zfast/review')
import rvlib as L

zf = [json.loads(l) for l in open(sys.argv[1])]
refs = {}
for rf in sys.argv[2].split(','):
    for l in open(rf):
        d = json.loads(l); key = (int(d['T0']), float.fromhex(d['u']) if d['u'].startswith(('0x', '-0x')) else float(d['u']))
        refs.setdefault(key, []).append(d)
rows = []; bad = []
summ = dict(n=0, single_overlap=0, single_contained=0, sess_overlap=0, sess_contained=0, max_ratio_single=0.0, max_ratio_sess=0.0,
            max_diff=0.0, ref_pairs=0, ref_pairs_overlap=0, max_ref_diff=0.0, missing=0)
for z in zf:
    key = (z['T0'], z['u'])
    if key not in refs: summ['missing'] += 1; continue
    for r in refs[key]:
        a = L.compare(z['single'], r['Z']); b = L.compare(z['sess'], r['Z'])
        summ['n'] += 1
        summ['single_overlap'] += a['overlap']; summ['single_contained'] += a['contained']
        summ['sess_overlap'] += b['overlap']; summ['sess_contained'] += b['contained']
        summ['max_ratio_single'] = max(summ['max_ratio_single'], a['ratio']); summ['max_ratio_sess'] = max(summ['max_ratio_sess'], b['ratio'])
        summ['max_diff'] = max(summ['max_diff'], a['diff'], b['diff'])
        row = dict(T0=z['T0'], u=z['u'], cls=z['cls'], ref=r['cmd'], single=a, sess=b, ref_rad=a['rad_ref'])
        rows.append(row)
        if not (a['overlap'] and b['overlap']): bad.append(row)
    if len(refs[key]) >= 2:
        c = L.compare(refs[key][0]['Z'], refs[key][1]['Z'])
        summ['ref_pairs'] += 1; summ['ref_pairs_overlap'] += c['overlap']; summ['max_ref_diff'] = max(summ['max_ref_diff'], c['diff'])
out = dict(summary=summ, failures=bad, rows=rows)
json.dump(out, L.xopen(sys.argv[3]), indent=0)
print(json.dumps(summ, indent=1)); print('failures:', len(bad))
for b in bad[:10]: print(b)
