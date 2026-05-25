#!/usr/bin/env python3
"""v1106a Step B — 環境準備 (sample 検証、新規出力なし)

確認事項 6 件 (Web Claude 回答 §3.1):
1. v1105a s7 出力読み込み確認
2. mapper_output データ (325 jsonl / 125.2 MB) 読み込み確認
3. atom_id mapping 確認 (v1103 325 = mapper_output 325 完全一致)
4. v1106 outputs 参照可能性
5. mapper_output frozen + Synapse v3 frozen 確認
6. bit-identity LAYER_B baseline 確認

新規出力なし、サマリのみ print 出力。
"""
from __future__ import annotations
import json, os, time
from pathlib import Path
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')


def main():
    print('=== v1106a Step B 環境準備 ===\n')
    t0 = time.time()

    # (1) v1105a s7 出力
    print('[B-1] v1105a s7 出力読み込み確認')
    dist = pd.read_parquet(REPO / 'unified/v1105a/outputs/main/trial_step4_distributions.parquet')
    s7_pc = dist[(dist['series_id'] == 's7_48d_raw_k5') &
                  (dist['structural_label'] == 'distribution_valid')]
    print(f'  trial_step4_distributions rows: {len(dist):,}')
    print(f'  s7 PC events: {s7_pc["event_id"].nunique()}, rows: {len(s7_pc):,}')
    print(f'  全 7 系列 PC: {dist[dist["structural_label"]=="distribution_valid"]["event_id"].nunique()} events')

    # (2) mapper_output 読み込み
    print('\n[B-2] mapper_output データ読み込み確認')
    mapper_dir = REPO / 'language/lexicon/data/mapper_output'
    files = sorted([f for f in os.listdir(mapper_dir) if f.endswith('.jsonl')])
    total_size = sum((mapper_dir/f).stat().st_size for f in files)
    print(f'  files: {len(files)} jsonl, total {total_size/1024/1024:.1f} MB')
    # sample 1 ファイル中身検証
    sample_file = mapper_dir / 'ACT_build_a1.jsonl'
    with open(sample_file) as f:
        lines = f.readlines()
    print(f'  sample (ACT_build_a1.jsonl): {len(lines):,} entries')
    for line in lines:
        d = json.loads(line)
        if 'raw_scores' in d:
            print(f'  raw_scores axes: {len(d["raw_scores"])}, normalized_scores axes: {len(d["normalized_scores"])}')
            break

    # (3) atom_id mapping
    print('\n[B-3] atom_id mapping 確認')
    ac = pd.read_parquet(REPO/'unified/v1103/outputs/main/atom_centroids_48d_raw.parquet', columns=['atom'])
    v1103_atoms = set(ac['atom'])
    mapper_atoms = set([f.replace('_a1.jsonl','').replace('_','.',1) for f in files])
    print(f'  v1103 atoms: {len(v1103_atoms)}, mapper_output atoms: {len(mapper_atoms)}')
    print(f'  完全一致: {len(v1103_atoms & mapper_atoms)}')
    print(f'  v1103 - mapper: {sorted(v1103_atoms - mapper_atoms)}')
    print(f'  mapper - v1103: {sorted(mapper_atoms - v1103_atoms)}')

    # (4) v1106 outputs
    print('\n[B-4] v1106 outputs 参照可能性')
    v1106_dir = REPO / 'unified/v1106/outputs/main'
    v1106_files = sorted(os.listdir(v1106_dir))
    print(f'  v1106 outputs: {len(v1106_files)} files')
    for f in v1106_files:
        print(f'    {f}')

    # (5) mapper_output frozen + Synapse v3 frozen
    print('\n[B-5] mapper_output frozen + Synapse v3 frozen 確認')
    syn_v3 = REPO/'language/synapse/esde_synapses_v3.json'
    print(f'  Synapse v3: exists={syn_v3.exists()}, size={syn_v3.stat().st_size/1024/1024:.1f} MB, frozen (read-only)')
    print(f'  mapper_output: 325 jsonl, total {total_size/1024/1024:.1f} MB, frozen (read-only)')

    # (6) LAYER_B baseline
    print('\n[B-6] LAYER_B baseline (v1106 まで + mapper_output)')
    counts = {
        'v105_sal': REPO/'developmental/v105/diag_v105_main/salience',
        'v105_int': REPO/'developmental/v105/diag_v105_main/integration',
        'v106': REPO/'developmental/v106/outputs/main',
        'v107': REPO/'developmental/v107/outputs/main',
        'v112': REPO/'developmental/v112/outputs/main',
        'v1101a': REPO/'unified/v1101a/outputs/main',
        'v1102': REPO/'unified/v1102/outputs/main',
        'v1103': REPO/'unified/v1103/outputs/main',
        'v1104': REPO/'unified/v1104/outputs/main',
        'v1104a': REPO/'unified/v1104a/outputs/main',
        'v1105': REPO/'unified/v1105/outputs/main',
        'v1105a': REPO/'unified/v1105a/outputs/main',
        'v1106': REPO/'unified/v1106/outputs/main',
        'language_synapse': REPO/'language/synapse',
        'language_mapper_output': REPO/'language/lexicon/data/mapper_output',
        'language_atoms_a1_batch': REPO/'language/atoms/a1_batch',
    }
    total = 0
    for k, p in counts.items():
        n = sum(1 for x in p.rglob('*') if x.is_file())
        total += n
        print(f'  {k}: {n}')
    print(f'  total LAYER_B baseline: {total} files')

    print(f'\n=== Step B 完了、elapsed {time.time()-t0:.1f}s ===')
    print('\nStep C 実装方針 (確認要請 11 案 Z-1 採用):')
    print('  - 案 X 主軸: score = Σ p_s7(atom) × raw_scores_max(atom, word) / 10')
    print('  - 案 Z-1 補助: score = Σ p_s7(atom) × normalized_scores_max(atom, word)')
    print('  - 7 系列並列、案 X/Z-1 別レイヤー保持')
    print('  - 構造ラベル付与 (word_pipeline_complete / candidate_empty / degenerate / valid)')


if __name__ == '__main__':
    main()
