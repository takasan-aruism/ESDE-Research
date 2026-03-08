#!/usr/bin/env python3
"""
ESDE Ecology — Region-wise Observer
==========================================
Phase : Ecology
Role  : Claude (Implementation)
Arch  : Gemini | Audit: GPT

PURPOSE
-------
Observe whether the global observer can be decomposed into multiple local
observer regions, measure inter-region active-link structure over time,
and track temporal dynamics (persistence, coexistence, divergence).

CONSTRAINTS
-----------
- Core physics, chemistry, thermodynamics: UNCHANGED (imported from v19g_canon)
- No external ontology. All concepts are ESDE-native.
- Spatial partition: 2x2 grid on node index space (4 regions)

BASELINE PARAMETERS
-------------------
  N          = 5000
  plb        = 0.007
  rate       = 0.002
  quiet_steps= 5000
  seeds      = 5
  partition  = 2x2

USAGE
-----
  # Sanity
  python ecology_v21_region.py --sanity

  # Single run
  python ecology_v21_region.py --seed 42

  # All 5 seeds (parallel)
  parallel -j 5 python ecology_v21_region.py --seed {1} \
    ::: 42 123 456 789 2024

  # Aggregate
  python ecology_v21_region.py --aggregate
"""

import numpy as np
import sys; from pathlib import Path as _P  # noqa
sys.path.insert(0, str(_P(__file__).resolve().parent.parent / "engine"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import csv, json, time, argparse, math
from collections import Counter, defaultdict
from pathlib import Path
from dataclasses import dataclass, asdict

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger
from chemistry import ChemistryEngine, ChemistryParams
from realization import RealizationOperator, RealizationParams
from autogrowth import AutoGrowthEngine, AutoGrowthParams
from intrusion import BoundaryIntrusionOperator, find_islands_sets

# Import canonical constants and functions (zero duplication)
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
# ECOLOGY v2.1 CONSTANTS
# ================================================================
ECO_N       = 5000
ECO_PLB     = 0.007
ECO_RATE    = 0.002
ECO_SEEDS   = [42, 123, 456, 789, 2024]
GRID_ROWS   = 2
GRID_COLS   = 2
N_REGIONS   = GRID_ROWS * GRID_COLS   # 4
MIN_C_NODES_FOR_VALID = 5             # below this, region flagged invalid

OUTPUT_DIR  = Path("outputs")


# ================================================================
# SPATIAL PARTITIONING (2x2 on node index grid)
# ================================================================
def assign_regions(N, rows=GRID_ROWS, cols=GRID_COLS):
    """
    Map node IDs 0..N-1 onto a sqrt(N) x sqrt(N) grid,
    then partition into rows x cols regions.
    Returns: dict {node_id: region_id} where region_id in 0..rows*cols-1
    """
    side = int(math.ceil(math.sqrt(N)))
    region_map = {}
    for i in range(N):
        r = i // side            # row in grid
        c = i % side             # col in grid
        rr = min(r * rows // side, rows - 1)
        rc = min(c * cols // side, cols - 1)
        region_map[i] = rr * cols + rc
    return region_map


# ================================================================
# LOCAL k-SELECTOR (per region)
# ================================================================
def compute_local_observer(nodes, prev_nodes, current_k):
    """
    Run the canonical k-selector on a subset of nodes.
    Returns: (new_k, j_scores, h_scores, k_dist_this_window, n_c)
    """
    n_c = len(nodes)
    if n_c < MIN_C_NODES_FOR_VALID:
        return None, {}, {}, {}, n_c

    j_scores = {}
    h_scores = {}
    for k in K_LEVELS:
        j, h, dr, tc = compute_J(nodes, prev_nodes, k)
        j_scores[k] = j
        h_scores[k] = h

    new_k = select_k_star(j_scores, current_k)
    return new_k, j_scores, h_scores, {}, n_c


# ================================================================
# INTER-REGION STRUCTURE
# ================================================================
def compute_inter_region(state, region_map):
    """
    For each pair (r1, r2), count active links and sum weights.
    Returns: dict {(r1, r2): {"edge_count": int, "edge_weight_sum": float}}
    """
    inter = defaultdict(lambda: {"edge_count": 0, "edge_weight_sum": 0.0})
    for (i, j) in state.alive_l:
        ri = region_map.get(i, -1)
        rj = region_map.get(j, -1)
        if ri < 0 or rj < 0:
            continue
        if ri == rj:
            continue  # intra-region, skip
        pair = (min(ri, rj), max(ri, rj))
        inter[pair]["edge_count"] += 1
        inter[pair]["edge_weight_sum"] += state.S[(i, j)]
    # Round weights
    for pair in inter:
        inter[pair]["edge_weight_sum"] = round(inter[pair]["edge_weight_sum"], 4)
    return dict(inter)


# ================================================================
# MAIN SIMULATION (mirrors run_canonical with region hooks)
# ================================================================
def run_ecology(seed, N=ECO_N, plb=ECO_PLB, rate=ECO_RATE,
                quiet_steps=QUIET_STEPS):
    """
    Run simulation with region-wise observer.
    Physics loop is identical to run_canonical.
    Region observation is added at each window.
    """
    p = dict(BASE_PARAMS)
    p["p_link_birth"] = plb

    state = GenesisState(N, C_MAX, seed)
    init_fert(state, TOPO_VAR, seed)
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
    region_map = assign_regions(N)

    # --- Injection (identical to run_canonical) ---
    for step in range(INJECTION_STEPS):
        if step % INJECT_INTERVAL == 0:
            tgts = physics.inject(state)
            chem.seed_on_injection(state, tgts or [])
        physics.step_pre_chemistry(state)
        chem.step(state)
        cd = physics.step_resonance(state)
        grower.step(state)
        physics.step_decay_exclusion(state)

    # --- Quiet phase: canonical + region observation ---
    # Global observer state
    k_star_seq = []
    switch_events = []
    margin_seq = []
    prev_nodes_global = None
    current_k_global = None
    island_summaries = []

    # Per-region observer state
    prev_nodes_region = {r: None for r in range(N_REGIONS)}
    current_k_region = {r: None for r in range(N_REGIONS)}
    region_k_seqs = {r: [] for r in range(N_REGIONS)}

    # Per-window logs
    window_logs = []
    inter_region_logs = []

    for step in range(quiet_steps):
        # Physics step (identical to run_canonical)
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

        # Seeding (identical to run_canonical)
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

            # --- Build C-node context list (canonical) ---
            all_nodes = []
            for i in state.alive_n:
                if int(state.Z[i]) != 3:
                    continue
                s = 1 if i in nm_s else 0
                m = 1 if i in nm_m else 0
                w = 1 if i in nm_w else 0
                ctx = {
                    "node_id": i,
                    "r_bits": f"{s}{m}{w}",
                    "boundary_mid": 1 if i in bnd_m else 0,
                    "intrusion_bin": min(node_intr.get(i, 0), 2),
                }
                all_nodes.append(ctx)

            # --- GLOBAL observer (canonical) ---
            # Strip node_id for canonical compute_J (it only uses r_bits etc.)
            global_nodes = [{k: v for k, v in n.items() if k != "node_id"}
                           for n in all_nodes]

            if global_nodes:
                j_scores_g = {}
                h_scores_g = {}
                for k in K_LEVELS:
                    j, h, dr, tc = compute_J(global_nodes, prev_nodes_global, k)
                    j_scores_g[k] = j
                    h_scores_g[k] = h

                new_k_g = select_k_star(j_scores_g, current_k_global)
                margin = round(j_scores_g.get(4, 0) - j_scores_g.get(3, 0), 4)
                margin_seq.append(margin)

                if current_k_global is not None and new_k_g != current_k_global:
                    switch_events.append(SwitchEvent(
                        seed=seed, N=N, window=len(k_star_seq) + 1,
                        step=INJECTION_STEPS + step + 1,
                        prev_k=current_k_global, new_k=new_k_g,
                        margin=margin, threshold=HYST_THRESHOLD,
                        j3=j_scores_g.get(3, 0), j4=j_scores_g.get(4, 0),
                        h3=h_scores_g.get(3, 0), h4=h_scores_g.get(4, 0),
                    ))

                current_k_global = new_k_g
                k_star_seq.append(new_k_g)

                island_summaries.append({
                    "n_islands_strong": len(isl_s),
                    "n_islands_mid": len(isl_m),
                    "n_C": len(global_nodes),
                    "none_ratio": round(sum(1 for n in global_nodes
                                            if n["r_bits"] == "000")
                                        / max(len(global_nodes), 1), 4),
                })
            else:
                k_star_seq.append(current_k_global or 0)

            prev_nodes_global = global_nodes if global_nodes else None

            # --- REGIONAL observer (Ecology) ---
            # Partition C-nodes by region
            region_nodes = {r: [] for r in range(N_REGIONS)}
            for ctx in all_nodes:
                rid = region_map.get(ctx["node_id"], 0)
                stripped = {k: v for k, v in ctx.items() if k != "node_id"}
                region_nodes[rid].append(stripped)

            region_window_data = {}
            for r in range(N_REGIONS):
                rnodes = region_nodes[r]
                n_c_local = len(rnodes)
                valid = n_c_local >= MIN_C_NODES_FOR_VALID

                if valid:
                    new_k_r, j_sc, h_sc, _, _ = compute_local_observer(
                        rnodes, prev_nodes_region[r], current_k_region[r])
                    if new_k_r is not None:
                        current_k_region[r] = new_k_r
                        region_k_seqs[r].append(new_k_r)
                    else:
                        region_k_seqs[r].append(current_k_region[r] or 0)
                    prev_nodes_region[r] = rnodes
                else:
                    region_k_seqs[r].append(current_k_region[r] or 0)

                none_ct = sum(1 for n in rnodes if n.get("r_bits", "000") == "000")

                region_window_data[r] = {
                    "local_dominant_k": current_k_region[r],
                    "local_node_count": n_c_local,
                    "local_none_ratio": round(none_ct / max(n_c_local, 1), 4),
                    "local_valid_flag": valid,
                }

            # --- Inter-region structure ---
            inter = compute_inter_region(state, region_map)

            # --- Log this window ---
            wlog = {
                "seed": seed, "window": win_idx,
                "step": INJECTION_STEPS + step + 1,
                "global_k": current_k_global,
                "global_n_C": len(global_nodes) if global_nodes else 0,
            }
            for r in range(N_REGIONS):
                rd = region_window_data[r]
                wlog[f"r{r}_k"] = rd["local_dominant_k"]
                wlog[f"r{r}_n_C"] = rd["local_node_count"]
                wlog[f"r{r}_none"] = rd["local_none_ratio"]
                wlog[f"r{r}_valid"] = rd["local_valid_flag"]
                # v2.2: switch flag (1 if local_k changed from previous window)
                rseq = region_k_seqs[r]
                wlog[f"r{r}_switch"] = 1 if len(rseq) >= 2 and rseq[-1] != rseq[-2] else 0

            # v2.2: divergence flag (1 if any local_k != global_k)
            div_flag = 0
            for r in range(N_REGIONS):
                if region_window_data[r]["local_dominant_k"] != current_k_global:
                    div_flag = 1
                    break
            wlog["divergence_flag"] = div_flag

            window_logs.append(wlog)

            # Inter-region log
            irlog = {"seed": seed, "window": win_idx}
            for r1 in range(N_REGIONS):
                for r2 in range(r1 + 1, N_REGIONS):
                    pair = (r1, r2)
                    ir = inter.get(pair, {"edge_count": 0, "edge_weight_sum": 0.0})
                    irlog[f"e_{r1}_{r2}_count"] = ir["edge_count"]
                    irlog[f"e_{r1}_{r2}_weight"] = ir["edge_weight_sum"]
            inter_region_logs.append(irlog)

            node_intr.clear()

        if step % 1000 == 999:
            print(f"      q{step+1}/{quiet_steps}: N={N} L={len(state.alive_l)} "
                  f"gk*={current_k_global} "
                  f"rk=[{','.join(str(current_k_region[r]) for r in range(N_REGIONS))}] "
                  f"({time.time()-t0:.0f}s)", flush=True)

    # ================================================================
    # RESULT ASSEMBLY
    # ================================================================
    elapsed = time.time() - t0
    n_windows = len(k_star_seq)
    kd = Counter(k_star_seq)
    dom_k = kd.most_common(1)[0][0] if kd else 0
    dom_frac = kd.most_common(1)[0][1] / max(n_windows, 1) if kd else 0
    n_switches = len(switch_events)
    sw_per_100 = round(n_switches / max(n_windows / 100, 1), 2)
    mid = n_windows // 2
    first_dom = Counter(k_star_seq[:mid]).most_common(1)[0][0] if mid > 0 else 0
    second_dom = Counter(k_star_seq[mid:]).most_common(1)[0][0] if mid > 0 else 0

    # Regional summaries
    region_summary = {}
    for r in range(N_REGIONS):
        rseq = region_k_seqs[r]
        if rseq:
            rkd = Counter(rseq)
            rmaj = rkd.most_common(1)[0]
            r_sw = sum(1 for i in range(1, len(rseq)) if rseq[i] != rseq[i-1])
            # v2.2: max continuous windows (longest streak of unchanged k)
            max_streak = 1
            cur_streak = 1
            for i in range(1, len(rseq)):
                if rseq[i] == rseq[i-1]:
                    cur_streak += 1
                    max_streak = max(max_streak, cur_streak)
                else:
                    cur_streak = 1
            region_summary[f"r{r}"] = {
                "dominant_k": rmaj[0],
                "agree_frac": round(rmaj[1] / max(len(rseq), 1), 4),
                "switches": r_sw,
                "max_continuous_windows": max_streak,
                "k_dist": {str(k): rkd.get(k, 0) for k in K_LEVELS},
            }
        else:
            region_summary[f"r{r}"] = {
                "dominant_k": 0, "agree_frac": 0, "switches": 0,
                "max_continuous_windows": 0,
                "k_dist": {},
            }

    # v2.2: divergence ratio (fraction of windows where any local != global)
    div_flags = [w.get("divergence_flag", 0) for w in window_logs]
    divergence_ratio = round(sum(div_flags) / max(len(div_flags), 1), 4)

    # v2.3: divergence episode tracking
    # Episode = continuous run of windows where divergence_flag == 1
    episodes = []
    cur_ep_start = None
    for i, df in enumerate(div_flags):
        if df == 1 and cur_ep_start is None:
            cur_ep_start = i
        elif df == 0 and cur_ep_start is not None:
            episodes.append(i - cur_ep_start)
            cur_ep_start = None
    if cur_ep_start is not None:
        episodes.append(len(div_flags) - cur_ep_start)

    divergence_episode_count = len(episodes)
    mean_divergence_duration = round(np.mean(episodes), 2) if episodes else 0
    max_divergence_duration = max(episodes) if episodes else 0

    # v2.3: local transition count per region
    for r in range(N_REGIONS):
        rseq = region_k_seqs[r]
        # Count transitions (already computed as 'switches' in region_summary)
        # Add explicitly named field for v2.3 spec compliance
        region_summary[f"r{r}"]["local_transition_count"] = region_summary[f"r{r}"]["switches"]

    # v2.3: global-local mismatch frequency per region
    for r in range(N_REGIONS):
        mismatch_count = 0
        valid_count = 0
        for w in window_logs:
            if not w.get(f"r{r}_valid", True):
                continue
            valid_count += 1
            if w.get(f"r{r}_k") != w.get("global_k"):
                mismatch_count += 1
        region_summary[f"r{r}"]["mismatch_frequency"] = round(
            mismatch_count / max(valid_count, 1), 4)

    # Mean inter-region edge counts
    inter_means = {}
    for r1 in range(N_REGIONS):
        for r2 in range(r1 + 1, N_REGIONS):
            counts = [log[f"e_{r1}_{r2}_count"] for log in inter_region_logs]
            weights = [log[f"e_{r1}_{r2}_weight"] for log in inter_region_logs]
            inter_means[f"e_{r1}_{r2}"] = {
                "mean_count": round(np.mean(counts), 1) if counts else 0,
                "mean_weight": round(np.mean(weights), 4) if weights else 0,
            }

    result = {
        "N": N, "seed": int(seed), "plb": plb, "rate": rate,
        "quiet_steps": quiet_steps, "n_windows": n_windows,
        "partition": f"{GRID_ROWS}x{GRID_COLS}",
        # Global
        "global_dominant_k": dom_k,
        "global_dom_frac": round(dom_frac, 4),
        "global_switches_per_100": sw_per_100,
        "global_time_stable": first_dom == second_dom,
        "global_mean_margin": round(np.mean(margin_seq), 4) if margin_seq else 0,
        "global_mean_n_C": round(np.mean([s["n_C"] for s in island_summaries]), 1) if island_summaries else 0,
        "global_mean_none_ratio": round(np.mean([s["none_ratio"] for s in island_summaries]), 4) if island_summaries else 0,
        # Regional
        "regions": region_summary,
        # Inter-region
        "inter_region": inter_means,
        # v2.2: temporal
        "divergence_ratio": divergence_ratio,
        # v2.3: interaction
        "divergence_episode_count": divergence_episode_count,
        "mean_divergence_duration": mean_divergence_duration,
        "max_divergence_duration": max_divergence_duration,
        # Runtime
        "elapsed": round(elapsed, 1),
    }

    return result, window_logs, inter_region_logs, [asdict(se) for se in switch_events]


# ================================================================
# AGGREGATE
# ================================================================
def aggregate():
    results = []
    for f in sorted(OUTPUT_DIR.glob("seed_*.json")):
        if "_window" in f.name or "_inter" in f.name or "_switch" in f.name:
            continue
        with open(f) as fh:
            results.append(json.load(fh))

    if not results:
        print("  No results found.")
        return

    print(f"  Loaded {len(results)} runs")
    print(f"\n{'='*80}")
    print(f"  ESDE Ecology — Region Observer Summary")
    print(f"{'='*80}")

    # Summary table
    print(f"\n  {'seed':>5} | {'gk*':>3} {'gsw':>5} {'div%':>5} | ", end="")
    for r in range(N_REGIONS):
        print(f"r{r}k* r{r}str ", end="")
    print(f"| inter_edges")
    print(f"  {'-'*90}")

    for res in results:
        rk_str = " ".join(
            f"{res['regions'][f'r{r}']['dominant_k']:>3} "
            f"{res['regions'][f'r{r}'].get('max_continuous_windows', '-'):>4}"
            for r in range(N_REGIONS))
        ie = res.get("inter_region", {})
        total_ie = sum(v["mean_count"] for v in ie.values())
        div_pct = res.get("divergence_ratio", 0) * 100
        print(f"  {res['seed']:>5} | k={res['global_dominant_k']} "
              f"{res['global_switches_per_100']:>5.1f} {div_pct:>4.0f}% | {rk_str} | {total_ie:.0f}")

    # Comparison: global vs local
    print(f"\n  Global vs Local k* comparison:")
    for res in results:
        gk = res["global_dominant_k"]
        local_ks = [res["regions"][f"r{r}"]["dominant_k"] for r in range(N_REGIONS)]
        match = all(lk == gk for lk in local_ks)
        print(f"    seed={res['seed']:>5}: global=k{gk}  "
              f"local=[{','.join(f'k{lk}' for lk in local_ks)}]  "
              f"{'MATCH' if match else 'DIVERGE'}")

    # v2.2: Temporal persistence summary
    print(f"\n  Region persistence (max continuous windows):")
    for res in results:
        streaks = " ".join(
            f"r{r}={res['regions'][f'r{r}'].get('max_continuous_windows', 0):>2}"
            for r in range(N_REGIONS))
        print(f"    seed={res['seed']:>5}: {streaks}  div_ratio={res.get('divergence_ratio', 0):.2f}")

    # v2.3: Divergence episodes
    print(f"\n  Divergence episodes:")
    for res in results:
        ep = res.get("divergence_episode_count", 0)
        mean_d = res.get("mean_divergence_duration", 0)
        max_d = res.get("max_divergence_duration", 0)
        print(f"    seed={res['seed']:>5}: episodes={ep} mean_dur={mean_d:.1f} max_dur={max_d}")

    # v2.3: Local transitions and mismatch frequency
    print(f"\n  Local transitions & mismatch frequency:")
    for res in results:
        trans = " ".join(
            f"r{r}={res['regions'][f'r{r}'].get('local_transition_count', 0):>2}"
            for r in range(N_REGIONS))
        mismatch = " ".join(
            f"r{r}={res['regions'][f'r{r}'].get('mismatch_frequency', 0):.2f}"
            for r in range(N_REGIONS))
        print(f"    seed={res['seed']:>5}: transitions=[{trans}]  mismatch=[{mismatch}]")

    # Write summary CSV
    rows = []
    for res in results:
        row = {
            "seed": res["seed"],
            "global_k": res["global_dominant_k"],
            "global_sw": res["global_switches_per_100"],
            "global_none": res["global_mean_none_ratio"],
            "global_n_C": res["global_mean_n_C"],
        }
        for r in range(N_REGIONS):
            rd = res["regions"][f"r{r}"]
            row[f"r{r}_k"] = rd["dominant_k"]
            row[f"r{r}_agree"] = rd["agree_frac"]
            row[f"r{r}_sw"] = rd["switches"]
            row[f"r{r}_max_streak"] = rd.get("max_continuous_windows", 0)
            # v2.3
            row[f"r{r}_transitions"] = rd.get("local_transition_count", 0)
            row[f"r{r}_mismatch"] = rd.get("mismatch_frequency", 0)
        # v2.2: divergence
        row["divergence_ratio"] = res.get("divergence_ratio", 0)
        # v2.3: episodes
        row["div_episode_count"] = res.get("divergence_episode_count", 0)
        row["div_mean_duration"] = res.get("mean_divergence_duration", 0)
        row["div_max_duration"] = res.get("max_divergence_duration", 0)
        ie = res.get("inter_region", {})
        for pair_key, vals in ie.items():
            row[f"{pair_key}_count"] = vals["mean_count"]
            row[f"{pair_key}_weight"] = vals["mean_weight"]
        rows.append(row)

    with open(OUTPUT_DIR / "ecology_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"\n  Summary: {OUTPUT_DIR / 'ecology_summary.csv'}")


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(
        description="ESDE Ecology — Region-wise Observer")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--N", type=int, default=ECO_N)
    parser.add_argument("--plb", type=float, default=ECO_PLB)
    parser.add_argument("--rate", type=float, default=ECO_RATE)
    parser.add_argument("--quiet-steps", type=int, default=QUIET_STEPS)
    parser.add_argument("--aggregate", action="store_true")
    parser.add_argument("--sanity", action="store_true")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.sanity:
        print(f"  SANITY: N={args.N} plb={args.plb} rate={args.rate} "
              f"seed=42 quiet=500 partition={GRID_ROWS}x{GRID_COLS}")
        res, wlogs, irlogs, sw = run_ecology(
            42, args.N, args.plb, args.rate, quiet_steps=500)
        print(f"  global k*={res['global_dominant_k']} "
              f"sw={res['global_switches_per_100']}")
        for r in range(N_REGIONS):
            rd = res["regions"][f"r{r}"]
            print(f"    region {r}: k*={rd['dominant_k']} "
                  f"agree={rd['agree_frac']:.2f} "
                  f"streak={rd.get('max_continuous_windows', 0)}")
        ie = res.get("inter_region", {})
        for pair_key, vals in ie.items():
            print(f"    {pair_key}: count={vals['mean_count']:.1f} "
                  f"weight={vals['mean_weight']:.4f}")
        print(f"  divergence_ratio={res.get('divergence_ratio', 0):.2f} "
              f"episodes={res.get('divergence_episode_count', 0)} "
              f"mean_dur={res.get('mean_divergence_duration', 0):.1f} "
              f"max_dur={res.get('max_divergence_duration', 0)}")
        print(f"  elapsed={res['elapsed']:.0f}s")
        print("  SANITY OK")
        return

    if args.aggregate:
        aggregate()
        return

    # Run mode
    seeds = [args.seed] if args.seed else ECO_SEEDS
    for seed in seeds:
        rf = OUTPUT_DIR / f"seed_{seed}.json"
        if rf.exists():
            print(f"  seed={seed}: skip (exists)")
            continue

        print(f"  seed={seed}...", flush=True)
        result, wlogs, irlogs, sw = run_ecology(
            seed, args.N, args.plb, args.rate, args.quiet_steps)

        with open(rf, "w") as f:
            json.dump(result, f, indent=2)
        with open(OUTPUT_DIR / f"seed_{seed}_windows.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=wlogs[0].keys())
            w.writeheader()
            w.writerows(wlogs)
        with open(OUTPUT_DIR / f"seed_{seed}_inter.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=irlogs[0].keys())
            w.writeheader()
            w.writerows(irlogs)
        if sw:
            with open(OUTPUT_DIR / f"seed_{seed}_switches.json", "w") as f:
                json.dump(sw, f, indent=2)

        print(f"    global k*={result['global_dominant_k']} "
              f"sw={result['global_switches_per_100']} "
              f"div={result.get('divergence_ratio', 0):.2f} "
              f"ep={result.get('divergence_episode_count', 0)} "
              f"({result['elapsed']:.0f}s)")
        for r in range(N_REGIONS):
            rd = result["regions"][f"r{r}"]
            print(f"      r{r}: k*={rd['dominant_k']} agree={rd['agree_frac']:.2f} "
                  f"streak={rd.get('max_continuous_windows', 0)} "
                  f"mm={rd.get('mismatch_frequency', 0):.2f}")


if __name__ == "__main__":
    main()
