#!/usr/bin/env python3
"""
ESDE v9.8c — Familiarity Time-Series Analysis
================================================
v9.8c の追加分析 §7 で残した宿題に答える分析。

問い:
  なぜ familiarity が高い cid ほど bonus を稼げないのか?

3 つの解釈案を時系列データで区別する:
  解釈 1 (古株の不利): bonus を稼ぐ cid は生まれた時点から familiarity が低い
  解釈 2 (減衰中):    bonus を稼ぐ cid は過去に高 familiarity だったが現在減衰中
  解釈 3 (交絡):      bonus を稼ぐ cid の familiarity は常に低-中、social は常に高い

データソース:
  introspection_log_seed*.csv (cid, window, current_familiarity, current_social, ...)
  per_subject_seed*.csv (ttl_bonus, birth_window, host_lost_window, ...)
  per_window_seed*.csv (window 単位のメタデータ、必要なら)

分析:
  1. bonus 群別の familiarity 時系列 (mean curve)
  2. 各 cid の familiarity slope 分布 (linear regression on each cid's history)
  3. birth_window と bonus の相関 (新しい cid が bonus を稼ぐか?)
  4. familiarity と social の同 cid 内での共変動

USAGE (from primitive/v98c):
  python v98c_familiarity_timeseries.py --tag short
  python v98c_familiarity_timeseries.py --tag long
  python v98c_familiarity_timeseries.py --tag short --tag-2 long
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


# ════════════════════════════════════════════════════════════════
# 各 cid の familiarity 時系列を再構成
# ════════════════════════════════════════════════════════════════
def build_cid_timeseries(intro_log):
    """introspection_log から (seed, cid) -> [(window, famil, social, stab, spread), ...]
    を構築する。time-ordered。"""
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
    # 各 cid の history を window 順に sort
    for k in cid_history:
        cid_history[k].sort(key=lambda x: x["window"])
    return cid_history


def linear_slope(xs, ys):
    """単純な最小二乗で線形回帰の slope を計算。"""
    if len(xs) < 2:
        return 0.0
    xs_arr = np.array(xs, dtype=float)
    ys_arr = np.array(ys, dtype=float)
    x_mean = xs_arr.mean()
    y_mean = ys_arr.mean()
    denom = ((xs_arr - x_mean) ** 2).sum()
    if denom == 0:
        return 0.0
    return ((xs_arr - x_mean) * (ys_arr - y_mean)).sum() / denom


# ════════════════════════════════════════════════════════════════
# 分析 1: bonus 群別の familiarity 時系列 (mean curve)
# ════════════════════════════════════════════════════════════════
def analysis_familiarity_curves(subjects, cid_history, tag):
    """bonus 群ごとに、cid の familiarity を「lifetime 内の相対位置」で揃えて
    mean curve を描く。"""
    print(f"\n{'='*70}")
    print(f"  分析 1: bonus 群別の familiarity 時系列 (curve) ({tag})")
    print(f"{'='*70}\n")

    # subject -> bonus 群
    def bonus_group(b):
        if b == 0: return "bonus_0"
        if b == 1: return "bonus_1"
        if b == 2: return "bonus_2"
        if 3 <= b <= 5: return "bonus_3_5"
        return "bonus_6_plus"

    # 各 cid の familiarity history を「正規化された lifetime 位置」で取る
    # 位置を 0-9 の 10 ビンに分けて、各ビンでの familiarity 平均を計算
    NBINS = 10
    bin_data = defaultdict(lambda: [[] for _ in range(NBINS)])  # group -> [[fams_at_bin0], ...]

    for s in subjects:
        seed = safe_int(s.get("seed"))
        cid = safe_int(s.get("cognitive_id"))
        bonus = safe_int(s.get("ttl_bonus"))
        group = bonus_group(bonus)

        history = cid_history.get((seed, cid), [])
        if len(history) < 2:
            continue

        # lifetime を 0-1 に正規化して、各 entry の famil をビンに配置
        n = len(history)
        for i, entry in enumerate(history):
            # i / (n-1) を 0-1 にする
            pos = i / (n - 1) if n > 1 else 0.0
            bin_idx = min(NBINS - 1, int(pos * NBINS))
            bin_data[group][bin_idx].append(entry["familiarity"])

    # 各群の各ビンで平均を計算
    print(f"  Mean familiarity by lifetime position (10 bins, 0=birth, 9=last hosted)")
    print(f"  {'group':>15}  {'count':>6}  " + 
          "  ".join(f"b{i}" for i in range(NBINS)))
    print(f"  {'-'*15}  {'-'*6}  " + "  ".join(["----"] * NBINS))
    for group in ["bonus_0", "bonus_1", "bonus_2", "bonus_3_5", "bonus_6_plus"]:
        bins = bin_data[group]
        # 全ビンの cid count (代表的に bin 0 を使う)
        counts = [len(b) for b in bins]
        n_unique = max(counts) if counts else 0
        means = []
        for b in bins:
            if b:
                means.append(np.mean(b))
            else:
                means.append(None)
        means_str = "  ".join(f"{m:>4.1f}" if m is not None else " n/a"
                              for m in means)
        print(f"  {group:>15}  {n_unique:>6}  {means_str}")

    print(f"\n  解釈の手がかり:")
    print(f"    - 解釈 1 (古株の不利): bonus 群間で曲線全体の高さが違うが形は同じ")
    print(f"      → bonus_0 が常に高く、bonus_6+ が常に低い")
    print(f"    - 解釈 2 (減衰中): bonus を稼ぐ群の曲線が右下がり (b0 高 → b9 低)")
    print(f"      → bonus_6+ の slope が負で、bonus_0 の slope は緩やか")
    print(f"    - 解釈 3 (交絡):  全群で曲線の形がほぼ同じ")
    print(f"      → 違いは familiarity の絶対値ではなく、social との組み合わせ")


# ════════════════════════════════════════════════════════════════
# 分析 2: 各 cid の familiarity slope 分布
# ════════════════════════════════════════════════════════════════
def analysis_slope_distribution(subjects, cid_history, tag):
    """各 cid の familiarity time series に対する linear slope を計算し、
    bonus 群別に分布を見る。"""
    print(f"\n{'='*70}")
    print(f"  分析 2: 各 cid の familiarity slope 分布 ({tag})")
    print(f"{'='*70}\n")

    def bonus_group(b):
        if b == 0: return "bonus_0"
        if b == 1: return "bonus_1"
        if b == 2: return "bonus_2"
        if 3 <= b <= 5: return "bonus_3_5"
        return "bonus_6_plus"

    group_slopes = defaultdict(list)

    for s in subjects:
        seed = safe_int(s.get("seed"))
        cid = safe_int(s.get("cognitive_id"))
        bonus = safe_int(s.get("ttl_bonus"))
        group = bonus_group(bonus)

        history = cid_history.get((seed, cid), [])
        if len(history) < 3:  # slope を計算するなら最低 3 点
            continue

        windows = [h["window"] for h in history]
        famils = [h["familiarity"] for h in history]
        slope = linear_slope(windows, famils)
        group_slopes[group].append(slope)

    # 各群の slope 統計
    print(f"  Familiarity slope (Δfamiliarity / window) by bonus group:")
    print(f"  {'group':>15}  {'count':>6}  {'mean':>8}  {'median':>8}  "
          f"{'p25':>8}  {'p75':>8}  {'%neg':>6}")
    print(f"  {'-'*15}  {'-'*6}  {'-'*8}  {'-'*8}  "
          f"{'-'*8}  {'-'*8}  {'-'*6}")
    for group in ["bonus_0", "bonus_1", "bonus_2", "bonus_3_5", "bonus_6_plus"]:
        slopes = group_slopes[group]
        if not slopes:
            print(f"  {group:>15}  {0:>6}  {'n/a':>8}")
            continue
        arr = np.array(slopes)
        n = len(arr)
        mean_val = arr.mean()
        median_val = np.median(arr)
        p25 = np.percentile(arr, 25)
        p75 = np.percentile(arr, 75)
        pct_neg = 100 * (arr < 0).sum() / n
        print(f"  {group:>15}  {n:>6}  {mean_val:>+8.3f}  {median_val:>+8.3f}  "
              f"{p25:>+8.3f}  {p75:>+8.3f}  {pct_neg:>5.1f}%")

    print(f"\n  解釈:")
    print(f"    - 全群で mean slope が負 → ESDE 全体の familiarity 減衰トレンド (v9.8b 既知)")
    print(f"    - bonus_6+ の mean slope が他群より強く負 → 解釈 2 (減衰中) 支持")
    print(f"    - bonus_6+ と bonus_0 で slope に差がない → 解釈 1 か 3")


# ════════════════════════════════════════════════════════════════
# 分析 3: birth_window と bonus の関係
# ════════════════════════════════════════════════════════════════
def analysis_birth_vs_bonus(subjects, tag):
    """新しく生まれた cid (高 birth_window) が bonus を稼ぐか?
    解釈 1 (古株の不利) を直接検証する。"""
    print(f"\n{'='*70}")
    print(f"  分析 3: birth_window と bonus の関係 ({tag})")
    print(f"{'='*70}\n")

    pairs = []
    for s in subjects:
        bw = safe_int(s.get("birth_window"))
        bonus = safe_int(s.get("ttl_bonus"))
        pairs.append((bw, bonus))

    if len(pairs) < 10:
        print(f"  Insufficient data ({len(pairs)} cids)")
        return

    bw_arr = np.array([p[0] for p in pairs])
    bonus_arr = np.array([p[1] for p in pairs])

    # Pearson 相関
    if bw_arr.std() > 0 and bonus_arr.std() > 0:
        r = np.corrcoef(bw_arr, bonus_arr)[0, 1]
        print(f"  Pearson r (birth_window vs ttl_bonus) = {r:+.4f}")
        print(f"    (positive = 新しい cid が多くの bonus を稼ぐ)")
        print(f"    (negative = 古い cid が多くの bonus を稼ぐ)")

    # birth_window を 4 区間に分けて bonus 平均を見る
    if bw_arr.max() > bw_arr.min():
        edges = np.percentile(bw_arr, [0, 25, 50, 75, 100])
        print(f"\n  Bonus by birth_window quartile:")
        print(f"    {'quartile':>10}  {'birth range':>15}  {'count':>6}  "
              f"{'mean bonus':>11}  {'% with bonus':>13}")
        print(f"    {'-'*10}  {'-'*15}  {'-'*6}  {'-'*11}  {'-'*13}")
        for i in range(4):
            mask = (bw_arr >= edges[i]) & (bw_arr <= edges[i+1])
            if i < 3:
                mask = (bw_arr >= edges[i]) & (bw_arr < edges[i+1])
            else:
                mask = (bw_arr >= edges[i]) & (bw_arr <= edges[i+1])
            sub = bonus_arr[mask]
            if len(sub) == 0:
                continue
            n = len(sub)
            mean_b = sub.mean()
            pct_w = 100 * (sub > 0).sum() / n
            print(f"    {f'Q{i+1}':>10}  {f'{int(edges[i])}-{int(edges[i+1])}':>15}  "
                  f"{n:>6}  {mean_b:>11.3f}  {pct_w:>12.1f}%")

    print(f"\n  解釈:")
    print(f"    - r が大きく正 → 解釈 1 (古株の不利) 強く支持")
    print(f"    - r がほぼ 0 → 古さは関係ない、別の要因")
    print(f"    - r が負 → 古い cid の方が有利 (予想と逆)")


# ════════════════════════════════════════════════════════════════
# 分析 4: familiarity と social の同 cid 内共変動
# ════════════════════════════════════════════════════════════════
def analysis_within_cid_cov(subjects, cid_history, tag):
    """各 cid の time series 内で、familiarity と social が一緒に動くか?
    解釈 3 (交絡) を検証する: もし両者が独立して動くなら、cross-cid の相関は別の現象。"""
    print(f"\n{'='*70}")
    print(f"  分析 4: familiarity と social の同 cid 内共変動 ({tag})")
    print(f"{'='*70}\n")

    def bonus_group(b):
        if b == 0: return "bonus_0"
        if b == 1: return "bonus_1"
        if b == 2: return "bonus_2"
        if 3 <= b <= 5: return "bonus_3_5"
        return "bonus_6_plus"

    # 各 cid について、その history 内での social と familiarity の Pearson 相関を計算
    group_within_corrs = defaultdict(list)

    for s in subjects:
        seed = safe_int(s.get("seed"))
        cid = safe_int(s.get("cognitive_id"))
        bonus = safe_int(s.get("ttl_bonus"))
        group = bonus_group(bonus)

        history = cid_history.get((seed, cid), [])
        if len(history) < 3:
            continue

        socs = np.array([h["social"] for h in history])
        fams = np.array([h["familiarity"] for h in history])
        if socs.std() == 0 or fams.std() == 0:
            continue
        r = np.corrcoef(socs, fams)[0, 1]
        if not np.isnan(r):
            group_within_corrs[group].append(r)

    print(f"  Within-cid correlation (social vs familiarity):")
    print(f"  {'group':>15}  {'count':>6}  {'mean r':>8}  {'median r':>10}  "
          f"{'%pos':>6}  {'%neg':>6}")
    print(f"  {'-'*15}  {'-'*6}  {'-'*8}  {'-'*10}  {'-'*6}  {'-'*6}")
    for group in ["bonus_0", "bonus_1", "bonus_2", "bonus_3_5", "bonus_6_plus"]:
        rs = group_within_corrs[group]
        if not rs:
            print(f"  {group:>15}  {0:>6}  {'n/a':>8}")
            continue
        arr = np.array(rs)
        n = len(arr)
        mean_r = arr.mean()
        median_r = np.median(arr)
        pct_pos = 100 * (arr > 0).sum() / n
        pct_neg = 100 * (arr < 0).sum() / n
        print(f"  {group:>15}  {n:>6}  {mean_r:>+8.3f}  {median_r:>+10.3f}  "
              f"{pct_pos:>5.1f}%  {pct_neg:>5.1f}%")

    print(f"\n  解釈:")
    print(f"    - mean r が +0.5 以上 → social と familiarity は同じ方向に動く")
    print(f"      (cid 内で「社交が増えるとき familiarity も増える」)")
    print(f"    - mean r が 0 付近 → 独立に動く (解釈 3 の交絡を弱める)")
    print(f"    - mean r が負 → 反対方向 (社交が増えるとき familiarity は減る)")


# ════════════════════════════════════════════════════════════════
# 分析 5: bonus 群別の cid lifetime (history 長) 分布
# ════════════════════════════════════════════════════════════════
def analysis_lifetime_distribution(subjects, cid_history, tag):
    """bonus 群ごとに「cid が hosted だった window 数」の分布を見る。
    history 長と bonus の関係を直接見る。"""
    print(f"\n{'='*70}")
    print(f"  分析 5: bonus 群別の cid lifetime (hosted window 数) ({tag})")
    print(f"{'='*70}\n")

    def bonus_group(b):
        if b == 0: return "bonus_0"
        if b == 1: return "bonus_1"
        if b == 2: return "bonus_2"
        if 3 <= b <= 5: return "bonus_3_5"
        return "bonus_6_plus"

    group_lifetimes = defaultdict(list)
    for s in subjects:
        seed = safe_int(s.get("seed"))
        cid = safe_int(s.get("cognitive_id"))
        bonus = safe_int(s.get("ttl_bonus"))
        group = bonus_group(bonus)

        history = cid_history.get((seed, cid), [])
        if len(history) > 0:
            group_lifetimes[group].append(len(history))

    print(f"  Hosted lifetime (number of windows with introspection entries):")
    print(f"  {'group':>15}  {'count':>6}  {'mean':>8}  {'median':>8}  "
          f"{'max':>6}")
    print(f"  {'-'*15}  {'-'*6}  {'-'*8}  {'-'*8}  {'-'*6}")
    for group in ["bonus_0", "bonus_1", "bonus_2", "bonus_3_5", "bonus_6_plus"]:
        lts = group_lifetimes[group]
        if not lts:
            print(f"  {group:>15}  {0:>6}  {'n/a':>8}")
            continue
        arr = np.array(lts)
        print(f"  {group:>15}  {len(arr):>6}  {arr.mean():>8.2f}  "
              f"{np.median(arr):>8.1f}  {arr.max():>6}")

    print(f"\n  解釈:")
    print(f"    - bonus を稼ぐ cid が長く生きていれば、「機会数の多さ」が説明")
    print(f"    - 短命でも bonus を稼ぐ cid がいれば、別のメカニズム")


# ════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════
def run_one(tag):
    base = Path(f"diag_v98c_pickup_{tag}")
    if not base.exists():
        print(f"\n  ERROR: {base} not found")
        return

    print(f"\n{'#'*70}")
    print(f"#  ESDE v9.8c Familiarity Time-Series Analysis — tag: {tag}")
    print(f"#  Source: {base}")
    print(f"{'#'*70}")

    print(f"\n  Loading data...")
    subjects = load_per_subject(base)
    intro_log = load_introspection_log(base)
    print(f"    subjects:   {len(subjects)}")
    print(f"    intro log:  {len(intro_log)}")

    print(f"\n  Building cid time-series...")
    cid_history = build_cid_timeseries(intro_log)
    print(f"    unique cids in history: {len(cid_history)}")

    # 5 つの分析
    analysis_familiarity_curves(subjects, cid_history, tag)
    analysis_slope_distribution(subjects, cid_history, tag)
    analysis_birth_vs_bonus(subjects, tag)
    analysis_within_cid_cov(subjects, cid_history, tag)
    analysis_lifetime_distribution(subjects, cid_history, tag)

    print(f"\n{'#'*70}")
    print(f"#  Familiarity time-series analysis complete: {tag}")
    print(f"{'#'*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="ESDE v9.8c familiarity time-series analysis "
                    "(answers §7 of v98c_additional_analysis_results)")
    parser.add_argument("--tag", type=str, default="short")
    parser.add_argument("--tag-2", type=str, default=None,
                        help="Optional second tag (run both)")
    args = parser.parse_args()

    run_one(args.tag)
    if args.tag_2:
        run_one(args.tag_2)


if __name__ == "__main__":
    main()
