#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# v1303g Step B — 注意センター Phase2前段: Now-event と Archive を照合し
#   Comparator 4分類の候補軸が dry に組めるかを見る（改善B'・後処理のみ・判定なし #12）
#
# 改善B'(Step A発見→Taka/GPT判断): literal定義は degenerate(Familiar-Stable92%/Novel-Random0%)。
#  (1)near_archive除外(archiveが寿命48%覆うbroadさで0.996飽和=判別無効・但しArchive概念は将来分解で戻す)
#  (2)Stable=θ帯 theta_in_stability_band(now θ>=cid安定帯閾値・Atomは12%稀ゆえ補助降格)
#  (3)pulseは別event_class now_pulse_event に分離(捨てず混ぜず=segregate・頻度で際立ち否定しない)
#  (4)4分類は構造的イベント限定(birth/death/α/β/c_conversion)
# Web Claude独立検証で4象限分離確認(Fam-St25.5/Fam-Un42.7/Nov-Co18.1/Nov-Ra13.7・誕生Novel率1.0)。
#
# 規律: 読=v1303f統合+ledger READ-ONLY/書=outputs/v1303g のみ・物理非書込(B型)。
#  照合列は合成しない(#11・別列)・4分類は分類であって合成でない・dryで確定分類しない。
#  閾値(near_window/θ帯)は研究者選択ゆえタグ明示(#CW7・将来内部化余地)。cid個別/n_core/B_Gen別(D)。
#  L型: 「Comparator成立/4分類できた/自律注意」と言わない。Atom意味解釈しない。
#  #12: (a)/(b)判定せず観察事実のみ。結果を確定しにいかない・前段で止める。検証ゲートで自己確認。
# ─────────────────────────────────────────────────────────────────────────────
import numpy as np
import pandas as pd
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CEN = REPO / "unified" / "v1303" / "outputs" / "v1303f" / "v1303f_attention_center_seed0.parquet"
LEDGER = REPO / "unified" / "v1303" / "outputs" / "v1303_ledger_seed0.parquet"
SUBJ = REPO / "developmental" / "v105" / "diag_v105_main_v2" / "subjects" / "per_subject_seed0.csv"
OUT = REPO / "unified" / "v1303" / "outputs" / "v1303g"
OUT.mkdir(parents=True, exist_ok=True)

NEAR_WINDOW = 500           # 研究者選択(#CW7) 近傍Archive判定窓(記録列・Familiarには使わない)
STRUCTURAL = ["cid_birth", "cid_death", "alpha_formation", "beta_formation", "c_conversion"]


def build():
    cen = pd.read_parquet(CEN)
    led = pd.read_parquet(LEDGER).sort_values(["cid", "t"])
    subj = pd.read_csv(SUBJ)
    bg = pd.to_numeric(subj.set_index("cognitive_id")["v11_b_gen"], errors="coerce").to_dict()

    now = cen[cen.event_class == "now_event"].copy()
    arch = cen[cen.event_class == "archive_persistence"]

    # event_class 再構成: pulse を別系統に segregate(改善B'-3)
    now["event_class"] = np.where(now["event_type"] == "pulse",
                                  "now_pulse_event", "now_structural_event")

    # cid の安定帯閾値(v1303e robust-range threshold)・archive時点集合
    thr = arch.groupby("cid")["theta_threshold"].first().to_dict()
    arch_t = {c: np.array(sorted(g.t.values)) for c, g in arch.groupby("cid")}

    # ledger の atom変化(event時点の rank_1 が前step10と違うか・補助列)
    led["atom_prev"] = led.groupby("cid")["rank_1_atom"].shift(1)
    led["atom_changed"] = (led["rank_1_atom"] != led["atom_prev"]) & led["atom_prev"].notna()
    ac = led.set_index(["cid", "t"])["atom_changed"].to_dict()

    # 照合5列(別列・合成しない)
    now = now.sort_values(["cid", "event_type", "t"])
    now["past_same"] = now.groupby(["cid", "event_type"]).cumcount() > 0   # 過去同種(再発)

    def near_arch(c, t):
        a = arch_t.get(c)
        return bool(a is not None and np.any(np.abs(a - t) <= NEAR_WINDOW))
    now["near_archive"] = [near_arch(c, t) for c, t in zip(now.cid, now.t)]  # 記録列(Familiarに使わない)

    now["theta_in_stability_band"] = [
        (thr.get(c) is not None) and (not pd.isna(thr.get(c, np.nan)))
        and (not pd.isna(th)) and (th >= thr.get(c, np.inf))
        for c, th in zip(now.cid, now.theta_resultant_length)]
    now["atom_changed"] = [ac.get((int(c), int(t)), np.nan) for c, t in zip(now.cid, now.t)]  # 補助列
    now["bgen"] = now["cid"].map(bg)
    now["bgen_stratum"] = np.where(now["bgen"].isna(), "unformed",
                                   np.where(now["bgen"] >= np.nanmedian([v for v in bg.values() if not pd.isna(v)]),
                                            "high", "low"))

    # 4分類候補軸(改善B'・dry・確定分類しない)= 構造的イベントのみ
    is_struct = now["event_class"] == "now_structural_event"
    now["familiar_flag"] = np.where(is_struct, now["past_same"], pd.NA)          # near_archive除外
    now["stable_flag"] = np.where(is_struct, now["theta_in_stability_band"], pd.NA)

    def quad(fam, sta):
        if pd.isna(fam):
            return None
        f = "Familiar" if fam else "Novel"
        if fam:
            s = "Stable" if sta else "Unstable"
        else:
            s = "Coherent" if sta else "Random"   # Novel側はCoherent/Random
        return f"{f}-{s}"
    now["dry_quadrant_candidate"] = [quad(f, s) for f, s in zip(now["familiar_flag"], now["stable_flag"])]
    now["classification_threshold_tag"] = "researcher_chosen:familiar=past_same,stable=theta>=cid_robustrange_v1303e,near_window=500"

    out = pd.concat([now, arch.assign(
        familiar_flag=pd.NA, stable_flag=pd.NA, dry_quadrant_candidate=None,
        past_same=pd.NA, near_archive=pd.NA, theta_in_stability_band=pd.NA,
        atom_changed=pd.NA, bgen=arch["cid"].map(bg))], ignore_index=True)
    return out, now


def verify_gates(now):
    g = {}
    st = now[now.event_class == "now_structural_event"]
    q = st["dry_quadrant_candidate"].value_counts(normalize=True)
    g["gate1_all4_quadrants_present"] = bool(set(["Familiar-Stable", "Familiar-Unstable",
                                                  "Novel-Coherent", "Novel-Random"]) <= set(q.index))
    g["gate2_not_degenerate(max<0.85)"] = bool(q.max() < 0.85)
    # 誕生は Novel に素直か(past_same=False ゆえ)
    birth = st[st.event_type == "cid_birth"]
    g["gate3_birth_is_novel"] = bool((birth["dry_quadrant_candidate"].str.startswith("Novel")).mean() > 0.95)
    # pulse は別event_classで4分類対象外
    g["gate4_pulse_segregated"] = bool((now[now.event_type == "pulse"]["event_class"] == "now_pulse_event").all()
                                       and now[now.event_type == "pulse"]["dry_quadrant_candidate"].isna().all())
    # near_archive は記録列だが Familiar には使っていない(familiar=past_same のみ)
    g["gate5_familiar_is_past_same_only"] = bool((st["familiar_flag"].astype(bool) == st["past_same"].astype(bool)).all())
    # 合成スコア列なし(#11)
    g["gate6_no_composite"] = bool(not any("composite" in c or "score" in c.lower() for c in now.columns))
    # 照合列の欠損(構造的イベントで past_same/theta_band が付くか)
    g["gate7_collation_cols_present"] = bool(st["past_same"].notna().all() and st["theta_in_stability_band"].notna().all())
    return g


def main():
    out, now = build()
    out.to_parquet(OUT / "v1303g_comparator_dry_seed0.parquet", index=False)
    gates = verify_gates(now)
    st = now[now.event_class == "now_structural_event"]

    print("=== v1303g 注意センター Phase2前段: Comparator 4分類 dry (改善B'・判定なし #12) ===")
    print(f"event_class: now_structural_event={int((now.event_class=='now_structural_event').sum())} "
          f"now_pulse_event={int((now.event_class=='now_pulse_event').sum())} (pulse別保持)")
    print(f"\n--- 4分類 dry候補 分布(構造的イベント{len(st)}件・確定分類しない) ---")
    q = st["dry_quadrant_candidate"].value_counts()
    for lab in ["Familiar-Stable", "Familiar-Unstable", "Novel-Coherent", "Novel-Random"]:
        n = int(q.get(lab, 0))
        print(f"  {lab:18s}: {n:5d} ({n/len(st)*100:.1f}%)")
    print(f"\n--- trigger別 4象限(構造的) ---")
    for trig in STRUCTURAL:
        g = st[st.event_type == trig]
        if len(g):
            qd = g["dry_quadrant_candidate"].value_counts(normalize=True)
            top = qd.index[0]
            print(f"  {trig:16s}: n={len(g):4d} | Novel率={(g['dry_quadrant_candidate'].str.startswith('Novel')).mean():.2f} "
                  f"Stable率={g['stable_flag'].astype(float).mean():.2f}")
    print(f"\n--- n_core別 Novel率 / B_Gen層別 ---")
    for nc in [2, 3, 4, 5]:
        s = st[st.n_core == nc]
        if len(s):
            print(f"  n_core={nc}: n={len(s):4d} Novel率={(s['dry_quadrant_candidate'].str.startswith('Novel')).mean():.2f} "
                  f"Stable率={s['stable_flag'].astype(float).mean():.2f}")
    for strat in ["low", "high"]:
        s = st[st.bgen_stratum == strat]
        if len(s):
            print(f"  B_Gen={strat}(n={len(s)}): Novel率={(s['dry_quadrant_candidate'].str.startswith('Novel')).mean():.2f}")
    print(f"\n--- 補助列 atom_changed(Stable判別に使わず): 構造的イベントでの変化率={st['atom_changed'].astype(float).mean():.3f} ---")
    print("\n--- 検証ゲート(全PASSで完了) ---")
    for k, v in gates.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}: {v}")
    print(f"\n  ★ 全ゲート PASS = {all(gates.values())}")
    print(f"\n出力: {OUT}/v1303g_comparator_dry_seed0.parquet")


if __name__ == "__main__":
    main()
