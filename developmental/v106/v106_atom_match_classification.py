#!/usr/bin/env python3
"""v10.6 atom match classification.

24 seeds の atom_cid_topk_seed*.csv から各 atom の rank_1_sim 24 値を集計、
5 段階に分類:

  strong_24/24            : 全 24 seeds で max_sim ≥ 0.5
  mixed_strong_partial    : strong と partial が混在、unmatched なし
  all_partial_no_strong   : 全 24 seeds で 0.3-0.5、0.5 超えなし
  occasionally_unmatched  : 一部 seed で max_sim < 0.3
  always_unmatched        : 全 24 seeds で max_sim < 0.3 (= 24/24 unmatched)

出力: outputs/main/stratified/atom_match_classification.csv
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MAIN_ROOT = REPO_ROOT / "developmental" / "v106" / "outputs" / "main"
STRAT_ROOT = MAIN_ROOT / "stratified"


def classify() -> pd.DataFrame:
    all_sims: dict[str, list[float]] = defaultdict(list)
    for s in range(24):
        df = pd.read_csv(MAIN_ROOT / f"atom_cid_topk_seed{s}.csv")
        for atom, sim in zip(df["atom"], df["rank_1_sim"]):
            all_sims[atom].append(float(sim))

    rows = []
    for atom, sims_list in all_sims.items():
        if len(sims_list) != 24:
            continue
        sims = np.array(sims_list)
        n_strong = int((sims >= 0.5).sum())
        n_partial = int(((sims >= 0.3) & (sims < 0.5)).sum())
        n_weak = int((sims < 0.3).sum())
        if n_strong == 24:
            cls = "strong_24/24"
        elif n_weak == 0 and n_strong >= 1:
            cls = "mixed_strong_partial"
        elif n_weak == 0:
            cls = "all_partial_no_strong"
        elif n_weak < 24:
            cls = "occasionally_unmatched"
        else:
            cls = "always_unmatched"
        rows.append({
            "atom": atom, "category": atom.split(".")[0],
            "min_sim": round(float(sims.min()), 4),
            "mean_sim": round(float(sims.mean()), 4),
            "max_sim": round(float(sims.max()), 4),
            "n_strong_seeds": n_strong,
            "n_partial_seeds": n_partial,
            "n_weak_seeds": n_weak,
            "match_class": cls,
        })
    return pd.DataFrame(rows).sort_values(
        ["match_class", "mean_sim"], ascending=[True, False]
    )


def main() -> None:
    df = classify()
    out = STRAT_ROOT / "atom_match_classification.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Saved {out} with {len(df)} atoms")
    print()
    print("=== match_class distribution ===")
    for cls, sub in df.groupby("match_class"):
        print(f"  {cls}: {len(sub)} atoms")
    print()
    print("=== category solid (strong + mixed) % ===")
    for cat in sorted(df["category"].unique()):
        sub = df[df["category"] == cat]
        solid = sub["match_class"].isin(["strong_24/24", "mixed_strong_partial"]).sum()
        pct = solid / len(sub) * 100
        print(f"  {cat}: {len(sub):3d} total, solid {solid:3d} ({pct:5.1f}%)")


if __name__ == "__main__":
    main()
