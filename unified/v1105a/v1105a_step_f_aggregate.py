#!/usr/bin/env python3
"""v1105a Step F — 試行全体の観察項目集計

設計書 v3 §2.6 通り、7 系列の共通比較指標 + layer_jaccard + 4 source レイヤー
別 + CID_n=2 (#L35) + #L34/#L36 試行内動的観察を集計。

入力 (read-only):
  - unified/v1105a/outputs/main/trial_step4_labels.parquet (Step E 出力)
  - unified/v1105a/outputs/main/trial_step4_distributions.parquet (Step E 出力)
  - unified/v1105a/outputs/main/trial_step2_associations.parquet (Step C 出力)

出力:
  - unified/v1105a/outputs/main/trial_summary_metrics.parquet
    (per (series_id) で共通比較指標 + reduction_ratio + max_prob/entropy 分布等)
  - unified/v1105a/outputs/main/trial_layer_jaccard.parquet
    (7 系列 × 7 系列対称行列)
  - unified/v1105a/outputs/main/trial_source_layer_overlap.parquet
    (4 source レイヤー間 atom 分布、#L34 観察)
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1105A_MAIN = REPO / 'unified/v1105a/outputs/main'

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
    V1105A_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1105a Step F 観察項目集計 ===')
    t0 = time.time()

    labels = pd.read_parquet(V1105A_MAIN / 'trial_step4_labels.parquet')
    dist = pd.read_parquet(V1105A_MAIN / 'trial_step4_distributions.parquet')
    assoc = pd.read_parquet(V1105A_MAIN / 'trial_step2_associations.parquet')
    print(f'Step E labels: {len(labels):,} rows')
    print(f'Step E distributions: {len(dist):,} rows')
    print(f'Step C associations: {len(assoc):,} rows')

    # --- (1) 系列別共通比較指標 ---
    print('\n[1] 系列別共通比較指標')
    rows = []
    for sid in SERIES_IDS:
        sub = labels[labels['series_id'] == sid]
        # valid 系列のみで集計
        v = sub[sub['structural_label'] == 'distribution_valid']
        n_total = len(sub)
        n_valid = len(v)
        n_empty = (sub['structural_label'] == 'candidate_empty').sum()
        n_degen = (sub['structural_label'] == 'distribution_degenerate').sum()

        # candidate_before は Step C assoc から (per event の source レイヤー union)
        # candidate_after は Step E n_candidates_after
        # reduction_ratio per-event を計算
        n_before_per_ev = assoc.groupby(['seed', 'event_id'])['candidate_atom'].nunique()
        merged = sub.merge(n_before_per_ev.rename('n_before').reset_index(),
                            on=['seed', 'event_id'], how='left')
        merged['n_before'] = merged['n_before'].fillna(0).astype(int)
        merged_v = merged[merged['structural_label'] == 'distribution_valid']
        if len(merged_v) > 0:
            mn_before = merged_v['n_before']
            mn_after = merged_v['n_candidates_after']
            reduction = 1 - mn_after / mn_before.replace(0, np.nan)
            reduction_mean = float(reduction.mean())
            reduction_median = float(reduction.median())
        else:
            reduction_mean = reduction_median = np.nan

        rows.append({
            'series_id': sid,
            'n_total_events': n_total,
            'n_pipeline_complete': n_valid,
            'pipeline_complete_rate': n_valid / n_total if n_total else 0,
            'n_candidate_empty': int(n_empty),
            'n_distribution_degenerate': int(n_degen),
            'n_distribution_valid': n_valid,
            'reduction_ratio_mean': reduction_mean,
            'reduction_ratio_median': reduction_median,
            'max_prob_mean': float(v['max_prob'].mean()) if len(v) else np.nan,
            'max_prob_median': float(v['max_prob'].median()) if len(v) else np.nan,
            'entropy_mean': float(v['entropy'].mean()) if len(v) else np.nan,
            'entropy_median': float(v['entropy'].median()) if len(v) else np.nan,
            'input_atom_in_top1_rate': float(v['input_atom_in_top1'].mean()) if len(v) else np.nan,
            'input_atom_in_top5_rate': float(v['input_atom_in_top5'].mean()) if len(v) else np.nan,
            'b_high_in_top5_rate': float(v['b_high_in_top5_count'].mean() / 5) if len(v) else np.nan,
        })
    summary = pd.DataFrame(rows)
    # LAYER_A bit-identity: 最終 sort で行順序決定論化
    summary = summary.sort_values('series_id').reset_index(drop=True)
    out_sum = V1105A_MAIN / 'trial_summary_metrics.parquet'
    summary.to_parquet(out_sum, index=False)
    print(f'wrote {out_sum.name}')

    # --- (2) layer_jaccard (7 系列 × 7 対称行列) ---
    print('\n[2] layer_jaccard (per-event top5 重なり)')
    # per-event の top5 atom set を取得
    valid_events = labels[labels['structural_label'] == 'distribution_valid'][
        ['seed', 'event_id', 'series_id', 'top5_atoms']].copy()
    valid_events['top5_set'] = valid_events['top5_atoms'].apply(
        lambda x: set(str(x).split('|')) if x else set())
    # pivot to per-event series_id -> top5_set
    pivot = valid_events.pivot_table(
        index=['seed', 'event_id'], columns='series_id',
        values='top5_set', aggfunc='first')

    jacc_rows = []
    for s1 in SERIES_IDS:
        for s2 in SERIES_IDS:
            if s1 not in pivot.columns or s2 not in pivot.columns:
                continue
            sub = pivot[[s1, s2]].dropna()
            if len(sub) == 0:
                jacc_rows.append({'s1': s1, 's2': s2, 'jaccard_mean': np.nan, 'n_events': 0})
                continue
            jaccs = []
            for _, r in sub.iterrows():
                a = r[s1]; b = r[s2]
                if isinstance(a, set) and isinstance(b, set) and len(a) > 0 and len(b) > 0:
                    j = len(a & b) / len(a | b)
                    jaccs.append(j)
            jacc_rows.append({
                's1': s1, 's2': s2,
                'jaccard_mean': float(np.mean(jaccs)) if jaccs else np.nan,
                'n_events': len(sub)
            })
    jacc_df = pd.DataFrame(jacc_rows)
    out_jacc = V1105A_MAIN / 'trial_layer_jaccard.parquet'
    jacc_df.to_parquet(out_jacc, index=False)
    print(f'wrote {out_jacc.name}')

    # --- (3) 4 source レイヤー間 atom 分布 (#L34 試行内観察) ---
    print('\n[3] 4 source レイヤー間 atom 分布')
    rows = []
    for layer in ['genesis_alpha', 'genesis_beta', 'language_alpha', 'language_beta']:
        sub = assoc[assoc['source_layer'] == layer]
        rows.append({
            'source_layer': layer,
            'n_rows': len(sub),
            'n_events': sub['event_id'].nunique(),
            'n_unique_candidate_atoms': sub['candidate_atom'].nunique(),
            'mean_cands_per_event': len(sub) / sub['event_id'].nunique() if sub['event_id'].nunique() else 0,
        })
    source_layer = pd.DataFrame(rows)
    print(source_layer.to_string())

    # Genesis vs Language Jaccard per scope (alpha / beta)
    print('\n--- Genesis vs Language candidate overlap per scope (Jaccard) ---')
    rows2 = []
    for scope in ['alpha', 'beta']:
        gen = assoc[assoc['source_layer'] == f'genesis_{scope}'].groupby(
            ['seed', 'event_id'])['candidate_atom'].apply(set)
        lang = assoc[assoc['source_layer'] == f'language_{scope}'].groupby(
            ['seed', 'event_id'])['candidate_atom'].apply(set)
        # 共通 event だけ
        common_evs = gen.index.intersection(lang.index)
        if len(common_evs) > 0:
            jaccs = []
            for ev in common_evs:
                a, b = gen[ev], lang[ev]
                if a and b:
                    jaccs.append(len(a & b) / len(a | b))
            rows2.append({
                'scope': scope,
                'n_common_events': len(common_evs),
                'jaccard_mean': float(np.mean(jaccs)) if jaccs else np.nan,
                'gen_only_events': len(gen.index.difference(lang.index)),
                'lang_only_events': len(lang.index.difference(gen.index)),
            })
        else:
            rows2.append({'scope': scope, 'n_common_events': 0,
                           'jaccard_mean': np.nan,
                           'gen_only_events': len(gen),
                           'lang_only_events': len(lang)})
    overlap = pd.DataFrame(rows2)
    out_olap = V1105A_MAIN / 'trial_source_layer_overlap.parquet'
    overlap.to_parquet(out_olap, index=False)
    print(overlap.to_string())

    print(f'\n=== Step F 完了、elapsed {time.time()-t0:.1f}s ===')

    # サマリ
    print('\n=== summary metrics (per series) ===')
    print(summary[['series_id', 'pipeline_complete_rate', 'max_prob_mean',
                    'entropy_mean', 'reduction_ratio_mean', 'b_high_in_top5_rate']
                   ].round(4).to_string(index=False))

    print('\n=== layer_jaccard 対称行列 (mean) ===')
    pv = jacc_df.pivot(index='s1', columns='s2', values='jaccard_mean').round(3)
    print(pv.reindex(SERIES_IDS)[SERIES_IDS].to_string())


if __name__ == '__main__':
    main()
