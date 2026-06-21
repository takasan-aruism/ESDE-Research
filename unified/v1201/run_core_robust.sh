#!/bin/bash
# core 頑健性: A/C/F を seed 6-23 追加 (既存0-5と合わせ24seed で sign-flip 確認)
cd /home/takasan/esde/ESDE-Research
TRACK=15; ROOT=run_m5_core; SEEDS="6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23"
echo "=== core robustness: A/C/F × seed[6-23] (24seed化) ==="; date
for c in A C F; do for s in $SEEDS; do
  python3 unified/v1201/m5_substrate_atom.py "$c" "$s" "$TRACK" core 1 "$ROOT" > "/tmp/m5cor_${c}_s${s}.log" 2>&1 & done; done
wait; echo "=== CORE ROBUST DONE ==="; date
