#!/usr/bin/env python3
"""
ESDE v9.4 — Label Perception Field (N-hop Perception)
=======================================================
Defines and records each label's "visible world" without
modifying any physical state. Pure observation layer.

Each label's perception range = its alive node count (hops).
World geometry = wrap-around torus (no edge bias).

USAGE:
  python v94_perception.py --seed 42
"""

import sys, math, time, json, csv, argparse
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

from esde_v82_engine import V82Engine, V82EncapsulationParams, V82_N
from v19g_canon import BASE_PARAMS
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9


# ================================================================
# WRAP-AROUND SUBSTRATE (TORUS)
# ================================================================
def build_torus_substrate(N):
    """Build wrap-around grid adjacency. Left↔Right, Top↔Bottom."""
    side = int(math.ceil(math.sqrt(N)))
    adj = {}
    for i in range(N):
        r, c = i // side, i % side
        nbs = []
        # Up (wrap)
        nr = (r - 1) % side
        nb = nr * side + c
        if nb < N: nbs.append(nb)
        # Down (wrap)
        nr = (r + 1) % side
        nb = nr * side + c
        if nb < N: nbs.append(nb)
        # Left (wrap)
        nc = (c - 1) % side
        nb = r * side + nc
        if nb < N: nbs.append(nb)
        # Right (wrap)
        nc = (c + 1) % side
        nb = r * side + nc
        if nb < N: nbs.append(nb)
        adj[i] = nbs
    return adj


# ================================================================
# PERCEPTION FIELD EXTRACTION
# ================================================================
def extract_perception(state, labels, macro_nodes, torus_sub, N):
    """Extract each label's perception field via BFS on torus substrate.

    max_hops = number of alive nodes in the label.
    Returns dict {lid: perception_data}.
    """
    side = int(math.ceil(math.sqrt(N)))

    # Build lookup: node → label_id (for core membership)
    node_to_label = {}
    for lid, label in labels.items():
        if lid in macro_nodes:
            continue
        for n in label["nodes"]:
            node_to_label[n] = lid

    # Per-node degree (for link strength stats)
    link_S = {}
    for lk in state.alive_l:
        link_S[lk] = state.S.get(lk, 0.0)

    results = {}

    for lid, label in labels.items():
        if lid in macro_nodes:
            continue

        core_nodes = frozenset(n for n in label["nodes"] if n in state.alive_n)
        n_alive = len(core_nodes)
        if n_alive == 0:
            continue

        max_hops = n_alive

        # BFS from core nodes on torus
        visited = {}  # node → hop
        hop_shells = defaultdict(set)

        # Core = hop 0
        for n in core_nodes:
            visited[n] = 0
            hop_shells[0].add(n)

        frontier = set(core_nodes)
        for hop in range(1, max_hops + 1):
            next_frontier = set()
            for n in frontier:
                for nb in torus_sub.get(n, []):
                    if nb not in visited and nb in state.alive_n:
                        visited[nb] = hop
                        hop_shells[hop].add(nb)
                        next_frontier.add(nb)
            frontier = next_frontier
            if not frontier:
                break

        # ── Analyze visible world ──
        visible_all = set(visited.keys())
        visible_non_core = visible_all - core_nodes

        # Classification
        wild_nodes = set()
        other_label_cores = defaultdict(set)  # {other_lid: set of nodes}

        for n in visible_non_core:
            owner = node_to_label.get(n)
            if owner is not None and owner != lid:
                other_label_cores[owner].add(n)
            else:
                wild_nodes.add(n)

        # Phase analysis
        phase_sig = label["phase_sig"]
        phase_diffs = []
        visible_thetas = []
        for n in visible_all:
            theta = float(state.theta[n])
            visible_thetas.append(theta)
            d = abs(theta - phase_sig)
            if d > math.pi:
                d = 2 * math.pi - d
            phase_diffs.append(d)

        # Link strength in visible area
        visible_link_S = []
        for lk in state.alive_l:
            if lk[0] in visible_all and lk[1] in visible_all:
                visible_link_S.append(state.S.get(lk, 0.0))

        # Theta variance (circular)
        if visible_thetas:
            sin_s = sum(math.sin(t) for t in visible_thetas)
            cos_s = sum(math.cos(t) for t in visible_thetas)
            R_circ = math.sqrt(sin_s**2 + cos_s**2) / len(visible_thetas)
            theta_var = 1.0 - R_circ  # 0=uniform, 1=dispersed
        else:
            theta_var = 0.0

        # Functional zones (rough classification)
        near_phase = sum(1 for d in phase_diffs if d < math.pi / 4)
        far_phase = sum(1 for d in phase_diffs if d > 3 * math.pi / 4)

        results[lid] = {
            "label_id": lid,
            "n_core": n_alive,
            "max_hops": max_hops,
            "visible_total": len(visible_all),
            "hop_shell_sizes": {h: len(hop_shells[h])
                                for h in sorted(hop_shells.keys())},
            # Composition
            "self_core_count": n_alive,
            "wild_count": len(wild_nodes),
            "other_label_core_count": sum(len(v) for v in other_label_cores.values()),
            "other_labels_visible": {str(k): len(v)
                                      for k, v in other_label_cores.items()},
            "n_other_labels_seen": len(other_label_cores),
            # Physics
            "mean_theta": round(math.atan2(
                sum(math.sin(t) for t in visible_thetas),
                sum(math.cos(t) for t in visible_thetas)), 4)
                if visible_thetas else 0.0,
            "theta_variance": round(theta_var, 4),
            "mean_link_strength": round(
                sum(visible_link_S) / max(1, len(visible_link_S)), 4)
                if visible_link_S else 0.0,
            "visible_links": len(visible_link_S),
            # Phase relationship
            "phase_sig": round(phase_sig, 4),
            "mean_phase_diff": round(
                sum(phase_diffs) / max(1, len(phase_diffs)), 4),
            "near_phase_count": near_phase,
            "far_phase_count": far_phase,
            "near_phase_ratio": round(
                near_phase / max(1, len(visible_all)), 4),
            # Functional zones
            "share": round(label["share"], 6),
            "born": label["born"],
        }

    return results


# ================================================================
# PAIRWISE OVERLAP
# ================================================================
def compute_overlaps(perceptions, state, labels, macro_nodes, torus_sub):
    """Compute pairwise overlap between label perception fields."""
    # Rebuild visible sets
    visible_sets = {}
    for lid, label in labels.items():
        if lid in macro_nodes:
            continue
        core_nodes = frozenset(n for n in label["nodes"] if n in state.alive_n)
        n_alive = len(core_nodes)
        if n_alive == 0:
            continue
        max_hops = n_alive

        visited = set()
        for n in core_nodes:
            visited.add(n)
        frontier = set(core_nodes)
        for hop in range(1, max_hops + 1):
            next_frontier = set()
            for n in frontier:
                for nb in torus_sub.get(n, []):
                    if nb not in visited and nb in state.alive_n:
                        visited.add(nb)
                        next_frontier.add(nb)
            frontier = next_frontier
            if not frontier:
                break
        visible_sets[lid] = visited

    # Pairwise
    lids = sorted(visible_sets.keys())
    overlaps = []
    for i, lid_a in enumerate(lids):
        for lid_b in lids[i+1:]:
            set_a = visible_sets[lid_a]
            set_b = visible_sets[lid_b]
            overlap = set_a & set_b
            if not overlap:
                continue

            # Can A see B's core?
            core_b = frozenset(n for n in labels[lid_b]["nodes"]
                               if n in state.alive_n)
            core_a = frozenset(n for n in labels[lid_a]["nodes"]
                               if n in state.alive_n)
            a_sees_b_core = len(core_b & set_a)
            b_sees_a_core = len(core_a & set_b)

            overlaps.append({
                "label_a": lid_a,
                "label_b": lid_b,
                "overlap_count": len(overlap),
                "overlap_ratio_a": round(len(overlap) / max(1, len(set_a)), 4),
                "overlap_ratio_b": round(len(overlap) / max(1, len(set_b)), 4),
                "core_visible_a_to_b": a_sees_b_core,
                "core_visible_b_to_a": b_sees_a_core,
                "a_total_visible": len(set_a),
                "b_total_visible": len(set_b),
            })

    return overlaps


# ================================================================
# MAIN
# ================================================================
def run(seed=42, n_windows=25, window_steps=500):
    print(f"\n{'='*65}")
    print(f"  ESDE v9.4 — Label Perception Field")
    print(f"  seed={seed} windows={n_windows} steps/win={window_steps}")
    print(f"  Geometry: wrap-around torus")
    print(f"  Perception range: alive_node_count hops")
    print(f"{'='*65}\n")

    t_start = time.time()
    N = V82_N

    # Build torus substrate (for perception only)
    torus_sub = build_torus_substrate(N)

    # Build engine (standard v9.3 conditions)
    encap_params = V82EncapsulationParams(
        stress_enabled=False, virtual_enabled=True)
    engine = V82Engine(seed=seed, N=N, encap_params=encap_params)
    engine.virtual = VirtualLayerV9(
        feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True

    # Injection
    engine.run_injection()
    print(f"  Injection done. links={len(engine.state.alive_l)}")

    # Run to maturation
    print(f"  Running {n_windows} windows...")
    for w in range(n_windows):
        engine.step_window(steps=window_steps)
        if w % 5 == 0:
            print(f"    w={w} links={len(engine.state.alive_l)} "
                  f"vLb={len(engine.virtual.labels)}")

    print(f"\n  Maturation done. links={len(engine.state.alive_l)} "
          f"labels={len(engine.virtual.labels)}")

    # ── Extract Perception Fields ──
    print(f"\n  Extracting perception fields...")
    t_perc = time.time()

    perceptions = extract_perception(
        engine.state, engine.virtual.labels,
        engine.virtual.macro_nodes, torus_sub, N)

    overlaps = compute_overlaps(
        perceptions, engine.state, engine.virtual.labels,
        engine.virtual.macro_nodes, torus_sub)

    t_perc_done = time.time() - t_perc
    print(f"  Extraction done ({t_perc_done:.1f}s). "
          f"{len(perceptions)} labels, {len(overlaps)} overlap pairs.")

    # ── Summary ──
    print(f"\n{'='*65}")
    print(f"  PERCEPTION FIELD SUMMARY")
    print(f"{'='*65}\n")

    # §6.1 Visible total
    vis_totals = [p["visible_total"] for p in perceptions.values()]
    core_sizes = [p["n_core"] for p in perceptions.values()]
    print(f"  §6.1 Visible world size:")
    print(f"    Core nodes: mean={np.mean(core_sizes):.1f} "
          f"range={min(core_sizes)}-{max(core_sizes)}")
    print(f"    Visible total: mean={np.mean(vis_totals):.0f} "
          f"range={min(vis_totals)}-{max(vis_totals)}")
    print(f"    Expansion ratio: {np.mean(vis_totals)/np.mean(core_sizes):.1f}x")

    # §6.2 Composition
    wilds = [p["wild_count"] for p in perceptions.values()]
    others = [p["other_label_core_count"] for p in perceptions.values()]
    n_seen = [p["n_other_labels_seen"] for p in perceptions.values()]
    print(f"\n  §6.2 What labels see:")
    print(f"    Wild nodes: mean={np.mean(wilds):.0f} "
          f"({np.mean(wilds)/np.mean(vis_totals)*100:.0f}% of visible)")
    print(f"    Other label cores visible: mean={np.mean(others):.1f}")
    print(f"    Other labels seen: mean={np.mean(n_seen):.1f} "
          f"range={min(n_seen)}-{max(n_seen)}")

    # How many labels can see at least 1 other label?
    seeing_others = sum(1 for p in perceptions.values()
                        if p["n_other_labels_seen"] > 0)
    print(f"    Labels seeing ≥1 other: {seeing_others}/{len(perceptions)} "
          f"({seeing_others/max(1,len(perceptions))*100:.0f}%)")

    # §6.3 Physics
    tvars = [p["theta_variance"] for p in perceptions.values()]
    mls = [p["mean_link_strength"] for p in perceptions.values()]
    print(f"\n  §6.3 Visible world character:")
    print(f"    Theta variance: mean={np.mean(tvars):.4f}")
    print(f"    Mean link S: mean={np.mean(mls):.4f}")

    # §6.4 Phase relationship
    mpd = [p["mean_phase_diff"] for p in perceptions.values()]
    npr = [p["near_phase_ratio"] for p in perceptions.values()]
    print(f"\n  §6.4 Phase relationship to visible world:")
    print(f"    Mean phase diff: mean={np.mean(mpd):.4f}")
    print(f"    Near-phase ratio: mean={np.mean(npr):.2%}")

    # §6.5 Overlaps
    if overlaps:
        ov_counts = [o["overlap_count"] for o in overlaps]
        core_vis = [o["core_visible_a_to_b"] + o["core_visible_b_to_a"]
                    for o in overlaps]
        print(f"\n  §6.5 Perception overlaps:")
        print(f"    Overlapping pairs: {len(overlaps)}")
        print(f"    Overlap size: mean={np.mean(ov_counts):.0f} "
              f"range={min(ov_counts)}-{max(ov_counts)}")
        print(f"    Mutual core visibility: mean={np.mean(core_vis):.1f}")

        # Top 10 overlaps
        top_ov = sorted(overlaps, key=lambda x: x["overlap_count"],
                         reverse=True)[:10]
        print(f"\n    Top 10 overlapping pairs:")
        for o in top_ov:
            print(f"      {o['label_a']:>4} ↔ {o['label_b']:>4}: "
                  f"overlap={o['overlap_count']:>4} "
                  f"core_vis={o['core_visible_a_to_b']}+{o['core_visible_b_to_a']} "
                  f"ratio_a={o['overlap_ratio_a']:.2f} "
                  f"ratio_b={o['overlap_ratio_b']:.2f}")
    else:
        print(f"\n  §6.5 Perception overlaps: NONE")

    # §7.1 Functional zones
    print(f"\n  §7.1 World character distribution:")
    isolated = sum(1 for p in perceptions.values()
                   if p["n_other_labels_seen"] == 0)
    social = sum(1 for p in perceptions.values()
                 if p["n_other_labels_seen"] >= 3)
    familiar = sum(1 for p in perceptions.values()
                   if p["near_phase_ratio"] > 0.5)
    alien = sum(1 for p in perceptions.values()
                if p["near_phase_ratio"] < 0.2)
    print(f"    Isolated (see 0 others): {isolated}/{len(perceptions)}")
    print(f"    Social (see 3+ others): {social}/{len(perceptions)}")
    print(f"    Familiar world (>50% near-phase): {familiar}/{len(perceptions)}")
    print(f"    Alien world (<20% near-phase): {alien}/{len(perceptions)}")

    t_total = time.time() - t_start
    print(f"\n  Total time: {t_total/60:.1f} min")

    # ── Save ──
    outdir = Path(f"diag_v94_perception_seed{seed}")
    outdir.mkdir(exist_ok=True)

    with open(outdir / "per_label_perception.json", "w") as f:
        json.dump(list(perceptions.values()), f, indent=2)

    if overlaps:
        with open(outdir / "pairwise_overlap.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=overlaps[0].keys())
            writer.writeheader()
            writer.writerows(overlaps)

    print(f"  Saved: {outdir}/per_label_perception.json")
    if overlaps:
        print(f"  Saved: {outdir}/pairwise_overlap.csv")

    print(f"\n{'='*65}")
    print(f"  END v9.4 Perception Field")
    print(f"{'='*65}\n")

    return perceptions, overlaps


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.4 Label Perception Field")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--windows", type=int, default=25)
    parser.add_argument("--window-steps", type=int, default=500)
    args = parser.parse_args()

    run(seed=args.seed, n_windows=args.windows,
        window_steps=args.window_steps)
