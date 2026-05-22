#!/usr/bin/env python3
"""v1104 Step H-4 観察 3 再調査 4 件

観察 3 初版 r=0.157 (trajectory stability ↔ response_max_prob 弱い相関) を
観察 2 の経験 (lift=0 は shuffle 種別 A 固有) と同じ視点で再調査する。

R1: 層化 (qc_regime × sim_basis × k = 12 strata) で相関分離
R2: weighting (n_chains 加重 vs 一様)、receiver_bin 粒度の影響
R3: 代替指標ペア (stability vs entropy、diffusion vs max_prob、chain_len vs max_prob)
R4: shuffle baseline (chain内 cid permutation で trajectory_stability 再計算 → 相関)

判定回避、判定語制限、selector 化禁止、|r| > 0.1 を弱、|r| > 0.3 を中、|r| > 0.5 を強の参考ガイドのみ。
"""
from __future__ import annotations
import argparse, time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1101A_MAIN = REPO_ROOT / 'unified/v1101a/outputs/main'
V1103_MAIN = REPO_ROOT / 'unified/v1103/outputs/main'
V1104_MAIN = REPO_ROOT / 'unified/v1104/outputs/main'
V106_MAIN = REPO_ROOT / 'developmental/v106/outputs/main'

WINDOW_RANGE = range(20, 70)


def load_response_metrics() -> pd.DataFrame:
    """v1103 response_atom_distribution から per (receiver_bin, metric, sim_basis, k) で
    max_prob / entropy / gini / top3_mass"""
    dist = pd.read_parquet(V1103_MAIN / 'response_atom_distribution.parquet')
    rows = []
    for (rbin, mt, sb, k), grp in dist.groupby(['receiver_bin', 'change_metric_type',
                                                  'sim_basis', 'k']):
        probs = np.sort(grp['response_prob'].to_numpy())[::-1]
        if len(probs) == 0:
            continue
        max_prob = float(probs[0])
        p_nonzero = probs[probs > 0]
        entropy = float(-np.sum(p_nonzero * np.log(p_nonzero))) if len(p_nonzero) > 0 else 0.0
        top3_mass = float(probs[:3].sum())
        gini = float(1 - np.sum(probs ** 2))
        rows.append({
            'receiver_bin': rbin, 'change_metric_type': mt,
            'sim_basis': sb, 'k': k,
            'response_max_prob': max_prob, 'response_entropy': entropy,
            'response_top3_mass': top3_mass, 'response_gini': gini,
            'n_candidates': len(probs),
        })
    return pd.DataFrame(rows)


def trajectory_metrics_per_chain(seed: int, shuffle_mode: str = 'none',
                                   rng: np.random.Generator | None = None) -> pd.DataFrame:
    """compute per-chain trajectory_stability with optional cid shuffle.

    shuffle_mode:
      'none' : 実 chain 系列
      'within': chain 内 cid 系列を permutation
    """
    em = pd.read_parquet(V1101A_MAIN / f'attention_emit_seed{seed}.parquet',
                          columns=['seed','window','change_scope','scope_id',
                                   'change_metric_type','attention_candidate_id','qc_regime'])
    em = em[em['window'].isin(WINDOW_RANGE)]
    em = em.dropna(subset=['attention_candidate_id'])
    em['attention_candidate_id'] = em['attention_candidate_id'].astype(int)
    if rng is None:
        rng = np.random.default_rng(seed * 7919 + 11)

    rows = []
    for (sc, sid, mt, rg), grp in em.groupby(['change_scope','scope_id',
                                                'change_metric_type','qc_regime']):
        grp = grp.sort_values('window').reset_index(drop=True)
        n = len(grp)
        if n < 2:
            continue
        cands = grp['attention_candidate_id'].to_numpy()
        if shuffle_mode == 'within':
            cands = rng.permutation(cands)
        n_same = int(np.sum(cands[1:] == cands[:-1]))
        stability = n_same / (n - 1)
        unique_c = int(len(set(cands.tolist())))
        rows.append({'seed': seed, 'change_scope': sc, 'scope_id': sid,
                     'change_metric_type': mt, 'qc_regime': rg,
                     'chain_length': n, 'trajectory_stability': stability,
                     'trajectory_unique_candidates': unique_c,
                     'diffusion_ratio': unique_c / n})
    return pd.DataFrame(rows)


def n_alpha_bin(n):
    if pd.isna(n): return 'NA'
    n = int(n)
    if n == 1: return 'alpha_n=1'
    if n == 2: return 'alpha_n=2'
    if n == 3: return 'alpha_n=3'
    return 'alpha_n=4+'


def n_beta_bin(n):
    if pd.isna(n): return 'NA'
    n = int(n)
    if n == 1: return 'beta_n=1'
    if n == 2: return 'beta_n=2'
    if n == 3: return 'beta_n=3'
    return 'beta_n=4+'


def gini_bin(g):
    if pd.isna(g): return 'NA'
    if g < 0.05: return 'gini=low'
    if g < 0.20: return 'gini=mid'
    return 'gini=high'


def cid_bin(n):
    if pd.isna(n): return 'NA'
    n = int(n)
    if n == 2: return 'CID_n=2'
    if n == 3: return 'CID_n=3'
    if n == 4: return 'CID_n=4'
    if n == 5: return 'CID_n=5'
    return 'CID_n=6+'


def aggregate_traj(traj_all: pd.DataFrame) -> pd.DataFrame:
    """per receiver_bin × metric × qc_regime aggregate trajectory metrics."""
    seeds = sorted(traj_all['seed'].unique().tolist())
    comp_a = pd.read_parquet(V1101A_MAIN / 'integration_composition_alpha.parquet')
    comp_b = pd.read_parquet(V1101A_MAIN / 'integration_composition_beta.parquet')
    cid_ncore_rows = []
    for sd in seeds:
        pc = V106_MAIN / 'window_trajectory' / f'window_cid_alignment_seed{sd}.csv'
        if pc.exists():
            d = pd.read_csv(pc, usecols=['cognitive_id', 'n_core_member'])
            for cid, n in d.groupby('cognitive_id')['n_core_member'].max().items():
                cid_ncore_rows.append({'seed': sd, 'scope_id': int(cid),
                                        'n_core_member': int(n)})
    cid_ncore = pd.DataFrame(cid_ncore_rows)

    parts = []
    keep_cols = ['seed','change_scope','scope_id','change_metric_type','qc_regime',
                 'chain_length','trajectory_stability','trajectory_unique_candidates',
                 'diffusion_ratio','receiver_bin']
    # alpha
    s = traj_all[traj_all['change_scope'] == 'alpha'].merge(
        comp_a.rename(columns={'alpha_id': 'scope_id'}), on=['seed', 'scope_id'], how='left'
    )
    s['receiver_bin'] = s['n_members'].apply(n_alpha_bin) + ' / ' + s['qc_gini_mean'].apply(gini_bin)
    parts.append(s[keep_cols])
    # beta
    s = traj_all[traj_all['change_scope'] == 'beta'].merge(
        comp_b.rename(columns={'beta_id': 'scope_id'}), on=['seed', 'scope_id'], how='left'
    )
    s['receiver_bin'] = s['n_members'].apply(n_beta_bin) + ' / ' + s['qc_gini_mean'].apply(gini_bin)
    parts.append(s[keep_cols])
    # CID
    s = traj_all[traj_all['change_scope'] == 'CID'].merge(
        cid_ncore, on=['seed', 'scope_id'], how='left'
    )
    s['receiver_bin'] = s['n_core_member'].apply(cid_bin)
    parts.append(s[keep_cols])
    # ESDE 系列
    s = traj_all[traj_all['change_scope'].str.startswith('ESDE')].copy()
    s['receiver_bin'] = s['change_scope']
    parts.append(s[keep_cols])

    rb = pd.concat(parts, ignore_index=True)
    agg = rb.groupby(['receiver_bin', 'change_metric_type', 'qc_regime']).agg(
        n_chains=('chain_length', 'count'),
        chain_len_mean=('chain_length', 'mean'),
        traj_stability_mean=('trajectory_stability', 'mean'),
        traj_unique_mean=('trajectory_unique_candidates', 'mean'),
        diffusion_ratio_mean=('diffusion_ratio', 'mean'),
    ).reset_index()
    return agg


def safe_pearson(x, y, w=None):
    x = np.asarray(x); y = np.asarray(y)
    mask = ~(np.isnan(x) | np.isnan(y))
    x = x[mask]; y = y[mask]
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
        return (np.nan, np.nan, len(x))
    if w is None:
        r, p = pearsonr(x, y)
        return (float(r), float(p), len(x))
    w = np.asarray(w)[mask].astype(float)
    if w.sum() == 0:
        return (np.nan, np.nan, len(x))
    mx = np.average(x, weights=w); my = np.average(y, weights=w)
    cov = np.average((x - mx) * (y - my), weights=w)
    sx = np.sqrt(np.average((x - mx) ** 2, weights=w))
    sy = np.sqrt(np.average((y - my) ** 2, weights=w))
    if sx == 0 or sy == 0:
        return (np.nan, np.nan, len(x))
    return (float(cov / (sx * sy)), np.nan, len(x))


# ---------- 再調査 1: 層化 ----------
def reinvestigation_1(merged: pd.DataFrame) -> pd.DataFrame:
    """qc_regime × sim_basis × k で相関分離"""
    rows = []
    for (qr, sb, k), grp in merged.groupby(['qc_regime', 'sim_basis', 'k']):
        for x_col, y_col in [('traj_stability_mean', 'response_max_prob'),
                              ('diffusion_ratio_mean', 'response_entropy')]:
            r, p, n = safe_pearson(grp[x_col], grp[y_col])
            rs, ps, _ = (np.nan, np.nan, n)
            if n >= 3 and grp[x_col].std() > 0 and grp[y_col].std() > 0:
                sub = grp[[x_col, y_col]].dropna()
                rs, ps = spearmanr(sub[x_col], sub[y_col])
            rows.append({
                'qc_regime': qr, 'sim_basis': sb, 'k': k,
                'pair': f'{x_col}_vs_{y_col}',
                'pearson_r': r, 'pearson_p': p,
                'spearman_r': float(rs), 'spearman_p': float(ps),
                'n': n,
                'significant_strong': not np.isnan(r) and abs(r) > 0.5,
                'significant_mid': not np.isnan(r) and abs(r) > 0.3,
                'significant_weak': not np.isnan(r) and abs(r) > 0.1,
            })
    df = pd.DataFrame(rows)
    out = V1104_MAIN / 'observation_3_stratified.parquet'
    df.to_parquet(out, index=False)
    print(f'  R1 wrote {out.name} ({len(df)} rows)')
    return df


# ---------- 再調査 2: weighting / pooled ----------
def reinvestigation_2(merged: pd.DataFrame) -> pd.DataFrame:
    """n_chains 加重 vs 一様、scope 別の相関"""
    rows = []
    for pair, (xc, yc) in [
        ('stability_vs_maxprob', ('traj_stability_mean', 'response_max_prob')),
        ('stability_vs_entropy', ('traj_stability_mean', 'response_entropy')),
        ('diffusion_vs_entropy', ('diffusion_ratio_mean', 'response_entropy')),
        ('diffusion_vs_maxprob', ('diffusion_ratio_mean', 'response_max_prob')),
        ('chain_len_vs_maxprob', ('chain_len_mean', 'response_max_prob')),
        ('stability_vs_top3', ('traj_stability_mean', 'response_top3_mass')),
        ('stability_vs_gini', ('traj_stability_mean', 'response_gini')),
    ]:
        # all pooled
        r_u, p_u, n = safe_pearson(merged[xc], merged[yc])
        r_w, _, _ = safe_pearson(merged[xc], merged[yc], merged['n_chains'])
        rows.append({'pair': pair, 'scope_filter': 'all',
                     'unweighted_r': r_u, 'unweighted_p': p_u,
                     'weighted_r': r_w, 'n': n})
        # alpha/beta/CID/ESDE filters by receiver_bin prefix
        prefix_map = {'alpha': 'alpha_', 'beta': 'beta_', 'CID': 'CID_', 'ESDE': 'ESDE_'}
        for sc_label, prefix in prefix_map.items():
            sub = merged[merged['receiver_bin'].str.startswith(prefix)]
            r_u2, p_u2, n2 = safe_pearson(sub[xc], sub[yc])
            r_w2, _, _ = safe_pearson(sub[xc], sub[yc], sub['n_chains'])
            rows.append({'pair': pair, 'scope_filter': sc_label,
                         'unweighted_r': r_u2, 'unweighted_p': p_u2,
                         'weighted_r': r_w2, 'n': n2})
    df = pd.DataFrame(rows)
    out = V1104_MAIN / 'observation_3_weighted.parquet'
    df.to_parquet(out, index=False)
    print(f'  R2 wrote {out.name} ({len(df)} rows)')
    return df


# ---------- 再調査 3: 代替指標 ----------
def reinvestigation_3(merged: pd.DataFrame) -> pd.DataFrame:
    """traj 側 × resp 側、4 × 4 = 16 ペアの相関を per qc_regime / sim_basis 集約しない一括"""
    traj_cols = ['traj_stability_mean', 'traj_unique_mean',
                 'diffusion_ratio_mean', 'chain_len_mean']
    resp_cols = ['response_max_prob', 'response_entropy',
                 'response_top3_mass', 'response_gini']
    rows = []
    for xc in traj_cols:
        for yc in resp_cols:
            r, p, n = safe_pearson(merged[xc], merged[yc])
            rs, ps = (np.nan, np.nan)
            if n >= 3 and merged[xc].std() > 0 and merged[yc].std() > 0:
                sub = merged[[xc, yc]].dropna()
                rs, ps = spearmanr(sub[xc], sub[yc])
            rows.append({'traj_metric': xc, 'resp_metric': yc,
                         'pearson_r': r, 'pearson_p': p,
                         'spearman_r': float(rs), 'spearman_p': float(ps),
                         'n': n,
                         'abs_pearson_r': abs(r) if not np.isnan(r) else 0.0})
    df = pd.DataFrame(rows).sort_values('abs_pearson_r', ascending=False)
    out = V1104_MAIN / 'observation_3_alt_metrics.parquet'
    df.to_parquet(out, index=False)
    print(f'  R3 wrote {out.name} ({len(df)} rows, top |r| = {df["abs_pearson_r"].max():.4f})')
    return df


# ---------- 再調査 4: shuffle baseline ----------
def reinvestigation_4(seeds: list[int], resp: pd.DataFrame) -> pd.DataFrame:
    """chain 内 cid permutation で trajectory_stability を再計算、相関比較。

    actual (none) vs shuffled (within) で 2 走、各 metric pair の相関差分を見る
    """
    rows = []
    for mode in ['none', 'within']:
        traj_dfs = []
        for sd in seeds:
            rng = np.random.default_rng(sd * 7919 + (0 if mode == 'none' else 9973))
            traj_dfs.append(trajectory_metrics_per_chain(sd, shuffle_mode=mode, rng=rng))
        traj_all = pd.concat(traj_dfs, ignore_index=True)
        traj_agg = aggregate_traj(traj_all)
        merged = traj_agg.merge(resp, on=['receiver_bin', 'change_metric_type'], how='left')

        for pair, (xc, yc) in [
            ('stability_vs_maxprob', ('traj_stability_mean', 'response_max_prob')),
            ('diffusion_vs_entropy', ('diffusion_ratio_mean', 'response_entropy')),
            ('stability_vs_entropy', ('traj_stability_mean', 'response_entropy')),
            ('diffusion_vs_maxprob', ('diffusion_ratio_mean', 'response_max_prob')),
        ]:
            r, p, n = safe_pearson(merged[xc], merged[yc])
            rs, ps = (np.nan, np.nan)
            if n >= 3 and merged[xc].std() > 0 and merged[yc].std() > 0:
                sub = merged[[xc, yc]].dropna()
                rs, ps = spearmanr(sub[xc], sub[yc])
            rows.append({'shuffle_mode': mode, 'pair': pair,
                         'pearson_r': r, 'pearson_p': p,
                         'spearman_r': float(rs), 'spearman_p': float(ps),
                         'n': n,
                         'traj_stability_mean_overall': float(merged['traj_stability_mean'].mean()),
                         'diffusion_ratio_mean_overall': float(merged['diffusion_ratio_mean'].mean())})

    df = pd.DataFrame(rows)
    out = V1104_MAIN / 'observation_3_shuffle_baseline.parquet'
    df.to_parquet(out, index=False)
    print(f'  R4 wrote {out.name} ({len(df)} rows)')
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', default='0..23')
    args = ap.parse_args()
    lo, hi = args.seeds.split('..')
    seeds = list(range(int(lo), int(hi) + 1))

    V1104_MAIN.mkdir(parents=True, exist_ok=True)
    print(f'=== v1104 Step H-4 観察 3 再調査 4 件 ===')
    print(f'seeds: {seeds}')

    t0 = time.time()
    resp = load_response_metrics()
    print(f'response metrics: {len(resp)} rows')

    print('\n[R1] 層化 (qc_regime × sim_basis × k)')
    # base merged (実 trajectory)
    base_traj = pd.concat(
        [trajectory_metrics_per_chain(sd, shuffle_mode='none') for sd in seeds],
        ignore_index=True)
    base_agg = aggregate_traj(base_traj)
    merged = base_agg.merge(resp, on=['receiver_bin', 'change_metric_type'], how='left')
    r1 = reinvestigation_1(merged)

    print('\n[R2] weighting / scope filter')
    r2 = reinvestigation_2(merged)

    print('\n[R3] 代替指標 (4 traj × 4 resp = 16 pairs)')
    r3 = reinvestigation_3(merged)

    print('\n[R4] shuffle baseline (chain内 cid permutation)')
    r4 = reinvestigation_4(seeds, resp)

    print(f'\n=== 4 再調査全完了、total elapsed {time.time()-t0:.1f}s ===')

    # summary printouts
    print('\n--- R1 summary (top 5 |r| of stability_vs_maxprob) ---')
    r1s = r1[r1['pair'] == 'traj_stability_mean_vs_response_max_prob'].copy()
    r1s['abs_r'] = r1s['pearson_r'].abs()
    print(r1s.sort_values('abs_r', ascending=False).head(5)[
        ['qc_regime','sim_basis','k','pearson_r','spearman_r','n']].to_string(index=False))
    print('\n--- R3 top 5 (代替指標) ---')
    print(r3.head(5)[['traj_metric','resp_metric','pearson_r','spearman_r','n']].to_string(index=False))
    print('\n--- R4 actual vs shuffled ---')
    print(r4[['shuffle_mode','pair','pearson_r','traj_stability_mean_overall']].to_string(index=False))


if __name__ == '__main__':
    main()
