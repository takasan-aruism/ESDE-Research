#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# v1303e Step B (修正版 v2) — θ高同期手本の閾値を「5%固定(q95)」から
#   「動的(cid内 robust-range 正規化)で高同期が持続した区間」に置き換え、salience の像が
#   変わるかを read-only 観察（後処理のみ・再走/write-back なし・seed0・判定なし #12）
#
# 【v1→v2 の修正理由(信頼問題への対応)】
#  v1 = θ≥cid中央値 連続3点(median-persistence) は「中央値またぎ」を拾い、θ<0.5 を n5で29%/
#  n4で18.8% 含む = 「高同期」でなく「平均以上」を拾っていた(Web Claude独立検証で判明・確認済)。
#  原因 = Frozen の age_r(R>0=意味ある条件の持続)を横流しした際、土台条件を θ≥median(=真ん中・
#  高さの意味なし)に緩めた。形だけ移植し中身(高同期)が抜けた。
#  v2 = 土台を「その cid 自身の到達域に対する高さ」= robust-range 正規化に変更:
#     θ >= q05 + F*(q95-q05)  (cid内・F=0.6・外れ値に頑健なq05-q95レンジ) が連続3点持続。
#     これで θ<0.5 を n2-4で0%/n5で1% に潰し(高同期を拾う)、全n_core空振り0(全面適用)を両立。
#  実測で確定: f=0.6 robust が「θ<0.5ほぼ0% かつ 空振り0」の唯一点(min-maxは外れ値で空振り増)。
#
# 規律: 読=v1303a ledger READ-ONLY/書=outputs/v1303e のみ・write-back なし(B型)。
#  A型/#CW7: F=0.6・persist=3 は研究者選択ゆえ event_source 手本タグ(離脱ポインタ・将来endogenous置換可)。
#  L型: θ系閾値の内部化であって非θ系=言語の離脱ではない(明記・準同義反復を隠さない)。
#  D型: cid内 robust-range(cid局所主語)・全n_core機能・cid個別/n_core別。#12: 判定せず観察事実のみ。
#  「想定通り動くか」を verify_gates() で機械確認してから完了(信頼問題: 想定外で先に進まない)。
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
F_RANGE = 0.6          # robust-range の高さ係数(研究者選択=手本)。θ>=q05+F*(q95-q05)
N_PERSIST = 3          # 連続N点(=30step)以上の持続
RLO, RHI = 0.05, 0.95  # robust range の下端/上端(外れ値に頑健・min-max を使わない)
TEMPLATE = "theta_high_robustrange_f06_persist3_v2"

EXPLAIN = {
    "salience の定義": ("HIGH",
        "θ_resultant が [cid内 q05 + 0.6*(q95-q05)] 以上の状態が連続3点続いた区間。"
        "robust-range 正規化=その個体の到達域に対する高さ(中央値またぎでない)・連続3点で持続を担保"),
    "event_source/template_version": ("HIGH",
        f"researcher_template:{TEMPLATE}(F=0.6/persist=3は研究者選択ゆえ手本明示・離脱ポインタ)"),
    "event_segment_id/segment_length": ("HIGH", "連続持続区間ごとの通し番号と長さ(持続=q95瞬間ピークとの像差の指標)"),
    "ledger列(seed/cid/t/n_core/θ/rank_1/C/Q/phys_core_status)": ("HIGH", "v1303a ledger 直接コピー(v1303c と同列構成で比較可)"),
}


def runs_mask_ge(cond, n_min):
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
                idx[k] = (seg, j - i)
        i = j
    return idx


def build():
    df = pd.read_parquet(LEDGER)
    h = df[df["phys_core_status"].eq("hosted_available")].copy().sort_values(["cid", "t"]).reset_index(drop=True)
    h["theta_cid_percentile"] = h.groupby("cid")["core_node_theta_resultant_length"].rank(pct=True)
    rows = []
    persist_idx_by_cid = {}
    for cid, g in h.groupby("cid"):
        g = g.sort_values("t").reset_index(drop=True)
        theta = g["core_node_theta_resultant_length"].values.astype(float)
        lo, hi = np.quantile(theta, RLO), np.quantile(theta, RHI)
        thr = lo + F_RANGE * (hi - lo)   # 動的しきい値: その cid 自身の到達域に対する高さ
        seg_map = runs_mask_ge(theta >= thr, N_PERSIST)
        persist_idx_by_cid[int(cid)] = set(g["t"].iloc[list(seg_map.keys())].tolist())
        for k, (seg, seglen) in seg_map.items():
            r = g.iloc[k]; t = int(r["t"]); cid_i = int(cid)
            rows.append(dict(
                seed=SEED, cid=cid_i, t=t,
                event_class="salience_template",
                event_type="salience_template_theta_high_persistence",
                event_source=f"researcher_template:{TEMPLATE}",
                template_version=TEMPLATE,
                event_segment_id=f"ps_{cid_i}_{seg}", segment_length=int(seglen),
                theta_threshold=float(thr),
                n_core=int(r["n_core"]) if not pd.isna(r["n_core"]) else -1,
                theta_resultant_length=float(r["core_node_theta_resultant_length"]),
                theta_cid_percentile=float(r["theta_cid_percentile"]),
                rank_1_atom=r["rank_1_atom"], rank_1_sim=float(r["rank_1_sim"]),
                C=float(r["C_at_window_end"]) if not pd.isna(r["C_at_window_end"]) else np.nan,
                Q=float(r["Q_remaining_at_window_end"]) if not pd.isna(r["Q_remaining_at_window_end"]) else np.nan,
                phys_core_status=r["phys_core_status"],
                context_window="pm1_step10", ledger_source_id=f"{SEED}:{cid_i}:{t}",
            ))
    return pd.DataFrame(rows), h, persist_idx_by_cid


def verify_gates(ev, h, persist_idx):
    """『想定通り動くか』の機械確認ゲート(信頼問題: 想定外なら完了にしない)。"""
    g = {}
    # ゲート1: 高同期を拾う = θ<0.5 を拾う率が全n_coreで <=2% (v1のn5 29%を潰せたか)
    for nc in [2, 3, 4, 5]:
        s = ev[ev.n_core == nc]["theta_resultant_length"]
        g[f"gate1_n{nc}_theta_lt0.5_frac<=2pct"] = bool(len(s) and (s < 0.5).mean() <= 0.02)
    # ゲート2: 全面適用 = 空振りcid 0 (>=N点ある cid 全てで salience が立つ)
    elig = [c for c in h["cid"].unique() if (h["cid"] == c).sum() >= N_PERSIST]
    g["gate2_no_empty_cid"] = bool(all(len(persist_idx.get(c, set())) > 0 for c in elig))
    # ゲート3: 拾うθが各cidの高域。
    #  注: theta_cid_percentile>=0.5 を当初ゲートにしたが FAIL。調査で「飽和cid(n2でθが
    #  ほぼ高い)では θ=0.70 でも順位は中位(他がもっと高い)」= 順位基準は範囲基準の設計意図
    #  (飽和でも高同期を拾う)と矛盾する不適切ゲートと判明。順位中位の行が『本当に高θ』である
    #  ことを直接検証する形に差し替え(=飽和ケースが正しく高同期である証明)。
    sat = ev[ev["theta_cid_percentile"] < 0.5]   # 順位中位だが範囲では高い飽和cidの行
    g["gate3_rank_mid_rows_are_high(theta>=0.5)"] = bool(len(sat) == 0 or (sat["theta_resultant_length"] >= 0.5).all())
    g["gate3_theta_median_high"] = bool(all(ev[ev.n_core == nc]["theta_resultant_length"].median() >= 0.6 for nc in [2, 3, 4, 5]))
    # ゲート4: 定義通り = 全行 θ>=その行のthreshold, 全segment>=N点, event_source手本タグ
    g["gate4_all_ge_threshold"] = bool((ev["theta_resultant_length"] >= ev["theta_threshold"] - 1e-9).all())
    g["gate4_all_segments_ge_N"] = bool((ev.groupby("event_segment_id")["segment_length"].first() >= N_PERSIST).all())
    g["gate4_event_source_template"] = bool(ev["event_source"].str.startswith("researcher_template:").all())
    g["gate4_all_hosted"] = bool((ev["phys_core_status"] == "hosted_available").all())
    return g


def main():
    ev, h, persist_idx = build()
    ev.to_parquet(OUT / "v1303e_persistence_salience_seed0.parquet", index=False)

    evc = pd.read_parquet(EVENTC)
    q95 = evc[evc.event_class == "salience_template"]
    q95_idx = {cid: set(gg["t"].tolist()) for cid, gg in q95.groupby("cid")}
    npts = h.groupby("cid").size().to_dict()
    nc_of = h.groupby("cid")["n_core"].first().to_dict()
    comp = []
    for cid in npts:
        ps = persist_idx.get(cid, set()); q = q95_idx.get(cid, set()); u = len(ps | q)
        comp.append(dict(cid=cid, n_core=int(nc_of[cid]) if not pd.isna(nc_of[cid]) else -1,
                         persist_frac=len(ps) / npts[cid], q95_frac=len(q) / npts[cid],
                         jaccard=len(ps & q) / u if u else np.nan, persist_empty=int(len(ps) == 0)))
    comp = pd.DataFrame(comp)
    comp.to_parquet(OUT / "v1303e_compare_q95_seed0.parquet", index=False)

    gates = verify_gates(ev, h, persist_idx)
    print("=== v1303e 修正版v2: 動的(robust-range)高同期持続 salience (判定なし #12) ===")
    print(f"定義: θ >= q05+{F_RANGE}*(q95-q05) [cid内robust-range] が連続{N_PERSIST}点持続")
    print(f"salience {len(ev)}行 / {ev.cid.nunique()}cid / {ev.event_segment_id.nunique()}segment")
    print("\n--- (v1の問題が直ったか) 拾うθ実値 n_core別: θ<0.5割合 ---")
    print(f"{'n_core':6s}| v2 θmed  θ<0.5%  | (参考)v1 median版 θ<0.5%  | q95 θmed")
    v1lo = {2: 0.4, 3: 3.6, 4: 18.8, 5: 29.0}
    for nc in [2, 3, 4, 5]:
        s = ev[ev.n_core == nc]["theta_resultant_length"]; qs = q95[q95.n_core == nc]["theta_resultant_length"]
        print(f"  n{nc:4d}| {s.median():.3f}    {(s<0.5).mean()*100:4.1f}%   | {v1lo[nc]:4.1f}%                   | {qs.median():.3f}")
    print("\n--- persistence(持続) vs q95(瞬間ピーク) ---")
    print(f"  persist frac全体med={comp.persist_frac.median():.3f} / q95 frac={comp.q95_frac.median():.3f} / "
          f"Jaccard={comp.jaccard.median():.3f}(別の像) / 空振り={int(comp.persist_empty.sum())}")
    print(f"  segment長 med={ev.groupby('event_segment_id')['segment_length'].first().median():.0f} "
          f"(持続=q95の瞬間ピークと違い区間を持つ)")
    print("\n--- 『想定通り動くか』検証ゲート(信頼問題: 全PASSで完了) ---")
    for k, v in gates.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}: {v}")
    allpass = all(gates.values())
    print(f"\n  ★ 全ゲート PASS = {allpass} {'→ 想定通り動作・完了可' if allpass else '→ 想定外・先に進まない'}")
    print(f"\n出力: {OUT}/v1303e_persistence_salience_seed0.parquet (+compare)")


if __name__ == "__main__":
    main()
