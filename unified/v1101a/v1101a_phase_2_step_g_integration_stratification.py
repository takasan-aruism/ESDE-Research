#!/usr/bin/env python3
"""v1101a 段階 2 Step G — Integration 構成層化観察

Taka 指摘 (2026-05-19): 段階 1/2 で Integration α/β を member 数や Q/C 分布の
偏りで層化観察していない。同じ alpha でも 5/5/5 と 5/2/2 では結果が異なる
はず。絶対格言 #4「集団平均の罠 / 層化必須」と直結。

新バージョン切らず v1101a 内追加観察。新規 main run 不要、既存出力流用のみ。

実装:
1. per (seed, alpha_id/beta_id) で n_members + member の qc_ratio gini 算出
   (gini = Q/C 分布の偏り、0=均等、1=極端な偏り)
2. 段階 1 attention_emit/propagation/causality を alpha_id/beta_id で join
3. n_members bin × gini bin で層化集計
4. 観察事実出力 (judgement なし、絶対格言 #12)

書き込み: unified/v1101a/outputs/main/ 配下のみ
"""
from __future__ import annotations
import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V105_INTEGRATION = REPO_ROOT / 'developmental/v105/diag_v105_main/integration'
V1101A_ROOT = REPO_ROOT / 'unified/v1101a'
OUT_MAIN = V1101A_ROOT / 'outputs/main'

N_MEMBERS_BINS = [(1,1,'n=1'), (2,2,'n=2'), (3,3,'n=3'), (4, 999,'n=4+')]
GINI_BINS = [(0.0, 0.05,'low (近均等)'), (0.05, 0.20,'mid'), (0.20, 1.0,'high (偏り)')]


def gini(values: np.ndarray) -> float:
    """gini index of values (0 = equal, ~1 = max inequality)"""
    if len(values) < 2:
        return 0.0
    v = np.sort(values.astype(float))
    n = len(v)
    cum = v.sum()
    if cum <= 0:
        return 0.0
    return float((2 * np.arange(1, n+1) - n - 1).dot(v) / (n * cum))


def load_alpha_members(seed: int) -> pd.DataFrame:
    """per alpha_id の member cids list を返す (cid, alpha_id) DataFrame"""
    p = V105_INTEGRATION / f'alpha_membership_log_seed{seed}.csv'
    df = pd.read_csv(p)
    rows = []
    for _, r in df.iterrows():
        ids_str = str(r['alpha_ids'])
        if ids_str in ('nan', '', 'None'): continue
        for aid in ids_str.split('|'):
            if aid.strip():
                rows.append({'cid': int(r['cid_id']), 'alpha_id': int(aid)})
    return pd.DataFrame(rows)


def load_beta_members(seed: int) -> pd.DataFrame:
    p = V105_INTEGRATION / f'beta_distribution_log_seed{seed}.csv'
    df = pd.read_csv(p)
    return df[['beta_id', 'target_cid']].drop_duplicates().rename(
        columns={'target_cid': 'cid'})


def compute_composition(seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """per (seed, alpha_id) / (seed, beta_id) で n_members + qc_ratio gini"""
    # 段階 1 attention_emit から CID scope の per (cid, window) qc_ratio を取得
    emit_path = OUT_MAIN / f'attention_emit_seed{seed}.parquet'
    emit = pd.read_parquet(emit_path, columns=['change_scope','scope_id','window','qc_ratio'])
    cid_qc = (emit[emit['change_scope']=='CID']
              [['scope_id','window','qc_ratio']]
              .rename(columns={'scope_id': 'cid'})
              .dropna(subset=['qc_ratio']))

    alpha_mem = load_alpha_members(seed)
    beta_mem = load_beta_members(seed)

    # alpha: per alpha_id × window で member の qc_ratio gini
    alpha_rows = []
    for aid, grp in alpha_mem.groupby('alpha_id'):
        member_cids = grp['cid'].tolist()
        n_mem = len(member_cids)
        # per window で gini
        sub = cid_qc[cid_qc['cid'].isin(member_cids)]
        if len(sub) == 0:
            alpha_rows.append({'seed': seed, 'alpha_id': int(aid),
                                'n_members': n_mem, 'qc_gini_mean': np.nan,
                                'qc_gini_max': np.nan, 'n_windows_observed': 0})
            continue
        gini_per_w = sub.groupby('window')['qc_ratio'].apply(
            lambda x: gini(x.to_numpy()) if len(x) >= 2 else 0.0)
        alpha_rows.append({
            'seed': seed, 'alpha_id': int(aid), 'n_members': n_mem,
            'qc_gini_mean': float(gini_per_w.mean()),
            'qc_gini_max': float(gini_per_w.max()),
            'n_windows_observed': int(len(gini_per_w)),
        })

    beta_rows = []
    for bid, grp in beta_mem.groupby('beta_id'):
        member_cids = grp['cid'].tolist()
        n_mem = len(member_cids)
        sub = cid_qc[cid_qc['cid'].isin(member_cids)]
        if len(sub) == 0:
            beta_rows.append({'seed': seed, 'beta_id': int(bid),
                               'n_members': n_mem, 'qc_gini_mean': np.nan,
                               'qc_gini_max': np.nan, 'n_windows_observed': 0})
            continue
        gini_per_w = sub.groupby('window')['qc_ratio'].apply(
            lambda x: gini(x.to_numpy()) if len(x) >= 2 else 0.0)
        beta_rows.append({
            'seed': seed, 'beta_id': int(bid), 'n_members': n_mem,
            'qc_gini_mean': float(gini_per_w.mean()),
            'qc_gini_max': float(gini_per_w.max()),
            'n_windows_observed': int(len(gini_per_w)),
        })

    return pd.DataFrame(alpha_rows), pd.DataFrame(beta_rows)


def bin_n_members(n: int) -> str:
    for lo, hi, label in N_MEMBERS_BINS:
        if lo <= n <= hi:
            return label
    return 'unknown'


def bin_gini(g: float) -> str:
    if pd.isna(g): return 'unknown'
    for lo, hi, label in GINI_BINS:
        if lo <= g < hi:
            return label
    return GINI_BINS[-1][2]


def stratified_observation(comp_alpha_all: pd.DataFrame, comp_beta_all: pd.DataFrame,
                            causality_all: pd.DataFrame) -> pd.DataFrame:
    """段階 1/2 attention_causality を alpha/beta 構成軸で層化集計"""
    rows = []
    # alpha scope
    alpha_lookup = comp_alpha_all.set_index(['seed','alpha_id'])
    sub = causality_all[causality_all['change_scope']=='alpha'].copy()
    sub = sub.merge(comp_alpha_all.rename(columns={'alpha_id':'scope_id'}),
                     on=['seed','scope_id'], how='left')
    sub['n_members_bin'] = sub['n_members'].apply(bin_n_members)
    sub['qc_gini_bin'] = sub['qc_gini_mean'].apply(bin_gini)

    for (n_bin, gini_bin), grp in sub.groupby(['n_members_bin','qc_gini_bin']):
        if len(grp) == 0: continue
        rows.append({
            'scope': 'alpha',
            'n_members_bin': n_bin, 'qc_gini_bin': gini_bin,
            'n_records': len(grp),
            'n_unique_integrations': grp['scope_id'].nunique(),
            'conscious_frac': float((grp['qc_regime']=='conscious_dominant').mean()),
            'mean_influence': float(grp['influence_candidate_count'].mean()),
            'mean_influence_cog': float(grp[grp['qc_regime']=='cognitive_dominant']['influence_candidate_count'].mean()),
            'mean_influence_csc': float(grp[grp['qc_regime']=='conscious_dominant']['influence_candidate_count'].mean()),
            'top_causality_sum': grp['causality_candidate_path_sum'].mode().iloc[0] if len(grp['causality_candidate_path_sum'].dropna())>0 else None,
            'top_causality_zscore': grp['causality_candidate_path_zscore'].mode().iloc[0] if len(grp['causality_candidate_path_zscore'].dropna())>0 else None,
            'familiarity_frac_zscore': float((grp['causality_candidate_path_zscore']=='familiarity').mean()),
            'integration_alpha_frac_zscore': float((grp['causality_candidate_path_zscore']=='integration_alpha').mean()),
            'integration_beta_frac_zscore': float((grp['causality_candidate_path_zscore']=='integration_beta').mean()),
        })

    # beta scope
    sub_b = causality_all[causality_all['change_scope']=='beta'].copy()
    sub_b = sub_b.merge(comp_beta_all.rename(columns={'beta_id':'scope_id'}),
                         on=['seed','scope_id'], how='left')
    sub_b['n_members_bin'] = sub_b['n_members'].apply(bin_n_members)
    sub_b['qc_gini_bin'] = sub_b['qc_gini_mean'].apply(bin_gini)

    for (n_bin, gini_bin), grp in sub_b.groupby(['n_members_bin','qc_gini_bin']):
        if len(grp) == 0: continue
        rows.append({
            'scope': 'beta',
            'n_members_bin': n_bin, 'qc_gini_bin': gini_bin,
            'n_records': len(grp),
            'n_unique_integrations': grp['scope_id'].nunique(),
            'conscious_frac': float((grp['qc_regime']=='conscious_dominant').mean()),
            'mean_influence': float(grp['influence_candidate_count'].mean()),
            'mean_influence_cog': float(grp[grp['qc_regime']=='cognitive_dominant']['influence_candidate_count'].mean()),
            'mean_influence_csc': float(grp[grp['qc_regime']=='conscious_dominant']['influence_candidate_count'].mean()),
            'top_causality_sum': grp['causality_candidate_path_sum'].mode().iloc[0] if len(grp['causality_candidate_path_sum'].dropna())>0 else None,
            'top_causality_zscore': grp['causality_candidate_path_zscore'].mode().iloc[0] if len(grp['causality_candidate_path_zscore'].dropna())>0 else None,
            'familiarity_frac_zscore': float((grp['causality_candidate_path_zscore']=='familiarity').mean()),
            'integration_alpha_frac_zscore': float((grp['causality_candidate_path_zscore']=='integration_alpha').mean()),
            'integration_beta_frac_zscore': float((grp['causality_candidate_path_zscore']=='integration_beta').mean()),
        })

    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', default='0..23')
    args = ap.parse_args()
    lo, hi = args.seeds.split('..')
    seeds = list(range(int(lo), int(hi)+1))

    print('=== v1101a 段階 2 Step G — Integration 構成層化観察 ===')
    print(f'seeds: {seeds}')

    t0 = time.time()
    alpha_dfs, beta_dfs = [], []
    for sd in seeds:
        ta, tb = compute_composition(sd)
        alpha_dfs.append(ta); beta_dfs.append(tb)
        print(f'  seed {sd}: alpha={len(ta)}, beta={len(tb)}')
    comp_alpha = pd.concat(alpha_dfs, ignore_index=True)
    comp_beta = pd.concat(beta_dfs, ignore_index=True)
    comp_alpha.to_parquet(OUT_MAIN / 'integration_composition_alpha.parquet', index=False)
    comp_beta.to_parquet(OUT_MAIN / 'integration_composition_beta.parquet', index=False)
    print(f'構成指標完了: alpha {len(comp_alpha)}, beta {len(comp_beta)}, elapsed={time.time()-t0:.1f}s')

    # 層化集計
    t1 = time.time()
    causality_all = pd.read_parquet(OUT_MAIN / 'attention_causality_all.parquet')
    df_strat = stratified_observation(comp_alpha, comp_beta, causality_all)
    df_strat.to_parquet(OUT_MAIN / 'stratified_observation_integration.parquet', index=False)
    print(f'層化集計完了: rows={len(df_strat)}, elapsed={time.time()-t1:.1f}s')

    print(f'\ntotal elapsed {time.time()-t0:.1f}s')


if __name__ == '__main__':
    main()
