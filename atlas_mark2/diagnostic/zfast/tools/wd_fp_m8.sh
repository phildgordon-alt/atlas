#!/bin/sh
# wd_fp_m8.sh LIMIT_MB OUTFILE cmd... : runs cmd > OUTFILE; kills it if RSS or phys_footprint > LIMIT_MB (RSS every 1 s, footprint every 10 s).
LIM=$1; OUT=$2; shift 2
"$@" < /dev/null > "$OUT" &
P=$!; MAX=0; n=0
while kill -0 $P 2>/dev/null; do
  R=$(ps -o rss= -p $P 2>/dev/null | tr -d ' '); R=${R:-0}; R=$((R/1024))
  if [ $((n % 10)) -eq 0 ]; then
    F=$(footprint -p $P 2>/dev/null | awk '/phys_footprint:/{v=$2; u=$3; if(u=="KB")v=v/1024; if(u=="GB")v=v*1024; printf "%d", v; exit}'); F=${F:-0}
    [ "$F" -gt "$R" ] && R=$F
  fi
  [ "$R" -gt "$MAX" ] && MAX=$R
  [ "$R" -gt "$LIM" ] && { kill $P; echo "WATCHDOG KILLED at ${R} MB" >&2; }
  n=$((n+1)); sleep 1
done
wait $P; rc=$?; echo "exit $rc peak_mb $MAX" >&2; exit $rc
