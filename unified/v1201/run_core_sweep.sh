#!/bin/bash
# core drift sweep: STRENGTH {2,4,8} で MAX_DRIFT/DRIFT_RATE をスケール、cid特異性が強まる帯を探す
cd /home/takasan/esde/ESDE-Research
TRACK=15; ROOT=run_m5_core; SEEDS="0 1 2 3 4 5 6 7"
echo "=== core drift sweep: C/F × st{2,4,8} × seed[0-7] (帯探索) ==="; date
for st in 2 4 8; do for c in C F; do for s in $SEEDS; do
  python3 unified/v1201/m5_substrate_atom.py "$c" "$s" "$TRACK" core "$st" "$ROOT" > "/tmp/m5csw_${c}_st${st}_s${s}.log" 2>&1 & done; done; done
wait; echo "=== CORE SWEEP DONE ==="; date
