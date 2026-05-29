#!/usr/bin/env python3
"""v1108a Step F — 観察 4: Gemini 予測 1/2 検証

予測 1: 社会的 cluster (EXS/REL/LOG 等) は孤立 cluster (PER/BOD/PRP 等) より
        時間結合減衰 τ が長い
予測 2: familiarity 減少率最大の turn で特定 Atom ペアの ΔC_ij が 3σ 以上尖鋭化
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1107A_MAIN = REPO / 'unified/v1107a/outputs/main'
V1108A_MAIN = REPO / 'unified/v1108a/outputs/main'

# v1107a cluster 定義
CLUSTER_SOCIAL = {'EXS', 'FND'}
CLUSTER_ISOLATED = {'BOD', 'PER', 'PRP'}


def main():
    print('=== v1108a Step F — 観察 4: Gemini 予測 1/2 検証 ===\n')
    t0 = time.time()

    hist = pd.read_parquet(V1108A_MAIN / 'self_dialogue_with_atom_probs.parquet')
    hist['top1_cat'] = hist['atom_top1'].str.split('.').str[0]

    # (1) 予測 1: 社会的 cluster vs 孤立 cluster の time-binding 持続性
    print('[1] 予測 1: 社会的 vs 孤立 cluster の time-binding')
    # 各 event の start atom category で分類
    events = hist[hist['turn'] == 0][['seed', 'start_cid', 'top1_cat']].copy()
    events['start_cluster'] = events['top1_cat'].apply(
        lambda c: 'social' if c in CLUSTER_SOCIAL else ('isolated' if c in CLUSTER_ISOLATED else 'other'))
    print(f'  social start events: {(events["start_cluster"]=="social").sum()}')
    print(f'  isolated start events: {(events["start_cluster"]=="isolated").sum()}')
    print(f'  other start events: {(events["start_cluster"]=="other").sum()}')

    # 同 atom が turn t と t+k で再出現するかを見て持続性測定
    # 単純化: 各 event で top1_atom が同じ atom である turn の連続長
    def measure_persistence(grp_sorted):
        atoms = grp_sorted['atom_top1'].tolist()
        max_run = 1
        cur_run = 1
        for i in range(1, len(atoms)):
            if atoms[i] == atoms[i-1] and atoms[i] is not None:
                cur_run += 1
                max_run = max(max_run, cur_run)
            else:
                cur_run = 1
        return max_run, len(atoms)

    persistence_rows = []
    event_cluster = events.set_index(['seed', 'start_cid'])['start_cluster'].to_dict()
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn')
        max_run, n_turn = measure_persistence(grp_sorted)
        cl = event_cluster.get((sd, sc), 'other')
        persistence_rows.append({
            'seed': sd, 'start_cid': sc,
            'start_cluster': cl,
            'max_persistence': max_run,
            'n_turn': n_turn,
        })
    p_df = pd.DataFrame(persistence_rows)
    print('\n  cluster 別最大持続 turn (top1_atom 連続):')
    for cl in ['social', 'isolated', 'other']:
        sub = p_df[p_df['start_cluster'] == cl]
        if len(sub) > 0:
            print(f'    {cl}: n={len(sub)}, max_persistence mean={sub["max_persistence"].mean():.2f}, '
                  f'median={sub["max_persistence"].median():.1f}')

    soc_pers = p_df[p_df['start_cluster'] == 'social']['max_persistence']
    iso_pers = p_df[p_df['start_cluster'] == 'isolated']['max_persistence']
    ratio = soc_pers.mean() / iso_pers.mean() if iso_pers.mean() > 0 else 0
    prediction_1_pass = ratio > 2.0
    print(f'\n  social / isolated 持続性比: {ratio:.2f} (predict: > 2.0)')
    print(f'  予測 1 通過: {prediction_1_pass}')

    # (2) 予測 2: familiarity 減少率最大 turn での Atom ペア尖鋭化
    print('\n[2] 予測 2: familiarity 減少率最大 turn での尖鋭化')
    delta_C = pd.read_parquet(V1108A_MAIN / 'observation_1_delta_C.parquet')
    rho_FH_pairs = pd.read_parquet(V1108A_MAIN / 'observation_2_rho_FH.parquet')

    # 各 event で familiarity 減少率最大の turn を抽出
    rho_FH_pairs['decrease_rate'] = -rho_FH_pairs['delta_F'] / (rho_FH_pairs['F_t'] + 1e-6)
    max_decrease_per_event = rho_FH_pairs.loc[
        rho_FH_pairs.groupby(['seed', 'start_cid'])['decrease_rate'].idxmax()]
    print(f'  特異 turn 抽出: {len(max_decrease_per_event):,} events')
    print(f'  特異 turn 平均 decrease_rate: '
          f'{max_decrease_per_event["decrease_rate"].mean():.4f}')

    # 特異 turn での top1 → top1 ペア
    special_turn_atoms = hist.merge(
        max_decrease_per_event[['seed', 'start_cid', 'turn']],
        on=['seed', 'start_cid', 'turn'])
    print(f'  特異 turn の top1 atom 出現: {special_turn_atoms["atom_top1"].nunique()} unique atoms')

    # 特異 turn での atom ペア結合と全体 ΔC_ij の比較
    # 簡易: top1 atom × その次 turn top1 atom のペアの ΔC_ij が分布上位にあるか
    special_pairs = []
    for (sd, sc, t), _ in special_turn_atoms.groupby(['seed', 'start_cid', 'turn']):
        row_t = hist[(hist['seed']==sd) & (hist['start_cid']==sc) & (hist['turn']==t)]
        row_tp = hist[(hist['seed']==sd) & (hist['start_cid']==sc) & (hist['turn']==t+1)]
        if len(row_t) == 0 or len(row_tp) == 0:
            continue
        ai = row_t.iloc[0]['atom_top1']
        aj = row_tp.iloc[0]['atom_top1']
        if ai is None or aj is None:
            continue
        special_pairs.append((ai, aj))

    if special_pairs:
        # delta_C lookup
        delta_lookup = {(r['atom_i'], r['atom_j']): r['delta_C']
                         for _, r in delta_C.iterrows()}
        special_deltas = [delta_lookup.get(p, 0.0) for p in special_pairs]
        special_arr = np.array(special_deltas)
        # 全体分布
        all_deltas = delta_C['delta_C'].values
        # 3σ 超え判定
        threshold_3sigma = all_deltas.mean() + 3 * all_deltas.std()
        n_above_3sigma = (special_arr > threshold_3sigma).sum()
        prediction_2_pass = n_above_3sigma / len(special_arr) > 0.1  # 10% 以上が 3σ
        print(f'  特異 turn ペア数: {len(special_pairs):,}')
        print(f'  特異 turn ペアの delta_C mean: {special_arr.mean():.6f}, '
              f'std: {special_arr.std():.6f}')
        print(f'  全体 delta_C mean: {all_deltas.mean():.6f}, std: {all_deltas.std():.6f}')
        print(f'  3σ 超え (>{threshold_3sigma:.6f}): {n_above_3sigma}/{len(special_arr)} '
              f'({n_above_3sigma/len(special_arr)*100:.1f}%)')
        print(f'  予測 2 通過: {prediction_2_pass}')
    else:
        prediction_2_pass = False
        special_arr = np.array([])

    # 構造ラベル
    if prediction_1_pass:
        label_1 = 'social_temporal_long_tau'
    else:
        label_1 = 'social_temporal_no_difference'
    if prediction_2_pass:
        label_2 = 'plasticity_singularity_focused'
    else:
        label_2 = 'plasticity_singularity_diffuse'

    sum_df = pd.DataFrame([{
        'soc_persistence_mean': float(soc_pers.mean()) if len(soc_pers) > 0 else 0,
        'iso_persistence_mean': float(iso_pers.mean()) if len(iso_pers) > 0 else 0,
        'soc_iso_ratio': float(ratio),
        'prediction_1_pass': bool(prediction_1_pass),
        'prediction_1_label': label_1,
        'n_special_pairs': len(special_pairs),
        'special_delta_mean': float(special_arr.mean()) if len(special_arr) > 0 else 0,
        'prediction_2_pass': bool(prediction_2_pass),
        'prediction_2_label': label_2,
        'elapsed_sec': round(time.time() - t0, 2),
    }])
    sum_df.to_parquet(V1108A_MAIN / 'observation_4_summary.parquet', index=False)

    print(f'\n--- 構造ラベル判定 ---')
    print(f'  予測 1: {label_1}')
    print(f'  予測 2: {label_2}')

    print(f'\n=== Step F 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
