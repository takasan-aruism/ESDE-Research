#!/usr/bin/env python3
"""v1107b Step E — 観察 3: shuffle baseline 比較 (基準 A)

軸ラベルシャッフル: 48 軸の値ベクトルをシャッフル → クラスタリングが構造を失うか
category ラベルシャッフル: 観察 2 category × scale 寄与の差別化が消えるか

基準 A 判定: silhouette > 0.5 AND z > 2

入力:
- unified/v1107b/outputs/main/axes_correlation_matrix.parquet
- unified/v1107b/outputs/main/observation_2_axis_contribution.parquet
- unified/v1107b/outputs/main/observation_2_summary.parquet

出力:
- unified/v1107b/outputs/main/observation_3_axis_shuffle.parquet (軸シャッフル)
- unified/v1107b/outputs/main/observation_3_category_shuffle.parquet (category シャッフル)
- unified/v1107b/outputs/main/observation_3_summary.parquet
"""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, AgglomerativeClustering, SpectralClustering
from sklearn.metrics import silhouette_score
from collections import Counter

REPO = Path('/home/takasan/esde/ESDE-Research')
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V1107B_MAIN = REPO / 'unified/v1107b/outputs/main'

N_SHUFFLE = 10
RNG_SEED = 42
K = 3  # 観察 1 で最良の agglomerative k=3 を使う


def cluster_silhouette(features, distance, method, k):
    if method == 'kmeans':
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(features)
    elif method == 'agglomerative':
        model = AgglomerativeClustering(n_clusters=k, metric='precomputed',
                                          linkage='average')
        labels = model.fit_predict(distance)
    elif method == 'spectral':
        affinity = np.clip(features, 0, None)
        model = SpectralClustering(n_clusters=k, affinity='precomputed',
                                     random_state=42, n_init=10)
        labels = model.fit_predict(affinity)
    if len(set(labels)) > 1:
        sil = float(silhouette_score(distance, labels, metric='precomputed'))
    else:
        sil = -1.0
    return labels, sil


def main():
    print('=== v1107b Step E — 観察 3: shuffle baseline ===\n')
    t0 = time.time()

    corr_df = pd.read_parquet(V1107B_MAIN / 'axes_correlation_matrix.parquet')
    axes_flat = list(corr_df.columns)
    corr = corr_df.values
    distance = 1.0 - corr
    np.fill_diagonal(distance, 0.0)

    # (1) 真の silhouette (3 手法 × k=3)
    print(f'[1] 真の silhouette (k={K})')
    true_sils = {}
    for method in ['kmeans', 'agglomerative', 'spectral']:
        _, sil = cluster_silhouette(corr, distance, method, K)
        true_sils[method] = sil
        print(f'  {method}: {sil:.4f}')

    # (2) 軸ラベルシャッフル: 48 軸の値ベクトル (atom centroid 集合) をシャッフル
    print(f'\n[2] 軸ラベルシャッフル baseline ({N_SHUFFLE} 回)')
    # 各軸の値ベクトル (325 atom にわたる値) をシャッフル
    # = corr matrix で行・列を独立にシャッフル
    rng = np.random.default_rng(RNG_SEED)
    shuf_axis_sils = {m: [] for m in ['kmeans', 'agglomerative', 'spectral']}
    for it in range(N_SHUFFLE):
        # 各列を独立に random permute (軸値ベクトルがランダム化)
        # corr 自体は 48×48 で、各軸 i の他軸との相関がシャッフル
        # → 軸 i の値ベクトル自体をシャッフル
        # corr from cosine sim なので、軸の値順序を変えると corr 変わる
        # 簡易: corr 行/列を独立に random permutation
        perm = rng.permutation(48)
        # row permutation
        corr_shuf = corr[perm][:, perm]
        # しかし row+col 同じ perm では labels も permute されるだけで分離は同じ
        # 真のシャッフル: 異なる perm を row/col に → 対称性失われる
        # ここでは「軸 ID をシャッフル後の cluster と元の cluster の一致度」を比較するため
        # corr の row/col 独立シャッフル (asymmetric な distance になる)
        perm2 = rng.permutation(48)
        # 各 row i を perm2 で並び替え
        corr_shuf2 = corr[perm][:, perm2]
        # 対称化 (距離行列にする)
        sym = (corr_shuf2 + corr_shuf2.T) / 2
        dist_shuf = 1.0 - sym
        np.fill_diagonal(dist_shuf, 0.0)
        for method in ['kmeans', 'agglomerative', 'spectral']:
            try:
                _, sil = cluster_silhouette(sym, dist_shuf, method, K)
                shuf_axis_sils[method].append(sil)
            except Exception:
                shuf_axis_sils[method].append(-1.0)

    shuf_rows = []
    for method in ['kmeans', 'agglomerative', 'spectral']:
        arr = np.array(shuf_axis_sils[method])
        true_v = true_sils[method]
        m = arr.mean(); s = arr.std()
        z = (true_v - m) / s if s > 0 else 0.0
        paired = float((arr < true_v).mean())
        shuf_rows.append({
            'method': method, 'k': K,
            'true_silhouette': true_v,
            'shuf_axis_mean': m, 'shuf_axis_std': s,
            'z_score': z, 'paired_rate': paired,
            'passes_z': z > 2.0,
            'passes_silhouette': true_v > 0.5,
        })
    axis_shuf_df = pd.DataFrame(shuf_rows)
    out1 = V1107B_MAIN / 'observation_3_axis_shuffle.parquet'
    axis_shuf_df.to_parquet(out1, index=False)
    print(axis_shuf_df.round(4).to_string(index=False))

    # (3) category ラベルシャッフル: 観察 2 の category × scale 寄与差別化
    print(f'\n[3] category ラベルシャッフル baseline (観察 2 寄与差別化)')
    contrib = pd.read_parquet(V1107B_MAIN / 'observation_2_axis_contribution.parquet')

    axes = []
    am = json.load(open(V106_MAIN / 'axes_metadata.json'))
    for ax in am['axes_order']:
        for lvl in ax['level_names']:
            axes.append(f'{ax["name"]}.{lvl}')

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

    def axis_scale(ax):
        if ax in gemini_micro: return 'Micro'
        if ax in gemini_meso: return 'Meso'
        if ax in gemini_macro: return 'Macro'
        return 'Other'

    axis_scales = [axis_scale(axes[i]) for i in range(48)]

    def compute_scale_cv(df):
        bias = []
        for cat in sorted(df['category'].unique()):
            sub = df[df['category'] == cat]
            ax_contribs = np.array([sub[f'axis_{i}'].mean() for i in range(48)])
            scale_sum = {'Micro': 0.0, 'Meso': 0.0, 'Macro': 0.0}
            for i, sc in enumerate(axis_scales):
                if sc in scale_sum:
                    scale_sum[sc] += ax_contribs[i]
            bias.append({'category': cat, **scale_sum})
        bdf = pd.DataFrame(bias)
        cvs = {}
        for sc in ['Micro', 'Meso', 'Macro']:
            mean = bdf[sc].mean()
            std = bdf[sc].std()
            cvs[sc] = abs(std / mean) if abs(mean) > 1e-6 else 0.0
        return max(cvs.values()), cvs

    # 真の CV
    true_cv, true_cvs_each = compute_scale_cv(contrib)
    print(f'  真の max scale CV: {true_cv:.4f} ({true_cvs_each})')

    # category シャッフル baseline
    shuf_cvs = []
    rng2 = np.random.default_rng(RNG_SEED + 100)
    for it in range(N_SHUFFLE):
        contrib_shuf = contrib.copy()
        contrib_shuf['category'] = rng2.permutation(contrib_shuf['category'].values)
        max_cv, _ = compute_scale_cv(contrib_shuf)
        shuf_cvs.append(max_cv)

    cv_arr = np.array(shuf_cvs)
    z = (true_cv - cv_arr.mean()) / cv_arr.std() if cv_arr.std() > 0 else 0.0
    paired = float((cv_arr < true_cv).mean())
    print(f'  shuffle: mean={cv_arr.mean():.4f}, std={cv_arr.std():.4f}')
    print(f'  z={z:.2f}, paired_rate={paired:.4f}')

    cat_shuf_df = pd.DataFrame([{
        'metric': 'max_scale_cv',
        'true': float(true_cv),
        'shuffle_mean': float(cv_arr.mean()),
        'shuffle_std': float(cv_arr.std()),
        'z_score': float(z),
        'paired_rate': paired,
        'passes_z': z > 2.0,
        'passes_paired': paired > 0.75,
    }])
    out2 = V1107B_MAIN / 'observation_3_category_shuffle.parquet'
    cat_shuf_df.to_parquet(out2, index=False)

    # (4) 基準 A 判定
    print('\n[4] 基準 A 判定')
    # silhouette > 0.5 (実環境では達成困難、観察 1 で max 0.36)
    # axis_shuffle で z > 2 が成立する method があるか
    # category_shuffle で z > 2 AND paired > 0.75 か
    axis_pass = axis_shuf_df[axis_shuf_df['passes_z']].shape[0] > 0
    silhouette_pass = (axis_shuf_df['true_silhouette'] > 0.5).any()
    cat_pass = bool(cat_shuf_df['passes_z'].iloc[0]) and bool(cat_shuf_df['passes_paired'].iloc[0])

    print(f'  軸シャッフル z>2 通過: {axis_pass}')
    print(f'  silhouette > 0.5 通過: {silhouette_pass}')
    print(f'  category シャッフル z>2 AND paired>0.75 通過: {cat_pass}')

    # 厳格判定: silhouette > 0.5 AND z > 2 (axis または category)
    criterion_a_strict = silhouette_pass and (axis_pass or cat_pass)
    # 緩和判定 (silhouette を緩めて category 通過のみで判定)
    criterion_a_lenient = cat_pass

    sum_df = pd.DataFrame([{
        'axis_shuffle_pass': axis_pass,
        'silhouette_above_05': silhouette_pass,
        'category_shuffle_pass': cat_pass,
        'criterion_a_strict': criterion_a_strict,
        'criterion_a_lenient': criterion_a_lenient,
        'max_silhouette': float(axis_shuf_df['true_silhouette'].max()),
        'category_z_score': float(cat_shuf_df['z_score'].iloc[0]),
        'category_paired_rate': float(cat_shuf_df['paired_rate'].iloc[0]),
    }])
    out3 = V1107B_MAIN / 'observation_3_summary.parquet'
    sum_df.to_parquet(out3, index=False)

    print(f'\n  基準 A (厳格、silhouette>0.5 AND z>2): {"PASS" if criterion_a_strict else "FAIL"}')
    print(f'  基準 A (緩和、category 通過のみ): {"PASS" if criterion_a_lenient else "FAIL"}')

    print(f'\n=== Step E 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
