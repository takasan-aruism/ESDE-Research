#!/usr/bin/env python3
"""v1101a 段階 2 Step G グラフ — Integration 構成層化 dashboard"""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
OUT_MAIN = REPO_ROOT / 'unified/v1101a/outputs/main'
OUT_DIR = REPO_ROOT / 'unified/v1101a/outputs'

PATH_COLORS = {
    'attention_via_salience': '#1f77b4', 'familiarity': '#ff7f0e',
    'integration_alpha': '#2ca02c', 'integration_beta': '#d62728',
    'temporal_coactivation': '#9467bd',
}


def main():
    df = pd.read_parquet(OUT_MAIN / 'stratified_observation_integration.parquet')
    alpha = df[df['scope']=='alpha'].copy()
    beta = df[df['scope']=='beta'].copy()
    alpha['cell'] = alpha['n_members_bin'] + ' / ' + alpha['qc_gini_bin']
    beta['cell'] = beta['n_members_bin'] + ' / ' + beta['qc_gini_bin']

    fig = make_subplots(rows=2, cols=2,
        subplot_titles=[
            'alpha: conscious_frac × 構成 (n × gini)',
            'alpha: causality_path z-score frac × 構成',
            'beta: conscious_frac × 構成',
            'beta: causality_path z-score frac × 構成',
        ],
        vertical_spacing=0.18, horizontal_spacing=0.10)

    # alpha conscious_frac
    fig.add_trace(go.Bar(x=alpha['cell'], y=alpha['conscious_frac'],
                          marker_color='#2ca02c',
                          text=[f'{v:.3f}<br>(n={r:,})' for v,r in
                                zip(alpha['conscious_frac'], alpha['n_records'])],
                          textposition='outside', showlegend=False),
                   row=1, col=1)
    fig.update_yaxes(title='conscious_frac', range=[0, 1], row=1, col=1)
    fig.update_xaxes(tickangle=-45, row=1, col=1)

    # alpha causality z-score (stacked: 5 path)
    for pt in ['attention_via_salience', 'familiarity', 'integration_alpha',
                'integration_beta', 'temporal_coactivation']:
        col = f'{pt}_frac_zscore' if pt in ('familiarity','integration_alpha','integration_beta') else None
        if col is None or col not in alpha.columns:
            continue
        fig.add_trace(go.Bar(x=alpha['cell'], y=alpha[col], name=pt,
                              marker_color=PATH_COLORS[pt],
                              showlegend=True,
                              text=[f'{v:.2f}' if v>0.02 else '' for v in alpha[col]],
                              textposition='inside'),
                       row=1, col=2)
    fig.update_yaxes(title='z-score path frac', range=[0, 1], row=1, col=2)
    fig.update_xaxes(tickangle=-45, row=1, col=2)

    # beta conscious_frac
    fig.add_trace(go.Bar(x=beta['cell'], y=beta['conscious_frac'],
                          marker_color='#d62728',
                          text=[f'{v:.3f}<br>(n={r:,})' for v,r in
                                zip(beta['conscious_frac'], beta['n_records'])],
                          textposition='outside', showlegend=False),
                   row=2, col=1)
    fig.update_yaxes(title='conscious_frac', range=[0, 1], row=2, col=1)
    fig.update_xaxes(tickangle=-45, row=2, col=1)

    # beta causality z-score
    for pt in ['familiarity','integration_alpha','integration_beta']:
        col = f'{pt}_frac_zscore'
        if col not in beta.columns: continue
        fig.add_trace(go.Bar(x=beta['cell'], y=beta[col], name=pt,
                              marker_color=PATH_COLORS[pt],
                              showlegend=False,
                              text=[f'{v:.2f}' if v>0.02 else '' for v in beta[col]],
                              textposition='inside'),
                       row=2, col=2)
    fig.update_yaxes(title='z-score path frac', range=[0, 1], row=2, col=2)
    fig.update_xaxes(tickangle=-45, row=2, col=2)

    fig.update_layout(
        height=1200, width=1700, barmode='relative',
        title=('v11.0.1.a 段階 2 Step G — Integration 構成層化観察 (Taka 指摘 2026-05-19)<br>'
               '<sub>絶対格言 #4「集団平均の罠 / 層化必須」遵守、alpha/beta を n_members × qc_gini で層化、'
               'judgement なし観察記録 (絶対格言 #12)、24 seeds 1 batch (段階 1/2 出力再集計)</sub>'),
        legend=dict(orientation='h', yanchor='bottom', y=-0.07, xanchor='center', x=0.5),
    )
    out = OUT_DIR / 'v1101a_phase_2_step_g_stratification.html'
    fig.write_html(out, include_plotlyjs='cdn')
    print(f'wrote {out} ({out.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
