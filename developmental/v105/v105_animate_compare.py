#!/usr/bin/env python3
"""ESDE v10.4 vs v10.5 比較アニメーション

同一 seed の同一物理層に対し、
  LEFT (v10.4): Integration ダブルブッキング許容、cid 多重所属
  RIGHT (v10.5): β 1 cid → 1 β 規律

を 71×71 グリッド上に並列表示。各 window の進化を slider/再生で操作。

期待される視覚的対比:
  - v10.4: 1 cid が複数 Integration に所属 → cid 間 edge が爆発的に多い (ダブルブッキング)
  - v10.5: 1 cid → 1 β → cid 間 edge が β 単位で整理 (会計清浄)

USAGE:
  python3 v105_animate_compare.py --seed 22
  python3 v105_animate_compare.py --seed 22 --all
"""
from __future__ import annotations
import argparse, csv, sys
from pathlib import Path
from collections import defaultdict

GRID_SIDE = 71
TRACKING_WINDOWS = 50

PALETTE_HEX = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#bcbd22", "#17becf",
    "#aec7e8", "#ffbb78", "#f7b6d2",
]
RECORDED_COLOR = "rgba(150,150,150,0.6)"


def parse_id_list(s):
    if not s or (isinstance(s, str) and s.startswith("merged")):
        return set()
    out = set()
    for x in str(s).split("|"):
        x = x.strip()
        if x.isdigit():
            out.add(int(x))
    return out


def parse_nodes_repr(s):
    s = s.strip().strip("[]")
    if not s:
        return []
    s = s.replace(",", " ")
    out = []
    for x in s.split():
        try:
            out.append(int(x))
        except Exception:
            pass
    return out


def load_cid_nodes(diag_dir, seed):
    p = diag_dir / "selfread" / f"per_cid_self_seed{seed}.csv"
    cid_nodes = {}
    if not p.exists():
        return cid_nodes
    with open(p) as f:
        for r in csv.DictReader(f):
            cid_nodes[int(r["cid_id"])] = parse_nodes_repr(
                r.get("member_nodes_repr", ""))
    return cid_nodes


# ════════════════════════════════════════════════════════════════════
# v10.4 Integration replay (multi-membership)
# ════════════════════════════════════════════════════════════════════

def build_v104_snapshots(diag_dir, seed):
    """v10.4 lifecycle log を replay → 各 window 末で
    cid → set of Integration IDs (active のみ) を返す。

    Returns: list[(window, cid_to_integs_dict, integration_state_dict)]
    """
    p = diag_dir / "integration" / f"integration_lifecycle_log_seed{seed}.csv"
    if not p.exists():
        return []

    events = []
    with open(p) as f:
        for r in csv.DictReader(f):
            events.append({
                "step": int(r["step"]),
                "integration_id": int(r["integration_id"]),
                "event_type": r["event_type"],
                "member_cids": r.get("member_cids", ""),
            })
    if not events:
        return []
    events.sort(key=lambda e: e["step"])
    max_step = events[-1]["step"]

    integ_state = {}  # iid -> {"cids": set, "state": "active"/"recorded"}
    boundaries = [(w + 1) * (max_step / TRACKING_WINDOWS)
                   for w in range(TRACKING_WINDOWS)]

    snapshots = []
    ev_idx = 0
    for w, boundary in enumerate(boundaries):
        while ev_idx < len(events) and events[ev_idx]["step"] <= boundary:
            e = events[ev_idx]
            iid = e["integration_id"]
            et = e["event_type"]
            cids = parse_id_list(e["member_cids"])
            if et == "birth":
                integ_state[iid] = {"cids": set(cids), "state": "active"}
            elif et == "member_ghosted" or et == "q_inherited":
                if iid in integ_state and cids:
                    integ_state[iid]["cids"] = set(cids)
            elif et == "active_to_recorded":
                if iid in integ_state:
                    integ_state[iid]["state"] = "recorded"
            ev_idx += 1
        # snapshot
        cid_to_integs = defaultdict(set)
        for iid, st in integ_state.items():
            if st["state"] != "active":
                continue
            for c in st["cids"]:
                cid_to_integs[c].add(iid)
        snapshots.append((w, dict(cid_to_integs),
                          {iid: st["state"] for iid, st in integ_state.items()}))
    return snapshots


# ════════════════════════════════════════════════════════════════════
# v10.5 β replay (再利用、シンプル化)
# ════════════════════════════════════════════════════════════════════

def build_v105_snapshots(diag_dir, seed):
    """v10.5 alpha + beta lifecycle を replay → cid → β (single)。

    Returns: list[(window, cid_to_beta_dict, beta_state_dict)]
    """
    p_a = diag_dir / "integration" / f"alpha_lifecycle_log_seed{seed}.csv"
    p_b = diag_dir / "integration" / f"beta_lifecycle_log_seed{seed}.csv"
    if not p_a.exists() or not p_b.exists():
        return []

    events = []
    with open(p_a) as f:
        for r in csv.DictReader(f):
            events.append({"step": int(r["step"]), "kind": "alpha",
                           "alpha_id": int(r["alpha_id"]),
                           "event_type": r["event_type"],
                           "member_cids": r.get("member_cids", "")})
    with open(p_b) as f:
        for r in csv.DictReader(f):
            events.append({"step": int(r["step"]), "kind": "beta",
                           "beta_id": int(r["beta_id"]),
                           "event_type": r["event_type"],
                           "member_alphas": r.get("member_alphas", ""),
                           "member_cids": r.get("member_cids", "")})
    events.sort(key=lambda e: (e["step"], 0 if e["kind"] == "alpha" else 1))
    if not events:
        return []
    max_step = max(e["step"] for e in events)

    alpha_state = {}
    beta_state = {}
    boundaries = [(w + 1) * (max_step / TRACKING_WINDOWS)
                   for w in range(TRACKING_WINDOWS)]
    snapshots = []
    ev_idx = 0
    for w, boundary in enumerate(boundaries):
        while ev_idx < len(events) and events[ev_idx]["step"] <= boundary:
            e = events[ev_idx]
            if e["kind"] == "alpha":
                aid = e["alpha_id"]
                et = e["event_type"]
                cids = parse_id_list(e["member_cids"])
                if et == "birth":
                    alpha_state[aid] = set(cids)
                elif et == "member_ghosted":
                    alpha_state[aid] = set(cids)
                elif et == "active_to_recorded":
                    if aid in alpha_state:
                        alpha_state[aid] = set()
            elif e["kind"] == "beta":
                bid = e["beta_id"]
                et = e["event_type"]
                alphas = parse_id_list(e["member_alphas"])
                if et == "birth":
                    beta_state[bid] = {"alphas": set(alphas), "state": "active"}
                elif et in ("alpha_added", "beta_merged", "q_c_inherited"):
                    if bid in beta_state and alphas:
                        beta_state[bid]["alphas"] = set(alphas)
                elif et == "active_to_recorded":
                    if bid in beta_state:
                        beta_state[bid]["state"] = "recorded"
            ev_idx += 1
        # cid → β
        alpha_to_beta = {}
        for bid, bs in beta_state.items():
            if bs["state"] != "active":
                continue
            for aid in bs["alphas"]:
                if aid not in alpha_to_beta:
                    alpha_to_beta[aid] = bid
        cid_candidates = defaultdict(list)
        for aid, cids in alpha_state.items():
            if not cids:
                continue
            bid = alpha_to_beta.get(aid)
            if bid is None:
                continue
            for c in cids:
                cid_candidates[c].append(bid)
        cid_to_beta_now = {c: min(bids) for c, bids in cid_candidates.items()}
        snapshots.append((w, cid_to_beta_now,
                          {bid: bs["state"] for bid, bs in beta_state.items()}))
    return snapshots


# ════════════════════════════════════════════════════════════════════
# 描画 helpers
# ════════════════════════════════════════════════════════════════════

def positions_for_cid(cid_nodes_list):
    out = []
    for n in cid_nodes_list:
        r = n // GRID_SIDE
        c = n % GRID_SIDE
        out.append((c, GRID_SIDE - 1 - r))
    return out


def color_for_id(group_id, recorded_set):
    if group_id in recorded_set:
        return RECORDED_COLOR
    return PALETTE_HEX[group_id % len(PALETTE_HEX)]


def build_v104_traces(cid_to_integs, integ_state, cid_nodes):
    """v10.4: cid → 多 Integration。
    color = smallest active Integration の ID。
    edges = same-Integration cid centroids (multi-Integration により多重 edge)。
    """
    recorded = {iid for iid, st in integ_state.items() if st == "recorded"}
    cid_centroids = {}
    node_x, node_y, node_color, node_text = [], [], [], []
    star_x, star_y = [], []

    cid_primary_integ = {}
    for cid, integs in cid_to_integs.items():
        nodes = cid_nodes.get(cid, [])
        if not nodes:
            continue
        # active のみ抽出
        active_integs = [i for i in integs if i not in recorded]
        if not active_integs:
            primary = min(integs) if integs else None
        else:
            primary = min(active_integs)
        if primary is None:
            continue
        cid_primary_integ[cid] = primary

        positions = positions_for_cid(nodes)
        cx = sum(p[0] for p in positions) / len(positions)
        cy = sum(p[1] for p in positions) / len(positions)
        cid_centroids[cid] = (cx, cy, primary)

        color = color_for_id(primary, recorded)
        for px, py in positions:
            node_x.append(px); node_y.append(py)
            node_color.append(color)
            node_text.append(
                f"cid {cid} → primary I{primary}<br>"
                f"belongs to {len(integs)} Integrations: "
                f"{sorted(integs)[:5]}{'...' if len(integs) > 5 else ''}")
        for px, py in positions:
            star_x += [cx, px, None]
            star_y += [cy, py, None]

    # cohort edges: 同 Integration を共有する cid pair (= 多重 edge by integration)
    integ_to_cids = defaultdict(list)
    for cid, integs in cid_to_integs.items():
        if cid not in cid_centroids:
            continue
        for iid in integs:
            if iid in recorded:
                continue
            integ_to_cids[iid].append(cid)
    cohort_x, cohort_y = [], []
    for iid, cids in integ_to_cids.items():
        if len(cids) < 2:
            continue
        for i in range(len(cids)):
            for j in range(i + 1, len(cids)):
                if cids[i] in cid_centroids and cids[j] in cid_centroids:
                    x1, y1, _ = cid_centroids[cids[i]]
                    x2, y2, _ = cid_centroids[cids[j]]
                    cohort_x += [x1, x2, None]
                    cohort_y += [y1, y2, None]

    return {
        "star_x": star_x, "star_y": star_y,
        "cohort_x": cohort_x, "cohort_y": cohort_y,
        "node_x": node_x, "node_y": node_y,
        "node_color": node_color, "node_text": node_text,
        "n_integs_active": sum(1 for iid, st in integ_state.items() if st == "active"),
        "n_integs_recorded": sum(1 for iid, st in integ_state.items() if st == "recorded"),
        "n_cids": len(cid_centroids),
        "edge_count": len(cohort_x) // 3,
    }


def build_v105_traces(cid_to_beta, beta_state, cid_nodes):
    """v10.5: cid → 単一 β。"""
    recorded = {bid for bid, st in beta_state.items() if st == "recorded"}
    cid_centroids = {}
    node_x, node_y, node_color, node_text = [], [], [], []
    star_x, star_y = [], []

    for cid, bid in cid_to_beta.items():
        nodes = cid_nodes.get(cid, [])
        if not nodes:
            continue
        positions = positions_for_cid(nodes)
        cx = sum(p[0] for p in positions) / len(positions)
        cy = sum(p[1] for p in positions) / len(positions)
        cid_centroids[cid] = (cx, cy, bid)
        color = color_for_id(bid, recorded)
        for px, py in positions:
            node_x.append(px); node_y.append(py)
            node_color.append(color)
            node_text.append(f"cid {cid} → β{bid}")
        for px, py in positions:
            star_x += [cx, px, None]
            star_y += [cy, py, None]

    beta_to_cids = defaultdict(list)
    for cid, (cx, cy, bid) in cid_centroids.items():
        if bid in recorded:
            continue
        beta_to_cids[bid].append(cid)
    cohort_x, cohort_y = [], []
    for bid, cids in beta_to_cids.items():
        if len(cids) < 2:
            continue
        for i in range(len(cids)):
            for j in range(i + 1, len(cids)):
                x1, y1, _ = cid_centroids[cids[i]]
                x2, y2, _ = cid_centroids[cids[j]]
                cohort_x += [x1, x2, None]
                cohort_y += [y1, y2, None]

    return {
        "star_x": star_x, "star_y": star_y,
        "cohort_x": cohort_x, "cohort_y": cohort_y,
        "node_x": node_x, "node_y": node_y,
        "node_color": node_color, "node_text": node_text,
        "n_betas_active": sum(1 for bid, st in beta_state.items() if st == "active"),
        "n_betas_recorded": sum(1 for bid, st in beta_state.items() if st == "recorded"),
        "n_cids": len(cid_centroids),
        "edge_count": len(cohort_x) // 3,
    }


# ════════════════════════════════════════════════════════════════════
# Plotly figure 構築 (subplots 横並び)
# ════════════════════════════════════════════════════════════════════

def build_figure(seed_to_data, seeds_to_show, default_seed):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.5, 0.5],
        subplot_titles=("v10.4: Integration (ダブルブッキング許容)",
                        "v10.5: β-Integration (1 cid → 1 β 規律)"),
        horizontal_spacing=0.06,
    )

    if len(seeds_to_show) == 1:
        seed = seeds_to_show[0]
        v104_snaps, v105_snaps, cid_nodes = seed_to_data[seed]
        plotly_frames = []
        for w in range(min(len(v104_snaps), len(v105_snaps))):
            _, ci, ist = v104_snaps[w]
            _, cb, bst = v105_snaps[w]
            t4 = build_v104_traces(ci, ist, cid_nodes)
            t5 = build_v105_traces(cb, bst, cid_nodes)
            plotly_frames.append(go.Frame(
                data=[
                    # v10.4 (col 1): xaxis="x", yaxis="y"
                    go.Scatter(x=t4["star_x"], y=t4["star_y"], mode="lines",
                                line=dict(color="rgba(0,0,0,0.12)", width=0.6),
                                hoverinfo="skip", showlegend=False,
                                xaxis="x", yaxis="y"),
                    go.Scatter(x=t4["cohort_x"], y=t4["cohort_y"], mode="lines",
                                line=dict(color="rgba(0,0,0,0.18)", width=0.6),
                                hoverinfo="skip", showlegend=False,
                                xaxis="x", yaxis="y"),
                    go.Scatter(x=t4["node_x"], y=t4["node_y"], mode="markers",
                                marker=dict(size=9, color=t4["node_color"],
                                            line=dict(width=0.4, color="rgba(0,0,0,0.4)")),
                                text=t4["node_text"], hoverinfo="text",
                                showlegend=False,
                                xaxis="x", yaxis="y"),
                    # v10.5 (col 2): xaxis="x2", yaxis="y2"
                    go.Scatter(x=t5["star_x"], y=t5["star_y"], mode="lines",
                                line=dict(color="rgba(0,0,0,0.15)", width=0.7),
                                hoverinfo="skip", showlegend=False,
                                xaxis="x2", yaxis="y2"),
                    go.Scatter(x=t5["cohort_x"], y=t5["cohort_y"], mode="lines",
                                line=dict(color="rgba(0,0,0,0.4)", width=1.4),
                                hoverinfo="skip", showlegend=False,
                                xaxis="x2", yaxis="y2"),
                    go.Scatter(x=t5["node_x"], y=t5["node_y"], mode="markers",
                                marker=dict(size=10, color=t5["node_color"],
                                            line=dict(width=0.5, color="rgba(0,0,0,0.5)")),
                                text=t5["node_text"], hoverinfo="text",
                                showlegend=False,
                                xaxis="x2", yaxis="y2"),
                ],
                name=str(w),
                layout=go.Layout(annotations=[
                    dict(text=f"<b>seed {seed} window {w}</b>",
                         xref="paper", yref="paper",
                         x=0.5, y=1.13, xanchor="center",
                         showarrow=False, font=dict(size=15)),
                    dict(text=f"v10.4: {t4['n_cids']} cids, "
                         f"{t4['n_integs_active']}+{t4['n_integs_recorded']} I, "
                         f"{t4['edge_count']} edges",
                         xref="paper", yref="paper",
                         x=0.25, y=1.04, xanchor="center",
                         showarrow=False, font=dict(size=11)),
                    dict(text=f"v10.5: {t5['n_cids']} cids, "
                         f"{t5['n_betas_active']}+{t5['n_betas_recorded']} β, "
                         f"{t5['edge_count']} edges",
                         xref="paper", yref="paper",
                         x=0.75, y=1.04, xanchor="center",
                         showarrow=False, font=dict(size=11)),
                ]),
            ))
        # 初期 frame (last)
        last = plotly_frames[-1]
        for tr in last.data:
            fig.add_trace(tr)
        fig.frames = plotly_frames

        slider_steps = [
            dict(method="animate",
                 args=[[str(w)],
                       dict(mode="immediate",
                            frame=dict(duration=300, redraw=True),
                            transition=dict(duration=100))],
                 label=str(w))
            for w in range(len(plotly_frames))
        ]
        fig.update_layout(
            title=f"v10.4 vs v10.5 同一 seed 比較 (seed {seed})<br>"
                  "<sub>左: 1 cid が複数 Integration に重複所属 (edges 多) / "
                  "右: 1 cid → 1 β の会計清浄 (edges 整理)</sub>",
            updatemenus=[dict(type="buttons", showactive=False,
                                x=0.05, y=1.20, xanchor="left", yanchor="top",
                                buttons=[
                                    dict(label="▶ Play", method="animate",
                                         args=[None, {"frame": {"duration": 500, "redraw": True},
                                                       "fromcurrent": True}]),
                                    dict(label="⏸ Pause", method="animate",
                                         args=[[None], {"frame": {"duration": 0, "redraw": False},
                                                         "mode": "immediate"}]),
                                ])],
            sliders=[dict(active=len(plotly_frames) - 1,
                          yanchor="top", y=-0.02, xanchor="left", x=0.10,
                          currentvalue=dict(prefix="window: ",
                                              visible=True, xanchor="right"),
                          pad=dict(b=10, t=30), len=0.85, steps=slider_steps)],
            xaxis=dict(visible=False, range=[-1, GRID_SIDE], scaleanchor="y", scaleratio=1),
            yaxis=dict(visible=False, range=[-1, GRID_SIDE]),
            xaxis2=dict(visible=False, range=[-1, GRID_SIDE], scaleanchor="y2", scaleratio=1),
            yaxis2=dict(visible=False, range=[-1, GRID_SIDE]),
            height=720, width=1500,
            margin=dict(t=160, b=80),
            plot_bgcolor="rgba(248,248,248,1)",
            showlegend=False,
        )
    else:
        # case B: dropdown
        plotly_frames = []
        seed_to_keys = {}
        for seed in seeds_to_show:
            v104_snaps, v105_snaps, cid_nodes = seed_to_data[seed]
            keys = []
            for w in range(min(len(v104_snaps), len(v105_snaps))):
                _, ci, ist = v104_snaps[w]
                _, cb, bst = v105_snaps[w]
                t4 = build_v104_traces(ci, ist, cid_nodes)
                t5 = build_v105_traces(cb, bst, cid_nodes)
                key = f"seed{seed}_w{w}"
                keys.append(key)
                plotly_frames.append(go.Frame(
                    data=[
                        go.Scatter(x=t4["star_x"], y=t4["star_y"], mode="lines",
                                    line=dict(color="rgba(0,0,0,0.12)", width=0.6),
                                    hoverinfo="skip", showlegend=False,
                                    xaxis="x", yaxis="y"),
                        go.Scatter(x=t4["cohort_x"], y=t4["cohort_y"], mode="lines",
                                    line=dict(color="rgba(0,0,0,0.18)", width=0.6),
                                    hoverinfo="skip", showlegend=False,
                                    xaxis="x", yaxis="y"),
                        go.Scatter(x=t4["node_x"], y=t4["node_y"], mode="markers",
                                    marker=dict(size=9, color=t4["node_color"],
                                                line=dict(width=0.4, color="rgba(0,0,0,0.4)")),
                                    text=t4["node_text"], hoverinfo="text",
                                    showlegend=False,
                                    xaxis="x", yaxis="y"),
                        go.Scatter(x=t5["star_x"], y=t5["star_y"], mode="lines",
                                    line=dict(color="rgba(0,0,0,0.15)", width=0.7),
                                    hoverinfo="skip", showlegend=False,
                                    xaxis="x2", yaxis="y2"),
                        go.Scatter(x=t5["cohort_x"], y=t5["cohort_y"], mode="lines",
                                    line=dict(color="rgba(0,0,0,0.4)", width=1.4),
                                    hoverinfo="skip", showlegend=False,
                                    xaxis="x2", yaxis="y2"),
                        go.Scatter(x=t5["node_x"], y=t5["node_y"], mode="markers",
                                    marker=dict(size=10, color=t5["node_color"],
                                                line=dict(width=0.5, color="rgba(0,0,0,0.5)")),
                                    text=t5["node_text"], hoverinfo="text",
                                    showlegend=False,
                                    xaxis="x2", yaxis="y2"),
                    ],
                    name=key,
                    layout=go.Layout(annotations=[
                        dict(text=f"<b>seed {seed} window {w}</b>",
                             xref="paper", yref="paper",
                             x=0.5, y=1.13, xanchor="center",
                             showarrow=False, font=dict(size=15)),
                        dict(text=f"v10.4: {t4['n_cids']} cids, "
                             f"{t4['n_integs_active']}+{t4['n_integs_recorded']} I, "
                             f"{t4['edge_count']} edges",
                             xref="paper", yref="paper",
                             x=0.25, y=1.04, xanchor="center",
                             showarrow=False, font=dict(size=11)),
                        dict(text=f"v10.5: {t5['n_cids']} cids, "
                             f"{t5['n_betas_active']}+{t5['n_betas_recorded']} β, "
                             f"{t5['edge_count']} edges",
                             xref="paper", yref="paper",
                             x=0.75, y=1.04, xanchor="center",
                             showarrow=False, font=dict(size=11)),
                    ]),
                ))
            seed_to_keys[seed] = keys

        last_key = seed_to_keys[default_seed][-1]
        last = next(f for f in plotly_frames if f.name == last_key)
        for tr in last.data:
            fig.add_trace(tr)
        fig.frames = plotly_frames

        steps = []
        for seed in seeds_to_show:
            for w, key in enumerate(seed_to_keys[seed]):
                steps.append(dict(method="animate",
                                   args=[[key],
                                         dict(mode="immediate",
                                              frame=dict(duration=300, redraw=True))],
                                   label=f"s{seed}w{w}"))
        seed_dropdown = []
        for seed in seeds_to_show:
            first_key = seed_to_keys[seed][-1]
            seed_dropdown.append(dict(label=f"seed {seed}", method="animate",
                                        args=[[first_key],
                                              dict(mode="immediate",
                                                   frame=dict(duration=300, redraw=True))]))
        fig.update_layout(
            title=f"v10.4 vs v10.5 同一 seed 比較 (24 seeds、初期: seed {default_seed})<br>"
                  "<sub>左: 1 cid が複数 Integration に重複所属 / 右: 1 cid → 1 β</sub>",
            updatemenus=[
                dict(type="buttons", showactive=False,
                     x=0.05, y=1.20, xanchor="left", yanchor="top",
                     buttons=[
                         dict(label="▶ Play", method="animate",
                              args=[None, {"frame": {"duration": 500, "redraw": True},
                                            "fromcurrent": True}]),
                         dict(label="⏸ Pause", method="animate",
                              args=[[None], {"frame": {"duration": 0, "redraw": False},
                                              "mode": "immediate"}]),
                     ]),
                dict(type="dropdown", showactive=True,
                     x=0.92, y=1.20, xanchor="right", yanchor="top",
                     buttons=seed_dropdown),
            ],
            sliders=[dict(active=len(seed_to_keys[default_seed]) - 1,
                          yanchor="top", y=-0.02, xanchor="left", x=0.10,
                          currentvalue=dict(prefix="frame: ",
                                              visible=True, xanchor="right"),
                          pad=dict(b=10, t=30), len=0.85, steps=steps)],
            xaxis=dict(visible=False, range=[-1, GRID_SIDE], scaleanchor="y", scaleratio=1),
            yaxis=dict(visible=False, range=[-1, GRID_SIDE]),
            xaxis2=dict(visible=False, range=[-1, GRID_SIDE], scaleanchor="y2", scaleratio=1),
            yaxis2=dict(visible=False, range=[-1, GRID_SIDE]),
            height=720, width=1500,
            margin=dict(t=160, b=80),
            plot_bgcolor="rgba(248,248,248,1)",
            showlegend=False,
        )

    return fig


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=22)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    diag_v104 = here.parent / "v104" / "diag_v104_main"
    diag_v105 = here / "diag_v105_main_v2"

    print(f"v104: {diag_v104}")
    print(f"v105: {diag_v105}")

    seeds = list(range(24)) if args.all else [args.seed]
    seed_to_data = {}
    for s in seeds:
        cid_nodes = load_cid_nodes(diag_v105, s)
        if not cid_nodes:
            print(f"  seed {s}: no cid_nodes (per_cid_self), skip")
            continue
        v104_snaps = build_v104_snapshots(diag_v104, s)
        v105_snaps = build_v105_snapshots(diag_v105, s)
        if not v104_snaps or not v105_snaps:
            print(f"  seed {s}: missing snapshots (v104={bool(v104_snaps)}, v105={bool(v105_snaps)})")
            continue
        seed_to_data[s] = (v104_snaps, v105_snaps, cid_nodes)
        print(f"  seed {s}: v104 {len(v104_snaps)} frames, v105 {len(v105_snaps)} frames, "
              f"{len(cid_nodes)} cids")

    if not seed_to_data:
        print("no data"); sys.exit(1)

    fig = build_figure(seed_to_data,
                        seeds_to_show=list(seed_to_data.keys()),
                        default_seed=args.seed)

    if args.all:
        out = args.out or "v105_compare_all_seeds.html"
    else:
        out = args.out or f"v105_compare_seed{args.seed}.html"
    out_path = here / out
    fig.write_html(str(out_path), include_plotlyjs="cdn")
    print(f"wrote {out_path} ({out_path.stat().st_size / 1024 / 1024:.2f} MB)")


if __name__ == "__main__":
    main()
