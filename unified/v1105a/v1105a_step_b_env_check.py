#!/usr/bin/env python3
"""v1105a Step B — 環境準備 (sample 検証、新規出力なし)

確認事項:
1. v108_standard 60,000 events 全 24 seeds 読み込み確認
2. per-atom trajectory_stability 計算源 (v1101a attention_emit + v106 cid_atom_sim_matrix)
3. per-atom density 計算源 (v1103 atom_centroids_48d_raw/norm)
4. atom_id (string) ↔ attention_candidate_id (int) マッピング
5. LAYER_B baseline (v1105 まで)

新規出力なし、サマリのみ print 出力。
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')


def main():
    print('=== v1105a Step B 環境準備 ===\n')

    # (1) v108_standard 60,000 events
    print('[B-1] v108_standard 60,000 events 読み込み確認')
    total = 0
    bins = {'bin_2': 0, 'bin_3_4': 0, 'bin_5_plus': 0}
    for sd in range(24):
        p = REPO/f'developmental/v112/outputs/main/atom_introduction_events_v108_standard_seed{sd}.parquet'
        if p.exists():
            d = pd.read_parquet(p, columns=['atom_id', 'n_core_bin'])
            total += len(d)
            for b in bins:
                bins[b] += (d['n_core_bin'] == b).sum()
    print(f'  total: {total:,} events / 24 seeds')
    print(f'  bin 構成: {bins}')

    # (2) per-atom trajectory 計算源
    print('\n[B-2] per-atom trajectory_stability 計算源')
    em = pd.read_parquet(REPO/'unified/v1101a/outputs/main/attention_emit_seed0.parquet',
                         columns=['attention_candidate_id'])
    print(f'  v1101a attention_emit_seed0: {len(em):,} rows')
    print(f'  attention_candidate_id 値域: {em["attention_candidate_id"].dropna().min():.0f}'
          f'-{em["attention_candidate_id"].dropna().max():.0f}')
    print(f'  unique candidate_id: {em["attention_candidate_id"].nunique()}')

    # (3) per-atom density 計算源
    print('\n[B-3] per-atom density 計算源')
    ac_raw = pd.read_parquet(REPO/'unified/v1103/outputs/main/atom_centroids_48d_raw.parquet')
    ac_norm = pd.read_parquet(REPO/'unified/v1103/outputs/main/atom_centroids_48d_normalized.parquet')
    aq = pd.read_parquet(REPO/'unified/v1103/outputs/main/atom_quality.parquet')
    print(f'  atom_centroids_48d_raw: {len(ac_raw)} atoms × {len(ac_raw.columns)-2} axes')
    print(f'  atom_centroids_48d_norm: {len(ac_norm)} atoms')
    print(f'  atom_quality: {len(aq)} atoms, cols: focus_rate_mean / nonzero_raw_mean / '
          f'nonzero_norm_mean / frac_OK')

    # (4) atom mapping (attention_candidate_id → atom name)
    print('\n[B-4] atom_id ↔ attention_candidate_id マッピング')
    sim = pd.read_parquet(REPO/'developmental/v106/outputs/main/cid_atom_sim_matrix_seed0.parquet')
    atom_cols_sim = [c for c in sim.columns if c not in ('seed', 'cid')]
    print(f'  v106 cid_atom_sim_matrix atom 列数: {len(atom_cols_sim)} (列 index が candidate_id に対応想定)')
    common = set(atom_cols_sim) & set(ac_raw['atom'].tolist())
    print(f'  sim_matrix atom ∩ v1103 atom_centroids: {len(common)} / '
          f'{len(atom_cols_sim)} / {len(ac_raw)}')
    # 列順 = candidate_id mapping を例示
    print(f'  例: candidate_id 0 → {atom_cols_sim[0]}, candidate_id 100 → {atom_cols_sim[100]}, '
          f'candidate_id 277 → {atom_cols_sim[277]}')

    # (5) LAYER_B baseline
    print('\n[B-5] LAYER_B baseline (v1105 まで)')
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
    }
    total = 0
    for k, p in counts.items():
        n = sum(1 for x in p.rglob('*') if x.is_file())
        total += n
        print(f'  {k}: {n}')
    print(f'  total LAYER_B baseline: {total} files')

    print('\n=== Step B 確認完了、Step C 着手可 ===')
    print('Step C 実装で必要な mapping:')
    print('  attention_candidate_id 0..N → atom name = v106 cid_atom_sim_matrix の atom 列順 index')
    print('  v1103 atom_centroids_48d_raw/norm の atom 名と直接 join 可能 (1 件除き 1:1)')


if __name__ == '__main__':
    main()
