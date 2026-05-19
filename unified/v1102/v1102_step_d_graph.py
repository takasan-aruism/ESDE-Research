#!/usr/bin/env python3
"""v1102 Step D — グラフ HTML 統合 (2 次元配置 + 内部波及 3 次元目)

設計書 §3 出口 #4 + §2.5:
- Section 1: 際立ち度ヒートマップ (receiver_bin × change_metric_type)
- Section 2: 際立った cells (score>=3) の 5 種応答 panel (Taka 整理対応)
- Section 3: v107 時間スケール (immediate/short/medium) 別 effect_delta 推移
- Section 4: B secondary Step G 重なり

軽量 HTML、v1101a 同型 (集計値ベース)、書込み unified/v1102/outputs/ のみ。
"""
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1102_MAIN = REPO_ROOT / 'unified/v1102/outputs/main'
OUT_DIR = REPO_ROOT / 'unified/v1102/outputs'


def main():
    df = pd.read_parquet(V1102_MAIN / 'outstanding_cells.parquet')
    thresh = pd.read_parquet(V1102_MAIN / 'outstanding_thresholds.parquet')

    # ── Section 1: 際立ち度ヒートマップ
    pivot = df.pivot_table(index='receiver_bin', columns='change_metric_type',
                            values='outstanding_score', aggfunc='max')
    # receiver_bin の順序
    bin_order = (['CID_n=2','CID_n=3','CID_n=4','CID_n=5','CID_n=6+']
                 + sorted([b for b in pivot.index if b.startswith('alpha')])
                 + sorted([b for b in pivot.index if b.startswith('beta')])
                 + ['ESDE_event','ESDE_step10','ESDE_window'])
    bin_order = [b for b in bin_order if b in pivot.index]
    pivot = pivot.reindex(bin_order)

    # sample 数 (n_records)
    n_pivot = df.pivot_table(index='receiver_bin', columns='change_metric_type',
                              values='n_records', aggfunc='max').reindex(bin_order)

    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=[
            'Section 1: 際立ち度ヒートマップ (receiver_bin × change_metric_type)',
            'Section 2: 際立った cells (score>=3) の応答 5 種 + サンプル数',
            'Section 3: v107 effect_delta 時間粒度推移 (immediate/short/medium) — 電話 vs 手紙の比喩',
            'Section 4: B secondary — Step G stratified 重なり (Integration scope のみ)',
        ],
        vertical_spacing=0.07,
        specs=[[{'type':'heatmap'}], [{'type':'scatter'}], [{'type':'scatter'}], [{'type':'scatter'}]],
    )

    # Section 1: heatmap
    fig.add_trace(go.Heatmap(
        z=pivot.values, x=list(pivot.columns), y=list(pivot.index),
        colorscale='Viridis', colorbar=dict(title='outstanding<br>score', len=0.2, y=0.91),
        text=[[f'{int(v) if not np.isnan(v) else "-"}<br>(n={int(n) if not np.isnan(n) else 0})'
               for v, n in zip(row, nrow)]
              for row, nrow in zip(pivot.values, n_pivot.values)],
        texttemplate='%{text}',
        hovertemplate='%{y} × %{x}<br>score=%{z}<extra></extra>',
    ), row=1, col=1)

    # Section 2: 際立った cells (score>=3) の応答 5 種 (per cell の 5 値)
    high = df[df['outstanding_score'] >= 3].sort_values('outstanding_score', ascending=False).copy()
    high['label'] = high['receiver_bin'] + '<br>' + high['change_metric_type']
    high_unique = high.drop_duplicates('label', keep='first').head(20)

    # 応答 5 種の正規化 (0-1 表示用)
    indicators = [
        ('conscious_frac', 'conscious_frac'),
        ('influence_count_mean', 'influence/200'),
        ('variability_lift_mean', 'variability_lift'),
        ('attention_count_mean_per_window', 'attn_count/100'),
    ]
    colors = ['#d62728','#1f77b4','#2ca02c','#ff7f0e']
    for (col, name), color in zip(indicators, colors):
        vals = high_unique[col].copy()
        if 'influence' in col:
            vals = vals / 200
        elif 'attention' in col:
            vals = vals / 100
        fig.add_trace(go.Bar(
            x=high_unique['label'], y=vals, name=name, marker_color=color,
            text=[f'{v:.2f}' for v in vals], textposition='outside',
        ), row=2, col=1)
    # n_records line
    fig.add_trace(go.Scatter(
        x=high_unique['label'], y=high_unique['n_records'],
        mode='markers+text', name='n_records', yaxis='y22',
        marker=dict(color='black', size=8, symbol='diamond'),
        text=[f'n={int(v)}' for v in high_unique['n_records']],
        textposition='top center',
    ), row=2, col=1)
    fig.update_yaxes(title='応答 5 種 (正規化済)', row=2, col=1)

    # Section 3: v107 effect_delta 時間粒度推移 (高スコア cell 限定)
    top_cells = high.drop_duplicates('label', keep='first').head(8)
    for _, row in top_cells.iterrows():
        for metric_letter, color in [('Q','#1f77b4'),('C','#d62728'),('R_familiarity','#2ca02c')]:
            ys = [row.get(f'effect_delta_{metric_letter}_{ts}_mean', np.nan)
                  for ts in ['immediate','short','medium']]
            fig.add_trace(go.Scatter(
                x=['immediate','short','medium'], y=ys,
                mode='lines+markers',
                name=f'{row["receiver_bin"][:20]}/{row["change_metric_type"][:5]}/Δ{metric_letter}',
                line=dict(color=color, width=1),
                showlegend=False,
                hovertemplate=f'{row["receiver_bin"]} | {row["change_metric_type"]} | Δ{metric_letter}<br>%{{x}} = %{{y:.4f}}<extra></extra>',
            ), row=3, col=1)
    fig.update_yaxes(title='effect_delta_*_mean', row=3, col=1)
    fig.add_hline(y=0, line_dash='dash', line_color='gray', row=3, col=1)

    # Section 4: B secondary Step G 重なり
    b_df = df[df['stepg_overlap_scope'].notna()].copy()
    b_df['label'] = b_df['receiver_bin'] + ' / ' + b_df['change_metric_type']
    b_df = b_df.sort_values('stepg_overlap_int_beta_z', ascending=False).head(15)
    fig.add_trace(go.Bar(
        x=b_df['label'], y=b_df['stepg_overlap_int_beta_z'],
        name='integration_beta_z', marker_color='#d62728',
        text=[f'{v:.2f}' for v in b_df['stepg_overlap_int_beta_z']],
        textposition='outside',
    ), row=4, col=1)
    fig.add_trace(go.Bar(
        x=b_df['label'], y=b_df['stepg_overlap_familiarity_z'],
        name='familiarity_z', marker_color='#ff7f0e',
        text=[f'{v:.2f}' for v in b_df['stepg_overlap_familiarity_z']],
        textposition='outside',
    ), row=4, col=1)
    fig.update_yaxes(title='Step G z-score frac', range=[0, 1], row=4, col=1)

    fig.update_layout(
        height=2000, width=1700, barmode='group',
        title=('v11.0.2 (v1102) 観察記録 dashboard — 条件が応答を変える: 受け手構造 × 時間スケールの 2 次元観察 '
               '<br><sub>設計書 §2.6 応答 5 種並列・per-cell 全セル残し、際立ち度とサンプル数を別軸で記録、'
               '神の手回避 #9 (Top 10% + IQR、構造的閾値)、judgement なし (#12)、24 seeds 1 batch (81 cells)</sub>'),
        legend=dict(orientation='h', yanchor='bottom', y=-0.05, xanchor='center', x=0.5),
    )
    fig.update_xaxes(tickangle=-45)

    out = OUT_DIR / 'v1102_observation.html'
    fig.write_html(out, include_plotlyjs='cdn')
    print(f'wrote {out} ({out.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
