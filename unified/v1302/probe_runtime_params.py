#!/usr/bin/env python3
"""v1302 §8 可否点検 — 最小 probe（plb/K_sync/decay_link の走行中書き換え反映と alive 非破綻のみ）。

【観察対象注釈ブロック / 同系・異系宣言】
- 同系内: 親 seed0 CID 縮小版の child engine を in-memory で起こすだけ。異系対応でない。
- 読=frozen: engine ソース（esde_v82_engine / esde_v43_engine / realization）。書込なし（probe は stdout のみ、ファイル非生成）。
- これは smoke でも実験 run でもない: 署名計算・Mantel・order-effect・親軌跡駆動・time-shuffle は一切含まない。
  数十 step を走らせ「runtime に param を set → realization/物理に反映されるか」「alive が壊れないか」だけを見る、step-0 端末 probe と同粒度。
- 親 physics/inject/ledger/state 非書込。
"""
import os, sys
os.environ.setdefault('OMP_NUM_THREADS', '1'); os.environ.setdefault('MKL_NUM_THREADS', '1'); os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
from pathlib import Path
import numpy as np
REPO = Path('/home/takasan/esde/ESDE-Research')
for p in ['autonomy/v82', 'ecology/engine', 'primitive/v910', 'cognition/semantic_injection/v4_pipeline/v43']:
    sys.path.insert(0, str(REPO / p))
from esde_v82_engine import V82Engine, V82EncapsulationParams
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9


def build(N=200, plb=0.007, seed=11):
    encap = V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)
    eng = V82Engine(seed=seed, N=N, plb=plb, encap_params=encap)
    eng.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    eng.pressure_params.pressure_prob = 0.0
    eng.run_injection()
    return eng


def alive_n(eng):
    return len(eng.state.alive_n)


def realized_rate(eng, windows=4, steps=500):
    """直近 windows×steps で生まれた active link 総数（plb 反映の代理量）。"""
    tot = 0
    for _ in range(windows):
        before = len(eng.state.alive_l)
        eng.step_window(steps=steps)
        tot += max(0, len(eng.state.alive_l) - before)
    return tot, len(eng.state.alive_l)


print('=== v1302 §8 probe: runtime param 書き換え可否 ===', flush=True)
eng = build()
print(f'[init] alive_n={alive_n(eng)} realizer.params.p_link_birth={eng.realizer.params.p_link_birth}', flush=True)

# --- 1. plb 走行中書き換え（最優先ブロッカー） ---
# realizer.params は frozen でない dataclass、step() が毎回 self.params.p_link_birth を読む構造。
eng.step_window(steps=500)
base_active = len(eng.state.alive_l)
print(f'[plb] 書換前: p_link_birth={eng.realizer.params.p_link_birth} active_links={base_active} alive_n={alive_n(eng)}', flush=True)
eng.realizer.params.p_link_birth = 0.05  # ~7倍に runtime 変更
print(f'[plb] runtime set -> {eng.realizer.params.p_link_birth}', flush=True)
n_hi, act_hi = realized_rate(eng, windows=4)
print(f'[plb] 高 plb 4window: 新規 active link={n_hi} active_total={act_hi} alive_n={alive_n(eng)}', flush=True)
eng.realizer.params.p_link_birth = 0.001  # 低に変更
n_lo, act_lo = realized_rate(eng, windows=4)
print(f'[plb] 低 plb 4window: 新規 active link={n_lo} active_total={act_lo} alive_n={alive_n(eng)}', flush=True)
print(f'[plb] => 反映判定: 高plb新規({n_hi}) vs 低plb新規({n_lo})  alive非破綻={alive_n(eng)>0}', flush=True)

# --- 2. K_sync / decay_rate_link 走行中書き換え（step-0 既証の再確認・3ドライバ写像形） ---
eng2 = build(seed=12)
eng2.step_window(steps=500)
print(f'\n[ksync/decay] 既定 K_sync={eng2.physics.params.K_sync} decay_link={eng2.physics.params.decay_rate_link} '
      f'decay_node={eng2.physics.params.decay_rate_node}', flush=True)
ok = True
for t in range(3):  # 10step 毎更新を模した tanh transform を 3 回当てる（数十 step 相当）
    z = np.tanh((t - 1) / 1.0)
    eng2.physics.params.K_sync = 0.1 * (1 + 0.3 * z)
    eng2.physics.params.decay_rate_link = 0.05 * (1 + 0.3 * z)
    eng2.step_window(steps=10)  # ← 親10step駆動と同じ刻み
    a = alive_n(eng2)
    print(f'  upd{t}: K_sync={eng2.physics.params.K_sync:.4f} decay_link={eng2.physics.params.decay_rate_link:.4f} alive_n={a}', flush=True)
    ok = ok and a > 0
print(f'[ksync/decay] 10step刻み更新 alive非破綻={ok}', flush=True)

# --- 3. decay_node が物理可（4本目・設計上 frozen だが書込自体は可）か ---
eng2.physics.params.decay_rate_node = 0.005 * 1.2
eng2.step_window(steps=10)
print(f'\n[decay_node] runtime set 可 alive_n={alive_n(eng2)} (設計では frozen=駆動に使わない)', flush=True)
print('=== probe 終了（ファイル非生成・実験 run なし） ===', flush=True)
