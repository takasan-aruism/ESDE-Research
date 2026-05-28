#!/usr/bin/env python3
"""v1107b Step F — 観察 4: v1108 部品化検討 (基準 C)

3 要件:
1. category → scale 偏り表が出力できる
2. scale → 軸 mapping (どの軸が Micro/Meso/Macro か) が出力できる
3. 新規入力 atom (category 既知) → 想定 scale 寄与パターン予測

入力:
- unified/v1107b/outputs/main/observation_2_category_scale_bias.parquet
- unified/v1107b/outputs/main/observation_1_axis_clusters.parquet

出力:
- unified/v1107b/outputs/main/observation_4_category_scale_map.parquet
- unified/v1107b/outputs/main/observation_4_scale_to_axes.parquet
- unified/v1107b/outputs/main/observation_4_summary.parquet
"""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V1107B_MAIN = REPO / 'unified/v1107b/outputs/main'


def main():
    print('=== v1107b Step F — 観察 4: v1108 部品化検討 ===\n')
    t0 = time.time()

    bias = pd.read_parquet(V1107B_MAIN / 'observation_2_category_scale_bias.parquet')

    # 要件 1: category → scale 偏り表
    print('[要件 1] category → scale 偏り表')
    map_rows = []
    for _, r in bias.iterrows():
        total = (r['gemini_micro_sum'] + r['gemini_meso_sum']
                  + r['gemini_macro_sum'] + r['gemini_other_sum'])
        if total > 0:
            micro_pct = r['gemini_micro_sum'] / total
            meso_pct = r['gemini_meso_sum'] / total
            macro_pct = r['gemini_macro_sum'] / total
        else:
            micro_pct = meso_pct = macro_pct = 0
        # dominant scale
        sums = {'Micro': r['gemini_micro_sum'], 'Meso': r['gemini_meso_sum'],
                 'Macro': r['gemini_macro_sum']}
        # Other 除く 3 scale で
        dominant = max(sums.items(), key=lambda x: x[1])[0]
        map_rows.append({
            'category': r['category'], 'n_events': int(r['n_events']),
            'dominant_scale': dominant,
            'micro_pct': float(micro_pct),
            'meso_pct': float(meso_pct),
            'macro_pct': float(macro_pct),
            'micro_sum': float(r['gemini_micro_sum']),
            'meso_sum': float(r['gemini_meso_sum']),
            'macro_sum': float(r['gemini_macro_sum']),
        })
    map_df = pd.DataFrame(map_rows)
    out1 = V1107B_MAIN / 'observation_4_category_scale_map.parquet'
    map_df.to_parquet(out1, index=False)
    print(map_df.round(4).to_string(index=False))
    req1_ok = len(map_df) >= 2
    print(f'  要件 1 OK: {req1_ok}')

    # 要件 2: scale → 軸 mapping (Gemini 仮説 + data 駆動 cluster)
    print('\n[要件 2] scale → 軸 mapping')
    am = json.load(open(V106_MAIN / 'axes_metadata.json'))
    axes = []
    for ax in am['axes_order']:
        for lvl in ax['level_names']:
            axes.append(f'{ax["name"]}.{lvl}')

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

    # data 駆動 (agglomerative k=3)
    clusters = pd.read_parquet(V1107B_MAIN / 'observation_1_axis_clusters.parquet')
    data_cluster = dict(zip(
        clusters[(clusters['method']=='agglomerative') & (clusters['k']==3)]['axis'],
        clusters[(clusters['method']=='agglomerative') & (clusters['k']==3)]['cluster']
    ))

    s2a_rows = []
    for ax in axes:
        if ax in gemini_micro: g = 'Micro'
        elif ax in gemini_meso: g = 'Meso'
        elif ax in gemini_macro: g = 'Macro'
        else: g = 'Other'
        dc = int(data_cluster.get(ax, -1))
        s2a_rows.append({
            'axis': ax, 'gemini_scale': g, 'data_cluster': dc,
        })
    s2a_df = pd.DataFrame(s2a_rows)
    out2 = V1107B_MAIN / 'observation_4_scale_to_axes.parquet'
    s2a_df.to_parquet(out2, index=False)
    print(f'  Gemini scale 軸数: Micro {(s2a_df["gemini_scale"]=="Micro").sum()}, '
          f'Meso {(s2a_df["gemini_scale"]=="Meso").sum()}, '
          f'Macro {(s2a_df["gemini_scale"]=="Macro").sum()}, '
          f'Other {(s2a_df["gemini_scale"]=="Other").sum()}')
    print(f'  data 駆動 cluster 軸数: {dict(s2a_df["data_cluster"].value_counts())}')
    req2_ok = len(s2a_df) == 48
    print(f'  要件 2 OK: {req2_ok}')

    # 要件 3: 新規 input_atom (category 既知) → 想定 scale パターン予測
    print('\n[要件 3] 新規 input_atom 予測枠組み')
    pred_rows = []
    for cat in sorted(map_df['category'].unique()):
        cat_row = map_df[map_df['category'] == cat].iloc[0]
        pred_rows.append({
            'input_category': cat,
            'predicted_dominant_scale': cat_row['dominant_scale'],
            'predicted_micro_pct': float(cat_row['micro_pct']),
            'predicted_meso_pct': float(cat_row['meso_pct']),
            'predicted_macro_pct': float(cat_row['macro_pct']),
        })
    pred_df = pd.DataFrame(pred_rows)
    print(pred_df.round(4).to_string(index=False))
    req3_ok = len(pred_df) > 0
    print(f'  要件 3 OK: {req3_ok}')

    # 統合判定
    v1108_ready = req1_ok and req2_ok and req3_ok

    print(f'\n[基準 C] v1108 部品化判定: {"v1108_ready" if v1108_ready else "v1108_not_ready"}')

    sum_df = pd.DataFrame([{
        'requirement_1_category_scale_map': req1_ok,
        'requirement_2_scale_to_axes': req2_ok,
        'requirement_3_prediction_framework': req3_ok,
        'v1108_ready': v1108_ready,
        'n_covered_categories': len(pred_df),
        'n_axes_mapped': len(s2a_df),
    }])
    out3 = V1107B_MAIN / 'observation_4_summary.parquet'
    sum_df.to_parquet(out3, index=False)
    print(f'wrote observation_4_*.parquet')

    print(f'\n=== Step F 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
