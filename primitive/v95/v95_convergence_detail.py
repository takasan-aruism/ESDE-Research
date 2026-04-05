#!/usr/bin/env python3
"""
ESDE v9.5 — Convergence Detail + Node Frequency Bias Detection
================================================================
Records:
1. Every step: which nodes are in structural set (frequency counter)
2. Convergence moments (|Δ| < threshold): full structural set + composition
3. High-divergence moments (|Δ| > threshold): same for comparison

Spatial: once per window. Structural: every step.
Existence layer: ZERO changes.

USAGE:
  python v95_convergence_detail.py --seed 42
"""

import sys, math, time, json, argparse
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter

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
# HELPERS
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


def compute_spatial(state, label, torus_sub, max_hops):
    core = frozenset(n for n in label["nodes"] if n in state.alive_n)
    if not core:
        return set(), core
    visited = set(core)
    frontier = set(core)
    for hop in range(1, max_hops + 1):
        nf = set()
        for n in frontier:
            for nb in torus_sub.get(n, []):
                if nb not in visited and nb in state.alive_n:
                    visited.add(nb)
                    nf.add(nb)
        frontier = nf
        if not frontier:
            break
    return visited, core


def compute_structural(core, max_hops, link_adj, alive_n):
    if not core:
        return set()
    visited = set(core)
    frontier = set(n for n in core if n in alive_n)
    for hop in range(1, max_hops + 1):
        nf = set()
        for n in frontier:
            for nb in link_adj.get(n, set()):
                if nb not in visited and nb in alive_n:
                    visited.add(nb)
                    nf.add(nb)
        frontier = nf
        if not frontier:
            break
    return visited


def build_link_adj(state):
    adj = defaultdict(set)
    for lk in state.alive_l:
        adj[lk[0]].add(lk[1])
        adj[lk[1]].add(lk[0])
    return adj


def circular_diff(a, b):
    d = a - b
    while d > math.pi: d -= 2 * math.pi
    while d < -math.pi: d += 2 * math.pi
    return d


# ================================================================
# MAIN
# ================================================================
def run(seed=42, maturation_windows=20, tracking_windows=5,
        window_steps=500, case_labels=None, top_k=10,
        convergence_threshold=0.3, divergence_threshold=2.5):

    if case_labels is None:
        case_labels = [87, 101, 112]

    print(f"\n{'='*65}")
    print(f"  ESDE v9.5 — Convergence Detail + Node Frequency Bias")
    print(f"  seed={seed} mat={maturation_windows} track={tracking_windows}")
    print(f"  steps/win={window_steps} top_k={top_k}")
    print(f"  convergence |Δ| < {convergence_threshold}")
    print(f"  divergence |Δ| > {divergence_threshold}")
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

    # Storage per label
    node_freq = {lid: Counter() for lid in tracked}      # node → count
    convergence_moments = {lid: [] for lid in tracked}    # detailed snapshots
    divergence_moments = {lid: [] for lid in tracked}     # for comparison
    total_steps = {lid: 0 for lid in tracked}

    # Node-to-label map
    node_to_label = {}
    for lid, lab in vl.labels.items():
        if lid not in vl.macro_nodes:
            for n in lab["nodes"]:
                node_to_label[n] = lid

    bg_prob = BASE_PARAMS["background_injection_prob"]

    # ── Tracking Phase ──
    print(f"\n  --- Tracking Phase ({tracking_windows} windows "
          f"× {window_steps} steps) ---\n")

    for tw in range(tracking_windows):
        w = maturation_windows + tw
        t0 = time.time()

        # Spatial: once per window
        spatial_fields = {}
        for lid in tracked:
            if lid not in vl.labels:
                continue
            label = vl.labels[lid]
            core_alive = sum(1 for n in label["nodes"]
                             if n in engine.state.alive_n)
            if core_alive == 0:
                continue
            sp_set, core = compute_spatial(
                engine.state, label, torus_sub, core_alive)
            spatial_fields[lid] = (sp_set, core, core_alive)

        # Update node_to_label
        node_to_label = {}
        for lid, lab in vl.labels.items():
            if lid not in vl.macro_nodes:
                for n in lab["nodes"]:
                    node_to_label[n] = lid

        n_conv = 0
        n_div = 0

        for step in range(window_steps):
            # Physics (canon)
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
            gz = float(engine._g_scores.sum())

            engine.intruder.step(engine.state)
            engine.physics.step_decay_exclusion(engine.state)

            # BG seeding (canon)
            al = list(engine.state.alive_n)
            na = len(al)
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
                            if engine.state.Z[t] == 0 and \
                               engine.state.rng.random() < 0.5:
                                engine.state.Z[t] = 1 if \
                                    engine.state.rng.random() < 0.5 else 2

            # ── Structural perception ──
            link_adj = build_link_adj(engine.state)

            for lid in list(spatial_fields.keys()):
                if lid not in vl.labels:
                    continue
                sp_set, core, max_hops = spatial_fields[lid]
                label = vl.labels[lid]
                phase_sig = label["phase_sig"]

                struct_set = compute_structural(
                    core, max_hops, link_adj, engine.state.alive_n)

                # Node frequency counter
                for n in struct_set:
                    node_freq[lid][n] += 1
                total_steps[lid] += 1

                # Compute Δ_phase
                if len(struct_set) >= 2:
                    thetas = [float(engine.state.theta[n]) for n in struct_set]
                    sin_s = sum(math.sin(t) for t in thetas)
                    cos_s = sum(math.cos(t) for t in thetas)
                    mean_theta = math.atan2(sin_s, cos_s)
                else:
                    mean_theta = phase_sig
                    thetas = [float(engine.state.theta[n]) for n in struct_set]

                delta = circular_diff(phase_sig, mean_theta)
                abs_delta = abs(delta)

                # ── Convergence moment: record full detail ──
                if abs_delta < convergence_threshold:
                    # Classify nodes in structural set
                    self_nodes = []
                    wild_nodes = []
                    other_label_nodes = defaultdict(list)
                    for n in struct_set:
                        if n in core:
                            self_nodes.append(n)
                        else:
                            owner = node_to_label.get(n)
                            if owner is not None and owner != lid:
                                other_label_nodes[owner].append(n)
                            else:
                                wild_nodes.append(n)

                    # θ distribution in structural set
                    near_phase = sum(1 for t in thetas
                                     if abs(circular_diff(phase_sig, t)) < math.pi/4)

                    convergence_moments[lid].append({
                        "w": w, "step": step,
                        "delta": round(delta, 4),
                        "abs_delta": round(abs_delta, 4),
                        "st_total": len(struct_set),
                        "self_count": len(self_nodes),
                        "wild_count": len(wild_nodes),
                        "other_labels": {str(k): len(v)
                                          for k, v in other_label_nodes.items()},
                        "n_other_labels": len(other_label_nodes),
                        "near_phase_ratio": round(
                            near_phase / max(1, len(struct_set)), 4),
                        "mean_theta": round(mean_theta, 4),
                        "struct_nodes": sorted(struct_set),
                    })
                    n_conv += 1

                # ── Divergence moment: record for comparison ──
                elif abs_delta > divergence_threshold:
                    wild_count = 0
                    other_count = 0
                    for n in struct_set:
                        if n not in core:
                            owner = node_to_label.get(n)
                            if owner is not None and owner != lid:
                                other_count += 1
                            else:
                                wild_count += 1

                    near_phase = sum(1 for t in thetas
                                     if abs(circular_diff(phase_sig, t)) < math.pi/4)

                    divergence_moments[lid].append({
                        "w": w, "step": step,
                        "delta": round(delta, 4),
                        "abs_delta": round(abs_delta, 4),
                        "st_total": len(struct_set),
                        "wild_count": wild_count,
                        "other_count": other_count,
                        "near_phase_ratio": round(
                            near_phase / max(1, len(struct_set)), 4),
                        "struct_nodes": sorted(struct_set),
                    })
                    n_div += 1

        # Window end: virtual layer step
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
        print(f"  w={w:>3} links={len(engine.state.alive_l):>5} "
              f"conv={n_conv} div={n_div} {sec:.0f}s")

    # ════════════════════════════════════════════════════════
    # ANALYSIS
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*65}")
    print(f"  NODE FREQUENCY BIAS ANALYSIS")
    print(f"{'='*65}")

    for lid in case_labels:
        freq = node_freq.get(lid)
        if not freq or total_steps[lid] == 0:
            print(f"\n  Label {lid}: NO DATA")
            continue

        sp_set = spatial_fields.get(lid, (set(), set(), 0))[0]
        core = spatial_fields.get(lid, (set(), set(), 0))[1]
        ts = total_steps[lid]

        # Sort by frequency
        sorted_nodes = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        total_nodes_ever = len(sorted_nodes)

        # Core frequency
        core_freqs = [(n, freq[n]) for n in core if n in freq]

        # Top 20 non-core
        non_core = [(n, c) for n, c in sorted_nodes if n not in core]

        # Frequency distribution
        counts = [c for _, c in sorted_nodes]
        mean_freq = np.mean(counts)
        std_freq = np.std(counts)

        # Hotspots (> mean + 2*std)
        hotspot_threshold = mean_freq + 2 * std_freq
        hotspots = [(n, c) for n, c in sorted_nodes
                    if c > hotspot_threshold and n not in core]

        # Nodes that appear in convergence moments
        conv_nodes = Counter()
        for cm in convergence_moments.get(lid, []):
            for n in cm["struct_nodes"]:
                if n not in core:
                    conv_nodes[n] += 1

        div_nodes = Counter()
        for dm in divergence_moments.get(lid, []):
            for n in dm["struct_nodes"]:
                if n not in core:
                    div_nodes[n] += 1

        print(f"\n  --- Label {lid} ({ts} steps, "
              f"{total_nodes_ever} unique nodes ever in structural) ---")
        print(f"    Freq: mean={mean_freq:.1f} std={std_freq:.1f} "
              f"max={max(counts)}")
        print(f"    Core nodes: {[f'{n}({freq[n]})' for n, _ in core_freqs]}")

        print(f"\n    Top 15 non-core by frequency:")
        for n, c in non_core[:15]:
            pct = c / ts * 100
            owner = node_to_label.get(n, "wild")
            in_sp = "SP" if n in sp_set else "  "
            in_conv = conv_nodes.get(n, 0)
            in_div = div_nodes.get(n, 0)
            print(f"      node {n:>5}: {c:>5} ({pct:>5.1f}%) "
                  f"{in_sp} owner={str(owner):>5} "
                  f"conv={in_conv} div={in_div}")

        print(f"\n    Hotspots (>{hotspot_threshold:.0f} appearances, "
              f"non-core): {len(hotspots)}")
        for n, c in hotspots[:10]:
            owner = node_to_label.get(n, "wild")
            print(f"      node {n:>5}: {c:>5} owner={str(owner):>5}")

        # ── Convergence vs Divergence node comparison ──
        n_conv_m = len(convergence_moments.get(lid, []))
        n_div_m = len(divergence_moments.get(lid, []))
        print(f"\n    Convergence moments: {n_conv_m}")
        print(f"    Divergence moments: {n_div_m}")

        if conv_nodes and div_nodes:
            conv_only = set(conv_nodes.keys()) - set(div_nodes.keys())
            div_only = set(div_nodes.keys()) - set(conv_nodes.keys())
            both = set(conv_nodes.keys()) & set(div_nodes.keys())
            print(f"    Nodes appearing ONLY in convergence: {len(conv_only)}")
            print(f"    Nodes appearing ONLY in divergence: {len(div_only)}")
            print(f"    Nodes in both: {len(both)}")

            if conv_only:
                top_conv_only = sorted(conv_only,
                                        key=lambda n: conv_nodes[n],
                                        reverse=True)[:10]
                print(f"    Top convergence-only nodes:")
                for n in top_conv_only:
                    owner = node_to_label.get(n, "wild")
                    print(f"      node {n:>5}: conv={conv_nodes[n]} "
                          f"freq={freq.get(n, 0)} owner={str(owner):>5}")

    # ── Convergence moment details ──
    print(f"\n{'='*65}")
    print(f"  CONVERGENCE MOMENT DETAILS")
    print(f"{'='*65}")

    for lid in case_labels:
        moments = convergence_moments.get(lid, [])
        if not moments:
            print(f"\n  Label {lid}: No convergence moments")
            continue

        print(f"\n  --- Label {lid} ({len(moments)} moments) ---")

        # Average composition of convergence moments
        avg_st = np.mean([m["st_total"] for m in moments])
        avg_wild = np.mean([m["wild_count"] for m in moments])
        avg_near = np.mean([m["near_phase_ratio"] for m in moments])
        avg_others = np.mean([m["n_other_labels"] for m in moments])

        print(f"    Average composition:")
        print(f"      st_total={avg_st:.1f} wild={avg_wild:.1f} "
              f"near_phase={avg_near:.1%} other_labels={avg_others:.1f}")

        # Compare with divergence moments
        div_m = divergence_moments.get(lid, [])
        if div_m:
            d_avg_st = np.mean([m["st_total"] for m in div_m])
            d_avg_near = np.mean([m["near_phase_ratio"] for m in div_m])
            print(f"    vs Divergence:")
            print(f"      st_total={d_avg_st:.1f} "
                  f"near_phase={d_avg_near:.1%}")
            print(f"      → Convergence has {'more' if avg_near > d_avg_near else 'less'}"
                  f" near-phase nodes")

        # Node overlap between convergence moments
        if len(moments) >= 2:
            all_conv_sets = [set(m["struct_nodes"]) for m in moments]
            # Pairwise Jaccard
            jaccards = []
            for i in range(len(all_conv_sets)):
                for j in range(i+1, min(i+5, len(all_conv_sets))):
                    inter = len(all_conv_sets[i] & all_conv_sets[j])
                    union = len(all_conv_sets[i] | all_conv_sets[j])
                    if union > 0:
                        jaccards.append(inter / union)
            if jaccards:
                print(f"    Structural set overlap between convergence moments:")
                print(f"      Jaccard: mean={np.mean(jaccards):.4f} "
                      f"std={np.std(jaccards):.4f}")

        # Show first 5 moments
        print(f"\n    First 5 moments:")
        for m in moments[:5]:
            others = m["other_labels"]
            others_str = " ".join(f"L{k}:{v}" for k, v in others.items()) if others else "none"
            print(f"      w={m['w']} step={m['step']} "
                  f"|Δ|={m['abs_delta']:.4f} "
                  f"st={m['st_total']} wild={m['wild_count']} "
                  f"near={m['near_phase_ratio']:.0%} "
                  f"others=[{others_str}]")

    t_total = time.time() - t_start
    print(f"\n  Total time: {t_total/60:.1f} min")

    # ── Save ──
    outdir = Path(f"diag_v95_convergence_seed{seed}")
    outdir.mkdir(exist_ok=True)

    # Node frequency (without struct_nodes lists for size)
    freq_save = {}
    for lid in tracked:
        if node_freq[lid]:
            freq_save[str(lid)] = {
                "total_steps": total_steps[lid],
                "unique_nodes": len(node_freq[lid]),
                "top50": dict(node_freq[lid].most_common(50)),
            }
    with open(outdir / "node_frequency.json", "w") as f:
        json.dump(freq_save, f, indent=2)

    # Convergence moments (with struct_nodes)
    conv_save = {}
    for lid in case_labels:
        conv_save[str(lid)] = convergence_moments.get(lid, [])
    with open(outdir / "convergence_moments.json", "w") as f:
        json.dump(conv_save, f, indent=2)

    # Divergence moments (without struct_nodes for size)
    div_save = {}
    for lid in case_labels:
        div_save[str(lid)] = [{k: v for k, v in m.items()
                                if k != "struct_nodes"}
                               for m in divergence_moments.get(lid, [])]
    with open(outdir / "divergence_moments.json", "w") as f:
        json.dump(div_save, f, indent=2)

    print(f"  Saved: {outdir}/node_frequency.json")
    print(f"  Saved: {outdir}/convergence_moments.json")
    print(f"  Saved: {outdir}/divergence_moments.json")
    print(f"\n{'='*65}")
    print(f"  END Convergence Detail")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.5 Convergence Detail + Node Frequency Bias")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--maturation-windows", type=int, default=20)
    parser.add_argument("--tracking-windows", type=int, default=5)
    parser.add_argument("--window-steps", type=int, default=500)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--case-labels", type=str, default="87,101,112")
    parser.add_argument("--conv-threshold", type=float, default=0.3)
    parser.add_argument("--div-threshold", type=float, default=2.5)
    args = parser.parse_args()

    cases = [int(x) for x in args.case_labels.split(",")]
    run(seed=args.seed,
        maturation_windows=args.maturation_windows,
        tracking_windows=args.tracking_windows,
        window_steps=args.window_steps,
        case_labels=cases,
        top_k=args.top_k,
        convergence_threshold=args.conv_threshold,
        divergence_threshold=args.div_threshold)
