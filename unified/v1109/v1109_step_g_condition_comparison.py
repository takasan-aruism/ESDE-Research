#!/usr/bin/env python3
"""v1109 Step G — Δw 条件比較 + #L58 全 vs 特異点 + #L59 global vs category

設計書 §3.4 + §8 反映 (GPT 指摘で段階化):
- Δw 条件: fixed (Step C-F で既実施) vs familiarity 連動 vs entropy 連動
- #L58 全 Atom ペア vs 特異点限定
- #L59 global vs category 別 (cluster_0 / cluster_1)
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1108A_MAIN = REPO / 'unified/v1108a/outputs/main'
V1109_MAIN = REPO / 'unified/v1109/outputs/main'

ATOM_TOPK = 10


def main():
    print('=== v1109 Step G — Δw 条件比較 + #L58 + #L59 ===\n')
    t0 = time.time()

    atom_df = pd.read_parquet(V1109_MAIN / 'atom_universe.parquet')
    atoms = atom_df['atom_full'].tolist()
    atom_to_idx = dict(zip(atoms, atom_df['atom_idx']))
    n_atoms = len(atoms)
    hist = pd.read_parquet(V1108A_MAIN / 'self_dialogue_with_atom_probs.parquet')

    # (1) Δw 条件: fixed vs familiarity vs entropy
    print('[1] Δw 条件: fixed vs familiarity vs entropy')
    H_max = np.log(ATOM_TOPK)
    prob_cols = [f'prob_top{i+1}' for i in range(ATOM_TOPK)]

    delta_w_rows = []
    for delta_cond in ['fixed', 'familiarity_weighted', 'entropy_weighted']:
        W = np.zeros((n_atoms, n_atoms))
        for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
            grp_sorted = grp.sort_values('turn').reset_index(drop=True)
            n = len(grp_sorted)
            if n < 2:
                continue
            for t in range(n - 1):
                ai = grp_sorted.iloc[t]['atom_top1']
                aj = grp_sorted.iloc[t+1]['atom_top1']
                if ai is None or aj is None:
                    continue
                i = atom_to_idx.get(ai, -1)
                j = atom_to_idx.get(aj, -1)
                if i < 0 or j < 0:
                    continue

                # Δw 計算
                if delta_cond == 'fixed':
                    dw = 1.0
                elif delta_cond == 'familiarity_weighted':
                    fam = grp_sorted.iloc[t]['last_familiarity_max']
                    dw = 1.0 if (fam is None or pd.isna(fam)) else 1.0 / (1.0 + fam / 50)
                else:  # entropy_weighted (Code A 案: H × (1 - H/H_max))
                    probs = grp_sorted.iloc[t][prob_cols].values.astype(np.float64)
                    probs = probs / probs.sum() if probs.sum() > 0 else probs
                    H_t = -np.sum(probs * np.log(probs + 1e-12))
                    H_norm = H_t / H_max if H_max > 0 else 0
                    dw = H_norm * (1.0 - H_norm)
                W[i, j] += dw

        asym = np.abs(W - W.T)
        delta_w_rows.append({
            'delta_w_condition': delta_cond,
            'asym_max': float(asym.max()),
            'asym_mean': float(asym.mean()),
            'W_sum': float(W.sum()),
            'n_nonzero': int((W > 0).sum()),
        })
        print(f'  {delta_cond}: asym max={asym.max():.4f}, '
              f'sum={W.sum():.2f}, n_nonzero={(W>0).sum()}')

    dw_df = pd.DataFrame(delta_w_rows)
    dw_df.to_parquet(V1109_MAIN / 'observation_G_delta_w.parquet', index=False)

    # (2) #L58 全 Atom ペア vs 特異点限定
    print('\n[2] #L58 全 Atom ペア vs 特異点限定')
    # 特異点 = 各 event の familiarity 減少率最大 turn
    rho_FH = pd.read_parquet(V1108A_MAIN / 'observation_2_rho_FH.parquet')
    rho_FH['decrease_rate'] = -rho_FH['delta_F'] / (rho_FH['F_t'] + 1e-6)
    special_turns = rho_FH.loc[
        rho_FH.groupby(['seed', 'start_cid'])['decrease_rate'].idxmax()]
    special_set = set(zip(special_turns['seed'], special_turns['start_cid'],
                            special_turns['turn']))

    # 全ペア W (既 Step C で計算済、W_observed)
    W_mat = np.load(V1109_MAIN / 'W_matrices.npz', allow_pickle=True)
    W_all = W_mat['W_observed']
    asym_all = np.abs(W_all - W_all.T)

    # 特異点限定 W
    W_special = np.zeros((n_atoms, n_atoms))
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn').reset_index(drop=True)
        for t in range(len(grp_sorted) - 1):
            if (int(sd), int(sc), t) not in special_set:
                continue
            ai = grp_sorted.iloc[t]['atom_top1']
            aj = grp_sorted.iloc[t+1]['atom_top1']
            if ai is None or aj is None: continue
            i = atom_to_idx.get(ai, -1); j = atom_to_idx.get(aj, -1)
            if i < 0 or j < 0: continue
            W_special[i, j] += 1.0
    asym_special = np.abs(W_special - W_special.T)

    L58_rows = [
        {'scope': 'all_pairs', 'asym_max': float(asym_all.max()),
          'asym_mean': float(asym_all.mean()), 'W_sum': float(W_all.sum())},
        {'scope': 'singular_point_only', 'asym_max': float(asym_special.max()),
          'asym_mean': float(asym_special.mean()), 'W_sum': float(W_special.sum())},
    ]
    L58_df = pd.DataFrame(L58_rows)
    L58_df.to_parquet(V1109_MAIN / 'observation_G_L58_comparison.parquet', index=False)
    print(L58_df.to_string(index=False))

    # (3) #L59 global vs category 別 (cluster_0 vs cluster_1)
    print('\n[3] #L59 global vs category 別')
    cluster_0_cats = {'EXS', 'FND', 'REL', 'LOG', 'VAL', 'WLD', 'COG', 'COM',
                       'ABS', 'SPC', 'CHG', 'TIM'}
    W_c0 = np.zeros((n_atoms, n_atoms))
    W_c1 = np.zeros((n_atoms, n_atoms))
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn').reset_index(drop=True)
        for t in range(len(grp_sorted) - 1):
            ai = grp_sorted.iloc[t]['atom_top1']
            aj = grp_sorted.iloc[t+1]['atom_top1']
            if ai is None or aj is None: continue
            i = atom_to_idx.get(ai, -1); j = atom_to_idx.get(aj, -1)
            if i < 0 or j < 0: continue
            cat_i = ai.split('.')[0]
            if cat_i in cluster_0_cats:
                W_c0[i, j] += 1.0
            else:
                W_c1[i, j] += 1.0

    asym_c0 = np.abs(W_c0 - W_c0.T)
    asym_c1 = np.abs(W_c1 - W_c1.T)

    L59_rows = [
        {'scope': 'global', 'asym_max': float(asym_all.max()),
          'asym_mean': float(asym_all.mean()), 'W_sum': float(W_all.sum())},
        {'scope': 'cluster_0_only', 'asym_max': float(asym_c0.max()),
          'asym_mean': float(asym_c0.mean()), 'W_sum': float(W_c0.sum())},
        {'scope': 'cluster_1_only', 'asym_max': float(asym_c1.max()),
          'asym_mean': float(asym_c1.mean()), 'W_sum': float(W_c1.sum())},
    ]
    L59_df = pd.DataFrame(L59_rows)
    L59_df.to_parquet(V1109_MAIN / 'observation_G_L59_comparison.parquet', index=False)
    print(L59_df.to_string(index=False))

    print(f'\n=== Step G 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
