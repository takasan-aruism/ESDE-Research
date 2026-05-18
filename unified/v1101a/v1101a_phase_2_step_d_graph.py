#!/usr/bin/env python3
"""v1101a 段階 2 Step D — グラフ HTML 拡張 (Section 5: 観察 A/B/C)

設計書 §3 出口 #5、段階 1 dashboard に Section 5 追加 (3 panel):
- Panel 1: 観察 A 候補数推移 (scope 別 mean_delta_unique)
- Panel 2: 観察 B 中心 atom 一致 frac (cog vs csc)
- Panel 3: 観察 C 予測可能性 (実測 vs shuffle baseline、Aruism 帯)

留保 #L4 正規化 + 留保 #L5 既存併記 (段階 1 Section 3a/3b) を継承し、Section 5 を追加。
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


def build_phase2_section(src_dir: Path) -> go.Figure:
    da = pd.read_parquet(src_dir / 'observation_a_candidate_count.parquet')
    db = pd.read_parquet(src_dir / 'observation_b_jaccard_proxy.parquet')
    dc = pd.read_parquet(src_dir / 'observation_c_predictability.parquet')

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=[
            'Obs A: 候補数推移 (csc-cog Δunique 平均、scope 別)',
            'Obs B: 中心 atom 隣接一致 frac (cog vs csc)',
            'Obs C: 予測可能性 vs shuffle baseline (Aruism 帯)',
        ],
        horizontal_spacing=0.08,
    )

    # Panel 1: Obs A — mean delta_unique per scope
    a_g = da.groupby('change_scope')['delta_unique'].mean().reindex(SCOPES)
    fig.add_trace(
        go.Bar(x=SCOPES, y=a_g.values,
               marker_color='#1f77b4',
               text=[f'{v:.2f}' for v in a_g.values],
               textposition='outside', showlegend=False),
        row=1, col=1)
    fig.update_yaxes(title='mean Δ(csc_post - cog_pre) unique', row=1, col=1)
    fig.update_xaxes(tickangle=-30, row=1, col=1)

    # Panel 2: Obs B — same_frac cog vs csc per scope
    b_g = db.groupby(['change_scope', 'qc_regime'])['jaccard_proxy_frac'].mean().unstack()
    for regime, color in [('cognitive_dominant', '#d62728'),
                           ('conscious_dominant', '#2ca02c')]:
        vals = [b_g.loc[s, regime] if s in b_g.index and regime in b_g.columns
                else np.nan for s in SCOPES]
        fig.add_trace(
            go.Bar(x=SCOPES, y=vals, name=regime,
                   marker_color=color,
                   text=[f'{v:.2f}' for v in vals],
                   textposition='outside', showlegend=True),
            row=1, col=2)
    fig.update_yaxes(title='mean same-center-atom frac', range=[0, 1], row=1, col=2)
    fig.update_xaxes(tickangle=-30, row=1, col=2)

    # Panel 3: Obs C — actual_predict_rate vs baseline_shuffle_mean per scope
    c_g = dc.groupby('change_scope').agg(
        actual=('actual_predict_rate', 'mean'),
        baseline=('baseline_shuffle_mean', 'mean'),
    ).reindex(SCOPES)
    fig.add_trace(
        go.Bar(x=SCOPES, y=c_g['actual'].values,
               name='actual predict rate',
               marker_color='#9467bd',
               text=[f'{v:.2f}' for v in c_g['actual']],
               textposition='outside', showlegend=True),
        row=1, col=3)
    fig.add_trace(
        go.Bar(x=SCOPES, y=c_g['baseline'].values,
               name='shuffle baseline',
               marker_color='#8c564b',
               text=[f'{v:.2f}' for v in c_g['baseline']],
               textposition='outside', showlegend=True),
        row=1, col=3)
    # 100% reference line
    fig.add_hline(y=1.0, line_dash='dash', line_color='red',
                  annotation_text='100% (Aruism 対称性: 到達するとランダム消失)',
                  row=1, col=3)
    fig.update_yaxes(title='predict rate', range=[0, 1.1], row=1, col=3)
    fig.update_xaxes(tickangle=-30, row=1, col=3)

    n_100 = (dc['actual_predict_rate'] >= 1.0).sum()
    n_total = len(dc)
    fig.update_layout(
        height=600, width=1700,
        title=(f'v11.0.1.a 段階 2 観察 A/B/C dashboard — '
               f'<sub>(a) 簡易版 cid state ledger 再生、shuffle baseline ×100 (rng=42)、'
               f'100% 到達 {n_100}/{n_total} records ({n_100/n_total*100:.0f}%) を観察事実として記録 '
               f'(箱 3 Aruism 対称性)、judgement なし (絶対格言 #12)</sub>'),
        barmode='group',
        legend=dict(orientation='h', yanchor='bottom', y=-0.25, xanchor='center', x=0.5),
    )
    return fig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='main', choices=['main', 'smoke'])
    args = ap.parse_args()
    src_dir = OUT_MAIN if args.src == 'main' else OUT_SMOKE

    fig = build_phase2_section(src_dir)
    out_path = V1101A_ROOT / 'outputs' / 'v1101a_phase_2_observations.html'
    fig.write_html(out_path, include_plotlyjs='cdn')
    print(f'wrote {out_path} ({out_path.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
