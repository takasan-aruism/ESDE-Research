"""v10.2 詳細解析 (5 本)

入力:
  diag_v102_main/{audit,balance,ingestion,subjects}/*.csv (24 seeds)

出力:
  diag_v102_main/analysis/
    analysis_1_individuality.csv (per cid)
    analysis_1_individuality_summary.csv
    analysis_2_topology.csv (per cid)
    analysis_2_topology_summary.csv
    analysis_3_temporal_dynamics.csv (per (seed,window))
    analysis_3_temporal_dynamics_n_core.csv (per (seed,window,n_core))
    analysis_4_inequality.csv (per (seed,window))
    analysis_4_inequality_summary.csv
    analysis_5_first_consciousness.csv (per cid)
    analysis_5_first_consciousness_summary.csv

設計メモ:
  global_step = (window - 20) * 500 + step  (tracking 開始基準)
  registered_global_step = (registered_window - 20) * 500 + registered_step
  tracking_lifetime = (host_lost_step or 25000) - registered_global_step
"""

from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent / "diag_v102_main"
OUT = ROOT / "analysis"
OUT.mkdir(exist_ok=True)

SEEDS = list(range(24))
TRACKING_START_WINDOW = 20
WINDOW_STEPS = 500
TRACKING_TOTAL_STEPS = 50 * WINDOW_STEPS  # 25000


def gini(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if x.size == 0:
        return np.nan
    if np.all(x == 0):
        return 0.0
    if (x < 0).any():
        x = x - x.min()
    x = np.sort(x)
    n = x.size
    cum = x.cumsum()
    return float((n + 1 - 2 * cum.sum() / cum[-1]) / n) if cum[-1] > 0 else 0.0


def top_share(x: np.ndarray, frac: float) -> float:
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if x.size == 0 or x.sum() <= 0:
        return np.nan
    x = np.sort(x)[::-1]
    k = max(1, int(np.ceil(x.size * frac)))
    return float(x[:k].sum() / x.sum())


def load_seed(seed: int) -> dict:
    """seed 1 つ分の必要 CSV をまとめてロード"""
    base = ROOT
    return {
        "ps": pd.read_csv(base / f"subjects/per_subject_seed{seed}.csv"),
        "psa": pd.read_csv(base / f"audit/per_subject_audit_seed{seed}.csv"),
        "bd": pd.read_csv(base / f"balance/balance_decisions_seed{seed}.csv"),
        "cj": pd.read_csv(base / f"balance/c_trajectory_seed{seed}.csv"),
        "ie": pd.read_csv(base / f"ingestion/ingestion_events_seed{seed}.csv"),
        "ev": pd.read_csv(base / f"audit/per_event_audit_seed{seed}.csv"),
        "bs": pd.read_csv(base / f"balance/balance_summary_seed{seed}.csv"),
    }


def build_cid_master(d: dict, seed: int) -> pd.DataFrame:
    """seed 内の cid マスター: per_subject + per_subject_audit を結合"""
    ps = d["ps"].rename(columns={"cognitive_id": "cid"})
    psa = d["psa"][["cid", "n_core_member", "v14_q0", "registered_window",
                    "registered_step"]].copy()

    m = ps.merge(psa, on="cid", how="left")
    m["seed"] = seed
    m["n_core"] = m["n_core_member"]

    # tracking 基準の生死 step
    m["registered_global_step"] = (
        (m["registered_window"] - TRACKING_START_WINDOW) * WINDOW_STEPS
        + m["registered_step"]
    )
    # host_lost_step は per_subject 由来 (tracking-relative)
    m["death_global_step"] = m["host_lost_step"].fillna(TRACKING_TOTAL_STEPS)
    m["tracking_lifetime"] = (
        m["death_global_step"] - m["registered_global_step"]
    ).clip(lower=0)

    # 発動群フラグ
    m["consciousness_activated"] = m["n_consciousness_decisions"].fillna(0) > 0
    return m


# =========================================================================
# 解析 1: 個別性 — 発動群 vs 非発動群
# =========================================================================
def analysis_1(all_seeds: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for seed_data in all_seeds:
        seed = seed_data["seed"]
        m = seed_data["master"]
        bd = seed_data["bd"]
        cj = seed_data["cj"]

        # 初回 cognition (= C+1) step
        cog = bd[bd["decision"] == "cognition"].sort_values("global_step")
        first_cog = (
            cog.groupby("observer_cid")["global_step"]
            .min()
            .rename("c_first_increment_step")
        )

        # 初期 window 認知活動密度 (登録後 5 window 平均)
        cj_sorted = cj.sort_values(["cid", "window"])

        def initial_density(g: pd.DataFrame) -> float:
            head = g.head(5)
            if len(head) == 0:
                return 0.0
            return head["n_cognition_in_window"].sum() / len(head)

        init_dens = (
            cj_sorted.groupby("cid").apply(initial_density, include_groups=False)
            .rename("initial_window_cognition_density")
        )

        # 初期接触相手の n_core 分布 (最初 5 件の balance_decisions)
        bd_sorted = bd.sort_values(["observer_cid", "global_step"])
        # n_core lookup
        n_core_map = m.set_index("cid")["n_core"].to_dict()

        def init_partner_n_core(g: pd.DataFrame) -> dict:
            head = g.head(5)
            partners = head["contacted_cid"].dropna().tolist()
            ns = [n_core_map.get(int(p), np.nan) for p in partners]
            ns = [n for n in ns if not np.isnan(n)]
            if not ns:
                return {"init_partner_n_core_mean": np.nan,
                        "init_partner_n_core_count": 0}
            return {"init_partner_n_core_mean": float(np.mean(ns)),
                    "init_partner_n_core_count": len(ns)}

        partner_records = []
        for cid_val, g in bd_sorted.groupby("observer_cid"):
            r = init_partner_n_core(g)
            r["cid"] = cid_val
            partner_records.append(r)
        partner_df = pd.DataFrame(partner_records)

        per = m[[
            "seed", "cid", "n_core", "v14_q0", "v11_b_gen",
            "tracking_lifetime", "n_cognition_decisions",
            "n_consciousness_decisions", "n_balance_skipped",
            "C_at_run_end", "v18_cognitive_gain_final",
            "consciousness_activated",
        ]].copy()
        per["group"] = np.where(per["consciousness_activated"], "activated",
                                "non_activated")
        per = per.merge(first_cog, left_on="cid", right_index=True, how="left")
        per = per.merge(init_dens, left_on="cid", right_index=True, how="left")
        per = per.merge(partner_df, on="cid", how="left")
        rows.append(per)

    df = pd.concat(rows, ignore_index=True)

    # 集計: n_core × group × 各指標 (mean / median / q1 / q3)
    metrics = [
        "v14_q0", "v11_b_gen", "tracking_lifetime",
        "n_cognition_decisions", "n_balance_skipped",
        "C_at_run_end", "v18_cognitive_gain_final",
        "c_first_increment_step", "initial_window_cognition_density",
        "init_partner_n_core_mean",
    ]
    agg_rows = []
    for n_core, g_nc in df.groupby("n_core"):
        for grp, g_g in g_nc.groupby("group"):
            row = {"n_core": int(n_core), "group": grp, "n": len(g_g)}
            for col in metrics:
                vals = pd.to_numeric(g_g[col], errors="coerce").dropna()
                if len(vals) == 0:
                    row[f"{col}_mean"] = np.nan
                    row[f"{col}_median"] = np.nan
                    row[f"{col}_q1"] = np.nan
                    row[f"{col}_q3"] = np.nan
                else:
                    row[f"{col}_mean"] = float(vals.mean())
                    row[f"{col}_median"] = float(vals.median())
                    row[f"{col}_q1"] = float(vals.quantile(0.25))
                    row[f"{col}_q3"] = float(vals.quantile(0.75))
            agg_rows.append(row)
    summary = pd.DataFrame(agg_rows).sort_values(["n_core", "group"])
    return df, summary


# =========================================================================
# 解析 2: トポロジー — lifecycle pattern
# =========================================================================
def classify_lifecycle(row: pd.Series) -> str:
    """4 分類: 完全非発動 / 後期発動 / 早期発動 / 反復発動"""
    n_con = row["n_consciousness_decisions"]
    if n_con == 0:
        return "no_activation"
    if n_con >= 5:  # 反復: 5 回以上
        return "repeated"
    # 初回発動の lifecycle phase (0-1) で early vs late
    phase = row.get("first_consciousness_phase", np.nan)
    if pd.isna(phase):
        return "single_unknown"
    return "early_single" if phase < 0.5 else "late_single"


def analysis_2(all_seeds: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for seed_data in all_seeds:
        seed = seed_data["seed"]
        m = seed_data["master"]
        bd = seed_data["bd"]

        # 初回 consciousness step / phase
        con = bd[bd["decision"] == "consciousness"].sort_values("global_step")
        first_con = (
            con.groupby("observer_cid")["global_step"]
            .min()
            .rename("first_consciousness_global_step")
        )
        per = m[[
            "seed", "cid", "n_core", "tracking_lifetime",
            "registered_global_step", "death_global_step",
            "n_consciousness_decisions", "n_cognition_decisions",
            "C_at_run_end",
        ]].copy()
        per = per.merge(first_con, left_on="cid", right_index=True, how="left")

        # phase = (first - registered) / (death - registered)
        denom = per["tracking_lifetime"].replace(0, np.nan)
        per["first_consciousness_phase"] = (
            (per["first_consciousness_global_step"] - per["registered_global_step"]) / denom
        )

        per["lifecycle_pattern"] = per.apply(classify_lifecycle, axis=1)
        rows.append(per)

    df = pd.concat(rows, ignore_index=True)

    # 集計: n_core × lifecycle_pattern の cid 数
    summary = (
        df.groupby(["n_core", "lifecycle_pattern"])
        .size()
        .reset_index(name="n")
    )
    # 各 n_core 内での比率
    totals = summary.groupby("n_core")["n"].sum().rename("total")
    summary = summary.merge(totals, on="n_core")
    summary["share"] = summary["n"] / summary["total"]
    summary = summary.sort_values(["n_core", "lifecycle_pattern"])
    return df, summary


# =========================================================================
# 解析 3: 動的均衡 vs 進化継続 — 時系列
# =========================================================================
def analysis_3(all_seeds: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    win_rows = []
    win_nc_rows = []

    for seed_data in all_seeds:
        seed = seed_data["seed"]
        m = seed_data["master"][["cid", "n_core"]].copy()
        cj = seed_data["cj"].merge(m, on="cid", how="left")
        bd = seed_data["bd"]
        ie = seed_data["ie"]
        ev = seed_data["ev"]

        # ev: E1/E2 の spend (event_type prefix で判定、spend_flag=True)
        # 値は "E1_death", "E1_birth", "E2_rise", "E2_fall", "E3_contact"
        ev_e12 = ev[
            ev["v14_event_type"].str.startswith(("E1_", "E2_"), na=False)
            & (ev["v14_spend_flag"] == True)
        ]
        # window はあるか?
        if "window" in ev_e12.columns:
            e12_per_window = ev_e12.groupby("window").size().rename("e1_e2_dissipation")
        else:
            e12_per_window = pd.Series(dtype=int)

        # ingestion: gain, digested per window
        ie_per_window = ie.groupby("window").agg(
            gain_in_window=("gain", "sum"),
            digestion_dissipation=("digested", "sum"),
            n_ingestion=("gain", "size"),
        )

        # consciousness events per window
        con_per_window = (
            bd[bd["decision"] == "consciousness"]
            .groupby("window").size().rename("n_consciousness_events")
        )

        # ghost residual_Q per window: ingestion_events に residual_Q_after があるが、
        # ghost 全体の総和は別途の集計が必要。ここでは hosted の Q + C のみ追う。
        # cj に Q_remaining_at_window_end と C_at_window_end がある
        win_agg = cj.groupby("window").agg(
            hosted_count=("cid", "nunique"),
            Q_total=("Q_remaining_at_window_end", "sum"),
            C_total=("C_at_window_end", "sum"),
            n_cognition=("n_cognition_in_window", "sum"),
            n_consciousness_in_w=("n_consciousness_in_window", "sum"),
        ).reset_index()

        win_agg = win_agg.merge(
            ie_per_window, on="window", how="left"
        ).merge(
            con_per_window.to_frame(), on="window", how="left"
        ).merge(
            e12_per_window.to_frame(), on="window", how="left"
        )

        win_agg["seed"] = seed
        win_agg["Q_plus_C_total"] = win_agg["Q_total"] + win_agg["C_total"]
        win_agg["Q_plus_C_per_capita"] = win_agg["Q_plus_C_total"] / win_agg["hosted_count"]
        for c in ["gain_in_window", "digestion_dissipation", "n_ingestion",
                  "n_consciousness_events", "e1_e2_dissipation"]:
            if c not in win_agg.columns:
                win_agg[c] = 0
            win_agg[c] = win_agg[c].fillna(0)
        win_rows.append(win_agg)

        # n_core 別: cj は n_core 既結合済
        win_nc_agg = cj.groupby(["window", "n_core"]).agg(
            hosted_count=("cid", "nunique"),
            Q_total=("Q_remaining_at_window_end", "sum"),
            C_total=("C_at_window_end", "sum"),
            n_cognition=("n_cognition_in_window", "sum"),
            n_consciousness_in_w=("n_consciousness_in_window", "sum"),
        ).reset_index()
        win_nc_agg["seed"] = seed
        win_nc_agg["Q_plus_C_total"] = win_nc_agg["Q_total"] + win_nc_agg["C_total"]
        win_nc_agg["Q_plus_C_per_capita"] = (
            win_nc_agg["Q_plus_C_total"] / win_nc_agg["hosted_count"]
        )
        win_nc_rows.append(win_nc_agg)

    df_win = pd.concat(win_rows, ignore_index=True)
    df_win_nc = pd.concat(win_nc_rows, ignore_index=True)
    # 列順整理
    df_win = df_win[[
        "seed", "window", "hosted_count", "Q_total", "C_total",
        "Q_plus_C_total", "Q_plus_C_per_capita",
        "n_cognition", "n_consciousness_in_w",
        "n_consciousness_events", "n_ingestion",
        "gain_in_window", "digestion_dissipation", "e1_e2_dissipation",
    ]]
    df_win_nc = df_win_nc[[
        "seed", "window", "n_core", "hosted_count", "Q_total", "C_total",
        "Q_plus_C_total", "Q_plus_C_per_capita",
        "n_cognition", "n_consciousness_in_w",
    ]]
    return df_win, df_win_nc


# =========================================================================
# 解析 4: 偏在性 — Gini
# =========================================================================
def analysis_4(all_seeds: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for seed_data in all_seeds:
        seed = seed_data["seed"]
        m = seed_data["master"][["cid", "n_core"]].copy()
        cj = seed_data["cj"].merge(m, on="cid", how="left")

        for window, g in cj.groupby("window"):
            row = {
                "seed": seed,
                "window": int(window),
                "hosted_count": g["cid"].nunique(),
                "C_total": float(g["C_at_window_end"].sum()),
                "C_gini": gini(g["C_at_window_end"].values),
                "C_top10_share": top_share(g["C_at_window_end"].values, 0.10),
                "C_top5_share": top_share(g["C_at_window_end"].values, 0.05),
                "C_top1_share": top_share(g["C_at_window_end"].values, 0.01),
            }
            for nc in [2, 3, 4, 5]:
                sub = g[g["n_core"] == nc]["C_at_window_end"].values
                row[f"C_gini_n_core_{nc}"] = gini(sub) if len(sub) > 0 else np.nan
                row[f"hosted_n_core_{nc}"] = len(sub)
            rows.append(row)

    df = pd.DataFrame(rows)

    # ingestion_events の residual_Q_after を ghost 食糧偏在の代理として
    # 各 window の ghost ごとの residual_Q (= ingestion_events 内の最大 residual_Q_after で代理は不適切)
    # → 簡易化: ingestion_events から ghost ごとの residual_Q_before の分布を per window で取る
    # 厳密には ghost ledger が必要。本解析では C 偏在のみを主軸とする。

    # 集計: 全 seed × 全 window の概要 + run 末 (window=69) の集計
    summary_rows = []
    for window, g in df.groupby("window"):
        row = {
            "window": int(window),
            "n_seeds": g["seed"].nunique(),
            "C_gini_mean": float(g["C_gini"].mean()),
            "C_gini_std": float(g["C_gini"].std()),
            "C_top10_share_mean": float(g["C_top10_share"].mean()),
            "C_top5_share_mean": float(g["C_top5_share"].mean()),
            "C_top1_share_mean": float(g["C_top1_share"].mean()),
            "hosted_count_mean": float(g["hosted_count"].mean()),
        }
        for nc in [2, 3, 4, 5]:
            row[f"C_gini_n_core_{nc}_mean"] = float(g[f"C_gini_n_core_{nc}"].mean())
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows).sort_values("window")
    return df, summary


# =========================================================================
# 解析 5: 初回意識発動 step / window
# =========================================================================
def analysis_5(all_seeds: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for seed_data in all_seeds:
        seed = seed_data["seed"]
        m = seed_data["master"]
        bd = seed_data["bd"]
        ie = seed_data["ie"]

        con = bd[bd["decision"] == "consciousness"].sort_values("global_step")
        if len(con) == 0:
            continue

        # 初回 consciousness 記録
        first_con = con.groupby("observer_cid").first()[
            ["window", "step", "global_step", "C_at_decision",
             "Q_at_decision", "contacted_cid"]
        ].rename(columns={
            "window": "first_consciousness_window",
            "step": "first_consciousness_step_in_window",
            "global_step": "first_consciousness_global_step",
            "C_at_decision": "C_at_first_consciousness",
            "Q_at_decision": "Q_at_first_consciousness",
            "contacted_cid": "first_consciousness_contacted_cid",
        })
        first_con.index.name = "cid"
        first_con = first_con.reset_index()

        # 初回発動と摂食の関係: 初回 consciousness と同じ global_step に ingestion_event
        # があったか
        ie_keys = ie[["observer_cid", "global_step", "gain", "received"]].copy()
        ie_keys = ie_keys.rename(columns={"observer_cid": "cid",
                                          "global_step": "first_consciousness_global_step"})
        first_con_ie = first_con.merge(
            ie_keys, on=["cid", "first_consciousness_global_step"], how="left"
        ).rename(columns={"gain": "first_ingestion_gain",
                          "received": "first_ingestion_received"})
        # 重複キー対応 (1 step に複数 ingestion はないはずだが念のため)
        first_con_ie = first_con_ie.drop_duplicates(subset=["seed", "cid"]) \
            if "seed" in first_con_ie.columns else \
            first_con_ie.drop_duplicates(subset=["cid"])

        # cid マスターと結合
        per = m[["seed", "cid", "n_core", "registered_global_step",
                 "death_global_step", "tracking_lifetime",
                 "n_consciousness_decisions"]].merge(
            first_con_ie, on="cid", how="inner"
        )
        per["age_at_first_consciousness"] = (
            per["first_consciousness_global_step"] - per["registered_global_step"]
        )
        per["lifecycle_phase_at_first"] = (
            per["age_at_first_consciousness"]
            / per["tracking_lifetime"].replace(0, np.nan)
        )
        per["steps_first_to_death"] = (
            per["death_global_step"] - per["first_consciousness_global_step"]
        )
        per["first_was_ingestion_success"] = (
            per["first_ingestion_received"].fillna(0) > 0
        )
        rows.append(per)

    df = pd.concat(rows, ignore_index=True)

    # 集計: n_core 別
    summary_rows = []
    for nc, g in df.groupby("n_core"):
        row = {
            "n_core": int(nc),
            "n_first_activated": len(g),
            "age_at_first_mean": float(g["age_at_first_consciousness"].mean()),
            "age_at_first_median": float(g["age_at_first_consciousness"].median()),
            "lifecycle_phase_at_first_mean": float(g["lifecycle_phase_at_first"].mean()),
            "lifecycle_phase_at_first_median": float(g["lifecycle_phase_at_first"].median()),
            "C_at_first_mean": float(g["C_at_first_consciousness"].mean()),
            "C_at_first_median": float(g["C_at_first_consciousness"].median()),
            "Q_at_first_mean": float(g["Q_at_first_consciousness"].mean()),
            "Q_at_first_median": float(g["Q_at_first_consciousness"].median()),
            "steps_first_to_death_mean": float(g["steps_first_to_death"].mean()),
            "steps_first_to_death_median": float(g["steps_first_to_death"].median()),
            "first_ingestion_success_rate": float(g["first_was_ingestion_success"].mean()),
            # 早期 (phase < 0.5) vs 晩期 (>= 0.5) の比率
            "early_first_share": float((g["lifecycle_phase_at_first"] < 0.5).mean()),
        }
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows).sort_values("n_core")
    return df, summary


# =========================================================================
# main
# =========================================================================
def main():
    print("Loading 24 seeds...")
    all_seeds = []
    for seed in SEEDS:
        d = load_seed(seed)
        d["seed"] = seed
        d["master"] = build_cid_master(d, seed)
        all_seeds.append(d)
        print(f"  seed {seed:>2}: {len(d['master'])} cids, "
              f"{len(d['bd'])} balance, {len(d['cj'])} c_traj, "
              f"{len(d['ie'])} ingestion")

    print("\nAnalysis 1: individuality")
    a1, a1s = analysis_1(all_seeds)
    a1.to_csv(OUT / "analysis_1_individuality.csv", index=False)
    a1s.to_csv(OUT / "analysis_1_individuality_summary.csv", index=False)
    print(f"  wrote {len(a1)} cid rows, {len(a1s)} summary rows")

    print("\nAnalysis 2: topology")
    a2, a2s = analysis_2(all_seeds)
    a2.to_csv(OUT / "analysis_2_topology.csv", index=False)
    a2s.to_csv(OUT / "analysis_2_topology_summary.csv", index=False)
    print(f"  wrote {len(a2)} cid rows, {len(a2s)} summary rows")

    print("\nAnalysis 3: temporal dynamics")
    a3, a3nc = analysis_3(all_seeds)
    a3.to_csv(OUT / "analysis_3_temporal_dynamics.csv", index=False)
    a3nc.to_csv(OUT / "analysis_3_temporal_dynamics_n_core.csv", index=False)
    print(f"  wrote {len(a3)} window rows, {len(a3nc)} (window,n_core) rows")

    print("\nAnalysis 4: inequality")
    a4, a4s = analysis_4(all_seeds)
    a4.to_csv(OUT / "analysis_4_inequality.csv", index=False)
    a4s.to_csv(OUT / "analysis_4_inequality_summary.csv", index=False)
    print(f"  wrote {len(a4)} window rows, {len(a4s)} summary rows")

    print("\nAnalysis 5: first consciousness")
    a5, a5s = analysis_5(all_seeds)
    a5.to_csv(OUT / "analysis_5_first_consciousness.csv", index=False)
    a5s.to_csv(OUT / "analysis_5_first_consciousness_summary.csv", index=False)
    print(f"  wrote {len(a5)} cid rows, {len(a5s)} summary rows")

    print("\nDone.")


if __name__ == "__main__":
    main()
