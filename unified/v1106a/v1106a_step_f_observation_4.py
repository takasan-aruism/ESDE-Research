#!/usr/bin/env python3
"""v1106a Step F — 観察 4: s7 主軸 vs s1-s6 補助系列の mapper_output 接続での違い

設計書 §2.5 通り、7 系列の word 候補 layer_jaccard 7×7 対称行列を計算、案 X/Z-1
別に集計。+ series_id × formula 別比較。

入力 (read-only):
  - unified/v1106a/outputs/main/observation_1_word_distributions.parquet
  - unified/v1106a/outputs/main/observation_1_labels.parquet

出力:
  - unified/v1106a/outputs/main/observation_4_layer_jaccard.parquet (案 X/Z-1 × 7×7)
  - unified/v1106a/outputs/main/observation_4_series_comparison.parquet
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'

SERIES_IDS = [
    's1_raw_density_raw', 's2_raw_density_norm',
    's3_qweighted_density_raw', 's4_qweighted_density_norm',
    's5_const_adjusted_density_raw', 's6_const_adjusted_density_norm',
    's7_48d_raw_k5',
]


def main():
    V1106A_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106a Step F 観察 4: 7 系列 word layer_jaccard (案 X/Z-1 別) ===')
    t0 = time.time()

    # (1) Step C distributions 読み込み
    print('[1] observation_1_word_distributions 読み込み')
    dist = pd.read_parquet(V1106A_MAIN / 'observation_1_word_distributions.parquet')
    print(f'  distributions: {len(dist):,} rows')

    # (2) per (seed, event, series, formula) で top5 word 抽出
    print('\n[2] per (event, series, formula) top5 word 抽出')
    dist_sorted = dist.sort_values(
        ['seed', 'event_id', 'series_id', 'formula', 'probability'],
        ascending=[True, True, True, True, False])
    dist_sorted['rank_in_event'] = dist_sorted.groupby(
        ['seed', 'event_id', 'series_id', 'formula']).cumcount() + 1
    top5 = dist_sorted[dist_sorted['rank_in_event'] <= 5]
    top5_sets = top5.groupby(['seed', 'event_id', 'series_id', 'formula']
                              )['candidate_word'].apply(set)
    print(f'  top5 sets: {len(top5_sets):,}')

    # (3) per formula で 7×7 Jaccard
    print('\n[3] 7×7 layer_jaccard 計算 (formula 別)')
    jacc_rows = []
    for formula in ['X', 'Z1']:
        formula_sets = top5_sets.xs(formula, level='formula')
        pivot = formula_sets.unstack(level='series_id')
        pivot = pivot.apply(lambda col: col.apply(lambda x: x if isinstance(x, set) else set()))

        for s1 in SERIES_IDS:
            for s2 in SERIES_IDS:
                if s1 not in pivot.columns or s2 not in pivot.columns:
                    jacc_rows.append({'formula': formula, 's1': s1, 's2': s2,
                                       'jaccard_mean': np.nan, 'n_events': 0})
                    continue
                jaccs = []
                for _, row in pivot.iterrows():
                    a = row[s1]; b = row[s2]
                    if isinstance(a, set) and isinstance(b, set) and len(a) > 0 and len(b) > 0:
                        j = len(a & b) / len(a | b)
                        jaccs.append(j)
                jacc_rows.append({
                    'formula': formula, 's1': s1, 's2': s2,
                    'jaccard_mean': float(np.mean(jaccs)) if jaccs else np.nan,
                    'n_events': len(jaccs),
                })
    jacc_df = pd.DataFrame(jacc_rows).sort_values(
        ['formula', 's1', 's2']).reset_index(drop=True)
    out1 = V1106A_MAIN / 'observation_4_layer_jaccard.parquet'
    jacc_df.to_parquet(out1, index=False)
    print(f'wrote {out1.name} ({len(jacc_df)} rows = 2 × 7×7)')

    # (4) series_id × formula 別集計
    print('\n[4] series × formula 別集計')
    labels = pd.read_parquet(V1106A_MAIN / 'observation_1_labels.parquet')
    series_comp = labels.groupby(['formula', 'series_id']).agg(
        n_events=('event_id', 'count'),
        n_words_mean=('n_words_after', 'mean'),
        n_words_median=('n_words_after', 'median'),
        n_words_max=('n_words_after', 'max'),
        max_prob_mean=('word_max_prob', 'mean'),
        max_prob_median=('word_max_prob', 'median'),
        entropy_mean=('word_entropy', 'mean'),
        entropy_median=('word_entropy', 'median'),
    ).reset_index().sort_values(['formula', 'series_id'])
    out2 = V1106A_MAIN / 'observation_4_series_comparison.parquet'
    series_comp.to_parquet(out2, index=False)
    print(f'wrote {out2.name}')

    print(f'\n=== Step F 完了、elapsed {time.time()-t0:.1f}s ===')

    print('\n--- 7×7 layer_jaccard (案 X) ---')
    pv_x = jacc_df[jacc_df['formula'] == 'X'].pivot(
        index='s1', columns='s2', values='jaccard_mean').round(3)
    print(pv_x.reindex(SERIES_IDS)[SERIES_IDS].to_string())

    print('\n--- 7×7 layer_jaccard (案 Z-1) ---')
    pv_z = jacc_df[jacc_df['formula'] == 'Z1'].pivot(
        index='s1', columns='s2', values='jaccard_mean').round(3)
    print(pv_z.reindex(SERIES_IDS)[SERIES_IDS].to_string())

    print('\n--- s7 vs s1-s6 別 jaccard (案 X / Z1) ---')
    for formula in ['X', 'Z1']:
        s7_row = jacc_df[(jacc_df['formula'] == formula) &
                          (jacc_df['s1'] == 's7_48d_raw_k5') &
                          (jacc_df['s2'] != 's7_48d_raw_k5')]
        print(f'\n  formula {formula}:')
        for _, row in s7_row.iterrows():
            print(f'    s7 vs {row["s2"]}: {row["jaccard_mean"]:.4f}')

    print('\n--- series 比較 (s7 vs s1-s6 #L40 持続確認) ---')
    print(series_comp.round(3).to_string(index=False))


if __name__ == '__main__':
    main()
