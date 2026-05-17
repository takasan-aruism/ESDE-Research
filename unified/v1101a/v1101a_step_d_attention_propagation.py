#!/usr/bin/env python3
"""
v11.0.1.a (v1101a) Step D — 注意候補中心の波及 (influence_candidate_count)
設計書 §3.3「注意候補中心の波及 = 影響候補」、v1101 observation_2 同型、source 置換。

中心 = Step C 出力 attention_candidate_id (= 各 (scope, metric_type) での最大変化 cid)
Δt 範囲 = ±10 windows (v1101 observation_2 と同じ 21 点)
influence_candidate_count = Δt 範囲内で周辺 cid の rank_1_atom が
    中心 cid の t0 rank_1_atom と一致した cid-window 数 (sum)

post-process のみ、書き込み unified/v1101a/outputs/ 配下。

usage:
    python v1101a_step_d_attention_propagation.py --seeds 0..23 --smoke-or-main main
    python v1101a_step_d_attention_propagation.py --seeds 0 --smoke-or-main smoke
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V106_MAIN = REPO_ROOT / 'developmental/v106/outputs/main'
V1101A_ROOT = REPO_ROOT / 'unified/v1101a'
OUT_MAIN = V1101A_ROOT / 'outputs/main'
OUT_SMOKE = V1101A_ROOT / 'outputs/smoke'

DELTA_T_HALF = 10  # ±10 windows = 21 points (v1101 observation_2 同型)


def load_window_trajectory(seed: int) -> pd.DataFrame:
    p = V106_MAIN / 'window_trajectory' / f'window_cid_alignment_seed{seed}.csv'
    df = pd.read_csv(p)
    return df[['cognitive_id', 'window', 'rank_1_atom']].copy()


def load_attention_emit(seed: int, src_dir: Path) -> pd.DataFrame:
    p = src_dir / f'attention_emit_seed{seed}.parquet'
    return pd.read_parquet(p)


def compute_propagation(seed: int, src_dir: Path, verbose: bool = True) -> pd.DataFrame:
    t0 = time.time()
    emit = load_attention_emit(seed, src_dir)
    win_traj = load_window_trajectory(seed)

    if verbose:
        print(f'[seed {seed}] emit rows={len(emit)}, window_traj rows={len(win_traj)}',
              flush=True)

    # cid → (window → rank_1_atom) lookup
    # window_traj: (cognitive_id, window, rank_1_atom)
    # multi-index for fast lookup
    wt_idx = win_traj.set_index(['cognitive_id', 'window'])['rank_1_atom']

    # unique (window, attention_candidate_id) — center 重複排除
    centers = (emit[['window', 'attention_candidate_id']]
               .dropna(subset=['attention_candidate_id'])
               .drop_duplicates()
               .reset_index(drop=True))
    if verbose:
        print(f'[seed {seed}] unique centers (window, cand) = {len(centers)}', flush=True)

    # pre-build per-window cid→rank_1_atom dict for fast lookup
    by_window = {int(w): grp.set_index('cognitive_id')['rank_1_atom'].to_dict()
                 for w, grp in win_traj.groupby('window')}
    all_cids = sorted(win_traj['cognitive_id'].unique().tolist())
    all_windows = sorted(by_window.keys())

    rows = []
    for _, c in centers.iterrows():
        w0 = int(c['window'])
        cid0 = int(c['attention_candidate_id'])
        # center の t0 rank_1_atom (window=w0 で cid=cid0)
        atom0 = by_window.get(w0, {}).get(cid0)
        if atom0 is None or (isinstance(atom0, float) and np.isnan(atom0)):
            rows.append({
                'window': w0,
                'attention_candidate_id': cid0,
                'center_atom_t0': None,
                'influence_candidate_count': 0,
                'n_delta_t_points': 0,
                'n_peripheral_cids_alive': 0,
            })
            continue
        # Δt 範囲: w0 ± DELTA_T_HALF
        target_windows = [w for w in range(w0 - DELTA_T_HALF, w0 + DELTA_T_HALF + 1)
                          if w in by_window]
        n_match = 0
        n_peripheral_alive = 0
        for wt in target_windows:
            wdict = by_window[wt]
            for cid_p, atom_p in wdict.items():
                if cid_p == cid0 and wt == w0:
                    continue  # exclude center self at t0
                n_peripheral_alive += 1
                if atom_p == atom0:
                    n_match += 1
        rows.append({
            'window': w0,
            'attention_candidate_id': cid0,
            'center_atom_t0': atom0,
            'influence_candidate_count': n_match,
            'n_delta_t_points': len(target_windows),
            'n_peripheral_cids_alive': n_peripheral_alive,
        })

    df_centers = pd.DataFrame(rows)
    df_centers['seed'] = seed

    # join back to emit records (per record キーは window + attention_candidate_id)
    merged = emit.merge(
        df_centers[['window', 'attention_candidate_id',
                    'center_atom_t0', 'influence_candidate_count',
                    'n_delta_t_points', 'n_peripheral_cids_alive']],
        on=['window', 'attention_candidate_id'],
        how='left',
        suffixes=('', '_d')
    )
    # Step C placeholder の influence_candidate_count を上書き
    if 'influence_candidate_count_d' in merged.columns:
        merged['influence_candidate_count'] = merged['influence_candidate_count_d']
        merged = merged.drop(columns=['influence_candidate_count_d'])

    elapsed = time.time() - t0
    if verbose:
        print(f'[seed {seed}] propagation done, '
              f'records={len(merged)}, centers={len(df_centers)}, '
              f'elapsed={elapsed:.1f}s', flush=True)
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

    print(f'=== v1101a Step D — attention propagation ===')
    print(f'seeds: {seeds}')
    print(f'src/out dir: {out_dir}')
    print()

    all_dfs = []
    t_start = time.time()
    for sd in seeds:
        df = compute_propagation(sd, src_dir, verbose=True)
        out_path = out_dir / f'attention_propagation_seed{sd}.parquet'
        df.to_parquet(out_path, index=False)
        print(f'  → wrote {out_path} ({len(df)} rows)')
        all_dfs.append(df)
        print()

    if len(all_dfs) > 1:
        df_all = pd.concat(all_dfs, ignore_index=True)
        out_path = out_dir / 'attention_propagation_all.parquet'
        df_all.to_parquet(out_path, index=False)
        print(f'  → concat: {out_path} ({len(df_all)} rows)')

    total_t = time.time() - t_start
    print(f'\ndone, total elapsed {total_t:.1f}s')


if __name__ == '__main__':
    main()
