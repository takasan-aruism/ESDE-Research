#!/usr/bin/env python3
"""v1106 Step D — 観察 2: Synapse 強度と s7 確率の整合

設計書 v1106 §2.3 通り、s7 (および全 7 系列) で確率上位の Atom が Synapse 強度
上位 synset と接続するか、相関指標で観察。

per (seed, event_id, series_id) で計算:
- top1_atom_top1_syn_strength: s7 top1 atom が接続する Synapse top1 synset weight
- top1_atom_mean_syn_strength: 同 atom が接続する全 synset の weight 平均
- top1_atom_n_syn_links: 同 atom が接続する Synapse synset 数
- top5_atom_top1_syn_strength_mean: top5 atom の各 top1 synset weight 平均
- atom_synapse_rank_correlation: top5 atom の確率順位と 各 atom の代表 Synapse
  強度 (top1 weight) 順位の Spearman 相関

7 系列で独立計算、別レイヤー保持。

入力 (read-only):
  - unified/v1105a/outputs/main/trial_step4_distributions.parquet
  - language/synapse/esde_synapses_v3.json + patches v3.1-v3.5

出力:
  - unified/v1106/outputs/main/observation_2_synapse_alignment.parquet
    (per (seed, event_id, series_id) で alignment 指標)
"""
from __future__ import annotations
import sys, time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

REPO = Path('/home/takasan/esde/ESDE-Research')
sys.path.insert(0, str(REPO / 'language'))
from synapse.store import SynapseStore

V1105A_MAIN = REPO / 'unified/v1105a/outputs/main'
V1106_MAIN = REPO / 'unified/v1106/outputs/main'
SYNAPSE_DIR = REPO / 'language/synapse'

EXCLUDED_ATOMS = {'FND.spaceless'}


def load_atom_to_synsets() -> dict:
    """atom → list of (synset_id, weight)、weight 降順 sort 済"""
    store = SynapseStore()
    store.load(
        str(SYNAPSE_DIR / 'esde_synapses_v3.json'),
        patches=[str(SYNAPSE_DIR / f'patches/synapse_{v}.json')
                  for v in ['v3.1', 'v3.2', 'v3.3', 'v3.3_hotfix', 'v3.4', 'v3.5']],
    )
    a2s = defaultdict(list)
    for synset_id, edges in store.synapses.items():
        for e in edges:
            atom = e.get('concept_id')
            if atom in EXCLUDED_ATOMS:
                continue
            a2s[atom].append((synset_id, e.get('weight', 0.0)))
    # 各 atom の synset list を weight 降順 sort
    for atom in a2s:
        a2s[atom].sort(key=lambda x: -x[1])
    return dict(a2s)


def main():
    V1106_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106 Step D 観察 2: Synapse 強度と s7 確率の整合 ===')
    t0 = time.time()

    # (1) atom → synsets lookup
    print('[1] atom → synsets lookup 構築')
    atom_to_synsets = load_atom_to_synsets()
    print(f'  atoms: {len(atom_to_synsets)}')

    # (2) v1105a 7 系列 PC events 読み込み
    print('\n[2] v1105a 7 系列 PC events 読み込み')
    dist = pd.read_parquet(V1105A_MAIN / 'trial_step4_distributions.parquet')
    pc = dist[dist['structural_label'] == 'distribution_valid'].copy()
    pc = pc[~pc['candidate_atom'].isin(EXCLUDED_ATOMS)]
    print(f'  PC rows: {len(pc):,}')

    # (3) per (event, series) alignment 指標計算
    print('\n[3] alignment 指標計算')
    out_rows = []
    grouped = pc.groupby(['seed', 'event_id', 'series_id'])
    n_grp = len(grouped)
    cnt = 0
    for (sd, eid, sid), grp in grouped:
        cnt += 1
        if cnt % 5000 == 0:
            print(f'  processed {cnt:,}/{n_grp:,}, elapsed {time.time()-t0:.1f}s')

        # 確率降順 sort、top1 / top5 を取得
        grp_sorted = grp.sort_values('probability', ascending=False)
        if len(grp_sorted) == 0:
            continue
        top1_atom = grp_sorted.iloc[0]['candidate_atom']
        top5_atoms = grp_sorted.head(5)['candidate_atom'].tolist()
        top5_probs = grp_sorted.head(5)['probability'].tolist()

        # top1_atom_top1_syn_strength
        if top1_atom in atom_to_synsets and atom_to_synsets[top1_atom]:
            top1_syn = atom_to_synsets[top1_atom][0]  # weight 降順 sort 済の先頭
            top1_atom_top1_syn_strength = top1_syn[1]
            top1_atom_top1_syn_id = top1_syn[0]
            top1_atom_mean_syn_strength = float(
                np.mean([w for _, w in atom_to_synsets[top1_atom]]))
            top1_atom_n_syn_links = len(atom_to_synsets[top1_atom])
        else:
            top1_atom_top1_syn_strength = np.nan
            top1_atom_top1_syn_id = None
            top1_atom_mean_syn_strength = np.nan
            top1_atom_n_syn_links = 0

        # top5_atom_top1_syn_strength_mean
        top5_top1_strengths = []
        for a in top5_atoms:
            if a in atom_to_synsets and atom_to_synsets[a]:
                top5_top1_strengths.append(atom_to_synsets[a][0][1])
        top5_atom_top1_syn_strength_mean = float(np.mean(top5_top1_strengths)) \
            if top5_top1_strengths else np.nan

        # atom_synapse_rank_correlation:
        # top5 atom の確率順位 (1..5) と 各 atom の代表 Synapse 強度 (top1 weight) 順位の Spearman
        top5_syn_strengths = []  # atom 順に対応 Synapse top1 weight
        for a in top5_atoms:
            if a in atom_to_synsets and atom_to_synsets[a]:
                top5_syn_strengths.append(atom_to_synsets[a][0][1])
            else:
                top5_syn_strengths.append(np.nan)
        if len(top5_atoms) >= 3 and \
           not all(np.isnan(s) for s in top5_syn_strengths) and \
           len(set(top5_syn_strengths)) > 1:
            # NaN を除外、対応する prob index を維持
            valid_pairs = [(p, s) for p, s in zip(top5_probs, top5_syn_strengths)
                            if not np.isnan(s)]
            if len(valid_pairs) >= 3:
                prob_arr = [p for p, _ in valid_pairs]
                syn_arr = [s for _, s in valid_pairs]
                if len(set(syn_arr)) > 1 and len(set(prob_arr)) > 1:
                    rho, _ = spearmanr(prob_arr, syn_arr)
                    atom_synapse_rank_correlation = float(rho) if not np.isnan(rho) else np.nan
                else:
                    atom_synapse_rank_correlation = np.nan
            else:
                atom_synapse_rank_correlation = np.nan
        else:
            atom_synapse_rank_correlation = np.nan

        out_rows.append({
            'seed': sd,
            'event_id': eid,
            'series_id': sid,
            'top1_atom': top1_atom,
            'top1_atom_top1_syn_strength': float(top1_atom_top1_syn_strength)
                if not np.isnan(top1_atom_top1_syn_strength) else np.nan,
            'top1_atom_top1_syn_id': top1_atom_top1_syn_id,
            'top1_atom_mean_syn_strength': top1_atom_mean_syn_strength,
            'top1_atom_n_syn_links': top1_atom_n_syn_links,
            'top5_atom_top1_syn_strength_mean': top5_atom_top1_syn_strength_mean,
            'atom_synapse_rank_correlation': atom_synapse_rank_correlation,
            'n_atoms_top5': len(top5_atoms),
        })

    df = pd.DataFrame(out_rows).sort_values(
        ['seed', 'event_id', 'series_id']).reset_index(drop=True)
    out = V1106_MAIN / 'observation_2_synapse_alignment.parquet'
    df.to_parquet(out, index=False)
    print(f'\nwrote {out.name} ({len(df):,} rows, elapsed {time.time()-t0:.1f}s)')

    # --- サマリ ---
    print('\n--- series_id 別 alignment 指標 mean ---')
    cols = ['top1_atom_top1_syn_strength', 'top1_atom_mean_syn_strength',
             'top1_atom_n_syn_links', 'top5_atom_top1_syn_strength_mean',
             'atom_synapse_rank_correlation']
    print(df.groupby('series_id')[cols].mean().round(4).to_string())

    print('\n--- atom_synapse_rank_correlation 分布 (s7) ---')
    s7 = df[df['series_id'] == 's7_48d_raw_k5']['atom_synapse_rank_correlation'].dropna()
    if len(s7) > 0:
        print(f'  n={len(s7)}, mean={s7.mean():.4f}, median={s7.median():.4f}, '
              f'std={s7.std():.4f}, '
              f'positive_rate={(s7>0).mean():.4f}, '
              f'>0.5={(s7>0.5).mean():.4f}, <-0.5={(s7<-0.5).mean():.4f}')


if __name__ == '__main__':
    main()
