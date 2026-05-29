#!/usr/bin/env python3
"""v1109 Step F — 8 測定指標集計 (GPT §3.4)

1. transition_asymmetry: W_ij vs W_ji
2. next_atom_shift: 重み適用前後で次候補がどれだけ変わったか
3. entropy_change: 分布が狭まりすぎていないか
4. max_prob: 一点集中していないか
5. heldout_lift: 未使用データでの効果 (Step E 結果集約)
6. diversity_retention: 多様性が保たれるか (unique atom 数)
7. loop_rate: 同じ Atom/CID に吸われ続けないか
8. category_transfer: category を跨いで効果が残るか
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1109_MAIN = REPO / 'unified/v1109/outputs/main'


def main():
    print('=== v1109 Step F — 8 測定指標集計 ===\n')
    t0 = time.time()

    W_mat = np.load(V1109_MAIN / 'W_matrices.npz', allow_pickle=True)
    applied = pd.read_parquet(V1109_MAIN / 'applied_distributions.parquet')
    holdout = pd.read_parquet(V1109_MAIN / 'observation_E_holdout_results.parquet')
    atoms = list(W_mat['atoms'])

    metric_rows = []
    for cond in ['baseline', 'observed', 'shuffled', 'frequency']:
        W = W_mat[f'W_{cond}']
        # 1. transition_asymmetry
        asym = np.abs(W - W.T)
        # 2-4. applied 集計
        sub = applied[applied['condition'] == cond]
        next_shift = (sub['orig_top1'] != sub['new_top1']).mean()
        # 6. diversity (unique atom 数 in next_top1)
        diversity = sub['new_top1'].nunique()
        # 7. loop_rate (prev == new_top1)
        loop_rate = (sub['prev_atom'] == sub['new_top1']).mean()
        # 8. category_transfer: prev cat ≠ new_top1 cat (cluster_0 ↔ cluster_1)
        prev_cat = sub['prev_atom'].str.split('.').str[0]
        new_cat = sub['new_top1'].str.split('.').str[0]
        cluster_0 = {'EXS', 'FND', 'REL', 'LOG', 'VAL', 'WLD', 'COG', 'COM', 'ABS', 'SPC', 'CHG', 'TIM'}
        prev_in_c0 = prev_cat.isin(cluster_0)
        new_in_c0 = new_cat.isin(cluster_0)
        cat_transfer = ((prev_in_c0 != new_in_c0) & sub['new_top1'].notna()).mean()

        metric_rows.append({
            'condition': cond,
            'transition_asym_max': float(asym.max()),
            'transition_asym_mean': float(asym.mean()),
            'next_atom_shift_rate': float(next_shift),
            'entropy_change_mean': float(sub['entropy_new'].mean() - sub['entropy_orig'].mean()),
            'max_prob_change_mean': float(sub['max_prob_new'].mean() - sub['max_prob_orig'].mean()),
            'diversity_n_unique_new_top1': int(diversity),
            'loop_rate': float(loop_rate),
            'category_transfer_rate': float(cat_transfer),
        })

    metric_df = pd.DataFrame(metric_rows)
    # heldout_lift (Step E から、3 種類 holdout の平均)
    heldout = pd.read_parquet(V1109_MAIN / 'observation_E_summary.parquet')
    avg_lift = heldout.groupby(lambda x: 'avg')[['observed_lift', 'shuffled_lift',
                                                     'frequency_lift']].mean()
    metric_df['heldout_lift_observed_mean'] = avg_lift.iloc[0]['observed_lift']
    metric_df['heldout_lift_shuffled_mean'] = avg_lift.iloc[0]['shuffled_lift']

    metric_df.to_parquet(V1109_MAIN / 'observation_F_metrics.parquet', index=False)
    print(metric_df.to_string(index=False))

    print(f'\n=== Step F 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
