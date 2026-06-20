#!/usr/bin/env python3
"""v13_childworld 寿命同期版（並列）— run 長 = CID 寿命 × 倍率(1:1, 1:10), 上限35000, CID死で停止

Taka 確定: 本体の時間経過を反映＝child の run 長を CID 寿命に合わせる。param(4 knob)は誕生 M_c のまま据え置き。
 run 長 = min(35000, lifespan_main × ratio)。ratio∈{1,10}。CID が死んだらそこで停止(=run長がそれ)。
 他は long run と同一(4 knob 据置・stress OFF・semantic_pressure OFF・4対照・写像=サンプラー#30)。判定/解釈は書かない。
一方向: 読=frozen(per_subject_seed0)。書=unified/v13_childworld/。child engine は in-memory・親物理非書込。
"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1'); os.environ.setdefault('MKL_NUM_THREADS', '1'); os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import sys, time, json, warnings
from pathlib import Path
import numpy as np, pandas as pd
import multiprocessing as mp
warnings.filterwarnings('ignore')
REPO = Path('/home/takasan/esde/ESDE-Research')
for p in ['autonomy/v82', 'ecology/engine', 'primitive/v910', 'cognition/semantic_injection/v4_pipeline/v43']:
    sys.path.insert(0, str(REPO / p))
from esde_v82_engine import V82Engine, V82EncapsulationParams
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9

THETA_KAPPA = 4.0
CAP = 35000
RATIOS = [1, 10]
MAIN_END_WIN = 70
N_WORKERS = max(1, (os.cpu_count() or 4) // 2)
OUT = REPO / 'unified/v13_childworld'
SIG = ['alive_ratio', 'link_density', 'R_density', 'sync_order', 'n_labels', 'label_density', 'mean_label_ncore']


def load():
    d = pd.read_csv(REPO / 'primitive/v918/diag_v918_main/subjects/per_subject_seed0.csv')
    n5 = d[d['v11_m_c_n_core'] == '5'].copy()
    for c in ['v11_b_gen', 'v11_m_c_s_avg', 'v11_m_c_r_core', 'v11_m_c_phase_sig', 'birth_window', 'host_lost_window']:
        n5[c] = pd.to_numeric(n5[c], errors='coerce')
    n5['life_main'] = ((n5.host_lost_window.fillna(MAIN_END_WIN).clip(upper=MAIN_END_WIN) - n5.birth_window) * 500).astype(int)
    sm, ss = n5.v11_m_c_s_avg.mean(), n5.v11_m_c_s_avg.std()
    rmin, rmax = n5.v11_m_c_r_core.min(), n5.v11_m_c_r_core.max()
    return [dict(cid=int(r.cognitive_id), N=int(round(r.v11_b_gen * 10)), life=int(r.life_main),
                 plb=float(0.007 * (1 + 0.15 * np.tanh((r.v11_m_c_s_avg - sm) / (ss + 1e-9)))),
                 k_sync=float(0.05 + (r.v11_m_c_r_core - rmin) / (rmax - rmin + 1e-9) * 0.25),
                 theta_mu=float(r.v11_m_c_phase_sig)) for _, r in n5.iterrows()]


def worker(task):
    N, plb, ks, tm, run_len = task['N'], task['plb'], task['k_sync'], task['theta_mu'], task['run_len']
    encap = V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)
    eng = V82Engine(seed=task['run_seed'], N=N, plb=plb, encap_params=encap)
    eng.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    for a, v in [('torque_order', 'age'), ('deviation_enabled', True), ('semantic_gravity_enabled', True)]:
        if hasattr(eng.virtual, a):
            setattr(eng.virtual, a, v)
    eng.physics.params.K_sync = ks
    eng.pressure_params.pressure_prob = 0.0
    if not (isinstance(tm, float) and np.isnan(tm)):
        eng.state.theta[:] = eng.state.rng.vonmises(tm, THETA_KAPPA, N) % (2 * np.pi)
    eng.run_injection()
    full, rem = run_len // 500, run_len % 500
    for _ in range(full):
        eng.step_window(steps=500)
    if rem > 0:
        eng.step_window(steps=rem)
    Nn = eng.state.n_nodes
    al = list(eng.state.alive_n); aln, ll = len(al), len(eng.state.alive_l)
    sync = float(abs(np.mean(np.exp(1j * eng.state.theta[al])))) if al else 0.0
    rpos = sum(1 for k in eng.state.alive_l if eng.state.R.get(k, 0) > 0)
    ncs = [len(i['nodes']) if isinstance(i, dict) else len(i.nodes) for i in eng.virtual.labels.values()]
    sg = dict(alive_ratio=aln / Nn, link_density=ll / Nn, R_density=rpos / max(ll, 1), sync_order=sync,
              n_labels=len(eng.virtual.labels), label_density=len(eng.virtual.labels) / Nn,
              mean_label_ncore=float(np.mean(ncs)) if ncs else 0.0)
    return {**{k: task[k] for k in ['ratio', 'control', 'cid', 'seed', 'N', 'plb', 'k_sync', 'theta_mu', 'life', 'run_len']}, **sg}


def build_tasks(K):
    Nmean = int(round(np.mean([k['N'] for k in K])))
    lifemean = int(round(np.mean([k['life'] for k in K])))
    Nlo, Nhi = min(k['N'] for k in K), max(k['N'] for k in K)
    plblo, plbhi = min(k['plb'] for k in K), max(k['plb'] for k in K)
    lifelo, lifehi = min(k['life'] for k in K), max(k['life'] for k in K)
    perm = np.random.default_rng(12345).permutation(len(K))
    tasks = []
    for ratio in RATIOS:
        for ctrl in ['real', 'shuffle', 'random', 'canon']:
            for i, k in enumerate(K):
                cid = k['cid']
                if ctrl == 'real':
                    N, plb, ks, tm, life = k['N'], k['plb'], k['k_sync'], k['theta_mu'], k['life']
                elif ctrl == 'shuffle':
                    kk = K[perm[i]]; N, plb, ks, tm, life = kk['N'], kk['plb'], kk['k_sync'], kk['theta_mu'], kk['life']
                elif ctrl == 'random':
                    rng = np.random.default_rng(cid * 1000 + ratio)
                    N = int(rng.integers(Nlo, Nhi + 1)); plb = float(rng.uniform(plblo, plbhi))
                    ks = float(rng.uniform(0.05, 0.30)); tm = float(rng.uniform(-np.pi, np.pi)); life = int(rng.integers(lifelo, lifehi + 1))
                else:
                    N, plb, ks, tm, life = Nmean, 0.007, 0.1, np.nan, lifemean
                run_len = min(CAP, life * ratio)
                for s in range(3):
                    tasks.append(dict(ratio=ratio, control=ctrl, cid=cid, seed=s, N=N, plb=plb, k_sync=ks,
                                      theta_mu=tm, life=life, run_len=run_len, run_seed=cid * 100 + s))
    return tasks


def main():
    t0 = time.time()
    K = load()
    tasks = build_tasks(K)
    tot = sum(t['run_len'] for t in tasks)
    print(f'=== 寿命同期 並列: {len(tasks)} child, 総step {tot}, workers={N_WORKERS} ===', flush=True)
    with mp.Pool(N_WORKERS, maxtasksperchild=4) as pool:
        rows = pool.map(worker, tasks)
    res = pd.DataFrame(rows)
    res.to_parquet(OUT / 'childworld_signatures_lifespan.parquet', index=False)
    summary = {'design': 'cw_lifespan_synced', 'ratios': RATIOS, 'cap': CAP, 'n_child': len(res),
               'stress': 'OFF', 'semantic_pressure': 'OFF', 'knobs': 'fixed birth M_c', 'total_s': round(time.time() - t0, 1)}
    for ratio in RATIOS:
        rr = res[res.ratio == ratio]
        real = rr[rr.control == 'real'].groupby('cid').agg(life=('life', 'first'), run_len=('run_len', 'first'),
            N=('N', 'first'), plb=('plb', 'first'), k_sync=('k_sync', 'first'), theta_mu=('theta_mu', 'first'),
            **{s: (s, 'mean') for s in SIG}).reset_index()
        d = {'real_corr': {
                'life__n_labels': round(float(real.life.corr(real.n_labels)), 3),
                'k_sync__sync_order': round(float(real.k_sync.corr(real.sync_order)), 3),
                'plb__link_density': round(float(real.plb.corr(real.link_density)), 3),
                'plb__label_density': round(float(real.plb.corr(real.label_density)), 3),
                'theta_mu__sync_order': round(float(real.theta_mu.corr(real.sync_order)), 3)}}
        by = rr.groupby(['control', 'cid'])[SIG].mean().reset_index()
        for ctrl in ['real', 'shuffle', 'random', 'canon']:
            sub = by[by.control == ctrl]
            d[ctrl] = {c: {'mean': round(float(sub[c].mean()), 4), 'std': round(float(sub[c].std()), 4)} for c in SIG}
        summary[f'ratio_{ratio}'] = d
    (OUT / 'childworld_summary_lifespan.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'=== 完了 {len(res)} child, {time.time()-t0:.0f}s ===', flush=True)
    for ratio in RATIOS:
        print(f'  ratio 1:{ratio} real_corr: {summary[f"ratio_{ratio}"]["real_corr"]}', flush=True)


if __name__ == '__main__':
    main()
