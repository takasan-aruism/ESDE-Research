#!/usr/bin/env python3
"""v1105 Step D — 観察 2: 段 4-c 地形 (応答 Atom を絞る)

設計書 v4 §2.3 案 B 採用:
  Language 48 次元密度 = 3 density 列 (raw_density / qweighted_density /
  const_adjusted_density) × 2 sim_basis (raw / norm) = 6 値別レイヤー保持
  + 補助 mean_pairwise_sim

設計書 §2.4 11 数値強度マップの段 4-c 部分:
  trajectory r 2 種 (stability_vs_maxprob / diffusion_vs_maxprob)
  density r 6 種 (3 density × 2 sim_basis、response=max_prob で)

入力 (read-only):
  - unified/v1104/outputs/main/observation_3_trajectory_response.parquet
    (972 rows = 27 receiver_bin × 3 metric × 2 qc_regime × 2 sim_basis × 3 k)
  - unified/v1103/outputs/main/density_summary.parquet (486 rows、3 density × 2 sim_basis)
  - unified/v1104a/outputs/main/observation_3_scope_n_stratified.parquet
    (Step C' で計算済の trajectory 相関)

出力:
  - unified/v1105/outputs/main/observation_2_terrain_4c.parquet
    (per (scope, stratum) で trajectory r 2 種 + density r 6 種 × response 2 種)
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
V1105_MAIN = REPO_ROOT / 'unified/v1105/outputs/main'

TRAJECTORY_PREDICTORS = ['traj_stability_mean', 'diffusion_ratio_mean']
RESPONSES = ['response_max_prob', 'response_entropy']
# Density 6 種 (sim_basis × density 列の組み合わせ、案 B)
DENSITY_LAYERS = [
    ('raw_density_raw', 'raw_density', 'raw'),
    ('raw_density_norm', 'raw_density', 'norm'),
    ('qweighted_density_raw', 'qweighted_density', 'raw'),
    ('qweighted_density_norm', 'qweighted_density', 'norm'),
    ('const_adjusted_density_raw', 'const_adjusted_density', 'raw'),
    ('const_adjusted_density_norm', 'const_adjusted_density', 'norm'),
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
    V1105_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1105 Step D 観察 2: 段 4-c 地形 (応答 Atom を絞る) ===')
    t0 = time.time()

    o3 = pd.read_parquet(V1104_MAIN / 'observation_3_trajectory_response.parquet')
    dsm = pd.read_parquet(V1103_MAIN / 'density_summary.parquet')
    print(f'observation_3 (trajectory+response): {len(o3):,} rows')
    print(f'density_summary: {len(dsm):,} rows')

    # density 6 値を pivot (sim_basis × density 列 = 6 列に展開)
    # density_summary は per (receiver_bin × metric × sim_basis × k) = 486 rows
    # pivot 後: per (receiver_bin × metric × k) で sim_basis 別の 3 density を 6 列にする
    dsm_pivot_parts = []
    for _, (col_label, dens_col, sb) in enumerate(DENSITY_LAYERS):
        sub = dsm[dsm['sim_basis'] == sb][['receiver_bin','change_metric_type','k', dens_col]].copy()
        sub = sub.rename(columns={dens_col: col_label})
        dsm_pivot_parts.append(sub)
    # 順次 merge
    dsm_pivot = dsm_pivot_parts[0]
    for part in dsm_pivot_parts[1:]:
        dsm_pivot = dsm_pivot.merge(part, on=['receiver_bin','change_metric_type','k'], how='outer')
    print(f'density 6 値 pivot: {len(dsm_pivot):,} rows (sim_basis を 6 列に展開)')

    # observation_3 と join (receiver_bin × metric × k で、qc_regime と sim_basis は trajectory 側に残す)
    # 注意: o3 の sim_basis は response 側の sim_basis (response_max_prob 等の集約基準)
    # density 6 値はもう pivot 済で sim_basis に依存しないため、receiver_bin × metric × k で 1:N join
    merged = o3.merge(dsm_pivot, on=['receiver_bin','change_metric_type','k'], how='left')
    print(f'merged: {len(merged):,} rows')

    # NaN 確認 (Step A 確認要請 7 解決後の coverage 監視)
    cov_rows = []
    for col_label, _, _ in DENSITY_LAYERS:
        n_nan = int(merged[col_label].isna().sum())
        cov_rows.append({'column': col_label, 'n_nan': n_nan,
                          'n_total': len(merged),
                          'coverage_rate': 1 - n_nan/len(merged)})
    print('coverage (density 6 値):')
    print(pd.DataFrame(cov_rows).to_string(index=False))

    # scope/stratum 定義 (v1104a Step C' と同型 + alpha/beta 集約参考)
    def scope_strata(df):
        # ESDE 集約 + 3 解像度
        yield 'ESDE', 'ESDE_all', df[df['receiver_bin'].str.startswith('ESDE_')]
        for esde in ['ESDE_event', 'ESDE_step10', 'ESDE_window']:
            yield 'ESDE', esde, df[df['receiver_bin'] == esde]
        # CID 集約 + 5 bin
        yield 'CID', 'CID_all', df[df['receiver_bin'].str.startswith('CID_n=')]
        for cn in sorted(df[df['receiver_bin'].str.startswith('CID_n=')]['receiver_bin'].unique()):
            yield 'CID', cn, df[df['receiver_bin'] == cn]
        # alpha / beta 集約 (参考)
        yield 'alpha', 'alpha_all', df[df['receiver_bin'].str.startswith('alpha_')]
        yield 'beta', 'beta_all', df[df['receiver_bin'].str.startswith('beta_')]

    # 計算: per (scope, stratum, predictor, response) で Pearson + Spearman
    rows = []
    all_predictors = [(p, 'trajectory') for p in TRAJECTORY_PREDICTORS] + \
                     [(p, 'density', sb) for p, _, sb in [(lc, dc, sb) for lc, dc, sb in DENSITY_LAYERS]]
    # 整理: trajectory 2 種 + density 6 種 を扱う
    pred_specs = [
        ('traj_stability_mean', 'trajectory', None),
        ('diffusion_ratio_mean', 'trajectory', None),
    ] + [(lc, 'density', sb) for lc, _, sb in DENSITY_LAYERS]

    for scope, stratum, sub in scope_strata(merged):
        for resp in RESPONSES:
            for pred, pred_type, density_sim_basis in pred_specs:
                if pred_type == 'density':
                    # density は sim_basis 列を pivot 済なので、resp 側の sim_basis フィルタは不要
                    sub_eff = sub
                else:
                    # trajectory は qc_regime × metric × receiver_bin で集約済、sim_basis は response 側集計用
                    sub_eff = sub
                r_p, p_p, r_s, p_s, n = safe_corr(sub_eff[pred], sub_eff[resp])
                rows.append({
                    'scope': scope,
                    'stratum': stratum,
                    'predictor': pred,
                    'predictor_type': pred_type,
                    'density_sim_basis': density_sim_basis,
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
    out = V1105_MAIN / 'observation_2_terrain_4c.parquet'
    df.to_parquet(out, index=False)
    print(f'\nwrote {out.name} ({len(df):,} rows, elapsed {time.time()-t0:.1f}s)')

    # --- サマリ: response=max_prob 主、trajectory 2 種 + density 6 種で 8 列の |r| pivot ---
    print('\n--- response=max_prob、scope × stratum × predictor の Pearson |r| ---')
    sub = df[df['response'] == 'response_max_prob'].copy()
    sub['stratum_label'] = sub['stratum']
    pv = sub.pivot_table(index='stratum_label', columns='predictor',
                          values='pearson_r').round(3)
    order = ['ESDE_event','ESDE_step10','ESDE_window','ESDE_all',
              'CID_n=2','CID_n=3','CID_n=4','CID_n=5','CID_n=6+','CID_all',
              'alpha_all','beta_all']
    pv = pv.reindex([x for x in order if x in pv.index])
    col_order = ['traj_stability_mean','diffusion_ratio_mean'] + [lc for lc, _, _ in DENSITY_LAYERS]
    pv = pv[[c for c in col_order if c in pv.columns]]
    print(pv.to_string())

    print('\n--- density 6 種 × scope=ESDE_all/CID_all で |r| > 0.5 strong ---')
    strong = df[(df['response'] == 'response_max_prob') &
                 (df['predictor_type'] == 'density') &
                 (df['stratum'].isin(['ESDE_all', 'CID_all'])) &
                 (df['significant_strong'])]
    print(strong[['stratum','predictor','density_sim_basis',
                   'pearson_r','spearman_r','n']].to_string(index=False))

    print('\n--- raw vs norm 反転チェック (qweighted, const_adjusted で #L17 同様の反転?) ---')
    for stratum in ['ESDE_all', 'CID_all', 'CID_n=2', 'CID_n=3']:
        ss = df[(df['response'] == 'response_max_prob') & (df['stratum'] == stratum) &
                 (df['predictor_type'] == 'density')]
        for dens in ['raw_density', 'qweighted_density', 'const_adjusted_density']:
            raw_r = ss[ss['predictor'] == f'{dens}_raw']['pearson_r']
            norm_r = ss[ss['predictor'] == f'{dens}_norm']['pearson_r']
            if len(raw_r) > 0 and len(norm_r) > 0:
                diff = float(raw_r.iloc[0]) - float(norm_r.iloc[0])
                sign_flip = (float(raw_r.iloc[0]) * float(norm_r.iloc[0])) < 0
                print(f'  [{stratum}/{dens}] raw r={float(raw_r.iloc[0]):+.3f}, '
                      f'norm r={float(norm_r.iloc[0]):+.3f}, Δ={diff:+.3f}, '
                      f'sign_flip={sign_flip}')


if __name__ == '__main__':
    main()
