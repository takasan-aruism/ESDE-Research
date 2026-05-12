#!/usr/bin/env python3
"""v11.0.0 Step C: 候補 6 (null cell ↔ base 優位照合) 事前検証 + 実装.

Web Claude/Taka 即決事項 (2026-05-12): 候補 6 を v1100 で実装まで進める。

入力:
  Language 側 4 mode pred_50.jsonl + ground_truth_50.jsonl
  Genesis 側 Map 5 (v113a null candidates 20 unique atoms)

処理:
  1. 各 token (50 候補 = 49 sentences × ~1 target) について
     base / B / C / BC の 4 mode で top-3 が ground truth に hit するか判定
  2. 「base が hit AND 他 3 mode 全 miss」の token を抽出 (base 優位 token)
  3. base 優位 token の top-3 atoms 集合と
     Genesis 側 Map 5 null cell atoms 集合の重なりを算出
  4. Jaccard 類似度 + 集合演算結果 + 解釈用補助統計

出力:
  unified/v1100/outputs/candidate_6_overlap.json

解釈規律 (Web Claude §5.4):
  - 「両系の整合性が証明された」と断定しない
  - 「base mode 優位 = null absorption と同じ」と即座解釈しない
  - GPT 監査運用指針 v1 (2026-04-23) の 3 解釈切り分けを参照
  - Step J 観察事実報告で「~の重なりが観察された」表現に統一
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
V1100_ROOT = (REPO_ROOT / "unified" / "v1100").resolve()
V1100_OUT = V1100_ROOT / "outputs"

MODES = ["base", "B", "C", "BC"]


def assert_output_under_v1100(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V1100_ROOT not in abs_path.parents and abs_path != V1100_ROOT:
        raise ValueError(f"Output path {path} not under v1100/")


def load_jsonl(path: Path) -> list[dict]:
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def main() -> int:
    t0 = time.time()
    print("=" * 72)
    print("v11.0.0 Step C: 候補 6 (null cell ↔ base 優位照合) 実装")
    print("=" * 72)

    V1100_OUT.mkdir(parents=True, exist_ok=True)

    # === Step B 環境チェック (統合) ===
    print(f"\n[Step B] 入力ファイル存在確認")
    inputs = {
        "ground_truth_50": EVAL_DATA / "ground_truth_50.jsonl",
        "berlin_sentences": EVAL_DATA / "berlin_sentences.jsonl",
        **{f"pred_50_{m}": OUT_V35 / m / "pred_50.jsonl" for m in MODES},
        **{f"token_diag_{m}": OUT_V35 / m / "token_diagnostics.jsonl" for m in MODES},
        "map5_genesis": GENESIS_MAP5,
    }
    for name, path in inputs.items():
        status = "OK" if path.exists() else "MISSING"
        print(f"  {name:<25s} {status}: {path.relative_to(REPO_ROOT)}")

    # === Step C 候補 6 実装 ===
    print(f"\n[Step C-1] Language 側 4 mode pred_50.jsonl 読み込み")
    preds = {}
    for mode in MODES:
        preds[mode] = load_jsonl(OUT_V35 / mode / "pred_50.jsonl")
        print(f"  {mode:<6s}: {len(preds[mode])} sentences")

    gt = load_jsonl(EVAL_DATA / "ground_truth_50.jsonl")
    print(f"  ground_truth: {len(gt)} sentences")

    # ground_truth を sentence_id × span_text で indexable に
    gt_lookup = {}
    for entry in gt:
        sid = entry["id"]
        for target in entry["targets"]:
            key = (sid, target["span_text"])
            gt_lookup[key] = {
                "atoms_top3": target.get("atoms_top3", []),
                "pos": target.get("pos"),
                "synapse_top1": target.get("synapse_top1"),
                "note": target.get("note", ""),
            }
    print(f"  ground_truth targets indexed: {len(gt_lookup)}")

    # 4 mode の予測を sentence_id × span_text で indexable に
    pred_lookup = {mode: {} for mode in MODES}
    for mode in MODES:
        for entry in preds[mode]:
            sid = entry["id"]
            for target in entry["targets"]:
                key = (sid, target["span_text"])
                pred_lookup[mode][key] = target.get("pred_top3", [])

    # === Step C-2 base 優位 token 抽出 ===
    print(f"\n[Step C-2] base 優位 token 抽出 (base hit AND 他 3 mode 全 miss)")
    base_winning_tokens = []
    all_token_records = []
    for key, gt_entry in gt_lookup.items():
        sid, span = key
        gt_atoms = set(gt_entry["atoms_top3"])
        if not gt_atoms:
            continue

        mode_hits = {}
        mode_top3 = {}
        for mode in MODES:
            top3 = pred_lookup[mode].get(key, [])
            mode_top3[mode] = top3
            mode_hits[mode] = any(a in gt_atoms for a in top3)

        record = {
            "sentence_id": sid,
            "span_text": span,
            "pos": gt_entry["pos"],
            "gt_atoms_top3": list(gt_atoms),
            "synapse_top1_gt": gt_entry["synapse_top1"],
            **{f"top3_{m}": mode_top3[m] for m in MODES},
            **{f"hit_{m}": mode_hits[m] for m in MODES},
            "is_base_winning": (mode_hits["base"] and not (mode_hits["B"] or mode_hits["C"] or mode_hits["BC"])),
        }
        all_token_records.append(record)
        if record["is_base_winning"]:
            base_winning_tokens.append(record)

    print(f"  total tokens: {len(all_token_records)}")
    print(f"  base hit count: {sum(1 for r in all_token_records if r['hit_base'])}")
    print(f"  B hit count:    {sum(1 for r in all_token_records if r['hit_B'])}")
    print(f"  C hit count:    {sum(1 for r in all_token_records if r['hit_C'])}")
    print(f"  BC hit count:   {sum(1 for r in all_token_records if r['hit_BC'])}")
    print(f"  **base 優位 (base hit AND 他全 miss): {len(base_winning_tokens)} tokens**")

    if base_winning_tokens:
        print(f"\n  base 優位 token 詳細 (top 10):")
        for r in base_winning_tokens[:10]:
            print(f"    {r['sentence_id']:<13s} {r['span_text']:<15s} pos={r['pos']:<5s} "
                  f"gt={r['gt_atoms_top3']}, base_top3={r['top3_base']}")

    # === Step C-3 base 優位 atom 集合の構築 ===
    print(f"\n[Step C-3] base 優位 atom 集合の構築")
    base_winning_atoms_top3 = set()
    base_winning_atoms_hit_in_gt = set()
    for r in base_winning_tokens:
        for atom in r["top3_base"]:
            base_winning_atoms_top3.add(atom)
        # gt と hit する atom のみ
        for atom in r["top3_base"]:
            if atom in r["gt_atoms_top3"]:
                base_winning_atoms_hit_in_gt.add(atom)
    print(f"  base 優位 token の top-3 union: {len(base_winning_atoms_top3)} atoms")
    print(f"  base 優位 token の hit atom: {len(base_winning_atoms_hit_in_gt)} atoms")

    # === Step C-4 Genesis 側 Map 5 null cell atoms ===
    print(f"\n[Step C-4] Genesis 側 Map 5 null cell atoms 取得")
    df_map5 = pd.read_parquet(GENESIS_MAP5)
    nc = df_map5[df_map5["is_null_cell_candidate"] == True]
    null_cell_atoms = set(nc["atom_id"].unique().tolist())
    print(f"  null cell rows: {len(nc)}")
    print(f"  null cell unique atoms: {len(null_cell_atoms)}")
    print(f"  atoms: {sorted(null_cell_atoms)}")

    # === Step C-5 集合演算 (Jaccard 類似度) ===
    print(f"\n[Step C-5] 集合演算 + Jaccard")

    def compute_set_stats(set_a, set_b, name_a, name_b):
        overlap = set_a & set_b
        only_a = set_a - set_b
        only_b = set_b - set_a
        union = set_a | set_b
        jaccard = len(overlap) / len(union) if union else 0.0
        return {
            "set_a_name": name_a, "set_b_name": name_b,
            "set_a_size": len(set_a), "set_b_size": len(set_b),
            "overlap": sorted(overlap), "overlap_size": len(overlap),
            "only_a": sorted(only_a), "only_a_size": len(only_a),
            "only_b": sorted(only_b), "only_b_size": len(only_b),
            "union_size": len(union),
            "jaccard": jaccard,
        }

    stats_top3 = compute_set_stats(
        base_winning_atoms_top3, null_cell_atoms,
        "language_base_winning_top3", "genesis_null_cell_atoms"
    )
    stats_hit = compute_set_stats(
        base_winning_atoms_hit_in_gt, null_cell_atoms,
        "language_base_winning_hit_in_gt", "genesis_null_cell_atoms"
    )

    print(f"\n  [top-3 union] Language base 優位 vs Genesis null cell:")
    print(f"    Language: {stats_top3['set_a_size']} atoms")
    print(f"    Genesis:  {stats_top3['set_b_size']} atoms")
    print(f"    overlap:  {stats_top3['overlap_size']} atoms — {stats_top3['overlap']}")
    print(f"    only_L:   {stats_top3['only_a_size']} atoms — {stats_top3['only_a']}")
    print(f"    only_G:   {stats_top3['only_b_size']} atoms — {stats_top3['only_b']}")
    print(f"    Jaccard:  {stats_top3['jaccard']:.4f}")

    print(f"\n  [hit in gt] Language base 優位 (gt と一致した atom) vs Genesis null cell:")
    print(f"    Language: {stats_hit['set_a_size']} atoms")
    print(f"    overlap:  {stats_hit['overlap_size']} atoms — {stats_hit['overlap']}")
    print(f"    Jaccard:  {stats_hit['jaccard']:.4f}")

    # === Step C-6 出力 ===
    out = {
        "metadata": {
            "step": "C (候補 6 事前検証 + 実装)",
            "date": "2026-05-12",
            "agent": "Code A",
            "interpretation_rule": (
                "解釈規律 (Web Claude §5.4): 「両系の整合性が証明された」「base mode 優位 = "
                "null absorption と同じ」と断定しない、観察事実として記録、判断は Taka 領域"
            ),
        },
        "input_files": {k: str(v.relative_to(REPO_ROOT)) for k, v in inputs.items() if v.exists()},
        "language_side": {
            "n_tokens_total": len(all_token_records),
            "base_hit_count": sum(1 for r in all_token_records if r["hit_base"]),
            "B_hit_count": sum(1 for r in all_token_records if r["hit_B"]),
            "C_hit_count": sum(1 for r in all_token_records if r["hit_C"]),
            "BC_hit_count": sum(1 for r in all_token_records if r["hit_BC"]),
            "n_base_winning_tokens": len(base_winning_tokens),
            "base_winning_tokens": base_winning_tokens,
            "base_winning_atoms_top3_union": sorted(base_winning_atoms_top3),
            "base_winning_atoms_hit_in_gt": sorted(base_winning_atoms_hit_in_gt),
        },
        "genesis_side": {
            "n_null_cell_rows": int(len(nc)),
            "null_cell_unique_atoms": sorted(null_cell_atoms),
            "n_null_cell_atoms": len(null_cell_atoms),
        },
        "overlap_analysis_top3_union": stats_top3,
        "overlap_analysis_hit_in_gt": stats_hit,
        "computation_metadata": {
            "elapsed_sec": round(time.time() - t0, 2),
        },
    }

    out_path = V1100_OUT / "candidate_6_overlap.json"
    assert_output_under_v1100(out_path)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)

    elapsed = time.time() - t0
    print(f"\nDONE  elapsed = {elapsed:.2f}s")
    print(f"  output = {out_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
