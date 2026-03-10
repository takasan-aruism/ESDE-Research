#!/usr/bin/env python3
"""
ESDE Cognition v3.2 — Concept Interaction Activation
======================================================
Phase : Cognition (v3.2)
Role  : Claude (Implementation)
Arch  : Gemini | Audit: GPT

PURPOSE
-------
Activate physical Merge/Split events between Concept A and Concept B.
v3.1 confirmed: domains persist, observer mapping is stable (checkerboard),
but merge=0 split=0 across all 100 seeds. Domains are static.

v3.2 introduces two minimal mechanisms to create boundary pressure:

  1. Semantic Diffusion: boundary nodes have a small probability per step
     of shifting their phase toward a neighboring concept's phase center.
     diffusion_probability = 0.005 (GPT recommended initial value)

  2. Cross-Boundary Link Bias: during realization (link birth), nodes at
     concept boundaries get a slight boost in p_link_birth for cross-concept
     links. boundary_link_boost = 1.5x (50% increase, applied only to
     cross-concept candidate links during seeding)

Both mechanisms are topological/probabilistic. No semantic rules.
Core physics unchanged. Ecology observations preserved.

CHANGES FROM v3.1
------------------
  - Semantic diffusion in quiet-phase step loop
  - Cross-boundary seeding boost
  - Same output schema (v3.1 compatible)
  - Output dir: outputs_v32/

USAGE
-----
  cd ~/esde/ESDE-Research/cognition/semantic_injection

  python cognition_v32.py --sanity
  parallel -j 20 python cognition_v32.py --seed {1} ::: $(seq 1 20)
  python cognition_v32.py --aggregate
"""

import numpy as np
import sys; from pathlib import Path as _P  # noqa
sys.path.insert(0, str(_P(__file__).resolve().parent.parent.parent / "ecology" / "engine"))

import engine_accel
from genesis_state import GenesisState as _GS
assert getattr(_GS.link_strength_sum, "__name__", "") == "_fast_link_strength_sum", \
    "FATAL: engine_accel failed to patch link_strength_sum."
del _GS

import matplotlib
matplotlib.use("Agg")
import csv, json, time, argparse, math
from collections import Counter, defaultdict
from pathlib import Path
from dataclasses import dataclass, asdict

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from chemistry import ChemistryEngine, ChemistryParams
from realization import RealizationOperator, RealizationParams
from autogrowth import AutoGrowthEngine, AutoGrowthParams
from intrusion import BoundaryIntrusionOperator, find_islands_sets

from v19g_canon import (
    OBSERVER_POLICY, HYST_THRESHOLD, LAMBDA, MU,
    K_LEVELS, WINDOW, QUIET_STEPS,
    BASE_PARAMS, ALL_SEEDS,
    INJECTION_STEPS, INJECT_INTERVAL, BETA, NODE_DECAY, BIAS, C_MAX,
    E_YIELD_SYN, E_YIELD_AUTO, TOPO_VAR,
    ctx_label, shannon, compute_J, select_k_star, SwitchEvent,
    init_fert,
)

# ================================================================
# COGNITION v3.2 CONSTANTS
# ================================================================
COG_N           = 5000
COG_PLB         = 0.007
COG_RATE        = 0.002
COG_SEEDS_SMALL = list(range(1, 21))   # initial 20 seeds
COG_SEEDS_FULL  = list(range(1, 101))  # expansion to 100
N_CONCEPTS_DEF  = 2
PHASE_SPREAD    = 0.3
CONCEPT_NAMES   = {0: "A", 1: "B", 2: "C"}

# v3.2: interaction parameters
DIFFUSION_PROB      = 0.005   # per boundary-node per step
DIFFUSION_STRENGTH  = 0.3     # how far toward neighbor's concept center
BOUNDARY_LINK_BOOST = 1.5     # multiplier on p_link_birth for cross-concept

# Merge/Split thresholds (same as v3.1)
MERGE_WEIGHT_THR    = 5.0
MERGE_PHASE_THR     = 0.5
SPLIT_MIN_COMP_SIZE = 3

GRID_ROWS = 2
GRID_COLS = 2
N_REGIONS = GRID_ROWS * GRID_COLS
MIN_C_NODES_FOR_VALID = 5

OUTPUT_DIR = Path("outputs_v32")


# ================================================================
# CONCEPT CLUSTER ASSIGNMENT (identical to v3.0/v3.1)
# ================================================================
def assign_concepts(N, n_concepts=2):
    side = int(math.ceil(math.sqrt(N)))
    concept_map = {}
    n_zones = 2 * n_concepts - 1
    zone_width = side / n_zones
    for i in range(N):
        col = i % side
        zone_idx = min(int(col / zone_width), n_zones - 1)
        if zone_idx % 2 == 0:
            cid = zone_idx // 2
            concept_map[i] = cid if cid < n_concepts else -1
        else:
            concept_map[i] = -1
    return concept_map


def inject_concept_phases(state, concept_map, n_concepts=2):
    centers = {c: (c + 0.5) * np.pi / n_concepts for c in range(n_concepts)}
    for node_id, cid in concept_map.items():
        if cid >= 0 and node_id < state.n_nodes:
            center = centers[cid]
            state.theta[node_id] = (center
                + state.rng.uniform(-PHASE_SPREAD, PHASE_SPREAD)) % (2 * np.pi)
    return centers  # return for diffusion use


def concept_zone_summary(concept_map, N):
    counts = Counter(concept_map.values())
    parts = []
    for c in sorted(counts):
        label = CONCEPT_NAMES.get(c, "neutral") if c >= 0 else "neutral"
        parts.append(f"{label}={counts[c]}")
    return ", ".join(parts)


# ================================================================
# CONCEPT BOUNDARY DETECTION
# ================================================================
def find_concept_boundary_nodes(state, concept_map):
    """
    Nodes whose concept differs from at least one alive neighbor's concept.
    Returns: set of node_ids that are on concept boundaries.
    """
    boundary = set()
    for n in state.alive_n:
        cn = concept_map.get(n, -1)
        if cn < 0:
            continue
        for nb in state.neighbors(n):
            if nb in state.alive_n:
                cnb = concept_map.get(nb, -1)
                if cnb >= 0 and cnb != cn:
                    boundary.add(n)
                    break
    return boundary


# ================================================================
# v3.2: SEMANTIC DIFFUSION
# ================================================================
def apply_semantic_diffusion(state, concept_map, concept_centers,
                             boundary_nodes, rng):
    """
    Boundary nodes have a small probability of shifting their phase
    toward a neighboring concept's phase center.
    Pure phase perturbation — no state changes.
    Returns: count of diffusion events.
    """
    events = 0
    for n in boundary_nodes:
        if rng.random() > DIFFUSION_PROB:
            continue
        cn = concept_map.get(n, -1)
        if cn < 0:
            continue
        # Find a neighbor with different concept
        diff_nbs = []
        for nb in state.neighbors(n):
            if nb in state.alive_n:
                cnb = concept_map.get(nb, -1)
                if cnb >= 0 and cnb != cn:
                    diff_nbs.append(nb)
        if not diff_nbs:
            continue
        # Pick a random different-concept neighbor
        target_nb = diff_nbs[rng.randint(len(diff_nbs))]
        target_c = concept_map[target_nb]
        target_center = concept_centers[target_c]
        # Shift phase toward target concept center
        current_theta = state.theta[n]
        diff = (target_center - current_theta + np.pi) % (2 * np.pi) - np.pi
        state.theta[n] = (current_theta + DIFFUSION_STRENGTH * diff) % (2 * np.pi)
        events += 1
    return events


# ================================================================
# v3.2: CROSS-BOUNDARY SEEDING BOOST
# ================================================================
def boosted_seeding(state, concept_map, boundary_nodes, g_scores, gz, rng):
    """
    Standard seeding with a boost: boundary nodes that seed a
    cross-concept neighbor get BOUNDARY_LINK_BOOST × base probability.
    """
    al = list(state.alive_n)
    na = len(al)
    if na == 0:
        return

    aa = np.array(al)
    if BIAS > 0 and gz > 0:
        ga = g_scores[aa]
        gs = ga.sum()
        if gs > 0:
            pg = ga / gs
            pd = (1 - BIAS) * (np.ones(na) / na) + BIAS * pg
            pd /= pd.sum()
        else:
            pd = np.ones(na) / na
    else:
        pd = np.ones(na) / na

    base_prob = BASE_PARAMS["background_injection_prob"]
    for idx in range(na):
        node = al[idx]
        # Boost probability for boundary nodes
        p = base_prob
        if node in boundary_nodes:
            p = min(base_prob * BOUNDARY_LINK_BOOST, 1.0)
        if rng.random() < p:
            t = int(rng.choice(aa, p=pd))
            state.E[t] = min(1.0, state.E[t] + 0.3)
            if state.Z[t] == 0 and rng.random() < 0.5:
                state.Z[t] = 1 if rng.random() < 0.5 else 2


# ================================================================
# SPATIAL PARTITION (2x2)
# ================================================================
def assign_regions(N, rows=GRID_ROWS, cols=GRID_COLS):
    side = int(math.ceil(math.sqrt(N)))
    region_map = {}
    for i in range(N):
        r = i // side
        c = i % side
        rr = min(r * rows // side, rows - 1)
        rc = min(c * cols // side, cols - 1)
        region_map[i] = rr * cols + rc
    return region_map


def compute_local_observer(nodes, prev_nodes, current_k):
    n_c = len(nodes)
    if n_c < MIN_C_NODES_FOR_VALID:
        return None, {}, {}, n_c
    j_scores = {}
    for k in K_LEVELS:
        j, h, dr, tc = compute_J(nodes, prev_nodes, k)
        j_scores[k] = j
    new_k = select_k_star(j_scores, current_k)
    return new_k, j_scores, {}, n_c


# ================================================================
# CONCEPT WINDOW METRICS (same as v3.1)
# ================================================================
def compute_concept_window(state, concept_map, n_concepts,
                           region_map, islands_m):
    concept_island_count = {c: 0 for c in range(n_concepts)}
    concept_nodes_in_islands = {c: 0 for c in range(n_concepts)}
    labeled_islands = []

    for isl in islands_m:
        c_in_isl = [n for n in isl
                     if n in state.alive_n and int(state.Z[n]) == 3]
        if len(c_in_isl) < 3:
            continue
        cc = Counter(concept_map.get(n, -1) for n in c_in_isl)
        total_concept = sum(v for k, v in cc.items() if k >= 0)
        if total_concept == 0:
            continue
        for c in range(n_concepts):
            if cc.get(c, 0) / total_concept > 0.5:
                concept_island_count[c] += 1
                concept_nodes_in_islands[c] += cc[c]
                labeled_islands.append((c, frozenset(n for n in isl
                                                      if n in state.alive_n)))
                break

    boundary_links = 0
    boundary_weight = 0.0
    pair_links = Counter()
    pair_weight = defaultdict(float)
    for (i, j) in state.alive_l:
        ci = concept_map.get(i, -1)
        cj = concept_map.get(j, -1)
        if ci >= 0 and cj >= 0 and ci != cj:
            boundary_links += 1
            boundary_weight += state.S[(i, j)]
            pair = (min(ci, cj), max(ci, cj))
            pair_links[pair] += 1
            pair_weight[pair] += state.S[(i, j)]

    all_c = [n for n in state.alive_n if int(state.Z[n]) == 3]
    cdist = Counter(concept_map.get(n, -1) for n in all_c)
    total = sum(cdist.values())
    entropy = 0.0
    if total > 0:
        for v in cdist.values():
            p = v / total
            if p > 0:
                entropy -= p * np.log2(p)

    region_entropy = {}
    for r in range(N_REGIONS):
        rc_nodes = [n for n in all_c if region_map.get(n) == r]
        rc_dist = Counter(concept_map.get(n, -1) for n in rc_nodes)
        rc_total = sum(rc_dist.values())
        re = 0.0
        if rc_total > 0:
            for v in rc_dist.values():
                p = v / rc_total
                if p > 0:
                    re -= p * np.log2(p)
        region_entropy[r] = round(re, 4)

    obs_concept = {}
    for r in range(N_REGIONS):
        rc_nodes = [n for n in all_c if region_map.get(n) == r]
        if not rc_nodes:
            obs_concept[r] = -1
            continue
        rc = Counter(concept_map.get(n, -1) for n in rc_nodes)
        best_c, best_n = -1, 0
        for c in range(n_concepts):
            if rc.get(c, 0) > best_n:
                best_c = c
                best_n = rc[c]
        obs_concept[r] = best_c if best_n > len(rc_nodes) * 0.3 else -1

    concept_c_counts = {c: 0 for c in range(n_concepts)}
    concept_c_counts[-1] = 0
    for n in all_c:
        cid = concept_map.get(n, -1)
        concept_c_counts[cid] = concept_c_counts.get(cid, 0) + 1

    return {
        "concept_island_count": concept_island_count,
        "concept_nodes_in_islands": concept_nodes_in_islands,
        "boundary_links": boundary_links,
        "boundary_weight": round(boundary_weight, 4),
        "pair_links": dict(pair_links),
        "pair_weight": {str(k): round(v, 4) for k, v in pair_weight.items()},
        "concept_entropy": round(entropy, 4),
        "region_entropy": region_entropy,
        "observer_concept": obs_concept,
        "concept_c_counts": concept_c_counts,
        "total_c_nodes": len(all_c),
        "labeled_islands": labeled_islands,
    }


# ================================================================
# MERGE / SPLIT DETECTION (same as v3.1)
# ================================================================
def detect_merge_split(state, concept_map, n_concepts,
                       prev_labeled, curr_labeled):
    merges = []
    splits = []

    for i, (c_i, nodes_i) in enumerate(curr_labeled):
        for j, (c_j, nodes_j) in enumerate(curr_labeled):
            if j <= i or c_i == c_j:
                continue
            cross_weight = 0.0
            cross_count = 0
            phase_diffs = []
            for n in nodes_i:
                for nb in state.neighbors(n):
                    if nb in nodes_j:
                        k = state.key(n, nb)
                        if k in state.alive_l:
                            cross_weight += state.S[k]
                            cross_count += 1
                            phase_diffs.append(state.theta[nb] - state.theta[n])
            if cross_weight >= MERGE_WEIGHT_THR and phase_diffs:
                mean_cos = float(np.mean(np.cos(phase_diffs)))
                if mean_cos > MERGE_PHASE_THR:
                    merges.append({
                        "concepts": (c_i, c_j),
                        "cross_weight": round(cross_weight, 4),
                        "cross_links": cross_count,
                        "phase_cos": round(mean_cos, 4),
                        "sizes": (len(nodes_i), len(nodes_j)),
                    })

    if prev_labeled:
        curr_adj = defaultdict(set)
        for (a, b) in state.alive_l:
            if state.S[(a, b)] >= 0.20:
                curr_adj[a].add(b)
                curr_adj[b].add(a)

        for prev_c, prev_nodes in prev_labeled:
            alive_prev = frozenset(n for n in prev_nodes if n in state.alive_n)
            if len(alive_prev) < SPLIT_MIN_COMP_SIZE * 2:
                continue
            visited = set()
            components = []
            for n in alive_prev:
                if n in visited:
                    continue
                comp = set()
                queue = [n]
                while queue:
                    nd = queue.pop()
                    if nd in visited or nd not in alive_prev:
                        continue
                    visited.add(nd)
                    comp.add(nd)
                    for nb in curr_adj.get(nd, set()):
                        if nb in alive_prev and nb not in visited:
                            queue.append(nb)
                components.append(comp)
            significant = [c for c in components
                          if len(c) >= SPLIT_MIN_COMP_SIZE]
            if len(significant) >= 2:
                splits.append({
                    "concept": prev_c,
                    "prev_size": len(alive_prev),
                    "n_fragments": len(significant),
                    "fragment_sizes": sorted([len(c) for c in significant],
                                            reverse=True),
                })

    return merges, splits


# ================================================================
# MAIN SIMULATION
# ================================================================
def run_cognition(seed, N=COG_N, plb=COG_PLB, rate=COG_RATE,
                  quiet_steps=QUIET_STEPS, n_concepts=N_CONCEPTS_DEF,
                  diffusion_prob=DIFFUSION_PROB,
                  boundary_boost=BOUNDARY_LINK_BOOST):
    p = dict(BASE_PARAMS)
    p["p_link_birth"] = plb

    state = GenesisState(N, C_MAX, seed)
    init_fert(state, TOPO_VAR, seed)

    concept_map = assign_concepts(N, n_concepts)
    concept_centers = inject_concept_phases(state, concept_map, n_concepts)
    region_map = assign_regions(N)

    physics = GenesisPhysics(PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True,
        phase_enabled=True, beta=BETA, decay_rate_node=NODE_DECAY,
        K_sync=0.1, alpha=0.0, gamma=1.0))
    cp = ChemistryParams(enabled=True, E_thr=p["reaction_energy_threshold"],
        exothermic_release=p["exothermic_release_amount"],
        E_yield_syn=E_YIELD_SYN, E_yield_auto=E_YIELD_AUTO)
    chem = ChemistryEngine(cp)
    rp = RealizationParams(enabled=True, p_link_birth=plb,
        latent_to_active_threshold=p["latent_to_active_threshold"],
        latent_refresh_rate=p["latent_refresh_rate"])
    realizer = RealizationOperator(rp)
    grower = AutoGrowthEngine(AutoGrowthParams(enabled=True,
        auto_growth_rate=p["auto_growth_rate"]))
    intruder = BoundaryIntrusionOperator(intrusion_rate=rate)
    state.EXTINCTION = p["link_death_threshold"]

    g_scores = np.zeros(N)
    t0 = time.time()
    node_intr = Counter()
    total_diffusion_events = 0

    # Injection phase (unchanged)
    for step in range(INJECTION_STEPS):
        if step % INJECT_INTERVAL == 0:
            tgts = physics.inject(state)
            chem.seed_on_injection(state, tgts or [])
        physics.step_pre_chemistry(state)
        chem.step(state)
        physics.step_resonance(state)
        grower.step(state)
        physics.step_decay_exclusion(state)

    # Quiet phase
    k_star_seq = []
    switch_events = []
    margin_seq = []
    prev_nodes_global = None
    current_k_global = None
    island_summaries = []

    prev_nodes_region = {r: None for r in range(N_REGIONS)}
    current_k_region = {r: None for r in range(N_REGIONS)}
    region_k_seqs = {r: [] for r in range(N_REGIONS)}

    concept_streaks = {c: 0 for c in range(n_concepts)}
    concept_max_streaks = {c: 0 for c in range(n_concepts)}
    concept_windows_with_island = {c: 0 for c in range(n_concepts)}

    prev_labeled_islands = []
    total_merge_events = 0
    total_split_events = 0
    merge_log = []
    split_log = []

    window_logs = []
    concept_window_logs = []

    _eta_t0 = time.time()
    _eta_total_windows = quiet_steps // WINDOW

    for step in range(quiet_steps):
        # === PHYSICS (identical to canonical) ===
        realizer.step(state)
        physics.step_pre_chemistry(state)
        chem.step(state)
        physics.step_resonance(state)
        g_scores[:] = 0
        grower.step(state)
        for k in state.alive_l:
            r = state.R.get(k, 0.0)
            if r > 0:
                a = min(grower.params.auto_growth_rate * r,
                        max(state.get_latent(k[0], k[1]), 0))
                if a > 0:
                    g_scores[k[0]] += a
                    g_scores[k[1]] += a
        gz = float(g_scores.sum())
        pre_S = {k: state.S[k] for k in state.alive_l}
        intruder.step(state)
        for k in state.alive_l:
            if k in pre_S and abs(state.S[k] - pre_S[k]) > 0.001:
                node_intr[k[0]] += 1
                node_intr[k[1]] += 1
        physics.step_decay_exclusion(state)

        # === v3.2: SEMANTIC DIFFUSION (after physics, before seeding) ===
        boundary_nodes = find_concept_boundary_nodes(state, concept_map)
        total_diffusion_events += apply_semantic_diffusion(
            state, concept_map, concept_centers, boundary_nodes, state.rng)

        # === v3.2: BOOSTED SEEDING (replaces standard seeding) ===
        boosted_seeding(state, concept_map, boundary_nodes,
                        g_scores, gz, state.rng)

        # ============================================================
        # WINDOW OBSERVATION
        # ============================================================
        if (step + 1) % WINDOW == 0:
            win_idx = (step + 1) // WINDOW

            _eta_elapsed = time.time() - _eta_t0
            if win_idx > 0:
                _eta_per_win = _eta_elapsed / win_idx
                _eta_remaining = _eta_per_win * (_eta_total_windows - win_idx)
                if win_idx % 5 == 0 or win_idx == _eta_total_windows:
                    print(f"    window {win_idx}/{_eta_total_windows}  "
                          f"elapsed={_eta_elapsed:.0f}s  "
                          f"ETA={_eta_remaining:.0f}s  "
                          f"total~{_eta_per_win * _eta_total_windows:.0f}s",
                          flush=True)

            isl_s = find_islands_sets(state, 0.30)
            isl_m = find_islands_sets(state, 0.20)
            isl_w = find_islands_sets(state, 0.10)
            nm_s = {n: 1 for isl in isl_s for n in isl}
            nm_m = {n: 1 for isl in isl_m for n in isl}
            nm_w = {n: 1 for isl in isl_w for n in isl}
            bnd_m = set()
            for isl in isl_m:
                for n in isl:
                    if n not in state.alive_n:
                        continue
                    for nb in state.neighbors(n):
                        if nb in state.alive_n and nb not in isl:
                            bnd_m.add(n)
                            break

            all_nodes = []
            all_nodes_with_id = []
            for i in state.alive_n:
                if int(state.Z[i]) != 3:
                    continue
                s = 1 if i in nm_s else 0
                m = 1 if i in nm_m else 0
                w = 1 if i in nm_w else 0
                ctx = {
                    "r_bits": f"{s}{m}{w}",
                    "boundary_mid": 1 if i in bnd_m else 0,
                    "intrusion_bin": min(node_intr.get(i, 0), 2),
                }
                all_nodes.append(ctx)
                all_nodes_with_id.append({"node_id": i, **ctx})

            n_C = len(all_nodes)

            if all_nodes:
                j_scores_g = {}
                for k in K_LEVELS:
                    j, h, dr, tc = compute_J(all_nodes, prev_nodes_global, k)
                    j_scores_g[k] = j
                new_k_g = select_k_star(j_scores_g, current_k_global)
                if current_k_global is not None and new_k_g != current_k_global:
                    switch_events.append(SwitchEvent(
                        seed=seed, N=N, window=win_idx,
                        step=(step + 1),
                        prev_k=current_k_global, new_k=new_k_g,
                        margin=round(j_scores_g.get(new_k_g, 0)
                                     - j_scores_g.get(current_k_global, 0), 6),
                        threshold=HYST_THRESHOLD,
                        j3=round(j_scores_g.get(3, 0), 6),
                        j4=round(j_scores_g.get(4, 0), 6),
                        h3=0.0, h4=0.0))
                current_k_global = new_k_g
                k_star_seq.append(new_k_g)
                margin = max(j_scores_g.values()) - sorted(
                    j_scores_g.values())[-2] if len(j_scores_g) > 1 else 0
                margin_seq.append(margin)
                prev_nodes_global = all_nodes
            else:
                k_star_seq.append(current_k_global or 0)
                margin_seq.append(0)

            island_summaries.append({
                "n_C": n_C,
                "n_islands_mid": len(isl_m),
                "none_ratio": round(sum(1 for nd in all_nodes
                    if nd["r_bits"] == "000") / max(n_C, 1), 4) if all_nodes else 0,
            })

            wlog = {
                "seed": seed, "window": win_idx,
                "global_k": current_k_global or 0,
                "global_n_C": n_C,
            }
            div_flag = 0
            for r in range(N_REGIONS):
                r_nodes = [nd for nd in all_nodes_with_id
                           if region_map.get(nd["node_id"]) == r]
                r_ctx = [{k: v for k, v in nd.items() if k != "node_id"}
                         for nd in r_nodes]
                new_k_r, _, _, r_n_c = compute_local_observer(
                    r_ctx, prev_nodes_region[r], current_k_region[r])
                if new_k_r is not None:
                    current_k_region[r] = new_k_r
                    prev_nodes_region[r] = r_ctx
                region_k_seqs[r].append(current_k_region[r] or 0)
                wlog[f"r{r}_k"] = current_k_region[r] or 0
                wlog[f"r{r}_n_C"] = r_n_c
                if (current_k_region[r] or 0) != (current_k_global or 0):
                    div_flag = 1
            wlog["divergence_flag"] = div_flag

            cmet = compute_concept_window(
                state, concept_map, n_concepts, region_map, isl_m)

            curr_labeled = cmet["labeled_islands"]
            m_events, s_events = detect_merge_split(
                state, concept_map, n_concepts,
                prev_labeled_islands, curr_labeled)
            total_merge_events += len(m_events)
            total_split_events += len(s_events)
            for me in m_events:
                merge_log.append({"window": win_idx, **me})
            for se in s_events:
                split_log.append({"window": win_idx, **se})
            prev_labeled_islands = curr_labeled

            for c in range(n_concepts):
                if cmet["concept_island_count"][c] > 0:
                    concept_streaks[c] += 1
                    concept_windows_with_island[c] += 1
                    concept_max_streaks[c] = max(
                        concept_max_streaks[c], concept_streaks[c])
                else:
                    concept_streaks[c] = 0

            clog = {"seed": seed, "window": win_idx}
            for c in range(n_concepts):
                cn = CONCEPT_NAMES[c]
                clog[f"{cn}_islands"] = cmet["concept_island_count"][c]
                clog[f"{cn}_nodes_in_isl"] = cmet["concept_nodes_in_islands"][c]
                clog[f"{cn}_c_nodes"] = cmet["concept_c_counts"].get(c, 0)
            clog["boundary_links"] = cmet["boundary_links"]
            clog["boundary_weight"] = cmet["boundary_weight"]
            clog["concept_entropy"] = cmet["concept_entropy"]
            for r in range(N_REGIONS):
                clog[f"r{r}_entropy"] = cmet["region_entropy"][r]
            clog["total_c_nodes"] = cmet["total_c_nodes"]
            for r in range(N_REGIONS):
                oc = cmet["observer_concept"][r]
                clog[f"r{r}_concept"] = CONCEPT_NAMES.get(oc, "neutral")
            clog["global_k"] = current_k_global or 0
            clog["div_flag"] = div_flag
            clog["merge_count"] = len(m_events)
            clog["split_count"] = len(s_events)
            concept_window_logs.append(clog)
            window_logs.append(wlog)

    # ============================================================
    # RESULT ASSEMBLY
    # ============================================================
    elapsed = time.time() - t0
    n_windows = len(k_star_seq)

    kc = Counter(k_star_seq)
    dom_k, dom_count = kc.most_common(1)[0] if kc else (0, 0)
    dom_frac = dom_count / max(n_windows, 1)
    sw_count = sum(1 for i in range(1, len(k_star_seq))
                   if k_star_seq[i] != k_star_seq[i-1])
    sw_per_100 = round(sw_count / max(n_windows - 1, 1) * 100, 1)

    div_flags = [w.get("divergence_flag", 0) for w in window_logs]
    divergence_ratio = round(sum(div_flags) / max(len(div_flags), 1), 4)
    episodes = []
    cur_start = None
    for i, df in enumerate(div_flags):
        if df == 1 and cur_start is None:
            cur_start = i
        elif df == 0 and cur_start is not None:
            episodes.append(i - cur_start)
            cur_start = None
    if cur_start is not None:
        episodes.append(len(div_flags) - cur_start)
    SHORT_LONG_THRESHOLD = 5
    long_div = sum(1 for e in episodes if e >= SHORT_LONG_THRESHOLD)
    if long_div >= 1:
        regime_label = "long_drift"
    elif sum(1 for e in episodes if e < SHORT_LONG_THRESHOLD) >= 2:
        regime_label = "short_burst"
    elif sum(div_flags) <= 2:
        regime_label = "quiet"
    else:
        regime_label = "mixed"

    concept_summary = {}
    for c in range(n_concepts):
        cn = CONCEPT_NAMES[c]
        concept_summary[cn] = {
            "persistence_frac": round(
                concept_windows_with_island[c] / max(n_windows, 1), 4),
            "max_streak": concept_max_streaks[c],
            "mean_islands": round(np.mean(
                [cl[f"{cn}_islands"] for cl in concept_window_logs]), 2),
            "mean_nodes_in_isl": round(np.mean(
                [cl[f"{cn}_nodes_in_isl"] for cl in concept_window_logs]), 1),
        }

    mean_bnd_links = round(np.mean(
        [cl["boundary_links"] for cl in concept_window_logs]), 1)
    mean_bnd_weight = round(np.mean(
        [cl["boundary_weight"] for cl in concept_window_logs]), 4)
    mean_entropy = round(np.mean(
        [cl["concept_entropy"] for cl in concept_window_logs]), 4)

    obs_concept_dominant = {}
    for r in range(N_REGIONS):
        rc = Counter(cl[f"r{r}_concept"] for cl in concept_window_logs)
        obs_concept_dominant[f"r{r}"] = rc.most_common(1)[0][0] if rc else "neutral"

    corr_div_ent = np.nan
    if len(concept_window_logs) >= 5:
        div_series = []
        ent_series = []
        for wl, cl in zip(window_logs, concept_window_logs):
            n_div = sum(1 for r in range(N_REGIONS)
                        if wl.get(f"r{r}_k", 0) != wl.get("global_k", 0))
            div_series.append(n_div)
            mean_re = np.mean([cl.get(f"r{r}_entropy", 0)
                              for r in range(N_REGIONS)])
            ent_series.append(mean_re)
        if np.std(div_series) > 0 and np.std(ent_series) > 0:
            corr_div_ent = round(float(
                np.corrcoef(div_series, ent_series)[0, 1]), 4)

    result = {
        "N": N, "seed": int(seed), "plb": plb, "rate": rate,
        "quiet_steps": quiet_steps, "n_windows": n_windows,
        "n_concepts": n_concepts,
        # v3.2 params
        "diffusion_prob": diffusion_prob,
        "boundary_link_boost": boundary_boost,
        "total_diffusion_events": total_diffusion_events,
        # Ecology
        "global_dominant_k": dom_k,
        "global_dom_frac": round(dom_frac, 4),
        "global_switches_per_100": sw_per_100,
        "global_mean_n_C": round(np.mean(
            [s["n_C"] for s in island_summaries]), 1) if island_summaries else 0,
        "global_mean_none_ratio": round(np.mean(
            [s["none_ratio"] for s in island_summaries]), 4) if island_summaries else 0,
        "divergence_ratio": divergence_ratio,
        "divergence_episode_count": len(episodes),
        "run_regime_label": regime_label,
        # Concept
        "concept_summary": concept_summary,
        "mean_boundary_links": mean_bnd_links,
        "mean_boundary_weight": mean_bnd_weight,
        "mean_concept_entropy": mean_entropy,
        "observer_concept_dominant": obs_concept_dominant,
        # Merge/Split
        "merge_count": total_merge_events,
        "split_count": total_split_events,
        # Correlation
        "corr_divergence_entropy": corr_div_ent,
        "elapsed": round(elapsed, 1),
    }

    return result, window_logs, concept_window_logs, \
        [asdict(se) for se in switch_events], merge_log, split_log


# ================================================================
# AGGREGATE
# ================================================================
def aggregate():
    results = []
    for f in sorted(OUTPUT_DIR.glob("seed_*.json")):
        if "_window" in f.name or "_concept" in f.name \
           or "_switch" in f.name or "_merge" in f.name or "_split" in f.name:
            continue
        with open(f) as fh:
            results.append(json.load(fh))

    if not results:
        print("  No results found.")
        return

    n = len(results)
    print(f"\n{'='*80}")
    print(f"  ESDE Cognition v3.2 — Aggregate ({n} seeds)")
    print(f"  diffusion_prob={results[0].get('diffusion_prob', '?')} "
          f"boundary_boost={results[0].get('boundary_link_boost', '?')}")
    print(f"{'='*80}")

    print(f"\n  Ecology Stability:")
    gk_dist = Counter(r["global_dominant_k"] for r in results)
    print(f"    Global k*: " + ", ".join(
        f"k={k}:{v}" for k, v in sorted(gk_dist.items())))
    regimes = Counter(r["run_regime_label"] for r in results)
    print(f"    Regimes: {dict(regimes)}")
    print(f"    Mean div ratio: "
          f"{np.mean([r['divergence_ratio'] for r in results]):.3f}")

    print(f"\n  Concept Persistence:")
    for cn in ["A", "B"]:
        persis = [r["concept_summary"][cn]["persistence_frac"]
                  for r in results if cn in r["concept_summary"]]
        streaks = [r["concept_summary"][cn]["max_streak"]
                   for r in results if cn in r["concept_summary"]]
        print(f"    {cn}: persist={np.mean(persis):.3f}±{np.std(persis):.3f} "
              f"streak={np.mean(streaks):.1f}±{np.std(streaks):.1f}")

    print(f"\n  Boundary & Entropy:")
    print(f"    Links: {np.mean([r['mean_boundary_links'] for r in results]):.1f}")
    print(f"    Weight: {np.mean([r['mean_boundary_weight'] for r in results]):.4f}")
    print(f"    Entropy: {np.mean([r['mean_concept_entropy'] for r in results]):.4f}")

    print(f"\n  Diffusion Events:")
    de = [r.get("total_diffusion_events", 0) for r in results]
    print(f"    Mean: {np.mean(de):.0f}  Range: [{min(de)}, {max(de)}]")

    print(f"\n  Merge/Split Events:")
    mc = [r["merge_count"] for r in results]
    sc = [r["split_count"] for r in results]
    print(f"    Merges: mean={np.mean(mc):.2f} max={max(mc)} "
          f"seeds>0: {sum(1 for x in mc if x > 0)}/{n}")
    print(f"    Splits: mean={np.mean(sc):.2f} max={max(sc)} "
          f"seeds>0: {sum(1 for x in sc if x > 0)}/{n}")

    print(f"\n  Divergence-Entropy Correlation:")
    valid_corr = [r["corr_divergence_entropy"] for r in results
                  if not np.isnan(r.get("corr_divergence_entropy", np.nan))]
    if valid_corr:
        print(f"    Mean r: {np.mean(valid_corr):.4f}±{np.std(valid_corr):.4f}")

    print(f"\n  Observer Mapping:")
    for r_idx in range(N_REGIONS):
        rkey = f"r{r_idx}"
        mapping = Counter(r["observer_concept_dominant"][rkey] for r in results)
        print(f"    {rkey}: {dict(mapping)}")

    rows = []
    for r in results:
        row = {
            "seed": r["seed"],
            "global_k": r["global_dominant_k"],
            "global_sw": r["global_switches_per_100"],
            "div_ratio": r["divergence_ratio"],
            "regime": r["run_regime_label"],
            "mean_bnd_links": r["mean_boundary_links"],
            "mean_bnd_weight": r["mean_boundary_weight"],
            "concept_entropy": r["mean_concept_entropy"],
            "merge_count": r["merge_count"],
            "split_count": r["split_count"],
            "diffusion_events": r.get("total_diffusion_events", 0),
            "corr_div_ent": r["corr_divergence_entropy"],
        }
        for cn in ["A", "B"]:
            if cn in r["concept_summary"]:
                cs = r["concept_summary"][cn]
                row[f"{cn}_persist"] = cs["persistence_frac"]
                row[f"{cn}_max_streak"] = cs["max_streak"]
                row[f"{cn}_mean_isl"] = cs["mean_islands"]
        for r_idx in range(N_REGIONS):
            row[f"r{r_idx}_concept"] = r["observer_concept_dominant"][f"r{r_idx}"]
        rows.append(row)

    csv_path = OUTPUT_DIR / "cognition_v32_summary.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"\n  CSV: {csv_path}")


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(
        description="ESDE Cognition v3.2 — Concept Interaction Activation")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--N", type=int, default=COG_N)
    parser.add_argument("--plb", type=float, default=COG_PLB)
    parser.add_argument("--rate", type=float, default=COG_RATE)
    parser.add_argument("--quiet-steps", type=int, default=QUIET_STEPS)
    parser.add_argument("--n-concepts", type=int, default=N_CONCEPTS_DEF)
    parser.add_argument("--diffusion-prob", type=float, default=DIFFUSION_PROB)
    parser.add_argument("--boundary-boost", type=float, default=BOUNDARY_LINK_BOOST)
    parser.add_argument("--aggregate", action="store_true")
    parser.add_argument("--sanity", action="store_true")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.sanity:
        print(f"  SANITY: N={args.N} rate={args.rate} seed=42 quiet=500 "
              f"diff_prob={args.diffusion_prob} bnd_boost={args.boundary_boost}")
        cmap = assign_concepts(args.N, args.n_concepts)
        print(f"  Zones: {concept_zone_summary(cmap, args.N)}")
        res, wl, cl, sw, ml, sl = run_cognition(
            42, args.N, args.plb, args.rate,
            quiet_steps=500, n_concepts=args.n_concepts,
            diffusion_prob=args.diffusion_prob,
            boundary_boost=args.boundary_boost)
        print(f"  k*={res['global_dominant_k']} div={res['divergence_ratio']:.2f}")
        for cn in ["A", "B"]:
            cs = res["concept_summary"][cn]
            print(f"  {cn}: persist={cs['persistence_frac']:.2f} "
                  f"isl={cs['mean_islands']:.2f}")
        print(f"  Boundary: links={res['mean_boundary_links']:.1f}")
        print(f"  Diffusion events: {res['total_diffusion_events']}")
        print(f"  Merge={res['merge_count']} Split={res['split_count']}")
        print(f"  elapsed={res['elapsed']:.0f}s")
        print("  SANITY OK")
        return

    if args.aggregate:
        aggregate()
        return

    seeds = [args.seed] if args.seed else COG_SEEDS_SMALL
    for seed in seeds:
        rf = OUTPUT_DIR / f"seed_{seed}.json"
        if rf.exists():
            print(f"  seed={seed}: skip (exists)")
            continue

        print(f"  seed={seed}...", flush=True)
        result, wl, cl, sw, ml, sl = run_cognition(
            seed, args.N, args.plb, args.rate,
            args.quiet_steps, args.n_concepts,
            args.diffusion_prob, args.boundary_boost)

        with open(rf, "w") as f:
            json.dump(result, f, indent=2)
        if cl:
            with open(OUTPUT_DIR / f"seed_{seed}_concept.csv", "w",
                       newline="") as f:
                w = csv.DictWriter(f, fieldnames=cl[0].keys())
                w.writeheader()
                w.writerows(cl)
        if ml:
            with open(OUTPUT_DIR / f"seed_{seed}_merge.json", "w") as f:
                json.dump(ml, f, indent=2)
        if sl:
            with open(OUTPUT_DIR / f"seed_{seed}_split.json", "w") as f:
                json.dump(sl, f, indent=2)
        if sw:
            with open(OUTPUT_DIR / f"seed_{seed}_switches.json", "w") as f:
                json.dump(sw, f, indent=2)

        print(f"    k*={result['global_dominant_k']} "
              f"div={result['divergence_ratio']:.2f} "
              f"merge={result['merge_count']} split={result['split_count']} "
              f"diff_ev={result['total_diffusion_events']} "
              f"({result['elapsed']:.0f}s)")


if __name__ == "__main__":
    main()
