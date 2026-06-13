#!/bin/bash
cd /home/takasan/esde/ESDE-Research
TRACK=${1:-15}; SEEDS="${2:-0} ${3:-1} ${4:-2}"
echo "=== field: B(control)/D(field)/E(shuffle) × st{1,3} seeds=[$SEEDS] track=$TRACK ==="; date
for s in $SEEDS; do python3 unified/v12_atomset/m5_substrate_atom.py B "$s" "$TRACK" field 1 > "/tmp/m5fld_B_st1_s${s}.log" 2>&1 & done
for st in 1 3; do for c in D E; do for s in $SEEDS; do
  python3 unified/v12_atomset/m5_substrate_atom.py "$c" "$s" "$TRACK" field "$st" > "/tmp/m5fld_${c}_st${st}_s${s}.log" 2>&1 & done; done; done
wait; echo "=== FIELD DONE ==="; date
