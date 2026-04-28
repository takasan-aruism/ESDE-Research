"""5 スケールの scale_summary.json を統合して比較表を生成。

入力:
  diag_v102_main_n500/scale_summary.json
  diag_v102_main_n1000/scale_summary.json
  diag_v102_main_n2500/scale_summary.json
  diag_v102_main/scale_summary.json          (= N=5000)
  diag_v102_main_n10000/scale_summary.json

出力:
  scale_comparison.csv (主要指標 5 列)
  scale_comparison_n_core.csv (n_core 別指標)
  scale_comparison_balance.csv (認知/意識バランス)

stdout に Markdown 表として print。
"""

import json
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent

SCALES = [
    (500, "diag_v102_main_n500"),
    (1000, "diag_v102_main_n1000"),
    (2500, "diag_v102_main_n2500"),
    (5000, "diag_v102_main"),
    (10000, "diag_v102_main_n10000"),
]


def load_all() -> list[tuple[int, dict]]:
    out = []
    for n, dirname in SCALES:
        p = ROOT / dirname / "scale_summary.json"
        if p.exists():
            with open(p) as f:
                out.append((n, json.load(f)))
        else:
            print(f"[skip] {p} not found", file=sys.stderr)
    return out


def main_overview(data: list[tuple[int, dict]]) -> pd.DataFrame:
    rows = []
    for n, d in data:
        b = d["balance"]
        c = d["c_accumulation"]
        ing = d.get("ingestion") or {}
        rows.append({
            "N": n,
            "n_subjects": d["n_subjects"],
            "subjects_per_seed": round(d["n_subjects_per_seed_mean"], 1),
            "Q0_median": d["q0"]["median"],
            "Q0_mean": round(d["q0"]["mean"], 2) if d["q0"]["mean"] else None,
            "B_Gen_median": (round(d["b_gen"]["median"], 2)
                             if d["b_gen"]["median"] else None),
            "n_decisions": b["total_decisions"],
            "cog_rate": round(b["cognition_rate"], 4),
            "con_rate": round(b["consciousness_rate"], 4),
            "skip_C0_rate": round(b["skip_c_zero_rate"], 4),
            "C_max": c["C_max"],
            "C_mean_run_end": round(c["C_mean_at_run_end"], 2),
            "n_hosted_run_end": c["n_hosted_at_run_end"],
            "n_unique_eaters": ing.get("n_unique_eaters"),
            "eater_rate": round(ing["eater_rate"], 4) if ing else None,
            "n_phantom": ing.get("n_phantom_contacts"),
            "n_empty_ing": ing.get("n_empty_ingestions"),
        })
    return pd.DataFrame(rows)


def n_core_table(data: list[tuple[int, dict]]) -> pd.DataFrame:
    """n_core × N の二軸表 (cid 数 + 意識発動経験率)"""
    rows = []
    all_ncores = set()
    for n, d in data:
        all_ncores.update(int(k) for k in d["n_core_distribution"].keys())
    all_ncores = sorted(all_ncores)

    for n, d in data:
        n_core_dist = d["n_core_distribution"]
        act = d["consciousness_activation_by_n_core"]
        for nc in all_ncores:
            cnt = n_core_dist.get(str(nc), 0) or n_core_dist.get(nc, 0)
            act_rec = act.get(str(nc)) or act.get(nc)
            rows.append({
                "N": n,
                "n_core": nc,
                "cid_count": cnt,
                "cid_share": (cnt / d["n_subjects"]
                              if d["n_subjects"] else 0),
                "consciousness_activation_rate": (
                    act_rec["activation_rate"] if act_rec else None),
                "Q0_median_by_n_core": (
                    d["q0_by_n_core"].get(str(nc), {}).get("median")
                    or d["q0_by_n_core"].get(nc, {}).get("median")),
                "B_Gen_median_by_n_core": (
                    d["b_gen_by_n_core"].get(str(nc), {}).get("median")
                    or d["b_gen_by_n_core"].get(nc, {}).get("median")),
            })
    return pd.DataFrame(rows)


def conservation_table(data: list[tuple[int, dict]]) -> pd.DataFrame:
    rows = []
    for n, d in data:
        c = d["conservation"]
        rows.append({
            "N": n,
            "Q+C_total_run_end": c["Q_plus_C_total_at_run_end"],
            "ghost_residual_Q": c["ghost_residual_Q_total_at_run_end"],
            "n_E1_E2_spend": c["n_e1_e2_spend"],
            "received_via_consciousness": c[
                "total_received_via_consciousness"],
            "digestion_dissipation": c["total_digestion_dissipation"],
            "Q+C_per_subject": (
                c["Q_plus_C_total_at_run_end"] / d["n_subjects"]
                if d["n_subjects"] else None),
        })
    return pd.DataFrame(rows)


def to_markdown(df: pd.DataFrame, title: str) -> str:
    """tabulate に依存しない簡易 Markdown 生成"""
    out = [f"\n### {title}\n"]
    cols = list(df.columns)
    out.append("| " + " | ".join(cols) + " |")
    out.append("| " + " | ".join(["---"] * len(cols)) + " |")

    def fmt(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "-"
        if isinstance(v, float):
            if abs(v) >= 1000:
                return f"{v:.0f}"
            return f"{v:.4g}"
        return str(v)

    for _, row in df.iterrows():
        out.append("| " + " | ".join(fmt(row[c]) for c in cols) + " |")
    return "\n".join(out)


if __name__ == "__main__":
    data = load_all()
    if len(data) == 0:
        print("No scale_summary.json found.")
        sys.exit(1)

    overview = main_overview(data)
    n_core = n_core_table(data)
    cons = conservation_table(data)

    overview.to_csv(ROOT / "scale_comparison.csv", index=False)
    n_core.to_csv(ROOT / "scale_comparison_n_core.csv", index=False)
    cons.to_csv(ROOT / "scale_comparison_conservation.csv", index=False)

    print(to_markdown(overview, "全体サマリ"))
    print(to_markdown(n_core, "n_core 別 cid 分布 + 意識発動率"))
    print(to_markdown(cons, "保存則 / 流入散逸"))
    print(f"\n[{len(data)} scales aggregated]")
