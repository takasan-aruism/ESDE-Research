#!/usr/bin/env python3
"""
v11.0.1.a (v1101a) Step E — 因果候補抽出 (causality_candidate_path + effect size)
設計書 §3.3「因果候補 — 注意候補を source として v10.7 5 種 relation_path で
繋がっている target を取る」、絶対格言 #10 (因果でなく因果候補) + #3 (効果サイズ)。

per (seed, source_cid=attention_candidate_id) で v10.7 relation_paths から
5 path_type 別 sum(relation_strength) を集約 → argmax = causality_candidate_path。
baselines_with_delta で per (seed, source_cid, path_type) の delta_Q_short /
delta_C_short / delta_R_familiarity_short 平均値を effect size として保存。

時間軸の扱い (留保): v10.7 relation_paths の timestamp は per event (秒/step)、
本 Step は per source_cid で全 timestamp 集約 (run 全体 static path map、
v10.7 attention_via_salience build_attention_via_salience_targets と同じ集約
スタイル)。段階 1 では時間軸付き解像度を採らず、static 集約のみ。

usage:
    python v1101a_step_e_attention_causality.py --seeds 0..23 --smoke-or-main main
    python v1101a_step_e_attention_causality.py --seeds 0 --smoke-or-main smoke
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V107_MAIN = REPO_ROOT / 'developmental/v107/outputs/main'
V1101A_ROOT = REPO_ROOT / 'unified/v1101a'
OUT_MAIN = V1101A_ROOT / 'outputs/main'
OUT_SMOKE = V1101A_ROOT / 'outputs/smoke'

PATH_TYPES = ['familiarity', 'attention_via_salience', 'integration_alpha',
              'integration_beta', 'temporal_coactivation']


def load_relation_paths(seed: int) -> pd.DataFrame:
    p = V107_MAIN / f'relation_paths_seed{seed}.parquet'
    return pd.read_parquet(p, columns=['source_cid', 'target_cid',
                                        'relation_path_type', 'relation_strength'])


def load_baselines_with_delta(seed: int) -> pd.DataFrame:
    p = V107_MAIN / f'baselines_with_delta_seed{seed}.parquet'
    return pd.read_parquet(p, columns=['source_cid', 'target_cid',
                                        'relation_path_type',
                                        'delta_Q_short', 'delta_C_short',
                                        'delta_R_familiarity_short'])


def load_attention_propagation(seed: int, src_dir: Path) -> pd.DataFrame:
    p = src_dir / f'attention_propagation_seed{seed}.parquet'
    return pd.read_parquet(p)


def compute_causality(seed: int, src_dir: Path, verbose: bool = True) -> pd.DataFrame:
    t0 = time.time()
    propag = load_attention_propagation(seed, src_dir)
    rel = load_relation_paths(seed)
    base = load_baselines_with_delta(seed)

    if verbose:
        print(f'[seed {seed}] propag rows={len(propag)}, relation_paths rows={len(rel)}, '
              f'baselines rows={len(base)}', flush=True)

    # ── per (source_cid, path_type) で strength 集約 + target count
    rel_agg = (rel.groupby(['source_cid', 'relation_path_type'])
                  .agg(strength_sum=('relation_strength', 'sum'),
                       n_targets=('target_cid', 'nunique'))
                  .reset_index())

    # ── per (source_cid) で 5 path_type の strength_sum を wide 化
    wide = rel_agg.pivot_table(index='source_cid',
                                columns='relation_path_type',
                                values='strength_sum',
                                fill_value=0.0).reset_index()
    # 欠落する path_type は 0 で fill
    for pt in PATH_TYPES:
        if pt not in wide.columns:
            wide[pt] = 0.0
    path_cols = [pt for pt in PATH_TYPES if pt in wide.columns]

    # ── 方式 1: sum argmax (現方式、現 causality_candidate_path_sum)
    wide['causality_candidate_path_sum'] = wide[path_cols].idxmax(axis=1)
    wide['causality_strength_sum_max'] = wide[path_cols].max(axis=1)
    wide['causality_strength_sum_total'] = wide[path_cols].sum(axis=1)

    # ── 方式 2: z-score argmax (path 内正規化、留保 #L5 対応)
    # 指示書 §4.3: 分散 0 path (integration の 1.0 固定 binary は per-source sum で
    # は分布が散るため通常 std > 0、ただし極端ケース対応として std < 1e-9 で z=0)。
    # 構造的決定、ハンドチューニングなし (絶対格言 #9)。
    zscore_data = {}
    for pt in path_cols:
        vals = wide[pt].to_numpy(dtype=float)
        mean = float(vals.mean())
        std = float(vals.std(ddof=0))
        if std < 1e-9:
            zscore_data[f'zscore_{pt}'] = pd.Series([0.0] * len(wide), index=wide.index)
        else:
            zscore_data[f'zscore_{pt}'] = pd.Series((vals - mean) / std, index=wide.index)
    zscore_df = pd.DataFrame(zscore_data)
    wide = pd.concat([wide, zscore_df], axis=1)

    zscore_cols = [f'zscore_{pt}' for pt in path_cols]
    # argmax で path_type 名取得 (zscore_ prefix を除去)
    wide['causality_candidate_path_zscore'] = (
        wide[zscore_cols].idxmax(axis=1).str.replace('zscore_', '', regex=False))
    wide['causality_zscore_max'] = wide[zscore_cols].max(axis=1)

    # 列名を分かりやすく
    rename_map = {pt: f'strength_{pt}' for pt in path_cols}
    wide = wide.rename(columns=rename_map)

    # ── effect size: per (source_cid, path_type) の delta_* 平均
    base_agg = (base.groupby(['source_cid', 'relation_path_type'])
                    .agg(effect_delta_Q_short=('delta_Q_short', 'mean'),
                         effect_delta_C_short=('delta_C_short', 'mean'),
                         effect_delta_R_short=('delta_R_familiarity_short', 'mean'),
                         n_baseline_rows=('delta_Q_short', 'size'))
                    .reset_index())

    # propag.attention_candidate_id を source_cid として merge
    # Step C placeholder の causality_candidate_path 列を drop してから merge
    propag_clean = propag.drop(columns=['causality_candidate_path'], errors='ignore')
    merged = propag_clean.merge(
        wide,
        left_on='attention_candidate_id', right_on='source_cid',
        how='left'
    ).drop(columns=['source_cid'])

    # ── effect size を 2 方式それぞれの causality_path に基づき lookup
    # sum 方式の effect
    base_sum = base_agg.rename(columns={
        'relation_path_type': 'causality_candidate_path_sum',
        'effect_delta_Q_short': 'effect_delta_Q_short_sum',
        'effect_delta_C_short': 'effect_delta_C_short_sum',
        'effect_delta_R_short': 'effect_delta_R_short_sum',
        'n_baseline_rows': 'n_baseline_rows_sum',
    })
    merged = merged.merge(
        base_sum,
        left_on=['attention_candidate_id', 'causality_candidate_path_sum'],
        right_on=['source_cid', 'causality_candidate_path_sum'],
        how='left',
    )
    if 'source_cid' in merged.columns:
        merged = merged.drop(columns=['source_cid'])

    # z-score 方式の effect
    base_zscore = base_agg.rename(columns={
        'relation_path_type': 'causality_candidate_path_zscore',
        'effect_delta_Q_short': 'effect_delta_Q_short_zscore',
        'effect_delta_C_short': 'effect_delta_C_short_zscore',
        'effect_delta_R_short': 'effect_delta_R_short_zscore',
        'n_baseline_rows': 'n_baseline_rows_zscore',
    })
    merged = merged.merge(
        base_zscore,
        left_on=['attention_candidate_id', 'causality_candidate_path_zscore'],
        right_on=['source_cid', 'causality_candidate_path_zscore'],
        how='left',
    )
    if 'source_cid' in merged.columns:
        merged = merged.drop(columns=['source_cid'])

    elapsed = time.time() - t0
    if verbose:
        print(f'[seed {seed}] causality done, records={len(merged)}, '
              f'unique sources matched={wide.shape[0]}, elapsed={elapsed:.1f}s',
              flush=True)
    return merged


def parse_seeds(spec: str) -> list[int]:
    if '..' in spec:
        lo, hi = spec.split('..')
        return list(range(int(lo), int(hi) + 1))
    return [int(s) for s in spec.split(',')]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', default='0..23', help='e.g. "0..23"')
    ap.add_argument('--smoke-or-main', default='main', choices=['smoke', 'main'])
    args = ap.parse_args()

    seeds = parse_seeds(args.seeds)
    src_dir = OUT_SMOKE if args.smoke_or_main == 'smoke' else OUT_MAIN
    out_dir = src_dir

    print(f'=== v1101a Step E — attention causality ===')
    print(f'seeds: {seeds}')
    print(f'src/out dir: {out_dir}')
    print()

    all_dfs = []
    t_start = time.time()
    for sd in seeds:
        df = compute_causality(sd, src_dir, verbose=True)
        out_path = out_dir / f'attention_causality_seed{sd}.parquet'
        df.to_parquet(out_path, index=False)
        print(f'  → wrote {out_path} ({len(df)} rows)')
        all_dfs.append(df)
        print()

    if len(all_dfs) > 1:
        df_all = pd.concat(all_dfs, ignore_index=True)
        out_path = out_dir / 'attention_causality_all.parquet'
        df_all.to_parquet(out_path, index=False)
        print(f'  → concat: {out_path} ({len(df_all)} rows)')

    total_t = time.time() - t_start
    print(f'\ndone, total elapsed {total_t:.1f}s')


if __name__ == '__main__':
    main()
