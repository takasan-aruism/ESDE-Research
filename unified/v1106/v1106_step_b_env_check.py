#!/usr/bin/env python3
"""v1106 Step B — 環境準備 (sample 検証、新規出力なし)

確認事項:
1. SynapseStore overlay 経由読み込み (v3.1-v3.5 patches、11,581 synset)
2. v1105a s7 PC events 抽出 (3,300 events × candidate_atom × probability)
3. FND.spaceless 除外フィルタの sample 確認
4. v1103 atom_centroids 利用可能性 (raw + normalized + atom_quality)
5. LAYER_B baseline (v1105a まで + Synapse データ追加)

新規出力なし、サマリのみ print 出力。
"""
from __future__ import annotations
import sys
from pathlib import Path
import json
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
sys.path.insert(0, str(REPO / 'language'))

from synapse.store import SynapseStore


def main():
    print('=== v1106 Step B 環境準備 ===\n')

    # (1) SynapseStore overlay
    print('[B-1] SynapseStore overlay 経由読み込み')
    store = SynapseStore()
    patches = [
        str(REPO / 'language/synapse/patches/synapse_v3.1.json'),
        str(REPO / 'language/synapse/patches/synapse_v3.2.json'),
        str(REPO / 'language/synapse/patches/synapse_v3.3.json'),
        str(REPO / 'language/synapse/patches/synapse_v3.3_hotfix.json'),
        str(REPO / 'language/synapse/patches/synapse_v3.4.json'),
        str(REPO / 'language/synapse/patches/synapse_v3.5.json'),
    ]
    store.load(str(REPO / 'language/synapse/esde_synapses_v3.json'), patches=patches)
    print(f'  synsets: {len(store.synapses):,}')
    print(f'  patches applied: {len(store._applied_patches)}')
    print(f'  patch stats: {store._patch_stats}')

    atoms_used = set()
    for synset_id, edges in store.synapses.items():
        for e in edges:
            atoms_used.add(e.get('concept_id'))
    print(f'  atoms_used: {len(atoms_used)}')

    # (2) v1105a s7 PC events
    print('\n[B-2] v1105a s7 PC events 抽出')
    dist = pd.read_parquet(REPO / 'unified/v1105a/outputs/main/trial_step4_distributions.parquet')
    s7_pc = dist[(dist['series_id'] == 's7_48d_raw_k5') &
                  (dist['structural_label'] == 'distribution_valid')]
    n_events = s7_pc['event_id'].nunique()
    print(f'  s7 PC distribution rows: {len(s7_pc):,}')
    print(f'  unique events: {n_events:,} (期待値 3,300 程度の 1/n_seeds)')

    # 全 7 系列の PC events
    all_pc = dist[dist['structural_label'] == 'distribution_valid']
    print(f'  全 7 系列 PC distribution rows: {len(all_pc):,}')
    print(f'  全 7 系列 unique events: {all_pc["event_id"].nunique():,}')

    # (3) FND.spaceless 除外
    print('\n[B-3] FND.spaceless 除外フィルタ確認')
    # Synapse 内で FND.spaceless を指す synset
    fnd_synsets = []
    for synset_id, edges in store.synapses.items():
        for e in edges:
            if e.get('concept_id') == 'FND.spaceless':
                fnd_synsets.append(synset_id)
                break
    print(f'  FND.spaceless を指す synset 数: {len(fnd_synsets)}')
    # 入力 atom (v1105a) に FND.spaceless が含まれるか
    s7_input_atoms = set(s7_pc['input_atom'].unique())
    print(f'  s7 PC input_atom 種別: {len(s7_input_atoms)}')
    print(f'  FND.spaceless が input_atom に含まれる: {"FND.spaceless" in s7_input_atoms}')
    # s7 PC candidate に FND.spaceless が含まれるか
    s7_cand_atoms = set(s7_pc['candidate_atom'].unique())
    print(f'  s7 PC candidate_atom 種別: {len(s7_cand_atoms)}')
    print(f'  FND.spaceless が candidate_atom に含まれる: {"FND.spaceless" in s7_cand_atoms}')

    # (4) v1103 atom_centroids 利用可能性
    print('\n[B-4] v1103 atom_centroids 利用可能性')
    ac_raw = pd.read_parquet(REPO / 'unified/v1103/outputs/main/atom_centroids_48d_raw.parquet')
    print(f'  atom_centroids_48d_raw: {len(ac_raw)} atoms × {len(ac_raw.columns)-2} axes')
    centroid_atoms = set(ac_raw['atom'])
    print(f'  Synapse atoms - centroid atoms (= FND.spaceless 等): {atoms_used - centroid_atoms}')
    print(f'  centroid atoms - Synapse atoms: {centroid_atoms - atoms_used}')

    # (5) LAYER_B baseline + Synapse データ追加
    print('\n[B-5] LAYER_B baseline (v1105a まで + Synapse データ追加)')
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
        'language_synapse': REPO/'language/synapse',  # Synapse データ追加
    }
    total = 0
    for k, p in counts.items():
        n = sum(1 for x in p.rglob('*') if x.is_file())
        total += n
        print(f'  {k}: {n}')
    print(f'  total LAYER_B baseline: {total} files')

    print('\n=== Step B 確認完了、Step C 着手可 ===')
    print('Step C 実装方針:')
    print('  - SynapseStore overlay 経由で 11,581 synset 取得')
    print('  - 接続式: score(s_j) = Σ p_s7(atom_i) × syn_weight(atom_i, s_j)')
    print('  - FND.spaceless は候補から除外 + 警告ログ')
    print('  - 7 系列並列で synset 候補確率分布生成')


if __name__ == '__main__':
    main()
