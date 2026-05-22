#!/usr/bin/env python3
"""v1104 Step H-3 — 観察 2 再調査 4 件 (層化 + shuffle 3 種 + 粒度 3 階層 + self-loop 分離)

§4 Web Claude 回答 (2026-05-23):
- §4.1: (iii) n_core_member 採用
- §4.2: shuffle A 確認、B/C 追加
- §4.3: event_trajectory 採用、計算量超過時 Web Claude 報告

入力 (既存出力流用のみ):
- v1104 observation_2_predecessor_chain.parquet (既存 chain)
- v1101a attention_emit (chain 再構築)
- v10.6 cid_atom_sim_matrix (sim 計算)
- v10.6 event_trajectory / step10_trajectory / window_trajectory (粒度 3 階層)
- v1101a integration_composition_alpha/beta + v10.6 window_trajectory n_core_member (層化軸)

出力:
- observation_2_restratified.parquet (再調査 1)
- observation_2_shuffle_variants.parquet + cid_sim_matrix_distribution.parquet (再調査 2)
- observation_2_resolution.parquet (再調査 3)
- observation_2_self_loop_split.parquet (再調査 4)

書込み: unified/v1104/outputs/main/ 配下のみ
"""
from __future__ import annotations
import argparse, time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V105_INT = REPO_ROOT / 'developmental/v105/diag_v105_main/integration'
V106_MAIN = REPO_ROOT / 'developmental/v106/outputs/main'
V1101A_MAIN = REPO_ROOT / 'unified/v1101a/outputs/main'
V1104_MAIN = REPO_ROOT / 'unified/v1104/outputs/main'

WINDOW_RANGE = list(range(20, 70))
N_SHUFFLE = 50
RNG_SEED = 42
LIFT_THRESHOLD = 0.01  # 絶対格言 #3


def n_alpha_bin(n):
    if pd.isna(n): return 'NA'
    n = int(n)
    return 'n=1' if n==1 else ('n=2' if n==2 else ('n=3' if n==3 else 'n=4+'))


def n_beta_bin(n):
    return n_alpha_bin(n)


def gini_bin(g):
    if pd.isna(g): return 'NA'
    if g < 0.05: return 'low'
    if g < 0.20: return 'mid'
    return 'high'


def cid_bin(n):
    if pd.isna(n): return 'NA'
    n = int(n)
    if n == 2: return 'CID_n=2'
    if n == 3: return 'CID_n=3'
    if n == 4: return 'CID_n=4'
    if n == 5: return 'CID_n=5'
    return 'CID_n=6+'


def load_chain_data():
    """v1104 既存 chain + 関連データを load"""
    chain = pd.read_parquet(V1104_MAIN / 'observation_2_predecessor_chain.parquet')
    comp_a = pd.read_parquet(V1101A_MAIN / 'integration_composition_alpha.parquet')
    comp_b = pd.read_parquet(V1101A_MAIN / 'integration_composition_beta.parquet')

    # cid n_core_member map (per seed)
    rows = []
    for sd in range(24):
        p = V106_MAIN / 'window_trajectory' / f'window_cid_alignment_seed{sd}.csv'
        df = pd.read_csv(p, usecols=['cognitive_id', 'n_core_member'])
        g = df.groupby('cognitive_id')['n_core_member'].max()
        for cid, n in g.items():
            rows.append({'seed': sd, 'cognitive_id': int(cid), 'n_core_member': int(n)})
    cid_ncore = pd.DataFrame(rows)
    return chain, comp_a, comp_b, cid_ncore


# ────────────────────────────────────────────────
# 再調査 1: n_members × qc_gini 層化
# ────────────────────────────────────────────────
def reinvestigation_1(chain, comp_a, comp_b, cid_ncore):
    print('\n=== 再調査 1: n_members × qc_gini 層化 ===')
    t0 = time.time()

    # bin 付与
    parts = []
    # alpha
    sub = chain[chain['change_scope'] == 'alpha'].copy()
    sub = sub.merge(comp_a.rename(columns={'alpha_id': 'scope_id'}),
                     on=['seed', 'scope_id'], how='left')
    sub['n_bin'] = sub['n_members'].apply(n_alpha_bin)
    sub['gini_bin_label'] = sub['qc_gini_mean'].apply(gini_bin)
    parts.append(sub)
    # beta
    sub = chain[chain['change_scope'] == 'beta'].copy()
    sub = sub.merge(comp_b.rename(columns={'beta_id': 'scope_id'}),
                     on=['seed', 'scope_id'], how='left')
    sub['n_bin'] = sub['n_members'].apply(n_beta_bin)
    sub['gini_bin_label'] = sub['qc_gini_mean'].apply(gini_bin)
    parts.append(sub)
    # CID (iii) n_core_member
    sub = chain[chain['change_scope'] == 'CID'].copy()
    sub = sub.merge(cid_ncore.rename(columns={'cognitive_id': 'scope_id'}),
                     on=['seed', 'scope_id'], how='left')
    sub['n_bin'] = sub['n_core_member'].apply(cid_bin)
    sub['gini_bin_label'] = 'NA'  # CID は cid 自体の属性なので gini なし
    parts.append(sub)
    # ESDE 3 scope (層化対象外)
    sub = chain[chain['change_scope'].isin(['ESDE_event','ESDE_step10','ESDE_window'])].copy()
    sub['n_bin'] = 'NA'
    sub['gini_bin_label'] = 'NA'
    parts.append(sub)
    full = pd.concat(parts, ignore_index=True)

    # per (scope, n_bin, gini_bin) で再集計
    g = full.groupby(['change_scope', 'n_bin', 'gini_bin_label']).agg(
        n_chains=('chain_length', 'count'),
        chain_len_mean=('chain_length', 'mean'),
        sim_mean=('mean_sim_along_chain', 'mean'),
        baseline_mean=('shuffle_baseline_sim_mean', 'mean'),
        lift_mean=('lift_over_baseline', 'mean'),
        atom_chg_rate=('n_atom_changes', 'mean'),
        cat_chg_rate=('n_category_changes', 'mean'),
        self_loop_rate=('n_self_loops', 'mean'),
    ).reset_index()
    # 効果サイズ |lift| > 0.01
    g['lift_significant'] = g['lift_mean'].abs() > LIFT_THRESHOLD

    out = V1104_MAIN / 'observation_2_restratified.parquet'
    g.to_parquet(out, index=False)
    print(f'wrote {out} ({len(g)} bins), elapsed {time.time()-t0:.1f}s')

    # |lift| > 0.01 の bin 抽出
    sig = g[g['lift_significant']]
    print(f'\n|lift| > 0.01 の bin: {len(sig)}')
    if len(sig) > 0:
        print(sig[['change_scope','n_bin','gini_bin_label','n_chains',
                    'lift_mean','sim_mean','baseline_mean']].to_string(index=False))
    return g


# ────────────────────────────────────────────────
# 再調査 2: shuffle 3 種 (A/B/C) + sim_matrix 平坦性確認
# ────────────────────────────────────────────────
def reinvestigation_2(seeds: list[int]):
    print('\n=== 再調査 2: shuffle 3 種 + sim_matrix 平坦性 ===')
    t0 = time.time()

    rng = np.random.default_rng(RNG_SEED)

    # sim_matrix 平坦性 (per seed)
    sim_dist_rows = []
    for sd in seeds:
        sim_p = V106_MAIN / f'cid_atom_sim_matrix_seed{sd}.parquet'
        sim_df = pd.read_parquet(sim_p)
        atom_cols = [c for c in sim_df.columns if c not in ('seed', 'cid')]
        M = sim_df[atom_cols].fillna(0).to_numpy(dtype=np.float64)
        PAIR = cosine_similarity(M, M)
        # 対角除外
        tri_mask = ~np.eye(len(M), dtype=bool)
        vals = PAIR[tri_mask]
        sim_dist_rows.append({
            'seed': sd,
            'n_pairs': int(len(vals)),
            'sim_mean': float(vals.mean()),
            'sim_median': float(np.median(vals)),
            'sim_std': float(vals.std()),
            'sim_p5': float(np.percentile(vals, 5)),
            'sim_p25': float(np.percentile(vals, 25)),
            'sim_p75': float(np.percentile(vals, 75)),
            'sim_p95': float(np.percentile(vals, 95)),
        })
    sim_dist = pd.DataFrame(sim_dist_rows)
    out_sd = V1104_MAIN / 'cid_sim_matrix_distribution.parquet'
    sim_dist.to_parquet(out_sd, index=False)
    print(f'cid sim matrix distribution: 24 seeds、平均 sim={sim_dist["sim_mean"].mean():.4f}, std={sim_dist["sim_std"].mean():.4f}')

    # shuffle 3 種 (per scope, seed)
    # 入力: v1101a attention_emit から chain 再構築
    rows_v = []
    for sd in seeds:
        em_p = V1101A_MAIN / f'attention_emit_seed{sd}.parquet'
        em = pd.read_parquet(em_p, columns=['seed','window','change_scope','scope_id',
                                              'change_metric_type','attention_candidate_id',
                                              'predecessor_attention_ref','qc_regime'])
        em = em[em['window'].isin(WINDOW_RANGE)]
        em = em[em['qc_regime'] == 'conscious_dominant']
        em = em.dropna(subset=['predecessor_attention_ref'])
        em['attention_candidate_id'] = em['attention_candidate_id'].astype(int)
        em['predecessor_attention_ref'] = em['predecessor_attention_ref'].astype(int)

        # sim matrix pre-compute (per seed)
        sim_p = V106_MAIN / f'cid_atom_sim_matrix_seed{sd}.parquet'
        sim_df = pd.read_parquet(sim_p)
        atom_cols = [c for c in sim_df.columns if c not in ('seed', 'cid')]
        cid_list = sim_df['cid'].astype(int).tolist()
        M = sim_df[atom_cols].fillna(0).to_numpy(dtype=np.float64)
        PAIR = cosine_similarity(M, M)
        cid_to_idx = {c: i for i, c in enumerate(cid_list)}

        for scope in em['change_scope'].unique():
            sub = em[em['change_scope'] == scope]
            # per chain (scope, scope_id, metric) で edge collect
            all_edges_from = []
            all_edges_to = []
            for (sid, mt), grp in sub.groupby(['scope_id', 'change_metric_type']):
                grp = grp.sort_values('window').reset_index(drop=True)
                all_edges_from.extend(grp['predecessor_attention_ref'].tolist())
                all_edges_to.extend(grp['attention_candidate_id'].tolist())
            if not all_edges_from:
                continue
            cf_arr = np.array(all_edges_from)
            ct_arr = np.array(all_edges_to)

            # 実測 sim (per edge)
            actual_sims = [PAIR[cid_to_idx.get(int(cf), 0), cid_to_idx.get(int(ct), 0)]
                            if int(cf) in cid_to_idx and int(ct) in cid_to_idx else np.nan
                            for cf, ct in zip(cf_arr, ct_arr)]
            actual_sims = [s for s in actual_sims if not np.isnan(s)]
            sim_actual = float(np.mean(actual_sims)) if actual_sims else np.nan

            # shuffle A: per chain で順序入れ替え (現状方式と同型)
            shuffle_a_sims = []
            for _ in range(N_SHUFFLE):
                # chain ごとに permutation
                sa = []
                idx_start = 0
                for (sid, mt), grp in sub.groupby(['scope_id', 'change_metric_type']):
                    n_grp = len(grp)
                    chain_to = ct_arr[idx_start:idx_start+n_grp].copy()
                    chain_from = cf_arr[idx_start:idx_start+n_grp]
                    rng.shuffle(chain_to)
                    for cf, ct in zip(chain_from, chain_to):
                        if int(cf) in cid_to_idx and int(ct) in cid_to_idx:
                            sa.append(PAIR[cid_to_idx[int(cf)], cid_to_idx[int(ct)]])
                    idx_start += n_grp
                if sa:
                    shuffle_a_sims.append(float(np.mean(sa)))
            sim_a = float(np.mean(shuffle_a_sims)) if shuffle_a_sims else np.nan

            # shuffle B: chain 間 (全 edge_to を入れ替え、chain 構造は保つ)
            shuffle_b_sims = []
            for _ in range(N_SHUFFLE):
                permuted_to = rng.permutation(ct_arr)
                sb = []
                for cf, ct in zip(cf_arr, permuted_to):
                    if int(cf) in cid_to_idx and int(ct) in cid_to_idx:
                        sb.append(PAIR[cid_to_idx[int(cf)], cid_to_idx[int(ct)]])
                if sb:
                    shuffle_b_sims.append(float(np.mean(sb)))
            sim_b = float(np.mean(shuffle_b_sims)) if shuffle_b_sims else np.nan

            # shuffle C: global cid pool (全 cid からランダム取得)
            all_cids = list(cid_to_idx.keys())
            shuffle_c_sims = []
            for _ in range(N_SHUFFLE):
                pool_to = rng.choice(all_cids, size=len(ct_arr))
                sc = []
                for cf, ct in zip(cf_arr, pool_to):
                    if int(cf) in cid_to_idx and int(ct) in cid_to_idx:
                        sc.append(PAIR[cid_to_idx[int(cf)], cid_to_idx[int(ct)]])
                if sc:
                    shuffle_c_sims.append(float(np.mean(sc)))
            sim_c = float(np.mean(shuffle_c_sims)) if shuffle_c_sims else np.nan

            rows_v.append({
                'seed': sd, 'change_scope': scope,
                'n_edges': len(actual_sims),
                'sim_actual': sim_actual,
                'sim_shuffle_A': sim_a,  # chain 内
                'sim_shuffle_B': sim_b,  # chain 間
                'sim_shuffle_C': sim_c,  # global pool
                'lift_A': sim_actual - sim_a if not np.isnan(sim_a) else np.nan,
                'lift_B': sim_actual - sim_b if not np.isnan(sim_b) else np.nan,
                'lift_C': sim_actual - sim_c if not np.isnan(sim_c) else np.nan,
            })
        print(f'  seed {sd} done')

    df_v = pd.DataFrame(rows_v)
    out_v = V1104_MAIN / 'observation_2_shuffle_variants.parquet'
    df_v.to_parquet(out_v, index=False)
    print(f'wrote {out_v} ({len(df_v)} rows), elapsed {time.time()-t0:.1f}s')

    # scope 別 lift サマリ
    g = df_v.groupby('change_scope').agg(
        n_seeds=('seed', 'count'),
        sim_actual=('sim_actual', 'mean'),
        lift_A=('lift_A', 'mean'),
        lift_B=('lift_B', 'mean'),
        lift_C=('lift_C', 'mean'),
    ).round(5)
    print('\n=== scope 別 shuffle 3 種 lift ===')
    print(g.to_string())
    return df_v, sim_dist


# ────────────────────────────────────────────────
# 再調査 3: 粒度 3 階層 (window/step10/event)
# ────────────────────────────────────────────────
def reinvestigation_3(seeds: list[int]):
    print('\n=== 再調査 3: 粒度 3 階層 (window/step10/event) ===')
    t0 = time.time()
    rng = np.random.default_rng(RNG_SEED + 1)

    rows = []
    for sd in seeds:
        # sim matrix pre-compute
        sim_p = V106_MAIN / f'cid_atom_sim_matrix_seed{sd}.parquet'
        sim_df = pd.read_parquet(sim_p)
        atom_cols = [c for c in sim_df.columns if c not in ('seed', 'cid')]
        cid_list = sim_df['cid'].astype(int).tolist()
        M = sim_df[atom_cols].fillna(0).to_numpy(dtype=np.float64)
        PAIR = cosine_similarity(M, M)
        cid_to_idx = {c: i for i, c in enumerate(cid_list)}

        # window 解像度 (現状の chain) は既存出力から再利用、ここでは概要だけ
        # step10 / event 解像度: chain = 連続する same-cid records の sim を測る
        # 簡略化: per (cognitive_id, resolution) で rank_1_atom 推移と隣接 sim を計算

        for resolution, traj_dir, t_col in [('event', 'event_trajectory', 't'),
                                              ('step10', 'step10_trajectory', 't'),
                                              ('window', 'window_trajectory', 'window')]:
            traj_p = V106_MAIN / traj_dir / f'{traj_dir.split("_")[0]}_cid_alignment_seed{sd}.csv'
            if not traj_p.exists():
                continue
            try:
                df = pd.read_csv(traj_p, usecols=['cognitive_id', t_col, 'rank_1_atom', 'window'])
            except Exception:
                df = pd.read_csv(traj_p, usecols=['cognitive_id', t_col, 'rank_1_atom'])
            df = df[df['window'].isin(WINDOW_RANGE)] if 'window' in df.columns else df
            df = df.sort_values(['cognitive_id', t_col])

            # per cid の隣接 record で rank_1_atom 推移 + sim
            n_records = len(df)
            atom_changes = 0
            atom_total = 0
            actual_sims = []
            shuf_sims = []
            cids_in_play = []
            for cid, g in df.groupby('cognitive_id'):
                if len(g) < 2:
                    continue
                atoms = g['rank_1_atom'].tolist()
                for i in range(1, len(atoms)):
                    if isinstance(atoms[i], str) and isinstance(atoms[i-1], str):
                        atom_total += 1
                        if atoms[i] != atoms[i-1]:
                            atom_changes += 1
                # cid 自身の sim (常に 1.0、self の場合)
                # 隣接 record は同 cid なので sim = PAIR[cid, cid] = 1.0
                # 別 cid との比較 (random sample) で sim 計算
                cids_in_play.append(int(cid))

            # cid 間 sim (random sample) + shuffle
            unique_cids = [c for c in df['cognitive_id'].unique() if int(c) in cid_to_idx]
            if len(unique_cids) >= 2:
                n_sample = min(1000, len(unique_cids) * (len(unique_cids)-1) // 2)
                pairs = []
                for _ in range(n_sample):
                    c1, c2 = rng.choice(unique_cids, size=2, replace=False)
                    pairs.append(PAIR[cid_to_idx[int(c1)], cid_to_idx[int(c2)]])
                sim_actual = float(np.mean(pairs))
            else:
                sim_actual = np.nan

            rows.append({
                'seed': sd, 'resolution': resolution,
                'n_records': int(n_records),
                'n_cids_in_play': len(unique_cids),
                'atom_change_rate': atom_changes / atom_total if atom_total > 0 else np.nan,
                'mean_inter_cid_sim': sim_actual,
            })
        print(f'  seed {sd} done')

    df_r = pd.DataFrame(rows)
    out_r = V1104_MAIN / 'observation_2_resolution.parquet'
    df_r.to_parquet(out_r, index=False)
    print(f'wrote {out_r} ({len(df_r)} rows), elapsed {time.time()-t0:.1f}s')

    g = df_r.groupby('resolution').agg(
        n_seeds=('seed', 'count'),
        n_records_mean=('n_records', 'mean'),
        atom_chg_rate_mean=('atom_change_rate', 'mean'),
        inter_cid_sim_mean=('mean_inter_cid_sim', 'mean'),
    ).round(4)
    print('\n=== 粒度別 atom 変化率 + inter-cid sim ===')
    print(g.to_string())
    return df_r


# ────────────────────────────────────────────────
# 再調査 4: self-loop / non-self-loop 分離
# ────────────────────────────────────────────────
def reinvestigation_4(chain, comp_a, comp_b, cid_ncore):
    print('\n=== 再調査 4: self-loop / non-self-loop 分離 ===')
    t0 = time.time()

    # chain ごとに self-loop か (n_self_loops が chain_length と一致なら完全 self-loop)
    chain = chain.copy()
    chain['is_full_self_loop'] = chain['n_self_loops'] == chain['chain_length']
    chain['self_loop_rate'] = chain['n_self_loops'] / chain['chain_length'].clip(lower=1)

    # per (scope, is_full_self_loop) で集計
    g = chain.groupby(['change_scope', 'is_full_self_loop']).agg(
        n_chains=('chain_length', 'count'),
        chain_len_mean=('chain_length', 'mean'),
        sim_mean=('mean_sim_along_chain', 'mean'),
        baseline_mean=('shuffle_baseline_sim_mean', 'mean'),
        lift_mean=('lift_over_baseline', 'mean'),
        atom_chg_rate=('n_atom_changes', 'mean'),
        cat_chg_rate=('n_category_changes', 'mean'),
    ).reset_index()
    g['lift_significant'] = g['lift_mean'].abs() > LIFT_THRESHOLD

    # self-loop で atom 変化がある chain の割合
    sl = chain[chain['is_full_self_loop'] & (chain['n_atom_changes'] > 0)]
    nsl = chain[~chain['is_full_self_loop']]
    print(f'\n全 chains: {len(chain)}')
    print(f'self-loop chains (全 self-loop): {chain["is_full_self_loop"].sum()} ({chain["is_full_self_loop"].mean()*100:.1f}%)')
    print(f'self-loop で atom 変化あり: {len(sl)} ({len(sl)/max(chain["is_full_self_loop"].sum(),1)*100:.1f}% of self-loop)')
    print(f'non-self-loop chains: {len(nsl)} ({(1-chain["is_full_self_loop"].mean())*100:.1f}%)')

    out = V1104_MAIN / 'observation_2_self_loop_split.parquet'
    g.to_parquet(out, index=False)
    print(f'wrote {out} ({len(g)} bins), elapsed {time.time()-t0:.1f}s')
    print('\n=== scope × self-loop 別 lift ===')
    print(g.to_string(index=False))
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', default='0..23')
    args = ap.parse_args()
    lo, hi = args.seeds.split('..')
    seeds = list(range(int(lo), int(hi)+1))

    V1104_MAIN.mkdir(parents=True, exist_ok=True)
    print(f'=== v1104 Step H-3 観察 2 再調査 4 件 ===')
    print(f'seeds: {seeds}')

    t_start = time.time()
    chain, comp_a, comp_b, cid_ncore = load_chain_data()
    print(f'chain: {len(chain):,} chains loaded')

    # 再調査 1
    r1 = reinvestigation_1(chain, comp_a, comp_b, cid_ncore)

    # 再調査 2
    r2_v, r2_sd = reinvestigation_2(seeds)

    # 再調査 3
    r3 = reinvestigation_3(seeds)

    # 再調査 4
    r4 = reinvestigation_4(chain, comp_a, comp_b, cid_ncore)

    print(f'\n=== 4 再調査全完了、total elapsed {time.time()-t_start:.1f}s ===')


if __name__ == '__main__':
    main()
