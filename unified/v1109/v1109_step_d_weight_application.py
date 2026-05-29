#!/usr/bin/env python3
"""v1109 Step D — 重み適用機構 (試行層) + Gemini 3 大ブレーキ

Step C で構築した W_observed / W_shuffled / W_frequency を各 turn の確率分布に適用。
Gemini 3 大ブレーキ (Code A 案、Q1-Q6 Taka 承認 2026-05-30):
- ブレーキ 1: 重み総和保存 (毎 event 終了で正規化)
- ブレーキ 2: エントロピー連動 Δw (本 Step では fixed Δw、Step G で連動)
- ブレーキ 3: 物理層接続可能性 (cid_atom_sim_matrix で抑制)

適用式 (Code A Q1 提案、α=0.5):
  P'_t+1(A_k) = P_t+1(A_k) × (1 + α × W_{prev_top1, k})
  正規化: Σ P'_t+1 = 1

入力:
- unified/v1109/outputs/main/W_matrices.npz
- unified/v1109/outputs/main/atom_universe.parquet
- unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet

出力:
- unified/v1109/outputs/main/applied_distributions.parquet
- unified/v1109/outputs/main/observation_D_summary.parquet
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V1108A_MAIN = REPO / 'unified/v1108a/outputs/main'
V1109_MAIN = REPO / 'unified/v1109/outputs/main'

ATOM_TOPK = 10
ALPHA = 0.5  # Code A Q1 提案 (Taka 承認)


def normalize_W(W):
    """ブレーキ 1: 行毎正規化 (各 prev_atom の遷移先確率合計を 1 に)"""
    row_sums = W.sum(axis=1, keepdims=True)
    return np.where(row_sums > 0, W / row_sums, W)


def apply_weight_to_distribution(probs, atoms_idx, W, alpha=ALPHA):
    """
    probs: (n_atoms_top_k,) of P_t+1 候補確率
    atoms_idx: (n_atoms_top_k,) of atom idx
    W: (n_atoms, n_atoms) 正規化済み weight matrix
    prev_idx: 直前 turn の top1 atom idx
    """
    pass  # 実際の適用はメインループ内


def compute_entropy(probs):
    p = probs[probs > 0]
    if len(p) == 0:
        return 0.0
    p = p / p.sum()
    return float(-np.sum(p * np.log(p + 1e-12)))


def main():
    print('=== v1109 Step D — 重み適用 + Gemini 3 大ブレーキ ===\n')
    t0 = time.time()

    # データ読み込み
    atom_df = pd.read_parquet(V1109_MAIN / 'atom_universe.parquet')
    atoms = atom_df['atom_full'].tolist()
    atom_to_idx = dict(zip(atoms, atom_df['atom_idx']))
    n_atoms = len(atoms)

    W_mat = np.load(V1109_MAIN / 'W_matrices.npz', allow_pickle=True)
    conditions = {
        'baseline': W_mat['W_baseline'],
        'observed': W_mat['W_observed'],
        'shuffled': W_mat['W_shuffled'],
        'frequency': W_mat['W_frequency'],
    }

    # ブレーキ 1: 重み総和保存正規化 (行単位)
    print('[1] ブレーキ 1: 重み総和保存正規化 (行単位)')
    W_normalized = {}
    for name, W in conditions.items():
        W_normalized[name] = normalize_W(W)
        print(f'  {name}: 行和 mean={W_normalized[name].sum(axis=1).mean():.4f}')

    # ブレーキ 3: 物理層接続可能性 (cid_atom_sim_matrix で抑制)
    # 各 atom に対する全 seed 平均 sim を計算
    print('\n[2] ブレーキ 3: 物理層接続可能性 (cid_atom_sim_matrix mean)')
    atom_to_sim = {a: [] for a in atoms}
    for sd in range(24):
        fp = V106_MAIN / f'cid_atom_sim_matrix_seed{sd}.parquet'
        sim_df = pd.read_parquet(fp)
        atom_cols = [c for c in sim_df.columns if c not in ('seed', 'cid')]
        for a in atoms:
            if a in atom_cols:
                atom_to_sim[a].append(float(sim_df[a].mean()))
    sim_avg = np.array([np.mean(atom_to_sim[a]) if atom_to_sim[a] else 0 for a in atoms])
    sim_avg_norm = sim_avg / sim_avg.max() if sim_avg.max() > 0 else sim_avg
    print(f'  接続可能性 mean: {sim_avg.mean():.4f}, min={sim_avg.min():.4f}, max={sim_avg.max():.4f}')

    # ブレーキ 3 を W に適用: W_ij × sim_avg_norm[j]
    for name in W_normalized:
        W_normalized[name] = W_normalized[name] * sim_avg_norm[None, :]

    # (3) 各 turn で次 turn 候補確率に適用
    print('\n[3] 各 turn で重み適用 + entropy/max_prob 測定')
    hist = pd.read_parquet(V1108A_MAIN / 'self_dialogue_with_atom_probs.parquet')

    applied_rows = []
    atom_top_cols = [f'atom_top{i+1}' for i in range(ATOM_TOPK)]
    prob_top_cols = [f'prob_top{i+1}' for i in range(ATOM_TOPK)]

    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn').reset_index(drop=True)
        n = len(grp_sorted)
        if n < 2:
            continue
        for t in range(n - 1):
            # turn t の top1 atom = prev
            prev_atom = grp_sorted.iloc[t]['atom_top1']
            if prev_atom is None or prev_atom not in atom_to_idx:
                continue
            prev_idx = atom_to_idx[prev_atom]

            # turn t+1 の top-K candidate
            cand_atoms = grp_sorted.iloc[t+1][atom_top_cols].values
            cand_probs = grp_sorted.iloc[t+1][prob_top_cols].values.astype(np.float64)
            cand_idx = np.array([atom_to_idx.get(a, -1) for a in cand_atoms], dtype=np.int32)
            actual_next = grp_sorted.iloc[t+1]['atom_top1']

            for cname, W_n in W_normalized.items():
                # 重み参照: W[prev_idx, cand_idx]
                w_vec = np.zeros(ATOM_TOPK)
                for k in range(ATOM_TOPK):
                    if cand_idx[k] >= 0:
                        w_vec[k] = W_n[prev_idx, cand_idx[k]]

                # 適用: P' = P × (1 + α × w)
                p_orig = cand_probs.copy()
                p_new = p_orig * (1 + ALPHA * w_vec)
                p_new = p_new / p_new.sum() if p_new.sum() > 0 else p_orig

                # 新 top1
                top1_idx = int(np.argmax(p_new))
                new_top1 = cand_atoms[top1_idx]
                # 一致 (heldout_lift 計算用)
                hit = (new_top1 == actual_next) if new_top1 is not None else False

                applied_rows.append({
                    'seed': int(sd), 'start_cid': int(sc), 'turn': t,
                    'condition': cname,
                    'prev_atom': prev_atom,
                    'orig_top1': cand_atoms[int(np.argmax(p_orig))] if p_orig.sum() > 0 else None,
                    'new_top1': new_top1,
                    'actual_next': actual_next,
                    'hit_actual': bool(hit),
                    'entropy_orig': compute_entropy(p_orig),
                    'entropy_new': compute_entropy(p_new),
                    'max_prob_orig': float(p_orig.max()),
                    'max_prob_new': float(p_new.max()),
                })

    applied_df = pd.DataFrame(applied_rows)
    applied_df.to_parquet(V1109_MAIN / 'applied_distributions.parquet', index=False)
    print(f'  applied entries: {len(applied_df):,}')

    # (4) 条件別集計
    print('\n[4] 条件別集計')
    cond_summary = applied_df.groupby('condition').agg(
        n=('seed', 'count'),
        hit_rate=('hit_actual', 'mean'),
        entropy_orig_mean=('entropy_orig', 'mean'),
        entropy_new_mean=('entropy_new', 'mean'),
        max_prob_orig_mean=('max_prob_orig', 'mean'),
        max_prob_new_mean=('max_prob_new', 'mean'),
    ).round(4).reset_index()
    cond_summary['entropy_change'] = cond_summary['entropy_new_mean'] - cond_summary['entropy_orig_mean']
    cond_summary['max_prob_change'] = cond_summary['max_prob_new_mean'] - cond_summary['max_prob_orig_mean']
    cond_summary.to_parquet(V1109_MAIN / 'observation_D_summary.parquet', index=False)
    print(cond_summary.to_string(index=False))

    # baseline hit rate との差 = lift
    baseline_hit = cond_summary[cond_summary['condition']=='baseline']['hit_rate'].iloc[0]
    print(f'\n  baseline hit rate: {baseline_hit:.4f}')
    for _, r in cond_summary.iterrows():
        if r['condition'] != 'baseline':
            lift = r['hit_rate'] - baseline_hit
            print(f'  {r["condition"]} lift over baseline: {lift:+.4f}')

    print(f'\n=== Step D 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
