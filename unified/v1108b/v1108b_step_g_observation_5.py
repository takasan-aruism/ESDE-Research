#!/usr/bin/env python3
"""v1108b Step G — 観察 5: attractor 収束 vs input 効果切り分け

v1106b 観察 2 (各 seed 2-3 個強 attractor、90%+ 集約) との比較。
同 seed 内で異なる category input を投入した時、参照 CID が同じ attractor に
集約するか、input に応じて変わるか。
"""
from __future__ import annotations
import time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1106B_MAIN = REPO / 'unified/v1106b/outputs/main'
V1108B_MAIN = REPO / 'unified/v1108b/outputs/main'
V106_MAIN = REPO / 'developmental/v106/outputs/main'


def main():
    print('=== v1108b Step G — 観察 5: attractor vs input 効果 ===\n')
    t0 = time.time()

    # v1106b 強 attractor 取得 (各 seed 2-3 個)
    attractors_v1106b = pd.read_parquet(V1106B_MAIN / 'observation_2_attractors.parquet')
    # 高 attractor: 5+ start から到達
    high_attractors = attractors_v1106b[attractors_v1106b['n_distinct_start_cid_arrival'] >= 5]
    print(f'  v1106b 強 attractor (5+ start 到達): {len(high_attractors)}')
    seed_attractor_set = defaultdict(set)
    for _, r in high_attractors.iterrows():
        seed_attractor_set[int(r['seed'])].add(int(r['cid']))

    # v1108b 全 325 atom の top-5 CID
    print('\n[1] v1108b 全 atom × top-5 CID と attractor 比較')
    raw_rows = []
    sel = pd.read_parquet(V1108B_MAIN / 'env_check_atom_selection.parquet')
    atoms = sel['atom_full'].tolist()

    for sd in range(24):
        sim_df = pd.read_parquet(V106_MAIN / f'cid_atom_sim_matrix_seed{sd}.parquet')
        atom_cols = [c for c in sim_df.columns if c not in ('seed', 'cid')]
        for atom in atoms:
            if atom not in atom_cols:
                continue
            # top-5 CID
            top5 = sim_df.sort_values(atom, ascending=False).head(5)
            for _, r in top5.iterrows():
                raw_rows.append({
                    'input_atom': atom,
                    'category': atom.split('.')[0],
                    'seed': sd,
                    'cid': int(r['cid']),
                    'sim': float(r[atom]),
                    'is_attractor': int(r['cid']) in seed_attractor_set.get(sd, set()),
                })
    raw_df = pd.DataFrame(raw_rows)
    print(f'  total top-5 CID samples: {len(raw_df):,}')

    # attractor 重複率
    print('\n[2] attractor 重複率')
    attractor_rate_overall = raw_df['is_attractor'].mean()
    print(f'  全体 attractor 重複率: {attractor_rate_overall:.4f}')

    # category 別 attractor 重複率
    cat_overlap = raw_df.groupby('category').agg(
        n_samples=('cid', 'count'),
        attractor_rate=('is_attractor', 'mean'),
        n_unique_cid=('cid', 'nunique'),
    ).reset_index().sort_values('attractor_rate', ascending=False)
    print('\n  category 別 attractor 重複率:')
    print(cat_overlap.round(4).to_string(index=False))

    # input 効果: 同 seed 内で異なる category の参照 CID overlap
    print('\n[3] 同 seed 内 category 間 CID 集合 overlap')
    cat_overlap_rows = []
    for sd in range(24):
        seed_data = raw_df[raw_df['seed'] == sd]
        cats = sorted(seed_data['category'].unique())
        for i, c1 in enumerate(cats):
            for c2 in cats[i+1:]:
                set1 = set(seed_data[seed_data['category'] == c1]['cid'])
                set2 = set(seed_data[seed_data['category'] == c2]['cid'])
                if len(set1 | set2) > 0:
                    jac = len(set1 & set2) / len(set1 | set2)
                else:
                    jac = 0
                cat_overlap_rows.append({
                    'seed': sd, 'cat_a': c1, 'cat_b': c2,
                    'jaccard': jac,
                    'overlap_count': len(set1 & set2),
                })
    cat_ov_df = pd.DataFrame(cat_overlap_rows)
    print(f'  total category pairs: {len(cat_ov_df):,}')
    print(f'  jaccard mean: {cat_ov_df["jaccard"].mean():.4f}, '
          f'median: {cat_ov_df["jaccard"].median():.4f}')

    # social vs isolated cluster の overlap
    cluster_0_cats = {'EXS', 'FND', 'REL', 'LOG', 'VAL', 'WLD'}
    cluster_1_cats = {'BOD', 'PER', 'PRP', 'BEI', 'NAT', 'MAT', 'ACT', 'ELM'}

    intra_0 = cat_ov_df[(cat_ov_df['cat_a'].isin(cluster_0_cats))
                         & (cat_ov_df['cat_b'].isin(cluster_0_cats))]
    intra_1 = cat_ov_df[(cat_ov_df['cat_a'].isin(cluster_1_cats))
                         & (cat_ov_df['cat_b'].isin(cluster_1_cats))]
    inter = cat_ov_df[
        ((cat_ov_df['cat_a'].isin(cluster_0_cats)) & (cat_ov_df['cat_b'].isin(cluster_1_cats)))
        | ((cat_ov_df['cat_a'].isin(cluster_1_cats)) & (cat_ov_df['cat_b'].isin(cluster_0_cats)))
    ]
    print(f'\n  intra cluster_0 jaccard: mean={intra_0["jaccard"].mean():.4f}, n={len(intra_0)}')
    print(f'  intra cluster_1 jaccard: mean={intra_1["jaccard"].mean():.4f}, n={len(intra_1)}')
    print(f'  inter cluster jaccard: mean={inter["jaccard"].mean():.4f}, n={len(inter)}')

    # 構造ラベル判定
    # attractor 重複率 > 0.5 → attractor_dominated
    # cat 間 jaccard mean < 0.3 → category_reference_switch_observed
    if attractor_rate_overall > 0.5:
        label = 'category_reference_attractor_dominated'
    elif cat_ov_df['jaccard'].mean() < 0.3:
        label = 'category_reference_switch_observed'
    elif intra_0['jaccard'].mean() > inter['jaccard'].mean() + 0.1:
        # intra cluster overlap が inter cluster より高ければ弱 switch
        label = 'category_reference_weak_switch'
    else:
        label = 'category_reference_not_resolved'

    sum_df = pd.DataFrame([{
        'attractor_rate_overall': float(attractor_rate_overall),
        'category_jaccard_mean': float(cat_ov_df['jaccard'].mean()),
        'intra_cluster_0_jaccard': float(intra_0['jaccard'].mean()) if len(intra_0) > 0 else 0,
        'intra_cluster_1_jaccard': float(intra_1['jaccard'].mean()) if len(intra_1) > 0 else 0,
        'inter_cluster_jaccard': float(inter['jaccard'].mean()) if len(inter) > 0 else 0,
        'structural_label': label,
        'elapsed_sec': round(time.time() - t0, 2),
    }])
    raw_df.to_parquet(V1108B_MAIN / 'observation_5_attractor_overlap.parquet', index=False)
    cat_ov_df.to_parquet(V1108B_MAIN / 'observation_5_category_jaccard.parquet', index=False)
    sum_df.to_parquet(V1108B_MAIN / 'observation_5_summary.parquet', index=False)

    print(f'\n--- 構造ラベル判定 ---')
    print(f'  attractor 重複率: {attractor_rate_overall:.4f}')
    print(f'  cat jaccard mean: {cat_ov_df["jaccard"].mean():.4f}')
    print(f'  intra cluster_0: {intra_0["jaccard"].mean():.4f} vs inter: {inter["jaccard"].mean():.4f}')
    print(f'  構造ラベル: {label}')

    print(f'\n=== Step G 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
