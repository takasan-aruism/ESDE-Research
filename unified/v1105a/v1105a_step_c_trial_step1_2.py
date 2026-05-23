#!/usr/bin/env python3
"""v1105a Step C — 試行 Step 1+2: 入力投入 + 段 4-b 連想 4 source レイヤー

設計書 v3 §2.2 + §2.3 通り:
- Step 1 入力投入: v108_standard 60,000 events を CID 単位で候補保持
- Step 2 段 4-b 連想: 4 source レイヤー並列で候補 atom set を取り出す
  - Genesis alpha: 入力 atom が登場した alpha chain 内の他 atom (predecessor 連鎖
    の atom set proxy)
  - Genesis beta: 同じく beta chain
  - Language alpha: alpha scope chain に登場する atom のうち Couple endpoint
    (12 atoms) と一致するもの
  - Language beta: 同じく beta

入力 (read-only):
  - developmental/v112/outputs/main/atom_introduction_events_v108_standard_seed{N}.parquet
    (24 seeds × 2500 events = 60,000 events)
  - unified/v1101a/outputs/main/attention_emit_seed{N}.parquet
    (alpha/beta scope chain 構築用)
  - developmental/v106/outputs/main/cid_atom_sim_matrix_seed{N}.parquet
    (atom_to_id mapping)
  - unified/v1103/outputs/main/proposals.json (Couple endpoint 12 atoms)

出力:
  - unified/v1105a/outputs/main/trial_step2_associations.parquet
    (per (seed, event_id, source_layer, candidate_atom) で source layer metadata 含む)
"""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1101A_MAIN = REPO / 'unified/v1101a/outputs/main'
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V112_MAIN = REPO / 'developmental/v112/outputs/main'
V1103_MAIN = REPO / 'unified/v1103/outputs/main'
V1105A_MAIN = REPO / 'unified/v1105a/outputs/main'

WINDOW_RANGE = range(20, 70)


def load_couple_endpoints() -> set:
    """v1103 proposals.json から B_COUPLE endpoint atoms 12 種"""
    with open(V1103_MAIN / 'proposals.json') as f:
        p = json.load(f)
    couple_atoms = set()
    for c in p['proposals']:
        if c['pattern'] == 'B_COUPLE':
            couple_atoms.add(c['atom_a'])
            couple_atoms.add(c['atom_b'])
    return couple_atoms


def build_seed_lookup(seed: int, couple_atoms: set) -> dict:
    """seed ごとに 4 source レイヤー lookup table を構築:
    atom_id → (genesis_alpha_set, genesis_beta_set, lang_alpha_set, lang_beta_set)
    """
    # atom_to_id mapping (cid_atom_sim_matrix の atom 列順 = candidate_id)
    sim = pd.read_parquet(V106_MAIN / f'cid_atom_sim_matrix_seed{seed}.parquet')
    atom_cols = [c for c in sim.columns if c not in ('seed', 'cid')]
    id_to_atom = {i: a for i, a in enumerate(atom_cols)}

    # attention_emit から alpha/beta chain 構築
    em = pd.read_parquet(V1101A_MAIN / f'attention_emit_seed{seed}.parquet',
                         columns=['window', 'change_scope', 'scope_id',
                                  'change_metric_type', 'attention_candidate_id',
                                  'qc_regime'])
    em = em[em['window'].isin(WINDOW_RANGE)].dropna(subset=['attention_candidate_id'])
    em['attention_candidate_id'] = em['attention_candidate_id'].astype(int)
    em['atom'] = em['attention_candidate_id'].map(id_to_atom)

    # per atom → 同 chain (scope_id, metric, qc_regime) 内 atom set
    # alpha chain
    alpha = em[em['change_scope'] == 'alpha']
    beta = em[em['change_scope'] == 'beta']

    # atom_id → 登場した chain (scope_id, metric, qc_regime) 内 atom set
    atom_to_alpha = {}
    atom_to_beta = {}
    # chain ごとに atom set 取得
    for (sid, mt, rg), grp in alpha.groupby(['scope_id', 'change_metric_type', 'qc_regime']):
        chain_atoms = set(grp['atom'].dropna())
        for atom in chain_atoms:
            if atom not in atom_to_alpha:
                atom_to_alpha[atom] = set()
            # その atom 以外の chain 内 atom を candidate に
            atom_to_alpha[atom].update(chain_atoms - {atom})
    for (sid, mt, rg), grp in beta.groupby(['scope_id', 'change_metric_type', 'qc_regime']):
        chain_atoms = set(grp['atom'].dropna())
        for atom in chain_atoms:
            if atom not in atom_to_beta:
                atom_to_beta[atom] = set()
            atom_to_beta[atom].update(chain_atoms - {atom})

    # Language layer: alpha/beta chain candidate のうち Couple endpoint に含まれるもの
    atom_to_lang_alpha = {atom: cands & couple_atoms for atom, cands in atom_to_alpha.items()}
    atom_to_lang_beta = {atom: cands & couple_atoms for atom, cands in atom_to_beta.items()}

    return {
        'genesis_alpha': atom_to_alpha,
        'genesis_beta': atom_to_beta,
        'language_alpha': atom_to_lang_alpha,
        'language_beta': atom_to_lang_beta,
        'id_to_atom': id_to_atom,
    }


def main():
    V1105A_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1105a Step C 試行 Step 1+2 ===')
    t0 = time.time()

    couple_atoms = load_couple_endpoints()
    print(f'Couple endpoint atoms: {len(couple_atoms)} (12 unique)')

    rows = []
    for seed in range(24):
        ts = time.time()
        lookup = build_seed_lookup(seed, couple_atoms)
        # 入力 events 読み込み
        p = V112_MAIN / f'atom_introduction_events_v108_standard_seed{seed}.parquet'
        events = pd.read_parquet(p, columns=['event_id', 'atom_id', 'source_cid',
                                              'n_core_member', 'n_core_bin'])
        # 各 event について 4 source レイヤーで candidate atom set 取得
        for _, ev in events.iterrows():
            atom = ev['atom_id']
            for layer_name in ['genesis_alpha', 'genesis_beta',
                                'language_alpha', 'language_beta']:
                cands = lookup[layer_name].get(atom, set())
                for cand in cands:
                    rows.append({
                        'seed': seed,
                        'event_id': ev['event_id'],
                        'input_atom': atom,
                        'source_cid': int(ev['source_cid']),
                        'n_core_member': int(ev['n_core_member']),
                        'n_core_bin': ev['n_core_bin'],
                        'source_layer': layer_name,
                        'candidate_atom': cand,
                    })
        print(f'  seed {seed}: events={len(events)}, '
              f'rows so far={len(rows):,}, elapsed {time.time()-ts:.1f}s')

    df = pd.DataFrame(rows)
    out = V1105A_MAIN / 'trial_step2_associations.parquet'
    df.to_parquet(out, index=False)
    print(f'\nwrote {out.name} ({len(df):,} rows, elapsed {time.time()-t0:.1f}s)')

    # --- サマリ ---
    print('\n--- source_layer 別 candidate 数 (per layer) ---')
    print(df.groupby('source_layer').size().to_string())
    print('\n--- n_core_bin × source_layer per-event 平均候補数 ---')
    g = df.groupby(['n_core_bin', 'source_layer', 'seed', 'event_id']).size().reset_index(name='n_cands')
    print(g.groupby(['n_core_bin', 'source_layer'])['n_cands'].agg(['mean', 'median', 'max']).round(2).to_string())
    print('\n--- 入力 atom 別 4 layer candidate 数 (top 5 events) ---')
    s = df.groupby(['input_atom', 'source_layer']).size().unstack(fill_value=0)
    print(s.head(8).to_string())


if __name__ == '__main__':
    main()
