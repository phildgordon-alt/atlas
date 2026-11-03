"""Run one frozen Atlas script as __main__ with only the host-path literals rewritten (same table as verify/boot/sitecustomize.py).
usage: ATLAS_REPO=... python -B verify/run_rewritten.py SCRIPT [args...]
The script file is not modified; __file__ is its real path, so scripts that hash themselves (e.g. TOOL_SHA in scan_turing5.py) report
the sha256 of the unmodified file."""
import os, sys, runpy
if sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE'):
    raise SystemExit('refusing to run under python -O / PYTHONOPTIMIZE (Atlas rule: safety checks are asserts)')
import sitecustomize as S   # the repository bootstrap (PYTHONPATH=verify/boot)
script = os.path.realpath(sys.argv[1])
sys.argv = [script] + sys.argv[2:]
sys.path.insert(0, os.path.dirname(script))
code = compile(S.rewrite(open(script, encoding='utf-8').read()), script, 'exec', dont_inherit=True)
g = {'__name__': '__main__', '__file__': script, '__builtins__': __builtins__}
exec(code, g)
