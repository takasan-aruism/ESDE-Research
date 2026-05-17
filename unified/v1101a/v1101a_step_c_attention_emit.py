#!/usr/bin/env python3
"""
v11.0.1.a (v1101a) Step C — 注意 emit ログ生成
設計書 §3.4 注意 emit スキーマに従う。
6 構造単位 (CID / α / β / ESDE-event / ESDE-step10 / ESDE-window)
× 3 変化指標 (atom_delta / rank1_flip_density / unit_kl_static)
× 24 seeds で attention emit records を出力。

post-process emitter のみ (改訂フレーム §3.5 emitter 境界条項)。
新規 main run 不要、v10.5/v10.6/v10.7/v1101 既存出力を read-only で流用。
書き込みは unified/v1101a/outputs/ 配下のみ (物理層 frozen 絶対)。

usage:
    python v1101a_step_c_attention_emit.py --seeds 0           # smoke (seed 0 のみ)
    python v1101a_step_c_attention_emit.py --seeds 0..23       # main 24 seeds 1 batch
    python v1101a_step_c_attention_emit.py --smoke-or-main smoke
    python v1101a_step_c_attention_emit.py --smoke-or-main main
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# ──────────────────────────────────────────────────────────────────
# paths (read-only sources + writable sink)
# ──────────────────────────────────────────────────────────────────
REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V106_MAIN = REPO_ROOT / 'developmental/v106/outputs/main'
V105_INTEGRATION = REPO_ROOT / 'developmental/v105/diag_v105_main/integration'
V1101A_ROOT = REPO_ROOT / 'unified/v1101a'
OUT_MAIN = V1101A_ROOT / 'outputs/main'
OUT_SMOKE = V1101A_ROOT / 'outputs/smoke'


# ──────────────────────────────────────────────────────────────────
# input loaders (read-only)
# ──────────────────────────────────────────────────────────────────
def load_window_trajectory(seed: int) -> pd.DataFrame:
    """v10.6 window_cid_alignment: per (cid, window) qc_ratio + rank_1 atom/sim."""
    p = V106_MAIN / 'window_trajectory' / f'window_cid_alignment_seed{seed}.csv'
    df = pd.read_csv(p)
    # qc_ratio = Q / (Q + C)、>0.5 で認知優位 (Q > C)、<0.5 で意識優位 (C > Q)
    qc_denom = (df['Q_remaining_at_window_end'] + df['C_at_window_end'])
    df['qc_ratio'] = np.where(
        qc_denom > 0,
        df['Q_remaining_at_window_end'] / qc_denom,
        np.nan,
    )
    return df[['seed', 'cognitive_id', 'window', 'step_at_window_end',
               'Q_remaining_at_window_end', 'C_at_window_end',
               'qc_ratio', 'rank_1_atom', 'rank_1_sim']].copy()


def load_event_trajectory(seed: int) -> pd.DataFrame:
    p = V106_MAIN / 'event_trajectory' / f'event_cid_alignment_seed{seed}.csv'
    df = pd.read_csv(p)
    qc_denom = (df['Q_remaining_at_window_end'] + df['C_at_window_end'])
    df['qc_ratio'] = np.where(
        qc_denom > 0,
        df['Q_remaining_at_window_end'] / qc_denom,
        np.nan,
    )
    return df[['seed', 'cognitive_id', 't', 'window',
               'Q_remaining_at_window_end', 'C_at_window_end',
               'qc_ratio', 'rank_1_atom', 'rank_1_sim']].copy()


def load_step10_trajectory(seed: int) -> pd.DataFrame:
    p = V106_MAIN / 'step10_trajectory' / f'step10_cid_alignment_seed{seed}.csv'
    df = pd.read_csv(p)
    qc_denom = (df['Q_remaining_at_window_end'] + df['C_at_window_end'])
    df['qc_ratio'] = np.where(
        qc_denom > 0,
        df['Q_remaining_at_window_end'] / qc_denom,
        np.nan,
    )
    return df[['seed', 'cognitive_id', 't', 'window',
               'Q_remaining_at_window_end', 'C_at_window_end',
               'qc_ratio', 'rank_1_atom', 'rank_1_sim']].copy()


def load_alpha_membership(seed: int) -> pd.DataFrame:
    """v10.5 alpha_membership_log: 最終 step snapshot で cid_id → alpha_ids ('|' 区切り)."""
    p = V105_INTEGRATION / f'alpha_membership_log_seed{seed}.csv'
    df = pd.read_csv(p)
    rows = []
    for _, r in df.iterrows():
        ids_str = str(r['alpha_ids'])
        if ids_str in ('nan', '', 'None'):
            continue
        for aid in ids_str.split('|'):
            if aid.strip():
                rows.append({'cid': int(r['cid_id']), 'alpha_id': int(aid)})
    return pd.DataFrame(rows)


def load_beta_membership(seed: int) -> pd.DataFrame:
    """v10.5 beta_distribution_log: per-distribution event の (beta_id, target_cid) unique."""
    p = V105_INTEGRATION / f'beta_distribution_log_seed{seed}.csv'
    df = pd.read_csv(p)
    return df[['beta_id', 'target_cid']].drop_duplicates().rename(
        columns={'target_cid': 'cid'})


def load_cid_atom_sim(seed: int) -> pd.DataFrame:
    """v10.6 cid_atom_sim_matrix: 228 cids × 326 atom 濃度ベクトル (run 最終時点、静的)."""
    p = V106_MAIN / f'cid_atom_sim_matrix_seed{seed}.parquet'
    return pd.read_parquet(p)


# ──────────────────────────────────────────────────────────────────
# variable change metrics — per cid per window
# ──────────────────────────────────────────────────────────────────
def compute_atom_delta(traj_window: pd.DataFrame) -> pd.DataFrame:
    """rank_1_sim の Δt 差分 (per cid, per window)、絶対値で量的変化"""
    df = traj_window.sort_values(['cognitive_id', 'window']).copy()
    df['atom_delta'] = (df.groupby('cognitive_id')['rank_1_sim']
                          .diff().abs().fillna(0.0))
    return df[['cognitive_id', 'window', 'atom_delta']]


def compute_rank1_flip(traj_window: pd.DataFrame) -> pd.DataFrame:
    """rank_1_atom の変化検出 (per cid, per window)、0/1 indicator
    隣接 window で rank_1_atom が異なれば 1。
    density は集約段階で per-window 平均化される。"""
    df = traj_window.sort_values(['cognitive_id', 'window']).copy()
    df['prev_atom'] = df.groupby('cognitive_id')['rank_1_atom'].shift(1)
    df['rank1_flip'] = np.where(
        df['prev_atom'].notna() & (df['rank_1_atom'] != df['prev_atom']),
        1.0, 0.0)
    return df[['cognitive_id', 'window', 'rank1_flip']]


def compute_unit_kl_static(sim_matrix: pd.DataFrame) -> pd.DataFrame:
    """各 cid 1 つ取り、326 atom 濃度を確率分布として normalize、
    他全 cid との平均 KL を unit_kl_static として返す (時間軸なし、留保 #L1)."""
    atom_cols = [c for c in sim_matrix.columns if c not in ('seed', 'cid')]
    M = sim_matrix[atom_cols].to_numpy(dtype=np.float64)
    # sim_matrix には per-cid 1 cell 程度の NaN がある (probe atom 自己参照由来) → 0 に
    M = np.nan_to_num(M, nan=0.0)
    # smoothing for KL safety
    eps = 1e-12
    M = M + eps
    P = M / M.sum(axis=1, keepdims=True)  # (n_cid, 326)
    logP = np.log(P)
    # KL(p || q) = sum p * (log p - log q)
    n = P.shape[0]
    out = np.zeros(n, dtype=np.float64)
    for i in range(n):
        # vectorized: KL(P_i || P_j) for all j
        klij = (P[i] * (logP[i] - logP)).sum(axis=1)  # (n,)
        klij[i] = 0.0
        out[i] = klij.sum() / max(n - 1, 1)
    cids = sim_matrix['cid'].astype(int).to_numpy()
    return pd.DataFrame({'cognitive_id': cids, 'unit_kl_static': out})


# ──────────────────────────────────────────────────────────────────
# qc_ratio aggregation across structural units
# ──────────────────────────────────────────────────────────────────
def aggregate_qc_at_window(per_cid_qc: pd.DataFrame, cids: list[int]) -> dict:
    """与えられた cid 集合の qc_ratio を集約。
    監査修正 #2 + 留保 #L2: 多数決 (Q>C cid 比率) と 中央値 を両方算出."""
    sub = per_cid_qc[per_cid_qc['cognitive_id'].isin(cids) & per_cid_qc['qc_ratio'].notna()]
    if len(sub) == 0:
        return {'qc_ratio_median': np.nan, 'qc_ratio_majority': np.nan, 'n_units': 0}
    return {
        'qc_ratio_median': float(sub['qc_ratio'].median()),
        'qc_ratio_majority': float((sub['qc_ratio'] > 0.5).mean()),
        'n_units': int(len(sub)),
    }


def qc_regime_from_majority(qc_majority: float) -> str:
    """qc_ratio_majority (= Q>C cid 比率) > 0.5 で cognitive_dominant"""
    if pd.isna(qc_majority):
        return 'undefined'
    return 'cognitive_dominant' if qc_majority > 0.5 else 'conscious_dominant'


def predicted_lock_mode_from_regime(regime: str) -> str:
    """旧 attention_locked。記録専用予測 (修正 #4)"""
    if regime == 'cognitive_dominant':
        return 'locked'   # 認知優位 → 自動固定モードの予測
    if regime == 'conscious_dominant':
        return 'selected'  # 意識優位 → 選択モードの予測
    return 'undefined'


# ──────────────────────────────────────────────────────────────────
# per-seed processing
# ──────────────────────────────────────────────────────────────────
def process_seed(seed: int, verbose: bool = True) -> pd.DataFrame:
    t0 = time.time()
    if verbose:
        print(f'[seed {seed}] loading inputs...', flush=True)

    traj_w = load_window_trajectory(seed)
    sim_mat = load_cid_atom_sim(seed)
    alpha_mem = load_alpha_membership(seed)
    beta_mem = load_beta_membership(seed)

    if verbose:
        print(f'[seed {seed}] window_traj rows={len(traj_w)}, n_cids={traj_w.cognitive_id.nunique()}, '
              f'n_windows={traj_w.window.nunique()}, '
              f'n_alphas={alpha_mem.alpha_id.nunique() if len(alpha_mem) else 0}, '
              f'n_betas={beta_mem.beta_id.nunique() if len(beta_mem) else 0}',
              flush=True)

    # per-cid per-window qc_ratio
    qc_per_cid = traj_w[['cognitive_id', 'window', 'qc_ratio']].copy()

    # ── change metrics (per cid per window or static)
    atom_delta_df = compute_atom_delta(traj_w)
    rank1_flip_df = compute_rank1_flip(traj_w)
    unit_kl_df = compute_unit_kl_static(sim_mat)  # 時間軸なし

    # joined metrics frame: per (cid, window)
    metrics = (qc_per_cid
               .merge(atom_delta_df, on=['cognitive_id', 'window'], how='left')
               .merge(rank1_flip_df, on=['cognitive_id', 'window'], how='left')
               .merge(unit_kl_df, on='cognitive_id', how='left'))

    # structural unit → member cids map
    all_cids = sorted(traj_w['cognitive_id'].unique().tolist())
    alpha_members = (alpha_mem.groupby('alpha_id')['cid'].apply(list).to_dict()
                     if len(alpha_mem) else {})
    beta_members = (beta_mem.groupby('beta_id')['cid'].apply(list).to_dict()
                    if len(beta_mem) else {})

    windows = sorted(traj_w['window'].unique().tolist())
    if verbose:
        print(f'[seed {seed}] iterating {len(windows)} windows × 6 scopes × 3 metrics...',
              flush=True)

    emit_rows: list[dict] = []
    METRIC_TYPES = ['atom_delta', 'rank1_flip_density', 'unit_kl_static']

    for w in windows:
        m_w = metrics[metrics['window'] == w]
        if len(m_w) == 0:
            continue

        # qc_ratio at window for each scope
        scope_qc = {
            'ESDE_window_all': aggregate_qc_at_window(m_w, all_cids),
        }
        for aid, members in alpha_members.items():
            scope_qc[f'alpha_{aid}'] = aggregate_qc_at_window(m_w, members)
        for bid, members in beta_members.items():
            scope_qc[f'beta_{bid}'] = aggregate_qc_at_window(m_w, members)

        # per metric_type × per scope_kind: collect attention candidates
        # CID scope: each cid is its own scope record
        for mt in METRIC_TYPES:
            if mt == 'rank1_flip_density':
                # density = mean of rank1_flip within window (per cid for CID scope,
                # mean for integration / ESDE scope)
                col = 'rank1_flip'
            elif mt == 'atom_delta':
                col = 'atom_delta'
            else:
                col = 'unit_kl_static'

            # ─ CID scope (per cid) ─
            cid_scope = m_w[['cognitive_id', col, 'qc_ratio']].dropna(subset=[col])
            if len(cid_scope) > 0:
                ranked = cid_scope.sort_values(col, ascending=False).reset_index(drop=True)
                for rank_within, row in ranked.iterrows():
                    qcr = float(row['qc_ratio']) if pd.notna(row['qc_ratio']) else np.nan
                    if pd.isna(qcr):
                        regime = 'undefined'
                    else:
                        regime = 'cognitive_dominant' if qcr > 0.5 else 'conscious_dominant'
                    qmaj = (1.0 if (pd.notna(qcr) and qcr > 0.5)
                            else (0.0 if pd.notna(qcr) else np.nan))
                    emit_rows.append({
                        'seed': seed,
                        'window': int(w),
                        'change_scope': 'CID',
                        'scope_id': int(row['cognitive_id']),
                        'change_metric_type': mt,
                        'change_metric_value': float(row[col]),
                        'change_rank_within_type': int(rank_within + 1),
                        'attention_candidate_id': int(row['cognitive_id']),
                        'qc_ratio': qcr,
                        'qc_ratio_majority': qmaj,
                        'qc_ratio_aggregation': 'self',
                        'qc_regime': regime,
                        'predicted_lock_mode': predicted_lock_mode_from_regime(regime),
                        'n_units_in_scope': 1,
                    })

            # ─ alpha scope (per alpha) ─
            for aid, members in alpha_members.items():
                sub = m_w[m_w['cognitive_id'].isin(members)].dropna(subset=[col])
                if len(sub) == 0:
                    continue
                # attention candidate = scope 内最大変化 cid
                top = sub.loc[sub[col].idxmax()]
                qc_agg = scope_qc[f'alpha_{aid}']
                regime = qc_regime_from_majority(qc_agg['qc_ratio_majority'])
                emit_rows.append({
                    'seed': seed,
                    'window': int(w),
                    'change_scope': 'alpha',
                    'scope_id': int(aid),
                    'change_metric_type': mt,
                    'change_metric_value': float(sub[col].mean()),
                    'change_rank_within_type': 0,  # scope 集約 → 順位は scope 間で算出する別ビュー
                    'attention_candidate_id': int(top['cognitive_id']),
                    'qc_ratio': qc_agg['qc_ratio_median'],
                    'qc_ratio_majority': qc_agg['qc_ratio_majority'],
                    'qc_ratio_aggregation': 'median+majority',
                    'qc_regime': regime,
                    'predicted_lock_mode': predicted_lock_mode_from_regime(regime),
                    'n_units_in_scope': qc_agg['n_units'],
                })

            # ─ beta scope (per beta) ─
            for bid, members in beta_members.items():
                sub = m_w[m_w['cognitive_id'].isin(members)].dropna(subset=[col])
                if len(sub) == 0:
                    continue
                top = sub.loc[sub[col].idxmax()]
                qc_agg = scope_qc[f'beta_{bid}']
                regime = qc_regime_from_majority(qc_agg['qc_ratio_majority'])
                emit_rows.append({
                    'seed': seed,
                    'window': int(w),
                    'change_scope': 'beta',
                    'scope_id': int(bid),
                    'change_metric_type': mt,
                    'change_metric_value': float(sub[col].mean()),
                    'change_rank_within_type': 0,
                    'attention_candidate_id': int(top['cognitive_id']),
                    'qc_ratio': qc_agg['qc_ratio_median'],
                    'qc_ratio_majority': qc_agg['qc_ratio_majority'],
                    'qc_ratio_aggregation': 'median+majority',
                    'qc_regime': regime,
                    'predicted_lock_mode': predicted_lock_mode_from_regime(regime),
                    'n_units_in_scope': qc_agg['n_units'],
                })

            # ─ ESDE_window scope (all cids) ─
            sub_all = m_w.dropna(subset=[col])
            if len(sub_all) > 0:
                top = sub_all.loc[sub_all[col].idxmax()]
                qc_agg = scope_qc['ESDE_window_all']
                regime = qc_regime_from_majority(qc_agg['qc_ratio_majority'])
                emit_rows.append({
                    'seed': seed,
                    'window': int(w),
                    'change_scope': 'ESDE_window',
                    'scope_id': -1,
                    'change_metric_type': mt,
                    'change_metric_value': float(sub_all[col].mean()),
                    'change_rank_within_type': 0,
                    'attention_candidate_id': int(top['cognitive_id']),
                    'qc_ratio': qc_agg['qc_ratio_median'],
                    'qc_ratio_majority': qc_agg['qc_ratio_majority'],
                    'qc_ratio_aggregation': 'median+majority',
                    'qc_regime': regime,
                    'predicted_lock_mode': predicted_lock_mode_from_regime(regime),
                    'n_units_in_scope': qc_agg['n_units'],
                })

    df_emit = pd.DataFrame(emit_rows)

    # ── ESDE-event / ESDE-step10 scopes (時間解像度の異なる集約)
    # event/step10 trajectory を別 read して per window-or-step で集約
    # 段階 1 は粗解像度のため event/step10 は window-equivalent な scope として処理
    # 留保: event/step10 trajectory の qc_ratio は window と同じソース由来でデータ重複
    # → 段階 1 では ESDE_event/ESDE_step10 を ESDE_window と並列に出力 (各時間解像度別)
    for resolution_name, loader in [('ESDE_event', load_event_trajectory),
                                     ('ESDE_step10', load_step10_trajectory)]:
        traj_r = loader(seed)
        # event/step10 解像度は per-(cid, t) 単位、window 列で集約
        windows_r = sorted(traj_r['window'].unique().tolist())
        for w in windows_r:
            sub = traj_r[traj_r['window'] == w]
            qc_vals = sub[['cognitive_id', 'qc_ratio']].dropna()
            if len(qc_vals) == 0:
                continue
            qc_med = float(qc_vals['qc_ratio'].median())
            qc_maj = float((qc_vals['qc_ratio'] > 0.5).mean())
            regime = qc_regime_from_majority(qc_maj)
            # 3 metrics for this resolution
            atom_delta_r = compute_atom_delta(traj_r.rename(columns={'t': 'window_dummy'}))
            # ↑ window-level でなく per (cid, t) 差分。集約は window 内平均
            for mt in METRIC_TYPES:
                if mt == 'atom_delta':
                    sub_m = sub.sort_values(['cognitive_id', 't'])
                    sub_m['atom_delta'] = (sub_m.groupby('cognitive_id')['rank_1_sim']
                                                .diff().abs().fillna(0.0))
                    val = float(sub_m['atom_delta'].mean())
                    top_cid = int(sub_m.loc[sub_m['atom_delta'].idxmax()]['cognitive_id'])
                elif mt == 'rank1_flip_density':
                    sub_m = sub.sort_values(['cognitive_id', 't']).copy()
                    sub_m['prev_atom'] = sub_m.groupby('cognitive_id')['rank_1_atom'].shift(1)
                    sub_m['flip'] = np.where(
                        sub_m['prev_atom'].notna() & (sub_m['rank_1_atom'] != sub_m['prev_atom']),
                        1.0, 0.0)
                    val = float(sub_m['flip'].mean())
                    grp_flip = sub_m.groupby('cognitive_id')['flip'].sum()
                    top_cid = int(grp_flip.idxmax()) if len(grp_flip) else -1
                else:  # unit_kl_static — 時間軸なし、scope 全体で 1 つの値
                    cids_here = sub['cognitive_id'].unique().tolist()
                    unit_kl_sub = unit_kl_df[
                        unit_kl_df['cognitive_id'].isin(cids_here)
                    ].dropna(subset=['unit_kl_static'])
                    if len(unit_kl_sub) == 0:
                        continue
                    val = float(unit_kl_sub['unit_kl_static'].mean())
                    top_idx = unit_kl_sub['unit_kl_static'].idxmax()
                    if pd.isna(top_idx):
                        continue
                    top_cid = int(unit_kl_sub.loc[top_idx, 'cognitive_id'])

                emit_rows_extra = {
                    'seed': seed,
                    'window': int(w),
                    'change_scope': resolution_name,
                    'scope_id': -1,
                    'change_metric_type': mt,
                    'change_metric_value': val,
                    'change_rank_within_type': 0,
                    'attention_candidate_id': top_cid,
                    'qc_ratio': qc_med,
                    'qc_ratio_majority': qc_maj,
                    'qc_ratio_aggregation': 'median+majority',
                    'qc_regime': regime,
                    'predicted_lock_mode': predicted_lock_mode_from_regime(regime),
                    'n_units_in_scope': int(len(qc_vals)),
                    'predecessor_attention_ref': pd.NA,
                }
                df_emit = pd.concat([df_emit, pd.DataFrame([emit_rows_extra])],
                                    ignore_index=True)

    # ── predecessor_attention_ref (箱 1)、全 scope 再走
    # 同 seed + 同 change_scope + 同 change_metric_type の中で (粒度 iii)、
    # 現 window より前で qc_regime=cognitive_dominant の中で最も直近の
    # attention_candidate_id を参照。scope_id 単位 (CID は cid 別、ESDE は -1 集約)。
    if len(df_emit) > 0:
        df_emit = df_emit.sort_values(['change_scope', 'change_metric_type',
                                        'scope_id', 'window']).reset_index(drop=True)
        df_emit['predecessor_attention_ref'] = pd.NA
        for (cs, mt, sid), grp in df_emit.groupby(
                ['change_scope', 'change_metric_type', 'scope_id']):
            last_cog = pd.NA
            for idx in grp.index:
                row = df_emit.loc[idx]
                if row['qc_regime'] == 'conscious_dominant' and not pd.isna(last_cog):
                    df_emit.at[idx, 'predecessor_attention_ref'] = last_cog
                if row['qc_regime'] == 'cognitive_dominant':
                    last_cog = int(row['attention_candidate_id'])

    # placeholder for Step D / E columns (filled later)
    df_emit['causality_candidate_path'] = pd.NA   # Step E
    df_emit['influence_candidate_count'] = pd.NA  # Step D

    elapsed = time.time() - t0
    if verbose:
        print(f'[seed {seed}] emit records={len(df_emit)}, elapsed={elapsed:.1f}s',
              flush=True)
    return df_emit


# ──────────────────────────────────────────────────────────────────
# main
# ──────────────────────────────────────────────────────────────────
def parse_seeds(spec: str) -> list[int]:
    if '..' in spec:
        lo, hi = spec.split('..')
        return list(range(int(lo), int(hi) + 1))
    return [int(s) for s in spec.split(',')]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', default='0', help='e.g. "0" or "0..23" or "0,1,2"')
    ap.add_argument('--smoke-or-main', default='smoke', choices=['smoke', 'main'])
    args = ap.parse_args()

    seeds = parse_seeds(args.seeds)
    out_dir = OUT_SMOKE if args.smoke_or_main == 'smoke' else OUT_MAIN
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f'=== v1101a Step C — attention emit ===')
    print(f'seeds: {seeds}')
    print(f'output dir: {out_dir}')
    print()

    all_dfs = []
    t_start = time.time()
    for sd in seeds:
        df = process_seed(sd, verbose=True)
        out_path = out_dir / f'attention_emit_seed{sd}.parquet'
        df.to_parquet(out_path, index=False)
        print(f'  → wrote {out_path} ({len(df)} rows)')
        all_dfs.append(df)
        print()

    if len(all_dfs) > 1:
        df_all = pd.concat(all_dfs, ignore_index=True)
        out_path = out_dir / 'attention_emit_all.parquet'
        df_all.to_parquet(out_path, index=False)
        print(f'  → concat: {out_path} ({len(df_all)} rows)')

    total_t = time.time() - t_start
    print(f'\ndone, total elapsed {total_t:.1f}s')


if __name__ == '__main__':
    main()
