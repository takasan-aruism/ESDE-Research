#!/usr/bin/env python3
"""
ESDE Cognition v3.4 — Concept Mediation
=========================================
Phase : Cognition (v3.4)
Role  : Claude (Implementation)
Arch  : Gemini | Audit: GPT

PURPOSE
-------
v3.3 showed A↔B bridges form but die in 1 window (bridge_max_life=1,
persist_bridges=0). Phase mismatch prevents direct stabilization.

v3.4 introduces Concept C as a phase mediator:
  θ_C = (θ_A + θ_B) / 2

C is injected into the boundary zone (previously neutral buffer).
The question: can A↔C↔B multi-step bridges form and persist?

CHANGES FROM v3.3
------------------
  1. Neutral buffer zone → Concept C zone
  2. tripartite_loop detection: k=3 islands with nodes from A, B, and C
  3. mediation_ratio: A→C→B diffusion paths vs direct A→B
  4. All v3.2/v3.3 mechanisms preserved (diffusion, boost, bridges)

USAGE
-----
  python cognition_v34.py --sanity
  parallel -j 20 python cognition_v34.py --seed {1} ::: $(seq 1 20)
  python cognition_v34.py --aggregate
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
# CONSTANTS
# ================================================================
COG_N           = 5000
COG_PLB         = 0.007
COG_RATE        = 0.002
COG_SEEDS_SMALL = list(range(1, 21))
N_CONCEPTS      = 3   # A, B, C (mediator)
PHASE_SPREAD    = 0.3
CONCEPT_NAMES   = {0: "A", 1: "B", 2: "C"}

DIFFUSION_PROB      = 0.005
DIFFUSION_STRENGTH  = 0.3
BOUNDARY_LINK_BOOST = 1.5

MERGE_WEIGHT_THR    = 5.0
MERGE_PHASE_THR     = 0.5
SPLIT_MIN_COMP_SIZE = 3
BRIDGE_S_THR        = 0.15

GRID_ROWS = 2
GRID_COLS = 2
N_REGIONS = GRID_ROWS * GRID_COLS
MIN_C_NODES_FOR_VALID = 5

OUTPUT_DIR = Path("outputs_v34")


# ================================================================
# CONCEPT ASSIGNMENT (v3.4: C replaces neutral buffer)
# ================================================================
def assign_concepts(N):
    """
    Layout on sqrt(N) columns: [A zone][C zone][B zone]
    Each zone ~1/3 of columns. No neutral buffer.
    """
    side = int(math.ceil(math.sqrt(N)))
    concept_map = {}
    third = side / 3.0
    for i in range(N):
        col = i % side
        if col < third:
            concept_map[i] = 0   # A
        elif col < 2 * third:
            concept_map[i] = 2   # C (mediator)
        else:
            concept_map[i] = 1   # B
    return concept_map


def inject_concept_phases(state, concept_map):
    """
    Phase centers: A=π/4, B=3π/4, C=(A+B)/2=π/2.
    C is exactly intermediate → cos(θ_A - θ_C) and cos(θ_B - θ_C)
    are both moderate, enabling bridging.
    """
    centers = {
        0: np.pi / 4,       # A
        1: 3 * np.pi / 4,   # B
        2: np.pi / 2,       # C (midpoint)
    }
    for node_id, cid in concept_map.items():
        if node_id < state.n_nodes:
            center = centers[cid]
            state.theta[node_id] = (center
                + state.rng.uniform(-PHASE_SPREAD, PHASE_SPREAD)) % (2 * np.pi)
    return centers


def concept_zone_summary(concept_map):
    counts = Counter(concept_map.values())
    return ", ".join(
        f"{CONCEPT_NAMES.get(c, '?')}={counts[c]}" for c in sorted(counts))


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


def find_concept_boundary_nodes(state, concept_map):
    boundary = set()
    for n in state.alive_n:
        cn = concept_map.get(n, -1)
        for nb in state.neighbors(n):
            if nb in state.alive_n:
                if concept_map.get(nb, -1) != cn:
                    boundary.add(n)
                    break
    return boundary


# ================================================================
# DIFFUSION (v3.2/v3.3, with flow + mediation tracking)
# ================================================================
def apply_semantic_diffusion(state, concept_map, concept_centers,
                             boundary_nodes, rng):
    events = 0
    flow = Counter()
    for n in boundary_nodes:
        if rng.random() > DIFFUSION_PROB:
            continue
        cn = concept_map.get(n, -1)
        diff_nbs = []
        for nb in state.neighbors(n):
            if nb in state.alive_n:
                cnb = concept_map.get(nb, -1)
                if cnb != cn:
                    diff_nbs.append(nb)
        if not diff_nbs:
            continue
        target_nb = diff_nbs[rng.randint(len(diff_nbs))]
        target_c = concept_map[target_nb]
        target_center = concept_centers[target_c]
        current_theta = state.theta[n]
        diff = (target_center - current_theta + np.pi) % (2 * np.pi) - np.pi
        state.theta[n] = (current_theta + DIFFUSION_STRENGTH * diff) % (2 * np.pi)
        events += 1
        flow[(cn, target_c)] += 1
    return events, flow


def boosted_seeding(state, concept_map, boundary_nodes, g_scores, gz, rng):
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
        p = base_prob
        if node in boundary_nodes:
            p = min(base_prob * BOUNDARY_LINK_BOOST, 1.0)
        if rng.random() < p:
            t = int(rng.choice(aa, p=pd))
            state.E[t] = min(1.0, state.E[t] + 0.3)
            if state.Z[t] == 0 and rng.random() < 0.5:
                state.Z[t] = 1 if rng.random() < 0.5 else 2


# ================================================================
# CONCEPT WINDOW METRICS (extended for 3 concepts)
# ================================================================
def compute_concept_window(state, concept_map, region_map, islands_m):
    n_concepts = N_CONCEPTS
    concept_island_count = {c: 0 for c in range(n_concepts)}
    concept_nodes_in_islands = {c: 0 for c in range(n_concepts)}
    labeled_islands = []

    for isl in islands_m:
        c_in_isl = [n for n in isl
                     if n in state.alive_n and int(state.Z[n]) == 3]
        if len(c_in_isl) < 3:
            continue
        cc = Counter(concept_map.get(n, -1) for n in c_in_isl)
        total = sum(cc.values())
        if total == 0:
            continue
        for c in range(n_concepts):
            if cc.get(c, 0) / total > 0.5:
                concept_island_count[c] += 1
                concept_nodes_in_islands[c] += cc[c]
                labeled_islands.append((c, frozenset(n for n in isl
                                                      if n in state.alive_n)))
                break

    # v3.4: tripartite loops — islands containing nodes from all 3 concepts
    tripartite_count = 0
    for isl in islands_m:
        c_in_isl = [n for n in isl
                     if n in state.alive_n and int(state.Z[n]) == 3]
        if len(c_in_isl) < 3:
            continue
        cc = Counter(concept_map.get(n, -1) for n in c_in_isl)
        if all(cc.get(c, 0) > 0 for c in range(n_concepts)):
            tripartite_count += 1

    # Boundary friction (all cross-concept pairs)
    boundary_links = 0
    boundary_weight = 0.0
    pair_links = Counter()
    for (i, j) in state.alive_l:
        ci = concept_map.get(i, -1)
        cj = concept_map.get(j, -1)
        if ci != cj:
            boundary_links += 1
            boundary_weight += state.S[(i, j)]
            pair = (min(ci, cj), max(ci, cj))
            pair_links[pair] += 1

    # Entropy
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
        best_c = rc.most_common(1)[0][0]
        best_n = rc.most_common(1)[0][1]
        obs_concept[r] = best_c if best_n > len(rc_nodes) * 0.3 else -1

    concept_c_counts = Counter(concept_map.get(n, -1) for n in all_c)

    return {
        "concept_island_count": concept_island_count,
        "concept_nodes_in_islands": concept_nodes_in_islands,
        "boundary_links": boundary_links,
        "boundary_weight": round(boundary_weight, 4),
        "pair_links": dict(pair_links),
        "concept_entropy": round(entropy, 4),
        "region_entropy": region_entropy,
        "observer_concept": obs_concept,
        "concept_c_counts": dict(concept_c_counts),
        "total_c_nodes": len(all_c),
        "labeled_islands": labeled_islands,
        "tripartite_count": tripartite_count,
    }


# ================================================================
# BRIDGE TRACKING (v3.3, unchanged)
# ================================================================
def compute_bridges(state, concept_map, prev_bridges):
    curr = {}
    for (i, j) in state.alive_l:
        if state.S[(i, j)] < BRIDGE_S_THR:
            continue
        ci = concept_map.get(i, -1)
        cj = concept_map.get(j, -1)
        if ci != cj:
            curr[(i, j)] = state.S[(i, j)]

    updated_lifespans = {}
    new_count = 0
    persistent_count = 0
    for k in curr:
        if k in prev_bridges:
            updated_lifespans[k] = prev_bridges[k] + 1
            persistent_count += 1
        else:
            updated_lifespans[k] = 1
            new_count += 1

    total_weight = sum(curr.values())
    lifespans = list(updated_lifespans.values())
    mean_lifespan = np.mean(lifespans) if lifespans else 0

    # v3.4: per-pair bridge counts
    pair_bridges = Counter()
    for (i, j) in curr:
        ci = concept_map.get(i, -1)
        cj = concept_map.get(j, -1)
        pair = (min(ci, cj), max(ci, cj))
        pair_bridges[pair] += 1

    return updated_lifespans, {
        "n_bridges": len(curr),
        "new_bridges": new_count,
        "persistent_bridges": persistent_count,
        "total_weight": round(total_weight, 4),
        "mean_lifespan": round(mean_lifespan, 2),
        "max_lifespan": max(lifespans) if lifespans else 0,
        "pair_bridges": dict(pair_bridges),
    }


# ================================================================
# MERGE / SPLIT DETECTION (unchanged)
# ================================================================
def detect_merge_split(state, concept_map,
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
                    "n_fragments": len(significant),
                    "fragment_sizes": sorted([len(c) for c in significant],
                                            reverse=True),
                })
    return merges, splits


# ================================================================
# MAIN SIMULATION
# ================================================================
def run_cognition(seed, N=COG_N, plb=COG_PLB, rate=COG_RATE,
                  quiet_steps=QUIET_STEPS):
    p = dict(BASE_PARAMS)
    p["p_link_birth"] = plb

    state = GenesisState(N, C_MAX, seed)
    init_fert(state, TOPO_VAR, seed)

    concept_map = assign_concepts(N)
    concept_centers = inject_concept_phases(state, concept_map)
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
    total_flow = Counter()

    # Injection
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

    concept_streaks = {c: 0 for c in range(N_CONCEPTS)}
    concept_max_streaks = {c: 0 for c in range(N_CONCEPTS)}
    concept_windows_with_island = {c: 0 for c in range(N_CONCEPTS)}

    prev_labeled_islands = []
    total_merge_events = 0
    total_split_events = 0
    prev_bridges = {}
    total_tripartite = 0

    window_logs = []
    concept_window_logs = []

    _eta_t0 = time.time()
    _eta_total_windows = quiet_steps // WINDOW

    for step in range(quiet_steps):
        # === PHYSICS ===
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

        # === DIFFUSION ===
        boundary_nodes = find_concept_boundary_nodes(state, concept_map)
        n_diff, step_flow = apply_semantic_diffusion(
            state, concept_map, concept_centers, boundary_nodes, state.rng)
        total_diffusion_events += n_diff
        total_flow += step_flow

        # === SEEDING ===
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
                          f"ETA={_eta_remaining:.0f}s",
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

            # Global observer
            if all_nodes:
                j_scores_g = {}
                for k in K_LEVELS:
                    j, h, dr, tc = compute_J(all_nodes, prev_nodes_global, k)
                    j_scores_g[k] = j
                new_k_g = select_k_star(j_scores_g, current_k_global)
                if current_k_global is not None and new_k_g != current_k_global:
                    switch_events.append(SwitchEvent(
                        seed=seed, N=N, window=win_idx, step=(step + 1),
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

            island_summaries.append({"n_C": n_C, "n_islands_mid": len(isl_m)})

            # Regional observers
            wlog = {"seed": seed, "window": win_idx,
                    "global_k": current_k_global or 0, "global_n_C": n_C}
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
                if (current_k_region[r] or 0) != (current_k_global or 0):
                    div_flag = 1
            wlog["divergence_flag"] = div_flag

            # Concept metrics
            cmet = compute_concept_window(state, concept_map, region_map, isl_m)
            total_tripartite += cmet["tripartite_count"]

            # Merge/Split
            curr_labeled = cmet["labeled_islands"]
            m_ev, s_ev = detect_merge_split(
                state, concept_map, prev_labeled_islands, curr_labeled)
            total_merge_events += len(m_ev)
            total_split_events += len(s_ev)
            prev_labeled_islands = curr_labeled

            # Bridges
            prev_bridges, bridge_stats = compute_bridges(
                state, concept_map, prev_bridges)

            # Persistence
            for c in range(N_CONCEPTS):
                if cmet["concept_island_count"][c] > 0:
                    concept_streaks[c] += 1
                    concept_windows_with_island[c] += 1
                    concept_max_streaks[c] = max(
                        concept_max_streaks[c], concept_streaks[c])
                else:
                    concept_streaks[c] = 0

            # Window log
            clog = {"seed": seed, "window": win_idx}
            for c in range(N_CONCEPTS):
                cn = CONCEPT_NAMES[c]
                clog[f"{cn}_islands"] = cmet["concept_island_count"][c]
                clog[f"{cn}_nodes_in_isl"] = cmet["concept_nodes_in_islands"][c]
            clog["tripartite"] = cmet["tripartite_count"]
            clog["boundary_links"] = cmet["boundary_links"]
            clog["boundary_weight"] = cmet["boundary_weight"]
            clog["concept_entropy"] = cmet["concept_entropy"]
            clog["n_bridges"] = bridge_stats["n_bridges"]
            clog["persistent_bridges"] = bridge_stats["persistent_bridges"]
            clog["bridge_mean_life"] = bridge_stats["mean_lifespan"]
            clog["bridge_max_life"] = bridge_stats["max_lifespan"]
            # Per-pair bridges (A-C, A-B, B-C)
            pb = bridge_stats["pair_bridges"]
            clog["bridges_AC"] = pb.get((0, 2), 0)
            clog["bridges_AB"] = pb.get((0, 1), 0)
            clog["bridges_BC"] = pb.get((1, 2), 0)
            clog["global_k"] = current_k_global or 0
            clog["div_flag"] = div_flag
            clog["merge"] = len(m_ev)
            clog["split"] = len(s_ev)
            for r in range(N_REGIONS):
                oc = cmet["observer_concept"][r]
                clog[f"r{r}_concept"] = CONCEPT_NAMES.get(oc, "?")
            concept_window_logs.append(clog)
            window_logs.append(wlog)

    # ============================================================
    # RESULT ASSEMBLY
    # ============================================================
    elapsed = time.time() - t0
    n_windows = len(k_star_seq)

    kc = Counter(k_star_seq)
    dom_k = kc.most_common(1)[0][0] if kc else 0
    sw_count = sum(1 for i in range(1, len(k_star_seq))
                   if k_star_seq[i] != k_star_seq[i-1])
    sw_per_100 = round(sw_count / max(n_windows - 1, 1) * 100, 1)

    div_flags = [w.get("divergence_flag", 0) for w in window_logs]
    divergence_ratio = round(sum(div_flags) / max(len(div_flags), 1), 4)

    concept_summary = {}
    for c in range(N_CONCEPTS):
        cn = CONCEPT_NAMES[c]
        concept_summary[cn] = {
            "persistence_frac": round(
                concept_windows_with_island[c] / max(n_windows, 1), 4),
            "max_streak": concept_max_streaks[c],
            "mean_islands": round(np.mean(
                [cl[f"{cn}_islands"] for cl in concept_window_logs]), 2),
        }

    obs_concept_dominant = {}
    for r in range(N_REGIONS):
        rc = Counter(cl[f"r{r}_concept"] for cl in concept_window_logs)
        obs_concept_dominant[f"r{r}"] = rc.most_common(1)[0][0] if rc else "?"

    # Flow
    flow_ac = total_flow.get((0, 2), 0) + total_flow.get((2, 0), 0)
    flow_bc = total_flow.get((1, 2), 0) + total_flow.get((2, 1), 0)
    flow_ab = total_flow.get((0, 1), 0) + total_flow.get((1, 0), 0)

    # v3.4: mediation ratio — diffusion via C vs direct A↔B
    mediation_paths = total_flow.get((0, 2), 0) + total_flow.get((2, 1), 0) \
                    + total_flow.get((1, 2), 0) + total_flow.get((2, 0), 0)
    direct_paths = total_flow.get((0, 1), 0) + total_flow.get((1, 0), 0)
    mediation_ratio = round(mediation_paths / max(direct_paths, 1), 4)

    # Bridge summary
    bridge_n = [cl["n_bridges"] for cl in concept_window_logs]
    bridge_persist = [cl["persistent_bridges"] for cl in concept_window_logs]
    bridge_life = [cl["bridge_mean_life"] for cl in concept_window_logs]
    bridge_max = [cl["bridge_max_life"] for cl in concept_window_logs]
    bridges_ac = [cl["bridges_AC"] for cl in concept_window_logs]
    bridges_bc = [cl["bridges_BC"] for cl in concept_window_logs]
    bridges_ab = [cl["bridges_AB"] for cl in concept_window_logs]

    result = {
        "N": N, "seed": int(seed), "plb": plb, "rate": rate,
        "quiet_steps": quiet_steps, "n_windows": n_windows,
        "n_concepts": N_CONCEPTS,
        # Ecology
        "global_dominant_k": dom_k,
        "global_switches_per_100": sw_per_100,
        "divergence_ratio": divergence_ratio,
        # Concept persistence
        "concept_summary": concept_summary,
        "mean_concept_entropy": round(np.mean(
            [cl["concept_entropy"] for cl in concept_window_logs]), 4),
        "observer_concept_dominant": obs_concept_dominant,
        # Merge/Split
        "merge_count": total_merge_events,
        "split_count": total_split_events,
        # v3.4: tripartite
        "total_tripartite": total_tripartite,
        "mean_tripartite": round(np.mean(
            [cl["tripartite"] for cl in concept_window_logs]), 2),
        # Diffusion flow
        "total_diffusion": total_diffusion_events,
        "flow_AC": flow_ac, "flow_BC": flow_bc, "flow_AB": flow_ab,
        "mediation_ratio": mediation_ratio,
        # Bridges
        "mean_n_bridges": round(np.mean(bridge_n), 1),
        "mean_persistent_bridges": round(np.mean(bridge_persist), 1),
        "mean_bridge_lifespan": round(np.mean(bridge_life), 2),
        "max_bridge_lifespan": max(bridge_max) if bridge_max else 0,
        "mean_bridges_AC": round(np.mean(bridges_ac), 1),
        "mean_bridges_BC": round(np.mean(bridges_bc), 1),
        "mean_bridges_AB": round(np.mean(bridges_ab), 1),
        "elapsed": round(elapsed, 1),
    }

    return result, window_logs, concept_window_logs, \
        [asdict(se) for se in switch_events]


# ================================================================
# AGGREGATE
# ================================================================
def aggregate():
    results = []
    for f in sorted(OUTPUT_DIR.glob("seed_*.json")):
        if "_window" in f.name or "_concept" in f.name or "_switch" in f.name:
            continue
        with open(f) as fh:
            results.append(json.load(fh))
    if not results:
        print("  No results found.")
        return

    n = len(results)
    print(f"\n{'='*80}")
    print(f"  ESDE Cognition v3.4 — Aggregate ({n} seeds)")
    print(f"{'='*80}")

    gk = Counter(r["global_dominant_k"] for r in results)
    print(f"\n  Ecology: k*={dict(gk)}")

    print(f"\n  Concept Persistence:")
    for cn in ["A", "B", "C"]:
        p = [r["concept_summary"][cn]["persistence_frac"]
             for r in results if cn in r["concept_summary"]]
        if p:
            print(f"    {cn}: persist={np.mean(p):.3f}±{np.std(p):.3f}")

    print(f"\n  Tripartite Loops (A+B+C in same island):")
    tp = [r["total_tripartite"] for r in results]
    print(f"    Total: mean={np.mean(tp):.1f} max={max(tp)} "
          f"seeds>0: {sum(1 for x in tp if x > 0)}/{n}")

    mc = [r["merge_count"] for r in results]
    sc = [r["split_count"] for r in results]
    print(f"\n  Merge={sum(mc)} Split={sum(sc)}")

    print(f"\n  Bridges (per-pair means):")
    print(f"    A↔C: {np.mean([r['mean_bridges_AC'] for r in results]):.1f}")
    print(f"    B↔C: {np.mean([r['mean_bridges_BC'] for r in results]):.1f}")
    print(f"    A↔B: {np.mean([r['mean_bridges_AB'] for r in results]):.1f}")
    pb = [r["mean_persistent_bridges"] for r in results]
    ml = [r["mean_bridge_lifespan"] for r in results]
    mx = [r["max_bridge_lifespan"] for r in results]
    print(f"    Persistent: {np.mean(pb):.1f}  "
          f"Lifespan: mean={np.mean(ml):.2f}  max={max(mx)}")

    print(f"\n  Diffusion Flow:")
    print(f"    A↔C: {np.mean([r['flow_AC'] for r in results]):.0f}")
    print(f"    B↔C: {np.mean([r['flow_BC'] for r in results]):.0f}")
    print(f"    A↔B: {np.mean([r['flow_AB'] for r in results]):.0f}")
    mr = [r["mediation_ratio"] for r in results]
    print(f"    Mediation ratio (via C / direct): {np.mean(mr):.2f}")

    print(f"\n  Entropy: {np.mean([r['mean_concept_entropy'] for r in results]):.4f}")

    print(f"\n  Observer Mapping:")
    for ri in range(N_REGIONS):
        rk = f"r{ri}"
        mp = Counter(r["observer_concept_dominant"][rk] for r in results)
        print(f"    {rk}: {dict(mp)}")

    # CSV
    rows = []
    for r in results:
        row = {
            "seed": r["seed"], "global_k": r["global_dominant_k"],
            "div_ratio": r["divergence_ratio"],
            "entropy": r["mean_concept_entropy"],
            "merge": r["merge_count"], "split": r["split_count"],
            "tripartite": r["total_tripartite"],
            "diffusion": r["total_diffusion"],
            "flow_AC": r["flow_AC"], "flow_BC": r["flow_BC"],
            "flow_AB": r["flow_AB"],
            "mediation_ratio": r["mediation_ratio"],
            "bridges": r["mean_n_bridges"],
            "persist_bridges": r["mean_persistent_bridges"],
            "bridge_life": r["mean_bridge_lifespan"],
            "bridge_max_life": r["max_bridge_lifespan"],
            "bridges_AC": r["mean_bridges_AC"],
            "bridges_BC": r["mean_bridges_BC"],
            "bridges_AB": r["mean_bridges_AB"],
        }
        for cn in ["A", "B", "C"]:
            if cn in r["concept_summary"]:
                row[f"{cn}_persist"] = r["concept_summary"][cn]["persistence_frac"]
        for ri in range(N_REGIONS):
            row[f"r{ri}_concept"] = r["observer_concept_dominant"][f"r{ri}"]
        rows.append(row)

    csv_path = OUTPUT_DIR / "cognition_v34_summary.csv"
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
        description="ESDE Cognition v3.4 — Concept Mediation")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--N", type=int, default=COG_N)
    parser.add_argument("--plb", type=float, default=COG_PLB)
    parser.add_argument("--rate", type=float, default=COG_RATE)
    parser.add_argument("--quiet-steps", type=int, default=QUIET_STEPS)
    parser.add_argument("--aggregate", action="store_true")
    parser.add_argument("--sanity", action="store_true")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.sanity:
        print(f"  SANITY: N={args.N} rate={args.rate} seed=42 quiet=500")
        cmap = assign_concepts(args.N)
        print(f"  Zones: {concept_zone_summary(cmap)}")
        res, wl, cl, sw = run_cognition(42, args.N, args.plb, args.rate, 500)
        print(f"  k*={res['global_dominant_k']} div={res['divergence_ratio']:.2f}")
        for cn in ["A", "B", "C"]:
            cs = res["concept_summary"][cn]
            print(f"  {cn}: persist={cs['persistence_frac']:.2f} "
                  f"isl={cs['mean_islands']:.2f}")
        print(f"  Tripartite: {res['total_tripartite']}")
        print(f"  Bridges: n={res['mean_n_bridges']:.1f} "
              f"persist={res['mean_persistent_bridges']:.1f} "
              f"life={res['mean_bridge_lifespan']:.2f} "
              f"max={res['max_bridge_lifespan']}")
        print(f"  Bridges AC={res['mean_bridges_AC']:.1f} "
              f"BC={res['mean_bridges_BC']:.1f} "
              f"AB={res['mean_bridges_AB']:.1f}")
        print(f"  Flow: AC={res['flow_AC']} BC={res['flow_BC']} "
              f"AB={res['flow_AB']} mediation={res['mediation_ratio']:.2f}")
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
            print(f"  seed={seed}: skip")
            continue
        print(f"  seed={seed}...", flush=True)
        result, wl, cl, sw = run_cognition(
            seed, args.N, args.plb, args.rate, args.quiet_steps)
        with open(rf, "w") as f:
            json.dump(result, f, indent=2)
        if cl:
            with open(OUTPUT_DIR / f"seed_{seed}_concept.csv", "w",
                       newline="") as f:
                w = csv.DictWriter(f, fieldnames=cl[0].keys())
                w.writeheader()
                w.writerows(cl)
        if sw:
            with open(OUTPUT_DIR / f"seed_{seed}_switches.json", "w") as f:
                json.dump(sw, f, indent=2)
        print(f"    k*={result['global_dominant_k']} "
              f"tri={result['total_tripartite']} "
              f"bridges_AC={result['mean_bridges_AC']:.0f} "
              f"bridges_BC={result['mean_bridges_BC']:.0f} "
              f"persist={result['mean_persistent_bridges']:.0f} "
              f"max_life={result['max_bridge_lifespan']} "
              f"mediation={result['mediation_ratio']:.2f} "
              f"({result['elapsed']:.0f}s)")


if __name__ == "__main__":
    main()
