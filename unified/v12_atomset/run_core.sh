#!/bin/bash
# v12 M5 core channel: 凍結核 phase_sig を動かす (Taka: 行き止まりを条件変えて越える)
# 核は torque標的+addressing基準 → 動いた核を dynamics/入力が読む → shuffleで「誰の経験か」が効く
# 判定: real(C/D)>shuffle(F/E) + 入力分布変化 + θ slight(特にNaN監視、phase_sig=θ直結)
cd /home/takasan/esde/ESDE-Research
TRACK=${1:-15}; SEEDS="${2:-0 1 2 3 4 5}"; ROOT=run_m5_core
echo "=== core: A/C/F(核drift,入力なし) + D/E(核drift+入力) seeds=[$SEEDS] ==="; date
for s in $SEEDS; do python3 unified/v12_atomset/m5_substrate_atom.py A "$s" "$TRACK" core 1 "$ROOT" > "/tmp/m5co_A_s${s}.log" 2>&1 & done
for c in C F D E; do for s in $SEEDS; do
  python3 unified/v12_atomset/m5_substrate_atom.py "$c" "$s" "$TRACK" core 1 "$ROOT" > "/tmp/m5co_${c}_s${s}.log" 2>&1 & done; done
wait; echo "=== CORE DONE ==="; date
