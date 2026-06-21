#!/bin/bash
# v12 M5 全チャネル並行 gate test (Taka: 全部撃つ + 各チャネルに shuffle 対照)
# A=baseline(チャネル非依存, torque dir に1セット), C=経験real, F=経験shuffle対照。入力なし(gate)。
# usage: run_allchannels.sh [TRACKING] [SEEDS...]
cd /home/takasan/esde/ESDE-Research
TRACK=${1:-15}; shift || true
SEEDS="${@:-0 1 2}"
CHANS="torque lambda link perception gravity multi"
echo "=== all-channels gate: chans=[$CHANS] conds=[A C F] seeds=[$SEEDS] track=$TRACK ==="
date
# A: 普遍 baseline (torque dir に1セット)
for s in $SEEDS; do
  python3 unified/v1201/m5_substrate_atom.py A "$s" "$TRACK" torque > "/tmp/m5ac_A_torque_s${s}.log" 2>&1 &
done
# C, F: 各チャネル
for ch in $CHANS; do
  for c in C F; do
    for s in $SEEDS; do
      python3 unified/v1201/m5_substrate_atom.py "$c" "$s" "$TRACK" "$ch" \
        > "/tmp/m5ac_${c}_${ch}_s${s}.log" 2>&1 &
    done
  done
done
wait
echo "=== ALL DONE ==="
date
