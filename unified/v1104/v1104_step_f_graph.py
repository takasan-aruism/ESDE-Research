#!/usr/bin/env python3
"""v1104 Step F — グラフ HTML (4 観察 dashboard)"""
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1104_MAIN = REPO_ROOT / 'unified/v1104/outputs/main'
OUT_DIR = REPO_ROOT / 'unified/v1104/outputs'


def main():
    obs1 = pd.read_parquet(V1104_MAIN / 'observation_1_cid_integration.parquet')
    obs2 = pd.read_parquet(V1104_MAIN / 'observation_2_predecessor_chain.parquet')
    obs3 = pd.read_parquet(V1104_MAIN / 'observation_3_trajectory_response.parquet')
    obs4 = pd.read_parquet(V1104_MAIN / 'observation_4_b_overlap.parquet')

    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=[
            'Obs 1: CID-Integration 像の差分 (n_members × qc_gini 層化、match_k1 vs jaccard_top3/5)',
            'Obs 2: predecessor 連鎖の lift_over_baseline (shuffle baseline 比較、scope 別)',
            'Obs 3: trajectory stability ↔ response_max_prob 対応 (qc_regime × sim_basis 別)',
            'Obs 4: A 際立ち (v1102 outstanding_score) vs B 際立ち (ESDE 自身の emit) 重なり',
        ],
        vertical_spacing=0.10,
        specs=[[{'type':'bar'}], [{'type':'bar'}], [{'type':'bar'}], [{'type':'bar'}]],
    )

    # Obs 1: 層化 bin 別 match_k1 / jaccard_top3 / jaccard_top5
    g1 = obs1.groupby(['n_members_bin','qc_gini_bin']).agg(
        n_records=('alpha_id', 'count'),
        match_k1=('match_rate_k1', 'mean'),
        j3=('jaccard_top3', 'mean'),
        j5=('jaccard_top5', 'mean'),
    ).reset_index()
    g1 = g1[(g1['n_members_bin']!='NA') & (g1['qc_gini_bin']!='NA')]
    g1['label'] = g1['n_members_bin'] + '/' + g1['qc_gini_bin']
    for col, name, color in [('match_k1','match_k1','#1f77b4'),
                              ('j3','jaccard_top3','#ff7f0e'),
                              ('j5','jaccard_top5','#2ca02c')]:
        fig.add_trace(go.Bar(x=g1['label'], y=g1[col], name=name, marker_color=color,
                              text=[f'{v:.2f}' for v in g1[col]], textposition='outside',
                              showlegend=(col=='match_k1')),
                       row=1, col=1)
    fig.update_yaxes(title='', row=1, col=1, range=[0, 1])
    fig.update_xaxes(tickangle=-45, row=1, col=1)

    # Obs 2: scope 別 lift_over_baseline + sim_mean
    g2 = obs2.groupby('change_scope').agg(
        sim=('mean_sim_along_chain', 'mean'),
        base=('shuffle_baseline_sim_mean', 'mean'),
        lift=('lift_over_baseline', 'mean'),
    ).reset_index()
    scope_order = ['CID','alpha','beta','ESDE_event','ESDE_step10','ESDE_window']
    g2 = g2.set_index('change_scope').reindex(scope_order).reset_index()
    fig.add_trace(go.Bar(x=g2['change_scope'], y=g2['sim'], name='sim_along_chain',
                          marker_color='#1f77b4', text=[f'{v:.4f}' for v in g2['sim']],
                          textposition='outside'),
                   row=2, col=1)
    fig.add_trace(go.Bar(x=g2['change_scope'], y=g2['base'], name='shuffle_baseline',
                          marker_color='#d62728', text=[f'{v:.4f}' for v in g2['base']],
                          textposition='outside'),
                   row=2, col=1)
    fig.update_yaxes(title='cosine sim (chain vs baseline)', row=2, col=1, range=[0.93, 1.005])

    # Obs 3: qc_regime × sim_basis 別 trajectory stability + response_max_prob
    g3 = obs3.groupby(['qc_regime','sim_basis']).agg(
        ts=('traj_stability_mean', 'mean'),
        rmp=('response_max_prob', 'mean'),
        re=('response_entropy', 'mean'),
    ).reset_index()
    g3['label'] = g3['qc_regime'] + '/' + g3['sim_basis']
    fig.add_trace(go.Bar(x=g3['label'], y=g3['ts'], name='traj_stability',
                          marker_color='#1f77b4',
                          text=[f'{v:.3f}' for v in g3['ts']], textposition='outside',
                          showlegend=False),
                   row=3, col=1)
    fig.add_trace(go.Bar(x=g3['label'], y=g3['rmp'], name='response_max_prob',
                          marker_color='#9467bd',
                          text=[f'{v:.3f}' for v in g3['rmp']], textposition='outside',
                          showlegend=False),
                   row=3, col=1)
    fig.update_yaxes(title='', row=3, col=1, range=[0, 1])
    fig.update_xaxes(tickangle=-30, row=3, col=1)

    # Obs 4: A vs B 際立ち重なり (Jaccard / Recall / Precision)
    a_high = (obs4['outstanding_score'] >= 3).sum()
    b_any = (obs4['B_outstanding_score'] >= 1).sum()
    b_strong = (obs4['B_outstanding_score'] >= 2).sum()
    inter = ((obs4['outstanding_score'] >= 3) & (obs4['B_outstanding_score'] >= 1)).sum()
    inter_strong = ((obs4['outstanding_score'] >= 3) & (obs4['B_outstanding_score'] >= 2)).sum()
    jaccard = inter / (a_high + b_any - inter) if (a_high + b_any - inter) > 0 else 0
    recall = inter / a_high if a_high > 0 else 0
    precision = inter / b_any if b_any > 0 else 0
    labels = ['A 際立ち\n(score≥3)', 'B 際立ち\n(B_score≥1)', 'B 際立ち\n(B_score≥2)',
              'A ∩ B≥1', 'A ∩ B≥2', 'Jaccard', 'Recall', 'Precision']
    vals = [a_high, b_any, b_strong, inter, inter_strong, jaccard, recall, precision]
    colors = ['#1f77b4','#ff7f0e','#ff7f0e','#2ca02c','#2ca02c','#9467bd','#9467bd','#9467bd']
    fig.add_trace(go.Bar(x=labels, y=vals, marker_color=colors,
                          text=[f'{v:.3f}' if isinstance(v, float) and v<1 else str(int(v))
                                for v in vals],
                          textposition='outside', showlegend=False),
                   row=4, col=1)
    fig.update_yaxes(title='', row=4, col=1)

    fig.update_layout(
        height=2000, width=1700, barmode='group',
        title=('v11.0.4 (v1104) 観察記録 — CID/IID が下でやっていることの点検 (4 観察 dashboard)<br>'
               '<sub>段 4-b/4-c を支える ESDE 内部処理確認、judgment なし (#12)、判定語制限遵守 '
               '(「連想」「成功/失敗」を使わない)、selector 化禁止 (B post-process 仮想評価のみ)</sub>'),
        legend=dict(orientation='h', yanchor='bottom', y=-0.03, xanchor='center', x=0.5),
    )

    out = OUT_DIR / 'v1104_observation.html'
    fig.write_html(out, include_plotlyjs='cdn')
    print(f'wrote {out} ({out.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
