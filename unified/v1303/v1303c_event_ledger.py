#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# v1303c Step B — 研究者手本イベント(誕生署名 R_positive + 位相高同期 θ-high)を
#   read-only 検出し、event_class で分けて cid/t に紐づく event_ledger に保持する
#   （道3版・既存 v1303a ledger の後処理のみ・再走なし・write-back しない）
#
# 規律宣言（Code A / 失敗記録12型・v1303c 道3設計）
#  1. 読: 既存 ledger (unified/v1303/outputs/v1303_ledger_seed0.parquet) READ-ONLY。
#     書: unified/v1303/outputs/v1303c/ のみ。物理/CID/親へ write-back しない（B型）。
#  2. 手本→離脱(A型/#CW7回避): event_source に手本タグを焼く＝将来 endogenous へ一括置換できる
#     離脱ポインタ。隠さない。θ高同期も「研究者手本」と明記(自律検出でない)。
#  3. 失敗型回避:
#     L型 → R_positive を「結節イベント」と偽らず event_class=birth_signature(誕生署名)。
#            event_type に onset を使わない(観測不能・捏造しない)。event_strength を使わず
#            resonating_internal_link_count(生カウント)。θ高同期を「本質」と言い切らない。
#     D型 → θ高同期は絶対値θ>0.9 でなく cid内 percentile 上位5%(n2偏り回避・CID局所主語)。
#     #11 → birth_signature と salience_template を event_class で分離(混ぜない・合成しない)。
#     #12/J → (a)/(b)判定しない。観察事実のみ。手本は2系統で打ち止め。seed0 のみ。
#     F型 → anchor=v105_v2 統一(v1114=v918 anchor は流用しない)。
#  4. 説明可能性ルーブリック(Step A §5)準拠。各列の操作定義は EXPLAIN dict に明記し、
#     実装後 verify_rubric() で生成 ledger が定義通りか自己検証する。
#  判定は Web Claude / Taka。
# ─────────────────────────────────────────────────────────────────────────────
import numpy as np
import pandas as pd
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LEDGER = REPO / "unified" / "v1303" / "outputs" / "v1303_ledger_seed0.parquet"
OUT = REPO / "unified" / "v1303" / "outputs" / "v1303c"
OUT.mkdir(parents=True, exist_ok=True)

SEED = 0
THETA_PCTL = 0.95          # cid内 percentile 上位5%（研究者手本・theta_high_cid_percentile_v1）
CONTEXT_WINDOW = "pm1_step10"  # pre/post 文脈 = 隣接 step10 行(t±10)に固定（恣意排除）

# 説明可能性ルーブリック（Step A §5）: 列 -> (level, 操作定義)。verify_rubric で突合。
EXPLAIN = {
    "seed/cid/t/n_core/theta_resultant_length/rank_1_atom/rank_1_sim/C/Q/"
    "phys_core_status/r_positive_count/internal_link_count":
        ("HIGH", "v1303a ledger 行からの直接コピー（変換なし）"),
    "event_class":
        ("HIGH", "birth_signature(R_positive>0行) か salience_template(θ cid内上位5%行) の二択。混ぜない"),
    "event_source/template_version":
        ("HIGH", "定数リテラルの手本タグ＝離脱ポインタ。birth=researcher_template:R_positive_birth_signature_v1 / salience=researcher_template:theta_high_cid_percentile_v1"),
    "event_type(birth)":
        ("HIGH", "present_at_birth(segment先頭かつi==0) / offset(segment末) / active(中間)。onsetは使わない(観測不能)"),
    "event_type(salience)":
        ("HIGH", "salience_template_theta_high（θ_cid_percentile>=0.95 の行）"),
    "event_segment_id":
        ("HIGH", "同一cid内で R_positive>0 が step10連続する塊への通し番号。salience は単独行ごと"),
    "theta_cid_percentile":
        ("HIGH", "その cid 生涯内での theta_resultant_length の percentile rank(0-1)"),
    "resonating_internal_link_count":
        ("MEDIUM", "= core_internal_R_positive_count の生カウント（共鳴する内部リンク数）。「強さ」と呼ばない"),
    "ledger_source_id/pre_t/post_t/pre_context_id/post_context_id/context_window":
        ("HIGH", "元ledger行(cid,t)と隣接step10行(t±10)への参照ポインタ。窓幅は pm1_step10 固定。隣接行が無ければ null"),
}


def build():
    df = pd.read_parquet(LEDGER)
    h = df[df["phys_core_status"].eq("hosted_available")].copy().sort_values(["cid", "t"]).reset_index(drop=True)

    # 隣接行存在判定用の (cid,t) 集合（pre/post 紐づけ・関係は作らず参照のみ）
    hosted_keys = set(zip(h["cid"].tolist(), h["t"].tolist()))

    # cid内 percentile（θ高同期判定の根拠・cid局所主語）
    #  - theta_cid_percentile: 各行の cid 内 percentile rank（0-1, 情報列）
    #  - 選定しきい値: cid 内 95パーセンタイル「値」(quantile 0.95) 以上を θ高同期とする
    #    （quantile しきい値方式＝設計検証値 n2:1090/n3:175/n4:606/n5:1349・全228cid網羅と一致。
    #     rank(pct) 方式は同値tieで一部cidが漏れるため値しきい値を採用＝説明可能性も明確）
    h["theta_cid_percentile"] = h.groupby("cid")["core_node_theta_resultant_length"].rank(pct=True)
    h["theta_cid_q95"] = h.groupby("cid")["core_node_theta_resultant_length"].transform(
        lambda x: x.quantile(THETA_PCTL))

    rows = []

    def base_cols(r):
        cid = int(r["cid"]); t = int(r["t"])
        pre_t = t - 10; post_t = t + 10
        pre_id = f"{SEED}:{cid}:{pre_t}" if (cid, pre_t) in hosted_keys else None
        post_id = f"{SEED}:{cid}:{post_t}" if (cid, post_t) in hosted_keys else None
        return dict(
            seed=SEED, cid=cid, t=t,
            n_core=int(r["n_core"]) if not pd.isna(r["n_core"]) else -1,
            theta_resultant_length=float(r["core_node_theta_resultant_length"]),
            theta_cid_percentile=float(r["theta_cid_percentile"]),
            rank_1_atom=r["rank_1_atom"], rank_1_sim=float(r["rank_1_sim"]),
            C=float(r["C_at_window_end"]) if not pd.isna(r["C_at_window_end"]) else np.nan,
            Q=float(r["Q_remaining_at_window_end"]) if not pd.isna(r["Q_remaining_at_window_end"]) else np.nan,
            phys_core_status=r["phys_core_status"],
            r_positive_count=float(r["core_internal_R_positive_count"]) if not pd.isna(r["core_internal_R_positive_count"]) else 0.0,
            internal_link_count=float(r["core_internal_link_count"]) if not pd.isna(r["core_internal_link_count"]) else 0.0,
            resonating_internal_link_count=float(r["core_internal_R_positive_count"]) if not pd.isna(r["core_internal_R_positive_count"]) else 0.0,
            ledger_source_id=f"{SEED}:{cid}:{t}",
            pre_t=pre_t if pre_id else None, post_t=post_t if post_id else None,
            context_window=CONTEXT_WINDOW,
            pre_context_id=pre_id, post_context_id=post_id,
        )

    # ── event_class = birth_signature（R_positive>0 の連続区間・誕生署名）──────
    seg_counter = 0
    for cid, g in h.groupby("cid"):
        g = g.sort_values("t").reset_index(drop=True)
        rpos = (g["core_internal_R_positive_count"].fillna(0).values > 0)
        i = 0
        n = len(g)
        while i < n:
            if not rpos[i]:
                i += 1
                continue
            # 連続区間 [i, j)
            j = i
            while j < n and rpos[j]:
                j += 1
            seg_counter += 1
            for k in range(i, j):
                r = g.iloc[k]
                # event_type: present_at_birth(先頭かつ cid の i==0) / offset(区間末) / active
                if k == i and i == 0:
                    et = "birth_signature_r_positive_present_at_birth"
                elif k == j - 1:
                    et = "birth_signature_r_positive_offset"
                else:
                    et = "birth_signature_r_positive_active"
                row = base_cols(r)
                row.update(dict(
                    event_class="birth_signature", event_type=et,
                    event_source="researcher_template:R_positive_birth_signature_v1",
                    template_version="r_positive_birth_signature_v1",
                    event_segment_id=f"bs_{cid}_{seg_counter}",
                ))
                rows.append(row)
            i = j

    # ── event_class = salience_template（θ >= cid内 q95 値・上位5%）────────────
    sal = h[h["core_node_theta_resultant_length"] >= h["theta_cid_q95"]]
    for _, r in sal.iterrows():
        row = base_cols(r)
        row.update(dict(
            event_class="salience_template", event_type="salience_template_theta_high",
            event_source="researcher_template:theta_high_cid_percentile_v1",
            template_version="theta_high_cid_percentile_v1",
            event_segment_id=None,  # salience は単独行ごと（区間化しない）
        ))
        rows.append(row)

    cols = ["seed", "cid", "t", "event_class", "event_type", "event_source", "template_version",
            "event_segment_id", "n_core", "theta_resultant_length", "theta_cid_percentile",
            "rank_1_atom", "rank_1_sim", "C", "Q", "phys_core_status",
            "r_positive_count", "internal_link_count", "resonating_internal_link_count",
            "ledger_source_id", "pre_t", "post_t", "context_window",
            "pre_context_id", "post_context_id"]
    ev = pd.DataFrame(rows)[cols]
    return ev, h


def health_checks(ev, h):
    out = {}
    bs = ev[ev["event_class"] == "birth_signature"]
    sal = ev[ev["event_class"] == "salience_template"]
    # 健全性1: birth_signature 行は全件 hosted（assert）
    out["health1_birth_all_hosted"] = bool((bs["phys_core_status"] == "hosted_available").all())
    out["health1_birth_rows"] = int(len(bs))
    # 健全性2: R_positive 行 rank_1 entropy vs 全hosted（assert せず効果記録・n_core別）
    def ent(s):
        vc = s.value_counts(); n = len(s)
        return float(-sum((c / n) * np.log2(c / n) for c in vc)) if n else np.nan
    for nc in [2, 5]:
        hn = h[h["n_core"] == nc]
        bn = bs[bs["n_core"] == nc]
        out[f"health2_n{nc}_entropy_all"] = round(ent(hn["rank_1_atom"]), 3)
        out[f"health2_n{nc}_entropy_birth"] = round(ent(bn["rank_1_atom"]), 3) if len(bn) else None
    # 健全性3: salience が全 n_core から拾えるか
    out["health3_salience_cid_per_ncore"] = {
        int(nc): int(sal[sal["n_core"] == nc]["cid"].nunique()) for nc in [2, 3, 4, 5]}
    out["health3_total_cid"] = {
        int(nc): int(h[h["n_core"] == nc]["cid"].nunique()) for nc in [2, 3, 4, 5]}
    return out


def verify_rubric(ev, h):
    """説明可能性ルーブリック(Step A §5)と生成 ledger の突合（実装後の自己検証）。"""
    chk = {}
    bs = ev[ev["event_class"] == "birth_signature"]
    sal = ev[ev["event_class"] == "salience_template"]
    # present_at_birth は本当に各 cid の i==0(=最初の hosted t)行のみか
    first_t = h.groupby("cid")["t"].min().to_dict()
    pab = bs[bs["event_type"].str.endswith("present_at_birth")]
    chk["present_at_birth_all_at_first_t"] = bool(
        all(first_t.get(int(r.cid)) == int(r.t) for r in pab.itertuples()))
    # birth_signature 行は全て R_positive>0 か（0行を混ぜていない）
    chk["birth_rows_all_rpos_positive"] = bool((bs["r_positive_count"] > 0).all())
    # salience 行は全て cid内 q95 値以上か（quantile しきい値方式）
    q95 = h.groupby("cid")["core_node_theta_resultant_length"].quantile(THETA_PCTL).to_dict()
    chk["salience_rows_all_above_cid_q95"] = bool(
        all(r.theta_resultant_length >= q95[int(r.cid)] for r in sal.itertuples()))
    # resonating_internal_link_count == r_positive_count（生カウント・別名の整合）
    chk["resonating_eq_rpos"] = bool((ev["resonating_internal_link_count"] == ev["r_positive_count"]).all())
    # event_class は2値のみ・event_source は手本タグのみ（離脱ポインタ）
    chk["event_class_only_two"] = sorted(ev["event_class"].unique().tolist()) == ["birth_signature", "salience_template"]
    chk["event_source_all_template"] = bool(ev["event_source"].str.startswith("researcher_template:").all())
    # pre/post context は隣接行が無ければ null（ledger_source_id 形式の検証）
    chk["pre_context_null_at_first_t"] = bool(
        pab["pre_context_id"].isna().all())  # 誕生時行は直前なし
    return chk


def main():
    ev, h = build()
    ev.to_parquet(OUT / "v1303c_event_ledger_seed0.parquet", index=False)
    hc = health_checks(ev, h)
    rub = verify_rubric(ev, h)

    print("=== v1303c event_ledger (道3・二系統 event_class・判定なし #12) ===")
    print(f"総イベント行={len(ev)} | birth_signature={int((ev['event_class']=='birth_signature').sum())} "
          f"salience_template={int((ev['event_class']=='salience_template').sum())}")
    print("\n--- event_class × event_type 内訳 ---")
    print(ev.groupby(["event_class", "event_type"]).size().to_dict())
    print("\n--- event_class 別 cid 分布 (n_core別) ---")
    for ec in ["birth_signature", "salience_template"]:
        s = ev[ev["event_class"] == ec]
        per = {int(nc): int(s[s["n_core"] == nc]["cid"].nunique()) for nc in [2, 3, 4, 5]}
        print(f"  {ec}: cid={s['cid'].nunique()} events={len(s)} | cid/n_core={per}")
    print("\n--- 欠損構造 ---")
    print(f"  pre_context_id null={int(ev['pre_context_id'].isna().sum())} "
          f"post_context_id null={int(ev['post_context_id'].isna().sum())}")
    print(f"  二系統 重なり(同一cid,t が両class)={ev.duplicated(['cid','t'], keep=False).sum()}")
    print("\n--- 素の分布 (event_class別・n_core別) θ_resultant ---")
    for ec in ["birth_signature", "salience_template"]:
        s = ev[ev["event_class"] == ec]
        line = f"  {ec}:"
        for nc in [2, 3, 4, 5]:
            sn = s[s["n_core"] == nc]
            if len(sn):
                line += f" n{nc} θmed={sn['theta_resultant_length'].median():.3f}"
        print(line)
    print("\n--- 健全性 sanity check ---")
    for k, v in hc.items():
        print(f"  {k}: {v}")
    print("\n--- 説明可能性ルーブリック突合 (実装後自己検証) ---")
    for k, v in rub.items():
        print(f"  {k}: {v}")
    allok = all(rub.values()) and hc["health1_birth_all_hosted"]
    print(f"\n  ルーブリック全項目 PASS = {all(rub.values())} | 健全性1 = {hc['health1_birth_all_hosted']}")
    print(f"\n出力: {OUT}/v1303c_event_ledger_seed0.parquet")


if __name__ == "__main__":
    main()
