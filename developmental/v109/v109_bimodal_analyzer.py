#!/usr/bin/env python3
"""v10.9 bimodal structural analyzer (Step E、即決 §2.5 + §3.1-3.3).

入力:
  - v108 main error_distribution_seed*.parquet (1,540 件 bimodal セル)
  - v108 main baselines_with_delta_seed*.parquet (delta 値元データ)
  - v108 main source_events_seed*.parquet (event_id × atom_id × source_cid)

処理 (各 (seed, atom_id, path, window) の bimodal セルについて):
  1. delta_C_{win} 値集合 vals 取得
  2. bimodal_subtype 判定 (sparse_outlier / mixed / genuine)
  3. genuine の場合 KDE + find_peaks で 2 ピーク抽出 (= peak_high_value, peak_low_value)
       KDE で 2 ピーク取れない場合は median-split fallback
  4. 各 (target_cid) を high/low 群に分類 (delta に最も近いピーク)
  5. 3 仮説で Cohen's d 効果量計算
       H1: target_cid の n_core_member 高 vs 低
       H2: target_cid が α/β に所属するか
       H3: target_cid の age (event_ts - target_birth_step) 高 vs 低
  6. 最大 effect_size の仮説を選択、閾値 0.3 未満は "unclassified"

出力:
  developmental/v109/outputs/{smoke,main}/
    bimodal_analysis_seed{N}.parquet
"""
from __future__ import annotations

import argparse
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy.stats import gaussian_kde

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V107_ROOT = (REPO_ROOT / "developmental" / "v107").resolve()
V108_ROOT = (REPO_ROOT / "developmental" / "v108").resolve()
V109_ROOT = (REPO_ROOT / "developmental" / "v109").resolve()

V108_MAIN = V108_ROOT / "outputs" / "main"

OUT_ROOT = V109_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"

sys.path.insert(0, str(V107_ROOT))
from v107_baseline_constructor import (  # noqa: E402
    _cid_meta_table, _build_alpha_beta_membership,
)

SEEDS = list(range(24))
N_SAMPLES_THRESHOLD = 10  # KDE 試行最低サンプル数 (即決 §3.1: 30 → 実情 10 に下げ)
EFFECT_SIZE_THRESHOLD = 0.3  # 即決 §3.3 unclassified 閾値
KDE_PROMINENCE_FRAC = 0.05  # find_peaks prominence (density.max の何 %)
SPARSE_UNIQUE_MAX = 5  # unique value <= 5 で sparse 判定
SPARSE_PCT_ZERO = 95.0  # zero 割合 95% 以上で sparse


def assert_output_under_v109(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V109_ROOT not in abs_path.parents and abs_path != V109_ROOT:
        raise ValueError(f"Output path {path} not under v109/")


def safe_write_parquet_v109(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v109(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


def classify_bimodal_subtype(vals: np.ndarray) -> str:
    if len(vals) == 0:
        return "empty"
    n_unique = len(np.unique(vals))
    pct_zero = (vals == 0).sum() / len(vals) * 100
    if n_unique <= SPARSE_UNIQUE_MAX and pct_zero >= SPARSE_PCT_ZERO:
        return "sparse_outlier"
    if n_unique <= SPARSE_UNIQUE_MAX:
        return "discrete_bimodal"
    return "genuine_bimodal"


def find_kde_peaks(vals: np.ndarray) -> dict | None:
    """KDE + find_peaks で 2 ピークを抽出。取れなければ None."""
    if len(vals) < N_SAMPLES_THRESHOLD:
        return None
    if vals.std() == 0:
        return None
    try:
        kde = gaussian_kde(vals)
    except Exception:
        return None
    pad = max(vals.std() * 0.5, 0.1)
    x_grid = np.linspace(vals.min() - pad, vals.max() + pad, 500)
    density = kde(x_grid)
    peaks_idx, props = find_peaks(density, prominence=density.max() * KDE_PROMINENCE_FRAC)
    if len(peaks_idx) < 2:
        return None
    sorted_peaks = sorted(peaks_idx, key=lambda i: -density[i])[:2]
    h_idx = max(sorted_peaks, key=lambda i: x_grid[i])
    l_idx = min(sorted_peaks, key=lambda i: x_grid[i])
    return {
        "peak_high_value": float(x_grid[h_idx]),
        "peak_high_density": float(density[h_idx]),
        "peak_low_value": float(x_grid[l_idx]),
        "peak_low_density": float(density[l_idx]),
        "method": "kde",
    }


def median_split_peaks(vals: np.ndarray) -> dict:
    """KDE 失敗時の fallback: 中央値分割で high/low の代表値を取る."""
    med = float(np.median(vals))
    high_vals = vals[vals > med]
    low_vals = vals[vals <= med]
    return {
        "peak_high_value": float(np.mean(high_vals)) if len(high_vals) else med,
        "peak_high_density": float("nan"),
        "peak_low_value": float(np.mean(low_vals)) if len(low_vals) else med,
        "peak_low_density": float("nan"),
        "method": "median_split",
    }


def cohens_d(group_a: np.ndarray, group_b: np.ndarray) -> float:
    if len(group_a) < 2 or len(group_b) < 2:
        return 0.0
    mean_a = float(np.mean(group_a))
    mean_b = float(np.mean(group_b))
    var_a = float(np.var(group_a, ddof=1))
    var_b = float(np.var(group_b, ddof=1))
    pooled_var = (var_a * (len(group_a) - 1) + var_b * (len(group_b) - 1)) / (len(group_a) + len(group_b) - 2)
    if pooled_var <= 0:
        return 0.0
    return abs(mean_a - mean_b) / np.sqrt(pooled_var)


def evaluate_hypotheses(df_cid: pd.DataFrame, peaks: dict,
                          cid_meta: pd.DataFrame, membership: dict) -> dict:
    """3 仮説評価。df_cid の各行に target_cid + delta_value 列が必要."""
    delta = df_cid["delta_value"].values
    midpoint = (peaks["peak_high_value"] + peaks["peak_low_value"]) / 2
    is_high = delta >= midpoint
    df_cid = df_cid.copy()
    df_cid["group_high"] = is_high

    # cid_meta との merge (target_cid -> n_core_member, birth_step, alpha/beta 内外)
    merged = df_cid.merge(
        cid_meta[["cognitive_id", "n_core_member", "birth_step"]].rename(
            columns={"cognitive_id": "target_cid"}
        ), on="target_cid", how="left"
    )
    merged["in_integration"] = merged["target_cid"].apply(
        lambda c: 1 if int(c) in membership and len(membership[int(c)]) > 0 else 0
    )
    merged["age_at_event"] = (merged["event_ts"] - merged["birth_step"]).clip(lower=0)

    high = merged[merged["group_high"]]
    low = merged[~merged["group_high"]]

    h1_a = high["n_core_member"].dropna().values
    h1_b = low["n_core_member"].dropna().values
    h1_d = cohens_d(h1_a, h1_b)

    h2_a = high["in_integration"].dropna().values
    h2_b = low["in_integration"].dropna().values
    h2_d = cohens_d(h2_a, h2_b)

    h3_a = high["age_at_event"].dropna().values
    h3_b = low["age_at_event"].dropna().values
    h3_d = cohens_d(h3_a, h3_b)

    scores = {"H1_n_core": h1_d, "H2_integration": h2_d, "H3_lifecycle": h3_d}
    best_name = max(scores, key=scores.get)
    best_score = scores[best_name]

    return {
        "n_high": int(len(high)), "n_low": int(len(low)),
        "h1_n_core_d": h1_d, "h1_high_mean": float(np.mean(h1_a)) if len(h1_a) else float("nan"),
        "h1_low_mean": float(np.mean(h1_b)) if len(h1_b) else float("nan"),
        "h2_integration_d": h2_d, "h2_high_pct": float(np.mean(h2_a)) if len(h2_a) else float("nan"),
        "h2_low_pct": float(np.mean(h2_b)) if len(h2_b) else float("nan"),
        "h3_lifecycle_d": h3_d, "h3_high_age_mean": float(np.mean(h3_a)) if len(h3_a) else float("nan"),
        "h3_low_age_mean": float(np.mean(h3_b)) if len(h3_b) else float("nan"),
        "best_hypothesis": best_name if best_score >= EFFECT_SIZE_THRESHOLD else "unclassified",
        "best_effect_size": float(best_score),
    }


def analyze_seed(seed: int, mode: str = "main") -> pd.DataFrame:
    """seed 内の全 bimodal セルを解析。"""
    err_path = V108_MAIN / f"error_distribution_seed{seed}.parquet"
    bld_path = V108_MAIN / f"baselines_with_delta_seed{seed}.parquet"
    src_path = V108_MAIN / f"source_events_seed{seed}.parquet"

    df_err = pd.read_parquet(err_path)
    bim = df_err[df_err["distribution_shape_label"] == "bimodal"].copy()
    if bim.empty:
        return pd.DataFrame()
    df_bld = pd.read_parquet(bld_path)
    df_src = pd.read_parquet(src_path)

    cid_meta = _cid_meta_table(seed)
    membership = _build_alpha_beta_membership(seed)

    # atom_id × event_id map (atom_introduction_event のみ)
    atom_evs = df_src[df_src["event_source_type"] == "atom_introduction_event"][
        ["event_id", "atom_id", "timestamp"]
    ]

    rows = []
    for _, target in bim.iterrows():
        atom_id = target["atom_id"]
        path = target["relation_path_type"]
        win = target["observation_window"]
        col = f"delta_C_{win}"

        atom_evs_sub = atom_evs[atom_evs["atom_id"] == atom_id]
        sub = df_bld[
            (df_bld["event_id"].isin(atom_evs_sub["event_id"]))
            & (df_bld["relation_path_type"] == path)
        ][["event_id", "target_cid", col]].dropna()

        if sub.empty:
            continue
        # event timestamp を attach (lifecycle age 用)
        sub = sub.merge(atom_evs_sub[["event_id", "timestamp"]], on="event_id", how="left").rename(
            columns={"timestamp": "event_ts", col: "delta_value"}
        )
        vals = sub["delta_value"].values
        subtype = classify_bimodal_subtype(vals)

        row = {
            "seed": int(seed), "atom_id": atom_id,
            "relation_path_type": path, "observation_window": win,
            "n_samples": int(len(vals)), "subtype": subtype,
            "n_unique": int(len(np.unique(vals))),
            "pct_zero": float((vals == 0).sum() / len(vals) * 100),
            "min": float(vals.min()), "max": float(vals.max()),
            "std": float(vals.std()),
            "bimodality_coefficient": float(target["bimodality_coefficient"]),
        }
        # KDE attempt
        peaks = find_kde_peaks(vals) if subtype == "genuine_bimodal" else None
        if peaks is None:
            peaks = median_split_peaks(vals)
        row.update({
            "peak_method": peaks["method"],
            "peak_high_value": peaks["peak_high_value"],
            "peak_low_value": peaks["peak_low_value"],
            "peak_high_density": peaks["peak_high_density"],
            "peak_low_density": peaks["peak_low_density"],
        })
        # 仮説評価 (subtype 問わず実施、ただし "sparse_outlier" は参考値)
        hyp = evaluate_hypotheses(sub[["target_cid", "delta_value", "event_ts"]],
                                       peaks, cid_meta, membership)
        row.update(hyp)
        rows.append(row)
    return pd.DataFrame(rows)


def _worker(args):
    seed, mode = args
    return analyze_seed(seed, mode)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    ap.add_argument("--n_workers", type=int, default=24)
    args = ap.parse_args()

    out_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    out_root.mkdir(parents=True, exist_ok=True)
    seeds = [0] if args.mode == "smoke" else SEEDS

    print(f"v10.9 bimodal analyzer - mode={args.mode}, seeds={len(seeds)}, n_workers={args.n_workers}")
    n_workers = max(1, min(args.n_workers, len(seeds)))

    t0 = time.time()
    if n_workers > 1 and len(seeds) > 1:
        print(f"=== 並列実行 ({n_workers} workers、24 seeds 単一バッチ) ===")
        with Pool(processes=n_workers) as pool:
            dfs = pool.map(_worker, [(s, args.mode) for s in seeds])
    else:
        print(f"=== 順次実行 ===")
        dfs = [_worker((s, args.mode)) for s in seeds]

    for s, df in zip(seeds, dfs):
        out = out_root / f"bimodal_analysis_seed{s}.parquet"
        if not df.empty:
            safe_write_parquet_v109(df, out)
        st = df["subtype"].value_counts().to_dict() if not df.empty else {}
        bh = df["best_hypothesis"].value_counts().to_dict() if not df.empty else {}
        print(f"  seed={s:>2}: cells={len(df)}, subtypes={st}, best={bh}")

    df_all = pd.concat([d for d in dfs if not d.empty], ignore_index=True)
    if not df_all.empty:
        safe_write_parquet_v109(df_all, out_root / "bimodal_analysis_all.parquet")
        print(f"\n=== cross-seed summary ===")
        print(f"  total cells: {len(df_all)}")
        print(f"  subtypes: {df_all['subtype'].value_counts().to_dict()}")
        print(f"  best_hypothesis (genuine + discrete only):")
        genuine = df_all[df_all["subtype"].isin(["genuine_bimodal", "discrete_bimodal"])]
        print(f"    {genuine['best_hypothesis'].value_counts().to_dict()}")
        print(f"  effect_size (best) describe (genuine only):")
        gen = df_all[df_all["subtype"] == "genuine_bimodal"]
        print(gen["best_effect_size"].describe())

    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
