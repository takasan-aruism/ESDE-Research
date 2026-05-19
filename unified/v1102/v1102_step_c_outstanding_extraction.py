#!/usr/bin/env python3
"""v1102 Step C — 際立ち掬い取り A primary + B secondary

設計書 §2.4 + Code A 認識確認 §4.2/4.3:
- A primary: primary_table の構造的指標分布から Top N% + IQR 外れ値で際立った
  セルを掬う。閾値は分布から構造的に (神の手回避 #9)、z-score 単体は不可
- B secondary: A 際立ち cell の v1101a 既存 emit (attention_candidate /
  causality_path_zscore / predicted_lock_mode / Step G stratified) との
  read-back。新規 emit なし、軽い踏み込み

出力: outstanding_cells.parquet
書込み: unified/v1102/outputs/{smoke,main}/ 配下のみ
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1101A_MAIN = REPO_ROOT / 'unified/v1101a/outputs/main'
V1102_MAIN = REPO_ROOT / 'unified/v1102/outputs/main'
V1102_SMOKE = REPO_ROOT / 'unified/v1102/outputs/smoke'

# A primary 構造的指標 (効果サイズ + baseline 乖離 + influence)
OUTSTANDING_METRICS_HIGH = [
    # 高値が際立ち
    'influence_count_mean',
    'influence_count_max',
    'variability_lift_mean',
    'variability_actual_mean',
    'attention_count_mean_per_window',
    'conscious_frac',
]
OUTSTANDING_METRICS_MAGNITUDE = [
    # 絶対値が大きいほど際立ち (effect_delta は正負両方)
    'effect_delta_Q_immediate_mean', 'effect_delta_Q_short_mean', 'effect_delta_Q_medium_mean',
    'effect_delta_C_immediate_mean', 'effect_delta_C_short_mean', 'effect_delta_C_medium_mean',
    'effect_delta_R_familiarity_immediate_mean', 'effect_delta_R_familiarity_short_mean',
    'effect_delta_R_familiarity_medium_mean',
]
TOP_PCT = 0.10  # Top 10% を際立ちと判定 (構造的、ヒストグラム分布から)


def threshold_top_pct(series: pd.Series, pct: float = TOP_PCT, use_abs: bool = False) -> tuple[float, np.ndarray]:
    """Top pct を際立ち判定する閾値 + 該当 mask"""
    s = series.dropna()
    if use_abs:
        s = s.abs()
        thresh = float(s.quantile(1 - pct))
        mask = series.fillna(0).abs() >= thresh
    else:
        thresh = float(s.quantile(1 - pct))
        mask = series >= thresh
    return thresh, mask.to_numpy()


def threshold_iqr_outlier(series: pd.Series, use_abs: bool = False) -> tuple[float, np.ndarray]:
    """IQR 外れ値 (Q3 + 1.5*IQR) で際立ち判定"""
    s = series.dropna()
    target = s.abs() if use_abs else s
    q1, q3 = float(target.quantile(0.25)), float(target.quantile(0.75))
    thresh = q3 + 1.5 * (q3 - q1)
    if use_abs:
        mask = series.fillna(0).abs() >= thresh
    else:
        mask = series >= thresh
    return thresh, mask.to_numpy()


def extract_outstanding(pt: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """A primary 掬い取り"""
    df = pt.copy()
    df['outstanding_score'] = 0  # 際立った指標数
    df['outstanding_metrics'] = ''
    df['outstanding_metric_list'] = [[] for _ in range(len(df))]

    threshold_info = []
    # 高値型指標
    for m in OUTSTANDING_METRICS_HIGH:
        if m not in df.columns:
            continue
        thresh_top, mask_top = threshold_top_pct(df[m], TOP_PCT, use_abs=False)
        thresh_iqr, mask_iqr = threshold_iqr_outlier(df[m], use_abs=False)
        # どちらか満たせば際立ち (or 結合)
        combined = mask_top | mask_iqr
        df.loc[combined, 'outstanding_score'] += 1
        for idx in df.index[combined]:
            df.at[idx, 'outstanding_metric_list'].append(m)
        threshold_info.append({
            'metric': m, 'kind': 'high',
            'thresh_top_pct': thresh_top, 'thresh_iqr': thresh_iqr,
            'n_top_pct': int(mask_top.sum()), 'n_iqr': int(mask_iqr.sum()),
            'n_combined': int(combined.sum()),
        })

    # 絶対値型指標 (effect_delta)
    for m in OUTSTANDING_METRICS_MAGNITUDE:
        if m not in df.columns:
            continue
        thresh_top, mask_top = threshold_top_pct(df[m], TOP_PCT, use_abs=True)
        thresh_iqr, mask_iqr = threshold_iqr_outlier(df[m], use_abs=True)
        combined = mask_top | mask_iqr
        df.loc[combined, 'outstanding_score'] += 1
        for idx in df.index[combined]:
            df.at[idx, 'outstanding_metric_list'].append(m)
        threshold_info.append({
            'metric': m, 'kind': 'magnitude',
            'thresh_top_pct': thresh_top, 'thresh_iqr': thresh_iqr,
            'n_top_pct': int(mask_top.sum()), 'n_iqr': int(mask_iqr.sum()),
            'n_combined': int(combined.sum()),
        })

    df['outstanding_metrics'] = df['outstanding_metric_list'].apply(
        lambda x: ' | '.join(sorted(set(x))) if len(x) > 0 else '')
    return df, pd.DataFrame(threshold_info)


def b_secondary_readback(df_outstanding: pd.DataFrame) -> pd.DataFrame:
    """B secondary: v1101a 既存 emit の read-back"""
    # Step G stratified との重なり
    strat = pd.read_parquet(V1101A_MAIN / 'stratified_observation_integration.parquet')

    df = df_outstanding.copy()
    df['stepg_overlap_scope'] = None  # alpha or beta
    df['stepg_overlap_n_records'] = None
    df['stepg_overlap_int_beta_z'] = None
    df['stepg_overlap_familiarity_z'] = None

    for idx, row in df.iterrows():
        rbin = row['receiver_bin']
        # Step G stratified から対応 cell を取得
        if rbin.startswith('alpha_n'):
            n_bin = rbin.split(' / ')[0].replace('alpha_', '')  # n=2 等
            gini_bin = rbin.split(' / ')[1].replace('gini=', '')  # high 等
            scope = 'alpha'
            gini_bin_map = {'low': 'low (近均等)', 'mid': 'mid', 'high': 'high (偏り)'}
            sg = strat[(strat['scope'] == scope)
                        & (strat['n_members_bin'] == n_bin)
                        & (strat['qc_gini_bin'] == gini_bin_map.get(gini_bin, gini_bin))]
        elif rbin.startswith('beta_n'):
            n_bin = rbin.split(' / ')[0].replace('beta_', '')
            gini_bin = rbin.split(' / ')[1].replace('gini=', '')
            scope = 'beta'
            gini_bin_map = {'low': 'low (近均等)', 'mid': 'mid', 'high': 'high (偏り)'}
            sg = strat[(strat['scope'] == scope)
                        & (strat['n_members_bin'] == n_bin)
                        & (strat['qc_gini_bin'] == gini_bin_map.get(gini_bin, gini_bin))]
        else:
            continue
        if len(sg) > 0:
            s = sg.iloc[0]
            df.at[idx, 'stepg_overlap_scope'] = scope
            df.at[idx, 'stepg_overlap_n_records'] = int(s['n_records'])
            df.at[idx, 'stepg_overlap_int_beta_z'] = float(s['integration_beta_frac_zscore'])
            df.at[idx, 'stepg_overlap_familiarity_z'] = float(s['familiarity_frac_zscore'])

    # outstanding_metric_list は parquet に出ない (list 型不可) ので drop
    df = df.drop(columns=['outstanding_metric_list'])
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='main', choices=['main', 'smoke'])
    args = ap.parse_args()

    src_dir = V1102_MAIN if args.src == 'main' else V1102_SMOKE

    print(f'=== v1102 Step C — 際立ち掬い取り A primary + B secondary ===')
    print(f'src: {src_dir}')

    pt = pd.read_parquet(src_dir / 'primary_table.parquet')
    print(f'primary_table: {len(pt)} cells, {len(pt.columns)} cols')

    df_a, df_thresh = extract_outstanding(pt)
    print(f'\nA primary thresholds (神の手回避 #9、Top 10% + IQR 外れ値):')
    print(df_thresh[['metric','kind','thresh_top_pct','thresh_iqr','n_top_pct','n_iqr','n_combined']].to_string(index=False))
    print()
    print(f'A primary: outstanding_score distribution:')
    print(df_a['outstanding_score'].value_counts().sort_index().to_string())

    df_full = b_secondary_readback(df_a)
    print(f'\nB secondary read-back: Step G overlap 取得 {df_full["stepg_overlap_scope"].notna().sum()} cells')

    df_thresh.to_parquet(src_dir / 'outstanding_thresholds.parquet', index=False)
    df_full.to_parquet(src_dir / 'outstanding_cells.parquet', index=False)
    print(f'\nwrote {src_dir}/outstanding_cells.parquet ({len(df_full)} cells)')
    print(f'wrote {src_dir}/outstanding_thresholds.parquet ({len(df_thresh)} threshold rows)')


if __name__ == '__main__':
    main()
