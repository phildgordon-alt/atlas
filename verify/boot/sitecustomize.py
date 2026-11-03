# Repository bootstrap (NOT part of any frozen pipeline). Active only when ATLAS_REPO is set (verify/quick_verify.sh sets it).
#
# Why: the frozen Atlas code contains a few absolute host paths (e.g. model5.py DIAG = '/Users/kiosk/atlas_mark2/diagnostic',
# zfast_provider.py LIBPATH = '.../zfast/bin/libzfast.v14.dylib', the pinned exact_tiling_check.py outside the tree). The frozen
# files are sha-pinned and are NOT edited. Instead, for every module whose source file lies inside $ATLAS_REPO/atlas_mark2, this
# finder reads the unmodified source, replaces ONLY those path literals (one regex pass, table below), and compiles it under its
# original filename. Code that hashes its own file (sha pins) still reads the unmodified bytes on disk.
# At exit it writes the list of loaded project modules to $ATLAS_BOOT_LOG (if set), so the verifier can check that every project
# module came from this repository and none from the original host tree.
import os, sys
_R = os.environ.get('ATLAS_REPO')
if _R:
    import re, importlib.abc, importlib.machinery, importlib.util, atexit
    _R = os.path.realpath(_R)
    _TREE = os.path.join(_R, 'atlas_mark2')
    # scratch copies of frozen code (e.g. replay_check/ copies made by a full replay under $OUT) get the same treatment
    _EXTRA = [os.path.realpath(x) for x in os.environ.get('ATLAS_REWRITE_DIRS', '').split(os.pathsep) if x]
    MAP = {
        '/Users/kiosk/atlas/workbench/math_ablation_20260928/audit_20261004/exact_tiling_check.py': os.path.join(_R, 'external', 'exact_tiling_check.py'),
        '/Users/kiosk/projects/atlas-rerun/.venv/bin/python': sys.executable,
        '/Users/kiosk/atlas_mark2': _TREE,
    }
    _RX = re.compile('|'.join(re.escape(k) for k in sorted(MAP, key=len, reverse=True)))

    def rewrite(src):
        return _RX.sub(lambda m: MAP[m.group(0)], src)

    class _Loader(importlib.machinery.SourceFileLoader):
        def source_to_code(self, data, path, *, _optimize=-1):
            return compile(rewrite(data.decode('utf-8')), path, 'exec', dont_inherit=True, optimize=_optimize)

        def get_code(self, fullname):            # never use or write bytecode caches for project modules
            return self.source_to_code(self.get_data(self.get_filename(fullname)), self.get_filename(fullname))

    class _Finder(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path=None, target=None):
            spec = importlib.machinery.PathFinder.find_spec(name, path)
            if spec is None or not spec.origin or not spec.origin.endswith('.py'):
                return spec
            o = os.path.realpath(spec.origin)
            if (o.startswith(_TREE + os.sep) or any(o.startswith(x + os.sep) for x in _EXTRA)) and 'site-packages' not in o:
                return importlib.util.spec_from_file_location(name, spec.origin, loader=_Loader(name, spec.origin),
                                                              submodule_search_locations=spec.submodule_search_locations)
            return spec

    sys.meta_path.insert(0, _Finder())

    def _report():
        log = os.environ.get('ATLAS_BOOT_LOG')
        if not log:
            return
        rows = []
        for n, m in list(sys.modules.items()):
            f = getattr(m, '__file__', None)
            if not f:
                continue
            f = os.path.realpath(f)
            if 'site-packages' in f or f.startswith(os.path.realpath(sys.base_prefix)) or f.startswith(os.path.realpath(sys.prefix)):
                continue
            rows.append(f'{n}\t{f}\t{"REPO" if f.startswith(_R + os.sep) else "OUTSIDE"}')
        with open(log, 'a') as fh:
            fh.write('\n'.join(sorted(rows)) + '\n')
    atexit.register(_report)
