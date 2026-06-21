#!/bin/bash
# core 10step細かい軌跡 (Long tracking50, A/C/F × seed0-3, FINE)
cd /home/takasan/esde/ESDE-Research
TRACK=50; ROOT=run_m5_core_fine; SEEDS="0 1 2 3"
echo "=== core FINE (10step, tracking50) A/C/F × seed[0-3] ==="; date
for c in A C F; do for s in $SEEDS; do
  python3 unified/v1201/m5_substrate_atom.py "$c" "$s" "$TRACK" core 1 "$ROOT" fine > "/tmp/m5fn_${c}_s${s}.log" 2>&1 & done; done
wait; echo "=== CORE FINE DONE ==="; date
