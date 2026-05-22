#!/usr/bin/env python3
"""v1104 Step D — 観察 3: attention trajectory ↔ response_atom_distribution 対応

設計書 §2.3 + Step A §1.5 確定 (GPT 追加 5):
- 既知再観察回避 (認知優位安定 / 意識優位移動は v1101a で確認済)
- 新規性は trajectory ↔ response_atom_distribution 対応に限定
  · trajectory 安定 ⇔ response 収束 が対応するか
  · trajectory 拡散 ⇔ response 拡散 が対応するか

入力:
- v1101a attention_emit (chain 構築)
- v1102 primary_table (receiver_bin × change_metric_type、時間粒度 effect_delta)
- v1103 response_atom_distribution (max_prob、entropy 算出)

出力: observation_3_trajectory_response.parquet
書込み: unified/v1104/outputs/main/ のみ
"""
from __future__ import annotations
import argparse, time
from pathlib import Path
import numpy as np
import pandas as pd
from collections import Counter

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1101A_MAIN = REPO_ROOT / 'unified/v1101a/outputs/main'
V1102_MAIN = REPO_ROOT / 'unified/v1102/outputs/main'
V1103_MAIN = REPO_ROOT / 'unified/v1103/outputs/main'
OUT_MAIN = REPO_ROOT / 'unified/v1104/outputs/main'

WINDOW_RANGE = list(range(20, 70))


def compute_trajectory_metrics(seed: int, verbose: bool = True) -> pd.DataFrame:
    """per (scope, scope_id, qc_regime) で trajectory 安定度 + 拡散度"""
    t0 = time.time()
    p = V1101A_MAIN / f'attention_emit_seed{seed}.parquet'
    em = pd.read_parquet(p, columns=['seed', 'window', 'change_scope', 'scope_id',
                                       'change_metric_type', 'attention_candidate_id',
                                       'qc_regime'])
    em = em[em['window'].isin(WINDOW_RANGE)]
    em = em.dropna(subset=['attention_candidate_id'])
    em['attention_candidate_id'] = em['attention_candidate_id'].astype(int)

    rows = []
    for (scope, scope_id, mt, regime), grp in em.groupby(
        ['change_scope', 'scope_id', 'change_metric_type', 'qc_regime']
    ):
        grp = grp.sort_values('window').reset_index(drop=True)
        n_records = len(grp)
        if n_records < 2:
            stability = np.nan
            diffusion_unique = 1 if n_records == 1 else 0
        else:
            cands = grp['attention_candidate_id'].tolist()
            # 安定度 = 隣接 window で同一 attention_candidate_id の割合
            n_same = sum(1 for i in range(1, n_records) if cands[i] == cands[i-1])
            stability = n_same / (n_records - 1)
            # 拡散度 = unique cid 数 / chain length
            diffusion_unique = len(set(cands))
        rows.append({
            'seed': seed,
            'change_scope': scope,
            'scope_id': scope_id,
            'change_metric_type': mt,
            'qc_regime': regime,
            'chain_length': n_records,
            'trajectory_stability': stability,
            'trajectory_unique_candidates': diffusion_unique,
            'diffusion_ratio': diffusion_unique / max(n_records, 1),
        })
    df = pd.DataFrame(rows)
    if verbose:
        print(f'[seed {seed}] trajectory metrics: {len(df)} chains, elapsed: {time.time()-t0:.1f}s')
    return df


def aggregate_per_receiver_bin(traj_all: pd.DataFrame) -> pd.DataFrame:
    """trajectory metrics を v1102 primary_table と同型の receiver_bin × metric 軸に集約"""
    # Step G alpha composition for n_members × qc_gini bin
    comp_a = pd.read_parquet(V1101A_MAIN / 'integration_composition_alpha.parquet')
    comp_b = pd.read_parquet(V1101A_MAIN / 'integration_composition_beta.parquet')

    # CID n_core_member map from v10.6 window_trajectory
    import os
    cid_ncore_rows = []
    for sd in range(24):
        p = REPO_ROOT / 'developmental/v106/outputs/main/window_trajectory' / f'window_cid_alignment_seed{sd}.csv'
        df = pd.read_csv(p, usecols=['cognitive_id', 'n_core_member'])
        g = df.groupby('cognitive_id')['n_core_member'].max()
        for cid, n in g.items():
            cid_ncore_rows.append({'seed': sd, 'scope_id': int(cid), 'n_core_member': int(n)})
    cid_ncore = pd.DataFrame(cid_ncore_rows)

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

    def gini_bin(g):
        if pd.isna(g): return 'NA'
        if g < 0.05: return 'gini=low'
        if g < 0.20: return 'gini=mid'
        return 'gini=high'

    def cid_bin(n):
        if pd.isna(n): return 'NA'
        n = int(n)
        if n == 2: return 'CID_n=2'
        if n == 3: return 'CID_n=3'
        if n == 4: return 'CID_n=4'
        if n == 5: return 'CID_n=5'
        return 'CID_n=6+'

    # receiver_bin 付与
    parts = []
    # alpha
    sub = traj_all[traj_all['change_scope'] == 'alpha'].copy()
    sub = sub.merge(comp_a.rename(columns={'alpha_id': 'scope_id'}), on=['seed', 'scope_id'], how='left')
    sub['receiver_bin'] = sub['n_members'].apply(n_alpha_bin) + ' / ' + sub['qc_gini_mean'].apply(gini_bin)
    parts.append(sub[['seed','window' if 'window' in sub.columns else None] if False else
                     ['seed','change_scope','scope_id','change_metric_type','qc_regime',
                      'chain_length','trajectory_stability','trajectory_unique_candidates',
                      'diffusion_ratio','receiver_bin']])
    # beta
    sub = traj_all[traj_all['change_scope'] == 'beta'].copy()
    sub = sub.merge(comp_b.rename(columns={'beta_id': 'scope_id'}), on=['seed', 'scope_id'], how='left')
    sub['receiver_bin'] = sub['n_members'].apply(n_beta_bin) + ' / ' + sub['qc_gini_mean'].apply(gini_bin)
    parts.append(sub[['seed','change_scope','scope_id','change_metric_type','qc_regime',
                      'chain_length','trajectory_stability','trajectory_unique_candidates',
                      'diffusion_ratio','receiver_bin']])
    # CID
    sub = traj_all[traj_all['change_scope'] == 'CID'].copy()
    sub = sub.merge(cid_ncore, on=['seed', 'scope_id'], how='left')
    sub['receiver_bin'] = sub['n_core_member'].apply(cid_bin)
    parts.append(sub[['seed','change_scope','scope_id','change_metric_type','qc_regime',
                      'chain_length','trajectory_stability','trajectory_unique_candidates',
                      'diffusion_ratio','receiver_bin']])
    # ESDE
    sub = traj_all[traj_all['change_scope'].isin(['ESDE_event','ESDE_step10','ESDE_window'])].copy()
    sub['receiver_bin'] = sub['change_scope']
    parts.append(sub[['seed','change_scope','scope_id','change_metric_type','qc_regime',
                      'chain_length','trajectory_stability','trajectory_unique_candidates',
                      'diffusion_ratio','receiver_bin']])

    full = pd.concat(parts, ignore_index=True)
    return full


def compute_response_distribution_metrics() -> pd.DataFrame:
    """v1103 response_atom_distribution から per (receiver_bin, metric, sim_basis, k) で max_prob / entropy"""
    p = V1103_MAIN / 'response_atom_distribution.parquet'
    dist = pd.read_parquet(p)
    rows = []
    for (rbin, mt, sb, k), grp in dist.groupby(['receiver_bin', 'change_metric_type',
                                                  'sim_basis', 'k']):
        probs = grp['response_prob'].to_numpy()
        if len(probs) == 0:
            continue
        max_prob = float(probs.max())
        # entropy = -sum(p * log p)
        p_nonzero = probs[probs > 0]
        entropy = float(-np.sum(p_nonzero * np.log(p_nonzero))) if len(p_nonzero) > 0 else 0.0
        rows.append({
            'receiver_bin': rbin,
            'change_metric_type': mt,
            'sim_basis': sb,
            'k': k,
            'response_max_prob': max_prob,
            'response_entropy': entropy,
            'n_candidates': len(probs),
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', default='0..23')
    args = ap.parse_args()
    lo, hi = args.seeds.split('..')
    seeds = list(range(int(lo), int(hi)+1))
    OUT_MAIN.mkdir(parents=True, exist_ok=True)

    print('=== v1104 Step D 観察 3 (trajectory ↔ response_atom_distribution 対応) ===')
    print(f'seeds: {seeds}, window: 20-69')

    t_start = time.time()
    traj_dfs = []
    for sd in seeds:
        traj_dfs.append(compute_trajectory_metrics(sd))
    traj_all = pd.concat(traj_dfs, ignore_index=True)

    # receiver_bin 集約
    print(f'\nreceiver_bin 集約 (Step G + cid n_core)...')
    traj_rb = aggregate_per_receiver_bin(traj_all)

    # per (receiver_bin, change_metric_type, qc_regime) で集約
    print(f'per (receiver_bin, metric, qc_regime) 集約...')
    traj_agg = traj_rb.groupby(['receiver_bin', 'change_metric_type', 'qc_regime']).agg(
        n_chains=('chain_length', 'count'),
        chain_len_mean=('chain_length', 'mean'),
        traj_stability_mean=('trajectory_stability', 'mean'),
        traj_unique_mean=('trajectory_unique_candidates', 'mean'),
        diffusion_ratio_mean=('diffusion_ratio', 'mean'),
    ).reset_index()

    # response_atom_distribution metrics
    print(f'response_atom_distribution metrics 算出...')
    resp = compute_response_distribution_metrics()

    # 対応観察: per (receiver_bin, metric) で trajectory と response を join
    # v1103 は意識優位のみ前提でなく全体 (qc_regime 横断)、また sim_basis × k で複数値
    # ここでは trajectory の qc_regime 別を保持しつつ response (sim_basis 別) を join
    print(f'対応観察 join...')
    merged = traj_agg.merge(resp, on=['receiver_bin', 'change_metric_type'], how='left')

    out = OUT_MAIN / 'observation_3_trajectory_response.parquet'
    merged.to_parquet(out, index=False)
    print(f'\nwrote {out} ({len(merged):,} rows)')

    # サマリ
    print(f'\n=== 全サマリ ===')
    print(f'n traj × resp combinations: {len(merged):,}')
    print(f'trajectory stability mean (全 chains): {traj_rb["trajectory_stability"].mean():.4f}')
    print(f'response_max_prob mean: {resp["response_max_prob"].mean():.4f}')
    print(f'response_entropy mean: {resp["response_entropy"].mean():.4f}')

    # 対応観察: trajectory stability vs response_max_prob (Pearson 相関)
    valid = merged.dropna(subset=['traj_stability_mean', 'response_max_prob'])
    if len(valid) >= 3:
        from scipy.stats import pearsonr, spearmanr
        rp, pp = pearsonr(valid['traj_stability_mean'], valid['response_max_prob'])
        rs, ps = spearmanr(valid['traj_stability_mean'], valid['response_max_prob'])
        print(f'\n=== trajectory stability vs response_max_prob 相関 ===')
        print(f'  Pearson r={rp:.4f}, p={pp:.4e}, n={len(valid)}')
        print(f'  Spearman r={rs:.4f}, p={ps:.4e}')

        rp2, pp2 = pearsonr(valid['diffusion_ratio_mean'], valid['response_entropy'])
        rs2, ps2 = spearmanr(valid['diffusion_ratio_mean'], valid['response_entropy'])
        print(f'\n=== diffusion_ratio vs response_entropy 相関 ===')
        print(f'  Pearson r={rp2:.4f}, p={pp2:.4e}')
        print(f'  Spearman r={rs2:.4f}, p={ps2:.4e}')

    print(f'\n=== qc_regime × sim_basis 別 (trajectory stability、response_max_prob 平均) ===')
    g = merged.groupby(['qc_regime', 'sim_basis']).agg(
        traj_stability_mean=('traj_stability_mean', 'mean'),
        response_max_prob_mean=('response_max_prob', 'mean'),
        response_entropy_mean=('response_entropy', 'mean'),
    ).round(4)
    print(g.to_string())

    print(f'\ntotal elapsed: {time.time()-t_start:.1f}s')


if __name__ == '__main__':
    main()
