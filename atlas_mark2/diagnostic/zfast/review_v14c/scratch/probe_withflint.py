import sys, runpy
import flint  # python-flint first, as the provider does
sys.argv = [sys.argv[1]] + sys.argv[2:]
runpy.run_path(sys.argv[0], run_name='__main__')
