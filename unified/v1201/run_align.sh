#!/bin/bash
# v12 M5 align channel (第三の口): 方向/強度分離+入力必須+共有OFF
# 条件: A(baseline) B(input,align算出のみ=control) D(input+align生きたループ) E(input+align shuffle)
# 判定: real(D)>shuffle(E) かつ 入力分布が D vs B で変わる + θ slight
cd /home/takasan/esde/ESDE-Research
TRACK=${1:-15}; SEEDS="${2:-0 1 2 3 4 5}"; ROOT=run_m5_align
echo "=== align: A/B/D/E seeds=[$SEEDS] track=$TRACK ==="; date
for s in $SEEDS; do python3 unified/v1201/m5_substrate_atom.py A "$s" "$TRACK" align 1 "$ROOT" > "/tmp/m5al_A_s${s}.log" 2>&1 & done
for c in B D E; do for s in $SEEDS; do
  python3 unified/v1201/m5_substrate_atom.py "$c" "$s" "$TRACK" align 1 "$ROOT" > "/tmp/m5al_${c}_s${s}.log" 2>&1 & done; done
wait; echo "=== ALIGN DONE ==="; date
