#!/usr/bin/env python3
"""案 5: 相互情報量で文法的組み合わせ抽出

全 atom ペア (A, B) の MI = log[P(A,B) / (P(A) × P(B))]
高 MI ペア = 偶然より強く共起 = 文法的まとまり候補
順序考慮 (A → B) と非順序 (A,B 共起) 両方を見る
"""
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
OUT = REPO / 'unified/grammar_exploration'


def main():
    hist = pd.read_parquet(REPO/'unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet')

    # 1. 順序考慮: P(A_t = i, A_{t+1} = j) (1 turn ペア)
    pair_count = Counter()
    atom_count = Counter()
    n_pairs = 0
    n_singles = 0
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp = grp.sort_values('turn').reset_index(drop=True)
        atoms = grp['atom_top1'].tolist()
        for t in range(len(atoms)):
            if atoms[t]:
                atom_count[atoms[t]] += 1
                n_singles += 1
        for t in range(len(atoms) - 1):
            if atoms[t] and atoms[t+1]:
                pair_count[(atoms[t], atoms[t+1])] += 1
                n_pairs += 1

    print(f'singles: {n_singles:,}, pairs: {n_pairs:,}')

    # 順序考慮 PMI
    rows = []
    for (i, j), c_ij in pair_count.items():
        if c_ij < 5:
            continue
        p_ij = c_ij / n_pairs
        p_i = atom_count[i] / n_singles
        p_j = atom_count[j] / n_singles
        if p_i > 0 and p_j > 0 and p_ij > 0:
            pmi = np.log(p_ij / (p_i * p_j))
            # NPMI (-1 to 1)
            npmi = pmi / -np.log(p_ij) if p_ij < 1 else 0
            rows.append({
                'atom_i': i, 'atom_j': j,
                'cat_i': i.split('.')[0],
                'cat_j': j.split('.')[0],
                'count': c_ij,
                'p_ij': p_ij,
                'pmi': float(pmi),
                'npmi': float(npmi),
            })
    df = pd.DataFrame(rows).sort_values('npmi', ascending=False)
    df.to_parquet(OUT/'case_5_pmi_ordered.parquet', index=False)
    print(f'pairs (≥5 obs): {len(df):,}')

    print('\n--- 順序考慮 高 PMI top 20 (偶然超過の組み合わせ) ---')
    print(df.head(20)[['atom_i', 'atom_j', 'count', 'pmi', 'npmi']].round(4).to_string(index=False))

    print('\n--- 自己ループ除外、非対角 top 15 ---')
    non_diag = df[df['atom_i'] != df['atom_j']]
    print(non_diag.head(15)[['atom_i', 'atom_j', 'count', 'pmi', 'npmi']].round(4).to_string(index=False))

    # 2. 非順序 (共起): P(A in event, B in event)
    event_atoms = defaultdict(set)
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        for a in grp['atom_top1'].dropna().unique():
            event_atoms[(sd, sc)].add(a)
    n_events = len(event_atoms)
    print(f'\nevents: {n_events}')

    atom_in_event = Counter()
    pair_in_event = Counter()
    for atoms_set in event_atoms.values():
        sorted_atoms = sorted(atoms_set)
        for a in sorted_atoms:
            atom_in_event[a] += 1
        for i, a1 in enumerate(sorted_atoms):
            for a2 in sorted_atoms[i+1:]:
                pair_in_event[(a1, a2)] += 1

    rows2 = []
    for (a, b), c in pair_in_event.items():
        if c < 10:
            continue
        p_ab = c / n_events
        p_a = atom_in_event[a] / n_events
        p_b = atom_in_event[b] / n_events
        if p_a > 0 and p_b > 0 and p_ab > 0:
            pmi = np.log(p_ab / (p_a * p_b))
            npmi = pmi / -np.log(p_ab) if p_ab < 1 else 0
            rows2.append({
                'atom_a': a, 'atom_b': b,
                'cat_a': a.split('.')[0],
                'cat_b': b.split('.')[0],
                'cooccur_events': c,
                'pmi': float(pmi),
                'npmi': float(npmi),
            })
    df_cooc = pd.DataFrame(rows2).sort_values('npmi', ascending=False)
    df_cooc.to_parquet(OUT/'case_5_pmi_cooccurrence.parquet', index=False)

    print('\n--- 非順序 (event 共起) 高 PMI top 15 ---')
    print(df_cooc.head(15)[['atom_a', 'atom_b', 'cooccur_events',
                                'pmi', 'npmi']].round(4).to_string(index=False))

    # 集約
    print('\n--- 集約 ---')
    print(f'順序考慮 PMI mean: {df["pmi"].mean():.4f}, median: {df["pmi"].median():.4f}')
    print(f'  npmi > 0.5 (強い順序結合): {(df["npmi"] > 0.5).sum()}')
    print(f'  npmi > 0.3 (中程度): {(df["npmi"] > 0.3).sum()}')
    print(f'非順序 PMI mean: {df_cooc["pmi"].mean():.4f}')
    print(f'  npmi > 0.5: {(df_cooc["npmi"] > 0.5).sum()}')


if __name__ == '__main__':
    main()
