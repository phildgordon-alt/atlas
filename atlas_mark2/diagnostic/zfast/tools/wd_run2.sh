#!/bin/sh
# wd_run2.sh LIMIT_MB INFILE OUTFILE cmd... : runs cmd < INFILE > OUTFILE; kills it if RSS > LIMIT_MB (polled 0.5 s).
# (wd_run.sh lost stdin: sh gives background jobs /dev/null.)
LIM=$1; IN=$2; OUT=$3; shift 3
"$@" < "$IN" > "$OUT" &
P=$!; MAX=0
while kill -0 $P 2>/dev/null; do
  R=$(ps -o rss= -p $P 2>/dev/null | tr -d ' ')
  if [ -n "$R" ]; then [ "$R" -gt "$MAX" ] && MAX=$R; [ "$R" -gt $((LIM*1024)) ] && { kill $P; echo "WATCHDOG KILLED at ${R} KB" >&2; }; fi
  sleep 0.5
done
wait $P; echo "exit $? peak_rss_kb $MAX" >&2
