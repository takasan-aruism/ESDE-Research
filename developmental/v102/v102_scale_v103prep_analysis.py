"""v10.2 N-sweep / v10.3 三項共鳴 直結 4 解析

Code A (実装担当) 提案:
  α. 3 cid 共有 link の発生頻度 (triple onset)
  β. 反復発動者の C 振動パターン (主役の C 動学)
  γ. イベント発火 per-cid 分布 (E1/E2/E3 の cid 別頻度)
  δ. ingestion network: eater × ghost n_core ペア構造

出力:
  developmental/v102/followup/
    v103_alpha_triple_link.csv          (per N の triple onset 頻度)
    v103_alpha_triple_link_examples.csv (N=5000 で実例)
    v103_beta_C_swing.csv               (per cid の C 動学指標)
    v103_beta_C_swing_summary.csv       (n_core × group 集計)
    v103_gamma_event_per_cid.csv        (per (N, n_core, group, event_type))
    v103_delta_ingestion_network.csv    (eater n_core × ghost n_core × N)
"""

from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent
OUT = ROOT / "followup"
OUT.mkdir(exist_ok=True)

SCALES = [
    (500, "diag_v102_main_n500"),
    (1000, "diag_v102_main_n1000"),
    (2500, "diag_v102_main_n2500"),
    (5000, "diag_v102_main"),
    (10000, "diag_v102_main_n10000"),
]

TRACKING_START_WINDOW = 20
WINDOW_STEPS = 500
TRACKING_TOTAL_STEPS = 50 * WINDOW_STEPS
SEEDS = list(range(24))


# =========================================================================
# α. 3 cid 共有 link の発生頻度
# =========================================================================
def analysis_alpha() -> tuple[pd.DataFrame, pd.DataFrame]:
    """per_event_audit で (link_id, global_step) ごとに distinct cid を数え、
    3 cid 以上が同時 onset する link 数を集計する。

    α1 (strict simultaneous): 同一 global_step に 3 cid 以上が同 link で E3
    α2 (cumulative): run 全体で同 link に E3 した distinct cid が 3 以上"""
    rows = []
    examples = []

    for N, dirname in SCALES:
        base = ROOT / dirname
        triple_simultaneous_count = 0
        cumulative_3plus_count = 0
        cumulative_4plus_count = 0
        cumulative_5plus_count = 0
        total_e3_events = 0
        total_links_with_e3 = 0

        for seed in SEEDS:
            f = base / f"audit/per_event_audit_seed{seed}.csv"
            df = pd.read_csv(f)
            e3 = df[df["v14_event_type"] == "E3_contact"].copy()
            total_e3_events += len(e3)

            # α1: 同一 (global_step, link_id) で distinct cid >= 3
            simul = (e3.groupby(["global_step", "link_id"])["cid"]
                     .nunique().reset_index(name="n_cids"))
            triple_simul = simul[simul["n_cids"] >= 3]
            triple_simultaneous_count += len(triple_simul)

            # 例の収集 (N=5000 のみ)
            if N == 5000 and len(triple_simul) > 0:
                for _, t in triple_simul.head(20).iterrows():
                    cids = e3[(e3["global_step"] == t["global_step"])
                              & (e3["link_id"] == t["link_id"])]["cid"].tolist()
                    examples.append({
                        "N": N,
                        "seed": seed,
                        "global_step": int(t["global_step"]),
                        "link_id": t["link_id"],
                        "n_cids": int(t["n_cids"]),
                        "cids": ",".join(str(c) for c in sorted(set(cids))),
                    })

            # α2: 同 link_id を共有した distinct cid 数 (run 全期間累積)
            cumul = (e3.groupby("link_id")["cid"]
                     .nunique().reset_index(name="n_distinct_cids"))
            total_links_with_e3 += len(cumul)
            cumulative_3plus_count += (cumul["n_distinct_cids"] >= 3).sum()
            cumulative_4plus_count += (cumul["n_distinct_cids"] >= 4).sum()
            cumulative_5plus_count += (cumul["n_distinct_cids"] >= 5).sum()

        rows.append({
            "N": N,
            "total_E3_events": int(total_e3_events),
            "total_unique_links_with_E3": int(total_links_with_e3),
            "triple_simultaneous_onset": int(triple_simultaneous_count),
            "cumulative_3plus_cids_per_link": int(cumulative_3plus_count),
            "cumulative_4plus_cids_per_link": int(cumulative_4plus_count),
            "cumulative_5plus_cids_per_link": int(cumulative_5plus_count),
            "triple_simul_rate": (
                triple_simultaneous_count / total_links_with_e3
                if total_links_with_e3 else 0),
            "cumul_3plus_rate": (
                cumulative_3plus_count / total_links_with_e3
                if total_links_with_e3 else 0),
        })

    summary = pd.DataFrame(rows)
    examples_df = pd.DataFrame(examples) if examples else pd.DataFrame()
    return summary, examples_df


# =========================================================================
# β. C 動学パターン (反復発動者の C 振動)
# =========================================================================
def analysis_beta() -> tuple[pd.DataFrame, pd.DataFrame]:
    """c_trajectory で各 cid の C 時系列を取り、以下の指標を計算:
      - C_max, C_min (alive 期間中)
      - C_swing_amplitude = C_max - C_min
      - C_swing_total = sum |dC/dw| (total absolute movement)
      - n_C_decreases = C が減少した window 数 (= consciousness 発動回数の代替)
    n_core × n_consciousness bin で集計
    """
    cid_rows = []
    for N, dirname in SCALES:
        base = ROOT / dirname
        for seed in SEEDS:
            cj = pd.read_csv(base / f"balance/c_trajectory_seed{seed}.csv")
            ps = pd.read_csv(base / f"subjects/per_subject_seed{seed}.csv")
            psa = pd.read_csv(base / f"audit/per_subject_audit_seed{seed}.csv")

            # cid → n_core, n_consciousness の lookup
            ps_keys = ps.rename(columns={"cognitive_id": "cid"})[
                ["cid", "n_consciousness_decisions"]]
            psa_keys = psa[["cid", "n_core_member"]]
            meta = ps_keys.merge(psa_keys, on="cid", how="left")

            cj_sorted = cj.sort_values(["cid", "window"])
            for cid, sub in cj_sorted.groupby("cid"):
                sub = sub.sort_values("window")
                C_vals = sub["C_at_window_end"].values
                if len(C_vals) < 2:
                    continue
                dC = np.diff(C_vals)
                C_max = int(C_vals.max())
                C_min = int(C_vals.min())
                C_swing_amplitude = int(C_max - C_min)
                C_swing_total = float(np.sum(np.abs(dC)))
                n_C_decreases = int((dC < 0).sum())
                n_C_increases = int((dC > 0).sum())

                meta_row = meta[meta["cid"] == cid]
                if len(meta_row) == 0:
                    continue
                n_core = meta_row["n_core_member"].iloc[0]
                n_con = (meta_row["n_consciousness_decisions"].iloc[0]
                         if not pd.isna(
                             meta_row["n_consciousness_decisions"].iloc[0])
                         else 0)

                cid_rows.append({
                    "N": N,
                    "seed": seed,
                    "cid": int(cid),
                    "n_core": int(n_core) if pd.notna(n_core) else None,
                    "n_consciousness": int(n_con),
                    "n_windows_alive": len(sub),
                    "C_max": C_max,
                    "C_min": C_min,
                    "C_swing_amplitude": C_swing_amplitude,
                    "C_swing_total": C_swing_total,
                    "n_C_decreases": n_C_decreases,
                    "n_C_increases": n_C_increases,
                })
    df = pd.DataFrame(cid_rows)

    # 集計: n_core × group (group = no_act / single / repeated)
    def grp(n_con):
        if n_con == 0: return "no_activation"
        elif n_con < 5: return "single_or_few"
        else: return "repeated_5plus"

    df["group"] = df["n_consciousness"].apply(grp)
    summary_rows = []
    for N in sorted(df["N"].unique()):
        for n_core in sorted(df[df["N"] == N]["n_core"].dropna().unique()):
            for g in ["no_activation", "single_or_few", "repeated_5plus"]:
                sub = df[(df["N"] == N) & (df["n_core"] == n_core)
                         & (df["group"] == g)]
                if len(sub) == 0:
                    continue
                summary_rows.append({
                    "N": N,
                    "n_core": int(n_core),
                    "group": g,
                    "n_cid": len(sub),
                    "C_max_median": float(sub["C_max"].median()),
                    "C_swing_amplitude_median": float(
                        sub["C_swing_amplitude"].median()),
                    "C_swing_total_median": float(
                        sub["C_swing_total"].median()),
                    "n_C_decreases_median": float(
                        sub["n_C_decreases"].median()),
                    "n_C_increases_median": float(
                        sub["n_C_increases"].median()),
                    "n_windows_alive_median": float(
                        sub["n_windows_alive"].median()),
                })
    summary = pd.DataFrame(summary_rows)
    return df, summary


# =========================================================================
# γ. イベント発火 per-cid 分布
# =========================================================================
def analysis_gamma() -> pd.DataFrame:
    """per_event_audit で各 cid の E1_*/E2_*/E3_contact を数え、
    n_core × group 別に分布を集計"""
    rows = []
    for N, dirname in SCALES:
        base = ROOT / dirname
        per_seed = []
        for seed in SEEDS:
            ev = pd.read_csv(base / f"audit/per_event_audit_seed{seed}.csv")
            ps = pd.read_csv(base / f"subjects/per_subject_seed{seed}.csv")
            psa = pd.read_csv(base / f"audit/per_subject_audit_seed{seed}.csv")

            # event type をシンプルに分類
            def cat(et):
                if et.startswith("E1_"): return "E1"
                elif et.startswith("E2_"): return "E2"
                elif et == "E3_contact": return "E3"
                else: return "other"
            ev["category"] = ev["v14_event_type"].apply(cat)

            # per cid event count by category
            per_cid_event = (ev.groupby(["cid", "category"]).size()
                             .unstack(fill_value=0).reset_index())
            for c in ["E1", "E2", "E3"]:
                if c not in per_cid_event.columns:
                    per_cid_event[c] = 0

            # n_core, n_consciousness と join
            ps_keys = ps.rename(columns={"cognitive_id": "cid"})[
                ["cid", "n_consciousness_decisions"]]
            psa_keys = psa[["cid", "n_core_member"]]
            meta = ps_keys.merge(psa_keys, on="cid", how="left")
            merged = per_cid_event.merge(meta, on="cid", how="inner")
            merged["seed"] = seed
            per_seed.append(merged)

        df = pd.concat(per_seed, ignore_index=True)
        df["n_consciousness"] = df["n_consciousness_decisions"].fillna(
            0).astype(int)
        df["n_core"] = df["n_core_member"].fillna(-1).astype(int)

        def grp(n_con):
            if n_con == 0: return "no_activation"
            elif n_con < 5: return "single_or_few"
            else: return "repeated_5plus"
        df["group"] = df["n_consciousness"].apply(grp)

        for n_core in sorted(df["n_core"].unique()):
            if n_core < 0:
                continue
            for g in ["no_activation", "single_or_few", "repeated_5plus"]:
                sub = df[(df["n_core"] == n_core) & (df["group"] == g)]
                if len(sub) == 0:
                    continue
                rows.append({
                    "N": N,
                    "n_core": int(n_core),
                    "group": g,
                    "n_cid": len(sub),
                    "E1_median": float(sub["E1"].median()),
                    "E1_mean": float(sub["E1"].mean()),
                    "E2_median": float(sub["E2"].median()),
                    "E2_mean": float(sub["E2"].mean()),
                    "E3_median": float(sub["E3"].median()),
                    "E3_mean": float(sub["E3"].mean()),
                    "total_events_median": float(
                        (sub["E1"] + sub["E2"] + sub["E3"]).median()),
                })
    return pd.DataFrame(rows)


# =========================================================================
# δ. ingestion network: eater × ghost n_core ペア
# =========================================================================
def analysis_delta() -> tuple[pd.DataFrame, pd.DataFrame]:
    """ingestion_events の eater (observer_cid) と ghost (ghost_cid) の
    n_core クロス表を作る"""
    rows = []
    eater_degree_rows = []
    for N, dirname in SCALES:
        base = ROOT / dirname
        for seed in SEEDS:
            ie = pd.read_csv(base / f"ingestion/ingestion_events_seed{seed}.csv")
            psa = pd.read_csv(base / f"audit/per_subject_audit_seed{seed}.csv")
            cid_to_ncore = psa.set_index("cid")["n_core_member"].to_dict()

            ie["eater_n_core"] = ie["observer_cid"].map(cid_to_ncore)
            ie["ghost_n_core"] = ie["ghost_cid"].map(cid_to_ncore)
            ie["seed"] = seed
            ie["N"] = N
            rows.append(ie[[
                "N", "seed", "observer_cid", "ghost_cid",
                "eater_n_core", "ghost_n_core",
                "received", "digested", "was_empty",
            ]])

            # eater 別摂食回数 (= eater degree)
            for eater_cid, sub in ie.groupby("observer_cid"):
                eater_n_core = cid_to_ncore.get(eater_cid)
                eater_degree_rows.append({
                    "N": N,
                    "seed": seed,
                    "eater_cid": int(eater_cid),
                    "eater_n_core": int(eater_n_core) if pd.notna(eater_n_core) else None,
                    "n_unique_ghosts": int(sub["ghost_cid"].nunique()),
                    "n_total_ingestions": len(sub),
                    "total_received": float(sub["received"].sum()),
                })

    all_ie = pd.concat(rows, ignore_index=True)
    eater_degree = pd.DataFrame(eater_degree_rows)

    # クロス表: eater n_core × ghost n_core × N
    cross = (all_ie.groupby(["N", "eater_n_core", "ghost_n_core"])
             .agg(n_events=("received", "size"),
                  total_received=("received", "sum"))
             .reset_index())
    return cross, eater_degree


# =========================================================================
# main
# =========================================================================
def main():
    print("## α: 3 cid 共有 link の発生頻度")
    alpha_summary, alpha_examples = analysis_alpha()
    alpha_summary.to_csv(OUT / "v103_alpha_triple_link.csv", index=False)
    if len(alpha_examples) > 0:
        alpha_examples.to_csv(OUT / "v103_alpha_triple_link_examples.csv",
                              index=False)
    print(alpha_summary.to_string(index=False))
    if len(alpha_examples) > 0:
        print(f"\n  examples (N=5000): {len(alpha_examples)} rows recorded")
        print(alpha_examples.head(10).to_string(index=False))

    print("\n## β: 反復発動者の C 振動")
    beta_detail, beta_summary = analysis_beta()
    beta_detail.to_csv(OUT / "v103_beta_C_swing.csv", index=False)
    beta_summary.to_csv(OUT / "v103_beta_C_swing_summary.csv", index=False)
    # n_core=5 のみ表示
    print(beta_summary[beta_summary["n_core"] == 5].to_string(index=False))

    print("\n## γ: per-cid event 分布")
    gamma_df = analysis_gamma()
    gamma_df.to_csv(OUT / "v103_gamma_event_per_cid.csv", index=False)
    print(gamma_df[gamma_df["n_core"].isin([2, 5])].to_string(index=False))

    print("\n## δ: ingestion network (eater × ghost n_core)")
    delta_cross, delta_eater = analysis_delta()
    delta_cross.to_csv(OUT / "v103_delta_ingestion_network.csv", index=False)
    delta_eater.to_csv(OUT / "v103_delta_eater_degree.csv", index=False)
    # N=5000 のクロス表のみ表示
    print("--- N=5000 cross table ---")
    cross5 = delta_cross[delta_cross["N"] == 5000]
    pivot = cross5.pivot_table(
        index="eater_n_core", columns="ghost_n_core",
        values="n_events", fill_value=0)
    print(pivot.to_string())


if __name__ == "__main__":
    main()
