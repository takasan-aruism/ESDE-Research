#!/usr/bin/env python3
"""v1104 Step B — 観察 1: CID-Integration 像の差分

設計書 §2.1 + Step A §1.3 確定:
- match_rate_k1: 各 CID 単独 rank_1_atom と Integration α top_atom の完全一致率
- jaccard_top3: 各 CID 単独 (cid_atom_sim_matrix) top-3 atom 集合 と α top-3 集合
  の Jaccard、member 平均
- jaccard_top5: 同 top-5
- 不一致パターン分類 (category 内置換 / 間置換)
- Step G n_members_bin × qc_gini_bin で層化

入力:
- alpha_lifecycle_log_seed{N}.csv (per-step member 構成変化)
- v10.6 window_trajectory (per (cid, window) rank_1_atom)
- v10.6 cid_atom_sim_matrix (per cid 326 atom 静的濃度)
- v1101a integration_composition_alpha.parquet (Step G、n_members/qc_gini)

出力: observation_1_cid_integration.parquet
書込み: unified/v1104/outputs/main/ のみ
"""
from __future__ import annotations
import argparse, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V105_INT = REPO_ROOT / 'developmental/v105/diag_v105_main/integration'
V106_MAIN = REPO_ROOT / 'developmental/v106/outputs/main'
V1101A_MAIN = REPO_ROOT / 'unified/v1101a/outputs/main'
OUT_MAIN = REPO_ROOT / 'unified/v1104/outputs/main'

WINDOW_RANGE = list(range(20, 70))  # window 20-69 (Step A §5.1 確定、window=19 除外)


def replay_alpha_lifecycle(seed: int) -> pd.DataFrame:
    """alpha_lifecycle_log を per-step replay、(step, alpha_id, member_cids set) 列を返す"""
    p = V105_INT / f'alpha_lifecycle_log_seed{seed}.csv'
    df = pd.read_csv(p)
    df = df.sort_values('step').reset_index(drop=True)
    # alpha_id -> current member_cids set (state)
    state: dict[int, set[int]] = {}
    rows = []
    for _, ev in df.iterrows():
        aid = int(ev['alpha_id'])
        et = ev['event_type']
        mc_str = str(ev.get('member_cids', ''))
        mc_set = set(int(x) for x in mc_str.split('|') if x.strip().isdigit())
        if et == 'birth':
            state[aid] = mc_set
        elif et == 'member_ghosted':
            # member_cids 列は ghost 後の残り cids
            state[aid] = mc_set if mc_set else state.get(aid, set())
        elif et == 'active_to_recorded':
            # 状態は維持 (member は変わらない想定)
            pass
        rows.append({
            'seed': seed,
            'step': int(ev['step']),
            'alpha_id': aid,
            'event_type': et,
            'member_cids_after': sorted(state.get(aid, set())),
        })
    return pd.DataFrame(rows)


def get_per_window_active_members(seed: int, window_step_map: dict) -> pd.DataFrame:
    """各 window の終端 step 時点での per (alpha_id) active member_cids"""
    lifecycle = replay_alpha_lifecycle(seed)
    # per (alpha_id, step) の latest state
    lifecycle_sorted = lifecycle.sort_values(['alpha_id', 'step'])

    rows = []
    for w, end_step in window_step_map.items():
        # この window 終端 step までの最新 state per alpha_id
        sub = lifecycle_sorted[lifecycle_sorted['step'] <= end_step]
        latest = sub.groupby('alpha_id').tail(1)
        for _, r in latest.iterrows():
            members = r['member_cids_after']
            if not members:
                continue
            rows.append({
                'seed': seed,
                'window': w,
                'alpha_id': int(r['alpha_id']),
                'member_cids': members,
                'n_members': len(members),
            })
    return pd.DataFrame(rows)


def category_of(atom: str) -> str:
    return atom.split('.')[0] if isinstance(atom, str) and '.' in atom else 'UNK'


def compute_observation_1(seed: int, verbose: bool = True) -> pd.DataFrame:
    t0 = time.time()
    # v10.6 window_trajectory load
    p = V106_MAIN / 'window_trajectory' / f'window_cid_alignment_seed{seed}.csv'
    win_traj = pd.read_csv(p, usecols=['cognitive_id', 'window', 'step_at_window_end',
                                         'rank_1_atom'])
    win_traj = win_traj[win_traj['window'].isin(WINDOW_RANGE)]
    # window → step_at_window_end map
    window_step_map = (win_traj.groupby('window')['step_at_window_end']
                        .max().to_dict())

    # per (cid, window) rank_1_atom
    cid_rank1 = win_traj.set_index(['cognitive_id', 'window'])['rank_1_atom'].to_dict()

    # v10.6 cid_atom_sim_matrix (per cid 326 atom 濃度、static)
    sim_p = V106_MAIN / f'cid_atom_sim_matrix_seed{seed}.parquet'
    sim_df = pd.read_parquet(sim_p)
    atom_cols = [c for c in sim_df.columns if c not in ('seed', 'cid')]
    # per cid top-3 / top-5 atoms (静的)
    cid_top3 = {}
    cid_top5 = {}
    for _, row in sim_df.iterrows():
        cid = int(row['cid'])
        vals = row[atom_cols].astype(float)
        # NaN を最小値扱い (sim_matrix の per-cid 1 cell NaN、段階 2 で nan_to_num 処理)
        vals = vals.fillna(-np.inf)
        top_idx = vals.nlargest(5).index.tolist()
        cid_top3[cid] = set(top_idx[:3])
        cid_top5[cid] = set(top_idx[:5])

    # per-window active members
    active = get_per_window_active_members(seed, window_step_map)
    if verbose:
        print(f'[seed {seed}] active alpha-window records: {len(active)}, '
              f'elapsed setup: {time.time()-t0:.1f}s')

    # observation 1 計算
    rows = []
    for _, r in active.iterrows():
        w = int(r['window'])
        members = r['member_cids']
        if len(members) < 1:
            continue
        # 各 member の per-window rank_1_atom
        member_ranks = []
        for cid in members:
            rk = cid_rank1.get((cid, w))
            if isinstance(rk, str):
                member_ranks.append(rk)
        if not member_ranks:
            continue
        # alpha top_atom (member rank_1 multiset の modal value)
        from collections import Counter
        c = Counter(member_ranks)
        alpha_top_atom, alpha_top_count = c.most_common(1)[0]
        # alpha top-3 / top-5 (頻度順)
        alpha_top3 = set(a for a, _ in c.most_common(3))
        alpha_top5 = set(a for a, _ in c.most_common(5))

        # match_rate_k1
        match_k1 = alpha_top_count / len(member_ranks)

        # jaccard_top3 / top5: 各 member cid の cid_atom_sim_matrix top-3/5 と alpha top-3/5 の Jaccard、member 平均
        j3s = []
        j5s = []
        for cid in members:
            if cid in cid_top3:
                inter3 = len(cid_top3[cid] & alpha_top3)
                union3 = len(cid_top3[cid] | alpha_top3)
                j3s.append(inter3 / union3 if union3 > 0 else 0.0)
                inter5 = len(cid_top5[cid] & alpha_top5)
                union5 = len(cid_top5[cid] | alpha_top5)
                j5s.append(inter5 / union5 if union5 > 0 else 0.0)
        jaccard_top3 = float(np.mean(j3s)) if j3s else np.nan
        jaccard_top5 = float(np.mean(j5s)) if j5s else np.nan

        # 不一致パターン分類: k=1 で不一致時、置換 atom の category
        n_intra_cat = 0
        n_inter_cat = 0
        n_match = 0
        alpha_cat = category_of(alpha_top_atom)
        for rk in member_ranks:
            if rk == alpha_top_atom:
                n_match += 1
            else:
                if category_of(rk) == alpha_cat:
                    n_intra_cat += 1
                else:
                    n_inter_cat += 1

        rows.append({
            'seed': seed,
            'window': w,
            'alpha_id': int(r['alpha_id']),
            'n_members': int(r['n_members']),
            'n_members_with_rank1': len(member_ranks),
            'alpha_top_atom': alpha_top_atom,
            'alpha_top_count': alpha_top_count,
            'match_rate_k1': match_k1,
            'jaccard_top3': jaccard_top3,
            'jaccard_top5': jaccard_top5,
            'n_match': n_match,
            'n_intra_category_mismatch': n_intra_cat,
            'n_inter_category_mismatch': n_inter_cat,
        })

    df = pd.DataFrame(rows)
    if verbose:
        print(f'[seed {seed}] obs1 rows: {len(df)}, elapsed: {time.time()-t0:.1f}s')
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', default='0..23')
    args = ap.parse_args()
    lo, hi = args.seeds.split('..')
    seeds = list(range(int(lo), int(hi)+1))

    OUT_MAIN.mkdir(parents=True, exist_ok=True)
    print(f'=== v1104 Step B 観察 1 (CID-Integration 像の差分) ===')
    print(f'seeds: {seeds}, window range: {WINDOW_RANGE[0]}-{WINDOW_RANGE[-1]} ({len(WINDOW_RANGE)} windows)')
    print()

    t_start = time.time()
    dfs = []
    for sd in seeds:
        df = compute_observation_1(sd, verbose=True)
        dfs.append(df)

    all_df = pd.concat(dfs, ignore_index=True)

    # Step G n_members_bin × qc_gini_bin で層化
    print('\nStep G composition と join...')
    comp = pd.read_parquet(V1101A_MAIN / 'integration_composition_alpha.parquet')
    all_df = all_df.merge(comp[['seed', 'alpha_id', 'n_members', 'qc_gini_mean']]
                            .rename(columns={'n_members': 'n_members_total',
                                              'qc_gini_mean': 'qc_gini_total'}),
                            on=['seed', 'alpha_id'], how='left')

    def n_bin(n):
        if pd.isna(n): return 'NA'
        n = int(n)
        if n == 1: return 'n=1'
        if n == 2: return 'n=2'
        if n == 3: return 'n=3'
        return 'n=4+'

    def gini_bin(g):
        if pd.isna(g): return 'NA'
        if g < 0.05: return 'low'
        if g < 0.20: return 'mid'
        return 'high'

    all_df['n_members_bin'] = all_df['n_members_total'].apply(n_bin)
    all_df['qc_gini_bin'] = all_df['qc_gini_total'].apply(gini_bin)

    out = OUT_MAIN / 'observation_1_cid_integration.parquet'
    all_df.to_parquet(out, index=False)
    print(f'\nwrote {out} ({len(all_df):,} rows)')

    # サマリ
    print(f'\n=== 全 24 seeds サマリ ===')
    print(f'total alpha-window records: {len(all_df):,}')
    print(f'match_rate_k1 mean: {all_df["match_rate_k1"].mean():.4f}')
    print(f'jaccard_top3 mean: {all_df["jaccard_top3"].mean():.4f}')
    print(f'jaccard_top5 mean: {all_df["jaccard_top5"].mean():.4f}')
    print()
    print('=== 層化サマリ (n_members_bin × qc_gini_bin) ===')
    g = all_df.groupby(['n_members_bin', 'qc_gini_bin']).agg(
        n_records=('alpha_id', 'count'),
        match_k1_mean=('match_rate_k1', 'mean'),
        jaccard_top3_mean=('jaccard_top3', 'mean'),
        jaccard_top5_mean=('jaccard_top5', 'mean'),
        inter_cat_mean=('n_inter_category_mismatch', 'mean'),
    ).round(4)
    print(g.to_string())

    print(f'\ntotal elapsed: {time.time()-t_start:.1f}s')


if __name__ == '__main__':
    main()
