#!/usr/bin/env python3
"""
ESDE v8.4 — Local Wave (Static Micro-Climate)
================================================
Apply a fixed spatial decay multiplier (sin wave over x-coordinate).
Oasis zones (mult < 1.0): decay slower, structures survive easier.
Penalty zones (mult > 1.0): decay faster, structures die easier.

Engine change: ZERO. Monkey-patch physics._decay only.
Virtual layer change: ZERO. Centroid computed in calibrate loop.

Grid: side = ceil(sqrt(N)) = 71 for N=5000.
Gradient: local_multiplier[i] = 1.0 + A * sin(2π * x_i / side)
  where x_i = i % side (x-coordinate on grid)

USAGE
-----
  # Sanity (no local wave)
  python esde_v84_calibrate.py --seed 42 --windows 200

  # With local wave
  python esde_v84_calibrate.py --seed 42 --windows 200 --local-amp 0.3
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

    print(f"\n  ESDE v8.4 — Local Wave (Static Micro-Climate)")
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

    tag = f"v84_N{N}_seed{seed}_{tag_str.replace('+','_')}"
    csv_path = output_dir / f"{tag}.csv"
    status_path = output_dir / f"{tag}_status.txt"
    f = open(csv_path, "w", newline="")
    writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
    writer.writeheader()

    # Centroid log (per-window, per-label)
    centroid_log = []

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
            "version": "v8.4", "N": N,
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
        },
        "virtual_summary": engine.virtual.summary(),
        "lifecycle_log": engine.virtual.lifecycle_log,
    }
    # Add centroid log if local wave is active
    if local_amplitude > 0 and centroid_log:
        detail["centroid_log"] = centroid_log
    
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
        description="ESDE v8.4 Local Wave (Static Micro-Climate)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--windows", type=int, default=200)
    parser.add_argument("--window-steps", type=int, default=V82_WINDOW)
    parser.add_argument("--N", type=int, default=V82_N)
    parser.add_argument("--output", type=str, default="calibration_v84")
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
