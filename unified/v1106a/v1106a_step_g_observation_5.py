#!/usr/bin/env python3
"""v1106a Step G — 観察 5: #L41 解消確認

設計書 §2.6 通り、v1106 で確定した #L41 (Synapse v3 weight=1.0 普遍化で atom 間
差別化困難) が mapper_output (raw_scores 0-10 整数 + normalized_scores 0-1) で
解消するかを構造事実として記録。

Step D 出力 (observation_2_mapper_alignment) を再集計、v1106 (Step D 出力
observation_2_synapse_alignment) と直接対比。

指標:
- top1_score_eq_max: top1 score が最大値タイ (raw=10 / norm≈1.0) になる割合
- rank_correlation の NaN 率 / 計算可能率 / 平均
- v1106 直接対比 (Synapse v3 weight=1.0 vs mapper_output raw=10 / norm=1.0)

入力 (read-only):
  - unified/v1106a/outputs/main/observation_2_mapper_alignment.parquet (Step D)
  - unified/v1106/outputs/main/observation_2_synapse_alignment.parquet (v1106 比較)

出力:
  - unified/v1106a/outputs/main/observation_5_L41_resolution.parquet
    (per (formula × series_id) で #L41 関連指標 + v1106 比較)
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1106_MAIN = REPO / 'unified/v1106/outputs/main'
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'

SERIES_IDS = [
    's1_raw_density_raw', 's2_raw_density_norm',
    's3_qweighted_density_raw', 's4_qweighted_density_norm',
    's5_const_adjusted_density_raw', 's6_const_adjusted_density_norm',
    's7_48d_raw_k5',
]


def main():
    V1106A_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106a Step G 観察 5: #L41 解消確認 ===')
    t0 = time.time()

    # (1) Step D 出力読み込み
    print('[1] v1106a Step D 出力 + v1106 比較データ読み込み')
    align = pd.read_parquet(V1106A_MAIN / 'observation_2_mapper_alignment.parquet')
    print(f'  v1106a alignment: {len(align):,} rows')
    v1106_align = pd.read_parquet(V1106_MAIN / 'observation_2_synapse_alignment.parquet')
    print(f'  v1106 alignment: {len(v1106_align):,} rows')

    # (2) per (formula, series_id) で #L41 関連指標集計
    print('\n[2] #L41 関連指標集計')

    rows = []
    for formula in ['X', 'Z1']:
        for sid in SERIES_IDS:
            sub = align[(align['formula'] == formula) & (align['series_id'] == sid)]
            if len(sub) == 0:
                continue
            # top1 score 最大値判定 (X: max=10、Z1: max=1.0 近似)
            if formula == 'X':
                max_val = 10.0
                tied_thresh = 9.999  # >= 10 を tied 扱い
            else:
                max_val = 1.0
                tied_thresh = 0.999  # >= 0.999 を tied 扱い
            top1_tied = (sub['top1_atom_top1_score'] >= tied_thresh).sum()
            top1_tied_rate = top1_tied / len(sub)

            top5_tied = (sub['top5_atom_top1_score_mean'] >= tied_thresh).sum()
            top5_tied_rate = top5_tied / len(sub)

            # rank_correlation: NaN 率 / 計算可能率 / 計算可能 events の mean
            rc = sub['atom_word_rank_correlation']
            n_nan = rc.isna().sum()
            n_valid = (~rc.isna()).sum()
            rc_mean = float(rc.mean()) if n_valid > 0 else np.nan
            rc_pos_rate = float((rc > 0).mean()) if n_valid > 0 else np.nan

            rows.append({
                'formula': formula, 'series_id': sid,
                'n_events': len(sub),
                'top1_score_mean': float(sub['top1_atom_top1_score'].mean()),
                'top1_score_max_val': max_val,
                'top1_tied_count': int(top1_tied),
                'top1_tied_rate': float(top1_tied_rate),
                'top5_tied_rate': float(top5_tied_rate),
                'rc_n_valid': int(n_valid),
                'rc_n_nan': int(n_nan),
                'rc_valid_rate': float(n_valid / len(sub)),
                'rc_mean': rc_mean,
                'rc_positive_rate': rc_pos_rate,
            })
    df = pd.DataFrame(rows)

    # (3) v1106 比較 (Synapse v3)
    print('\n[3] v1106 Synapse v3 直接比較')
    v1106_rows = []
    for sid in SERIES_IDS:
        sub = v1106_align[v1106_align['series_id'] == sid]
        if len(sub) == 0:
            continue
        # Synapse v3 weight max = 1.0
        top1_tied = (sub['top1_atom_top1_syn_strength'] >= 0.999).sum()
        top1_tied_rate = top1_tied / len(sub)
        rc = sub['atom_synapse_rank_correlation']
        n_nan = rc.isna().sum()
        n_valid = (~rc.isna()).sum()
        v1106_rows.append({
            'source': 'v1106_Synapse_v3',
            'series_id': sid,
            'n_events': len(sub),
            'top1_score_mean': float(sub['top1_atom_top1_syn_strength'].mean()),
            'top1_tied_rate': float(top1_tied_rate),
            'rc_n_valid': int(n_valid),
            'rc_valid_rate': float(n_valid / len(sub)),
        })
    v1106_df = pd.DataFrame(v1106_rows)

    # (4) 出力
    df_sorted = df.sort_values(['formula', 'series_id']).reset_index(drop=True)
    out = V1106A_MAIN / 'observation_5_L41_resolution.parquet'
    df_sorted.to_parquet(out, index=False)
    print(f'wrote {out.name} ({len(df_sorted)} rows)')

    print(f'\n=== Step G 完了、elapsed {time.time()-t0:.1f}s ===')

    print('\n--- v1106a × formula × series (top1 tied rate / rc valid rate / rc mean) ---')
    print(df[['formula', 'series_id', 'n_events', 'top1_score_mean',
              'top1_tied_rate', 'rc_valid_rate', 'rc_mean', 'rc_positive_rate']
            ].round(4).to_string(index=False))

    print('\n--- v1106 Synapse v3 直接比較 ---')
    print(v1106_df[['series_id', 'n_events', 'top1_score_mean',
                    'top1_tied_rate', 'rc_valid_rate']].round(4).to_string(index=False))

    print('\n--- #L41 解消判定の構造事実集約 ---')
    print('  v1106 Synapse v3: top1_score 1.0 普遍 (top1_tied_rate ~100%)、rc 計算不能 NaN 多発')
    print(f"  v1106a 案 X (raw_scores=10 tied): top1_tied_rate range = "
          f"{df[df['formula']=='X']['top1_tied_rate'].min():.4f} - "
          f"{df[df['formula']=='X']['top1_tied_rate'].max():.4f}")
    print(f"  v1106a 案 Z-1 (norm=1.0 tied): top1_tied_rate range = "
          f"{df[df['formula']=='Z1']['top1_tied_rate'].min():.4f} - "
          f"{df[df['formula']=='Z1']['top1_tied_rate'].max():.4f}")
    print(f"  v1106a rc 計算可能率 (案 Z-1): "
          f"{df[df['formula']=='Z1']['rc_valid_rate'].mean():.4f} "
          f"(Z-1 のみ計算可、案 X は tied で NaN)")


if __name__ == '__main__':
    main()
