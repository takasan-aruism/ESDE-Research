#!/usr/bin/env python3
"""v1104 Step H-4 グラフ拡張 — 観察 3 再調査 4 件 dashboard"""
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1104_MAIN = REPO_ROOT / 'unified/v1104/outputs/main'
OUT_DIR = REPO_ROOT / 'unified/v1104/outputs'


def main():
    r1 = pd.read_parquet(V1104_MAIN / 'observation_3_stratified.parquet')
    r2 = pd.read_parquet(V1104_MAIN / 'observation_3_weighted.parquet')
    r3 = pd.read_parquet(V1104_MAIN / 'observation_3_alt_metrics.parquet')
    r4 = pd.read_parquet(V1104_MAIN / 'observation_3_shuffle_baseline.parquet')

    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=[
            '再調査 1 層化 (qc_regime × sim_basis × k = 24 strata)、ペア別 |r|、max 0.256',
            '再調査 2 scope-filter — ESDE 限定で stability/diffusion vs max_prob が |r|>0.4 顕在化、alpha/beta 消失',
            '再調査 3 代替指標 4×4=16 ペア (pooled)、最強 r=0.157 で pooled では新指標も限定的',
            '再調査 4 shuffle baseline (chain内 cid permutation)、stability_mean 0.805→0.772、相関係数はほぼ不変',
        ],
        vertical_spacing=0.07, row_heights=[0.25, 0.30, 0.20, 0.25],
    )

    # R1: stratified, 24 strata × 2 pairs, take stability_vs_maxprob and diffusion_vs_entropy
    r1s = r1[r1['pair'] == 'traj_stability_mean_vs_response_max_prob'].copy()
    r1s['label'] = (r1s['qc_regime'].str[:4] + '/' + r1s['sim_basis'] + '/k=' +
                    r1s['k'].astype(str))
    r1d = r1[r1['pair'] == 'diffusion_ratio_mean_vs_response_entropy'].copy()
    r1d['label'] = (r1d['qc_regime'].str[:4] + '/' + r1d['sim_basis'] + '/k=' +
                    r1d['k'].astype(str))
    fig.add_trace(go.Bar(x=r1s['label'], y=r1s['pearson_r'], name='stability_vs_maxprob',
                          marker_color='#1f77b4',
                          text=[f'{v:.3f}' for v in r1s['pearson_r']],
                          textposition='outside'),
                   row=1, col=1)
    fig.add_trace(go.Bar(x=r1d['label'], y=r1d['pearson_r'], name='diffusion_vs_entropy',
                          marker_color='#ff7f0e',
                          text=[f'{v:.3f}' for v in r1d['pearson_r']],
                          textposition='outside'),
                   row=1, col=1)
    fig.add_hline(y=0.3, line_dash='dash', line_color='red',
                  annotation_text='|r|=0.3 (中)', row=1, col=1)
    fig.add_hline(y=-0.3, line_dash='dash', line_color='red', row=1, col=1)
    fig.update_xaxes(tickangle=-60, row=1, col=1)
    fig.update_yaxes(title='pearson_r', row=1, col=1, range=[-0.5, 0.5])

    # R2: scope filter heatmap-style, pair × scope_filter unweighted_r
    pivot = r2.pivot_table(index='pair', columns='scope_filter', values='unweighted_r')
    pair_order = ['stability_vs_maxprob', 'stability_vs_entropy', 'stability_vs_top3',
                  'stability_vs_gini', 'diffusion_vs_maxprob', 'diffusion_vs_entropy',
                  'chain_len_vs_maxprob']
    pivot = pivot.reindex([p for p in pair_order if p in pivot.index])
    scope_order = ['all', 'ESDE', 'CID', 'beta', 'alpha']
    pivot = pivot[[s for s in scope_order if s in pivot.columns]]
    fig.add_trace(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale='RdBu', zmid=0, zmin=-0.5, zmax=0.5,
        text=[[f'{v:.3f}' if not np.isnan(v) else '' for v in row] for row in pivot.values],
        texttemplate='%{text}', textfont={'size': 11}, showscale=True,
        colorbar=dict(title='pearson_r', y=0.50, len=0.25),
    ), row=2, col=1)

    # R3: alt metrics, top 8 by |r|
    r3s = r3.copy()
    r3s['label'] = r3s['traj_metric'].str.replace('_mean','') + ' vs ' + r3s['resp_metric'].str.replace('response_','')
    r3s = r3s.sort_values('abs_pearson_r', ascending=False).head(8)
    fig.add_trace(go.Bar(x=r3s['label'], y=r3s['pearson_r'],
                          marker_color=['#d62728' if r < 0 else '#2ca02c' for r in r3s['pearson_r']],
                          text=[f'{v:.3f}' for v in r3s['pearson_r']],
                          textposition='outside', showlegend=False),
                   row=3, col=1)
    fig.add_hline(y=0.1, line_dash='dash', line_color='gray', row=3, col=1)
    fig.add_hline(y=-0.1, line_dash='dash', line_color='gray', row=3, col=1)
    fig.update_xaxes(tickangle=-30, row=3, col=1)
    fig.update_yaxes(title='pearson_r (pooled)', row=3, col=1, range=[-0.25, 0.25])

    # R4: actual vs shuffled, pair-grouped
    r4_actual = r4[r4['shuffle_mode'] == 'none']
    r4_shuf = r4[r4['shuffle_mode'] == 'within']
    pairs = r4_actual['pair'].tolist()
    fig.add_trace(go.Bar(x=pairs, y=r4_actual['pearson_r'], name='actual (none)',
                          marker_color='#1f77b4',
                          text=[f'{v:.3f}' for v in r4_actual['pearson_r']],
                          textposition='outside'),
                   row=4, col=1)
    fig.add_trace(go.Bar(x=pairs, y=r4_shuf['pearson_r'], name='shuffled (within)',
                          marker_color='#d62728',
                          text=[f'{v:.3f}' for v in r4_shuf['pearson_r']],
                          textposition='outside'),
                   row=4, col=1)
    fig.update_xaxes(tickangle=-15, row=4, col=1)
    fig.update_yaxes(title='pearson_r', row=4, col=1, range=[-0.6, 0.6])

    fig.update_layout(
        height=2100, width=1700, barmode='group',
        title=('v11.0.4 (v1104) Step H-4 観察 3 再調査 dashboard<br>'
               '<sub>パターン候補: scope mixing 希釈 (pooled r=0.157 → ESDE-only |r|>0.4)、'
               '層化単独効果は限定 (max r=0.256)、judgment 回避 + 判定語制限</sub>'),
        legend=dict(orientation='h', yanchor='bottom', y=-0.02, xanchor='center', x=0.5),
    )

    out = OUT_DIR / 'v1104_reinvestigation_obs3.html'
    fig.write_html(out, include_plotlyjs='cdn')
    print(f'wrote {out} ({out.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
