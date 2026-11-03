"""make_mut.py [names]: mutant copies of the PRODUCTION v12a sources (bin/src_v12a, sha-checked) in review2/mut/<name>/ and drivers
review2/bin/rd3.<name> (rd3.c + the mutant zfast.c).  One error term shrunk 10x per mutant, or one injected logic bug (controls).
Production files are only read."""
import os, shutil, hashlib, subprocess, sys
R = '/Users/kiosk/atlas_mark2/diagnostic/zfast/review2'
SRC = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/src_v12a'
SHA = {'zfast.c': 'f6cdca3780c601d501fd509ceefb3202140f02bb404d9dc64dc1bedc3b988d65', 'zfast_m3b.inc': '13aba52536f144f91d4eccbf10b2dfa1c7b219b9b178bad1fdfa9924405af921',
       'zfast_m3c.inc': '685c2a96f310678d8b5ae8e66a12a0451bfa102af031dcd20bc70e60f27ae6b4', 'zfast.h': '1342bb5ed03f20c58f092d5154c553149783d86213d4fe091bd7a1fe2377e16a'}
for f, h in SHA.items():
    assert hashlib.sha256(open(f'{SRC}/{f}', 'rb').read()).hexdigest() == h, f
D10 = 'mag_div_ui({0}, {0}, 10); '
M = {
 # ---- error terms / 10
 'ec':      ('zfast.c', '#define ZF_EC 4.88e-16', '#define ZF_EC 4.88e-17'),
 'phfloor': ('zfast.c', '    mag_add_ui_2exp_si(err, err, 1, -64);\n}', '    mag_add_ui_2exp_si(err, err, 1, -64);\n    mag_div_ui(err, err, 10);\n}'),
 'interp':  ('zfast.c', '    mag_div(tmp, tmp, tmp2);\n    mag_add(err, err, tmp);\n    mag_add_ui_2exp_si(err, err, 1, -64);',
                        '    mag_div(tmp, tmp, tmp2);\n    mag_div_ui(tmp, tmp, 10);\n    mag_add(err, err, tmp);\n    mag_add_ui_2exp_si(err, err, 1, -64);'),
 'fxeps':   ('zfast.c', '    mag_add_ui_2exp_si(err, err, 1, -257);', '    mag_add_ui_2exp_si(err, err, 1, -257);\n    mag_div_ui(err, err, 10);'),
 'roundZ':  ('zfast.c', 'mag_set_d(tmp, 3.03 * u + ZF_EC);', 'mag_set_d(tmp, 0.303 * u + ZF_EC);'),
 'sumZ':    ('zfast.c', 'mag_set_d(tmp, 15.0 * u / (1.0 - 15.0 * u) * (1.0 + ZF_EC) * (1.0 + 3.1 * u) + ng * ng * u * u * 2.0);',
                        'mag_set_d(tmp, 0.1 * (15.0 * u / (1.0 - 15.0 * u) * (1.0 + ZF_EC) * (1.0 + 3.1 * u) + ng * ng * u * u * 2.0));'),
 'trig7':   ('zfast.c', '        mag_mul_ui(e1, err, 7);\n', '        mag_mul_ui(e1, err, 7); mag_div_ui(e1, e1, 10);\n'),
 'rs':      ('zfast.c', '    acb_add_error_mag(S, err);\n', '    mag_div_ui(err, err, 10); acb_add_error_mag(S, err);\n'),
 'wpoly':   ('zfast.c', '    mag_set_d(tmp, (RDEG + 1) * u / (1 - (RDEG + 1) * u)); mag_mul(tmp, tmp, sumabs);\n    mag_add(e, e, tmp);\n    mag_mul_2exp_si(tmp, e, 1); mag_add(mx, sumabs, tmp);       /* |p_hat|',
                        '    mag_set_d(tmp, (RDEG + 1) * u / (1 - (RDEG + 1) * u)); mag_mul(tmp, tmp, sumabs);\n    mag_add(e, e, tmp);\n    mag_div_ui(e, e, 10);\n    mag_mul_2exp_si(tmp, e, 1); mag_add(mx, sumabs, tmp);       /* |p_hat|'),
 'hjet':    ('zfast.c', '        acb_add_error_mag(H1, e1);', '        mag_div_ui(e1, e1, 10); acb_add_error_mag(H1, e1);'),
 'logp':    ('zfast_m3b.inc', '    mag_set_d(tmp, (RDEG + 1) * u / (1 - (RDEG + 1) * u)); mag_mul(tmp, tmp, sumabs);\n    mag_add(e, e, tmp);\n',
                              '    mag_set_d(tmp, (RDEG + 1) * u / (1 - (RDEG + 1) * u)); mag_mul(tmp, tmp, sumabs);\n    mag_add(e, e, tmp);\n    mag_div_ui(e, e, 10);\n'),
 'm3mom':   ('zfast_m3b.inc', '                mag_add(R->err + j * K2 + k, R->err + j * K2 + k, term);', '                mag_div_ui(term, term, 10); mag_add(R->err + j * K2 + k, R->err + j * K2 + k, term);'),
 'm3trig':  ('zfast_m3b.inc', '                mag_mul(term, trig, Xk);', '                mag_mul(term, trig, Xk); mag_div_ui(term, term, 10);'),
 'm3sum':   ('zfast_m3b.inc', '                mag_mul(tmp, sumc, mw[j]); mag_mul(tmp, tmp, Xk); mag_add(term, term, tmp);',
                              '                mag_mul(tmp, sumc, mw[j]); mag_mul(tmp, tmp, Xk); mag_div_ui(tmp, tmp, 10); mag_add(term, term, tmp);'),
 'm3tay':   ('zfast_m3b.inc', '        mag_mul(q, q, fac); mag_mul(q, q, ex); mag_mul(q, q, S->V + j * S->nb + b);',
                              '        mag_mul(q, q, fac); mag_mul(q, q, ex); mag_mul(q, q, S->V + j * S->nb + b); mag_div_ui(q, q, 10);'),
 'm3ctay':  ('zfast_m3c.inc', 'mag_mul(q, q, S->V + bb); mag_mul(q, q, zb);', 'mag_mul(q, q, S->V + bb); mag_mul(q, q, zb); mag_div_ui(q, q, 10);'),
 'Vb':      ('zfast_m3b.inc', '            arb_get_mag(mg, w); mag_add(S->V + j * nb + b, S->V + j * nb + b, mg);', '            arb_get_mag(mg, w); mag_div_ui(mg, mg, 10); mag_add(S->V + j * nb + b, S->V + j * nb + b, mg);'),
 'nozb':    ('zfast_m3c.inc', 'mag_mul(q, q, S->V + bb); mag_mul(q, q, zb);', 'mag_mul(q, q, S->V + bb);'),
 # ---- logic-bug positive controls
 'bugquad': ('zfast.c', '    return ((q + 1) & 2) ? -r : r;          /* q = 1, 2 negative */', '    return (q & 2) ? -r : r;'),
 'bugtail': ('zfast_m3b.inc', '        for (ulong n = Nt + 1; n <= S->Nw; n++)', '        for (ulong n = Nt + 2; n <= S->Nw; n++)'),
 'bugws':   ('zfast_m3c.inc', 'arb_set_d(e, 0.5); if (ws > 0) arb_add(e, e, b, S->wp); else arb_sub(e, e, b, S->wp);', 'arb_set_d(e, 0.5); if (ws < 0) arb_add(e, e, b, S->wp); else arb_sub(e, e, b, S->wp);'),
 'bughc':   ('zfast_m3c.inc', 'if (ws > 0) arb_neg(acb_imagref(hc), acb_imagref(hc));', 'if (ws < 0) arb_neg(acb_imagref(hc), acb_imagref(hc));'),
 'bugconj': ('zfast_m3c.inc', '    zfm_sum_c(Sm + 2, S, b, -1, 0, u, Nt, prec); acb_conj(Sm + 2, Sm + 2);', '    zfm_sum_c(Sm + 2, S, b, -1, 0, u, Nt, prec);'),
}
names = sys.argv[1:] or list(M)
for name in names:
    f, old, new = M[name]
    d = f'{R}/mut/{name}'
    if os.path.exists(d): print('exists', d); continue
    os.makedirs(d)
    for g in SHA: shutil.copyfile(f'{SRC}/{g}', f'{d}/{g}')
    s = open(f'{d}/{f}').read(); assert s.count(old) == 1, (name, s.count(old))
    with open(f'{d}/{f}.mut', 'x') as h: h.write(s.replace(old, new))
    os.replace(f'{d}/{f}.mut', f'{d}/{f}')          # replaces the fresh COPY inside review2/mut only
    with open(f'{d}/MUTATION.txt', 'x') as h: h.write(f'file: {f}\n--- old\n{old}\n+++ new\n{new}\n')
    r = subprocess.run(['sh', f'{R}/build.sh', f'{R}/bin/rd3.{name}', f'-I{d}', f'{R}/src/rd3.c'], capture_output=True, text=True)
    print(name, r.stdout.strip(), r.stderr.strip()[-300:])
