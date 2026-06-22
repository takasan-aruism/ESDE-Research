#!/usr/bin/env python3
"""v1302 (B)案 実 probe — auto_growth_rate / beta を静的水準＋走行中書き換えで R/S/cluster が動くか観察（stdout のみ・ファイル非生成）。

【観察対象注釈ブロック / 同系・異系宣言】
- 同系内: 親 seed0 CID 縮小版の child engine を in-memory で起こすだけ。異系対応でない。
- 読=frozen: engine ソース。書込なし(stdout のみ)。
- これは smoke でも実験 run でもない: 親軌跡駆動・time-shuffle・署名計算・Mantel を含まない。
  auto_growth_rate / beta を 3-4 水準に固定 or 走行中書換し、loop/meanR/mean_S/cluster を比較するだけ。判定は置かない。
- 親 physics/inject/ledger/state 非書込。
"""
import os, sys
os.environ.setdefault('OMP_NUM_THREADS','1'); os.environ.setdefault('MKL_NUM_THREADS','1'); os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
from pathlib import Path
import numpy as np
REPO=Path('/home/takasan/esde/ESDE-Research')
for p in ['autonomy/v82','ecology/engine','primitive/v910','cognition/semantic_injection/v4_pipeline/v43']:
    sys.path.insert(0,str(REPO/p))
from esde_v82_engine import V82Engine, V82EncapsulationParams
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9

def build(N=200, seed=11):
    encap=V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)
    eng=V82Engine(seed=seed, N=N, plb=0.007, encap_params=encap)
    eng.virtual=VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8,1.2))
    eng.pressure_params.pressure_prob=0.0
    eng.run_injection()
    return eng

def measure(eng):
    st=eng.state
    cyc=st.find_all_cycles(eng.physics.params.max_cycle_length)
    n_loops=sum(len(v) for v in cyc.values())
    Rs=[st.R.get(k,0.0) for k in st.alive_l]
    Ss=[st.S[k] for k in st.alive_l]
    labs=list(eng.virtual.labels.values())
    sizes=sorted([len(l['nodes']) for l in labs], reverse=True)
    return dict(alive_l=len(st.alive_l), n_loops=n_loops,
                meanR=round(float(np.mean(Rs)),3) if Rs else 0.0,
                maxR=round(float(np.max(Rs)),3) if Rs else 0.0,
                meanS=round(float(np.mean(Ss)),4) if Ss else 0.0,
                n_labels=len(labs), max_size=max(sizes) if sizes else 0, top5=sizes[:5])

def line(tag, m):
    print(f'{tag}: loops={m["n_loops"]:>4} meanR={m["meanR"]:>5} maxR={m["maxR"]:>5} '
          f'meanS={m["meanS"]:>6} | alive_l={m["alive_l"]:>4} labels={m["n_labels"]:>3} '
          f'max_size={m["max_size"]:>3} top5={m["top5"]}', flush=True)

NW=120  # 1200 step (auto_growth は累積ゆえ長めに)
print('=== (B) probe A: auto_growth_rate 静的水準 (1200step, beta=canon1.0) ===', flush=True)
for agr in [0.0, 0.03, 0.1, 0.3]:
    eng=build()
    eng.grower.params.auto_growth_rate=agr
    for _ in range(NW): eng.step_window(steps=10)
    line(f'auto_growth={agr:>4}', measure(eng))

print('=== (B) probe B: beta 静的水準 (1200step, auto_growth=canon0.03) ===', flush=True)
for bt in [0.5, 1.0, 2.0, 4.0]:
    eng=build()
    eng.physics.params.beta=bt
    for _ in range(NW): eng.step_window(steps=10)
    line(f'beta={bt:>4} (Rcap={5.0/bt:.2f})', measure(eng))

print('=== (B) probe C: 走行中書き換え (600step canon → auto_growth=0.3 に runtime set → 600step) ===', flush=True)
eng=build()
for _ in range(60): eng.step_window(steps=10)
print('  [前半 canon auto_growth=0.03]'); line('  t=600 ', measure(eng))
eng.grower.params.auto_growth_rate=0.3
print('  [runtime set auto_growth_rate -> 0.3]')
for _ in range(60): eng.step_window(steps=10)
line('  t=1200', measure(eng))
print('=== probe 終了(ファイル非生成・実験 run なし) ===', flush=True)
