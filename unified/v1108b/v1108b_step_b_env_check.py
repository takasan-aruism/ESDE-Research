#!/usr/bin/env python3
"""v1108b Step B — 環境準備 (24 category × 全 325 atom 選定、Taka 承認 案 B)

物理層 frozen 規律厳密維持:
- v1106b/v1107 は read-only
- 新規ファイルは unified/v1108b/ 配下のみ

24 category × 全 325 atom (案 B) を input 試行対象として登録。
v1107c で 19 不在 cat 216 atom + v1107a 5 cat 109 atom = 325 atom (FND.spaceless 除く)

出力:
- unified/v1108b/outputs/main/env_check_atom_selection.parquet (325 atom × category)
- unified/v1108b/outputs/main/env_check_summary.parquet
"""
from __future__ import annotations
import hashlib, json, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V105_SUB = REPO / 'developmental/v105/diag_v105_main/subjects'
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V1103_MAIN = REPO / 'unified/v1103/outputs/main'
V1106B_MAIN = REPO / 'unified/v1106b/outputs/main'
V1107A_MAIN = REPO / 'unified/v1107a/outputs/main'
V1107B_MAIN = REPO / 'unified/v1107b/outputs/main'
V1107C_MAIN = REPO / 'unified/v1107c/outputs/main'
V1108B_MAIN = REPO / 'unified/v1108b/outputs/main'
MAPPER_DIR = REPO / 'language/lexicon/data/mapper_output'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main():
    V1108B_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1108b Step B — 環境準備 (24 cat × 全 325 atom、案 B) ===\n')
    t0 = time.time()

    # (1) リソース存在 + frozen hash
    print('[1] リソース存在 + frozen hash')
    resources = {
        'v106 axes_metadata': V106_MAIN / 'axes_metadata.json',
        'v1103 atom_centroids': V1103_MAIN / 'atom_centroids_48d_raw.parquet',
        'v1106b cid_props': V1106B_MAIN / 'env_check_cid_props.parquet',
        'v1107a cluster_profiles': V1107A_MAIN / 'observation_4_cluster_profiles.parquet',
        'v1107a category_to_cluster': V1107A_MAIN / 'observation_4_category_to_cluster.parquet',
        'v1107b axis_contribution': V1107B_MAIN / 'observation_2_axis_contribution.parquet',
        'v1107c cluster_assignment': V1107C_MAIN / 'cluster_assignment.parquet',
        'v1107c all_24_cats': V1107C_MAIN / 'all_24_category_comparison.parquet',
    }
    rsrc_rows = []
    for k, p in resources.items():
        ok = p.exists()
        size = p.stat().st_size if ok else 0
        h = sha(p) if ok else None
        print(f'  {k}: {"✓" if ok else "✗"} hash={h}')
        rsrc_rows.append({'resource': k, 'exists': ok, 'size_bytes': size, 'sha256_16': h})

    # per-seed
    n_cid_atom_sim = sum(1 for sd in range(24)
                          if (V106_MAIN / f'cid_atom_sim_matrix_seed{sd}.parquet').exists())
    n_cid_struct = sum(1 for sd in range(24)
                        if (V106_MAIN / f'cid_structure_profile_seed{sd}.csv').exists())
    n_per_sub = sum(1 for sd in range(24)
                     if (V105_SUB / f'per_subject_seed{sd}.csv').exists())
    print(f'  per-seed: cid_atom_sim {n_cid_atom_sim}/24, cid_struct {n_cid_struct}/24, '
          f'per_subject {n_per_sub}/24')

    n_mapper = len(list(MAPPER_DIR.glob('*_a1.jsonl')))
    print(f'  mapper_output: {n_mapper} files (期待 325)')

    # (2) 24 category × 全 325 atom 登録 (案 B)
    print('\n[2] 24 category × 全 325 atom 登録 (Taka 承認 案 B)')
    d = json.load(open(REPO/'language/atoms/esde_dictionary.json'))
    # mapper_output 存在 atom のみ採用 (FND.spaceless 除外)
    mapper_atoms = {f.stem.replace('_a1', '').replace('_', '.', 1)
                     for f in MAPPER_DIR.glob('*_a1.jsonl')}

    atom_rows = []
    for atom_full in d['concepts'].keys():
        cat = atom_full.split('.')[0]
        in_mapper = atom_full in mapper_atoms
        atom_rows.append({
            'category': cat,
            'atom_full': atom_full,
            'atom_name': atom_full.split('.', 1)[1],
            'in_mapper_output': in_mapper,
        })
    atom_df = pd.DataFrame(atom_rows)
    # mapper にあるもののみ実 input 試行対象
    selected = atom_df[atom_df['in_mapper_output']].copy()
    selected.to_parquet(V1108B_MAIN / 'env_check_atom_selection.parquet', index=False)
    print(f'  esde_dictionary atoms: {len(atom_df)}')
    print(f'  mapper_output 存在 atoms: {len(selected)} (FND.spaceless 除く)')
    print(f'  category 別 atom 数:')
    cat_count = selected.groupby('category').size().reset_index(name='n_atoms').sort_values(
        'n_atoms', ascending=False)
    print(cat_count.to_string(index=False))

    # (3) summary
    sum_df = pd.DataFrame([{
        'n_total_atoms_in_dict': len(atom_df),
        'n_input_atoms_selected': len(selected),
        'n_categories': selected['category'].nunique(),
        'min_atoms_per_cat': int(cat_count['n_atoms'].min()),
        'max_atoms_per_cat': int(cat_count['n_atoms'].max()),
        'mean_atoms_per_cat': float(cat_count['n_atoms'].mean()),
        'physics_frozen_v1106b_readonly': True,
        'output_dir_only': 'unified/v1108b/outputs/main/',
        'elapsed_sec': round(time.time() - t0, 2),
    }])
    sum_df.to_parquet(V1108B_MAIN / 'env_check_summary.parquet', index=False)

    pd.DataFrame(rsrc_rows).to_parquet(V1108B_MAIN / 'env_check_resources.parquet', index=False)

    print(f'\n=== Step B 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
