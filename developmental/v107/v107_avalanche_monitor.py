#!/usr/bin/env python3
"""v10.7 avalanche monitor + peak_lag analyzer.

Step F の 5 機能:
  1. multi_hop (3 hop 上限): familiarity 経路で 2-hop / 3-hop neighbor を BFS
  2. 減衰率追跡 (hop 別 baseline_excess_change)
  3. 共鳴ループ検出 (loop_2_hop / loop_3_hop)
  4. peak_lag 測定 (10 step bin、lag 0-1000、101 bins)
  5. 波及パターン分類 (即時型 / 遅延型 / 残響型)

multi-hop の対象は familiarity 経路 (グラフ構造を持つ唯一の path)。
attention_via_salience / integration / temporal_coactivation は 1-hop で完結
(意味的に multi-hop 概念が無い、or run 集約値、or 時間窓固有)。

入力: source_events / relation_paths / baselines_with_delta (Step C-E 出力)
出力: developmental/v107/outputs/{smoke,main}/
  - multi_hop_paths_seed{N}.parquet
  - decay_rate_seed{N}.parquet
  - resonance_loops_seed{N}.parquet
  - peak_lag_curve_seed{N}.parquet
  - wave_patterns_seed{N}.parquet
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V105_ROOT = (REPO_ROOT / "developmental" / "v105").resolve()
V106_ROOT = (REPO_ROOT / "developmental" / "v106").resolve()
V107_ROOT = (REPO_ROOT / "developmental" / "v107").resolve()

DIAG_ROOT = V105_ROOT / "diag_v105_main_v2"
NET_DIR = DIAG_ROOT / "network"
INT_DIR = DIAG_ROOT / "integration"
PULSE_DIR = DIAG_ROOT / "pulse"
BAL_DIR = DIAG_ROOT / "balance"
SAL_DIR = DIAG_ROOT / "salience"
AUDIT_DIR = DIAG_ROOT / "audit"

OUT_ROOT = V107_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"

sys.path.insert(0, str(V106_ROOT))
from v106_post_process import safe_read_csv  # noqa: E402

SEEDS = list(range(24))
TOP_N_PER_HOP = 20
MAX_HOPS = 3
LAG_BINS = list(range(0, 1010, 10))  # 101 bins (0, 10, 20, ..., 1000)


def assert_output_under_v107(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V107_ROOT not in abs_path.parents and abs_path != V107_ROOT:
        raise ValueError(f"Output path {path} not under v107/")


def safe_write_parquet_v107(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v107(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


# ----------------------------------------------------------------------
# 1. multi-hop graph traversal (familiarity 経路)
# ----------------------------------------------------------------------
def build_familiarity_adjacency(seed: int) -> dict[int, dict[int, float]]:
    df = safe_read_csv(NET_DIR / f"fam_edges_seed{seed}.csv")
    adj: dict[int, dict[int, float]] = {}
    for _, r in df.iterrows():
        a, b = int(r["from"]), int(r["to"])
        f = float(r["familiarity"])
        adj.setdefault(a, {})[b] = max(adj.get(a, {}).get(b, 0), f)
        adj.setdefault(b, {})[a] = max(adj.get(b, {}).get(a, 0), f)
    return adj


def bfs_multi_hop(adj: dict[int, dict[int, float]], source_cid: int,
                    max_hops: int = MAX_HOPS) -> dict[int, dict[int, float]]:
    """source_cid から hop_distance 別の neighbor を返す.
    Returns: {hop: {target_cid: cumulative_strength}}
    """
    visited = {source_cid}
    by_hop: dict[int, dict[int, float]] = {h: {} for h in range(1, max_hops + 1)}
    current_layer = {source_cid: 0.0}  # cid -> cumulative strength
    for h in range(1, max_hops + 1):
        next_layer: dict[int, float] = {}
        for cid, prev_strength in current_layer.items():
            for nb, fam in adj.get(cid, {}).items():
                if nb in visited:
                    continue
                # 累積強度: 経路の弱リンク (min) で評価
                strength = min(prev_strength if prev_strength > 0 else fam, fam)
                if nb not in next_layer or next_layer[nb] < strength:
                    next_layer[nb] = strength
        for cid, strength in next_layer.items():
            visited.add(cid)
            by_hop[h][cid] = strength
        current_layer = next_layer
        if not current_layer:
            break
    return by_hop


def build_multi_hop_paths(seed: int, source_events: pd.DataFrame) -> pd.DataFrame:
    adj = build_familiarity_adjacency(seed)
    rows = []
    cache: dict[int, dict[int, dict[int, float]]] = {}
    for _, ev in source_events[["event_id", "source_cid", "timestamp"]].iterrows():
        s_cid = int(ev["source_cid"])
        if s_cid not in cache:
            cache[s_cid] = bfs_multi_hop(adj, s_cid, MAX_HOPS)
        by_hop = cache[s_cid]
        for hop in range(1, MAX_HOPS + 1):
            sorted_neighbors = sorted(
                by_hop[hop].items(), key=lambda x: -x[1]
            )[:TOP_N_PER_HOP]
            for tcid, strength in sorted_neighbors:
                rows.append({
                    "event_id": ev["event_id"],
                    "source_cid": s_cid,
                    "timestamp": int(ev["timestamp"]),
                    "target_cid": int(tcid),
                    "relation_path_type": f"familiarity_hop{hop}",
                    "relation_strength": float(strength),
                    "hop_distance": hop,
                })
    if not rows:
        return pd.DataFrame(columns=[
            "event_id", "source_cid", "timestamp", "target_cid",
            "relation_path_type", "relation_strength", "hop_distance", "seed",
        ])
    df = pd.DataFrame(rows)
    df["seed"] = seed
    return df


# ----------------------------------------------------------------------
# 2. 減衰率追跡 (hop 別 baseline_excess_change)
# ----------------------------------------------------------------------
def compute_decay_rate(df_excess: pd.DataFrame, df_multi_hop: pd.DataFrame) -> pd.DataFrame:
    """hop 別の mean delta_C, delta_Q, n_pulses を集計, 減衰パターン分類."""
    delta_cols = ["mean_delta_C_immediate", "mean_delta_Q_immediate",
                    "mean_delta_R_familiarity_immediate",
                    "mean_n_pulses_in_window_immediate",
                    "mean_delta_C_medium",
                    "mean_n_pulses_in_window_medium"]
    # multi_hop の (event, target, hop) に Step E の excess_change を結合...
    # ただし excess_change は (event, relation_path_type) 集計なので、
    # multi_hop 用に再集計が必要。
    # シンプル: hop 別 path_type で excess_change から取る (familiarity_hop1/2/3)
    rows = []
    for hop in range(1, MAX_HOPS + 1):
        path_type = f"familiarity_hop{hop}"
        sub = df_excess[df_excess["relation_path_type"] == path_type]
        row = {"hop_distance": hop, "path_type": path_type, "n_events": int(len(sub))}
        for col in delta_cols:
            if col in sub.columns:
                row[f"hop_mean_{col}"] = float(sub[col].mean()) if len(sub) else 0.0
        rows.append(row)
    df = pd.DataFrame(rows)
    if len(df) >= 2:
        # 減衰パターン: hop_1 vs hop_2 vs hop_3 の比較
        m1 = df[df["hop_distance"] == 1]["hop_mean_mean_delta_C_immediate"].iloc[0] \
            if len(df[df["hop_distance"] == 1]) else 0
        m2 = df[df["hop_distance"] == 2]["hop_mean_mean_delta_C_immediate"].iloc[0] \
            if len(df[df["hop_distance"] == 2]) else 0
        m3 = df[df["hop_distance"] == 3]["hop_mean_mean_delta_C_immediate"].iloc[0] \
            if len(df[df["hop_distance"] == 3]) else 0
        if abs(m1) < 1e-9:
            pattern = "no_signal"
        elif abs(m2) < abs(m1) * 0.1:
            pattern = "sharp_decay"
        elif abs(m3) < abs(m1) * 0.5:
            pattern = "exponential"
        elif abs(m1 - m2) < abs(m1) * 0.1 and abs(m2 - m3) < abs(m2) * 0.1:
            pattern = "maintained"
        else:
            pattern = "linear"
        df["decay_pattern"] = pattern
    return df


# ----------------------------------------------------------------------
# 3. 共鳴ループ検出
# ----------------------------------------------------------------------
def detect_resonance_loops(seed: int) -> pd.DataFrame:
    """familiarity edge の双方向対称性で 2-hop loop、グラフ traversal で 3-hop loop."""
    adj = build_familiarity_adjacency(seed)
    loops_2 = []
    seen_pairs = set()
    for cid_a, neighbors in adj.items():
        for cid_b, fam_ab in neighbors.items():
            if (cid_a, cid_b) in seen_pairs or (cid_b, cid_a) in seen_pairs:
                continue
            fam_ba = adj.get(cid_b, {}).get(cid_a)
            if fam_ba is not None:
                loops_2.append({
                    "loop_type": "loop_2_hop",
                    "cid_a": cid_a, "cid_b": cid_b,
                    "fam_ab": fam_ab, "fam_ba": fam_ba,
                    "min_strength": min(fam_ab, fam_ba),
                })
            seen_pairs.add((cid_a, cid_b))

    # 3-hop loop: A -> B -> C -> A (A と C 接続あり)
    loops_3 = []
    seen_triples = set()
    for a, neighbors_a in adj.items():
        for b in neighbors_a:
            for c in adj.get(b, {}):
                if c == a:
                    continue
                if a in adj.get(c, {}):
                    triple = tuple(sorted([a, b, c]))
                    if triple in seen_triples:
                        continue
                    seen_triples.add(triple)
                    loops_3.append({
                        "loop_type": "loop_3_hop",
                        "cid_a": a, "cid_b": b, "cid_c": c,
                        "min_strength": min(neighbors_a[b], adj[b][c], adj[c][a]),
                    })

    df_loops = pd.DataFrame(loops_2 + loops_3)
    df_loops["seed"] = seed
    return df_loops


# ----------------------------------------------------------------------
# 4. peak_lag 測定 (10 step bin、lag 0-1000)
# ----------------------------------------------------------------------
def compute_peak_lag_curve(seed: int, df_targets: pd.DataFrame) -> pd.DataFrame:
    """relation_path_type × lag bin で mean_delta_C を集計、curve として記録.

    シンプル版: 各 relation_path_type について、target cid の post_event_state を
    lag 0, 10, 20, ..., 1000 で取得、mean delta_C を curve として算出する.
    """
    df_pulse = safe_read_csv(PULSE_DIR / f"pulse_log_seed{seed}.csv")
    df_bd = safe_read_csv(BAL_DIR / f"balance_decisions_seed{seed}.csv")

    # bd_q を per-target sorted で
    bd_q = df_bd[["observer_cid", "step", "C_at_decision"]].rename(
        columns={"observer_cid": "target_cid", "step": "ts"}
    ).sort_values(["target_cid", "ts"]).reset_index(drop=True)

    # df_targets: (event_id, target_cid, timestamp, relation_path_type)
    base = df_targets[["event_id", "source_cid", "timestamp", "target_cid",
                          "relation_path_type"]].copy()
    base["target_cid"] = base["target_cid"].astype(int)

    rows = []
    sample = base
    if len(base) > 50000:
        # smoke で重い場合のサブサンプル (relation_path 別均等)
        sample = base.groupby("relation_path_type", group_keys=False).apply(
            lambda g: g.sample(n=min(5000, len(g)), random_state=42)
        )
    print(f"  peak_lag sample size: {len(sample):,} (from {len(base):,})")

    # pre C
    sample = sample.copy()
    sample["_orig_idx"] = np.arange(len(sample))
    sample_sorted = sample.sort_values("timestamp", kind="mergesort").reset_index(drop=True)
    bd_q_sorted = bd_q.rename(columns={"ts": "timestamp"}).sort_values(
        "timestamp", kind="mergesort"
    ).reset_index(drop=True)
    pre_merged = pd.merge_asof(
        sample_sorted, bd_q_sorted, on="timestamp", by="target_cid",
        direction="backward",
    ).rename(columns={"C_at_decision": "C_pre"})
    sample = pre_merged.sort_values("_orig_idx").reset_index(drop=True).drop(
        columns=["_orig_idx"]
    )
    sample["C_pre"] = sample["C_pre"].fillna(0.0)

    # 各 lag bin で post C を取得
    for lag in LAG_BINS:
        sample[f"_post_t_{lag}"] = sample["timestamp"] + lag
        sample["_orig_idx"] = np.arange(len(sample))
        ss = sample.sort_values(f"_post_t_{lag}", kind="mergesort").reset_index(drop=True)
        bd_q_temp = bd_q.rename(columns={"ts": f"_post_t_{lag}"}).sort_values(
            f"_post_t_{lag}", kind="mergesort"
        ).reset_index(drop=True)
        merged = pd.merge_asof(
            ss, bd_q_temp, on=f"_post_t_{lag}", by="target_cid",
            direction="backward",
        ).rename(columns={"C_at_decision": f"C_post_lag{lag}"})
        sample = merged.sort_values("_orig_idx").reset_index(drop=True).drop(
            columns=["_orig_idx"]
        )
        sample[f"C_post_lag{lag}"] = sample[f"C_post_lag{lag}"].fillna(0.0)
        sample[f"delta_C_lag{lag}"] = sample[f"C_post_lag{lag}"] - sample["C_pre"]
        sample = sample.drop(columns=[f"C_post_lag{lag}", f"_post_t_{lag}"])

    # 集計: relation_path_type × lag で mean delta_C
    out_rows = []
    for path, sub in sample.groupby("relation_path_type"):
        for lag in LAG_BINS:
            out_rows.append({
                "relation_path_type": path,
                "lag_bin": lag,
                "n_records": int(len(sub)),
                "mean_delta_C_at_lag": float(sub[f"delta_C_lag{lag}"].mean()),
                "median_delta_C_at_lag": float(sub[f"delta_C_lag{lag}"].median()),
            })
    df_curve = pd.DataFrame(out_rows)
    df_curve["seed"] = seed
    return df_curve


def compute_peak_lag_per_path(df_curve: pd.DataFrame) -> pd.DataFrame:
    """各 relation_path_type の peak_lag を argmax で同定."""
    rows = []
    for path, sub in df_curve.groupby("relation_path_type"):
        sub = sub.sort_values("lag_bin").reset_index(drop=True)
        abs_curve = sub["mean_delta_C_at_lag"].abs()
        peak_idx = abs_curve.idxmax()
        peak_lag = int(sub.loc[peak_idx, "lag_bin"])
        peak_value = float(sub.loc[peak_idx, "mean_delta_C_at_lag"])
        rows.append({
            "relation_path_type": path,
            "peak_lag": peak_lag,
            "peak_mean_delta_C": peak_value,
            "abs_peak_value": float(abs_curve.iloc[peak_idx]),
            "curve_max": float(sub["mean_delta_C_at_lag"].max()),
            "curve_min": float(sub["mean_delta_C_at_lag"].min()),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 5. 波及パターン分類
# ----------------------------------------------------------------------
def classify_wave_patterns(df_peak: pd.DataFrame, df_curve: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in df_peak.iterrows():
        path = r["relation_path_type"]
        peak_lag = int(r["peak_lag"])
        sub = df_curve[df_curve["relation_path_type"] == path].sort_values("lag_bin")
        sub_abs = sub["mean_delta_C_at_lag"].abs().values
        # 即時型: peak_lag < 10
        # 遅延型: peak_lag > 100
        # 残響型: 複数のピーク (local max が 2 つ以上)
        local_maxes = 0
        for i in range(1, len(sub_abs) - 1):
            if sub_abs[i] > sub_abs[i - 1] and sub_abs[i] > sub_abs[i + 1] and \
               sub_abs[i] > 0.001:
                local_maxes += 1
        if local_maxes >= 2:
            wave_class = "echo"  # 残響型
        elif peak_lag < 10:
            wave_class = "immediate"
        elif peak_lag > 100:
            wave_class = "delayed"
        else:
            wave_class = "short_term"
        rows.append({
            "relation_path_type": path,
            "peak_lag": peak_lag,
            "n_local_maxes": local_maxes,
            "wave_pattern_class": wave_class,
            "abs_peak_value": float(r["abs_peak_value"]),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    args = ap.parse_args()

    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    out_root.mkdir(parents=True, exist_ok=True)
    seeds = [0] if args.mode == "smoke" else SEEDS
    print(f"v10.7 avalanche + peak_lag - mode={args.mode}, seeds={seeds}")

    summaries = []
    t0 = time.time()
    for seed in seeds:
        ts = time.time()
        if args.mode == "smoke":
            ev_path = SMOKE_ROOT / f"source_events_seed{seed}.parquet"
            rp_path = SMOKE_ROOT / f"relation_paths_seed{seed}.parquet"
            ex_path = SMOKE_ROOT / f"excess_change_seed{seed}.parquet"
            tg_path = SMOKE_ROOT / f"baselines_with_delta_seed{seed}.parquet"
        else:
            ev_path = MAIN_ROOT / "source_events" / f"source_events_seed{seed}.parquet"
            rp_path = MAIN_ROOT / "relation_paths" / f"relation_paths_seed{seed}.parquet"
            ex_path = MAIN_ROOT / "excess_change" / f"excess_change_seed{seed}.parquet"
            tg_path = MAIN_ROOT / "baselines_with_delta" / f"baselines_with_delta_seed{seed}.parquet"

        if not all(p.exists() for p in [ev_path, rp_path, ex_path, tg_path]):
            print(f"  WARN: prerequisite outputs missing for seed {seed}")
            continue

        src_ev = pd.read_parquet(ev_path)
        rp = pd.read_parquet(rp_path)
        ex = pd.read_parquet(ex_path)
        tg = pd.read_parquet(tg_path)

        # 1. multi-hop
        df_mh = build_multi_hop_paths(seed, src_ev)
        out_mh = out_root / f"multi_hop_paths_seed{seed}.parquet"
        if args.mode == "main":
            out_mh = MAIN_ROOT / "multi_hop_paths" / f"multi_hop_paths_seed{seed}.parquet"
        safe_write_parquet_v107(df_mh, out_mh)

        # 2. 減衰率: multi_hop の hop 別 path_type で excess_change を集計するため、
        # multi_hop に対して baseline_constructor を再 run する代わりに、簡略化:
        # 既存 excess_change から familiarity_hop{1,2,3} を抽出
        # ただし Step E は familiarity (1-hop) しか持たないので、Step F では
        # multi_hop の hop 数 別の cid 集合を Step E excess の対応 cid と join する
        # 実装簡略化: rp + multi_hop を統合して compute_decay_rate
        rp_with_mh = pd.concat([rp, df_mh], ignore_index=True)
        # familiarity_hop1 を familiarity と同義として記録 (Step E 互換)
        # ただし Step E excess_change の familiarity row は hop 1 に相当
        # Step F の multi_hop は hop 2, 3 のみ追加で、hop 1 は既に Step E にある
        # 集計: familiarity (Step E hop 1) + familiarity_hop2/3 (Step F)
        ex_with_hop = ex.copy()
        ex_with_hop.loc[ex_with_hop["relation_path_type"] == "familiarity",
                         "relation_path_type"] = "familiarity_hop1"
        df_decay = compute_decay_rate(ex_with_hop, df_mh)
        out_d = out_root / f"decay_rate_seed{seed}.parquet"
        if args.mode == "main":
            out_d = MAIN_ROOT / "decay_rate" / f"decay_rate_seed{seed}.parquet"
        safe_write_parquet_v107(df_decay, out_d)

        # 3. 共鳴ループ
        df_loops = detect_resonance_loops(seed)
        out_l = out_root / f"resonance_loops_seed{seed}.parquet"
        if args.mode == "main":
            out_l = MAIN_ROOT / "resonance_loops" / f"resonance_loops_seed{seed}.parquet"
        safe_write_parquet_v107(df_loops, out_l)

        # 4. peak_lag curve
        df_curve = compute_peak_lag_curve(seed, tg)
        out_c = out_root / f"peak_lag_curve_seed{seed}.parquet"
        if args.mode == "main":
            out_c = MAIN_ROOT / "peak_lag_curve" / f"peak_lag_curve_seed{seed}.parquet"
        safe_write_parquet_v107(df_curve, out_c)

        # 5. 波及パターン
        df_peak = compute_peak_lag_per_path(df_curve)
        df_wave = classify_wave_patterns(df_peak, df_curve)
        df_wave["seed"] = seed
        out_w = out_root / f"wave_patterns_seed{seed}.parquet"
        if args.mode == "main":
            out_w = MAIN_ROOT / "wave_patterns" / f"wave_patterns_seed{seed}.parquet"
        safe_write_parquet_v107(df_wave, out_w)

        elapsed = time.time() - ts
        summary = {
            "seed": seed,
            "n_multi_hop_records": int(len(df_mh)),
            "n_decay_rows": int(len(df_decay)),
            "n_loop_2_hop": int((df_loops.get("loop_type") == "loop_2_hop").sum())
                if not df_loops.empty else 0,
            "n_loop_3_hop": int((df_loops.get("loop_type") == "loop_3_hop").sum())
                if not df_loops.empty else 0,
            "n_curve_rows": int(len(df_curve)),
            "n_wave_classes": int(len(df_wave)),
            "elapsed_sec": round(elapsed, 2),
        }
        print(f"  seed={seed}: mh={summary['n_multi_hop_records']:,}, "
              f"loops_2={summary['n_loop_2_hop']}, loops_3={summary['n_loop_3_hop']}, "
              f"curve={summary['n_curve_rows']}, waves={summary['n_wave_classes']}, "
              f"elapsed={elapsed:.1f}s")
        summaries.append(summary)

    df_sum = pd.DataFrame(summaries)
    sum_path = out_root / "step_f_run_summary.parquet"
    if args.mode == "main":
        sum_path = MAIN_ROOT / "step_f_run_summary.parquet"
    safe_write_parquet_v107(df_sum, sum_path)
    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s, output = {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
