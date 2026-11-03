#!/bin/sh
# wd_run.sh LIMIT_MB OUTFILE cmd... < input : runs cmd (stdin passed) and kills it if its RSS exceeds LIMIT_MB (polled 0.5 s).
LIM=$1; OUT=$2; shift 2
"$@" > "$OUT" &
P=$!
while kill -0 $P 2>/dev/null; do
  R=$(ps -o rss= -p $P 2>/dev/null | tr -d ' '); [ -n "$R" ] && [ "$R" -gt $((LIM*1024)) ] && { kill $P; echo "WATCHDOG KILLED at ${R} KB" >&2; }
  sleep 0.5
done
wait $P; echo "exit $?" >&2
