#!/usr/bin/env python3
"""v1106 Step E — 観察 3: synset 候補の広がり/絞り

設計書 v1106 §2.4 通り、Synapse 接続後の synset 候補数が広がるか絞られるかを
構造事実として記録。候補爆発リスク観察 (v1106 で制御しない、観察のみ)。

指標:
- n_synsets_after (Step C 既存)
- synset_expansion_ratio = n_synsets_after / n_candidates_after (atom 1 個あたり何 synset)
- total_synset_coverage = n_synsets_after / 11,581 (Synapse 全体カバレッジ)

per (seed, event_id, series_id) で計算、7 系列別集計。

入力 (read-only):
  - unified/v1106/outputs/main/observation_1_labels.parquet (Step C 出力)
  - unified/v1105a/outputs/main/trial_step4_labels.parquet (n_candidates_after)

出力:
  - unified/v1106/outputs/main/observation_3_expansion.parquet
    (per (seed, event_id, series_id) で expansion + coverage 指標)
  - unified/v1106/outputs/main/observation_3_summary.parquet
    (per series_id で分布統計)
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1105A_MAIN = REPO / 'unified/v1105a/outputs/main'
V1106_MAIN = REPO / 'unified/v1106/outputs/main'

SYNAPSE_TOTAL = 11581  # overlay 後の synset 総数


def main():
    V1106_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106 Step E 観察 3: synset 候補の広がり/絞り ===')
    t0 = time.time()

    # (1) Step C labels (n_synsets_after) 読み込み
    print('[1] Step C labels 読み込み')
    o1 = pd.read_parquet(V1106_MAIN / 'observation_1_labels.parquet')
    print(f'  observation_1_labels: {len(o1):,} rows')

    # (2) v1105a labels (n_candidates_after) 読み込み
    print('\n[2] v1105a labels 読み込み (n_candidates_after)')
    v1a_labels = pd.read_parquet(V1105A_MAIN / 'trial_step4_labels.parquet',
                                   columns=['seed', 'event_id', 'series_id',
                                            'n_candidates_after'])
    print(f'  v1105a labels: {len(v1a_labels):,} rows')

    # (3) join + 指標計算
    print('\n[3] expansion / coverage 計算')
    merged = o1.merge(v1a_labels, on=['seed', 'event_id', 'series_id'], how='left')
    merged['synset_expansion_ratio'] = (
        merged['n_synsets_after'] / merged['n_candidates_after'].replace(0, np.nan))
    merged['total_synset_coverage'] = merged['n_synsets_after'] / SYNAPSE_TOTAL

    # valid のみで集計 (v1106 では全 23,100 が valid)
    valid = merged[merged['structural_label'] == 'synset_distribution_valid'].copy()
    print(f'  valid event-series: {len(valid):,}')

    valid_sorted = valid.sort_values(['seed', 'event_id', 'series_id']).reset_index(drop=True)
    out = V1106_MAIN / 'observation_3_expansion.parquet'
    valid_sorted.to_parquet(out, index=False)
    print(f'wrote {out.name} ({len(valid_sorted):,} rows)')

    # (4) 系列別分布統計
    print('\n[4] 系列別分布統計')
    summary_rows = []
    for sid in sorted(valid['series_id'].unique()):
        sub = valid[valid['series_id'] == sid]
        ns = sub['n_synsets_after']
        er = sub['synset_expansion_ratio'].dropna()
        cov = sub['total_synset_coverage']
        summary_rows.append({
            'series_id': sid,
            'n_events': len(sub),
            'n_synsets_mean': float(ns.mean()),
            'n_synsets_median': float(ns.median()),
            'n_synsets_max': int(ns.max()),
            'n_synsets_min': int(ns.min()),
            'n_synsets_p95': float(ns.quantile(0.95)),
            'n_synsets_p99': float(ns.quantile(0.99)),
            'expansion_ratio_mean': float(er.mean()) if len(er) else np.nan,
            'expansion_ratio_median': float(er.median()) if len(er) else np.nan,
            'expansion_ratio_max': float(er.max()) if len(er) else np.nan,
            'coverage_mean': float(cov.mean()),
            'coverage_median': float(cov.median()),
            'coverage_max': float(cov.max()),
            'coverage_p95': float(cov.quantile(0.95)),
        })
    summary = pd.DataFrame(summary_rows).sort_values('series_id').reset_index(drop=True)
    out2 = V1106_MAIN / 'observation_3_summary.parquet'
    summary.to_parquet(out2, index=False)
    print(f'wrote {out2.name}')

    print(f'\n=== Step E 完了、elapsed {time.time()-t0:.1f}s ===')

    print('\n--- 系列別集計 ---')
    cols_print = ['series_id', 'n_synsets_mean', 'n_synsets_median', 'n_synsets_max',
                   'expansion_ratio_mean', 'expansion_ratio_max',
                   'coverage_mean', 'coverage_max']
    print(summary[cols_print].round(2).to_string(index=False))

    print('\n--- 候補爆発リスク観察 (s7) ---')
    s7 = valid[valid['series_id'] == 's7_48d_raw_k5']
    print(f'  s7 n_synsets: max={s7["n_synsets_after"].max()}, '
          f'p99={s7["n_synsets_after"].quantile(0.99):.0f}, '
          f'p95={s7["n_synsets_after"].quantile(0.95):.0f}')
    print(f'  s7 expansion_ratio: max={s7["synset_expansion_ratio"].max():.2f}, '
          f'mean={s7["synset_expansion_ratio"].mean():.2f}')
    print(f'  s7 coverage (Synapse 11,581 中の割合): max={100*s7["total_synset_coverage"].max():.2f}%, '
          f'mean={100*s7["total_synset_coverage"].mean():.2f}%')

    # 候補爆発しているか (留保候補)
    print('\n--- 候補数別分布 (s7、event 数比率) ---')
    for thresh in [100, 500, 1000]:
        n = (s7['n_synsets_after'] >= thresh).sum()
        pct = 100 * n / len(s7) if len(s7) else 0
        print(f'  >= {thresh} synset: {n:,} events ({pct:.2f}%)')


if __name__ == '__main__':
    main()
