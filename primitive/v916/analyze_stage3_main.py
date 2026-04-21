"""
v9.16 段階 3 本番 run 集計スクリプト (Describe only)

diag_v916_main/ 配下の 24 seeds 結果を読み、指示書 §11 構成に沿った
基本統計・age_factor 分布・3 値分布・段階 2 比較を算出して出力する。

実行: python analyze_stage3_main.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path


V916 = Path(__file__).parent
V915S2 = V916.parent / "v915s2"
MAIN = V916 / "diag_v916_main"
S2_MAIN = V915S2 / "diag_v915s2_main"

SEEDS = list(range(24))


def md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path) -> list[dict]:
    with open(path) as f:
        return list(csv.DictReader(f))


def pct(num, denom):
    if denom == 0:
        return 0.0
    return 100.0 * num / denom


def quantile(xs: list[float], q: float) -> float:
    if not xs:
        return 0.0
    xs = sorted(xs)
    idx = max(0, min(len(xs) - 1, int(q * (len(xs) - 1))))
    return xs[idx]


def main():
    out: dict = {}

    # --------------------------------------------------------------
    # 0. bit-identity baseline (v9.14) md5 vs seed0 production
    # --------------------------------------------------------------
    v914_main = V916.parent / "v914" / "diag_v914_long"
    baseline_files = [
        ("aggregates", "per_window_seed0.csv"),
        ("pulse", "pulse_log_seed0.csv"),
        ("labels", "per_label_seed0.csv"),
        ("audit", "per_event_audit_seed0.csv"),
        ("audit", "per_subject_audit_seed0.csv"),
        ("audit", "run_level_audit_summary_seed0.csv"),
    ]
    bi_check: list[dict] = []
    if v914_main.exists():
        for sub, name in baseline_files:
            p_v916 = MAIN / sub / name
            p_v914 = v914_main / sub / name
            if p_v916.exists() and p_v914.exists():
                bi_check.append({
                    "file": f"{sub}/{name}",
                    "v916_md5": md5(p_v916),
                    "v914_md5": md5(p_v914),
                    "match": md5(p_v916) == md5(p_v914),
                })
    out["bit_identity_v914_main"] = bi_check

    # --------------------------------------------------------------
    # 1. Fetch 総数 / event 分布 (24 seeds 合算)
    # --------------------------------------------------------------
    total_obs_rows = 0
    per_seed_obs_rows = {}
    per_event_type_rows = defaultdict(int)
    per_seed_total_events = {}
    for s in SEEDS:
        p_obs = MAIN / "selfread" / f"observation_log_seed{s}.csv"
        if not p_obs.exists():
            continue
        rows = load(p_obs)
        per_seed_obs_rows[s] = len(rows)
        total_obs_rows += len(rows)
        for r in rows:
            per_event_type_rows[r["event_type_coarse"]] += 1

        # per_event_audit 行数も取る (Fetch 総数整合確認用)
        p_ev = MAIN / "audit" / f"per_event_audit_seed{s}.csv"
        if p_ev.exists():
            with open(p_ev) as f:
                per_seed_total_events[s] = sum(1 for _ in f) - 1

    out["obs_log_total_rows"] = total_obs_rows
    out["obs_log_per_seed"] = per_seed_obs_rows
    out["event_type_distribution"] = dict(per_event_type_rows)
    out["per_event_audit_per_seed"] = per_seed_total_events

    # v915s2 main fetch 総数 (per_cid_self で比較)
    v915s2_fetch_by_seed = {}
    v916_fetch_by_seed = {}
    for s in SEEDS:
        p_s2 = S2_MAIN / "selfread" / f"per_cid_self_seed{s}.csv"
        p_v916 = MAIN / "selfread" / f"per_cid_self_seed{s}.csv"
        if p_s2.exists():
            rows = load(p_s2)
            v915s2_fetch_by_seed[s] = sum(int(r["fetch_count"]) for r in rows)
        if p_v916.exists():
            rows = load(p_v916)
            v916_fetch_by_seed[s] = sum(int(r["fetch_count"]) for r in rows)
    out["fetch_total_v915s2_per_seed"] = v915s2_fetch_by_seed
    out["fetch_total_v916_per_seed"] = v916_fetch_by_seed
    out["fetch_total_all_seeds_v915s2"] = sum(v915s2_fetch_by_seed.values())
    out["fetch_total_all_seeds_v916"] = sum(v916_fetch_by_seed.values())
    out["fetch_total_match"] = (
        v915s2_fetch_by_seed == v916_fetch_by_seed
    )

    # --------------------------------------------------------------
    # 2. age_factor 分布 (全 obs_log 行集計)
    # --------------------------------------------------------------
    all_af: list[float] = []
    af_by_ncore = defaultdict(list)
    af_by_event_type = defaultdict(list)
    # 全セルの 3 値 count
    total_match_cells = 0
    total_mismatch_cells = 0
    total_missing_cells = 0
    for s in SEEDS:
        p = MAIN / "selfread" / f"observation_log_seed{s}.csv"
        if not p.exists():
            continue
        for r in load(p):
            af = float(r["age_factor"])
            nc = int(r["n_core"])
            et = r["event_type_coarse"]
            all_af.append(af)
            af_by_ncore[nc].append(af)
            af_by_event_type[et].append(af)
            total_match_cells += int(r["match_count"])
            total_mismatch_cells += int(r["mismatch_count"])
            total_missing_cells += int(r["missing_count"])

    def _af_stats(vals):
        if not vals:
            return None
        return {
            "n": len(vals),
            "min": round(min(vals), 4),
            "q25": round(quantile(vals, 0.25), 4),
            "median": round(statistics.median(vals), 4),
            "mean": round(statistics.mean(vals), 4),
            "q75": round(quantile(vals, 0.75), 4),
            "max": round(max(vals), 4),
        }

    out["age_factor_all"] = _af_stats(all_af)
    out["age_factor_by_ncore"] = {
        nc: _af_stats(vals) for nc, vals in sorted(af_by_ncore.items())
    }
    out["age_factor_by_event_type"] = {
        et: _af_stats(vals) for et, vals in sorted(af_by_event_type.items())
    }

    # --------------------------------------------------------------
    # 3. 3 値分布 (node-cell level, 全 obs_log)
    # --------------------------------------------------------------
    total_cells = total_match_cells + total_mismatch_cells + total_missing_cells
    out["three_value_cells"] = {
        "match": total_match_cells,
        "mismatch": total_mismatch_cells,
        "missing": total_missing_cells,
        "total": total_cells,
        "match_pct": round(pct(total_match_cells, total_cells), 2),
        "mismatch_pct": round(pct(total_mismatch_cells, total_cells), 2),
        "missing_pct": round(pct(total_missing_cells, total_cells), 2),
    }

    # --------------------------------------------------------------
    # 3b. 3 値分布 × event 種別
    # --------------------------------------------------------------
    three_val_by_event = defaultdict(
        lambda: {"match": 0, "mismatch": 0, "missing": 0}
    )
    for s in SEEDS:
        p = MAIN / "selfread" / f"observation_log_seed{s}.csv"
        if not p.exists():
            continue
        for r in load(p):
            et = r["event_type_coarse"]
            three_val_by_event[et]["match"] += int(r["match_count"])
            three_val_by_event[et]["mismatch"] += int(r["mismatch_count"])
            three_val_by_event[et]["missing"] += int(r["missing_count"])
    for et, d in three_val_by_event.items():
        t = d["match"] + d["mismatch"] + d["missing"]
        d["total"] = t
        d["match_pct"] = round(pct(d["match"], t), 2)
        d["mismatch_pct"] = round(pct(d["mismatch"], t), 2)
        d["missing_pct"] = round(pct(d["missing"], t), 2)
    out["three_value_by_event"] = dict(three_val_by_event)

    # --------------------------------------------------------------
    # 4. age_factor 区間別の 3 値比率
    # --------------------------------------------------------------
    af_bins = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6),
               (0.6, 0.8), (0.8, 1.0 + 1e-9)]
    af_bin_3val = {f"[{lo:.1f},{hi:.1f})":
                   {"match": 0, "mismatch": 0, "missing": 0,
                    "event_rows": 0}
                   for lo, hi in af_bins}
    for s in SEEDS:
        p = MAIN / "selfread" / f"observation_log_seed{s}.csv"
        if not p.exists():
            continue
        for r in load(p):
            af = float(r["age_factor"])
            for lo, hi in af_bins:
                if lo <= af < hi:
                    key = f"[{lo:.1f},{hi:.1f})"
                    af_bin_3val[key]["match"] += int(r["match_count"])
                    af_bin_3val[key]["mismatch"] += int(r["mismatch_count"])
                    af_bin_3val[key]["missing"] += int(r["missing_count"])
                    af_bin_3val[key]["event_rows"] += 1
                    break
    for key, d in af_bin_3val.items():
        t = d["match"] + d["mismatch"] + d["missing"]
        d["total_cells"] = t
        d["match_pct"] = round(pct(d["match"], t), 2)
        d["mismatch_pct"] = round(pct(d["mismatch"], t), 2)
        d["missing_pct"] = round(pct(d["missing"], t), 2)
    out["three_value_by_age_factor_bin"] = af_bin_3val

    # --------------------------------------------------------------
    # 5. cid レベル統計 (per_cid_self 集約、fetched のみ)
    # --------------------------------------------------------------
    total_cids = 0
    fetched_cids = 0
    cids_any_mismatch = 0
    cids_with_missing = 0
    cids_fully_blind = 0
    cids_q_zero_ever = 0  # age_factor_final == 0 の cid
    af_final_values: list[float] = []
    af_avg_values: list[float] = []
    q0_hist = defaultdict(int)
    for s in SEEDS:
        p = MAIN / "selfread" / f"per_cid_self_seed{s}.csv"
        if not p.exists():
            continue
        for r in load(p):
            total_cids += 1
            fc = int(r["fetch_count"])
            q0_hist[int(r["Q0"])] += 1
            if fc == 0:
                continue
            fetched_cids += 1
            if r["any_mismatch_ever"] == "True":
                cids_any_mismatch += 1
            if int(r["total_missing_count"]) > 0:
                cids_with_missing += 1
            if int(r["total_observed_count"]) == 0:
                cids_fully_blind += 1
            af_f_str = r["age_factor_final"]
            if af_f_str != "unformed":
                af_f = float(af_f_str)
                af_final_values.append(af_f)
                if af_f == 0.0:
                    cids_q_zero_ever += 1
            af_avg_str = r["avg_age_factor"]
            if af_avg_str != "unformed":
                af_avg_values.append(float(af_avg_str))

    out["cid_level"] = {
        "total_registry_cids": total_cids,
        "fetched_cids": fetched_cids,
        "cids_any_mismatch_ever": cids_any_mismatch,
        "cids_with_missing": cids_with_missing,
        "cids_with_missing_pct": round(pct(cids_with_missing, fetched_cids), 2),
        "cids_fully_blind": cids_fully_blind,
        "cids_q_zero_final": cids_q_zero_ever,
        "cids_q_zero_final_pct": round(pct(cids_q_zero_ever, fetched_cids), 2),
        "age_factor_final_stats": _af_stats(af_final_values),
        "age_factor_avg_stats": _af_stats(af_avg_values),
    }
    # top Q0 distribution (集約)
    q0_dist = sorted(q0_hist.items())
    out["q0_distribution_head"] = q0_dist[:15]
    out["q0_distribution_tail"] = q0_dist[-5:]

    # --------------------------------------------------------------
    # 6. 段階 2 との theta_diff_norm 比較 (divergence_log)
    #    v9.15s2: theta_diff_norm, v9.16: theta_diff_norm_all (同計算のはず)
    # --------------------------------------------------------------
    # seed0 だけでサンプル比較 (同一 cid/step ペアで値が一致するか)
    p_v916_div = MAIN / "selfread" / "divergence_log_seed0.csv"
    p_s2_div = S2_MAIN / "selfread" / "divergence_log_seed0.csv"
    div_compare = {}
    if p_v916_div.exists() and p_s2_div.exists():
        rows_v916 = load(p_v916_div)
        rows_s2 = load(p_s2_div)
        # key: (cid_id, step, event_type_full)
        key_v916 = {(r["cid_id"], r["step"], r["event_type_full"]):
                    float(r["theta_diff_norm_all"]) for r in rows_v916}
        key_s2 = {(r["cid_id"], r["step"], r["event_type_full"]):
                  float(r["theta_diff_norm"]) for r in rows_s2}
        common = set(key_v916) & set(key_s2)
        diffs = [abs(key_v916[k] - key_s2[k]) for k in common]
        div_compare = {
            "v916_rows": len(rows_v916),
            "v915s2_rows": len(rows_s2),
            "common_keys": len(common),
            "max_abs_diff": round(max(diffs), 6) if diffs else 0.0,
            "mean_abs_diff": round(
                sum(diffs) / len(diffs), 6) if diffs else 0.0,
        }
    out["divergence_all_vs_s2"] = div_compare

    # --------------------------------------------------------------
    # 7. theta_diff_norm_observed の分布 (段階 3 新規、n_observed>0 のみ)
    # --------------------------------------------------------------
    obs_div_vals = []
    obs_div_norm_vals = []
    for s in SEEDS:
        p = MAIN / "selfread" / f"divergence_log_seed{s}.csv"
        if not p.exists():
            continue
        for r in load(p):
            n_obs = int(r["n_observed"])
            if n_obs > 0:
                obs_div_vals.append(float(r["theta_diff_norm_observed"]))
                obs_div_norm_vals.append(
                    float(r["theta_diff_norm_observed_normalized"]))
    out["theta_diff_norm_observed_stats"] = _af_stats(obs_div_vals)
    out["theta_diff_norm_observed_normalized_stats"] = _af_stats(
        obs_div_norm_vals)

    # --------------------------------------------------------------
    # 8. Seed 別 CV (age_factor 平均 / missing_fraction)
    # --------------------------------------------------------------
    seed_af_mean = {}  # seed -> mean age_factor (fetched cid 平均)
    seed_miss_frac = {}  # seed -> mean final_missing_fraction
    for s in SEEDS:
        p = MAIN / "selfread" / f"per_cid_self_seed{s}.csv"
        if not p.exists():
            continue
        af_vals, mf_vals = [], []
        for r in load(p):
            if int(r["fetch_count"]) == 0:
                continue
            if r["avg_age_factor"] != "unformed":
                af_vals.append(float(r["avg_age_factor"]))
            if r["final_missing_fraction"] != "unformed":
                mf_vals.append(float(r["final_missing_fraction"]))
        if af_vals:
            seed_af_mean[s] = statistics.mean(af_vals)
        if mf_vals:
            seed_miss_frac[s] = statistics.mean(mf_vals)

    def cv(d):
        vs = list(d.values())
        if len(vs) < 2:
            return 0.0
        m = statistics.mean(vs)
        sd = statistics.stdev(vs)
        return round(sd / m, 4) if m != 0 else 0.0

    out["seed_cv"] = {
        "avg_age_factor_mean_per_seed_CV": cv(seed_af_mean),
        "final_missing_fraction_mean_per_seed_CV": cv(seed_miss_frac),
        "avg_age_factor_per_seed": {
            k: round(v, 4) for k, v in sorted(seed_af_mean.items())},
        "final_missing_fraction_per_seed": {
            k: round(v, 4) for k, v in sorted(seed_miss_frac.items())},
    }

    # --------------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------------
    json_out = V916 / "analyze_stage3_main_output.json"
    with open(json_out, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {json_out}")

    # 短い要約
    print("\n=== SUMMARY ===")
    print(f"Fetch 総数一致 (v916 vs v915s2): {out['fetch_total_match']}")
    print(f"v916 total fetch: {out['fetch_total_all_seeds_v916']}")
    print(f"v915s2 total fetch: {out['fetch_total_all_seeds_v915s2']}")
    print(f"obs_log rows: {out['obs_log_total_rows']}")
    print(f"age_factor mean (all events): {out['age_factor_all']['mean']}")
    print(f"age_factor median: {out['age_factor_all']['median']}")
    print(f"3 値 (match/mismatch/missing): "
          f"{out['three_value_cells']['match_pct']}% / "
          f"{out['three_value_cells']['mismatch_pct']}% / "
          f"{out['three_value_cells']['missing_pct']}%")
    print(f"fetched cid: {out['cid_level']['fetched_cids']}")
    print(f"cids_with_missing: {out['cid_level']['cids_with_missing']} "
          f"({out['cid_level']['cids_with_missing_pct']}%)")
    print(f"cids_q_zero_final: {out['cid_level']['cids_q_zero_final']} "
          f"({out['cid_level']['cids_q_zero_final_pct']}%)")
    print(f"divergence max abs diff vs v915s2: "
          f"{out['divergence_all_vs_s2'].get('max_abs_diff', 'N/A')}")
    print(f"seed CV avg_age_factor: "
          f"{out['seed_cv']['avg_age_factor_mean_per_seed_CV']}")
    print(f"seed CV final_missing_fraction: "
          f"{out['seed_cv']['final_missing_fraction_mean_per_seed_CV']}")


if __name__ == "__main__":
    main()
