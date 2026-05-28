#!/usr/bin/env python3
"""v1107a Step D — 観察 2: category × CID profile クラスタリング

5 category を CID profile 特徴ベクトルでクラスタリング (k=2-4)。
cluster 命名は機械的 (cluster_0/1/2...)、意味解釈は Phase Result まで保留。

入力:
- unified/v1107a/outputs/main/observation_1_category_profiles.parquet

出力:
- unified/v1107a/outputs/main/observation_2_clusters.parquet (各 k での cluster 割当)
- unified/v1107a/outputs/main/observation_2_summary.parquet
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

REPO = Path('/home/takasan/esde/ESDE-Research')
V1107A_MAIN = REPO / 'unified/v1107a/outputs/main'

# 特徴ベクトル構成
FEATURE_COLS = [
    'pct_hosted', 'pct_ghost', 'pct_reaped',
    'last_familiarity_max_mean',
    'n_alphas_currently_mean',
    'current_social_mean',
    'current_stability_mean',
]


def main():
    print('=== v1107a Step D — 観察 2: クラスタリング ===\n')
    t0 = time.time()

    prof = pd.read_parquet(V1107A_MAIN / 'observation_1_category_profiles.parquet')
    print(f'  categories: {len(prof)}')

    # 特徴ベクトル抽出 + 標準化
    X_raw = prof[FEATURE_COLS].values.astype(np.float64)
    # NaN を 0 埋め
    X_raw = np.nan_to_num(X_raw, nan=0.0)
    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)
    print(f'  feature dim: {X.shape}')

    # クラスタリング k=2-4 (5 category なので最大 4)
    results = []
    assignments = {}
    K_RANGE = [2, 3, 4]
    for method in ['kmeans', 'agglomerative']:
        for k in K_RANGE:
            if method == 'kmeans':
                model = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = model.fit_predict(X)
            else:
                model = AgglomerativeClustering(n_clusters=k, linkage='average')
                labels = model.fit_predict(X)
            if len(set(labels)) > 1 and k < len(prof):
                sil = float(silhouette_score(X, labels))
            else:
                sil = -1.0
            results.append({'method': method, 'k': k, 'silhouette': sil})
            assignments[(method, k)] = labels

    res_df = pd.DataFrame(results)
    print('\n--- silhouette score ---')
    print(res_df.pivot(index='k', columns='method', values='silhouette').round(4).to_string())

    # cluster 割当出力
    assign_rows = []
    for (method, k), labels in assignments.items():
        for cat, lbl in zip(prof['category'].tolist(), labels):
            assign_rows.append({
                'method': method, 'k': k,
                'category': cat, 'cluster': int(lbl),
            })
    assign_df = pd.DataFrame(assign_rows)
    out1 = V1107A_MAIN / 'observation_2_clusters.parquet'
    assign_df.to_parquet(out1, index=False)
    print(f'\nwrote {out1.name}')

    # 最適 k (silhouette 最大) で cluster 構成表示
    best = res_df.sort_values('silhouette', ascending=False).iloc[0]
    print(f'\n--- 最適 {best["method"]} k={int(best["k"])} (silhouette {best["silhouette"]:.4f}) ---')
    best_assign = assignments[(best['method'], int(best['k']))]
    for cl in sorted(set(best_assign)):
        cats = [c for c, l in zip(prof['category'], best_assign) if l == cl]
        print(f'  cluster_{cl}: {cats}')

    # cluster 別 CID profile
    print(f'\n--- 最適 cluster 別の CID profile ---')
    prof_with_cluster = prof.copy()
    prof_with_cluster['cluster'] = best_assign
    for cl in sorted(set(best_assign)):
        sub = prof_with_cluster[prof_with_cluster['cluster'] == cl]
        cats = sub['category'].tolist()
        print(f'\n  cluster_{cl} ({cats}):')
        print(f'    pct_hosted/ghost/reaped: '
              f'{sub["pct_hosted"].mean():.3f}/{sub["pct_ghost"].mean():.3f}/{sub["pct_reaped"].mean():.3f}')
        print(f'    familiarity mean: {sub["last_familiarity_max_mean"].mean():.2f}')
        print(f'    n_alphas mean: {sub["n_alphas_currently_mean"].mean():.3f}')
        print(f'    social mean: {sub["current_social_mean"].mean():.3f}')

    # summary
    purity_each_in_one_cluster = 1.0  # 各 category は 1 cluster に属する (purity 自明 1.0)
    sum_df = pd.DataFrame([{
        'best_method': str(best['method']),
        'best_k': int(best['k']),
        'best_silhouette': float(best['silhouette']),
        'max_silhouette': float(res_df['silhouette'].max()),
        'cluster_count_n': int(best['k']),
        'category_purity_in_clusters': purity_each_in_one_cluster,
    }])
    out2 = V1107A_MAIN / 'observation_2_summary.parquet'
    sum_df.to_parquet(out2, index=False)
    print(f'\nwrote {out2.name}')

    print(f'\n=== Step D 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
