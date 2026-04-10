#!/usr/bin/env python3
"""
ESDE v9.8c — Additional Analysis
==================================
v9.8 trilogy 完了後、次の段階に進む前に v9.8c のデータを深掘りする。

4 つの分析:
  1. bonus を稼ぐ cid の特徴 (どんな disposition か)
  2. dur=18 の cid の履歴 (pickup_log から何があったか)
  3. ghost 化直前のタグパターン (v9.8b 仮説 7)
  4. 4 軸 (social/stability/spread/familiarity) と pickup 勝率の相関

Run A (short, 48 seeds × 10 win) と Run B (long, 5 seeds × 50 win) の
両方のデータを使う。

USAGE (from primitive/v98c):
  python v98c_additional_analysis.py --tag short
  python v98c_additional_analysis.py --tag long
  python v98c_additional_analysis.py --tag short --tag-2 long  # 両方一気に

入力:
  diag_v98c_pickup_{tag}/subjects/per_subject_seed*.csv
  diag_v98c_pickup_{tag}/pickup/pickup_log_seed*.csv
  diag_v98c_pickup_{tag}/pickup/death_pool_log_seed*.csv

出力:
  stdout に結果を表示
  diag_v98c_pickup_{tag}/analysis/  に補助 CSV を出力
"""

import csv
import argparse
import glob
import math
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np


# ════════════════════════════════════════════════════════════════
# データ読み込み
# ════════════════════════════════════════════════════════════════
def load_per_subject(base):
    """per_subject CSV を全 seed 集約。"""
    rows = []
    files = sorted(glob.glob(str(base / "subjects" / "per_subject_seed*.csv")))
    for f in files:
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                rows.append(row)
    return rows


def load_pickup_log(base):
    """pickup_log CSV を全 seed 集約。
    seed を識別するために、seed の情報を row に付加する。"""
    rows = []
    files = sorted(glob.glob(str(base / "pickup" / "pickup_log_seed*.csv")))
    for f in files:
        # ファイル名から seed を抽出
        seed = int(Path(f).stem.replace("pickup_log_seed", ""))
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                row["_seed"] = seed
                rows.append(row)
    return rows


def load_introspection_log(base):
    """introspection_log CSV を全 seed 集約。"""
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
# 分析 1: bonus を稼ぐ cid の特徴
# ════════════════════════════════════════════════════════════════
def analysis_1_bonus_features(subjects, tag):
    """bonus を稼ぐ cid と稼がない cid で disposition を比較。"""
    print(f"\n{'='*70}")
    print(f"  分析 1: bonus を稼ぐ cid の特徴 ({tag})")
    print(f"{'='*70}\n")

    # bonus でグループ分け
    bins = {"bonus_0": [], "bonus_1": [], "bonus_2": [],
            "bonus_3_5": [], "bonus_6_plus": []}

    for s in subjects:
        bonus = safe_int(s.get("ttl_bonus", 0))
        if bonus == 0:
            bins["bonus_0"].append(s)
        elif bonus == 1:
            bins["bonus_1"].append(s)
        elif bonus == 2:
            bins["bonus_2"].append(s)
        elif 3 <= bonus <= 5:
            bins["bonus_3_5"].append(s)
        else:
            bins["bonus_6_plus"].append(s)

    print(f"  Group sizes:")
    for name, group in bins.items():
        print(f"    {name:>15}: {len(group):>5} cids")

    # 各 group で disposition の平均を取る
    # (current_* がある cid だけを対象。tag 生成された hosted cid のみ)
    print(f"\n  Disposition by bonus group (current_* averages):")
    print(f"    {'group':>15}  {'count':>6}  {'social':>8}  {'stab':>8}  "
          f"{'spread':>8}  {'famil':>8}  {'partners':>9}")
    print(f"    {'-'*15}  {'-'*6}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*9}")

    for name, group in bins.items():
        # current_* がある cid だけを対象
        valid = [s for s in group if s.get("current_social", "") != ""]
        if not valid:
            print(f"    {name:>15}  {0:>6}  {'n/a':>8}  {'n/a':>8}  "
                  f"{'n/a':>8}  {'n/a':>8}  {'n/a':>9}")
            continue
        socs = [safe_float(s.get("current_social")) for s in valid]
        stabs = [safe_float(s.get("current_stability")) for s in valid]
        spreads = [safe_float(s.get("current_spread")) for s in valid]
        famils = [safe_float(s.get("current_familiarity")) for s in valid]
        partners = [safe_int(s.get("last_n_partners")) for s in valid]
        print(f"    {name:>15}  {len(valid):>6}  "
              f"{np.mean(socs):>8.3f}  {np.mean(stabs):>8.3f}  "
              f"{np.mean(spreads):>8.3f}  {np.mean(famils):>8.2f}  "
              f"{np.mean(partners):>9.1f}")

    # last_n_partners と bonus の相関 (パートナーが多い cid は勝ちやすいか?)
    print(f"\n  Correlation: last_n_partners vs ttl_bonus")
    pairs = []
    for s in subjects:
        partners = safe_int(s.get("last_n_partners"))
        bonus = safe_int(s.get("ttl_bonus"))
        if partners > 0 or bonus > 0:
            pairs.append((partners, bonus))
    if len(pairs) >= 2:
        partners_arr = np.array([p[0] for p in pairs])
        bonus_arr = np.array([p[1] for p in pairs])
        if partners_arr.std() > 0 and bonus_arr.std() > 0:
            r = np.corrcoef(partners_arr, bonus_arr)[0, 1]
            print(f"    Pearson r = {r:+.4f}  (n={len(pairs)})")
        else:
            print(f"    (variance zero, no correlation)")

    # ttl_bonus と n_pickups_won の確認 (これは定義上 1:1)
    print(f"\n  Sanity check: ttl_bonus == n_pickups_won")
    mismatches = [s for s in subjects
                  if safe_int(s.get("ttl_bonus")) != safe_int(s.get("n_pickups_won"))]
    print(f"    Mismatches: {len(mismatches)}/{len(subjects)} (should be 0)")

    # 勝率 (n_won / (n_won + n_lost)) の分布
    print(f"\n  Win rate distribution (cids that participated in pickup):")
    win_rates = []
    for s in subjects:
        won = safe_int(s.get("n_pickups_won"))
        lost = safe_int(s.get("n_pickups_lost"))
        total = won + lost
        if total > 0:
            win_rates.append(won / total)
    if win_rates:
        print(f"    n cids participated: {len(win_rates)}")
        print(f"    mean win rate:       {np.mean(win_rates):.3f}")
        print(f"    median win rate:     {np.median(win_rates):.3f}")
        # ヒストグラム (5 bins)
        hist = Counter()
        for r in win_rates:
            b = min(4, int(r * 5))  # 0-4
            hist[b] += 1
        for b in range(5):
            label = f"{b/5:.1f}-{(b+1)/5:.1f}"
            n = hist.get(b, 0)
            bar = "█" * min(40, int(n / max(1, max(hist.values())) * 40))
            print(f"    {label:>10}: {n:>5} {bar}")


# ════════════════════════════════════════════════════════════════
# 分析 2: dur=18 の cid の履歴 (および高 dur cid の特徴)
# ════════════════════════════════════════════════════════════════
def analysis_2_high_dur_history(subjects, pickup_log, tag):
    """dur > 10 の cid を取り出し、pickup_log から履歴を再構成。"""
    print(f"\n{'='*70}")
    print(f"  分析 2: 元の TTL=10 を超えた cid の履歴 ({tag})")
    print(f"{'='*70}\n")

    # dur > 10 の cid を取り出す (final_state=reaped で ghost_duration > 10)
    high_dur = []
    for s in subjects:
        dur = safe_int(s.get("ghost_duration"))
        state = s.get("final_state", "")
        if state == "reaped" and dur > 10:
            high_dur.append(s)

    if not high_dur:
        print(f"  No cids with ghost_duration > 10 found.")
        return

    print(f"  Total cids with ghost_duration > 10: {len(high_dur)}")
    dur_dist = Counter()
    for s in high_dur:
        dur_dist[safe_int(s.get("ghost_duration"))] += 1
    for d in sorted(dur_dist.keys()):
        print(f"    dur={d:>2}: {dur_dist[d]:>3}")

    # 上位 5 cid を選んで詳細に調べる
    high_dur_sorted = sorted(high_dur,
                              key=lambda s: -safe_int(s.get("ghost_duration")))
    top_5 = high_dur_sorted[:5]

    print(f"\n  Top 5 longest-lived cids:")
    print(f"    {'#':>3}  {'seed':>4}  {'cid':>5}  {'dur':>4}  {'bonus':>5}  "
          f"{'soc':>6}  {'stab':>6}  {'spread':>7}  {'famil':>7}  "
          f"{'partners':>9}")

    # 各 cid の pickup 履歴を pickup_log から取り出す
    for i, s in enumerate(top_5):
        seed = safe_int(s.get("seed"))
        cid = safe_int(s.get("cognitive_id"))
        dur = safe_int(s.get("ghost_duration"))
        bonus = safe_int(s.get("ttl_bonus"))
        soc = safe_float(s.get("current_social"))
        stab = safe_float(s.get("current_stability"))
        spread = safe_float(s.get("current_spread"))
        famil = safe_float(s.get("current_familiarity"))
        partners = safe_int(s.get("last_n_partners"))

        print(f"    {i+1:>3}  {seed:>4}  {cid:>5}  {dur:>4}  {bonus:>5}  "
              f"{soc:>6.3f}  {stab:>6.3f}  {spread:>7.3f}  "
              f"{famil:>7.2f}  {partners:>9}")

    # 最長 cid (dur=18) の pickup 履歴を詳しく追う
    if top_5:
        champion = top_5[0]
        seed = safe_int(champion.get("seed"))
        cid = safe_int(champion.get("cognitive_id"))
        dur = safe_int(champion.get("ghost_duration"))
        bonus = safe_int(champion.get("ttl_bonus"))

        print(f"\n  --- Champion cid history (seed={seed}, cid={cid}, dur={dur}) ---")
        print(f"    Total pickup wins recorded: {bonus}")

        # pickup_log で この cid が winner になったエントリを拾う
        wins = [p for p in pickup_log
                if p.get("_seed") == seed
                and safe_int(p.get("winner_cid")) == cid]

        if wins:
            print(f"\n    Win events:")
            print(f"      {'window':>6}  {'phase_dist':>11}  {'n_cands':>8}  "
                  f"{'cum_bonus':>10}  {'outcome':>12}")
            wins_sorted = sorted(wins, key=lambda w: safe_int(w.get("window")))
            for w in wins_sorted:
                win = safe_int(w.get("window"))
                pd = safe_float(w.get("winner_phase_dist"))
                nc = safe_int(w.get("n_candidates"))
                cb = safe_int(w.get("winner_new_ttl_bonus"))
                out = w.get("outcome", "")
                print(f"      {win:>6}  {pd:>11.4f}  {nc:>8}  "
                      f"{cb:>10}  {out:>12}")

        # この cid が loser として記録された回数も
        losses = []
        for p in pickup_log:
            if p.get("_seed") != seed:
                continue
            loser_str = p.get("loser_cids", "")
            if loser_str:
                loser_ids = [safe_int(x) for x in loser_str.split("|")]
                if cid in loser_ids:
                    losses.append(p)
        print(f"\n    Total losses: {len(losses)}")
        if losses:
            print(f"    Win/loss ratio: {len(wins)}/{len(losses)+len(wins)} "
                  f"= {len(wins)/(len(losses)+len(wins)):.3f}")


# ════════════════════════════════════════════════════════════════
# 分析 3: ghost 化直前のタグパターン (v9.8b 仮説 7)
# ════════════════════════════════════════════════════════════════
def analysis_3_pre_ghost_tags(subjects, intro_log, tag):
    """ghost 化した cid の、ghost 化直前 (host_lost_window-1) のタグ分布を見る。
    仮説: ghost 化直前には特定のタグ (loss_familiarity 等) が偏るかもしれない。"""
    print(f"\n{'='*70}")
    print(f"  分析 3: ghost 化直前のタグパターン ({tag})")
    print(f"{'='*70}\n")

    # subjects から ghost 化した cid (host_lost_window がある) を取り出す
    ghost_cids_meta = []  # [(seed, cid, host_lost_w), ...]
    for s in subjects:
        host_lost = s.get("host_lost_window", "")
        if host_lost == "":
            continue
        try:
            host_lost_w = int(host_lost)
        except ValueError:
            continue
        seed = safe_int(s.get("seed"))
        cid = safe_int(s.get("cognitive_id"))
        ghost_cids_meta.append((seed, cid, host_lost_w))

    print(f"  Cids that became ghost: {len(ghost_cids_meta)}")

    if not ghost_cids_meta:
        return

    # intro_log をインデックス化: (seed, cid, window) -> entry
    intro_by_key = {}
    for entry in intro_log:
        key = (entry.get("_seed"),
               safe_int(entry.get("cid")),
               safe_int(entry.get("window")))
        intro_by_key[key] = entry

    # 各 ghost 化 cid について、host_lost_window-1 (= 最後の hosted window) の
    # タグを取り出す
    pre_ghost_tags_count = Counter()
    pre_ghost_no_entry = 0
    pre_ghost_empty = 0
    pre_ghost_total = 0

    # baseline: 全 hosted cid の任意の window でのタグ分布
    baseline_tags_count = Counter()
    baseline_total = 0

    for seed, cid, host_lost_w in ghost_cids_meta:
        # host_lost_w-1 が「最後の hosted window」(これが pre-ghost moment)
        pre_w = host_lost_w - 1
        key = (seed, cid, pre_w)
        if key not in intro_by_key:
            pre_ghost_no_entry += 1
            continue
        entry = intro_by_key[key]
        tags_str = entry.get("tags", "")
        pre_ghost_total += 1
        if not tags_str:
            pre_ghost_empty += 1
        else:
            for t in tags_str.split("|"):
                pre_ghost_tags_count[t] += 1

    # baseline: ghost 化していない全 entry のタグ分布 (比較対象)
    for entry in intro_log:
        baseline_total += 1
        tags_str = entry.get("tags", "")
        if tags_str:
            for t in tags_str.split("|"):
                baseline_tags_count[t] += 1

    print(f"\n  Pre-ghost moments (host_lost-1) entries found: {pre_ghost_total}")
    print(f"    No introspection entry: {pre_ghost_no_entry}")
    print(f"    Empty tags:             {pre_ghost_empty}")
    print(f"    With tags:              {pre_ghost_total - pre_ghost_empty}")

    print(f"\n  Tag frequency comparison (pre-ghost vs baseline):")
    print(f"    {'tag':>20}  {'pre-ghost':>12}  {'baseline':>12}  {'ratio':>8}")
    print(f"    {'-'*20}  {'-'*12}  {'-'*12}  {'-'*8}")

    all_tags = ["gain_social", "loss_social",
                "gain_stability", "loss_stability",
                "gain_spread", "loss_spread",
                "gain_familiarity", "loss_familiarity"]
    for t in all_tags:
        pg = pre_ghost_tags_count.get(t, 0)
        bl = baseline_tags_count.get(t, 0)
        # frequency per entry
        pg_freq = pg / max(1, pre_ghost_total)
        bl_freq = bl / max(1, baseline_total)
        ratio = pg_freq / bl_freq if bl_freq > 0 else float('inf')
        ratio_str = f"{ratio:.3f}" if bl_freq > 0 else "n/a"
        print(f"    {t:>20}  {pg_freq:>12.4f}  {bl_freq:>12.4f}  {ratio_str:>8}")

    print(f"\n  Interpretation:")
    print(f"    ratio > 1.0: pre-ghost で baseline より頻出")
    print(f"    ratio < 1.0: pre-ghost で baseline より少ない")
    print(f"    例えば loss_familiarity の ratio が顕著に高ければ、")
    print(f"    'familiarity を失うことが ghost 化の前兆' という仮説の証拠")


# ════════════════════════════════════════════════════════════════
# 分析 4: 4 軸動力学と pickup 勝率の相関
# ════════════════════════════════════════════════════════════════
def analysis_4_dispositions_vs_winrate(subjects, tag):
    """各 cid の disposition (current_*) と pickup 勝率の相関を見る。"""
    print(f"\n{'='*70}")
    print(f"  分析 4: 4 軸動力学と pickup 勝率の相関 ({tag})")
    print(f"{'='*70}\n")

    # cid ごとに (disposition, win_rate) ペアを作る
    pairs = []
    for s in subjects:
        won = safe_int(s.get("n_pickups_won"))
        lost = safe_int(s.get("n_pickups_lost"))
        total = won + lost
        if total < 1:
            continue
        win_rate = won / total
        # disposition (現在値)
        soc = safe_float(s.get("current_social"))
        stab = safe_float(s.get("current_stability"))
        spread = safe_float(s.get("current_spread"))
        famil = safe_float(s.get("current_familiarity"))
        # データがある場合だけ
        if s.get("current_social", "") == "":
            continue
        pairs.append({
            "win_rate": win_rate,
            "social": soc,
            "stability": stab,
            "spread": spread,
            "familiarity": famil,
            "n_total": total,
        })

    print(f"  Cids participated in pickup with disposition data: {len(pairs)}")

    if len(pairs) < 5:
        print(f"  Insufficient data.")
        return

    # 各軸との相関
    print(f"\n  Pearson correlation: disposition vs win_rate")
    print(f"    {'axis':>15}  {'r':>8}  {'p (approx)':>11}")
    print(f"    {'-'*15}  {'-'*8}  {'-'*11}")

    win_arr = np.array([p["win_rate"] for p in pairs])
    for axis in ["social", "stability", "spread", "familiarity"]:
        ax_arr = np.array([p[axis] for p in pairs])
        if ax_arr.std() == 0 or win_arr.std() == 0:
            print(f"    {axis:>15}  {'n/a':>8}  {'n/a':>11}")
            continue
        r = np.corrcoef(ax_arr, win_arr)[0, 1]
        # 簡易的な p 値判定 (|r| × sqrt(n-2) / sqrt(1-r^2))
        n = len(pairs)
        if abs(r) < 0.999:
            t_stat = abs(r) * math.sqrt(n - 2) / math.sqrt(1 - r * r)
            # 自由度 large 近似で t > 1.96 → p < 0.05
            sig = "*" if t_stat > 1.96 else ""
            sig += "*" if t_stat > 2.58 else ""
            sig += "*" if t_stat > 3.29 else ""
            p_str = f"{sig if sig else 'n.s.'}"
        else:
            p_str = "***"
        print(f"    {axis:>15}  {r:>+8.4f}  {p_str:>11}")

    # 4 軸の組み合わせ archetype と勝率
    print(f"\n  Win rate by disposition archetype:")
    print(f"    (high = > 0.5, low = <= 0.5; familiarity uses 20.0)")

    # 各 cid を 4 軸の high/low パターンで分類
    archetypes = defaultdict(list)
    for p in pairs:
        sig = (
            "Hs" if p["social"] > 0.5 else "Ls",
            "Hst" if p["stability"] > 0.5 else "Lst",
            "Hsp" if p["spread"] > 0.5 else "Lsp",
            "Hf" if p["familiarity"] > 20.0 else "Lf",
        )
        archetypes[sig].append(p["win_rate"])

    print(f"    {'archetype':>30}  {'count':>6}  {'mean wr':>9}")
    print(f"    {'-'*30}  {'-'*6}  {'-'*9}")
    arch_sorted = sorted(archetypes.items(),
                          key=lambda x: -np.mean(x[1]) if x[1] else 0)
    for sig, rates in arch_sorted[:15]:
        sig_str = "/".join(sig)
        if rates:
            mean_wr = np.mean(rates)
            print(f"    {sig_str:>30}  {len(rates):>6}  {mean_wr:>9.3f}")

    # win_rate と n_total (拾得参加機会数) の関係
    print(f"\n  Relationship: pickup participation count vs win_rate")
    n_arr = np.array([p["n_total"] for p in pairs])
    if n_arr.std() > 0:
        r = np.corrcoef(n_arr, win_arr)[0, 1]
        print(f"    Pearson r (n_total vs win_rate) = {r:+.4f}")
        print(f"    (positive = 多く参加する cid ほど勝率が高い、つまり Matthew effect)")


# ════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════
def run_one(tag):
    base = Path(f"diag_v98c_pickup_{tag}")
    if not base.exists():
        print(f"\n  ERROR: {base} not found")
        return

    print(f"\n{'#'*70}")
    print(f"#  ESDE v9.8c Additional Analysis — tag: {tag}")
    print(f"#  Source: {base}")
    print(f"{'#'*70}")

    print(f"\n  Loading data...")
    subjects = load_per_subject(base)
    pickup_log = load_pickup_log(base)
    intro_log = load_introspection_log(base)
    print(f"    subjects:    {len(subjects)}")
    print(f"    pickup log:  {len(pickup_log)}")
    print(f"    intro log:   {len(intro_log)}")

    # 4 つの分析
    analysis_1_bonus_features(subjects, tag)
    analysis_2_high_dur_history(subjects, pickup_log, tag)
    analysis_3_pre_ghost_tags(subjects, intro_log, tag)
    analysis_4_dispositions_vs_winrate(subjects, tag)

    print(f"\n{'#'*70}")
    print(f"#  Analysis complete: {tag}")
    print(f"{'#'*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="ESDE v9.8c additional analysis "
                    "(bonus features, dur=18 history, pre-ghost tags, "
                    "dispositions vs winrate)")
    parser.add_argument("--tag", type=str, default="short")
    parser.add_argument("--tag-2", type=str, default=None,
                        help="Optional second tag (run both)")
    args = parser.parse_args()

    run_one(args.tag)
    if args.tag_2:
        run_one(args.tag_2)


if __name__ == "__main__":
    main()
