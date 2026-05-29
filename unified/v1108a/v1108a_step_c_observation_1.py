#!/usr/bin/env python3
"""v1108a Step C — 観察 1: ΔC_ij (Atom 遷移結合カーネル)

ΔC_ij = <P_t(A_i) × P_{t+1}(A_j)> - shuffle baseline

各 event の turn t と turn t+1 の atom_probs (top-10) を共起させ、Atom ペア結合度を測定。
非対称性 ΔC_ij ≠ ΔC_ji が時間軸方向性の構造事実。

入力:
- unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet (Step B 出力)

出力:
- unified/v1108a/outputs/main/observation_1_delta_C.parquet (上位 Atom ペア結合度)
- unified/v1108a/outputs/main/observation_1_summary.parquet
"""
from __future__ import annotations
import time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1108A_MAIN = REPO / 'unified/v1108a/outputs/main'

ATOM_TOPK = 10
RNG_SEED = 42
N_SHUFFLE = 10


def prepare_event_arrays(hist_df, atom_to_idx, n_atoms):
    """各 event を numpy 配列化 (atoms_idx (n_turn, 10), probs (n_turn, 10))"""
    event_arrays = []
    atom_cols = [f'atom_top{i+1}' for i in range(ATOM_TOPK)]
    prob_cols = [f'prob_top{i+1}' for i in range(ATOM_TOPK)]
    for (sd, sc), grp in hist_df.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn')
        n = len(grp_sorted)
        if n < 2:
            continue
        atoms_arr = grp_sorted[atom_cols].values  # (n, 10) object
        probs_arr = grp_sorted[prob_cols].values.astype(np.float64)  # (n, 10)
        # atom name → idx (-1 で無効)
        atoms_idx = np.full((n, ATOM_TOPK), -1, dtype=np.int32)
        for i in range(n):
            for j in range(ATOM_TOPK):
                a = atoms_arr[i, j]
                if a is not None and a in atom_to_idx:
                    atoms_idx[i, j] = atom_to_idx[a]
        event_arrays.append((atoms_idx, probs_arr))
    return event_arrays


def compute_C_ij_vectorized(event_arrays, n_atoms, shuffled=False, rng=None):
    """各 event の turn pair で C_ij を bulk update (np.add.at)"""
    C = np.zeros((n_atoms, n_atoms), dtype=np.float64)
    n_pairs = 0
    for atoms_idx, probs in event_arrays:
        n = atoms_idx.shape[0]
        if shuffled:
            order = rng.permutation(n)
        else:
            order = np.arange(n)
        # 全 turn pair (n-1 個)
        idx_t = order[:-1]
        idx_tp = order[1:]
        # atoms_idx[idx_t]: (n-1, 10)
        # probs[idx_t]: (n-1, 10)
        at = atoms_idx[idx_t]
        pt = probs[idx_t]
        atp = atoms_idx[idx_tp]
        ptp = probs[idx_tp]
        # 全 turn pair × 10 × 10 ペアを一度に
        # outer product per turn pair: (n-1, 10) × (n-1, 10) → (n-1, 10, 10)
        prob_outer = pt[:, :, None] * ptp[:, None, :]  # (n-1, 10, 10)
        # i index: at (n-1, 10) → broadcast (n-1, 10, 10)
        i_idx = np.broadcast_to(at[:, :, None], (n-1, ATOM_TOPK, ATOM_TOPK))
        j_idx = np.broadcast_to(atp[:, None, :], (n-1, ATOM_TOPK, ATOM_TOPK))
        # valid mask (i>=0 AND j>=0)
        mask = (i_idx >= 0) & (j_idx >= 0)
        valid_i = i_idx[mask]
        valid_j = j_idx[mask]
        valid_p = prob_outer[mask]
        # bulk add
        np.add.at(C, (valid_i, valid_j), valid_p)
        n_pairs += n - 1
    return C, n_pairs


def main():
    print('=== v1108a Step C — 観察 1: ΔC_ij Atom 遷移結合 ===\n')
    t0 = time.time()

    hist = pd.read_parquet(V1108A_MAIN / 'self_dialogue_with_atom_probs.parquet')
    print(f'  rows: {len(hist):,}, events: {hist[["seed","start_cid"]].drop_duplicates().shape[0]}')

    # atom universe (全 atom_top1..10 の union)
    all_atoms_set = set()
    for col_idx in range(ATOM_TOPK):
        col = f'atom_top{col_idx+1}'
        all_atoms_set.update(hist[col].dropna().unique())
    all_atoms = sorted(all_atoms_set)
    atom_to_idx = {a: i for i, a in enumerate(all_atoms)}
    n_atoms = len(all_atoms)
    print(f'  unique atoms in atom_top1..10: {n_atoms}')

    # event 配列化
    print('\n[1] event 配列化 (numpy)')
    t1 = time.time()
    event_arrays = prepare_event_arrays(hist, atom_to_idx, n_atoms)
    print(f'  events: {len(event_arrays)} ({time.time()-t1:.1f}s)')

    # (1) 真の C_ij
    print('\n[2] 真の C_ij 計算 (vectorized)')
    t1 = time.time()
    C_true, n_pairs = compute_C_ij_vectorized(event_arrays, n_atoms, shuffled=False)
    print(f'  非ゼロ Atom ペア数: {(C_true > 0).sum():,}, 総 turn ペア数: {n_pairs:,} ({time.time()-t1:.1f}s)')
    C_true_norm = C_true / n_pairs

    # (2) Shuffle baseline (10 回)
    print(f'\n[3] Shuffle baseline ({N_SHUFFLE} 回)')
    rng = np.random.default_rng(RNG_SEED)
    C_shuf_runs = np.zeros((N_SHUFFLE, n_atoms, n_atoms), dtype=np.float64)
    for it in range(N_SHUFFLE):
        t1 = time.time()
        C_s, n_s = compute_C_ij_vectorized(event_arrays, n_atoms, shuffled=True, rng=rng)
        C_shuf_runs[it] = C_s / n_s
        print(f'  iter {it+1}: ({time.time()-t1:.1f}s)')

    # (3) ΔC_ij = C_true - mean(C_shuffled)、z スコア
    print(f'\n[4] ΔC_ij + z スコア (vectorized)')
    shuf_mean = C_shuf_runs.mean(axis=0)
    shuf_std = C_shuf_runs.std(axis=0)
    delta_C = C_true_norm - shuf_mean
    # z スコア
    with np.errstate(divide='ignore', invalid='ignore'):
        z = np.where(shuf_std > 0, delta_C / shuf_std, np.where(delta_C != 0, 100.0, 0.0))
    z = np.clip(z, -100, 100)

    # DataFrame 化 (非ゼロのみ、メモリ節約)
    # 非ゼロ条件: C_true > 0 OR shuf_mean > 0
    mask = (C_true_norm > 0) | (shuf_mean > 0)
    ii, jj = np.where(mask)
    rows = pd.DataFrame({
        'atom_i': [all_atoms[i] for i in ii],
        'atom_j': [all_atoms[j] for j in jj],
        'C_true': C_true_norm[ii, jj],
        'C_shuf_mean': shuf_mean[ii, jj],
        'delta_C': delta_C[ii, jj],
        'z_score': z[ii, jj],
    })
    delta_df = rows

    # (4) 非対称性 ΔC_ij ≠ ΔC_ji
    print('\n[5] 非対称性 ΔC_ij vs ΔC_ji')
    # 対角 mask
    off_diag = ii != jj
    ii_od = ii[off_diag]
    jj_od = jj[off_diag]
    delta_ij = delta_C[ii_od, jj_od]
    delta_ji = delta_C[jj_od, ii_od]
    asym = np.abs(delta_ij - delta_ji)
    asym_df = pd.DataFrame({
        'atom_i': [all_atoms[i] for i in ii_od],
        'atom_j': [all_atoms[j] for j in jj_od],
        'delta_ij': delta_ij,
        'delta_ji': delta_ji,
        'asymmetry': asym,
    }).sort_values('asymmetry', ascending=False)

    # (5) 出力 + サマリ
    delta_df_sorted = delta_df.sort_values('delta_C', ascending=False)
    out1 = V1108A_MAIN / 'observation_1_delta_C.parquet'
    delta_df_sorted.to_parquet(out1, index=False)
    print(f'\nwrote {out1.name} ({len(delta_df_sorted):,} pairs)')

    out2 = V1108A_MAIN / 'observation_1_asymmetry.parquet'
    asym_df.to_parquet(out2, index=False)

    print('\n--- ΔC_ij top 20 (最も強い時間結合) ---')
    print(delta_df_sorted.head(20).to_string(index=False))

    print('\n--- 非対称性 top 15 (時間軸方向性) ---')
    print(asym_df.head(15).to_string(index=False))

    # 統計
    print('\n--- 集約統計 ---')
    n_positive = (delta_df['delta_C'] > 0).sum()
    n_negative = (delta_df['delta_C'] < 0).sum()
    n_significant = (delta_df['z_score'] > 2).sum()
    print(f'  全 Atom ペア: {len(delta_df):,}')
    print(f'  ΔC > 0: {n_positive:,}, ΔC < 0: {n_negative:,}')
    print(f'  z > 2 (有意): {n_significant:,} ({n_significant/len(delta_df)*100:.2f}%)')
    print(f'  対角ペア (atom_i==atom_j): {(delta_df["atom_i"] == delta_df["atom_j"]).sum()}')

    print(f'  非対称性 max: {asym_df["asymmetry"].max():.6f}')
    print(f'  非対称性 mean: {asym_df["asymmetry"].mean():.6f}')

    sum_df = pd.DataFrame([{
        'n_atom_pairs_total': len(delta_df),
        'n_pairs_positive_delta': int(n_positive),
        'n_pairs_significant_z2': int(n_significant),
        'asymmetry_max': float(asym_df['asymmetry'].max()),
        'asymmetry_mean': float(asym_df['asymmetry'].mean()),
        'n_turn_pairs': int(n_pairs),
        'elapsed_sec': round(time.time() - t0, 2),
    }])
    out3 = V1108A_MAIN / 'observation_1_summary.parquet'
    sum_df.to_parquet(out3, index=False)

    print(f'\n=== Step C 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
