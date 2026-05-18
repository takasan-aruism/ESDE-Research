#!/usr/bin/env python3
"""
v11.0.1.a (v1101a) Step F — グラフ HTML 統合 (v1101 同型、単一 HTML)
設計書 §6 出口 #5、留保 #L4 (alpha records 92.5% 偏り → 正規化必須)、
§5.7 確認要請 2 (top_k=10 別ビュー切り出し)。

3 セクション構成:
  Section 1 (Step C): qc_regime 分布 by (scope, metric_type)
  Section 2 (Step D): influence_candidate_count by (scope, qc_regime)
  Section 3 (Step E): causality_candidate_path 分布 by (scope, qc_regime)
+ top_k=10 attention_candidate 別ビュー (§5.7 確認要請 2)

留保 #L4 対応: records 数 raw でなく、scope 内割合に正規化して表示。

usage:
    python v1101a_step_f_graph_html.py --src main
    python v1101a_step_f_graph_html.py --src smoke
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1101A_ROOT = REPO_ROOT / 'unified/v1101a'
OUT_MAIN = V1101A_ROOT / 'outputs/main'
OUT_SMOKE = V1101A_ROOT / 'outputs/smoke'

SCOPES = ['CID', 'alpha', 'beta', 'ESDE_event', 'ESDE_step10', 'ESDE_window']
METRICS = ['atom_delta', 'rank1_flip_density', 'unit_kl_static']
PATHS = ['attention_via_salience', 'familiarity', 'integration_alpha',
         'integration_beta', 'temporal_coactivation']

PATH_COLORS = {
    'attention_via_salience': '#1f77b4',
    'familiarity': '#ff7f0e',
    'integration_alpha': '#2ca02c',
    'integration_beta': '#d62728',
    'temporal_coactivation': '#9467bd',
}
REGIME_COLORS = {
    'cognitive_dominant': '#d62728',
    'conscious_dominant': '#2ca02c',
    'undefined': '#888888',
}


def load_data(src_dir: Path) -> pd.DataFrame:
    p = src_dir / 'attention_causality_all.parquet'
    print(f'loading {p}')
    return pd.read_parquet(p)


def section_1_qc_regime(df: pd.DataFrame, fig: go.Figure, row: int):
    """qc_regime conscious 割合 by (scope, metric_type)、留保 #L4 正規化済"""
    pivot = (df.groupby(['change_scope', 'change_metric_type', 'qc_regime'])
               .size().unstack(fill_value=0))
    pivot['conscious_frac'] = (pivot['conscious_dominant'] /
                               (pivot['cognitive_dominant']
                                + pivot['conscious_dominant']))
    pivot = pivot.reset_index()
    for j, mt in enumerate(METRICS):
        sub = pivot[pivot['change_metric_type'] == mt].set_index('change_scope')
        vals = [sub.loc[s, 'conscious_frac'] if s in sub.index else np.nan
                for s in SCOPES]
        fig.add_trace(
            go.Bar(x=SCOPES, y=vals, name=mt,
                   marker_color=['#d62728' if v < 0.5 else '#2ca02c' for v in vals],
                   showlegend=False, text=[f'{v:.2f}' for v in vals],
                   textposition='outside'),
            row=row, col=j + 1)
        fig.update_yaxes(range=[0, 1], row=row, col=j + 1,
                         title='conscious frac' if j == 0 else None)
        fig.update_xaxes(title=mt, row=row, col=j + 1, tickangle=-30)


def section_2_influence(df: pd.DataFrame, fig: go.Figure, row: int):
    """influence_candidate_count cognitive vs conscious、scope 別、留保 #L4 正規化済 (per record mean)"""
    g = (df.groupby(['change_scope', 'qc_regime'])
           ['influence_candidate_count'].mean().unstack())
    for j, regime in enumerate(['cognitive_dominant', 'conscious_dominant']):
        vals = [g.loc[s, regime] if s in g.index and regime in g.columns
                else np.nan for s in SCOPES]
        fig.add_trace(
            go.Bar(x=SCOPES, y=vals, name=regime,
                   marker_color=REGIME_COLORS[regime],
                   text=[f'{v:.0f}' for v in vals], textposition='outside',
                   showlegend=(row == 2 and j < 2)),
            row=row, col=1)
    fig.update_yaxes(title='mean influence_candidate_count', row=row, col=1)
    fig.update_xaxes(tickangle=-30, row=row, col=1)

    # 倍率 (conscious / cognitive)
    if 'cognitive_dominant' in g.columns and 'conscious_dominant' in g.columns:
        ratio = (g['conscious_dominant'] / g['cognitive_dominant']).reindex(SCOPES)
        fig.add_trace(
            go.Bar(x=SCOPES, y=ratio,
                   marker_color='#9467bd',
                   text=[f'{v:.2f}×' for v in ratio], textposition='outside',
                   showlegend=False),
            row=row, col=2)
        fig.update_yaxes(title='conscious / cognitive ratio',
                         range=[0, max(2.0, ratio.max() * 1.1)], row=row, col=2)
        fig.update_xaxes(tickangle=-30, row=row, col=2)

    # seed 間 std (留保 #L3 確認)
    seed_mean = (df.groupby(['seed', 'change_scope'])
                   ['influence_candidate_count'].mean().unstack())
    std_vals = seed_mean.std().reindex(SCOPES)
    fig.add_trace(
        go.Bar(x=SCOPES, y=std_vals,
               marker_color='#8c564b',
               text=[f'{v:.1f}' for v in std_vals], textposition='outside',
               showlegend=False),
        row=row, col=3)
    fig.update_yaxes(title='std across 24 seeds', row=row, col=3)
    fig.update_xaxes(tickangle=-30, row=row, col=3)


def section_3_causality(df: pd.DataFrame, fig: go.Figure, row: int,
                         path_col: str = 'causality_candidate_path_sum'):
    """causality_candidate_path 分布 (path_col = sum or zscore、留保 #L5 対応)"""
    # Panel 1: scope 別 causality frac (stacked bar)
    ct = pd.crosstab(df['change_scope'], df[path_col], normalize='index')
    for pt in PATHS:
        vals = [ct.loc[s, pt] if s in ct.index and pt in ct.columns else 0.0
                for s in SCOPES]
        fig.add_trace(
            go.Bar(x=SCOPES, y=vals, name=pt,
                   marker_color=PATH_COLORS[pt],
                   showlegend=(row == 3),
                   text=[f'{v:.2f}' if v > 0.01 else '' for v in vals],
                   textposition='inside'),
            row=row, col=1)
    fig.update_yaxes(title='causality path fraction', range=[0, 1], row=row, col=1)
    fig.update_xaxes(tickangle=-30, row=row, col=1)

    # Panel 2: qc_regime × causality
    ct2 = pd.crosstab(df['qc_regime'], df[path_col], normalize='index')
    for pt in PATHS:
        vals = [ct2.loc[r, pt] if r in ct2.index and pt in ct2.columns else 0.0
                for r in ['cognitive_dominant', 'conscious_dominant']]
        fig.add_trace(
            go.Bar(x=['cognitive', 'conscious'], y=vals,
                   marker_color=PATH_COLORS[pt],
                   showlegend=False,
                   text=[f'{v:.2f}' if v > 0.01 else '' for v in vals],
                   textposition='inside'),
            row=row, col=2)
    fig.update_yaxes(title='causality path fraction', range=[0, 1], row=row, col=2)

    # Panel 3: seed 別 path 別占有率 (留保 #L3)
    if 'zscore' in path_col:
        # z-score 方式: integration_beta 占有率 (最大変動 path)
        seed_metric = df.groupby('seed').apply(
            lambda d: (d[path_col] == 'integration_beta').mean(),
            include_groups=False).reindex(range(24))
        ylabel = 'integration_beta frac (z-score)'
    else:
        # sum 方式: attention_via_salience 占有率 (現方式 dominant)
        seed_metric = df.groupby('seed').apply(
            lambda d: (d[path_col] == 'attention_via_salience').mean(),
            include_groups=False).reindex(range(24))
        ylabel = 'attention_via_salience frac (sum)'
    fig.add_trace(
        go.Bar(x=[f's{i}' for i in range(24)], y=seed_metric.values,
               marker_color='#1f77b4',
               text=[f'{v:.2f}' for v in seed_metric.values],
               textposition='outside', showlegend=False),
        row=row, col=3)
    fig.update_yaxes(title=ylabel, range=[0, 1], row=row, col=3)
    fig.update_xaxes(tickangle=-90, row=row, col=3)


def section_topk_view(df: pd.DataFrame, k: int = 10) -> go.Figure:
    """§5.7 確認要請 2 — top_k=10 attention_candidate per (scope, metric_type) 別ビュー."""
    fig = make_subplots(rows=len(SCOPES), cols=len(METRICS),
                        subplot_titles=[f'{s} | {m}' for s in SCOPES
                                        for m in METRICS],
                        vertical_spacing=0.04, horizontal_spacing=0.04)
    for i, scope in enumerate(SCOPES, 1):
        for j, mt in enumerate(METRICS, 1):
            sub = df[(df['change_scope'] == scope)
                     & (df['change_metric_type'] == mt)]
            if len(sub) == 0:
                continue
            # 24 seeds 全体で attention_candidate_id 別 mean change_metric_value
            agg = (sub.groupby('attention_candidate_id')['change_metric_value']
                      .mean().nlargest(k))
            fig.add_trace(
                go.Bar(x=[str(int(c)) for c in agg.index], y=agg.values,
                       marker_color='#1f77b4', showlegend=False,
                       text=[f'{v:.3f}' for v in agg.values],
                       textposition='outside'),
                row=i, col=j)
            fig.update_xaxes(title='attention_candidate_id', row=i, col=j,
                             tickangle=-45)
    fig.update_layout(height=200 * len(SCOPES), width=400 * len(METRICS),
                      title=f'Top {k} attention_candidates per (scope, metric_type)'
                            f' — §5.7 確認要請 2 別ビュー')
    return fig


def build_main_dashboard(df: pd.DataFrame) -> go.Figure:
    """4 セクション dashboard (Section 3 を sum / z-score 2 行に拡張、留保 #L5 対応)"""
    subplot_titles = (
        # Section 1
        [f'qc_regime conscious frac | {m}' for m in METRICS]
        # Section 2
        + ['Influence (cognitive vs conscious)',
           'Influence ratio (conscious / cognitive)',
           'Influence std across 24 seeds (留保 #L3)']
        # Section 3a (sum 方式、現方式)
        + ['Causality by scope [SUM] (留保 #L4 正規化)',
           'Causality by qc_regime [SUM]',
           'Per-seed attention_via_salience frac [SUM]']
        # Section 3b (z-score 方式、留保 #L5 対応)
        + ['Causality by scope [Z-SCORE] (留保 #L5 集約方式併記)',
           'Causality by qc_regime [Z-SCORE]',
           'Per-seed integration_beta frac [Z-SCORE]']
    )
    fig = make_subplots(rows=4, cols=3,
                        subplot_titles=subplot_titles,
                        vertical_spacing=0.10, horizontal_spacing=0.08,
                        specs=[[{}, {}, {}], [{}, {}, {}], [{}, {}, {}], [{}, {}, {}]])
    section_1_qc_regime(df, fig, row=1)
    section_2_influence(df, fig, row=2)
    section_3_causality(df, fig, row=3, path_col='causality_candidate_path_sum')
    section_3_causality(df, fig, row=4, path_col='causality_candidate_path_zscore')
    fig.update_layout(
        height=1800, width=1700,
        title=('v11.0.1.a (v1101a) ESDE スケール注意機構 — 段階 1 観察記録 dashboard '
               '<br><sub>留保 #L4 正規化済 + 留保 #L5 対応 (causality 2 方式 SUM/Z-SCORE 併記、'
               'v1101 留保 #33 集計単位で像が変わる同型対応)、判定なし観察記録 (絶対格言 #12)、'
               '24 seeds 1 batch (1,726,974 records)</sub>'),
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=-0.05, xanchor='center', x=0.5),
        barmode='relative',  # Section 3 stacked path frac、Section 1/2 は単一 trace のため影響なし
    )
    return fig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='main', choices=['main', 'smoke'])
    args = ap.parse_args()

    src_dir = OUT_MAIN if args.src == 'main' else OUT_SMOKE
    out_dir = V1101A_ROOT / 'outputs'

    df = load_data(src_dir)
    print(f'records: {len(df):,}, scopes: {df["change_scope"].nunique()}, '
          f'seeds: {df["seed"].nunique()}')

    # Main dashboard
    fig_main = build_main_dashboard(df)
    out_main = out_dir / 'v1101a_observation.html'
    fig_main.write_html(out_main, include_plotlyjs='cdn')
    size_main = out_main.stat().st_size
    print(f'  → wrote {out_main} ({size_main:,} bytes)')

    # Top-k view (§5.7 確認要請 2)
    fig_topk = section_topk_view(df, k=10)
    out_topk = out_dir / 'v1101a_topk_attention_candidates.html'
    fig_topk.write_html(out_topk, include_plotlyjs='cdn')
    size_topk = out_topk.stat().st_size
    print(f'  → wrote {out_topk} ({size_topk:,} bytes)')

    print('done')


if __name__ == '__main__':
    main()
