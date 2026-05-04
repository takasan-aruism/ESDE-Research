#!/usr/bin/env python3
"""ESDE v10.5 — β-Integration 時系列アニメーション (Plotly HTML)

case A: 単一 seed の β 時系列 (per window snapshot、50 frames)
case B: 24 seeds dropdown 切替版

入力:
  diag_v105_main_v2/integration/beta_lifecycle_log_seed{N}.csv
  diag_v105_main_v2/integration/beta_membership_log_seed{N}.csv (run 末スナップ)

出力:
  v105_integration_seed{N}.html (case A)
  v105_integration_all_seeds.html (case B)

可視化:
  - x: birth_step (時間軸)
  - y: 構成 α 数 (alpha_count)
  - size: 構成 cid 数 (cid_count)
  - color: active=teal / recorded=gray
  - hover: beta_id, αs, cids, Q_inherited, C_inherited, age
  - frame: per window (maturation 終わりから tracking 50 まで = 50 frames)
  - サブタイムライン: active/recorded β 数の推移 + 現フレーム位置の縦線

USAGE:
  python3 v105_animate_integration.py --seed 22                    # case A (seed 22)
  python3 v105_animate_integration.py --seed 22 --all              # case B (24 seeds)
"""
from __future__ import annotations
import argparse, csv, sys
from pathlib import Path
from collections import defaultdict


def reconstruct_beta_snapshots(lifecycle_path: Path):
    """β の lifecycle log から、event 時刻順に β の状態を replay。

    Returns:
        events: list of dict (timestamped β state)
        最終的に各 β の (birth_step, last_event_step, max_alpha_count,
        max_cid_count, became_recorded_step, Q_inherited, C_inherited)
        を全 step 横断で再構築。
    """
    events = []
    with open(lifecycle_path) as f:
        for r in csv.DictReader(f):
            events.append({
                "step": int(r["step"]),
                "beta_id": int(r["beta_id"]),
                "event_type": r["event_type"],
                "member_alphas": r.get("member_alphas", ""),
                "member_cids": r.get("member_cids", ""),
                "q_inherited_total": int(r.get("q_inherited_total") or 0),
                "c_inherited_total": int(r.get("c_inherited_total") or 0),
                "q_inherited_delta": int(r.get("q_inherited_delta") or 0),
                "c_inherited_delta": int(r.get("c_inherited_delta") or 0),
            })
    return events


def build_window_snapshots(events, window_steps=500, maturation_windows=20,
                            tracking_windows=50):
    """events を再生して、各 window 末ごとの β snapshot (dict) を返す。

    Returns:
        list of (window_idx, dict[beta_id -> state]) where state is dict with:
          birth_step, alpha_count, cid_count, Q, C, state ('active'/'recorded')
    """
    # window 境界: maturation_windows × window_steps から開始、
    # 各 tracking window 終わりで snapshot。
    # global_step は injection 後の累積 (maturation 含むが、
    # lifecycle log の step は v913_global_step で tracking 中の累積)。
    # 単純化: 全 events を step でソート、各 frame = window 末で snapshot。
    events_sorted = sorted(events, key=lambda e: e["step"])

    # 各 frame 境界 (step) = window_steps × i (1-indexed window)
    # tracking phase は window 0 から window 49 まで (50 frames)
    # frame_step[i] = (i+1) × window_steps - 1 (window i 末)
    frames = []
    state_per_beta: dict[int, dict] = {}

    ev_idx = 0
    for w in range(tracking_windows):
        boundary_step = (w + 1) * window_steps - 1
        # この境界までの events を消費
        while ev_idx < len(events_sorted) and events_sorted[ev_idx]["step"] <= boundary_step:
            ev = events_sorted[ev_idx]
            bid = ev["beta_id"]
            et = ev["event_type"]
            if et == "birth":
                state_per_beta[bid] = {
                    "birth_step": ev["step"],
                    "alpha_count": 1,
                    "cid_count": len([c for c in ev["member_cids"].split("|") if c]),
                    "Q": 0,
                    "C": 0,
                    "state": "active",
                    "last_event_step": ev["step"],
                }
            elif et == "alpha_added":
                if bid in state_per_beta:
                    n_a = len([a for a in ev["member_alphas"].split("|") if a])
                    state_per_beta[bid]["alpha_count"] = max(
                        state_per_beta[bid]["alpha_count"], n_a)
                    state_per_beta[bid]["last_event_step"] = ev["step"]
            elif et == "beta_merged":
                # この β が他の β を取り込んだ。member_alphas に最新値が入る
                if bid in state_per_beta:
                    n_a = len([a for a in ev["member_alphas"].split("|") if a])
                    state_per_beta[bid]["alpha_count"] = n_a
                    state_per_beta[bid]["Q"] = ev["q_inherited_total"]
                    state_per_beta[bid]["C"] = ev["c_inherited_total"]
                    state_per_beta[bid]["last_event_step"] = ev["step"]
            elif et == "q_c_inherited":
                if bid in state_per_beta:
                    n_a = len([a for a in ev["member_alphas"].split("|") if a]) if ev["member_alphas"] else 0
                    n_c = len([c for c in ev["member_cids"].split("|") if c]) if ev["member_cids"] else 0
                    state_per_beta[bid]["alpha_count"] = n_a if n_a > 0 else state_per_beta[bid]["alpha_count"]
                    state_per_beta[bid]["cid_count"] = max(
                        state_per_beta[bid]["cid_count"], n_c)
                    state_per_beta[bid]["Q"] = ev["q_inherited_total"]
                    state_per_beta[bid]["C"] = ev["c_inherited_total"]
                    state_per_beta[bid]["last_event_step"] = ev["step"]
            elif et == "active_to_recorded":
                if bid in state_per_beta:
                    state_per_beta[bid]["state"] = "recorded"
                    state_per_beta[bid]["last_event_step"] = ev["step"]
            ev_idx += 1
        # snapshot at boundary
        frames.append((w, {bid: dict(s) for bid, s in state_per_beta.items()}))
    return frames


def build_plotly_figure(seed_to_frames: dict, seeds_to_show: list[int],
                          *, default_seed: int):
    """seed → frames から plotly figure を構築。

    seeds_to_show が複数なら dropdown で seed 切替、
    1 個なら slider で frame 切替のみ。
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    # メインプロット (β 散布) + サブプロット (active/recorded 推移)
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.08,
        subplot_titles=(
            "β-Integration network (size = cid count, color = state)",
            "β count timeline (active / recorded)"
        ),
        shared_xaxes=False,
    )

    # 1 つの seed だけ default で表示。case B は seed dropdown
    if len(seeds_to_show) == 1:
        seed = seeds_to_show[0]
        frames_for_seed = seed_to_frames[seed]
        # 各 frame をフレーム化
        plotly_frames = []
        for w, betas in frames_for_seed:
            xs, ys, sizes, colors, texts = [], [], [], [], []
            for bid, s in betas.items():
                xs.append(s["birth_step"])
                ys.append(s["alpha_count"])
                sizes.append(max(8, min(60, s["cid_count"] * 4)))
                colors.append("teal" if s["state"] == "active" else "lightgray")
                age = w * 500 - s["birth_step"]
                texts.append(
                    f"β{bid}<br>state={s['state']}<br>"
                    f"αs={s['alpha_count']}<br>cids={s['cid_count']}<br>"
                    f"Q={s['Q']} C={s['C']}<br>age={age} steps"
                )
            n_active = sum(1 for s in betas.values() if s["state"] == "active")
            n_recorded = sum(1 for s in betas.values() if s["state"] == "recorded")
            # 累積タイムライン (window 0..w)
            t_active = []; t_recorded = []
            for ww, bbs in frames_for_seed[:w + 1]:
                t_active.append(sum(1 for s in bbs.values() if s["state"] == "active"))
                t_recorded.append(sum(1 for s in bbs.values() if s["state"] == "recorded"))
            t_x = list(range(w + 1))

            plotly_frames.append(go.Frame(
                data=[
                    go.Scatter(
                        x=xs, y=ys, mode="markers",
                        marker=dict(size=sizes, color=colors,
                                    line=dict(width=1, color="DarkSlateGray")),
                        text=texts, hoverinfo="text",
                        name="β",
                        xaxis="x", yaxis="y",
                    ),
                    go.Scatter(
                        x=t_x, y=t_active, mode="lines+markers",
                        line=dict(color="teal", width=2),
                        marker=dict(size=4),
                        name="active",
                        xaxis="x2", yaxis="y2",
                    ),
                    go.Scatter(
                        x=t_x, y=t_recorded, mode="lines+markers",
                        line=dict(color="gray", width=2, dash="dot"),
                        marker=dict(size=4),
                        name="recorded",
                        xaxis="x2", yaxis="y2",
                    ),
                ],
                name=str(w),
                layout=go.Layout(
                    annotations=[
                        dict(text=f"<b>seed {seed} window {w} "
                             f"(step {(w + 1) * 500})</b><br>"
                             f"active={n_active}, recorded={n_recorded}, "
                             f"total={n_active + n_recorded}",
                             xref="paper", yref="paper",
                             x=0.5, y=1.10, xanchor="center",
                             showarrow=False, font=dict(size=14)),
                        dict(text="β-Integration network (size = cid count, color = state)",
                             xref="paper", yref="paper",
                             x=0.5, y=1.0, xanchor="center", showarrow=False,
                             font=dict(size=12)),
                        dict(text="β count timeline (active / recorded)",
                             xref="paper", yref="paper",
                             x=0.5, y=0.30, xanchor="center", showarrow=False,
                             font=dict(size=12)),
                    ]
                ),
            ))

        # 初期 frame (last)
        last_frame = plotly_frames[-1]
        for tr in last_frame.data:
            fig.add_trace(tr,
                          row=1 if tr.name == "β" else 2,
                          col=1)

        fig.frames = plotly_frames

        # Slider + play/pause
        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    showactive=False,
                    x=0.05, y=1.18, xanchor="left", yanchor="top",
                    buttons=[
                        dict(label="▶ Play", method="animate",
                             args=[None, {"frame": {"duration": 400, "redraw": True},
                                           "fromcurrent": True,
                                           "transition": {"duration": 100}}]),
                        dict(label="⏸ Pause", method="animate",
                             args=[[None], {"frame": {"duration": 0, "redraw": False},
                                             "mode": "immediate",
                                             "transition": {"duration": 0}}]),
                    ],
                )
            ],
            sliders=[
                dict(
                    active=len(plotly_frames) - 1,
                    yanchor="top", y=-0.02, xanchor="left", x=0.10,
                    currentvalue=dict(prefix="window: ",
                                       visible=True, xanchor="right",
                                       font=dict(size=12)),
                    transition=dict(duration=200),
                    pad=dict(b=10, t=30),
                    len=0.85,
                    steps=[
                        dict(method="animate",
                             args=[[str(w)],
                                   dict(mode="immediate",
                                        frame=dict(duration=200, redraw=True),
                                        transition=dict(duration=100))],
                             label=str(w))
                        for w in range(len(plotly_frames))
                    ],
                )
            ],
            title=f"v10.5 β-Integration 時系列 (seed {seed})",
            xaxis=dict(title="birth_step"),
            yaxis=dict(title="α count"),
            xaxis2=dict(title="window"),
            yaxis2=dict(title="β count"),
            height=850,
            showlegend=True,
            margin=dict(t=120, b=80),
        )

    else:
        # case B: seeds_to_show 複数、各 seed に対し frame 群を持つ。
        # plotly は単一 figure に複数 seed を frame 化することは難しいので、
        # ここでは seed dropdown で複数 figure を切り替えるアプローチ。
        # 簡略化: 各 seed の frame を 1 つの figure に dropdown で切り替える形。
        # plotly の updatemenus + frames は 1 つの frame 名前空間しか持たないので、
        # seed × window の名前を unique にする。
        frame_by_label = {}  # "seed{N}_w{W}" -> Frame
        seed_to_frame_keys = {}

        for seed in seeds_to_show:
            frames_for_seed = seed_to_frames[seed]
            keys = []
            for w, betas in frames_for_seed:
                xs, ys, sizes, colors, texts = [], [], [], [], []
                for bid, s in betas.items():
                    xs.append(s["birth_step"])
                    ys.append(s["alpha_count"])
                    sizes.append(max(8, min(60, s["cid_count"] * 4)))
                    colors.append("teal" if s["state"] == "active" else "lightgray")
                    age = w * 500 - s["birth_step"]
                    texts.append(
                        f"β{bid}<br>state={s['state']}<br>"
                        f"αs={s['alpha_count']}<br>cids={s['cid_count']}<br>"
                        f"Q={s['Q']} C={s['C']}<br>age={age} steps"
                    )
                n_active = sum(1 for s in betas.values() if s["state"] == "active")
                n_recorded = sum(1 for s in betas.values() if s["state"] == "recorded")
                t_active = []; t_recorded = []
                for ww, bbs in frames_for_seed[:w + 1]:
                    t_active.append(sum(1 for s in bbs.values() if s["state"] == "active"))
                    t_recorded.append(sum(1 for s in bbs.values() if s["state"] == "recorded"))
                t_x = list(range(w + 1))
                key = f"seed{seed}_w{w}"
                keys.append(key)
                frame_by_label[key] = go.Frame(
                    data=[
                        go.Scatter(x=xs, y=ys, mode="markers",
                                    marker=dict(size=sizes, color=colors,
                                                line=dict(width=1, color="DarkSlateGray")),
                                    text=texts, hoverinfo="text",
                                    name="β"),
                        go.Scatter(x=t_x, y=t_active, mode="lines+markers",
                                    line=dict(color="teal", width=2),
                                    marker=dict(size=4),
                                    name="active",
                                    xaxis="x2", yaxis="y2"),
                        go.Scatter(x=t_x, y=t_recorded, mode="lines+markers",
                                    line=dict(color="gray", width=2, dash="dot"),
                                    marker=dict(size=4),
                                    name="recorded",
                                    xaxis="x2", yaxis="y2"),
                    ],
                    name=key,
                    layout=go.Layout(
                        annotations=[
                            dict(text=f"<b>seed {seed} window {w} (step {(w + 1) * 500})</b><br>"
                                 f"active={n_active}, recorded={n_recorded}, total={n_active + n_recorded}",
                                 xref="paper", yref="paper",
                                 x=0.5, y=1.10, xanchor="center",
                                 showarrow=False, font=dict(size=14)),
                        ]
                    ),
                )
            seed_to_frame_keys[seed] = keys

        # 初期 frame: default_seed の最終 window
        default_keys = seed_to_frame_keys[default_seed]
        last_key = default_keys[-1]
        last_frame = frame_by_label[last_key]
        for tr in last_frame.data:
            fig.add_trace(tr,
                          row=1 if tr.name == "β" else 2,
                          col=1)

        fig.frames = list(frame_by_label.values())

        # Slider: 全 frame
        # Dropdown: seed 切替 (各 seed の最初の frame に jump)
        steps = []
        for seed in seeds_to_show:
            for w, key in enumerate(seed_to_frame_keys[seed]):
                steps.append(dict(
                    method="animate",
                    args=[[key],
                          dict(mode="immediate",
                               frame=dict(duration=200, redraw=True),
                               transition=dict(duration=100))],
                    label=f"s{seed}w{w}",
                ))

        seed_dropdown = []
        for seed in seeds_to_show:
            first_key = seed_to_frame_keys[seed][-1]  # 最終 window で表示
            seed_dropdown.append(
                dict(
                    label=f"seed {seed}",
                    method="animate",
                    args=[[first_key],
                          dict(mode="immediate",
                               frame=dict(duration=300, redraw=True),
                               transition=dict(duration=100))],
                )
            )

        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    showactive=False,
                    x=0.05, y=1.18, xanchor="left", yanchor="top",
                    buttons=[
                        dict(label="▶ Play", method="animate",
                             args=[None, {"frame": {"duration": 400, "redraw": True},
                                           "fromcurrent": True,
                                           "transition": {"duration": 100}}]),
                        dict(label="⏸ Pause", method="animate",
                             args=[[None], {"frame": {"duration": 0, "redraw": False},
                                             "mode": "immediate",
                                             "transition": {"duration": 0}}]),
                    ],
                ),
                dict(
                    type="dropdown",
                    showactive=True,
                    x=0.92, y=1.18, xanchor="right", yanchor="top",
                    buttons=seed_dropdown,
                ),
            ],
            sliders=[
                dict(
                    active=len(default_keys) - 1,
                    yanchor="top", y=-0.02, xanchor="left", x=0.10,
                    currentvalue=dict(prefix="frame: ",
                                       visible=True, xanchor="right",
                                       font=dict(size=12)),
                    transition=dict(duration=200),
                    pad=dict(b=10, t=30),
                    len=0.85,
                    steps=steps,
                )
            ],
            title=f"v10.5 β-Integration 時系列 (24 seeds、初期表示: seed {default_seed})",
            xaxis=dict(title="birth_step"),
            yaxis=dict(title="α count"),
            xaxis2=dict(title="window"),
            yaxis2=dict(title="β count"),
            height=850,
            showlegend=True,
            margin=dict(t=120, b=80),
        )

    return fig


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=22)
    parser.add_argument("--diag-dir", type=str,
                        default="diag_v105_main_v2")
    parser.add_argument("--all", action="store_true",
                        help="案 B: 24 seeds dropdown 切替版")
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()

    diag = Path(args.diag_dir)
    if not diag.is_absolute():
        diag = Path(__file__).resolve().parent / diag
    print(f"reading from {diag}")

    seeds = list(range(24)) if args.all else [args.seed]
    seed_to_frames = {}
    for s in seeds:
        lp = diag / "integration" / f"beta_lifecycle_log_seed{s}.csv"
        if not lp.exists():
            print(f"  WARNING: {lp} not found, skip seed {s}")
            continue
        events = reconstruct_beta_snapshots(lp)
        snapshots = build_window_snapshots(events)
        seed_to_frames[s] = snapshots
        print(f"  seed {s}: {len(events)} events, {len(snapshots)} window frames")

    if not seed_to_frames:
        print("no data")
        sys.exit(1)

    if args.all:
        out = args.out or "v105_integration_all_seeds.html"
        fig = build_plotly_figure(seed_to_frames,
                                   seeds_to_show=list(seed_to_frames.keys()),
                                   default_seed=args.seed)
    else:
        out = args.out or f"v105_integration_seed{args.seed}.html"
        fig = build_plotly_figure(seed_to_frames,
                                   seeds_to_show=[args.seed],
                                   default_seed=args.seed)

    out_path = Path(out)
    if not out_path.is_absolute():
        out_path = Path(__file__).resolve().parent / out_path
    fig.write_html(str(out_path), include_plotlyjs="cdn")
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"wrote {out_path} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
