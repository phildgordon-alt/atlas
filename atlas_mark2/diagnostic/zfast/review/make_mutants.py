"""Build mutant copies of the production zfast sources (bin/src_v10b, sha-checked) in review/mut/<name>/ and compile
review/bin/rv_drv.<name>.  Each mutant shrinks ONE error term by 10x (or more for the slack-measuring 'all' mutants), or injects
one logic bug (positive controls).  The production sources are only read."""
import os, shutil, hashlib, subprocess, sys
R = '/Users/kiosk/atlas_mark2/diagnostic/zfast/review'
SRC = '/Users/kiosk/atlas_mark2/diagnostic/zfast/bin/src_v10b'
SHA = {'zfast.c': '5aa73c8fb5e8d6f13ccd3cec8e924662ba11b20dd8b4744f5baf070264cb5a01', 'zfast_m3.inc': 'a1f679a9353c88d9cb32b1cdb2ccd19b9b5dd15318930fe36306882051f21655',
       'zfast.h': '021151164cc88510d6b14b32e07830a66f9bad61dc1391225700763fe04d3ed3'}
for f, h in SHA.items():
    assert hashlib.sha256(open(f'{SRC}/{f}', 'rb').read()).hexdigest() == h, f

M = {
 # one error term / 10
 'ec':      ('zfast.c', '#define ZF_EC 4.88e-16', '#define ZF_EC 4.88e-17'),
 'rs':      ('zfast.c', '    acb_add_error_mag(S, err);\n', '    mag_div_ui(err, err, 10); acb_add_error_mag(S, err);\n'),
 'sumZ':    ('zfast.c', 'mag_set_d(tmp, 15.0 * u / (1.0 - 15.0 * u) * (1.0 + ZF_EC) * (1.0 + 3.1 * u) + ng * ng * u * u * 2.0);',
                        'mag_set_d(tmp, 0.1 * (15.0 * u / (1.0 - 15.0 * u) * (1.0 + ZF_EC) * (1.0 + 3.1 * u) + ng * ng * u * u * 2.0));'),
 'roundZ':  ('zfast.c', 'mag_set_d(tmp, 3.03 * u + ZF_EC);', 'mag_set_d(tmp, 0.303 * u + ZF_EC);'),
 'phase':   ('zfast.c', '    mag_add_ui_2exp_si(err, err, 1, -64);\n}', '    mag_add_ui_2exp_si(err, err, 1, -64);\n    mag_div_ui(err, err, 10);\n}'),
 'interp':  ('zfast.c', '    mag_div(tmp, tmp, tmp2);\n    mag_add(err, err, tmp);', '    mag_div(tmp, tmp, tmp2);\n    mag_div_ui(tmp, tmp, 10);\n    mag_add(err, err, tmp);'),
 'fxeps':   ('zfast.c', 'mag_add_ui_2exp_si(err, err, 1, -257);', 'mag_add_ui_2exp_si(err, err, 1, -261);'),
 'wpoly':   ('zfast.c', '    mag_mul_2exp_si(tmp, e, 1); mag_add(mx, sumabs, tmp);       /* |p_hat|', '    mag_div_ui(e, e, 10); mag_mul_2exp_si(tmp, e, 1); mag_add(mx, sumabs, tmp);       /* |p_hat|'),
 'hjet':    ('zfast.c', '        acb_add_error_mag(H1, e1);', '        mag_div_ui(e1, e1, 10); acb_add_error_mag(H1, e1);'),
 'm3tay':   ('zfast_m3.inc', '        mag_add(rem, rem, q);\n    }', '        mag_div_ui(q, q, 10); mag_add(rem, rem, q);\n    }'),
 'm3mom':   ('zfast_m3.inc', '                mag_add(R->err + j * K2 + k, R->err + j * K2 + k, term);', '                mag_div_ui(term, term, 10); mag_add(R->err + j * K2 + k, R->err + j * K2 + k, term);'),
 'm3logp':  ('zfast_m3.inc', '    mag_add(e, e, tmp);\n    mag_mul_2exp_si(tmp, e, 1); mag_add(mx, sumabs, tmp);\ndone:\n    arb_clear(a); arb_clear(q); arb_clear(Lba);',
                             '    mag_add(e, e, tmp);\n    mag_div_ui(e, e, 10);\n    mag_mul_2exp_si(tmp, e, 1); mag_add(mx, sumabs, tmp);\ndone:\n    arb_clear(a); arb_clear(q); arb_clear(Lba);'),
 # slack measurement: the whole a-priori fast-part bound of single-point Z divided by 10^k
 'allZ1e2': ('zfast.c', '    arb_add_error_mag(acc, tot);\n    arb_set(res, acc);', '    mag_div_ui(tot, tot, 100); arb_add_error_mag(acc, tot);\n    arb_set(res, acc);'),
 'allZ1e3': ('zfast.c', '    arb_add_error_mag(acc, tot);\n    arb_set(res, acc);', '    mag_div_ui(tot, tot, 1000); arb_add_error_mag(acc, tot);\n    arb_set(res, acc);'),
 'allZ1e4': ('zfast.c', '    arb_add_error_mag(acc, tot);\n    arb_set(res, acc);', '    mag_div_ui(tot, tot, 10000); arb_add_error_mag(acc, tot);\n    arb_set(res, acc);'),
 'allZ1e5': ('zfast.c', '    arb_add_error_mag(acc, tot);\n    arb_set(res, acc);', '    mag_div_ui(tot, tot, 100000); arb_add_error_mag(acc, tot);\n    arb_set(res, acc);'),
 'allM1e3': ('zfast_m3.inc', '                mag_add(R->err + j * K2 + k, R->err + j * K2 + k, term);', '                mag_div_ui(term, term, 1000); mag_add(R->err + j * K2 + k, R->err + j * K2 + k, term);'),
 'allM1e5': ('zfast_m3.inc', '                mag_add(R->err + j * K2 + k, R->err + j * K2 + k, term);', '                mag_div_ui(term, term, 100000); mag_add(R->err + j * K2 + k, R->err + j * K2 + k, term);'),
 # logic-bug positive controls
 'bugquad': ('zfast.c', '    return ((q + 1) & 2) ? -r : r;          /* q = 1, 2 negative */', '    return (q & 2) ? -r : r;'),
 'bugsign': ('zfast.c', '    if (fmpz_is_even(N)) acb_neg(S, S);\n    acb_set(res, S);', '    acb_set(res, S);'),
 'bugtail': ('zfast_m3.inc', '        for (ulong n = Nt + 1; n <= S->Nw; n++)', '        for (ulong n = Nt + 2; n <= S->Nw; n++)'),
}
names = sys.argv[1:] or list(M)
for name in names:
    f, old, new = M[name]
    d = f'{R}/mut/{name}'
    if os.path.exists(d): print('exists', d); continue
    os.makedirs(d)
    for g in SHA: shutil.copyfile(f'{SRC}/{g}', f'{d}/{g}')
    s = open(f'{d}/{f}').read(); assert s.count(old) == 1, (name, s.count(old))
    open(f'{d}/{f}', 'w').write(s.replace(old, new))
    with open(f'{d}/MUTATION.txt', 'x') as h: h.write(f'file: {f}\n--- old\n{old}\n+++ new\n{new}\n')
    r = subprocess.run(['sh', f'{R}/build_rv.sh', d, name], capture_output=True, text=True)
    print(name, r.stdout.strip(), r.stderr.strip()[-300:])
