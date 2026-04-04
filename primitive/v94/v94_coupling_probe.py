#!/usr/bin/env python3
"""
ESDE v9.4 — Label-to-Label Coupling Probe
============================================
Measures how each label's torque affects other labels' local equilibrium
during sequential application.

For each label's torque application in detail windows:
  - Record theta snapshot of ALL label patches BEFORE
  - Apply torque (single label, sequential)
  - Record theta snapshot AFTER
  - Compute per-label impact: how much did OTHER labels' patches change?

This gives a label-to-label interaction matrix per window.

USAGE:
  python v94_coupling_probe.py --seed 42
"""

import sys, math, time, json, argparse
import numpy as np
from pathlib import Path
from collections import defaultdict

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_V82_DIR = _REPO_ROOT / "autonomy" / "v82"
_V43_DIR = _REPO_ROOT / "cognition" / "semantic_injection" / "v4_pipeline" / "v43"
_V41_DIR = _V43_DIR.parent / "v41"
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_SCRIPT_DIR), str(_V82_DIR), str(_V43_DIR), str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from esde_v82_engine import (V82Engine, V82EncapsulationParams,
                              V82_WINDOW, V82_N, find_islands_sets,
                              apply_stress_decay)
from v19g_canon import BASE_PARAMS
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9


# ================================================================
# LABEL PATCH SNAPSHOT
# ================================================================
def snapshot_label_patches(state, labels, macro_nodes):
    """For each label, compute mean theta of its alive nodes."""
    patches = {}
    for lid, label in labels.items():
        if lid in macro_nodes:
            continue
        thetas = [float(state.theta[n]) for n in label["nodes"]
                  if n in state.alive_n]
        if len(thetas) >= 2:
            sin_s = sum(math.sin(t) for t in thetas)
            cos_s = sum(math.cos(t) for t in thetas)
            patches[lid] = {
                "mean_theta": math.atan2(sin_s, cos_s),
                "theta_std": float(np.std(thetas)),
                "n_alive": len(thetas),
            }
        elif len(thetas) == 1:
            patches[lid] = {
                "mean_theta": thetas[0],
                "theta_std": 0.0,
                "n_alive": 1,
            }
    return patches


def compute_impact(pre_patches, post_patches, actor_lid):
    """Compute how much each label's patch changed due to actor's torque."""
    impacts = {}
    for lid in pre_patches:
        if lid == actor_lid:
            continue
        if lid not in post_patches:
            continue
        pre = pre_patches[lid]["mean_theta"]
        post = post_patches[lid]["mean_theta"]
        # Circular difference
        d = post - pre
        # Normalize to [-pi, pi]
        while d > math.pi: d -= 2 * math.pi
        while d < -math.pi: d += 2 * math.pi
        impacts[lid] = {
            "delta_theta": round(d, 6),
            "abs_delta": round(abs(d), 6),
        }
    return impacts


# ================================================================
# SINGLE-LABEL TORQUE (extracted from VL sequential loop)
# ================================================================
def apply_single_label_torque(state, label, lid, vl, substrate):
    """Apply torque for ONE label. Returns torque magnitude applied."""
    budget = 1.0
    energy = budget * label["share"]
    if energy < 0.0001:
        return 0.0

    window_count = vl._last_window_count if hasattr(vl, '_last_window_count') else 0
    age = window_count - label["born"]
    rigidity_factor = 1.0 / (1.0 + vl.rigidity_beta * age)
    torque_mag = energy * rigidity_factor * vl._torque_multiplier
    total_applied = 0.0

    # Core torque
    for n in label["nodes"]:
        if n not in state.alive_n:
            continue
        theta_n = float(state.theta[n])
        torque = torque_mag * math.sin(label["phase_sig"] - theta_n)
        state.theta[n] += torque
        total_applied += abs(torque)

    # Semantic gravity
    if substrate and vl.semantic_gravity_enabled:
        gf = vl._gravity_factors.get(lid, 1.0)
        grav_mag = torque_mag / max(1, len(label["nodes"])) * gf
        for n in label["nodes"]:
            for nb in substrate.get(n, set()):
                if nb not in state.alive_n:
                    continue
                if nb in label["nodes"]:
                    continue
                theta_nb = float(state.theta[nb])
                grav_torque = grav_mag * math.sin(
                    label["phase_sig"] - theta_nb)
                state.theta[nb] += grav_torque
                total_applied += abs(grav_torque)

    return total_applied


# ================================================================
# MAIN PROBE
# ================================================================
def run_coupling_probe(seed=42, n_windows=25, detail_start=20,
                       window_steps=500, top_k=10):
    """
    Run engine to maturation, then in detail windows:
    decompose sequential torque label-by-label and record
    inter-label impacts.
    """
    print(f"\n{'='*65}")
    print(f"  ESDE v9.4 — Label-to-Label Coupling Probe")
    print(f"  seed={seed} steps/win={window_steps} "
          f"detail_start={detail_start} top_k={top_k}")
    print(f"{'='*65}\n")

    t_start = time.time()

    # Build engine (same as v9.3 best condition)
    encap_params = V82EncapsulationParams(
        stress_enabled=False, virtual_enabled=True)
    engine = V82Engine(seed=seed, N=V82_N, encap_params=encap_params)

    engine.virtual = VirtualLayerV9(
        feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True

    engine.run_injection()
    print(f"  Injection done. links={len(engine.state.alive_l)}")

    # ── Maturation ──
    print(f"  Maturation ({detail_start} windows)...")
    for w in range(detail_start):
        engine.step_window(steps=window_steps)
        if w % 5 == 0:
            print(f"    w={w} links={len(engine.state.alive_l)} "
                  f"vLb={len(engine.virtual.labels)}")

    print(f"  Maturation done. labels={len(engine.virtual.labels)}")

    # ── Detail Windows ──
    n_detail = n_windows - detail_start
    print(f"\n  --- Detail Phase ({n_detail} windows) ---\n")

    coupling_log = []  # per-window coupling data

    for w in range(detail_start, n_windows):
        t0 = time.time()
        vl = engine.virtual

        # ── DESIGN NOTE (V94-2): Physical layer is FROZEN in detail windows.
        # Only theta changes via torque are measured. No decay, no realizer,
        # no chemistry, no resonance. This is intentional: we measure
        # pure θ-space coupling between labels, isolated from physics.
        # Physical dynamics (§4.2 repair response) will be added in v9.4b.

        # Increment window_count (#V94-1 fix)
        engine.window_count += 1

        # Run birth/share/cull via normal step() FIRST
        # But we need to intercept the torque part.
        # Strategy: run step() with torque disabled, then do torque manually.

        # Save torque state
        saved_multiplier = vl._torque_multiplier

        # Run step() but skip torque by setting multiplier to 0
        vl._torque_multiplier = 0.0
        isl_m = find_islands_sets(engine.state, 0.20)

        class _Isl:
            pass
        islands_dict = {}
        for i, isl in enumerate(isl_m):
            obj = _Isl()
            obj.nodes = isl
            islands_dict[i] = obj

        vs = vl.step(engine.state, engine.window_count,
                      islands=islands_dict, substrate=engine.substrate)
        engine.virtual_stats = vs

        # Restore multiplier
        vl._torque_multiplier = saved_multiplier
        vl._last_window_count = engine.window_count

        # Now manually apply torque label-by-label with coupling measurement
        import random as _rnd
        label_ids = [lid for lid in vl.labels if lid not in vl.macro_nodes]
        # age order
        label_ids.sort(key=lambda lid: vl.labels[lid]["born"])

        # Select top-K labels by share for detailed tracking
        all_by_share = sorted(label_ids,
                               key=lambda lid: vl.labels[lid]["share"],
                               reverse=True)
        tracked = set(all_by_share[:top_k])

        window_interactions = []

        for lid in label_ids:
            label = vl.labels[lid]
            energy = 1.0 * label["share"]
            if energy < 0.0001:
                continue

            # Only record full interaction matrix for tracked labels
            if lid in tracked:
                pre = snapshot_label_patches(engine.state, vl.labels, vl.macro_nodes)

            # Apply this label's torque
            mag = apply_single_label_torque(
                engine.state, label, lid, vl, engine.substrate)

            if lid in tracked and mag > 0:
                post = snapshot_label_patches(engine.state, vl.labels, vl.macro_nodes)
                impacts = compute_impact(pre, post, lid)

                # Find top impacted labels
                sorted_impacts = sorted(impacts.items(),
                                         key=lambda x: x[1]["abs_delta"],
                                         reverse=True)

                window_interactions.append({
                    "actor": lid,
                    "actor_share": round(label["share"], 6),
                    "actor_age": engine.window_count - label["born"],
                    "actor_nodes": len(label["nodes"]),
                    "torque_mag": round(mag, 6),
                    "n_impacted": sum(1 for _, v in sorted_impacts
                                      if v["abs_delta"] > 0.0001),
                    "top5_impacts": [
                        {"target": tid,
                         "target_share": round(vl.labels[tid]["share"], 6),
                         "target_nodes": len(vl.labels[tid]["nodes"]),
                         "delta_theta": v["delta_theta"],
                         "abs_delta": v["abs_delta"]}
                        for tid, v in sorted_impacts[:5]
                    ],
                    "self_delta": round(
                        post.get(lid, {}).get("mean_theta", 0) -
                        pre.get(lid, {}).get("mean_theta", 0), 6)
                    if lid in post and lid in pre else 0,
                })

        # Collect stats
        links = len(engine.state.alive_l)
        n_labels = len(vl.labels)

        # Summary
        n_actors = len(window_interactions)
        if window_interactions:
            mean_impacted = np.mean([x["n_impacted"] for x in window_interactions])
            mean_top_delta = np.mean([
                x["top5_impacts"][0]["abs_delta"]
                for x in window_interactions if x["top5_impacts"]])
        else:
            mean_impacted = 0
            mean_top_delta = 0

        coupling_log.append({
            "window": w,
            "links": links,
            "n_labels": n_labels,
            "n_tracked_actors": n_actors,
            "mean_impacted": round(float(mean_impacted), 1),
            "mean_top_delta": round(float(mean_top_delta), 6),
            "interactions": window_interactions,
        })

        sec = time.time() - t0
        print(f"  w={w:>3} links={links:>5} vLb={n_labels:>3} "
              f"actors={n_actors} impacted={mean_impacted:.1f} "
              f"top_Δθ={mean_top_delta:.5f} {sec:.0f}s")

    # ── Summary ──
    print(f"\n{'='*65}")
    print(f"  SUMMARY")
    print(f"{'='*65}\n")

    # Aggregate across all detail windows
    all_interactions = []
    for entry in coupling_log:
        all_interactions.extend(entry["interactions"])

    if all_interactions:
        # §4.1: Does a label's action affect other labels?
        all_impacted = [x["n_impacted"] for x in all_interactions]
        print(f"  §4.1 Label impact reach:")
        print(f"    Mean labels impacted per actor: {np.mean(all_impacted):.1f}")
        print(f"    Max labels impacted: {max(all_impacted)}")
        print(f"    Actors with 0 impact: "
              f"{sum(1 for x in all_impacted if x == 0)}/{len(all_impacted)}")

        # §4.4: Does response depend on target identity?
        # Group by actor, show if different targets get different impacts
        actor_targets = defaultdict(list)
        for x in all_interactions:
            for t in x["top5_impacts"]:
                actor_targets[x["actor"]].append(t["abs_delta"])

        print(f"\n  §4.4 Response variation by target:")
        for actor in list(actor_targets.keys())[:5]:
            deltas = actor_targets[actor]
            if len(deltas) >= 2:
                print(f"    Actor {actor}: "
                      f"mean={np.mean(deltas):.6f} "
                      f"std={np.std(deltas):.6f} "
                      f"range={min(deltas):.6f}-{max(deltas):.6f}")

        # Recurring pairs (§4.3: stable patterns)
        pair_counts = defaultdict(list)
        for x in all_interactions:
            for t in x["top5_impacts"]:
                pair_counts[(x["actor"], t["target"])].append(t["abs_delta"])

        recurring = {k: v for k, v in pair_counts.items() if len(v) >= 3}
        print(f"\n  §4.3 Recurring interaction pairs (3+ windows):")
        print(f"    Total recurring pairs: {len(recurring)}")
        for (a, t), deltas in sorted(recurring.items(),
                                       key=lambda x: np.mean(x[1]),
                                       reverse=True)[:10]:
            print(f"    {a} → {t}: "
                  f"n={len(deltas)} mean_Δ={np.mean(deltas):.6f} "
                  f"std={np.std(deltas):.6f}")

    t_total = time.time() - t_start
    print(f"\n  Total time: {t_total/60:.1f} min")

    # Save
    outdir = Path(f"diag_v94_coupling_seed{seed}")
    outdir.mkdir(exist_ok=True)

    # Save summary (without full interactions for size)
    summary = [{k: v for k, v in e.items() if k != "interactions"}
               for e in coupling_log]
    with open(outdir / "coupling_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Save full log
    with open(outdir / "coupling_full.json", "w") as f:
        json.dump(coupling_log, f, indent=2)

    print(f"  Saved: {outdir}/coupling_summary.json")
    print(f"  Saved: {outdir}/coupling_full.json")

    print(f"\n{'='*65}")
    print(f"  END v9.4 Coupling Probe")
    print(f"{'='*65}\n")

    return coupling_log


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.4 Label-to-Label Coupling Probe")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--windows", type=int, default=25)
    parser.add_argument("--detail-start", type=int, default=20)
    parser.add_argument("--window-steps", type=int, default=500)
    parser.add_argument("--top-k", type=int, default=10,
                        help="Track top-K labels by share for detailed coupling")
    args = parser.parse_args()

    run_coupling_probe(
        seed=args.seed,
        n_windows=args.windows,
        detail_start=args.detail_start,
        window_steps=args.window_steps,
        top_k=args.top_k)
