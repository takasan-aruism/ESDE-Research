#!/usr/bin/env python3
"""v1106a Step E — 観察 3: word 候補の広がり/絞り

設計書 v3 §2.4 通り、mapper_output 接続後の word 候補数を集計、候補爆発リスク観察。

指標:
- n_words_after (Step C 既存)
- word_expansion_ratio = n_words_after / n_candidates_after
- total_word_coverage_unique = n_words_after / 17,790 (unique 17,790 word base)
- total_word_coverage_lexicon = n_words_after / 32,666 (Lexicon 全体 base)

per (seed, event_id, series_id, formula) で計算、7 系列 × 2 案別集計。

入力 (read-only):
  - unified/v1106a/outputs/main/observation_1_labels.parquet (Step C)
  - unified/v1105a/outputs/main/trial_step4_labels.parquet (n_candidates_after)

出力:
  - unified/v1106a/outputs/main/observation_3_expansion.parquet (per event-series-formula)
  - unified/v1106a/outputs/main/observation_3_summary.parquet (per series_id × formula 分布統計)
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1105A_MAIN = REPO / 'unified/v1105a/outputs/main'
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'

UNIQUE_WORDS = 17790  # mapper_output status=OK の unique word
LEXICON_TOTAL = 32666  # a1_batch _summary total_core_words

SERIES_IDS = [
    's1_raw_density_raw', 's2_raw_density_norm',
    's3_qweighted_density_raw', 's4_qweighted_density_norm',
    's5_const_adjusted_density_raw', 's6_const_adjusted_density_norm',
    's7_48d_raw_k5',
]


def main():
    V1106A_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106a Step E 観察 3: word 候補広がり/絞り ===')
    t0 = time.time()

    # (1) Step C labels
    print('[1] Step C labels 読み込み')
    o1 = pd.read_parquet(V1106A_MAIN / 'observation_1_labels.parquet')
    print(f'  observation_1_labels: {len(o1):,} rows')

    # (2) v1105a labels (n_candidates_after)
    print('\n[2] v1105a labels 読み込み (n_candidates_after)')
    v1a = pd.read_parquet(V1105A_MAIN / 'trial_step4_labels.parquet',
                          columns=['seed', 'event_id', 'series_id', 'n_candidates_after'])
    print(f'  v1105a labels: {len(v1a):,} rows')

    # (3) join + 指標計算
    print('\n[3] expansion / coverage 計算')
    merged = o1.merge(v1a, on=['seed', 'event_id', 'series_id'], how='left')
    merged['word_expansion_ratio'] = (
        merged['n_words_after'] / merged['n_candidates_after'].replace(0, np.nan))
    merged['total_word_coverage_unique'] = merged['n_words_after'] / UNIQUE_WORDS
    merged['total_word_coverage_lexicon'] = merged['n_words_after'] / LEXICON_TOTAL

    valid = merged[merged['structural_label'] == 'word_distribution_valid'].copy()
    print(f'  valid event-series-formula: {len(valid):,}')

    valid_sorted = valid.sort_values(['seed', 'event_id', 'series_id', 'formula']
                                       ).reset_index(drop=True)
    out = V1106A_MAIN / 'observation_3_expansion.parquet'
    valid_sorted.to_parquet(out, index=False)
    print(f'wrote {out.name} ({len(valid_sorted):,} rows)')

    # (4) 系列別分布統計
    print('\n[4] 系列 × formula 別分布統計')
    summary_rows = []
    for formula in ['X', 'Z1']:
        for sid in SERIES_IDS:
            sub = valid[(valid['formula'] == formula) & (valid['series_id'] == sid)]
            if len(sub) == 0:
                continue
            ns = sub['n_words_after']
            er = sub['word_expansion_ratio'].dropna()
            cov_u = sub['total_word_coverage_unique']
            cov_l = sub['total_word_coverage_lexicon']
            summary_rows.append({
                'formula': formula, 'series_id': sid, 'n_events': len(sub),
                'n_words_mean': float(ns.mean()),
                'n_words_median': float(ns.median()),
                'n_words_max': int(ns.max()),
                'n_words_min': int(ns.min()),
                'n_words_p95': float(ns.quantile(0.95)),
                'n_words_p99': float(ns.quantile(0.99)),
                'expansion_ratio_mean': float(er.mean()) if len(er) else np.nan,
                'expansion_ratio_max': float(er.max()) if len(er) else np.nan,
                'coverage_unique_mean': float(cov_u.mean()),
                'coverage_unique_max': float(cov_u.max()),
                'coverage_lexicon_mean': float(cov_l.mean()),
                'coverage_lexicon_max': float(cov_l.max()),
            })
    summary = pd.DataFrame(summary_rows).sort_values(['formula', 'series_id']
                                                       ).reset_index(drop=True)
    out2 = V1106A_MAIN / 'observation_3_summary.parquet'
    summary.to_parquet(out2, index=False)
    print(f'wrote {out2.name}')

    print(f'\n=== Step E 完了、elapsed {time.time()-t0:.1f}s ===')

    print('\n--- 系列別集計 (主要指標) ---')
    cols = ['formula', 'series_id', 'n_words_mean', 'n_words_max',
            'expansion_ratio_mean', 'coverage_unique_mean', 'coverage_unique_max']
    print(summary[cols].round(2).to_string(index=False))

    print('\n--- 候補爆発リスク観察 (s7 × 案 X/Z-1) ---')
    for formula in ['X', 'Z1']:
        s7 = valid[(valid['formula'] == formula) & (valid['series_id'] == 's7_48d_raw_k5')]
        print(f'  s7 ({formula}): n_words max={s7["n_words_after"].max()}, '
              f'p99={s7["n_words_after"].quantile(0.99):.0f}, '
              f'p95={s7["n_words_after"].quantile(0.95):.0f}, '
              f'coverage_unique max={100*s7["total_word_coverage_unique"].max():.2f}%, '
              f'coverage_lexicon max={100*s7["total_word_coverage_lexicon"].max():.2f}%')

    print('\n--- 候補数別分布 (s7-X、event 数比率) ---')
    s7x = valid[(valid['formula'] == 'X') & (valid['series_id'] == 's7_48d_raw_k5')]
    for thresh in [100, 500, 1000, 2000]:
        n = (s7x['n_words_after'] >= thresh).sum()
        pct = 100 * n / len(s7x) if len(s7x) else 0
        print(f'  >= {thresh} words: {n:,} events ({pct:.2f}%)')


if __name__ == '__main__':
    main()
