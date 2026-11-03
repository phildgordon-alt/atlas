#!/bin/sh
# run_rd.sh DRIVER INFILE OUTFILE : stdin from file (wd_fp.sh background jobs get /dev/null stdin)
[ -e "$3" ] && { echo "exists $3"; exit 1; }
exec "$1" < "$2" > "$3"
