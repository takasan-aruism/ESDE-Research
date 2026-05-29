#!/usr/bin/env python3
"""v1108b Step F — 観察 4: 48 軸 Macro/Micro 寄与整合 (v1107b 継承、補助根拠扱い)

v1107b で 5 cat の Macro/Micro 寄与差別化を確認。
v1108b で 24 cat 全体の Macro/Micro 寄与傾向を確認、cluster_0/1 と整合するか。
"""
from __future__ import annotations
import time, json
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V1107B_MAIN = REPO / 'unified/v1107b/outputs/main'
V1108B_MAIN = REPO / 'unified/v1108b/outputs/main'

# v1107b の Macro/Meso/Micro 仮説マッピング (Code A 案、作業仮説扱い)
GEMINI_MICRO = {'temporal.emergence', 'temporal.indication', 'scale.individual',
                  'interconnection.independent', 'ontological.material'}
GEMINI_MESO = {'interconnection.catalytic', 'interconnection.chained',
                 'interconnection.synchronous', 'interconnection.resonant',
                 'resonance.structural', 'resonance.essential',
                 'epistemological.experience', 'ontological.relational'}
GEMINI_MACRO = {'scale.ecosystem', 'scale.stellar', 'scale.cosmic',
                  'resonance.existential', 'ontological.semantic',
                  'experience.comprehension', 'lawfulness.necessary',
                  'value_generation.sacred'}


def main():
    print('=== v1108b Step F — 観察 4: 48 軸 Macro/Micro 整合 (補助根拠) ===\n')
    t0 = time.time()

    # v1107b axis 寄与 (5 cat) を読み込み、24 cat 全体に応用するため
    # event 単位の axis 寄与を使用
    contrib = pd.read_parquet(V1107B_MAIN / 'observation_2_axis_contribution.parquet')
    print(f'  events with axis contribution: {len(contrib)}')

    axes = []
    am = json.load(open(V106_MAIN / 'axes_metadata.json'))
    for ax in am['axes_order']:
        for lvl in ax['level_names']:
            axes.append(f'{ax["name"]}.{lvl}')

    def axis_scale(ax):
        if ax in GEMINI_MICRO: return 'Micro'
        if ax in GEMINI_MESO: return 'Meso'
        if ax in GEMINI_MACRO: return 'Macro'
        return 'Other'

    axis_scales = [axis_scale(axes[i]) for i in range(48)]

    # category 別 scale 寄与
    print('\n[1] 5 cat 既知の Macro/Meso/Micro 寄与 (v1107b)')
    bias_rows = []
    for cat in sorted(contrib['category'].unique()):
        sub = contrib[contrib['category'] == cat]
        ax_contribs = np.array([sub[f'axis_{i}'].mean() for i in range(48)])
        scale_sum = {'Micro': 0.0, 'Meso': 0.0, 'Macro': 0.0, 'Other': 0.0}
        for i, sc in enumerate(axis_scales):
            scale_sum[sc] += ax_contribs[i]
        bias_rows.append({
            'category': cat, 'n_events': len(sub),
            'micro_sum': scale_sum['Micro'],
            'meso_sum': scale_sum['Meso'],
            'macro_sum': scale_sum['Macro'],
        })
    bias_5 = pd.DataFrame(bias_rows)
    print(bias_5.round(4).to_string(index=False))

    # 24 cat 推定: v1108b observation_1 から CID 物理量に基づき推定
    # ただし v1108b は cid_atom_sim 経由で参照 CID を見ているだけで、
    # 48 軸寄与 (atom_centroid × word_raw) は持たない
    # → v1108b で 24 cat の Macro/Micro 寄与を直接計算するには
    #    v1107b と同じ event 単位 axis 寄与計算が必要
    # → 補助根拠として 5 cat 結果を引用する形にする (GPT §2.3 反映)

    # 24 cat 全体については v1108b observation_2 の strength_signed と比較
    # cluster_0 寄り (strength > 0) cat が Macro 寄与高なら整合
    atom_dist = pd.read_parquet(V1108B_MAIN / 'observation_2_atom_distances.parquet')
    cat_strength = atom_dist.groupby('category')['strength_signed'].mean().reset_index()

    # 5 cat (PER/EXS/BOD/FND/PRP) で macro 寄与 vs strength_signed 相関
    print('\n[2] 5 cat 既知の Macro 寄与 vs cluster strength 整合')
    merge_5 = bias_5.merge(cat_strength, on='category')
    print(merge_5[['category', 'macro_sum', 'micro_sum', 'strength_signed']].round(4).to_string(index=False))

    from scipy.stats import pearsonr
    if len(merge_5) >= 3:
        rho, p = pearsonr(merge_5['macro_sum'].values, merge_5['strength_signed'].values)
        print(f'  corr(macro_sum, strength_signed) = {rho:.4f} (p={p:.4f})')
    else:
        rho = 0; p = 1
    macro_aligned = rho > 0.5 and p < 0.5  # 5 cat なので緩め threshold

    bias_5.to_parquet(V1108B_MAIN / 'observation_4_5cat_scale_bias.parquet', index=False)
    merge_5.to_parquet(V1108B_MAIN / 'observation_4_scale_strength_correlation.parquet',
                        index=False)

    # 構造ラベル: v1107b #L54 が v1108b cluster と整合するか (5 cat 範囲)
    label = 'macro_micro_aligned_with_cluster' if macro_aligned else 'macro_micro_not_aligned'

    sum_df = pd.DataFrame([{
        'n_cat_with_axis_contribution': len(bias_5),
        'correlation_macro_strength': float(rho),
        'p_value': float(p),
        'macro_aligned': bool(macro_aligned),
        'structural_label': label,
        'note': '48 軸寄与は 5 cat のみ (v1107b ベース)、24 cat 全体は補助根拠扱い (GPT §2.3)',
        'elapsed_sec': round(time.time() - t0, 2),
    }])
    sum_df.to_parquet(V1108B_MAIN / 'observation_4_summary.parquet', index=False)

    print(f'\n--- 構造ラベル判定 (補助根拠) ---')
    print(f'  Macro 寄与 vs cluster strength 相関: {rho:.4f}')
    print(f'  構造ラベル: {label}')
    print(f'  注: 48 軸寄与は 5 cat のみ (v1107b ベース)、24 cat 全体は補助根拠扱い')

    print(f'\n=== Step F 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
