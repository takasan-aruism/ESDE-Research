#!/usr/bin/env python3
"""v1104a Step B' — 追加調整 1: 観察 2 を scope × n-size × shuffle × self-loop 層化

Step H-3 reinvestigation_2 を per-chain 保持に拡張、scope × n-size_bin × shuffle_type
× is_self_loop で集約。

入力 (read-only):
  - unified/v1101a/outputs/main/attention_emit_seed{N}.parquet (chain 構築)
  - developmental/v106/outputs/main/cid_atom_sim_matrix_seed{N}.parquet (PAIR sim)
  - developmental/v106/outputs/main/window_trajectory/window_cid_alignment_seed{N}.csv (cid_n_core)
  - unified/v1101a/outputs/main/integration_composition_alpha.parquet (n_alpha_members)
  - unified/v1101a/outputs/main/integration_composition_beta.parquet (n_beta_members)

出力:
  - unified/v1104a/outputs/main/observation_2_per_chain_shuffle.parquet (per chain)
  - unified/v1104a/outputs/main/observation_2_scope_stratified.parquet (集約)
  - unified/v1104a/outputs/main/observation_2_nan_report.json (defensive NaN report)
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1101A_MAIN = REPO_ROOT / 'unified/v1101a/outputs/main'
V106_MAIN = REPO_ROOT / 'developmental/v106/outputs/main'
V1104A_MAIN = REPO_ROOT / 'unified/v1104a/outputs/main'

WINDOW_RANGE = range(20, 70)
N_SHUFFLE = 10
RNG_SEED = 1104


# ---------- n-size bin functions (v1104a §1.5 別列名運用) ----------
def cid_n_core_bin(n):
    if pd.isna(n): return 'NA'
    n = int(n)
    if n == 2: return 'CID_n=2'
    if n == 3: return 'CID_n=3'
    if n == 4: return 'CID_n=4'
    return 'CID_n=5+'


def n_alpha_bin(n):
    if pd.isna(n): return 'NA'
    n = int(n)
    if n == 1: return 'alpha_n=1'
    if n == 2: return 'alpha_n=2'
    if n == 3: return 'alpha_n=3'
    return 'alpha_n=4+'


def n_beta_bin(n):
    if pd.isna(n): return 'NA'
    n = int(n)
    if n == 1: return 'beta_n=1'
    if n == 2: return 'beta_n=2'
    if n == 3: return 'beta_n=3'
    return 'beta_n=4+'


def compute_per_chain_shuffle(seeds: list[int]) -> tuple[pd.DataFrame, dict]:
    """per chain で shuffle A/B/C 再計算"""
    nan_report = {'cid_n_core_missing': 0, 'edges_dropped_unknown_cid': 0,
                  'chains_with_partial_unknown': 0}
    rng = np.random.default_rng(RNG_SEED)

    rows = []
    for sd in seeds:
        em_p = V1101A_MAIN / f'attention_emit_seed{sd}.parquet'
        em = pd.read_parquet(em_p, columns=['seed','window','change_scope','scope_id',
                                              'change_metric_type','attention_candidate_id',
                                              'predecessor_attention_ref','qc_regime'])
        em = em[em['window'].isin(WINDOW_RANGE)]
        em = em[em['qc_regime'] == 'conscious_dominant']
        em = em.dropna(subset=['predecessor_attention_ref'])
        em['attention_candidate_id'] = em['attention_candidate_id'].astype(int)
        em['predecessor_attention_ref'] = em['predecessor_attention_ref'].astype(int)

        sim_p = V106_MAIN / f'cid_atom_sim_matrix_seed{sd}.parquet'
        sim_df = pd.read_parquet(sim_p)
        atom_cols = [c for c in sim_df.columns if c not in ('seed', 'cid')]
        cid_list = sim_df['cid'].astype(int).tolist()
        M = sim_df[atom_cols].fillna(0).to_numpy(dtype=np.float64)
        PAIR = cosine_similarity(M, M)
        cid_to_idx = {c: i for i, c in enumerate(cid_list)}
        all_cids = np.array(list(cid_to_idx.keys()))

        for scope in em['change_scope'].unique():
            sub = em[em['change_scope'] == scope]

            # per scope: chain ごとに edges を取得、scope 内 to_pool も用意
            chains = []
            for (sid, mt), grp in sub.groupby(['scope_id', 'change_metric_type']):
                grp = grp.sort_values('window').reset_index(drop=True)
                cf = grp['predecessor_attention_ref'].to_numpy()
                ct = grp['attention_candidate_id'].to_numpy()
                chains.append((int(sid), str(mt), cf, ct))

            scope_to_pool = np.concatenate([c[3] for c in chains]) if chains else np.array([])

            for (sid, mt, cf_arr, ct_arr) in chains:
                n_edges = len(cf_arr)
                if n_edges == 0:
                    continue

                # 実測 sim (per edge)
                actual_sims = []
                unknown_partial = False
                for cf, ct in zip(cf_arr, ct_arr):
                    if int(cf) in cid_to_idx and int(ct) in cid_to_idx:
                        actual_sims.append(PAIR[cid_to_idx[int(cf)], cid_to_idx[int(ct)]])
                    else:
                        nan_report['edges_dropped_unknown_cid'] += 1
                        unknown_partial = True
                if unknown_partial:
                    nan_report['chains_with_partial_unknown'] += 1
                if not actual_sims:
                    continue
                sim_actual = float(np.mean(actual_sims))
                n_self_loops = int(np.sum(cf_arr == ct_arr))
                is_full_self_loop = bool(n_self_loops == n_edges)

                # shuffle A: chain 内 permutation
                a_sims = []
                for _ in range(N_SHUFFLE):
                    to_perm = rng.permutation(ct_arr)
                    s = [PAIR[cid_to_idx[int(cf)], cid_to_idx[int(ct)]]
                         for cf, ct in zip(cf_arr, to_perm)
                         if int(cf) in cid_to_idx and int(ct) in cid_to_idx]
                    if s:
                        a_sims.append(float(np.mean(s)))
                sim_a = float(np.mean(a_sims)) if a_sims else np.nan

                # shuffle B: scope 内 chain 間 (scope_to_pool からサンプル)
                b_sims = []
                for _ in range(N_SHUFFLE):
                    idx = rng.choice(len(scope_to_pool), size=n_edges, replace=False
                                      if n_edges <= len(scope_to_pool) else True)
                    to_b = scope_to_pool[idx]
                    s = [PAIR[cid_to_idx[int(cf)], cid_to_idx[int(ct)]]
                         for cf, ct in zip(cf_arr, to_b)
                         if int(cf) in cid_to_idx and int(ct) in cid_to_idx]
                    if s:
                        b_sims.append(float(np.mean(s)))
                sim_b = float(np.mean(b_sims)) if b_sims else np.nan

                # shuffle C: global cid pool
                c_sims = []
                for _ in range(N_SHUFFLE):
                    to_c = rng.choice(all_cids, size=n_edges)
                    s = [PAIR[cid_to_idx[int(cf)], cid_to_idx[int(ct)]]
                         for cf, ct in zip(cf_arr, to_c)
                         if int(cf) in cid_to_idx and int(ct) in cid_to_idx]
                    if s:
                        c_sims.append(float(np.mean(s)))
                sim_c = float(np.mean(c_sims)) if c_sims else np.nan

                rows.append({
                    'seed': sd,
                    'change_scope': scope,
                    'scope_id': sid,
                    'change_metric_type': mt,
                    'chain_length': n_edges,
                    'n_self_loops': n_self_loops,
                    'is_full_self_loop': is_full_self_loop,
                    'sim_actual': sim_actual,
                    'sim_shuffle_A': sim_a,
                    'sim_shuffle_B': sim_b,
                    'sim_shuffle_C': sim_c,
                    'lift_A': sim_actual - sim_a if not np.isnan(sim_a) else np.nan,
                    'lift_B': sim_actual - sim_b if not np.isnan(sim_b) else np.nan,
                    'lift_C': sim_actual - sim_c if not np.isnan(sim_c) else np.nan,
                })
        print(f'  seed {sd}: {sum(1 for r in rows if r["seed"]==sd):,} chains')

    return pd.DataFrame(rows), nan_report


def load_n_size_maps() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """cid_n_core / integration_n_alpha_members / integration_n_beta_members"""
    cid_rows = []
    for sd in range(24):
        p = V106_MAIN / 'window_trajectory' / f'window_cid_alignment_seed{sd}.csv'
        d = pd.read_csv(p, usecols=['cognitive_id', 'n_core_member'])
        for cid, n in d.groupby('cognitive_id')['n_core_member'].max().items():
            cid_rows.append({'seed': sd, 'scope_id': int(cid),
                              'cid_n_core': int(n)})
    cid_map = pd.DataFrame(cid_rows)

    a = pd.read_parquet(V1101A_MAIN / 'integration_composition_alpha.parquet',
                         columns=['seed', 'alpha_id', 'n_members']
                       ).rename(columns={'alpha_id': 'scope_id',
                                          'n_members': 'integration_n_alpha_members'})
    b = pd.read_parquet(V1101A_MAIN / 'integration_composition_beta.parquet',
                         columns=['seed', 'beta_id', 'n_members']
                       ).rename(columns={'beta_id': 'scope_id',
                                          'n_members': 'integration_n_beta_members'})
    return cid_map, a, b


def stratify_per_chain(per_chain: pd.DataFrame, cid_map: pd.DataFrame,
                        a_map: pd.DataFrame, b_map: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """per-chain に n-size bin を join、scope × n-size_bin × shuffle × self-loop で集約"""
    nan_report = {'cid_join_missing': 0, 'alpha_join_missing': 0,
                  'beta_join_missing': 0}

    pc = per_chain.copy()

    # CID join
    m_cid = pc[pc['change_scope'] == 'CID'].merge(
        cid_map, on=['seed', 'scope_id'], how='left')
    nan_report['cid_join_missing'] = int(m_cid['cid_n_core'].isna().sum())
    m_cid['n_size_bin'] = m_cid['cid_n_core'].apply(cid_n_core_bin)

    # alpha join
    m_a = pc[pc['change_scope'] == 'alpha'].merge(
        a_map, on=['seed', 'scope_id'], how='left')
    nan_report['alpha_join_missing'] = int(m_a['integration_n_alpha_members'].isna().sum())
    m_a['n_size_bin'] = m_a['integration_n_alpha_members'].apply(n_alpha_bin)

    # beta join
    m_b = pc[pc['change_scope'] == 'beta'].merge(
        b_map, on=['seed', 'scope_id'], how='left')
    nan_report['beta_join_missing'] = int(m_b['integration_n_beta_members'].isna().sum())
    m_b['n_size_bin'] = m_b['integration_n_beta_members'].apply(n_beta_bin)

    # ESDE 3 解像度 (層化対象外、scope そのものを n_size_bin に)
    m_esde = pc[pc['change_scope'].str.startswith('ESDE')].copy()
    m_esde['n_size_bin'] = m_esde['change_scope']

    keep = ['seed','change_scope','scope_id','change_metric_type','chain_length',
            'n_self_loops','is_full_self_loop','sim_actual',
            'sim_shuffle_A','sim_shuffle_B','sim_shuffle_C',
            'lift_A','lift_B','lift_C','n_size_bin']
    combined = pd.concat([m_cid[keep], m_a[keep], m_b[keep], m_esde[keep]],
                         ignore_index=True)

    # 集約: scope × n_size_bin × shuffle_type × is_self_loop
    agg_rows = []
    for (scope, nbin, isl), grp in combined.groupby(
        ['change_scope', 'n_size_bin', 'is_full_self_loop']):
        for st, lift_col in [('A', 'lift_A'), ('B', 'lift_B'), ('C', 'lift_C')]:
            vals = grp[lift_col].dropna()
            if len(vals) == 0:
                continue
            agg_rows.append({
                'change_scope': scope,
                'n_size_bin': nbin,
                'is_full_self_loop': isl,
                'shuffle_type': st,
                'n_chains': len(vals),
                'lift_mean': float(vals.mean()),
                'lift_median': float(vals.median()),
                'lift_std': float(vals.std()),
                'abs_lift_mean': float(vals.abs().mean()),
                'significant_001': bool(abs(vals.mean()) > 0.01),
            })
    return pd.DataFrame(agg_rows), nan_report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', default='0..23')
    args = ap.parse_args()
    lo, hi = args.seeds.split('..')
    seeds = list(range(int(lo), int(hi)+1))

    V1104A_MAIN.mkdir(parents=True, exist_ok=True)
    print(f'=== v1104a Step B 追加調整 1 ===')
    print(f'seeds: {seeds}, N_SHUFFLE: {N_SHUFFLE}')

    t0 = time.time()
    print('\n[1] per-chain shuffle A/B/C 再計算')
    pc, nr_shuf = compute_per_chain_shuffle(seeds)
    pc_out = V1104A_MAIN / 'observation_2_per_chain_shuffle.parquet'
    pc.to_parquet(pc_out, index=False)
    print(f'  wrote {pc_out.name} ({len(pc):,} chains, {time.time()-t0:.1f}s)')

    print('\n[2] n-size join + scope-stratified 集約')
    t1 = time.time()
    cid_map, a_map, b_map = load_n_size_maps()
    print(f'  cid_map: {len(cid_map):,}, a_map: {len(a_map):,}, b_map: {len(b_map):,}')
    strat, nr_join = stratify_per_chain(pc, cid_map, a_map, b_map)
    strat_out = V1104A_MAIN / 'observation_2_scope_stratified.parquet'
    strat.to_parquet(strat_out, index=False)
    print(f'  wrote {strat_out.name} ({len(strat):,} rows, {time.time()-t1:.1f}s)')

    nan_report = {**nr_shuf, **nr_join}
    nr_out = V1104A_MAIN / 'observation_2_nan_report.json'
    nr_out.write_text(json.dumps(nan_report, indent=2), encoding='utf-8')
    print(f'  NaN report: {nan_report}')

    print(f'\n=== total elapsed {time.time()-t0:.1f}s ===')

    # サマリ
    print('\n--- scope × shuffle_type lift_mean (is_full_self_loop=False) ---')
    s = strat[strat['is_full_self_loop'] == False]
    print(s.groupby(['change_scope', 'shuffle_type'])['lift_mean'].mean().round(4)
            .to_string())
    print('\n--- scope × n_size_bin × shuffle_type lift_mean (is_full_self_loop=False) ---')
    s2 = s.groupby(['change_scope', 'n_size_bin', 'shuffle_type'])['lift_mean'].mean().round(4)
    print(s2.to_string())


if __name__ == '__main__':
    main()
