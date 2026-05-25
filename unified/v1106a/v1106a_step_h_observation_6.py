#!/usr/bin/env python3
"""v1106a Step H — 観察 6: #L42 解消確認

設計書 §2.7 通り、v1106 で確定した #L42 (s1-s6 集計値完全同値 = density 6 種が
Synapse 接続段階で平均化) が mapper_output で解消するかを構造事実として記録。
Step F の preview を正式集計、v1106 (Synapse v3) と直接対比。

指標:
- s1-s6 集計値 (n_words / max_prob / entropy) の標準偏差 (差が出るか)
- s1 vs s5 layer_jaccard (couple_bonus 効果、X / Z-1 別)
- per-event top5 jaccard の分布
- s1-s6 vs s7 の差

入力 (read-only):
  - unified/v1106a/outputs/main/observation_1_labels.parquet (Step C)
  - unified/v1106a/outputs/main/observation_4_layer_jaccard.parquet (Step F)
  - unified/v1106a/outputs/main/observation_4_series_comparison.parquet (Step F)
  - unified/v1106/outputs/main/observation_4_layer_jaccard.parquet (v1106 比較)
  - unified/v1106/outputs/main/observation_4_series_comparison.parquet (v1106 比較)

出力:
  - unified/v1106a/outputs/main/observation_6_L42_resolution.parquet
    (per (formula) で s1-s6 集計値 std + couple_bonus 効果指標 + v1106 比較)
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1106_MAIN = REPO / 'unified/v1106/outputs/main'
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'

S16 = ['s1_raw_density_raw', 's2_raw_density_norm',
       's3_qweighted_density_raw', 's4_qweighted_density_norm',
       's5_const_adjusted_density_raw', 's6_const_adjusted_density_norm']
S7 = 's7_48d_raw_k5'


def main():
    V1106A_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106a Step H 観察 6: #L42 解消確認 ===')
    t0 = time.time()

    # (1) v1106a Step F 出力 + v1106 比較
    print('[1] Step F 出力 + v1106 比較データ読み込み')
    series_v1a = pd.read_parquet(V1106A_MAIN / 'observation_4_series_comparison.parquet')
    jacc_v1a = pd.read_parquet(V1106A_MAIN / 'observation_4_layer_jaccard.parquet')
    series_v1 = pd.read_parquet(V1106_MAIN / 'observation_4_series_comparison.parquet')
    jacc_v1 = pd.read_parquet(V1106_MAIN / 'observation_4_layer_jaccard.parquet')
    print(f'  v1106a series_comparison: {len(series_v1a)}, layer_jaccard: {len(jacc_v1a)}')
    print(f'  v1106 series_comparison: {len(series_v1)}, layer_jaccard: {len(jacc_v1)}')

    # (2) s1-s6 集計値 std 計算 (#L42 差別化指標、formula 別)
    print('\n[2] s1-s6 集計値の差 (std) 計算')
    rows = []
    for formula in ['X', 'Z1']:
        sub = series_v1a[(series_v1a['formula'] == formula) &
                          (series_v1a['series_id'].isin(S16))]
        rows.append({
            'source': f'v1106a_{formula}',
            'n_words_mean_std': float(sub['n_words_mean'].std()),
            'max_prob_mean_std': float(sub['max_prob_mean'].std()),
            'entropy_mean_std': float(sub['entropy_mean'].std()),
            'n_words_mean_range': float(sub['n_words_mean'].max() - sub['n_words_mean'].min()),
            'max_prob_mean_range': float(sub['max_prob_mean'].max() - sub['max_prob_mean'].min()),
            'entropy_mean_range': float(sub['entropy_mean'].max() - sub['entropy_mean'].min()),
        })
    # v1106 (Synapse v3): s1-s6 集計値 std
    sub_v1 = series_v1[series_v1['series_id'].isin(S16)]
    rows.append({
        'source': 'v1106_Synapse_v3',
        'n_words_mean_std': float(sub_v1['n_synsets_mean'].std()),
        'max_prob_mean_std': float(sub_v1['max_prob_mean'].std()),
        'entropy_mean_std': float(sub_v1['entropy_mean'].std()),
        'n_words_mean_range': float(sub_v1['n_synsets_mean'].max() - sub_v1['n_synsets_mean'].min()),
        'max_prob_mean_range': float(sub_v1['max_prob_mean'].max() - sub_v1['max_prob_mean'].min()),
        'entropy_mean_range': float(sub_v1['entropy_mean'].max() - sub_v1['entropy_mean'].min()),
    })
    std_df = pd.DataFrame(rows)
    print('\n--- s1-s6 集計値 std / range (差別化が出れば >0、同値なら 0) ---')
    print(std_df.round(6).to_string(index=False))

    # (3) couple_bonus 効果 (s1 vs s5、X / Z-1 / v1106)
    print('\n[3] couple_bonus 効果 (s1 vs s5 layer_jaccard)')
    couple_rows = []
    for formula in ['X', 'Z1']:
        s1s5 = jacc_v1a[(jacc_v1a['formula'] == formula) &
                         (jacc_v1a['s1'] == 's1_raw_density_raw') &
                         (jacc_v1a['s2'] == 's5_const_adjusted_density_raw')]
        s2s6 = jacc_v1a[(jacc_v1a['formula'] == formula) &
                         (jacc_v1a['s1'] == 's2_raw_density_norm') &
                         (jacc_v1a['s2'] == 's6_const_adjusted_density_norm')]
        couple_rows.append({
            'source': f'v1106a_{formula}',
            's1_vs_s5_jaccard': float(s1s5['jaccard_mean'].iloc[0]),
            's2_vs_s6_jaccard': float(s2s6['jaccard_mean'].iloc[0]),
        })
    # v1106
    s1s5_v1 = jacc_v1[(jacc_v1['s1'] == 's1_raw_density_raw') &
                      (jacc_v1['s2'] == 's5_const_adjusted_density_raw')]
    s2s6_v1 = jacc_v1[(jacc_v1['s1'] == 's2_raw_density_norm') &
                      (jacc_v1['s2'] == 's6_const_adjusted_density_norm')]
    couple_rows.append({
        'source': 'v1106_Synapse_v3',
        's1_vs_s5_jaccard': float(s1s5_v1['jaccard_mean'].iloc[0]),
        's2_vs_s6_jaccard': float(s2s6_v1['jaccard_mean'].iloc[0]),
    })
    couple_df = pd.DataFrame(couple_rows)
    print(couple_df.round(4).to_string(index=False))

    # (4) per-event top5 jaccard 分布 (s1 vs s5、event level)
    print('\n[4] per-event top5 jaccard 分布 (Step C 出力から再計算)')
    dist = pd.read_parquet(V1106A_MAIN / 'observation_1_word_distributions.parquet')
    dist_sorted = dist.sort_values(
        ['seed', 'event_id', 'series_id', 'formula', 'probability'],
        ascending=[True, True, True, True, False])
    dist_sorted['rank_in_event'] = dist_sorted.groupby(
        ['seed', 'event_id', 'series_id', 'formula']).cumcount() + 1
    top5 = dist_sorted[dist_sorted['rank_in_event'] <= 5]
    top5_sets = top5.groupby(['seed', 'event_id', 'series_id', 'formula']
                              )['candidate_word'].apply(set)

    event_jacc_rows = []
    for formula in ['X', 'Z1']:
        s1_sets = top5_sets.xs(('s1_raw_density_raw', formula),
                                  level=('series_id', 'formula'))
        s5_sets = top5_sets.xs(('s5_const_adjusted_density_raw', formula),
                                  level=('series_id', 'formula'))
        common_idx = s1_sets.index.intersection(s5_sets.index)
        jaccs = []
        for idx in common_idx:
            a, b = s1_sets[idx], s5_sets[idx]
            if len(a) > 0 and len(b) > 0:
                jaccs.append(len(a & b) / len(a | b))
        jaccs_arr = np.array(jaccs)
        event_jacc_rows.append({
            'formula': formula, 'pair': 's1_vs_s5',
            'n_events': len(jaccs),
            'jaccard_mean': float(jaccs_arr.mean()),
            'jaccard_median': float(np.median(jaccs_arr)),
            'jaccard_min': float(jaccs_arr.min()),
            'jaccard_max': float(jaccs_arr.max()),
            'jaccard_std': float(jaccs_arr.std()),
            'pct_exactly_1.0': float((jaccs_arr >= 0.9999).mean()),
        })
    event_jacc_df = pd.DataFrame(event_jacc_rows)
    print(event_jacc_df.round(4).to_string(index=False))

    # (5) 出力
    out = V1106A_MAIN / 'observation_6_L42_resolution.parquet'
    std_df.to_parquet(out, index=False)
    print(f'\nwrote {out.name}')

    print(f'\n=== Step H 完了、elapsed {time.time()-t0:.1f}s ===')

    print('\n--- #L42 解消判定の構造事実集約 ---')
    print('  v1106 Synapse v3: s1-s6 集計値完全同値 (std=0)、s1 vs s5 jaccard = 0.99 (couple_bonus 効果ほぼなし)')
    print(f"  v1106a 案 X: s1-s6 集計値 std = "
          f"n_words {std_df[std_df['source']=='v1106a_X']['n_words_mean_std'].iloc[0]:.4f}, "
          f"max_prob {std_df[std_df['source']=='v1106a_X']['max_prob_mean_std'].iloc[0]:.6f}, "
          f"entropy {std_df[std_df['source']=='v1106a_X']['entropy_mean_std'].iloc[0]:.4f}")
    print(f"  v1106a 案 Z-1: s1-s6 集計値 std = "
          f"n_words {std_df[std_df['source']=='v1106a_Z1']['n_words_mean_std'].iloc[0]:.4f}, "
          f"max_prob {std_df[std_df['source']=='v1106a_Z1']['max_prob_mean_std'].iloc[0]:.6f}, "
          f"entropy {std_df[std_df['source']=='v1106a_Z1']['entropy_mean_std'].iloc[0]:.4f}")


if __name__ == '__main__':
    main()
