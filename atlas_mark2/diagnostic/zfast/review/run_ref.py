"""Run the independent references (rv_ref) for a points file under the footprint watchdog (FP_MB=800), one fresh process per
magnitude group.  usage: run_ref.py TAG MODE[,MODE] [extra_prec]
MODE: AZ (stock Arb hardy_z) or GZ (Arb powsum_smooth + Gabcke C0/C1 correction, R1 bound).  -> data/ref_TAG_MODE.jsonl"""
import sys, json, subprocess, os, collections
sys.path.insert(0, '/Users/kiosk/atlas_mark2/diagnostic/zfast/review')
import rvlib as L

tag = sys.argv[1]; modes = sys.argv[2].split(','); xp = int(sys.argv[3]) if len(sys.argv) > 3 else 128
pts = json.load(open(f'{L.R}/data/points_{tag}.json'))
groups = collections.OrderedDict()
for p in pts: groups.setdefault(len(str(p['T0'])), []).append(p)
for mode in modes:
    outp = f'{L.R}/data/ref_{tag}_{mode}.jsonl'
    assert not os.path.exists(outp)
    for g, ps in groups.items():
        inp = f'{L.R}/data/refin_{tag}_{mode}_{g}.txt'
        with L.xopen(inp) as f:
            for p in ps:
                prec = xp + p['T0'].bit_length()
                if mode == 'AZ': f.write(f"AZ {p['T0']} {p['u'].hex()} {prec}\n")
                else: f.write(f"GZ {p['T0']} {p['u'].hex()} {prec} -1\n")
        env = dict(os.environ, FP_MB='800', RSS_KB='800000', TL='7200')
        r = subprocess.run([L.WD, L.REF, inp, outp], env=env, capture_output=True, text=True)
        print(mode, g, len(ps), r.stdout.strip(), r.stderr.strip()[-200:], flush=True)
