#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# v1303e 調査 — Frozen 神の手排除の方法(persistence-based birth / MAD-DT)が
#   θ高同期閾値(cid内 q95 上位5%固定)に応用できるか・5%固定と違う像を拾うか
#   （read-only 後処理のみ・再走/write-back なし・seed0・判定なし #12）
#
# 規律宣言(Code A):
#  読: v1303a ledger + v1303c event_ledger READ-ONLY。書: outputs/v1303e/ のみ。
#  Frozen の方法の型(実コードから抽出):
#   - MAD-DT型(v105_memory_readout.py:990-1010): theta=mean(|Δ履歴|), R=Δ/(theta+eps),
#     R>1.0で発火 = 「履歴平均変化で正規化した surprise」への閾値(=Δ遷移検出器)。
#   - persistence型(age_r≥τ, v104_memory_readout.py:1741/2367): age_r=連続R>0 step数,
#     age_r≥τで選択 = 「状態が持続した区間」検出器(=値閾値を持続時間閾値に置換)。
#  概念整理: θ-high salience は「状態(値が高い)」→ persistence型が自然に対応。MAD-DTは
#   元来Δ(遷移)検出器ゆえ θ値に当てるのは適応(θ値版MAD-DT)・Δに当てると遷移を拾う(別salience)。
#  規律: θをθで言い換える準同義反復に注意(神の手は厳格にしない方針ゆえθ寄りは許容)。
#   判定せず観察事実のみ(#12)。結果を確定しにいかない(可能性を開いたまま)。応用可否はTaka。
# ─────────────────────────────────────────────────────────────────────────────
import numpy as np
import pandas as pd
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LEDGER = REPO / "unified" / "v1303" / "outputs" / "v1303_ledger_seed0.parquet"
OUT = REPO / "unified" / "v1303" / "outputs" / "v1303e"
OUT.mkdir(parents=True, exist_ok=True)
MIN_POINTS = 30


def runs_mask_ge(cond, n_min):
    """cond(bool配列)の連続Trueが長さ>=n_min の区間に属する index集合(persistence型)。"""
    idx = set()
    n = len(cond)
    i = 0
    while i < n:
        if not cond[i]:
            i += 1
            continue
        j = i
        while j < n and cond[j]:
            j += 1
        if j - i >= n_min:
            idx.update(range(i, j))
        i = j
    return idx


def n_segments_ge(cond, n_min):
    n = len(cond); i = 0; segs = 0
    while i < n:
        if not cond[i]:
            i += 1; continue
        j = i
        while j < n and cond[j]:
            j += 1
        if j - i >= n_min:
            segs += 1
        i = j
    return segs


def methods_for_cid(theta):
    """各方式の選択 index集合を返す。theta = θ_resultant の時系列。"""
    n = len(theta)
    med = np.median(theta)
    mad = np.median(np.abs(theta - med)) + 1e-12
    q95 = np.quantile(theta, 0.95)
    q75 = np.quantile(theta, 0.75)
    d = np.abs(np.diff(theta))  # |Δθ|（遷移）
    out = {}
    # 基準: 5%固定
    out["q95_fixed5pct"] = set(np.where(theta >= q95)[0].tolist())
    # MAD-DT(値版): θ >= median + k·MAD（k=1,2,3）= 履歴中央値からの上振れ
    for k in (1, 2, 3):
        out[f"madvalue_k{k}"] = set(np.where(theta >= med + k * mad)[0].tolist())
    # MAD-DT(Δ版・元来の型に忠実): |Δθ| >= median(|Δ|) + k·MAD(|Δ|) = 遷移surprise（k=1）
    dmed = np.median(d); dmad = np.median(np.abs(d - dmed)) + 1e-12
    out["maddelta_k1_transition"] = set((np.where(d >= dmed + 1 * dmad)[0] + 1).tolist())
    # persistence型: θ >= median を連続N点（N=3,5）持続した区間（age_r≥τ 応用）
    cond_med = theta >= med
    out["persist_median_N3"] = runs_mask_ge(cond_med, 3)
    out["persist_median_N5"] = runs_mask_ge(cond_med, 5)
    # persistence型(上位帯): θ >= q75 を連続3点
    out["persist_q75_N3"] = runs_mask_ge(theta >= q75, 3)
    # transition型(n2の崩れ・GPT): 下位5% Δθ符号付き = θが急落した時点
    sd = np.diff(theta)
    drop_thr = np.quantile(sd, 0.05)
    out["transition_drop5pct"] = set((np.where(sd <= drop_thr)[0] + 1).tolist())
    return out


def jaccard(A, B):
    u = len(A | B)
    return len(A & B) / u if u else np.nan


def main():
    df = pd.read_parquet(LEDGER)
    h = df[df["phys_core_status"].eq("hosted_available")].copy().sort_values(["cid", "t"])

    rows = []
    for cid, g in h.groupby("cid"):
        g = g.sort_values("t").reset_index(drop=True)
        theta = g["core_node_theta_resultant_length"].values.astype(float)
        n = len(theta)
        if n < MIN_POINTS:
            continue
        nc = int(g["n_core"].iloc[0]) if not pd.isna(g["n_core"].iloc[0]) else -1
        m = methods_for_cid(theta)
        ref = m["q95_fixed5pct"]
        rec = {"cid": int(cid), "n_core": nc, "n_points": n,
               "theta_std": float(np.std(theta)), "theta_median": float(np.median(theta))}
        for name, idx in m.items():
            rec[f"{name}__count"] = len(idx)
            rec[f"{name}__frac"] = len(idx) / n
            rec[f"{name}__empty"] = int(len(idx) == 0)
            if name != "q95_fixed5pct":
                rec[f"{name}__jaccard_q95"] = jaccard(idx, ref)
        # persistence のセグメント数（n2 で機能するか）
        cond_med = theta >= np.median(theta)
        rec["persist_median_N3__nseg"] = n_segments_ge(cond_med, 3)
        rows.append(rec)

    res = pd.DataFrame(rows)
    res.to_parquet(OUT / "v1303e_threshold_compare_seed0.parquet", index=False)

    METHODS = ["q95_fixed5pct", "madvalue_k1", "madvalue_k2", "madvalue_k3",
               "maddelta_k1_transition", "persist_median_N3", "persist_median_N5",
               "persist_q75_N3", "transition_drop5pct"]

    print("=== v1303e Frozen方法のθ閾値応用 調査 (read-only後処理・判定なし #12) ===")
    print(f"対象cid={len(res)} (min_points={MIN_POINTS})")

    print("\n--- (項目1) 方式別イベント数(frac=拾う割合) n_core別中央値 + (項目3)空振りcid数 ---")
    print(f"{'method':24s} | " + " ".join(f"n{nc}frac" for nc in [2,3,4,5]) + " | 空振りcid(n2/全)")
    for name in METHODS:
        line = f"{name:24s} |"
        for nc in [2, 3, 4, 5]:
            s = res[res.n_core == nc]
            line += f" {s[f'{name}__frac'].median():.3f}"
        empty_n2 = int(res[(res.n_core == 2)][f"{name}__empty"].sum())
        empty_all = int(res[f"{name}__empty"].sum())
        line += f" | {empty_n2}/{empty_all}"
        print(line)

    print("\n--- (項目2/5) q95(5%固定)との重なり Jaccard n_core別中央値 (低い=違う像=多様性拡張) ---")
    print(f"{'method':24s} | " + " ".join(f"n{nc}" for nc in [2,3,4,5]))
    for name in METHODS:
        if name == "q95_fixed5pct":
            continue
        line = f"{name:24s} |"
        for nc in [2, 3, 4, 5]:
            s = res[res.n_core == nc]
            line += f" {s[f'{name}__jaccard_q95'].median():.3f}"
        print(line)

    print("\n--- (項目4) madvalue の k を下げた時の過剰検出 (frac が5%固定0.05を超えるか) ---")
    for k in (1, 2, 3):
        s = res
        over = int((s[f"madvalue_k{k}__frac"] > 0.10).sum())
        print(f"  madvalue_k{k}: frac中央={s[f'madvalue_k{k}__frac'].median():.3f} "
              f"| frac>0.10 の cid={over}/{len(s)} (過剰検出傾向)")

    print("\n--- persistence が n2 で機能するか (空振りでなくセグメントが立つか) ---")
    for nc in [2, 5]:
        s = res[res.n_core == nc]
        print(f"  n_core={nc}: persist_median_N3 セグメント数 med={s['persist_median_N3__nseg'].median():.0f} "
              f"空振り={int(s['persist_median_N3__empty'].sum())}/{len(s)} | "
              f"madvalue_k3 空振り={int(s['madvalue_k3__empty'].sum())}/{len(s)}")

    print("\n--- 概念整理(観察): θ-high=状態, MAD-DT(Δ版)=遷移 の拾うものの違い ---")
    print(f"  madvalue_k1(値版・状態) vs q95 Jaccard全体med={res['madvalue_k1__jaccard_q95'].median():.3f}")
    print(f"  maddelta_k1(Δ版・遷移)  vs q95 Jaccard全体med={res['maddelta_k1_transition__jaccard_q95'].median():.3f} (低い=遷移は状態と別物)")
    print(f"  persist_median_N3(持続)  vs q95 Jaccard全体med={res['persist_median_N3__jaccard_q95'].median():.3f}")
    print(f"\n出力: {OUT}/v1303e_threshold_compare_seed0.parquet")


if __name__ == "__main__":
    main()
