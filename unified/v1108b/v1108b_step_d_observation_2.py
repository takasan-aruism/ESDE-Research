#!/usr/bin/env python3
"""v1108b Step D — 観察 2: cluster_0/1 への距離・分布・強度 (GPT §2.2)

v1107a cluster 中心 (cluster_0 = EXS/FND 社会的、cluster_1 = BOD/PER/PRP 孤立) への
euclidean 距離 (標準化後) を 325 atom 全体 + 24 cat 集約で測定。
距離差 |d_0 - d_1| を「強度」として連続量扱い (GPT §2.2 二値決定回避)。

入力:
- unified/v1108b/outputs/main/observation_1_atom_profiles.parquet
- unified/v1107a/outputs/main/observation_4_cluster_profiles.parquet

出力:
- unified/v1108b/outputs/main/observation_2_atom_distances.parquet
- unified/v1108b/outputs/main/observation_2_category_distances.parquet
- unified/v1108b/outputs/main/observation_2_summary.parquet
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

REPO = Path('/home/takasan/esde/ESDE-Research')
V1107A_MAIN = REPO / 'unified/v1107a/outputs/main'
V1108B_MAIN = REPO / 'unified/v1108b/outputs/main'


def main():
    print('=== v1108b Step D — 観察 2: cluster 距離 ===\n')
    t0 = time.time()

    atom_prof = pd.read_parquet(V1108B_MAIN / 'observation_1_atom_profiles.parquet')
    cluster_centers = pd.read_parquet(V1107A_MAIN / 'observation_4_cluster_profiles.parquet')

    # 特徴ベクトル
    feature_cols = ['pct_hosted', 'pct_ghost', 'pct_reaped',
                      'last_familiarity_max_mean', 'n_alphas_currently_mean',
                      'current_stability_mean', 'current_social_mean']

    # cluster 中心抽出
    centers = {}
    for _, c in cluster_centers.iterrows():
        # cluster_profiles の列名から
        center = np.array([
            c['weighted_pct_hosted'], c['weighted_pct_ghost'], c['weighted_pct_reaped'],
            c['weighted_familiarity_mean'], c['weighted_n_alphas_mean'],
            0.0,  # stability (cluster_profiles で計算されていない)
            c['weighted_social_mean'],
        ])
        centers[int(c['cluster'])] = center
    print(f'  cluster centers: {len(centers)}')

    # 325 atom + cluster centers をまとめて標準化
    atom_features = atom_prof[feature_cols].fillna(0.0).values
    center_features = np.vstack([centers[0], centers[1]])
    all_features = np.vstack([atom_features, center_features])
    scaler = StandardScaler()
    all_std = scaler.fit_transform(all_features)
    atom_std = all_std[:len(atom_prof)]
    centers_std = all_std[len(atom_prof):]

    # 距離計算
    print('\n[1] 325 atom × cluster_0/1 euclidean 距離')
    d0 = np.linalg.norm(atom_std - centers_std[0], axis=1)
    d1 = np.linalg.norm(atom_std - centers_std[1], axis=1)
    dist_diff = np.abs(d0 - d1)
    nearest_cluster = np.where(d0 < d1, 0, 1)

    atom_dist = atom_prof[['input_atom', 'category']].copy()
    atom_dist['distance_to_cluster_0'] = d0
    atom_dist['distance_to_cluster_1'] = d1
    atom_dist['distance_diff'] = dist_diff
    atom_dist['nearest_cluster'] = nearest_cluster
    # 強度 (連続量): 距離差 / 平均距離
    avg_dist = (d0 + d1) / 2
    atom_dist['strength_signed'] = (d1 - d0) / avg_dist  # cluster_0 寄りなら正
    atom_dist.to_parquet(V1108B_MAIN / 'observation_2_atom_distances.parquet', index=False)

    print(f'  atom 別最近接 cluster: cluster_0 {(nearest_cluster==0).sum()}, '
          f'cluster_1 {(nearest_cluster==1).sum()}')
    print(f'  distance_diff: mean={dist_diff.mean():.4f}, '
          f'median={np.median(dist_diff):.4f}, max={dist_diff.max():.4f}')
    print(f'  strength_signed (cluster_0 寄り正): '
          f'mean={atom_dist["strength_signed"].mean():.4f}')

    # category 別集約
    print('\n[2] 24 category × cluster 距離集約')
    cat_rows = []
    for cat in sorted(atom_dist['category'].unique()):
        sub = atom_dist[atom_dist['category'] == cat]
        n0 = int((sub['nearest_cluster'] == 0).sum())
        n1 = int((sub['nearest_cluster'] == 1).sum())
        cat_rows.append({
            'category': cat,
            'n_atoms': len(sub),
            'n_nearest_cluster_0': n0,
            'n_nearest_cluster_1': n1,
            'pct_to_cluster_0': float(n0 / len(sub)),
            'mean_d0': float(sub['distance_to_cluster_0'].mean()),
            'mean_d1': float(sub['distance_to_cluster_1'].mean()),
            'mean_distance_diff': float(sub['distance_diff'].mean()),
            'mean_strength_signed': float(sub['strength_signed'].mean()),
        })
    cat_df = pd.DataFrame(cat_rows).sort_values('mean_strength_signed', ascending=False)
    cat_df.to_parquet(V1108B_MAIN / 'observation_2_category_distances.parquet', index=False)
    print(cat_df[['category', 'n_atoms', 'pct_to_cluster_0', 'mean_distance_diff',
                    'mean_strength_signed']].round(4).to_string(index=False))

    # cluster 別 category 構成 (atom 多数決)
    print('\n[3] cluster 別 category 構成 (atom 多数決ベース)')
    for cl in [0, 1]:
        cats = cat_df[(cat_df['n_nearest_cluster_0'] if cl==0 else cat_df['n_nearest_cluster_1'])
                       > cat_df['n_atoms'] / 2]['category'].tolist()
        print(f'  cluster_{cl}: {sorted(cats)}')

    # summary
    n_strong_switch = (atom_dist['distance_diff'] > 0.5).sum()  # threshold 例
    n_weak_switch = ((atom_dist['distance_diff'] > 0.1) & (atom_dist['distance_diff'] <= 0.5)).sum()
    n_very_weak = (atom_dist['distance_diff'] <= 0.1).sum()

    # 構造ラベル判定
    cat_in_cluster_0 = (cat_df['pct_to_cluster_0'] > 0.5).sum()
    cat_in_cluster_1 = (cat_df['pct_to_cluster_0'] < 0.5).sum()
    both_clusters = cat_in_cluster_0 >= 5 and cat_in_cluster_1 >= 5

    if both_clusters and atom_dist['distance_diff'].mean() > 0.3:
        label = 'category_reference_switch_observed'
    elif both_clusters:
        label = 'category_reference_weak_switch'
    else:
        label = 'category_reference_not_resolved'

    sum_df = pd.DataFrame([{
        'n_atoms': len(atom_dist),
        'n_categories': cat_df['category'].nunique(),
        'mean_distance_diff': float(atom_dist['distance_diff'].mean()),
        'median_distance_diff': float(atom_dist['distance_diff'].median()),
        'max_distance_diff': float(atom_dist['distance_diff'].max()),
        'n_strong_switch_gt_05': int(n_strong_switch),
        'n_weak_switch_01_05': int(n_weak_switch),
        'n_very_weak_le_01': int(n_very_weak),
        'cat_in_cluster_0': int(cat_in_cluster_0),
        'cat_in_cluster_1': int(cat_in_cluster_1),
        'structural_label': label,
        'elapsed_sec': round(time.time() - t0, 2),
    }])
    sum_df.to_parquet(V1108B_MAIN / 'observation_2_summary.parquet', index=False)
    print(f'\n--- 構造ラベル判定 ---')
    print(f'  distance_diff strong (>0.5): {n_strong_switch}')
    print(f'  distance_diff weak (0.1-0.5): {n_weak_switch}')
    print(f'  distance_diff very weak (<=0.1): {n_very_weak}')
    print(f'  cat_in_cluster_0: {cat_in_cluster_0}, cat_in_cluster_1: {cat_in_cluster_1}')
    print(f'  構造ラベル: {label}')

    print(f'\n=== Step D 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
