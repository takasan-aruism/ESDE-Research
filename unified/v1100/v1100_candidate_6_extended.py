#!/usr/bin/env python3
"""v11.0.0 Step C 追加分析: 4 mode 予測の差分構造.

Step C で 4 mode の hit count が完全一致 (26/26/26/26) → base 優位 token が 0 と
判定された。これは Web Claude §2.2 言及「base mode が B/C/BC を R@1/R@3 ともに
上回る (R@3=0.329)」と一見矛盾する観察事実。

追加分析:
  1. 各 token で 4 mode の top-3 atom が完全一致するか
  2. top-3 が違う token と同じ token の分離
  3. score 値での比較 (hit/miss ではない)
  4. R@1 / R@3 の独立算出

これは Aruism「予想と違えば再観察」の実践、留保 #33 (集計単位による方向反転)
と同型の構造的観察。

規律:
  - 解釈断定なし (絶対格言 #10, #12)
  - 観察事実のみ記録
  - GPT 監査運用指針 v1 の 3 解釈切り分け参照
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LANG_PROJ = REPO_ROOT / "language" / "projection"
EVAL_DATA = LANG_PROJ / "eval_data"
OUT_V35 = LANG_PROJ / "output_v35"
V1100_ROOT = (REPO_ROOT / "unified" / "v1100").resolve()
V1100_OUT = V1100_ROOT / "outputs"

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
    print("v11.0.0 Step C 追加: 4 mode 予測の差分構造分析")
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

    # === 分析 1: 4 mode の top-3 完全一致率 ===
    print(f"\n[分析 1] 4 mode の top-3 完全一致 vs 部分一致 vs 完全不一致")
    n_all_same = 0
    n_partial_diff = 0
    n_all_diff = 0
    n_total = 0
    diff_examples = []
    for key in gt_lookup:
        top3_sets = {mode: tuple(pred_lookup[mode].get(key, {}).get("top3", [])) for mode in MODES}
        unique_top3 = set(top3_sets.values())
        n_total += 1
        if len(unique_top3) == 1:
            n_all_same += 1
        elif len(unique_top3) == 4:
            n_all_diff += 1
        else:
            n_partial_diff += 1
            if len(diff_examples) < 5:
                diff_examples.append({"key": list(key), **{f"top3_{m}": list(t) for m, t in top3_sets.items()}})
    print(f"  total tokens: {n_total}")
    print(f"  4 mode 完全一致: {n_all_same} ({n_all_same/n_total*100:.1f}%)")
    print(f"  4 mode 部分一致: {n_partial_diff} ({n_partial_diff/n_total*100:.1f}%)")
    print(f"  4 mode 完全不一致: {n_all_diff} ({n_all_diff/n_total*100:.1f}%)")
    if diff_examples:
        print(f"  差分例 (top 3):")
        for ex in diff_examples[:3]:
            print(f"    {ex['key']}: base={ex['top3_base']}, B={ex['top3_B']}, C={ex['top3_C']}, BC={ex['top3_BC']}")

    # === 分析 2: hit/miss が 4 mode で同一かどうか ===
    print(f"\n[分析 2] hit/miss パターンの 4 mode 別比較")
    hit_patterns = {}
    for key, gt_target in gt_lookup.items():
        gt_atoms = set(gt_target.get("atoms_top3", []))
        if not gt_atoms:
            continue
        pat = tuple(
            any(a in gt_atoms for a in pred_lookup[mode].get(key, {}).get("top3", []))
            for mode in MODES
        )
        hit_patterns[pat] = hit_patterns.get(pat, 0) + 1
    print(f"  hit pattern (base, B, C, BC) → count:")
    for pat, cnt in sorted(hit_patterns.items(), key=lambda x: -x[1]):
        marker = " ← 4 mode 同一" if (pat == (True,) * 4 or pat == (False,) * 4) else " ← 差あり"
        print(f"    {pat}: {cnt}{marker}")

    # === 分析 3: R@1 / R@3 計算 ===
    print(f"\n[分析 3] R@1 / R@3 (4 mode 別、ground_truth atoms_top3 と照合)")
    for mode in MODES:
        n_r1 = 0
        n_r3 = 0
        n_eval = 0
        for key, gt_target in gt_lookup.items():
            gt_atoms = set(gt_target.get("atoms_top3", []))
            if not gt_atoms:
                continue
            top3 = pred_lookup[mode].get(key, {}).get("top3", [])
            if not top3:
                continue
            n_eval += 1
            if top3[0] in gt_atoms:
                n_r1 += 1
            if any(a in gt_atoms for a in top3):
                n_r3 += 1
        r1 = n_r1 / n_eval if n_eval else 0
        r3 = n_r3 / n_eval if n_eval else 0
        print(f"  {mode:<5s}: R@1={r1:.4f} ({n_r1}/{n_eval}), R@3={r3:.4f} ({n_r3}/{n_eval})")

    # === 分析 4: 4 mode の score 差 (hit が同じでも score 違うかも) ===
    print(f"\n[分析 4] top-1 score の 4 mode 差分 (mean)")
    score_diffs = []
    for key in gt_lookup:
        scores = {mode: pred_lookup[mode].get(key, {}).get("scores", [0])[0] if pred_lookup[mode].get(key, {}).get("scores") else 0 for mode in MODES}
        max_s = max(scores.values())
        min_s = min(scores.values())
        score_diffs.append(max_s - min_s)
    if score_diffs:
        mean_diff = sum(score_diffs) / len(score_diffs)
        max_diff = max(score_diffs)
        print(f"  top-1 score の 4 mode 差 (max - min): mean={mean_diff:.4f}, max={max_diff:.4f}")
        print(f"  → score 差 > 0 の token 数: {sum(1 for d in score_diffs if d > 0)}/{len(score_diffs)}")

    # 出力
    out = {
        "metadata": {
            "step": "C 追加分析",
            "purpose": "4 mode hit pattern 完全一致 → Web Claude §2.2 言及との照合",
            "interpretation_rule": "断定なし、観察事実のみ記録",
        },
        "top3_uniqueness": {
            "n_total": n_total,
            "n_all_same": n_all_same,
            "n_partial_diff": n_partial_diff,
            "n_all_diff": n_all_diff,
            "diff_examples": diff_examples,
        },
        "hit_patterns": {str(k): v for k, v in hit_patterns.items()},
        "recall_by_mode": {},
        "score_diff_stats": {
            "mean": mean_diff if score_diffs else 0,
            "max": max_diff if score_diffs else 0,
            "n_tokens_with_diff": sum(1 for d in score_diffs if d > 0),
            "n_tokens_total": len(score_diffs),
        },
    }
    for mode in MODES:
        n_r1 = sum(1 for key, gt_target in gt_lookup.items()
                   if (gt_atoms := set(gt_target.get("atoms_top3", []))) and (top3 := pred_lookup[mode].get(key, {}).get("top3", [])) and top3[0] in gt_atoms)
        n_r3 = sum(1 for key, gt_target in gt_lookup.items()
                   if (gt_atoms := set(gt_target.get("atoms_top3", []))) and (top3 := pred_lookup[mode].get(key, {}).get("top3", [])) and any(a in gt_atoms for a in top3))
        n_eval = sum(1 for key, gt_target in gt_lookup.items() if gt_target.get("atoms_top3") and pred_lookup[mode].get(key, {}).get("top3"))
        out["recall_by_mode"][mode] = {"r1": n_r1/n_eval if n_eval else 0, "r3": n_r3/n_eval if n_eval else 0, "n_eval": n_eval}

    with open(V1100_OUT / "candidate_6_extended_analysis.json", "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nDONE elapsed = {time.time()-t0:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
