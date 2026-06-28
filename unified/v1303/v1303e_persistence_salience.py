#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# v1303e Step B — θ高同期手本の閾値を「5%固定(q95)」から「persistence(内部履歴由来・
#   θ中央値以上が連続3点持続=age_r型)」に置き換え、salience の像が変わるかを read-only 観察
#   （後処理のみ・再走/write-back なし・seed0・判定なし #12・判断A=全面適用 persistence一本）
#
# 規律宣言(Code A):
#  読: v1303a ledger + v1303c event_ledger(q95版 salience・比較用) READ-ONLY。
#  書: unified/v1303/outputs/v1303e/ のみ。write-back しない(B型)。
#  persistence型: Frozen の persistence-based birth(age_r≥τ, v104:1741/2367)と同型=
#   「状態が連続して持続した時間」で閾値を立てる。θに当てる=θがcid中央値以上で連続3点(=30step)。
#  A型/#CW7: N=3・median は研究者選択ゆえ event_source に手本タグ(離脱ポインタ・将来endogenous置換可)。
#   閾値内部化は多様性拡張の意図(神の手を厳格にしない・Taka方針)。
#  L型: persistenceを「離脱」「優れている」と言わない=θ系の言い換え(閾値内部化)であって
#   非θ系=言語の離脱ではないことを明記。準同義反復の側面を隠さない。
#  D型: cid内中央値基準(cid局所主語)・全n_coreで機能するmedian基準を採用(q75はn2空振り)。
#  #12: (a)/(b)判定せず観察事実のみ。結果を確定しにいかない。応用可否はTaka。
#  説明可能性ルーブリック準拠・実装後 verify_rubric() で自己検証。
# ─────────────────────────────────────────────────────────────────────────────
import numpy as np
import pandas as pd
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LEDGER = REPO / "unified" / "v1303" / "outputs" / "v1303_ledger_seed0.parquet"
EVENTC = REPO / "unified" / "v1303" / "outputs" / "v1303c" / "v1303c_event_ledger_seed0.parquet"
OUT = REPO / "unified" / "v1303" / "outputs" / "v1303e"
OUT.mkdir(parents=True, exist_ok=True)

SEED = 0
N_PERSIST = 3          # 連続N点(=30step)以上の持続を salience とする(age_r≥τ 応用・研究者選択ゆえ手本)
CONTEXT_WINDOW = "pm1_step10"

EXPLAIN = {
    "persistence salience の定義": ("HIGH",
        "θ_resultant が cid内中央値以上の状態が連続N_PERSIST(=3)点続いた区間に属する時点。runs_mask_ge で機械抽出"),
    "event_type": ("HIGH", "salience_template_theta_high_persistence(全行同一)"),
    "event_source/template_version": ("HIGH",
        "researcher_template:theta_high_persistence_median_N3_v1(手本タグ=離脱ポインタ・N3/medianは研究者選択を明示)"),
    "event_segment_id": ("HIGH", "同一cid内で連続持続区間ごとの通し番号 ps_{cid}_{k}"),
    "segment_length": ("HIGH", "その持続区間の長さ(step10点数)。q95(瞬間ピーク)との像の違いの指標"),
    "theta_cid_percentile": ("HIGH", "情報列: その行のθのcid内percentile rank(0-1)"),
    "比較(jaccard_q95)": ("HIGH", "cid単位で persistence時点集合 と v1303c q95時点集合 の Jaccard(低い=違う像)"),
    "ledger列(seed/cid/t/n_core/θ/rank_1/C/Q/phys_core_status)": ("HIGH", "v1303a ledger 直接コピー(v1303c salience と同列構成で比較可能)"),
}


def runs_mask_ge(cond, n_min):
    """cond(bool)の連続Trueが長さ>=n_min の区間に属する index集合(persistence型)。segment id も返す。"""
    idx = {}
    n = len(cond); i = 0; seg = 0
    while i < n:
        if not cond[i]:
            i += 1; continue
        j = i
        while j < n and cond[j]:
            j += 1
        if j - i >= n_min:
            seg += 1
            for k in range(i, j):
                idx[k] = (seg, j - i)  # idx -> (segment番号, 区間長)
        i = j
    return idx


def build():
    df = pd.read_parquet(LEDGER)
    h = df[df["phys_core_status"].eq("hosted_available")].copy().sort_values(["cid", "t"]).reset_index(drop=True)
    h["theta_cid_percentile"] = h.groupby("cid")["core_node_theta_resultant_length"].rank(pct=True)

    rows = []
    persist_idx_by_cid = {}   # cid -> set(t)（q95比較用）
    for cid, g in h.groupby("cid"):
        g = g.sort_values("t").reset_index(drop=True)
        theta = g["core_node_theta_resultant_length"].values.astype(float)
        med = np.median(theta)
        seg_map = runs_mask_ge(theta >= med, N_PERSIST)
        persist_idx_by_cid[int(cid)] = set(g["t"].iloc[list(seg_map.keys())].tolist())
        for k, (seg, seglen) in seg_map.items():
            r = g.iloc[k]
            t = int(r["t"])
            cid_i = int(cid)
            rows.append(dict(
                seed=SEED, cid=cid_i, t=t,
                event_class="salience_template",
                event_type="salience_template_theta_high_persistence",
                event_source="researcher_template:theta_high_persistence_median_N3_v1",
                template_version="theta_high_persistence_median_N3_v1",
                event_segment_id=f"ps_{cid_i}_{seg}", segment_length=int(seglen),
                n_core=int(r["n_core"]) if not pd.isna(r["n_core"]) else -1,
                theta_resultant_length=float(r["core_node_theta_resultant_length"]),
                theta_cid_percentile=float(r["theta_cid_percentile"]),
                rank_1_atom=r["rank_1_atom"], rank_1_sim=float(r["rank_1_sim"]),
                C=float(r["C_at_window_end"]) if not pd.isna(r["C_at_window_end"]) else np.nan,
                Q=float(r["Q_remaining_at_window_end"]) if not pd.isna(r["Q_remaining_at_window_end"]) else np.nan,
                phys_core_status=r["phys_core_status"],
                context_window=CONTEXT_WINDOW,
                ledger_source_id=f"{SEED}:{cid_i}:{t}",
            ))
    ev = pd.DataFrame(rows)
    return ev, h, persist_idx_by_cid


def main():
    ev, h, persist_idx = build()
    ev.to_parquet(OUT / "v1303e_persistence_salience_seed0.parquet", index=False)

    # q95版(v1303c)との比較
    evc = pd.read_parquet(EVENTC)
    q95 = evc[evc.event_class == "salience_template"]
    q95_idx = {cid: set(g["t"].tolist()) for cid, g in q95.groupby("cid")}

    # cid別 frac / jaccard / segment
    npts = h.groupby("cid").size().to_dict()
    nc_of = h.groupby("cid")["n_core"].first().to_dict()
    comp = []
    for cid in npts:
        ps = persist_idx.get(cid, set())
        q = q95_idx.get(cid, set())
        u = len(ps | q)
        comp.append(dict(cid=cid, n_core=int(nc_of[cid]) if not pd.isna(nc_of[cid]) else -1,
                         n_points=npts[cid],
                         persist_frac=len(ps) / npts[cid], q95_frac=len(q) / npts[cid],
                         jaccard=len(ps & q) / u if u else np.nan,
                         persist_empty=int(len(ps) == 0)))
    comp = pd.DataFrame(comp)
    comp.to_parquet(OUT / "v1303e_compare_q95_seed0.parquet", index=False)

    # 健全性
    hc = {}
    hc["health1_persist_empty_cid"] = int(comp["persist_empty"].sum())  # 0であるべき
    hc["health2_all_hosted"] = bool((ev["phys_core_status"] == "hosted_available").all())
    hc["health3_jaccard_q95_by_ncore"] = {int(nc): round(float(comp[comp.n_core == nc]["jaccard"].median()), 3)
                                          for nc in [2, 3, 4, 5]}
    rub = verify_rubric(ev, h, persist_idx)

    print("=== v1303e persistence salience (閾値内部化・判定なし #12) ===")
    print(f"persistence salience 行={len(ev)} cid={ev['cid'].nunique()} | event_source=手本タグ(離脱ポインタ)")
    print(f"segment数={ev['event_segment_id'].nunique()} segment長 med={ev.groupby('event_segment_id')['segment_length'].first().median():.0f}")
    print("\n--- persistence vs q95(5%固定) frac・空振り・Jaccard (n_core別中央値) ---")
    print(f"{'n_core':6s} | persist_frac q95_frac jaccard | persist空振り/cid")
    for nc in [2, 3, 4, 5]:
        s = comp[comp.n_core == nc]
        print(f"  n{nc:4d} | {s['persist_frac'].median():.3f}        {s['q95_frac'].median():.3f}     "
              f"{s['jaccard'].median():.3f}   | {int(s['persist_empty'].sum())}/{len(s)}")
    print("\n--- 像の違い: persistenceは持続区間(広い)・q95は瞬間ピーク(狭い) ---")
    print(f"  persistence frac 全体med={comp['persist_frac'].median():.3f} (cidの寿命の約{comp['persist_frac'].median()*100:.0f}%が持続高同期)")
    print(f"  q95 frac 全体med={comp['q95_frac'].median():.3f} (約5%の瞬間ピーク)")
    print(f"  Jaccard 全体med={comp['jaccard'].median():.3f} (低い=別の時点を拾う=多様性拡張の像)")
    print("\n--- 健全性 sanity check ---")
    for k, v in hc.items():
        print(f"  {k}: {v}")
    print("\n--- 説明可能性ルーブリック突合(実装後自己検証) ---")
    for k, v in rub.items():
        print(f"  {k}: {v}")
    print(f"\n  ルーブリック全項目 PASS = {all(rub.values())} | 健全性1(空振り0)={hc['health1_persist_empty_cid']==0}")
    print(f"\n出力: {OUT}/v1303e_persistence_salience_seed0.parquet (+compare)")


def verify_rubric(ev, h, persist_idx):
    chk = {}
    # persistence行は全てθ>=cid中央値か(持続区間の定義)
    med_of = h.groupby("cid")["core_node_theta_resultant_length"].median().to_dict()
    chk["persist_rows_all_ge_median"] = bool(
        all(r.theta_resultant_length >= med_of[int(r.cid)] - 1e-9 for r in ev.itertuples()))
    # 各segmentが連続N_PERSIST点以上か
    seglen = ev.groupby("event_segment_id")["segment_length"].first()
    chk["all_segments_ge_N"] = bool((seglen >= N_PERSIST).all())
    # event_source は全行 手本タグ(離脱ポインタ)
    chk["event_source_all_template"] = bool(ev["event_source"].str.startswith("researcher_template:").all())
    # 全行 hosted(q95版と同じ性質)
    chk["all_hosted"] = bool((ev["phys_core_status"] == "hosted_available").all())
    # 空振りcidなし(全面適用の前提・全n_core機能)
    chk["no_empty_cid"] = bool(all(len(persist_idx.get(cid, set())) > 0 for cid in h["cid"].unique()
                                   if (h["cid"] == cid).sum() >= N_PERSIST))
    # event_typeは単一(persistence版で統一)
    chk["event_type_single"] = bool(ev["event_type"].nunique() == 1)
    return chk


if __name__ == "__main__":
    main()
