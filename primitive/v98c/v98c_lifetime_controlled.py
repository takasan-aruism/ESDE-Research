#!/usr/bin/env python3
"""
ESDE v9.8c — Lifetime-Controlled Analysis
============================================
v9.8c familiarity 時系列分析の続き。GPT 監査 §5 の候補 1 と 2 を実装する。

問い:
  lifetime を統制した比較で、bonus や disposition の差が残るか?
  残れば disposition の影響は本物、残らなければ元の差は lifetime に強く交絡。

  familiarity の plateau 値 (9-13) は更新則由来か、run 境界効果か?

データソース:
  introspection_log_seed*.csv
  per_subject_seed*.csv

分析:
  1. lifetime ビン × bonus 群の cross-tabulation
     (同じ lifetime を持つ cid 同士で bonus 分布が違うか?)
  2. lifetime ビン内での disposition 比較
     (同じ lifetime の cid 同士で social, familiarity に差が残るか?)
  3. lifetime ビン内での familiarity plateau 値
     (lifetime が短い cid と長い cid で plateau 値が違うか?)
  4. early-birth 効果と lifetime 効果の分離
     (birth_window と lifetime の両方で統制したとき何が残るか?)
  5. familiarity の最終値 (last hosted window) の分布
     (plateau に達した cid とそうでない cid を区別)

USAGE (from primitive/v98c):
  python v98c_lifetime_controlled.py --tag short
  python v98c_lifetime_controlled.py --tag long
  python v98c_lifetime_controlled.py --tag short --tag-2 long
"""

import csv
import argparse
import glob
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np


# ════════════════════════════════════════════════════════════════
# データ読み込み
# ════════════════════════════════════════════════════════════════
def load_per_subject(base):
    rows = []
    files = sorted(glob.glob(str(base / "subjects" / "per_subject_seed*.csv")))
    for f in files:
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                rows.append(row)
    return rows


def load_introspection_log(base):
    rows = []
    files = sorted(glob.glob(
        str(base / "introspection" / "introspection_log_seed*.csv")))
    for f in files:
        seed = int(Path(f).stem.replace("introspection_log_seed", ""))
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                row["_seed"] = seed
                rows.append(row)
    return rows


def safe_float(s, default=0.0):
    if s is None or s == "":
        return default
    try:
        return float(s)
    except (ValueError, TypeError):
        return default


def safe_int(s, default=0):
    if s is None or s == "":
        return default
    try:
        return int(s)
    except (ValueError, TypeError):
        return default


def build_cid_history(intro_log):
    cid_history = defaultdict(list)
    for entry in intro_log:
        seed = entry["_seed"]
        cid = safe_int(entry.get("cid"))
        win = safe_int(entry.get("window"))
        famil = safe_float(entry.get("current_familiarity"))
        soc = safe_float(entry.get("current_social"))
        stab = safe_float(entry.get("current_stability"))
        spread = safe_float(entry.get("current_spread"))
        cid_history[(seed, cid)].append({
            "window": win,
            "familiarity": famil,
            "social": soc,
            "stability": stab,
            "spread": spread,
        })
    for k in cid_history:
        cid_history[k].sort(key=lambda x: x["window"])
    return cid_history


# ════════════════════════════════════════════════════════════════
# Lifetime ビン定義
# ════════════════════════════════════════════════════════════════
def lifetime_bin(n):
    """history 長 (introspection entry 数) を lifetime ビンに分ける。"""
    if n <= 2:
        return "L01_very_short"   # 1-2 win
    elif n <= 5:
        return "L02_short"        # 3-5 win
    elif n <= 10:
        return "L03_medium"       # 6-10 win
    elif n <= 20:
        return "L04_long"         # 11-20 win
    elif n <= 35:
        return "L05_very_long"    # 21-35 win
    else:
        return "L06_extreme"      # 36+ win


LIFETIME_BIN_ORDER = ["L01_very_short", "L02_short", "L03_medium",
                       "L04_long", "L05_very_long", "L06_extreme"]


def bonus_bin(b):
    if b == 0: return "b0"
    if b == 1: return "b1"
    if b == 2: return "b2"
    if 3 <= b <= 5: return "b3-5"
    return "b6+"


BONUS_BIN_ORDER = ["b0", "b1", "b2", "b3-5", "b6+"]


# ════════════════════════════════════════════════════════════════
# 分析 1: lifetime × bonus cross-tabulation
# ════════════════════════════════════════════════════════════════
def analysis_1_cross_tab(subjects, cid_history, tag):
    """各 lifetime ビン内での bonus 分布。
    同じ lifetime の cid 同士で bonus が違うか?"""
    print(f"\n{'='*70}")
    print(f"  分析 1: lifetime × bonus cross-tabulation ({tag})")
    print(f"{'='*70}\n")

    cell_count = defaultdict(int)
    cell_bonus = defaultdict(list)
    lifetime_counts = Counter()
    bonus_counts = Counter()

    for s in subjects:
        seed = safe_int(s.get("seed"))
        cid = safe_int(s.get("cognitive_id"))
        bonus = safe_int(s.get("ttl_bonus"))
        history = cid_history.get((seed, cid), [])
        n = len(history)
        if n == 0:
            continue
        lb = lifetime_bin(n)
        bb = bonus_bin(bonus)
        cell_count[(lb, bb)] += 1
        cell_bonus[lb].append(bonus)
        lifetime_counts[lb] += 1
        bonus_counts[bb] += 1

    # Cross-tab table
    print(f"  Cross-tabulation: lifetime bin × bonus group")
    print(f"  (counts; row = lifetime bin, col = bonus group)")
    print()
    header = f"  {'lifetime':>16} | " + " ".join(f"{b:>6}" for b in BONUS_BIN_ORDER) + f" | {'total':>6}"
    print(header)
    print(f"  {'-'*16} | " + " ".join(["-" * 6] * len(BONUS_BIN_ORDER)) + f" | {'-'*6}")
    for lb in LIFETIME_BIN_ORDER:
        if lifetime_counts[lb] == 0:
            continue
        cells = [cell_count.get((lb, bb), 0) for bb in BONUS_BIN_ORDER]
        total = sum(cells)
        row = f"  {lb:>16} | " + " ".join(f"{c:>6}" for c in cells) + f" | {total:>6}"
        print(row)
    print(f"  {'-'*16} | " + " ".join(["-" * 6] * len(BONUS_BIN_ORDER)) + f" | {'-'*6}")
    totals = [bonus_counts.get(bb, 0) for bb in BONUS_BIN_ORDER]
    print(f"  {'total':>16} | " + " ".join(f"{c:>6}" for c in totals) +
          f" | {sum(totals):>6}")

    # Mean bonus per lifetime bin
    print(f"\n  Mean bonus per lifetime bin:")
    print(f"  {'lifetime':>16}  {'count':>6}  {'mean bonus':>11}  "
          f"{'median':>8}  {'max':>5}  {'%>0':>5}")
    print(f"  {'-'*16}  {'-'*6}  {'-'*11}  {'-'*8}  {'-'*5}  {'-'*5}")
    for lb in LIFETIME_BIN_ORDER:
        bonuses = cell_bonus.get(lb, [])
        if not bonuses:
            continue
        arr = np.array(bonuses)
        mean_b = arr.mean()
        med_b = np.median(arr)
        max_b = arr.max()
        pct_pos = 100 * (arr > 0).sum() / len(arr)
        print(f"  {lb:>16}  {len(arr):>6}  {mean_b:>11.3f}  "
              f"{med_b:>8.1f}  {max_b:>5d}  {pct_pos:>4.1f}%")

    print(f"\n  解釈:")
    print(f"    - lifetime ビンが大きいほど bonus 平均が monotonic に上がる")
    print(f"      → bonus は lifetime の関数")
    print(f"    - 同じ lifetime ビン内でも bonus に分散がある")
    print(f"      → lifetime 以外の要因 (phase 位置等) も影響する")


# ════════════════════════════════════════════════════════════════
# 分析 2: lifetime ビン内 disposition 比較
# ════════════════════════════════════════════════════════════════
def analysis_2_dispositions_within_lifetime(subjects, cid_history, tag):
    """同じ lifetime ビン内で、bonus の有無別に disposition を比較。
    lifetime を統制した上で、bonus と disposition の関係が残るか?"""
    print(f"\n{'='*70}")
    print(f"  分析 2: lifetime ビン内 disposition 比較 ({tag})")
    print(f"{'='*70}\n")

    # 各 (lifetime_bin, has_bonus) で current_* を平均
    # has_bonus: bonus > 0 か bonus == 0 の二値
    cell_data = defaultdict(lambda: {"social": [], "stability": [],
                                     "spread": [], "familiarity": [],
                                     "partners": []})

    for s in subjects:
        seed = safe_int(s.get("seed"))
        cid = safe_int(s.get("cognitive_id"))
        bonus = safe_int(s.get("ttl_bonus"))
        history = cid_history.get((seed, cid), [])
        n = len(history)
        if n == 0:
            continue
        if s.get("current_social", "") == "":
            continue
        lb = lifetime_bin(n)
        has_bonus = "with_bonus" if bonus > 0 else "no_bonus"
        cell_data[(lb, has_bonus)]["social"].append(safe_float(s.get("current_social")))
        cell_data[(lb, has_bonus)]["stability"].append(safe_float(s.get("current_stability")))
        cell_data[(lb, has_bonus)]["spread"].append(safe_float(s.get("current_spread")))
        cell_data[(lb, has_bonus)]["familiarity"].append(safe_float(s.get("current_familiarity")))
        cell_data[(lb, has_bonus)]["partners"].append(safe_int(s.get("last_n_partners")))

    print(f"  Mean disposition by (lifetime bin, has_bonus):")
    print(f"  {'lifetime':>16}  {'group':>11}  {'count':>6}  "
          f"{'social':>8}  {'famil':>8}  {'partners':>9}")
    print(f"  {'-'*16}  {'-'*11}  {'-'*6}  "
          f"{'-'*8}  {'-'*8}  {'-'*9}")

    for lb in LIFETIME_BIN_ORDER:
        for hb in ["no_bonus", "with_bonus"]:
            d = cell_data.get((lb, hb))
            if not d or not d["social"]:
                continue
            n_cell = len(d["social"])
            soc = np.mean(d["social"])
            fam = np.mean(d["familiarity"])
            par = np.mean(d["partners"])
            print(f"  {lb:>16}  {hb:>11}  {n_cell:>6}  "
                  f"{soc:>8.3f}  {fam:>8.2f}  {par:>9.1f}")
        # row separator
        if any((lb, hb) in cell_data for hb in ["no_bonus", "with_bonus"]):
            print(f"  {' '*16}  {' '*11}  {' '*6}  "
                  f"{' '*8}  {' '*8}  {' '*9}")

    print(f"  解釈:")
    print(f"    - 同じ lifetime ビン内で no_bonus と with_bonus の disposition")
    print(f"      に差があれば、disposition の影響は本物")
    print(f"    - 差がほぼなければ、§7 で見えた群差は lifetime の関数")
    print(f"    - 特に familiarity の値: 同じ lifetime で同程度なら lifetime")
    print(f"      が plateau 値を決めている")


# ════════════════════════════════════════════════════════════════
# 分析 3: lifetime ビン内 familiarity plateau 値
# ════════════════════════════════════════════════════════════════
def analysis_3_familiarity_plateau(subjects, cid_history, tag):
    """各 lifetime ビン内で、cid の familiarity 推移を見る。
    特に plateau 値が lifetime によって違うか?"""
    print(f"\n{'='*70}")
    print(f"  分析 3: lifetime ビン別の familiarity plateau ({tag})")
    print(f"{'='*70}\n")

    # 各 lifetime ビンで「最後の N window の familiarity 平均」を取る
    # これが plateau 値の代表

    bin_initial = defaultdict(list)
    bin_final = defaultdict(list)
    bin_min = defaultdict(list)
    bin_max = defaultdict(list)

    for (seed, cid), history in cid_history.items():
        n = len(history)
        if n == 0:
            continue
        lb = lifetime_bin(n)
        # 初期 (b0)
        bin_initial[lb].append(history[0]["familiarity"])
        # 終端 (b9)
        bin_final[lb].append(history[-1]["familiarity"])
        # 全体の min/max
        fams = [h["familiarity"] for h in history]
        bin_min[lb].append(min(fams))
        bin_max[lb].append(max(fams))

    print(f"  Familiarity statistics by lifetime bin:")
    print(f"  {'lifetime':>16}  {'count':>6}  {'init mean':>10}  "
          f"{'final mean':>11}  {'max mean':>10}  {'min mean':>10}")
    print(f"  {'-'*16}  {'-'*6}  {'-'*10}  {'-'*11}  "
          f"{'-'*10}  {'-'*10}")
    for lb in LIFETIME_BIN_ORDER:
        if lb not in bin_initial:
            continue
        n_cells = len(bin_initial[lb])
        init_m = np.mean(bin_initial[lb])
        fin_m = np.mean(bin_final[lb])
        max_m = np.mean(bin_max[lb])
        min_m = np.mean(bin_min[lb])
        print(f"  {lb:>16}  {n_cells:>6}  {init_m:>10.2f}  {fin_m:>11.2f}  "
              f"{max_m:>10.2f}  {min_m:>10.2f}")

    print(f"\n  解釈:")
    print(f"    - 全ビンで最終値が 9-13 程度に集まれば、")
    print(f"      familiarity は lifetime に依存しない plateau に達する")
    print(f"      → 更新則由来 (内的構造)")
    print(f"    - lifetime ビンが大きいほど最終値が下がるなら、")
    print(f"      familiarity は時間とともに減衰し続けている")
    print(f"      → run 境界効果も考えられる")


# ════════════════════════════════════════════════════════════════
# 分析 4: early-birth と lifetime の分離
# ════════════════════════════════════════════════════════════════
def analysis_4_birth_lifetime_decomposition(subjects, cid_history, tag):
    """birth_window と lifetime は交絡している (早く生まれれば長く生きる機会がある)。
    両者の効果を分離する。
    
    方針: birth_window の四分位 × lifetime ビン で bonus 平均を見る。
    もし lifetime ビン内で birth_window の効果が消えれば、birth_window の効果は
    lifetime を介してのみ作用している。"""
    print(f"\n{'='*70}")
    print(f"  分析 4: early-birth 効果 vs lifetime 効果の分離 ({tag})")
    print(f"{'='*70}\n")

    # birth_window の四分位
    bws = []
    for s in subjects:
        bws.append(safe_int(s.get("birth_window")))
    if len(bws) < 4:
        print(f"  Insufficient data")
        return
    bws_arr = np.array(bws)
    edges = np.percentile(bws_arr, [0, 25, 50, 75, 100])

    def bw_quartile(bw):
        if bw <= edges[1]: return "Q1_early"
        if bw <= edges[2]: return "Q2"
        if bw <= edges[3]: return "Q3"
        return "Q4_late"

    BW_ORDER = ["Q1_early", "Q2", "Q3", "Q4_late"]

    # (bw_quartile, lifetime_bin) -> [bonus, ...]
    cell = defaultdict(list)
    for s in subjects:
        seed = safe_int(s.get("seed"))
        cid = safe_int(s.get("cognitive_id"))
        bw = safe_int(s.get("birth_window"))
        bonus = safe_int(s.get("ttl_bonus"))
        history = cid_history.get((seed, cid), [])
        n = len(history)
        if n == 0:
            continue
        bwq = bw_quartile(bw)
        lb = lifetime_bin(n)
        cell[(bwq, lb)].append(bonus)

    print(f"  Mean bonus by (birth_quartile × lifetime_bin):")
    print(f"  {'birth/life':>14} | " +
          " ".join(f"{lb[:8]:>9}" for lb in LIFETIME_BIN_ORDER))
    print(f"  {'-'*14} | " + " ".join(["-" * 9] * len(LIFETIME_BIN_ORDER)))
    for bwq in BW_ORDER:
        cells = []
        for lb in LIFETIME_BIN_ORDER:
            data = cell.get((bwq, lb), [])
            if data:
                cells.append(f"{np.mean(data):>9.2f}")
            else:
                cells.append(f"{'.':>9}")
        print(f"  {bwq:>14} | " + " ".join(cells))

    print(f"\n  Cell counts:")
    print(f"  {'birth/life':>14} | " +
          " ".join(f"{lb[:8]:>9}" for lb in LIFETIME_BIN_ORDER))
    print(f"  {'-'*14} | " + " ".join(["-" * 9] * len(LIFETIME_BIN_ORDER)))
    for bwq in BW_ORDER:
        cells = []
        for lb in LIFETIME_BIN_ORDER:
            data = cell.get((bwq, lb), [])
            cells.append(f"{len(data):>9}")
        print(f"  {bwq:>14} | " + " ".join(cells))

    print(f"\n  解釈:")
    print(f"    - 同じ lifetime ビン内で各 birth_quartile の bonus が同じなら、")
    print(f"      birth_window の効果は lifetime を介する間接効果")
    print(f"    - 同じ lifetime ビン内でも birth_quartile で bonus が違うなら、")
    print(f"      birth_window 自体に独立な効果がある")
    print(f"    - cell counts が偏っていれば (例: Q1 × L06 が多い)、")
    print(f"      birth_window と lifetime の交絡が確認される")


# ════════════════════════════════════════════════════════════════
# 分析 5: 同じ lifetime での within-cid social-familiarity 相関
# ════════════════════════════════════════════════════════════════
def analysis_5_within_cid_corr_by_lifetime(subjects, cid_history, tag):
    """v98c familiarity timeseries の発見 (within-cid 負相関) を、
    lifetime ビンで統制して再検証する。
    
    bonus_6+ で相関が弱かったのは、bonus_6+ cid が長命だからかもしれない。
    同じ lifetime ビン内で、bonus と相関の関係が残るか?"""
    print(f"\n{'='*70}")
    print(f"  分析 5: lifetime 統制した within-cid social-familiarity 相関 ({tag})")
    print(f"{'='*70}\n")

    # (lifetime_bin, has_bonus) -> [r, r, ...]
    cell_corrs = defaultdict(list)

    for s in subjects:
        seed = safe_int(s.get("seed"))
        cid = safe_int(s.get("cognitive_id"))
        bonus = safe_int(s.get("ttl_bonus"))
        history = cid_history.get((seed, cid), [])
        if len(history) < 3:
            continue
        socs = np.array([h["social"] for h in history])
        fams = np.array([h["familiarity"] for h in history])
        if socs.std() == 0 or fams.std() == 0:
            continue
        r = np.corrcoef(socs, fams)[0, 1]
        if np.isnan(r):
            continue
        lb = lifetime_bin(len(history))
        hb = "with_bonus" if bonus > 0 else "no_bonus"
        cell_corrs[(lb, hb)].append(r)

    print(f"  Within-cid social-familiarity correlation by (lifetime, has_bonus):")
    print(f"  {'lifetime':>16}  {'group':>11}  {'count':>6}  "
          f"{'mean r':>9}  {'median r':>10}")
    print(f"  {'-'*16}  {'-'*11}  {'-'*6}  {'-'*9}  {'-'*10}")
    for lb in LIFETIME_BIN_ORDER:
        for hb in ["no_bonus", "with_bonus"]:
            rs = cell_corrs.get((lb, hb), [])
            if not rs:
                continue
            arr = np.array(rs)
            print(f"  {lb:>16}  {hb:>11}  {len(arr):>6}  "
                  f"{arr.mean():>+9.3f}  {np.median(arr):>+10.3f}")

    print(f"\n  解釈:")
    print(f"    - 同じ lifetime ビン内で no_bonus と with_bonus の相関が同じなら、")
    print(f"      『bonus_6+ で相関が弱い』のは lifetime 効果")
    print(f"      → social-familiarity 結合の緩和は構造的解放ではなく統計効果")
    print(f"    - 同じ lifetime ビン内でも with_bonus で相関が弱ければ、")
    print(f"      bonus 自体に何か独立な効果がある")
    print(f"    - lifetime ビンが大きいほど全体的に相関が弱くなれば、")
    print(f"      『時間とともにトレードオフが緩む』という構造が示唆される")


# ════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════
def run_one(tag):
    base = Path(f"diag_v98c_pickup_{tag}")
    if not base.exists():
        print(f"\n  ERROR: {base} not found")
        return

    print(f"\n{'#'*70}")
    print(f"#  ESDE v9.8c Lifetime-Controlled Analysis — tag: {tag}")
    print(f"#  Source: {base}")
    print(f"{'#'*70}")

    print(f"\n  Loading data...")
    subjects = load_per_subject(base)
    intro_log = load_introspection_log(base)
    print(f"    subjects:  {len(subjects)}")
    print(f"    intro log: {len(intro_log)}")

    print(f"\n  Building cid history...")
    cid_history = build_cid_history(intro_log)
    print(f"    unique cids: {len(cid_history)}")

    analysis_1_cross_tab(subjects, cid_history, tag)
    analysis_2_dispositions_within_lifetime(subjects, cid_history, tag)
    analysis_3_familiarity_plateau(subjects, cid_history, tag)
    analysis_4_birth_lifetime_decomposition(subjects, cid_history, tag)
    analysis_5_within_cid_corr_by_lifetime(subjects, cid_history, tag)

    print(f"\n{'#'*70}")
    print(f"#  Lifetime-controlled analysis complete: {tag}")
    print(f"{'#'*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="ESDE v9.8c lifetime-controlled analysis "
                    "(answers GPT audit §5 candidates 1 and 2)")
    parser.add_argument("--tag", type=str, default="short")
    parser.add_argument("--tag-2", type=str, default=None)
    args = parser.parse_args()

    run_one(args.tag)
    if args.tag_2:
        run_one(args.tag_2)


if __name__ == "__main__":
    main()
