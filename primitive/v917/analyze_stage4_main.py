"""
v9.17 段階 4 本番 run 分析スクリプト (Step 8 レポート向け)。
24 seed 合算の観察統計を抽出して JSON + stderr に出力する。

禁止 (指示書 §10.3):
  - 断定表現、飛躍、比喩、擬人化を行わない
  - 段階間の「進化・成長」判定を行わない
  観察値のみ抽出する。
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

V917 = Path("diag_v917_main")
V916 = Path("/home/takasan/esde/ESDE-Research/primitive/v916/diag_v916_main")


def summarize_numeric(values):
    if not values:
        return {"n": 0}
    arr = np.asarray(values, dtype=float)
    return {
        "n": int(arr.size),
        "min": float(np.min(arr)),
        "q25": float(np.percentile(arr, 25)),
        "median": float(np.median(arr)),
        "mean": float(np.mean(arr)),
        "q75": float(np.percentile(arr, 75)),
        "max": float(np.max(arr)),
        "std": float(np.std(arr)),
    }


def cv(values):
    if not values or np.mean(values) == 0:
        return None
    return float(np.std(values) / np.mean(values))


# -----------------------------------------------------------------
# Section 2: 下層 (他者読み)
# -----------------------------------------------------------------

visible_ratios_all = []
fetched_counts_all = []
missing_counts_all = []

# per-cid 統計 (per_subject から)
per_subject_v917 = defaultdict(list)  # seed -> list of dict
unique_contacts_by_cid = []  # list of values across all (cid,seed)
total_other_contacts_by_cid = []
avg_visible_by_cid_per_seed = defaultdict(list)  # seed -> list

# n_core 情報 (per_subject_audit の n_core_member)
cid_ncore = {}  # (seed, cid) -> n_core

# Fetch 総数 (v915 self-read event count, per_subject の v915_fetch_count)
v915_fetch_count_by_seed = defaultdict(int)

# visible_ratio を n_core 別 (観察元)
visible_by_ncore = defaultdict(list)

# step 分布
other_records_step = []

for seed in range(24):
    audit_path = V917 / "audit" / f"per_subject_audit_seed{seed}.csv"
    with open(audit_path) as f:
        for r in csv.DictReader(f):
            cid_ncore[(seed, int(r["cid"]))] = int(r["n_core_member"])

    per_subj_path = V917 / "subjects" / f"per_subject_seed{seed}.csv"
    with open(per_subj_path) as f:
        for r in csv.DictReader(f):
            cid = int(r["cognitive_id"])
            v917_total_other = int(r["v917_total_other_contacts"])
            v917_unique = int(r["v917_unique_contacts"])
            avg_vr_str = r["v917_avg_visible_ratio"]
            total_other_contacts_by_cid.append(v917_total_other)
            unique_contacts_by_cid.append(v917_unique)
            if avg_vr_str not in ("unformed", ""):
                try:
                    avg_vr = float(avg_vr_str)
                    avg_visible_by_cid_per_seed[seed].append(avg_vr)
                except ValueError:
                    pass
            v915_fc_str = r.get("v915_fetch_count", "0")
            try:
                v915_fetch_count_by_seed[seed] += int(v915_fc_str)
            except ValueError:
                pass

    or_path = V917 / "selfread" / f"other_records_seed{seed}.csv"
    with open(or_path) as f:
        for r in csv.DictReader(f):
            v = float(r["visible_ratio"])
            visible_ratios_all.append(v)
            nf = int(r["n_features_fetched"])
            nm = int(r["n_features_missing"])
            fetched_counts_all.append(nf)
            missing_counts_all.append(nm)
            cid = int(r["cid_id"])
            ncore = cid_ncore.get((seed, cid))
            if ncore is not None:
                visible_by_ncore[ncore].append(v)
            other_records_step.append(int(r["step"]))


# -----------------------------------------------------------------
# Section 3: 上層 (接触体候補)
# -----------------------------------------------------------------

all_compositions = []      # list of frozenset
all_ncore_pairs = []       # list of sorted (a_nc, b_nc) tuples
all_q0_pairs = []          # list of sorted (a_q0, b_q0) tuples
age_factor_category = Counter()  # "both_high", "one_low", "both_low"
ilog_rows_per_seed = []
ilog_compositions_per_seed = []
interaction_step = []

AGE_HIGH_THRESH = 0.5
for seed in range(24):
    ip = V917 / "selfread" / f"interaction_log_seed{seed}.csv"
    rows_n = 0
    compositions_this_seed = set()
    for r in csv.reader(open(ip)):
        pass
    with open(ip) as f:
        for r in csv.DictReader(f):
            rows_n += 1
            a_id = int(r["cid_a_id"])
            b_id = int(r["cid_b_id"])
            all_compositions.append(frozenset({a_id, b_id}))
            compositions_this_seed.add(frozenset({a_id, b_id}))
            a_nc = int(r["cid_a_n_core"])
            b_nc = int(r["cid_b_n_core"])
            all_ncore_pairs.append(tuple(sorted([a_nc, b_nc])))
            a_q0 = int(r["cid_a_Q0"])
            b_q0 = int(r["cid_b_Q0"])
            all_q0_pairs.append(tuple(sorted([a_q0, b_q0])))
            a_af = float(r["cid_a_age_factor"])
            b_af = float(r["cid_b_age_factor"])
            if a_af >= AGE_HIGH_THRESH and b_af >= AGE_HIGH_THRESH:
                age_factor_category["both_high"] += 1
            elif a_af < AGE_HIGH_THRESH and b_af < AGE_HIGH_THRESH:
                age_factor_category["both_low"] += 1
            else:
                age_factor_category["one_low"] += 1
            interaction_step.append(int(r["step"]))
    ilog_rows_per_seed.append(rows_n)
    ilog_compositions_per_seed.append(len(compositions_this_seed))

# 再接触 (同じ frozenset が複数 seed を跨がず、seed 内で複数回出現するケース)
# 24 seed 全体の composition 分布を数える
comp_counter = Counter(all_compositions)
multi_compositions = sum(1 for n in comp_counter.values() if n > 1)

# -----------------------------------------------------------------
# Section 5: v9.16 段階 3 との比較
# -----------------------------------------------------------------

# E3 event 数の合計 (v916 vs v917)
def count_e3(root):
    t = 0
    for s in range(24):
        p = root / "audit" / f"per_event_audit_seed{s}.csv"
        with open(p) as f:
            for r in csv.DictReader(f):
                if r["v14_event_type"] == "E3_contact":
                    t += 1
    return t


e3_v917 = count_e3(V917)
e3_v916 = count_e3(V916)

# Fetch 総数 (v915_fetch_count の合計)
def total_v915_fetch(root):
    t = 0
    for s in range(24):
        p = root / "subjects" / f"per_subject_seed{s}.csv"
        with open(p) as f:
            for r in csv.DictReader(f):
                try:
                    t += int(r.get("v915_fetch_count", "0"))
                except ValueError:
                    pass
    return t


fetch_v917 = total_v915_fetch(V917)
fetch_v916 = total_v915_fetch(V916)

# theta_diff_norm_all の max 差分 (per_cid_self から)
def collect_theta_diff_max(root):
    """per_cid_self_seed{N}.csv の divergence_norm_max を全 cid 合計"""
    out = {}
    for s in range(24):
        p = root / "selfread" / f"per_cid_self_seed{s}.csv"
        with open(p) as f:
            for r in csv.DictReader(f):
                cid = int(r["cid_id"])
                v = r.get("divergence_norm_max", "")
                if v and v != "unformed":
                    try:
                        out[(s, cid)] = float(v)
                    except ValueError:
                        pass
    return out


d917 = collect_theta_diff_max(V917)
d916 = collect_theta_diff_max(V916)
common = set(d917.keys()) & set(d916.keys())
diff_abs = [abs(d917[k] - d916[k]) for k in common]
theta_diff_max_diff = max(diff_abs) if diff_abs else None
theta_diff_cid_count = len(common)

# -----------------------------------------------------------------
# Section 6: seed 別分散
# -----------------------------------------------------------------

avg_visible_per_seed = {}
total_other_per_seed = {}
for seed in range(24):
    vrs = avg_visible_by_cid_per_seed[seed]
    avg_visible_per_seed[seed] = float(np.mean(vrs)) if vrs else 0.0
    # Sum of total_other_contacts per seed
    per_subj = V917 / "subjects" / f"per_subject_seed{seed}.csv"
    t = 0
    with open(per_subj) as f:
        for r in csv.DictReader(f):
            try:
                t += int(r["v917_total_other_contacts"])
            except ValueError:
                pass
    total_other_per_seed[seed] = t

avg_visible_seed_values = list(avg_visible_per_seed.values())
total_other_seed_values = list(total_other_per_seed.values())


# -----------------------------------------------------------------
# Output
# -----------------------------------------------------------------

# visible_ratio 区間別の取得量
vr_bins = [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.001]
fetched_by_vr_bin = defaultdict(list)
for v, f in zip(visible_ratios_all, fetched_counts_all):
    for i in range(len(vr_bins) - 1):
        if vr_bins[i] <= v < vr_bins[i+1]:
            fetched_by_vr_bin[f"[{vr_bins[i]:.1f},{vr_bins[i+1]:.1f})"].append(f)
            break

# n_core pair 組み合わせ表
ncore_pair_counter = Counter(all_ncore_pairs)
# n_core 分類用 bucket: <=2, 3, 4, >=5
def _bucket(nc):
    if nc <= 2: return "2"
    if nc == 3: return "3"
    if nc == 4: return "4"
    return "5+"
ncore_bucket_pairs = Counter(
    tuple(sorted([_bucket(a), _bucket(b)])) for (a, b) in all_ncore_pairs
)

# per-seed stats for ilog
ilog_rows_seed_arr = np.array(ilog_rows_per_seed)

# window 別分布 (step → window: cumulative_step / window_steps)
WINDOW_STEPS = 500
window_counts = Counter(step // WINDOW_STEPS for step in interaction_step)

# cid 接触回数分布を n_core 別に
contacts_by_ncore = defaultdict(list)
for seed in range(24):
    per_subj = V917 / "subjects" / f"per_subject_seed{seed}.csv"
    audit = V917 / "audit" / f"per_subject_audit_seed{seed}.csv"
    ncore_map = {}
    with open(audit) as f:
        for r in csv.DictReader(f):
            ncore_map[int(r["cid"])] = int(r["n_core_member"])
    with open(per_subj) as f:
        for r in csv.DictReader(f):
            cid = int(r["cognitive_id"])
            nc = ncore_map.get(cid)
            if nc is None:
                continue
            contacts_by_ncore[nc].append(int(r["v917_total_other_contacts"]))

# 接触体 cid vs 非接触体 cid 数
n_has_contact = sum(1 for c in total_other_contacts_by_cid if c > 0)
n_no_contact = sum(1 for c in total_other_contacts_by_cid if c == 0)

result = {
    "section_2": {  # 下層
        "visible_ratio": summarize_numeric(visible_ratios_all),
        "fetched_features_per_event": summarize_numeric(fetched_counts_all),
        "missing_features_per_event": summarize_numeric(missing_counts_all),
        "visible_ratio_by_ncore": {
            str(k): summarize_numeric(v)
            for k, v in sorted(visible_by_ncore.items())
        },
        "fetched_by_visible_ratio_bin": {
            k: summarize_numeric(v)
            for k, v in sorted(fetched_by_vr_bin.items())
        },
        "cid_total_other_contacts": summarize_numeric(total_other_contacts_by_cid),
        "cid_unique_contacts": summarize_numeric(unique_contacts_by_cid),
        "contacts_by_ncore": {
            str(k): summarize_numeric(v)
            for k, v in sorted(contacts_by_ncore.items())
        },
        "n_cids_with_contact": n_has_contact,
        "n_cids_without_contact": n_no_contact,
        "n_cids_total": n_has_contact + n_no_contact,
    },
    "section_3": {  # 上層
        "total_ilog_rows": sum(ilog_rows_per_seed),
        "total_unique_compositions_24seeds": len(comp_counter),
        "compositions_multi_occurrence": multi_compositions,
        "ncore_bucket_pair_counts": {
            f"{a}x{b}": n for (a, b), n in sorted(ncore_bucket_pairs.items(), key=lambda x: -x[1])
        },
        "age_factor_category": dict(age_factor_category),
        "interaction_step_distribution": summarize_numeric(interaction_step),
        "ilog_rows_per_seed_summary": summarize_numeric(ilog_rows_per_seed),
        "interactions_by_window": {str(k): v for k, v in sorted(window_counts.items())},
    },
    "section_4": {  # 整合
        "e3_events_total": e3_v917,
        "other_records_total": len(visible_ratios_all),
        "other_records_equals_e3": len(visible_ratios_all) == e3_v917,
        "ilog_rows_total": sum(ilog_rows_per_seed),
        "ilog_ratio_vs_e3_over_2": sum(ilog_rows_per_seed) / (e3_v917 / 2),
    },
    "section_5": {  # v9.16 比較
        "e3_events_v917": e3_v917,
        "e3_events_v916": e3_v916,
        "e3_events_equal": e3_v917 == e3_v916,
        "v915_fetch_count_v917": fetch_v917,
        "v915_fetch_count_v916": fetch_v916,
        "v915_fetch_count_equal": fetch_v917 == fetch_v916,
        "theta_diff_norm_all_max_abs_diff": theta_diff_max_diff,
        "theta_diff_cids_compared": theta_diff_cid_count,
    },
    "section_6": {  # seed 別分散
        "avg_visible_ratio_per_seed": avg_visible_per_seed,
        "avg_visible_ratio_cv": cv(avg_visible_seed_values),
        "total_other_contacts_per_seed": total_other_per_seed,
        "total_other_contacts_cv": cv(total_other_seed_values),
    },
}

out_path = "analyze_stage4_main_output.json"
with open(out_path, "w") as f:
    json.dump(result, f, indent=2, default=str)
print(f"written {out_path}")

# Print a compact summary
print()
print("=== Section 2: 下層 ===")
print(f"visible_ratio: {result['section_2']['visible_ratio']}")
print(f"fetched_features_per_event: {result['section_2']['fetched_features_per_event']}")
print(f"n_cids_with_contact: {n_has_contact} / n_cids_without_contact: {n_no_contact}")
print()
print("=== Section 3: 上層 ===")
print(f"total ilog rows: {sum(ilog_rows_per_seed)}")
print(f"unique compositions: {len(comp_counter)}, multi-occurrence: {multi_compositions}")
print(f"age_factor_category: {dict(age_factor_category)}")
print()
print("=== Section 5: v9.16 比較 ===")
print(f"E3 events: v917={e3_v917}, v916={e3_v916}, equal={e3_v917==e3_v916}")
print(f"v915_fetch_count: v917={fetch_v917}, v916={fetch_v916}, equal={fetch_v917==fetch_v916}")
print(f"theta_diff_norm_all max abs diff: {theta_diff_max_diff}")
print()
print("=== Section 6: 分散 ===")
print(f"avg_visible_ratio CV: {cv(avg_visible_seed_values):.4f}")
print(f"total_other_contacts CV: {cv(total_other_seed_values):.4f}")
