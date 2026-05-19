#!/usr/bin/env python3
"""v1103 Step D — グラフ HTML (4 種密度 × multi-k × sim_basis、receiver_bin 別)"""
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1103_MAIN = REPO_ROOT / 'unified/v1103/outputs/main'
V1103_OUT = REPO_ROOT / 'unified/v1103/outputs'


def main():
    dist = pd.read_parquet(V1103_MAIN / 'response_atom_distribution.parquet')
    dens = pd.read_parquet(V1103_MAIN / 'density_summary.parquet')

    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=[
            'Section 1: 4 種密度 × sim_basis (raw/norm) × multi-k (5/10/20) — 留保 #33 同型「集計単位で像が変わる」',
            'Section 2: receiver_bin 別 raw_density × sim_basis × k=10 — 受け手構造で密度が反転するか',
            'Section 3: candidate atom 確率分布 top10 (代表 cell、Aruism 対称性 100% 未満確認)',
            'Section 4: Monitor 検出数 vs 受け手構造',
        ],
        vertical_spacing=0.08,
    )

    # Section 1: 4 種密度
    pivot = dens.groupby(['sim_basis','k'])[['raw_density','qweighted_density','const_adjusted_density']].mean().reset_index()
    pivot['label'] = pivot['sim_basis'] + '×k=' + pivot['k'].astype(str)
    for col, color in [('raw_density','#1f77b4'),('qweighted_density','#ff7f0e'),('const_adjusted_density','#2ca02c')]:
        fig.add_trace(go.Bar(x=pivot['label'], y=pivot[col], name=col,
                              text=[f'{v:.3f}' for v in pivot[col]], textposition='outside',
                              marker_color=color),
                       row=1, col=1)
    fig.update_yaxes(title='mean density', row=1, col=1, range=[0, 1])

    # Section 2: receiver_bin 別 raw_density (k=10、sim_basis 別)
    sub = dens[dens['k']==10].groupby(['receiver_bin','sim_basis'])['raw_density'].mean().unstack()
    rb_order = sorted(sub.index)
    for basis, color in [('raw','#1f77b4'),('norm','#d62728')]:
        if basis in sub.columns:
            vals = sub[basis].reindex(rb_order)
            fig.add_trace(go.Bar(x=rb_order, y=vals.values, name=f'{basis}_density',
                                  marker_color=color, text=[f'{v:.2f}' for v in vals],
                                  textposition='outside', showlegend=True),
                           row=2, col=1)
    fig.update_yaxes(title='raw_density (k=10)', row=2, col=1, range=[0, 1])
    fig.update_xaxes(tickangle=-45, row=2, col=1)

    # Section 3: 候補確率分布 top10 (代表 cell = CID_n=5 / atom_delta / raw / k=10)
    rep = dist[(dist['receiver_bin']=='CID_n=5') & (dist['change_metric_type']=='atom_delta')
                & (dist['sim_basis']=='raw') & (dist['k']==10)].sort_values('response_prob', ascending=False).head(10)
    fig.add_trace(go.Bar(x=rep['candidate_atom'], y=rep['response_prob'],
                          marker_color=['#d62728' if m else '#1f77b4' for m in rep['is_monitor']],
                          text=[f'{v:.3f}' for v in rep['response_prob']],
                          textposition='outside', showlegend=False),
                   row=3, col=1)
    fig.add_hline(y=1.0, line_dash='dash', line_color='red',
                  annotation_text='100% (Aruism 対称性 — 到達するとランダム消失)',
                  row=3, col=1)
    fig.update_yaxes(title='response_prob (代表 CID_n=5/atom_delta/raw/k=10)', range=[0, 1.1], row=3, col=1)
    fig.update_xaxes(tickangle=-30, row=3, col=1)

    # Section 4: Monitor 検出数 × receiver_bin
    mon = dens.groupby('receiver_bin')['n_monitor'].mean().reindex(rb_order)
    fig.add_trace(go.Bar(x=rb_order, y=mon.values,
                          marker_color='#9467bd',
                          text=[f'{v:.2f}' for v in mon],
                          textposition='outside', showlegend=False),
                   row=4, col=1)
    fig.update_yaxes(title='mean n_monitor per cell', row=4, col=1)
    fig.update_xaxes(tickangle=-45, row=4, col=1)

    max_p = dist['response_prob'].max()
    n_100 = (dist['response_prob'] >= 0.999).sum()
    fig.update_layout(
        height=1800, width=1700, barmode='group',
        title=('v11.0.3 (v1103) 観察記録 — 段 4-c 48 次元密度の偏り点検<br>'
               f'<sub>4 種密度並列 + multi-k sensitivity + raw/norm 並列 (§5.1)、Aruism 対称性 max_prob={max_p:.3f} '
               f'(100% 到達 {n_100} rows)、judgement なし (#12)、48 次元人為性留保あり (§4)、Constitution v1.0 適用</sub>'),
        legend=dict(orientation='h', yanchor='bottom', y=-0.02, xanchor='center', x=0.5),
    )

    out = V1103_OUT / 'v1103_observation.html'
    fig.write_html(out, include_plotlyjs='cdn')
    print(f'wrote {out} ({out.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
