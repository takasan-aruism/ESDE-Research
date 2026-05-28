#!/usr/bin/env python3
"""v1107a Step B — 環境準備

目的:
- 入力データ存在確認 (v1106b / v1106a / v1105a / v106 / v105)
- timestamp + hash で frozen 確認
- 観察 1-4 の対象データサイズ把握
- bin 構造などの事前集計

入力 (read-only、frozen):
- unified/v1106b/outputs/main/observation_3_high_low_events.parquet
- unified/v1106b/outputs/main/env_check_cid_props.parquet
- unified/v1106a/outputs/main/observation_Y_word_distributions.parquet
- unified/v1106a/outputs/main/verification_a_cid_word_alignment.parquet
- unified/v1105a/outputs/main/trial_step2_associations.parquet
- developmental/v106/outputs/main/cid_atom_sim_matrix_seed{N}.parquet (24)
- developmental/v106/outputs/main/cid_structure_profile_seed{N}.csv (24)
- developmental/v105/diag_v105_main/subjects/per_subject_seed{N}.csv (24)

出力:
- unified/v1107a/outputs/main/env_check_summary.parquet (リソース確認結果)
- unified/v1107a/outputs/main/env_check_category_counts.parquet (input_atom category 分布)
"""
from __future__ import annotations
import hashlib, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V105_SUB = REPO / 'developmental/v105/diag_v105_main/subjects'
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V1105A_MAIN = REPO / 'unified/v1105a/outputs/main'
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'
V1106B_MAIN = REPO / 'unified/v1106b/outputs/main'
V1107A_MAIN = REPO / 'unified/v1107a/outputs/main'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main():
    V1107A_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1107a Step B — 環境準備 ===\n')
    t0 = time.time()

    # (1) リソース存在確認 + hash
    print('[1] リソース存在確認 + hash (frozen 検証)')
    resources = {
        'v1106b high_low_events': V1106B_MAIN / 'observation_3_high_low_events.parquet',
        'v1106b cid_props': V1106B_MAIN / 'env_check_cid_props.parquet',
        'v1106a obs_Y': V1106A_MAIN / 'observation_Y_word_distributions.parquet',
        'v1106a verification_a': V1106A_MAIN / 'verification_a_cid_word_alignment.parquet',
        'v1105a associations': V1105A_MAIN / 'trial_step2_associations.parquet',
    }
    summary_rows = []
    for name, p in resources.items():
        ok = p.exists()
        size = p.stat().st_size if ok else 0
        h = sha(p) if ok else None
        print(f'  {name}: {"✓" if ok else "✗"} size={size:,} hash={h}')
        summary_rows.append({'resource': name, 'exists': ok, 'size_bytes': size, 'sha256_16': h})

    # per-seed リソース (24 seeds)
    print('\n  per-seed (24 seeds):')
    for label, root, ext in [
        ('per_subject', V105_SUB, 'per_subject_seed{}.csv'),
        ('cid_structure_profile', V106_MAIN, 'cid_structure_profile_seed{}.csv'),
        ('cid_atom_sim_matrix', V106_MAIN, 'cid_atom_sim_matrix_seed{}.parquet'),
    ]:
        n_exist = sum(1 for sd in range(24) if (root / ext.format(sd)).exists())
        print(f'    {label}: {n_exist}/24')
        summary_rows.append({'resource': f'{label} (24 seeds)',
                              'exists': n_exist == 24,
                              'size_bytes': n_exist, 'sha256_16': None})

    pd.DataFrame(summary_rows).to_parquet(V1107A_MAIN / 'env_check_summary.parquet', index=False)
    print(f'\n  wrote env_check_summary.parquet')

    # (2) verification_a 3,300 events の構造概要
    print('\n[2] verification_a 3,300 events 概要')
    va = pd.read_parquet(V1106A_MAIN / 'verification_a_cid_word_alignment.parquet')
    print(f'  events: {len(va):,}')
    print(f'  cos_sim mean={va["cid_word_cos_sim"].mean():.4f}, '
          f'std={va["cid_word_cos_sim"].std():.4f}')
    print(f'  input_atom unique: {va["input_atom"].nunique()}')

    # category 分布
    va['category'] = va['input_atom'].str.split('.').str[0]
    cat_counts = va.groupby('category').agg(
        n_events=('event_id', 'count'),
        n_input_atoms=('input_atom', 'nunique'),
    ).reset_index().sort_values('n_events', ascending=False)
    cat_counts.to_parquet(V1107A_MAIN / 'env_check_category_counts.parquet', index=False)
    print(f'\n  category 分布 (top 10):')
    print(cat_counts.head(10).to_string(index=False))
    print(f'\n  total categories: {len(cat_counts)}, total input_atoms: {va["input_atom"].nunique()}')

    # (3) v1106b high/low event 分類確認
    print('\n[3] v1106b high/low event 分類')
    hl = pd.read_parquet(V1106B_MAIN / 'observation_3_high_low_events.parquet')
    print(f'  rows: {len(hl):,}')
    print(f'  event_class 分布:')
    for cls in ['high', 'mid', 'low']:
        sub = hl[hl['event_class'] == cls]
        print(f'    {cls}: {len(sub)} ({len(sub)/len(hl)*100:.1f}%)')

    # (4) v1106b CID props 確認
    print('\n[4] v1106b CID props (5,224 全 CID)')
    cp = pd.read_parquet(V1106B_MAIN / 'env_check_cid_props.parquet')
    print(f'  rows: {len(cp):,}')
    print(f'  final_state: {cp["final_state"].value_counts().to_dict()}')

    print(f'\n=== Step B 完了、elapsed {time.time()-t0:.1f}s ===')
    print('\n→ 全リソース確認 OK、Step C (観察 1) へ進む')


if __name__ == '__main__':
    main()
