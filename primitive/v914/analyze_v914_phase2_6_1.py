#!/usr/bin/env python3
"""
v9.14 Phase 2 §6.1 — Event-type Efficiency Analysis

Aggregates per_event_audit CSVs across all seeds to quantify
information efficiency per event type (E1_death / E1_birth / E2_rise /
E2_fall / E3_contact), overall and per n_core bucket (2, 3, 4, 5+).

Output: v914_event_type_efficiency.md

Describe only. No conclusions.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
SHORT_DIR = SCRIPT_DIR / "diag_v914_short"
LONG_DIR = SCRIPT_DIR / "diag_v914_long"
OUT_PATH = SCRIPT_DIR / "v914_event_type_efficiency.md"

EVENT_TYPES = ["E1_death", "E1_birth", "E2_rise", "E2_fall", "E3_contact"]
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
    frames = [pd.read_csv(f) for f in files]
    return pd.concat(frames, ignore_index=True)


def load_subjects(audit_dir: Path) -> pd.DataFrame:
    files = sorted(audit_dir.glob("per_subject_audit_seed*.csv"))
    frames = [pd.read_csv(f) for f in files]
    return pd.concat(frames, ignore_index=True)


def _fmt(x, digits: int = 4) -> str:
    if x is None or (isinstance(x, float) and (np.isnan(x) or not np.isfinite(x))):
        return "-"
    if isinstance(x, (int, np.integer)):
        return f"{int(x):d}"
    return f"{float(x):.{digits}g}"


def aggregate_event_type(events: pd.DataFrame, exhaustion_map: pd.DataFrame) -> pd.DataFrame:
    """Per event-type aggregate over all rows in `events`.

    exhaustion_map: DataFrame with columns (seed, cid, q_spent_total).
    Used to compute exhaustion_contribution = share of that cid's q_spent
    contributed by this event type, averaged across cids.
    """
    rows = []
    # Precompute per-(seed,cid,event_type) spend counts to compute exhaustion contribution
    spend_by_sci = (
        events[events["v14_spend_flag"]]
        .groupby(["seed", "cid", "v14_event_type"], observed=True)
        .size()
        .rename("spend_this_type")
        .reset_index()
    )
    merged_sci = spend_by_sci.merge(
        exhaustion_map, on=["seed", "cid"], how="left"
    )
    merged_sci["share"] = np.where(
        merged_sci["q_spent_total"] > 0,
        merged_sci["spend_this_type"] / merged_sci["q_spent_total"],
        np.nan,
    )

    for ev_type in EVENT_TYPES:
        sub = events[events["v14_event_type"] == ev_type]
        n_all = len(sub)
        spend = sub[sub["v14_spend_flag"]]
        n_spend = len(spend)
        spend_rate = n_spend / n_all if n_all > 0 else np.nan
        delta_mean = spend["v14_delta_norm"].mean() if n_spend else np.nan
        delta_p50 = spend["v14_delta_norm"].median() if n_spend else np.nan
        delta_p90 = spend["v14_delta_norm"].quantile(0.90) if n_spend else np.nan
        att_mean = spend["v14_attention_delta"].mean() if n_spend else np.nan
        att_p50 = spend["v14_attention_delta"].median() if n_spend else np.nan
        fam_mean = spend["v14_familiarity_delta"].mean() if n_spend else np.nan
        fam_p50 = spend["v14_familiarity_delta"].median() if n_spend else np.nan

        type_shares = merged_sci[merged_sci["v14_event_type"] == ev_type]["share"]
        ex_contrib = type_shares.mean() if len(type_shares) else np.nan

        rows.append(
            dict(
                event_type=ev_type,
                event_count=n_all,
                spend_count=n_spend,
                spend_rate=spend_rate,
                delta_mean=delta_mean,
                delta_p50=delta_p50,
                delta_p90=delta_p90,
                attention_delta_mean=att_mean,
                attention_delta_p50=att_p50,
                familiarity_delta_mean=fam_mean,
                familiarity_delta_p50=fam_p50,
                exhaustion_contribution=ex_contrib,
            )
        )
    return pd.DataFrame(rows)


def aggregate_event_x_ncore(
    events: pd.DataFrame, subjects: pd.DataFrame, exhaustion_map: pd.DataFrame
) -> pd.DataFrame:
    """Per (event_type, n_core bucket) aggregate."""
    nmap = subjects[["seed", "cid", "n_core_member"]].copy()
    nmap["bucket"] = nmap["n_core_member"].apply(bucket_of)
    ev = events.merge(nmap[["seed", "cid", "bucket"]], on=["seed", "cid"], how="left")

    # Exhaustion contribution per (seed, cid, event_type)
    spend_by_sci = (
        ev[ev["v14_spend_flag"]]
        .groupby(["seed", "cid", "bucket", "v14_event_type"], observed=True)
        .size()
        .rename("spend_this_type")
        .reset_index()
    )
    merged_sci = spend_by_sci.merge(exhaustion_map, on=["seed", "cid"], how="left")
    merged_sci["share"] = np.where(
        merged_sci["q_spent_total"] > 0,
        merged_sci["spend_this_type"] / merged_sci["q_spent_total"],
        np.nan,
    )

    rows = []
    for b in BUCKETS:
        for ev_type in EVENT_TYPES:
            sub = ev[(ev["bucket"] == b) & (ev["v14_event_type"] == ev_type)]
            n_all = len(sub)
            spend = sub[sub["v14_spend_flag"]]
            n_spend = len(spend)
            spend_rate = n_spend / n_all if n_all > 0 else np.nan
            delta_mean = spend["v14_delta_norm"].mean() if n_spend else np.nan
            delta_p50 = spend["v14_delta_norm"].median() if n_spend else np.nan
            delta_p90 = (
                spend["v14_delta_norm"].quantile(0.90) if n_spend else np.nan
            )
            att_mean = spend["v14_attention_delta"].mean() if n_spend else np.nan
            att_p50 = spend["v14_attention_delta"].median() if n_spend else np.nan
            fam_mean = spend["v14_familiarity_delta"].mean() if n_spend else np.nan
            fam_p50 = spend["v14_familiarity_delta"].median() if n_spend else np.nan
            type_shares = merged_sci[
                (merged_sci["bucket"] == b)
                & (merged_sci["v14_event_type"] == ev_type)
            ]["share"]
            ex_contrib = type_shares.mean() if len(type_shares) else np.nan
            rows.append(
                dict(
                    bucket=b,
                    event_type=ev_type,
                    event_count=n_all,
                    spend_count=n_spend,
                    spend_rate=spend_rate,
                    delta_mean=delta_mean,
                    delta_p50=delta_p50,
                    delta_p90=delta_p90,
                    attention_delta_mean=att_mean,
                    attention_delta_p50=att_p50,
                    familiarity_delta_mean=fam_mean,
                    familiarity_delta_p50=fam_p50,
                    exhaustion_contribution=ex_contrib,
                )
            )
    return pd.DataFrame(rows)


def exhaustion_map_from_subjects(subjects: pd.DataFrame) -> pd.DataFrame:
    return subjects[["seed", "cid", "v14_q_spent"]].rename(
        columns={"v14_q_spent": "q_spent_total"}
    )


def md_table_event_type(df: pd.DataFrame) -> str:
    cols = [
        "event_type",
        "event_count",
        "spend_count",
        "spend_rate",
        "delta_mean",
        "delta_p50",
        "delta_p90",
        "attention_delta_mean",
        "attention_delta_p50",
        "familiarity_delta_mean",
        "familiarity_delta_p50",
        "exhaustion_contribution",
    ]
    header = "| " + " | ".join(cols) + " |\n"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |\n"
    body = ""
    for _, r in df.iterrows():
        vals = []
        for c in cols:
            v = r[c]
            if c in ("event_type",):
                vals.append(str(v))
            elif c in ("event_count", "spend_count"):
                vals.append(_fmt(v, 0))
            else:
                vals.append(_fmt(v, 4))
        body += "| " + " | ".join(vals) + " |\n"
    return header + sep + body


def md_table_event_x_ncore(df: pd.DataFrame) -> str:
    cols = [
        "bucket",
        "event_type",
        "event_count",
        "spend_count",
        "spend_rate",
        "delta_mean",
        "delta_p50",
        "delta_p90",
        "attention_delta_mean",
        "attention_delta_p50",
        "familiarity_delta_mean",
        "familiarity_delta_p50",
        "exhaustion_contribution",
    ]
    header = "| " + " | ".join(cols) + " |\n"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |\n"
    body = ""
    for _, r in df.iterrows():
        vals = []
        for c in cols:
            v = r[c]
            if c in ("bucket", "event_type"):
                vals.append(str(v))
            elif c in ("event_count", "spend_count"):
                vals.append(_fmt(v, 0))
            else:
                vals.append(_fmt(v, 4))
        body += "| " + " | ".join(vals) + " |\n"
    return header + sep + body


def compute_observations(
    short_by_type: pd.DataFrame,
    long_by_type: pd.DataFrame,
    short_xn: pd.DataFrame,
    long_xn: pd.DataFrame,
) -> list[str]:
    """Describe-only observations: numeric facts, no conclusions."""
    obs: list[str] = []

    def pick(df, col, ev):
        row = df[df["event_type"] == ev]
        if row.empty:
            return None
        val = row.iloc[0][col]
        return None if (isinstance(val, float) and np.isnan(val)) else val

    obs.append(
        "Short run の event_count は "
        f"E3_contact={_fmt(pick(short_by_type, 'event_count', 'E3_contact'), 0)}, "
        f"E1_death={_fmt(pick(short_by_type, 'event_count', 'E1_death'), 0)}, "
        f"E2_rise={_fmt(pick(short_by_type, 'event_count', 'E2_rise'), 0)}, "
        f"E2_fall={_fmt(pick(short_by_type, 'event_count', 'E2_fall'), 0)}, "
        f"E1_birth={_fmt(pick(short_by_type, 'event_count', 'E1_birth'), 0)}。"
    )
    obs.append(
        "Long run の event_count は "
        f"E3_contact={_fmt(pick(long_by_type, 'event_count', 'E3_contact'), 0)}, "
        f"E1_death={_fmt(pick(long_by_type, 'event_count', 'E1_death'), 0)}, "
        f"E2_rise={_fmt(pick(long_by_type, 'event_count', 'E2_rise'), 0)}, "
        f"E2_fall={_fmt(pick(long_by_type, 'event_count', 'E2_fall'), 0)}, "
        f"E1_birth={_fmt(pick(long_by_type, 'event_count', 'E1_birth'), 0)}。"
    )
    obs.append(
        "Short run の spend_rate は全 event type で "
        f"E1_death={_fmt(pick(short_by_type, 'spend_rate', 'E1_death'), 4)}, "
        f"E1_birth={_fmt(pick(short_by_type, 'spend_rate', 'E1_birth'), 4)}, "
        f"E2_rise={_fmt(pick(short_by_type, 'spend_rate', 'E2_rise'), 4)}, "
        f"E2_fall={_fmt(pick(short_by_type, 'spend_rate', 'E2_fall'), 4)}, "
        f"E3_contact={_fmt(pick(short_by_type, 'spend_rate', 'E3_contact'), 4)}。"
    )
    obs.append(
        "Long run の spend_rate は "
        f"E1_death={_fmt(pick(long_by_type, 'spend_rate', 'E1_death'), 4)}, "
        f"E1_birth={_fmt(pick(long_by_type, 'spend_rate', 'E1_birth'), 4)}, "
        f"E2_rise={_fmt(pick(long_by_type, 'spend_rate', 'E2_rise'), 4)}, "
        f"E2_fall={_fmt(pick(long_by_type, 'spend_rate', 'E2_fall'), 4)}, "
        f"E3_contact={_fmt(pick(long_by_type, 'spend_rate', 'E3_contact'), 4)}。"
    )
    obs.append(
        "Long run の delta_mean (spend のみ) は "
        f"E1_death={_fmt(pick(long_by_type, 'delta_mean', 'E1_death'), 4)}, "
        f"E1_birth={_fmt(pick(long_by_type, 'delta_mean', 'E1_birth'), 4)}, "
        f"E2_rise={_fmt(pick(long_by_type, 'delta_mean', 'E2_rise'), 4)}, "
        f"E2_fall={_fmt(pick(long_by_type, 'delta_mean', 'E2_fall'), 4)}, "
        f"E3_contact={_fmt(pick(long_by_type, 'delta_mean', 'E3_contact'), 4)}。"
    )
    obs.append(
        "Long run の attention_delta_mean は "
        f"E1_death={_fmt(pick(long_by_type, 'attention_delta_mean', 'E1_death'), 4)}, "
        f"E2_rise={_fmt(pick(long_by_type, 'attention_delta_mean', 'E2_rise'), 4)}, "
        f"E3_contact={_fmt(pick(long_by_type, 'attention_delta_mean', 'E3_contact'), 4)}。"
    )
    obs.append(
        "Long run の familiarity_delta_mean は "
        f"E1_death={_fmt(pick(long_by_type, 'familiarity_delta_mean', 'E1_death'), 4)}, "
        f"E2_rise={_fmt(pick(long_by_type, 'familiarity_delta_mean', 'E2_rise'), 4)}, "
        f"E3_contact={_fmt(pick(long_by_type, 'familiarity_delta_mean', 'E3_contact'), 4)}。"
    )
    obs.append(
        "Long run の exhaustion_contribution (各 event 種が cid の q_spent に "
        "占める平均割合) は "
        f"E1_death={_fmt(pick(long_by_type, 'exhaustion_contribution', 'E1_death'), 4)}, "
        f"E2_rise={_fmt(pick(long_by_type, 'exhaustion_contribution', 'E2_rise'), 4)}, "
        f"E3_contact={_fmt(pick(long_by_type, 'exhaustion_contribution', 'E3_contact'), 4)}。"
    )

    # n_core bucket observation for long run E3
    e3_long = long_xn[long_xn["event_type"] == "E3_contact"]
    parts = []
    for _, r in e3_long.iterrows():
        parts.append(f"bucket={r['bucket']}: {_fmt(r['event_count'],0)}")
    obs.append("Long run E3_contact の event_count (n_core バケット別): " + ", ".join(parts) + "。")

    e3_long_spend = e3_long[["bucket", "spend_rate"]]
    parts = []
    for _, r in e3_long_spend.iterrows():
        parts.append(f"bucket={r['bucket']}: {_fmt(r['spend_rate'],4)}")
    obs.append("Long run E3_contact の spend_rate (n_core バケット別): " + ", ".join(parts) + "。")

    return obs


def write_report(
    short_by_type: pd.DataFrame,
    long_by_type: pd.DataFrame,
    short_xn: pd.DataFrame,
    long_xn: pd.DataFrame,
    out_path: Path,
) -> None:
    buf = []
    buf.append("# v9.14 §6.1 — Event-type Efficiency\n")
    buf.append("*Phase 2 §6.1 output — Describe only.*\n")
    buf.append("")
    buf.append("## 1. 計算方法\n")
    buf.append(
        "- 入力: `diag_v914_{short,long}/audit/per_event_audit_seed*.csv` "
        "(短 48 seeds / 長 5 seeds)、`per_subject_audit_seed*.csv` (n_core マップ用)。"
    )
    buf.append(
        "- 集計単位: event 種別 (E1_death / E1_birth / E2_rise / E2_fall / E3_contact)、"
        "および event 種 × n_core バケット (2 / 3 / 4 / 5+)。"
    )
    buf.append(
        "- `event_count` は全 event、`spend_count`/`delta_*`/`attention_delta_*`/"
        "`familiarity_delta_*` は `v14_spend_flag=True` の event のみを対象。"
    )
    buf.append(
        "- `exhaustion_contribution` は各 (seed, cid) 内でその event 種が占める "
        "`spend 回数 / q_spent_total` 比を cid 平均したもの (q_spent_total=0 の cid は除外)。"
    )
    buf.append(
        "- n_core バケット = `per_subject_audit.n_core_member` を 2/3/4/5+ に集約 (v9.14 慣習)。"
    )
    buf.append("")
    buf.append("## 2. Short run: event 種別集計\n")
    buf.append(md_table_event_type(short_by_type))
    buf.append("")
    buf.append("## 3. Long run: event 種別集計\n")
    buf.append(md_table_event_type(long_by_type))
    buf.append("")
    buf.append("## 4. Short run: event 種 × n_core バケット\n")
    buf.append(md_table_event_x_ncore(short_xn))
    buf.append("")
    buf.append("## 5. Long run: event 種 × n_core バケット\n")
    buf.append(md_table_event_x_ncore(long_xn))
    buf.append("")
    buf.append("## 6. 観察事項 (Describe, do not decide)\n")
    for i, line in enumerate(
        compute_observations(short_by_type, long_by_type, short_xn, long_xn), start=1
    ):
        buf.append(f"{i}. {line}")
    buf.append("")
    buf.append("---\n")
    buf.append("*End of §6.1 report.*")
    out_path.write_text("\n".join(buf))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_PATH))
    args = ap.parse_args()

    short_events = load_events(SHORT_DIR / "audit")
    short_subjects = load_subjects(SHORT_DIR / "audit")
    long_events = load_events(LONG_DIR / "audit")
    long_subjects = load_subjects(LONG_DIR / "audit")

    short_exh = exhaustion_map_from_subjects(short_subjects)
    long_exh = exhaustion_map_from_subjects(long_subjects)

    short_by_type = aggregate_event_type(short_events, short_exh)
    long_by_type = aggregate_event_type(long_events, long_exh)
    short_xn = aggregate_event_x_ncore(short_events, short_subjects, short_exh)
    long_xn = aggregate_event_x_ncore(long_events, long_subjects, long_exh)

    write_report(short_by_type, long_by_type, short_xn, long_xn, Path(args.out))
    print(f"wrote: {args.out}")

    print("\n--- Short by event type ---")
    print(short_by_type.to_string(index=False))
    print("\n--- Long by event type ---")
    print(long_by_type.to_string(index=False))


if __name__ == "__main__":
    main()
