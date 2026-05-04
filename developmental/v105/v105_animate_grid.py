#!/usr/bin/env python3
"""ESDE v10.5 — 71×71 トーラスグリッド × β-Integration アニメーション

各 window 末で 71×71 グリッドの各セルが「現時点でどの β に属する cid の
member_node か」で色塗りされる。β-merge イベントで色が一気に統合される
様子が視覚化される (案 ii: lifecycle event 厳密再生)。

実装:
  - per_cid_self_seed{N}.csv の member_nodes_repr (frozen at birth)
  - per_subject の birth_window / host_lost_window
  - alpha_lifecycle / beta_lifecycle event を step 順に再生
  - 各 window 末で cid_to_β を再構築
    - alpha_state[α] = set[cid] (events 再生で更新)
    - beta_state[β] = {alphas: set[α], state}
    - cid → α (集合) → β (= min α_id 経由で 1 個に絞る)

色:
  - β_id mod 12 で discrete palette (β-merge 時に色が一気に統合される)
  - recorded β は gray
  - empty cell は white

USAGE:
  python3 v105_animate_grid.py --seed 22
  python3 v105_animate_grid.py --seed 22 --all
"""
from __future__ import annotations
import argparse, csv, sys
from pathlib import Path
from collections import defaultdict

WINDOW_STEPS = 500
TRACKING_WINDOWS = 50
GRID_SIDE = 71  # ceil(sqrt(5000))


def parse_id_list(s: str) -> set[int]:
    """'1|2|3' or '' or 'merged_from_beta_5' → set[int]"""
    if not s or s.startswith("merged"):
        return set()
    out = set()
    for x in s.split("|"):
        x = x.strip()
        if x.isdigit():
            out.add(int(x))
    return out


def parse_nodes_repr(s: str) -> list[int]:
    """'[18,66,1083,2145,4008]' or '[18 66 ...]' → [18, 66, ...]"""
    s = s.strip().strip("[]")
    if not s:
        return []
    # comma + whitespace 両対応
    s = s.replace(",", " ")
    out = []
    for x in s.split():
        try:
            out.append(int(x))
        except Exception:
            pass
    return out


def build_per_window_cid_to_beta(
    diag_dir: Path, seed: int,
) -> tuple[list[tuple[int, dict[int, int]]], dict[int, list[int]],
            dict[int, str], dict[int, int]]:
    """seed の per-window cid→β (active β に対する所属) を再構築。

    Returns:
        snapshots: list[(window, cid_to_beta_dict)]
        cid_nodes: cid → frozen member_nodes
        beta_state_final: bid → "active"/"recorded" (run 末)
        cid_birth_window: cid → birth_window
    """
    # 1) cid の frozen nodes
    cid_nodes: dict[int, list[int]] = {}
    p = diag_dir / "selfread" / f"per_cid_self_seed{seed}.csv"
    if not p.exists():
        return [], {}, {}, {}
    with open(p) as f:
        for r in csv.DictReader(f):
            cid = int(r["cid_id"])
            nodes = parse_nodes_repr(r.get("member_nodes_repr", ""))
            cid_nodes[cid] = nodes

    # 2) cid birth_window / host_lost (window 単位、approximation)
    cid_birth_window: dict[int, int] = {}
    cid_host_lost_window: dict[int, int | None] = {}
    p_sub = diag_dir / "subjects" / f"per_subject_seed{seed}.csv"
    with open(p_sub) as f:
        for r in csv.DictReader(f):
            cid = int(r["cognitive_id"])
            try:
                bw = int(r["birth_window"])
            except (ValueError, KeyError):
                continue
            # tracking phase 起点を 0 とする (maturation 内 birth は w=-1 等)
            cid_birth_window[cid] = bw
            hlw = r.get("host_lost_window", "") or ""
            cid_host_lost_window[cid] = (int(hlw) if hlw.isdigit() else None)

    # 3) events 再生
    alpha_events = []
    p = diag_dir / "integration" / f"alpha_lifecycle_log_seed{seed}.csv"
    with open(p) as f:
        for r in csv.DictReader(f):
            alpha_events.append({
                "step": int(r["step"]),
                "kind": "alpha",
                "alpha_id": int(r["alpha_id"]),
                "event_type": r["event_type"],
                "member_cids": r.get("member_cids", ""),
            })

    beta_events = []
    p = diag_dir / "integration" / f"beta_lifecycle_log_seed{seed}.csv"
    with open(p) as f:
        for r in csv.DictReader(f):
            beta_events.append({
                "step": int(r["step"]),
                "kind": "beta",
                "beta_id": int(r["beta_id"]),
                "event_type": r["event_type"],
                "member_alphas": r.get("member_alphas", ""),
                "member_cids": r.get("member_cids", ""),
            })

    all_events = alpha_events + beta_events
    all_events.sort(key=lambda e: (e["step"], 0 if e["kind"] == "alpha" else 1))

    alpha_state: dict[int, set[int]] = {}            # α_id → set[cid]
    beta_state: dict[int, dict] = {}                  # β_id → {"alphas": set, "state": str}

    snapshots = []
    ev_idx = 0
    # ESDE main loop の global_step は tracking 開始時から 0 ではなく
    # maturation 中も link 動態 step を進める (v913_global_step)。
    # main loop で tracking 開始時に既に多くの step が経過している。
    # 単純化: events を全部 step 順に消費し、frame 境界は等間隔ではなく
    # event の step 値で扱う。
    # しかし frame は window 単位で表示したい。
    # アプローチ:
    #   - events の step max を取得
    #   - tracking 50 frames を均等に取る (event step max / 50 が境界)
    if not all_events:
        return [], cid_nodes, {}, cid_birth_window
    max_step = max(e["step"] for e in all_events)
    # 境界: maturation 終了を 0 と仮定し、tracking 50 windows で等分
    boundaries = [(w + 1) * (max_step / TRACKING_WINDOWS) for w in range(TRACKING_WINDOWS)]

    for w, boundary in enumerate(boundaries):
        while ev_idx < len(all_events) and all_events[ev_idx]["step"] <= boundary:
            e = all_events[ev_idx]
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
                elif et == "alpha_added":
                    if bid in beta_state and alphas:
                        beta_state[bid]["alphas"] = set(alphas)
                elif et == "beta_merged":
                    if bid in beta_state and alphas:
                        beta_state[bid]["alphas"] = set(alphas)
                elif et == "q_c_inherited":
                    if bid in beta_state and alphas:
                        beta_state[bid]["alphas"] = set(alphas)
                elif et == "active_to_recorded":
                    if bid in beta_state:
                        beta_state[bid]["state"] = "recorded"
            ev_idx += 1

        # snapshot: cid → β (active β only)
        # 効率化: α → β の逆引きマップ
        alpha_to_beta = {}
        for bid, bs in beta_state.items():
            if bs["state"] != "active":
                continue
            for aid in bs["alphas"]:
                if aid not in alpha_to_beta:
                    alpha_to_beta[aid] = bid

        cid_to_beta_now = {}
        for cid in alpha_state.get(0, set()) | set().union(*alpha_state.values(),
                                                             set()):
            pass
        # 直接: 全 α の cids を回って cid → α → β
        cid_candidates = defaultdict(list)  # cid -> [β_id]
        for aid, cids in alpha_state.items():
            if not cids:
                continue
            bid = alpha_to_beta.get(aid)
            if bid is None:
                continue
            for c in cids:
                cid_candidates[c].append(bid)

        for cid, bids in cid_candidates.items():
            cid_to_beta_now[cid] = min(bids)  # tie-break: 最小 β_id

        snapshots.append((w, cid_to_beta_now))

    beta_state_final = {bid: bs["state"] for bid, bs in beta_state.items()}
    return snapshots, cid_nodes, beta_state_final, cid_birth_window


def build_grid_frames(
    snapshots: list[tuple[int, dict[int, int]]],
    cid_nodes: dict[int, list[int]],
    beta_state_final: dict[int, str],
):
    """各 window snapshot から 71×71 グリッドを構築。

    cell value: β_id (0..N) or -1 (empty)
    """
    import numpy as np

    grids = []
    for w, cid_to_beta in snapshots:
        grid = np.full((GRID_SIDE, GRID_SIDE), -1, dtype=np.int32)
        for cid, bid in cid_to_beta.items():
            for node in cid_nodes.get(cid, []):
                row = node // GRID_SIDE
                col = node % GRID_SIDE
                if 0 <= row < GRID_SIDE and 0 <= col < GRID_SIDE:
                    # 最小 β_id 優先 (重なり時)
                    if grid[row, col] == -1 or bid < grid[row, col]:
                        grid[row, col] = bid
        grids.append((w, grid))
    return grids


def beta_id_to_color(bid: int, recorded_set: set[int]) -> str:
    """β_id を色に: recorded は gray、active は palette[mod 12]"""
    if bid == -1:
        return "rgba(255,255,255,0)"  # empty
    if bid in recorded_set:
        return "rgba(150,150,150,0.6)"  # recorded grey
    palette = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
        "#aec7e8", "#ffbb78",
    ]
    return palette[bid % len(palette)]


def grid_to_color_index(grid, recorded_set):
    """β_id grid → 色 index grid。
    -1 (empty): 0
    recorded β: 13
    active β: (β_id mod 12) + 1 (= 1..12)
    """
    import numpy as np
    z = np.zeros_like(grid, dtype=np.int8)
    for r in range(grid.shape[0]):
        for c in range(grid.shape[1]):
            bid = int(grid[r, c])
            if bid == -1:
                z[r, c] = 0
            elif bid in recorded_set:
                z[r, c] = 13
            else:
                z[r, c] = (bid % 12) + 1
    return z


# 14 段階の discrete colorscale (0=empty white, 1-12=palette, 13=recorded gray)
DISCRETE_COLORSCALE = [
    [0/13, "rgba(255,255,255,1)"],     # 0: empty
    [1/13, "#1f77b4"],
    [2/13, "#ff7f0e"],
    [3/13, "#2ca02c"],
    [4/13, "#d62728"],
    [5/13, "#9467bd"],
    [6/13, "#8c564b"],
    [7/13, "#e377c2"],
    [8/13, "#bcbd22"],  # gray-1 を黄緑系に変更
    [9/13, "#17becf"],
    [10/13, "#aec7e8"],
    [11/13, "#ffbb78"],
    [12/13, "#f7b6d2"],
    [13/13, "rgba(150,150,150,0.7)"],  # 13: recorded gray
]


def build_plotly_grid_figure(seed_to_data: dict, seeds_to_show: list[int],
                              *, default_seed: int):
    import plotly.graph_objects as go
    import numpy as np

    fig = go.Figure()

    # 1 seed の場合 — slider のみ
    if len(seeds_to_show) == 1:
        seed = seeds_to_show[0]
        grids, beta_state_final = seed_to_data[seed]
        recorded_set = {bid for bid, st in beta_state_final.items() if st == "recorded"}

        plotly_frames = []
        for w, grid in grids:
            unique_bids = sorted(set(grid.flatten().tolist()) - {-1})
            n_active = sum(1 for b in unique_bids if b not in recorded_set)
            n_recorded = sum(1 for b in unique_bids if b in recorded_set)
            n_filled = int((grid != -1).sum())

            z = grid_to_color_index(grid, recorded_set)

            plotly_frames.append(go.Frame(
                data=[go.Heatmap(
                    z=z, zmin=0, zmax=13,
                    colorscale=DISCRETE_COLORSCALE,
                    showscale=False,
                    hoverinfo="skip",
                    xgap=0.5, ygap=0.5,
                )],
                name=str(w),
                layout=go.Layout(
                    annotations=[
                        dict(text=f"<b>seed {seed} window {w}</b><br>"
                             f"active β = {n_active}, recorded β = {n_recorded}, "
                             f"filled cells = {n_filled}/{GRID_SIDE*GRID_SIDE}",
                             xref="paper", yref="paper",
                             x=0.5, y=1.08, xanchor="center",
                             showarrow=False, font=dict(size=14))
                    ]
                ),
            ))

        # 初期 frame (last)
        last = plotly_frames[-1]
        for tr in last.data:
            fig.add_trace(tr)
        fig.frames = plotly_frames

        fig.update_layout(
            updatemenus=[
                dict(type="buttons", showactive=False,
                     x=0.05, y=1.18, xanchor="left", yanchor="top",
                     buttons=[
                         dict(label="▶ Play", method="animate",
                              args=[None, {"frame": {"duration": 500, "redraw": True},
                                            "fromcurrent": True,
                                            "transition": {"duration": 100}}]),
                         dict(label="⏸ Pause", method="animate",
                              args=[[None], {"frame": {"duration": 0, "redraw": False},
                                              "mode": "immediate",
                                              "transition": {"duration": 0}}]),
                     ]),
            ],
            sliders=[
                dict(active=len(plotly_frames) - 1,
                     yanchor="top", y=-0.02, xanchor="left", x=0.10,
                     currentvalue=dict(prefix="window: ", visible=True,
                                        xanchor="right", font=dict(size=12)),
                     transition=dict(duration=200),
                     pad=dict(b=10, t=30), len=0.85,
                     steps=[
                         dict(method="animate",
                              args=[[str(w)],
                                    dict(mode="immediate",
                                         frame=dict(duration=300, redraw=True),
                                         transition=dict(duration=100))],
                              label=str(w))
                         for w in range(len(plotly_frames))
                     ]),
            ],
            title=f"v10.5 71×71 トーラスグリッド × β-Integration (seed {seed})",
            xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
            yaxis=dict(visible=False),
            height=850,
            width=900,
            margin=dict(t=120, b=80),
        )

    else:
        # case B: dropdown 切替 (Heatmap + discrete colorscale で軽量化)
        plotly_frames = []
        seed_to_keys: dict[int, list[str]] = {}
        for seed in seeds_to_show:
            grids, beta_state_final = seed_to_data[seed]
            recorded_set = {bid for bid, st in beta_state_final.items() if st == "recorded"}
            keys = []
            for w, grid in grids:
                unique_bids = sorted(set(grid.flatten().tolist()) - {-1})
                n_active = sum(1 for b in unique_bids if b not in recorded_set)
                n_recorded = sum(1 for b in unique_bids if b in recorded_set)
                n_filled = int((grid != -1).sum())

                z = grid_to_color_index(grid, recorded_set)
                key = f"seed{seed}_w{w}"
                keys.append(key)
                plotly_frames.append(go.Frame(
                    data=[go.Heatmap(
                        z=z, zmin=0, zmax=13,
                        colorscale=DISCRETE_COLORSCALE,
                        showscale=False,
                        hoverinfo="skip",
                        xgap=0.5, ygap=0.5,
                    )],
                    name=key,
                    layout=go.Layout(
                        annotations=[
                            dict(text=f"<b>seed {seed} window {w}</b><br>"
                                 f"active β = {n_active}, recorded β = {n_recorded}, "
                                 f"filled cells = {n_filled}/{GRID_SIDE*GRID_SIDE}",
                                 xref="paper", yref="paper",
                                 x=0.5, y=1.08, xanchor="center",
                                 showarrow=False, font=dict(size=14))
                        ]
                    ),
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
                steps.append(dict(
                    method="animate",
                    args=[[key],
                          dict(mode="immediate",
                               frame=dict(duration=300, redraw=True),
                               transition=dict(duration=100))],
                    label=f"s{seed}w{w}",
                ))

        seed_dropdown = []
        for seed in seeds_to_show:
            first_key = seed_to_keys[seed][-1]
            seed_dropdown.append(dict(
                label=f"seed {seed}",
                method="animate",
                args=[[first_key],
                      dict(mode="immediate",
                           frame=dict(duration=300, redraw=True),
                           transition=dict(duration=100))],
            ))

        fig.update_layout(
            updatemenus=[
                dict(type="buttons", showactive=False,
                     x=0.05, y=1.18, xanchor="left", yanchor="top",
                     buttons=[
                         dict(label="▶ Play", method="animate",
                              args=[None, {"frame": {"duration": 500, "redraw": True},
                                            "fromcurrent": True,
                                            "transition": {"duration": 100}}]),
                         dict(label="⏸ Pause", method="animate",
                              args=[[None], {"frame": {"duration": 0, "redraw": False},
                                              "mode": "immediate",
                                              "transition": {"duration": 0}}]),
                     ]),
                dict(type="dropdown", showactive=True,
                     x=0.92, y=1.18, xanchor="right", yanchor="top",
                     buttons=seed_dropdown),
            ],
            sliders=[
                dict(active=len(seed_to_keys[default_seed]) - 1,
                     yanchor="top", y=-0.02, xanchor="left", x=0.10,
                     currentvalue=dict(prefix="frame: ", visible=True,
                                        xanchor="right", font=dict(size=12)),
                     transition=dict(duration=200),
                     pad=dict(b=10, t=30), len=0.85,
                     steps=steps),
            ],
            title=f"v10.5 71×71 トーラスグリッド × β-Integration (24 seeds、初期: seed {default_seed})",
            xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
            yaxis=dict(visible=False),
            height=850,
            width=900,
            margin=dict(t=120, b=80),
        )

    return fig


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=22)
    parser.add_argument("--diag-dir", type=str, default="diag_v105_main_v2")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()

    diag = Path(args.diag_dir)
    if not diag.is_absolute():
        diag = Path(__file__).resolve().parent / diag
    print(f"reading from {diag}")

    seeds = list(range(24)) if args.all else [args.seed]
    seed_to_data = {}
    for s in seeds:
        snapshots, cid_nodes, beta_state, cid_birth = (
            build_per_window_cid_to_beta(diag, s))
        if not snapshots:
            print(f"  seed {s}: no data, skip")
            continue
        grids = build_grid_frames(snapshots, cid_nodes, beta_state)
        seed_to_data[s] = (grids, beta_state)
        n_recorded = sum(1 for st in beta_state.values() if st == "recorded")
        print(f"  seed {s}: {len(grids)} frames, "
              f"{len(cid_nodes)} cids with frozen nodes, "
              f"β_state final: {n_recorded} recorded")

    if not seed_to_data:
        print("no data"); sys.exit(1)

    fig = build_plotly_grid_figure(
        seed_to_data,
        seeds_to_show=list(seed_to_data.keys()),
        default_seed=args.seed,
    )

    if args.all:
        out = args.out or "v105_grid_all_seeds.html"
    else:
        out = args.out or f"v105_grid_seed{args.seed}.html"
    out_path = Path(out)
    if not out_path.is_absolute():
        out_path = Path(__file__).resolve().parent / out_path
    fig.write_html(str(out_path), include_plotlyjs="cdn")
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"wrote {out_path} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
