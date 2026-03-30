#!/usr/bin/env python3
"""
ESDE v8.5 — Label Tracking + Frozenset Thaw Pressure
======================================================
v8.4 local wave + label tracking (C-light/D-light) + Stage 1 thaw logging.

New instrumentation (engine/virtual_layer change: ZERO):
  1. Representative label tracking: C-light (internal reweighting) + D-light (territory skew)
  2. Stage 1 frozenset thaw: hypothetical membership update logged but NOT applied

USAGE
-----
  python esde_v85_calibrate.py --seed 42 --windows 200 --local-amp 0.3
"""

import sys, csv, json, time, argparse, os, math
import numpy as np
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_V82_DIR = _SCRIPT_DIR.parent / "v82"
_V4_PIPELINE = _REPO_ROOT / "cognition" / "semantic_injection" / "v4_pipeline"
_V43_DIR = _V4_PIPELINE / "v43"
_V41_DIR = _V4_PIPELINE / "v41"
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_SCRIPT_DIR), str(_V82_DIR), str(_V43_DIR), str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from esde_v82_engine import V82Engine, V82EncapsulationParams, V82_WINDOW, V82_N
from v19g_canon import BASE_PARAMS


# ================================================================
# LOCAL WAVE: Static Micro-Climate
# ================================================================

def build_local_multiplier(N, amplitude, mode="x_coordinate"):
    """Build spatial decay multiplier array.
    
    mode='x_coordinate': sin wave along grid x-axis.
        local_multiplier[i] = 1.0 + A * sin(2π * x / side)
        Global mean = 1.0 (mean-preserving).
    
    mode='node_index': sin wave along raw node ID (fallback).
        local_multiplier[i] = 1.0 + A * sin(2π * i / N)
    """
    mult = np.ones(N)
    if amplitude == 0:
        return mult
    
    if mode == "x_coordinate":
        side = int(math.ceil(math.sqrt(N)))
        for i in range(N):
            x = i % side
            mult[i] = 1.0 + amplitude * math.sin(2 * math.pi * x / side)
    elif mode == "node_index":
        for i in range(N):
            mult[i] = 1.0 + amplitude * math.sin(2 * math.pi * i / N)
    
    return mult


def make_patched_decay(original_decay, local_multiplier):
    """Create a patched _decay that applies local_multiplier to link decay.
    
    Original: eff = decay_rate_link / (1 + beta * r)
    Patched:  eff *= mean(local_mult[i], local_mult[j])
    
    Node decay is NOT modified (nodes don't have spatial decay bias).
    """
    def patched_decay(self, state):
        p = self.params
        # Node decay: unchanged
        for i in list(state.alive_n):
            state.E[i] *= (1.0 - p.decay_rate_node)
        
        # Link decay: with local multiplier
        for k in list(state.alive_l):
            r = state.R.get(k, 0.0)
            eff = p.decay_rate_link / (1.0 + p.beta * r)
            # Apply spatial multiplier
            n1, n2 = k
            spatial = 0.5 * (local_multiplier[n1] + local_multiplier[n2])
            eff *= spatial
            state.S[k] *= (1.0 - eff)
    
    return patched_decay


def compute_label_centroids(engine, local_multiplier):
    """Compute spatial centroids + per-node physical state + territory spatial distribution.
    
    Returns:
      - csv_stats: aggregated stats for CSV logging
      - centroid_data: per-label per-window data for detail.json
    
    Instruments:
      C: frozenset内ノードの物理状態 (oasis側/penalty側の生存差)
      D: territory空間分布 (territoryリンクの空間的偏り)
      L4: edge environment class (oasis-oasis / oasis-penalty / penalty-penalty)
    """
    side = int(math.ceil(math.sqrt(engine.N)))
    labels = engine.virtual.labels
    state = engine.state
    
    # Pre-compute degree map for territory
    deg = {}
    for lk in state.alive_l:
        n1, n2 = lk
        deg[n1] = deg.get(n1, 0) + 1
        deg[n2] = deg.get(n2, 0) + 1
    
    # Edge environment class (GPT L4)
    edge_oo = 0  # oasis-oasis
    edge_op = 0  # oasis-penalty (cross-boundary)
    edge_pp = 0  # penalty-penalty
    edge_other = 0  # neutral involved
    for lk in state.alive_l:
        n1, n2 = lk
        m1 = local_multiplier[n1]
        m2 = local_multiplier[n2]
        is_oasis_1 = m1 < 0.95
        is_oasis_2 = m2 < 0.95
        is_pen_1 = m1 > 1.05
        is_pen_2 = m2 > 1.05
        if is_oasis_1 and is_oasis_2:
            edge_oo += 1
        elif is_pen_1 and is_pen_2:
            edge_pp += 1
        elif (is_oasis_1 and is_pen_2) or (is_pen_1 and is_oasis_2):
            edge_op += 1
        else:
            edge_other += 1
    
    # Pre-compute per-node neighbor list for territory (D)
    node_neighbors = {}  # node -> list of (other_node, link_key)
    for lk in state.alive_l:
        n1, n2 = lk
        node_neighbors.setdefault(n1, []).append(n2)
        node_neighbors.setdefault(n2, []).append(n1)
    
    # Per-label analysis
    centroid_data = []
    oasis_count = 0
    penalty_count = 0
    
    for lid, label in labels.items():
        nodes = label["nodes"]
        if not nodes:
            continue
        
        # Basic centroid
        xs = [n % side for n in nodes]
        ys = [n // side for n in nodes]
        mean_x = sum(xs) / len(xs)
        mean_y = sum(ys) / len(ys)
        mean_mult = sum(local_multiplier[n] for n in nodes) / len(nodes)
        
        # ── C: Per-node physical state ──
        n_alive = sum(1 for n in nodes if n in state.alive_n)
        e_vals = [float(state.E[n]) for n in nodes if n in state.alive_n]
        mean_e = sum(e_vals) / len(e_vals) if e_vals else 0
        links_per_node = [deg.get(n, 0) for n in nodes]
        mean_links = sum(links_per_node) / len(links_per_node)
        oasis_nodes = [n for n in nodes if local_multiplier[n] < 0.95]
        penalty_nodes = [n for n in nodes if local_multiplier[n] > 1.05]
        oasis_links = sum(deg.get(n, 0) for n in oasis_nodes)
        penalty_links = sum(deg.get(n, 0) for n in penalty_nodes)
        
        # ── D: Territory spatial distribution ──
        label_node_set = set(nodes)
        terr_oasis = 0
        terr_penalty = 0
        terr_neutral = 0
        for n in nodes:
            for other in node_neighbors.get(n, []):
                if other in label_node_set:
                    continue  # skip internal links
                m_other = local_multiplier[other]
                if m_other < 0.95:
                    terr_oasis += 1
                elif m_other > 1.05:
                    terr_penalty += 1
                else:
                    terr_neutral += 1
        
        entry = {
            "label_id": lid,
            "nodes": len(nodes),
            "centroid_x": round(mean_x, 2),
            "centroid_y": round(mean_y, 2),
            "mean_local_mult": round(mean_mult, 4),
            # C: node physical state
            "n_alive": n_alive,
            "mean_E": round(mean_e, 4),
            "mean_links_per_node": round(mean_links, 2),
            "n_oasis_nodes": len(oasis_nodes),
            "n_penalty_nodes": len(penalty_nodes),
            "oasis_node_links": oasis_links,
            "penalty_node_links": penalty_links,
            # D: territory spatial distribution
            "terr_oasis": terr_oasis,
            "terr_penalty": terr_penalty,
            "terr_neutral": terr_neutral,
        }
        centroid_data.append(entry)
        
        if mean_mult < 0.9:
            oasis_count += 1
        elif mean_mult > 1.1:
            penalty_count += 1
    
    n_labels = len(centroid_data)
    return {
        "n_labels": n_labels,
        "n_oasis": oasis_count,
        "n_penalty": penalty_count,
        "n_neutral": n_labels - oasis_count - penalty_count,
        # L4: edge environment class
        "edge_oo": edge_oo,
        "edge_op": edge_op,
        "edge_pp": edge_pp,
    }, centroid_data


# ================================================================
# LABEL TRACKING (C-light + D-light)
# ================================================================

def select_representative_labels(engine, local_multiplier, n_per_size=2):
    """Select representative labels for tracking.
    Pick up to n_per_size from each size class that are alive.
    Prefer labels near oasis/penalty boundary (mult ≈ 1.0) for interesting tracking.
    """
    side = int(math.ceil(math.sqrt(engine.N)))
    labels = engine.virtual.labels
    
    by_size = {}
    for lid, label in labels.items():
        nodes = label["nodes"]
        n = len(nodes)
        mean_mult = sum(local_multiplier[nd] for nd in nodes) / max(1, n)
        by_size.setdefault(n, []).append((lid, abs(mean_mult - 1.0)))
    
    selected = []
    for size in sorted(by_size.keys()):
        # Sort by distance from boundary (mult=1.0), take closest
        candidates = sorted(by_size[size], key=lambda x: x[1])
        for lid, _ in candidates[:n_per_size]:
            selected.append(lid)
    
    return set(selected)


def track_label_detail(engine, lid, local_multiplier, node_neighbors, deg):
    """C-light + D-light for a single label.
    Returns dict of tracking metrics, or None if label is dead.
    deg: pre-computed degree map {node: link_count}
    """
    labels = engine.virtual.labels
    if lid not in labels:
        return None
    
    label = labels[lid]
    nodes = label["nodes"]
    if not nodes:
        return None
    
    state = engine.state
    side = int(math.ceil(math.sqrt(engine.N)))
    
    # C-light: internal reweighting
    oasis_nodes = [n for n in nodes if local_multiplier[n] < 0.95]
    penalty_nodes = [n for n in nodes if local_multiplier[n] > 1.05]
    neutral_nodes = [n for n in nodes
                     if 0.95 <= local_multiplier[n] <= 1.05]
    
    oasis_links = sum(deg.get(n, 0) for n in oasis_nodes)
    penalty_links = sum(deg.get(n, 0) for n in penalty_nodes)
    oasis_alive = sum(1 for n in oasis_nodes if n in state.alive_n)
    penalty_alive = sum(1 for n in penalty_nodes if n in state.alive_n)
    
    oasis_E = [float(state.E[n]) for n in oasis_nodes if n in state.alive_n]
    penalty_E = [float(state.E[n]) for n in penalty_nodes if n in state.alive_n]
    
    # D-light: territory skew
    label_node_set = set(nodes)
    terr_oasis = 0
    terr_penalty = 0
    for n in nodes:
        for other in node_neighbors.get(n, []):
            if other in label_node_set:
                continue
            m = local_multiplier[other]
            if m < 0.95:
                terr_oasis += 1
            elif m > 1.05:
                terr_penalty += 1
    
    terr_total = terr_oasis + terr_penalty
    terr_skew = ((terr_oasis - terr_penalty) / max(1, terr_total))
    
    xs = [n % side for n in nodes]
    ys = [n // side for n in nodes]
    
    return {
        "label_id": lid,
        "nodes": len(nodes),
        "centroid_x": round(sum(xs) / len(xs), 2),
        "centroid_y": round(sum(ys) / len(ys), 2),
        "share": round(label["share"], 6),
        # C-light
        "n_oasis_nodes": len(oasis_nodes),
        "n_penalty_nodes": len(penalty_nodes),
        "n_neutral_nodes": len(neutral_nodes),
        "oasis_alive": oasis_alive,
        "penalty_alive": penalty_alive,
        "oasis_links": oasis_links,
        "penalty_links": penalty_links,
        "oasis_mean_E": round(sum(oasis_E) / max(1, len(oasis_E)), 4) if oasis_E else 0,
        "penalty_mean_E": round(sum(penalty_E) / max(1, len(penalty_E)), 4) if penalty_E else 0,
        "link_ratio": round(oasis_links / max(1, penalty_links), 3) if penalty_links > 0 else 0,
        # D-light
        "terr_oasis": terr_oasis,
        "terr_penalty": terr_penalty,
        "terr_skew": round(terr_skew, 4),
    }


# ================================================================
# STAGE 1: FROZENSET THAW PRESSURE (hypothetical only)
# ================================================================

def compute_thaw_pressure(engine, local_multiplier):
    """For each alive label, compute what would happen if frozenset were thawed.
    
    Method:
    1. Get label's phase_sig
    2. Find nearest other label's phase_sig → half-distance = theta_range
    3. Find all alive nodes within ±theta_range of phase_sig
    4. Compare with current nodes (Jaccard)
    
    theta_range is NOT a fixed constant. It is determined by the local
    density of labels in phase space. Dense areas → narrow range.
    Sparse areas → wide range. This is dynamic equilibrium:
    the system's own structure determines the measurement scale.
    
    Returns list of per-label thaw pressure dicts.
    Does NOT modify any label data.
    """
    labels = engine.virtual.labels
    state = engine.state
    
    # Build alive node theta array for fast lookup
    alive_list = list(state.alive_n)
    if not alive_list:
        return []
    alive_thetas = {n: float(state.theta[n]) for n in alive_list}
    
    # Pre-compute all label phase_sigs for nearest-neighbor distance
    label_sigs = {}
    for lid, label in labels.items():
        if label["nodes"]:
            label_sigs[lid] = label["phase_sig"]
    
    results = []
    for lid, label in labels.items():
        nodes = label["nodes"]
        if not nodes:
            continue
        
        phase_sig = label["phase_sig"]
        
        # ── Dynamic theta_range from nearest label distance ──
        # Find minimum phase distance to any other label
        min_dist = math.pi  # worst case: half circle
        for other_lid, other_sig in label_sigs.items():
            if other_lid == lid:
                continue
            d = abs(phase_sig - other_sig)
            if d > math.pi:
                d = 2 * math.pi - d
            if d < min_dist:
                min_dist = d
        
        # theta_range = half of nearest neighbor distance
        # Dense → narrow, Sparse → wide. Dynamic equilibrium.
        theta_range = max(0.05, min_dist / 2.0)  # min 0.05 rad ≈ 3°
        
        # Current nodes' theta values
        current_thetas = []
        for n in nodes:
            if n in state.alive_n:
                current_thetas.append(float(state.theta[n]))
        
        if len(current_thetas) < 2:
            results.append({
                "label_id": lid,
                "nodes_current": len(nodes),
                "nodes_hypothetical": len(nodes),
                "jaccard": 1.0,
                "n_add": 0,
                "n_drop": 0,
                "add_oasis_frac": 0,
                "drop_penalty_frac": 0,
                "thaw_pressure": 0,
                "theta_range": round(theta_range, 4),
            })
            continue
        
        # Find hypothetical nodes: alive nodes within theta_range of phase_sig
        hypothetical = set()
        for n, theta in alive_thetas.items():
            d = abs(theta - phase_sig)
            if d > math.pi:
                d = 2 * math.pi - d
            if d <= theta_range:
                hypothetical.add(n)
        
        current_set = set(nodes)
        
        # Jaccard
        intersection = current_set & hypothetical
        union = current_set | hypothetical
        jaccard = len(intersection) / max(1, len(union))
        
        # Add / drop
        added = hypothetical - current_set
        dropped = current_set - hypothetical
        
        # Spatial bias of adds and drops
        add_oasis = sum(1 for n in added if local_multiplier[n] < 0.95)
        add_penalty = sum(1 for n in added if local_multiplier[n] > 1.05)
        drop_oasis = sum(1 for n in dropped if local_multiplier[n] < 0.95)
        drop_penalty = sum(1 for n in dropped if local_multiplier[n] > 1.05)
        
        add_oasis_frac = add_oasis / max(1, len(added)) if added else 0
        drop_penalty_frac = drop_penalty / max(1, len(dropped)) if dropped else 0
        
        # Thaw pressure: 1 - jaccard (0 = no pressure, 1 = total replacement)
        thaw_pressure = 1.0 - jaccard
        
        results.append({
            "label_id": lid,
            "nodes_current": len(nodes),
            "nodes_hypothetical": len(hypothetical),
            "jaccard": round(jaccard, 4),
            "n_add": len(added),
            "n_drop": len(dropped),
            "add_oasis_frac": round(add_oasis_frac, 3),
            "drop_penalty_frac": round(drop_penalty_frac, 3),
            "thaw_pressure": round(thaw_pressure, 4),
            "theta_range": round(theta_range, 4),
        })
    
    return results


# ================================================================
# LOG FIELDS
# ================================================================

LOG_FIELDS = [
    "window", "alive_nodes", "alive_links",
    "n_clusters", "max_size",
    "k_star", "entropy", "milestone", "physics_seconds",
    "stressed", "calcified", "mean_omega",
    "stress_intensity", "link_ema",
    "total_rplus",
    "budget", "v_labels", "v_born", "v_died",
    "v_torque_n", "v_mean_torque", "v_top_share",
    "v_label_rplus_rate",
    "v_oldest_age", "v_mean_age",
    "v_mean_share_5node", "v_share_std",
    "v_births_5node", "v_deaths_5node",
    "macro_nodes_active", "compressed_links_removed",
    "occ_max", "occ_mean", "occ_nonzero",
    "vacancy_mean", "history_max", "history_gini",
    # v8.4 local wave columns
    "lw_n_oasis", "lw_n_penalty", "lw_n_neutral",
    "lw_edge_oo", "lw_edge_op", "lw_edge_pp",
    # v8.5 thaw pressure summary
    "thaw_mean_jaccard", "thaw_mean_pressure",
    "thaw_mean_add", "thaw_mean_drop",
    "thaw_mean_range",
]


# ================================================================
# RUN
# ================================================================

def run(seed, n_windows, window_steps, output_dir, encap_params, N,
        compression_enabled=False, compress_at_window=50,
        compress_min_age=10,
        maturation_alpha=0.10, rigidity_beta=0.10,
        local_amplitude=0.0):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tags = []
    if encap_params.stress_enabled: tags.append("stress")
    if encap_params.virtual_enabled: tags.append("metab")
    if local_amplitude > 0: tags.append(f"local_A{local_amplitude}")
    if not tags: tags.append("baseline")
    tag_str = "+".join(tags)

    # Build local multiplier
    local_multiplier = build_local_multiplier(N, local_amplitude, mode="x_coordinate")
    side = int(math.ceil(math.sqrt(N)))

    print(f"\n  ESDE v8.5 — Label Tracking + Thaw Pressure")
    print(f"  N={N} seed={seed} windows={n_windows} "
          f"steps/win={window_steps} [{tag_str}]")
    print(f"  maturation_alpha={maturation_alpha} rigidity_beta={rigidity_beta}")
    if local_amplitude > 0:
        print(f"  LOCAL WAVE: amplitude={local_amplitude} mode=x_coordinate "
              f"grid_side={side}")
        print(f"    mult range: [{local_multiplier.min():.3f}, {local_multiplier.max():.3f}]")
        print(f"    mult mean:  {local_multiplier.mean():.4f}")
    print(f"  Injection...", flush=True)

    t_start = time.time()
    engine = V82Engine(seed=seed, N=N, encap_params=encap_params,
                       compression_enabled=compression_enabled,
                       compress_at_window=compress_at_window,
                       compress_min_age=compress_min_age,
                       maturation_alpha=maturation_alpha,
                       rigidity_beta=rigidity_beta)

    # ── Monkey-patch: apply local multiplier to decay ──
    if local_amplitude > 0:
        import types
        patched = make_patched_decay(engine.physics._decay, local_multiplier)
        engine.physics._decay = types.MethodType(patched, engine.physics)
        print(f"  Decay monkey-patch applied.")

    engine.run_injection()
    t_inj = time.time() - t_start
    print(f"  Injection done ({t_inj:.0f}s). Starting windows.\n")

    tag = f"v85_N{N}_seed{seed}_{tag_str.replace('+','_')}"
    csv_path = output_dir / f"{tag}.csv"
    status_path = output_dir / f"{tag}_status.txt"
    f = open(csv_path, "w", newline="")
    writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
    writer.writeheader()

    # Centroid log (per-window, per-label)
    centroid_log = []
    # v8.5: label tracking + thaw pressure
    tracking_log = []   # C-light + D-light for representative labels
    thaw_log = []       # Stage 1 hypothetical thaw for all labels
    rep_labels = set()  # representative label IDs (selected at w50)

    # Header
    print(f"  {'win':>4} {'clst':>4} {'R+':>5} {'sI':>5} "
          f"{'vLb':>4} {'topS':>6} {'rR+':>6} "
          f"{'lnks':>6} {'M':>1} {'sec':>5} {'ETA':>6}"
          f"{'oasis':>6}{'pen':>5}" if local_amplitude > 0 else "")
    print(f"  {'-'*68}")

    times = []

    for w in range(n_windows):
        t0 = time.time()
        frame = engine.step_window(steps=window_steps)
        sec = time.time() - t0
        times.append(sec)

        isum = engine.last_isum
        vl = engine.virtual_stats
        ss = engine.stress_stats

        rplus = sum(1 for lk in engine.state.alive_l
                    if engine.state.R.get(lk, 0.0) > 0)

        # Compute spatial stats
        if local_amplitude > 0:
            lw_stats, cdata = compute_label_centroids(engine, local_multiplier)
            for cd in cdata:
                cd["window"] = frame.window
            centroid_log.extend(cdata)
        else:
            lw_stats = {"n_oasis": 0, "n_penalty": 0, "n_neutral": 0,
                        "edge_oo": 0, "edge_op": 0, "edge_pp": 0}

        # ── v8.5: Representative label tracking ──
        if local_amplitude > 0:
            # Select representatives at w50 (after initial transient)
            if frame.window == 50 and not rep_labels:
                rep_labels = select_representative_labels(
                    engine, local_multiplier, n_per_size=2)
                print(f"  [v8.5] Selected {len(rep_labels)} representative labels"
                      f" at w{frame.window}")

            # Pre-compute node neighbors + degree map (single scan)
            _nn = {}
            _deg = {}
            for lk in engine.state.alive_l:
                n1, n2 = lk
                _nn.setdefault(n1, []).append(n2)
                _nn.setdefault(n2, []).append(n1)
                _deg[n1] = _deg.get(n1, 0) + 1
                _deg[n2] = _deg.get(n2, 0) + 1

            # Track representatives
            if rep_labels:
                for rlid in list(rep_labels):
                    td = track_label_detail(engine, rlid, local_multiplier, _nn, _deg)
                    if td is not None:
                        td["window"] = frame.window
                        tracking_log.append(td)
                    # Don't remove dead labels from rep_labels
                    # (their absence is informative)

        # ── v8.5: Stage 1 thaw pressure ──
        thaw_summary = {"mean_jaccard": 1.0, "mean_pressure": 0.0,
                        "mean_add": 0, "mean_drop": 0, "mean_range": 0}
        if local_amplitude > 0 and frame.window >= 50:
            thaw_results = compute_thaw_pressure(engine, local_multiplier)
            if thaw_results:
                for tr in thaw_results:
                    tr["window"] = frame.window
                thaw_log.extend(thaw_results)
                # Summary for CSV
                jaccards = [r["jaccard"] for r in thaw_results]
                pressures = [r["thaw_pressure"] for r in thaw_results]
                adds = [r["n_add"] for r in thaw_results]
                drops = [r["n_drop"] for r in thaw_results]
                ranges = [r.get("theta_range", 0) for r in thaw_results]
                thaw_summary = {
                    "mean_jaccard": round(np.mean(jaccards), 4),
                    "mean_pressure": round(np.mean(pressures), 4),
                    "mean_add": round(np.mean(adds), 1),
                    "mean_drop": round(np.mean(drops), 1),
                    "mean_range": round(np.mean(ranges), 4),
                }

        row = {
            "window": frame.window,
            "alive_nodes": frame.alive_nodes,
            "alive_links": frame.alive_links,
            "n_clusters": isum.get("n_clusters", 0),
            "max_size": isum.get("max_size", 0),
            "k_star": frame.k_star,
            "entropy": round(frame.entropy, 4),
            "milestone": frame.milestone,
            "physics_seconds": round(sec, 1),
            "stressed": ss.get("stressed", 0),
            "calcified": ss.get("calcified", 0),
            "mean_omega": ss.get("mean_omega", 0),
            "stress_intensity": ss.get("stress_intensity", 1.0),
            "link_ema": ss.get("link_ema", 0),
            "total_rplus": rplus,
            "budget": vl.get("budget", 0),
            "v_labels": vl.get("labels_active", 0),
            "v_born": vl.get("labels_born", 0),
            "v_died": vl.get("labels_died", 0),
            "v_torque_n": vl.get("torque_events", 0),
            "v_mean_torque": vl.get("mean_torque", 0),
            "v_top_share": vl.get("top_share", 0),
            "v_label_rplus_rate": vl.get("label_rplus_rate", 0),
            "v_oldest_age": vl.get("v_oldest_age", 0),
            "v_mean_age": vl.get("v_mean_age", 0),
            "v_mean_share_5node": vl.get("v_mean_share_5node", 0),
            "v_share_std": vl.get("v_share_std", 0),
            "v_births_5node": vl.get("v_births_5node", 0),
            "v_deaths_5node": vl.get("v_deaths_5node", 0),
            "macro_nodes_active": vl.get("macro_nodes_active", 0),
            "compressed_links_removed": vl.get("compressed_links_removed", 0),
            "occ_max": vl.get("occ_max", 0),
            "occ_mean": vl.get("occ_mean", 0),
            "occ_nonzero": vl.get("occ_nonzero", 0),
            "vacancy_mean": vl.get("vacancy_mean", 0),
            "history_max": vl.get("history_max", 0),
            "history_gini": vl.get("history_gini", 0),
            # v8.4 local wave
            "lw_n_oasis": lw_stats["n_oasis"],
            "lw_n_penalty": lw_stats["n_penalty"],
            "lw_n_neutral": lw_stats["n_neutral"],
            "lw_edge_oo": lw_stats["edge_oo"],
            "lw_edge_op": lw_stats["edge_op"],
            "lw_edge_pp": lw_stats["edge_pp"],
            # v8.5 thaw pressure summary
            "thaw_mean_jaccard": thaw_summary["mean_jaccard"],
            "thaw_mean_pressure": thaw_summary["mean_pressure"],
            "thaw_mean_add": thaw_summary["mean_add"],
            "thaw_mean_drop": thaw_summary["mean_drop"],
            "thaw_mean_range": thaw_summary["mean_range"],
        }
        writer.writerow(row)
        f.flush()

        # ETA
        avg_sec = np.mean(times[-10:])
        remaining = (n_windows - w - 1) * avg_sec
        eta_str = f"{remaining/3600:.1f}h" if remaining > 3600 else f"{remaining/60:.0f}m"

        extra = ""
        if local_amplitude > 0:
            extra = f" oa={lw_stats['n_oasis']:>2} pn={lw_stats['n_penalty']:>2}"

        print(f"  {frame.window:>4} "
              f"{isum.get('n_clusters',0):>4} "
              f"{rplus:>5} "
              f"{ss.get('stress_intensity',1.0):>5.3f} "
              f"{vl.get('labels_active',0):>4} "
              f"{vl.get('top_share',0):>6.4f} "
              f"{vl.get('label_rplus_rate',0):>6.1f} "
              f"{frame.alive_links:>6} "
              f"{frame.milestone:>1} "
              f"{sec:>5.0f} "
              f"{eta_str:>6}"
              f"{extra}")

        with open(status_path, "w") as sf:
            elapsed = time.time() - t_start
            sf.write(f"seed={seed} N={N} w={frame.window}/{n_windows} "
                     f"links={frame.alive_links} R+={rplus} "
                     f"vLb={vl.get('labels_active',0)} "
                     f"sI={ss.get('stress_intensity',1.0):.3f} "
                     f"sec/win={avg_sec:.0f} ETA={eta_str} "
                     f"elapsed={elapsed/3600:.1f}h\n")

    f.close()
    t_total = time.time() - t_start

    # JSON detail
    json_path = output_dir / f"{tag}_detail.json"
    detail = {
        "meta": {
            "version": "v8.5", "N": N,
            "seed": seed, "n_windows": n_windows,
            "window_steps": window_steps,
            "stress_enabled": bool(encap_params.stress_enabled),
            "virtual_enabled": bool(encap_params.virtual_enabled),
            "final_alive_links": frame.alive_links,
            "total_seconds": round(t_total, 0),
            "mean_sec_per_window": round(np.mean(times), 1),
            "maturation_alpha": maturation_alpha,
            "rigidity_beta": rigidity_beta,
            "local_amplitude": local_amplitude,
            "local_mode": "x_coordinate",
            "grid_side": side,
            "representative_labels": sorted(rep_labels) if rep_labels else [],
        },
        "virtual_summary": engine.virtual.summary(),
        "lifecycle_log": engine.virtual.lifecycle_log,
    }
    # Add logs if local wave is active
    if local_amplitude > 0:
        if centroid_log:
            detail["centroid_log"] = centroid_log
        if tracking_log:
            detail["tracking_log"] = tracking_log
        if thaw_log:
            detail["thaw_log"] = thaw_log
    
    with open(json_path, "w") as jf:
        json.dump(detail, jf, indent=2, default=str)

    os.remove(status_path)

    print(f"\n  DONE: seed={seed} N={N} "
          f"links={frame.alive_links} R+={rplus} "
          f"vLb={vl.get('labels_active',0)} "
          f"total={t_total/3600:.1f}h ({np.mean(times):.0f}s/win)")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}\n")


def main():
    parser = argparse.ArgumentParser(
        description="ESDE v8.5 Label Tracking + Thaw Pressure")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--windows", type=int, default=200)
    parser.add_argument("--window-steps", type=int, default=V82_WINDOW)
    parser.add_argument("--N", type=int, default=V82_N)
    parser.add_argument("--output", type=str, default="calibration_v85")
    parser.add_argument("--no-stress", action="store_true")
    parser.add_argument("--no-virtual", action="store_true")
    parser.add_argument("--maturation-alpha", type=float, default=0.10)
    parser.add_argument("--rigidity-beta", type=float, default=0.10)
    parser.add_argument("--local-amp", type=float, default=0.0,
                        help="Local wave amplitude (0=off, 0.3=±30%% decay bias)")
    args = parser.parse_args()

    params = V82EncapsulationParams(
        stress_enabled=not args.no_stress,
        virtual_enabled=not args.no_virtual,
    )

    run(seed=args.seed, n_windows=args.windows,
        window_steps=args.window_steps, output_dir=args.output,
        encap_params=params, N=args.N,
        maturation_alpha=args.maturation_alpha,
        rigidity_beta=args.rigidity_beta,
        local_amplitude=args.local_amp)


if __name__ == "__main__":
    main()
