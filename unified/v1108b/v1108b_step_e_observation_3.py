#!/usr/bin/env python3
"""v1108b Step E — 観察 3: 出力候補性質変化 (entropy / max_prob / top-k 分散)

cluster_0 寄り入力 (strength_signed > 0) vs cluster_1 寄り (strength_signed < 0) で
出力 word/atom 候補性質を比較。自然文判定は回避。

入力:
- unified/v1108b/outputs/main/observation_2_atom_distances.parquet
- unified/v1106a/outputs/main/observation_Y_word_distributions.parquet
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'
V1108B_MAIN = REPO / 'unified/v1108b/outputs/main'


def main():
    print('=== v1108b Step E — 観察 3: 出力候補性質変化 ===\n')
    t0 = time.time()

    # atom distance
    atom_dist = pd.read_parquet(V1108B_MAIN / 'observation_2_atom_distances.parquet')

    # observation_Y word 分布 (v1106a) を読み込み、各 event の入力 atom と紐付ける
    dist = pd.read_parquet(V1106A_MAIN / 'observation_Y_word_distributions.parquet')
    s7 = dist[dist['series_id'] == 's7_48d_raw_k5']
    s7_evt = s7.groupby(['seed', 'event_id', 'input_atom']).agg(
        n_words=('candidate_word', 'count'),
        max_prob=('probability', 'max'),
        sum_prob=('probability', 'sum'),
    ).reset_index()

    # 各 event について output entropy 計算
    print('[1] event 別 output entropy / max_prob / top-k 分散計算')
    entropy_rows = []
    for (sd, eid, ia), grp in s7.groupby(['seed', 'event_id', 'input_atom']):
        probs = grp['probability'].values
        if len(probs) == 0 or probs.sum() == 0:
            continue
        p = probs / probs.sum()
        eps = 1e-12
        ent = float(-np.sum(p * np.log(p + eps)))
        max_p = float(p.max())
        # top-10 集中度
        top10_sum = float(np.sort(p)[-10:].sum()) if len(p) >= 10 else float(p.sum())
        entropy_rows.append({
            'seed': sd, 'event_id': eid, 'input_atom': ia,
            'category': ia.split('.')[0],
            'output_entropy': ent,
            'output_max_prob': max_p,
            'top10_concentration': top10_sum,
            'n_unique_words': len(p),
        })
    out_df = pd.DataFrame(entropy_rows)
    print(f'  events: {len(out_df):,}')

    # input atom → strength_signed
    strength_lookup = atom_dist.set_index('input_atom')['strength_signed'].to_dict()
    out_df['strength_signed'] = out_df['input_atom'].map(strength_lookup)
    valid = out_df.dropna(subset=['strength_signed'])
    print(f'  with strength: {len(valid):,}')

    # cluster 寄りで分類
    valid_pos = valid[valid['strength_signed'] > 0]  # cluster_0 寄り
    valid_neg = valid[valid['strength_signed'] < 0]  # cluster_1 寄り
    print(f'  cluster_0 寄り events: {len(valid_pos):,}')
    print(f'  cluster_1 寄り events: {len(valid_neg):,}')

    # 出力性質比較
    print('\n[2] 出力性質比較')
    comp_rows = []
    for col, label in [('output_entropy', 'entropy'),
                         ('output_max_prob', 'max_prob'),
                         ('top10_concentration', 'top10_conc'),
                         ('n_unique_words', 'n_words')]:
        m0 = float(valid_pos[col].mean()) if len(valid_pos) > 0 else 0
        m1 = float(valid_neg[col].mean()) if len(valid_neg) > 0 else 0
        comp_rows.append({
            'metric': label,
            'cluster_0_mean': m0,
            'cluster_1_mean': m1,
            'diff': m0 - m1,
            'pct_diff': (m0 - m1) / m1 * 100 if m1 != 0 else 0,
        })
        print(f'  {label}: cluster_0={m0:.4f}, cluster_1={m1:.4f}, diff={m0-m1:+.4f}')

    comp_df = pd.DataFrame(comp_rows)
    out_df.to_parquet(V1108B_MAIN / 'observation_3_output_properties.parquet', index=False)
    comp_df.to_parquet(V1108B_MAIN / 'observation_3_cluster_comparison.parquet', index=False)

    # category 別出力性質
    print('\n[3] category 別出力性質')
    cat_summary = valid.groupby('category').agg(
        n_events=('event_id', 'count'),
        entropy_mean=('output_entropy', 'mean'),
        max_prob_mean=('output_max_prob', 'mean'),
        top10_conc_mean=('top10_concentration', 'mean'),
        n_words_mean=('n_unique_words', 'mean'),
        strength_mean=('strength_signed', 'mean'),
    ).round(4).reset_index().sort_values('strength_mean', ascending=False)
    cat_summary.to_parquet(V1108B_MAIN / 'observation_3_category_summary.parquet', index=False)
    print(cat_summary.to_string(index=False))

    # 構造ラベル判定: cluster_0 と cluster_1 で出力性質に差があるか
    # entropy diff > 0.1 or max_prob diff > 0.005 で差別化と判定
    significant = (abs(comp_rows[0]['diff']) > 0.05
                    or abs(comp_rows[1]['diff']) > 0.001)
    label = 'output_properties_differ' if significant else 'output_properties_similar'

    sum_df = pd.DataFrame([{
        'n_events_total': len(valid),
        'cluster_0_count': len(valid_pos),
        'cluster_1_count': len(valid_neg),
        'entropy_diff': float(comp_rows[0]['diff']),
        'max_prob_diff': float(comp_rows[1]['diff']),
        'top10_conc_diff': float(comp_rows[2]['diff']),
        'output_differs': bool(significant),
        'structural_label': label,
        'elapsed_sec': round(time.time() - t0, 2),
    }])
    sum_df.to_parquet(V1108B_MAIN / 'observation_3_summary.parquet', index=False)

    print(f'\n--- 構造ラベル判定 ---')
    print(f'  entropy diff: {comp_rows[0]["diff"]:.4f}')
    print(f'  max_prob diff: {comp_rows[1]["diff"]:.4f}')
    print(f'  構造ラベル: {label}')

    print(f'\n=== Step E 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
