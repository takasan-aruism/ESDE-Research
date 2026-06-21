#!/usr/bin/env python3
"""v1301 本番 run（確定設計）— 17 CID × 4対照 × 3 seed = 204 child

設計(確定): n_core=5 の17 CID, 4 knob(N=B_Gen×10 / plb←S_avg / K_sync←r_core / 初期θ←phase_sig),
  他 canon 固定, stress OFF + semantic_pressure OFF(現行 main 縮小), 写像=サンプラー(#30)。
対照: real / shuffle / random / canon。readout=物理署名(N 正規化)+位相状態。判定・解釈は書かない。
一方向: 読=frozen(per_subject_seed0)。書=unified/v1301/ のみ。親物理 非書込。child engine は in-memory。
"""
import sys, time, json, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
REPO = Path('/home/takasan/esde/ESDE-Research')
for p in ['autonomy/v82', 'ecology/engine', 'primitive/v910', 'cognition/semantic_injection/v4_pipeline/v43']:
    sys.path.insert(0, str(REPO / p))
from esde_v82_engine import V82Engine, V82EncapsulationParams
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9

THETA_KAPPA, STEPS, N_SEED = 4.0, 500, 3
OUT = REPO / 'unified/v1301'


def load_cids():
    d = pd.read_csv(REPO / 'primitive/v918/diag_v918_main/subjects/per_subject_seed0.csv')
    n5 = d[d['v11_m_c_n_core'] == '5'].copy()
    for c in ['v11_b_gen', 'v11_m_c_s_avg', 'v11_m_c_r_core', 'v11_m_c_phase_sig']:
        n5[c] = pd.to_numeric(n5[c], errors='coerce')
    return n5[['cognitive_id', 'v11_b_gen', 'v11_m_c_s_avg', 'v11_m_c_r_core', 'v11_m_c_phase_sig']].dropna().reset_index(drop=True)


def real_knobs(df):
    sm, ss = df.v11_m_c_s_avg.mean(), df.v11_m_c_s_avg.std()
    rmin, rmax = df.v11_m_c_r_core.min(), df.v11_m_c_r_core.max()
    out = []
    for _, r in df.iterrows():
        out.append(dict(cid=int(r.cognitive_id),
                        N=int(round(r.v11_b_gen * 10)),
                        plb=float(0.007 * (1 + 0.15 * np.tanh((r.v11_m_c_s_avg - sm) / (ss + 1e-9)))),
                        k_sync=float(0.05 + (r.v11_m_c_r_core - rmin) / (rmax - rmin + 1e-9) * 0.25),
                        theta_mu=float(r.v11_m_c_phase_sig)))
    return out


def build_child(N, plb, k_sync, theta_mu, seed):
    encap = V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)      # stress OFF
    eng = V82Engine(seed=seed, N=N, plb=plb, encap_params=encap)
    eng.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    for a, v in [('torque_order', 'age'), ('deviation_enabled', True), ('semantic_gravity_enabled', True)]:
        if hasattr(eng.virtual, a):
            setattr(eng.virtual, a, v)
    eng.physics.params.K_sync = k_sync
    eng.pressure_params.pressure_prob = 0.0                                          # semantic_pressure OFF
    if theta_mu is not None:                                                         # canon は uniform θ
        eng.state.theta[:] = eng.state.rng.vonmises(theta_mu, THETA_KAPPA, N) % (2 * np.pi)
    eng.run_injection()
    for _ in range(STEPS // 50):
        eng.step_window(steps=50)
    return eng


def signature(eng):
    N = eng.state.n_nodes
    al = list(eng.state.alive_n)
    aln, ll = len(al), len(eng.state.alive_l)
    sync = float(abs(np.mean(np.exp(1j * eng.state.theta[al])))) if al else 0.0
    rpos = sum(1 for k in eng.state.alive_l if eng.state.R.get(k, 0) > 0)
    labs = eng.virtual.labels
    ncs = [len(i['nodes']) if isinstance(i, dict) else len(i.nodes) for i in labs.values()]
    return dict(alive_ratio=aln / N, link_density=ll / N, R_density=rpos / max(ll, 1),
                sync_order=sync, n_labels=len(labs), label_density=len(labs) / N,
                mean_label_ncore=float(np.mean(ncs)) if ncs else 0.0)


def main():
    t0 = time.time()
    df = load_cids()
    realK = real_knobs(df)
    Nmean = int(round(df.v11_b_gen.mean() * 10))
    Nlo, Nhi = min(k['N'] for k in realK), max(k['N'] for k in realK)
    plblo, plbhi = min(k['plb'] for k in realK), max(k['plb'] for k in realK)
    perm = np.random.default_rng(12345).permutation(len(realK))                      # shuffle 固定置換

    rows = []
    for ctrl in ['real', 'shuffle', 'random', 'canon']:
        for i, k in enumerate(realK):
            cid = k['cid']
            if ctrl == 'real':
                N, plb, ks, tm = k['N'], k['plb'], k['k_sync'], k['theta_mu']
            elif ctrl == 'shuffle':
                kk = realK[perm[i]]; N, plb, ks, tm = kk['N'], kk['plb'], kk['k_sync'], kk['theta_mu']
            elif ctrl == 'random':
                rng = np.random.default_rng(cid * 1000)
                N = int(rng.integers(Nlo, Nhi + 1)); plb = float(rng.uniform(plblo, plbhi))
                ks = float(rng.uniform(0.05, 0.30)); tm = float(rng.uniform(-np.pi, np.pi))
            else:  # canon
                N, plb, ks, tm = Nmean, 0.007, 0.1, None
            for s in range(N_SEED):
                eng = build_child(N, plb, ks, tm, seed=cid * 100 + s)
                sg = signature(eng)
                rows.append(dict(control=ctrl, cid=cid, seed=s, N=N, plb=plb, k_sync=ks,
                                 theta_mu=(tm if tm is not None else np.nan), **sg))
        print(f'  {ctrl} done ({time.time()-t0:.0f}s)', flush=True)

    res = pd.DataFrame(rows)
    res.to_parquet(OUT / 'childworld_signatures.parquet', index=False)

    # 3 seed 平均 → (control,cid) 署名。対照ごとの分布(判定でなく素の記述)
    sig_cols = ['alive_ratio', 'link_density', 'R_density', 'sync_order', 'n_labels', 'label_density', 'mean_label_ncore']
    by_cc = res.groupby(['control', 'cid'])[sig_cols].mean().reset_index()
    summary = {'design': 'cw_run_real_shuffle_random_canon', 'n_cid': len(realK), 'n_seed': N_SEED,
               'n_child': len(res), 'steps': STEPS, 'stress': 'OFF', 'semantic_pressure': 'OFF(pressure_prob=0)',
               'note_body_diff': '本体main(stress OFF/semantic_pressure ON)との差: 本childはsemantic_pressureも切る',
               'total_s': round(time.time() - t0, 1)}
    for ctrl in ['real', 'shuffle', 'random', 'canon']:
        sub = by_cc[by_cc.control == ctrl]
        summary[ctrl] = {c: {'mean': round(float(sub[c].mean()), 4), 'std': round(float(sub[c].std()), 4),
                             'min': round(float(sub[c].min()), 4), 'max': round(float(sub[c].max()), 4)} for c in sig_cols}
    (OUT / 'childworld_summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'=== 完了 {len(res)} child, {time.time()-t0:.0f}s → childworld_signatures.parquet + summary.json ===', flush=True)


if __name__ == '__main__':
    main()
