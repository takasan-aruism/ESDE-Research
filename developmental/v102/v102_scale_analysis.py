"""v10.2 スケールテスト 結果集計スクリプト

任意の diag_v102_main_n{N}/ ディレクトリを受け取り、
スケール比較に必要な指標を抽出して JSON として返す。

使い方:
  python3 v102_scale_analysis.py diag_v102_main_n500
  python3 v102_scale_analysis.py diag_v102_main         # = N=5000

出力:
  diag_v102_main_n{N}/scale_summary.json
"""

import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np


def gini(x):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if x.size == 0 or x.sum() <= 0:
        return None
    x = np.sort(x)
    n = x.size
    cum = x.cumsum()
    return float((n + 1 - 2 * cum.sum() / cum[-1]) / n)


def aggregate_seed_dir(root: Path) -> dict:
    seeds = sorted(int(p.stem.replace("per_subject_seed", ""))
                   for p in (root / "subjects").glob("per_subject_seed*.csv"))

    # 全 seed の per_subject 結合
    ps_list = []
    psa_list = []
    bs_list = []
    is_list = []  # ingestion summary
    for s in seeds:
        ps = pd.read_csv(root / f"subjects/per_subject_seed{s}.csv")
        ps["seed"] = s
        ps_list.append(ps)

        psa = pd.read_csv(root / f"audit/per_subject_audit_seed{s}.csv")
        psa_list.append(psa)

        bs = pd.read_csv(root / f"balance/balance_summary_seed{s}.csv")
        bs_list.append(bs)

        ie_s_path = root / f"ingestion/ingestion_summary_seed{s}.csv"
        if ie_s_path.exists():
            ies = pd.read_csv(ie_s_path)
            is_list.append(ies)

    ps_all = pd.concat(ps_list, ignore_index=True)
    psa_all = pd.concat(psa_list, ignore_index=True)
    bs_all = pd.concat(bs_list, ignore_index=True)
    is_all = pd.concat(is_list, ignore_index=True) if is_list else pd.DataFrame()

    # cid マスター: per_subject + n_core
    psa_keys = psa_all[["seed", "cid", "n_core_member", "v14_q0"]].rename(
        columns={"cid": "cognitive_id", "n_core_member": "n_core"}
    )
    master = ps_all.merge(psa_keys, on=["seed", "cognitive_id"], how="left")

    # ============================================
    # 集計
    # ============================================
    n_seeds = len(seeds)
    n_subjects = len(master)

    # n_core 分布
    n_core_dist = master["n_core"].value_counts().sort_index().to_dict()
    n_core_dist = {int(k): int(v) for k, v in n_core_dist.items()
                   if not pd.isna(k)}

    # 'unformed' などの文字列が混じる可能性があるので強制 numeric 化
    master["v11_b_gen_num"] = pd.to_numeric(
        master["v11_b_gen"], errors="coerce"
    )
    master["v14_q0_num"] = pd.to_numeric(
        master["v14_q0"], errors="coerce"
    )

    q0 = master["v14_q0_num"].dropna()
    bgen = master["v11_b_gen_num"].replace([np.inf, -np.inf], np.nan).dropna()
    q0_summary = {
        "mean": float(q0.mean()) if len(q0) else None,
        "median": float(q0.median()) if len(q0) else None,
        "p25": float(q0.quantile(0.25)) if len(q0) else None,
        "p75": float(q0.quantile(0.75)) if len(q0) else None,
        "n_with_q0": int(len(q0)),
    }
    bgen_summary = {
        "mean": float(bgen.mean()) if len(bgen) else None,
        "median": float(bgen.median()) if len(bgen) else None,
        "p25": float(bgen.quantile(0.25)) if len(bgen) else None,
        "p75": float(bgen.quantile(0.75)) if len(bgen) else None,
        "n_with_bgen": int(len(bgen)),
    }

    # Q0 / B_Gen を n_core 別にも
    q0_by_ncore = {}
    bgen_by_ncore = {}
    for nc in sorted(master["n_core"].dropna().unique()):
        sub = master[master["n_core"] == nc]
        q0_sub = sub["v14_q0_num"].dropna()
        bgen_sub = sub["v11_b_gen_num"].replace(
            [np.inf, -np.inf], np.nan).dropna()
        q0_by_ncore[int(nc)] = {
            "n": int(len(sub)),
            "median": float(q0_sub.median()) if len(q0_sub) else None,
            "mean": float(q0_sub.mean()) if len(q0_sub) else None,
        }
        bgen_by_ncore[int(nc)] = {
            "median": float(bgen_sub.median()) if len(bgen_sub) else None,
            "mean": float(bgen_sub.mean()) if len(bgen_sub) else None,
        }

    # 寿命 (final_state ごと)
    final_state_dist = master["final_state"].value_counts().to_dict()

    # 認知 / 意識バランス (24 seeds 合計)
    bs_total = bs_all.sum(numeric_only=True)
    total_decisions = int(bs_total.get("total_decisions", 0))
    n_cognition = int(bs_total.get("n_cognition_won", 0))
    n_consciousness = int(bs_total.get("n_consciousness_won", 0))
    n_skip_q_zero = int(bs_total.get("n_skip_q_zero_only", 0))
    n_skip_c_zero = int(bs_total.get("n_skip_c_zero_only", 0))
    n_skip_both = int(bs_total.get("n_skip_both_zero", 0))
    n_skip_no_cand = int(bs_total.get("n_skip_no_candidates", 0))

    balance = {
        "total_decisions": total_decisions,
        "n_cognition": n_cognition,
        "n_consciousness": n_consciousness,
        "cognition_rate": (n_cognition / total_decisions
                           if total_decisions else None),
        "consciousness_rate": (n_consciousness / total_decisions
                               if total_decisions else None),
        "n_skip_q_zero": n_skip_q_zero,
        "n_skip_c_zero": n_skip_c_zero,
        "n_skip_both_zero": n_skip_both,
        "n_skip_no_candidates": n_skip_no_cand,
        "skip_c_zero_rate": (n_skip_c_zero / total_decisions
                             if total_decisions else None),
    }

    # C 蓄積
    c_summary = {
        "C_max": int(bs_all["C_max"].max()),
        "C_mean_at_run_end": float(bs_all["C_mean_at_run_end"].mean()),
        "C_p50_mean": float(bs_all["C_p50"].mean()),
        "C_p95_mean": float(bs_all["C_p95"].mean()),
        "n_hosted_at_run_end": int(bs_all["n_hosted_at_run_end"].sum()),
    }

    # 摂食 (ingestion)
    if not is_all.empty:
        ingestion = {
            "n_ingestion_events": int(is_all["n_ingestion_events"].sum()),
            "n_empty_ingestions": int(is_all["n_empty_ingestions"].sum()),
            "n_phantom_contacts": int(is_all["n_phantom_contacts"].sum()),
            "total_gain": int(is_all["total_gain"].sum()),
            "total_received": int(is_all["total_received"].sum()),
            "total_digested": int(is_all["total_digested"].sum()),
            "n_unique_eaters": int(is_all["n_unique_eaters"].sum()),
            "eater_rate": (
                float(is_all["n_unique_eaters"].sum() / n_subjects)
                if n_subjects else None
            ),
        }
    else:
        ingestion = None

    # 意識発動経験率 (n_core 別)
    activated = master["n_consciousness_decisions"].fillna(0) > 0
    consciousness_activation = {}
    for nc in sorted(master["n_core"].dropna().unique()):
        sub = master[master["n_core"] == nc]
        n_total = len(sub)
        n_act = int((sub["n_consciousness_decisions"].fillna(0) > 0).sum())
        consciousness_activation[int(nc)] = {
            "n": n_total,
            "n_activated": n_act,
            "activation_rate": n_act / n_total if n_total else None,
        }

    # 全体 conservation
    conservation = {
        "Q_plus_C_total_at_run_end": int(
            bs_all["Q_plus_C_total_at_run_end"].sum()),
        "ghost_residual_Q_total_at_run_end": int(
            bs_all["ghost_residual_Q_total_at_run_end"].sum()),
        "n_e1_e2_spend": int(bs_all["n_e1_e2_spend"].sum()),
        "total_received_via_consciousness": int(
            bs_all["total_received_via_consciousness"].sum()),
        "total_digestion_dissipation": int(
            bs_all["total_digestion_dissipation"].sum()),
    }

    return {
        "n_seeds": n_seeds,
        "n_subjects": n_subjects,
        "n_subjects_per_seed_mean": n_subjects / n_seeds if n_seeds else None,
        "n_core_distribution": n_core_dist,
        "final_state_distribution": {
            str(k): int(v) for k, v in final_state_dist.items()
        },
        "q0": q0_summary,
        "b_gen": bgen_summary,
        "q0_by_n_core": q0_by_ncore,
        "b_gen_by_n_core": bgen_by_ncore,
        "balance": balance,
        "c_accumulation": c_summary,
        "ingestion": ingestion,
        "consciousness_activation_by_n_core": consciousness_activation,
        "conservation": conservation,
    }


def main():
    if len(sys.argv) < 2:
        print("usage: python v102_scale_analysis.py <diag_dir>")
        sys.exit(1)

    root = Path(sys.argv[1])
    if not root.exists():
        print(f"ERROR: {root} not found")
        sys.exit(1)

    print(f"Aggregating {root}...")
    summary = aggregate_seed_dir(root)
    out = root / "scale_summary.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Wrote {out}")
    print(f"  n_subjects: {summary['n_subjects']}")
    print(f"  n_core_dist: {summary['n_core_distribution']}")
    print(f"  cognition_rate: {summary['balance']['cognition_rate']:.4f}")
    print(f"  consciousness_rate: {summary['balance']['consciousness_rate']:.4f}")
    print(f"  C_max: {summary['c_accumulation']['C_max']}")
    if summary['ingestion']:
        print(f"  eater_rate: {summary['ingestion']['eater_rate']:.4f}")


if __name__ == "__main__":
    main()
