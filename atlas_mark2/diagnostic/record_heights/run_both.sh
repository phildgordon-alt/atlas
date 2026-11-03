#!/bin/bash
D=/Users/kiosk/atlas_mark2/diagnostic/record_heights; cd $D
./run_pilot.sh 15 0.01 21600
if grep -q "big_1e15 rc=0" v5run/pilot.log; then ./run_pilot.sh 16 0.02 21600; else echo "1e15 not closed; 1e16 skipped" >> v5run/pilot.log; fi
