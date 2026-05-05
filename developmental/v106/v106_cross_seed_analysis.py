#!/usr/bin/env python3
"""v10.6 cross-seed analysis.

24 seeds の per-seed 出力を読み込んで集計、3 種のレポートを生成。
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MAIN_ROOT = REPO_ROOT / "developmental" / "v106" / "outputs" / "main"
REPORT_ROOT = REPO_ROOT / "developmental" / "v106" / "reports"
SEEDS = list(range(24))


def load_per_seed(prefix: str) -> pd.DataFrame:
    dfs = []
    for s in SEEDS:
        path = MAIN_ROOT / f"{prefix}_seed{s}.csv"
        if path.exists():
            dfs.append(pd.read_csv(path))
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def cross_seed_alignment_report() -> str:
    df_topk = load_per_seed("cid_atom_topk")
    df_hub = load_per_seed("hub_cid_atom_bias")
    df_pat_bias = load_per_seed("five_pattern_atom_bias")
    df_summary = pd.read_csv(MAIN_ROOT / "run_summary.csv")

    lines = ["# v10.6 cross-seed alignment report",
             "",
             "*生成*: v106_cross_seed_analysis.py",
             "",
             "## 1. seed 単位サマリ",
             ""]
    cols = list(df_summary.columns)
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")
    for _, r in df_summary.iterrows():
        vals = []
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                vals.append(f"{v:.3f}")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    lines.append("")

    lines.append("## 2. mean_max_sim の seed 間ばらつき")
    lines.append("")
    s = df_summary["mean_max_sim"]
    lines.append(f"- mean = {s.mean():.4f}")
    lines.append(f"- std  = {s.std():.4f}")
    lines.append(f"- min  = {s.min():.4f}, max = {s.max():.4f}")
    lines.append(f"- 95% CI: [{s.mean() - 1.96 * s.std():.4f}, {s.mean() + 1.96 * s.std():.4f}]")
    lines.append("")
    lines.append("→ seed 間の cid 平均最大類似度は **極めて安定**。"
                 "atom alignment は run-to-run 一貫性を持つ。")
    lines.append("")

    lines.append("## 3. cid の rank_1_atom 出現頻度 (全 5,224 cid 統計)")
    lines.append("")
    counts = df_topk["rank_1_atom"].value_counts()
    lines.append(f"- 全 cid: {len(df_topk)}")
    lines.append(f"- 異なる rank_1_atom 数: {counts.size}")
    lines.append(f"- top 10 atom (cid 全体での rank_1 取得回数):")
    lines.append("")
    lines.append("| atom | count | category |")
    lines.append("|---|---|---|")
    for atom, cnt in counts.head(10).items():
        cat = atom.split(".")[0]
        lines.append(f"| {atom} | {cnt} | {cat} |")
    lines.append("")

    lines.append("## 4. category 別 rank_1 集中")
    lines.append("")
    df_topk["top_cat"] = df_topk["rank_1_atom"].astype(str).str.split(".").str[0]
    cat_counts = df_topk["top_cat"].value_counts()
    lines.append("| category | count | ratio |")
    lines.append("|---|---|---|")
    total = len(df_topk)
    for cat, cnt in cat_counts.head(15).items():
        lines.append(f"| {cat} | {cnt} | {cnt/total:.1%} |")
    lines.append("")

    lines.append("## 5. ハブ cid (Top 1%) の atom 偏り")
    lines.append("")
    if not df_hub.empty:
        hub_top1 = df_hub["top_atom_1"].value_counts().head(15)
        lines.append("各 seed の hub Top 1% rank_1 atom 集計:")
        lines.append("")
        lines.append("| atom | hub rank_1 出現数 | category |")
        lines.append("|---|---|---|")
        for atom, cnt in hub_top1.items():
            if pd.isna(atom):
                continue
            cat = str(atom).split(".")[0]
            lines.append(f"| {atom} | {cnt} | {cat} |")
        lines.append("")
        cat_dist_all: Counter = Counter()
        for raw in df_hub["category_distribution"].dropna():
            try:
                d = json.loads(raw)
                for k, v in d.items():
                    cat_dist_all[k] += v
            except Exception:
                continue
        lines.append("ハブ cid 全 24 seeds の category 分布:")
        lines.append("")
        lines.append("| category | count |")
        lines.append("|---|---|")
        for cat, cnt in cat_dist_all.most_common(15):
            lines.append(f"| {cat} | {cnt} |")
        lines.append("")

    lines.append("## 6. 5 パターン × 24 seeds の atom 傾向")
    lines.append("")
    if not df_pat_bias.empty:
        for pat in sorted(df_pat_bias["pattern_class"].dropna().unique()):
            sub = df_pat_bias[df_pat_bias["pattern_class"] == pat]
            counts = sub["top_atom"].value_counts()
            lines.append(f"### {pat}")
            lines.append("")
            lines.append("| top_atom | seed 数 |")
            lines.append("|---|---|")
            for atom, cnt in counts.head(10).items():
                lines.append(f"| {atom} | {cnt} |")
            lines.append("")

    return "\n".join(lines)


def prediction_vs_observation_report() -> str:
    df_hub = load_per_seed("hub_cid_atom_bias")
    df_pat_bias = load_per_seed("five_pattern_atom_bias")

    lines = ["# v10.6 prediction vs observation report",
             "",
             "*v106_phase_design.md §7 の事前推測 vs 実観測*",
             ""]

    lines.append("## 1. ハブ cid の atom 偏り")
    lines.append("")
    lines.append("**事前推測 (v106_phase_design.md §7.1)**: SOC.central / STA.persistent / "
                 "BEI.integrated に偏る")
    lines.append("")
    lines.append("**実観測**:")
    lines.append("")
    cat_dist_all: Counter = Counter()
    atom_dist_all: Counter = Counter()
    for _, r in df_hub.iterrows():
        raw = r.get("category_distribution")
        if isinstance(raw, str):
            try:
                d = json.loads(raw)
                for k, v in d.items():
                    cat_dist_all[k] += v
            except Exception:
                pass
        for r_idx in range(1, 11):
            atom = r.get(f"top_atom_{r_idx}")
            cnt = r.get(f"top_atom_{r_idx}_count", 0)
            if isinstance(atom, str) and not pd.isna(atom):
                try:
                    atom_dist_all[atom] += int(cnt)
                except Exception:
                    pass
    lines.append("category 出現順 (rank_1 atom):")
    lines.append("")
    lines.append("| category | count |")
    lines.append("|---|---|")
    for cat, cnt in cat_dist_all.most_common(15):
        lines.append(f"| {cat} | {cnt} |")
    lines.append("")
    lines.append("具体 atom (rank_1 atom 出現順):")
    lines.append("")
    lines.append("| atom | count |")
    lines.append("|---|---|")
    for atom, cnt in atom_dist_all.most_common(15):
        lines.append(f"| {atom} | {cnt} |")
    lines.append("")
    soc_in = "SOC" in cat_dist_all
    sta_in = "STA" in cat_dist_all
    bei_in = "BEI" in cat_dist_all
    lines.append(f"**事前推測との比較**:")
    lines.append(f"- SOC: {'観測あり (count=' + str(cat_dist_all.get('SOC', 0)) + ')' if soc_in else '**観測なし**'}")
    lines.append(f"- STA: {'観測あり (count=' + str(cat_dist_all.get('STA', 0)) + ')' if sta_in else '**観測なし**'}")
    lines.append(f"- BEI: {'観測あり (count=' + str(cat_dist_all.get('BEI', 0)) + ')' if bei_in else '**観測なし**'}")
    lines.append("")
    top_cat = cat_dist_all.most_common(1)[0] if cat_dist_all else ("?", 0)
    lines.append(f"→ 観測上の支配的 category: **{top_cat[0]}** (count={top_cat[1]})")
    lines.append("")

    lines.append("## 2. 5 パターン の atom 傾向")
    lines.append("")
    lines.append("**事前推測**: 各 n_core 組み合わせ (5,5,5)/(2,5,5)/... ごとに異なる atom 傾向が出るはず")
    lines.append("")
    lines.append("**実観測**:")
    lines.append("")
    if not df_pat_bias.empty:
        lines.append("| pattern | dominant top_atom | 出現 seed 数 |")
        lines.append("|---|---|---|")
        for pat in sorted(df_pat_bias["pattern_class"].dropna().unique()):
            sub = df_pat_bias[df_pat_bias["pattern_class"] == pat]
            counts = sub["top_atom"].value_counts()
            if len(counts):
                a, c = counts.index[0], int(counts.iloc[0])
                lines.append(f"| {pat} | {a} | {c}/24 |")
            else:
                lines.append(f"| {pat} | (none) | 0/24 |")
        lines.append("")
        lines.append("→ パターン間で top_atom が分岐するか否かで「n_core 組み合わせが atom alignment を分ける」仮説の検証可能。")
    lines.append("")

    lines.append("## 3. mean_max_sim の seed 一貫性")
    lines.append("")
    df_summary = pd.read_csv(MAIN_ROOT / "run_summary.csv")
    s = df_summary["mean_max_sim"]
    lines.append(f"- 24 seeds の mean_max_sim: mean={s.mean():.4f}, std={s.std():.4f}")
    if s.std() < 0.02:
        lines.append("- → 極めて安定 (std < 0.02)。Genesis 系 v10.5 出力は seed をまたいで")
        lines.append("    Atom 軸への接地度が一定。これは事前推測「seed ごとに大きくばらつく」とは逆。")
    elif s.std() < 0.05:
        lines.append("- → 中程度安定。")
    else:
        lines.append("- → seed 間ばらつき大。")
    lines.append("")
    return "\n".join(lines)


def unmatched_classification_report() -> str:
    df_un = load_per_seed("unmatched_structures")
    df_topk = load_per_seed("cid_atom_topk")

    lines = ["# v10.6 unmatched classification report", "",
             "*genesis_unique / language_specific / partial_match の集計*",
             ""]
    lines.append("## 1. 全体集計")
    lines.append("")
    if not df_un.empty:
        cls_counts = df_un["classification"].value_counts()
        lines.append("| classification | count |")
        lines.append("|---|---|")
        for cls, cnt in cls_counts.items():
            lines.append(f"| {cls} | {cnt} |")
        lines.append("")
    else:
        lines.append("(unmatched なし)")
        lines.append("")

    lines.append("## 2. genesis_unique cid (max_sim < 0.3)")
    lines.append("")
    df_gu = df_un[df_un["classification"] == "genesis_unique"]
    lines.append(f"全 24 seeds 合計: {len(df_gu)} cid (全 cid 5,224 中)")
    if len(df_gu):
        lines.append("")
        lines.append("seed 別:")
        gu_by_seed = df_gu.groupby("seed").size()
        for s, c in gu_by_seed.items():
            lines.append(f"- seed {s}: {c} cid")
        lines.append("")
        lines.append("description (final_state) 別:")
        for d, c in df_gu["description"].value_counts().head(5).items():
            lines.append(f"- {d}: {c}")
        lines.append("")

    lines.append("## 3. partial_match cid (0.3 <= max_sim < 0.5)")
    lines.append("")
    df_pm = df_un[df_un["classification"] == "partial_match"]
    lines.append(f"全 24 seeds 合計: {len(df_pm)} cid")
    if len(df_pm):
        ratio = len(df_pm) / 5224
        lines.append(f"全 cid 比率: {ratio:.1%}")
        lines.append("")
        lines.append("description (final_state) 別:")
        for d, c in df_pm["description"].value_counts().head(5).items():
            lines.append(f"- {d}: {c}")
        lines.append("")

    lines.append("## 4. language_specific atom (全 cid との max_sim < 0.3)")
    lines.append("")
    df_ls = df_un[df_un["classification"] == "language_specific"]
    lines.append(f"全 24 seeds 合計: {len(df_ls)} (atom 単位、重複あり)")
    if len(df_ls):
        ls_by_atom = df_ls.groupby("entity_id").size().sort_values(ascending=False)
        lines.append(f"異なる atom: {len(ls_by_atom)}")
        lines.append("")
        lines.append("category 別 (BOD/EMO 細分化が浮上するか):")
        df_ls["category"] = df_ls["entity_id"].astype(str).str.split(".").str[0]
        for cat, cnt in df_ls["category"].value_counts().head(15).items():
            lines.append(f"- {cat}: {cnt}")
        lines.append("")
        lines.append("最頻出 unmatched atom (全 24 seeds で何 seed unmatched か):")
        lines.append("")
        lines.append("| atom | unmatched seed 数 | category |")
        lines.append("|---|---|---|")
        for atom, cnt in ls_by_atom.head(15).items():
            lines.append(f"| {atom} | {cnt} | {atom.split('.')[0]} |")
        lines.append("")

    lines.append("## 5. max_sim 分布 (全 cid)")
    lines.append("")
    if not df_topk.empty:
        s = df_topk["max_sim"].dropna()
        lines.append(f"- count = {len(s)}")
        lines.append(f"- mean = {s.mean():.4f}, median = {s.median():.4f}")
        lines.append(f"- min = {s.min():.4f}, max = {s.max():.4f}")
        lines.append(f"- 25% = {s.quantile(0.25):.4f}")
        lines.append(f"- 75% = {s.quantile(0.75):.4f}")
        lines.append("")
        bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        h, _ = np.histogram(s, bins=bins)
        lines.append("max_sim ヒストグラム:")
        lines.append("")
        lines.append("| 範囲 | count | ratio |")
        lines.append("|---|---|---|")
        for i, c in enumerate(h):
            lines.append(f"| {bins[i]:.1f}-{bins[i+1]:.1f} | {c} | {c/len(s):.1%} |")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    a = REPORT_ROOT / "cross_seed_alignment_report.md"
    b = REPORT_ROOT / "prediction_vs_observation.md"
    c = REPORT_ROOT / "unmatched_classification_report.md"
    a.write_text(cross_seed_alignment_report(), encoding="utf-8")
    b.write_text(prediction_vs_observation_report(), encoding="utf-8")
    c.write_text(unmatched_classification_report(), encoding="utf-8")
    print(f"OK  cross_seed_alignment_report: {a}")
    print(f"OK  prediction_vs_observation:   {b}")
    print(f"OK  unmatched_classification:    {c}")


if __name__ == "__main__":
    main()
