#!/usr/bin/env python3
"""v1105a Step D — 試行 Step 3: rank-based 絞り 7 系列並列 (per-atom rank)

設計書 v3 §2.4 通り、rank_source/trajectory/density 3 軸を per-atom 計算、
緩やか減衰関数 w = 1/log(rank+2) の積で score、各系列内で正規化。
7 系列並列、B emit は read-only 観察列、独自発明禁止。

3 軸 per-atom rank:
- rank_source: Step C 4 source レイヤー出現回数 (高頻度 = 上位 rank)
- rank_trajectory: per-atom stability (v1101a attention_emit から ESDE 細粒
  scope で計算)
- rank_density: per-atom density (v1103 atom_centroids から cosine_sim 計算、
  7 系列別)

7 系列:
- 系列 1: raw_density × sim_basis=raw
- 系列 2: raw_density × sim_basis=norm
- 系列 3: qweighted_density × raw (× focus_rate_mean)
- 系列 4: qweighted_density × norm
- 系列 5: const_adjusted × raw (× couple_bonus 1.1)
- 系列 6: const_adjusted × norm
- 系列 7: 48 次元 raw (k=5 制限、Step E で適用)

入力 (read-only):
  - unified/v1105a/outputs/main/trial_step2_associations.parquet (Step C 出力)
  - unified/v1101a/outputs/main/attention_emit_seed{N}.parquet (per-atom stability)
  - unified/v1103/outputs/main/atom_centroids_48d_raw.parquet
  - unified/v1103/outputs/main/atom_centroids_48d_normalized.parquet
  - unified/v1103/outputs/main/atom_quality.parquet
  - unified/v1103/outputs/main/proposals.json (couple endpoints for const_adjusted)
  - developmental/v106/outputs/main/cid_atom_sim_matrix_seed{N}.parquet (atom mapping)

出力:
  - unified/v1105a/outputs/main/trial_step3_distributions.parquet
    (per (seed, event_id, series_id, candidate_atom) で probability, ranks, B flag)
"""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

REPO = Path('/home/takasan/esde/ESDE-Research')
V1101A_MAIN = REPO / 'unified/v1101a/outputs/main'
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V1103_MAIN = REPO / 'unified/v1103/outputs/main'
V1105A_MAIN = REPO / 'unified/v1105a/outputs/main'

WINDOW_RANGE = range(20, 70)

SERIES = [
    ('s1_raw_density_raw', 'raw_density', 'raw'),
    ('s2_raw_density_norm', 'raw_density', 'norm'),
    ('s3_qweighted_density_raw', 'qweighted_density', 'raw'),
    ('s4_qweighted_density_norm', 'qweighted_density', 'norm'),
    ('s5_const_adjusted_density_raw', 'const_adjusted_density', 'raw'),
    ('s6_const_adjusted_density_norm', 'const_adjusted_density', 'norm'),
    ('s7_48d_raw_k5', 'raw_density', 'raw'),  # 48D k=5 制限は Step E で適用
]


def compute_per_atom_stability(seed: int) -> dict:
    """seed ごとに per-atom (= attention_candidate_id) stability を計算
    ESDE_event + ESDE_step10 scope に絞って (細粒、#L31 trajectory 主役)"""
    em = pd.read_parquet(V1101A_MAIN / f'attention_emit_seed{seed}.parquet',
                         columns=['window', 'change_scope', 'scope_id',
                                  'change_metric_type', 'attention_candidate_id',
                                  'qc_regime'])
    em = em[em['window'].isin(WINDOW_RANGE)].dropna(subset=['attention_candidate_id'])
    em['attention_candidate_id'] = em['attention_candidate_id'].astype(int)
    em = em[em['change_scope'].isin(['ESDE_event', 'ESDE_step10'])]

    stab = {}
    for atom_id in em['attention_candidate_id'].unique():
        # この atom が登場した chain (scope, scope_id, metric, qc_regime) を見つけ、
        # その chain で隣接 window で同 atom が連続した数 / chain length-1
        atom_grp = em[em['attention_candidate_id'] == atom_id]
        chain_keys = atom_grp[['change_scope', 'scope_id', 'change_metric_type',
                                'qc_regime']].drop_duplicates().values.tolist()
        n_same = 0
        n_pairs = 0
        for sc, sid, mt, rg in chain_keys:
            chain = em[(em['change_scope'] == sc) & (em['scope_id'] == sid) &
                       (em['change_metric_type'] == mt) & (em['qc_regime'] == rg)
                       ].sort_values('window')
            if len(chain) < 2:
                continue
            atoms = chain['attention_candidate_id'].values
            n_same += int(np.sum(atoms[1:] == atoms[:-1]))
            n_pairs += len(atoms) - 1
        stab[atom_id] = n_same / n_pairs if n_pairs > 0 else np.nan
    return stab


def main():
    V1105A_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1105a Step D 試行 Step 3 ===')
    t0 = time.time()

    # 共通データ load
    print('[1] 共通データ load')
    assoc = pd.read_parquet(V1105A_MAIN / 'trial_step2_associations.parquet')
    print(f'  Step C output: {len(assoc):,} rows')

    ac_raw = pd.read_parquet(V1103_MAIN / 'atom_centroids_48d_raw.parquet'
                              ).set_index('atom').drop(columns=['n_words'])
    ac_norm = pd.read_parquet(V1103_MAIN / 'atom_centroids_48d_normalized.parquet'
                               ).set_index('atom').drop(columns=['n_words'])
    aq = pd.read_parquet(V1103_MAIN / 'atom_quality.parquet').set_index('atom')

    # couple endpoints (const_adjusted bonus 用)
    with open(V1103_MAIN / 'proposals.json') as f:
        prop = json.load(f)
    couple_endpoints = set()
    for c in prop['proposals']:
        if c['pattern'] == 'B_COUPLE':
            couple_endpoints.add(c['atom_a'])
            couple_endpoints.add(c['atom_b'])

    # B 高 flag (v1102 outstanding_cells の B_outstanding_score >= 2)
    o4_bma = pd.read_parquet(REPO / 'unified/v1104a/outputs/main' /
                              'observation_4_b_minus_a_cells.parquet')
    b_high_atoms = set()  # B_outstanding_score >= 2 の cell に出現する atom_top1
    # observation_4_b_overlap.parquet の atom_top1 から B 高 atom を抽出
    o4 = pd.read_parquet(REPO / 'unified/v1104/outputs/main' /
                         'observation_4_b_overlap.parquet')
    b_high_atoms = set(o4[o4['B_outstanding_score'] >= 2]['atom_top1_name'].dropna())
    print(f'  B 高 atoms (B_score>=2): {len(b_high_atoms)}')

    # per-atom stability (seed 別、ESDE_event + ESDE_step10 統合)
    print('[2] per-atom stability 計算 (24 seeds)')
    seed_stab = {}
    for sd in range(24):
        seed_stab[sd] = compute_per_atom_stability(sd)
    print(f'  stability lookup 構築完了')

    # atom mapping (per seed の cid_atom_sim_matrix の atom 列順)
    seed_id_to_atom = {}
    for sd in range(24):
        sim = pd.read_parquet(V106_MAIN / f'cid_atom_sim_matrix_seed{sd}.parquet',
                               columns=['cid'])
        # 列名を直接取得
        sim_full = pd.read_parquet(V106_MAIN / f'cid_atom_sim_matrix_seed{sd}.parquet')
        atom_cols = [c for c in sim_full.columns if c not in ('seed', 'cid')]
        seed_id_to_atom[sd] = {i: a for i, a in enumerate(atom_cols)}

    # ---- per-event 7 系列 rank-based 絞り ----
    print('[3] per-event × 7 系列 rank-based score 計算')
    out_rows = []
    grouped = assoc.groupby(['seed', 'event_id', 'input_atom'])
    n_events = len(grouped)
    cnt = 0
    for (sd, eid, input_atom), grp in grouped:
        cnt += 1
        if cnt % 5000 == 0:
            print(f'  processed {cnt:,}/{n_events:,} events, elapsed {time.time()-t0:.1f}s')

        # candidate atom 集合 (4 source レイヤー union)
        candidates = grp['candidate_atom'].unique().tolist()
        if not candidates:
            continue

        # rank_source: source レイヤー出現回数 (高頻度 = 低 rank)
        cand_source_count = grp.groupby('candidate_atom').size()
        # rank: 高頻度 = 1 位 (ascending=False)
        rank_source = cand_source_count.rank(method='average', ascending=False).to_dict()

        # rank_trajectory: per-atom stability (該当 seed の lookup)
        stab_lookup = seed_stab[sd]
        atom_to_id = {a: i for i, a in seed_id_to_atom[sd].items()}
        cand_stab = {}
        for cand in candidates:
            if cand in atom_to_id:
                cid_int = atom_to_id[cand]
                cand_stab[cand] = stab_lookup.get(cid_int, np.nan)
            else:
                cand_stab[cand] = np.nan
        # NaN は中央値 rank を仮代入 (rank 計算のため)
        stab_series = pd.Series(cand_stab)
        # 高 stability = 1 位
        rank_trajectory = stab_series.fillna(stab_series.median() if not stab_series.dropna().empty else 0).rank(
            method='average', ascending=False).to_dict()

        # rank_density (7 系列): input atom と candidate atom の cosine_sim
        # 7 系列分 density 計算
        if input_atom not in ac_raw.index:
            continue  # 入力 atom が centroids に無い場合 skip (今回は 100% カバレッジ確認済)
        v_raw = ac_raw.loc[input_atom].values.reshape(1, -1)
        v_norm = ac_norm.loc[input_atom].values.reshape(1, -1)

        cand_in_ac = [c for c in candidates if c in ac_raw.index]
        if not cand_in_ac:
            continue
        cand_raw = ac_raw.loc[cand_in_ac].values
        cand_norm = ac_norm.loc[cand_in_ac].values
        sim_raw = cosine_similarity(v_raw, cand_raw)[0]  # raw embedding cos sim
        sim_norm = cosine_similarity(v_norm, cand_norm)[0]  # norm embedding cos sim

        # qweighted: cosine_sim × focus_rate_mean
        focus = np.array([aq.loc[c, 'focus_rate_mean'] if c in aq.index else 0.5
                           for c in cand_in_ac])
        # const_adjusted: cosine_sim × couple_bonus (1.1 if endpoint else 1.0)
        couple_bonus = np.array([1.1 if c in couple_endpoints else 1.0 for c in cand_in_ac])

        density_per_series = {
            's1_raw_density_raw': sim_raw,
            's2_raw_density_norm': sim_norm,
            's3_qweighted_density_raw': sim_raw * focus,
            's4_qweighted_density_norm': sim_norm * focus,
            's5_const_adjusted_density_raw': sim_raw * couple_bonus,
            's6_const_adjusted_density_norm': sim_norm * couple_bonus,
            's7_48d_raw_k5': sim_raw,
        }

        for series_id, dens_vals in density_per_series.items():
            # rank_density for this series
            rank_dens = pd.Series(dens_vals, index=cand_in_ac).rank(
                method='average', ascending=False).to_dict()

            # 7 系列 s7 (48D k=5) は top-5 のみ採用
            if series_id == 's7_48d_raw_k5':
                top5_idx = np.argsort(-dens_vals)[:5]
                cand_subset = [cand_in_ac[i] for i in top5_idx]
            else:
                cand_subset = cand_in_ac

            # score 計算
            score_rows = []
            for c in cand_subset:
                r_s = rank_source.get(c, len(candidates) + 1)  # 不在は最下位
                r_t = rank_trajectory.get(c, len(candidates) + 1)
                r_d = rank_dens.get(c, len(cand_in_ac) + 1)
                w_s = 1.0 / np.log(r_s + 2)
                w_t = 1.0 / np.log(r_t + 2)
                w_d = 1.0 / np.log(r_d + 2)
                score = w_s * w_t * w_d
                score_rows.append((c, score, r_s, r_t, r_d))

            # 正規化
            scores_arr = np.array([s[1] for s in score_rows])
            total = scores_arr.sum()
            if total <= 0:
                continue
            probs = scores_arr / total

            for (c, score, r_s, r_t, r_d), p in zip(score_rows, probs):
                out_rows.append({
                    'seed': sd,
                    'event_id': eid,
                    'input_atom': input_atom,
                    'series_id': series_id,
                    'candidate_atom': c,
                    'probability': float(p),
                    'rank_source': float(r_s),
                    'rank_trajectory': float(r_t),
                    'rank_density': float(r_d),
                    'b_high': bool(c in b_high_atoms),
                })

    df = pd.DataFrame(out_rows)
    out = V1105A_MAIN / 'trial_step3_distributions.parquet'
    df.to_parquet(out, index=False)
    print(f'\n[4] wrote {out.name} ({len(df):,} rows, elapsed {time.time()-t0:.1f}s)')

    # --- サマリ ---
    print('\n--- series_id 別 events × 平均候補数 ---')
    s = df.groupby('series_id').agg(
        n_rows=('candidate_atom', 'count'),
        n_events=('event_id', 'nunique'),
        cand_mean=('candidate_atom', lambda x: len(x) / x.nunique() if x.nunique() else 0),
    ).round(2)
    print(s.to_string())

    print('\n--- 各系列の max_prob 分布 ---')
    mp = df.groupby(['seed', 'event_id', 'series_id'])['probability'].max().reset_index()
    print(mp.groupby('series_id')['probability'].agg(['mean', 'median', 'max', 'min']).round(4).to_string())

    print('\n--- entropy 平均 ---')
    def calc_ent(probs):
        p = np.array(probs)
        p = p[p > 0]
        return float(-np.sum(p * np.log(p))) if len(p) > 0 else 0.0
    ent = df.groupby(['seed', 'event_id', 'series_id'])['probability'].apply(calc_ent).reset_index()
    print(ent.groupby('series_id')['probability'].agg(['mean', 'median']).round(4).to_string())

    print('\n--- B 高 atom 上位到達率 (top5 中の b_high 比率) ---')
    # top5 を計算
    df_sorted = df.sort_values(['seed', 'event_id', 'series_id', 'probability'],
                                ascending=[True, True, True, False])
    df_sorted['rank_in_event'] = df_sorted.groupby(['seed','event_id','series_id']).cumcount() + 1
    top5 = df_sorted[df_sorted['rank_in_event'] <= 5]
    b_top5_ratio = top5.groupby('series_id')['b_high'].mean()
    print(b_top5_ratio.round(4).to_string())


if __name__ == '__main__':
    main()
