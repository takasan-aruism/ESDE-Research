#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# v1303d Step B — 研究者手本(θ高同期)を ESDE 内在量で置換できるか：
#   手本(salience θ-high) と内生的珍しさ候補の「重なり」を cid内percentile + shuffle比で
#   read-only に読み、離脱候補を選別する（後処理のみ・再走/write-back なし）
#
# 規律宣言（Code A / 失敗記録12型・v1303d 設計）
#  1. 読: v1303a ledger + v1303c event_ledger(salience行) READ-ONLY。
#     書: unified/v1303/outputs/v1303d/ のみ。write-back しない（B型）。
#  2. 手本→離脱(A型/#CW7): 内生候補は ESDE 内在量に限る。**合成指標を作らない**(神の手)。
#     θ手本を内生量で置換できる候補を探す＝離脱の道筋。但し「外せた」と言わず「候補を読めた」まで。
#  3. 失敗型回避:
#     C型 → 重なりは絶対値でなく shuffle比(full + circular)で測る。θ系候補の重なりは
#            同義反復ゆえ離脱証拠に弱い(secondary)。予測を当てにいかない。
#     D型 → 内生候補も cid内 percentile 上位5%(絶対値閾値の n2偏り回避)。cid個別・n_core別・
#            B_Gen層別(数値B_Genを持つ45cidのみ・eligible明示)。全CID平均の重なり率を出さない。
#     #11 → 候補を合成しない(候補別テーブル・両方向)。θ系/非θ系を混ぜない。C/Q(window)は
#            時点トリガーにせず文脈属性として横に添える(Atom/sim step10と粒度混同しない)。
#     L型 → Atom 意味解釈しない(切替の有無)。乾いた操作定義。
#     #12/J → (a)/(a')/(b)判定しない。観察事実のみ。seed0 のみ。F型 → anchor=v105_v2。
#  4. 説明可能性ルーブリック(下 EXPLAIN)準拠。実装後 verify_rubric() で自己検証。
#  判定は Web Claude / Taka。
# ─────────────────────────────────────────────────────────────────────────────
import numpy as np
import pandas as pd
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LEDGER = REPO / "unified" / "v1303" / "outputs" / "v1303_ledger_seed0.parquet"
EVENTL = REPO / "unified" / "v1303" / "outputs" / "v1303c" / "v1303c_event_ledger_seed0.parquet"
OUT = REPO / "unified" / "v1303" / "outputs" / "v1303d"
OUT.mkdir(parents=True, exist_ok=True)

PCTL = 0.95          # cid内 上位5%（手本・候補とも同じ土俵・D型回避）
N_SHUF = 200
SEED = 42
MIN_POINTS = 30

# 内生候補の三分類（C/Q は時点トリガーから除外＝window粒度の偽スパイク回避・§1.2）
PRIMARY = ["atom_switch", "sim_delta_high"]       # 非θ系・離脱の主証拠
SECONDARY = ["theta_jump_high", "theta_maddt_high"]  # θ系・補助(同義反復ゆえ弱い)
CANDIDATES = PRIMARY + SECONDARY

EXPLAIN = {
    "theta_high_idx": ("HIGH", "手本=各cidのθ_resultant cid内q95値以上の時点index(=v1303c salience)"),
    "atom_switch": ("HIGH", "rank_1_atom[i]!=rank_1_atom[i-1] の時点(二値イベント・percentile化しない)。atom固定cidは候補なし(eligibleから除外)"),
    "sim_delta_high": ("HIGH", "|Δrank_1_sim| の cid内q95値以上の時点(上位5%)"),
    "theta_jump_high": ("HIGH", "|Δθ_resultant| の cid内q95値以上の時点(θ系・補助)"),
    "theta_maddt_high": ("HIGH", "|θ-cid中央値|/cid_MAD の cid内q95値以上(MAD-DT的・θ系・補助)"),
    "overlap_exact": ("HIGH", "|theta_high ∩ candidate| 同一時点の一致数"),
    "overlap_pm1": ("HIGH", "|theta_high ∩ (candidate±1 step10)| 近傍一致数(exactと分離)"),
    "dir_theta_to_cand / dir_cand_to_theta": ("HIGH", "両方向の被覆率(非対称を畳まない)"),
    "ratio_full / ratio_circular": ("MEDIUM", "観測overlap / shuffle null平均。full=時間順破壊(局所構造壊す)・circular=位相ずらし(局所構造保つ)。>1で偶然超え"),
    "bgen_stratum": ("MEDIUM", "数値B_Gen(45cid)を中央値で high/low 層別。unformed 183cid は除外(eligible_bgen明示)"),
}


def cid_high_idx(vals, pctl=PCTL):
    """cid内 q95値以上の時点index集合（上位5%・値しきい値方式＝v1303cと同じ）。"""
    v = np.asarray(vals, float)
    if len(v) == 0:
        return set()
    thr = np.quantile(v, pctl)
    return set(np.where(v >= thr)[0].tolist())


def candidate_idx(name, atoms, sim, theta):
    n = len(atoms)
    if name == "atom_switch":
        return set((np.where(atoms[1:] != atoms[:-1])[0] + 1).tolist())
    if name == "sim_delta_high":
        d = np.abs(np.diff(sim))
        idx = cid_high_idx(d)
        return set((np.array(sorted(idx)) + 1).tolist()) if idx else set()
    if name == "theta_jump_high":
        d = np.abs(np.diff(theta))
        idx = cid_high_idx(d)
        return set((np.array(sorted(idx)) + 1).tolist()) if idx else set()
    if name == "theta_maddt_high":
        med = np.median(theta)
        mad = np.median(np.abs(theta - med)) + 1e-9
        z = np.abs(theta - med) / mad
        return cid_high_idx(z)
    return set()


def overlap_counts(A, B, n, w=1):
    """A,B は index集合。exact と ±w 近傍の一致、両方向被覆率。"""
    exact = len(A & B)
    Bexp = set()
    for b in B:
        for dd in range(-w, w + 1):
            x = b + dd
            if 0 <= x < n:
                Bexp.add(x)
    Aexp = set()
    for a in A:
        for dd in range(-w, w + 1):
            x = a + dd
            if 0 <= x < n:
                Aexp.add(x)
    pm1 = len(A & Bexp)
    dir_A_to_B = len(A & Bexp) / len(A) if A else np.nan   # Aの各点の近傍にBがある率
    dir_B_to_A = len(B & Aexp) / len(B) if B else np.nan
    return exact, pm1, dir_A_to_B, dir_B_to_A


def shuffle_null(theta_high, cand, n, rng, mode):
    """手本(theta_high)固定で候補側だけ shuffle し overlap_pm1 の null を返す。"""
    k = len(cand)
    if k == 0:
        return np.nan
    vals = []
    for _ in range(N_SHUF):
        if mode == "full":
            pos = set(rng.choice(n, size=k, replace=False).tolist())
        else:  # circular: 候補の相対間隔を保ち位相だけずらす
            off = int(rng.randint(1, n))
            pos = set(((np.array(sorted(cand)) + off) % n).tolist())
        _, pm1, _, _ = overlap_counts(theta_high, pos, n)
        vals.append(pm1)
    return float(np.mean(vals))


def main():
    df = pd.read_parquet(LEDGER)
    h = df[df["phys_core_status"].eq("hosted_available")].copy().sort_values(["cid", "t"])
    h["bgen"] = pd.to_numeric(h["v11_b_gen"], errors="coerce")
    rng = np.random.RandomState(SEED)

    rows = []
    for cid, g in h.groupby("cid"):
        g = g.sort_values("t").reset_index(drop=True)
        n = len(g)
        if n < MIN_POINTS:
            continue
        atoms = g["rank_1_atom"].values
        sim = g["rank_1_sim"].values.astype(float)
        theta = g["core_node_theta_resultant_length"].values.astype(float)
        nc = int(g["n_core"].iloc[0]) if not pd.isna(g["n_core"].iloc[0]) else -1
        bgen = g["bgen"].iloc[0]
        theta_high = cid_high_idx(theta)  # 手本

        for name in CANDIDATES:
            cand = candidate_idx(name, atoms, sim, theta)
            eligible = (name != "atom_switch") or (len(set(atoms)) > 1)
            rec = dict(cid=int(cid), n_core=nc, n_points=n,
                       bgen=float(bgen) if not pd.isna(bgen) else np.nan,
                       candidate=name,
                       cls="primary" if name in PRIMARY else "secondary",
                       eligible=bool(eligible),
                       n_theta_high=len(theta_high), n_candidate=len(cand))
            if not eligible or len(cand) == 0:
                rec.update(overlap_exact=np.nan, overlap_pm1=np.nan,
                           dir_theta_to_cand=np.nan, dir_cand_to_theta=np.nan,
                           ratio_full=np.nan, ratio_circular=np.nan)
            else:
                ex, pm1, d_tc, d_ct = overlap_counts(theta_high, cand, n)
                nf = shuffle_null(theta_high, cand, n, rng, "full")
                ncirc = shuffle_null(theta_high, cand, n, rng, "circular")
                rec.update(overlap_exact=ex, overlap_pm1=pm1,
                           dir_theta_to_cand=d_tc, dir_cand_to_theta=d_ct,
                           ratio_full=(pm1 / nf) if nf and nf > 0 else np.nan,
                           ratio_circular=(pm1 / ncirc) if ncirc and ncirc > 0 else np.nan)
            rows.append(rec)

    res = pd.DataFrame(rows)
    # B_Gen 層別（数値B_Genを持つcidのみ・eligible明示）
    bg_cids = res.dropna(subset=["bgen"])["cid"].unique()
    bg_med = res.dropna(subset=["bgen"]).groupby("cid")["bgen"].first().median()
    res["bgen_stratum"] = np.where(res["bgen"].isna(), "unformed",
                                   np.where(res["bgen"] >= bg_med, "high", "low"))
    res.to_parquet(OUT / "v1303d_overlap_seed0.parquet", index=False)

    # ── 観察事実プリント ──────────────────────────────────────────────────
    print("=== v1303d 手本(θ高同期) vs 内生候補 重なり (候補別・cid内percentile・shuffle比・判定なし) ===")
    print(f"対象cid={res['cid'].nunique()} | shuffle={N_SHUF}(full+circular) seed={SEED}")
    print(f"eligible_cid: atom_switch={int(res[(res.candidate=='atom_switch')&res.eligible]['cid'].nunique())}/228 "
          f"(atom固定6cidは候補なしで分離) | 数値B_Gen cid={len(bg_cids)}/228")

    print("\n--- 候補別 重なり ratio (ratio>1=偶然超え・circular=局所構造保つ厳しい対照) cid中央値 ---")
    for name in CANDIDATES:
        s = res[(res.candidate == name) & res.eligible]
        print(f" [{('PRI' if name in PRIMARY else 'SEC')}] {name:16s}: "
              f"ratio_full med={s['ratio_full'].median():.2f} ratio_circular med={s['ratio_circular'].median():.2f} | "
              f">circular1.0 の cid={int((s['ratio_circular']>1).sum())}/{len(s)} | "
              f"exact med={s['overlap_exact'].median():.0f} pm1 med={s['overlap_pm1'].median():.0f}")

    print("\n--- 両方向(非対称) 被覆率 cid中央値 ---")
    for name in CANDIDATES:
        s = res[(res.candidate == name) & res.eligible]
        print(f" {name:16s}: θ→候補={s['dir_theta_to_cand'].median():.3f} 候補→θ={s['dir_cand_to_theta'].median():.3f}")

    # 【コード自己検証で判明】集約中央値は n_core 異質性を潰す(θ_maddt cid=0=8.17 vs 中央0)。
    # n2はθ-high≈3点/候補≈4点でイベント疎(overlap測定不能)。→ 全候補 per-n_core + 十分subset で出す。
    print("\n--- n_core別 ratio_circular (全候補・中央値) ※n2は疎で参考値 ---")
    for name in CANDIDATES:
        line = f" [{('PRI' if name in PRIMARY else 'SEC')}] {name:16s}:"
        for nc in [2, 3, 4, 5]:
            s = res[(res.candidate == name) & res.eligible & (res.n_core == nc)]
            if len(s):
                line += f" n{nc}={s['ratio_circular'].median():.2f}"
        print(line)

    print("\n--- イベント十分subset (n_theta_high>=10 & n_candidate>=10) の ratio_circular ---")
    suf = res[(res.n_theta_high >= 10) & (res.n_candidate >= 10) & res.eligible]
    print(f"  対象cid(候補横断)={suf['cid'].nunique()} (大半は n4/n5)")
    for name in CANDIDATES:
        s = suf[suf.candidate == name]
        if len(s):
            print(f"   [{('PRI' if name in PRIMARY else 'SEC')}] {name:16s}: "
                  f"ratio_circular med={s['ratio_circular'].median():.2f} "
                  f">1.0 cid={int((s['ratio_circular']>1).sum())}/{len(s)} "
                  f"| θ→候補={s['dir_theta_to_cand'].median():.3f} 候補→θ={s['dir_cand_to_theta'].median():.3f}")

    print("\n--- B_Gen層別 ratio_circular (primary・数値B_Gen 45cid) ---")
    for name in PRIMARY:
        line = f" {name:16s}:"
        for st in ["low", "high"]:
            s = res[(res.candidate == name) & res.eligible & (res.bgen_stratum == st)]
            if len(s):
                line += f" {st}(n={s['cid'].nunique()})={s['ratio_circular'].median():.2f}"
        print(line)

    # ── 健全性 sanity check ───────────────────────────────────────────────
    print("\n--- 健全性 sanity check (主題の出口にしない) ---")
    print(f"  健全性3 eligible: atom_switch eligible={int(res[(res.candidate=='atom_switch')&res.eligible]['cid'].nunique())} "
          f"/ atom固定(候補なし)={int(res[(res.candidate=='atom_switch')&(~res.eligible)]['cid'].nunique())}")
    print(f"  健全性2 B_Gen層別 eligible_bgen_cid={len(bg_cids)} (unformed 183除外)")

    # ── 説明可能性ルーブリック 実装後突合 ─────────────────────────────────
    rub = verify_rubric(res, h)
    print("\n--- 説明可能性ルーブリック突合 (実装後自己検証) ---")
    for k, v in rub.items():
        print(f"  {k}: {v}")
    print(f"\n  ルーブリック全項目 PASS = {all(rub.values())}")
    print(f"\n出力: {OUT}/v1303d_overlap_seed0.parquet")


def verify_rubric(res, h):
    chk = {}
    # 手本θ-high の数は v1303c salience と cid単位で整合するはず(同じ q95 上位5%定義)
    ev = pd.read_parquet(EVENTL)
    sal_per_cid = ev[ev.event_class == "salience_template"].groupby("cid").size()
    th_per_cid = res.groupby("cid")["n_theta_high"].first()
    common = th_per_cid.index.intersection(sal_per_cid.index)
    chk["theta_high_matches_v1303c_salience"] = bool(
        (th_per_cid.loc[common] == sal_per_cid.loc[common]).mean() > 0.99)
    # atom固定cid は atom_switch を eligible=False にしているか
    au = h.groupby("cid")["rank_1_atom"].nunique()
    fixed = set(au[au == 1].index.tolist())
    asw = res[res.candidate == "atom_switch"]
    chk["atom_fixed_cids_ineligible"] = bool(
        (~asw[asw.cid.isin(fixed)]["eligible"]).all()) if fixed else True
    # primary/secondary 分類が正しいか
    chk["primary_secondary_tagged"] = bool(
        set(res[res.cls == "primary"]["candidate"].unique()) == set(PRIMARY) and
        set(res[res.cls == "secondary"]["candidate"].unique()) == set(SECONDARY))
    # C/Q は候補に入っていない(時点トリガーから除外)
    chk["cq_not_a_candidate"] = bool(
        not any(c in res["candidate"].unique() for c in ["C", "Q", "c_delta", "q_delta"]))
    # 合成指標を作っていない(候補列は個別のみ・composite無し)
    chk["no_composite_score"] = bool("composite" not in res.columns and "combined" not in res.columns)
    # eligible でない or 候補0 の行は ratio が NaN(偽の重なりを作っていない)
    bad = res[(~res.eligible) | (res.n_candidate == 0)]
    chk["ineligible_ratio_nan"] = bool(bad["ratio_circular"].isna().all()) if len(bad) else True
    return chk


if __name__ == "__main__":
    main()
