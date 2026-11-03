#!/bin/bash
# Y3 (reproduce x_1e22) and Y4 (fresh 1e23 window + closest-pair window [2,4]) with atlas_v5z4; 2 zfast threads.
cd /Users/kiosk/atlas_mark2/diagnostic/zfast/atlas_v5z4; export ZFAST_THREADS=2
./run_window.sh w_1e22 10000000000000000000000 10000000000000000000000 10000000000000000000002 0.005 - - 1.0
echo Y3DONE >> runs/v5z.log
./run_window.sh w_1e23 100000000000000000000000 100000000000000000000000 100000000000000000000002 0.005 - - 1.0
./run_window.sh wp_1e23 100000000000000000000000 100000000000000000000002 100000000000000000000004 0.005 - - 3.0
echo Y4DONE >> runs/v5z.log
