#!/bin/bash
# align over-drive: STRENGTH {5,20} で生きたループが起動する閾値を探す (A,B は st1 流用)
cd /home/takasan/esde/ESDE-Research
TRACK=${1:-15}; SEEDS="${2:-0 1 2 3 4 5}"; ROOT=run_m5_align
echo "=== align over-drive: D/E × st{5,20} seeds=[$SEEDS] ==="; date
for st in 5 20; do for c in D E; do for s in $SEEDS; do
  python3 unified/v1201/m5_substrate_atom.py "$c" "$s" "$TRACK" align "$st" "$ROOT" > "/tmp/m5alod_${c}_st${st}_s${s}.log" 2>&1 & done; done; done
wait; echo "=== ALIGN OD DONE ==="; date
