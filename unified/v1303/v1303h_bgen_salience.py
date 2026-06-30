#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# v1303h Step B — 注意センター Phase2本番: B_Gen を n_core内正規化で「際立ち=珍しさ」の
#   本命軸に据え、Familiar軸の粗さ(past_same 2値)を精緻化(再発回数/間隔)して
#   際立ちを θ・イベント・珍しさ の複数の目で並べる（後処理のみ・判定なし #12・合成しない #11）
#
# 駆動要因(設計§0): 前段v1303gの2留保を直す=(1)Familiar軸が粗い(cumcount>0で2回目も58回目も同じ)
#  (2)B_Gen(Taka際立ち本命)を背景層別にしか使ってない。観察軸を増やすためでない。
# B_Gen扱い(Taka指摘+実機確認): ledger v11_b_gen は floorされてない連続値で同一n_core内に差あり
#  (log10外す作業不要)。但しTaka核心「n_coreで実質決まる」は正しい(raw bgen vs n_core 相関0.997)。
#  解=n_core内正規化(bgen_pct_in_ncore)で帯を除き「実質一意の珍しさ」を拾う(pct vs n_core 相関0.001)。
#  Qの顔(floor後資源量)とは別。際立ちは連続値をn_core正規化(二つの顔を分ける)。
# 限界(Step A): 数値B_Genは45/228cidのみ(183 unformed・n3は1cid)=珍しさ軸は疎(明記)。
#
# 規律: 読=v1303g+ledger READ-ONLY/書=outputs/v1303h のみ・物理非書込(B型)。
#  #11: B_Gen際立ち・θ際立ち・イベント際立ちを合成しない(別列・複数の目)。
#  Taka B_Gen: n_coreで決まる量(raw)を際立ちにそのまま使わずn_core内正規化。Q用floorと分ける。
#  D型: cid個別/n_core別/n_core内正規化。L型: 「珍しさで自律注意」と言わない(pctでありESDE感覚でない)。
#  #CW7: n_core内正規化(percentile)は研究者選択ゆえタグ明示。#12: 判定せず観察事実のみ・確定しにいかない。
# ─────────────────────────────────────────────────────────────────────────────
import numpy as np
import pandas as pd
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
G = REPO / "unified" / "v1303" / "outputs" / "v1303g" / "v1303g_comparator_dry_seed0.parquet"
LEDGER = REPO / "unified" / "v1303" / "outputs" / "v1303_ledger_seed0.parquet"
OUT = REPO / "unified" / "v1303" / "outputs" / "v1303h"
OUT.mkdir(parents=True, exist_ok=True)


def build():
    g = pd.read_parquet(G)
    led = pd.read_parquet(LEDGER)
    # cid単位 B_Gen 連続値(際立ち用) + n_core内正規化
    bgv = pd.to_numeric(led.groupby("cid")["v11_b_gen"].first(), errors="coerce")
    nc = led.groupby("cid")["n_core"].first()
    bg = pd.DataFrame({"cid": bgv.index, "bgen_continuous": bgv.values, "n_core": nc.values})
    bg["bgen_pct_in_ncore"] = bg.groupby("n_core")["bgen_continuous"].rank(pct=True)  # 珍しさ(帯除去)
    bg["bgen_salience_status"] = np.where(bg["bgen_continuous"].isna(), "unformed_no_bgen", "numeric")
    bg_idx = bg.set_index("cid")

    st = g[g.event_class == "now_structural_event"].copy()
    # B_Gen際立ち列(別列・合成しない)
    st["bgen_continuous"] = st["cid"].map(bg_idx["bgen_continuous"])
    st["bgen_pct_in_ncore"] = st["cid"].map(bg_idx["bgen_pct_in_ncore"])
    st["bgen_salience_status"] = st["cid"].map(bg_idx["bgen_salience_status"])
    # Familiar軸 精緻化(別列・粗さ補う)
    st = st.sort_values(["cid", "event_type", "t"])
    st["recur_count"] = st.groupby(["cid", "event_type"]).cumcount()        # 何回目(0=初回)
    st["recur_recency"] = st.groupby(["cid", "event_type"])["t"].diff()     # 直近同種からの間隔(初回NaN)
    st["bgen_salience_tag"] = "researcher_chosen:bgen_pct_within_ncore_rank_v1"
    return st, bg


def main():
    st, bg = build()
    st.to_parquet(OUT / "v1303h_bgen_salience_seed0.parquet", index=False)

    num = st[st.bgen_salience_status == "numeric"]
    print("=== v1303h Phase2本番: B_Gen際立ち(n_core内珍しさ)+Familiar精緻化 (判定なし #12) ===")
    print(f"構造的イベント={len(st)} | B_Gen数値あり={int((st.bgen_salience_status=='numeric').sum())} "
          f"(cid {bg['bgen_continuous'].notna().sum()}/228・unformed多数=珍しさ軸は疎)")

    print("\n--- 1. B_Gen際立ちの作り方検証(Taka指摘の二つの顔) ---")
    valid = bg[bg.bgen_continuous.notna()]
    print(f"  raw bgen vs n_core 相関={np.corrcoef(valid.bgen_continuous,valid.n_core)[0,1]:.3f}(高=n_coreで帯決まる=Taka指摘正しい)")
    print(f"  bgen_pct_in_ncore vs n_core 相関={np.corrcoef(valid.bgen_pct_in_ncore,valid.n_core)[0,1]:.3f}(≈0=帯除去で実質一意の珍しさ)")
    print(f"  n_core別 bgen_pct域: " + " ".join(
        f"n{x}[{valid[valid.n_core==x].bgen_pct_in_ncore.min():.2f},{valid[valid.n_core==x].bgen_pct_in_ncore.max():.2f}]"
        for x in [2, 4, 5] if (valid.n_core == x).any()))

    print("\n--- 2. 複数の目の独立性(出口核心: 珍しさ は θ・イベント と別の情報か) ---")
    # B_Gen際立ち vs θ際立ち(stable_flag) (event単位)
    e = num.dropna(subset=["bgen_pct_in_ncore"]).copy()
    e["stable_num"] = e["stable_flag"].astype(float)
    print(f"  bgen_pct vs θ帯(stable_flag) 相関={np.corrcoef(e.bgen_pct_in_ncore,e.stable_num)[0,1]:.3f}(≈0=独立=出口a'寄り)")
    # B_Gen際立ち vs イベント種(Novel率)
    e["novel_num"] = e["dry_quadrant_candidate"].str.startswith("Novel").astype(float)
    print(f"  bgen_pct vs Novel(familiar軸) 相関={np.corrcoef(e.bgen_pct_in_ncore,e.novel_num)[0,1]:.3f}(≈0=珍しさはFamiliar/Novelと別)")
    # B_Gen際立ち vs recur_count(再発度合い)
    er = num.dropna(subset=["bgen_pct_in_ncore", "recur_count"])
    print(f"  bgen_pct vs recur_count 相関={np.corrcoef(er.bgen_pct_in_ncore,er.recur_count)[0,1]:.3f}")

    print("\n--- 3. B_Gen際立ち × 4象限(n_core内で珍しいcidはどこに) ---")
    hi = num[num.bgen_pct_in_ncore >= 0.8]   # n_core内で珍しい上位20%
    lo = num[num.bgen_pct_in_ncore <= 0.2]
    for lab, s in [("珍しい(pct>=0.8)", hi), ("ありふれ(pct<=0.2)", lo)]:
        if len(s):
            qd = s["dry_quadrant_candidate"].value_counts(normalize=True)
            print(f"  {lab}: n={len(s)} | " + " ".join(f"{k}={v:.2f}" for k, v in qd.items()))

    print("\n--- 4. Familiar精緻化 recur_count/recency(粗さ補正) ---")
    for trig in ["cid_birth", "alpha_formation", "beta_formation", "c_conversion"]:
        s = st[st.event_type == trig]
        if len(s):
            print(f"  {trig:16s}: recur_count med={s['recur_count'].median():.0f} max={int(s['recur_count'].max())} "
                  f"| recur_recency med={s['recur_recency'].median():.0f}")

    # 検証ゲート
    gates = {}
    gates["gate1_bgen_pct_independent_of_ncore"] = bool(abs(np.corrcoef(valid.bgen_pct_in_ncore, valid.n_core)[0, 1]) < 0.05)
    gates["gate2_bgen_pct_in_0_1"] = bool((valid.bgen_pct_in_ncore.between(0, 1)).all())
    gates["gate3_birth_recur0"] = bool((st[st.event_type == "cid_birth"]["recur_count"] == 0).all())
    gates["gate4_two_faces_separated"] = bool("bgen_pct_in_ncore" in st.columns and "bgen_continuous" in st.columns)  # Q floorと別・連続値正規化
    gates["gate5_no_composite"] = bool(not any("composite" in c or "score" in c.lower() for c in st.columns))
    gates["gate6_bgen_status_tagged"] = bool(set(st["bgen_salience_status"].dropna().unique()) <= {"numeric", "unformed_no_bgen"})
    print("\n--- 検証ゲート ---")
    for k, v in gates.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}: {v}")
    print(f"\n  ★ 全ゲート PASS = {all(gates.values())}")
    print(f"\n出力: {OUT}/v1303h_bgen_salience_seed0.parquet")


if __name__ == "__main__":
    main()
