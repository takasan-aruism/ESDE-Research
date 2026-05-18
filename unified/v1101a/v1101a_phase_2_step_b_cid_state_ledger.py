#!/usr/bin/env python3
"""v1101a 段階 2 Step B — cid state ledger 再生 (a) 簡易版

設計書 §2.5 + 認識確認 §2.2 (a) 簡易版採用 (Taka 確定 2026-05-19):
- 入力: atom_introduction_events_v108_standard_seed{N}.parquet (24 seeds 揃い、
  段階 1 attention_candidate_id を 98.7% カバー) + atom_profiles_cache.npz
  (326 atom 参照ベクトル)
- per (cid, window) で「これまでに intro された atom 集合」累積
- atom_profiles[intro_atoms].mean(axis=0) → cid_vec
- cosine_sim(cid_vec, atom_profiles[326 atoms]) → 326 atom 濃度

留保 #L1 対応: 時間軸付き unit_KL_delta を per (cid_pair, window) + 単一 cid
の per-window 自己 KL 差分で算出。出力に「(a) 簡易版 atom_profiles mean ベース、
完全再現の濃度時系列ではない」性質を明記 (Taka 条件、2026-05-19)。

留保 #41 段階 1 解決済 (Code A 認識確認 §1.1): 本 Step は member_cids 復元を
行わない、段階 1 取得済の member 情報を使用前提。

書き込み: unified/v1101a/outputs/{smoke,main}/ 配下のみ。
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V106_MAIN = REPO_ROOT / 'developmental/v106/outputs/main'
V112_MAIN = REPO_ROOT / 'developmental/v112/outputs/main'
V1101A_ROOT = REPO_ROOT / 'unified/v1101a'
OUT_MAIN = V1101A_ROOT / 'outputs/main'
OUT_SMOKE = V1101A_ROOT / 'outputs/smoke'

ATOM_PROFILES_CACHE = V106_MAIN / 'atom_profiles_cache.npz'


def load_atom_profiles():
    cache = np.load(ATOM_PROFILES_CACHE)
    atom_names = cache['atom_names']  # (326,) str
    profiles = cache['profiles']  # (326, 48) float32
    valid_mask = cache['valid_mask']  # (326,) bool
    return list(atom_names), profiles, valid_mask


def load_window_step_map(seed: int) -> dict:
    """v10.6 window_trajectory から per-window 終端 step を取得。"""
    p = V106_MAIN / 'window_trajectory' / f'window_cid_alignment_seed{seed}.csv'
    df = pd.read_csv(p, usecols=['window', 'step_at_window_end'])
    return df.groupby('window')['step_at_window_end'].max().to_dict()


def load_attention_candidate_cids(seed: int, src_dir: Path) -> set[int]:
    """段階 1 attention_emit から unique attention_candidate_id 集合"""
    p = src_dir / f'attention_emit_seed{seed}.parquet'
    df = pd.read_parquet(p, columns=['attention_candidate_id'])
    return set(df['attention_candidate_id'].dropna().astype(int).unique())


def load_atom_intro_events(seed: int) -> pd.DataFrame:
    """v108_standard を採用 (段階 1 attention_candidate_id を 98.7% カバー)"""
    p = V112_MAIN / f'atom_introduction_events_v108_standard_seed{seed}.parquet'
    return pd.read_parquet(p, columns=['source_cid', 'timestamp', 'atom_id'])


def reconstruct_per_seed(seed: int, atom_names: list[str],
                          atom_profiles: np.ndarray, valid_mask: np.ndarray,
                          src_dir: Path, verbose: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    t0 = time.time()
    intro = load_atom_intro_events(seed)
    win_step = load_window_step_map(seed)
    attn_cids = load_attention_candidate_cids(seed, src_dir)

    atom_to_idx = {a: i for i, a in enumerate(atom_names)}
    valid_idx = np.where(valid_mask)[0]

    windows = sorted(win_step.keys())
    # intro events を timestamp 順にソート
    intro_sorted = intro.sort_values('timestamp').reset_index(drop=True)
    # cid フィルタ: 段階 1 attention_candidate_id に絞る (覆盖率 98.7%)
    intro_filt = intro_sorted[intro_sorted['source_cid'].isin(attn_cids)].copy()
    if verbose:
        print(f'[seed {seed}] intro_filt={len(intro_filt)}, attn_cids={len(attn_cids)}, windows={len(windows)}',
              flush=True)

    # per cid, 累積 atom 集合 (atom_idx の set として保持)
    cid_atoms: dict[int, set[int]] = {c: set() for c in attn_cids}
    # 出力 records
    cid_state_records = []
    cid_vec_per_window = {}  # (cid, window) -> 326 dim vector
    # event を window で区切って累積
    event_ptr = 0
    n_events = len(intro_filt)
    for w in windows:
        end_step = win_step[w]
        while event_ptr < n_events:
            row = intro_filt.iloc[event_ptr]
            if row['timestamp'] > end_step:
                break
            cid = int(row['source_cid'])
            atom_id = row['atom_id']
            if atom_id in atom_to_idx:
                cid_atoms[cid].add(atom_to_idx[atom_id])
            event_ptr += 1
        # この window 終端での per-cid 状態を snapshot
        for cid in attn_cids:
            atom_set = cid_atoms[cid]
            if len(atom_set) == 0:
                # まだ atom intro なし → cid_vec 0、326 atom 濃度全 0
                concentrations = np.zeros(len(atom_names), dtype=np.float32)
                n_intro = 0
            else:
                cid_vec = atom_profiles[list(atom_set)].mean(axis=0)
                # 326 atom それぞれとの cosine_sim
                valid_profiles = atom_profiles[valid_idx]
                concentrations = np.zeros(len(atom_names), dtype=np.float32)
                concentrations[valid_idx] = cosine_similarity(
                    cid_vec.reshape(1, -1), valid_profiles)[0]
                n_intro = len(atom_set)
            cid_vec_per_window[(cid, w)] = concentrations
            rec = {'seed': seed, 'cid': cid, 'window': w, 'n_intro_atoms_cumulative': n_intro}
            for atom_idx, atom_name in enumerate(atom_names):
                rec[atom_name] = float(concentrations[atom_idx])
            cid_state_records.append(rec)

    df_state = pd.DataFrame(cid_state_records)

    # 時間軸付き unit_KL_delta (per cid の前後 window 自己 KL 差分)
    # 326 atom 濃度を確率分布として正規化、隣接 window で KL(p_t || p_{t+1})
    eps = 1e-12
    kl_records = []
    for cid in attn_cids:
        prev_p = None
        for w in windows:
            conc = cid_vec_per_window[(cid, w)]
            # 確率分布化: max を引いて非負化 + softening
            # 簡易版: 濃度値を非負シフトし正規化
            shifted = conc - conc.min() + eps
            p = shifted / shifted.sum()
            if prev_p is not None:
                # KL(prev_p || p) = sum prev * (log prev - log p)
                kl = float(np.sum(prev_p * (np.log(prev_p + eps) - np.log(p + eps))))
                kl_records.append({
                    'seed': seed, 'cid': cid, 'window': w, 'window_prev': w - 1,
                    'unit_kl_self_delta': kl,
                    'note_simplified': '(a) atom_profiles mean ベース簡易版',
                })
            prev_p = p

    df_kl = pd.DataFrame(kl_records)

    elapsed = time.time() - t0
    if verbose:
        print(f'[seed {seed}] cid_state={len(df_state)} rows, kl_delta={len(df_kl)} rows, '
              f'elapsed={elapsed:.1f}s', flush=True)
    return df_state, df_kl


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
    src_dir = OUT_SMOKE if args.smoke_or_main == 'smoke' else OUT_MAIN
    out_dir = src_dir

    print(f'=== v1101a 段階 2 Step B — cid state ledger 再生 (a) 簡易版 ===')
    print(f'seeds: {seeds}, src/out: {out_dir}')

    atom_names, atom_profiles, valid_mask = load_atom_profiles()
    print(f'atom_profiles: {len(atom_names)} atoms, valid {valid_mask.sum()}, '
          f'profile dim {atom_profiles.shape[1]}')
    print()

    state_dfs, kl_dfs = [], []
    t_start = time.time()
    for sd in seeds:
        df_state, df_kl = reconstruct_per_seed(
            sd, atom_names, atom_profiles, valid_mask, src_dir, verbose=True)
        state_path = out_dir / f'cid_state_ledger_seed{sd}.parquet'
        kl_path = out_dir / f'unit_kl_delta_seed{sd}.parquet'
        df_state.to_parquet(state_path, index=False)
        df_kl.to_parquet(kl_path, index=False)
        print(f'  → wrote {state_path.name} ({len(df_state)} rows) + {kl_path.name} ({len(df_kl)} rows)')
        state_dfs.append(df_state)
        kl_dfs.append(df_kl)
        print()

    if len(state_dfs) > 1:
        all_state = pd.concat(state_dfs, ignore_index=True)
        all_kl = pd.concat(kl_dfs, ignore_index=True)
        all_state.to_parquet(out_dir / 'cid_state_ledger_all.parquet', index=False)
        all_kl.to_parquet(out_dir / 'unit_kl_delta_all.parquet', index=False)
        print(f'  → concat: cid_state_ledger_all ({len(all_state)} rows), '
              f'unit_kl_delta_all ({len(all_kl)} rows)')

    total = time.time() - t_start
    print(f'\ndone, total elapsed {total:.1f}s')


if __name__ == '__main__':
    main()
