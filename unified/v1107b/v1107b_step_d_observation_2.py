#!/usr/bin/env python3
"""v1107b Step D — 観察 2: axis 寄与分解 + category × scale 偏り

verification_a 3,300 events で、各 event の cid_word_cos_sim を 48 軸別に分解し、
input_atom category 別 × scale (Gemini 仮説 + data 駆動 cluster) の寄与偏りを集計。

入力:
- unified/v1106b/outputs/main/observation_3_high_low_events.parquet (event_class + cos_sim)
- unified/v1106a/outputs/main/verification_a_cid_word_alignment.parquet
- unified/v1106a/outputs/main/observation_Y_word_distributions.parquet
- language/lexicon/data/mapper_output/*_a1.jsonl
- unified/v1103/outputs/main/atom_centroids_48d_raw.parquet
- developmental/v106/outputs/main/cid_structure_profile_seed{N}.csv
- unified/v1107b/outputs/main/observation_1_axis_clusters.parquet (data 駆動 cluster)

出力:
- unified/v1107b/outputs/main/observation_2_axis_contribution.parquet (event × 軸寄与)
- unified/v1107b/outputs/main/observation_2_category_scale_bias.parquet (category × scale)
- unified/v1107b/outputs/main/observation_2_summary.parquet
"""
from __future__ import annotations
import json, time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V1103_MAIN = REPO / 'unified/v1103/outputs/main'
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'
V1106B_MAIN = REPO / 'unified/v1106b/outputs/main'
V1107B_MAIN = REPO / 'unified/v1107b/outputs/main'
MAPPER_DIR = REPO / 'language/lexicon/data/mapper_output'


def get_axes():
    am = json.load(open(V106_MAIN / 'axes_metadata.json'))
    return [f'{ax["name"]}.{lvl}' for ax in am['axes_order'] for lvl in ax['level_names']]


def main():
    print('=== v1107b Step D — 観察 2: axis 寄与分解 + category × scale ===\n')
    t0 = time.time()

    axes = get_axes()

    # (1) Gemini 仮説スケール定義
    gemini_micro = {'temporal.emergence', 'temporal.indication', 'scale.individual',
                     'interconnection.independent', 'ontological.material'}
    gemini_meso = {'interconnection.catalytic', 'interconnection.chained',
                    'interconnection.synchronous', 'interconnection.resonant',
                    'resonance.structural', 'resonance.essential',
                    'epistemological.experience', 'ontological.relational'}
    gemini_macro = {'scale.ecosystem', 'scale.stellar', 'scale.cosmic',
                     'resonance.existential', 'ontological.semantic',
                     'experience.comprehension', 'lawfulness.necessary',
                     'value_generation.sacred'}

    def label_axis(ax):
        if ax in gemini_micro: return 'Micro'
        if ax in gemini_meso: return 'Meso'
        if ax in gemini_macro: return 'Macro'
        return 'Other'

    # (2) data 駆動 cluster 取得 (観察 1 で計算済、agglomerative k=3 を採用)
    clusters_df = pd.read_parquet(V1107B_MAIN / 'observation_1_axis_clusters.parquet')
    agg_k3 = clusters_df[(clusters_df['method']=='agglomerative') & (clusters_df['k']==3)]
    data_cluster_map = dict(zip(agg_k3['axis'], agg_k3['cluster']))
    print(f'  data 駆動 cluster (agglomerative k=3): {len(set(data_cluster_map.values()))} clusters')

    # (3) verification_a の event ごとに cid 48d × word centroid 48d 軸寄与計算
    print('\n[2] event ごとの軸寄与計算')
    va = pd.read_parquet(V1106B_MAIN / 'observation_3_high_low_events.parquet')
    va['category'] = va['input_atom'].str.split('.').str[0]
    print(f'  events: {len(va):,}')

    # CID 48d vec を全 seed 読み込み
    cid_vec = {}
    for sd in range(24):
        fp = V106_MAIN / f'cid_structure_profile_seed{sd}.csv'
        if not fp.exists():
            continue
        df = pd.read_csv(fp, usecols=['seed', 'cid'] + [f'dim_{i}' for i in range(48)])
        for _, r in df.iterrows():
            cid_vec[(int(r['seed']), int(r['cid']))] = np.array(
                [r[f'dim_{i}'] for i in range(48)], dtype=np.float64)
    print(f'  CID 48d vec: {len(cid_vec):,}')

    # word 48d vec (atom 別 word の raw_scores)
    word_to_atom_vec = defaultdict(dict)
    for fp in sorted(MAPPER_DIR.glob('*_a1.jsonl')):
        atom = fp.stem.replace('_a1', '').replace('_', '.', 1)
        with open(fp) as f:
            for line in f:
                r = json.loads(line)
                if r.get('status') != 'OK':
                    continue
                rs = r.get('raw_scores')
                if not isinstance(rs, dict):
                    continue
                vec = np.array([rs.get(ax, 0.0) for ax in axes], dtype=np.float64)
                word_to_atom_vec[r['word']][atom] = vec
    print(f'  unique words: {len(word_to_atom_vec):,}')

    # event ごとに word 加重 48d centroid + cid_vec × 軸寄与
    print('\n[3] event ごとの軸寄与計算 (cid 48d × word weighted 48d)')
    dist = pd.read_parquet(V1106A_MAIN / 'observation_Y_word_distributions.parquet')
    s7 = dist[dist['series_id'] == 's7_48d_raw_k5']

    # word_centroid を event 単位で事前計算
    word_centroids = {}
    for (sd, eid), grp in s7.groupby(['seed', 'event_id']):
        wc = np.zeros(48)
        tp = 0.0
        for _, row in grp.iterrows():
            w = row['candidate_word']
            if w not in word_to_atom_vec:
                continue
            vecs = list(word_to_atom_vec[w].values())
            wv = np.mean(vecs, axis=0)
            wc += row['probability'] * wv
            tp += row['probability']
        if tp > 0:
            wc /= tp
        if np.linalg.norm(wc) > 0:
            word_centroids[(sd, eid)] = wc

    # 各 event で axis 別寄与 = (cid_vec[i] * wc[i]) / (||cid|| * ||wc||)
    print('\n[4] axis 寄与計算 (per event)')
    contrib_rows = []
    cnt = 0
    n_grp = len(va)
    for _, row in va.iterrows():
        cnt += 1
        if cnt % 1000 == 0:
            print(f'  processed {cnt}/{n_grp}')
        sd = int(row['seed'])
        eid = row['event_id']
        cid = int(row['cid'])
        key = (sd, eid)
        if key not in word_centroids or (sd, cid) not in cid_vec:
            continue
        wc = word_centroids[key]
        cv = cid_vec[(sd, cid)]
        cn = np.linalg.norm(cv); wn = np.linalg.norm(wc)
        if cn == 0 or wn == 0:
            continue
        # 軸別寄与 (加法分解)
        contribs = (cv * wc) / (cn * wn)
        contrib_rows.append({
            'seed': sd, 'event_id': eid, 'input_atom': row['input_atom'],
            'category': row['category'], 'event_class': row['event_class'],
            **{f'axis_{i}': float(contribs[i]) for i in range(48)},
        })

    contrib_df = pd.DataFrame(contrib_rows)
    out1 = V1107B_MAIN / 'observation_2_axis_contribution.parquet'
    contrib_df.to_parquet(out1, index=False)
    print(f'  wrote {out1.name} ({len(contrib_df)} rows)')

    # (5) category × scale 偏り集計 (Gemini 仮説 + data 駆動 cluster)
    print('\n[5] category × scale 偏り集計')
    axis_to_gemini = [label_axis(a) for a in axes]
    axis_to_data_cluster = [data_cluster_map.get(a, -1) for a in axes]

    bias_rows = []
    for cat in sorted(contrib_df['category'].unique()):
        sub = contrib_df[contrib_df['category'] == cat]
        # 各軸の平均寄与
        axis_contribs = np.array([sub[f'axis_{i}'].mean() for i in range(48)])
        # Gemini scale 合計
        gemini_sum = {'Micro': 0.0, 'Meso': 0.0, 'Macro': 0.0, 'Other': 0.0}
        for i, lbl in enumerate(axis_to_gemini):
            gemini_sum[lbl] += axis_contribs[i]
        # Data cluster 合計
        data_sum = defaultdict(float)
        for i, cl in enumerate(axis_to_data_cluster):
            data_sum[f'cluster_{cl}'] += axis_contribs[i]
        row = {
            'category': cat, 'n_events': len(sub),
            'gemini_micro_sum': gemini_sum['Micro'],
            'gemini_meso_sum': gemini_sum['Meso'],
            'gemini_macro_sum': gemini_sum['Macro'],
            'gemini_other_sum': gemini_sum['Other'],
        }
        for k, v in data_sum.items():
            row[f'data_{k}_sum'] = v
        bias_rows.append(row)

    bias_df = pd.DataFrame(bias_rows)
    out2 = V1107B_MAIN / 'observation_2_category_scale_bias.parquet'
    bias_df.to_parquet(out2, index=False)
    print(f'  wrote {out2.name}')

    print('\n--- category × Gemini scale 寄与 ---')
    print(bias_df[['category', 'n_events',
                    'gemini_micro_sum', 'gemini_meso_sum',
                    'gemini_macro_sum', 'gemini_other_sum']].round(4).to_string(index=False))

    print('\n--- category × data 駆動 cluster 寄与 ---')
    data_cols = [c for c in bias_df.columns if c.startswith('data_')]
    print(bias_df[['category'] + data_cols].round(4).to_string(index=False))

    # (6) scale 偏りの差別化指標
    print('\n[6] scale 偏り差別化判定')
    # 各 scale の category 間 std
    summary = {}
    for col in ['gemini_micro_sum', 'gemini_meso_sum', 'gemini_macro_sum']:
        std = float(bias_df[col].std())
        mean = float(bias_df[col].mean())
        summary[col + '_std'] = std
        summary[col + '_cv'] = std / mean if abs(mean) > 1e-6 else 0.0
        print(f'  {col}: mean={mean:.4f}, std={std:.4f}, CV={summary[col+"_cv"]:.4f}')

    # 判定: 1 つの scale で category 間に有意な差
    max_cv = max(abs(summary[k]) for k in summary if k.endswith('_cv'))
    differentiated = max_cv > 0.2  # threshold
    print(f'\n  max CV across scales: {max_cv:.4f}')
    print(f'  構造ラベル: {"scale_usage_differentiated" if differentiated else "scale_usage_uniform"}')

    sum_df = pd.DataFrame([{
        'scale_max_cv': max_cv,
        'differentiated': differentiated,
        **summary,
    }])
    out3 = V1107B_MAIN / 'observation_2_summary.parquet'
    sum_df.to_parquet(out3, index=False)
    print(f'\nwrote {out3.name}')

    print(f'\n=== Step D 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
