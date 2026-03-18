#!/usr/bin/env python3
"""
ESDE v5.0 — Circulation Dynamics Calibration
===============================================
USAGE
-----
  # Sanity
  python esde_v50_calibrate.py --seed 42 --windows 10

  # Standard
  parallel -j 2 python esde_v50_calibrate.py --seed {1} --windows 200 ::: 42 123

  # Ablation: circulation off (pure v4.9 behavior)
  python esde_v50_calibrate.py --seed 42 --windows 100 --no-circulation

  # Ablation: v4.8c baseline
  python esde_v50_calibrate.py --seed 42 --windows 100 --no-history --no-void --no-circulation

  # Aggregate
  python esde_v50_calibrate.py --aggregate --output calibration_v50
"""

import sys, csv, json, time, argparse
import numpy as np
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from esde_v50_engine import V50Engine, V50EncapsulationParams, V50_WINDOW

LOG_FIELDS = [
    "window", "alive_nodes", "alive_links",
    "n_clusters", "n_encapsulated", "n_candidates",
    "max_size", "max_density_ratio", "max_seen_count",
    "mean_inner_entropy", "max_inner_entropy",
    "total_inner_triangles", "motif_recurrence_count",
    "encap_events_total", "dissolve_events_total",
    "hardened_links_count", "k_star", "entropy", "entropy_delta",
    "milestone", "physics_seconds",
    "max_lifespan", "mean_continuity", "max_continuity", "mean_turnover_rate",
    "pd_p_count", "pd_d_count", "pd_both_count",
    "resonant_incorporations", "dissonant_incorporations",
    "resonant_rejections", "dissonant_rejections",
    "resonance_total_events", "resonance_ratio",
    "personalities_recorded",
    "max_relaxed_lifespan", "max_strict_lifespan",
    "identity_stable", "identity_drift",
    "identity_new", "identity_reformation", "mean_jaccard",
    "motif_alpha", "motif_beta", "motif_gamma",
    "cooled_nodes", "mean_cooling_factor",
    "z_hardened", "z_softened", "z_tensioned",
    "alpha_t", "compound_restore", "inert_penalty",
    "delta_L", "delta_Z0", "drift_applied",
    # v4.9 Phase 1
    "mean_h_age", "max_h_age", "mean_h_res", "max_h_res",
    "mean_h_str", "max_h_str",
    "mature_links", "rigid_links", "brittle_links",
    "hist_matured", "hist_snapped", "hist_suppressed",
    "avalanche_events", "cascade_links",
    # v4.9 Phase 2b
    "void_mean_V", "void_max_V", "void_active_nodes",
    "gen_births", "gen_candidates", "gen_max_T", "gen_max_delta",
    "void_consumed", "void_deposited",
    "proliferation_pi", "void_induced_births",
    # v4.9 Phase 3
    "void_total_mass", "void_variance",
    "void_isolated_high", "void_active_neighbor_high",
    "void_diffusion_events", "void_to_active", "void_c_diff",
    # v4.9 Phase 4
    "cascade_splashes",
    # v5.0 Circulation
    "circ_proximity_restored", "circ_proximity_restore_total",
    "circ_heat_events", "circ_heat_total",
    "circ_capture_events", "circ_capture_total",
    "circ_dynamic_bg_prob",
    "circ_pi_tension_snap", "circ_pi_tension_entropy",
    "circ_pi_tension_energy",
]


def run(seed, n_windows, window_steps, output_dir, encap_params):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  ESDE v5.0 — Circulation Dynamics")
    print(f"  seed={seed} windows={n_windows} steps/win={window_steps}")
    print(f"  history={encap_params.history_enabled} "
          f"void={encap_params.void_enabled} "
          f"circulation={encap_params.circulation_enabled}")
    print(f"  Injection...", flush=True)

    engine = V50Engine(seed=seed, encap_params=encap_params)
    engine.run_injection()

    h_tag = "hist" if encap_params.history_enabled else "nohist"
    v_tag = "void" if encap_params.void_enabled else "novoid"
    c_tag = "circ" if encap_params.circulation_enabled else "nocirc"
    tag = f"v50_seed{seed}_{h_tag}_{v_tag}_{c_tag}"
    csv_path = output_dir / f"{tag}.csv"
    f = open(csv_path, "w", newline="")
    writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
    writer.writeheader()

    max_ms = 0

    print(f"\n  {'win':>4} {'clst':>4} {'mxSz':>4} {'rLif':>4} "
          f"{'mxDR':>5} {'drft':>4} "
          f"{'rest':>7} {'Π':>5} "
          f"{'prox':>4} {'heat':>4} {'capt':>5} "
          f"{'gBr':>4} {'snap':>4} {'mV':>5} "
          f"{'lnks':>5} {'M':>1} {'sec':>4}")
    print(f"  {'-'*110}")

    for w in range(n_windows):
        t0 = time.time()
        frame = engine.step_window(steps=window_steps)
        sec = time.time() - t0

        isum = engine.last_isum
        assert isum, f"last_isum empty at window {w+1}"
        cs = engine.cooling_stats
        zs = engine.z_stats
        hs = engine.history_stats
        vs = engine.void_stats
        cc = engine.circulation_stats
        max_ms = max(max_ms, frame.milestone)

        traj = engine.drift_trajectory
        cur = traj[-1] if traj else {}
        cur_alpha = cur.get("alpha_t", 0)
        cur_restore = cur.get("compound_restore",
                              encap_params.z_decay_compound_restore)
        cur_inert = cur.get("inert_penalty",
                            encap_params.z_decay_inert_penalty)
        cur_dL = cur.get("delta_L", 0)
        cur_dZ0 = cur.get("delta_Z0", 0)
        cur_applied = cur.get("applied", False)

        row = {
            "window": frame.window,
            "alive_nodes": frame.alive_nodes,
            "alive_links": frame.alive_links,
            "n_clusters": isum["n_clusters"],
            "n_encapsulated": isum["n_encapsulated"],
            "n_candidates": isum["n_candidates"],
            "max_size": isum["max_size"],
            "max_density_ratio": isum["max_density_ratio"],
            "max_seen_count": isum["max_seen_count"],
            "mean_inner_entropy": isum["mean_inner_entropy"],
            "max_inner_entropy": isum["max_inner_entropy"],
            "total_inner_triangles": isum["total_inner_tri"],
            "motif_recurrence_count": isum["motif_recurrence"],
            "encap_events_total": isum["encap_events"],
            "dissolve_events_total": isum["dissolve_events"],
            "hardened_links_count": len(engine.hardening),
            "k_star": frame.k_star,
            "entropy": round(frame.entropy, 4),
            "entropy_delta": round(frame.entropy_delta, 4),
            "milestone": frame.milestone,
            "physics_seconds": round(sec, 1),
            "max_lifespan": isum["max_lifespan"],
            "mean_continuity": isum["mean_continuity"],
            "max_continuity": isum["max_continuity"],
            "mean_turnover_rate": isum["mean_turnover_rate"],
            "pd_p_count": isum["pd_p_count"],
            "pd_d_count": isum["pd_d_count"],
            "pd_both_count": isum["pd_both_count"],
            "resonant_incorporations": isum["resonant_incorporations"],
            "dissonant_incorporations": isum["dissonant_incorporations"],
            "resonant_rejections": isum["resonant_rejections"],
            "dissonant_rejections": isum["dissonant_rejections"],
            "resonance_total_events": isum["resonance_total_events"],
            "resonance_ratio": isum["resonance_ratio"],
            "personalities_recorded": isum["personalities_recorded"],
            "max_relaxed_lifespan": isum["max_relaxed_lifespan"],
            "max_strict_lifespan": isum["max_strict_lifespan"],
            "identity_stable": isum["identity_stable"],
            "identity_drift": isum["identity_drift"],
            "identity_new": isum["identity_new"],
            "identity_reformation": isum["identity_reformation"],
            "mean_jaccard": isum["mean_jaccard"],
            "motif_alpha": isum["motif_alpha"],
            "motif_beta": isum["motif_beta"],
            "motif_gamma": isum["motif_gamma"],
            "cooled_nodes": cs.get("cooled_nodes", 0),
            "mean_cooling_factor": cs.get("mean_cooling_factor", 1.0),
            "z_hardened": zs.get("hardened", 0),
            "z_softened": zs.get("softened", 0),
            "z_tensioned": zs.get("tensioned", 0),
            "alpha_t": cur_alpha,
            "compound_restore": cur_restore,
            "inert_penalty": cur_inert,
            "delta_L": cur_dL,
            "delta_Z0": cur_dZ0,
            "drift_applied": 1 if cur_applied else 0,
            # Phase 1
            "mean_h_age": hs.get("mean_h_age", 0),
            "max_h_age": hs.get("max_h_age", 0),
            "mean_h_res": hs.get("mean_h_res", 0),
            "max_h_res": hs.get("max_h_res", 0),
            "mean_h_str": hs.get("mean_h_str", 0),
            "max_h_str": hs.get("max_h_str", 0),
            "mature_links": hs.get("mature_links", 0),
            "rigid_links": hs.get("rigid_links", 0),
            "brittle_links": hs.get("brittle_links", 0),
            "hist_matured": hs.get("matured", 0),
            "hist_snapped": hs.get("snapped", 0),
            "hist_suppressed": hs.get("suppressed_nodes", 0),
            "avalanche_events": hs.get("avalanche_events", 0),
            "cascade_links": hs.get("cascade_links", 0),
            # Phase 2
            "void_mean_V": vs.get("mean_V", 0),
            "void_max_V": vs.get("max_V", 0),
            "void_active_nodes": vs.get("active_V_nodes", 0),
            "gen_births": vs.get("gen_births", 0),
            "gen_candidates": vs.get("gen_candidates", 0),
            "gen_max_T": round(vs.get("gen_max_T", 0), 6),
            "gen_max_delta": round(vs.get("gen_max_delta", 0), 6),
            "void_consumed": vs.get("consumed_events", 0),
            "void_deposited": round(hs.get("void_deposited", 0), 4),
            "proliferation_pi": cur.get("proliferation_pi",
                                        encap_params.proliferation_pi),
            "void_induced_births": vs.get("void_induced_births", 0),
            # Phase 3
            "void_total_mass": vs.get("total_void_mass", 0),
            "void_variance": vs.get("void_variance", 0),
            "void_isolated_high": vs.get("isolated_high_V", 0),
            "void_active_neighbor_high": vs.get("active_neighbor_high_V", 0),
            "void_diffusion_events": vs.get("diffusion_events", 0),
            "void_to_active": vs.get("void_to_active", 0),
            "void_c_diff": vs.get("c_diff", 0),
            # Phase 4
            "cascade_splashes": vs.get("cascade_splashes", 0),
            # v5.0 Circulation
            "circ_proximity_restored": cc.get("proximity_restored", 0),
            "circ_proximity_restore_total": round(
                cc.get("proximity_total_restore", 0), 4),
            "circ_heat_events": cc.get("heat_events", 0),
            "circ_heat_total": round(cc.get("heat_total", 0), 4),
            "circ_capture_events": cc.get("capture_events", 0),
            "circ_capture_total": round(cc.get("capture_total", 0), 4),
            "circ_dynamic_bg_prob": cc.get("dynamic_bg_prob", 0),
            "circ_pi_tension_snap": cc.get("pi_tension_snap", 0),
            "circ_pi_tension_entropy": cc.get("pi_tension_entropy", 0),
            "circ_pi_tension_energy": cc.get("pi_tension_energy", 0),
        }
        writer.writerow(row)
        f.flush()

        cur_pi = cur.get("proliferation_pi",
                         encap_params.proliferation_pi)

        print(f"  {frame.window:>4} {isum['n_clusters']:>4} "
              f"{isum['max_size']:>4} "
              f"{isum['max_relaxed_lifespan']:>4} "
              f"{isum['max_density_ratio']:>5.2f} "
              f"{isum['identity_drift']:>4} "
              f"{cur_restore:>7.4f} "
              f"{cur_pi:>5.2f} "
              f"{cc.get('proximity_restored',0):>4} "
              f"{cc.get('heat_events',0):>4} "
              f"{cc.get('capture_total',0):>5.1f} "
              f"{vs.get('gen_births',0):>4} "
              f"{hs.get('snapped',0):>4} "
              f"{vs.get('mean_V',0):>5.3f} "
              f"{frame.alive_links:>5} "
              f"{frame.milestone:>1} {sec:>4.0f}")

    f.close()

    json_path = output_dir / f"{tag}_detail.json"
    detail = engine.island_tracker.detailed_report()
    detail["meta"] = {
        "version": "v5.0",
        "seed": seed, "n_windows": n_windows,
        "window_steps": window_steps,
        "history_enabled": bool(encap_params.history_enabled),
        "void_enabled": bool(encap_params.void_enabled),
        "circulation_enabled": bool(encap_params.circulation_enabled),
        "final_restore": cur_restore,
        "final_inert": cur_inert,
        "final_alive_links": frame.alive_links,
        "max_milestone": max_ms,
        "max_relaxed_lifespan": isum["max_relaxed_lifespan"],
        "max_cluster_size": max(
            int(fr.max_cluster_size) for fr in engine.frames),
    }
    detail["drift_trajectory"] = engine.drift_trajectory
    detail["final_history_summary"] = engine.link_history.summary()
    detail["final_void_summary"] = {
        "mean_V": float(np.mean(engine.void_field)),
        "max_V": float(np.max(engine.void_field)),
        "active_nodes": int(np.sum(engine.void_field > 0.01)),
    }
    detail["final_circulation_summary"] = engine.circulation_stats
    with open(json_path, "w") as jf:
        json.dump(detail, jf, indent=2, default=str)

    print(f"\n  {'='*60}")
    print(f"  SUMMARY (seed={seed})")
    print(f"  {'='*60}")
    hsum = engine.link_history.summary()
    print(f"  Final restore: {cur_restore:.6f}  "
          f"inert: {cur_inert:.6f}")
    print(f"  Max lifespan: {isum['max_relaxed_lifespan']}  "
          f"Max size: {max(int(fr.max_cluster_size) for fr in engine.frames)}")
    print(f"  History: mature={hsum['mature_links']} "
          f"rigid={hsum['rigid_links']} brittle={hsum['brittle_links']}")
    print(f"  Void: mean_V={float(np.mean(engine.void_field)):.4f} "
          f"max_V={float(np.max(engine.void_field)):.4f} "
          f"active={int(np.sum(engine.void_field > 0.01))}")
    print(f"  Circulation: Π={engine.current_pi:.4f} "
          f"heat_total={cc.get('heat_total',0):.4f} "
          f"capture_total={cc.get('capture_total',0):.4f}")
    print(f"  Final links: {frame.alive_links}  Max milestone: {max_ms}")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}\n")


def aggregate(output_dir):
    output_dir = Path(output_dir)
    json_files = sorted(output_dir.glob("v50_*_detail.json"))
    if not json_files:
        print(f"  No v5.0 JSON files in {output_dir}")
        return
    print(f"\n  {'='*80}")
    print(f"  ESDE v5.0 — Aggregate ({len(json_files)} runs)")
    print(f"  {'='*80}")
    print(f"\n  {'seed':>6} {'rLife':>5} {'mxSz':>5} {'links':>5} "
          f"{'matr':>5} {'brit':>5} {'maxV':>5} {'Π':>5} {'mxM':>3}")
    print(f"  {'-'*55}")
    for jf in json_files:
        with open(jf) as fh:
            d = json.load(fh)
        m = d["meta"]
        h = d.get("final_history_summary", {})
        v = d.get("final_void_summary", {})
        c = d.get("final_circulation_summary", {})
        pi_val = c.get("pi_tension_snap", 0) + c.get(
            "pi_tension_entropy", 0) + c.get("pi_tension_energy", 0)
        print(f"  {m['seed']:>6} {m['max_relaxed_lifespan']:>5} "
              f"{m['max_cluster_size']:>5} {m['final_alive_links']:>5} "
              f"{h.get('mature_links',0):>5} {h.get('brittle_links',0):>5} "
              f"{v.get('max_V',0):>5.2f} {pi_val:>5.3f} "
              f"{m.get('max_milestone',0):>3}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="ESDE v5.0 Circulation Dynamics")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--windows", type=int, default=200)
    parser.add_argument("--window-steps", type=int, default=V50_WINDOW)
    parser.add_argument("--output", type=str, default="calibration_v50")
    parser.add_argument("--no-history", action="store_true")
    parser.add_argument("--no-void", action="store_true")
    parser.add_argument("--no-circulation", action="store_true")
    parser.add_argument("--no-drift", action="store_true")
    parser.add_argument("--alpha-min", type=float, default=0.0001)
    parser.add_argument("--alpha-beta", type=float, default=0.01)
    parser.add_argument("--drift-interval", type=int, default=3)
    parser.add_argument("--init-restore", type=float, default=0.5)
    parser.add_argument("--init-inert", type=float, default=0.02)
    parser.add_argument("--cooling-strength", type=float, default=1.0)
    parser.add_argument("--no-cooling", action="store_true")
    parser.add_argument("--no-z-coupling", action="store_true")
    parser.add_argument("--z-hetero-dampen", type=float, default=0.3)
    parser.add_argument("--jaccard-thr", type=float, default=0.3)
    parser.add_argument("--whirlpool-hops", type=int, default=2)
    parser.add_argument("--density-threshold", type=float, default=1.5)
    parser.add_argument("--persistence", type=int, default=3)
    parser.add_argument("--aggregate", action="store_true")
    args = parser.parse_args()

    if args.aggregate:
        aggregate(args.output)
        return

    params = V50EncapsulationParams(
        ratio_threshold=args.density_threshold,
        min_persistence=args.persistence,
        whirlpool_hops=args.whirlpool_hops,
        jaccard_threshold=args.jaccard_thr,
        cooling_strength=args.cooling_strength,
        cooling_enabled=not args.no_cooling,
        z_coupling_enabled=not args.no_z_coupling,
        z_decay_compound_restore=args.init_restore,
        z_decay_inert_penalty=args.init_inert,
        z_phase_hetero_dampen=args.z_hetero_dampen,
        alpha_min=args.alpha_min,
        alpha_beta=args.alpha_beta,
        drift_interval=args.drift_interval,
        drift_enabled=not args.no_drift,
        history_enabled=not args.no_history,
        void_enabled=not args.no_void,
        circulation_enabled=not args.no_circulation,
    )

    run(seed=args.seed, n_windows=args.windows,
        window_steps=args.window_steps, output_dir=args.output,
        encap_params=params)


if __name__ == "__main__":
    main()
