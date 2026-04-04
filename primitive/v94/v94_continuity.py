#!/usr/bin/env python3
"""
ESDE v9.4+ — Existence Layer Continuity Observation
=====================================================
Tracks label perception fields across multiple windows.
No new rules. Pure observation of whether labels maintain
consistent world views, partner relationships, and types.

USAGE:
  python v94_continuity.py --seed 42
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
# TORUS SUBSTRATE
# ================================================================
def build_torus_substrate(N):
    side = int(math.ceil(math.sqrt(N)))
    adj = {}
    for i in range(N):
        r, c = i // side, i % side
        nbs = []
        nbs.append(((r - 1) % side) * side + c)
        nbs.append(((r + 1) % side) * side + c)
        nbs.append(r * side + ((c - 1) % side))
        nbs.append(r * side + ((c + 1) % side))
        adj[i] = [nb for nb in nbs if nb < N]
    return adj


# ================================================================
# PERCEPTION EXTRACTION (same as v94_perception, streamlined)
# ================================================================
def extract_perception_fast(state, labels, macro_nodes, torus_sub, N):
    """Extract perception fields. Returns {lid: {stats..., visible_set}}."""
    node_to_label = {}
    for lid, label in labels.items():
        if lid in macro_nodes:
            continue
        for n in label["nodes"]:
            node_to_label[n] = lid

    results = {}
    for lid, label in labels.items():
        if lid in macro_nodes:
            continue
        core_nodes = frozenset(n for n in label["nodes"] if n in state.alive_n)
        n_alive = len(core_nodes)
        if n_alive == 0:
            continue

        max_hops = n_alive

        # BFS
        visited = {}
        for n in core_nodes:
            visited[n] = 0
        frontier = set(core_nodes)
        for hop in range(1, max_hops + 1):
            nf = set()
            for n in frontier:
                for nb in torus_sub.get(n, []):
                    if nb not in visited and nb in state.alive_n:
                        visited[nb] = hop
                        nf.add(nb)
            frontier = nf
            if not frontier:
                break

        visible_all = set(visited.keys())
        visible_non_core = visible_all - core_nodes

        # Classification
        wild_count = 0
        other_labels = defaultdict(int)
        for n in visible_non_core:
            owner = node_to_label.get(n)
            if owner is not None and owner != lid:
                other_labels[owner] += 1
            else:
                wild_count += 1

        # Phase
        phase_sig = label["phase_sig"]
        phase_diffs = []
        for n in visible_all:
            d = abs(float(state.theta[n]) - phase_sig)
            if d > math.pi:
                d = 2 * math.pi - d
            phase_diffs.append(d)

        near_phase = sum(1 for d in phase_diffs if d < math.pi / 4)

        # Theta variance (circular)
        thetas = [float(state.theta[n]) for n in visible_all]
        if thetas:
            sin_s = sum(math.sin(t) for t in thetas)
            cos_s = sum(math.cos(t) for t in thetas)
            R_circ = math.sqrt(sin_s**2 + cos_s**2) / len(thetas)
            theta_var = 1.0 - R_circ
        else:
            theta_var = 0.0

        results[lid] = {
            "n_core": n_alive,
            "visible_total": len(visible_all),
            "wild_count": wild_count,
            "other_labels_visible": dict(other_labels),
            "n_other_labels_seen": len(other_labels),
            "theta_variance": round(theta_var, 4),
            "mean_phase_diff": round(
                sum(phase_diffs) / max(1, len(phase_diffs)), 4),
            "near_phase_ratio": round(
                near_phase / max(1, len(visible_all)), 4),
            "share": round(label["share"], 6),
            "born": label["born"],
            "visible_set": visible_all,  # kept for Jaccard
        }

    return results


def jaccard(set_a, set_b):
    if not set_a and not set_b:
        return 1.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / max(1, union)


def classify_type(perc):
    """Assign type tags based on perception stats."""
    tags = []
    if perc["n_other_labels_seen"] >= 3:
        tags.append("social")
    elif perc["n_other_labels_seen"] == 0:
        tags.append("isolated")
    if perc["near_phase_ratio"] > 0.5:
        tags.append("familiar")
    elif perc["near_phase_ratio"] < 0.2:
        tags.append("alien")
    if perc["visible_total"] >= 200:
        tags.append("wide")
    elif perc["visible_total"] <= 50:
        tags.append("local")
    return tags if tags else ["neutral"]


# ================================================================
# MAIN
# ================================================================
def run(seed=42, maturation_windows=20, tracking_windows=10,
        window_steps=500, case_labels=None):

    if case_labels is None:
        case_labels = [87, 101, 112]

    print(f"\n{'='*65}")
    print(f"  ESDE v9.4+ — Existence Layer Continuity Observation")
    print(f"  seed={seed} mat={maturation_windows} track={tracking_windows}")
    print(f"  steps/win={window_steps} cases={case_labels}")
    print(f"{'='*65}\n")

    t_start = time.time()
    N = V82_N
    torus_sub = build_torus_substrate(N)

    # Engine setup (v9.3 best conditions)
    encap_params = V82EncapsulationParams(
        stress_enabled=False, virtual_enabled=True)
    engine = V82Engine(seed=seed, N=N, encap_params=encap_params)
    engine.virtual = VirtualLayerV9(
        feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True

    engine.run_injection()
    print(f"  Injection done. links={len(engine.state.alive_l)}")

    # Maturation
    print(f"  Maturation ({maturation_windows} windows)...")
    for w in range(maturation_windows):
        engine.step_window(steps=window_steps)
        if w % 5 == 0:
            print(f"    w={w} links={len(engine.state.alive_l)} "
                  f"vLb={len(engine.virtual.labels)}")
    print(f"  Maturation done. labels={len(engine.virtual.labels)}")

    # ── Tracking Phase ──
    print(f"\n  --- Tracking Phase ({tracking_windows} windows) ---\n")

    # Storage
    label_history = defaultdict(list)  # {lid: [per-window perception]}
    prev_perceptions = {}  # previous window's perceptions

    timeline_rows = []  # for CSV

    for tw in range(tracking_windows):
        w = maturation_windows + tw
        t0 = time.time()

        engine.step_window(steps=window_steps)

        # Extract perception
        perceptions = extract_perception_fast(
            engine.state, engine.virtual.labels,
            engine.virtual.macro_nodes, torus_sub, N)

        # Compute persistence metrics for each label
        for lid, perc in perceptions.items():
            entry = {
                "window": w,
                "n_core": perc["n_core"],
                "visible_total": perc["visible_total"],
                "wild_count": perc["wild_count"],
                "n_seen": perc["n_other_labels_seen"],
                "partners": sorted(perc["other_labels_visible"].keys()),
                "theta_variance": perc["theta_variance"],
                "mean_phase_diff": perc["mean_phase_diff"],
                "near_phase_ratio": perc["near_phase_ratio"],
                "share": perc["share"],
                "born": perc["born"],
                "age": w - perc["born"],
                "type_tags": classify_type(perc),
            }

            # §6.1 World persistence (vs previous window)
            if lid in prev_perceptions:
                prev = prev_perceptions[lid]
                entry["world_jaccard"] = round(
                    jaccard(perc["visible_set"], prev["visible_set"]), 4)
                entry["near_phase_drift"] = round(
                    perc["near_phase_ratio"] - prev["near_phase_ratio"], 4)
            else:
                entry["world_jaccard"] = None
                entry["near_phase_drift"] = None

            # §6.2 Social persistence
            if lid in prev_perceptions:
                prev_partners = set(prev_perceptions[lid]["other_labels_visible"].keys())
                curr_partners = set(perc["other_labels_visible"].keys())
                if prev_partners or curr_partners:
                    entry["partner_jaccard"] = round(
                        jaccard(prev_partners, curr_partners), 4)
                else:
                    entry["partner_jaccard"] = 1.0
                entry["partners_retained"] = len(prev_partners & curr_partners)
                entry["partners_new"] = len(curr_partners - prev_partners)
                entry["partners_lost"] = len(prev_partners - curr_partners)
            else:
                entry["partner_jaccard"] = None
                entry["partners_retained"] = None
                entry["partners_new"] = None
                entry["partners_lost"] = None

            label_history[lid].append(entry)

            # CSV row
            timeline_rows.append({
                "window": w,
                "label_id": lid,
                "age": entry["age"],
                "n_core": entry["n_core"],
                "visible_total": entry["visible_total"],
                "n_seen": entry["n_seen"],
                "near_phase_ratio": entry["near_phase_ratio"],
                "theta_variance": entry["theta_variance"],
                "share": entry["share"],
                "type_tag": "|".join(entry["type_tags"]),
                "world_jaccard": entry["world_jaccard"] if entry["world_jaccard"] is not None else "",
                "partner_jaccard": entry["partner_jaccard"] if entry["partner_jaccard"] is not None else "",
            })

        prev_perceptions = perceptions

        # Print summary
        n_labels = len(perceptions)
        alive_labels = [lid for lid in perceptions]
        jaccards = [e["world_jaccard"] for lid in perceptions
                     for e in [label_history[lid][-1]]
                     if e["world_jaccard"] is not None]
        mean_j = np.mean(jaccards) if jaccards else 0
        sec = time.time() - t0
        print(f"  w={w:>3} labels={n_labels:>3} "
              f"world_J={mean_j:.3f} {sec:.0f}s")

    # ── Analysis ──
    print(f"\n{'='*65}")
    print(f"  CONTINUITY ANALYSIS")
    print(f"{'='*65}")

    # §6.1 World persistence
    all_j = []
    for lid, history in label_history.items():
        for e in history:
            if e["world_jaccard"] is not None:
                all_j.append(e["world_jaccard"])
    print(f"\n  §6.1 World persistence (visible node Jaccard):")
    if all_j:
        print(f"    mean={np.mean(all_j):.4f} std={np.std(all_j):.4f} "
              f"min={min(all_j):.4f} max={max(all_j):.4f}")

    # §6.2 Social persistence
    all_pj = []
    for lid, history in label_history.items():
        for e in history:
            if e["partner_jaccard"] is not None:
                all_pj.append(e["partner_jaccard"])
    print(f"\n  §6.2 Social persistence (partner Jaccard):")
    if all_pj:
        print(f"    mean={np.mean(all_pj):.4f} std={np.std(all_pj):.4f}")

    # §6.3 Type persistence
    print(f"\n  §6.3 Type persistence:")
    for lid, history in label_history.items():
        if len(history) < 3:
            continue
        types_over_time = ["|".join(e["type_tags"]) for e in history]
        unique_types = set(types_over_time)
        if len(unique_types) == 1:
            stability = "STABLE"
        elif len(unique_types) <= 2:
            stability = "mostly_stable"
        else:
            stability = "variable"

        # Only print case study labels + any interesting ones
        if lid in case_labels or stability == "STABLE":
            print(f"    L{lid}: {stability} "
                  f"types={types_over_time}")

    # §6.4 Boundary persistence
    print(f"\n  §6.4 Boundary persistence (recurring overlap pairs):")
    pair_windows = defaultdict(int)
    for lid, history in label_history.items():
        for e in history:
            for partner in e["partners"]:
                pair = tuple(sorted([lid, int(partner)]))
                pair_windows[pair] += 1

    persistent_pairs = {k: v for k, v in pair_windows.items()
                        if v >= tracking_windows * 0.7}
    print(f"    Total pairs seen: {len(pair_windows)}")
    print(f"    Pairs present ≥70% of windows: {len(persistent_pairs)}")
    if persistent_pairs:
        for pair, count in sorted(persistent_pairs.items(),
                                    key=lambda x: x[1], reverse=True)[:15]:
            print(f"      {pair[0]:>4} ↔ {pair[1]:>4}: "
                  f"{count}/{tracking_windows} windows "
                  f"({count/tracking_windows:.0%})")

    # ── Case Studies ──
    print(f"\n{'='*65}")
    print(f"  CASE STUDY TIMELINES")
    print(f"{'='*65}")

    for lid in case_labels:
        history = label_history.get(lid, [])
        if not history:
            print(f"\n  Label {lid}: NOT FOUND (may have died)")
            continue

        print(f"\n  --- Label {lid} ({len(history)} windows) ---")
        print(f"  {'w':>4} {'vis':>5} {'seen':>4} {'near%':>6} "
              f"{'θvar':>6} {'wJ':>6} {'pJ':>6} {'type':>15}")
        print(f"  {'-'*55}")
        for e in history:
            wj = f"{e['world_jaccard']:.3f}" if e['world_jaccard'] is not None else "  —"
            pj = f"{e['partner_jaccard']:.3f}" if e['partner_jaccard'] is not None else "  —"
            tags = "|".join(e["type_tags"])
            print(f"  {e['window']:>4} {e['visible_total']:>5} "
                  f"{e['n_seen']:>4} {e['near_phase_ratio']*100:>5.1f}% "
                  f"{e['theta_variance']:>6.3f} {wj:>6} {pj:>6} "
                  f"{tags:>15}")

        # Persistence summary
        if len(history) >= 2:
            js = [e["world_jaccard"] for e in history if e["world_jaccard"] is not None]
            pjs = [e["partner_jaccard"] for e in history if e["partner_jaccard"] is not None]
            print(f"  Summary: world_J mean={np.mean(js):.4f}" if js else "")
            print(f"           partner_J mean={np.mean(pjs):.4f}" if pjs else "")
            types = ["|".join(e["type_tags"]) for e in history]
            print(f"           type stability: {len(set(types))} unique / {len(types)} windows")

    t_total = time.time() - t_start
    print(f"\n  Total time: {t_total/60:.1f} min")

    # ── Save ──
    outdir = Path(f"diag_v94_continuity_seed{seed}")
    outdir.mkdir(exist_ok=True)

    # Case study JSON
    case_data = {}
    for lid in case_labels:
        h = label_history.get(lid, [])
        # Strip visible_set (not JSON serializable)
        case_data[str(lid)] = [{k: v for k, v in e.items()
                                  if k != "visible_set"}
                                 for e in h]
    with open(outdir / "case_study_timeline.json", "w") as f:
        json.dump(case_data, f, indent=2)

    # Timeline CSV
    if timeline_rows:
        with open(outdir / "label_type_timeline.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=timeline_rows[0].keys())
            writer.writeheader()
            writer.writerows(timeline_rows)

    # Full history JSON (without visible_set)
    full_data = {}
    for lid, history in label_history.items():
        full_data[str(lid)] = [{k: v for k, v in e.items()
                                  if k != "visible_set"}
                                 for e in history]
    with open(outdir / "per_label_time_series.json", "w") as f:
        json.dump(full_data, f, indent=2)

    print(f"  Saved: {outdir}/case_study_timeline.json")
    print(f"  Saved: {outdir}/label_type_timeline.csv")
    print(f"  Saved: {outdir}/per_label_time_series.json")

    print(f"\n{'='*65}")
    print(f"  END Continuity Observation")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.4+ Existence Layer Continuity Observation")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--maturation-windows", type=int, default=20)
    parser.add_argument("--tracking-windows", type=int, default=10)
    parser.add_argument("--window-steps", type=int, default=500)
    parser.add_argument("--case-labels", type=str, default="87,101,112",
                        help="Comma-separated label IDs for case study")
    args = parser.parse_args()

    cases = [int(x) for x in args.case_labels.split(",")]
    run(seed=args.seed,
        maturation_windows=args.maturation_windows,
        tracking_windows=args.tracking_windows,
        window_steps=args.window_steps,
        case_labels=cases)
