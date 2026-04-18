#!/usr/bin/env python3
"""
v9.14 Phase 2 §6.2 — n_core Efficiency Analysis

Quantifies spend efficiency and exhaustion profile per n_core bucket
(2, 3, 4, 5+), for both short (48 seeds) and long (5 seeds) runs.

Output: v914_ncore_efficiency.md

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
OUT_PATH = SCRIPT_DIR / "v914_ncore_efficiency.md"

BUCKETS = ["2", "3", "4", "5+"]


def bucket_of(n: int) -> str:
    if n <= 2:
        return "2"
    if n == 3:
        return "3"
    if n == 4:
        return "4"
    return "5+"


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


def basic_per_bucket(
    subjects: pd.DataFrame, events: pd.DataFrame
) -> pd.DataFrame:
    """Basic per-bucket metrics.

    - n_cids, q0_mean/std, q_spent_mean/std
    - exhaustion_ratio, non_exhaustion_ratio
    - event_count_mean per cid, event_per_q0 = event_count_mean / q0_mean
    """
    sub = subjects.copy()
    sub["bucket"] = sub["n_core_member"].apply(bucket_of)
    ev_count_per_cid = (
        events.groupby(["seed", "cid"], observed=True).size().rename("event_count")
    )
    sub = sub.merge(
        ev_count_per_cid.reset_index(), on=["seed", "cid"], how="left"
    )
    sub["event_count"] = sub["event_count"].fillna(0).astype(int)

    rows = []
    for b in BUCKETS:
        s = sub[sub["bucket"] == b]
        n = len(s)
        if n == 0:
            rows.append(
                dict(
                    bucket=b,
                    n_cids=0,
                    q0_mean=np.nan,
                    q0_std=np.nan,
                    q_spent_mean=np.nan,
                    q_spent_std=np.nan,
                    exhaustion_ratio=np.nan,
                    non_exhaustion_ratio=np.nan,
                    event_count_mean=np.nan,
                    event_per_q0=np.nan,
                )
            )
            continue
        exh = (s["v14_q_remaining"] == 0).mean()
        rows.append(
            dict(
                bucket=b,
                n_cids=n,
                q0_mean=s["v14_q0"].mean(),
                q0_std=s["v14_q0"].std(ddof=0),
                q_spent_mean=s["v14_q_spent"].mean(),
                q_spent_std=s["v14_q_spent"].std(ddof=0),
                exhaustion_ratio=exh,
                non_exhaustion_ratio=1.0 - exh,
                event_count_mean=s["event_count"].mean(),
                event_per_q0=(
                    s["event_count"].mean() / s["v14_q0"].mean()
                    if s["v14_q0"].mean() > 0
                    else np.nan
                ),
            )
        )
    return pd.DataFrame(rows)


def efficiency_per_bucket(
    subjects: pd.DataFrame, events: pd.DataFrame
) -> pd.DataFrame:
    """Per-bucket spend efficiency metrics.

    - attention_gain / spend_count
    - familiarity_gain / spend_count
    - delta_total / spend_count
    """
    sub = subjects.copy()
    sub["bucket"] = sub["n_core_member"].apply(bucket_of)

    spend = events[events["v14_spend_flag"]].copy()
    spend_per_cid = (
        spend.groupby(["seed", "cid"], observed=True)
        .agg(
            spend_count=("v14_spend_flag", "size"),
            attn_sum=("v14_attention_delta", "sum"),
            fam_sum=("v14_familiarity_delta", "sum"),
            delta_sum=("v14_delta_norm", "sum"),
        )
        .reset_index()
    )

    m = sub.merge(spend_per_cid, on=["seed", "cid"], how="left")
    for c in ["spend_count", "attn_sum", "fam_sum", "delta_sum"]:
        m[c] = m[c].fillna(0)

    rows = []
    for b in BUCKETS:
        s = m[m["bucket"] == b]
        tot_spend = s["spend_count"].sum()
        rows.append(
            dict(
                bucket=b,
                n_cids=len(s),
                spend_count_total=int(tot_spend),
                attention_gain_total=s["attn_sum"].sum(),
                familiarity_gain_total=s["fam_sum"].sum(),
                delta_gain_total=s["delta_sum"].sum(),
                attn_per_spend=(
                    s["attn_sum"].sum() / tot_spend if tot_spend > 0 else np.nan
                ),
                fam_per_spend=(
                    s["fam_sum"].sum() / tot_spend if tot_spend > 0 else np.nan
                ),
                delta_per_spend=(
                    s["delta_sum"].sum() / tot_spend if tot_spend > 0 else np.nan
                ),
            )
        )
    return pd.DataFrame(rows)


def exhaustion_step_profile(
    subjects: pd.DataFrame, events: pd.DataFrame
) -> pd.DataFrame:
    """Step/window at which Q first reaches 0, per bucket.

    Defined as the step of the *event* where q_remaining transitioned
    to 0 (first occurrence of v14_q_remaining==0 per (seed, cid)).
    """
    exh_cids = subjects[subjects["v14_q_remaining"] == 0][
        ["seed", "cid", "n_core_member"]
    ].copy()
    exh_cids["bucket"] = exh_cids["n_core_member"].apply(bucket_of)

    ev = events[events["v14_q_remaining"] == 0].copy()
    first_zero = (
        ev.sort_values(["seed", "cid", "global_step"])
        .groupby(["seed", "cid"], observed=True)
        .first()
        .reset_index()[["seed", "cid", "global_step", "window", "step"]]
        .rename(columns={"global_step": "exhaust_global_step",
                         "window": "exhaust_window",
                         "step": "exhaust_step"})
    )
    merged = exh_cids.merge(first_zero, on=["seed", "cid"], how="left")

    rows = []
    for b in BUCKETS:
        s = merged[merged["bucket"] == b]
        if len(s) == 0:
            rows.append(
                dict(
                    bucket=b,
                    n_exhausted=0,
                    exhaust_step_mean=np.nan,
                    exhaust_step_median=np.nan,
                    exhaust_step_min=np.nan,
                    exhaust_step_max=np.nan,
                    exhaust_window_mean=np.nan,
                    exhaust_window_median=np.nan,
                    exhaust_window_min=np.nan,
                    exhaust_window_max=np.nan,
                )
            )
            continue
        gs = s["exhaust_global_step"]
        wd = s["exhaust_window"]
        rows.append(
            dict(
                bucket=b,
                n_exhausted=len(s),
                exhaust_step_mean=gs.mean(),
                exhaust_step_median=gs.median(),
                exhaust_step_min=gs.min(),
                exhaust_step_max=gs.max(),
                exhaust_window_mean=wd.mean(),
                exhaust_window_median=wd.median(),
                exhaust_window_min=wd.min(),
                exhaust_window_max=wd.max(),
            )
        )
    return pd.DataFrame(rows)


def non_exhaustion_profile(
    subjects: pd.DataFrame, events: pd.DataFrame
) -> pd.DataFrame:
    """Characterize cids that did NOT exhaust Q (q_remaining > 0)."""
    sub = subjects.copy()
    sub["bucket"] = sub["n_core_member"].apply(bucket_of)
    ev_count_per_cid = (
        events.groupby(["seed", "cid"], observed=True).size().rename("event_count")
    )
    sub = sub.merge(ev_count_per_cid.reset_index(), on=["seed", "cid"], how="left")
    sub["event_count"] = sub["event_count"].fillna(0).astype(int)

    non_exh = sub[sub["v14_q_remaining"] > 0]
    exh = sub[sub["v14_q_remaining"] == 0]

    rows = []
    for b in BUCKETS:
        n_total = (sub["bucket"] == b).sum()
        n_sub = non_exh[non_exh["bucket"] == b]
        n_exh_sub = exh[exh["bucket"] == b]
        n_non_exh = len(n_sub)
        rows.append(
            dict(
                bucket=b,
                n_total=int(n_total),
                n_non_exhausted=int(n_non_exh),
                non_exhausted_share=(
                    n_non_exh / n_total if n_total > 0 else np.nan
                ),
                non_exh_q0_mean=n_sub["v14_q0"].mean() if n_non_exh else np.nan,
                non_exh_q0_std=n_sub["v14_q0"].std(ddof=0) if n_non_exh else np.nan,
                non_exh_q_remaining_mean=(
                    n_sub["v14_q_remaining"].mean() if n_non_exh else np.nan
                ),
                non_exh_event_count_mean=(
                    n_sub["event_count"].mean() if n_non_exh else np.nan
                ),
                exh_q0_mean=n_exh_sub["v14_q0"].mean() if len(n_exh_sub) else np.nan,
                exh_event_count_mean=(
                    n_exh_sub["event_count"].mean() if len(n_exh_sub) else np.nan
                ),
            )
        )
    return pd.DataFrame(rows)


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
    short_basic, long_basic, short_eff, long_eff, long_exh, long_ne
) -> list[str]:
    obs: list[str] = []

    def pick(df, col, b):
        r = df[df["bucket"] == b]
        if r.empty:
            return None
        v = r.iloc[0][col]
        return None if (isinstance(v, float) and np.isnan(v)) else v

    obs.append(
        "Q0_mean は n_core に単調増加: short で "
        f"2={_fmt(pick(short_basic,'q0_mean','2'),4)}, "
        f"3={_fmt(pick(short_basic,'q0_mean','3'),4)}, "
        f"4={_fmt(pick(short_basic,'q0_mean','4'),4)}, "
        f"5+={_fmt(pick(short_basic,'q0_mean','5+'),4)}。"
    )
    obs.append(
        "exhaustion_ratio (Q_remaining=0 の cid 割合) は short で "
        f"2={_fmt(pick(short_basic,'exhaustion_ratio','2'),4)}, "
        f"3={_fmt(pick(short_basic,'exhaustion_ratio','3'),4)}, "
        f"4={_fmt(pick(short_basic,'exhaustion_ratio','4'),4)}, "
        f"5+={_fmt(pick(short_basic,'exhaustion_ratio','5+'),4)}、"
        "long で "
        f"2={_fmt(pick(long_basic,'exhaustion_ratio','2'),4)}, "
        f"3={_fmt(pick(long_basic,'exhaustion_ratio','3'),4)}, "
        f"4={_fmt(pick(long_basic,'exhaustion_ratio','4'),4)}, "
        f"5+={_fmt(pick(long_basic,'exhaustion_ratio','5+'),4)}。"
    )
    obs.append(
        "event_count_mean は short で "
        f"2={_fmt(pick(short_basic,'event_count_mean','2'),4)}, "
        f"3={_fmt(pick(short_basic,'event_count_mean','3'),4)}, "
        f"4={_fmt(pick(short_basic,'event_count_mean','4'),4)}, "
        f"5+={_fmt(pick(short_basic,'event_count_mean','5+'),4)}、"
        "long で "
        f"2={_fmt(pick(long_basic,'event_count_mean','2'),4)}, "
        f"3={_fmt(pick(long_basic,'event_count_mean','3'),4)}, "
        f"4={_fmt(pick(long_basic,'event_count_mean','4'),4)}, "
        f"5+={_fmt(pick(long_basic,'event_count_mean','5+'),4)}。"
    )
    obs.append(
        "event_per_q0 (平均 event 数 ÷ 平均 Q0) は long で "
        f"2={_fmt(pick(long_basic,'event_per_q0','2'),4)}, "
        f"3={_fmt(pick(long_basic,'event_per_q0','3'),4)}, "
        f"4={_fmt(pick(long_basic,'event_per_q0','4'),4)}, "
        f"5+={_fmt(pick(long_basic,'event_per_q0','5+'),4)}。"
    )
    obs.append(
        "attention_per_spend (総 attention_delta / 総 spend 回数) は long で "
        f"2={_fmt(pick(long_eff,'attn_per_spend','2'),4)}, "
        f"3={_fmt(pick(long_eff,'attn_per_spend','3'),4)}, "
        f"4={_fmt(pick(long_eff,'attn_per_spend','4'),4)}, "
        f"5+={_fmt(pick(long_eff,'attn_per_spend','5+'),4)}。"
    )
    obs.append(
        "familiarity_per_spend は long で "
        f"2={_fmt(pick(long_eff,'fam_per_spend','2'),4)}, "
        f"3={_fmt(pick(long_eff,'fam_per_spend','3'),4)}, "
        f"4={_fmt(pick(long_eff,'fam_per_spend','4'),4)}, "
        f"5+={_fmt(pick(long_eff,'fam_per_spend','5+'),4)}。"
    )
    obs.append(
        "delta_per_spend は long で "
        f"2={_fmt(pick(long_eff,'delta_per_spend','2'),4)}, "
        f"3={_fmt(pick(long_eff,'delta_per_spend','3'),4)}, "
        f"4={_fmt(pick(long_eff,'delta_per_spend','4'),4)}, "
        f"5+={_fmt(pick(long_eff,'delta_per_spend','5+'),4)}。"
    )
    obs.append(
        "Exhaustion の到達タイミング (long run, global_step 中央値) は "
        f"2={_fmt(pick(long_exh,'exhaust_step_median','2'),0)}, "
        f"3={_fmt(pick(long_exh,'exhaust_step_median','3'),0)}, "
        f"4={_fmt(pick(long_exh,'exhaust_step_median','4'),0)}, "
        f"5+={_fmt(pick(long_exh,'exhaust_step_median','5+'),0)}。"
    )
    obs.append(
        "Non-exhaustion cid の割合 (long run) は "
        f"2={_fmt(pick(long_ne,'non_exhausted_share','2'),4)}, "
        f"3={_fmt(pick(long_ne,'non_exhausted_share','3'),4)}, "
        f"4={_fmt(pick(long_ne,'non_exhausted_share','4'),4)}, "
        f"5+={_fmt(pick(long_ne,'non_exhausted_share','5+'),4)}。"
    )
    obs.append(
        "Non-exhaustion と exhaustion の event_count_mean 差 (long, 5+ バケット): "
        f"non_exhausted={_fmt(pick(long_ne,'non_exh_event_count_mean','5+'),4)}、"
        f"exhausted={_fmt(pick(long_ne,'exh_event_count_mean','5+'),4)}。"
    )

    return obs


def write_report(
    short_basic,
    long_basic,
    short_eff,
    long_eff,
    long_exh,
    long_ne,
    out_path: Path,
) -> None:
    buf: list[str] = []
    buf.append("# v9.14 §6.2 — n_core Efficiency\n")
    buf.append("*Phase 2 §6.2 output — Describe only.*\n")
    buf.append("")
    buf.append("## 1. 計算方法\n")
    buf.append(
        "- 入力: `diag_v914_{short,long}/audit/per_subject_audit_seed*.csv` "
        "(cid 単位) と `per_event_audit_seed*.csv` (event 単位)。"
    )
    buf.append(
        "- n_core バケット = `n_core_member` を 2 / 3 / 4 / 5+ に集約。"
        "n_core=6 以上は「5+」に含める。"
    )
    buf.append(
        "- 基礎指標: n_cids, q0_mean/std, q_spent_mean/std, exhaustion_ratio "
        "(= Q_remaining==0 の cid 割合), event_count_mean (= 1 cid あたり event 数平均), "
        "event_per_q0 (= event_count_mean / q0_mean)。"
    )
    buf.append(
        "- Efficiency 指標: 各バケットの全 cid を合算した "
        "(attention_delta 総和) / (spend 回数合計)、"
        "(familiarity_delta 総和) / (spend 回数合計)、"
        "(delta_norm 総和) / (spend 回数合計)。spend_flag=True のみ。"
    )
    buf.append(
        "- Exhaustion プロファイル (long 専用): 各 cid で Q_remaining が初めて 0 に "
        "到達した event の global_step (= engine の通し step) と window を分布集計。"
    )
    buf.append(
        "- Non-exhaustion cid: per_subject の `v14_q_remaining > 0` で抽出、"
        "同バケットの exhausted cid と q0/event_count を対照。"
    )
    buf.append("")

    buf.append("## 2. Short run: 基礎指標\n")
    buf.append(
        md_table(
            short_basic,
            int_cols=["n_cids"],
        )
    )
    buf.append("")
    buf.append("## 3. Long run: 基礎指標\n")
    buf.append(md_table(long_basic, int_cols=["n_cids"]))
    buf.append("")

    buf.append("## 4. Efficiency 指標 (spend あたり)\n")
    buf.append("### 4.1 Short run\n")
    buf.append(md_table(short_eff, int_cols=["n_cids", "spend_count_total"]))
    buf.append("")
    buf.append("### 4.2 Long run\n")
    buf.append(md_table(long_eff, int_cols=["n_cids", "spend_count_total"]))
    buf.append("")

    buf.append("## 5. Long run: Exhaustion プロファイル\n")
    buf.append(md_table(long_exh, int_cols=["n_exhausted"]))
    buf.append("")

    buf.append("## 6. Long run: Non-exhaustion cid の特性\n")
    buf.append(md_table(long_ne, int_cols=["n_total", "n_non_exhausted"]))
    buf.append("")

    buf.append("## 7. 観察事項 (Describe, do not decide)\n")
    for i, line in enumerate(
        compute_observations(short_basic, long_basic, short_eff, long_eff, long_exh, long_ne),
        start=1,
    ):
        buf.append(f"{i}. {line}")
    buf.append("")
    buf.append("---\n")
    buf.append("*End of §6.2 report.*")
    out_path.write_text("\n".join(buf))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_PATH))
    args = ap.parse_args()

    short_events = load_events(SHORT_DIR / "audit")
    short_subjects = load_subjects(SHORT_DIR / "audit")
    long_events = load_events(LONG_DIR / "audit")
    long_subjects = load_subjects(LONG_DIR / "audit")

    short_basic = basic_per_bucket(short_subjects, short_events)
    long_basic = basic_per_bucket(long_subjects, long_events)
    short_eff = efficiency_per_bucket(short_subjects, short_events)
    long_eff = efficiency_per_bucket(long_subjects, long_events)
    long_exh = exhaustion_step_profile(long_subjects, long_events)
    long_ne = non_exhaustion_profile(long_subjects, long_events)

    write_report(short_basic, long_basic, short_eff, long_eff, long_exh, long_ne, Path(args.out))
    print(f"wrote: {args.out}")
    print("\n--- Long basic ---")
    print(long_basic.to_string(index=False))
    print("\n--- Long efficiency ---")
    print(long_eff.to_string(index=False))
    print("\n--- Long exhaustion ---")
    print(long_exh.to_string(index=False))
    print("\n--- Long non-exh ---")
    print(long_ne.to_string(index=False))


if __name__ == "__main__":
    main()
