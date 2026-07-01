# 観察対象注釈ブロック（v1303 Final attention output schema 固定）
# 系の別: 同系内（同一 seed0 v105 main_v2・同一物理・同一時間軸）。異系対応でない（F型回避）。
# 性質: 新しい試験ではない。schema 固定 + eye registry 固定（Taka 判断済の eye 線引きを parquet に固定）。
# 過去失敗の回避: A 神の手（cutoff なし・p_select は ESDE 正規化 salience）/ B 物理介入（read-only・書込 v1303 配下のみ）/
#                 D 平均化（per-t 選択分布を本体・marginal は参考）/ #11 合成（eye 別列・合成 pull しない）/
#                 L 意味盛り（"注意した" と書かない・crown なし・軸数を成果に数えない）/ #5 新観察軸を足さない（固定のみ）。
# 版規律: v1303k / Step C を作らない。本作業で v1303 を閉じる。投影/子ESDE/Atom は v1304+ stub（memo に記述のみ）。
# insight: p_select_given_eye_t（per-t 選択分布）が本体。marginal=露出時間支配で参考・single trajectory=chance 支配で例示のみ。

import sys, os
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v1303j_selector import build_alive_grid, attach_values, SEED
from v1303j_stepB_dist_audit import attach_exact_p

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs" / "v1303j"
METHOD = "v1303_final_attention_output"

# eye registry（Taka + GPT 判断を固定・source_col=Step A/B 内部作業列 → canonical eye_id）
REGISTRY = [
    dict(eye_id="now_theta", eye_family="dynamic_theta",
         eye_role="momentary synchrony (瞬間の位相同期・基準 eye)", status="formal",
         source_col="now_theta", source_table="v1303f_attention_center",
         salience_kind="theta_resultant_length (0-1)"),
    dict(eye_id="archive_theta_percentile", eye_family="archive_theta",
         eye_role="archive-state theta position (Archive 区間内 θ 位置・duration でない)", status="formal",
         source_col="persist_thetapct", source_table="v1303e_persistence_salience",
         salience_kind="theta_cid_percentile"),
    dict(eye_id="link_rarity", eye_family="dynamic_non_theta_physics",
         eye_role="internal-link rarity (非θの物理側稀さ・θと違う軸)", status="formal",
         source_col="link_rarity", source_table="v1303i_dynamic_rarity",
         salience_kind="rarity_internal_link_within_ncore"),
    dict(eye_id="bgen_static_prior", eye_family="static_rarity",
         eye_role="birth rarity prior (誕生時の珍しさ・時間不変・degenerate は性質)", status="formal",
         source_col="bgen_pct", source_table="v1303h_bgen_salience",
         salience_kind="bgen_pct_in_ncore (per-cid 定数)"),
    dict(eye_id="aux_peer_relative_theta", eye_family="theta_relative",
         eye_role="peer-relative theta (仲間内 θ 位置・θ-family ゆえ本体に数えない)", status="auxiliary",
         source_col="peer_theta", source_table="v1303i_dynamic_rarity",
         salience_kind="rarity_theta_within_ncore"),
]


def log(m):
    print(f"[v1303-final] {m}", flush=True)


def build_schema(grid):
    # cid 属性
    cid_bgen = grid.groupby("cid")["bgen_pct"].first()
    bgen_med = cid_bgen.dropna().median()

    def bgen_status(cid):
        v = cid_bgen.get(cid)
        if pd.isna(v):
            return "no_bgen"
        return "high" if v >= bgen_med else "low"

    frames = []
    for reg in REGISTRY:
        col = reg["source_col"]
        pcol = "p_" + col
        clip = grid[col].clip(lower=0)
        s = clip.groupby(grid["t"]).transform("sum")
        df = pd.DataFrame({
            "eye_id": reg["eye_id"],
            "eye_family": reg["eye_family"],
            "eye_role": reg["eye_role"],
            "eye_status": reg["status"],
            "cid": grid["cid"].astype(int),
            "t": grid["t"].astype(int),
            "salience_raw": grid[col],                       # clip 前の生値
            "salience_pct_or_norm": clip,                     # 正規化に入る値（clip 済）
            "p_select_given_eye_t": grid[pcol],               # 本体＝per-t 選択確率
            "rank_given_eye_t": grid.groupby("t")[col].rank(ascending=False, method="min"),
            "eligible_count": grid.groupby("t")[col].transform("count").astype(int),
            "fallback_flag": (s.fillna(0.0) == 0.0).astype(int),
            "n_core": grid["n_core"],
            "event_tags": grid["dry_quadrant_candidate"],
            "bgen_status": grid["cid"].map(bgen_status),
            "source_table": reg["source_table"],
            "method_tag": METHOD,
        })
        frames.append(df)
    schema = pd.concat(frames, ignore_index=True)
    # 固定チェック: 各 (eye,t) で Σ_cid p_select == 1
    chk = schema.groupby(["eye_id", "t"])["p_select_given_eye_t"].sum()
    assert np.allclose(chk.to_numpy(), 1.0), "p_select が (eye,t) で 1 に正規化されていない"
    schema.to_parquet(OUT / f"v1303_final_attention_output_seed{SEED}.parquet")
    log(f"attention output schema fixed: {len(schema)} rows / "
        f"{schema['eye_id'].nunique()} eyes / {schema['cid'].nunique()} cids")
    return schema


def write_registry():
    reg = pd.DataFrame(REGISTRY)
    reg.to_parquet(OUT / "attention_eye_registry.parquet")
    lines = ["# v1303 attention eye registry（固定・Taka + GPT 判断）\n",
             "*性質*: 正式 eye 4 + 補助 eye 1。eye_id が canonical・source_col は Step A/B 内部作業列（値不変）。\n",
             "| eye_id | family | role | status | source_col | source_table | salience |",
             "|---|---|---|---|---|---|---|"]
    for r in REGISTRY:
        lines.append(f"| `{r['eye_id']}` | {r['eye_family']} | {r['eye_role']} | **{r['status']}** | "
                     f"`{r['source_col']}` | {r['source_table']} | {r['salience_kind']} |")
    lines += [
        "\n**改名**: `persist_thetapct` → `archive_theta_percentile`（Step B: pulled/eligible seglen 0.955・"
        "corr(pullprob,seglen) −0.14 ＝長 segment を過剰選択せず＝duration lens でない・Archive 内 θ percentile）。",
        "**peer 降格**: `peer_theta` → `aux_peer_relative_theta`（θ-family ゆえ本体に数えず捨てず aux 保持）。",
        "**不採用（戻さない）**: global_theta（raw θ 冗長）/ within_cid_theta（within_ncore と 0.988）/ "
        "R_positive rarity（98% 欠損で退化）/ C-Q 重複系。",
        "\n**構造の正直な記述（crown でない）**: 5 独立系でなく A: dynamic physical cluster"
        "（now/archive_θ/link/peer・per-t corr 0.43–0.77）+ B: static prior（bgen・直交）。"
        "多系性は薄いが link は非θゆえ物理側の別軸。軸数を成果に数えない（DNA=4記号に相当）。",
    ]
    (HERE / "attention_eye_registry.md").write_text("\n".join(lines), encoding="utf-8")
    log("eye registry (parquet + md) fixed")


def main():
    grid = build_alive_grid()
    grid = attach_values(grid)
    grid = attach_exact_p(grid)
    build_schema(grid)
    write_registry()
    log("DONE (v1303 Final schema 固定). smoke 後停止・承認待ち。")


if __name__ == "__main__":
    main()
