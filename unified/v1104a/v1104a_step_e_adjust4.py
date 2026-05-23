#!/usr/bin/env python3
"""v1104a Step E' — 追加調整 4: 観察 4 を scope-filter で再点検

設計書 §2.4 通り:
- observation_4_b_overlap.parquet (81 cells = 27 receiver_bin × 3 metric) を
  scope-filter (all / CID / alpha / beta / ESDE) で 5 グループに分割
- 各グループで A∩B / A∪B / A\B / B\A を再計算
- Jaccard / Recall (A 中の B 比率) / Precision (B 中の A 比率) を per-scope で算出
- B\A の件数と分布を scope 別に記録 (意味判定なし、selector 化禁止)

A primary: A_outstanding_high (= outstanding_score >= 3、既存定義)
B primary: B_outstanding_score >= 1 (any) / >= 2 (strong)

入力 (read-only):
  - unified/v1104/outputs/main/observation_4_b_overlap.parquet (81 cells、A/B 列既存)

出力:
  - unified/v1104a/outputs/main/observation_4_scope_filtered.parquet
    (per (scope_filter, metric_filter, A∩B etc 件数 + Jaccard/Recall/Precision))
  - unified/v1104a/outputs/main/observation_4_b_minus_a_cells.parquet
    (B が独自に拾う cell の receiver_bin 内訳、scope 別)
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1104_MAIN = REPO_ROOT / 'unified/v1104/outputs/main'
V1104A_MAIN = REPO_ROOT / 'unified/v1104a/outputs/main'


def scope_of_receiver_bin(rb: str) -> str:
    if rb.startswith('CID_n='): return 'CID'
    if rb.startswith('alpha_'): return 'alpha'
    if rb.startswith('beta_'): return 'beta'
    if rb.startswith('ESDE_'): return 'ESDE'
    return 'other'


def compute_overlap(sub: pd.DataFrame, b_threshold: int) -> dict:
    """sub 内で A∩B / A∪B / A\\B / B\\A 件数 + Jaccard/Recall/Precision"""
    a_idx = set(sub[sub['A_outstanding_high']].index)
    b_idx = set(sub[sub['B_outstanding_score'] >= b_threshold].index)
    inter = a_idx & b_idx
    union = a_idx | b_idx
    a_only = a_idx - b_idx  # A\B
    b_only = b_idx - a_idx  # B\A
    return {
        'n_cells_total': len(sub),
        'n_A': len(a_idx),
        'n_B': len(b_idx),
        'n_A_and_B': len(inter),
        'n_A_or_B': len(union),
        'n_A_only': len(a_only),
        'n_B_only': len(b_only),
        'jaccard': len(inter) / len(union) if union else 0.0,
        'recall_B_covers_A': len(inter) / len(a_idx) if a_idx else np.nan,
        'precision_B_is_A': len(inter) / len(b_idx) if b_idx else np.nan,
        'b_only_indices': sorted(b_only),
    }


def main():
    V1104A_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1104a Step E 追加調整 4: 観察 4 scope-filter ===')
    t0 = time.time()

    o4 = pd.read_parquet(V1104_MAIN / 'observation_4_b_overlap.parquet')
    print(f'observation_4 loaded: {len(o4):,} cells')
    print(f'columns relevant: A_outstanding_high, B_outstanding_score, B_outstanding_*')
    print(f'  receiver_bin uniques: {len(o4["receiver_bin"].unique())}')
    print(f'  change_metric_type: {o4["change_metric_type"].unique()}')

    o4 = o4.reset_index(drop=True)
    o4['scope'] = o4['receiver_bin'].apply(scope_of_receiver_bin)
    print(f'  scope counts: {o4["scope"].value_counts().to_dict()}')

    # scope-filter 5 グループ × B_threshold 1/2 で集計
    rows = []
    b_minus_a_rows = []
    scope_groups = ['all', 'CID', 'alpha', 'beta', 'ESDE']
    for scope_label in scope_groups:
        if scope_label == 'all':
            sub = o4
        else:
            sub = o4[o4['scope'] == scope_label]
        for b_thr in [1, 2]:
            o = compute_overlap(sub, b_thr)
            rows.append({
                'scope_filter': scope_label,
                'b_threshold': b_thr,
                **{k: v for k, v in o.items() if k != 'b_only_indices'},
            })
            # B\A cell 内訳
            for idx in o['b_only_indices']:
                cell = sub.loc[idx]
                b_minus_a_rows.append({
                    'scope_filter': scope_label,
                    'b_threshold': b_thr,
                    'receiver_bin': cell['receiver_bin'],
                    'change_metric_type': cell['change_metric_type'],
                    'B_outstanding_score': int(cell['B_outstanding_score']),
                    'B_cmv': bool(cell.get('B_outstanding_cmv', False)),
                    'B_sal': bool(cell.get('B_outstanding_sal', False)),
                    'B_crank': bool(cell.get('B_outstanding_crank', False)),
                    'A_outstanding_score': cell['outstanding_score'],
                })

    out_main = V1104A_MAIN / 'observation_4_scope_filtered.parquet'
    pd.DataFrame(rows).to_parquet(out_main, index=False)
    print(f'\nwrote {out_main.name} ({len(rows)} rows)')

    out_bma = V1104A_MAIN / 'observation_4_b_minus_a_cells.parquet'
    pd.DataFrame(b_minus_a_rows).to_parquet(out_bma, index=False)
    print(f'wrote {out_bma.name} ({len(b_minus_a_rows)} B\\A cells)')

    print(f'\nelapsed {time.time()-t0:.1f}s')

    # --- サマリ ---
    print('\n--- scope × B_threshold 別 overlap (B_threshold=1) ---')
    df = pd.DataFrame(rows)
    s1 = df[df['b_threshold'] == 1]
    print(s1[['scope_filter', 'n_cells_total', 'n_A', 'n_B',
              'n_A_and_B', 'n_A_only', 'n_B_only',
              'jaccard', 'recall_B_covers_A', 'precision_B_is_A']
           ].round(4).to_string(index=False))

    print('\n--- scope × B_threshold 別 overlap (B_threshold=2 strong) ---')
    s2 = df[df['b_threshold'] == 2]
    print(s2[['scope_filter', 'n_cells_total', 'n_A', 'n_B',
              'n_A_and_B', 'n_A_only', 'n_B_only',
              'jaccard', 'recall_B_covers_A', 'precision_B_is_A']
           ].round(4).to_string(index=False))

    print('\n--- B\\A cell 分布 (scope 別件数、b_threshold=1) ---')
    bma = pd.DataFrame(b_minus_a_rows)
    bma1 = bma[bma['b_threshold'] == 1]
    print(bma1.groupby(['scope_filter'])['receiver_bin'].agg(['count', 'nunique']).to_string())
    print('\n--- B\\A の受信側分布 (b_threshold=1, scope=all) ---')
    bma1_all = bma1[bma1['scope_filter'] == 'all']
    print(bma1_all.groupby(['receiver_bin', 'change_metric_type']).size().to_string())


if __name__ == '__main__':
    main()
