#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# v1303f Step B2 — 注意センター統合 Phase1: Now-event(canonical再構成) と
#   Archive-persistence(v1303e) を event_class 分離で1体系の統合レコードに並べる
#   （後処理のみ・物理非書込・判定なし #12・合成しない・Comparator土台のみ）
#
# 統合方針(Taka確定): 現在(Now/Archive/Comparator 3系分離)を主・過去(v1114)をspecとして統合。
#  - Now系  = v1114型6トリガー(canonical再構成・t付き・228宇宙) + (将来)v1303e q95瞬間
#  - Archive系 = v1303e persistence(stable-above-baseline 持続区間)
#  - Comparator = v1114のEWMA+zは前駆体(簡易novelty)。Phase1は監査列のみ・4分類しない。
# 規律: 読=canonicalログ/v1303e/B1出力 READ-ONLY・書=outputs/v1303f のみ・物理非書込(B型)。
#  合成しない(#11)・n_core層化/cid個別/時間軸・判定数値は監査用rawで残すが判定に使わない(GPT)。
#  familiarity は canonical(fam_edges 最終スナップ・37/228cid)から限界タグ付きで(判断3)。
#  persistence は stable-above-baseline と乾いた命名(GPT6)。検証ゲートで自己確認してから完了。
# 言わない: 「注意センター統合された/Comparator成立/CIDが自律注意/Atom理解開始」。
#  Phase1は「過去と現在の際立ちを同じCID宇宙で1体系に event_class 分けて並べた」まで。
# ─────────────────────────────────────────────────────────────────────────────
import re
import numpy as np
import pandas as pd
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DIAG = REPO / "developmental" / "v105" / "diag_v105_main_v2"
LEDGER = REPO / "unified" / "v1303" / "outputs" / "v1303_ledger_seed0.parquet"
NOWEV = REPO / "unified" / "v1303" / "outputs" / "v1303f" / "v1303f_now_events_seed0.parquet"
PERSIST = REPO / "unified" / "v1303" / "outputs" / "v1303e" / "v1303e_persistence_salience_seed0.parquet"
OUT = REPO / "unified" / "v1303" / "outputs" / "v1303f"
SEED = 0
WIN = 500  # EWMA+z の集計窓(tracking step)


def familiarity_table():
    """canonical fam_edges(最終スナップ・静的)から per-cid familiarity(37/228cid・限界タグ)。"""
    fe = pd.read_csv(DIAG / "network" / f"fam_edges_seed{SEED}.csv")
    subj = pd.read_csv(DIAG / "subjects" / f"per_subject_seed{SEED}.csv")
    nc = pd.to_numeric(subj.set_index("cognitive_id")["v11_m_c_n_core"], errors="coerce").to_dict()
    rows = []
    for cid, g in fe.groupby("from"):
        partners_nc = [nc.get(int(t)) for t in g["to"] if not pd.isna(nc.get(int(t)))]
        rows.append(dict(cid=int(cid), familiarity_n=int(len(g)),
                         familiarity_partner_mean_ncore=float(np.mean(partners_nc)) if partners_nc else np.nan,
                         familiarity_status="canonical_final_snapshot"))
    return pd.DataFrame(rows)


def ewma_z(now):
    """trigger別 window集計で EWMA+z(Comparator前駆体・監査列)。判定に使わない。"""
    now = now.copy()
    now["window"] = (now["t"] // WIN).astype(int)
    out = []
    for trig, g in now.groupby("trigger"):
        cnt = g.groupby("window").size()
        wins = range(int(now["window"].min()), int(now["window"].max()) + 1)
        cnt = cnt.reindex(wins, fill_value=0).astype(float)
        ewma = cnt.ewm(alpha=0.3, adjust=False).mean()
        dev = cnt - ewma
        sd = dev.std() + 1e-9
        z = dev / sd
        for w in wins:
            out.append((trig, w, float(cnt[w]), float(ewma[w]), float(z[w])))
    return pd.DataFrame(out, columns=["trigger", "window", "trigger_count_in_window",
                                      "trigger_rate_ewma", "z_like_deviation"])


def build():
    led = pd.read_parquet(LEDGER).sort_values(["cid", "t"])
    led_cids = set(int(c) for c in led["cid"].unique())
    now = pd.read_parquet(NOWEV)
    fam = familiarity_table()
    zt = ewma_z(now)
    now["window"] = (now["t"] // WIN).astype(int)

    # point を ledger から付与。【自己チェックで修正】death は host_lost_step=ghost行(theta NaN)に
    # 当たるため、hosted_available のみに絞り direction="backward"(その時点 or 直前の最後の hosted
    # 状態)で結合する。これで pulse等=その hosted行・death=死ぬ直前の最後の hosted状態 を point に。
    # point_source_t で point の出所 t を透明化(death は event_t と異なる=最後のhosted t)。
    cols = ["cid", "t", "n_core", "core_node_theta_resultant_length", "rank_1_atom",
            "rank_1_sim", "C_at_window_end", "Q_remaining_at_window_end", "phys_core_status"]
    Lh = led[led["phys_core_status"] == "hosted_available"][cols].rename(
        columns={"core_node_theta_resultant_length": "theta_resultant_length",
                 "C_at_window_end": "C", "Q_remaining_at_window_end": "Q"})
    Lh["point_source_t"] = Lh["t"]
    now = now.sort_values("t")
    merged = pd.merge_asof(now, Lh.sort_values("t"), on="t", by="cid", direction="backward")
    merged = merged.merge(zt, on=["trigger", "window"], how="left")
    merged = merged.merge(fam, on="cid", how="left")
    merged["familiarity_status"] = merged["familiarity_status"].fillna("missing_no_fam_edge")

    now_rows = pd.DataFrame(dict(
        seed=SEED, cid=merged["cid"], t=merged["t"],
        event_class="now_event", event_type=merged["trigger"],
        event_source="reconstructed_from_canonical_diag_v105_main_v2",
        n_core=merged["n_core"], theta_resultant_length=merged["theta_resultant_length"],
        rank_1_atom=merged["rank_1_atom"], rank_1_sim=merged["rank_1_sim"],
        C=merged["C"], Q=merged["Q"], phys_core_status=merged["phys_core_status"],
        point_source_t=merged["point_source_t"],  # point の出所 t(death は event_t と異なる=最後のhosted)
        point_lag=merged["t"] - merged["point_source_t"],
        familiarity_n=merged["familiarity_n"],
        familiarity_partner_mean_ncore=merged["familiarity_partner_mean_ncore"],
        familiarity_status=merged["familiarity_status"],
        # Comparator前駆体(監査列・判定に使わない)
        trigger_count_in_window=merged["trigger_count_in_window"],
        trigger_rate_ewma=merged["trigger_rate_ewma"],
        z_like_deviation=merged["z_like_deviation"],
        # Archive固有列は null
        event_segment_id=None, segment_length=np.nan, theta_threshold=np.nan,
        comparator_class=None,  # Phase2 土台(本格判定しない)
    ))

    # Archive-persistence (v1303e) を同じ schema に
    ps = pd.read_parquet(PERSIST)
    fam_idx = fam.set_index("cid")
    arch_rows = pd.DataFrame(dict(
        seed=SEED, cid=ps["cid"], t=ps["t"],
        event_class="archive_persistence", event_type=ps["event_type"],
        event_source=ps["event_source"],
        n_core=ps["n_core"], theta_resultant_length=ps["theta_resultant_length"],
        rank_1_atom=ps["rank_1_atom"], rank_1_sim=ps["rank_1_sim"],
        C=ps["C"], Q=ps["Q"], phys_core_status=ps["phys_core_status"],
        point_source_t=ps["t"], point_lag=0,  # archive は自行=exact
        familiarity_n=ps["cid"].map(fam_idx["familiarity_n"]),
        familiarity_partner_mean_ncore=ps["cid"].map(fam_idx["familiarity_partner_mean_ncore"]),
        familiarity_status=ps["cid"].map(fam_idx["familiarity_status"]).fillna("missing_no_fam_edge"),
        trigger_count_in_window=np.nan, trigger_rate_ewma=np.nan, z_like_deviation=np.nan,
        event_segment_id=ps["event_segment_id"], segment_length=ps["segment_length"],
        theta_threshold=ps["theta_threshold"], comparator_class=None,
    ))

    cen = pd.concat([now_rows, arch_rows], ignore_index=True)
    return cen, led_cids, fam


def verify_gates(cen, led_cids, fam):
    g = {}
    g["gate1_all_in_universe"] = bool(set(int(c) for c in cen["cid"].unique()) <= led_cids)
    g["gate2_event_class_two"] = sorted(cen["event_class"].unique()) == ["archive_persistence", "now_event"]
    nw = cen[cen.event_class == "now_event"]
    g["gate3_now_point_joined"] = bool(nw["n_core"].notna().mean() > 0.98)
    g["gate3b_now_theta_joined"] = bool(nw["theta_resultant_length"].notna().mean() > 0.98)  # death も最後のhostedで付く
    g["gate4_no_composite_col"] = bool(not any(k in cen.columns for k in ["composite", "combined_score", "fused"]))
    g["gate5_raw_audit_present"] = bool({"z_like_deviation", "trigger_rate_ewma"} <= set(cen.columns))
    g["gate6_comparator_scaffold_only"] = bool(cen["comparator_class"].isna().all())  # 4分類しない
    g["gate7_familiarity_tagged"] = bool(set(cen["familiarity_status"].dropna().unique())
                                         <= {"canonical_final_snapshot", "missing_no_fam_edge"})
    return g


def main():
    cen, led_cids, fam = build()
    cen.to_parquet(OUT / "v1303f_attention_center_seed0.parquet", index=False)
    gates = verify_gates(cen, led_cids, fam)

    print("=== v1303f Step B2: 注意センター統合 Phase1 (Now/Archive event_class分離・判定なし) ===")
    print(f"統合レコード={len(cen)} | cid={cen['cid'].nunique()}(228宇宙)")
    print(f"  now_event={int((cen.event_class=='now_event').sum())} "
          f"archive_persistence={int((cen.event_class=='archive_persistence').sum())}")
    print("\n--- now_event: trigger別件数(n_core別cid) ---")
    nw = cen[cen.event_class == "now_event"]
    for trig, g in nw.groupby("event_type"):
        print(f"  {trig:16s}: {len(g):5d} | cid={g['cid'].nunique()} | θ付与={g['theta_resultant_length'].notna().mean():.2f}")
    print(f"\n--- familiarity(canonical fam_edges・限界) ---")
    print(f"  familiarity あり cid={int((fam.shape[0]))}/228 (canonical_final_snapshot) 残りmissing")
    print(f"  統合レコードで familiarity_n notna={cen['familiarity_n'].notna().mean():.3f}")
    print(f"\n--- Comparator前駆体(EWMA+z 監査列・判定に使わない) z_like_deviation 分布 ---")
    print(f"  now_event z med={nw['z_like_deviation'].median():.2f} 範囲[{nw['z_like_deviation'].min():.1f},{nw['z_like_deviation'].max():.1f}]")
    print(f"  comparator_class: 全null(Phase2土台のみ)={cen['comparator_class'].isna().all()}")
    print("\n--- 検証ゲート(全PASSで Phase1完了) ---")
    for k, v in gates.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}: {v}")
    print(f"\n  ★ 全ゲート PASS = {all(gates.values())}")
    print(f"\n出力: {OUT}/v1303f_attention_center_seed0.parquet")


if __name__ == "__main__":
    main()
