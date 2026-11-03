"""production dylib: an authenticated line whose arb radius is (man 0, exp 4) -> FLINT throws inside arb_load_str (process abort)"""
import hashlib, hmac, shutil, subprocess, os
ZF='/Users/kiosk/atlas_mark2/diagnostic/zfast/'; PY='/Users/kiosk/projects/atlas-rerun/.venv/bin/python'
src='out_attack/A.txt'; key='out_attack/keys/A.key'; dst='flint_abort.txt'; kd='flint_abort.key'
L=open(src).read().split('\n')[:-1]; b=L[3][:L[3].rindex(' #')]; t=b.split(' '); assert t[9]=='0' and t[10]=='0'; t[10]='4'; b=' '.join(t)
L[3]=b+' #'+hmac.new(open(key,'rb').read(), b.encode(), hashlib.sha256).hexdigest(); open(dst,'w').write('\n'.join(L)+'\n'); shutil.copy(key,kd)
e={k:v for k,v in os.environ.items() if not k.startswith('ZFAST')}
p=subprocess.run(['nice','-n','19',PY,'-B',ZF+'tools/m12_probe.py',ZF+'bin/libzfast.v14b.dylib','v14b','100000000000000','50.0','61.0','0.012','18','12','2','1',dst,'47','0.004','10','gen','a'*32,kd,'8'],capture_output=True,text=True,env=e)
print('rc', p.returncode, 'stderr', p.stderr[-200:].replace('\n',' '), 'stdout', p.stdout[-200:])
