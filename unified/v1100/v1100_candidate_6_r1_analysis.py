#!/usr/bin/env python3
"""v11.0.0 Step C 追加 2: R@1 ベースの base 優位 token 抽出と Genesis 照合.

Step C 追加分析で発見:
  - R@3 では 4 mode の hit pattern 完全同一 (base 優位 token = 0)
  - R@1 では base が他を上回る (R@1=0.96 vs B/C/BC=0.78)
  - これは留保 #33 (集計単位による方向反転) と同型構造

R@1 ベースで「base が top-1 で gt と一致 AND 他 3 mode が top-1 で miss」の
token を抽出し、その top-1 atom 集合と Genesis Map 5 null cell atom 集合の
重なりを照合する。

これが「Web Claude §2.2 言及の base 優位」と「Map 5 null absorption」の
構造的同型性 (留保 #34 候補) の本来の検証。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LANG_PROJ = REPO_ROOT / "language" / "projection"
EVAL_DATA = LANG_PROJ / "eval_data"
OUT_V35 = LANG_PROJ / "output_v35"
GENESIS_MAP5 = REPO_ROOT / "developmental" / "v113a" / "outputs" / "main" / "map5_null_phase_per_cell.parquet"
V1100_OUT = (REPO_ROOT / "unified" / "v1100" / "outputs").resolve()

MODES = ["base", "B", "C", "BC"]


def load_jsonl(path):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def main():
    t0 = time.time()
    print("=" * 72)
    print("v11.0.0 Step C R@1 ベース照合 (留保 #33 同型構造の検証)")
    print("=" * 72)

    # 読み込み
    gt = load_jsonl(EVAL_DATA / "ground_truth_50.jsonl")
    gt_lookup = {}
    for entry in gt:
        for target in entry["targets"]:
            gt_lookup[(entry["id"], target["span_text"])] = target

    pred_lookup = {mode: {} for mode in MODES}
    for mode in MODES:
        for entry in load_jsonl(OUT_V35 / mode / "pred_50.jsonl"):
            for target in entry["targets"]:
                pred_lookup[mode][(entry["id"], target["span_text"])] = {
                    "top3": target.get("pred_top3", []),
                    "scores": target.get("scores_top3", []),
                }

    # === R@1 base 優位 token 抽出 ===
    print(f"\n[R@1 base 優位 token 抽出]")
    print("  条件: base が top-1 で gt_top1 と一致 AND B/C/BC が top-1 で miss")
    r1_winning = []
    for key, gt_target in gt_lookup.items():
        gt_top3 = gt_target.get("atoms_top3", [])
        if not gt_top3:
            continue
        gt_top1 = gt_top3[0]  # 最有力 atom (atoms_top3 の 1 番目)

        top1 = {mode: pred_lookup[mode].get(key, {}).get("top3", [None])[0] for mode in MODES}
        if top1["base"] is None:
            continue

        # base hits gt_top1 (top-1 一致) かつ B/C/BC は gt_top1 と一致しない
        base_hit = (top1["base"] == gt_top1)
        b_hit = (top1["B"] == gt_top1)
        c_hit = (top1["C"] == gt_top1)
        bc_hit = (top1["BC"] == gt_top1)

        if base_hit and not (b_hit or c_hit or bc_hit):
            r1_winning.append({
                "sentence_id": key[0],
                "span_text": key[1],
                "pos": gt_target.get("pos"),
                "gt_top1": gt_top1,
                "gt_atoms_top3": gt_top3,
                "base_top1": top1["base"],
                "B_top1": top1["B"],
                "C_top1": top1["C"],
                "BC_top1": top1["BC"],
            })

    print(f"  R@1 base 優位 tokens: {len(r1_winning)}")
    print(f"\n  詳細 (top 10):")
    for r in r1_winning[:10]:
        print(f"    {r['sentence_id']:<13s} {r['span_text']:<15s} "
              f"gt_top1={r['gt_top1']:<20s} base={r['base_top1']:<18s} B/C/BC={r['B_top1']}")

    # R@1 base 優位 token の top-1 atom 集合
    r1_winning_atoms = set(r["base_top1"] for r in r1_winning)
    print(f"\n  R@1 base 優位の base top-1 atom 集合: {sorted(r1_winning_atoms)}")
    print(f"  集合サイズ: {len(r1_winning_atoms)}")

    # === Genesis Map 5 null cell atoms ===
    df_map5 = pd.read_parquet(GENESIS_MAP5)
    nc = df_map5[df_map5["is_null_cell_candidate"] == True]
    null_cell_atoms = set(nc["atom_id"].unique().tolist())
    print(f"\n  Genesis Map 5 null cell atoms: {sorted(null_cell_atoms)} ({len(null_cell_atoms)} atoms)")

    # === 集合演算 ===
    overlap = r1_winning_atoms & null_cell_atoms
    only_L = r1_winning_atoms - null_cell_atoms
    only_G = null_cell_atoms - r1_winning_atoms
    union = r1_winning_atoms | null_cell_atoms
    jaccard = len(overlap) / len(union) if union else 0.0

    print(f"\n[集合演算 (R@1 ベース)]")
    print(f"  Language base 優位 (R@1): {len(r1_winning_atoms)} atoms")
    print(f"  Genesis null cell:        {len(null_cell_atoms)} atoms")
    print(f"  overlap:                  {len(overlap)} atoms — {sorted(overlap)}")
    print(f"  only Language:            {len(only_L)} atoms — {sorted(only_L)}")
    print(f"  only Genesis:             {len(only_G)} atoms — {sorted(only_G)}")
    print(f"  Jaccard:                  {jaccard:.4f}")

    # 出力
    out = {
        "metadata": {
            "step": "C R@1 ベース照合 (留保 #33 同型構造の検証)",
            "method": "base が top-1 で gt_top1 と一致 AND B/C/BC が top-1 で miss",
            "rationale": (
                "Step C 初回 (R@3 ベース) で base 優位 token = 0、"
                "追加分析で R@1 では 0.96 vs 0.78、留保 #33 同型構造を発見。"
                "本書は R@1 ベースで本来の検証を実施。"
            ),
            "interpretation_rule": "断定なし、観察事実のみ記録、Taka 直感判断対象",
        },
        "r1_winning_tokens": r1_winning,
        "n_r1_winning_tokens": len(r1_winning),
        "language_base_winning_atoms_r1": sorted(r1_winning_atoms),
        "genesis_null_cell_atoms": sorted(null_cell_atoms),
        "overlap_analysis": {
            "set_a_name": "language_base_winning_R1",
            "set_a_size": len(r1_winning_atoms),
            "set_b_name": "genesis_null_cell_atoms",
            "set_b_size": len(null_cell_atoms),
            "overlap": sorted(overlap),
            "overlap_size": len(overlap),
            "only_language": sorted(only_L),
            "only_language_size": len(only_L),
            "only_genesis": sorted(only_G),
            "only_genesis_size": len(only_G),
            "union_size": len(union),
            "jaccard": jaccard,
        },
        "computation_metadata": {"elapsed_sec": round(time.time() - t0, 2)},
    }
    with open(V1100_OUT / "candidate_6_r1_overlap.json", "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nDONE elapsed = {time.time()-t0:.2f}s")
    print(f"  output = unified/v1100/outputs/candidate_6_r1_overlap.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
