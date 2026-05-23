#!/usr/bin/env python3
"""v1104a Step D' — 追加調整 3: 観察 3 (trajectory) vs v1103 48 次元密度 比較

Step A' 確認要請 2 案 A 採用: density_summary.parquet の 3 種
(raw_density / qweighted_density / const_adjusted_density) + 補助 mean_pairwise_sim
を density 比較対象、atom_centroids_48d_* (per-atom) は本主題範囲外。

設計書 §2.3.4 通り:
- 同一 receiver_bin / 同一 response (max_prob, entropy 2 種固定) / 同一 scope で比較
- coverage 欠損 (join 失敗) は別 parquet 記録
- 異なる scope/response 間で |r| 横並びにしない

入力 (read-only):
  - unified/v1104/outputs/main/observation_3_trajectory_response.parquet (trajectory+response)
  - unified/v1103/outputs/main/density_summary.parquet (3 density + mean_pairwise_sim)

出力:
  - unified/v1104a/outputs/main/observation_3_density_comparison.parquet
    (per (scope, stratum, predictor, response) の Pearson + Spearman + ランキング)
  - unified/v1104a/outputs/main/observation_3_density_coverage.parquet
    (coverage 欠損の理由と件数)
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1103_MAIN = REPO_ROOT / 'unified/v1103/outputs/main'
V1104_MAIN = REPO_ROOT / 'unified/v1104/outputs/main'
V1104A_MAIN = REPO_ROOT / 'unified/v1104a/outputs/main'


TRAJECTORY_PREDICTORS = [
    'traj_stability_mean', 'traj_unique_mean',
    'diffusion_ratio_mean', 'chain_len_mean',
]
DENSITY_PREDICTORS = [
    'raw_density', 'qweighted_density', 'const_adjusted_density',
    'mean_pairwise_sim',
]
RESPONSES = ['response_max_prob', 'response_entropy']


def safe_corr(x, y):
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    mask = ~(np.isnan(x) | np.isnan(y))
    x = x[mask]; y = y[mask]
    n = len(x)
    if n < 3 or np.std(x) == 0 or np.std(y) == 0:
        return (np.nan, np.nan, np.nan, np.nan, n)
    r_p, p_p = pearsonr(x, y)
    r_s, p_s = spearmanr(x, y)
    return (float(r_p), float(p_p), float(r_s), float(p_s), n)


def main():
    V1104A_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1104a Step D 追加調整 3: 観察 3 vs 48 次元密度 3 種 ===')
    t0 = time.time()

    o3 = pd.read_parquet(V1104_MAIN / 'observation_3_trajectory_response.parquet')
    print(f'observation_3 (trajectory+response): {len(o3):,} rows')

    dsm = pd.read_parquet(V1103_MAIN / 'density_summary.parquet',
                           columns=['receiver_bin', 'change_metric_type',
                                    'sim_basis', 'k', 'raw_density',
                                    'qweighted_density', 'const_adjusted_density',
                                    'mean_pairwise_sim'])
    print(f'density_summary: {len(dsm):,} rows')

    # join: receiver_bin × metric × sim_basis × k (qc_regime は trajectory のみ、複製)
    merged = o3.merge(dsm, on=['receiver_bin', 'change_metric_type',
                                'sim_basis', 'k'], how='left')
    print(f'merged: {len(merged):,} rows')

    # coverage 欠損 (どれか density 列が NaN)
    cov_rows = []
    for col in DENSITY_PREDICTORS:
        n_nan = int(merged[col].isna().sum())
        cov_rows.append({'column': col, 'n_nan': n_nan,
                          'n_total': len(merged),
                          'coverage_rate': float(1 - n_nan/len(merged))})
    # 重複 join check (trajectory 側 rows との 1:1 想定)
    cov_rows.append({'column': '_merged_vs_obs3_diff',
                      'n_nan': len(merged) - len(o3),
                      'n_total': len(o3),
                      'coverage_rate': float(len(merged)/len(o3))})
    cov = pd.DataFrame(cov_rows)
    cov_out = V1104A_MAIN / 'observation_3_density_coverage.parquet'
    cov.to_parquet(cov_out, index=False)
    print(f'wrote {cov_out.name}')
    print(cov.to_string(index=False))

    # scope/stratum 定義
    def scope_strata(df):
        """(scope_label, stratum_label, filter_fn) を yield"""
        # ESDE 集約: ESDE_all (3 解像度合算) + 3 解像度個別
        yield 'ESDE', 'ESDE_all', df[df['receiver_bin'].str.startswith('ESDE_')]
        for esde in ['ESDE_event', 'ESDE_step10', 'ESDE_window']:
            yield 'ESDE', esde, df[df['receiver_bin'] == esde]
        # CID 集約 + 5 bin (CID_n=2..6+) 個別
        yield 'CID', 'CID_all', df[df['receiver_bin'].str.startswith('CID_n=')]
        for cn in sorted(df[df['receiver_bin'].str.startswith('CID_n=')]['receiver_bin'].unique()):
            yield 'CID', cn, df[df['receiver_bin'] == cn]
        # alpha / beta は参考のみ (集約のみ、設計書 §2.3.4: ESDE / CID の同一 scope で比較)
        yield 'alpha', 'alpha_all', df[df['receiver_bin'].str.startswith('alpha_')]
        yield 'beta', 'beta_all', df[df['receiver_bin'].str.startswith('beta_')]

    # 比較計算: per (scope, stratum, predictor, response) で Pearson + Spearman
    rows = []
    all_predictors = [(p, 'trajectory') for p in TRAJECTORY_PREDICTORS] + \
                     [(p, 'density') for p in DENSITY_PREDICTORS]
    for scope, stratum, sub in scope_strata(merged):
        for resp in RESPONSES:
            for pred, pred_type in all_predictors:
                r_p, p_p, r_s, p_s, n = safe_corr(sub[pred], sub[resp])
                rows.append({
                    'scope': scope,
                    'stratum': stratum,
                    'predictor': pred,
                    'predictor_type': pred_type,
                    'response': resp,
                    'n': n,
                    'pearson_r': r_p, 'pearson_p': p_p,
                    'spearman_r': r_s, 'spearman_p': p_s,
                    'abs_pearson_r': abs(r_p) if not np.isnan(r_p) else np.nan,
                    'significant_strong': not np.isnan(r_p) and abs(r_p) > 0.5,
                    'significant_mid': not np.isnan(r_p) and abs(r_p) > 0.3,
                    'significant_weak': not np.isnan(r_p) and abs(r_p) > 0.1,
                })
    df = pd.DataFrame(rows)

    # per (scope, stratum, response) で predictor 内ランキング
    df['rank_in_scope_response'] = df.groupby(['scope', 'stratum', 'response'])[
        'abs_pearson_r'].rank(ascending=False, method='min')

    out = V1104A_MAIN / 'observation_3_density_comparison.parquet'
    df.to_parquet(out, index=False)
    print(f'\nwrote {out.name} ({len(df):,} rows, elapsed {time.time()-t0:.1f}s)')

    # --- サマリ ---
    print('\n--- 同一 (scope, stratum, response) 内の top predictor (|r| 最大) ---')
    print('  ESDE 系:')
    for stratum in ['ESDE_all', 'ESDE_event', 'ESDE_step10', 'ESDE_window']:
        for resp in RESPONSES:
            sub = df[(df['stratum'] == stratum) & (df['response'] == resp)]
            top = sub.sort_values('abs_pearson_r', ascending=False).head(1)
            if len(top) > 0:
                t = top.iloc[0]
                print(f'    {stratum:14s}/{resp:18s}: '
                      f'{t["predictor"]:25s} r={t["pearson_r"]:.4f} '
                      f'({t["predictor_type"]:10s})')

    print('  CID 系:')
    for stratum in ['CID_all', 'CID_n=2', 'CID_n=3', 'CID_n=4', 'CID_n=5', 'CID_n=6+']:
        for resp in RESPONSES:
            sub = df[(df['stratum'] == stratum) & (df['response'] == resp)]
            top = sub.sort_values('abs_pearson_r', ascending=False).head(1)
            if len(top) > 0 and not np.isnan(top.iloc[0]['pearson_r']):
                t = top.iloc[0]
                print(f'    {stratum:14s}/{resp:18s}: '
                      f'{t["predictor"]:25s} r={t["pearson_r"]:.4f} '
                      f'({t["predictor_type"]:10s})')
            else:
                print(f'    {stratum:14s}/{resp:18s}: (全 predictor NaN)')

    print('\n--- ESDE_all / CID_all で trajectory vs density 別の最大 |r| ---')
    for stratum in ['ESDE_all', 'CID_all']:
        for resp in RESPONSES:
            for pt in ['trajectory', 'density']:
                sub = df[(df['stratum'] == stratum) & (df['response'] == resp) &
                          (df['predictor_type'] == pt)]
                top = sub.sort_values('abs_pearson_r', ascending=False).head(1)
                if len(top) > 0 and not np.isnan(top.iloc[0]['pearson_r']):
                    t = top.iloc[0]
                    print(f'  {stratum}/{resp}/{pt}: {t["predictor"]} r={t["pearson_r"]:.4f}')


if __name__ == '__main__':
    main()
