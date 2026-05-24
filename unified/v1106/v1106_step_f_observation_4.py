#!/usr/bin/env python3
"""v1106 Step F — 観察 4: s7 主軸 vs s1-s6 補助系列の Synapse 接続での違い

設計書 v1106 §2.5 通り、7 系列の synset 候補 layer_jaccard (top5 synset の
重なり) を per-event で計算、系列間平均 7×7 対称行列を生成。

入力 (read-only):
  - unified/v1106/outputs/main/observation_1_synset_distributions.parquet (Step C)
  - unified/v1106/outputs/main/observation_1_labels.parquet (Step C)

出力:
  - unified/v1106/outputs/main/observation_4_layer_jaccard.parquet
    (7×7 = 49 rows、対称行列 mean jaccard)
  - unified/v1106/outputs/main/observation_4_series_comparison.parquet
    (per series_id で max_prob / entropy / n_synsets の集計、s7 vs s1-s6 比較)
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1106_MAIN = REPO / 'unified/v1106/outputs/main'

SERIES_IDS = [
    's1_raw_density_raw',
    's2_raw_density_norm',
    's3_qweighted_density_raw',
    's4_qweighted_density_norm',
    's5_const_adjusted_density_raw',
    's6_const_adjusted_density_norm',
    's7_48d_raw_k5',
]


def main():
    V1106_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106 Step F 観察 4: 7 系列 layer_jaccard ===')
    t0 = time.time()

    # (1) Step C 出力読み込み
    print('[1] Step C synset distributions 読み込み')
    dist = pd.read_parquet(V1106_MAIN / 'observation_1_synset_distributions.parquet')
    print(f'  distributions: {len(dist):,} rows')

    # (2) per (seed, event_id, series_id) で top5 synset 抽出
    print('\n[2] per (seed, event, series) top5 synset 抽出')
    dist_sorted = dist.sort_values(['seed', 'event_id', 'series_id', 'probability'],
                                     ascending=[True, True, True, False])
    dist_sorted['rank_in_event'] = dist_sorted.groupby(
        ['seed', 'event_id', 'series_id']).cumcount() + 1
    top5 = dist_sorted[dist_sorted['rank_in_event'] <= 5]
    # per (seed, event, series) → top5 synset set
    top5_sets = top5.groupby(['seed', 'event_id', 'series_id'])['candidate_synset'].apply(set)
    print(f'  top5 sets: {len(top5_sets):,}')

    # (3) per event で 7 系列 × 7 系列 Jaccard 計算
    print('\n[3] 7×7 layer_jaccard 計算')
    pivot = top5_sets.unstack(level='series_id')  # (seed, event_id) × series_id
    # NaN を空 set に置換
    pivot = pivot.apply(lambda col: col.apply(lambda x: x if isinstance(x, set) else set()))
    print(f'  events: {len(pivot):,}')

    jaccard_rows = []
    for s1 in SERIES_IDS:
        for s2 in SERIES_IDS:
            if s1 not in pivot.columns or s2 not in pivot.columns:
                jaccard_rows.append({'s1': s1, 's2': s2, 'jaccard_mean': np.nan, 'n_events': 0})
                continue
            jaccs = []
            for _, row in pivot.iterrows():
                a = row[s1]; b = row[s2]
                if len(a) > 0 and len(b) > 0:
                    j = len(a & b) / len(a | b)
                    jaccs.append(j)
            jaccard_rows.append({
                's1': s1, 's2': s2,
                'jaccard_mean': float(np.mean(jaccs)) if jaccs else np.nan,
                'n_events': len(jaccs),
            })
    jacc_df = pd.DataFrame(jaccard_rows).sort_values(['s1', 's2']).reset_index(drop=True)
    out1 = V1106_MAIN / 'observation_4_layer_jaccard.parquet'
    jacc_df.to_parquet(out1, index=False)
    print(f'wrote {out1.name} ({len(jacc_df)} rows = 7×7)')

    # (4) per series_id 集計 (max_prob / entropy / n_synsets)
    print('\n[4] series_id 別集計 (s7 vs s1-s6 比較用)')
    labels = pd.read_parquet(V1106_MAIN / 'observation_1_labels.parquet')
    series_comp = labels.groupby('series_id').agg(
        n_events=('event_id', 'count'),
        n_synsets_mean=('n_synsets_after', 'mean'),
        n_synsets_median=('n_synsets_after', 'median'),
        n_synsets_max=('n_synsets_after', 'max'),
        max_prob_mean=('synset_max_prob', 'mean'),
        max_prob_median=('synset_max_prob', 'median'),
        entropy_mean=('synset_entropy', 'mean'),
        entropy_median=('synset_entropy', 'median'),
    ).reset_index().sort_values('series_id')
    out2 = V1106_MAIN / 'observation_4_series_comparison.parquet'
    series_comp.to_parquet(out2, index=False)
    print(f'wrote {out2.name}')

    print(f'\n=== Step F 完了、elapsed {time.time()-t0:.1f}s ===')

    # --- サマリ ---
    print('\n--- 7×7 layer_jaccard 対称行列 (top5 synset の event 平均 jaccard) ---')
    pv = jacc_df.pivot(index='s1', columns='s2', values='jaccard_mean').round(3)
    pv = pv.reindex(SERIES_IDS)[SERIES_IDS]
    print(pv.to_string())

    print('\n--- s7 vs s1-s6 別 jaccard ---')
    s7_row = jacc_df[(jacc_df['s1'] == 's7_48d_raw_k5') & (jacc_df['s2'] != 's7_48d_raw_k5')]
    print(s7_row[['s2', 'jaccard_mean']].round(4).to_string(index=False))

    print('\n--- series_id 別比較 (s7 独立挙動の確認) ---')
    print(series_comp.round(3).to_string(index=False))


if __name__ == '__main__':
    main()
