#!/usr/bin/env python3
"""(III) 位置情報込み重み層 W_ijp — v1109 の修正版

W_ij だけでなく W_ij_position を構築。各 (atom_i, atom_j) 遷移を turn 位置で区別。
位置別の非対称性が v1109 (位置混合) より強く出るかを検証。
"""
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
OUT = REPO / 'unified/grammar_exploration'

POS_BINS = [(0, 5), (5, 15), (15, 25), (25, 41)]


def main():
    hist = pd.read_parquet(REPO/'unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet')

    # 位置別 (turn bin 別) の遷移カウント
    pos_W = {f'{a}-{b}': Counter() for a, b in POS_BINS}

    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        atoms = grp.sort_values('turn')['atom_top1'].tolist()
        for t in range(len(atoms) - 1):
            if atoms[t] and atoms[t+1]:
                for (a, b) in POS_BINS:
                    if a <= t < b:
                        pos_W[f'{a}-{b}'][(atoms[t], atoms[t+1])] += 1
                        break

    print(f'位置別遷移カウント:')
    for k, W in pos_W.items():
        n = sum(W.values())
        print(f'  turn {k}: total={n:,}, unique pairs={len(W)}')

    # 位置別の非対称性
    print('\n--- 位置別 asymmetry max ---')
    asym_results = []
    for pos_key, W in pos_W.items():
        if len(W) == 0: continue
        atoms_set = set()
        for (i, j) in W:
            atoms_set.add(i); atoms_set.add(j)
        atom_list = sorted(atoms_set)
        atom_idx = {a: i for i, a in enumerate(atom_list)}
        n = len(atom_list)
        M = np.zeros((n, n))
        for (i, j), c in W.items():
            M[atom_idx[i], atom_idx[j]] = c
        asym = np.abs(M - M.T)
        asym_results.append({
            'position_bin': pos_key,
            'n_pairs': len(W),
            'total_transitions': sum(W.values()),
            'asym_max': float(asym.max()),
            'asym_mean': float(asym.mean()),
            'asym_density': float(asym.max() / sum(W.values())) if sum(W.values()) > 0 else 0,
        })
        print(f'  turn {pos_key}: asym_max={asym.max():.0f}, density={asym.max()/sum(W.values()):.4f}')

    pos_df = pd.DataFrame(asym_results)
    pos_df.to_parquet(OUT/'III_position_asymmetry.parquet', index=False)

    # 位置別と v1109 比較
    print('\n--- v1109 (位置混合) vs 位置別 ---')
    v1109_asym_max = 195.0
    pos_max_total = pos_df['asym_max'].sum()
    print(f'  v1109 (位置混合): asym_max = {v1109_asym_max}')
    print(f'  位置別 (4 bin): asym_max 合計 = {pos_max_total:.0f}')
    print(f'  位置別 max density mean: {pos_df["asym_density"].mean():.4f}')

    # 位置別で出現する atom が異なるか (position-specific atom)
    print('\n--- position-specific atom (位置でしか出ない atom) ---')
    pos_atoms = {k: set() for k in pos_W}
    for pos_key, W in pos_W.items():
        for (i, j) in W:
            pos_atoms[pos_key].add(i)
            pos_atoms[pos_key].add(j)

    all_atoms = set()
    for s in pos_atoms.values():
        all_atoms.update(s)
    print(f'  全 atom: {len(all_atoms)}')
    for pos_key, s in pos_atoms.items():
        unique_to_pos = s - set().union(*[pos_atoms[k] for k in pos_atoms if k != pos_key])
        print(f'  turn {pos_key}: {len(s)} atoms, position-unique {len(unique_to_pos)}')
        if unique_to_pos:
            print(f'    unique: {sorted(unique_to_pos)[:5]}')

    # 上位 transition (位置別)
    print('\n--- 各位置 bin top 5 transition ---')
    for pos_key, W in pos_W.items():
        top5 = sorted(W.items(), key=lambda x: -x[1])[:5]
        print(f'\n  turn {pos_key}:')
        for (i, j), c in top5:
            print(f'    {i:25s} → {j:25s} : {c}')


if __name__ == '__main__':
    main()
