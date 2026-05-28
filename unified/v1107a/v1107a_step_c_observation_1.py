#!/usr/bin/env python3
"""v1107a Step C — 観察 1: category × CID profile 集計

5 category (PER/EXS/BOD/FND/PRP、構造制約) × 参照 CID 物理量分布を集計。
各 event で input_atom の category と参照 CID (CID 自身) 物理量を merge。

入力 (read-only):
- unified/v1106a/outputs/main/verification_a_cid_word_alignment.parquet
- unified/v1106b/outputs/main/env_check_cid_props.parquet

出力:
- unified/v1107a/outputs/main/observation_1_category_profiles.parquet
- unified/v1107a/outputs/main/observation_1_summary.parquet
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'
V1106B_MAIN = REPO / 'unified/v1106b/outputs/main'
V1107A_MAIN = REPO / 'unified/v1107a/outputs/main'


def main():
    print('=== v1107a Step C — 観察 1: category × CID profile ===\n')
    t0 = time.time()

    # (1) 入力読み込み + category 付与 (v1106b 側で CID 物理量 merge 済み)
    print('[1] 入力読み込み + category 付与')
    va = pd.read_parquet(V1106B_MAIN / 'observation_3_high_low_events.parquet')
    va['category'] = va['input_atom'].str.split('.').str[0]
    print(f'  events: {len(va):,}, categories: {va["category"].nunique()}, '
          f'input_atoms: {va["input_atom"].nunique()}')

    # (2) category × CID profile 集計
    print('\n[2] category × CID profile 集計')
    profiles = []
    for cat in sorted(va['category'].unique()):
        sub = va[va['category'] == cat]
        # final_state 分布
        fs_counts = sub['final_state'].value_counts(normalize=True).to_dict()
        # 物理量 mean / std / cv
        profile = {
            'category': cat,
            'n_events': len(sub),
            'n_input_atoms': sub['input_atom'].nunique(),
            'pct_hosted': fs_counts.get('hosted', 0.0),
            'pct_ghost': fs_counts.get('ghost', 0.0),
            'pct_reaped': fs_counts.get('reaped', 0.0),
        }
        for col in ['last_familiarity_max', 'n_alphas_currently',
                      'current_stability', 'current_social']:
            valid = sub[col].dropna()
            if len(valid) > 0:
                m = float(valid.mean())
                s = float(valid.std())
                profile[f'{col}_mean'] = m
                profile[f'{col}_std'] = s
                profile[f'{col}_cv'] = s / m if m > 1e-6 else 0.0
            else:
                profile[f'{col}_mean'] = None
                profile[f'{col}_std'] = None
                profile[f'{col}_cv'] = None
        profiles.append(profile)
    prof_df = pd.DataFrame(profiles)
    out1 = V1107A_MAIN / 'observation_1_category_profiles.parquet'
    prof_df.to_parquet(out1, index=False)
    print(f'  wrote {out1.name}')

    # 集計表示
    print('\n--- category × final_state 分布 ---')
    print(prof_df[['category', 'n_events', 'pct_hosted', 'pct_ghost', 'pct_reaped']
                    ].round(4).to_string(index=False))

    print('\n--- category × familiarity / n_alphas / social ---')
    print(prof_df[['category', 'last_familiarity_max_mean', 'last_familiarity_max_cv',
                    'n_alphas_currently_mean', 'n_alphas_currently_cv',
                    'current_social_mean', 'current_social_std']
                    ].round(4).to_string(index=False))

    # (3) 差別化指標 (Q1 threshold チェック)
    print('\n[3] 差別化指標 (Q1 threshold)')
    summary = {}

    # final_state 分布の category 間 std
    fs_cols = ['pct_hosted', 'pct_ghost', 'pct_reaped']
    fs_std_per_state = {c: float(prof_df[c].std()) for c in fs_cols}
    summary['final_state_std'] = fs_std_per_state
    summary['final_state_std_max'] = max(fs_std_per_state.values())
    print(f'  final_state pct std (across categories):')
    for c, s in fs_std_per_state.items():
        marker = '✓' if s > 0.10 else '✗'
        print(f'    {c}: std={s:.4f} {marker} (threshold 0.10)')

    # familiarity / n_alphas / social CV (category 間)
    for col in ['last_familiarity_max', 'n_alphas_currently', 'current_social']:
        mean_col = f'{col}_mean'
        means = prof_df[mean_col].dropna().values
        if len(means) > 1:
            std_across = float(np.std(means))
            mean_across = float(np.mean(means))
            cv_across = std_across / mean_across if abs(mean_across) > 1e-6 else 0.0
            summary[f'{col}_cv_across_cats'] = cv_across
            threshold = 0.30 if col == 'last_familiarity_max' else 0.50 if col == 'n_alphas_currently' else 0.10
            marker = '✓' if abs(cv_across) > threshold else '✗'
            print(f'  {col} (category 間): mean={mean_across:.3f}, std={std_across:.3f}, '
                  f'CV={cv_across:.4f} {marker} (threshold {threshold})')

    # 判定: 1 つでも threshold 超え → category_profile_differentiated
    differentiated = (
        summary['final_state_std_max'] > 0.10
        or summary.get('last_familiarity_max_cv_across_cats', 0) > 0.30
        or summary.get('n_alphas_currently_cv_across_cats', 0) > 0.50
        or summary.get('current_social_cv_across_cats', 0) > 0.10
    )
    print(f'\n  構造ラベル: {"category_profile_differentiated" if differentiated else "category_profile_uniform"}')

    sum_df = pd.DataFrame([{
        'category_count': int(prof_df['category'].nunique()),
        'final_state_std_max': summary['final_state_std_max'],
        'familiarity_cv': summary.get('last_familiarity_max_cv_across_cats'),
        'n_alphas_cv': summary.get('n_alphas_currently_cv_across_cats'),
        'social_cv': summary.get('current_social_cv_across_cats'),
        'differentiated': differentiated,
    }])
    out2 = V1107A_MAIN / 'observation_1_summary.parquet'
    sum_df.to_parquet(out2, index=False)
    print(f'\nwrote {out2.name}')

    print(f'\n=== Step C 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
