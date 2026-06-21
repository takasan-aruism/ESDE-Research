#!/usr/bin/env python3
"""v13 child-world step-0 — CID 情報が child に伝わるか（real が shuffle より親 CID に対応するか）を pairing(Mantel) で固める。

【観察対象注釈ブロック / 同系・異系宣言】
- 同系内: 各 child は親 seed0 CID の縮小版（N=B_gen×10）。異系対応(v1110-v1113)でない。過去成功 v10.2/v10.7/v9.18/v106 と同型＝同系内動学の観察。
- 読=frozen: per_subject_seed0 / v19g_canon / 仕様書。書=unified/v1301/ のみ。child engine は in-memory、親 physics/inject/ledger/state 非書込（一方向、v9.13 方針内）。

【設計（Web Claude 指示書 §8 点検 → 承認後の確定版）】
- 問い: stratum 内で real の child 署名距離が親 CID 距離(D_parent)に対応するか（Mantel + 置換 null）。
- チャネル6本: N←B_gen / plb←S_avg(s_plb=0.3 に拡幅) / K_sync←r_core(100%伝達) / 初期θ←phase_sig(84%) / decay_node←V1 / decay_link←V2。beta=1.0 frozen。Z 後回し。
- transform は real/canon 同一式・stratum 内 z。run 長は共通固定 35k（観測窓を揃える＝寿命同期の交絡を避ける、§8.2b）。
- 署名 = child が育てた label 個体群の創発人口統計（入力の直写しを避ける、§4/§8.2）: n_labels / size mean,std / share gini / mean age / lifecycle 活動量。phase_sig や sync_order(入力の写し)は使わない。
- 対照: real(各CID×seed) + canon(stratum 既定×seed=seed雑音床)。shuffle は child 再 run せず Mantel 置換で表現（無料）。
- D_parent 2 通り: Mc(S_avg,r_core,phase_sig) と 6入力(＋B_gen,V1,V2)。V1/V2 が伝達を足すか引くか（§8.6-1）。
- n_core 別(n2/n4/n5)・合算なし(#33/集団平均の罠)。判定なし(success/fail 置かない)。
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
RUN_LEN = 35000
S_PLB, S_DN, S_DL = 0.3, 0.3, 0.3          # 拡幅率（probe で s=0.4 端でも非破綻を確認）
BASE_PLB, BASE_DN, BASE_DL = 0.007, 0.005, 0.05  # canon base（child デフォルトと一致を実機確認済）
STRATA = ['2', '4', '5']                    # n_core=3 は 3 CID で Mantel 不能ゆえ除外
# §8.4 候補。完全populated かつ M_c から独立な非 M_c 軸を選定（M_c を超える clean identity の有無を見る検証核）。
# 当初案 v11_mean_delta は S_avg と層内 r=0.73=M_c 二重注入(#33違反)、delta_familiarity は n2 で 25/54 NaN ゆえ不採用。
# capture_rate(M_c |r|≤0.30) / n_captured(≤0.28, capture_rate と 0.26=別物)。decay_node/link への割当は構造同型弱く暫定（Taka 可変）。
V1_COL, V2_COL = 'v11_capture_rate', 'v11_n_captured'   # V1→decay_node(E) / V2→decay_link(S)
N_SEEDS = int(os.environ.get('CW_SEEDS', '3'))         # smoke=3 → 承認後拡張
N_CANON_SEEDS = 6
MANTEL_K = 999
N_WORKERS = max(1, (os.cpu_count() or 4) // 2)
OUT = REPO / 'unified/v1301'
SIG = ['n_labels', 'mean_size', 'std_size', 'share_gini', 'mean_age', 'lifecycle_events']


def gini(x):
    x = np.sort(np.asarray(x, float))
    if x.size == 0 or x.sum() <= 0:
        return 0.0
    n = x.size
    return float((2 * np.sum((np.arange(1, n + 1)) * x) - (n + 1) * x.sum()) / (n * x.sum()))


def load():
    d = pd.read_csv(REPO / 'primitive/v918/diag_v918_main/subjects/per_subject_seed0.csv')
    cols = ['v11_b_gen', 'v11_m_c_s_avg', 'v11_m_c_r_core', 'v11_m_c_phase_sig', V1_COL, V2_COL]
    cids, stats = [], {}
    for nc in STRATA:
        s = d[d['v11_m_c_n_core'] == nc].copy()
        for c in cols:
            s[c] = pd.to_numeric(s[c], errors='coerce')
        s = s.dropna(subset=cols)
        st = dict(b_mean=float(s.v11_b_gen.mean()),
                  s_mean=float(s.v11_m_c_s_avg.mean()), s_std=float(s.v11_m_c_s_avg.std() + 1e-9),
                  r_min=float(s.v11_m_c_r_core.min()), r_max=float(s.v11_m_c_r_core.max()),
                  v1_mean=float(s[V1_COL].mean()), v1_std=float(s[V1_COL].std() + 1e-9),
                  v2_mean=float(s[V2_COL].mean()), v2_std=float(s[V2_COL].std() + 1e-9))
        stats[nc] = st
        for _, r in s.iterrows():
            cids.append(dict(stratum=nc, cid=int(r.cognitive_id),
                             b_gen=float(r.v11_b_gen), s_avg=float(r.v11_m_c_s_avg),
                             r_core=float(r.v11_m_c_r_core), phase_sig=float(r.v11_m_c_phase_sig),
                             V1=float(r[V1_COL]), V2=float(r[V2_COL])))
    return cids, stats


def transform(c, st):
    """real: CID 値→6 param（stratum 内 z、real/canon 同一式）。"""
    return dict(N=int(round(c['b_gen'] * 10)),
                plb=BASE_PLB * (1 + S_PLB * np.tanh((c['s_avg'] - st['s_mean']) / st['s_std'])),
                ksync=0.05 + (c['r_core'] - st['r_min']) / (st['r_max'] - st['r_min'] + 1e-9) * 0.25,
                theta_mu=c['phase_sig'],
                dnode=BASE_DN * (1 + S_DN * np.tanh((c['V1'] - st['v1_mean']) / st['v1_std'])),
                dlink=BASE_DL * (1 + S_DL * np.tanh((c['V2'] - st['v2_mean']) / st['v2_std'])))


def canon_params(st):
    return dict(N=int(round(st['b_mean'] * 10)), plb=BASE_PLB, ksync=0.1,
                theta_mu=None, dnode=BASE_DN, dlink=BASE_DL)


def worker(task):
    pm = task['params']
    encap = V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)
    eng = V82Engine(seed=task['run_seed'], N=pm['N'], plb=pm['plb'], encap_params=encap)
    eng.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    for a, v in [('torque_order', 'age'), ('deviation_enabled', True), ('semantic_gravity_enabled', True)]:
        if hasattr(eng.virtual, a):
            setattr(eng.virtual, a, v)
    eng.physics.params.K_sync = pm['ksync']
    eng.physics.params.decay_rate_node = pm['dnode']
    eng.physics.params.decay_rate_link = pm['dlink']
    eng.pressure_params.pressure_prob = 0.0
    if pm['theta_mu'] is not None:
        eng.state.theta[:] = eng.state.rng.vonmises(pm['theta_mu'], THETA_KAPPA, pm['N']) % (2 * np.pi)
    eng.run_injection()
    for _ in range(RUN_LEN // 500):
        eng.step_window(steps=500)
    v = eng.virtual
    labs = list(v.labels.values())
    sizes = [len(l['nodes']) for l in labs]
    shares = [l['share'] for l in labs]
    wc = int(getattr(eng, 'window_count', RUN_LEN // 500))
    ages = [wc - l['born'] for l in labs]
    sig = dict(n_labels=len(labs),
               mean_size=float(np.mean(sizes)) if sizes else 0.0,
               std_size=float(np.std(sizes)) if sizes else 0.0,
               share_gini=gini(shares),
               mean_age=float(np.mean(ages)) if ages else 0.0,
               lifecycle_events=int(len(getattr(v, 'lifecycle_log', []))))
    keep = ['stratum', 'control', 'cid', 'seed', 'b_gen', 's_avg', 'r_core', 'phase_sig', 'V1', 'V2']
    pstore = {f'p_{k}': (pm[k] if pm[k] is not None else np.nan) for k in pm}
    return {**{k: task.get(k) for k in keep}, **pstore, **sig}


def build_tasks(cids, stats):
    tasks = []
    for c in cids:
        for s in range(N_SEEDS):
            tasks.append(dict(stratum=c['stratum'], control='real', cid=c['cid'], seed=s,
                              b_gen=c['b_gen'], s_avg=c['s_avg'], r_core=c['r_core'],
                              phase_sig=c['phase_sig'], V1=c['V1'], V2=c['V2'],
                              params=transform(c, stats[c['stratum']]),
                              run_seed=c['cid'] * 100 + s))
    for nc in STRATA:
        for s in range(N_CANON_SEEDS):
            tasks.append(dict(stratum=nc, control='canon', cid=-1 - s, seed=s,
                              b_gen=np.nan, s_avg=np.nan, r_core=np.nan, phase_sig=np.nan,
                              V1=np.nan, V2=np.nan, params=canon_params(stats[nc]),
                              run_seed=900000 + int(nc) * 100 + s))
    return tasks


# ---------- 解析（Mantel・n_core 別・合算なし） ----------
def _pdist(M):
    from scipy.spatial.distance import pdist, squareform
    return squareform(pdist(M, 'euclidean'))


def _zstd(A):
    A = np.asarray(A, float)
    return (A - A.mean(0)) / (A.std(0) + 1e-9)


def mantel(Dp, Dc, k, rng):
    iu = np.triu_indices(Dp.shape[0], 1)
    a, b = Dp[iu], Dc[iu]
    r_obs = float(np.corrcoef(a, b)[0, 1])
    n = Dp.shape[0]
    null = np.empty(k)
    for i in range(k):
        perm = rng.permutation(n)
        Dpp = Dp[np.ix_(perm, perm)]
        null[i] = np.corrcoef(Dpp[iu], b)[0, 1]
    p = float((np.sum(null >= r_obs) + 1) / (k + 1))  # 片側（伝達なら正）
    return r_obs, p, null.tolist()


def analyse(res):
    rng = np.random.default_rng(20260621)
    report = {}
    for nc in STRATA:
        real = res[(res.stratum == int(nc)) & (res.control == 'real')]
        g = real.groupby('cid').agg(**{s: (s, 'mean') for s in SIG},
                                    **{c: (c, 'first') for c in ['s_avg', 'r_core', 'phase_sig', 'b_gen', 'V1', 'V2']}).reset_index()
        ncid = len(g)
        if ncid < 5:
            report[f'n{nc}'] = dict(n_cid=ncid, note='Mantel 不能（記述のみ）')
            continue
        Dc = _pdist(_zstd(g[SIG].values))
        ph = g.phase_sig.values
        Dp_mc = _pdist(_zstd(np.column_stack([g.s_avg, g.r_core, np.cos(ph), np.sin(ph)])))
        Dp_6 = _pdist(_zstd(np.column_stack([g.b_gen, g.s_avg, g.r_core, np.cos(ph), np.sin(ph), g.V1, g.V2])))
        r_mc, p_mc, null_mc = mantel(Dp_mc, Dc, MANTEL_K, rng)
        r_6, p_6, null_6 = mantel(Dp_6, Dc, MANTEL_K, rng)
        # 公平な signal/noise: 同一標準化スケールで within-CID(seed 雑音) と between-CID を比較。
        #  （旧版は 3seed平均 real vs 1seed canon で footing 不一致＝雑音過大評価だったため改訂。canon は参考床として別途残す）
        from scipy.spatial.distance import pdist
        mu, sd = real[SIG].mean().values, real[SIG].std().values + 1e-9
        Mz = (real[SIG].values - mu) / sd
        rr = real.assign(**{f'_z{i}': Mz[:, i] for i in range(len(SIG))})
        zc = [f'_z{i}' for i in range(len(SIG))]
        within = [d for _, sub in rr.groupby('cid') if len(sub) > 1 for d in pdist(sub[zc].values)]
        between = pdist(rr.groupby('cid')[zc].mean().values)
        canon = res[(res.stratum == int(nc)) & (res.control == 'canon')]
        cg = canon.groupby('cid').agg(**{s: (s, 'mean') for s in SIG}).reset_index()
        canon_off = pdist((cg[SIG].values - mu) / sd) if len(cg) > 1 else np.array([0.0])
        report[f'n{nc}'] = dict(
            n_cid=ncid,
            mantel_Mc=dict(r=round(r_mc, 3), perm_p=round(p_mc, 4)),
            mantel_6input=dict(r=round(r_6, 3), perm_p=round(p_6, 4)),
            between_cid_mean_D=round(float(np.mean(between)), 3),
            within_cid_seednoise_mean_D=round(float(np.mean(within)) if within else 0.0, 3),
            signal_over_noise=round(float(np.mean(between) / (np.mean(within) + 1e-9)) if within else 0.0, 2),
            canon_floor_mean_D=round(float(np.mean(canon_off)), 3),
            null_Mc=null_mc, null_6=null_6)
    return report


def main():
    t0 = time.time()
    cids, stats = load()
    tasks = build_tasks(cids, stats)
    print(f'=== step-0: {len(tasks)} child (real {sum(1 for t in tasks if t["control"]=="real")} + canon {sum(1 for t in tasks if t["control"]=="canon")}), '
          f'seeds={N_SEEDS}, run_len={RUN_LEN}, workers={N_WORKERS} ===', flush=True)
    with mp.Pool(N_WORKERS, maxtasksperchild=4) as pool:
        rows = pool.map(worker, tasks)
    res = pd.DataFrame(rows)
    res['stratum'] = res['stratum'].astype(int)
    res.to_parquet(OUT / 'cw_step0_signatures.parquet', index=False)
    report = analyse(res)
    meta = dict(design='step0_pairing', run_len=RUN_LEN, n_seeds=N_SEEDS,
                channels6='N,plb,K_sync,theta,decay_node,decay_link (beta frozen)',
                widths=dict(s_plb=S_PLB, s_dn=S_DN, s_dl=S_DL),
                V1=V1_COL, V2=V2_COL, signature=SIG, mantel_K=MANTEL_K,
                total_s=round(time.time() - t0, 1), report=report)
    (OUT / 'cw_step0_summary.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f'=== 完了 {len(res)} child, {time.time()-t0:.0f}s ===', flush=True)
    for nc in STRATA:
        r = report.get(f'n{nc}', {})
        if 'mantel_Mc' in r:
            print(f'  n{nc} (cid={r["n_cid"]}): Mantel_Mc r={r["mantel_Mc"]["r"]} p={r["mantel_Mc"]["perm_p"]} | '
                  f'6input r={r["mantel_6input"]["r"]} p={r["mantel_6input"]["perm_p"]} | '
                  f'signal/noise={r["signal_over_noise"]}', flush=True)
        else:
            print(f'  n{nc}: {r.get("note","")}', flush=True)


if __name__ == '__main__':
    main()
