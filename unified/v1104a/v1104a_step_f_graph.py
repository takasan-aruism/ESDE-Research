#!/usr/bin/env python3
"""v1104a Step F' — グラフ HTML (追加調整 4 件 dashboard)"""
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1104A_MAIN = REPO_ROOT / 'unified/v1104a/outputs/main'
OUT_DIR = REPO_ROOT / 'unified/v1104a/outputs'


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    adj1 = pd.read_parquet(V1104A_MAIN / 'observation_2_scope_stratified.parquet')
    adj2 = pd.read_parquet(V1104A_MAIN / 'observation_3_scope_n_stratified.parquet')
    adj3 = pd.read_parquet(V1104A_MAIN / 'observation_3_density_comparison.parquet')
    adj4 = pd.read_parquet(V1104A_MAIN / 'observation_4_scope_filtered.parquet')

    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=[
            '追加調整 1: 観察 2 scope × n-size × shuffle × self-loop lift_mean — CID 100% self-loop、alpha non-self-loop lift_C=0.152 が最強',
            '追加調整 2: 観察 3 CID scope cid_n_core 層化 (全 NaN、構造的) + ESDE 3 解像度 r — event/step10 で stability 0.64 / diffusion -0.62 強相関',
            '追加調整 3: trajectory vs density 比較 — scope/粒度依存の優劣逆転 (event/step10 で trajectory 強、window/CID/集約で density 強)',
            '追加調整 4: 観察 4 scope-filter — CID precision 1.0 (B subset)、alpha/beta recall 1.0 (B superset)、ESDE A=0/B=9 (B のみ独自)',
        ],
        vertical_spacing=0.07, row_heights=[0.30, 0.22, 0.26, 0.22],
    )

    # ---------- 追加調整 1: scope × n_size_bin × shuffle_type × is_self_loop ----------
    a1 = adj1[adj1['is_full_self_loop'] == False].copy()
    a1['label'] = a1['change_scope'] + '/' + a1['n_size_bin']
    scope_order = ['alpha', 'beta', 'CID', 'ESDE_event', 'ESDE_step10', 'ESDE_window']
    for st, color in [('A', '#1f77b4'), ('B', '#ff7f0e'), ('C', '#2ca02c')]:
        sub = a1[a1['shuffle_type'] == st].sort_values(['change_scope', 'n_size_bin'])
        fig.add_trace(go.Bar(x=sub['label'], y=sub['lift_mean'], name=f'shuffle {st}',
                              marker_color=color,
                              text=[f'{v:.3f}' for v in sub['lift_mean']],
                              textposition='outside'),
                       row=1, col=1)
    fig.add_hline(y=0.01, line_dash='dash', line_color='red',
                  annotation_text='|lift|=0.01', row=1, col=1)
    fig.add_hline(y=-0.01, line_dash='dash', line_color='red', row=1, col=1)
    fig.update_xaxes(tickangle=-60, row=1, col=1)
    fig.update_yaxes(title='lift_mean (non-self-loop)', row=1, col=1)

    # ---------- 追加調整 2: stability_vs_maxprob (CID 全 NaN + ESDE 3 解像度) ----------
    a2s = adj2[adj2['pair'] == 'stability_vs_maxprob'].copy()
    a2d = adj2[adj2['pair'] == 'diffusion_vs_maxprob'].copy()
    fig.add_trace(go.Bar(x=a2s['stratum'], y=a2s['pearson_r'],
                          name='stability_vs_maxprob',
                          marker_color='#1f77b4',
                          text=[f'{v:.3f}' if not np.isnan(v) else 'NaN'
                                for v in a2s['pearson_r']],
                          textposition='outside'),
                   row=2, col=1)
    fig.add_trace(go.Bar(x=a2d['stratum'], y=a2d['pearson_r'],
                          name='diffusion_vs_maxprob',
                          marker_color='#ff7f0e',
                          text=[f'{v:.3f}' if not np.isnan(v) else 'NaN'
                                for v in a2d['pearson_r']],
                          textposition='outside'),
                   row=2, col=1)
    fig.add_hline(y=0.5, line_dash='dash', line_color='red',
                  annotation_text='|r|=0.5 (強)', row=2, col=1)
    fig.add_hline(y=-0.5, line_dash='dash', line_color='red', row=2, col=1)
    fig.update_xaxes(tickangle=-30, row=2, col=1)
    fig.update_yaxes(title='pearson_r', row=2, col=1, range=[-1, 1])

    # ---------- 追加調整 3: top predictor per (stratum, max_prob) ----------
    a3 = adj3[adj3['response'] == 'response_max_prob'].copy()
    strata_order = ['ESDE_event', 'ESDE_step10', 'ESDE_window', 'ESDE_all',
                    'CID_n=2', 'CID_n=3', 'CID_n=4', 'CID_n=5', 'CID_n=6+', 'CID_all']
    rows = []
    for st in strata_order:
        for pt in ['trajectory', 'density']:
            sub = a3[(a3['stratum'] == st) & (a3['predictor_type'] == pt)]
            sub = sub.dropna(subset=['pearson_r'])
            if len(sub) == 0:
                rows.append({'stratum': st, 'type': pt, 'r': 0, 'predictor': 'NaN'})
                continue
            top = sub.iloc[sub['abs_pearson_r'].argmax()]
            rows.append({'stratum': st, 'type': pt, 'r': top['pearson_r'],
                          'predictor': top['predictor']})
    a3p = pd.DataFrame(rows)
    for pt, color in [('trajectory', '#1f77b4'), ('density', '#d62728')]:
        sub = a3p[a3p['type'] == pt]
        fig.add_trace(go.Bar(x=sub['stratum'], y=sub['r'], name=f'top {pt}',
                              marker_color=color,
                              text=[f'{r:.2f}<br>{p}' for r, p in zip(sub['r'], sub['predictor'])],
                              textposition='outside'),
                       row=3, col=1)
    fig.add_hline(y=0.5, line_dash='dash', line_color='red', row=3, col=1)
    fig.add_hline(y=-0.5, line_dash='dash', line_color='red', row=3, col=1)
    fig.update_xaxes(tickangle=-30, row=3, col=1)
    fig.update_yaxes(title='pearson_r (top per type)', row=3, col=1, range=[-1.1, 1.1])

    # ---------- 追加調整 4: scope-filter Jaccard/Recall/Precision (b_thr=1) ----------
    a4 = adj4[adj4['b_threshold'] == 1].copy()
    for col, color in [('jaccard', '#1f77b4'),
                        ('recall_B_covers_A', '#ff7f0e'),
                        ('precision_B_is_A', '#2ca02c')]:
        fig.add_trace(go.Bar(x=a4['scope_filter'], y=a4[col], name=col,
                              marker_color=color,
                              text=[f'{v:.3f}' if not np.isnan(v) else 'NaN'
                                    for v in a4[col]],
                              textposition='outside'),
                       row=4, col=1)
    fig.update_yaxes(title='ratio', row=4, col=1, range=[0, 1.15])

    fig.update_layout(
        height=2100, width=1700, barmode='group',
        title=('v11.0.4a (v1104a) Step F\' 追加調整 4 件 dashboard<br>'
               '<sub>scope × 層化 × shuffle/density で観察方法依存を整理。'
               'CID 100% self-loop、event/step10 trajectory 強、'
               'window/集約 density 強、ESDE B のみ独自。'
               'judgment 回避 + 判定語制限 + selector 化禁止</sub>'),
        legend=dict(orientation='h', yanchor='bottom', y=-0.02, xanchor='center', x=0.5),
    )
    out = OUT_DIR / 'v1104a_observation.html'
    fig.write_html(out, include_plotlyjs='cdn')
    print(f'wrote {out} ({out.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
