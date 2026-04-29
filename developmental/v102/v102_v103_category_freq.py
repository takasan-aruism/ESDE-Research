"""v10.3 第三項候補カテゴリの事前頻度推定 (N=5000、24 seeds)

既存 E3_contact イベントから「双方向 E3 候補ペア」を再構成し、
各ペアについて Category 3a/3b/3c/4b の第三項候補出現頻度を計算する。

候補ペア定義: 同一 (global_step, link_id) で異なる cid が両側に E3 onset
→ そのペアが将来 v10.3 で双方向 E3 発火する候補

Category:
- 3a 共有 ghost: 両者が食べた ghost 集合の intersection が空でないか
- 3b 共有 phase: 両者の M_c phase_sig が同 bin (π/4 幅 = 8 bins)
- 3c 共有 birth_window: 両者の birth_window が同じか (= 同世代)
- 4b 世代距離: |birth_window_a - birth_window_b| の分布

出力:
  followup/v103_cat_3a_freq.csv  per pair の共有 ghost 数
  followup/v103_cat_3bcd_freq.csv per pair の phase/birth/age delta
  followup/v103_cat_summary.csv  N=5000 全ペアの集計
"""

from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent
OUT = ROOT / "followup"
OUT.mkdir(exist_ok=True)

N_TARGET = 5000
DIRNAME = "diag_v102_main"
SEEDS = list(range(24))

# 共有 phase bin width
PHASE_BIN = np.pi / 4  # 8 bins covering [0, 2π)


def main():
    base = ROOT / DIRNAME
    pairs_rows = []
    summary_per_seed = []

    for seed in SEEDS:
        # 既存 E3 events から候補ペア抽出
        ev = pd.read_csv(base / f"audit/per_event_audit_seed{seed}.csv")
        e3 = ev[ev["v14_event_type"] == "E3_contact"].copy()

        # 同一 (global_step, link_id) で異なる cid → 候補ペア
        groups = e3.groupby(["global_step", "link_id"])["cid"].apply(list)
        candidate_pairs = set()
        for cids in groups:
            cids = sorted(set(cids))
            for i in range(len(cids)):
                for j in range(i + 1, len(cids)):
                    candidate_pairs.add((int(cids[i]), int(cids[j])))

        # per_subject から M_c とライフサイクル情報
        ps = pd.read_csv(base / f"subjects/per_subject_seed{seed}.csv")
        ps = ps.rename(columns={"cognitive_id": "cid"})
        psa = pd.read_csv(base / f"audit/per_subject_audit_seed{seed}.csv")
        psa_keys = psa[["cid", "n_core_member"]]
        m = ps.merge(psa_keys, on="cid", how="left")

        # M_c lookup (phase_sig, birth_window, n_core)
        info = m[["cid", "v11_m_c_phase_sig", "birth_window",
                  "n_core_member"]].set_index("cid")
        info["phase_num"] = pd.to_numeric(
            info["v11_m_c_phase_sig"], errors="coerce")
        info["phase_bin"] = (info["phase_num"] / PHASE_BIN).fillna(-1).astype(int)

        # ingestion 履歴 (3a 用)
        ie = pd.read_csv(base / f"ingestion/ingestion_events_seed{seed}.csv")
        eaten_ghosts = ie.groupby("observer_cid")["ghost_cid"].apply(set).to_dict()

        # ペアごとの第三項候補
        n_pairs = len(candidate_pairs)
        n_3a_yes = 0  # 共有 ghost あり
        n_3b_yes = 0  # 共有 phase bin
        n_3c_yes = 0  # 共有 birth_window
        gen_distances = []

        per_pair = []
        for cid_a, cid_b in candidate_pairs:
            if cid_a not in info.index or cid_b not in info.index:
                continue

            # 3a 共有 ghost
            ga = eaten_ghosts.get(cid_a, set())
            gb = eaten_ghosts.get(cid_b, set())
            n_shared_ghost = len(ga & gb)
            if n_shared_ghost > 0:
                n_3a_yes += 1

            # 3b 共有 phase bin
            pba = info.loc[cid_a, "phase_bin"]
            pbb = info.loc[cid_b, "phase_bin"]
            same_phase = (pba == pbb) and (pba >= 0)
            if same_phase:
                n_3b_yes += 1

            # 3c 共有 birth_window
            bwa = info.loc[cid_a, "birth_window"]
            bwb = info.loc[cid_b, "birth_window"]
            same_birth = (bwa == bwb)
            if same_birth:
                n_3c_yes += 1

            # 4b 世代距離
            gen_dist = abs(bwa - bwb)
            gen_distances.append(gen_dist)

            per_pair.append({
                "seed": seed,
                "cid_a": cid_a,
                "cid_b": cid_b,
                "n_core_a": info.loc[cid_a, "n_core_member"],
                "n_core_b": info.loc[cid_b, "n_core_member"],
                "n_shared_ghost": n_shared_ghost,
                "same_phase_bin": int(same_phase),
                "same_birth_window": int(same_birth),
                "generation_distance": int(gen_dist),
                "phase_bin_a": int(pba),
                "phase_bin_b": int(pbb),
            })

        pairs_rows.extend(per_pair)
        summary_per_seed.append({
            "seed": seed,
            "n_candidate_pairs": n_pairs,
            "n_3a_shared_ghost": n_3a_yes,
            "rate_3a": n_3a_yes / n_pairs if n_pairs else 0,
            "n_3b_same_phase": n_3b_yes,
            "rate_3b": n_3b_yes / n_pairs if n_pairs else 0,
            "n_3c_same_birth": n_3c_yes,
            "rate_3c": n_3c_yes / n_pairs if n_pairs else 0,
            "gen_dist_median": float(np.median(gen_distances))
                                if gen_distances else None,
            "gen_dist_p25": float(np.percentile(gen_distances, 25))
                            if gen_distances else None,
            "gen_dist_p75": float(np.percentile(gen_distances, 75))
                            if gen_distances else None,
        })

    # 集計
    pairs_df = pd.DataFrame(pairs_rows)
    pairs_df.to_csv(OUT / "v103_cat_per_pair.csv", index=False)
    summary_df = pd.DataFrame(summary_per_seed)
    summary_df.to_csv(OUT / "v103_cat_summary_per_seed.csv", index=False)

    # 全 24 seeds の集計
    agg = pd.DataFrame([{
        "N": N_TARGET,
        "n_candidate_pairs_total": int(summary_df["n_candidate_pairs"].sum()),
        "n_candidate_pairs_per_seed_mean":
            float(summary_df["n_candidate_pairs"].mean()),
        "rate_3a_mean": float(summary_df["rate_3a"].mean()),
        "rate_3b_mean": float(summary_df["rate_3b"].mean()),
        "rate_3c_mean": float(summary_df["rate_3c"].mean()),
        "gen_dist_median_overall":
            float(summary_df["gen_dist_median"].mean()),
    }])
    agg.to_csv(OUT / "v103_cat_summary.csv", index=False)

    print("## 候補ペア数 (N=5000、24 seeds 合計)")
    print(f"  total candidate pairs: {agg['n_candidate_pairs_total'].iloc[0]}")
    print(f"  mean per seed: {agg['n_candidate_pairs_per_seed_mean'].iloc[0]:.1f}")
    print()
    print("## 第三項カテゴリの出現率 (per pair)")
    print(f"  3a 共有 ghost: rate = {agg['rate_3a_mean'].iloc[0]:.4f}")
    print(f"  3b 共有 phase bin (π/4): rate = {agg['rate_3b_mean'].iloc[0]:.4f}")
    print(f"  3c 共有 birth_window: rate = {agg['rate_3c_mean'].iloc[0]:.4f}")
    print(f"  4b 世代距離 median: {agg['gen_dist_median_overall'].iloc[0]:.2f} window")
    print()

    # 主役ペアでの抽出
    pairs_df_clean = pairs_df.dropna(subset=["n_core_a", "n_core_b"])
    main_pool = pairs_df_clean[
        ((pairs_df_clean["n_core_a"] >= 4) & (pairs_df_clean["n_core_b"] >= 4))
    ]
    print(f"## 主役ペア (両者 n_core >= 4): {len(main_pool)} 件")
    if len(main_pool) > 0:
        print(f"  3a rate: {main_pool['n_shared_ghost'].gt(0).mean():.4f}")
        print(f"  3b rate: {main_pool['same_phase_bin'].mean():.4f}")
        print(f"  3c rate: {main_pool['same_birth_window'].mean():.4f}")
        print(f"  gen_dist median: {main_pool['generation_distance'].median():.1f}")

    # 共起 (複数カテゴリ同時)
    pairs_df_clean["n_categories"] = (
        pairs_df_clean["n_shared_ghost"].gt(0).astype(int)
        + pairs_df_clean["same_phase_bin"].astype(int)
        + pairs_df_clean["same_birth_window"].astype(int)
    )
    print()
    print("## 複数カテゴリ同時 (3a/3b/3c のうちいくつ該当か):")
    print(pairs_df_clean["n_categories"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()
