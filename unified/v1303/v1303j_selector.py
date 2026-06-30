# 観察対象注釈ブロック（v1303j selector）
# 系の別: 同系内（全 cid は同一 seed0 v105 main_v2・同一物理・同一時間軸。cross-cid 比較は同系内）。
#         異系対応ではない（v1110-1113 の異 seed node ID inject とは別物・F型回避）。
# 過去成功との照合: v12.1 ルーレット（argmax で潰さず確率比例で引く・レア切り捨てない）/
#                   v1114 pull（押し込むでなく拾う）/ v106 read-only 後処理。
# 過去失敗の回避: A 神の手（cutoff 入れない）/ B 物理介入（read-only・書込は unified/v1303/outputs/v1303j 配下のみ）/
#                 C 自己成就（uniform baseline と比較）/ D 平均化（n_core 保持・潰さない）/
#                 #11 合成（目ごと別系列・合成なし・目間 corr で distinct 確認）/ L 意味盛り（"注意した" と書かない）。
# grid/alive 出所: per_subject_seed0.csv（host_lost_step/birth_window）+ c_trajectory(window->step)。
#                  v1303i グリッドには依存しない（生成元欠落のため）。v1303i は link/peer の値ソースとしてのみ join。
#
# v1303j Step A selector（rev3）。read-only・物理非書込・seed0 のみ・判定なし（#12）。
# emitter の目（瞬間θ/持続θ/link 稀さ/静的 B_Gen/peer-rel θ）を、研究者 cutoff なしで
# ESDE 固有の珍しさが pull する selector の形にする。各 t・各目で独立に珍しさ比例ルーレット 1 本引き。

import numpy as np
import pandas as pd
from pathlib import Path

SEED = 0
SELECTOR_RNG_SEED = 1303  # 固定。RNG 単発軌跡を読みすぎない（rev3 §10-4）。
REPO = Path(__file__).resolve().parents[2]
DIAG = REPO / "developmental" / "v105" / "diag_v105_main_v2"
V1303 = REPO / "unified" / "v1303" / "outputs"
OUT = REPO / "unified" / "v1303" / "outputs" / "v1303j"
OUT.mkdir(parents=True, exist_ok=True)

T_STEP = 10
T_MAX = 25000
WINDOW_STEP = 500  # c_trajectory: 1 window = 500 step（実測・グローバル線形）

# 目の定義（pull 採用 5 目）。global θ / within_cid θ は θ-family 冗長ゆえ落とす（pull しない）。
EYES = ["now_theta", "persist_thetapct", "link_rarity", "bgen_pct", "peer_theta"]
EYE_LABEL = {
    "now_theta": "瞬間θ(f raw theta_resultant_length)",
    "persist_thetapct": "持続θ(e theta_cid_percentile)",
    "link_rarity": "link稀さ非θ(i rarity_internal_link_within_ncore)",
    "bgen_pct": "静的B_Gen(h bgen_pct_in_ncore・per-cid定数)",
    "peer_theta": "peer-rel θ(i rarity_theta_within_ncore・prove-by-trajectory)",
}


def log(m):
    print(f"[v1303j] {m}", flush=True)


# ---------------------------------------------------------------------------
# 1. grid / alive（per_subject + window->step から自前再構築・v1303i 非依存）
# ---------------------------------------------------------------------------
def build_alive_grid():
    ps = pd.read_csv(DIAG / "subjects" / f"per_subject_seed{SEED}.csv")
    ps = ps[["cognitive_id", "birth_window", "host_lost_step", "final_state"]].copy()
    ps = ps.rename(columns={"cognitive_id": "cid"})
    # birth_step = max(0, (birth_window-20)*500)  ＝birth window の開始 step（window<20=logging前生まれは0）
    ps["birth_step"] = ((ps["birth_window"].astype(float) - 20.0) * WINDOW_STEP).clip(lower=0.0)
    # host_lost: NaN は末端まで alive
    ps["host_lost_eff"] = ps["host_lost_step"].fillna(T_MAX + T_STEP)

    t_grid = np.arange(T_STEP, T_MAX + 1, T_STEP)
    rows = []
    for _, r in ps.iterrows():
        cid = int(r["cid"]); b = r["birth_step"]; h = r["host_lost_eff"]
        alive_t = t_grid[(t_grid >= b) & (t_grid < h)]
        if len(alive_t):
            rows.append(pd.DataFrame({"cid": cid, "t": alive_t}))
    grid = pd.concat(rows, ignore_index=True)
    grid = grid.merge(ps[["cid", "final_state", "birth_step", "host_lost_step"]], on="cid", how="left")
    log(f"alive grid: {len(grid)} (cid,t) rows / {grid['cid'].nunique()} cids / "
        f"final_state {ps['final_state'].value_counts().to_dict()}")
    return grid.sort_values("t").reset_index(drop=True)


# ---------------------------------------------------------------------------
# 2. 値ソースを alive grid に join（asof backward / cid broadcast）
# ---------------------------------------------------------------------------
def asof_join(grid, src, col, newname):
    s = src[["cid", "t", col]].dropna(subset=[col]).rename(columns={col: newname}).sort_values("t")
    return pd.merge_asof(grid, s, on="t", by="cid", direction="backward")


def attach_values(grid):
    f = pd.read_parquet(V1303 / "v1303f" / f"v1303f_attention_center_seed{SEED}.parquet")
    fnow = f[f["event_class"] == "now_event"]
    grid = asof_join(grid, fnow, "theta_resultant_length", "now_theta")

    e = pd.read_parquet(V1303 / "v1303e" / f"v1303e_persistence_salience_seed{SEED}.parquet")
    grid = asof_join(grid, e, "theta_cid_percentile", "persist_thetapct")
    # 持続θ の segment タグ（duration lens か確認・rev3 §10-3）
    eseg = e[["cid", "t", "event_segment_id", "segment_length"]].dropna(subset=["event_segment_id"]).sort_values("t")
    grid = pd.merge_asof(grid, eseg, on="t", by="cid", direction="backward")

    i = pd.read_parquet(V1303 / "v1303i" / f"v1303i_dynamic_rarity_seed{SEED}.parquet")
    grid = asof_join(grid, i, "rarity_internal_link_within_ncore", "link_rarity")
    grid = asof_join(grid, i, "rarity_theta_within_ncore", "peer_theta")
    grid = asof_join(grid, i, "rarity_theta_global", "global_theta")        # 参考(pullしない)
    grid = asof_join(grid, i, "rarity_theta_within_cid", "within_cid_theta")  # 参考(pullしない)
    grid = asof_join(grid, i, "n_core", "n_core")
    grid["n_core"] = grid.groupby("cid")["n_core"].ffill().bfill()

    # 静的 B_Gen: per-cid 定数 broadcast（coverage 0.56・44%は値なし=uniform fallback）
    h = pd.read_parquet(V1303 / "v1303h" / f"v1303h_bgen_salience_seed{SEED}.parquet")
    bgen = h.dropna(subset=["bgen_pct_in_ncore"]).groupby("cid")["bgen_pct_in_ncore"].first()
    grid["bgen_pct"] = grid["cid"].map(bgen)
    # 4象限タグ（カテゴリ・pull 次元にしない・record に付ける・rev2 §2）
    quad = h.dropna(subset=["dry_quadrant_candidate"])[["cid", "t", "dry_quadrant_candidate"]].sort_values("t")
    grid = pd.merge_asof(grid, quad, on="t", by="cid", direction="backward")

    grid["n_core_bin"] = grid["n_core"].apply(
        lambda x: "n_unknown" if pd.isna(x) else (f"n{int(x)}" if x <= 5 else "n6+"))
    return grid.sort_values(["t", "cid"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 3. 目間 corr（§3.0 ゲート・auto-drop なし・read-only）
# ---------------------------------------------------------------------------
def eye_corr(grid):
    cols = ["now_theta", "persist_thetapct", "link_rarity", "bgen_pct", "peer_theta",
            "global_theta", "within_cid_theta"]
    C = grid[cols].corr().round(4)
    C.to_parquet(OUT / f"v1303j_eye_corr_seed{SEED}.parquet")
    log("eye-corr matrix saved")
    return C


# ---------------------------------------------------------------------------
# 4. ルーレット 1 本引き（い）＋全順位（あ）＋ uniform baseline
# ---------------------------------------------------------------------------
def run_selector(grid):
    rng = np.random.default_rng(SELECTOR_RNG_SEED)
    pull_rows, rank_rows = [], []
    meta_cols = ["n_core", "n_core_bin", "dry_quadrant_candidate", "event_segment_id", "segment_length"]

    eyes_and_uniform = EYES + ["uniform"]
    for eye in eyes_and_uniform:
        base_eye = "now_theta" if eye == "uniform" else eye  # uniform は値不問・alive 全体から一様
        for t, g in grid.groupby("t", sort=True):
            alive_n = len(g)
            if eye == "uniform":
                elig = g
                vals = np.ones(len(elig))
                fallback = 0
            else:
                elig = g[g[eye].notna()]
                if len(elig) == 0:
                    # 全 NaN → uniform fallback（alive 全体）
                    elig = g
                    vals = np.ones(len(elig)); fallback = 1
                else:
                    vals = np.clip(elig[eye].to_numpy(dtype=float), 0.0, None)
                    if vals.sum() <= 0:
                        vals = np.ones(len(elig)); fallback = 1  # 全 0 → uniform
                    else:
                        fallback = 0
            p = vals / vals.sum()
            cids = elig["cid"].to_numpy()
            picked_idx = rng.choice(len(cids), p=p)
            picked_cid = int(cids[picked_idx])

            # rank_of_picked: salience 降順（1=最大）。uniform/fallback は salience 定義せず NaN。
            prow = elig.iloc[picked_idx]
            if eye == "uniform" or fallback:
                rank_picked = np.nan; sal_picked = np.nan
            else:
                order = elig[eye].rank(ascending=False, method="min")
                rank_picked = float(order.iloc[picked_idx]); sal_picked = float(prow[eye])

            pull_rows.append({
                "eye": eye, "t": int(t), "picked_cid": picked_cid,
                "rank_of_picked": rank_picked, "salience_of_picked": sal_picked,
                "eligible_count": int(len(elig)), "alive_count": int(alive_n),
                "fallback_uniform_flag": int(fallback),
                "n_core": prow["n_core"], "n_core_bin": prow["n_core_bin"],
                "dry_quadrant_candidate": prow.get("dry_quadrant_candidate"),
                "event_segment_id": prow.get("event_segment_id"),
                "segment_length": prow.get("segment_length"),
            })

            # 全順位（あ）: cutoff なし。uniform は順位を出さない。
            if eye != "uniform" and not fallback:
                rr = elig[["cid", eye]].copy()
                rr["rank"] = rr[eye].rank(ascending=False, method="min")
                rr["eye"] = eye; rr["t"] = int(t)
                rr = rr.rename(columns={eye: "salience"})
                rank_rows.append(rr[["eye", "t", "cid", "rank", "salience"]])

    pull = pd.DataFrame(pull_rows)
    pull.to_parquet(OUT / f"v1303j_selector_pull_seed{SEED}.parquet")
    full_rank = pd.concat(rank_rows, ignore_index=True)
    full_rank.to_parquet(OUT / f"v1303j_full_rank_seed{SEED}.parquet")
    log(f"pull series: {len(pull)} (eye,t) rows / full_rank: {len(full_rank)} rows")
    return pull


# ---------------------------------------------------------------------------
# 5. cross-eye 並置（生 percentile 横並び・合成なし・pull なし）
# ---------------------------------------------------------------------------
def cross_eye(grid):
    out = grid[["t", "cid"]].copy()
    for eye in EYES:
        # 各 t で eligible 内 percentile（NaN は NaN のまま）
        out[f"pct_{eye}"] = grid.groupby("t")[eye].rank(pct=True)
    out.to_parquet(OUT / f"v1303j_cross_eye_pct_seed{SEED}.parquet")
    log(f"cross-eye pct: {len(out)} (t,cid) rows")
    return out


# ---------------------------------------------------------------------------
# 6. sanity / baseline（distinct cid・fallback 率・uniform 比較・degenerate 検出）
# ---------------------------------------------------------------------------
def sanity(pull, grid):
    rows = []
    for eye in EYES + ["uniform"]:
        pe = pull[pull["eye"] == eye]
        rows.append({
            "eye": eye, "label": EYE_LABEL.get(eye, "uniform baseline"),
            "n_t": len(pe), "distinct_pulled_cid": pe["picked_cid"].nunique(),
            "fallback_uniform_rate": round(pe["fallback_uniform_flag"].mean(), 4),
            "mean_eligible_count": round(pe["eligible_count"].mean(), 1),
            "mean_alive_count": round(pe["alive_count"].mean(), 1),
        })
    san = pd.DataFrame(rows)
    san.to_parquet(OUT / f"v1303j_sanity_seed{SEED}.parquet")
    log("sanity saved")
    return san


# ---------------------------------------------------------------------------
# 7. 観察事実報告（判定なし #12）
# ---------------------------------------------------------------------------
def write_observation(C, pull, san, grid):
    # 瞬間θ vs peer-rel θ vs uniform の pulled-cid 系列の別軌跡度（rev3 §10-2）
    def series(eye):
        return pull[pull["eye"] == eye].sort_values("t")["picked_cid"].to_numpy()
    now_s, peer_s, uni_s = series("now_theta"), series("peer_theta"), series("uniform")
    agree_now_peer = float((now_s == peer_s).mean()) if len(now_s) == len(peer_s) else np.nan

    # 持続θ pull が長い segment に集中するか（duration lens か・rev3 §10-3）
    pe = pull[pull["eye"] == "persist_thetapct"]
    seg_len_pulled = pe["segment_length"].dropna()

    lines = []
    lines.append("# v1303j Step A 観察事実報告（selector・seed0・read-only・判定なし #12）\n")
    lines.append("*作成*: 2026-07-01、Code A。**事実のみ・success/fail を置かない。(あ)(い)採否・distinct 読み・within_ncore 最終採否・cross-eye pull は Taka 領域。**\n")
    lines.append("## 0. 構成")
    lines.append(f"- alive grid: {len(grid)} (cid,t) 行 / {grid['cid'].nunique()} cids / t∈[{T_STEP},{T_MAX}] step{T_STEP}")
    lines.append("- grid/alive 出所: per_subject_seed0.csv（host_lost_step/birth_window）+ c_trajectory(window→step=500)。v1303i 非依存。\n")

    lines.append("## 1. 目間 corr（§3.0 ゲート・auto-drop なし）")
    lines.append("```")
    lines.append(C.to_string())
    lines.append("```")
    lines.append("- 注: matrix は substrate 依存（事前調査 付録 A: within_ncore×瞬間θ は exact 0.83 / asof 0.37）。distinct 読みは Taka。\n")

    lines.append("## 2. pull 系列の sanity（目別 distinct cid・fallback 率・eligible）")
    lines.append("```")
    lines.append(san.to_string(index=False))
    lines.append("```")
    lines.append("- 静的 B_Gen は per-cid 定数ゆえ distinct cid 数が少ない＝**期待挙動（degenerate を隠さず記録・「失敗」と書かない）**。")
    lines.append("- B_Gen の fallback 率＝B_Gen 未定義 cid のみの t で uniform に落ちた割合（coverage 0.56 由来）。B_Gen pull は「全 CID 中」でなく「eligible 集合内で珍しい」と読む（rev3 §10-1）。\n")

    mean_elig = pull[pull["eye"] == "now_theta"]["eligible_count"].mean()
    chance = 1.0 / mean_elig
    lines.append("## 3. within_ncore（peer-rel θ）出口＝瞬間θと別軌跡か（rev3 §10-2）")
    lines.append(f"- pulled-cid 一致率(瞬間θ, peer-rel θ) = {agree_now_peer:.3f}")
    lines.append(f"- 参考: 瞬間θ vs uniform 一致率 = {float((now_s==uni_s).mean()):.3f} / chance(1/mean_eligible) = {chance:.3f}")
    lines.append("- **⚠ Code A の正直な留保（この指標は弱い）**: single-draw（~25 cid から1本引き）の pulled-cid 一致率は、")
    lines.append(f"  目が同一でも別物でも chance(≈{chance:.3f}) に支配され、distinct 性を判定できない（peer も uniform も chance 付近）。")
    lines.append("  rev3 §10-4「RNG 単発軌跡を読みすぎない」が実際に効いている。**distinct 性の情報は値 corr（§1: peer×瞬間θ asof 0.37）と")
    lines.append("  cross-eye pct 側にあり、軌跡ベースの確定は many-RNG 集約（Step B）が要る**。Code A は一致率の事実と本留保のみ・判定は Taka。\n")

    lines.append("## 4. 持続θ＝duration lens か（segment タグ・rev3 §10-3）")
    if len(seg_len_pulled):
        lines.append(f"- 持続θ pull の segment_length: n={len(seg_len_pulled)} / median={seg_len_pulled.median():.1f} / "
                     f"max={seg_len_pulled.max():.0f}（タグ付き pull 割合 {len(seg_len_pulled)/len(pe):.2f}）")
        lines.append("- 長 segment に集中するかの読みは Taka。集中しなければ Archive lens の salience 要再考と記録。\n")
    else:
        lines.append("- 持続θ pull に segment タグ無し＝Archive lens の salience 要再考と記録。\n")

    lines.append("## 5. 言える / 言えない")
    lines.append("- **言える**: 珍しさ値に比例して pull した attention trajectory を目ごとに作った（read-only・seed0）。")
    lines.append("- **言えない**: 「ESDE が注意した / 自律的に選んだ / 投影が始まった」。RNG 単発軌跡を唯一の注意と読まない（§10-4）。")
    lines.append("- 出口＝目ごと attention trajectory（将来の投影＝応答方向の入力・先送り stub）。\n")
    lines.append("## 6. 次段")
    lines.append("- smoke seed0 まで。main・複数 seed には進まない。承認後に Step B（正式カラム化・複数 seed・RNG 安定性検査）。")

    (REPO / "unified" / "v1303" / "v1303j_observation.md").write_text("\n".join(lines), encoding="utf-8")
    log("observation.md written")


def main():
    grid = build_alive_grid()
    grid = attach_values(grid)
    C = eye_corr(grid)
    pull = run_selector(grid)
    cross_eye(grid)
    san = sanity(pull, grid)
    write_observation(C, pull, san, grid)
    log("DONE (Step A seed0). smoke 後停止・承認待ち。")


if __name__ == "__main__":
    main()
