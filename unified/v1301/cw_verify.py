#!/usr/bin/env python3
"""v1301 実装 検証フェーズ（§8: 本番前の「回るか＋効くか」確認）

確認: (1) 17 CID の4 knob(real)が立つ (2) stress OFF + semantic_pressure OFF が効いている
      (3) §5 K_sync が実際に sync_order を変えるか(書けても読まれねば無視) (4) N=B_Gen×10 の1 child コスト。
一方向: 読=frozen(per_subject_seed0)。書=なし(child engine は in-memory)。親物理非書込。
"""
import sys, time, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
REPO = Path('/home/takasan/esde/ESDE-Research')
for p in ['autonomy/v82', 'ecology/engine', 'primitive/v910', 'cognition/semantic_injection/v4_pipeline/v43']:
    sys.path.insert(0, str(REPO / p))
from esde_v82_engine import V82Engine, V82EncapsulationParams
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9

THETA_KAPPA = 4.0  # 初期θ von Mises 集中度
STEPS = 500


def load_cids():
    d = pd.read_csv(REPO / 'primitive/v918/diag_v918_main/subjects/per_subject_seed0.csv')
    n5 = d[d['v11_m_c_n_core'] == '5'].copy()
    for c in ['v11_b_gen', 'v11_m_c_s_avg', 'v11_m_c_r_core', 'v11_m_c_phase_sig']:
        n5[c] = pd.to_numeric(n5[c], errors='coerce')
    return n5[['cognitive_id', 'v11_b_gen', 'v11_m_c_s_avg', 'v11_m_c_r_core', 'v11_m_c_phase_sig']].dropna().reset_index(drop=True)


def real_knobs(df):
    """real 写像(サンプラー・#30): N=B_Gen×10, plb←S_avg(±15%小幅), K_sync←r_core[0.05,0.3], θ←phase_sig"""
    sm, ss = df.v11_m_c_s_avg.mean(), df.v11_m_c_s_avg.std()
    rmin, rmax = df.v11_m_c_r_core.min(), df.v11_m_c_r_core.max()
    K = []
    for _, r in df.iterrows():
        N = int(round(r.v11_b_gen * 10))
        plb = 0.007 * (1 + 0.15 * np.tanh((r.v11_m_c_s_avg - sm) / (ss + 1e-9)))
        ksync = 0.05 + (r.v11_m_c_r_core - rmin) / (rmax - rmin + 1e-9) * (0.30 - 0.05)
        K.append(dict(cid=int(r.cognitive_id), N=N, plb=round(plb, 5), k_sync=round(ksync, 4),
                      theta_mu=round(float(r.v11_m_c_phase_sig), 4)))
    return K


def build_child(N, plb, k_sync, theta_mu, seed, sem_off=True):
    encap = V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)   # stress OFF
    eng = V82Engine(seed=seed, N=N, plb=plb, encap_params=encap)
    eng.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    for a, v in [('torque_order', 'age'), ('deviation_enabled', True), ('semantic_gravity_enabled', True)]:
        if hasattr(eng.virtual, a):
            setattr(eng.virtual, a, v)
    eng.physics.params.K_sync = k_sync                       # 同期系 knob (後書き)
    if sem_off:
        eng.pressure_params.pressure_prob = 0.0              # semantic_pressure OFF
    # 初期θ ← phase_sig(von Mises) = 世界の初期条件(実現値コピーでない・死線でない)
    eng.state.theta[:] = eng.state.rng.vonmises(theta_mu, THETA_KAPPA, N) % (2 * np.pi)
    eng.run_injection()
    return eng


def sync_order(eng):
    al = list(eng.state.alive_n)
    if not al:
        return 0.0
    return float(abs(np.mean(np.exp(1j * eng.state.theta[al]))))


def run_child(eng, steps=STEPS):
    for _ in range(steps // 50):
        eng.step_window(steps=50)
    return eng


def main():
    df = load_cids()
    K = real_knobs(df)
    print(f'=== 17 CID real knob(先頭6) ===')
    print(f"{'cid':>4}{'N=Bgen×10':>11}{'plb←Savg':>11}{'K_sync←rcore':>13}{'θμ←phase':>10}")
    for k in K[:6]:
        print(f"{k['cid']:>4}{k['N']:>11}{k['plb']:>11}{k['k_sync']:>13}{k['theta_mu']:>10}")
    print(f"  N 範囲: [{min(k['N'] for k in K)}, {max(k['N'] for k in K)}]  "
          f"plb 範囲: [{min(k['plb'] for k in K)}, {max(k['plb'] for k in K)}]  "
          f"K_sync 範囲: [{min(k['k_sync'] for k in K)}, {max(k['k_sync'] for k in K)}]")

    print('\n=== (2) stress/semantic_pressure OFF 確認 ===')
    e = build_child(340, 0.007, 0.1, 0.0, seed=0)
    print(f"  stress_enabled = {e.island_tracker.params.stress_enabled} (False 期待)")
    print(f"  pressure_prob  = {e.pressure_params.pressure_prob} (0.0 期待=semantic_pressure 無効)")

    print('\n=== (3) §5 K_sync が実際に効くか: 同条件で K_sync 0.05 vs 0.5 → sync_order ===')
    t0 = time.time()
    e_lo = run_child(build_child(340, 0.007, 0.05, 0.0, seed=7))
    e_hi = run_child(build_child(340, 0.007, 0.50, 0.0, seed=7))
    so_lo, so_hi = sync_order(e_lo), sync_order(e_hi)
    print(f"  K_sync=0.05 → sync_order={so_lo:.4f} / K_sync=0.50 → sync_order={so_hi:.4f} / 差={abs(so_hi-so_lo):.4f}")
    print(f"  → K_sync は {'効く(sync_order が変わる)' if abs(so_hi-so_lo)>0.02 else '⚠効かない(差≈0=読まれてない?)'}")

    print('\n=== (4) 1 child(real, N=B_Gen×10) コスト ===')
    k0 = K[0]
    t1 = time.time()
    e1 = run_child(build_child(k0['N'], k0['plb'], k0['k_sync'], k0['theta_mu'], seed=k0['cid']*100))
    dt = time.time() - t1
    al, ll = len(e1.state.alive_n), len(e1.state.alive_l)
    print(f"  cid {k0['cid']} N={k0['N']}: {dt:.2f}s, alive_n={al} alive_l={ll} labels={len(e1.virtual.labels)} sync_order={sync_order(e1):.4f}")
    print(f"  概算 204 child(17×4×3) × ~{dt:.1f}s = ~{204*dt/60:.0f} 分")
    print(f"\n  検証総時間 {time.time()-t0:.0f}s")


if __name__ == '__main__':
    main()
