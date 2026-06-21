#!/bin/bash
# v12 M5 substrate 並行試行: 5条件(A-E) × 複数seed × tracking、Pool並行
# usage: run_substrate_batch.sh [TRACKING] [SEEDS...]
cd /home/takasan/esde/ESDE-Research
TRACK=${1:-15}
shift || true
SEEDS="${@:-0 1 2}"
CONDS="A B C D E"
echo "=== batch: conds=[$CONDS] seeds=[$SEEDS] tracking=$TRACK ==="
date
for c in $CONDS; do
  for s in $SEEDS; do
    python3 unified/v1201/m5_substrate_smoke.py "$c" "$s" "$TRACK" \
      > "/tmp/m5sub_${c}_s${s}.log" 2>&1 &
  done
done
wait
echo "=== ALL DONE ==="
date
