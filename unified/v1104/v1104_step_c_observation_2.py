#!/usr/bin/env python3
"""v1104 Step C — 観察 2: predecessor 連鎖の経路

設計書 §2.2 + Step A §1.4 確定 (判定語制限、GPT 追加 4):
- Code A は「連想」と判定しない、cid/atom/category/similarity 推移のみ記録
- 整理語は Web Claude Phase Result 領域

入力:
- attention_emit_seed{N}.parquet (predecessor_attention_ref、conscious 行)
- v10.6 window_trajectory (per (cid, window) rank_1_atom)
- v10.6 cid_atom_sim_matrix (cid 間類似度地形)

出力: observation_2_predecessor_chain.parquet
書込み: unified/v1104/outputs/main/ のみ
"""
from __future__ import annotations
import argparse, time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V106_MAIN = REPO_ROOT / 'developmental/v106/outputs/main'
V1101A_MAIN = REPO_ROOT / 'unified/v1101a/outputs/main'
OUT_MAIN = REPO_ROOT / 'unified/v1104/outputs/main'

WINDOW_RANGE = list(range(20, 70))  # Step A §5.1 確定
RNG_SEED = 42
N_SHUFFLE = 50


def category_of(atom: str) -> str:
    return atom.split('.')[0] if isinstance(atom, str) and '.' in atom else 'UNK'


def compute_observation_2(seed: int, verbose: bool = True) -> pd.DataFrame:
    t0 = time.time()
    # attention_emit 読み込み
    p = V1101A_MAIN / f'attention_emit_seed{seed}.parquet'
    em = pd.read_parquet(p, columns=['seed', 'window', 'change_scope', 'scope_id',
                                       'change_metric_type', 'attention_candidate_id',
                                       'predecessor_attention_ref', 'qc_regime'])
    em = em[em['window'].isin(WINDOW_RANGE)]
    em = em[em['qc_regime'] == 'conscious_dominant']
    em = em.dropna(subset=['predecessor_attention_ref'])
    em['attention_candidate_id'] = em['attention_candidate_id'].astype(int)
    em['predecessor_attention_ref'] = em['predecessor_attention_ref'].astype(int)
    if verbose:
        print(f'[seed {seed}] conscious + predecessor rows: {len(em):,}')

    # v10.6 per (cid, window) rank_1_atom
    win_p = V106_MAIN / 'window_trajectory' / f'window_cid_alignment_seed{seed}.csv'
    wt = pd.read_csv(win_p, usecols=['cognitive_id', 'window', 'rank_1_atom'])
    wt = wt[wt['window'].isin(WINDOW_RANGE)]
    rank1_map = wt.set_index(['cognitive_id', 'window'])['rank_1_atom'].to_dict()

    # cid_atom_sim_matrix → 228×228 cid pair cosine sim matrix を pre-compute (O(1) lookup)
    sim_p = V106_MAIN / f'cid_atom_sim_matrix_seed{seed}.parquet'
    sim_df = pd.read_parquet(sim_p)
    atom_cols = [c for c in sim_df.columns if c not in ('seed', 'cid')]
    cid_list = sim_df['cid'].astype(int).tolist()
    M = sim_df[atom_cols].fillna(0).to_numpy(dtype=np.float64)
    cid_to_idx = {c: i for i, c in enumerate(cid_list)}
    # 全ペア cosine sim を 1 回で計算 (228×228 行列)
    PAIR_SIM = cosine_similarity(M, M)  # shape (n_cid, n_cid)

    def cid_sim(c1: int, c2: int) -> float:
        i1 = cid_to_idx.get(c1)
        i2 = cid_to_idx.get(c2)
        if i1 is None or i2 is None:
            return np.nan
        return float(PAIR_SIM[i1, i2])

    # 各 edge: predecessor → attention_candidate の 1-step 遷移
    # per (scope, scope_id, metric_type) で window 順
    rng = np.random.default_rng(RNG_SEED + seed)

    rows = []
    for (scope, scope_id, mt), grp in em.groupby(['change_scope', 'scope_id', 'change_metric_type']):
        grp = grp.sort_values('window').reset_index(drop=True)
        # 連鎖の長さ (連続 conscious window 数)
        chain_len = len(grp)
        # 各 edge: cid_from = predecessor / cid_to = attention_candidate
        cid_seq_to = grp['attention_candidate_id'].tolist()
        cid_seq_from = grp['predecessor_attention_ref'].tolist()
        # 経路の分岐 / ループ判定
        n_unique_to = len(set(cid_seq_to))
        n_loops = sum(1 for i in range(len(cid_seq_to)) if cid_seq_from[i] == cid_seq_to[i])

        # 経路上の遷移指標 (atom 推移、category 推移、cid_atom_sim_matrix 類似度)
        atom_changes = 0
        cat_changes = 0
        sims = []
        for i, w in enumerate(grp['window'].tolist()):
            cid_to = int(cid_seq_to[i])
            cid_from = int(cid_seq_from[i])
            atom_to = rank1_map.get((cid_to, w))
            atom_from = rank1_map.get((cid_from, w))
            if isinstance(atom_to, str) and isinstance(atom_from, str):
                if atom_to != atom_from:
                    atom_changes += 1
                if category_of(atom_to) != category_of(atom_from):
                    cat_changes += 1
            s = cid_sim(cid_from, cid_to)
            if not np.isnan(s):
                sims.append(s)

        mean_sim = float(np.mean(sims)) if sims else np.nan

        # shuffle baseline: attention_candidate_id 列を permutation して同じ edge 計算
        baseline_sims = []
        for _ in range(N_SHUFFLE):
            shuffled = rng.permutation(cid_seq_to)
            ss = []
            for cf, ct in zip(cid_seq_from, shuffled):
                s = cid_sim(int(cf), int(ct))
                if not np.isnan(s):
                    ss.append(s)
            if ss:
                baseline_sims.append(float(np.mean(ss)))
        baseline_mean = float(np.mean(baseline_sims)) if baseline_sims else np.nan
        baseline_std = float(np.std(baseline_sims)) if baseline_sims else np.nan
        lift = (mean_sim - baseline_mean) if not (np.isnan(mean_sim) or np.isnan(baseline_mean)) else np.nan

        rows.append({
            'seed': seed,
            'change_scope': scope,
            'scope_id': scope_id,
            'change_metric_type': mt,
            'chain_length': chain_len,
            'n_unique_destinations': n_unique_to,
            'n_self_loops': n_loops,
            'n_atom_changes': atom_changes,
            'n_category_changes': cat_changes,
            'mean_sim_along_chain': mean_sim,
            'shuffle_baseline_sim_mean': baseline_mean,
            'shuffle_baseline_sim_std': baseline_std,
            'lift_over_baseline': lift,
        })

    df = pd.DataFrame(rows)
    if verbose:
        print(f'[seed {seed}] chains: {len(df)}, elapsed: {time.time()-t0:.1f}s')
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', default='0..23')
    args = ap.parse_args()
    lo, hi = args.seeds.split('..')
    seeds = list(range(int(lo), int(hi)+1))
    OUT_MAIN.mkdir(parents=True, exist_ok=True)

    print(f'=== v1104 Step C 観察 2 (predecessor 連鎖) ===')
    print(f'seeds: {seeds}, window: 20-69, shuffle baseline N={N_SHUFFLE} per chain')
    print()

    t_start = time.time()
    dfs = []
    for sd in seeds:
        dfs.append(compute_observation_2(sd))
    all_df = pd.concat(dfs, ignore_index=True)

    out = OUT_MAIN / 'observation_2_predecessor_chain.parquet'
    all_df.to_parquet(out, index=False)
    print(f'\nwrote {out} ({len(all_df):,} chains)')

    # サマリ
    print(f'\n=== 全 24 seeds サマリ ===')
    print(f'chain_length: mean={all_df["chain_length"].mean():.2f}, median={all_df["chain_length"].median()}, max={all_df["chain_length"].max()}')
    print(f'n_unique_destinations: mean={all_df["n_unique_destinations"].mean():.2f}')
    print(f'n_self_loops mean: {all_df["n_self_loops"].mean():.2f}')
    print(f'mean_sim_along_chain: {all_df["mean_sim_along_chain"].mean():.4f}')
    print(f'shuffle_baseline_sim_mean: {all_df["shuffle_baseline_sim_mean"].mean():.4f}')
    print(f'lift_over_baseline: {all_df["lift_over_baseline"].mean():.4f}')
    print(f'atom_changes per chain (mean): {(all_df["n_atom_changes"]/all_df["chain_length"]).mean():.4f}')
    print(f'category_changes per chain (mean): {(all_df["n_category_changes"]/all_df["chain_length"]).mean():.4f}')
    print()
    print('=== scope 別 sim と lift ===')
    g = all_df.groupby('change_scope').agg(
        n_chains=('chain_length', 'count'),
        chain_len_mean=('chain_length', 'mean'),
        sim_mean=('mean_sim_along_chain', 'mean'),
        baseline_mean=('shuffle_baseline_sim_mean', 'mean'),
        lift_mean=('lift_over_baseline', 'mean'),
        atom_chg_rate=('n_atom_changes', 'mean'),
    ).round(4)
    print(g.to_string())

    print(f'\ntotal elapsed: {time.time()-t_start:.1f}s')


if __name__ == '__main__':
    main()
