#!/usr/bin/env python3
"""
ESDE Cognition v3.0 — Semantic Injection
==========================================
Phase : Cognition (v3.0)
Role  : Claude (Implementation)
Arch  : Gemini | Audit: GPT

PURPOSE
-------
Inject structured semantic embeddings (concept clusters) into the ESDE
topology via phase coherence + spatial localization. Observe whether
they form stable, persistent concept islands, how they interact at
boundaries, and whether the established observer ecology survives.

SEMANTIC INJECTION MECHANISM
-----------------------------
  1. Spatial assignment: nodes divided into concept zones + neutral buffer
     For 2 concepts on sqrt(N) x sqrt(N) grid:
       Concept A : left third of columns
       Neutral   : middle third (buffer)
       Concept B : right third
  2. Phase initialization: concept nodes get coherent theta values
       Concept A : theta ~ pi/4  +/- 0.3
       Concept B : theta ~ 3pi/4 +/- 0.3
       Neutral   : random (standard)
  3. NO ongoing bias — purely initial conditions, then hands-off.
     The question: can physics alone sustain semantic structure?

CONSTRAINTS
-----------
  - Core physics, chemistry, thermodynamics: UNCHANGED (from v19g_canon)
  - Ecology observations: ALL preserved (global/local k*, divergence, regime)
  - No ontology expansion. No external semantic hierarchies.

CONCEPT OBSERVABLES (new)
--------------------------
  - concept_island_count:       islands dominated (>50%) by one concept
  - concept_island_persistence: fraction of windows with >= 1 concept island
  - concept_boundary_friction:  active links between different concept zones
  - concept_entropy:            distribution entropy of concepts among C-nodes
  - observer_concept_mapping:   which 2x2 observer region attends which concept

USAGE
-----
  cd ~/esde/ESDE-Research/cognition/semantic_injection

  # Sanity
  python cognition_v30.py --sanity

  # Single run
  python cognition_v30.py --seed 42

  # Full sweep (10 seeds, parallel on Ryzen)
  parallel -j 20 python cognition_v30.py --seed {1} \
    ::: 42 123 456 789 2024 7 314 999 55 1337

  # Aggregate
  python cognition_v30.py --aggregate
"""

import numpy as np
import sys; from pathlib import Path as _P  # noqa
sys.path.insert(0, str(_P(__file__).resolve().parent.parent.parent / "ecology" / "engine"))

# engine_accel: monkey-patch hot paths (MUST be before any engine use)
import engine_accel
from genesis_state import GenesisState as _GS
assert getattr(_GS.link_strength_sum, "__name__", "") == "_fast_link_strength_sum", \
    "FATAL: engine_accel failed to patch link_strength_sum. Run will be 2-3x slower."
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
# COGNITION v3.0 CONSTANTS
# ================================================================
COG_N           = 5000
COG_PLB         = 0.007
COG_RATE        = 0.002
COG_SEEDS       = ALL_SEEDS  # 10 canonical seeds
N_CONCEPTS_DEF  = 2
PHASE_SPREAD    = 0.3        # +/- radians around concept center
CONCEPT_NAMES   = {0: "A", 1: "B", 2: "C"}

# Observer partition (inherited from ecology)
GRID_ROWS = 2
GRID_COLS = 2
N_REGIONS = GRID_ROWS * GRID_COLS
MIN_C_NODES_FOR_VALID = 5

OUTPUT_DIR = Path("outputs")


# ================================================================
# CONCEPT CLUSTER ASSIGNMENT
# ================================================================
def assign_concepts(N, n_concepts=2):
    """
    Map nodes to concept zones based on spatial grid position.
    Layout (2 concepts): [A][buffer][B] in column space.
    Layout (3 concepts): [A][buf][B][buf][C] in column space.
    Returns: dict {node_id: concept_id} where -1 = neutral.
    """
    side = int(math.ceil(math.sqrt(N)))
    concept_map = {}
    n_zones = 2 * n_concepts - 1  # concept + buffer alternating
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
    """
    Set phase coherence for concept nodes. Neutral nodes keep random theta.
    Phase centers are evenly spaced in [0, pi] to maximize separation.
    """
    centers = {c: (c + 0.5) * np.pi / n_concepts for c in range(n_concepts)}
    for node_id, cid in concept_map.items():
        if cid >= 0 and node_id < state.n_nodes:
            center = centers[cid]
            state.theta[node_id] = (center
                + state.rng.uniform(-PHASE_SPREAD, PHASE_SPREAD)) % (2 * np.pi)


def concept_zone_summary(concept_map, N):
    """Print concept zone sizes."""
    counts = Counter(concept_map.values())
    parts = []
    for c in sorted(counts):
        label = CONCEPT_NAMES.get(c, "neutral") if c >= 0 else "neutral"
        parts.append(f"{label}={counts[c]}")
    return ", ".join(parts)


# ================================================================
# SPATIAL PARTITION (2x2, same as ecology)
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


# ================================================================
# LOCAL k-SELECTOR (per region, same as ecology)
# ================================================================
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
# CONCEPT WINDOW METRICS
# ================================================================
def compute_concept_window(state, concept_map, n_concepts,
                           region_map, islands_m):
    """
    Compute concept-specific observables for one window.
    islands_m: mid-threshold (0.20) islands from standard detection.
    """
    # --- 1. Concept island classification ---
    concept_island_count = {c: 0 for c in range(n_concepts)}
    concept_nodes_in_islands = {c: 0 for c in range(n_concepts)}

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

    # --- 2. Boundary friction ---
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

    # --- 3. Concept entropy among C-nodes ---
    all_c = [n for n in state.alive_n if int(state.Z[n]) == 3]
    cdist = Counter(concept_map.get(n, -1) for n in all_c)
    total = sum(cdist.values())
    entropy = 0.0
    if total > 0:
        for v in cdist.values():
            p = v / total
            if p > 0:
                entropy -= p * np.log2(p)

    # --- 4. Observer-to-concept mapping ---
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
        # require >30% dominance to assign
        obs_concept[r] = best_c if best_n > len(rc_nodes) * 0.3 else -1

    # --- 5. Concept C-node counts ---
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
        "observer_concept": obs_concept,
        "concept_c_counts": concept_c_counts,
        "total_c_nodes": len(all_c),
    }


# ================================================================
# MAIN SIMULATION
# ================================================================
def run_cognition(seed, N=COG_N, plb=COG_PLB, rate=COG_RATE,
                  quiet_steps=QUIET_STEPS, n_concepts=N_CONCEPTS_DEF):
    """
    Run simulation with concept injection + ecology observations.
    Physics loop: identical to run_canonical / run_ecology.
    Additions: concept phase injection at init, concept tracking per window.
    """
    p = dict(BASE_PARAMS)
    p["p_link_birth"] = plb

    # --- State initialization ---
    state = GenesisState(N, C_MAX, seed)
    init_fert(state, TOPO_VAR, seed)

    # --- Concept injection (BEFORE physics starts) ---
    concept_map = assign_concepts(N, n_concepts)
    inject_concept_phases(state, concept_map, n_concepts)
    region_map = assign_regions(N)

    # --- Engine setup (identical to ecology) ---
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

    # --- Injection phase (identical to canonical) ---
    for step in range(INJECTION_STEPS):
        if step % INJECT_INTERVAL == 0:
            tgts = physics.inject(state)
            chem.seed_on_injection(state, tgts or [])
        physics.step_pre_chemistry(state)
        chem.step(state)
        physics.step_resonance(state)
        grower.step(state)
        physics.step_decay_exclusion(state)

    # --- Quiet phase: canonical + region + concept observation ---
    # Global observer
    k_star_seq = []
    switch_events = []
    margin_seq = []
    prev_nodes_global = None
    current_k_global = None
    island_summaries = []

    # Regional observers
    prev_nodes_region = {r: None for r in range(N_REGIONS)}
    current_k_region = {r: None for r in range(N_REGIONS)}
    region_k_seqs = {r: [] for r in range(N_REGIONS)}

    # Concept persistence tracking
    concept_streaks = {c: 0 for c in range(n_concepts)}
    concept_max_streaks = {c: 0 for c in range(n_concepts)}
    concept_windows_with_island = {c: 0 for c in range(n_concepts)}

    # Logs
    window_logs = []
    concept_window_logs = []

    # ETA tracking
    _eta_t0 = time.time()
    _eta_total_windows = quiet_steps // WINDOW

    for step in range(quiet_steps):
        # === PHYSICS (identical to run_canonical) ===
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

        # Seeding (identical to canonical)
        al = list(state.alive_n)
        na = len(al)
        if na > 0:
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
            mk = state.rng.random(na) < BASE_PARAMS["background_injection_prob"]
            for idx in range(na):
                if mk[idx]:
                    t = int(state.rng.choice(aa, p=pd))
                    state.E[t] = min(1.0, state.E[t] + 0.3)
                    if state.Z[t] == 0 and state.rng.random() < 0.5:
                        state.Z[t] = 1 if state.rng.random() < 0.5 else 2

        # ============================================================
        # WINDOW OBSERVATION
        # ============================================================
        if (step + 1) % WINDOW == 0:
            win_idx = (step + 1) // WINDOW

            # ETA display
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

            # --- Island detection (canonical) ---
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

            # --- C-node context (canonical) ---
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

            # --- GLOBAL observer (canonical) ---
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

            # Island summary
            none_count = sum(1 for nd in all_nodes
                            if nd["r_bits"] == "000") if all_nodes else 0
            island_summaries.append({
                "n_C": n_C,
                "n_islands_mid": len(isl_m),
                "none_ratio": round(none_count / max(n_C, 1), 4),
            })

            # --- REGIONAL observers (ecology) ---
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

            # --- CONCEPT metrics (new in v3.0) ---
            cmet = compute_concept_window(
                state, concept_map, n_concepts, region_map, isl_m)

            # Concept persistence tracking
            for c in range(n_concepts):
                if cmet["concept_island_count"][c] > 0:
                    concept_streaks[c] += 1
                    concept_windows_with_island[c] += 1
                    concept_max_streaks[c] = max(
                        concept_max_streaks[c], concept_streaks[c])
                else:
                    concept_streaks[c] = 0

            # Concept window log
            clog = {"seed": seed, "window": win_idx}
            for c in range(n_concepts):
                cn = CONCEPT_NAMES[c]
                clog[f"{cn}_islands"] = cmet["concept_island_count"][c]
                clog[f"{cn}_nodes_in_isl"] = cmet["concept_nodes_in_islands"][c]
                clog[f"{cn}_c_nodes"] = cmet["concept_c_counts"].get(c, 0)
            clog["boundary_links"] = cmet["boundary_links"]
            clog["boundary_weight"] = cmet["boundary_weight"]
            clog["concept_entropy"] = cmet["concept_entropy"]
            clog["total_c_nodes"] = cmet["total_c_nodes"]
            for r in range(N_REGIONS):
                oc = cmet["observer_concept"][r]
                clog[f"r{r}_concept"] = CONCEPT_NAMES.get(oc, "neutral")
            clog["global_k"] = current_k_global or 0
            clog["div_flag"] = div_flag
            concept_window_logs.append(clog)

            window_logs.append(wlog)

    # ============================================================
    # AGGREGATE RESULTS
    # ============================================================
    elapsed = time.time() - t0
    n_windows = len(k_star_seq)

    # Global observer summary
    kc = Counter(k_star_seq)
    dom_k, dom_count = kc.most_common(1)[0] if kc else (0, 0)
    dom_frac = dom_count / max(n_windows, 1)
    sw_count = sum(1 for i in range(1, len(k_star_seq))
                   if k_star_seq[i] != k_star_seq[i-1])
    sw_per_100 = round(sw_count / max(n_windows - 1, 1) * 100, 1)

    # Divergence (ecology v2.2+)
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

    # Concept summary
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

    # Boundary summary
    mean_bnd_links = round(np.mean(
        [cl["boundary_links"] for cl in concept_window_logs]), 1)
    mean_bnd_weight = round(np.mean(
        [cl["boundary_weight"] for cl in concept_window_logs]), 4)
    mean_entropy = round(np.mean(
        [cl["concept_entropy"] for cl in concept_window_logs]), 4)

    # Observer-concept dominant mapping
    obs_concept_dominant = {}
    for r in range(N_REGIONS):
        rc = Counter(cl[f"r{r}_concept"] for cl in concept_window_logs)
        obs_concept_dominant[f"r{r}"] = rc.most_common(1)[0][0] if rc else "neutral"

    result = {
        "N": N, "seed": int(seed), "plb": plb, "rate": rate,
        "quiet_steps": quiet_steps, "n_windows": n_windows,
        "n_concepts": n_concepts,
        "concept_zone_sizes": dict(Counter(concept_map.values())),
        # Ecology: global observer
        "global_dominant_k": dom_k,
        "global_dom_frac": round(dom_frac, 4),
        "global_switches_per_100": sw_per_100,
        "global_mean_n_C": round(np.mean(
            [s["n_C"] for s in island_summaries]), 1) if island_summaries else 0,
        "global_mean_none_ratio": round(np.mean(
            [s["none_ratio"] for s in island_summaries]), 4) if island_summaries else 0,
        # Ecology: divergence
        "divergence_ratio": divergence_ratio,
        "divergence_episode_count": len(episodes),
        "run_regime_label": regime_label,
        # Concept: persistence
        "concept_summary": concept_summary,
        # Concept: boundary
        "mean_boundary_links": mean_bnd_links,
        "mean_boundary_weight": mean_bnd_weight,
        "mean_concept_entropy": mean_entropy,
        # Concept: observer mapping
        "observer_concept_dominant": obs_concept_dominant,
        # Runtime
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

    print(f"\n{'='*80}")
    print(f"  ESDE Cognition v3.0 — Aggregate Summary ({len(results)} seeds)")
    print(f"{'='*80}")

    # Ecology stability check
    print(f"\n  Ecology Stability:")
    gk_dist = Counter(r["global_dominant_k"] for r in results)
    print(f"    Global k* distribution: "
          + ", ".join(f"k={k}:{v}" for k, v in sorted(gk_dist.items())))
    regimes = Counter(r["run_regime_label"] for r in results)
    print(f"    Regime distribution: {dict(regimes)}")
    print(f"    Mean divergence ratio: "
          f"{np.mean([r['divergence_ratio'] for r in results]):.3f}")

    # Concept persistence
    print(f"\n  Concept Persistence:")
    for cn in ["A", "B", "C"]:
        persis = [r["concept_summary"][cn]["persistence_frac"]
                  for r in results if cn in r["concept_summary"]]
        if not persis:
            continue
        streaks = [r["concept_summary"][cn]["max_streak"]
                   for r in results if cn in r["concept_summary"]]
        islands = [r["concept_summary"][cn]["mean_islands"]
                   for r in results if cn in r["concept_summary"]]
        print(f"    {cn}: persist={np.mean(persis):.3f} "
              f"max_streak={np.mean(streaks):.1f} "
              f"mean_islands={np.mean(islands):.2f}")

    # Boundary friction
    print(f"\n  Boundary Friction:")
    print(f"    Mean boundary links: "
          f"{np.mean([r['mean_boundary_links'] for r in results]):.1f}")
    print(f"    Mean boundary weight: "
          f"{np.mean([r['mean_boundary_weight'] for r in results]):.4f}")
    print(f"    Mean concept entropy: "
          f"{np.mean([r['mean_concept_entropy'] for r in results]):.4f}")

    # Observer-concept mapping
    print(f"\n  Observer-Concept Mapping:")
    for r_idx in range(N_REGIONS):
        rkey = f"r{r_idx}"
        mapping = Counter(r["observer_concept_dominant"][rkey] for r in results)
        print(f"    {rkey}: {dict(mapping)}")

    # Write summary CSV
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
        }
        for cn in ["A", "B", "C"]:
            if cn in r["concept_summary"]:
                cs = r["concept_summary"][cn]
                row[f"{cn}_persist"] = cs["persistence_frac"]
                row[f"{cn}_max_streak"] = cs["max_streak"]
                row[f"{cn}_mean_isl"] = cs["mean_islands"]
        for r_idx in range(N_REGIONS):
            row[f"r{r_idx}_concept"] = r["observer_concept_dominant"][f"r{r_idx}"]
        rows.append(row)

    csv_path = OUTPUT_DIR / "cognition_summary.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"\n  Summary CSV: {csv_path}")


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(
        description="ESDE Cognition v3.0 — Semantic Injection")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--N", type=int, default=COG_N)
    parser.add_argument("--plb", type=float, default=COG_PLB)
    parser.add_argument("--rate", type=float, default=COG_RATE)
    parser.add_argument("--quiet-steps", type=int, default=QUIET_STEPS)
    parser.add_argument("--n-concepts", type=int, default=N_CONCEPTS_DEF)
    parser.add_argument("--aggregate", action="store_true")
    parser.add_argument("--sanity", action="store_true")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.sanity:
        print(f"  SANITY: N={args.N} plb={args.plb} rate={args.rate} "
              f"seed=42 quiet=500 concepts={args.n_concepts}")
        cmap = assign_concepts(args.N, args.n_concepts)
        print(f"  Zones: {concept_zone_summary(cmap, args.N)}")
        res, wlogs, clogs, sw = run_cognition(
            42, args.N, args.plb, args.rate,
            quiet_steps=500, n_concepts=args.n_concepts)
        print(f"  global k*={res['global_dominant_k']} "
              f"sw={res['global_switches_per_100']} "
              f"div={res['divergence_ratio']:.2f} "
              f"regime={res['run_regime_label']}")
        for cn in ["A", "B", "C"]:
            if cn in res["concept_summary"]:
                cs = res["concept_summary"][cn]
                print(f"  Concept {cn}: persist={cs['persistence_frac']:.2f} "
                      f"max_streak={cs['max_streak']} "
                      f"mean_islands={cs['mean_islands']:.2f}")
        print(f"  Boundary: links={res['mean_boundary_links']:.1f} "
              f"weight={res['mean_boundary_weight']:.4f}")
        print(f"  Entropy: {res['mean_concept_entropy']:.4f}")
        print(f"  Observer→Concept: {res['observer_concept_dominant']}")
        print(f"  elapsed={res['elapsed']:.0f}s")
        print("  SANITY OK")
        return

    if args.aggregate:
        aggregate()
        return

    # Run mode
    seeds = [args.seed] if args.seed else COG_SEEDS
    for seed in seeds:
        rf = OUTPUT_DIR / f"seed_{seed}.json"
        if rf.exists():
            print(f"  seed={seed}: skip (exists)")
            continue

        print(f"  seed={seed} (N={args.N}, concepts={args.n_concepts})...",
              flush=True)
        result, wlogs, clogs, sw = run_cognition(
            seed, args.N, args.plb, args.rate,
            args.quiet_steps, args.n_concepts)

        with open(rf, "w") as f:
            json.dump(result, f, indent=2)
        if clogs:
            with open(OUTPUT_DIR / f"seed_{seed}_concept.csv", "w",
                       newline="") as f:
                w = csv.DictWriter(f, fieldnames=clogs[0].keys())
                w.writeheader()
                w.writerows(clogs)
        if sw:
            with open(OUTPUT_DIR / f"seed_{seed}_switches.json", "w") as f:
                json.dump(sw, f, indent=2)

        print(f"    global k*={result['global_dominant_k']} "
              f"sw={result['global_switches_per_100']} "
              f"div={result['divergence_ratio']:.2f} "
              f"regime={result['run_regime_label']}")
        for cn in ["A", "B", "C"]:
            if cn in result["concept_summary"]:
                cs = result["concept_summary"][cn]
                print(f"    {cn}: persist={cs['persistence_frac']:.2f} "
                      f"streak={cs['max_streak']} "
                      f"isl={cs['mean_islands']:.2f}")
        print(f"    boundary={result['mean_boundary_links']:.1f} "
              f"entropy={result['mean_concept_entropy']:.4f} "
              f"({result['elapsed']:.0f}s)")


if __name__ == "__main__":
    main()
