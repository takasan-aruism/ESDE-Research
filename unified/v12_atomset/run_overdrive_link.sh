#!/bin/bash
# v12 M5: torque over-drive 閾値探索 + link 接続グラフ metric (Taka #1 #4)
cd /home/takasan/esde/ESDE-Research
TRACK=${1:-15}; SEEDS="${2:-0} ${3:-1} ${4:-2}"
echo "=== over-drive(torque st 1,3,10) + link(graph metric) seeds=[$SEEDS] track=$TRACK ==="; date
# A baseline (degree 記録版)
for s in $SEEDS; do python3 unified/v12_atomset/m5_substrate_atom.py A "$s" "$TRACK" torque 1 > "/tmp/m5od_A_s${s}.log" 2>&1 & done
# torque over-drive 閾値探索
for st in 1 3 10; do for c in C F; do for s in $SEEDS; do
  python3 unified/v12_atomset/m5_substrate_atom.py "$c" "$s" "$TRACK" torque "$st" > "/tmp/m5od_torque${st}_${c}_s${s}.log" 2>&1 & done; done; done
# link 接続グラフ metric (st1)
for c in C F; do for s in $SEEDS; do
  python3 unified/v12_atomset/m5_substrate_atom.py "$c" "$s" "$TRACK" link 1 > "/tmp/m5od_link_${c}_s${s}.log" 2>&1 & done; done
wait; echo "=== ALL DONE ==="; date
