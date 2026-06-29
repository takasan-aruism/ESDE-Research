#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# v1303f Step B1 — v1114型 Now-event を canonical diag_v105_main_v2 ログから
#   t+cid 付き・v1303と同一228 cid宇宙で再構成（後処理のみ・判定なし #12）
#
# 統合方針(Taka確定): v1114=データ源でなく spec/参考実装。別run・退化バグ・t曖昧の443 JSONを
#   使わず、v1114のトリガー設計(6種)を canonical ログに再適用して t付き・228宇宙で再構成。
# v1114 spec(step2a_live_observer.py): 10step chunk毎に cog state の delta検出=
#   cid_birth(新cid)/cid_death(死)/alpha_formation(新α member_cids)/beta_formation/
#   pulse(v10_pulse_count増)/c_conversion(cog.C増)。EWMA+z で発生率異常な trigger だけ記録。
# 本Phase1: 全イベントを再構成(novelty フィルタはかけず)、z は後段で監査列(Comparator前駆体)。
#
# 規律: 読=canonical ログ READ-ONLY/書=outputs/v1303f のみ。物理非書込(B型)。判定せず事実のみ。
#   時間anchor確認済: 全ログ tracking-step域[0,25000]=ledger t と同一原点。pulse等は step10丸め。
#   本スクリプトは再構成+join健全性の検証まで(統合ledgerは Step B2・一括にしない)。
# ─────────────────────────────────────────────────────────────────────────────
import ast
import re
import numpy as np
import pandas as pd
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DIAG = REPO / "developmental" / "v105" / "diag_v105_main_v2"
LEDGER = REPO / "unified" / "v1303" / "outputs" / "v1303_ledger_seed0.parquet"
OUT = REPO / "unified" / "v1303" / "outputs" / "v1303f"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 0


def round10(t):
    return int(np.round(float(t) / 10.0) * 10)


def parse_cids(s):
    """member_cids 文字列を int集合に。'{0, 5}' / '[0,5]' / 'frozenset({0,5})' 等に頑健。"""
    if pd.isna(s):
        return []
    nums = re.findall(r"\d+", str(s))
    return [int(x) for x in nums]


def reconstruct_events():
    led = pd.read_parquet(LEDGER)
    led_cids = set(int(c) for c in led["cid"].unique())
    ev = []

    # cid_birth: ledger 各cidの最初の hosted t（v1303 t空間での誕生）
    birth_t = led.groupby("cid")["t"].min()
    for cid, t in birth_t.items():
        ev.append((int(cid), int(t), "cid_birth"))

    # cid_death: per_subject host_lost_step（ghost化＝v1114のdeath）
    subj = pd.read_csv(DIAG / "subjects" / f"per_subject_seed{SEED}.csv")
    hl = pd.to_numeric(subj["host_lost_step"], errors="coerce")
    for cid, t in zip(subj["cognitive_id"], hl):
        if not pd.isna(t):
            ev.append((int(cid), round10(t), "cid_death"))

    # pulse: pulse_log 各行（t→step10丸め）
    pl = pd.read_csv(DIAG / "pulse" / f"pulse_log_seed{SEED}.csv")
    for cid, t in zip(pl["cid"], pl["t"]):
        ev.append((int(cid), round10(t), "pulse"))

    # alpha_formation / beta_formation: lifecycle event_type=='birth' → member_cids at step
    for name, fn in [("alpha_formation", "integration/alpha_lifecycle_log_seed%d.csv"),
                     ("beta_formation", "integration/beta_lifecycle_log_seed%d.csv")]:
        lc = pd.read_csv(DIAG / (fn % SEED))
        births = lc[lc["event_type"] == "birth"]
        for cids_s, step in zip(births["member_cids"], births["step"]):
            for cid in parse_cids(cids_s):
                ev.append((int(cid), round10(step), name))

    # c_conversion: c_trajectory で C_at_window_end が前window比 増えた (cid,window)
    ct = pd.read_csv(DIAG / "balance" / f"c_trajectory_seed{SEED}.csv").sort_values(["cid", "window"])
    ct["C_prev"] = ct.groupby("cid")["C_at_window_end"].shift(1).fillna(0)
    inc = ct[ct["C_at_window_end"] > ct["C_prev"]]
    for cid, step in zip(inc["cid"], inc["step_at_window_end"]):
        ev.append((int(cid), round10(step), "c_conversion"))

    df = pd.DataFrame(ev, columns=["cid", "t", "trigger"])
    df["seed"] = SEED
    df["in_ledger_universe"] = df["cid"].isin(led_cids)
    return df, led


def main():
    df, led = reconstruct_events()
    # join健全性: (cid,t) が ledger hosted行に一致するか
    led_key = set(zip((int(c) for c in led["cid"]), (int(t) for t in led["t"])))
    df["joins_hosted_row"] = [(c, t) in led_key for c, t in zip(df["cid"], df["t"])]
    df.to_parquet(OUT / "v1303f_now_events_seed0.parquet", index=False)

    print("=== v1303f Step B1: Now-event 再構成 (canonical由来・t付き・228宇宙・判定なし) ===")
    print(f"総イベント={len(df)} | cid={df['cid'].nunique()} | t範囲[{df['t'].min()},{df['t'].max()}]")
    print("\n--- (健全性0) CID宇宙: 全イベントが v1303 ledger の228宇宙内か(別run混入なし) ---")
    print(f"  in_ledger_universe: True={int(df['in_ledger_universe'].sum())}/{len(df)} "
          f"(False={int((~df['in_ledger_universe']).sum())}=宇宙外なら異常)")
    print("\n--- trigger別 件数 + (健全性1)hosted行へのjoin率 ---")
    for trig, g in df.groupby("trigger"):
        jr = g["joins_hosted_row"].mean()
        print(f"  {trig:16s}: {len(g):5d}件 | hosted_join={jr:.3f} | cid={g['cid'].nunique()}")
    print("\n--- join しない理由の切り分け(cid_death/c_conversionは非hosted時点が正常) ---")
    nojoin = df[~df["joins_hosted_row"]]
    print(f"  join しない={len(nojoin)} | trigger内訳={nojoin['trigger'].value_counts().to_dict()}")
    print("  (cid_death=ghost化時点ゆえ hosted ledger に無いのは正常。pulse/alpha等が大量にjoin外なら要調査)")
    # t丸めズレの確認: join外の pulse がどれだけ近傍±10で拾えるか
    led_key = set(zip((int(c) for c in led["cid"]), (int(t) for t in led["t"])))
    pj = nojoin[nojoin["trigger"] == "pulse"]
    near = sum(1 for c, t in zip(pj["cid"], pj["t"]) if (c, t-10) in led_key or (c, t+10) in led_key)
    print(f"  join外pulse={len(pj)} のうち ±10 で拾える={near} (step10丸めの端数)")
    print(f"\n出力: {OUT}/v1303f_now_events_seed0.parquet")


if __name__ == "__main__":
    main()
