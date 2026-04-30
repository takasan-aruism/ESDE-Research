"""ESDE v10.3 — Bidirectional E3 post-process

実装指示書 §3 と §5.4 に基づき、bidirectional_e3_log を window 単位で
集計して以下を生成する:

  1. has_3rd_cid_* フラグを bidirectional_e3_log に書き戻し (in-place)
     - has_3rd_cid_closed (Cat 1a): A-B, B-C, C-A が同 window
     - has_3rd_cid_open (Cat 1b): A-B + B-C (or A-C) があり、A-C は無い
     - has_3rd_cid_proximate (Cat 1c): TODO (member_nodes 距離が必要)
  2. bidirectional_e3_3rd_cid_log_seed{N}.csv を生成
  3. per_window 集計 (n_closed_triads, n_open_triads, etc) を per_window CSV に追加
  4. per_subject 集計 (n_be3_total, n_be3_partners 等) を per_subject CSV に追加

使い方:
  python3 v103_be3_postprocess.py <diag_dir> <seed>
  python3 v103_be3_postprocess.py diag_v103_main 0
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd


def detect_triads_per_window(be3_df: pd.DataFrame) -> dict:
    """window 内の closed/open triad を検出。

    Returns:
        per_pair_flags: (window, cid_a, cid_b) -> {
            "has_3rd_closed": bool,
            "has_3rd_open": bool,
            "third_cids_closed": list[int],
            "third_cids_open": list[int],
        }
        window_stats: window -> {
            "n_closed_triads": int,
            "n_open_triads": int,
            "triad_member_count": int,
        }
    """
    per_pair_flags = {}
    window_stats = defaultdict(
        lambda: {"n_closed": 0, "n_open": 0, "members": set()})

    for w, sub in be3_df[be3_df["fired"] == True].groupby("window"):
        # window 内の発火ペアを edge として graph 構築
        edges = set()
        for _, r in sub.iterrows():
            a, b = int(r["cid_a"]), int(r["cid_b"])
            edges.add((min(a, b), max(a, b)))

        # 隣接 dict
        adj = defaultdict(set)
        for a, b in edges:
            adj[a].add(b)
            adj[b].add(a)

        # 三角形 (closed triad) 検出
        closed_triads = set()
        for a, b in edges:
            common = adj[a] & adj[b]
            for c in common:
                tri = tuple(sorted([a, b, c]))
                closed_triads.add(tri)

        # 各 (a, b) ペアごとの 3rd cid 候補
        for (a, b) in edges:
            third_closed = []
            third_open = []
            common = adj[a] & adj[b]  # closed triad の C 候補
            for c in common:
                third_closed.append(c)
            # open triad: A-B + (A-C または B-C) で C-A or C-B がなければ open
            for c in (adj[a] - adj[b] - {b}):
                # A-C はあるが B-C はない
                third_open.append(c)
            for c in (adj[b] - adj[a] - {a}):
                # B-C はあるが A-C はない
                third_open.append(c)
            third_open = sorted(set(third_open))

            key = (int(w), a, b)
            per_pair_flags[key] = {
                "has_3rd_closed": bool(third_closed),
                "has_3rd_open": bool(third_open),
                "third_cids_closed": sorted(set(third_closed)),
                "third_cids_open": third_open,
            }

        window_stats[int(w)]["n_closed"] = len(closed_triads)
        # open triad 数 (= 各ペアで open 候補が居れば 1 つカウント)
        window_stats[int(w)]["n_open"] = sum(
            1 for k, v in per_pair_flags.items()
            if k[0] == int(w) and v["has_3rd_open"]
        )
        members = set()
        for tri in closed_triads:
            members.update(tri)
        window_stats[int(w)]["members"] = members

    # window_stats を dict に変換
    window_stats_out = {}
    for w, s in window_stats.items():
        window_stats_out[w] = {
            "n_closed_triads": s["n_closed"],
            "n_open_triads": s["n_open"],
            "triad_member_count": len(s["members"]),
        }
    return per_pair_flags, window_stats_out


def write_3rd_cid_log(be3_df: pd.DataFrame, per_pair_flags: dict,
                      out_path: Path, seed: int) -> int:
    """bidirectional_e3_3rd_cid_log を生成。"""
    rows = []
    for _, r in be3_df[be3_df["fired"] == True].iterrows():
        a, b = int(r["cid_a"]), int(r["cid_b"])
        key = (int(r["window"]), a, b)
        flags = per_pair_flags.get(key)
        if not flags:
            continue

        for c in flags["third_cids_closed"]:
            rows.append({
                "seed": seed,
                "window": int(r["window"]),
                "step": int(r["step"]),
                "global_step": int(r["global_step"]),
                "cid_a": a,
                "cid_b": b,
                "cid_c": int(c),
                "c_role": "closed_third",
            })
        for c in flags["third_cids_open"]:
            rows.append({
                "seed": seed,
                "window": int(r["window"]),
                "step": int(r["step"]),
                "global_step": int(r["global_step"]),
                "cid_a": a,
                "cid_b": b,
                "cid_c": int(c),
                "c_role": "open_intermediary",
            })

    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    return len(df)


def add_flags_to_be3_log(be3_df: pd.DataFrame, per_pair_flags: dict,
                         out_path: Path) -> None:
    """bidirectional_e3_log に has_3rd_* フラグを追加して書き戻し。"""
    has_closed = []
    has_open = []
    n_closed = []
    n_open = []
    for _, r in be3_df.iterrows():
        if not r["fired"]:
            has_closed.append(False)
            has_open.append(False)
            n_closed.append(0)
            n_open.append(0)
            continue
        key = (int(r["window"]), int(r["cid_a"]), int(r["cid_b"]))
        flags = per_pair_flags.get(key, {})
        has_closed.append(bool(flags.get("has_3rd_closed", False)))
        has_open.append(bool(flags.get("has_3rd_open", False)))
        n_closed.append(len(flags.get("third_cids_closed", [])))
        n_open.append(len(flags.get("third_cids_open", [])))
    be3_df["has_3rd_cid_closed"] = has_closed
    be3_df["has_3rd_cid_open"] = has_open
    be3_df["n_3rd_cid_closed"] = n_closed
    be3_df["n_3rd_cid_open"] = n_open
    be3_df.to_csv(out_path, index=False)


def compute_per_subject_stats(be3_df: pd.DataFrame) -> pd.DataFrame:
    """per cid の双方向 E3 集計。"""
    rows = []
    fired = be3_df[be3_df["fired"] == True]

    cid_records = defaultdict(
        lambda: {"n_be3": 0, "partners": defaultdict(int), "c_spent": 0})
    for _, r in fired.iterrows():
        cid_a, cid_b = int(r["cid_a"]), int(r["cid_b"])
        is_shadow = bool(r.get("shadow_audit", False))
        cid_records[cid_a]["n_be3"] += 1
        cid_records[cid_a]["partners"][cid_b] += 1
        if not is_shadow:
            cid_records[cid_a]["c_spent"] += 1
        cid_records[cid_b]["n_be3"] += 1
        cid_records[cid_b]["partners"][cid_a] += 1
        if not is_shadow:
            cid_records[cid_b]["c_spent"] += 1

    for cid, rec in cid_records.items():
        partners = rec["partners"]
        n_repeated = sum(1 for v in partners.values() if v >= 2)
        # ncore-distribution は be3_df から相手の ncore を集計
        rows.append({
            "cid": cid,
            "n_be3_total": rec["n_be3"],
            "n_be3_partners": len(partners),
            "n_be3_repeated_partners": n_repeated,
            "c_spent_on_be3_total": rec["c_spent"],
        })

    return pd.DataFrame(rows)


def main():
    if len(sys.argv) < 3:
        print("usage: python v103_be3_postprocess.py <diag_dir> <seed>")
        sys.exit(1)

    diag_dir = Path(sys.argv[1])
    seed = int(sys.argv[2])

    be3_dir = diag_dir / "bidirectional"
    be3_log = be3_dir / f"bidirectional_e3_log_seed{seed}.csv"
    if not be3_log.exists():
        print(f"ERROR: {be3_log} not found")
        sys.exit(1)

    print(f"Loading {be3_log}...")
    be3_df = pd.read_csv(be3_log)
    print(f"  {len(be3_df)} rows ({(be3_df['fired'] == True).sum()} fired)")

    if (be3_df["fired"] == True).sum() == 0:
        print("No fired events. Skip post-processing.")
        return

    print("Detecting triads per window...")
    per_pair_flags, window_stats = detect_triads_per_window(be3_df)
    print(f"  {len(per_pair_flags)} pair-level flags")
    print(f"  {len(window_stats)} window stats")

    # 3rd_cid_log
    third_cid_path = be3_dir / f"bidirectional_e3_3rd_cid_log_seed{seed}.csv"
    n_3rd = write_3rd_cid_log(be3_df, per_pair_flags, third_cid_path, seed)
    print(f"  wrote bidirectional_e3_3rd_cid_log: {n_3rd} rows")

    # be3_log に flags 追加 (in-place 更新)
    add_flags_to_be3_log(be3_df, per_pair_flags, be3_log)
    print(f"  updated {be3_log} with has_3rd_* flags")

    # per_window 集計
    window_summary_path = be3_dir / f"bidirectional_e3_window_summary_seed{seed}.csv"
    ws_rows = []
    for w in sorted(window_stats.keys()):
        ws = window_stats[w]
        ws["seed"] = seed
        ws["window"] = w
        ws_rows.append(ws)
    pd.DataFrame(ws_rows).to_csv(window_summary_path, index=False)
    print(f"  wrote per_window summary: {len(ws_rows)} rows")

    # per_subject 集計
    subj_summary_path = be3_dir / f"bidirectional_e3_per_subject_seed{seed}.csv"
    ps = compute_per_subject_stats(be3_df)
    ps["seed"] = seed
    ps.to_csv(subj_summary_path, index=False)
    print(f"  wrote per_subject summary: {len(ps)} rows")

    print("Done.")


if __name__ == "__main__":
    main()
