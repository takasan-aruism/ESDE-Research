#!/usr/bin/env python3
"""
ESDE v9.4+ — Step-Level World Change Log
==========================================
Records what each tracked label "sees" at regular intervals within
each window. Both spatial perception (torus BFS) and structural
perception (alive link BFS) are captured.

No new rules. Pure observation. State is never modified.

USAGE:
  python v94_worldlog.py --seed 42
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

from esde_v82_engine import (V82Engine, V82EncapsulationParams, V82_N,
                              find_islands_sets)
from v19g_canon import BASE_PARAMS, BIAS
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
# DUAL PERCEPTION (spatial + structural)
# ================================================================
def compute_perception(state, label, lid, torus_sub, max_hops,
                       node_to_label, link_adj=None):
    """Compute both spatial and structural perception for one label.

    Spatial: BFS on torus substrate (fixed grid, wrap-around)
    Structural: BFS on alive links (dynamic, changes every step)

    link_adj: pre-built adjacency dict. If None, built on-the-fly.
    Returns dict with both perception fields + summary stats.
    """
    core_nodes = frozenset(n for n in label["nodes"] if n in state.alive_n)
    n_alive = len(core_nodes)
    if n_alive == 0:
        return None

    # ── Spatial perception (torus BFS) ──
    spatial_visited = {}
    for n in core_nodes:
        spatial_visited[n] = 0
    frontier = set(core_nodes)
    for hop in range(1, max_hops + 1):
        nf = set()
        for n in frontier:
            for nb in torus_sub.get(n, []):
                if nb not in spatial_visited and nb in state.alive_n:
                    spatial_visited[nb] = hop
                    nf.add(nb)
        frontier = nf
        if not frontier:
            break
    spatial_set = set(spatial_visited.keys())

    # ── Structural perception (alive link BFS) ──
    if link_adj is None:
        link_adj = defaultdict(set)
        for lk in state.alive_l:
            n1, n2 = lk
            link_adj[n1].add(n2)
            link_adj[n2].add(n1)

    struct_visited = {}
    for n in core_nodes:
        struct_visited[n] = 0
    frontier = set(core_nodes)
    for hop in range(1, max_hops + 1):
        nf = set()
        for n in frontier:
            for nb in link_adj.get(n, set()):
                if nb not in struct_visited and nb in state.alive_n:
                    struct_visited[nb] = hop
                    nf.add(nb)
        frontier = nf
        if not frontier:
            break
    struct_set = set(struct_visited.keys())

    # ── Analyze both fields ──
    phase_sig = label["phase_sig"]

    def analyze_field(visible_set):
        if not visible_set:
            return {"total": 0}

        wild = 0
        other_labels = set()
        other_core_count = 0
        for n in visible_set:
            if n in core_nodes:
                continue
            owner = node_to_label.get(n)
            if owner is not None and owner != lid:
                other_labels.add(owner)
                other_core_count += 1
            else:
                wild += 1

        # θ stats
        thetas = [float(state.theta[n]) for n in visible_set]
        phase_diffs = []
        for t in thetas:
            d = abs(t - phase_sig)
            if d > math.pi:
                d = 2 * math.pi - d
            phase_diffs.append(d)

        near_phase = sum(1 for d in phase_diffs if d < math.pi / 4)

        # Circular variance
        sin_s = sum(math.sin(t) for t in thetas)
        cos_s = sum(math.cos(t) for t in thetas)
        R_circ = math.sqrt(sin_s**2 + cos_s**2) / len(thetas)
        theta_var = 1.0 - R_circ

        # Link stats within visible set
        n_links = 0
        s_sum = 0.0
        r_plus = 0
        for lk in state.alive_l:
            if lk[0] in visible_set and lk[1] in visible_set:
                n_links += 1
                s_sum += state.S.get(lk, 0.0)
                if state.R.get(lk, 0.0) > 0:
                    r_plus += 1

        return {
            "total": len(visible_set),
            "wild": wild,
            "other_labels_seen": sorted(other_labels),
            "n_seen": len(other_labels),
            "other_core_count": other_core_count,
            "mean_theta": round(math.atan2(sin_s, cos_s), 4),
            "theta_var": round(theta_var, 4),
            "mean_phase_diff": round(
                sum(phase_diffs) / len(phase_diffs), 4),
            "near_phase_ratio": round(
                near_phase / len(visible_set), 4),
            "n_links": n_links,
            "mean_S": round(s_sum / max(1, n_links), 4),
            "r_plus": r_plus,
        }

    spatial_stats = analyze_field(spatial_set)
    struct_stats = analyze_field(struct_set)

    # Overlap between spatial and structural
    both = spatial_set & struct_set
    spatial_only = spatial_set - struct_set
    struct_only = struct_set - spatial_set

    return {
        "n_core": n_alive,
        "share": round(label["share"], 6),
        "phase_sig": round(phase_sig, 4),
        "spatial": spatial_stats,
        "structural": struct_stats,
        "overlap_spatial_structural": len(both),
        "spatial_only": len(spatial_only),
        "structural_only": len(struct_only),
    }


# ================================================================
# MAIN
# ================================================================
def run(seed=42, maturation_windows=20, tracking_windows=5,
        window_steps=500, perception_interval=50,
        case_labels=None, top_k=10):

    if case_labels is None:
        case_labels = [87, 101, 112]

    print(f"\n{'='*65}")
    print(f"  ESDE v9.4+ — Step-Level World Change Log")
    print(f"  seed={seed} mat={maturation_windows} track={tracking_windows}")
    print(f"  steps/win={window_steps} perc_interval={perception_interval}")
    print(f"  cases={case_labels} top_k={top_k}")
    print(f"{'='*65}\n")

    t_start = time.time()
    N = V82_N
    torus_sub = build_torus_substrate(N)

    # Engine setup
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
    print(f"  Maturation done. labels={len(engine.virtual.labels)}\n")

    # Select tracked labels
    vl = engine.virtual
    all_labels = [(lid, lab["share"]) for lid, lab in vl.labels.items()
                  if lid not in vl.macro_nodes]
    all_labels.sort(key=lambda x: x[1], reverse=True)
    tracked = set(lid for lid, _ in all_labels[:top_k])
    for cl in case_labels:
        if cl in vl.labels:
            tracked.add(cl)
    print(f"  Tracking {len(tracked)} labels: {sorted(tracked)}")

    # Build node_to_label
    node_to_label = {}
    for lid, lab in vl.labels.items():
        if lid not in vl.macro_nodes:
            for n in lab["nodes"]:
                node_to_label[n] = lid

    # ── Tracking Phase ──
    print(f"\n  --- Tracking Phase ({tracking_windows} windows "
          f"× {window_steps} steps) ---\n")

    world_log = defaultdict(list)  # {lid: [entries]}
    steps_per_perception = perception_interval
    perceptions_per_window = window_steps // steps_per_perception

    for tw in range(tracking_windows):
        w = maturation_windows + tw
        t0 = time.time()

        # Run physics step by step, take perception snapshots
        bg_prob = BASE_PARAMS["background_injection_prob"]
        p = engine.island_tracker.params

        for step in range(window_steps):
            global_step = tw * window_steps + step

            # Physics step (same as engine.step_window inner loop)
            engine.realizer.step(engine.state)
            engine.physics.step_pre_chemistry(engine.state)
            engine.chem.step(engine.state)
            engine.physics.step_resonance(engine.state)

            engine._g_scores[:] = 0
            engine.grower.step(engine.state)
            agr = engine.grower.params.auto_growth_rate
            for k in engine.state.alive_l:
                r = engine.state.R.get(k, 0.0)
                if r > 0:
                    a = min(agr * r,
                            max(engine.state.get_latent(k[0], k[1]), 0))
                    if a > 0:
                        engine._g_scores[k[0]] += a
                        engine._g_scores[k[1]] += a

            engine.intruder.step(engine.state)
            engine.physics.step_decay_exclusion(engine.state)

            # Background seeding (canon-compliant: BIAS + Z seeding)
            al = list(engine.state.alive_n)
            na = len(al)
            gz = float(engine._g_scores.sum())
            if na > 0:
                aa = np.array(al)
                if BIAS > 0 and gz > 0:
                    ga = engine._g_scores[aa]
                    gs = ga.sum()
                    if gs > 0:
                        pg = ga / gs
                        pd = (1 - BIAS) * (np.ones(na) / na) + BIAS * pg
                        pd /= pd.sum()
                    else:
                        pd = np.ones(na) / na
                else:
                    pd = np.ones(na) / na
                mk = engine.state.rng.random(na) < bg_prob
                for idx in range(na):
                    if mk[idx]:
                        t = int(engine.state.rng.choice(aa, p=pd))
                        if t in engine.state.alive_n:
                            engine.state.E[t] = min(
                                1.0, engine.state.E[t] + 0.3)
                            # Z seeding (canon)
                            if engine.state.Z[t] == 0 and \
                               engine.state.rng.random() < 0.5:
                                engine.state.Z[t] = 1 if \
                                    engine.state.rng.random() < 0.5 else 2

            # Torque (sub-window, if interval hit)
            if step > 0 and step % steps_per_perception == 0:
                vl.apply_torque_only(
                    engine.state, engine.window_count,
                    substrate=engine.substrate)

            # ── Perception snapshot ──
            if step % steps_per_perception == 0:
                # Update node_to_label (labels may have changed)
                node_to_label = {}
                for lid, lab in vl.labels.items():
                    if lid not in vl.macro_nodes:
                        for n in lab["nodes"]:
                            node_to_label[n] = lid

                # Build link_adj once, share across all labels (#VWL-2)
                _link_adj = defaultdict(set)
                for lk in engine.state.alive_l:
                    n1, n2 = lk
                    _link_adj[n1].add(n2)
                    _link_adj[n2].add(n1)

                for lid in tracked:
                    if lid not in vl.labels:
                        continue
                    label = vl.labels[lid]
                    core_alive = sum(1 for n in label["nodes"]
                                     if n in engine.state.alive_n)
                    if core_alive == 0:
                        continue

                    perc = compute_perception(
                        engine.state, label, lid,
                        torus_sub, core_alive, node_to_label,
                        link_adj=_link_adj)

                    if perc is not None:
                        perc["window"] = w
                        perc["step"] = step
                        perc["global_step"] = global_step
                        perc["total_links"] = len(engine.state.alive_l)
                        world_log[lid].append(perc)

        # End of window: run virtual layer step
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
        engine.window_count += 1

        sec = time.time() - t0
        n_entries = sum(len(world_log[lid]) for lid in tracked
                        if lid in vl.labels)
        print(f"  w={w:>3} links={len(engine.state.alive_l):>5} "
              f"vLb={len(vl.labels):>3} entries={n_entries} {sec:.0f}s")

    # ── Analysis ──
    print(f"\n{'='*65}")
    print(f"  WORLD CHANGE ANALYSIS")
    print(f"{'='*65}")

    for lid in sorted(tracked):
        entries = world_log.get(lid, [])
        if len(entries) < 2:
            continue

        print(f"\n  --- Label {lid} ({len(entries)} snapshots) ---")

        # Spatial vs structural comparison
        sp_totals = [e["spatial"]["total"] for e in entries]
        st_totals = [e["structural"]["total"] for e in entries]
        sp_seen = [e["spatial"]["n_seen"] for e in entries]
        st_seen = [e["structural"]["n_seen"] for e in entries]
        sp_near = [e["spatial"]["near_phase_ratio"] for e in entries]
        st_near = [e["structural"]["near_phase_ratio"] for e in entries]

        print(f"    {'':>12} {'spatial':>10} {'structural':>12}")
        print(f"    {'visible':>12} {np.mean(sp_totals):>9.0f} "
              f"{np.mean(st_totals):>11.0f}")
        print(f"    {'n_seen':>12} {np.mean(sp_seen):>9.1f} "
              f"{np.mean(st_seen):>11.1f}")
        print(f"    {'near_phase':>12} {np.mean(sp_near):>8.1%} "
              f"{np.mean(st_near):>10.1%}")
        print(f"    {'links':>12} {np.mean([e['spatial']['n_links'] for e in entries]):>9.0f} "
              f"{np.mean([e['structural']['n_links'] for e in entries]):>11.0f}")

        # Step-to-step θ change
        sp_thetas = [e["spatial"]["mean_theta"] for e in entries]
        diffs = []
        for i in range(1, len(sp_thetas)):
            d = sp_thetas[i] - sp_thetas[i-1]
            while d > math.pi: d -= 2 * math.pi
            while d < -math.pi: d += 2 * math.pi
            diffs.append(abs(d))
        if diffs:
            print(f"    θ drift/interval: mean={np.mean(diffs):.4f} "
                  f"max={max(diffs):.4f}")

        # Spatial-structural overlap
        overlaps = [e["overlap_spatial_structural"] for e in entries]
        sp_only = [e["spatial_only"] for e in entries]
        st_only = [e["structural_only"] for e in entries]
        print(f"    spatial∩structural: {np.mean(overlaps):.0f}  "
              f"spatial_only: {np.mean(sp_only):.0f}  "
              f"structural_only: {np.mean(st_only):.0f}")

    # Timeline for case labels
    print(f"\n{'='*65}")
    print(f"  CASE STUDY STEP TIMELINES")
    print(f"{'='*65}")

    for lid in case_labels:
        entries = world_log.get(lid, [])
        if not entries:
            print(f"\n  Label {lid}: NOT FOUND")
            continue

        print(f"\n  --- Label {lid} ---")
        print(f"  {'step':>5} {'sp_vis':>6} {'st_vis':>6} {'sp_n':>4} "
              f"{'st_n':>4} {'sp_near':>7} {'st_near':>7} "
              f"{'sp_lnk':>6} {'st_lnk':>6} {'overlap':>7}")
        print(f"  {'-'*63}")

        for e in entries[:30]:  # limit output
            sp = e["spatial"]
            st = e["structural"]
            print(f"  {e['step']:>5} {sp['total']:>6} {st['total']:>6} "
                  f"{sp['n_seen']:>4} {st['n_seen']:>4} "
                  f"{sp['near_phase_ratio']*100:>6.1f}% "
                  f"{st['near_phase_ratio']*100:>6.1f}% "
                  f"{sp['n_links']:>6} {st['n_links']:>6} "
                  f"{e['overlap_spatial_structural']:>7}")

    t_total = time.time() - t_start
    print(f"\n  Total time: {t_total/60:.1f} min")

    # ── Save ──
    outdir = Path(f"diag_v94_worldlog_seed{seed}")
    outdir.mkdir(exist_ok=True)

    # Strip sets for JSON
    save_log = {}
    for lid, entries in world_log.items():
        save_log[str(lid)] = entries
    with open(outdir / "world_log.json", "w") as f:
        json.dump(save_log, f, indent=2, default=str)

    print(f"  Saved: {outdir}/world_log.json")
    print(f"\n{'='*65}")
    print(f"  END World Change Log")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.4+ Step-Level World Change Log")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--maturation-windows", type=int, default=20)
    parser.add_argument("--tracking-windows", type=int, default=5)
    parser.add_argument("--window-steps", type=int, default=500)
    parser.add_argument("--perception-interval", type=int, default=50,
                        help="Steps between perception snapshots")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--case-labels", type=str, default="87,101,112")
    args = parser.parse_args()

    cases = [int(x) for x in args.case_labels.split(",")]
    run(seed=args.seed,
        maturation_windows=args.maturation_windows,
        tracking_windows=args.tracking_windows,
        window_steps=args.window_steps,
        perception_interval=args.perception_interval,
        case_labels=cases,
        top_k=args.top_k)
