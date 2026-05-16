#!/usr/bin/env python3
"""v1101 Step F — グラフ HTML 統合出力

観察 1/2/3 を単一 HTML に統合 (v105 Plotly pattern 踏襲、include_plotlyjs="cdn")

入力 (read-only):
  unified/v1101/outputs/main/observation_1_center_cids.parquet
  unified/v1101/outputs/main/observation_1_random_cids.parquet
  unified/v1101/outputs/main/observation_1_trajectory.parquet
  unified/v1101/outputs/main/observation_1_summary.parquet
  unified/v1101/outputs/main/observation_2_events.parquet
  unified/v1101/outputs/main/observation_2_propagation.parquet
  unified/v1101/outputs/main/observation_2_summary.parquet
  unified/v1101/outputs/main/observation_3_cid_atom_distribution.parquet
  unified/v1101/outputs/main/observation_3_integration_summary.parquet
  unified/v1101/outputs/main/observation_3_esde_aggregate.parquet

出力:
  unified/v1101/outputs/v1101_observation.html
"""
from __future__ import annotations
import html as html_lib
import time
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

V1101_OUT = Path("/home/takasan/esde/ESDE-Research/unified/v1101/outputs")
MAIN_OUT = V1101_OUT / "main"
HTML_OUT = V1101_OUT / "v1101_observation.html"

ATOM_COLORS = px.colors.qualitative.Alphabet  # 26-color discrete palette
ROLE_COLOR = {"center": "#d62728", "random": "#888888"}
SHOW_SEEDS_TRAJ = [0, 12, 23]   # representative seeds for trajectory plot


def load_data() -> dict:
    d = {}
    d["centers"] = pd.read_parquet(MAIN_OUT / "observation_1_center_cids.parquet")
    d["randoms"] = pd.read_parquet(MAIN_OUT / "observation_1_random_cids.parquet")
    d["traj"] = pd.read_parquet(MAIN_OUT / "observation_1_trajectory.parquet")
    d["o1_sum"] = pd.read_parquet(MAIN_OUT / "observation_1_summary.parquet")
    d["prop"] = pd.read_parquet(MAIN_OUT / "observation_2_propagation.parquet")
    d["o2_sum"] = pd.read_parquet(MAIN_OUT / "observation_2_summary.parquet")
    d["cid_dist"] = pd.read_parquet(MAIN_OUT / "observation_3_cid_atom_distribution.parquet")
    d["intg"] = pd.read_parquet(MAIN_OUT / "observation_3_integration_summary.parquet")
    d["esde"] = pd.read_parquet(MAIN_OUT / "observation_3_esde_aggregate.parquet")
    return d


def fig_obs1_summary(o1_sum: pd.DataFrame) -> go.Figure:
    """観察 1 集計: dominant_atom_fraction の center vs random、4 解像度 × 2 条件."""
    # group by (condition_pool, resolution, role), mean dominant_atom_fraction across seeds × random cids
    g = o1_sum.groupby(["condition_pool", "resolution", "role"])["dominant_atom_fraction"].mean().reset_index()
    fig = make_subplots(rows=1, cols=2, subplot_titles=("v112 受容 cid pool 中心", "v108_standard top_k_100 中心"))
    for col_i, cond in enumerate(["v112", "v108_standard"], start=1):
        sub = g[g.condition_pool == cond]
        for role in ["center", "random"]:
            sub_role = sub[sub.role == role].sort_values("resolution")
            fig.add_trace(
                go.Bar(
                    x=sub_role["resolution"],
                    y=sub_role["dominant_atom_fraction"],
                    name=f"{role} ({cond})",
                    marker_color=ROLE_COLOR[role],
                    showlegend=(col_i == 1),
                    text=[f"{v:.2f}" for v in sub_role["dominant_atom_fraction"]],
                    textposition="outside",
                ),
                row=1, col=col_i,
            )
    fig.update_layout(
        title="観察 1 集計: 中心 cid (n_pulses_short 最大) vs ランダム比較対照、dominant_atom_fraction (24 seeds 平均)",
        barmode="group", height=420, margin=dict(t=80, b=40),
    )
    fig.update_yaxes(title="dominant_atom_fraction", range=[0, 1.1])
    fig.update_xaxes(title="解像度")
    return fig


def fig_obs1_trajectory(traj: pd.DataFrame) -> go.Figure:
    """観察 1 trajectory 例: 3 seed × 2 condition、step10 解像度、中心 vs ランダム."""
    df = traj[(traj.resolution == "step10") & (traj.seed.isin(SHOW_SEEDS_TRAJ))].copy()
    fig = make_subplots(
        rows=len(SHOW_SEEDS_TRAJ), cols=2,
        subplot_titles=[f"seed {s} — {c}" for s in SHOW_SEEDS_TRAJ for c in ["v112", "v108_standard"]],
        shared_xaxes=False, vertical_spacing=0.08,
    )
    # Build atom -> color map (limit to atoms present in this subset)
    unique_atoms = sorted(df["rank_1_atom"].dropna().unique().tolist())
    atom_to_color = {a: ATOM_COLORS[i % len(ATOM_COLORS)] for i, a in enumerate(unique_atoms)}

    seen_legend: set[str] = set()
    for row_i, s in enumerate(SHOW_SEEDS_TRAJ, start=1):
        for col_i, cond in enumerate(["v112", "v108_standard"], start=1):
            sub = df[(df.seed == s) & (df.condition_pool == cond)]
            for role in ["random", "center"]:  # random first → center on top
                sub_role = sub[sub.role == role]
                if sub_role.empty:
                    continue
                cids = sub_role["cognitive_id"].unique()
                for cid in cids:
                    g = sub_role[sub_role["cognitive_id"] == cid].sort_values("t")
                    line_color = ROLE_COLOR[role]
                    line_width = 2.2 if role == "center" else 0.9
                    line_opacity = 0.95 if role == "center" else 0.45
                    fig.add_trace(
                        go.Scatter(
                            x=g["t"], y=g["rank_1_sim"],
                            mode="lines",
                            line=dict(color=line_color, width=line_width),
                            opacity=line_opacity,
                            name=f"{role}",
                            legendgroup=role,
                            showlegend=(role not in seen_legend),
                            hovertemplate=(f"role={role}<br>cid={cid}<br>"
                                           "t=%{x}<br>rank_1_sim=%{y:.3f}<br>"
                                           "atom=%{customdata}<extra></extra>"),
                            customdata=g["rank_1_atom"],
                        ),
                        row=row_i, col=col_i,
                    )
                    seen_legend.add(role)
    fig.update_layout(
        title="観察 1 trajectory 例 (step10 解像度): 中心 cid (赤、太線) vs ランダム比較対照 (灰、細線)",
        height=720, margin=dict(t=80, b=40),
        hovermode="closest",
    )
    fig.update_xaxes(title="t (step)")
    fig.update_yaxes(title="rank_1_sim", range=[-0.1, 0.8])
    return fig


def fig_obs2_heatmap(o2_sum: pd.DataFrame) -> go.Figure:
    """観察 2 ヒートマップ: Δt × atom × center_match_rate."""
    # atom ordered by max center_match_rate over Δt
    peaks = o2_sum.groupby("atom_intro")["center_match_rate"].max().sort_values(ascending=True)
    atom_order = peaks.index.tolist()
    pivot = o2_sum.pivot(index="atom_intro", columns="delta_t", values="center_match_rate").reindex(atom_order)
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale="Hot", zmin=0, zmax=1.0,
        colorbar=dict(title="center_match_rate"),
        hovertemplate="atom=%{y}<br>Δt=%{x}<br>center_match_rate=%{z:.3f}<extra></extra>",
    ))
    fig.update_layout(
        title="観察 2 取り込み点中心の波及: 中心 cid が atom_intro を rank_1 として表現する比率 (heatmap, 10,500 events × 21 Δt)",
        xaxis_title="Δt (step)", yaxis_title="atom_intro (取り込み atom)",
        height=620, margin=dict(t=80, b=40, l=120),
    )
    return fig


def fig_obs2_top_lines(o2_sum: pd.DataFrame) -> go.Figure:
    """観察 2: 4 主要 atom (PER.sound / PRP.bright / TIM.appear / WLD.artless) の波及曲線."""
    top_atoms = ["PER.sound", "PRP.bright", "TIM.appear", "WLD.artless"]
    fig = make_subplots(rows=1, cols=2,
                         subplot_titles=("center_match_rate (中心 cid 自身が atom_intro と一致)",
                                         "match_fraction (周辺 cid 平均一致率)"))
    palette = px.colors.qualitative.Bold
    for i, a in enumerate(top_atoms):
        sub = o2_sum[o2_sum.atom_intro == a].sort_values("delta_t")
        color = palette[i % len(palette)]
        fig.add_trace(
            go.Scatter(x=sub["delta_t"], y=sub["center_match_rate"],
                       mode="lines+markers", name=a, line=dict(color=color), legendgroup=a),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(x=sub["delta_t"], y=sub["match_fraction_mean"],
                       mode="lines+markers", name=a, line=dict(color=color),
                       legendgroup=a, showlegend=False),
            row=1, col=2,
        )
    fig.update_layout(
        title="観察 2: 中心 cid 支配可能 4 atom の波及プロファイル (Δt 軸、21 points)",
        height=420, margin=dict(t=80, b=40),
    )
    for c in (1, 2):
        fig.update_xaxes(title="Δt (step)", row=1, col=c)
    fig.update_yaxes(title="比率", row=1, col=1, range=[0, 1])
    fig.update_yaxes(title="比率", row=1, col=2, range=[0, 0.4])
    return fig


def fig_obs3_reversal(cid_dist: pd.DataFrame, intg: pd.DataFrame, esde: pd.DataFrame) -> go.Figure:
    """観察 3 核心発見: 6 観察単位の top atom (横並び bar)."""
    # 6 panels: CID-static, β, α, ESDE-event, ESDE-step10, ESDE-window
    panels = [
        ("CID 単位 (sim_mean)", cid_dist.nlargest(10, "sim_mean")[["atom", "sim_mean"]].rename(columns={"sim_mean": "value"}), "sim_mean"),
        ("Integration β top_atom", intg[intg.unit == "beta"].nlargest(10, "n_appearances_as_top")[["atom", "n_appearances_as_top"]].rename(columns={"n_appearances_as_top": "value"}), "n_βs as top"),
        ("Integration α dominant_atom", intg[intg.unit == "alpha_stratified"].nlargest(10, "n_appearances_as_top")[["atom", "n_appearances_as_top"]].rename(columns={"n_appearances_as_top": "value"}), "n pattern_classes as dominant"),
        ("ESDE event rank_1", esde[esde.resolution == "event"].nlargest(10, "n_records_event")[["atom", "ratio_within_res"]].rename(columns={"ratio_within_res": "value"}), "ratio"),
        ("ESDE step10 rank_1", esde[esde.resolution == "step10"].nlargest(10, "n_records_event")[["atom", "ratio_within_res"]].rename(columns={"ratio_within_res": "value"}), "ratio"),
        ("ESDE window rank_1", esde[esde.resolution == "window"].nlargest(10, "n_records_event")[["atom", "ratio_within_res"]].rename(columns={"ratio_within_res": "value"}), "ratio"),
    ]
    fig = make_subplots(rows=2, cols=3, subplot_titles=[p[0] for p in panels],
                        vertical_spacing=0.15, horizontal_spacing=0.12)
    palette = px.colors.qualitative.Set3
    for i, (title, df_p, xtitle) in enumerate(panels):
        r, c = (i // 3) + 1, (i % 3) + 1
        df_p = df_p.iloc[::-1].reset_index(drop=True)  # ascending for horizontal bar
        colors = [palette[j % len(palette)] for j in range(len(df_p))]
        fig.add_trace(
            go.Bar(
                x=df_p["value"], y=df_p["atom"], orientation="h",
                marker_color=colors,
                text=[f"{v:.3f}" if isinstance(v, float) else str(v) for v in df_p["value"]],
                textposition="auto",
                hovertemplate=f"{title}<br>atom=%{{y}}<br>value=%{{x}}<extra></extra>",
                showlegend=False,
            ),
            row=r, col=c,
        )
        fig.update_xaxes(title=xtitle, row=r, col=c)

    fig.update_layout(
        title="観察 3 核心発見: 観察単位による dominant atom の構造的反転 (top 10 atoms × 6 観察単位)",
        height=720, margin=dict(t=80, b=40),
    )
    return fig


def build_html(figs: dict, summaries: dict) -> str:
    """各 figure を section 化して 1 HTML に統合."""
    head = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>v11.0.1 (v1101) Atom 的隆盛の統計的観察 Dashboard</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         max-width: 1280px; margin: 24px auto; padding: 0 16px; color: #222; }
  h1 { border-bottom: 2px solid #333; padding-bottom: 8px; }
  h2 { margin-top: 40px; border-bottom: 1px solid #aaa; padding-bottom: 4px; }
  .summary { background: #f4f4f4; padding: 12px 16px; border-left: 4px solid #1f77b4; margin: 12px 0; }
  .key-finding { background: #fff3cd; padding: 12px 16px; border-left: 4px solid #d62728; margin: 12px 0; }
  .meta { color: #666; font-size: 0.9em; }
  table { border-collapse: collapse; margin: 8px 0; }
  th, td { border: 1px solid #ccc; padding: 4px 8px; font-size: 0.92em; }
  th { background: #eee; }
</style></head><body>
"""
    body_intro = """
<h1>v11.0.1 (v1101) Atom 的隆盛の統計的観察 Dashboard</h1>
<p class="meta">Code A、2026-05-17 / Taka 3 日長考の結論主題「Atom 的隆盛の統計的観察」を観察 1 + 観察 2 + 観察 3 の 3 視点で可視化</p>
<div class="summary">
<b>主題</b>: v10.8 以降「Atom を取り込む」枠組みで「取り込んだ後どうなるか」が観察フレームとして空白だった状況を、観察対象を「Atom らしきものの ESDE 内部の隆盛」(状態、確定的でない濃度) に転換することで埋める。
<br><br>
<b>3 観察視点</b>:
<ul>
<li><b>観察 1</b>「一点を捉える」 — 中心 cid (n_pulses_short 最大) の atom 状態時系列、ランダム比較対照付き</li>
<li><b>観察 2</b>「取り込み点中心の波及」 — v10.12 受容 cid pool 420 中心 + 周辺 cid (同 seed 全 ~228) の Δt=±100 step time-locked 観察</li>
<li><b>観察 3</b>「補助平均統計 3 単位」 — CID / Integration / ESDE の atom 隆盛集約 (核心発見: 観察単位による dominant atom 反転)</li>
</ul>
<b>データ</b>: v10.6 既存出力 (cid_atom_sim_matrix + 4 解像度 trajectory + beta/alpha_atom_aggregate × 24 seeds) + v10.8/v10.12 atom_introduction_events + propagation_profile を流用、新規 main run なし、v10.x outputs read-only。
</div>
"""

    section_obs1 = """
<h2>観察 1: 一点を捉える</h2>
<div class="key-finding">
<b>観察 1 主要発見</b>:
<ol>
<li>v108_standard 中心 cid の dominant_atom が <code>WLD.artless</code> で 24 seeds 中 <b>21 seed 一致</b> (87.5%)、v112 は PER.sound 10 / TIM.moment 5 / TIM.appear 4 に分散</li>
<li>v108_standard 中心 cid の dominant_atom_fraction <b>0.92-1.00</b> (単 atom ロック) vs v112 中心 cid <b>0.47-0.81</b> (複数 atom 揺れ)</li>
<li>両条件で中心 cid の trajectory row 数 < ランダムの約 1/3-1/4</li>
<li>window 解像度のみ v112 中心 cid の atom_change_rate <b>0.156 < ランダム 0.297</b></li>
</ol>
</div>
"""
    section_obs2 = """
<h2>観察 2: 取り込み点中心の波及</h2>
<div class="key-finding">
<b>観察 2 主要発見</b>:
<ol>
<li>25 取り込み atom 中 <b>4 atom のみ中心 cid を支配可</b>: PER.sound (peak 84.8% at Δt=+20)、PRP.bright (peak 49.3% at Δt=-90)、TIM.appear (peak 14.8% at Δt=-100)、WLD.artless (peak 8.8% at Δt=+70)、残り <b>21 atom は center_match_rate = 0%</b></li>
<li>周辺 cid の atom 分布は取り込み atom に依存せず <b>PER.sound + WLD.artless が常時 ~60% 占有</b> (per (event, Δt=0) で各 8.4 / 8.0 cid)</li>
<li>atom_entropy_mean が Δt 方向で <b>単調減少</b> 2.138 → 2.070 bits (取り込み後集中化)</li>
<li>PER.sound 波及プロファイル特異: 中心 cid 一致率 Δt=-10 で 32.6% → Δt=+20 で 84.8% peak → 減衰</li>
</ol>
</div>
"""
    section_obs3 = """
<h2>観察 3: 補助平均統計 3 単位 — 観察単位による dominant atom 反転 (核心発見)</h2>
<div class="key-finding">
<b>観察 3 核心発見</b> (齟齬 L candidate): 同じ ESDE 系で観察単位を変えるだけで <b>dominant atom が 5 つに分裂</b>:
<table>
<tr><th>観察単位</th><th>1 位 atom</th><th>値</th></tr>
<tr><td>CID 単位 (cid_atom_sim_matrix sim_mean)</td><td>CHG.begin</td><td>0.536</td></tr>
<tr><td>Integration β top_atom</td><td>FND.logic</td><td>160 βs (79%)</td></tr>
<tr><td>Integration α pattern_class dominant</td><td>TIM.moment</td><td>114 (79%)</td></tr>
<tr><td>ESDE event resolution rank_1</td><td>WLD.artless + PER.sound</td><td>26.2% + 25.9%</td></tr>
<tr><td>ESDE step10 resolution rank_1</td><td>PER.sound</td><td>28.3%</td></tr>
<tr><td>ESDE window resolution rank_1</td><td>TIM.moment</td><td>34.2%</td></tr>
</table>
Taka 整理「平均化の罠」(絶対格言 #4) + 「Integration 内 cid に同方向を強制しない」の直接的観察的根拠、v10.13.a 留保 #33 (集計単位による方向反転) の Atom レベル一般化。
</div>
"""
    section_close = """
<h2>規律遵守 + 留保</h2>
<div class="summary">
Code A は本観察事実を判定しない (絶対格言 #12 Aruism 判定回避)。観察 1/2/3 の解釈統合は Web Claude Phase Result 領域。新規留保: #41 candidate (Integration member_cids 個別 list 未 persistence)、#42 candidate (観察単位による dominant atom 反転)。物理層 frozen 絶対 (v10.6 / v10.8 / v10.12 main outputs 不変、書き込み unified/v1101/ 配下のみ)。
</div>
<p class="meta">入力データ: unified/v1101/outputs/main/observation_{1,2,3}_*.parquet (合計 8 ファイル、7 MB)</p>
</body></html>
"""
    parts = [head, body_intro]
    # First fig with full plotly.js via CDN; subsequent without
    parts.append(section_obs1)
    parts.append(figs["o1_summary"].to_html(full_html=False, include_plotlyjs="cdn"))
    parts.append(figs["o1_traj"].to_html(full_html=False, include_plotlyjs=False))
    parts.append(section_obs2)
    parts.append(figs["o2_heat"].to_html(full_html=False, include_plotlyjs=False))
    parts.append(figs["o2_lines"].to_html(full_html=False, include_plotlyjs=False))
    parts.append(section_obs3)
    parts.append(figs["o3_reversal"].to_html(full_html=False, include_plotlyjs=False))
    parts.append(section_close)
    return "\n".join(parts)


def main():
    V1101_OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    print("[F-1] load observation 1/2/3 data")
    d = load_data()

    print("[F-2] build observation 1 figures (summary + trajectory)")
    f_o1_sum = fig_obs1_summary(d["o1_sum"])
    f_o1_traj = fig_obs1_trajectory(d["traj"])

    print("[F-3] build observation 2 figures (heatmap + top lines)")
    f_o2_heat = fig_obs2_heatmap(d["o2_sum"])
    f_o2_lines = fig_obs2_top_lines(d["o2_sum"])

    print("[F-4] build observation 3 figure (reversal panels)")
    f_o3_reversal = fig_obs3_reversal(d["cid_dist"], d["intg"], d["esde"])

    print("[F-5] assemble single HTML")
    figs = {
        "o1_summary": f_o1_sum,
        "o1_traj": f_o1_traj,
        "o2_heat": f_o2_heat,
        "o2_lines": f_o2_lines,
        "o3_reversal": f_o3_reversal,
    }
    summaries = {}
    html_text = build_html(figs, summaries)
    HTML_OUT.write_text(html_text, encoding="utf-8")

    dt = time.time() - t0
    size_kb = HTML_OUT.stat().st_size / 1024
    print(f"Step F done in {dt:.1f}s, output: {HTML_OUT} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
