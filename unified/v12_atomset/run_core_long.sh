#!/bin/bash
# core Long: tracking 50 (個性化が育つ時間、Short20超え)。A/C/F、n_core層化で分析
cd /home/takasan/esde/ESDE-Research
TRACK=50; ROOT=run_m5_core_long; SEEDS="0 1 2 3 4 5 6 7"
echo "=== core LONG (tracking50) A/C/F × seed[0-7] ==="; date
for c in A C F; do for s in $SEEDS; do
  python3 unified/v12_atomset/m5_substrate_atom.py "$c" "$s" "$TRACK" core 1 "$ROOT" > "/tmp/m5lo_${c}_s${s}.log" 2>&1 & done; done
wait; echo "=== CORE LONG DONE ==="; date
