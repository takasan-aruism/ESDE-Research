#!/usr/bin/env python3
"""v1107b Step B — 環境準備

目的:
- 入力データ存在確認 (v1106b / v1106a / v1103 / v106 / v105 / mapper_output)
- axes_metadata 読み込み + 48 軸構造確認
- atom_centroids + mapper_output サイズ確認
- 軸間 cosine sim マトリクス事前計算 (観察 1 入力)

入力 (read-only、frozen):
- developmental/v106/outputs/main/axes_metadata.json
- unified/v1103/outputs/main/atom_centroids_48d_raw.parquet
- language/lexicon/data/mapper_output/*_a1.jsonl
- unified/v1106b/outputs/main/observation_3_high_low_events.parquet
- unified/v1106a/outputs/main/observation_Y_word_distributions.parquet
- unified/v1106a/outputs/main/verification_a_cid_word_alignment.parquet
- unified/v1105a/outputs/main/trial_step2_associations.parquet
- developmental/v106/outputs/main/cid_structure_profile_seed{N}.csv (24)

出力:
- unified/v1107b/outputs/main/env_check_summary.parquet
- unified/v1107b/outputs/main/env_check_axes_meta.parquet (48 axes 構造)
- unified/v1107b/outputs/main/axes_correlation_matrix.parquet (軸間 corr、観察 1 入力)
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
V1105A_MAIN = REPO / 'unified/v1105a/outputs/main'
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'
V1106B_MAIN = REPO / 'unified/v1106b/outputs/main'
V1107B_MAIN = REPO / 'unified/v1107b/outputs/main'
MAPPER_DIR = REPO / 'language/lexicon/data/mapper_output'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main():
    V1107B_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1107b Step B — 環境準備 ===\n')
    t0 = time.time()

    # (1) リソース存在確認
    print('[1] リソース存在確認')
    resources = {
        'v106 axes_metadata': V106_MAIN / 'axes_metadata.json',
        'v1103 atom_centroids': V1103_MAIN / 'atom_centroids_48d_raw.parquet',
        'v1106b high_low_events': V1106B_MAIN / 'observation_3_high_low_events.parquet',
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

    n_mapper = len(list(MAPPER_DIR.glob('*_a1.jsonl')))
    print(f'  mapper_output: {n_mapper} files (期待 325)')
    summary_rows.append({'resource': 'mapper_output (325 files)',
                          'exists': n_mapper == 325, 'size_bytes': n_mapper, 'sha256_16': None})

    n_cid_struct = sum(1 for sd in range(24)
                        if (V106_MAIN / f'cid_structure_profile_seed{sd}.csv').exists())
    print(f'  cid_structure_profile: {n_cid_struct}/24')

    pd.DataFrame(summary_rows).to_parquet(V1107B_MAIN / 'env_check_summary.parquet', index=False)

    # (2) axes_metadata 構造確認
    print('\n[2] 48 axes 構造確認')
    am = json.load(open(V106_MAIN / 'axes_metadata.json'))
    axes_rows = []
    axes_flat = []
    for ax in am['axes_order']:
        for lvl in ax['level_names']:
            axes_flat.append(f'{ax["name"]}.{lvl}')
            axes_rows.append({
                'axis_group': ax['name'],
                'n_levels': ax['n_levels'],
                'level': lvl,
                'axis_full': f'{ax["name"]}.{lvl}',
            })
    print(f'  total axes: {len(axes_flat)}')
    for ax in am['axes_order']:
        print(f'  {ax["name"]} ({ax["n_levels"]}): {", ".join(ax["level_names"])}')

    pd.DataFrame(axes_rows).to_parquet(V1107B_MAIN / 'env_check_axes_meta.parquet', index=False)

    # (3) atom_centroids 48d データ
    print('\n[3] atom_centroids_48d 48 軸データ')
    ac = pd.read_parquet(V1103_MAIN / 'atom_centroids_48d_raw.parquet')
    centroids = ac[axes_flat].values  # (325, 48)
    print(f'  atoms: {ac.shape[0]}, axes: {len(axes_flat)}')
    print(f'  centroid value range: {centroids.min():.3f} - {centroids.max():.3f}')

    # (4) 軸間 cosine sim マトリクス事前計算 (観察 1 で使用)
    print('\n[4] 軸間 cosine sim マトリクス (48 × 48)')
    # 各軸を 325 atom にわたる値ベクトルとして見る
    axis_vecs = centroids.T  # (48, 325)
    # cosine sim
    norms = np.linalg.norm(axis_vecs, axis=1, keepdims=True)
    normalized = axis_vecs / np.where(norms > 0, norms, 1.0)
    corr = normalized @ normalized.T  # (48, 48)
    corr_df = pd.DataFrame(corr, index=axes_flat, columns=axes_flat)
    corr_df.to_parquet(V1107B_MAIN / 'axes_correlation_matrix.parquet')
    print(f'  軸間 cosine sim: mean={corr[np.triu_indices_from(corr, k=1)].mean():.4f}, '
          f'min={corr[np.triu_indices_from(corr, k=1)].min():.4f}, '
          f'max={corr[np.triu_indices_from(corr, k=1)].max():.4f}')

    # axis_group 内 vs 群間 cos_sim
    print(f'\n  軸 group 内 vs 群間 cos_sim 比較:')
    group_of = {f'{ax["name"]}.{lvl}': ax['name']
                  for ax in am['axes_order'] for lvl in ax['level_names']}
    intra = []
    inter = []
    for i in range(len(axes_flat)):
        for j in range(i+1, len(axes_flat)):
            if group_of[axes_flat[i]] == group_of[axes_flat[j]]:
                intra.append(corr[i, j])
            else:
                inter.append(corr[i, j])
    print(f'    intra-group (同 group 内): mean={np.mean(intra):.4f}, n={len(intra)}')
    print(f'    inter-group (異 group 間): mean={np.mean(inter):.4f}, n={len(inter)}')

    # (5) Gemini 仮説軸照合 (再確認)
    print('\n[5] Gemini 仮説軸の実環境照合 (Q4 段階 1 入力)')
    gemini_hypothesis = {
        'Micro_candidate': ['temporal.immediate', 'scale.individual'],
        'Meso_candidate': ['interconnection.independent', 'interconnection.catalytic',
                            'interconnection.chained', 'interconnection.synchronous',
                            'interconnection.resonant',
                            'resonance.superficial', 'resonance.structural',
                            'resonance.essential', 'resonance.existential'],
        'Macro_candidate': ['ontological.entirety', 'experience.integrated'],
    }
    for scale, cands in gemini_hypothesis.items():
        existing = [c for c in cands if c in axes_flat]
        missing = [c for c in cands if c not in axes_flat]
        print(f'  {scale}: 実在 {len(existing)}/{len(cands)}, 不在 {missing}')

    print(f'\n=== Step B 完了、elapsed {time.time()-t0:.1f}s ===')
    print('\n→ 全リソース確認 OK、Step C (観察 1) へ進む')


if __name__ == '__main__':
    main()
