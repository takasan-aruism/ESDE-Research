#!/usr/bin/env python3
"""v1301 Long run（並列）— 17 CID × 4対照 × 3 seed = 204 child を long で並列

通常 long（maturation20 + tracking50 = 70 window × 500 = 35,000 step）。1 window=500step の
smoke（cw_run.py）の像が本スケール(long)で保つか/反転するかを確認（smoke seed0 を絶対視しない）。
並列: multiprocessing.Pool（物理コア）+ OMP/MKL/OPENBLAS_NUM_THREADS=1（24-seed run と同じ）。
設計は確定（4 knob・stress OFF・semantic_pressure OFF・現行 main 縮小・写像=サンプラー#30）。判定/解釈は書かない。
一方向: 読=frozen(per_subject_seed0)。書=unified/v1301/。child engine は in-memory・親物理非書込。
"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import sys, time, json, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import multiprocessing as mp
warnings.filterwarnings('ignore')

REPO = Path('/home/takasan/esde/ESDE-Research')
for p in ['autonomy/v82', 'ecology/engine', 'primitive/v910', 'cognition/semantic_injection/v4_pipeline/v43']:
    sys.path.insert(0, str(REPO / p))
from esde_v82_engine import V82Engine, V82EncapsulationParams
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9

THETA_KAPPA = 4.0
WINDOWS = 70            # 通常 long: mat20+track50。重ければ起動前に調整
N_WORKERS = max(1, (os.cpu_count() or 4) // 2)   # 物理コア数(Ryzen 24C=48HT→24); HT は compute-bound で利得なし
OUT = REPO / 'unified/v1301'
SIG = ['alive_ratio', 'link_density', 'R_density', 'sync_order', 'n_labels', 'label_density', 'mean_label_ncore']


def load_cids():
    d = pd.read_csv(REPO / 'primitive/v918/diag_v918_main/subjects/per_subject_seed0.csv')
    n5 = d[d['v11_m_c_n_core'] == '5'].copy()
    for c in ['v11_b_gen', 'v11_m_c_s_avg', 'v11_m_c_r_core', 'v11_m_c_phase_sig']:
        n5[c] = pd.to_numeric(n5[c], errors='coerce')
    return n5[['cognitive_id', 'v11_b_gen', 'v11_m_c_s_avg', 'v11_m_c_r_core', 'v11_m_c_phase_sig']].dropna().reset_index(drop=True)


def real_knobs(df):
    sm, ss = df.v11_m_c_s_avg.mean(), df.v11_m_c_s_avg.std()
    rmin, rmax = df.v11_m_c_r_core.min(), df.v11_m_c_r_core.max()
    return [dict(cid=int(r.cognitive_id), N=int(round(r.v11_b_gen * 10)),
                 plb=float(0.007 * (1 + 0.15 * np.tanh((r.v11_m_c_s_avg - sm) / (ss + 1e-9)))),
                 k_sync=float(0.05 + (r.v11_m_c_r_core - rmin) / (rmax - rmin + 1e-9) * 0.25),
                 theta_mu=float(r.v11_m_c_phase_sig)) for _, r in df.iterrows()]


def worker(task):
    N, plb, ks, tm, seed = task['N'], task['plb'], task['k_sync'], task['theta_mu'], task['run_seed']
    encap = V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)       # stress OFF
    eng = V82Engine(seed=seed, N=N, plb=plb, encap_params=encap)
    eng.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    for a, v in [('torque_order', 'age'), ('deviation_enabled', True), ('semantic_gravity_enabled', True)]:
        if hasattr(eng.virtual, a):
            setattr(eng.virtual, a, v)
    eng.physics.params.K_sync = ks
    eng.pressure_params.pressure_prob = 0.0                                           # semantic_pressure OFF
    if not (isinstance(tm, float) and np.isnan(tm)):
        eng.state.theta[:] = eng.state.rng.vonmises(tm, THETA_KAPPA, N) % (2 * np.pi)
    eng.run_injection()
    for _ in range(WINDOWS):
        eng.step_window(steps=500)
    Nn = eng.state.n_nodes
    al = list(eng.state.alive_n); aln, ll = len(al), len(eng.state.alive_l)
    sync = float(abs(np.mean(np.exp(1j * eng.state.theta[al])))) if al else 0.0
    rpos = sum(1 for k in eng.state.alive_l if eng.state.R.get(k, 0) > 0)
    ncs = [len(i['nodes']) if isinstance(i, dict) else len(i.nodes) for i in eng.virtual.labels.values()]
    sg = dict(alive_ratio=aln / Nn, link_density=ll / Nn, R_density=rpos / max(ll, 1), sync_order=sync,
              n_labels=len(eng.virtual.labels), label_density=len(eng.virtual.labels) / Nn,
              mean_label_ncore=float(np.mean(ncs)) if ncs else 0.0)
    return {**{k: task[k] for k in ['control', 'cid', 'seed', 'N', 'plb', 'k_sync', 'theta_mu']}, **sg}


def build_tasks():
    df = load_cids(); realK = real_knobs(df)
    Nmean = int(round(df.v11_b_gen.mean() * 10))
    Nlo, Nhi = min(k['N'] for k in realK), max(k['N'] for k in realK)
    plblo, plbhi = min(k['plb'] for k in realK), max(k['plb'] for k in realK)
    perm = np.random.default_rng(12345).permutation(len(realK))
    tasks = []
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
            else:
                N, plb, ks, tm = Nmean, 0.007, 0.1, np.nan
            for s in range(3):
                tasks.append(dict(control=ctrl, cid=cid, seed=s, N=N, plb=plb, k_sync=ks,
                                  theta_mu=tm, run_seed=cid * 100 + s))
    return tasks


def main():
    t0 = time.time()
    tasks = build_tasks()
    print(f'=== Long 並列 run: {len(tasks)} child, WINDOWS={WINDOWS}(=35000step), workers={N_WORKERS} ===', flush=True)
    with mp.Pool(N_WORKERS, maxtasksperchild=4) as pool:
        rows = pool.map(worker, tasks)
    res = pd.DataFrame(rows)
    res.to_parquet(OUT / 'childworld_signatures_long.parquet', index=False)
    by_cc = res.groupby(['control', 'cid'])[SIG].mean().reset_index()
    summary = {'design': 'cw_run_long_parallel', 'windows': WINDOWS, 'steps_per_child': WINDOWS * 500,
               'n_child': len(res), 'workers': N_WORKERS, 'stress': 'OFF', 'semantic_pressure': 'OFF',
               'total_s': round(time.time() - t0, 1)}
    for ctrl in ['real', 'shuffle', 'random', 'canon']:
        sub = by_cc[by_cc.control == ctrl]
        summary[ctrl] = {c: {'mean': round(float(sub[c].mean()), 4), 'std': round(float(sub[c].std()), 4)} for c in SIG}
    # real 入力→出力 素の相関(記述)
    real = res[res.control == 'real'].groupby('cid').agg(
        N=('N', 'first'), plb=('plb', 'first'), k_sync=('k_sync', 'first'), theta_mu=('theta_mu', 'first'),
        **{s: (s, 'mean') for s in SIG}).reset_index()
    summary['real_corr'] = {
        'k_sync__sync_order': round(float(real.k_sync.corr(real.sync_order)), 3),
        'plb__link_density': round(float(real.plb.corr(real.link_density)), 3),
        'plb__label_density': round(float(real.plb.corr(real.label_density)), 3),
        'N__label_density': round(float(real.N.corr(real.label_density)), 3),
        'theta_mu__sync_order': round(float(real.theta_mu.corr(real.sync_order)), 3),
    }
    (OUT / 'childworld_summary_long.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'=== 完了 {len(res)} child, {time.time()-t0:.0f}s → *_long.parquet + *_long.json ===', flush=True)
    print(f'  real_corr: {summary["real_corr"]}', flush=True)


if __name__ == '__main__':
    main()
