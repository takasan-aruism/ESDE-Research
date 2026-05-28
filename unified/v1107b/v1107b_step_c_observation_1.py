#!/usr/bin/env python3
"""v1107b Step C — 観察 1: 48 axes クラスタリング (3 手法併用)

Step B で計算した軸間 cos_sim マトリクス (48×48) を入力として、
k-means + 階層 + spectral の 3 手法で k=2-6 クラスタリング。
silhouette score で最適 k 選択。
Gemini 仮説 + Code A 案マッピングとの purity 測定。

入力 (read-only):
- unified/v1107b/outputs/main/axes_correlation_matrix.parquet
- unified/v1107b/outputs/main/env_check_axes_meta.parquet

出力:
- unified/v1107b/outputs/main/observation_1_axis_clusters.parquet (3 手法 × k=2-6 結果)
- unified/v1107b/outputs/main/observation_1_hypothesis_purity.parquet (仮説検証)
- unified/v1107b/outputs/main/observation_1_summary.parquet
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, AgglomerativeClustering, SpectralClustering
from sklearn.metrics import silhouette_score
from collections import Counter

REPO = Path('/home/takasan/esde/ESDE-Research')
V1107B_MAIN = REPO / 'unified/v1107b/outputs/main'

K_RANGE = list(range(2, 7))


def purity(labels, true_groups):
    """labels: cluster 割当て、true_groups: 仮説 group の割当て
    各 cluster で最頻出 true group の割合を平均"""
    score = 0
    total = 0
    for cl in set(labels):
        mask = labels == cl
        if mask.sum() == 0:
            continue
        true_in_cl = [g for g, m in zip(true_groups, mask) if m]
        most_common = Counter(true_in_cl).most_common(1)[0][1]
        score += most_common
        total += mask.sum()
    return score / total if total > 0 else 0


def main():
    print('=== v1107b Step C — 観察 1: 48 axes クラスタリング ===\n')
    t0 = time.time()

    corr_df = pd.read_parquet(V1107B_MAIN / 'axes_correlation_matrix.parquet')
    axes_flat = list(corr_df.columns)
    corr = corr_df.values
    print(f'  軸数: {len(axes_flat)}, 軸間 cos_sim mean: {corr[np.triu_indices_from(corr, k=1)].mean():.4f}')

    # 距離化 (1 - cosine sim、kmeans 用には別途座標化)
    # spectral には affinity matrix そのまま使える
    distance = 1.0 - corr
    np.fill_diagonal(distance, 0.0)

    # kmeans 用に特徴空間化 (各軸を 48 次元 cos_sim ベクトルとして扱う)
    features = corr  # (48, 48)、各軸を他 48 軸との sim ベクトルとする

    # (1) 3 手法 × k=2-6 クラスタリング
    print('\n[1] 3 手法 × k=2-6 クラスタリング')
    results = []
    cluster_assignments = {}  # method × k → labels

    for method_name in ['kmeans', 'agglomerative', 'spectral']:
        for k in K_RANGE:
            try:
                if method_name == 'kmeans':
                    model = KMeans(n_clusters=k, random_state=42, n_init=10)
                    labels = model.fit_predict(features)
                elif method_name == 'agglomerative':
                    model = AgglomerativeClustering(n_clusters=k, metric='precomputed',
                                                      linkage='average')
                    labels = model.fit_predict(distance)
                elif method_name == 'spectral':
                    # affinity = cos_sim (>0)
                    affinity = np.clip(corr, 0, None)
                    model = SpectralClustering(n_clusters=k, affinity='precomputed',
                                                 random_state=42, n_init=10)
                    labels = model.fit_predict(affinity)
                # silhouette
                if len(set(labels)) > 1:
                    sil = float(silhouette_score(distance, labels, metric='precomputed'))
                else:
                    sil = -1.0
                results.append({
                    'method': method_name, 'k': k,
                    'silhouette': sil,
                    'cluster_sizes': sorted(Counter(labels).values(), reverse=True),
                })
                cluster_assignments[(method_name, k)] = labels
            except Exception as e:
                print(f'  {method_name} k={k}: ERROR {e}')

    res_df = pd.DataFrame(results)
    print('\n--- silhouette score (3 手法 × k) ---')
    pivot = res_df.pivot(index='k', columns='method', values='silhouette').round(4)
    print(pivot.to_string())

    # 最適 k を method 別に選択
    best_per_method = {}
    for method in ['kmeans', 'agglomerative', 'spectral']:
        sub = res_df[res_df['method'] == method].sort_values('silhouette', ascending=False)
        best_per_method[method] = (int(sub.iloc[0]['k']), float(sub.iloc[0]['silhouette']))
    print(f'\n--- 各手法の最適 k ---')
    for m, (k, s) in best_per_method.items():
        print(f'  {m}: k={k}, silhouette={s:.4f}')

    # (2) クラスタ assignment 出力 (3 手法 × k=2-6)
    print('\n[2] クラスタ assignment 出力')
    assign_rows = []
    for (method, k), labels in cluster_assignments.items():
        for ax, lbl in zip(axes_flat, labels):
            assign_rows.append({
                'method': method, 'k': k,
                'axis': ax, 'cluster': int(lbl),
                'axis_group': ax.split('.')[0],
            })
    assign_df = pd.DataFrame(assign_rows)
    out1 = V1107B_MAIN / 'observation_1_axis_clusters.parquet'
    assign_df.to_parquet(out1, index=False)
    print(f'  wrote {out1.name} ({len(assign_df)} rows)')

    # (3) Gemini 仮説 + Code A 案マッピングとの purity (Q4 段階 2)
    print('\n[3] 仮説マッピングとの purity 測定 (Q4 段階 2)')

    # Gemini 仮説 (実環境再構成、Q4 段階 1)
    gemini_micro = {'temporal.emergence', 'temporal.indication', 'scale.individual',
                     'interconnection.independent', 'ontological.material'}
    gemini_meso = {'interconnection.catalytic', 'interconnection.chained',
                    'interconnection.synchronous', 'interconnection.resonant',
                    'resonance.structural', 'resonance.essential',
                    'epistemological.experience', 'ontological.relational'}
    gemini_macro = {'scale.ecosystem', 'scale.stellar', 'scale.cosmic',
                     'resonance.existential', 'ontological.semantic',
                     'experience.comprehension', 'lawfulness.necessary',
                     'value_generation.sacred'}

    def label_axis(ax):
        if ax in gemini_micro: return 'Micro'
        if ax in gemini_meso: return 'Meso'
        if ax in gemini_macro: return 'Macro'
        return 'Other'

    true_labels = np.array([label_axis(ax) for ax in axes_flat])
    covered = [ax for ax in axes_flat if label_axis(ax) != 'Other']
    print(f'  仮説でカバーされる軸: {len(covered)}/{len(axes_flat)}')
    print(f'  Micro {(true_labels == "Micro").sum()}, '
          f'Meso {(true_labels == "Meso").sum()}, '
          f'Macro {(true_labels == "Macro").sum()}, '
          f'Other {(true_labels == "Other").sum()}')

    purity_rows = []
    for (method, k), labels in cluster_assignments.items():
        # 仮説でカバーされる軸のみで purity 計算
        mask = true_labels != 'Other'
        if mask.sum() > 0:
            p = purity(labels[mask], true_labels[mask])
        else:
            p = 0.0
        # 全軸での purity (Other 含む)
        p_all = purity(labels, true_labels)
        purity_rows.append({
            'method': method, 'k': k,
            'purity_covered': p,
            'purity_all': p_all,
            'n_covered': int(mask.sum()),
        })
    purity_df = pd.DataFrame(purity_rows)
    out2 = V1107B_MAIN / 'observation_1_hypothesis_purity.parquet'
    purity_df.to_parquet(out2, index=False)
    print(f'  wrote {out2.name}')

    print('\n--- 仮説 purity (k=3 のみ表示) ---')
    print(purity_df[purity_df['k'] == 3].round(4).to_string(index=False))

    print('\n--- 全 k の purity_covered ---')
    purity_pivot = purity_df.pivot(index='k', columns='method', values='purity_covered').round(4)
    print(purity_pivot.to_string())

    # (4) summary
    print('\n[4] summary')
    # 最高 silhouette × 最高 purity の組み合わせ
    best_overall = res_df.merge(purity_df, on=['method', 'k']).sort_values(
        ['silhouette', 'purity_covered'], ascending=False).iloc[0]
    print(f'  最高 silhouette × purity: method={best_overall["method"]}, k={best_overall["k"]}, '
          f'silhouette={best_overall["silhouette"]:.4f}, purity={best_overall["purity_covered"]:.4f}')

    # 仮説判定 (Q4 段階 2 threshold)
    max_purity_covered = purity_df['purity_covered'].max()
    if max_purity_covered > 0.7:
        hypothesis_label = 'gemini_hypothesis_supported'
    elif max_purity_covered > 0.4:
        hypothesis_label = 'gemini_hypothesis_partial'
    else:
        hypothesis_label = 'gemini_hypothesis_rejected_alternative_k'

    # silhouette > 0.5 が成立する k があるか (axes_no_scale_structure 判定)
    max_silhouette = res_df['silhouette'].max()
    if max_silhouette < 0.3:
        hypothesis_label = 'axes_no_scale_structure'

    print(f'  構造ラベル: {hypothesis_label}')
    print(f'  (max purity covered: {max_purity_covered:.4f}, max silhouette: {max_silhouette:.4f})')

    sum_df = pd.DataFrame([{
        'best_method': str(best_overall['method']),
        'best_k': int(best_overall['k']),
        'best_silhouette': float(best_overall['silhouette']),
        'best_purity': float(best_overall['purity_covered']),
        'max_silhouette_overall': float(max_silhouette),
        'max_purity_overall': float(max_purity_covered),
        'hypothesis_label': hypothesis_label,
    }])
    out3 = V1107B_MAIN / 'observation_1_summary.parquet'
    sum_df.to_parquet(out3, index=False)
    print(f'\nwrote {out3.name}')

    print(f'\n=== Step C 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
