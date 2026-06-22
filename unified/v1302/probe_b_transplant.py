#!/usr/bin/env python3
"""v1302 §1-3 (B) probe — add_link で親 member 構造(模擬)を子に移植し、(a)alive 化 (b)R が閉路から内生 (c)非破綻 を確認（stdout のみ・ファイル非生成）。

【観察対象注釈ブロック / 同系・異系宣言】
- 同系内: 親 member 構造を模した小グラフを子 child engine に instantiate するだけ。異系対応でない。
- 読=frozen: engine ソース。書込なし(stdout)。
- これは smoke でも実験 run でもない: 署名計算・Mantel・親軌跡駆動・time-shuffle を含まない。
  add_link で閉路を含む形を子に入れ、数十 step で R が立つか/alive 非破綻かを見るだけ。判定は置かない。
- 親 physics/inject/ledger/state 非書込。移植は子 in-memory state への add_link のみ。
"""
import os, sys
os.environ.setdefault('OMP_NUM_THREADS','1'); os.environ.setdefault('MKL_NUM_THREADS','1'); os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
from pathlib import Path
import numpy as np
REPO=Path('/home/takasan/esde/ESDE-Research')
for p in ['autonomy/v82','ecology/engine','primitive/v910','cognition/semantic_injection/v4_pipeline/v43']:
    sys.path.insert(0,str(REPO/p))
from esde_v82_engine import V82Engine, V82EncapsulationParams

def build(N=200, seed=11):
    encap=V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)
    eng=V82Engine(seed=seed, N=N, plb=0.007, encap_params=encap)
    eng.pressure_params.pressure_prob=0.0
    return eng

def Rstats(eng):
    st=eng.state
    cyc=st.find_all_cycles(eng.physics.params.max_cycle_length)
    n_loops=sum(len(v) for v in cyc.values())
    Rs=[st.R.get(k,0.0) for k in st.alive_l]
    return len(st.alive_n), len(st.alive_l), n_loops, (round(float(np.max(Rs)),3) if Rs else 0.0), (round(float(np.mean(Rs)),3) if Rs else 0.0)

# 親 member 構造(模擬): 2三角形 + ブリッジ = 閉路を含む structural field を模す
# child-local node id (0..N-1) に remap 済みと仮定。S は fresh 値(canon inject_link_strength 相当 0.1)、E も fresh。
eng=build()
S0=0.1
edges=[(0,1),(1,2),(0,2),     # 三角形A (閉路)
       (3,4),(4,5),(3,5),     # 三角形B (閉路)
       (2,3),                  # ブリッジ(コア間)
       (5,6),(6,7),(2,8)]      # 周辺 structural field
print('=== (B) probe: add_link 移植前 ===', flush=True)
print(f'  alive_n={len(eng.state.alive_n)} alive_l={len(eng.state.alive_l)}', flush=True)
nodes=sorted(set([n for e in edges for n in e]))
# 正しい移植レシピ: ノードを alive_n に明示登録 + E/theta fresh、その後 add_link
for n in nodes:
    eng.state.alive_n.add(n)
    eng.state.E[n]=0.5
ok_add=True
for (i,j) in edges:
    r=eng.state.add_link(i,j,S0)
    ok_add = ok_add and (eng.state.key(i,j) in eng.state.alive_l)
a_n,a_l,loops,maxR,meanR = Rstats(eng)
print(f'=== 移植直後(step 前) ===', flush=True)
print(f'  add_link 全成立={ok_add} alive_n={a_n} alive_l={a_l} | find_all_cycles loops={loops}', flush=True)
# step_resonance を一度だけ回して R が内生で立つか
eng.physics.step_resonance(eng.state)
a_n,a_l,loops,maxR,meanR = Rstats(eng)
print(f'=== step_resonance 1回後: R 内生 ===', flush=True)
print(f'  loops={loops} maxR={maxR} meanR={meanR}  (閉路2つ→R>0 が立てば内生確認)', flush=True)
# 数十 step 回して非破綻
for _ in range(30): eng.step_window(steps=10)  # 300 step
a_n,a_l,loops,maxR,meanR = Rstats(eng)
print(f'=== 300step 後: 非破綻 + 進化 ===', flush=True)
print(f'  alive_n={a_n} alive_l={a_l} loops={loops} maxR={maxR} meanR={meanR} '
      f'labels={len(eng.virtual.labels)} | alive非破綻={a_n>0}', flush=True)
print('=== probe 終了(ファイル非生成・実験 run なし) ===', flush=True)
