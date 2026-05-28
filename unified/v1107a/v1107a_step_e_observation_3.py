#!/usr/bin/env python3
"""v1107a Step E — 観察 3: shuffle baseline 比較 (基準 A)

category ラベルを 10 回シャッフルして、
- 観察 1 差別化指標 (final_state_std, familiarity CV, n_alphas CV, social CV)
- 観察 2 silhouette (k=2)
が真と比較してどれだけ違うかを測定。

基準 A 判定: z > 2 AND paired diff > 0 rate > 0.75

入力:
- unified/v1106b/outputs/main/observation_3_high_low_events.parquet

出力:
- unified/v1107a/outputs/main/observation_3_shuffle_comparison.parquet
- unified/v1107a/outputs/main/observation_3_summary.parquet
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

REPO = Path('/home/takasan/esde/ESDE-Research')
V1106B_MAIN = REPO / 'unified/v1106b/outputs/main'
V1107A_MAIN = REPO / 'unified/v1107a/outputs/main'

N_SHUFFLE = 10
RNG_SEED = 42


def compute_metrics(va):
    """category × CID profile の差別化指標 + silhouette"""
    profiles = []
    for cat in sorted(va['category'].unique()):
        sub = va[va['category'] == cat]
        fs = sub['final_state'].value_counts(normalize=True).to_dict()
        prof = {
            'category': cat,
            'pct_hosted': fs.get('hosted', 0.0),
            'pct_ghost': fs.get('ghost', 0.0),
            'pct_reaped': fs.get('reaped', 0.0),
        }
        for col in ['last_familiarity_max', 'n_alphas_currently',
                      'current_stability', 'current_social']:
            valid = sub[col].dropna()
            prof[f'{col}_mean'] = float(valid.mean()) if len(valid) > 0 else 0.0
        profiles.append(prof)
    prof_df = pd.DataFrame(profiles)

    # 差別化指標
    fs_std = max(float(prof_df['pct_hosted'].std()),
                  float(prof_df['pct_ghost'].std()),
                  float(prof_df['pct_reaped'].std()))
    means = prof_df['last_familiarity_max_mean'].values
    fam_cv = float(np.std(means) / np.mean(means)) if np.mean(means) > 0 else 0.0
    means = prof_df['n_alphas_currently_mean'].values
    na_cv = float(np.std(means) / np.mean(means)) if abs(np.mean(means)) > 1e-6 else 0.0
    means = prof_df['current_social_mean'].values
    so_cv = float(np.std(means) / np.mean(means)) if abs(np.mean(means)) > 1e-6 else 0.0

    # silhouette (k=2)
    feature_cols = ['pct_hosted', 'pct_ghost', 'pct_reaped',
                     'last_familiarity_max_mean', 'n_alphas_currently_mean',
                     'current_stability_mean', 'current_social_mean']
    X = np.nan_to_num(prof_df[feature_cols].values, nan=0.0)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    if len(prof_df) >= 2:
        model = KMeans(n_clusters=2, random_state=42, n_init=10)
        labels = model.fit_predict(Xs)
        if len(set(labels)) > 1:
            sil = float(silhouette_score(Xs, labels))
        else:
            sil = -1.0
    else:
        sil = -1.0

    return {
        'final_state_std_max': fs_std,
        'familiarity_cv': abs(fam_cv),
        'n_alphas_cv': abs(na_cv),
        'social_cv': abs(so_cv),
        'silhouette_k2': sil,
    }


def main():
    print('=== v1107a Step E — 観察 3: shuffle baseline ===\n')
    t0 = time.time()

    va = pd.read_parquet(V1106B_MAIN / 'observation_3_high_low_events.parquet')
    va['category'] = va['input_atom'].str.split('.').str[0]
    print(f'  events: {len(va)}, categories: {va["category"].nunique()}')

    # (1) 真の指標
    print('\n[1] 真の指標')
    true_metrics = compute_metrics(va)
    for k, v in true_metrics.items():
        print(f'  {k}: {v:.4f}')

    # (2) shuffle baseline (10 回)
    print(f'\n[2] shuffle baseline ({N_SHUFFLE} 回)')
    rng = np.random.default_rng(RNG_SEED)
    shuf_results = []
    for it in range(N_SHUFFLE):
        va_shuf = va.copy()
        va_shuf['category'] = rng.permutation(va_shuf['category'].values)
        m = compute_metrics(va_shuf)
        m['iter'] = it
        shuf_results.append(m)
    shuf_df = pd.DataFrame(shuf_results)
    print(f'  shuffle 平均:')
    for col in ['final_state_std_max', 'familiarity_cv', 'n_alphas_cv',
                  'social_cv', 'silhouette_k2']:
        m = shuf_df[col].mean(); s = shuf_df[col].std()
        print(f'    {col}: mean={m:.4f}, std={s:.4f}')

    # (3) z スコア + paired diff > 0 rate
    print('\n[3] 真 vs shuffle 比較')
    cmp_rows = []
    for col in ['final_state_std_max', 'familiarity_cv', 'n_alphas_cv',
                  'social_cv', 'silhouette_k2']:
        true_val = true_metrics[col]
        shuf_mean = float(shuf_df[col].mean())
        shuf_std = float(shuf_df[col].std())
        z = (true_val - shuf_mean) / shuf_std if shuf_std > 0 else 0.0
        paired_rate = float((shuf_df[col] < true_val).mean())
        cmp_rows.append({
            'metric': col,
            'true': true_val,
            'shuffle_mean': shuf_mean,
            'shuffle_std': shuf_std,
            'z_score': z,
            'paired_rate': paired_rate,
            'passes_z': z > 2.0,
            'passes_paired': paired_rate > 0.75,
        })
    cmp_df = pd.DataFrame(cmp_rows)
    print(cmp_df.round(4).to_string(index=False))

    out1 = V1107A_MAIN / 'observation_3_shuffle_comparison.parquet'
    cmp_df.to_parquet(out1, index=False)
    print(f'\nwrote {out1.name}')

    # (4) 基準 A 判定
    print('\n[4] 基準 A 判定')
    # 1 つでも z>2 AND paired>0.75 を満たす指標があれば通過
    passing_metrics = cmp_df[(cmp_df['passes_z']) & (cmp_df['passes_paired'])]
    n_passing = len(passing_metrics)
    print(f'  z>2 AND paired>0.75 を満たす指標: {n_passing}')
    if n_passing > 0:
        print('  通過指標:')
        for _, r in passing_metrics.iterrows():
            print(f'    {r["metric"]}: z={r["z_score"]:.2f}, paired={r["paired_rate"]:.2f}')

    criterion_a_passed = n_passing > 0
    print(f'\n  基準 A: {"shuffle_passes_threshold" if criterion_a_passed else "shuffle_fails_threshold"}')

    sum_df = pd.DataFrame([{
        'n_passing_metrics': n_passing,
        'criterion_a_passed': criterion_a_passed,
        'max_z_score': float(cmp_df['z_score'].max()),
        'max_paired_rate': float(cmp_df['paired_rate'].max()),
    }])
    out2 = V1107A_MAIN / 'observation_3_summary.parquet'
    sum_df.to_parquet(out2, index=False)
    print(f'wrote {out2.name}')

    print(f'\n=== Step E 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
