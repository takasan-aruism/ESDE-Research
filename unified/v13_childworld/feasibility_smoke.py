#!/usr/bin/env python3
"""v13_childworld 実装可能性 smoke (調査・実装ゼロ・再現用)

CID-conditioned child-world 設計(Web Claude 設計)の Code A 実装前チェック:
 (1) V82Engine(N=100)+VirtualLayerV9 が standalone で回るか・コスト・生存・ラベル形成
 (2) plb(p_link_birth) 変調で child の構造(ラベル数/n_core)が変わるか
 (3) n_core=5 CID 形態(s_avg/r_core/phase_sig)が seed0 既存データから取れるか・母集団数

一方向: 読=frozen(per_subject_seed0 / source_events_seed0)。書=なし(親物理 非書込、child engine は in-memory のみ)。
"""
import sys, time, tracemalloc
from pathlib import Path
import numpy as np
import pandas as pd
import warnings; warnings.filterwarnings('ignore')

REPO = Path('/home/takasan/esde/ESDE-Research')
for p in ['autonomy/v82', 'ecology/engine', 'primitive/v910',
          'cognition/semantic_injection/v4_pipeline/v43']:
    sys.path.insert(0, str(REPO / p))

from esde_v82_engine import V82Engine, V82EncapsulationParams, V82_N
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9


def build_child(seed, N=100, plb=0.007):
    """child-world = V82Engine 縮小版 + VirtualLayerV9 (autonomy/v82 既存ルール、param 変調のみ、新法則なし)"""
    encap = V82EncapsulationParams(stress_enabled=True, virtual_enabled=True)
    eng = V82Engine(seed=seed, N=N, plb=plb, encap_params=encap)
    eng.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    for a, v in [('torque_order', 'age'), ('deviation_enabled', True), ('semantic_gravity_enabled', True)]:
        if hasattr(eng.virtual, a):
            setattr(eng.virtual, a, v)
    eng.run_injection()
    return eng


def main():
    print('=== (1)(2) child-world: N=100, run_injection(300)+500step, canon と plb±20% ===')
    tracemalloc.start()
    first_dt = None
    for tag, plb in [('canon', 0.007), ('plb+20%', 0.0084), ('plb-20%', 0.0056)]:
        t0 = time.time()
        eng = build_child(42, N=100, plb=plb)
        for _ in range(10):
            eng.step_window(steps=50)            # 500 step
        dt = time.time() - t0
        first_dt = first_dt or dt
        def _nnodes(info):
            nd = info['nodes'] if isinstance(info, dict) else getattr(info, 'nodes', [])
            return len(nd)
        ncores = sorted(_nnodes(info) for info in eng.virtual.labels.values())
        print(f'  {tag}: plb={plb} time={dt:.2f}s alive_n={len(eng.state.alive_n)} '
              f'alive_l={len(eng.state.alive_l)} labels={len(eng.virtual.labels)} label_n_core={ncores[:12]}')
    _, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
    print(f'  peak mem ~{peak/1e6:.0f}MB (1 child)')

    print('\n=== (3) n_core=5 CID 形態の取得(string→numeric)・母集団 ===')
    d = pd.read_csv(REPO / 'primitive/v918/diag_v918_main/subjects/per_subject_seed0.csv')
    cidcol = 'cognitive_id'
    for c in ['v11_m_c_s_avg', 'v11_m_c_r_core', 'v11_m_c_phase_sig']:
        d[c + '_num'] = pd.to_numeric(d[c], errors='coerce')
    n5 = d[d['v11_m_c_n_core'] == '5']                          # M_c n_core は string 格納
    se = pd.read_parquet(REPO / 'developmental/v107/outputs/main/source_events_seed0.parquet')
    se5 = set(se[se.n_core_member == 5].source_cid.unique())
    ms5 = set(n5[cidcol].astype(int))
    print(f'  M_c n_core=="5": {len(n5)} / source_events n_core=5: {len(se5)} / 積集合(形態取得可): {len(se5 & ms5)}')
    print(f'  s_avg [{n5["v11_m_c_s_avg_num"].min():.3f}, {n5["v11_m_c_s_avg_num"].max():.3f}] / '
          f'r_core [{n5["v11_m_c_r_core_num"].min():.3f}, {n5["v11_m_c_r_core_num"].max():.3f}] / '
          f'phase_sig [{n5["v11_m_c_phase_sig_num"].min():.3f}, {n5["v11_m_c_phase_sig_num"].max():.3f}]')
    n_pop = len(se5 & ms5)
    print(f'\n  → 実装母集団 = 形態が取れる n_core=5 CID = {n_pop} 個')
    print(f'  → コスト概算: {n_pop} CID × 3 seed × 4 対照 = {n_pop*12} child × ~{first_dt:.1f}s = ~{n_pop*12*first_dt/60:.0f} 分 (物理+virtual)')


if __name__ == '__main__':
    main()
