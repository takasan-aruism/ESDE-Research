#!/usr/bin/env python3
"""v1302 設計監査 §1-3【最優先 probe】中心仮説 K_sync↑ → loop/R↑ を直接観察（stdout のみ・ファイル非生成）。

【観察対象注釈ブロック / 同系・異系宣言】
- 同系内: 親 seed0 CID 縮小版の child engine を in-memory で起こすだけ。異系対応でない。
- 読=frozen: engine ソース。書込なし(stdout のみ)。
- これは smoke でも実験 run でもない: 親軌跡駆動・time-shuffle・署名計算・Mantel を含まない。
  静的 K_sync を 3 水準に固定して数百 step 走らせ、形成 loop 数 / mean R / label サイズ分布を比較するだけ。判定は置かない(観察事実のみ)。
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

def build(ksync, N=200, seed=11):
    encap=V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)
    eng=V82Engine(seed=seed, N=N, plb=0.007, encap_params=encap)
    eng.virtual=VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8,1.2))
    eng.pressure_params.pressure_prob=0.0
    eng.physics.params.K_sync=ksync
    eng.run_injection()
    return eng

def measure(eng):
    st=eng.state
    cyc=st.find_all_cycles(eng.physics.params.max_cycle_length)  # {len:[cycles]}
    n_loops=sum(len(v) for v in cyc.values())
    Rs=[st.R.get(k,0.0) for k in st.alive_l]
    meanR=float(np.mean(Rs)) if Rs else 0.0
    maxR=float(np.max(Rs)) if Rs else 0.0
    labs=list(eng.virtual.labels.values())
    sizes=sorted([len(l['nodes']) for l in labs], reverse=True)
    return dict(alive_n=len(st.alive_n), alive_l=len(st.alive_l), n_loops=n_loops,
                meanR=round(meanR,3), maxR=round(maxR,3), n_labels=len(labs),
                mean_size=round(float(np.mean(sizes)),2) if sizes else 0.0,
                max_size=max(sizes) if sizes else 0, top5=sizes[:5])

print('=== §1-3 probe: K_sync 3水準・同seed・300step後の loop/R/label ===', flush=True)
print('(中心仮説: K_sync↑ → 位相同期↑ → 閉路/R↑ → cluster 大。偽なら coherence→K_sync が偏りを増幅しない)', flush=True)
for ks in [0.03, 0.1, 0.3]:
    eng=build(ks)
    for _ in range(30):
        eng.step_window(steps=10)  # 300 step
    m=measure(eng)
    print(f'K_sync={ks:>4}: loops={m["n_loops"]:>4} meanR={m["meanR"]:>5} maxR={m["maxR"]:>4} '
          f'| alive_l={m["alive_l"]:>4} | labels={m["n_labels"]:>3} mean_size={m["mean_size"]:>5} '
          f'max_size={m["max_size"]:>3} top5={m["top5"]}', flush=True)
# 念のため長め(600step)でも傾向を確認
print('--- 600step ---', flush=True)
for ks in [0.03, 0.1, 0.3]:
    eng=build(ks)
    for _ in range(60):
        eng.step_window(steps=10)
    m=measure(eng)
    print(f'K_sync={ks:>4}: loops={m["n_loops"]:>4} meanR={m["meanR"]:>5} maxR={m["maxR"]:>4} '
          f'| alive_l={m["alive_l"]:>4} | labels={m["n_labels"]:>3} mean_size={m["mean_size"]:>5} '
          f'max_size={m["max_size"]:>3} top5={m["top5"]}', flush=True)
print('=== probe 終了(ファイル非生成・実験 run なし) ===', flush=True)
