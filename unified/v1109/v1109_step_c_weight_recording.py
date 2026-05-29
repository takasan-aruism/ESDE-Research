#!/usr/bin/env python3
"""v1109 Step C — 重み記録機構 (認知層) + 4 条件構築

4 条件で W_ij 行列を構築:
1. baseline: W = 0 (重みなし、対照)
2. observed: 実際の atom_top1 遷移で Δw 加算
3. shuffled: 各 event 内で turn 順序シャッフル後の遷移 (10 回平均)
4. frequency: 各 atom 出現頻度の outer product (順序情報なし)

注意 (Code A Q1-Q6 提案、Taka 承認 2026-05-30):
- α = 0.5 固定 (Step D で sensitivity 分析)
- Δw fixed (Step G で familiarity/entropy 連動と比較)

入力:
- unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet
- unified/v1109/outputs/main/atom_universe.parquet

出力:
- unified/v1109/outputs/main/W_baseline.parquet (W=0 確認)
- unified/v1109/outputs/main/W_observed.parquet
- unified/v1109/outputs/main/W_shuffled.parquet (10 回平均)
- unified/v1109/outputs/main/W_frequency.parquet
- unified/v1109/outputs/main/observation_C_summary.parquet
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1108A_MAIN = REPO / 'unified/v1108a/outputs/main'
V1109_MAIN = REPO / 'unified/v1109/outputs/main'

N_SHUFFLE = 10
RNG_SEED = 42
DELTA_W = 1.0  # fixed Δw (基準値、Step G で familiarity/entropy 連動と比較)


def build_event_arrays(hist, atom_to_idx):
    """各 event を numpy 配列化 (atoms_idx (n_turn,) for top1 only)"""
    events = []
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn').reset_index(drop=True)
        n = len(grp_sorted)
        if n < 2:
            continue
        # top1 atom のみ使用 (重み記録は実際の遷移先=top1 を使う)
        atoms = grp_sorted['atom_top1'].values
        idx = np.array([atom_to_idx.get(a, -1) for a in atoms], dtype=np.int32)
        events.append({
            'seed': int(sd), 'start_cid': int(sc),
            'atoms_idx': idx,
        })
    return events


def update_W_observed(events, n_atoms):
    """各 event の turn t → t+1 で W_{i,j} += Δw_fixed"""
    W = np.zeros((n_atoms, n_atoms), dtype=np.float64)
    n_transitions = 0
    for ev in events:
        idx = ev['atoms_idx']
        for t in range(len(idx) - 1):
            i = idx[t]; j = idx[t+1]
            if i < 0 or j < 0:
                continue
            W[i, j] += DELTA_W
            n_transitions += 1
    return W, n_transitions


def update_W_shuffled(events, n_atoms, rng):
    """各 event 内で turn 順序シャッフル後の遷移で W 蓄積"""
    W = np.zeros((n_atoms, n_atoms), dtype=np.float64)
    n_transitions = 0
    for ev in events:
        idx = ev['atoms_idx']
        n = len(idx)
        if n < 2:
            continue
        perm = rng.permutation(n)
        idx_shuf = idx[perm]
        for t in range(n - 1):
            i = idx_shuf[t]; j = idx_shuf[t+1]
            if i < 0 or j < 0:
                continue
            W[i, j] += DELTA_W
            n_transitions += 1
    return W, n_transitions


def update_W_frequency(events, n_atoms):
    """Atom 出現頻度の outer product (順序情報なし)"""
    freq = np.zeros(n_atoms, dtype=np.float64)
    for ev in events:
        idx = ev['atoms_idx']
        for i in idx:
            if i >= 0:
                freq[i] += 1
    # outer product (i 出現 × j 出現)、対角含む
    total = freq.sum()
    if total > 0:
        freq_norm = freq / total
    else:
        freq_norm = freq
    # スケール合わせるため observed 総和に合わせる
    W = np.outer(freq, freq) / total if total > 0 else np.outer(freq, freq)
    return W, int(total)


def compute_asymmetry(W):
    """W_ij vs W_ji の非対称性"""
    return np.abs(W - W.T)


def main():
    print('=== v1109 Step C — 重み記録機構 (4 条件) ===\n')
    t0 = time.time()

    # atom universe
    atom_df = pd.read_parquet(V1109_MAIN / 'atom_universe.parquet')
    atoms = atom_df['atom_full'].tolist()
    atom_to_idx = dict(zip(atoms, atom_df['atom_idx']))
    n_atoms = len(atoms)
    print(f'  atom universe: {n_atoms}')

    # self_dialogue
    hist = pd.read_parquet(V1108A_MAIN / 'self_dialogue_with_atom_probs.parquet')
    events = build_event_arrays(hist, atom_to_idx)
    print(f'  events with 2+ turns: {len(events)}')

    # (1) baseline (W=0)
    W_baseline = np.zeros((n_atoms, n_atoms))
    print(f'\n[1] baseline: W=0、対照群')

    # (2) observed
    print(f'\n[2] observed: 実際の遷移で W 蓄積')
    W_observed, n_tr_obs = update_W_observed(events, n_atoms)
    print(f'  total transitions: {n_tr_obs:,}')
    print(f'  W sum: {W_observed.sum():.0f}')
    print(f'  non-zero cells: {(W_observed > 0).sum():,}')
    asym_obs = compute_asymmetry(W_observed)
    print(f'  asymmetry max: {asym_obs.max():.4f}, mean: {asym_obs.mean():.6f}')

    # (3) shuffled (10 回平均)
    print(f'\n[3] shuffled: 10 回シャッフル平均')
    rng = np.random.default_rng(RNG_SEED)
    W_shuf_runs = np.zeros((N_SHUFFLE, n_atoms, n_atoms))
    for it in range(N_SHUFFLE):
        W_s, _ = update_W_shuffled(events, n_atoms, rng)
        W_shuf_runs[it] = W_s
    W_shuffled = W_shuf_runs.mean(axis=0)
    W_shuf_std = W_shuf_runs.std(axis=0)
    print(f'  W mean sum: {W_shuffled.sum():.0f}')
    print(f'  non-zero cells: {(W_shuffled > 0).sum():,}')
    asym_shuf = compute_asymmetry(W_shuffled)
    print(f'  asymmetry max: {asym_shuf.max():.4f}, mean: {asym_shuf.mean():.6f}')

    # (4) frequency
    print(f'\n[4] frequency: 出現頻度 outer product')
    W_frequency, n_tr_freq = update_W_frequency(events, n_atoms)
    print(f'  W sum: {W_frequency.sum():.2f}')
    print(f'  non-zero cells: {(W_frequency > 0).sum():,}')
    asym_freq = compute_asymmetry(W_frequency)
    print(f'  asymmetry max: {asym_freq.max():.6f}, mean: {asym_freq.mean():.6f}')

    # (5) 出力 (DataFrame 化、非ゼロセルのみ)
    def W_to_df(W, label):
        ii, jj = np.where(W != 0)
        return pd.DataFrame({
            'atom_i': [atoms[i] for i in ii],
            'atom_j': [atoms[j] for j in jj],
            'W': W[ii, jj],
            'condition': label,
        })

    W_observed_df = W_to_df(W_observed, 'observed')
    W_observed_df.to_parquet(V1109_MAIN / 'W_observed.parquet', index=False)
    W_shuf_df = W_to_df(W_shuffled, 'shuffled')
    W_shuf_df.to_parquet(V1109_MAIN / 'W_shuffled.parquet', index=False)
    W_freq_df = W_to_df(W_frequency, 'frequency')
    W_freq_df.to_parquet(V1109_MAIN / 'W_frequency.parquet', index=False)

    # 行列を numpy 保存 (Step D 用)
    np.savez(V1109_MAIN / 'W_matrices.npz',
              W_baseline=W_baseline, W_observed=W_observed,
              W_shuffled=W_shuffled, W_shuf_std=W_shuf_std,
              W_frequency=W_frequency, atoms=np.array(atoms))

    # (6) 4 条件比較サマリ
    print(f'\n[5] 4 条件比較サマリ')
    sum_rows = [
        {'condition': 'baseline', 'asym_max': 0.0, 'asym_mean': 0.0,
          'W_sum': 0.0, 'n_nonzero': 0,
          'n_transitions': 0},
        {'condition': 'observed', 'asym_max': float(asym_obs.max()),
          'asym_mean': float(asym_obs.mean()),
          'W_sum': float(W_observed.sum()),
          'n_nonzero': int((W_observed > 0).sum()),
          'n_transitions': n_tr_obs},
        {'condition': 'shuffled', 'asym_max': float(asym_shuf.max()),
          'asym_mean': float(asym_shuf.mean()),
          'W_sum': float(W_shuffled.sum()),
          'n_nonzero': int((W_shuffled > 0).sum()),
          'n_transitions': n_tr_obs},  # shuffle も同等
        {'condition': 'frequency', 'asym_max': float(asym_freq.max()),
          'asym_mean': float(asym_freq.mean()),
          'W_sum': float(W_frequency.sum()),
          'n_nonzero': int((W_frequency > 0).sum()),
          'n_transitions': 0},
    ]
    sum_df = pd.DataFrame(sum_rows)
    sum_df.to_parquet(V1109_MAIN / 'observation_C_summary.parquet', index=False)
    print(sum_df.to_string(index=False))

    # observed vs shuffled の非対称性比較
    print(f'\n--- observed vs shuffled 比較 ---')
    asym_diff = asym_obs - asym_shuf
    print(f'  asymmetry observed > shuffled: {(asym_diff > 0).sum():,} ペア')
    print(f'  asymmetry max: observed {asym_obs.max():.4f} vs shuffled {asym_shuf.max():.4f}')
    print(f'  ratio: {asym_obs.max()/asym_shuf.max() if asym_shuf.max() > 0 else 0:.2f}x')

    print(f'\n=== Step C 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
