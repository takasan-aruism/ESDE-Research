#!/usr/bin/env python3
"""v13_childworld 配線可能性 probe (調査・実装ゼロ・再現用)

(A) CID 値: per_subject_seed0 の数値カラムが n_core=5 の17 CID で散るか(CV)。
(B) 物理 param: per-child instance で変調できるかを実走で確認
    (constructor / physics.params post-construction / state init / module定数=不可)。

一方向: 読=frozen(per_subject_seed0)。書=なし(child engine は in-memory のみ, 親物理 非書込)。
"""
import sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
warnings.filterwarnings('ignore')

REPO = Path('/home/takasan/esde/ESDE-Research')
for p in ['autonomy/v82', 'ecology/engine', 'primitive/v910',
          'cognition/semantic_injection/v4_pipeline/v43']:
    sys.path.insert(0, str(REPO / p))


def probe_A():
    print('=== (A) CID 値が n_core=5 の17 CID で散るか (CV 降順, 上位) ===')
    d = pd.read_csv(REPO / 'primitive/v918/diag_v918_main/subjects/per_subject_seed0.csv')
    n5 = d[d['v11_m_c_n_core'] == '5'].copy()
    print(f'  母集団 {len(n5)} CID / per_subject 全 {len(d.columns)} カラム')
    rows = []
    for c in d.columns:
        s = pd.to_numeric(n5[c], errors='coerce')
        if s.notna().sum() < len(n5) * 0.5:
            continue
        mn, mx, me, sd = float(s.min()), float(s.max()), float(s.mean()), float(s.std())
        if mx == mn:
            continue
        cv = sd / abs(me) if abs(me) > 1e-9 else 99.0
        rows.append((c, round(mn, 3), round(mx, 3), round(cv, 3)))
    rows.sort(key=lambda r: -r[3])
    n_scatter = sum(1 for r in rows if r[3] > 0.1)
    print(f'  散る列(CV>0.1): {n_scatter} / 数値列 {len(rows)}')
    for c, mn, mx, cv in rows[:18]:
        print(f'    {c:<32}[{mn}, {mx}] CV={cv}')
    # B_Gen / n_core が散らない(n_core 決定)ことの確認
    bg = pd.to_numeric(n5['v11_b_gen'], errors='coerce')
    print(f'  ※ B_Gen: [{bg.min():.2f},{bg.max():.2f}] CV={bg.std()/bg.mean():.3f} (n5 で帯狭=n_core 決定, 散らない)')


def probe_B():
    print('\n=== (B) 物理 param の per-child 変調 配線(実走) ===')
    from esde_v82_engine import V82Engine
    e = V82Engine(seed=42, N=100, plb=0.0084)
    print(f'  [constructor] N=100 / plb=0.0084 → realizer.p_link_birth={e.realizer.params.p_link_birth}  ✓')
    base = (e.physics.params.K_sync, e.physics.params.beta, e.physics.params.decay_rate_node)
    e.physics.params.K_sync = 0.5
    e.physics.params.beta = 3.0
    e.physics.params.decay_rate_node = 0.02
    print(f'  [physics.params 書込] K_sync/beta/decay_node {base} → '
          f'{(e.physics.params.K_sync, e.physics.params.beta, e.physics.params.decay_rate_node)}  ✓')
    e.run_injection()
    for _ in range(4):
        e.step_window(steps=50)
    print(f'  → 変調後 200step 走行 OK: alive_n={len(e.state.alive_n)} alive_l={len(e.state.alive_l)}  ✓')
    e2 = V82Engine(seed=42, N=100)
    e2.state.theta[:] = e2.state.rng.vonmises(1.0, 4.0, 100) % (2 * np.pi)   # phase_sig→von Mises
    e2.state.F[:] = 1.5
    print(f'  [state init 書込] theta(初期θ)/F(肥沃度): theta[0]={e2.state.theta[0]:.2f} F[0]={e2.state.F[0]}  ✓')
    print('  [不可] BIAS: モジュール定数(esde_v82_engine.py:179 / v43:528 で global 読み) = per-instance 不可')
    print('  [不可] grid幅: build_substrate(N) で N 従属 = 独立 knob 不可')


if __name__ == '__main__':
    probe_A()
    probe_B()
