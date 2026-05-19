#!/usr/bin/env python3
"""v1102 Step B — primary table 構築 (受け手構造 × 時間スケール × 応答 5 種)

設計書 §2.6 確定:
- 応答指標 5 種並列、主従なし (attention trajectory / influence / variability /
  atom profile / category profile)
- per-cell サンプル数で除外せず、全セル残し、際立ち度とサンプル数を別軸で記録

設計書 §1.3 + §2.2 + §2.3:
- 入力: atom_introduction_events_v108_standard (固定)
- 受け手構造軸: Integration α/β (Step G n_members × qc_gini) + CID (n_core_member)
  + ESDE 4 解像度
- 時間スケール軸: window (v10.6 trajectory) + immediate/short/medium (v10.7
  baselines_with_delta)
- 既存出力流用、新規 main run なし
- post-process、物理層 frozen
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V106_MAIN = REPO_ROOT / 'developmental/v106/outputs/main'
V107_MAIN = REPO_ROOT / 'developmental/v107/outputs/main'
V112_MAIN = REPO_ROOT / 'developmental/v112/outputs/main'
V1101A_MAIN = REPO_ROOT / 'unified/v1101a/outputs/main'
V1102_ROOT = REPO_ROOT / 'unified/v1102'
OUT_MAIN = V1102_ROOT / 'outputs/main'
OUT_SMOKE = V1102_ROOT / 'outputs/smoke'

# CID n_core_member bin (Code A 認識確認 §2.2)
CID_NCORE_BINS = [(2, 2, 'CID_n=2'), (3, 3, 'CID_n=3'),
                   (4, 4, 'CID_n=4'), (5, 5, 'CID_n=5'),
                   (6, 999, 'CID_n=6+')]


def bin_cid_ncore(n: int) -> str:
    for lo, hi, label in CID_NCORE_BINS:
        if lo <= n <= hi:
            return label
    return 'CID_n=unknown'


def load_attention_emit_with_composition(seeds: list[int]) -> pd.DataFrame:
    """attention_emit_*.parquet を Step G 構成情報と結合"""
    emit_dfs = []
    for sd in seeds:
        p = V1101A_MAIN / f'attention_emit_seed{sd}.parquet'
        df = pd.read_parquet(p)
        emit_dfs.append(df)
    emit = pd.concat(emit_dfs, ignore_index=True)

    # Step G composition
    ca = pd.read_parquet(V1101A_MAIN / 'integration_composition_alpha.parquet')
    cb = pd.read_parquet(V1101A_MAIN / 'integration_composition_beta.parquet')

    # alpha bin merge
    alpha = emit[emit['change_scope'] == 'alpha'].copy()
    alpha = alpha.merge(ca.rename(columns={'alpha_id': 'scope_id'}),
                         on=['seed', 'scope_id'], how='left')

    beta = emit[emit['change_scope'] == 'beta'].copy()
    beta = beta.merge(cb.rename(columns={'beta_id': 'scope_id'}),
                       on=['seed', 'scope_id'], how='left')

    cid_em = emit[emit['change_scope'] == 'CID'].copy()
    esde = emit[emit['change_scope'].isin(['ESDE_event', 'ESDE_step10', 'ESDE_window'])].copy()

    return alpha, beta, cid_em, esde


def load_cid_ncore_map(seeds: list[int]) -> pd.DataFrame:
    """per (seed, cid) で n_core_member max"""
    rows = []
    for sd in seeds:
        p = V106_MAIN / 'window_trajectory' / f'window_cid_alignment_seed{sd}.csv'
        df = pd.read_csv(p, usecols=['cognitive_id', 'n_core_member'])
        g = df.groupby('cognitive_id')['n_core_member'].max()
        for cid, n in g.items():
            rows.append({'seed': sd, 'scope_id': int(cid), 'n_core_member': int(n)})
    return pd.DataFrame(rows)


def bin_n_members_alpha(n) -> str:
    """alpha n_members bin (Step G 既存)"""
    if pd.isna(n):
        return 'alpha_n=NA'
    n = int(n)
    if n == 1: return 'alpha_n=1'
    if n == 2: return 'alpha_n=2'
    if n == 3: return 'alpha_n=3'
    return 'alpha_n=4+'


def bin_n_members_beta(n) -> str:
    if pd.isna(n):
        return 'beta_n=NA'
    n = int(n)
    if n == 1: return 'beta_n=1'
    if n == 2: return 'beta_n=2'
    if n == 3: return 'beta_n=3'
    return 'beta_n=4+'


def bin_gini(g) -> str:
    if pd.isna(g): return 'gini=NA'
    if g < 0.05: return 'gini=low'
    if g < 0.20: return 'gini=mid'
    return 'gini=high'


def load_v107_delta_per_cid(seeds: list[int]) -> pd.DataFrame:
    """v10.7 baselines_with_delta から per (seed, source_cid) で immediate/short/medium delta mean"""
    dfs = []
    cols = ['source_cid'] + [f'delta_{m}_{t}' for m in ['Q','C','R_familiarity']
                              for t in ['immediate','short','medium']]
    for sd in seeds:
        p = V107_MAIN / f'baselines_with_delta_seed{sd}.parquet'
        df = pd.read_parquet(p, columns=cols)
        df['seed'] = sd
        g = df.groupby(['seed', 'source_cid'], as_index=False).agg(
            **{c: (c, 'mean') for c in cols if c != 'source_cid'}
        )
        dfs.append(g)
    return pd.concat(dfs, ignore_index=True)


def load_cid_state_summary(seeds: list[int], atom_names: list[str]) -> pd.DataFrame:
    """cid_state_ledger から per (seed, cid) で 326 atom 濃度 mean + 24 category mean"""
    dfs = []
    for sd in seeds:
        p = V1101A_MAIN / f'cid_state_ledger_seed{sd}.parquet'
        df = pd.read_parquet(p)
        # per (seed, cid) で全 window 平均
        atom_cols = [c for c in df.columns if c in atom_names]
        g = df.groupby(['seed', 'cid'], as_index=False)[atom_cols].mean()
        # category mean (prefix 別)
        prefixes = sorted(set(a.split('.')[0] for a in atom_cols))
        for pfx in prefixes:
            cols_in_cat = [c for c in atom_cols if c.split('.')[0] == pfx]
            if cols_in_cat:
                g[f'cat_{pfx}'] = g[cols_in_cat].mean(axis=1)
        dfs.append(g)
    return pd.concat(dfs, ignore_index=True), prefixes


def compute_primary_table(seeds: list[int], verbose: bool = True) -> pd.DataFrame:
    """primary table = per (receiver_bin, change_metric_type) で応答 5 種 + サンプル数集約"""
    t0 = time.time()
    if verbose:
        print(f'loading inputs for seeds {seeds}...')

    # atom_profiles で atom_names 取得
    import numpy as np_
    cache = np_.load(V106_MAIN / 'atom_profiles_cache.npz')
    atom_names_list = list(cache['atom_names'])

    alpha, beta, cid_em, esde = load_attention_emit_with_composition(seeds)
    cid_ncore = load_cid_ncore_map(seeds)
    cid_em = cid_em.merge(cid_ncore, on=['seed', 'scope_id'], how='left')

    # propagation (influence) + causality (causality_path) も join
    propag_dfs = []
    caus_dfs = []
    for sd in seeds:
        propag_dfs.append(pd.read_parquet(
            V1101A_MAIN / f'attention_propagation_seed{sd}.parquet',
            columns=['seed', 'window', 'change_scope', 'scope_id', 'change_metric_type',
                      'attention_candidate_id', 'influence_candidate_count']))
        caus_dfs.append(pd.read_parquet(
            V1101A_MAIN / f'attention_causality_seed{sd}.parquet',
            columns=['seed', 'window', 'change_scope', 'scope_id', 'change_metric_type',
                      'attention_candidate_id', 'causality_candidate_path_zscore']))
    propag = pd.concat(propag_dfs, ignore_index=True)
    caus = pd.concat(caus_dfs, ignore_index=True)

    # observation_c (variability)
    obsc = pd.read_parquet(V1101A_MAIN / 'observation_c_predictability.parquet')

    # v107 effect size per (seed, source_cid)
    if verbose:
        print('  loading v107 baselines_with_delta...')
    v107_per_cid = load_v107_delta_per_cid(seeds)

    # cid_state_ledger summary per (seed, cid)
    if verbose:
        print('  loading cid_state_ledger summary...')
    cid_state, category_prefixes = load_cid_state_summary(seeds, atom_names_list)

    # receiver_bin 付与
    alpha['receiver_bin'] = (
        alpha['n_members'].apply(bin_n_members_alpha) + ' / '
        + alpha['qc_gini_mean'].apply(bin_gini))
    beta['receiver_bin'] = (
        beta['n_members'].apply(bin_n_members_beta) + ' / '
        + beta['qc_gini_mean'].apply(bin_gini))
    cid_em['receiver_bin'] = cid_em['n_core_member'].apply(bin_cid_ncore)
    esde['receiver_bin'] = esde['change_scope']  # ESDE_event/step10/window をそのまま

    # 統合 emit データ
    all_em = pd.concat([
        alpha[['seed', 'window', 'change_scope', 'scope_id', 'attention_candidate_id',
                'change_metric_type', 'qc_regime', 'receiver_bin']],
        beta[['seed', 'window', 'change_scope', 'scope_id', 'attention_candidate_id',
               'change_metric_type', 'qc_regime', 'receiver_bin']],
        cid_em[['seed', 'window', 'change_scope', 'scope_id', 'attention_candidate_id',
                 'change_metric_type', 'qc_regime', 'receiver_bin']],
        esde[['seed', 'window', 'change_scope', 'scope_id', 'attention_candidate_id',
               'change_metric_type', 'qc_regime', 'receiver_bin']],
    ], ignore_index=True)

    # propag を join (window + change_scope + scope_id + change_metric_type で merge)
    all_em = all_em.merge(
        propag[['seed', 'window', 'change_scope', 'scope_id', 'change_metric_type',
                 'influence_candidate_count']],
        on=['seed', 'window', 'change_scope', 'scope_id', 'change_metric_type'],
        how='left')
    all_em = all_em.merge(
        caus[['seed', 'window', 'change_scope', 'scope_id', 'change_metric_type',
               'causality_candidate_path_zscore']],
        on=['seed', 'window', 'change_scope', 'scope_id', 'change_metric_type'],
        how='left')

    if verbose:
        print(f'all_em rows: {len(all_em)}, elapsed={time.time()-t0:.1f}s')

    # alpha/beta member_cids map (cid_state_ledger join 用)
    ca = pd.read_parquet(V1101A_MAIN / 'integration_composition_alpha.parquet')
    cb = pd.read_parquet(V1101A_MAIN / 'integration_composition_beta.parquet')
    # alpha/beta member_cids は v105 log から再取得 (Step G load_alpha_members 同型は重い)
    # 簡易: emit から (seed, scope_id, attention_candidate_id) で member cid を回収
    # attention_candidate_id は alpha/beta scope では「scope 内最大変化 cid」だが、
    # cid 集合の代理として scope_id ベースで cid_state aggregate を計算する
    # → per cell の cid 集合 = grp['attention_candidate_id'].unique()
    #    これが厳密な「member cids」ではないが「実際に attention 候補になった cid 群」、
    #    應答 read-back の意味で妥当 (judgement Taka 領域)

    # primary table: per (receiver_bin, time_scale=window 軸) 集約
    rows = []
    cat_cols = [f'cat_{p}' for p in category_prefixes]
    for (rbin, mt), grp in all_em.groupby(['receiver_bin', 'change_metric_type']):
        cell = {
            'receiver_bin': rbin,
            'change_metric_type': mt,
            'time_scale': 'window',
            'n_records': len(grp),
            'n_seeds_present': grp['seed'].nunique(),
            'n_unique_attention_candidates': grp['attention_candidate_id'].nunique(),
            'attention_count_mean_per_window': float(
                grp.groupby('window').size().mean()) if len(grp) > 0 else np.nan,
            'influence_count_mean': float(grp['influence_candidate_count'].mean()),
            'influence_count_max': float(grp['influence_candidate_count'].max())
                if len(grp.dropna(subset=['influence_candidate_count'])) > 0 else np.nan,
            'conscious_frac': float((grp['qc_regime'] == 'conscious_dominant').mean()),
            'top_causality_zscore': (
                grp['causality_candidate_path_zscore'].mode().iloc[0]
                if len(grp['causality_candidate_path_zscore'].dropna()) > 0 else None),
        }
        # variability lift_over_baseline (observation_c から、scope+metric 単位で)
        # observation_c は per (seed, change_scope, change_metric_type) で 1 値
        # receiver_bin に紐付けるには change_scope を分解する必要、簡易化:
        # CID / alpha / beta / ESDE_* の scope レベルでマッチ
        scope_match = None
        if rbin.startswith('CID'): scope_match = 'CID'
        elif rbin.startswith('alpha'): scope_match = 'alpha'
        elif rbin.startswith('beta'): scope_match = 'beta'
        elif rbin in ('ESDE_event', 'ESDE_step10', 'ESDE_window'): scope_match = rbin
        if scope_match:
            obsc_sub = obsc[(obsc['change_scope'] == scope_match)
                              & (obsc['change_metric_type'] == mt)]
            cell['variability_lift_mean'] = float(obsc_sub['lift_over_baseline'].mean()) \
                if len(obsc_sub) > 0 else np.nan
            cell['variability_actual_mean'] = float(obsc_sub['actual_predict_rate'].mean()) \
                if len(obsc_sub) > 0 else np.nan
        else:
            cell['variability_lift_mean'] = np.nan
            cell['variability_actual_mean'] = np.nan

        # ── 応答 4: atom profile (cid_state_ledger 由来、(a) 簡易版ベース、留保 #L1)
        # cell に含まれる cid 集合 = grp['attention_candidate_id'].unique()
        cell_cids = grp[['seed', 'attention_candidate_id']].dropna().drop_duplicates()
        cell_cids['attention_candidate_id'] = cell_cids['attention_candidate_id'].astype(int)
        cid_state_sub = cid_state.merge(
            cell_cids.rename(columns={'attention_candidate_id': 'cid'}),
            on=['seed', 'cid'], how='inner')
        if len(cid_state_sub) > 0:
            atom_mean = cid_state_sub[atom_names_list].mean()
            top_atom = atom_mean.idxmax()
            cell['atom_top1_name'] = top_atom
            cell['atom_top1_concentration'] = float(atom_mean[top_atom])
            cell['atom_top1_note'] = '(a) 簡易版 atom_profiles mean ベース、完全再現でない (留保 #L1)'
        else:
            cell['atom_top1_name'] = None
            cell['atom_top1_concentration'] = np.nan
            cell['atom_top1_note'] = '(a) 簡易版、サンプルなし'

        # ── 応答 5: category profile (24 prefix 集約)
        if len(cid_state_sub) > 0:
            cat_mean = cid_state_sub[cat_cols].mean()
            top_cat = cat_mean.idxmax().replace('cat_', '')
            cell['category_top1_name'] = top_cat
            cell['category_top1_concentration'] = float(cat_mean[f'cat_{top_cat}'])
        else:
            cell['category_top1_name'] = None
            cell['category_top1_concentration'] = np.nan

        # ── v107 effect size × 3 時間粒度 (時間スケール軸 immediate/short/medium)
        v107_sub = v107_per_cid.merge(
            cell_cids.rename(columns={'attention_candidate_id': 'source_cid'}),
            on=['seed', 'source_cid'], how='inner')
        if len(v107_sub) > 0:
            for ts in ['immediate', 'short', 'medium']:
                for metric in ['Q', 'C', 'R_familiarity']:
                    col = f'delta_{metric}_{ts}'
                    cell[f'effect_{col}_mean'] = float(v107_sub[col].mean())
        else:
            for ts in ['immediate', 'short', 'medium']:
                for metric in ['Q', 'C', 'R_familiarity']:
                    cell[f'effect_delta_{metric}_{ts}_mean'] = np.nan

        rows.append(cell)

    df_pt = pd.DataFrame(rows)
    if verbose:
        print(f'primary_table rows: {len(df_pt)}, elapsed={time.time()-t0:.1f}s')
    return df_pt


def parse_seeds(spec: str) -> list[int]:
    if '..' in spec:
        lo, hi = spec.split('..')
        return list(range(int(lo), int(hi) + 1))
    return [int(s) for s in spec.split(',')]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', default='0..23')
    ap.add_argument('--smoke-or-main', default='main', choices=['smoke', 'main'])
    args = ap.parse_args()

    seeds = parse_seeds(args.seeds)
    out_dir = OUT_SMOKE if args.smoke_or_main == 'smoke' else OUT_MAIN
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f'=== v1102 Step B — primary table 構築 ===')
    print(f'seeds: {seeds}, output: {out_dir}')

    df = compute_primary_table(seeds, verbose=True)
    out_path = out_dir / 'primary_table.parquet'
    df.to_parquet(out_path, index=False)
    print(f'\nwrote {out_path} ({len(df)} cells)')


if __name__ == '__main__':
    main()
