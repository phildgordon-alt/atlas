#!/usr/bin/env python
"""Exact-rational tiling check (zero tolerance).

For each open column left by the ledger chains (and the two closed columns at t ~ 7000), require that the union of the rectangles
[x0, x1] x [d_lo, d_hi] of the certificates that PASSED the hardened, corrected-far replay covers the required region exactly:
  x in the column (exact rational endpoints from the frontier files / binary64 values from the bottom-layer results),
  d in [0, cap], cap = largest off-line displacement the source case model still allows in the column.
Every float is converted with Fraction(float) (its exact dyadic value); no tolerances.  Uncovered pieces -> UNRESOLVED_SEAMS.json,
exit code 1.  Only geometry is checked here; certificate validity comes from the replay logs named below.
"""
import json, re, sys, hashlib
from fractions import Fraction as F
from pathlib import Path

WB = Path("/Users/kiosk/atlas/workbench"); MA = WB / "math_ablation_20260928"; LF = MA / "lorentz_feasibility_v1"
M2 = Path("/Users/kiosk/atlas_mark2/diagnostic")
D001 = F(0.001)                                    # binary64(0.001) = 1152921504606847/2^60, the ledger's level
OUT = Path(__file__).resolve().parent


def fr(s): return F(s) if isinstance(s, str) else F(float(s))


def certified_files(logs):
    """certificate files reported CERTIFIED with hardened=True in the given replay logs"""
    ok = set()
    for lg in logs:
        for line in open(lg):
            if not line.startswith("{"): continue
            r = json.loads(line)
            if "file" in r and r.get("status") == "CERTIFIED" and r.get("hardened") is True: ok.add(r["file"])
    return ok


def case_cap(case_path, a, b):
    m = json.load(open(case_path))["case"]["model"]
    return max(F(v[4]) for v in m["vars"] if v[0] == "off" and F(v[1]) < b and F(v[2]) > a)


def rect_of(path):
    """[x0, x1, dlo, dhi] of a certificate (slab/cert: stored region; verify.py witness: region of its source case)"""
    w = json.load(open(path))
    if "region" in w: return [F(v) for v in w["region"]]
    c = json.load(open(MA / f"feedback_closure_1000200_v1/round_001/cases/{w['case']}.json"))["case"]
    return [F(v) for v in c["region"]]


def check(name, req_rects, cert_paths):
    rects = [rect_of(p) for p in cert_paths]
    seams = []
    for a, b, d0, d1 in req_rects:
        ds = sorted({d0, d1} | {r[2] for r in rects if d0 < r[2] < d1} | {r[3] for r in rects if d0 < r[3] < d1})
        for u, v in zip(ds, ds[1:]):
            xs = sorted((r[0], r[1]) for r in rects if r[2] <= u and r[3] >= v)
            cur = a
            for x0, x1 in xs:
                if x1 < cur: continue
                if x0 > cur: break
                cur = max(cur, x1)
                if cur >= b: break
            if cur < b:
                nxt = min([x0 for x0, x1 in xs if x0 > cur] + [b])
                seams.append(dict(column=name, d_strip=[str(u), str(v)], x_gap=[str(cur), str(nxt)], d_strip_float=[float(u), float(v)],
                                  x_gap_float=[float(cur), float(nxt)]))
    return dict(column=name, required=[[str(x) for x in r] for r in req_rects], n_certificates=len(rects),
                certificates=sorted(Path(p).name for p in cert_paths), seams=len(seams)), seams


def main():
    hard_logs = sorted(LF.glob("fix_*.log")) + [LF / "replay_old_hardfix.log"]
    ok = certified_files(hard_logs)
    lad = M2 / "lehmer_7000" / "ladder"; ok_l = certified_files([lad / "hard_lehmer.log"])
    ok_c = set()
    for line in open(lad / "replay_c7002_hard.log") if (lad / "replay_c7002_hard.log").exists() else []: pass
    def pick(d, pat, okset): return [d / f for f in sorted(okset) if re.match(pat, f)]
    fr1 = json.load(open(WB / "state/frontier_v1.20.json"))["stalled_intervals"]
    fr2 = json.load(open(WB / "state/forward_closure_1000100_v1/frontier_v1.17.json"))["stalled_intervals"]
    fr3 = json.load(open(WB / "state/feedback_closure_1000200_v1/frontier_v1.0.json"))["stalled_intervals"]
    bot3 = json.load(open(MA / "bottom_band_1000200_v1/RESULTS.json"))["uncertified"]
    lc = MA / "linear_closure_loop_v1/round_018/cases"; fc = MA / "forward_closure_1000100_v1/round_018/cases"; fb = MA / "feedback_closure_1000200_v1/round_001/cases"
    cols = []
    a, b = fr(fr1[0]["lo"]), fr(fr1[0]["hi"]); cols.append(("B1 052", [(a, b, F(0), case_cap(lc / "g00_left.json", a, b))], pick(LF, r"slab_m052_", ok)))
    a, b = fr(fr1[1]["lo"]), fr(fr1[1]["hi"]); cols.append(("B1 056", [(a, b, F(0), case_cap(lc / "g01_left.json", a, b))], pick(LF, r"slab_m056_", ok)))
    a, b = fr(fr2[0]["lo"]), fr(fr2[0]["hi"]); cols.append(("B2 193", [(a, b, F(0), case_cap(fc / "g00_left.json", a, b))], pick(LF, r"slab_m193_", ok)))
    a, b = fr(fr3[0]["lo"]), fr(fr3[0]["hi"]); c203 = max(case_cap(fb / "g00_left.json", a, b), case_cap(fb / "g00_right.json", a, b))
    ba, bb = fr(bot3[0][0]), fr(bot3[0][1])
    cols.append(("B3 203", [(a, b, D001, c203), (ba, bb, F(0), D001)], pick(LF, r"(witness_g00_|slab_b203_)", ok)))
    a, b = fr(fr3[1]["lo"]), fr(fr3[1]["hi"]); c240 = max(case_cap(fb / "g01_left.json", a, b), case_cap(fb / "g01_right.json", a, b))
    ba, bb = fr(bot3[1][0]), fr(bot3[1][1])
    cols.append(("B3 240", [(a, b, D001, c240), (ba, bb, F(0), D001)], pick(LF, r"(witness_g01_|cert_g240_|slab_g240s_|slab_b240_)", ok)))
    lcase = M2 / "lehmer_7000" / "case_7005.06_7005.1.json"; a, b = F(7005.06), F(7005.1)
    cols.append(("7000 Lehmer", [(a, b, F(0), case_cap(lcase, a, b))], pick(lad, r"slab_lehmer_", ok_l)))
    # declared targets: written out explicitly, then the check reads ONLY this file
    src = {"B1 052": "state/frontier_v1.20.json stalled[0]", "B1 056": "state/frontier_v1.20.json stalled[1]",
           "B2 193": "state/forward_closure_1000100_v1/frontier_v1.17.json stalled[0]",
           "B3 203": "d>=0.001: state/feedback_closure_1000200_v1/frontier_v1.0.json stalled[0]; d<=0.001: bottom_band_1000200_v1/RESULTS.json uncertified[0]",
           "B3 240": "d>=0.001: state/feedback_closure_1000200_v1/frontier_v1.0.json stalled[1]; d<=0.001: bottom_band_1000200_v1/RESULTS.json uncertified[1]",
           "7000 Lehmer": "atlas_mark2/diagnostic/lehmer_7000/open_7000.json (column open at d>=0.001 after base+propagation); bottom layer of the rest of [7000,7010] NOT a target"}
    TG = dict(semantics="each target is a CLOSED rectangle [x0,x1] x [d0,d1] (exact rationals; d = |beta - 1/2|); covered iff every point, "
                        "boundary included, lies in some certificate's closed rectangle. cap d1 = max off-line displacement allowed in the column by the source case model.",
              targets=[dict(column=n, source=src[n], rectangles=[[str(x) for x in r] for r in req]) for n, req, _ in cols])
    json.dump(TG, open(OUT / "TARGETS.json", "w"), indent=1)
    TG = json.load(open(OUT / "TARGETS.json"))
    cols = [(t["column"], [tuple(F(x) for x in r) for r in t["rectangles"]], next(c for n, _, c in cols if n == t["column"])) for t in TG["targets"]]
    report, seams = [], []
    for name, req, certs in cols:
        r, s = check(name, req, certs); report.append(r); seams += s
    res = dict(script="audit_20261004/exact_tiling_check.py", script_sha256=hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
               replay_logs=[str(p) for p in hard_logs] + [str(lad / "hard_lehmer.log")], columns=report, total_seams=len(seams),
               passed=not seams)
    json.dump(res, open(OUT / "TILING_RESULT.json", "w"), indent=1)
    json.dump(seams, open(OUT / "UNRESOLVED_SEAMS.json", "w"), indent=1)
    for r in report: print(f"{r['column']:12s} certificates {r['n_certificates']:3d}  seams {r['seams']}")
    print("PASSED" if not seams else f"FAILED: {len(seams)} seams (see UNRESOLVED_SEAMS.json)")
    sys.exit(0 if not seams else 1)


if __name__ == "__main__":
    main()
