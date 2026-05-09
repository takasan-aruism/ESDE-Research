#!/usr/bin/env python3
"""v10.10 Step B': Multi-gate 母集団全実測.

各 gate 候補について 24 seeds の cid 母集団を実測。
- A: age <= 560 (age=200 発火では常に成立、形式的)
- a: age <= 1000 (緩和、age=200 発火では同様に常に成立)
- B: in_integration == 0 (timestamp 別、age=200 時点で α/β 外)
- C: familiarity_max >= per-seed p75
- c: familiarity_max >= per-seed p50
- 死亡前条件: birth + 200 < min(host_lost, reaped) (age=200 通過可能)

加えて timing 軸の追加観察:
- age=300 / age=500 発火時点での同 gate 母集団
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V105_ROOT = (REPO_ROOT / "developmental" / "v105").resolve()
V107_ROOT = (REPO_ROOT / "developmental" / "v107").resolve()
V110_ROOT = (REPO_ROOT / "developmental" / "v110").resolve()
DIAG_ROOT = V105_ROOT / "diag_v105_main_v2"

sys.path.insert(0, str(V107_ROOT))
from v107_baseline_constructor import _cid_meta_table  # noqa: E402

OUT_DIR = V110_ROOT / "outputs" / "environment_check"
OUT_DIR.mkdir(parents=True, exist_ok=True)
RUN_END = 25000
SEEDS = list(range(24))


def safe_read_csv(p):
    return pd.read_csv(p)


def build_alpha_beta_intervals(seed: int) -> dict[int, list[tuple[int, int]]]:
    """各 cid の (in_step, out_step) 区間リスト (timestamp 別 in_integration 判定用).

    alpha/beta birth で member_cids が in、death で out。
    death event に member_cids がない場合、対応する birth event の alpha_id を追跡。
    """
    cid_intervals: dict[int, list[tuple[int, int]]] = {}
    for fname in ["alpha_lifecycle_log", "beta_lifecycle_log"]:
        df = safe_read_csv(DIAG_ROOT / f"integration/{fname}_seed{seed}.csv")
        if df.empty:
            continue
        # alpha_id 別に birth → death の対応を追跡
        if "alpha_id" in df.columns:
            id_col = "alpha_id"
        elif "beta_id" in df.columns:
            id_col = "beta_id"
        else:
            id_col = None

        if id_col:
            # 同一 id の birth (member_cids 取得) と death (out_step 取得) を pair 化
            for aid, sub in df.groupby(id_col):
                births = sub[sub["event_type"] == "birth"]
                deaths = sub[sub["event_type"] == "death"]
                if births.empty:
                    continue
                t_in = int(births.iloc[0]["step"])
                t_out = int(deaths.iloc[0]["step"]) if not deaths.empty else RUN_END
                mems_str = str(births.iloc[0].get("member_cids") or "")
                for c_str in mems_str.split("|"):
                    if not c_str.strip():
                        continue
                    try:
                        c = int(c_str)
                    except ValueError:
                        continue
                    cid_intervals.setdefault(c, []).append((t_in, t_out))
        else:
            # フォールバック: birth から RUN_END まで
            births = df[df["event_type"] == "birth"]
            for _, r in births.iterrows():
                mems = str(r.get("member_cids") or "")
                t_in = int(r["step"])
                for c_str in mems.split("|"):
                    if not c_str.strip():
                        continue
                    try:
                        c = int(c_str)
                    except ValueError:
                        continue
                    cid_intervals.setdefault(c, []).append((t_in, RUN_END))
    return cid_intervals


def cid_in_integration_at(cid: int, t: int, intervals: dict) -> bool:
    for (t_in, t_out) in intervals.get(cid, []):
        if t_in <= t < t_out:
            return True
    return False


def evaluate_gates_for_seed(seed: int, age_target: int) -> dict:
    """seed 内で各 gate の cid 数を評価。"""
    m = _cid_meta_table(seed)
    intervals = build_alpha_beta_intervals(seed)
    fam = m["last_familiarity_max"].fillna(0)
    p75 = float(fam.quantile(0.75))
    p50 = float(fam.quantile(0.50))
    death = pd.concat([
        m["host_lost_step"].fillna(RUN_END),
        m["reaped_step"].fillna(RUN_END),
    ], axis=1).min(axis=1)

    # 各 cid について event_t = birth + age_target 時点で gate 評価
    counts = {}
    for cid_idx, row in m.iterrows():
        cid = int(row["cognitive_id"])
        birth = int(row["birth_step"])
        t_event = birth + age_target
        if t_event >= RUN_END:
            continue
        d = death.iloc[cid_idx]
        if t_event >= d:
            continue  # 死亡前に age_target に到達できない

        age_ok_A = (age_target <= 560)  # A 条件
        age_ok_a = (age_target <= 1000)  # a 緩和
        out_integ = not cid_in_integration_at(cid, t_event, intervals)
        fam_v = float(row["last_familiarity_max"]) if pd.notna(row["last_familiarity_max"]) else 0.0
        fam_C = (fam_v >= p75)
        fam_c = (fam_v >= p50)

        # 各 gate (age=age_target 発火を前提、A/a の差は age_target 自体で表現)
        gates = {
            "ABC": age_ok_A and out_integ and fam_C,
            "ABc": age_ok_A and out_integ and fam_c,
            "aBC": age_ok_a and out_integ and fam_C,
            "AB":  age_ok_A and out_integ,
            "AC":  age_ok_A and fam_C,
            "BC":  out_integ and fam_C,
            "A":   age_ok_A,
            "B":   out_integ,
            "C":   fam_C,
            "Bc":  out_integ and fam_c,  # 追加: B + c 緩和
            "all_pass": True,  # 何も条件をかけない (age_target 通過のみ)
        }
        for k, v in gates.items():
            if v:
                counts[k] = counts.get(k, 0) + 1
    counts["seed"] = seed
    counts["age_target"] = age_target
    counts["p75_fam"] = p75
    counts["p50_fam"] = p50
    return counts


def main():
    print(f"v10.10 Step B': Multi-gate 母集団全実測")
    print(f"  age_target candidates: 200 (標準), 300 (timing 軸), 500 (timing 軸)")
    print()

    AGE_TARGETS = [200, 300, 500]
    all_rows = []
    t0 = time.time()
    for at in AGE_TARGETS:
        for seed in SEEDS:
            r = evaluate_gates_for_seed(seed, at)
            all_rows.append(r)
        print(f"  age_target={at}: {SEEDS[-1]+1} seeds 完了 ({time.time()-t0:.1f}s)")

    df = pd.DataFrame(all_rows).fillna(0)
    int_cols = [c for c in df.columns if c not in ("p75_fam", "p50_fam")]
    for c in int_cols:
        df[c] = df[c].astype(int)
    out_csv = OUT_DIR / "multi_gate_population.csv"
    df.to_csv(out_csv, index=False)
    print(f"\n  saved: {out_csv}")

    # 集計表 (age_target × gate)
    GATES = ["ABC", "ABc", "aBC", "AB", "AC", "BC", "A", "B", "C", "Bc", "all_pass"]
    print(f"\n=== Multi-gate 母集団 (24 seeds 合計) ===")
    print(f"{'gate':<10}", end="")
    for at in AGE_TARGETS:
        print(f"{'age=' + str(at):<14}", end="")
    print()
    for g in GATES:
        print(f"{g:<10}", end="")
        for at in AGE_TARGETS:
            sub = df[df["age_target"] == at]
            if g in sub.columns:
                tot = int(sub[g].sum())
                per = tot / 25 / 24
                print(f"{tot:>5} (p{per:>4.2f})  ", end="")
            else:
                print(f"{'-':<14}", end="")
        print()

    # Code A 最低実行線判定
    print(f"\n=== 最低実行線判定 (per (atom × seed) >= 3 = total >= 1,800) ===")
    for at in AGE_TARGETS:
        sub = df[df["age_target"] == at]
        for g in GATES:
            if g not in sub.columns:
                continue
            tot = int(sub[g].sum())
            per = tot / 25 / 24
            label = "✓" if per >= 3 else ("△" if per >= 1 else "✗")
            judge_3 = "PASS" if per >= 3 else "FAIL"
            judge_5 = "PASS" if per >= 5 else "FAIL"
            print(f"  age={at} {g:<10}: total={tot:>5}, per={per:>5.2f}, "
                  f"min_line(>=3)={judge_3}, recommend(>=5)={judge_5} {label}")
        print()

    # seed 別の最小 events
    print(f"\n=== gate × age_target で min/max seed events ===")
    for at in [200]:  # 標準
        sub = df[df["age_target"] == at]
        for g in ["ABC", "ABc", "AB", "BC", "AC", "B", "Bc"]:
            if g not in sub.columns:
                continue
            print(f"  age={at} {g:<8}: min seed events={int(sub[g].min())}, "
                  f"max={int(sub[g].max())}, mean={sub[g].mean():.1f}, std={sub[g].std():.1f}")

    print(f"\nDONE  total elapsed = {time.time()-t0:.2f}s")


if __name__ == "__main__":
    main()
