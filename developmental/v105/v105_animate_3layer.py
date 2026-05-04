#!/usr/bin/env python3
"""ESDE v10.5 — 物理 / v10.4 / v10.5 3-row 比較アニメーション

71×71 トーラスグリッド × 同一 seed × 同一 window slider で:
  上段: 物理層 (alive_l リンク網、cid 表示なし、~2700 links/window)
  中段: v10.4 認知層 (Integration ダブルブッキング)
  下段: v10.5 認知層 (β クリーン)

「下層は嵐、中層はもつれ、上層は秩序」という階層を一望。

USAGE:
  python3 v105_animate_3layer.py --seed 22
  python3 v105_animate_3layer.py --seed 22 --all
"""
from __future__ import annotations
import argparse, csv, sys, re
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

LINK_ID_RE = re.compile(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)")


def node_to_xy(n):
    r = n // GRID_SIDE
    c = n % GRID_SIDE
    return c, GRID_SIDE - 1 - r


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


def positions_for_cid(cid_nodes_list):
    return [node_to_xy(n) for n in cid_nodes_list]


def color_for_id(group_id, recorded_set):
    if group_id in recorded_set:
        return RECORDED_COLOR
    return PALETTE_HEX[group_id % len(PALETTE_HEX)]


# ════════════════════════════════════════════════════════════════════
# 物理層: link_snapshot_log から各 window 末の alive_l を取得
# ════════════════════════════════════════════════════════════════════

def load_alive_links_per_window(diag_dir, seed):
    """Returns: list[(window_idx_0based, list[(n1, n2)])]
    snapshot は window 20-69 (50 frames) を window 0-49 にリマップ。"""
    p = diag_dir / "persistence" / f"link_snapshot_log_seed{seed}.csv"
    if not p.exists():
        return []
    by_window = defaultdict(list)
    with open(p) as f:
        for r in csv.DictReader(f):
            w = int(r["window"])
            m = LINK_ID_RE.match(r["link_id"])
            if not m:
                continue
            n1, n2 = int(m.group(1)), int(m.group(2))
            by_window[w].append((n1, n2))
    sorted_ws = sorted(by_window.keys())
    return [(i, by_window[w]) for i, w in enumerate(sorted_ws)]


# ════════════════════════════════════════════════════════════════════
# v10.4 / v10.5 snapshot reconstruction (再利用、コンパクト)
# ════════════════════════════════════════════════════════════════════

def build_v104_snapshots(diag_dir, seed):
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
    integ_state = {}
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
            elif et in ("member_ghosted", "q_inherited") and iid in integ_state and cids:
                integ_state[iid]["cids"] = set(cids)
            elif et == "active_to_recorded" and iid in integ_state:
                integ_state[iid]["state"] = "recorded"
            ev_idx += 1
        cid_to_integs = defaultdict(set)
        for iid, st in integ_state.items():
            if st["state"] != "active":
                continue
            for c in st["cids"]:
                cid_to_integs[c].add(iid)
        snapshots.append((w, dict(cid_to_integs),
                          {iid: st["state"] for iid, st in integ_state.items()}))
    return snapshots


def build_v105_snapshots(diag_dir, seed):
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
                if et in ("birth", "member_ghosted"):
                    alpha_state[aid] = set(cids)
                elif et == "active_to_recorded" and aid in alpha_state:
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
                elif et == "active_to_recorded" and bid in beta_state:
                    beta_state[bid]["state"] = "recorded"
            ev_idx += 1
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
# trace builders
# ════════════════════════════════════════════════════════════════════

def build_physics_traces(alive_links):
    """物理層: alive_l のリンク群を line segments で。"""
    edge_x, edge_y = [], []
    for n1, n2 in alive_links:
        x1, y1 = node_to_xy(n1)
        x2, y2 = node_to_xy(n2)
        edge_x += [x1, x2, None]
        edge_y += [y1, y2, None]
    return {"edge_x": edge_x, "edge_y": edge_y, "n_links": len(alive_links)}


def build_v104_traces(cid_to_integs, integ_state, cid_nodes):
    recorded = {iid for iid, st in integ_state.items() if st == "recorded"}
    cid_centroids = {}
    node_x, node_y, node_color, node_text = [], [], [], []
    star_x, star_y = [], []
    for cid, integs in cid_to_integs.items():
        nodes = cid_nodes.get(cid, [])
        if not nodes:
            continue
        active_integs = [i for i in integs if i not in recorded]
        primary = min(active_integs) if active_integs else (
            min(integs) if integs else None)
        if primary is None:
            continue
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
                f"in {len(integs)} Integrations")
        for px, py in positions:
            star_x += [cx, px, None]
            star_y += [cy, py, None]
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
    return {"star_x": star_x, "star_y": star_y,
            "cohort_x": cohort_x, "cohort_y": cohort_y,
            "node_x": node_x, "node_y": node_y,
            "node_color": node_color, "node_text": node_text,
            "n_integs_active": sum(1 for st in integ_state.values() if st == "active"),
            "n_cids": len(cid_centroids), "edge_count": len(cohort_x) // 3}


def build_v105_traces(cid_to_beta, beta_state, cid_nodes):
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
    return {"star_x": star_x, "star_y": star_y,
            "cohort_x": cohort_x, "cohort_y": cohort_y,
            "node_x": node_x, "node_y": node_y,
            "node_color": node_color, "node_text": node_text,
            "n_betas_active": sum(1 for st in beta_state.values() if st == "active"),
            "n_cids": len(cid_centroids), "edge_count": len(cohort_x) // 3}


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
# Plotly figure: 3 rows × 1 col
# ════════════════════════════════════════════════════════════════════

def build_figure(seed_to_data, seeds_to_show, default_seed):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=3, cols=1,
        row_heights=[0.34, 0.33, 0.33],
        subplot_titles=(
            "物理層: alive_l (~2700 links/window 入れ替わり)",
            "v10.4 認知層: Integration (cid 多重所属)",
            "v10.5 認知層: β-Integration (1 cid → 1 β)"
        ),
        vertical_spacing=0.06,
    )

    def make_frame_data(physics_alive, ci, ist, cb, bst, cid_nodes):
        tp = build_physics_traces(physics_alive)
        t4 = build_v104_traces(ci, ist, cid_nodes)
        t5 = build_v105_traces(cb, bst, cid_nodes)
        return [
            # row 1: physics
            go.Scatter(x=tp["edge_x"], y=tp["edge_y"], mode="lines",
                        line=dict(color="rgba(0,80,200,0.3)", width=0.5),
                        hoverinfo="skip", showlegend=False,
                        xaxis="x", yaxis="y"),
            # row 2: v10.4
            go.Scatter(x=t4["star_x"], y=t4["star_y"], mode="lines",
                        line=dict(color="rgba(0,0,0,0.12)", width=0.5),
                        hoverinfo="skip", showlegend=False,
                        xaxis="x2", yaxis="y2"),
            go.Scatter(x=t4["cohort_x"], y=t4["cohort_y"], mode="lines",
                        line=dict(color="rgba(0,0,0,0.18)", width=0.5),
                        hoverinfo="skip", showlegend=False,
                        xaxis="x2", yaxis="y2"),
            go.Scatter(x=t4["node_x"], y=t4["node_y"], mode="markers",
                        marker=dict(size=7, color=t4["node_color"],
                                    line=dict(width=0.4, color="rgba(0,0,0,0.4)")),
                        text=t4["node_text"], hoverinfo="text",
                        showlegend=False,
                        xaxis="x2", yaxis="y2"),
            # row 3: v10.5
            go.Scatter(x=t5["star_x"], y=t5["star_y"], mode="lines",
                        line=dict(color="rgba(0,0,0,0.15)", width=0.6),
                        hoverinfo="skip", showlegend=False,
                        xaxis="x3", yaxis="y3"),
            go.Scatter(x=t5["cohort_x"], y=t5["cohort_y"], mode="lines",
                        line=dict(color="rgba(0,0,0,0.4)", width=1.2),
                        hoverinfo="skip", showlegend=False,
                        xaxis="x3", yaxis="y3"),
            go.Scatter(x=t5["node_x"], y=t5["node_y"], mode="markers",
                        marker=dict(size=8, color=t5["node_color"],
                                    line=dict(width=0.5, color="rgba(0,0,0,0.5)")),
                        text=t5["node_text"], hoverinfo="text",
                        showlegend=False,
                        xaxis="x3", yaxis="y3"),
        ], tp, t4, t5

    if len(seeds_to_show) == 1:
        seed = seeds_to_show[0]
        physics_snaps, v104_snaps, v105_snaps, cid_nodes = seed_to_data[seed]
        plotly_frames = []
        n_frames = min(len(physics_snaps), len(v104_snaps), len(v105_snaps))
        for w in range(n_frames):
            _, physics_alive = physics_snaps[w]
            _, ci, ist = v104_snaps[w]
            _, cb, bst = v105_snaps[w]
            data, tp, t4, t5 = make_frame_data(
                physics_alive, ci, ist, cb, bst, cid_nodes)
            plotly_frames.append(go.Frame(
                data=data, name=str(w),
                layout=go.Layout(annotations=[
                    dict(text=f"<b>seed {seed} window {w}</b>",
                         xref="paper", yref="paper",
                         x=0.5, y=1.04, xanchor="center",
                         showarrow=False, font=dict(size=15)),
                    dict(text=f"alive_l = {tp['n_links']}",
                         xref="paper", yref="paper",
                         x=0.99, y=0.985, xanchor="right",
                         showarrow=False, font=dict(size=10)),
                    dict(text=f"{t4['n_cids']} cids, "
                         f"{t4['n_integs_active']} active I, "
                         f"{t4['edge_count']} edges",
                         xref="paper", yref="paper",
                         x=0.99, y=0.65, xanchor="right",
                         showarrow=False, font=dict(size=10)),
                    dict(text=f"{t5['n_cids']} cids, "
                         f"{t5['n_betas_active']} active β, "
                         f"{t5['edge_count']} edges",
                         xref="paper", yref="paper",
                         x=0.99, y=0.32, xanchor="right",
                         showarrow=False, font=dict(size=10)),
                ]),
            ))
        last = plotly_frames[-1]
        for tr in last.data:
            fig.add_trace(tr)
        fig.frames = plotly_frames
        slider_steps = [
            dict(method="animate",
                 args=[[str(w)],
                       dict(mode="immediate",
                            frame=dict(duration=300, redraw=True))],
                 label=str(w))
            for w in range(n_frames)]
        fig.update_layout(
            title=f"v10.5 — 物理 / v10.4 / v10.5 階層比較 (seed {seed})<br>"
                  "<sub>同一物理から異なる認知層が抽出される様子。"
                  "上: 嵐、中: もつれ、下: 秩序</sub>",
            updatemenus=[dict(type="buttons", showactive=False,
                                x=0.05, y=1.07, xanchor="left", yanchor="top",
                                buttons=[
                                    dict(label="▶ Play", method="animate",
                                         args=[None, {"frame": {"duration": 500, "redraw": True},
                                                       "fromcurrent": True}]),
                                    dict(label="⏸ Pause", method="animate",
                                         args=[[None], {"frame": {"duration": 0, "redraw": False},
                                                         "mode": "immediate"}]),
                                ])],
            sliders=[dict(active=n_frames - 1,
                          yanchor="top", y=-0.02, xanchor="left", x=0.10,
                          currentvalue=dict(prefix="window: ", visible=True,
                                              xanchor="right"),
                          pad=dict(b=10, t=30), len=0.85, steps=slider_steps)],
            xaxis=dict(visible=False, range=[-1, GRID_SIDE], scaleanchor="y", scaleratio=1),
            yaxis=dict(visible=False, range=[-1, GRID_SIDE]),
            xaxis2=dict(visible=False, range=[-1, GRID_SIDE], scaleanchor="y2", scaleratio=1),
            yaxis2=dict(visible=False, range=[-1, GRID_SIDE]),
            xaxis3=dict(visible=False, range=[-1, GRID_SIDE], scaleanchor="y3", scaleratio=1),
            yaxis3=dict(visible=False, range=[-1, GRID_SIDE]),
            height=1500, width=900,
            margin=dict(t=100, b=80),
            plot_bgcolor="rgba(248,248,248,1)",
            showlegend=False,
        )
    else:
        plotly_frames = []
        seed_to_keys = {}
        for seed in seeds_to_show:
            physics_snaps, v104_snaps, v105_snaps, cid_nodes = seed_to_data[seed]
            keys = []
            n_frames = min(len(physics_snaps), len(v104_snaps), len(v105_snaps))
            for w in range(n_frames):
                _, physics_alive = physics_snaps[w]
                _, ci, ist = v104_snaps[w]
                _, cb, bst = v105_snaps[w]
                data, tp, t4, t5 = make_frame_data(
                    physics_alive, ci, ist, cb, bst, cid_nodes)
                key = f"seed{seed}_w{w}"
                keys.append(key)
                plotly_frames.append(go.Frame(
                    data=data, name=key,
                    layout=go.Layout(annotations=[
                        dict(text=f"<b>seed {seed} window {w}</b>",
                             xref="paper", yref="paper",
                             x=0.5, y=1.04, xanchor="center",
                             showarrow=False, font=dict(size=15)),
                        dict(text=f"alive_l = {tp['n_links']}",
                             xref="paper", yref="paper",
                             x=0.99, y=0.985, xanchor="right",
                             showarrow=False, font=dict(size=10)),
                        dict(text=f"{t4['n_cids']} cids, "
                             f"{t4['n_integs_active']} active I, "
                             f"{t4['edge_count']} edges",
                             xref="paper", yref="paper",
                             x=0.99, y=0.65, xanchor="right",
                             showarrow=False, font=dict(size=10)),
                        dict(text=f"{t5['n_cids']} cids, "
                             f"{t5['n_betas_active']} active β, "
                             f"{t5['edge_count']} edges",
                             xref="paper", yref="paper",
                             x=0.99, y=0.32, xanchor="right",
                             showarrow=False, font=dict(size=10)),
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
            title=f"v10.5 — 物理 / v10.4 / v10.5 階層比較 (24 seeds、初期: seed {default_seed})<br>"
                  "<sub>同一物理から異なる認知層が抽出される様子</sub>",
            updatemenus=[
                dict(type="buttons", showactive=False,
                     x=0.05, y=1.07, xanchor="left", yanchor="top",
                     buttons=[
                         dict(label="▶ Play", method="animate",
                              args=[None, {"frame": {"duration": 500, "redraw": True},
                                            "fromcurrent": True}]),
                         dict(label="⏸ Pause", method="animate",
                              args=[[None], {"frame": {"duration": 0, "redraw": False},
                                              "mode": "immediate"}]),
                     ]),
                dict(type="dropdown", showactive=True,
                     x=0.92, y=1.07, xanchor="right", yanchor="top",
                     buttons=seed_dropdown),
            ],
            sliders=[dict(active=len(seed_to_keys[default_seed]) - 1,
                          yanchor="top", y=-0.02, xanchor="left", x=0.10,
                          currentvalue=dict(prefix="frame: ", visible=True,
                                              xanchor="right"),
                          pad=dict(b=10, t=30), len=0.85, steps=steps)],
            xaxis=dict(visible=False, range=[-1, GRID_SIDE], scaleanchor="y", scaleratio=1),
            yaxis=dict(visible=False, range=[-1, GRID_SIDE]),
            xaxis2=dict(visible=False, range=[-1, GRID_SIDE], scaleanchor="y2", scaleratio=1),
            yaxis2=dict(visible=False, range=[-1, GRID_SIDE]),
            xaxis3=dict(visible=False, range=[-1, GRID_SIDE], scaleanchor="y3", scaleratio=1),
            yaxis3=dict(visible=False, range=[-1, GRID_SIDE]),
            height=1500, width=900,
            margin=dict(t=100, b=80),
            plot_bgcolor="rgba(248,248,248,1)",
            showlegend=False,
        )

    return fig


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=22)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument("--frame-skip", type=int, default=1,
                        help="N frames ごとに 1 サンプル (1=全 50 frames、2=25 frames)")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    diag_v104 = here.parent / "v104" / "diag_v104_main"
    diag_v105 = here / "diag_v105_main_v2"

    seeds = list(range(24)) if args.all else [args.seed]
    seed_to_data = {}
    skip = max(1, args.frame_skip)
    for s in seeds:
        cid_nodes = load_cid_nodes(diag_v105, s)
        if not cid_nodes:
            print(f"  seed {s}: no cid_nodes, skip"); continue
        physics = load_alive_links_per_window(diag_v105, s)
        v104 = build_v104_snapshots(diag_v104, s)
        v105 = build_v105_snapshots(diag_v105, s)
        if not (physics and v104 and v105):
            print(f"  seed {s}: missing data, skip"); continue
        # frame skip 適用 (HTML サイズ削減)
        if skip > 1:
            physics = physics[::skip]
            v104 = v104[::skip]
            v105 = v105[::skip]
        seed_to_data[s] = (physics, v104, v105, cid_nodes)
        print(f"  seed {s}: physics {len(physics)} frames "
              f"({sum(len(a) for _, a in physics)} total links), "
              f"v104 {len(v104)} frames, v105 {len(v105)} frames")

    if not seed_to_data:
        print("no data"); sys.exit(1)
    fig = build_figure(seed_to_data,
                        seeds_to_show=list(seed_to_data.keys()),
                        default_seed=args.seed)
    if args.all:
        out = args.out or "v105_3layer_all_seeds.html"
    else:
        out = args.out or f"v105_3layer_seed{args.seed}.html"
    out_path = here / out
    fig.write_html(str(out_path), include_plotlyjs="cdn")
    print(f"wrote {out_path} ({out_path.stat().st_size / 1024 / 1024:.2f} MB)")


if __name__ == "__main__":
    main()
