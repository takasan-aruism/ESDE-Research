#!/bin/bash
# v12 M5 再走v2: survival metric + seed6 + link修正(S強化) + confound除去(lifespan抜き)
cd /home/takasan/esde/ESDE-Research
TRACK=${1:-15}; SEEDS="${2:-0 1 2 3 4 5}"; ROOT=run_m5_atom_v2
echo "=== retest v2: seeds=[$SEEDS] track=$TRACK (lifespan抜き culture, link=S強化) ==="; date
# A baseline (degree記録, torque dir)
for s in $SEEDS; do python3 unified/v1201/m5_substrate_atom.py A "$s" "$TRACK" torque 1 "$ROOT" > "/tmp/m5v2_A_s${s}.log" 2>&1 & done
# torque C/F (survival効果, confound除去)
for c in C F; do for s in $SEEDS; do python3 unified/v1201/m5_substrate_atom.py "$c" "$s" "$TRACK" torque 1 "$ROOT" > "/tmp/m5v2_torque_${c}_s${s}.log" 2>&1 & done; done
# link C/F (修正版=S強化)
for c in C F; do for s in $SEEDS; do python3 unified/v1201/m5_substrate_atom.py "$c" "$s" "$TRACK" link 1 "$ROOT" > "/tmp/m5v2_link_${c}_s${s}.log" 2>&1 & done; done
# field B/D/E (survival)
for c in B D E; do for s in $SEEDS; do python3 unified/v1201/m5_substrate_atom.py "$c" "$s" "$TRACK" field 1 "$ROOT" > "/tmp/m5v2_field_${c}_s${s}.log" 2>&1 & done; done
wait; echo "=== RETEST V2 DONE ==="; date
