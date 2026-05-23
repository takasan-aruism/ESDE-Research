#!/usr/bin/env python3
"""v1104a Step C' — 追加調整 2: 観察 3 を CID scope の cid_n_core 層化

入力 (read-only):
  - unified/v1104/outputs/main/observation_3_trajectory_response.parquet
    (receiver_bin に CID_n=2..6+ / ESDE_window/step10/event / alpha_*/beta_* 埋め込み済)

出力:
  - unified/v1104a/outputs/main/observation_3_scope_n_stratified.parquet
    (per (scope, cid_n_core_bin, pair) + ESDE-only 参考値)
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1104_MAIN = REPO_ROOT / 'unified/v1104/outputs/main'
V1104A_MAIN = REPO_ROOT / 'unified/v1104a/outputs/main'


PAIRS = [
    ('stability_vs_maxprob', 'traj_stability_mean', 'response_max_prob'),
    ('diffusion_vs_maxprob', 'diffusion_ratio_mean', 'response_max_prob'),
    ('stability_vs_entropy', 'traj_stability_mean', 'response_entropy'),
    ('diffusion_vs_entropy', 'diffusion_ratio_mean', 'response_entropy'),
]


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
    print('=== v1104a Step C 追加調整 2: 観察 3 CID scope cid_n_core 層化 ===')
    t0 = time.time()

    o3 = pd.read_parquet(V1104_MAIN / 'observation_3_trajectory_response.parquet')
    print(f'observation_3 loaded: {len(o3):,} rows')

    rows = []

    # CID scope: cid_n_core_bin 別 (4 bin: n=2/3/4/5+)
    print('\n[1] CID scope cid_n_core 層化 (4 bin)')
    cid_sub = o3[o3['receiver_bin'].str.startswith('CID_n=')].copy()
    print(f'  CID rows: {len(cid_sub):,}')
    print(f'  receiver_bin values: {sorted(cid_sub["receiver_bin"].unique())}')
    # Step A' §1.1 通り: CID_n=5+ は将来拡張用 (実体は n=5 のみ)
    # observation_3_trajectory_response の receiver_bin は CID_n=2..6+ なので、そのまま使用

    for cid_bin in sorted(cid_sub['receiver_bin'].unique()):
        bin_sub = cid_sub[cid_sub['receiver_bin'] == cid_bin]
        for pair_name, xc, yc in PAIRS:
            r_p, p_p, r_s, p_s, n = safe_corr(bin_sub[xc], bin_sub[yc])
            rows.append({
                'scope': 'CID',
                'stratum': cid_bin,
                'pair': pair_name,
                'n': n,
                'pearson_r': r_p, 'pearson_p': p_p,
                'spearman_r': r_s, 'spearman_p': p_s,
                'abs_pearson_r': abs(r_p) if not np.isnan(r_p) else np.nan,
                'significant_strong': not np.isnan(r_p) and abs(r_p) > 0.5,
                'significant_mid': not np.isnan(r_p) and abs(r_p) > 0.3,
                'significant_weak': not np.isnan(r_p) and abs(r_p) > 0.1,
            })

    # CID 集約 (全 CID 行を 1 grp として再計算、参考値)
    for pair_name, xc, yc in PAIRS:
        r_p, p_p, r_s, p_s, n = safe_corr(cid_sub[xc], cid_sub[yc])
        rows.append({
            'scope': 'CID',
            'stratum': 'CID_all',
            'pair': pair_name,
            'n': n,
            'pearson_r': r_p, 'pearson_p': p_p,
            'spearman_r': r_s, 'spearman_p': p_s,
            'abs_pearson_r': abs(r_p) if not np.isnan(r_p) else np.nan,
            'significant_strong': not np.isnan(r_p) and abs(r_p) > 0.5,
            'significant_mid': not np.isnan(r_p) and abs(r_p) > 0.3,
            'significant_weak': not np.isnan(r_p) and abs(r_p) > 0.1,
        })

    # ESDE-only scope 参考値 (層化対象外、全体 |r| のみ)
    print('\n[2] ESDE-only scope 参考値 (層化対象外、3 解像度 別 + ESDE_all)')
    esde_sub = o3[o3['receiver_bin'].str.startswith('ESDE_')].copy()
    print(f'  ESDE rows: {len(esde_sub):,}')

    for esde_bin in sorted(esde_sub['receiver_bin'].unique()):
        bin_sub = esde_sub[esde_sub['receiver_bin'] == esde_bin]
        for pair_name, xc, yc in PAIRS:
            r_p, p_p, r_s, p_s, n = safe_corr(bin_sub[xc], bin_sub[yc])
            rows.append({
                'scope': 'ESDE',
                'stratum': esde_bin,
                'pair': pair_name,
                'n': n,
                'pearson_r': r_p, 'pearson_p': p_p,
                'spearman_r': r_s, 'spearman_p': p_s,
                'abs_pearson_r': abs(r_p) if not np.isnan(r_p) else np.nan,
                'significant_strong': not np.isnan(r_p) and abs(r_p) > 0.5,
                'significant_mid': not np.isnan(r_p) and abs(r_p) > 0.3,
                'significant_weak': not np.isnan(r_p) and abs(r_p) > 0.1,
            })

    # ESDE 全体集約
    for pair_name, xc, yc in PAIRS:
        r_p, p_p, r_s, p_s, n = safe_corr(esde_sub[xc], esde_sub[yc])
        rows.append({
            'scope': 'ESDE',
            'stratum': 'ESDE_all',
            'pair': pair_name,
            'n': n,
            'pearson_r': r_p, 'pearson_p': p_p,
            'spearman_r': r_s, 'spearman_p': p_s,
            'abs_pearson_r': abs(r_p) if not np.isnan(r_p) else np.nan,
            'significant_strong': not np.isnan(r_p) and abs(r_p) > 0.5,
            'significant_mid': not np.isnan(r_p) and abs(r_p) > 0.3,
            'significant_weak': not np.isnan(r_p) and abs(r_p) > 0.1,
        })

    df = pd.DataFrame(rows)
    out = V1104A_MAIN / 'observation_3_scope_n_stratified.parquet'
    df.to_parquet(out, index=False)
    print(f'\nwrote {out.name} ({len(df)} rows, elapsed {time.time()-t0:.1f}s)')

    # --- サマリ ---
    print('\n--- CID scope cid_n_core 層化 (stability_vs_maxprob, Pearson r) ---')
    s1 = df[(df['scope'] == 'CID') & (df['pair'] == 'stability_vs_maxprob')]
    print(s1[['stratum', 'n', 'pearson_r', 'spearman_r',
              'significant_mid', 'significant_strong']].to_string(index=False))

    print('\n--- CID scope cid_n_core 層化 (diffusion_vs_maxprob, Pearson r) ---')
    s2 = df[(df['scope'] == 'CID') & (df['pair'] == 'diffusion_vs_maxprob')]
    print(s2[['stratum', 'n', 'pearson_r', 'spearman_r',
              'significant_mid', 'significant_strong']].to_string(index=False))

    print('\n--- ESDE 3 解像度 参考値 (stability_vs_maxprob, diffusion_vs_maxprob) ---')
    s3 = df[(df['scope'] == 'ESDE') & (df['pair'].isin(['stability_vs_maxprob',
                                                          'diffusion_vs_maxprob']))]
    print(s3.pivot_table(index='stratum', columns='pair', values='pearson_r').round(4)
            .to_string())

    print('\n--- CID_all vs ESDE_all 比較 (全 pair) ---')
    cmp = df[df['stratum'].isin(['CID_all', 'ESDE_all'])]
    print(cmp.pivot_table(index='pair', columns='stratum', values='pearson_r').round(4)
            .to_string())


if __name__ == '__main__':
    main()
