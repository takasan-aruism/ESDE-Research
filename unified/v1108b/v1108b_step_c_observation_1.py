#!/usr/bin/env python3
"""v1108b Step C — 観察 1: 24 cat × 全 325 atom input 励起と参照 CID profile 測定

v1107c 枠組み流用、全 325 atom (案 B、Taka 承認) を input として明示的励起。
各 atom × 24 seeds × top-5 CID で参照 CID の物理量分布を測定。

入力 (read-only frozen):
- v106 cid_atom_sim_matrix_seed{N}.parquet (24 seeds)
- v105 per_subject_seed{N}.csv (24 seeds)
- unified/v1108b/outputs/main/env_check_atom_selection.parquet

出力:
- unified/v1108b/outputs/main/observation_1_atom_profiles.parquet (325 atom × CID profile)
- unified/v1108b/outputs/main/observation_1_category_profiles.parquet (24 cat 集約)
- unified/v1108b/outputs/main/observation_1_summary.parquet
"""
from __future__ import annotations
import time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V105_SUB = REPO / 'developmental/v105/diag_v105_main/subjects'
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V1108B_MAIN = REPO / 'unified/v1108b/outputs/main'

TOP_K_CID = 5


def main():
    print('=== v1108b Step C — 観察 1: 24 cat × 全 325 atom 励起 ===\n')
    t0 = time.time()

    sel = pd.read_parquet(V1108B_MAIN / 'env_check_atom_selection.parquet')
    atoms = sel['atom_full'].tolist()
    print(f'  input atoms: {len(atoms)}')

    # CID 物理量 (24 seeds)
    print('\n[1] CID 物理量読み込み')
    cid_props = {}
    for sd in range(24):
        df = pd.read_csv(V105_SUB / f'per_subject_seed{sd}.csv',
                          usecols=['cognitive_id', 'final_state',
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

    # atom 別 input 励起と参照 CID profile
    print(f'\n[2] 各 atom × 24 seeds × top-{TOP_K_CID} CID 取得')
    raw_rows = []
    for i, atom in enumerate(atoms):
        if (i+1) % 50 == 0:
            print(f'  processed {i+1}/{len(atoms)}, elapsed {time.time()-t0:.1f}s')
        for sd in range(24):
            sim_df = pd.read_parquet(V106_MAIN / f'cid_atom_sim_matrix_seed{sd}.parquet',
                                       columns=['cid', atom])
            sim_df = sim_df.sort_values(atom, ascending=False).head(TOP_K_CID)
            for _, r in sim_df.iterrows():
                cid = int(r['cid'])
                if (sd, cid) not in cid_props:
                    continue
                p = cid_props[(sd, cid)]
                raw_rows.append({
                    'input_atom': atom,
                    'category': atom.split('.')[0],
                    'seed': sd, 'cid': cid,
                    'sim_to_atom': float(r[atom]),
                    'final_state': p['final_state'],
                    'last_familiarity_max': p['last_familiarity_max'],
                    'n_alphas_currently': p['n_alphas_currently'],
                    'current_stability': p['current_stability'],
                    'current_social': p['current_social'],
                })
    raw_df = pd.DataFrame(raw_rows)
    print(f'  total rows: {len(raw_df):,}')

    # atom 別集計 (325 atom)
    print('\n[3] 325 atom × CID profile 集計')
    atom_profiles = []
    for atom in atoms:
        sub = raw_df[raw_df['input_atom'] == atom]
        if len(sub) == 0:
            continue
        fs_counts = sub['final_state'].value_counts(normalize=True).to_dict()
        prof = {
            'input_atom': atom,
            'category': atom.split('.')[0],
            'n_top_cid_obs': len(sub),
            'pct_hosted': float(fs_counts.get('hosted', 0)),
            'pct_ghost': float(fs_counts.get('ghost', 0)),
            'pct_reaped': float(fs_counts.get('reaped', 0)),
        }
        for col in ['last_familiarity_max', 'n_alphas_currently',
                      'current_stability', 'current_social']:
            valid = sub[col].dropna()
            prof[f'{col}_mean'] = float(valid.mean()) if len(valid) > 0 else 0.0
            prof[f'{col}_std'] = float(valid.std()) if len(valid) > 1 else 0.0
        atom_profiles.append(prof)
    atom_df = pd.DataFrame(atom_profiles)
    atom_df.to_parquet(V1108B_MAIN / 'observation_1_atom_profiles.parquet', index=False)
    print(f'  wrote observation_1_atom_profiles.parquet ({len(atom_df)} atoms)')

    # category 別集計 (24 cat)
    print('\n[4] 24 cat × CID profile 集計 (atom 内平均)')
    cat_profiles = []
    for cat in sorted(atom_df['category'].unique()):
        sub = atom_df[atom_df['category'] == cat]
        prof = {
            'category': cat,
            'n_atoms': len(sub),
            'pct_hosted_mean': float(sub['pct_hosted'].mean()),
            'pct_hosted_std': float(sub['pct_hosted'].std()),
            'pct_reaped_mean': float(sub['pct_reaped'].mean()),
            'last_familiarity_max_mean': float(sub['last_familiarity_max_mean'].mean()),
            'n_alphas_currently_mean': float(sub['n_alphas_currently_mean'].mean()),
            'current_social_mean': float(sub['current_social_mean'].mean()),
            'current_stability_mean': float(sub['current_stability_mean'].mean()),
            # atom 内分散も記録 (input 効果の指標)
            'familiarity_atom_var': float(sub['last_familiarity_max_mean'].var()),
            'n_alphas_atom_var': float(sub['n_alphas_currently_mean'].var()),
        }
        cat_profiles.append(prof)
    cat_df = pd.DataFrame(cat_profiles).sort_values('current_social_mean', ascending=False)
    cat_df.to_parquet(V1108B_MAIN / 'observation_1_category_profiles.parquet', index=False)
    print(f'  wrote observation_1_category_profiles.parquet ({len(cat_df)} categories)')

    print('\n--- 24 category × 参照 CID profile (social 順) ---')
    print(cat_df[['category', 'n_atoms', 'pct_hosted_mean', 'pct_reaped_mean',
                    'last_familiarity_max_mean', 'n_alphas_currently_mean',
                    'current_social_mean']].round(3).to_string(index=False))

    # summary
    sum_df = pd.DataFrame([{
        'n_atoms_processed': int(len(atom_df)),
        'n_categories': int(cat_df['category'].nunique()),
        'n_total_observations': int(len(raw_df)),
        'social_max_category': str(cat_df.iloc[0]['category']),
        'social_max_value': float(cat_df['current_social_mean'].max()),
        'social_min_category': str(cat_df.iloc[-1]['category']),
        'social_min_value': float(cat_df['current_social_mean'].min()),
        'social_range': float(cat_df['current_social_mean'].max() - cat_df['current_social_mean'].min()),
        'elapsed_sec': round(time.time() - t0, 2),
    }])
    sum_df.to_parquet(V1108B_MAIN / 'observation_1_summary.parquet', index=False)

    print(f'\n=== Step C 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
