#!/bin/bash
# v12 M5 per-Atom substrate 並行: 5条件(A-E) × seed × tracking × CHANNEL
# usage: run_atom_batch.sh [TRACKING] [CHANNEL] [SEEDS...]
cd /home/takasan/esde/ESDE-Research
TRACK=${1:-15}
CHAN=${2:-torque}
shift 2 2>/dev/null || true
SEEDS="${@:-0 1 2}"
CONDS="A B C D E"
echo "=== atom batch: conds=[$CONDS] seeds=[$SEEDS] tracking=$TRACK channel=$CHAN ==="
date
for c in $CONDS; do
  for s in $SEEDS; do
    python3 unified/v12_atomset/m5_substrate_atom.py "$c" "$s" "$TRACK" "$CHAN" \
      > "/tmp/m5atom_${c}_s${s}.log" 2>&1 &
  done
done
wait
echo "=== ALL DONE ==="
date
