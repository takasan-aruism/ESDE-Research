#!/usr/bin/env python3
"""v1113 post-process — per-cid / n_core 別層化観察 (集団平均の罠回避)

Taka 指摘 (2026-06-04):
- 本実装の初版は atom 別の集団平均のみで、per-cid / n_core 別を入れていなかった
- 「特に響く少数 CID」が集団平均に埋もれる ([[code-a-blind-spots]] §13)
- features.parquet を使って後段で per-cid / n_core 別を補完

入力: unified/attention_center_prep/run_v1113/cid_features_all.parquet
出力:
- run_v1113/per_cid_summary.parquet (per-cid: cid, atom_seed, n_core, real_max, null_max_mean, rank, gap)
- run_v1113/ncore_summary.parquet (n_core 群別集計)
- run_v1113/top_sim_pairs.parquet (上位 sim ペア + 特性次元分解)
- run_v1113/per_cid_summary.json (人間可読サマリ)
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

import sys, json, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
STAGE5 = REPO / 'unified/attention_center_prep'
OUT_DIR = STAGE5 / 'run_v1113'

# 本実装と同じ
ATOM_SEEDS = [42, 100, 200]
OTHER_SEED_FIXED = 999
NULL_OTHER_SEEDS = [12345, 54321, 7777, 11111, 33333]
FEATURE_KEYS = [
    'phase_sig_cos', 'phase_sig_sin',
    'phi_cos', 'phi_sin',
    'n_core', 'lifespan',
    'Q0', 'Q_remaining', 'C',
    'familiarity_n', 'v10_pulse_count', 'v11_n_captured', 'v11_b_gen',
    'cid_ttl_bonus', 'v18_birth_v_unified_concentration',
]

# n_core 群分け (v10.2 教訓に従う)
NCORE_BANDS = [
    ('n_core_2', lambda nc: nc == 2),
    ('n_core_3', lambda nc: nc == 3),
    ('n_core_4_5', lambda nc: 4 <= nc <= 5),
    ('n_core_6plus', lambda nc: nc >= 6),
]


def features_to_matrix(df_subset):
    return df_subset[FEATURE_KEYS].astype(float).values


def z_score_normalize_global(all_matrix):
    mean = all_matrix.mean(axis=0)
    std = all_matrix.std(axis=0)
    std_safe = np.where(std < 1e-9, 1.0, std)
    return (all_matrix - mean) / std_safe, mean, std_safe


def cosine_sim_matrix(A, B):
    if A.shape[0] == 0 or B.shape[0] == 0:
        return np.zeros((A.shape[0], B.shape[0]))
    A_norm = np.linalg.norm(A, axis=1, keepdims=True)
    B_norm = np.linalg.norm(B, axis=1, keepdims=True)
    A_norm_safe = np.where(A_norm < 1e-9, 1.0, A_norm)
    B_norm_safe = np.where(B_norm < 1e-9, 1.0, B_norm)
    return (A / A_norm_safe) @ (B / B_norm_safe).T


def main():
    print('=== v1113 post-process — per-cid / n_core 別層化 ===\n')

    features_path = OUT_DIR / 'cid_features_all.parquet'
    if not features_path.exists():
        print(f'ERROR: {features_path} が存在しない。本実行 (v1113_cid_feature_resonance.py) 完了後に実行する。')
        sys.exit(1)

    df = pd.read_parquet(features_path)
    print(f'features 読み込み: {len(df)} 行')
    print(f'  systems: {df["system"].unique().tolist()}')
    print(f'  per system: {df["system"].value_counts().to_dict()}\n')

    # 全 system 結合行列で z-score 標準化 (本実装と同じ)
    all_matrix = features_to_matrix(df)
    all_matrix_z, z_mean, z_std = z_score_normalize_global(all_matrix)
    df = df.reset_index(drop=True)

    # system 別 z-normalized index 範囲
    system_indices = {}
    for sys_name, group_df in df.groupby('system', sort=False):
        system_indices[sys_name] = group_df.index.values

    # === per-cid 観察 (各 atom CID 別) ===
    print('=' * 60)
    print('per-cid 観察 (各 atom CID 別、real vs null 5 系)')
    print('=' * 60)
    per_cid_rows = []
    for sa in ATOM_SEEDS:
        atom_label = f'atom_{sa}'
        atom_idx = system_indices[atom_label]
        atom_z = all_matrix_z[atom_idx]
        atom_df_sub = df.iloc[atom_idx].reset_index(drop=True)

        real_idx = system_indices['real_other']
        real_z = all_matrix_z[real_idx]

        null_z_list = []
        for ns in NULL_OTHER_SEEDS:
            null_label = f'null_other_{ns}'
            null_idx = system_indices[null_label]
            null_z_list.append((ns, all_matrix_z[null_idx]))

        # 各 atom CID × all real_other CIDs の sim 行列
        sim_real = cosine_sim_matrix(atom_z, real_z)
        # 各 atom CID × all null_other CIDs の sim 行列 (5 系)
        sim_null_per_seed = [cosine_sim_matrix(atom_z, nz) for (_, nz) in null_z_list]

        for i, cid_row in atom_df_sub.iterrows():
            cid = int(cid_row['cid'])
            n_core = float(cid_row['n_core'])
            # real: この atom CID i と全 real_other の sim
            real_sims_i = sim_real[i]
            real_max_i = float(np.max(real_sims_i)) if real_sims_i.size > 0 else 0.0
            real_mean_i = float(np.mean(real_sims_i)) if real_sims_i.size > 0 else 0.0
            # null: 5 系それぞれで max / mean を取る
            null_maxs_i = [float(np.max(sn[i])) if sn[i].size > 0 else 0.0
                           for sn in sim_null_per_seed]
            null_means_i = [float(np.mean(sn[i])) if sn[i].size > 0 else 0.0
                            for sn in sim_null_per_seed]
            null_max_overall = float(max(null_maxs_i)) if null_maxs_i else 0.0
            null_max_mean = float(np.mean(null_maxs_i)) if null_maxs_i else 0.0
            null_mean_overall = float(np.mean(null_means_i)) if null_means_i else 0.0
            # rank: real_max が null 5 系のうち何個の max を超えたか
            rank_max = sum(1 for nm in null_maxs_i if real_max_i > nm)
            # gap (max): real_max - null_max_mean
            gap_max = real_max_i - null_max_mean
            # gap (mean): real_mean - null_mean_overall
            gap_mean = real_mean_i - null_mean_overall

            per_cid_rows.append({
                'atom_seed': sa,
                'cid': cid,
                'n_core': n_core,
                'real_max': real_max_i,
                'real_mean': real_mean_i,
                'null_max_seeds': null_maxs_i,
                'null_max_overall': null_max_overall,
                'null_max_mean': null_max_mean,
                'null_mean_overall': null_mean_overall,
                'rank_max': rank_max,
                'gap_max': gap_max,
                'gap_mean': gap_mean,
                'above_null_max': bool(real_max_i > null_max_overall),
            })

    per_cid_df = pd.DataFrame(per_cid_rows)
    # null_max_seeds は list で parquet に保存しづらいので、文字列化または展開
    per_cid_df['null_max_seeds_str'] = per_cid_df['null_max_seeds'].apply(
        lambda x: ','.join(f'{v:.4f}' for v in x))
    per_cid_df_save = per_cid_df.drop(columns=['null_max_seeds'])
    per_cid_df_save.to_parquet(OUT_DIR / 'per_cid_summary.parquet', index=False)
    print(f'\n保存: per_cid_summary.parquet ({len(per_cid_df)} 行)\n')

    # 統計 (atom 別)
    print('per-cid 集計 (atom 別、CID 単位の rank/gap 分布):')
    for sa in ATOM_SEEDS:
        sub = per_cid_df[per_cid_df['atom_seed'] == sa]
        n_cid = len(sub)
        if n_cid == 0:
            print(f'  atom={sa}: CID 0 個')
            continue
        n_above_max = int(sub['above_null_max'].sum())
        n_rank5 = int((sub['rank_max'] == len(NULL_OTHER_SEEDS)).sum())
        n_rank4 = int((sub['rank_max'] == len(NULL_OTHER_SEEDS) - 1).sum())
        median_rank = float(sub['rank_max'].median())
        mean_gap_max = float(sub['gap_max'].mean())
        print(f'  atom={sa}: n_cid={n_cid}, above_null_max={n_above_max}/{n_cid} '
              f'({100*n_above_max/n_cid:.0f}%), rank=5/5: {n_rank5}, rank=4/5: {n_rank4}, '
              f'median rank={median_rank:.1f}, mean gap_max={mean_gap_max:+.4f}')

    # === n_core 別層化 (v10.2 哲学) ===
    print('\n' + '=' * 60)
    print('n_core 別層化 (v10.2 集団平均の罠回避)')
    print('=' * 60)
    ncore_rows = []
    for sa in ATOM_SEEDS:
        sub_atom = per_cid_df[per_cid_df['atom_seed'] == sa]
        for band_name, band_fn in NCORE_BANDS:
            sub_band = sub_atom[sub_atom['n_core'].apply(band_fn)]
            n_cid = len(sub_band)
            if n_cid == 0:
                ncore_rows.append({
                    'atom_seed': sa, 'ncore_band': band_name, 'n_cid': 0,
                    'above_null_max_ratio': 0.0, 'mean_real_max': 0.0,
                    'mean_null_max': 0.0, 'mean_gap_max': 0.0, 'median_rank': 0.0,
                })
                continue
            ncore_rows.append({
                'atom_seed': sa, 'ncore_band': band_name, 'n_cid': n_cid,
                'above_null_max_ratio': float(sub_band['above_null_max'].mean()),
                'mean_real_max': float(sub_band['real_max'].mean()),
                'mean_null_max': float(sub_band['null_max_mean'].mean()),
                'mean_gap_max': float(sub_band['gap_max'].mean()),
                'median_rank': float(sub_band['rank_max'].median()),
            })

    ncore_df = pd.DataFrame(ncore_rows)
    ncore_df.to_parquet(OUT_DIR / 'ncore_summary.parquet', index=False)
    print(f'\n保存: ncore_summary.parquet ({len(ncore_df)} 行)')

    print('\nn_core 別 (atom × band):')
    pivot = ncore_df.pivot(index='ncore_band', columns='atom_seed', values='above_null_max_ratio')
    print('above_null_max_ratio (CID 単位、real_max が null 5 系の max を超えた割合):')
    print(pivot.to_string())
    print('\nn_cid (各 band の CID 数):')
    pivot_n = ncore_df.pivot(index='ncore_band', columns='atom_seed', values='n_cid')
    print(pivot_n.to_string())
    print('\nmean_gap_max (real_max - null_max_mean、CID 単位平均):')
    pivot_g = ncore_df.pivot(index='ncore_band', columns='atom_seed', values='mean_gap_max')
    print(pivot_g.to_string())

    # === 上位 sim ペア (per atom、上位 10 個) ===
    print('\n' + '=' * 60)
    print('上位 sim ペア (per atom、real vs real_other、上位 10)')
    print('=' * 60)
    top_sim_rows = []
    for sa in ATOM_SEEDS:
        atom_label = f'atom_{sa}'
        atom_idx = system_indices[atom_label]
        atom_z = all_matrix_z[atom_idx]
        atom_df_sub = df.iloc[atom_idx].reset_index(drop=True)
        real_idx = system_indices['real_other']
        real_z = all_matrix_z[real_idx]
        real_df_sub = df.iloc[real_idx].reset_index(drop=True)

        sim_real = cosine_sim_matrix(atom_z, real_z)
        if sim_real.size == 0:
            continue
        flat_idx = np.argsort(sim_real.flatten())[::-1][:10]  # 上位 10
        for rank, fi in enumerate(flat_idx):
            i, j = np.unravel_index(fi, sim_real.shape)
            sim_val = float(sim_real[i, j])
            atom_cid = int(atom_df_sub.iloc[i]['cid'])
            real_cid = int(real_df_sub.iloc[j]['cid'])
            # 特性次元分解 (各次元の積、cosine 寄与)
            atom_v = atom_z[i]
            real_v = real_z[j]
            atom_norm = float(np.linalg.norm(atom_v)) if np.linalg.norm(atom_v) > 1e-9 else 1.0
            real_norm = float(np.linalg.norm(real_v)) if np.linalg.norm(real_v) > 1e-9 else 1.0
            per_dim_contribution = (atom_v * real_v) / (atom_norm * real_norm)
            # 上位 3 次元
            top3_idx = np.argsort(np.abs(per_dim_contribution))[::-1][:3]
            top3_dims = [(FEATURE_KEYS[k], float(per_dim_contribution[k])) for k in top3_idx]
            top_sim_rows.append({
                'atom_seed': sa, 'rank': rank + 1,
                'atom_cid': atom_cid, 'real_other_cid': real_cid,
                'sim': sim_val,
                'atom_n_core': float(atom_df_sub.iloc[i]['n_core']),
                'real_other_n_core': float(real_df_sub.iloc[j]['n_core']),
                'top3_dims_str': ', '.join(f'{n}={v:+.3f}' for n, v in top3_dims),
            })

    top_sim_df = pd.DataFrame(top_sim_rows)
    top_sim_df.to_parquet(OUT_DIR / 'top_sim_pairs.parquet', index=False)
    print(f'\n保存: top_sim_pairs.parquet ({len(top_sim_df)} 行)')
    print('\n上位 sim ペア (per atom):')
    for sa in ATOM_SEEDS:
        sub = top_sim_df[top_sim_df['atom_seed'] == sa]
        print(f'\n  atom={sa}:')
        for _, row in sub.iterrows():
            print(f'    [{row["rank"]:2d}] atom_cid={row["atom_cid"]} '
                  f'(n_core={row["atom_n_core"]:.0f}) × '
                  f'real_cid={row["real_other_cid"]} '
                  f'(n_core={row["real_other_n_core"]:.0f}): '
                  f'sim={row["sim"]:.4f} | top3={row["top3_dims_str"]}')

    # === サマリ JSON ===
    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'design': 'v1113_postprocess_per_cid',
        'ATOM_SEEDS': ATOM_SEEDS,
        'OTHER_SEED_FIXED': OTHER_SEED_FIXED,
        'NULL_OTHER_SEEDS': NULL_OTHER_SEEDS,
        'NCORE_BANDS': [name for name, _ in NCORE_BANDS],
        'per_atom_summary': [],
    }
    for sa in ATOM_SEEDS:
        sub = per_cid_df[per_cid_df['atom_seed'] == sa]
        if len(sub) == 0:
            continue
        summary['per_atom_summary'].append({
            'atom_seed': sa,
            'n_cid_total': len(sub),
            'n_above_null_max': int(sub['above_null_max'].sum()),
            'pct_above_null_max': float(sub['above_null_max'].mean() * 100),
            'n_rank_5': int((sub['rank_max'] == len(NULL_OTHER_SEEDS)).sum()),
            'n_rank_4': int((sub['rank_max'] == len(NULL_OTHER_SEEDS) - 1).sum()),
            'median_rank': float(sub['rank_max'].median()),
            'mean_gap_max': float(sub['gap_max'].mean()),
            'max_gap_max': float(sub['gap_max'].max()),
        })

    (OUT_DIR / 'per_cid_summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print('\n=== post-process 完了 ===')


if __name__ == '__main__':
    main()
