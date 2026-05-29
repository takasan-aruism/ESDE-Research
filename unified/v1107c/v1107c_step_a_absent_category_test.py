#!/usr/bin/env python3
"""v1107c — 19 不在 category 試行 (v1107a/b 実験方法妥当性検証)

Taka 指摘 (2026-05-29): v1107a の「19 不在 = データ的制約」表現は誤り。
ESDE 内部では 19 category も処理可能。実験者効果 (v1105a で input_atom が 19 種に
絞られた) を省いたテストで「INPUT 次第でどうとでも拡張される ESDE の可能性」を
構造事実として確認する。

手順:
1. 19 不在 category × 216 atom を input_atom として使う
2. 各 atom について 24 seeds × cid_atom_sim_matrix で top-K CID (K=5)
3. 各 top-K CID の物理量 (final_state / familiarity / n_alphas / social) 集計
4. 19 category × CID profile を v1107a 5 category と並べて比較
5. 二極化 (cluster_0 vs cluster_1) に振り分けられるかを確認

入力 (read-only):
- language/atoms/esde_dictionary.json
- unified/v1103/outputs/main/atom_centroids_48d_raw.parquet
- developmental/v106/outputs/main/cid_atom_sim_matrix_seed{N}.parquet
- developmental/v105/diag_v105_main/subjects/per_subject_seed{N}.csv
- unified/v1107a/outputs/main/observation_1_category_profiles.parquet (比較用)
- unified/v1107a/outputs/main/observation_4_cluster_profiles.parquet (cluster 中心)

出力:
- unified/v1107c/outputs/main/absent_category_profiles.parquet (19 category × profile)
- unified/v1107c/outputs/main/all_24_category_comparison.parquet (5 既知 + 19 新規)
- unified/v1107c/outputs/main/cluster_assignment.parquet (各 category の cluster 割当)
- unified/v1107c/outputs/main/summary.parquet
"""
from __future__ import annotations
import json, time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V105_SUB = REPO / 'developmental/v105/diag_v105_main/subjects'
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V1103_MAIN = REPO / 'unified/v1103/outputs/main'
V1107A_MAIN = REPO / 'unified/v1107a/outputs/main'
V1107C_MAIN = REPO / 'unified/v1107c/outputs/main'

TOP_K_CID = 5  # 各 atom × seed で参照する CID 数

PRESENT_CATS = {'PER', 'EXS', 'BOD', 'FND', 'PRP'}


def main():
    V1107C_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1107c — 19 不在 category 試行 (v1107a/b 妥当性検証) ===\n')
    t0 = time.time()

    # (1) atom 一覧 (19 不在 category)
    d = json.load(open(REPO/'language/atoms/esde_dictionary.json'))
    absent_atoms = [c for c in d['concepts'].keys() if c.split('.')[0] not in PRESENT_CATS]
    absent_cats = sorted(set(c.split('.')[0] for c in absent_atoms))
    print(f'  19 不在 category: {absent_cats}')
    print(f'  不在 category の総 atom 数: {len(absent_atoms)}')

    # (2) per_subject 全 seed 集約
    print('\n[1] CID 物理量集約 (24 seeds)')
    cid_props = {}
    for sd in range(24):
        fp = V105_SUB / f'per_subject_seed{sd}.csv'
        df = pd.read_csv(fp, usecols=['cognitive_id', 'final_state',
                                        'last_familiarity_max', 'n_alphas_currently',
                                        'current_stability', 'current_social'])
        for _, r in df.iterrows():
            cid_props[(sd, int(r['cognitive_id']))] = {
                'final_state': r['final_state'],
                'last_familiarity_max': r['last_familiarity_max'],
                'n_alphas_currently': r['n_alphas_currently'],
                'current_stability': r['current_stability'],
                'current_social': r['current_social'],
            }
    print(f'  total CID: {len(cid_props):,}')

    # (3) 各 atom × seed × top-K CID を取得
    print(f'\n[2] 各 atom × 24 seeds × top-{TOP_K_CID} CID 取得')
    profile_rows = []
    n_atoms = len(absent_atoms)
    for i, atom in enumerate(absent_atoms):
        if (i+1) % 30 == 0:
            print(f'  processed {i+1}/{n_atoms} atoms, elapsed {time.time()-t0:.1f}s')
        for sd in range(24):
            fp = V106_MAIN / f'cid_atom_sim_matrix_seed{sd}.parquet'
            sim_df = pd.read_parquet(fp, columns=['cid', atom])
            sim_df = sim_df.sort_values(atom, ascending=False).head(TOP_K_CID)
            for _, r in sim_df.iterrows():
                cid = int(r['cid'])
                if (sd, cid) not in cid_props:
                    continue
                p = cid_props[(sd, cid)]
                profile_rows.append({
                    'input_atom': atom,
                    'category': atom.split('.')[0],
                    'seed': sd,
                    'cid': cid,
                    'sim_to_atom': float(r[atom]),
                    'final_state': p['final_state'],
                    'last_familiarity_max': p['last_familiarity_max'],
                    'n_alphas_currently': p['n_alphas_currently'],
                    'current_stability': p['current_stability'],
                    'current_social': p['current_social'],
                })
    raw_df = pd.DataFrame(profile_rows)
    print(f'  total rows: {len(raw_df):,}')

    # (4) 19 category × CID profile 集計
    print(f'\n[3] 19 category × CID profile 集計')
    cat_profiles = []
    for cat in sorted(raw_df['category'].unique()):
        sub = raw_df[raw_df['category'] == cat]
        fs_counts = sub['final_state'].value_counts(normalize=True).to_dict()
        prof = {
            'category': cat,
            'category_status': 'absent',
            'n_atoms': sub['input_atom'].nunique(),
            'n_top_cid_observations': len(sub),
            'pct_hosted': float(fs_counts.get('hosted', 0)),
            'pct_ghost': float(fs_counts.get('ghost', 0)),
            'pct_reaped': float(fs_counts.get('reaped', 0)),
        }
        for col in ['last_familiarity_max', 'n_alphas_currently',
                      'current_stability', 'current_social']:
            valid = sub[col].dropna()
            prof[f'{col}_mean'] = float(valid.mean()) if len(valid) > 0 else 0.0
        cat_profiles.append(prof)
    abs_df = pd.DataFrame(cat_profiles)
    abs_df.to_parquet(V1107C_MAIN / 'absent_category_profiles.parquet', index=False)
    print(abs_df.round(4).to_string(index=False))

    # (5) v1107a 5 既知 category と並べる
    print(f'\n[4] 5 既知 category と 19 新規 category の対比')
    known_prof = pd.read_parquet(V1107A_MAIN / 'observation_1_category_profiles.parquet')
    known_prof['category_status'] = 'present (v1107a)'
    known_prof['n_atoms'] = known_prof['n_input_atoms']
    known_prof['n_top_cid_observations'] = known_prof['n_events']
    keep_cols = ['category', 'category_status', 'n_atoms', 'n_top_cid_observations',
                  'pct_hosted', 'pct_ghost', 'pct_reaped',
                  'last_familiarity_max_mean', 'n_alphas_currently_mean',
                  'current_stability_mean', 'current_social_mean']
    known_prof_red = known_prof[keep_cols].copy()
    abs_df_red = abs_df[keep_cols].copy()
    all24 = pd.concat([known_prof_red, abs_df_red], ignore_index=True)
    all24.to_parquet(V1107C_MAIN / 'all_24_category_comparison.parquet', index=False)
    print(all24.round(4).to_string(index=False))

    # (6) v1107a cluster 中心と比較し、各不在 category の cluster 割当
    print(f'\n[5] v1107a cluster 中心と比較し、19 category の cluster 割当')
    cluster_centers = pd.read_parquet(V1107A_MAIN / 'observation_4_cluster_profiles.parquet')
    # cluster_0 (EXS/FND 社会的) と cluster_1 (BOD/PER/PRP 孤立) の特徴
    print('\n  v1107a cluster 中心:')
    for _, c in cluster_centers.iterrows():
        print(f'    cluster_{int(c["cluster"])}: hosted={c["weighted_pct_hosted"]:.3f}, '
              f'n_alphas={c["weighted_n_alphas_mean"]:.2f}, social={c["weighted_social_mean"]:.3f}')

    # 各 category について最寄り cluster
    feature_cols = ['pct_hosted', 'pct_ghost', 'pct_reaped',
                      'last_familiarity_max_mean', 'n_alphas_currently_mean',
                      'current_stability_mean', 'current_social_mean']
    centers_arr = []
    for _, c in cluster_centers.iterrows():
        center = np.array([
            c['weighted_pct_hosted'], c['weighted_pct_ghost'], c['weighted_pct_reaped'],
            c['weighted_familiarity_mean'], c['weighted_n_alphas_mean'],
            0.0,  # stability mean (cluster_profiles では計算されていないので 0 埋め)
            c['weighted_social_mean'],
        ])
        centers_arr.append((int(c['cluster']), center))

    # 標準化 (24 category 全体で)
    feat_24 = all24[feature_cols].fillna(0.0).values
    means = feat_24.mean(axis=0); stds = feat_24.std(axis=0)
    stds[stds == 0] = 1.0
    feat_24_std = (feat_24 - means) / stds
    centers_std = []
    for cl, c in centers_arr:
        c_std = (c - means) / stds
        centers_std.append((cl, c_std))

    assignments = []
    for i, row in all24.iterrows():
        f = feat_24_std[i]
        dists = [(cl, float(np.linalg.norm(f - cs))) for cl, cs in centers_std]
        nearest = min(dists, key=lambda x: x[1])
        assignments.append({
            'category': row['category'],
            'category_status': row['category_status'],
            'assigned_cluster': nearest[0],
            'distance_to_cluster_0': dists[0][1],
            'distance_to_cluster_1': dists[1][1],
        })
    assign_df = pd.DataFrame(assignments)
    assign_df.to_parquet(V1107C_MAIN / 'cluster_assignment.parquet', index=False)
    print('\n  各 category の cluster 割当 (最寄り):')
    print(assign_df.round(3).to_string(index=False))

    # (7) cluster 別の category 構成 (5 既知 + 19 新規)
    print(f'\n[6] cluster 別 category 構成')
    for cl in sorted(assign_df['assigned_cluster'].unique()):
        sub = assign_df[assign_df['assigned_cluster'] == cl]
        present = sub[sub['category_status'] == 'present (v1107a)']['category'].tolist()
        absent = sub[sub['category_status'] == 'absent']['category'].tolist()
        print(f'  cluster_{cl}:')
        print(f'    既知 (v1107a): {present}')
        print(f'    新規 (v1107c): {absent}')

    # (8) summary
    print(f'\n[7] summary')
    # 二極化が 24 category 全体で成立するかの判定
    cluster_counts = assign_df.groupby(['assigned_cluster', 'category_status']).size().reset_index(name='n')
    # 19 不在 category が 2 cluster に分布するか
    abs_dist = assign_df[assign_df['category_status'] == 'absent']['assigned_cluster'].value_counts().to_dict()
    print(f'  19 不在 category の cluster 分布: {abs_dist}')

    # 二極化が拡張可能か
    both_clusters_have_absent = len(abs_dist) >= 2
    # 5 既知 category と整合するか (PER/BOD/PRP の cluster と EXS/FND の cluster に新規も振り分けられる)
    known_dist = assign_df[assign_df['category_status'] == 'present (v1107a)']['assigned_cluster'].value_counts().to_dict()

    sum_df = pd.DataFrame([{
        'n_present_cats': len(known_dist) if isinstance(known_dist, dict) else 5,
        'n_absent_cats_assigned_to_cluster_0': abs_dist.get(0, 0),
        'n_absent_cats_assigned_to_cluster_1': abs_dist.get(1, 0),
        'both_clusters_have_absent': both_clusters_have_absent,
        'extension_validated': both_clusters_have_absent,
    }])
    sum_df.to_parquet(V1107C_MAIN / 'summary.parquet', index=False)

    print(f'\n=== v1107c 完了、elapsed {time.time()-t0:.1f}s ===\n')

    # 結論
    print('--- 結論 ---')
    print(f'  v1107a 「19 不在 = データ的制約」表現の検証:')
    if both_clusters_have_absent:
        print(f'    → 撤回: 19 category も 2 cluster に振り分けられる')
        print(f'    → ESDE 拡張可能性 (INPUT 次第でどうとでも拡張) 確認')
        print(f'    → v1107a/b 結論は 24 category 全体に拡張可能')
    else:
        print(f'    → 19 category がすべて同一 cluster に集中、別の構造的事実')


if __name__ == '__main__':
    main()
