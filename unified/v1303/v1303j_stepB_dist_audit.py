# 観察対象注釈ブロック（v1303j Step B distribution audit）
# 系の別: 同系内（同一 seed0 v105 main_v2・同一物理・同一時間軸・cross-cid は同系内）。異系対応でない（F型回避）。
# 過去成功との照合: Step A selector（正規化 salience roulette）/ v12.1 ルーレット / v106 read-only 後処理。
# 過去失敗の回避: A 神の手（cutoff/閾値なし・uniform 比較で判定）/ B 物理介入（read-only・書込 v1303j 配下のみ）/
#                 C 自己成就（uniform baseline 比較・sampler を exact で検証）/ D 平均化（n_core 層化）/
#                 #11 合成（eye ごと別・合成 pull しない）/ L 意味盛り（"注意した" と書かない）。
# 版規律: v1303k を作らない。本作業は v1303j Step B。投影/子ESDE/Atom は v1303 非対象（次版 stub）。
# insight: 選択分布は正規化 salience で厳密（p=clip(sal,0)/Σ・RNG 不要）。many-RNG は sampler 検証と分散図示のみ。

import sys, os
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v1303j_selector import build_alive_grid, attach_values, EYES, EYE_LABEL, SEED, OUT  # Step A 資産を再利用

SELECTOR_RNG_SEED = 1303
N_RNG = 200
EYES_U = EYES + ["uniform"]


def log(m):
    print(f"[v1303j-B] {m}", flush=True)


# ---------------------------------------------------------------------------
# 1. exact 選択確率 p[eye,cid,t] = clip(sal,0)/Σ_eligible（RNG 不要・決定論）
# ---------------------------------------------------------------------------
def attach_exact_p(grid):
    alive_ct = grid.groupby("t")["cid"].transform("size")
    for eye in EYES:
        v = grid[eye].clip(lower=0)                     # NaN は eligible 外（保持）
        s = v.groupby(grid["t"]).transform("sum")       # 各 t の eligible clip 和（NaN skip）
        p = (v / s).fillna(0.0)
        fb = s.fillna(0.0) == 0.0                        # 全 NaN or 全 0 → uniform fallback（alive 全体）
        p = p.mask(fb, 1.0 / alive_ct)
        grid["p_" + eye] = p
    grid["p_uniform"] = 1.0 / alive_ct
    # 検証: 各 t で Σ_cid p == 1
    for eye in EYES_U:
        chk = grid.groupby("t")["p_" + eye].sum()
        assert np.allclose(chk, 1.0), f"{eye}: per-t p が 1 に正規化されていない"
    return grid


# ---------------------------------------------------------------------------
# 2. exact 選択頻度 freq[eye,cid] = mean_t p（Σ_cid = 1）+ cid 属性
# ---------------------------------------------------------------------------
def selection_dist(grid):
    T = grid["t"].nunique()
    # cid 属性（n_core_bin は代表値・bgen_level は cid 定数の高/低）
    cid_ncbin = grid.groupby("cid")["n_core_bin"].agg(lambda s: s.mode().iloc[0])
    cid_bgen = grid.groupby("cid")["bgen_pct"].first()
    bgen_med = cid_bgen.dropna().median()
    rows = []
    for eye in EYES_U:
        fr = grid.groupby("cid")["p_" + eye].sum() / T
        for cid, f in fr.items():
            rows.append({"eye": eye, "cid": int(cid), "freq": float(f),
                         "n_core_bin": cid_ncbin.get(cid),
                         "bgen_level": ("high" if (pd.notna(cid_bgen.get(cid)) and cid_bgen.get(cid) >= bgen_med)
                                        else ("low" if pd.notna(cid_bgen.get(cid)) else "no_bgen"))})
    dist = pd.DataFrame(rows)
    assert np.allclose(dist.groupby("eye")["freq"].sum(), 1.0), "freq が eye ごと 1 に集約されていない"
    dist.to_parquet(OUT / f"v1303j_stepB_selection_dist_seed{SEED}.parquet")
    log(f"selection_dist saved (T={T})")
    return dist


# ---------------------------------------------------------------------------
# 3. concentration / entropy（exact・各 eye）
# ---------------------------------------------------------------------------
def concentration(dist):
    rows = []
    for eye in EYES_U:
        f = dist[dist["eye"] == eye]["freq"].to_numpy()
        f = f[f > 0]
        H = -(f * np.log(f)).sum()
        eff = float(np.exp(H))
        fs = np.sort(f)[::-1]
        rows.append({"eye": eye, "label": EYE_LABEL.get(eye, "uniform baseline"),
                     "entropy": round(float(H), 4), "effective_cid_count": round(eff, 1),
                     "inv_sumsq": round(float(1.0 / (f ** 2).sum()), 1),
                     "top1_cum": round(float(fs[:1].sum()), 4),
                     "top5_cum": round(float(fs[:5].sum()), 4),
                     "top10_cum": round(float(fs[:10].sum()), 4),
                     "nonzero_cid": int((dist[dist["eye"] == eye]["freq"] > 0).sum())})
    con = pd.DataFrame(rows)
    con.to_parquet(OUT / f"v1303j_stepB_concentration_seed{SEED}.parquet")
    log("concentration saved")
    return con


# ---------------------------------------------------------------------------
# 4. eye 間選択分布相関（distinct 性の本命・単発一致率でなく分布相関）
# ---------------------------------------------------------------------------
def dist_corr(dist, grid):
    # marginal（時間平均 freq の cid 上相関）。⚠ 露出時間支配で salience が洗い流される D 型の罠を含むため
    #  「本体」でなく参考として出す（下の per-t が本体）。
    wide = dist.pivot(index="cid", columns="eye", values="freq").fillna(0.0)
    M = wide[EYES_U].corr().round(4)
    out = M.reset_index().melt(id_vars="eye", var_name="eye2", value_name="marginal_dist_corr")
    out.to_parquet(OUT / f"v1303j_stepB_dist_corr_seed{SEED}.parquet")
    log("dist_corr (marginal・参考) saved")
    return M


def per_t_metrics(grid):
    """本体 instrument。marginal は D 型平均化で潰れるため per-t で distinct 性と珍しさ選択を測る。"""
    T = grid["t"].nunique()
    # (a) per-t の distinct 性: eye ペアの per-t 分布相関を t 平均（uniform は定数ゆえ相関対象外）
    tgroups = list(grid.groupby("t"))
    pairs = [(a, b) for i, a in enumerate(EYES) for b in EYES[i + 1:]]
    acc = {f"{a}×{b}": [] for a, b in pairs}
    # (b) per-t の珍しさ選択(C型): uniform からの乖離 = KL(p_eye||uniform)=log(alive)-H(p) と effective count
    kl = {e: [] for e in EYES}
    eff = {e: [] for e in EYES}
    for _, g in tgroups:
        ac = g["cid"].shape[0]
        logac = np.log(ac)
        cols = {e: g["p_" + e].to_numpy() for e in EYES}
        for e in EYES:
            p = cols[e]; pnz = p[p > 0]
            H = -(pnz * np.log(pnz)).sum()
            kl[e].append(logac - H)          # 0=uniform と同じ, 大=珍しさが集中選択
            eff[e].append(np.exp(H))          # per-t effective selected cid 数
        for a, b in pairs:
            va, vb = cols[a], cols[b]
            if va.std() > 0 and vb.std() > 0:
                acc[f"{a}×{b}"].append(np.corrcoef(va, vb)[0, 1])
    pert_corr = pd.DataFrame([{"pair": k, "mean_per_t_corr": round(float(np.mean(v)), 4)} for k, v in acc.items()])
    pert_eye = pd.DataFrame([{
        "eye": e, "label": EYE_LABEL.get(e, e),
        "mean_per_t_KL_from_uniform": round(float(np.mean(kl[e])), 4),
        "mean_per_t_effective_count": round(float(np.mean(eff[e])), 2),
    } for e in EYES])
    # uniform の基準値（KL=0・effective=mean alive）を付記
    mean_alive = float(np.mean([g.shape[0] for _, g in tgroups]))
    pert_eye = pd.concat([pert_eye, pd.DataFrame([{
        "eye": "uniform", "label": "uniform baseline",
        "mean_per_t_KL_from_uniform": 0.0, "mean_per_t_effective_count": round(mean_alive, 2)}])],
        ignore_index=True)
    pert_corr.to_parquet(OUT / f"v1303j_stepB_pert_corr_seed{SEED}.parquet")
    pert_eye.to_parquet(OUT / f"v1303j_stepB_pert_eye_seed{SEED}.parquet")
    log("per_t metrics saved (本体)")
    return pert_corr, pert_eye


# ---------------------------------------------------------------------------
# 5. persist_thetapct は duration lens か（pulled vs eligible segment_length）
# ---------------------------------------------------------------------------
def persist_duration(grid):
    m = grid[(grid["p_persist_thetapct"] > 0) & grid["segment_length"].notna()].copy()
    w = m["p_persist_thetapct"].to_numpy()
    L = m["segment_length"].to_numpy(dtype=float)
    pulled_mean = float((w * L).sum() / w.sum())          # 選択確率重みの期待 segment_length
    eligible_mean = float(L.mean())                        # eligible 一様
    corr_p_len = float(np.corrcoef(w, L)[0, 1]) if w.std() > 0 and L.std() > 0 else np.nan
    res = pd.DataFrame([{
        "n_rows": int(len(m)),
        "pulled_weighted_mean_seglen": round(pulled_mean, 3),
        "eligible_mean_seglen": round(eligible_mean, 3),
        "pulled_over_eligible": round(pulled_mean / eligible_mean, 4) if eligible_mean else np.nan,
        "eligible_median_seglen": round(float(np.median(L)), 1),
        "eligible_max_seglen": round(float(L.max()), 1),
        "corr_pullprob_seglen": round(corr_p_len, 4),
    }])
    res.to_parquet(OUT / f"v1303j_stepB_persist_duration_seed{SEED}.parquet")
    log("persist_duration saved")
    return res


# ---------------------------------------------------------------------------
# 6. many-RNG 確認（sampler が exact に収束するか・単発分散）
# ---------------------------------------------------------------------------
def many_rng(grid, dist):
    rng = np.random.default_rng(SELECTOR_RNG_SEED)
    T = grid["t"].nunique()
    max_cid = int(grid["cid"].max()) + 1
    rows = []
    single_var = []
    for eye in EYES_U:
        counts = np.zeros(max_cid)
        pcol = "p_" + eye
        for _, g in grid.groupby("t"):
            p = g[pcol].to_numpy()
            cids = g["cid"].to_numpy()
            idx = rng.choice(len(cids), size=N_RNG, p=p)
            bc = np.bincount(idx, minlength=len(cids))
            np.add.at(counts, cids, bc)
            # 単発分散: この t の 200 draw が何種類の cid に散ったか
            single_var.append({"eye": eye, "t": int(g["t"].iloc[0]),
                               "distinct_in_Ndraw": int(np.unique(idx).size)})
        freq_emp = counts / (N_RNG * T)
        fe = dist[dist["eye"] == eye].set_index("cid")["freq"]
        emp_series = pd.Series(freq_emp, index=np.arange(max_cid))
        common = fe.index
        c = float(np.corrcoef(emp_series.loc[common].to_numpy(), fe.loc[common].to_numpy())[0, 1])
        maxdiff = float(np.abs(emp_series.loc[common].to_numpy() - fe.loc[common].to_numpy()).max())
        rows.append({"eye": eye, "corr_emp_exact": round(c, 5), "max_abs_diff": round(maxdiff, 5),
                     "mean_distinct_in_Ndraw": round(float(
                         pd.DataFrame([s for s in single_var if s["eye"] == eye])["distinct_in_Ndraw"].mean()), 2)})
    mr = pd.DataFrame(rows)
    mr.to_parquet(OUT / f"v1303j_stepB_manyrng_seed{SEED}.parquet")
    log(f"many_rng saved (N={N_RNG})")
    return mr


# ---------------------------------------------------------------------------
# 7. 観察事実報告（判定なし #12）
# ---------------------------------------------------------------------------
def write_observation(dist, con, M, pert_corr, pert_eye, dur, mr, grid):
    L = []
    L.append("# v1303j Step B 観察事実報告（distribution audit・seed0・read-only・判定なし #12）\n")
    L.append("*作成*: 2026-07-01、Code A。**事実のみ・success/fail を置かない。正式採用 eye / persist 命名 / peer 採否 / bgen 読み は Taka 領域。**\n")
    L.append("## 0. insight の実装 + instrument の正直な訂正")
    L.append("- 選択確率 p[eye,cid,t]=clip(sal,0)/Σ_eligible を厳密算出（RNG 不要）。freq[eye,cid]=mean_t p（Σ_cid=1）。")
    L.append("- 単発 chance 支配（Step A の弱点）は厳密値ゆえ消える。many-RNG は sampler 検証と分散図示のみ。")
    L.append("- **⚠ Code A の正直な訂正**: 設計 §3.3 が「本体」とした **marginal（時間平均 freq）分布相関は D 型（平均化）の罠を含む**。")
    L.append("  freq=mean_t p は各 cid の露出時間（何ステップ pool に居たか）に支配され salience 形状が洗い流されるため、")
    L.append("  θ/link/peer が **全て uniform と ~0.99**（下表）になり distinct 性も珍しさ選択も測れない。**本体は per-t（§2b/§2c）に移す**。\n")

    L.append("## 1. concentration / entropy（marginal・exact・各 eye）")
    L.append("```"); L.append(con.to_string(index=False)); L.append("```")
    L.append("- bgen は per-cid 定数ゆえ低 entropy / 少 effective count＝背景静的優先度（degenerate は性質・「失敗」と書かない）。")
    L.append("- 注: この marginal concentration も露出時間の影響を受ける（θ/link/peer の eff+count が uniform 111.8 に近い）。\n")

    L.append("## 2a. marginal eye 間分布相関（⚠ 参考のみ・D 型で潰れる）")
    L.append("```"); L.append(M.to_string()); L.append("```")
    L.append("- 全ペア~0.99・now×uniform 0.99＝露出時間支配で salience が消えた状態。**distinct 判定に使わない**。\n")

    L.append("## 2b. per-t eye 間分布相関（本体・distinct 性・単発一致率でない）")
    L.append("```"); L.append(pert_corr.to_string(index=False)); L.append("```")
    L.append("- per-t では 1 未満に割れる＝目は per-t で distinct（marginal で消えていたもの）。読み（採否）は Taka。\n")

    L.append("## 2c. per-t 珍しさ選択（本体・C 型・uniform からの乖離）")
    L.append("```"); L.append(pert_eye.to_string(index=False)); L.append("```")
    L.append("- mean_per_t_KL_from_uniform: 0=uniform と同じ（珍しさが選んでいない）・大=per-t で集中選択。")
    L.append("- effective_count が uniform 基準より小さいほど per-t で珍しさが選択を絞っている。読みは Taka。\n")

    L.append("## 3. persist_thetapct は duration lens か（pulled vs eligible segment_length）")
    L.append("```"); L.append(dur.to_string(index=False)); L.append("```")
    L.append("- segment_length を salience に入れていないのに `pulled_over_eligible`>1 かつ `corr_pullprob_seglen`>0 なら長 segment 過剰選択＝duration lens 寄り、")
    L.append("  ≈1 / ≈0 なら短 segment 母集団多数＝『Archive 内 θ-percentile lens』寄り。命名は Taka（名前を間違えなければ問題ない）。\n")

    L.append("## 4. many-RNG 確認（sampler 検証 + 単発分散・N=200）")
    L.append("```"); L.append(mr.to_string(index=False)); L.append("```")
    L.append("- corr_emp_exact ≈ 1.0 かつ max_abs_diff 小 ＝ roulette sampler は exact 分布に収束（バグなし）。")
    L.append("- mean_distinct_in_Ndraw ＝ 200 draw が何種類の cid に散るか（単発を唯一の注意と読まない定量・§10-4）。\n")

    L.append("## 5. 選択分布の層化（n_core 別・bgen 高低別）")
    for eye in ["now_theta", "peer_theta", "link_rarity", "persist_thetapct", "bgen_pct"]:
        d = dist[dist["eye"] == eye]
        by_nc = d.groupby("n_core_bin")["freq"].sum().round(3).to_dict()
        by_bg = d.groupby("bgen_level")["freq"].sum().round(3).to_dict()
        L.append(f"- {eye}: n_core別 {by_nc} / bgen高低別 {by_bg}")
    L.append("")

    L.append("## 6. 言える / 言えない")
    L.append("- **言える**: 目ごとの選択分布・eye 間分布相関・concentration・persist の segment_length 比較を厳密に出した（read-only・seed0）。")
    L.append("- **言えない**: 「ESDE が注意した / 自律選択した / どの eye が正しい」。正式 eye 採否・persist 命名・peer 採否は Taka。")
    L.append("- 出口＝正式 eye 選定材料 → Taka 決定 → v1303 Final で attention output schema 固定 → v1303 クローズ。投影/子ESDE/Atom は v1304+ stub。\n")
    L.append("## 7. 次段")
    L.append("- smoke seed0 まで。main・複数 seed には進まない。Taka の正式 eye 決定後に v1303 Final。")

    (Path(__file__).resolve().parent / "v1303j_stepB_observation.md").write_text("\n".join(L), encoding="utf-8")
    log("stepB_observation.md written")


def main():
    grid = build_alive_grid()
    grid = attach_values(grid)
    grid = attach_exact_p(grid)
    dist = selection_dist(grid)
    con = concentration(dist)
    M = dist_corr(dist, grid)
    pert_corr, pert_eye = per_t_metrics(grid)
    dur = persist_duration(grid)
    mr = many_rng(grid, dist)
    write_observation(dist, con, M, pert_corr, pert_eye, dur, mr, grid)
    log("DONE (Step B seed0). smoke 後停止・承認待ち。")


if __name__ == "__main__":
    main()
