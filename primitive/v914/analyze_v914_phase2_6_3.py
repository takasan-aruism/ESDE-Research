#!/usr/bin/env python3
"""
v9.14 Phase 2 §6.3 — Shadow-vs-Fixed Overlap Analysis

Compares Layer A fixed pulse (pulse_log) with Layer B event-driven
spend (per_event_audit) by observation timing and information content.

Metrics:
  - Exact overlap (Jaccard on step sets per cid)
  - Neighborhood overlap (±N for N ∈ {5, 10, 25})
  - Independence: only_A / only_B / both (±25 bound)
  - Content comparison: v11_delta ↔ v14_delta_norm correlation on
    exact matches; v11_captured ↔ v14_spend_flag agreement
  - All of the above stratified by n_core bucket (2/3/4/5+)

Convention:
  - Layer A pulses with pulse_n ≤ 3 (v11_captured == "cold_start")
    are excluded (§3.7 recommendation).
  - Step alignment uses `global_step` (per_event) vs `t` (pulse_log),
    which are the same engine step clock.

Output: v914_shadow_overlap.md
Describe only. No conclusions.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
SHORT_DIR = SCRIPT_DIR / "diag_v914_short"
LONG_DIR = SCRIPT_DIR / "diag_v914_long"
OUT_PATH = SCRIPT_DIR / "v914_shadow_overlap.md"

BUCKETS = ["2", "3", "4", "5+"]
NEIGHBORHOODS = [5, 10, 25]


def bucket_of(n: int) -> str:
    if n <= 2:
        return "2"
    if n == 3:
        return "3"
    if n == 4:
        return "4"
    return "5+"


def load_pulse(pulse_dir: Path) -> pd.DataFrame:
    files = sorted(pulse_dir.glob("pulse_log_seed*.csv"))
    frames = []
    for f in files:
        df = pd.read_csv(f)
        frames.append(df)
    pl = pd.concat(frames, ignore_index=True)
    # Exclude cold_start
    pl = pl[pl["pulse_n"] > 3].copy()
    return pl


def load_events(audit_dir: Path) -> pd.DataFrame:
    files = sorted(audit_dir.glob("per_event_audit_seed*.csv"))
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def load_subjects(audit_dir: Path) -> pd.DataFrame:
    files = sorted(audit_dir.glob("per_subject_audit_seed*.csv"))
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def _fmt(x, digits: int = 4) -> str:
    if x is None or (isinstance(x, float) and (np.isnan(x) or not np.isfinite(x))):
        return "-"
    if isinstance(x, (int, np.integer)):
        return f"{int(x):d}"
    return f"{float(x):.{digits}g}"


def _nearest_within(a_steps: np.ndarray, b_steps_sorted: np.ndarray, tol: int) -> np.ndarray:
    """For each element in a_steps, True if ∃ b in b_steps within ±tol."""
    if len(a_steps) == 0:
        return np.zeros(0, dtype=bool)
    if len(b_steps_sorted) == 0:
        return np.zeros(len(a_steps), dtype=bool)
    idx = np.searchsorted(b_steps_sorted, a_steps)
    out = np.zeros(len(a_steps), dtype=bool)
    for i, (a, j) in enumerate(zip(a_steps, idx)):
        if j < len(b_steps_sorted) and abs(b_steps_sorted[j] - a) <= tol:
            out[i] = True
            continue
        if j > 0 and abs(b_steps_sorted[j - 1] - a) <= tol:
            out[i] = True
    return out


def compute_per_cid_overlap(
    pulse_df: pd.DataFrame, event_df: pd.DataFrame, bucket_map: pd.DataFrame
) -> pd.DataFrame:
    """Per (seed, cid) overlap metrics.

    Returns DataFrame with columns:
      seed, cid, bucket, n_A, n_B,
      exact_intersection, exact_union, jaccard,
      matched_A_5, matched_A_10, matched_A_25,
      matched_B_5, matched_B_10, matched_B_25,
      only_A_25, only_B_25, both_25.
    """
    # Pre-group
    pulse_g = dict(tuple(pulse_df.groupby(["seed", "cid"])))
    event_g = dict(tuple(event_df.groupby(["seed", "cid"])))

    bucket_map_dict = {
        (int(r["seed"]), int(r["cid"])): r["bucket"]
        for _, r in bucket_map.iterrows()
    }

    keys = set(pulse_g.keys()) | set(event_g.keys())
    rows = []
    for key in keys:
        A = pulse_g.get(key)
        B = event_g.get(key)
        A_steps = np.sort(A["t"].values.astype(int)) if A is not None else np.array([], dtype=int)
        B_steps = np.sort(B["global_step"].values.astype(int)) if B is not None else np.array([], dtype=int)

        A_set = set(A_steps.tolist())
        B_set = set(B_steps.tolist())
        inter = len(A_set & B_set)
        union = len(A_set | B_set)
        jaccard = inter / union if union > 0 else np.nan

        row = dict(
            seed=int(key[0]),
            cid=int(key[1]),
            bucket=bucket_map_dict.get(key, "?"),
            n_A=len(A_steps),
            n_B=len(B_steps),
            exact_intersection=inter,
            exact_union=union,
            jaccard=jaccard,
        )
        for N in NEIGHBORHOODS:
            matched_A = _nearest_within(A_steps, B_steps, N)
            matched_B = _nearest_within(B_steps, A_steps, N)
            row[f"matched_A_{N}"] = int(matched_A.sum())
            row[f"matched_B_{N}"] = int(matched_B.sum())
        only_A_25 = len(A_steps) - row["matched_A_25"]
        only_B_25 = len(B_steps) - row["matched_B_25"]
        both_25 = row["matched_A_25"]
        row["only_A_25"] = only_A_25
        row["only_B_25"] = only_B_25
        row["both_25"] = both_25
        rows.append(row)
    return pd.DataFrame(rows)


def aggregate_overlap(df: pd.DataFrame, by_bucket: bool = False) -> pd.DataFrame:
    groups = [("all", df)]
    if by_bucket:
        groups = [(b, df[df["bucket"] == b]) for b in BUCKETS]

    rows = []
    for tag, s in groups:
        n_cids = len(s)
        n_A_tot = s["n_A"].sum()
        n_B_tot = s["n_B"].sum()
        inter_tot = s["exact_intersection"].sum()
        union_tot = s["exact_union"].sum()
        jaccard_micro = inter_tot / union_tot if union_tot > 0 else np.nan
        jaccard_macro = s["jaccard"].mean()

        row = dict(
            group=tag,
            n_cids=n_cids,
            n_A_total=int(n_A_tot),
            n_B_total=int(n_B_tot),
            exact_intersection=int(inter_tot),
            exact_union=int(union_tot),
            jaccard_micro=jaccard_micro,
            jaccard_macro_mean=jaccard_macro,
        )
        for N in NEIGHBORHOODS:
            m_A = s[f"matched_A_{N}"].sum()
            m_B = s[f"matched_B_{N}"].sum()
            row[f"match_rate_A_by_B_{N}"] = (
                m_A / n_A_tot if n_A_tot > 0 else np.nan
            )
            row[f"match_rate_B_by_A_{N}"] = (
                m_B / n_B_tot if n_B_tot > 0 else np.nan
            )
        tot_A = int(n_A_tot)
        tot_B = int(n_B_tot)
        m25A = s["matched_A_25"].sum()
        m25B = s["matched_B_25"].sum()
        only_A = tot_A - m25A
        only_B = tot_B - m25B
        both = m25A
        # Share of event perspective (only_A vs only_B vs both — on the union of events)
        total_evs = tot_A + tot_B  # may double-count matches (A and B separately)
        row["only_A_25_count"] = int(only_A)
        row["only_B_25_count"] = int(only_B)
        row["both_25_count_A"] = int(m25A)
        row["both_25_count_B"] = int(m25B)
        row["only_A_25_share_of_A"] = only_A / tot_A if tot_A > 0 else np.nan
        row["only_B_25_share_of_B"] = only_B / tot_B if tot_B > 0 else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def content_comparison(pulse_df: pd.DataFrame, event_df: pd.DataFrame) -> dict:
    """Merge on (seed, cid, step) for exact matches and compute:
        - Pearson r between v11_delta and v14_delta_norm
        - Agreement rate between v11_captured and v14_spend_flag
    """
    p = pulse_df[["seed", "cid", "t", "v11_delta", "v11_captured"]].rename(
        columns={"t": "step"}
    )
    # Collapse potential duplicates on (seed, cid, step) — shouldn't happen
    # for pulse_log but defensive.
    p = p.drop_duplicates(subset=["seed", "cid", "step"], keep="first")

    e = event_df[
        ["seed", "cid", "global_step", "v14_event_type", "v14_delta_norm", "v14_spend_flag"]
    ].rename(columns={"global_step": "step"})
    # Collapse multiple events at the same step per cid (E1/E2/E3 can co-fire);
    # keep max v14_delta_norm & OR the spend flag.
    e_agg = (
        e.groupby(["seed", "cid", "step"], observed=True)
        .agg(
            v14_delta_max=("v14_delta_norm", "max"),
            v14_spend_any=("v14_spend_flag", "any"),
            has_e3=("v14_event_type", lambda s: (s == "E3_contact").any()),
            has_e1e2=(
                "v14_event_type",
                lambda s: s.isin(["E1_death", "E1_birth", "E2_rise", "E2_fall"]).any(),
            ),
        )
        .reset_index()
    )

    merged = p.merge(e_agg, on=["seed", "cid", "step"], how="inner")
    # Captured flag — pulse_log stores "TRUE"/"FALSE"/"cold_start"
    captured_bool = merged["v11_captured"].map(
        {"TRUE": True, "FALSE": False, "True": True, "False": False}
    )
    valid = captured_bool.notna()
    m = merged[valid].copy()
    m["captured"] = captured_bool[valid].astype(bool)

    result = {}
    if len(m) > 1:
        r = np.corrcoef(m["v11_delta"], m["v14_delta_max"])[0, 1]
        result["pearson_all"] = float(r)
    else:
        result["pearson_all"] = float("nan")
    result["n_matches_all"] = int(len(m))
    result["agreement_captured_vs_spend"] = float(
        (m["captured"] == m["v14_spend_any"]).mean()
    ) if len(m) else float("nan")

    # Stratify: matches involving E1/E2 only (no E3) vs matches with E3
    m_e1e2_only = m[m["has_e1e2"] & ~m["has_e3"]]
    m_e3_any = m[m["has_e3"]]
    for tag, sub in [("e1e2_only", m_e1e2_only), ("e3_any", m_e3_any)]:
        result[f"n_matches_{tag}"] = int(len(sub))
        if len(sub) > 1:
            r = np.corrcoef(sub["v11_delta"], sub["v14_delta_max"])[0, 1]
            result[f"pearson_{tag}"] = float(r)
        else:
            result[f"pearson_{tag}"] = float("nan")
        result[f"agreement_{tag}"] = (
            float((sub["captured"] == sub["v14_spend_any"]).mean())
            if len(sub) else float("nan")
        )

    return result


def compute_baseline_expectation(pulse_df: pd.DataFrame, event_df: pd.DataFrame) -> dict:
    """Simple baseline: if Layer B events were uniformly distributed
    over each cid's observation span, expected match rate for A∈B(±N)
    is approximately 1 - (1 - (2N+1)/T)^{n_B} where T is span length.

    We report a population-level approximation: per cid mean of
    p_expected_N = 1 - (1 - (2N+1)/T)^{n_B}, averaged across cids.
    """
    # Compute per-cid span
    p_groups = pulse_df.groupby(["seed", "cid"])
    e_groups = event_df.groupby(["seed", "cid"])

    recs = []
    for key, g in p_groups:
        if g["t"].empty:
            continue
        t_min = int(g["t"].min())
        t_max = int(g["t"].max())
        span = max(1, t_max - t_min + 1)
        n_A = len(g)
        if key in e_groups.groups:
            eg = e_groups.get_group(key)
            n_B = len(eg)
        else:
            n_B = 0
        recs.append((n_A, n_B, span))
    recs = np.array(recs) if recs else np.zeros((0, 3))
    result = {}
    for N in NEIGHBORHOODS:
        if len(recs) == 0:
            result[f"baseline_match_rate_A_by_B_{N}"] = float("nan")
            continue
        p = 1 - (1 - (2 * N + 1) / recs[:, 2]) ** np.where(recs[:, 1] > 0, recs[:, 1], 0)
        # avoid NaN from negative or zero span
        p = np.clip(p, 0, 1)
        weights = recs[:, 0]
        if weights.sum() > 0:
            result[f"baseline_match_rate_A_by_B_{N}"] = float(
                (p * weights).sum() / weights.sum()
            )
        else:
            result[f"baseline_match_rate_A_by_B_{N}"] = float("nan")
    return result


def md_table(df: pd.DataFrame, int_cols: list[str] | None = None) -> str:
    int_cols = int_cols or []
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |\n"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |\n"
    body = ""
    for _, r in df.iterrows():
        vals = []
        for c in cols:
            v = r[c]
            if isinstance(v, str):
                vals.append(v)
            elif c in int_cols:
                vals.append(_fmt(v, 0))
            else:
                vals.append(_fmt(v, 4))
        body += "| " + " | ".join(vals) + " |\n"
    return header + sep + body


def compute_observations(
    short_all, long_all, short_bb, long_bb, short_content, long_content, short_base, long_base
) -> list[str]:
    obs: list[str] = []

    def pick(df, col, g="all"):
        r = df[df["group"] == g]
        if r.empty:
            return None
        return r.iloc[0][col]

    obs.append(
        "Short run: Layer A pulse 数 (cold_start 除外) = "
        f"{_fmt(pick(short_all, 'n_A_total'), 0)}、"
        f"Layer B event 数 = {_fmt(pick(short_all, 'n_B_total'), 0)}、"
        f"exact Jaccard (micro) = {_fmt(pick(short_all, 'jaccard_micro'), 4)}。"
    )
    obs.append(
        "Long run: Layer A pulse 数 = "
        f"{_fmt(pick(long_all, 'n_A_total'), 0)}、"
        f"Layer B event 数 = {_fmt(pick(long_all, 'n_B_total'), 0)}、"
        f"exact Jaccard (micro) = {_fmt(pick(long_all, 'jaccard_micro'), 4)}。"
    )
    obs.append(
        "±25 step 近接マッチ率 (A 基準, long): "
        f"{_fmt(pick(long_all, 'match_rate_A_by_B_25'), 4)} "
        f"(ベースライン均一分布期待 {_fmt(long_base['baseline_match_rate_A_by_B_25'], 4)})。"
    )
    obs.append(
        "±25 step 近接マッチ率 (B 基準, long): "
        f"{_fmt(pick(long_all, 'match_rate_B_by_A_25'), 4)}。"
    )
    obs.append(
        f"Short run の n_core バケット別 ±25 match_rate_A_by_B: "
        f"2={_fmt(pick(short_bb, 'match_rate_A_by_B_25', '2'), 4)}, "
        f"3={_fmt(pick(short_bb, 'match_rate_A_by_B_25', '3'), 4)}, "
        f"4={_fmt(pick(short_bb, 'match_rate_A_by_B_25', '4'), 4)}, "
        f"5+={_fmt(pick(short_bb, 'match_rate_A_by_B_25', '5+'), 4)}。"
    )
    obs.append(
        f"Long run の n_core バケット別 ±25 match_rate_A_by_B: "
        f"2={_fmt(pick(long_bb, 'match_rate_A_by_B_25', '2'), 4)}, "
        f"3={_fmt(pick(long_bb, 'match_rate_A_by_B_25', '3'), 4)}, "
        f"4={_fmt(pick(long_bb, 'match_rate_A_by_B_25', '4'), 4)}, "
        f"5+={_fmt(pick(long_bb, 'match_rate_A_by_B_25', '5+'), 4)}。"
    )
    obs.append(
        f"Long run の only_A_25_share_of_A (±25 で B に未マッチな A の割合) = "
        f"{_fmt(pick(long_all, 'only_A_25_share_of_A'), 4)}、"
        f"only_B_25_share_of_B = {_fmt(pick(long_all, 'only_B_25_share_of_B'), 4)}。"
    )
    obs.append(
        f"Long run exact-match での内容相関 (v11_delta vs v14_delta_norm): "
        f"n={long_content['n_matches_all']}, "
        f"Pearson r = {_fmt(long_content['pearson_all'], 4)}。"
    )
    obs.append(
        f"Long run exact-match での v11_captured と v14_spend_flag の一致率 = "
        f"{_fmt(long_content['agreement_captured_vs_spend'], 4)} "
        f"(n={long_content['n_matches_all']})。"
    )
    obs.append(
        "Long run, E3 を含まない (E1/E2 のみの) exact-match: "
        f"n={long_content['n_matches_e1e2_only']}, "
        f"Pearson r = {_fmt(long_content['pearson_e1e2_only'], 4)}, "
        f"一致率 = {_fmt(long_content['agreement_e1e2_only'], 4)}。"
    )
    obs.append(
        "Long run, E3 を含む exact-match: "
        f"n={long_content['n_matches_e3_any']}, "
        f"Pearson r = {_fmt(long_content['pearson_e3_any'], 4)}, "
        f"一致率 = {_fmt(long_content['agreement_e3_any'], 4)}。"
    )
    return obs


def write_report(
    short_all,
    long_all,
    short_bb,
    long_bb,
    short_content,
    long_content,
    short_base,
    long_base,
    out_path: Path,
) -> None:
    buf: list[str] = []
    buf.append("# v9.14 §6.3 — Shadow-vs-Fixed Overlap\n")
    buf.append("*Phase 2 §6.3 output — Describe only.*\n")
    buf.append("")
    buf.append("## 1. 計算方法\n")
    buf.append(
        "- Layer A: `diag_v914_{short,long}/pulse/pulse_log_seed*.csv` (cid × t)。"
        "cold_start (`pulse_n ≤ 3`) は除外。"
    )
    buf.append(
        "- Layer B: `diag_v914_{short,long}/audit/per_event_audit_seed*.csv` "
        "(cid × global_step × event_type)。"
    )
    buf.append(
        "- Step 軸: pulse_log の `t` と per_event の `global_step` が engine の共通 step 時計。"
    )
    buf.append(
        "- 厳密マッチ (Jaccard): 各 (seed, cid) で A_steps ∩ B_steps / A_steps ∪ B_steps。"
        "全体は micro-average (inter 総和 / union 総和) と macro-mean (cid 平均) の 2 種で記載。"
    )
    buf.append(
        "- 近接マッチ (±N): N ∈ {5, 10, 25}。`match_rate_A_by_B_N` = "
        "A のうち ±N step 以内に B event が存在する割合。B 基準は対称定義。"
    )
    buf.append(
        "- 独立性 (±25): `only_A` = A で捕捉・B で ±25 未捕捉、`only_B` 同様、"
        "`both` = ±25 で相手あり (A 基準 count)。"
    )
    buf.append(
        "- ベースライン期待値: Layer B event が cid の観測期間で一様分布すると仮定した場合の "
        "`match_rate_A_by_B_N` の理論値。cid ごとに "
        "p = 1 − (1 − (2N+1)/span)^{n_B} を計算し、n_A weighted 平均。"
    )
    buf.append(
        "- 内容比較: exact-match の行について v11_delta と v14_delta_norm の Pearson 相関、"
        "`v11_captured` と `v14_spend_flag` の一致率。同 step 内で複数 event が発火した場合、"
        "Layer B 側は max(delta) + any(spend_flag) に集約。event_type 層別 (E3 を含むかどうか) も算出。"
    )
    buf.append(
        "- n_core バケット (2/3/4/5+) 別の計算は per_subject_audit の `n_core_member` を使用。"
    )
    buf.append("")

    buf.append("## 2. Short run: overlap 集計\n")
    buf.append(
        md_table(
            short_all,
            int_cols=[
                "n_cids",
                "n_A_total",
                "n_B_total",
                "exact_intersection",
                "exact_union",
                "only_A_25_count",
                "only_B_25_count",
                "both_25_count_A",
                "both_25_count_B",
            ],
        )
    )
    buf.append("")
    buf.append(
        f"ベースライン期待 match_rate_A_by_B: "
        f"±5={_fmt(short_base['baseline_match_rate_A_by_B_5'],4)}, "
        f"±10={_fmt(short_base['baseline_match_rate_A_by_B_10'],4)}, "
        f"±25={_fmt(short_base['baseline_match_rate_A_by_B_25'],4)}"
    )
    buf.append("")

    buf.append("## 3. Long run: overlap 集計\n")
    buf.append(
        md_table(
            long_all,
            int_cols=[
                "n_cids",
                "n_A_total",
                "n_B_total",
                "exact_intersection",
                "exact_union",
                "only_A_25_count",
                "only_B_25_count",
                "both_25_count_A",
                "both_25_count_B",
            ],
        )
    )
    buf.append("")
    buf.append(
        f"ベースライン期待 match_rate_A_by_B: "
        f"±5={_fmt(long_base['baseline_match_rate_A_by_B_5'],4)}, "
        f"±10={_fmt(long_base['baseline_match_rate_A_by_B_10'],4)}, "
        f"±25={_fmt(long_base['baseline_match_rate_A_by_B_25'],4)}"
    )
    buf.append("")

    buf.append("## 4. 内容的比較 (exact-match)\n")
    buf.append("### 4.1 Short run\n")
    sc = short_content
    buf.append(
        f"- 全マッチ: n={sc['n_matches_all']}, "
        f"Pearson(v11_delta, v14_delta_norm) = {_fmt(sc['pearson_all'],4)}, "
        f"agreement(captured, spend_flag) = {_fmt(sc['agreement_captured_vs_spend'],4)}"
    )
    buf.append(
        f"- E3 非含 (E1/E2 のみ): n={sc['n_matches_e1e2_only']}, "
        f"Pearson = {_fmt(sc['pearson_e1e2_only'],4)}, "
        f"agreement = {_fmt(sc['agreement_e1e2_only'],4)}"
    )
    buf.append(
        f"- E3 含む: n={sc['n_matches_e3_any']}, "
        f"Pearson = {_fmt(sc['pearson_e3_any'],4)}, "
        f"agreement = {_fmt(sc['agreement_e3_any'],4)}"
    )
    buf.append("")
    buf.append("### 4.2 Long run\n")
    lc = long_content
    buf.append(
        f"- 全マッチ: n={lc['n_matches_all']}, "
        f"Pearson(v11_delta, v14_delta_norm) = {_fmt(lc['pearson_all'],4)}, "
        f"agreement(captured, spend_flag) = {_fmt(lc['agreement_captured_vs_spend'],4)}"
    )
    buf.append(
        f"- E3 非含 (E1/E2 のみ): n={lc['n_matches_e1e2_only']}, "
        f"Pearson = {_fmt(lc['pearson_e1e2_only'],4)}, "
        f"agreement = {_fmt(lc['agreement_e1e2_only'],4)}"
    )
    buf.append(
        f"- E3 含む: n={lc['n_matches_e3_any']}, "
        f"Pearson = {_fmt(lc['pearson_e3_any'],4)}, "
        f"agreement = {_fmt(lc['agreement_e3_any'],4)}"
    )
    buf.append("")

    buf.append("## 5. n_core バケット別 overlap\n")
    buf.append("### 5.1 Short run\n")
    buf.append(
        md_table(
            short_bb,
            int_cols=[
                "n_cids",
                "n_A_total",
                "n_B_total",
                "exact_intersection",
                "exact_union",
                "only_A_25_count",
                "only_B_25_count",
                "both_25_count_A",
                "both_25_count_B",
            ],
        )
    )
    buf.append("")
    buf.append("### 5.2 Long run\n")
    buf.append(
        md_table(
            long_bb,
            int_cols=[
                "n_cids",
                "n_A_total",
                "n_B_total",
                "exact_intersection",
                "exact_union",
                "only_A_25_count",
                "only_B_25_count",
                "both_25_count_A",
                "both_25_count_B",
            ],
        )
    )
    buf.append("")

    buf.append("## 6. 観察事項 (Describe, do not decide)\n")
    for i, line in enumerate(
        compute_observations(
            short_all, long_all, short_bb, long_bb,
            short_content, long_content, short_base, long_base,
        ),
        start=1,
    ):
        buf.append(f"{i}. {line}")
    buf.append("")
    buf.append("---\n")
    buf.append("*End of §6.3 report.*")
    out_path.write_text("\n".join(buf))


def run_dir(diag_dir: Path):
    pulse = load_pulse(diag_dir / "pulse")
    events = load_events(diag_dir / "audit")
    subjects = load_subjects(diag_dir / "audit")
    bucket_map = subjects[["seed", "cid", "n_core_member"]].copy()
    bucket_map["bucket"] = bucket_map["n_core_member"].apply(bucket_of)
    per_cid = compute_per_cid_overlap(pulse, events, bucket_map)
    overall = aggregate_overlap(per_cid, by_bucket=False)
    by_bucket = aggregate_overlap(per_cid, by_bucket=True)
    content = content_comparison(pulse, events)
    baseline = compute_baseline_expectation(pulse, events)
    return overall, by_bucket, content, baseline


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_PATH))
    args = ap.parse_args()

    short_all, short_bb, short_content, short_base = run_dir(SHORT_DIR)
    long_all, long_bb, long_content, long_base = run_dir(LONG_DIR)

    write_report(
        short_all, long_all, short_bb, long_bb,
        short_content, long_content, short_base, long_base,
        Path(args.out),
    )
    print(f"wrote: {args.out}")
    print("\n--- Short overall ---")
    print(short_all.to_string(index=False))
    print("\n--- Long overall ---")
    print(long_all.to_string(index=False))
    print("\n--- Long by bucket ---")
    print(long_bb.to_string(index=False))
    print("\n--- Long content ---")
    print(long_content)
    print("\n--- Long baseline ---")
    print(long_base)


if __name__ == "__main__":
    main()
