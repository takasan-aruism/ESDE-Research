#!/usr/bin/env python3
"""v1104 Step H-3 グラフ拡張 — 再調査 4 件 dashboard"""
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1104_MAIN = REPO_ROOT / 'unified/v1104/outputs/main'
OUT_DIR = REPO_ROOT / 'unified/v1104/outputs'


def main():
    r1 = pd.read_parquet(V1104_MAIN / 'observation_2_restratified.parquet')
    r2 = pd.read_parquet(V1104_MAIN / 'observation_2_shuffle_variants.parquet')
    r3 = pd.read_parquet(V1104_MAIN / 'observation_2_resolution.parquet')
    r4 = pd.read_parquet(V1104_MAIN / 'observation_2_self_loop_split.parquet')
    sd = pd.read_parquet(V1104_MAIN / 'cid_sim_matrix_distribution.parquet')

    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=[
            '再調査 1: n_members × qc_gini 層化 (|lift| > 0.01 = 全 27 bin で 0、層化しても shuffle A 由来 lift=0 は変わらない)',
            '再調査 2: shuffle 3 種 (A 現状 / B chain間 / C global pool)、lift 比較 — 種別変えると lift > 0 出現',
            '再調査 3: 粒度 3 階層 (window/step10/event) の atom_change_rate + inter-cid sim',
            '再調査 4: self-loop / non-self-loop 分離 (scope × is_self_loop の lift) — non-self-loop でも |lift|<0.01',
        ],
        vertical_spacing=0.08,
    )

    # 再調査 1: scope × n_bin の lift_mean (scope 別 max bar)
    g1 = r1.groupby('change_scope')['lift_mean'].agg(['min','max','mean']).reset_index()
    fig.add_trace(go.Bar(x=g1['change_scope'], y=g1['max'], name='lift_max',
                          marker_color='#1f77b4', text=[f'{v:.5f}' for v in g1['max']],
                          textposition='outside'),
                   row=1, col=1)
    fig.add_trace(go.Bar(x=g1['change_scope'], y=g1['min'], name='lift_min',
                          marker_color='#d62728', text=[f'{v:.5f}' for v in g1['min']],
                          textposition='outside'),
                   row=1, col=1)
    fig.add_hline(y=0.01, line_dash='dash', line_color='red',
                  annotation_text='|lift|=0.01 (絶対格言 #3)',
                  row=1, col=1)
    fig.add_hline(y=-0.01, line_dash='dash', line_color='red', row=1, col=1)
    fig.update_yaxes(title='lift (per bin)', row=1, col=1)

    # 再調査 2: scope × shuffle 種別 lift
    g2 = r2.groupby('change_scope').agg(
        lift_A=('lift_A','mean'),
        lift_B=('lift_B','mean'),
        lift_C=('lift_C','mean'),
    ).reset_index()
    scope_order = ['CID','alpha','beta','ESDE_event','ESDE_step10','ESDE_window']
    g2 = g2.set_index('change_scope').reindex(scope_order).reset_index()
    for col, color in [('lift_A','#1f77b4'),('lift_B','#ff7f0e'),('lift_C','#2ca02c')]:
        fig.add_trace(go.Bar(x=g2['change_scope'], y=g2[col], name=col,
                              marker_color=color,
                              text=[f'{v:.4f}' for v in g2[col]], textposition='outside'),
                       row=2, col=1)
    fig.add_hline(y=0.01, line_dash='dash', line_color='red',
                  annotation_text='|lift|=0.01', row=2, col=1)
    fig.update_yaxes(title='lift over baseline', row=2, col=1)

    # 再調査 3: 粒度別 atom_change_rate + inter_cid_sim
    g3 = r3.groupby('resolution').agg(
        atom_chg=('atom_change_rate','mean'),
        sim=('mean_inter_cid_sim','mean'),
        n_rec=('n_records','mean'),
    ).reindex(['window','step10','event']).reset_index()
    fig.add_trace(go.Bar(x=g3['resolution'], y=g3['atom_chg'], name='atom_change_rate',
                          marker_color='#9467bd',
                          text=[f'{v:.3f}' for v in g3['atom_chg']], textposition='outside'),
                   row=3, col=1)
    fig.add_trace(go.Bar(x=g3['resolution'], y=g3['sim'], name='inter_cid_sim_mean',
                          marker_color='#8c564b',
                          text=[f'{v:.3f}' for v in g3['sim']], textposition='outside'),
                   row=3, col=1)
    fig.update_yaxes(title='rate / sim', row=3, col=1, range=[0, 1])

    # 再調査 4: scope × is_self_loop の lift
    r4_disp = r4.copy()
    r4_disp['label'] = r4_disp['change_scope'] + '/' + r4_disp['is_full_self_loop'].astype(str)
    fig.add_trace(go.Bar(x=r4_disp['label'], y=r4_disp['lift_mean'],
                          marker_color=['#2ca02c' if sl else '#1f77b4' for sl in r4_disp['is_full_self_loop']],
                          text=[f'{v:.5f}' for v in r4_disp['lift_mean']], textposition='outside',
                          showlegend=False),
                   row=4, col=1)
    fig.add_hline(y=0.01, line_dash='dash', line_color='red',
                  annotation_text='|lift|=0.01', row=4, col=1)
    fig.update_yaxes(title='lift', row=4, col=1)
    fig.update_xaxes(tickangle=-30, row=4, col=1)

    fig.update_layout(
        height=2000, width=1700, barmode='group',
        title=('v11.0.4 (v1104) Step H-3 観察 2 再調査 dashboard<br>'
               '<sub>パターン α (観察方法問題) 候補: shuffle C で alpha 0.166 / beta 0.139 の lift、'
               '既存 lift=0 は shuffle 種別 A 固有、judgment 回避 + 判定語制限</sub>'),
        legend=dict(orientation='h', yanchor='bottom', y=-0.03, xanchor='center', x=0.5),
    )

    out = OUT_DIR / 'v1104_reinvestigation.html'
    fig.write_html(out, include_plotlyjs='cdn')
    print(f'wrote {out} ({out.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
