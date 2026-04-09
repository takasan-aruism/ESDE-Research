#!/usr/bin/env python3
"""
ESDE v9.8c — Information Pickup Results Aggregator
======================================================
Combines per-seed CSVs from v9.8c into unified summaries.
Builds on v9.8b aggregator; adds pickup statistics analysis.

If sibling baselines exist, also runs comparison:
  ../v98b/diag_v98b_introspection_{tag}/  → v98b comparison block (primary)
  ../v98a/diag_v98a_subject_{tag}/        → v98a comparison block
  ../v97/diag_v97_feedback_{tag}/         → v97 comparison block
  ../v96/diag_v96_baseline_{tag}/         → v96 comparison block
  All five available                      → 5-way summary at the end

USAGE (from primitive/v98c):
  python v98c_aggregate.py --tag short
  python v98c_aggregate.py --tag long

Layout assumed:
  primitive/v96/diag_v96_baseline_{tag}/         ← v96 baseline (optional)
  primitive/v97/diag_v97_feedback_{tag}/         ← v97 feedback (optional)
  primitive/v98a/diag_v98a_subject_{tag}/        ← v98a subject reversal (optional)
  primitive/v98b/diag_v98b_introspection_{tag}/  ← v98b introspection (optional)
  primitive/v98c/diag_v98c_pickup_{tag}/         ← v98c pickup (required)
  primitive/v98c/v98c_aggregate.py               ← THIS FILE
"""

import json, csv, argparse, glob
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict


# ════════════════════════════════════════════════════════════════
# Single-directory aggregation
# ════════════════════════════════════════════════════════════════
def _aggregate_one(base: Path, label: str, verbose: bool = True) -> dict:
    """Aggregate one diag directory. Returns metrics dict (or {} on missing)."""
    if not base.exists():
        if verbose:
            print(f"  ERROR: {base} not found")
        return {}

    if verbose:
        print(f"\n{'='*65}")
        print(f"  {label}")
        print(f"  Source: {base}")
        print(f"{'='*65}\n")

    metrics = {"label": label, "base": str(base)}

    # ── 1. per_window CSVs ──
    window_files = sorted(glob.glob(str(base / "aggregates" / "per_window_seed*.csv")))
    all_window_rows = []
    for f in window_files:
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                all_window_rows.append(row)

    n_seeds = len(window_files)
    if verbose:
        print(f"  Window CSVs: {n_seeds} seeds, {len(all_window_rows)} total rows")
    metrics["n_seeds"] = n_seeds
    metrics["n_window_rows"] = len(all_window_rows)

    if all_window_rows:
        combined_w = base / "aggregates" / "combined_window_summary.csv"
        with open(combined_w, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=all_window_rows[0].keys())
            writer.writeheader()
            writer.writerows(all_window_rows)

        by_window = defaultdict(list)
        for row in all_window_rows:
            w = int(row["window"])
            by_window[w].append(row)

        if verbose:
            # Detect v9.8a-specific columns
            has_subject_cols = "subject_count_total" in all_window_rows[0]
            print(f"\n  --- Per-Window Cross-Seed Summary ---\n")
            if has_subject_cols:
                print(f"  {'win':>4} {'seeds':>5} {'social':>7} {'spread':>7} "
                      f"{'famil':>7} {'recip':>6} {'cidT':>6} {'host':>5} "
                      f"{'ghost':>5} {'gDur':>5}")
            else:
                print(f"  {'win':>4} {'seeds':>5} {'social':>7} {'stabil':>7} "
                      f"{'spread':>7} {'famil':>7} {'recip':>6} {'asymm':>6} "
                      f"{'att_ov':>6} {'labels':>6}")
            print(f"  {'-'*70}")

        per_window_summary = {}
        for w in sorted(by_window.keys()):
            rows = by_window[w]
            ns = len(rows)
            ms = np.mean([float(r["mean_social"]) for r in rows])
            mst = np.mean([float(r["mean_stability"]) for r in rows])
            msp = np.mean([float(r["mean_spread"]) for r in rows])
            mf = np.mean([float(r["mean_familiarity"]) for r in rows])
            mr = np.mean([int(r["reciprocal_pairs"]) for r in rows])
            ma = np.mean([int(r["asymmetric_pairs"]) for r in rows])
            mo = np.mean([float(r["att_overlap_mean"]) for r in rows])
            ml = np.mean([int(r["v_labels"]) for r in rows])

            window_entry = {
                "social": ms, "stability": mst, "spread": msp,
                "familiarity": mf, "recip": mr, "asymm": ma,
                "att_overlap": mo, "labels": ml,
            }

            # v9.8a-specific
            if "subject_count_total" in rows[0]:
                cidT = np.mean([int(r["subject_count_total"]) for r in rows])
                host = np.mean([int(r["subject_hosted"]) for r in rows])
                ghost = np.mean([int(r["subject_ghost"]) for r in rows])
                gDur = np.mean([float(r.get("ghost_duration_mean", 0))
                                for r in rows])
                gBirth = np.mean([int(r.get("ghost_births", 0)) for r in rows])
                gReap = np.mean([int(r.get("ghost_reaped", 0)) for r in rows])
                window_entry.update({
                    "cid_total": cidT, "hosted": host, "ghost": ghost,
                    "ghost_dur_mean": gDur,
                    "ghost_births": gBirth, "ghost_reaped": gReap,
                })
                if verbose:
                    print(f"  {w:>4} {ns:>5} {ms:>7.3f} {msp:>7.4f} "
                          f"{mf:>7.2f} {mr:>6.1f} {cidT:>6.0f} {host:>5.1f} "
                          f"{ghost:>5.1f} {gDur:>5.2f}")
            else:
                if verbose:
                    print(f"  {w:>4} {ns:>5} {ms:>7.3f} {mst:>7.3f} "
                          f"{msp:>7.4f} {mf:>7.2f} {mr:>6.1f} {ma:>6.1f} "
                          f"{mo:>6.1f} {ml:>6.1f}")

            per_window_summary[w] = window_entry

        metrics["per_window"] = per_window_summary

        # Era deltas
        ws = sorted(by_window.keys())
        if len(ws) >= 2:
            first_w, last_w = ws[0], ws[-1]
            metrics["era"] = {
                "first_w": first_w, "last_w": last_w,
                "social_first": per_window_summary[first_w]["social"],
                "social_last": per_window_summary[last_w]["social"],
                "recip_first": per_window_summary[first_w]["recip"],
                "recip_last": per_window_summary[last_w]["recip"],
                "att_ov_first": per_window_summary[first_w]["att_overlap"],
                "att_ov_last": per_window_summary[last_w]["att_overlap"],
                "labels_first": per_window_summary[first_w]["labels"],
                "labels_last": per_window_summary[last_w]["labels"],
                "famil_first": per_window_summary[first_w]["familiarity"],
                "famil_last": per_window_summary[last_w]["familiarity"],
            }
            # v9.8a era
            if "cid_total" in per_window_summary[first_w]:
                metrics["era"].update({
                    "cidT_first": per_window_summary[first_w]["cid_total"],
                    "cidT_last": per_window_summary[last_w]["cid_total"],
                    "ghost_first": per_window_summary[first_w]["ghost"],
                    "ghost_last": per_window_summary[last_w]["ghost"],
                })

    # ── 2. per_label CSVs (v96/v97 ブリッジ) ──
    label_files = sorted(glob.glob(str(base / "labels" / "per_label_seed*.csv")))
    all_label_rows = []
    for f in label_files:
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                all_label_rows.append(row)

    if verbose:
        print(f"\n  Label CSVs: {len(label_files)} seeds, "
              f"{len(all_label_rows)} total labels")

    if all_label_rows:
        combined_l = base / "labels" / "combined_label_summary.csv"
        with open(combined_l, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=all_label_rows[0].keys())
            writer.writeheader()
            writer.writerows(all_label_rows)

        socials = [float(r["last_social"]) for r in all_label_rows
                   if r["last_social"]]
        stabilities = [float(r["last_stability"]) for r in all_label_rows
                       if r["last_stability"]]
        spreads = [float(r["last_spread"]) for r in all_label_rows
                   if r["last_spread"]]
        familiarities = [float(r["last_familiarity"]) for r in all_label_rows
                         if r["last_familiarity"]]
        lifespans = [int(r["lifespan"]) for r in all_label_rows
                     if r["lifespan"]]
        alive_count = sum(1 for r in all_label_rows if r["alive"] == "True")
        dead_count = sum(1 for r in all_label_rows if r["alive"] == "False")

        metrics["n_labels"] = len(all_label_rows)
        metrics["n_alive"] = alive_count
        metrics["n_dead"] = dead_count
        metrics["mean_lifespan"] = float(np.mean(lifespans)) if lifespans else 0.0
        metrics["dist_social_mean"] = float(np.mean(socials)) if socials else 0.0
        metrics["dist_stability_mean"] = float(np.mean(stabilities)) if stabilities else 0.0
        metrics["dist_spread_mean"] = float(np.mean(spreads)) if spreads else 0.0
        metrics["dist_familiarity_mean"] = float(np.mean(familiarities)) if familiarities else 0.0

        if verbose:
            print(f"\n  --- Label Population Summary ---\n")
            print(f"  Total labels: {len(all_label_rows)}")
            print(f"  Alive: {alive_count}  Dead: {dead_count}")
            print(f"  Mean lifespan: {np.mean(lifespans):.1f} windows "
                  f"(std={np.std(lifespans):.1f})")

        type_counter = Counter()
        for r in all_label_rows:
            tt = r.get("trajectory_type", "")
            for t in tt.split("|"):
                if t:
                    type_counter[t] += 1
        metrics["trajectory_types"] = dict(type_counter)

        # Death vs disposition
        dead_rows = [r for r in all_label_rows if r["alive"] == "False"
                     and r["last_social"]]
        alive_rows = [r for r in all_label_rows if r["alive"] == "True"
                      and r["last_social"]]

        if dead_rows and alive_rows:
            death_disposition = {}
            for field in ["last_social", "last_stability", "last_spread",
                          "last_familiarity", "last_partners"]:
                d_vals = [float(r[field]) for r in dead_rows if r[field]]
                a_vals = [float(r[field]) for r in alive_rows if r[field]]
                if d_vals and a_vals:
                    a_mean = float(np.mean(a_vals))
                    d_mean = float(np.mean(d_vals))
                    death_disposition[field] = {
                        "alive": a_mean, "dead": d_mean, "diff": a_mean - d_mean
                    }
            metrics["death_disposition"] = death_disposition

    # ── 3. per_subject CSVs (v9.8a only) ──
    subject_files = sorted(glob.glob(str(base / "subjects" / "per_subject_seed*.csv")))
    all_subject_rows = []
    for f in subject_files:
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                all_subject_rows.append(row)

    if subject_files and verbose:
        print(f"\n  Subject CSVs: {len(subject_files)} seeds, "
              f"{len(all_subject_rows)} total subjects")

    if all_subject_rows:
        states = Counter(r["final_state"] for r in all_subject_rows)
        ghost_durs = [int(r["ghost_duration"]) for r in all_subject_rows
                      if r.get("ghost_duration") and int(r["ghost_duration"]) > 0]

        metrics["n_subjects"] = len(all_subject_rows)
        metrics["subject_states"] = dict(states)
        metrics["ghost_duration_count"] = len(ghost_durs)
        if ghost_durs:
            metrics["ghost_duration_mean"] = float(np.mean(ghost_durs))
            metrics["ghost_duration_max"] = int(max(ghost_durs))
            metrics["ghost_duration_median"] = float(np.median(ghost_durs))

        if verbose:
            print(f"\n  --- Subject Layer Summary ---\n")
            print(f"  Total subjects (cid total): {len(all_subject_rows)}")
            print(f"  Final states:")
            for state, n in states.most_common():
                pct = n / len(all_subject_rows) * 100
                print(f"    {state:>10}: {n:>5} ({pct:>5.1f}%)")
            if ghost_durs:
                print(f"  Ghost duration (subjects with non-zero ghost period):")
                print(f"    count:  {len(ghost_durs)}")
                print(f"    mean:   {np.mean(ghost_durs):.2f} windows")
                print(f"    median: {np.median(ghost_durs):.1f}")
                print(f"    max:    {max(ghost_durs)}")

                # Histogram
                print(f"\n  Ghost duration distribution:")
                hist = Counter(ghost_durs)
                for dur in sorted(hist.keys()):
                    n = hist[dur]
                    bar = "█" * min(40, int(n / max(1, max(hist.values())) * 40))
                    print(f"    dur={dur:>2}: {n:>4} {bar}")

    # ── 4. Convergence bias ──
    bias_files = sorted(glob.glob(str(base / "aggregates" / "conv_bias_seed*.json")))
    ratios, conv_means, div_means = [], [], []

    for f in bias_files:
        with open(f) as fh:
            data = json.load(fh)
            if data.get("ratio") is not None:
                ratios.append(data["ratio"])
            if data.get("conv_near_mean") is not None:
                conv_means.append(data["conv_near_mean"])
            if data.get("div_near_mean") is not None:
                div_means.append(data["div_near_mean"])

    if verbose:
        print(f"\n  --- Convergence Near-Phase Bias ({len(bias_files)} seeds) ---\n")
    if ratios:
        metrics["conv_ratio_mean"] = float(np.mean(ratios))
        metrics["conv_ratio_std"] = float(np.std(ratios))
        metrics["conv_ratio_min"] = float(min(ratios))
        metrics["conv_ratio_max"] = float(max(ratios))
        metrics["conv_near_mean"] = float(np.mean(conv_means))
        metrics["div_near_mean"] = float(np.mean(div_means))
        metrics["conv_seeds_above_1"] = sum(1 for r in ratios if r > 1.0)
        metrics["conv_seeds_total"] = len(ratios)
        if verbose:
            print(f"    conv/div ratio: mean={np.mean(ratios):.2f} "
                  f"std={np.std(ratios):.2f} "
                  f"min={min(ratios):.2f} max={max(ratios):.2f}")
            above_1 = metrics["conv_seeds_above_1"]
            print(f"    Seeds with ratio > 1.0: {above_1}/{len(ratios)} "
                  f"({above_1/len(ratios)*100:.0f}%)")

    # ── 5. Introspection log (v9.8b only) ──
    intro_files = sorted(glob.glob(
        str(base / "introspection" / "introspection_log_seed*.csv")))
    all_intro_rows = []
    for f in intro_files:
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                all_intro_rows.append(row)

    if intro_files and verbose:
        print(f"\n  Introspection CSVs: {len(intro_files)} seeds, "
              f"{len(all_intro_rows)} total tag entries")

    if all_intro_rows:
        # タグ頻度分析
        tag_counter = Counter()
        n_tags_per_entry = []
        n_empty_entries = 0
        n_nonempty_entries = 0
        tag_by_state = {"hosted": Counter(), "ghost": Counter()}

        for row in all_intro_rows:
            tags_str = row.get("tags", "")
            state = row.get("state", "unknown")
            if tags_str:
                tags = tags_str.split("|")
                n_tags_per_entry.append(len(tags))
                n_nonempty_entries += 1
                for t in tags:
                    tag_counter[t] += 1
                    if state in tag_by_state:
                        tag_by_state[state][t] += 1
            else:
                n_tags_per_entry.append(0)
                n_empty_entries += 1

        metrics["n_intro_entries"] = len(all_intro_rows)
        metrics["n_intro_empty"] = n_empty_entries
        metrics["n_intro_nonempty"] = n_nonempty_entries
        metrics["tag_counter"] = dict(tag_counter)
        metrics["tag_entries_mean"] = float(np.mean(n_tags_per_entry)) \
            if n_tags_per_entry else 0.0

        if verbose:
            print(f"\n  --- Introspection Tag Analysis ---\n")
            print(f"    Total entries:      {len(all_intro_rows)}")
            print(f"    With tags:          {n_nonempty_entries} "
                  f"({n_nonempty_entries/len(all_intro_rows)*100:.1f}%)")
            print(f"    Empty (below threshold): {n_empty_entries} "
                  f"({n_empty_entries/len(all_intro_rows)*100:.1f}%)")
            print(f"    Mean tags per entry:   {metrics['tag_entries_mean']:.2f}")

            print(f"\n  Tag frequency (all axes):")
            max_count = max(tag_counter.values()) if tag_counter else 1
            for tag in ["gain_social", "loss_social",
                        "gain_stability", "loss_stability",
                        "gain_spread", "loss_spread",
                        "gain_familiarity", "loss_familiarity"]:
                n = tag_counter.get(tag, 0)
                bar = "█" * min(40, int(n / max(1, max_count) * 40))
                print(f"    {tag:>18}: {n:>6} {bar}")

            # Axis balance check
            print(f"\n  Axis balance (gain vs loss):")
            for axis in ["social", "stability", "spread", "familiarity"]:
                g = tag_counter.get(f"gain_{axis}", 0)
                l = tag_counter.get(f"loss_{axis}", 0)
                total = g + l
                if total > 0:
                    ratio = g / total
                    print(f"    {axis:>12}: gain={g:>5}  loss={l:>5}  "
                          f"gain_ratio={ratio:.2f}")

            # Delta statistics
            deltas = {
                "social": [float(r["delta_social"]) for r in all_intro_rows
                           if r.get("delta_social")],
                "stability": [float(r["delta_stability"]) for r in all_intro_rows
                              if r.get("delta_stability")],
                "spread": [float(r["delta_spread"]) for r in all_intro_rows
                           if r.get("delta_spread")],
                "familiarity": [float(r["delta_familiarity"]) for r in all_intro_rows
                                if r.get("delta_familiarity")],
            }
            print(f"\n  Delta statistics (absolute values):")
            print(f"    {'axis':>12}  {'mean':>8}  {'median':>8}  "
                  f"{'p90':>8}  {'max':>8}")
            for axis, vals in deltas.items():
                if vals:
                    abs_vals = [abs(v) for v in vals]
                    print(f"    {axis:>12}  {np.mean(abs_vals):>8.4f}  "
                          f"{np.median(abs_vals):>8.4f}  "
                          f"{np.percentile(abs_vals, 90):>8.4f}  "
                          f"{max(abs_vals):>8.4f}")

            metrics["delta_stats"] = {
                axis: {
                    "mean_abs": float(np.mean([abs(v) for v in vals])),
                    "median_abs": float(np.median([abs(v) for v in vals])),
                    "p90_abs": float(np.percentile([abs(v) for v in vals], 90)),
                    "max_abs": float(max([abs(v) for v in vals])),
                } if vals else None
                for axis, vals in deltas.items()
            }

    # ── 6. Pickup logs (v9.8c only) ──
    pickup_files = sorted(glob.glob(
        str(base / "pickup" / "pickup_log_seed*.csv")))
    death_pool_files = sorted(glob.glob(
        str(base / "pickup" / "death_pool_log_seed*.csv")))

    if pickup_files or death_pool_files:
        # Death pool log の集計
        all_death_records = []
        for f in death_pool_files:
            with open(f) as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    all_death_records.append(row)

        # Pickup log の集計
        all_pickups = []
        for f in pickup_files:
            with open(f) as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    all_pickups.append(row)

        n_records_total = len(all_death_records)
        n_consumed = sum(1 for r in all_death_records
                         if r.get("removal_reason") == "consumed")
        n_expired = sum(1 for r in all_death_records
                        if r.get("removal_reason") == "expired")
        n_active = sum(1 for r in all_death_records
                       if not r.get("removed_at") or r.get("removed_at") == "")

        n_pickups_total = len(all_pickups)
        n_uncontested = sum(1 for p in all_pickups
                            if p.get("outcome") == "uncontested")
        n_contested = sum(1 for p in all_pickups
                          if p.get("outcome") == "contested")

        # 競争統計: 候補数の分布
        candidate_counts = []
        winner_dists = []
        for p in all_pickups:
            try:
                candidate_counts.append(int(p.get("n_candidates", 0)))
                winner_dists.append(float(p.get("winner_phase_dist", 0)))
            except (ValueError, TypeError):
                pass

        # ttl_bonus 統計を per_subject から取る
        ttl_bonuses = []
        n_pickups_per_cid = []
        n_lost_per_cid = []
        for r in all_subject_rows:
            try:
                tb = int(r.get("ttl_bonus", 0))
                ttl_bonuses.append(tb)
                n_pickups_per_cid.append(int(r.get("n_pickups_won", 0)))
                n_lost_per_cid.append(int(r.get("n_pickups_lost", 0)))
            except (ValueError, TypeError):
                pass

        metrics["pickup"] = {
            "n_records_total": n_records_total,
            "n_consumed": n_consumed,
            "n_expired": n_expired,
            "n_active": n_active,
            "n_pickups_total": n_pickups_total,
            "n_uncontested": n_uncontested,
            "n_contested": n_contested,
            "consumption_rate": (n_consumed / n_records_total
                                  if n_records_total > 0 else 0),
            "contested_rate": (n_contested / n_pickups_total
                                if n_pickups_total > 0 else 0),
            "mean_ttl_bonus": float(np.mean(ttl_bonuses)) if ttl_bonuses else 0,
            "max_ttl_bonus": int(max(ttl_bonuses)) if ttl_bonuses else 0,
            "n_cids_with_bonus": sum(1 for b in ttl_bonuses if b > 0),
            "n_cids_total": len(ttl_bonuses),
        }

        if verbose:
            print(f"\n  --- Pickup Statistics (v9.8c) ---\n")
            print(f"  Death records: {n_records_total} total")
            print(f"    consumed:     {n_consumed:>5} "
                  f"({100*n_consumed/max(1,n_records_total):.1f}%)")
            print(f"    expired:      {n_expired:>5} "
                  f"({100*n_expired/max(1,n_records_total):.1f}%)")
            print(f"    still active: {n_active:>5}")

            print(f"\n  Pickup events: {n_pickups_total} total")
            print(f"    uncontested:  {n_uncontested:>5} "
                  f"({100*n_uncontested/max(1,n_pickups_total):.1f}%)")
            print(f"    contested:    {n_contested:>5} "
                  f"({100*n_contested/max(1,n_pickups_total):.1f}%)")

            if candidate_counts:
                print(f"\n  Candidate count distribution (per pickup):")
                cand_hist = Counter(candidate_counts)
                max_count = max(cand_hist.values())
                for n in sorted(cand_hist.keys()):
                    c = cand_hist[n]
                    bar = "█" * min(40, int(c / max_count * 40))
                    print(f"    n={n:>2}: {c:>5} {bar}")

            if winner_dists:
                print(f"\n  Winner phase distance:")
                print(f"    mean:   {np.mean(winner_dists):.4f}")
                print(f"    median: {np.median(winner_dists):.4f}")
                print(f"    max:    {max(winner_dists):.4f}")

            if ttl_bonuses:
                print(f"\n  TTL bonus distribution (per cid):")
                print(f"    cids with bonus:  {sum(1 for b in ttl_bonuses if b > 0)}/{len(ttl_bonuses)}")
                print(f"    mean bonus:       {np.mean(ttl_bonuses):.2f}")
                print(f"    max bonus:        {max(ttl_bonuses)}")
                bonus_hist = Counter(ttl_bonuses)
                print(f"    distribution:")
                max_count = max(bonus_hist.values())
                for b in sorted(bonus_hist.keys()):
                    c = bonus_hist[b]
                    bar = "█" * min(40, int(c / max_count * 40))
                    print(f"      bonus={b:>2}: {c:>5} {bar}")

    if verbose:
        print(f"\n{'='*65}")
        print(f"  AGGREGATION COMPLETE: {label}")
        print(f"{'='*65}\n")

    return metrics


# ════════════════════════════════════════════════════════════════
# Pairwise comparison (used for v98a vs v97 and v98a vs v96)
# ════════════════════════════════════════════════════════════════
def _format_delta(new_val, old_val, fmt=".4f"):
    if old_val is None or new_val is None:
        return "n/a"
    delta = new_val - old_val
    sign = "+" if delta >= 0 else ""
    return f"{old_val:{fmt}} → {new_val:{fmt}} ({sign}{delta:{fmt}})"


def _compare_pair(new_metrics: dict, old_metrics: dict,
                  new_name: str, old_name: str, tag: str):
    print(f"\n{'='*70}")
    print(f"  {old_name}  vs  {new_name}   ({tag})")
    print(f"{'='*70}\n")

    print(f"  --- Sample Sizes ---")
    print(f"    seeds:        {old_name}={old_metrics.get('n_seeds','?'):>5}  "
          f"{new_name}={new_metrics.get('n_seeds','?'):>5}")
    print(f"    labels total: {old_name}={old_metrics.get('n_labels','?'):>5}  "
          f"{new_name}={new_metrics.get('n_labels','?'):>5}")
    print(f"    alive:        {old_name}={old_metrics.get('n_alive','?'):>5}  "
          f"{new_name}={new_metrics.get('n_alive','?'):>5}")
    print(f"    dead:         {old_name}={old_metrics.get('n_dead','?'):>5}  "
          f"{new_name}={new_metrics.get('n_dead','?'):>5}")

    print(f"\n  --- Convergence Near-Phase Bias (structural property) ---")
    print(f"    conv/div ratio mean: "
          f"{_format_delta(new_metrics.get('conv_ratio_mean'), old_metrics.get('conv_ratio_mean'), '.3f')}")
    print(f"    conv near_phase:     "
          f"{_format_delta(new_metrics.get('conv_near_mean'), old_metrics.get('conv_near_mean'), '.4f')}")
    print(f"    div near_phase:      "
          f"{_format_delta(new_metrics.get('div_near_mean'), old_metrics.get('div_near_mean'), '.4f')}")

    print(f"\n  --- Disposition Distributions ---")
    for key, name, fmt in [("dist_social_mean", "social", ".4f"),
                           ("dist_stability_mean", "stability", ".4f"),
                           ("dist_spread_mean", "spread", ".4f"),
                           ("dist_familiarity_mean", "familiarity", ".2f")]:
        print(f"    {name:>12}: "
              f"{_format_delta(new_metrics.get(key), old_metrics.get(key), fmt)}")
    print(f"    {'lifespan':>12}: "
          f"{_format_delta(new_metrics.get('mean_lifespan'), old_metrics.get('mean_lifespan'), '.2f')}")

    new_dd = new_metrics.get("death_disposition", {})
    old_dd = old_metrics.get("death_disposition", {})
    if new_dd and old_dd:
        print(f"\n  --- Alive vs Dead Disposition Gap ---")
        for field in ["last_social", "last_stability", "last_spread",
                      "last_familiarity", "last_partners"]:
            new_diff = new_dd.get(field, {}).get("diff")
            old_diff = old_dd.get(field, {}).get("diff")
            print(f"    {field:>18}: "
                  f"{_format_delta(new_diff, old_diff, '.3f')}")

    new_era = new_metrics.get("era", {})
    old_era = old_metrics.get("era", {})
    if new_era and old_era:
        print(f"\n  --- Era Growth (first → last window, Δ within run) ---")
        print(f"    {'metric':>14}  {'{}'.format(old_name+' Δ'):>14}  "
              f"{'{}'.format(new_name+' Δ'):>14}  {'diff':>10}")
        print(f"    {'-'*60}")
        for key_first, key_last, name, fmt in [
            ("social_first", "social_last", "social", ".3f"),
            ("recip_first", "recip_last", "recip", ".1f"),
            ("att_ov_first", "att_ov_last", "att_overlap", ".1f"),
            ("labels_first", "labels_last", "labels", ".1f"),
            ("famil_first", "famil_last", "familiarity", ".2f"),
        ]:
            old_d = old_era.get(key_last, 0) - old_era.get(key_first, 0)
            new_d = new_era.get(key_last, 0) - new_era.get(key_first, 0)
            diff = new_d - old_d
            print(f"    {name:>14}  {old_d:>+14{fmt}}  {new_d:>+14{fmt}}  "
                  f"{diff:>+10{fmt}}")

    print(f"\n{'='*70}")


# ════════════════════════════════════════════════════════════════
# v9.8a-specific subject layer report
# ════════════════════════════════════════════════════════════════
def _report_subject_layer(v98a_metrics: dict, tag: str):
    print(f"\n{'='*70}")
    print(f"  v9.8a SUBJECT LAYER REPORT   ({tag})")
    print(f"{'='*70}\n")

    n_subj = v98a_metrics.get("n_subjects", 0)
    if n_subj == 0:
        print(f"  No subject data found.\n")
        return

    print(f"  --- Subject Lifecycle Census ---")
    print(f"    Total cids ever born:   {n_subj}")
    states = v98a_metrics.get("subject_states", {})
    for state, n in sorted(states.items()):
        pct = n / n_subj * 100
        print(f"    {state:>12}: {n:>5} ({pct:>5.1f}%)")

    print(f"\n  --- Ghost Duration ---")
    n_gd = v98a_metrics.get("ghost_duration_count", 0)
    if n_gd > 0:
        print(f"    Subjects with ghost period: {n_gd}")
        print(f"    Mean duration:    {v98a_metrics.get('ghost_duration_mean', 0):.2f} windows")
        print(f"    Median duration:  {v98a_metrics.get('ghost_duration_median', 0):.1f}")
        print(f"    Max duration:     {v98a_metrics.get('ghost_duration_max', 0)}")
    else:
        print(f"    No subjects entered ghost state with measurable duration.")

    print(f"\n  --- Survival Beyond Host Death ---")
    reaped = states.get("reaped", 0)
    ghosts_now = states.get("ghost", 0)
    hosted_now = states.get("hosted", 0)
    total_dead = reaped + ghosts_now
    if n_subj > 0:
        survived_pct = (total_dead / n_subj) * 100  # 全 dead が ghost を経由
        print(f"    Subjects that left host:    {total_dead}/{n_subj} "
              f"({survived_pct:.1f}%)")
        print(f"    Currently still hosted:     {hosted_now}")
        print(f"    Currently ghost (waiting):  {ghosts_now}")
        print(f"    Reaped (TTL exceeded):      {reaped}")

    print(f"\n  NOTE: TTL = 10 windows is a PROVISIONAL engineering value")
    print(f"        for memory/runtime control, not a theoretical claim.")
    print(f"        v9.8a observes the duration distribution; the value")
    print(f"        will be revisited based on data.")

    print(f"\n{'='*70}\n")


# ════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════
def run(tag="short"):
    # v98c (required, primary)
    v98c_base = Path(f"diag_v98c_pickup_{tag}")
    v98c_metrics = _aggregate_one(
        v98c_base, f"ESDE v9.8c — Information Pickup Aggregation ({tag})")

    if not v98c_metrics:
        return

    # subject layer report (v98c も subject layer を継承している)
    _report_subject_layer(v98c_metrics, tag)

    # v98b (optional, v9.8c の直接の先行)
    v98b_base = Path(f"../v98b/diag_v98b_introspection_{tag}")
    v98b_metrics = {}
    if v98b_base.exists():
        v98b_metrics = _aggregate_one(
            v98b_base, f"ESDE v9.8b — Minimal Introspection Aggregation ({tag})")
        if v98b_metrics:
            _compare_pair(v98c_metrics, v98b_metrics, "v98c", "v98b", tag)
    else:
        print(f"\n  NOTE: v98b not found at {v98b_base}")

    # v98a (optional)
    v98a_base = Path(f"../v98a/diag_v98a_subject_{tag}")
    v98a_metrics = {}
    if v98a_base.exists():
        v98a_metrics = _aggregate_one(
            v98a_base, f"ESDE v9.8a — Subject Reversal Aggregation ({tag})")
        if v98a_metrics:
            _compare_pair(v98c_metrics, v98a_metrics, "v98c", "v98a", tag)
    else:
        print(f"\n  NOTE: v98a not found at {v98a_base}")

    # v97 (optional)
    v97_base = Path(f"../v97/diag_v97_feedback_{tag}")
    v97_metrics = {}
    if v97_base.exists():
        v97_metrics = _aggregate_one(
            v97_base, f"ESDE v9.7 — Feedback Aggregation ({tag})")
        if v97_metrics:
            _compare_pair(v98c_metrics, v97_metrics, "v98c", "v97", tag)
    else:
        print(f"\n  NOTE: v97 not found at {v97_base}")

    # v96 (optional)
    v96_base = Path(f"../v96/diag_v96_baseline_{tag}")
    v96_metrics = {}
    if v96_base.exists():
        v96_metrics = _aggregate_one(
            v96_base, f"ESDE v9.6 — Baseline Aggregation ({tag})")
        if v96_metrics:
            _compare_pair(v98c_metrics, v96_metrics, "v98c", "v96", tag)
    else:
        print(f"\n  NOTE: v96 not found at {v96_base}")

    # 5-way summary if all available
    if v97_metrics and v96_metrics and v98a_metrics and v98b_metrics:
        print(f"\n{'='*70}")
        print(f"  5-WAY SUMMARY  v96 / v97 / v98a / v98b / v98c   ({tag})")
        print(f"{'='*70}\n")

        print(f"  --- Convergence Near-Phase Bias (structural anchor) ---")
        print(f"    {'version':>8}  {'ratio mean':>12}  {'conv':>8}  {'div':>8}")
        for name, m in [("v96", v96_metrics), ("v97", v97_metrics),
                        ("v98a", v98a_metrics), ("v98b", v98b_metrics),
                        ("v98c", v98c_metrics)]:
            r = m.get("conv_ratio_mean")
            c = m.get("conv_near_mean")
            d = m.get("div_near_mean")
            r_str = f"{r:.4f}" if r is not None else "n/a"
            c_str = f"{c:.4f}" if c is not None else "n/a"
            d_str = f"{d:.4f}" if d is not None else "n/a"
            print(f"    {name:>8}  {r_str:>12}  {c_str:>8}  {d_str:>8}")

        print(f"\n  --- Disposition (mean across all labels) ---")
        print(f"    {'metric':>12}  {'v96':>10}  {'v97':>10}  "
              f"{'v98a':>10}  {'v98b':>10}  {'v98c':>10}")
        for key, name in [("dist_social_mean", "social"),
                          ("dist_stability_mean", "stability"),
                          ("dist_spread_mean", "spread"),
                          ("dist_familiarity_mean", "familiarity"),
                          ("mean_lifespan", "lifespan")]:
            vals = []
            for m in [v96_metrics, v97_metrics, v98a_metrics,
                      v98b_metrics, v98c_metrics]:
                v = m.get(key)
                vals.append(f"{v:.4f}" if v is not None else "n/a")
            print(f"    {name:>12}  {vals[0]:>10}  {vals[1]:>10}  "
                  f"{vals[2]:>10}  {vals[3]:>10}  {vals[4]:>10}")

        print(f"\n  --- Sample Sizes ---")
        for name, m in [("v96", v96_metrics), ("v97", v97_metrics),
                        ("v98a", v98a_metrics), ("v98b", v98b_metrics),
                        ("v98c", v98c_metrics)]:
            print(f"    {name:>8}: seeds={m.get('n_seeds','?')}, "
                  f"labels={m.get('n_labels','?')}, "
                  f"alive={m.get('n_alive','?')}, "
                  f"dead={m.get('n_dead','?')}")

        # v98a vs v98b vs v98c の bit-level identity check
        # v9.8b は v98a と物理層 bit 一致していたが、
        # v9.8c は cog state を超えて TTL bonus を与えるので、
        # *物理層レベルでは* まだ bit 一致するはず (engine.state には触れない)。
        # ただし label の生死パターンが変わる可能性は非常に小さいがゼロではない:
        # cid_ttl_bonus は cog 内部のメタデータなので、reap タイミングだけが変わる。
        # vl.step や engine.state には影響しない。
        # → 期待: 物理層メトリクスは v98a/v98b/v98c で完全一致
        print(f"\n  --- v98a / v98b / v98c (physical layer identity check) ---")
        print(f"    All three should produce bit-identical physical layer outputs.")
        print(f"    v9.8c only adds cognitive-layer ttl_bonus (no engine.state changes).")
        for key, name in [("conv_ratio_mean", "conv_ratio"),
                          ("dist_stability_mean", "stability"),
                          ("dist_spread_mean", "spread"),
                          ("n_labels", "labels total"),
                          ("n_alive", "alive"),
                          ("n_dead", "dead")]:
            va = v98a_metrics.get(key)
            vb = v98b_metrics.get(key)
            vc = v98c_metrics.get(key)
            if va is not None and vb is not None and vc is not None:
                if isinstance(va, float):
                    diff_ab = vb - va
                    diff_ac = vc - va
                    match_ab = "EXACT" if abs(diff_ab) < 1e-10 else f"Δ={diff_ab:+.4e}"
                    match_ac = "EXACT" if abs(diff_ac) < 1e-10 else f"Δ={diff_ac:+.4e}"
                else:
                    diff_ab = vb - va
                    diff_ac = vc - va
                    match_ab = "EXACT" if diff_ab == 0 else f"Δ={diff_ab:+d}"
                    match_ac = "EXACT" if diff_ac == 0 else f"Δ={diff_ac:+d}"
                print(f"    {name:>14}: v98a={va}")
                print(f"    {' ':>14}  v98b={vb}  [v98a→v98b: {match_ab}]")
                print(f"    {' ':>14}  v98c={vc}  [v98a→v98c: {match_ac}]")

        # v98c-specific pickup summary
        pickup_data = v98c_metrics.get("pickup", {})
        if pickup_data:
            print(f"\n  --- v9.8c Pickup Summary ---")
            print(f"    Death records:    {pickup_data.get('n_records_total', 0)}")
            print(f"      consumed:       {pickup_data.get('n_consumed', 0)} "
                  f"({100*pickup_data.get('consumption_rate', 0):.1f}%)")
            print(f"      expired:        {pickup_data.get('n_expired', 0)}")
            print(f"    Pickup events:    {pickup_data.get('n_pickups_total', 0)}")
            print(f"      uncontested:    {pickup_data.get('n_uncontested', 0)}")
            print(f"      contested:      {pickup_data.get('n_contested', 0)} "
                  f"({100*pickup_data.get('contested_rate', 0):.1f}%)")
            print(f"    TTL bonus mean:   {pickup_data.get('mean_ttl_bonus', 0):.2f}")
            print(f"    TTL bonus max:    {pickup_data.get('max_ttl_bonus', 0)}")
            print(f"    cids with bonus:  {pickup_data.get('n_cids_with_bonus', 0)}/"
                  f"{pickup_data.get('n_cids_total', 0)}")

        print(f"\n{'='*70}")
        print(f"  END 5-WAY SUMMARY")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.8c Information Pickup Aggregator "
                    "(+ v98b/v98a/v97/v96 comparison, 5-way summary)")
    parser.add_argument("--tag", type=str, default="short")
    args = parser.parse_args()
    run(tag=args.tag)
