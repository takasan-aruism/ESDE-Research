#!/usr/bin/env python3
"""
v9.14 Phase 2 §6.4 — E3 Ablation Comparison

Compares the E3-enabled baseline (existing `diag_v914_{short,long}/`)
against the E3-disabled ablation (`diag_v914_{short,long}_noE3/`).

Metrics, all per n_core bucket (2/3/4/5+):
  - event_count: total + E1_death/E1_birth/E2_rise/E2_fall (E3 excluded)
  - spend_count
  - exhaustion_ratio
  - q_spent_mean
  - event_to_spend_ratio
  - attention_gain_total / spend
  - familiarity_gain_total / spend

Also:
  - Structural: Q0 ↔ spend correlation (per bucket and overall)
  - E1+E2 standalone profile in the ablation world
  - Exhaustion timing shift

Output: v914_e3_ablation_result.md

Describe only. No conclusions.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_PATH = SCRIPT_DIR / "v914_e3_ablation_result.md"

BUCKETS = ["2", "3", "4", "5+"]
E12_TYPES = ["E1_death", "E1_birth", "E2_rise", "E2_fall"]


def bucket_of(n: int) -> str:
    if n <= 2:
        return "2"
    if n == 3:
        return "3"
    if n == 4:
        return "4"
    return "5+"


def _fmt(x, digits: int = 4) -> str:
    if x is None or (isinstance(x, float) and (np.isnan(x) or not np.isfinite(x))):
        return "-"
    if isinstance(x, (int, np.integer)):
        return f"{int(x):d}"
    return f"{float(x):.{digits}g}"


def load_events(audit_dir: Path) -> pd.DataFrame:
    files = sorted(audit_dir.glob("per_event_audit_seed*.csv"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def load_subjects(audit_dir: Path) -> pd.DataFrame:
    files = sorted(audit_dir.glob("per_subject_audit_seed*.csv"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def basic_bucket_metrics(
    subjects: pd.DataFrame, events: pd.DataFrame, label: str
) -> pd.DataFrame:
    """Basic metrics per bucket; returns a DataFrame with `label` column."""
    if subjects.empty:
        return pd.DataFrame()
    sub = subjects.copy()
    sub["bucket"] = sub["n_core_member"].apply(bucket_of)

    ev = events.copy()
    ev = ev.merge(
        sub[["seed", "cid", "bucket"]], on=["seed", "cid"], how="left"
    )

    rows = []
    for b in BUCKETS:
        s = sub[sub["bucket"] == b]
        e = ev[ev["bucket"] == b]
        n_cids = len(s)

        ev_total = len(e)
        sp = e[e["v14_spend_flag"]]
        sp_count = len(sp)
        attn_tot = sp["v14_attention_delta"].sum() if sp_count else 0.0
        fam_tot = sp["v14_familiarity_delta"].sum() if sp_count else 0.0

        exh = (s["v14_q_remaining"] == 0).mean() if n_cids else np.nan

        per_type = {}
        for etype in E12_TYPES + ["E3_contact"]:
            per_type[f"count_{etype}"] = int(
                (e["v14_event_type"] == etype).sum()
            )

        row = dict(
            label=label,
            bucket=b,
            n_cids=n_cids,
            q0_mean=s["v14_q0"].mean() if n_cids else np.nan,
            q_spent_mean=s["v14_q_spent"].mean() if n_cids else np.nan,
            exhaustion_ratio=exh,
            event_count=ev_total,
            spend_count=sp_count,
            event_to_spend=ev_total / sp_count if sp_count else np.nan,
            attention_gain_total=attn_tot,
            familiarity_gain_total=fam_tot,
            attn_per_spend=attn_tot / sp_count if sp_count else np.nan,
            fam_per_spend=fam_tot / sp_count if sp_count else np.nan,
            **per_type,
        )
        rows.append(row)
    return pd.DataFrame(rows)


def make_comparison(base: pd.DataFrame, abl: pd.DataFrame) -> pd.DataFrame:
    """Join on bucket and compute absolute + relative diff for key columns."""
    if base.empty or abl.empty:
        return pd.DataFrame()
    b = base.set_index("bucket").drop(columns=["label"])
    a = abl.set_index("bucket").drop(columns=["label"])
    rows = []
    key_cols = [
        "n_cids",
        "q0_mean",
        "q_spent_mean",
        "exhaustion_ratio",
        "event_count",
        "spend_count",
        "event_to_spend",
        "attn_per_spend",
        "fam_per_spend",
        "count_E1_death",
        "count_E1_birth",
        "count_E2_rise",
        "count_E2_fall",
        "count_E3_contact",
    ]
    for bucket in BUCKETS:
        if bucket not in b.index or bucket not in a.index:
            continue
        base_row = b.loc[bucket]
        abl_row = a.loc[bucket]
        row = {"bucket": bucket}
        for c in key_cols:
            bv = base_row[c]
            av = abl_row[c]
            row[f"{c}_base"] = bv
            row[f"{c}_abl"] = av
            if isinstance(bv, (int, float)) and not pd.isna(bv) and bv != 0:
                row[f"{c}_rel"] = av / bv
            else:
                row[f"{c}_rel"] = np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def structural_q0_spend_corr(
    subjects: pd.DataFrame, label: str
) -> pd.DataFrame:
    """Q0 vs q_spent Pearson correlation, per bucket and overall."""
    if subjects.empty:
        return pd.DataFrame()
    sub = subjects.copy()
    sub["bucket"] = sub["n_core_member"].apply(bucket_of)
    rows = []
    for b in BUCKETS + ["all"]:
        s = sub if b == "all" else sub[sub["bucket"] == b]
        n = len(s)
        if n < 2 or s["v14_q0"].nunique() < 2:
            rows.append(dict(label=label, bucket=b, n=n, pearson_r=np.nan))
            continue
        r = np.corrcoef(s["v14_q0"], s["v14_q_spent"])[0, 1]
        rows.append(dict(label=label, bucket=b, n=n, pearson_r=float(r)))
    return pd.DataFrame(rows)


def e12_standalone_profile(
    subjects: pd.DataFrame, events: pd.DataFrame
) -> pd.DataFrame:
    """E1+E2-only efficiency per bucket in the ablation world.

    Shows: event counts, spend rate, delta/attention/familiarity per spend.
    """
    if events.empty:
        return pd.DataFrame()
    sub = subjects.copy()
    sub["bucket"] = sub["n_core_member"].apply(bucket_of)
    ev = events.merge(sub[["seed", "cid", "bucket"]], on=["seed", "cid"], how="left")
    # restrict to E1/E2
    ev = ev[ev["v14_event_type"].isin(E12_TYPES)]

    rows = []
    for b in BUCKETS:
        for etype in E12_TYPES:
            s = ev[(ev["bucket"] == b) & (ev["v14_event_type"] == etype)]
            n_events = len(s)
            sp = s[s["v14_spend_flag"]]
            n_spend = len(sp)
            rows.append(
                dict(
                    bucket=b,
                    event_type=etype,
                    event_count=n_events,
                    spend_count=n_spend,
                    spend_rate=(
                        n_spend / n_events if n_events > 0 else np.nan
                    ),
                    delta_mean=sp["v14_delta_norm"].mean() if n_spend else np.nan,
                    attn_mean=(
                        sp["v14_attention_delta"].mean() if n_spend else np.nan
                    ),
                    fam_mean=(
                        sp["v14_familiarity_delta"].mean() if n_spend else np.nan
                    ),
                )
            )
    return pd.DataFrame(rows)


def exhaustion_step_shift(
    base_sub: pd.DataFrame,
    base_ev: pd.DataFrame,
    abl_sub: pd.DataFrame,
    abl_ev: pd.DataFrame,
) -> pd.DataFrame:
    """Compare exhaustion timing (first v14_q_remaining==0 event)
    between baseline and ablation, per bucket."""
    rows = []

    def first_zero(sub, ev):
        if sub.empty or ev.empty:
            return pd.DataFrame()
        s = sub[sub["v14_q_remaining"] == 0][
            ["seed", "cid", "n_core_member"]
        ].copy()
        s["bucket"] = s["n_core_member"].apply(bucket_of)
        e = ev[ev["v14_q_remaining"] == 0]
        fz = (
            e.sort_values(["seed", "cid", "global_step"])
            .groupby(["seed", "cid"], observed=True)
            .first()
            .reset_index()[["seed", "cid", "global_step"]]
        )
        return s.merge(fz, on=["seed", "cid"], how="left")

    bf = first_zero(base_sub, base_ev)
    af = first_zero(abl_sub, abl_ev)

    for b in BUCKETS:
        bb = bf[bf["bucket"] == b] if not bf.empty else pd.DataFrame()
        aa = af[af["bucket"] == b] if not af.empty else pd.DataFrame()
        rows.append(
            dict(
                bucket=b,
                n_exh_base=len(bb),
                n_exh_abl=len(aa),
                median_step_base=(
                    bb["global_step"].median() if len(bb) else np.nan
                ),
                median_step_abl=(
                    aa["global_step"].median() if len(aa) else np.nan
                ),
                mean_step_base=(
                    bb["global_step"].mean() if len(bb) else np.nan
                ),
                mean_step_abl=(
                    aa["global_step"].mean() if len(aa) else np.nan
                ),
            )
        )
    return pd.DataFrame(rows)


def md_table(df: pd.DataFrame, int_cols: list[str] | None = None) -> str:
    if df.empty:
        return "_(empty)_\n"
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


def write_report(
    impl_info: dict,
    run_info: dict,
    comparisons: dict,
    corr_tables: dict,
    e12_tables: dict,
    exh_tables: dict,
    out_path: Path,
) -> None:
    buf: list[str] = []
    buf.append("# v9.14 §6.4 — E3 Ablation Result\n")
    buf.append("*Phase 2 §6.4 output — Describe only.*\n")
    buf.append("")

    buf.append("## 1. 実装 (flag + smoke + bit-identity)\n")
    for k, v in impl_info.items():
        buf.append(f"- **{k}**: {v}")
    buf.append("")

    buf.append("## 2. Ablation run の実行結果\n")
    for k, v in run_info.items():
        buf.append(f"- **{k}**: {v}")
    buf.append("")

    for tag in ["short", "long"]:
        if tag not in comparisons:
            continue
        buf.append(f"## 3.{['short','long'].index(tag)+1} {tag.capitalize()} run: E3 有効 vs 無効 比較\n")
        buf.append(
            md_table(
                comparisons[tag],
                int_cols=[
                    "n_cids_base", "n_cids_abl",
                    "event_count_base", "event_count_abl",
                    "spend_count_base", "spend_count_abl",
                    "count_E1_death_base", "count_E1_death_abl",
                    "count_E1_birth_base", "count_E1_birth_abl",
                    "count_E2_rise_base", "count_E2_rise_abl",
                    "count_E2_fall_base", "count_E2_fall_abl",
                    "count_E3_contact_base", "count_E3_contact_abl",
                ],
            )
        )
        buf.append("")

    buf.append("## 4. 構造的比較\n")
    for tag in ["short", "long"]:
        if tag not in corr_tables:
            continue
        buf.append(f"### 4.{['short','long'].index(tag)+1} {tag.capitalize()}: Q0 ↔ q_spent 相関\n")
        buf.append(md_table(corr_tables[tag], int_cols=["n"]))
        buf.append("")
    if "exh" in exh_tables and not exh_tables["exh"].empty:
        buf.append("### 4.3 Long: Exhaustion timing shift\n")
        buf.append(
            md_table(
                exh_tables["exh"],
                int_cols=["n_exh_base", "n_exh_abl"],
            )
        )
        buf.append("")

    buf.append("## 5. E1+E2 単独の特性 (ablation 側)\n")
    for tag in ["short", "long"]:
        if tag not in e12_tables:
            continue
        buf.append(f"### 5.{['short','long'].index(tag)+1} {tag.capitalize()}\n")
        buf.append(
            md_table(
                e12_tables[tag],
                int_cols=["event_count", "spend_count"],
            )
        )
        buf.append("")

    buf.append("## 6. 観察事項 (Describe, do not decide)\n")
    # Observations generated inline from the comparison tables
    obs: list[str] = []
    for tag in ["short", "long"]:
        if tag not in comparisons:
            continue
        cmp = comparisons[tag]
        for _, r in cmp.iterrows():
            parts = []
            parts.append(
                f"{tag} bucket={r['bucket']}: "
                f"event_count {_fmt(r['event_count_base'],0)} → {_fmt(r['event_count_abl'],0)} "
                f"(ratio {_fmt(r['event_count_rel'],4)}), "
                f"spend_count {_fmt(r['spend_count_base'],0)} → {_fmt(r['spend_count_abl'],0)}, "
                f"exhaustion_ratio {_fmt(r['exhaustion_ratio_base'],4)} → {_fmt(r['exhaustion_ratio_abl'],4)}, "
                f"q_spent_mean {_fmt(r['q_spent_mean_base'],4)} → {_fmt(r['q_spent_mean_abl'],4)}。"
            )
            obs.append(" ".join(parts))
    for i, line in enumerate(obs, start=1):
        buf.append(f"{i}. {line}")
    buf.append("")
    buf.append("---\n")
    buf.append("*End of §6.4 report.*")
    out_path.write_text("\n".join(buf))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-short", default=str(SCRIPT_DIR / "diag_v914_short"))
    ap.add_argument("--abl-short", default=str(SCRIPT_DIR / "diag_v914_short_noE3"))
    ap.add_argument("--base-long", default=str(SCRIPT_DIR / "diag_v914_long"))
    ap.add_argument("--abl-long", default=str(SCRIPT_DIR / "diag_v914_long_noE3"))
    ap.add_argument("--out", default=str(OUT_PATH))
    ap.add_argument("--impl-note", default="")  # e.g. "bit-identity OK on seed 0"
    ap.add_argument("--run-note", default="")  # e.g. "short wall 2h40m"
    args = ap.parse_args()

    def load_pair(base_d, abl_d):
        base_sub = load_subjects(Path(base_d) / "audit")
        base_ev = load_events(Path(base_d) / "audit")
        abl_sub = load_subjects(Path(abl_d) / "audit")
        abl_ev = load_events(Path(abl_d) / "audit")
        return base_sub, base_ev, abl_sub, abl_ev

    comparisons = {}
    corr_tables = {}
    e12_tables = {}
    exh_tables = {}

    # Short
    base_sub_s, base_ev_s, abl_sub_s, abl_ev_s = load_pair(
        args.base_short, args.abl_short
    )
    if not abl_sub_s.empty:
        base_tbl = basic_bucket_metrics(base_sub_s, base_ev_s, "base")
        abl_tbl = basic_bucket_metrics(abl_sub_s, abl_ev_s, "abl")
        comparisons["short"] = make_comparison(base_tbl, abl_tbl)
        corr_tables["short"] = pd.concat(
            [
                structural_q0_spend_corr(base_sub_s, "base"),
                structural_q0_spend_corr(abl_sub_s, "abl"),
            ],
            ignore_index=True,
        )
        e12_tables["short"] = e12_standalone_profile(abl_sub_s, abl_ev_s)

    # Long
    base_sub_l, base_ev_l, abl_sub_l, abl_ev_l = load_pair(
        args.base_long, args.abl_long
    )
    if not abl_sub_l.empty:
        base_tbl = basic_bucket_metrics(base_sub_l, base_ev_l, "base")
        abl_tbl = basic_bucket_metrics(abl_sub_l, abl_ev_l, "abl")
        comparisons["long"] = make_comparison(base_tbl, abl_tbl)
        corr_tables["long"] = pd.concat(
            [
                structural_q0_spend_corr(base_sub_l, "base"),
                structural_q0_spend_corr(abl_sub_l, "abl"),
            ],
            ignore_index=True,
        )
        e12_tables["long"] = e12_standalone_profile(abl_sub_l, abl_ev_l)
        exh_tables["exh"] = exhaustion_step_shift(
            base_sub_l, base_ev_l, abl_sub_l, abl_ev_l
        )

    impl_info = {
        "CLI flag": "`--disable-e3` (action=store_true, default False)",
        "挙動": "E3 event 発行を skip、contacted_pairs 登録は継続、"
                 "E1/E2 検知・spend packet は不変。Layer A 完全不変。",
        "smoke 条件": "1 seed × maturation 20 / tracking 10 / steps 500",
        "bit-identity": args.impl_note or "(run smoke and fill in)",
    }
    run_info = {
        "short ablation 出力": args.abl_short,
        "long ablation 出力": args.abl_long,
        "実行条件 short": "48 seeds × mat 20 / track 10 / steps 500, parallel -j24",
        "実行条件 long": "5 seeds × mat 20 / track 50 / steps 500, parallel -j5",
        "実行時間": args.run_note or "(see logs/ — fill in)",
    }

    write_report(
        impl_info, run_info, comparisons, corr_tables, e12_tables, exh_tables,
        Path(args.out),
    )
    print(f"wrote: {args.out}")


if __name__ == "__main__":
    main()
