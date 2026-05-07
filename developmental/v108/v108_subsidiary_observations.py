#!/usr/bin/env python3
"""v10.8 副次観察 3 件 (Step F).

1. Whiteout 監視 (Gemini A1)
   - 25 atom × 25 atom = 300 ペア (対角除く)
   - 各 atom の波及プロファイル (delta vector) の相関係数
   - 0.7 以上で whiteout_flag

2. Small-World 維持 (Gemini A6)
   - v10.7 vs v10.8 の loop_2_hop / loop_3_hop 比較
   - Step D smoke で既に同一値確認済 (構造的に不変)

3. 誤差分布の形状観察 (Gemini A5、Taka 示唆)
   - 25 atom × 5 relation_path × 3 window で delta 分布
   - mean / std / skewness / kurtosis / bimodality coefficient
   - 形状ラベル (normal / skewed / bimodal / other)
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V107_ROOT = (REPO_ROOT / "developmental" / "v107").resolve()
V108_ROOT = (REPO_ROOT / "developmental" / "v108").resolve()

V107_MAIN_OUT = V107_ROOT / "outputs" / "main"
OUT_ROOT = V108_ROOT / "outputs"
SMOKE_ROOT = OUT_ROOT / "smoke"
MAIN_ROOT = OUT_ROOT / "main"

SEEDS = list(range(24))
WHITEOUT_THRESHOLD = 0.7
BIMODALITY_THRESHOLD = 5.0 / 9.0  # ~0.555 (Sarle's formula)
RELATION_PATHS = [
    "familiarity", "attention_via_salience",
    "integration_alpha", "integration_beta", "temporal_coactivation",
]
DELTA_FIELDS_BY_WIN = {
    "immediate": ["mean_delta_R_familiarity_immediate",
                    "mean_delta_Q_immediate", "mean_delta_C_immediate",
                    "mean_delta_n_alphas_immediate",
                    "mean_delta_n_observed_immediate",
                    "mean_n_pulses_in_window_immediate"],
    "short": ["mean_delta_R_familiarity_short", "mean_delta_Q_short",
                "mean_delta_C_short", "mean_delta_n_alphas_short",
                "mean_delta_n_observed_short",
                "mean_n_pulses_in_window_short"],
    "medium": ["mean_delta_R_familiarity_medium", "mean_delta_Q_medium",
                "mean_delta_C_medium", "mean_delta_n_alphas_medium",
                "mean_delta_n_observed_medium",
                "mean_n_pulses_in_window_medium"],
}


def assert_output_under_v108(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V108_ROOT not in abs_path.parents and abs_path != V108_ROOT:
        raise ValueError(f"Output path {path} not under v108/")


def safe_write_parquet_v108(df: pd.DataFrame, path: Path) -> None:
    assert_output_under_v108(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


# ----------------------------------------------------------------------
# 1. Whiteout 監視
# ----------------------------------------------------------------------
def compute_atom_profile_vectors(df_excess: pd.DataFrame, df_src: pd.DataFrame,
                                    delta_fields: list[str]) -> pd.DataFrame:
    """各 atom_id ごとに mean delta vector を計算."""
    atom_events = df_src[df_src["event_source_type"] == "atom_introduction_event"][
        ["event_id", "atom_id"]
    ]
    df = df_excess.merge(atom_events, on="event_id", how="inner")
    profile = df.groupby("atom_id")[delta_fields].mean()
    return profile


def compute_whiteout_correlations(profile: pd.DataFrame, seed: int) -> pd.DataFrame:
    """25 atom 間で波及プロファイル相関係数を計算."""
    atoms = profile.index.tolist()
    rows = []
    for i, atom_a in enumerate(atoms):
        for j, atom_b in enumerate(atoms):
            if i >= j:
                continue
            vec_a = profile.loc[atom_a].to_numpy()
            vec_b = profile.loc[atom_b].to_numpy()
            if np.std(vec_a) == 0 or np.std(vec_b) == 0:
                corr = 0.0
            else:
                corr = float(np.corrcoef(vec_a, vec_b)[0, 1])
            rows.append({
                "seed": seed,
                "atom_id_a": atom_a, "atom_id_b": atom_b,
                "correlation_coefficient": corr,
                "whiteout_flag": abs(corr) >= WHITEOUT_THRESHOLD,
            })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 2. Small-World 維持
# ----------------------------------------------------------------------
def compare_smallworld(seed: int, in_root: Path) -> pd.DataFrame:
    """v10.7 vs v10.8 の loop_2_hop / loop_3_hop を比較."""
    v107_loops_path = V107_MAIN_OUT / f"resonance_loops_seed{seed}.parquet"
    v108_loops_path = in_root / f"resonance_loops_seed{seed}.parquet"
    if not (v107_loops_path.exists() and v108_loops_path.exists()):
        return pd.DataFrame()
    df_v107 = pd.read_parquet(v107_loops_path)
    df_v108 = pd.read_parquet(v108_loops_path)

    v107_l2 = (df_v107["loop_type"] == "loop_2_hop").sum() if not df_v107.empty else 0
    v107_l3 = (df_v107["loop_type"] == "loop_3_hop").sum() if not df_v107.empty else 0
    v108_l2 = (df_v108["loop_type"] == "loop_2_hop").sum() if not df_v108.empty else 0
    v108_l3 = (df_v108["loop_type"] == "loop_3_hop").sum() if not df_v108.empty else 0

    ratio_2 = v108_l2 / v107_l2 if v107_l2 > 0 else 1.0
    ratio_3 = v108_l3 / v107_l3 if v107_l3 > 0 else 1.0
    maintenance_2 = abs(ratio_2 - 1.0) <= 0.2
    maintenance_3 = abs(ratio_3 - 1.0) <= 0.2

    return pd.DataFrame([{
        "seed": seed,
        "v107_loop_2_hop": int(v107_l2), "v108_loop_2_hop": int(v108_l2),
        "v107_loop_3_hop": int(v107_l3), "v108_loop_3_hop": int(v108_l3),
        "ratio_2_hop": float(ratio_2), "ratio_3_hop": float(ratio_3),
        "maintenance_flag_2": maintenance_2, "maintenance_flag_3": maintenance_3,
        "maintenance_flag_overall": maintenance_2 and maintenance_3,
    }])


# ----------------------------------------------------------------------
# 3. 誤差分布の形状観察
# ----------------------------------------------------------------------
def sarle_bimodality_coefficient(arr: np.ndarray) -> float:
    """Sarle's bimodality coefficient.
    b = (g^2 + 1) / (k + 3 * (n-1)^2 / ((n-2)*(n-3)))
    g: skewness, k: excess kurtosis, n: sample size
    b > 5/9 で多峰性疑い.
    """
    n = len(arr)
    if n < 4:
        return 0.0
    g = skew(arr, bias=False)
    k = kurtosis(arr, fisher=True, bias=False)  # excess kurtosis
    correction = 3.0 * (n - 1) ** 2 / ((n - 2) * (n - 3))
    return float((g ** 2 + 1) / (k + correction))


def classify_distribution_shape(skewness: float, kurt: float, bimodality: float) -> str:
    if bimodality > BIMODALITY_THRESHOLD:
        return "bimodal"
    if abs(skewness) > 1.0:
        return "skewed"
    if kurt > 3.0:
        return "heavy_tail"
    if abs(skewness) < 0.5 and abs(kurt) < 1.0:
        return "normal"
    return "other"


def compute_error_distribution(df_baselines_with_delta: pd.DataFrame,
                                  df_src: pd.DataFrame, seed: int) -> pd.DataFrame:
    """25 atom × 5 path × 3 window で delta 分布の形状観察."""
    atom_events = df_src[df_src["event_source_type"] == "atom_introduction_event"][
        ["event_id", "atom_id"]
    ]
    df = df_baselines_with_delta.merge(atom_events, on="event_id", how="inner")

    rows = []
    for atom_id, sub in df.groupby("atom_id"):
        for path in RELATION_PATHS:
            sub_p = sub[sub["relation_path_type"] == path]
            for win, fields in DELTA_FIELDS_BY_WIN.items():
                # 6 量 × delta は別、ここでは delta_C_<win> を観察対象にする
                col = f"delta_C_{win}"
                if col not in sub_p.columns:
                    continue
                vals = sub_p[col].dropna().values
                if len(vals) < 10:
                    continue
                mean = float(np.mean(vals))
                median = float(np.median(vals))
                std = float(np.std(vals))
                sk = float(skew(vals, bias=False)) if len(vals) >= 8 else 0.0
                kr = float(kurtosis(vals, fisher=True, bias=False)) if len(vals) >= 8 else 0.0
                bm = sarle_bimodality_coefficient(vals)
                shape = classify_distribution_shape(sk, kr, bm)
                rows.append({
                    "seed": seed,
                    "atom_id": atom_id, "relation_path_type": path,
                    "observation_window": win, "n_samples": len(vals),
                    "mean": mean, "median": median, "std": std,
                    "skewness": sk, "kurtosis": kr,
                    "bimodality_coefficient": bm,
                    "distribution_shape_label": shape,
                })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Per-seed pipeline
# ----------------------------------------------------------------------
def run_seed_step_f(seed: int, in_root: Path, out_root: Path) -> dict:
    summary = {"seed": seed}
    t0 = time.time()

    # 入力読み込み
    df_excess = pd.read_parquet(in_root / f"excess_change_seed{seed}.parquet")
    df_src = pd.read_parquet(in_root / f"source_events_seed{seed}.parquet")
    df_blwd = pd.read_parquet(in_root / f"baselines_with_delta_seed{seed}.parquet")

    # delta フィールド (medium window) で profile vector
    medium_fields = DELTA_FIELDS_BY_WIN["medium"]

    # 1. Whiteout
    t = time.time()
    profile = compute_atom_profile_vectors(df_excess, df_src, medium_fields)
    df_whiteout = compute_whiteout_correlations(profile, seed)
    safe_write_parquet_v108(
        df_whiteout, out_root / f"whiteout_monitor_seed{seed}.parquet"
    )
    summary["t_whiteout"] = round(time.time() - t, 2)
    summary["n_whiteout_pairs"] = len(df_whiteout)
    summary["n_whiteout_flagged"] = int(df_whiteout["whiteout_flag"].sum())
    summary["whiteout_corr_max"] = float(df_whiteout["correlation_coefficient"].abs().max()) \
        if not df_whiteout.empty else 0.0

    # 2. Small-World
    t = time.time()
    df_sw = compare_smallworld(seed, in_root)
    safe_write_parquet_v108(
        df_sw, out_root / f"smallworld_comparison_seed{seed}.parquet"
    )
    summary["t_smallworld"] = round(time.time() - t, 2)
    if not df_sw.empty:
        r = df_sw.iloc[0]
        summary["v107_loop_2"] = int(r["v107_loop_2_hop"])
        summary["v108_loop_2"] = int(r["v108_loop_2_hop"])
        summary["v107_loop_3"] = int(r["v107_loop_3_hop"])
        summary["v108_loop_3"] = int(r["v108_loop_3_hop"])
        summary["smallworld_maintained"] = bool(r["maintenance_flag_overall"])

    # 3. 誤差分布
    t = time.time()
    df_err = compute_error_distribution(df_blwd, df_src, seed)
    safe_write_parquet_v108(
        df_err, out_root / f"error_distribution_seed{seed}.parquet"
    )
    summary["t_error_dist"] = round(time.time() - t, 2)
    summary["n_error_dist_rows"] = len(df_err)
    if not df_err.empty:
        shape_counts = df_err["distribution_shape_label"].value_counts().to_dict()
        summary["shape_counts"] = str(shape_counts)
        summary["n_bimodal"] = int((df_err["distribution_shape_label"] == "bimodal").sum())

    summary["t_total"] = round(time.time() - t0, 2)
    return summary


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    args = ap.parse_args()

    in_root = SMOKE_ROOT if args.mode == "smoke" else MAIN_ROOT
    out_root = in_root
    seeds = [0] if args.mode == "smoke" else SEEDS
    print(f"v10.8 副次観察 (Whiteout / Small-World / 誤差分布) - "
          f"mode={args.mode}, seeds={seeds}")

    summaries = []
    t0 = time.time()
    for seed in seeds:
        s = run_seed_step_f(seed, in_root, out_root)
        print(f"  seed={s['seed']}: "
              f"whiteout={s['n_whiteout_flagged']}/{s['n_whiteout_pairs']} (max_corr={s['whiteout_corr_max']:.3f}), "
              f"smallworld(v107/v108): l2={s.get('v107_loop_2', '?')}/{s.get('v108_loop_2', '?')} "
              f"l3={s.get('v107_loop_3', '?')}/{s.get('v108_loop_3', '?')} "
              f"maintained={s.get('smallworld_maintained', '?')}, "
              f"error_dist={s['n_error_dist_rows']} rows ({s.get('shape_counts', '')}), "
              f"t={s['t_total']}s")
        summaries.append(s)

    df_sum = pd.DataFrame(summaries)
    safe_write_parquet_v108(df_sum, out_root / "step_f_run_summary.parquet")
    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s, output = {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
