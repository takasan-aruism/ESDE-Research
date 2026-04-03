#!/usr/bin/env python3
"""
ESDE v9.2 — Step-Level Instrumentation
========================================
Record per-step θ distribution and alive_links within windows.
See whether torque effect is visible at step granularity
and whether stress equilibrium absorbs it.

Lightweight: 1 seed, 60 windows, detailed logging on w50-59.
3 conditions: interval=1, 5, 10.

USAGE
-----
  python v92_step_probe.py --seed 42 --feedback-interval 10
"""

import sys, json, time, argparse, math
import numpy as np
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_V82_DIR = _REPO_ROOT / "autonomy" / "v82"
_V43_DIR = _V82_DIR.parent / "v43"
_V41_DIR = _V82_DIR.parent / "v41"
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_SCRIPT_DIR), str(_V82_DIR), str(_V43_DIR), str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from esde_v82_engine import V82Engine, V82EncapsulationParams, V82_WINDOW, V82_N
from v19g_canon import BASE_PARAMS
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9


def run_step_probe(seed, feedback_interval, n_windows=60, detail_start=50,
                   local_amplitude=0.3, gamma=0.1, semantic_gravity=True,
                   torque_order="random", deviation_enabled=True,
                   window_steps=None, stress_enabled=True):
    """Run with step-level instrumentation within detail windows."""

    N = V82_N
    if window_steps is None:
        window_steps = V82_WINDOW  # 50

    encap_params = V82EncapsulationParams(
        stress_enabled=stress_enabled, virtual_enabled=True)

    engine = V82Engine(seed=seed, N=N, encap_params=encap_params)

    # Local wave monkey-patch
    if local_amplitude > 0:
        import types
        side = int(math.ceil(math.sqrt(N)))
        local_multiplier = np.ones(N)
        for i in range(N):
            x = i % side
            local_multiplier[i] = 1.0 + local_amplitude * math.sin(
                2 * math.pi * x / side)

        original_decay = engine.physics._decay.__func__

        def patched_decay(self_phys, state):
            original_decay(self_phys, state)
            for lk in list(state.alive_l):
                n1, n2 = lk
                mult = (local_multiplier[n1] + local_multiplier[n2]) / 2.0
                if mult != 1.0:
                    s = state.S.get(lk, 0.0)
                    if s > 0:
                        extra_decay = s * (mult - 1.0) * 0.01
                        state.S[lk] = max(0.0, s - extra_decay)

        engine.physics._decay = types.MethodType(patched_decay, engine.physics)

    # v9 VirtualLayer
    engine.virtual = VirtualLayerV9(
        feedback_gamma=gamma,
        feedback_clamp=(0.8, 1.2),
    )
    engine.virtual.semantic_gravity_enabled = semantic_gravity
    engine.virtual.torque_order = torque_order
    engine.virtual.deviation_enabled = deviation_enabled

    engine.run_injection()
    print(f"  Injection done. interval={feedback_interval} gamma={gamma} "
          f"gravity={'ON' if semantic_gravity else 'OFF'} order={torque_order} "
          f"deviation={'ON' if deviation_enabled else 'OFF'}")

    # Storage for step-level data
    step_log = []  # per-step within detail windows

    for w in range(n_windows):
        is_detail = (w >= detail_start)

        if not is_detail:
            # Normal window
            engine.step_window(steps=window_steps)
        else:
            # Detail window: step through manually
            bg_prob = BASE_PARAMS["background_injection_prob"]
            p = engine.island_tracker.params
            steps_since_torque = 99  # large initial value (no prior torque)

            for step in range(window_steps):
                # Record BEFORE physics step
                pre_theta_mean = float(np.mean(
                    [float(engine.state.theta[n]) for n in engine.state.alive_n]))
                pre_theta_std = float(np.std(
                    [float(engine.state.theta[n]) for n in engine.state.alive_n]))
                pre_links = len(engine.state.alive_l)
                pre_link_set = set(engine.state.alive_l)
                pre_S_map = {lk: float(engine.state.S.get(lk, 0))
                             for lk in engine.state.alive_l}
                pre_R_map = {lk: float(engine.state.R.get(lk, 0))
                             for lk in engine.state.alive_l}

                # Physics step (same as engine.step_window inner loop)
                engine.realizer.step(engine.state)
                engine.physics.step_pre_chemistry(engine.state)
                engine.chem.step(engine.state)
                engine.physics.step_resonance(engine.state)

                # g_scores
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

                # Background seeding (simplified)
                al = list(engine.state.alive_n)
                na = len(al)
                if na > 0:
                    aa = np.array(al)
                    mk = engine.state.rng.random(na) < bg_prob
                    triggered = np.where(mk)[0]
                    pd = np.ones(na) / na
                    for idx in triggered:
                        t_node = int(engine.state.rng.choice(aa, p=pd))
                        if t_node in engine.state.alive_n:
                            engine.state.E[t_node] = min(
                                1.0, engine.state.E[t_node] + 0.3)

                # Record AFTER physics, BEFORE torque
                post_links = len(engine.state.alive_l)
                post_physics_link_set = set(engine.state.alive_l)

                # Link quality snapshot (before torque)
                S_vals = [float(engine.state.S.get(lk, 0)) for lk in engine.state.alive_l]
                R_plus_count = sum(1 for lk in engine.state.alive_l
                                  if engine.state.R.get(lk, 0.0) > 0)

                # Links lost during this physics step
                lost_links = pre_link_set - post_physics_link_set
                gained_links = post_physics_link_set - pre_link_set
                lost_S = [float(pre_S_map.get(lk, 0)) for lk in lost_links]
                lost_R_plus = sum(1 for lk in lost_links
                                 if pre_R_map.get(lk, 0.0) > 0)

                # Apply torque at specified interval
                torque_applied = 0
                if feedback_interval > 0 and (step + 1) % feedback_interval == 0:
                    torque_applied = engine.virtual.apply_torque_only(
                        engine.state, engine.window_count,
                        substrate=engine.substrate)

                # Record AFTER torque
                post_torque_theta_mean = float(np.mean(
                    [float(engine.state.theta[n]) for n in engine.state.alive_n]))
                post_torque_theta_std = float(np.std(
                    [float(engine.state.theta[n]) for n in engine.state.alive_n]))
                post_torque_links = len(engine.state.alive_l)

                step_log.append({
                    "window": w,
                    "step": step,
                    "pre_theta_mean": round(pre_theta_mean, 6),
                    "pre_theta_std": round(pre_theta_std, 6),
                    "pre_links": pre_links,
                    "post_physics_links": post_links,
                    "torque_applied": torque_applied,
                    "post_torque_theta_mean": round(post_torque_theta_mean, 6),
                    "post_torque_theta_std": round(post_torque_theta_std, 6),
                    "post_torque_links": post_torque_links,
                    "theta_shift": round(post_torque_theta_mean - pre_theta_mean, 8),
                    "link_delta": post_torque_links - pre_links,
                    "steps_since_torque": steps_since_torque,
                    # Link quality (P4: what kind of links are lost?)
                    "n_lost": len(lost_links),
                    "n_gained": len(gained_links),
                    "mean_S_lost": round(np.mean(lost_S), 6) if lost_S else 0,
                    "mean_S_all": round(np.mean(S_vals), 6) if S_vals else 0,
                    "R_plus_count": R_plus_count,
                    "lost_R_plus": lost_R_plus,
                })

                # Track distance from last torque
                if torque_applied > 0:
                    steps_since_torque = 0
                else:
                    steps_since_torque += 1

            # End of detail window: run stress + observation + virtual.step
            # Stress (skip if disabled)
            if stress_enabled:
                current_links = len(engine.state.alive_l)
                if engine.link_ema is None:
                    engine.link_ema = float(current_links)
                tau = min(engine.window_count + 1, 20)
                alpha_ema = 2.0 / (tau + 1.0)
                engine.link_ema = (alpha_ema * current_links
                                   + (1 - alpha_ema) * engine.link_ema)
                stress_intensity = current_links / max(1.0, engine.link_ema)

                from esde_v82_engine import apply_stress_decay
                apply_stress_decay(engine.state, stress_intensity)

            # Island detection + virtual.step
            from esde_v82_engine import find_islands_sets
            isl_m = find_islands_sets(engine.state, 0.20)
            isum = engine.island_tracker.step(
                engine.state, engine.hardening,
                precomputed_islands=isl_m)
            engine.last_isum = isum

            engine.window_count += 1
            from esde_v43_engine import V43StateFrame
            f = V43StateFrame(
                window=engine.window_count,
                alive_nodes=len(engine.state.alive_n),
                alive_links=len(engine.state.alive_l),
                k_star=0, entropy=0.0, milestone=0)
            engine.frames.append(f)

            if p.virtual_enabled:
                # Convert list of frozensets to dict with .nodes attr
                class _Isl:
                    def __init__(self, nodes): self.nodes = nodes
                isl_for_vl = {i: _Isl(ns) for i, ns in enumerate(isl_m)}
                vs = engine.virtual.step(
                    engine.state, f.window,
                    islands=isl_for_vl,
                    substrate=engine.substrate)
                engine.virtual_stats = vs

        if w % 10 == 0 or is_detail:
            vl = engine.virtual_stats if hasattr(engine, 'virtual_stats') else {}
            print(f"  w={w:>3} links={len(engine.state.alive_l):>4} "
                  f"vLb={vl.get('labels_active', '?'):>3} "
                  f"M={vl.get('torque_multiplier', 1.0):.3f} "
                  f"{'[DETAIL]' if is_detail else ''}")

    return step_log, engine


def main():
    parser = argparse.ArgumentParser(
        description="ESDE v9.2 Step-Level Probe")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--feedback-interval", type=int, default=10,
                        help="Torque application interval in steps (1/5/10)")
    parser.add_argument("--gamma", type=float, default=0.1)
    parser.add_argument("--windows", type=int, default=60)
    parser.add_argument("--detail-start", type=int, default=50)
    parser.add_argument("--no-gravity", action="store_true",
                        help="Disable semantic gravity (label-external torque)")
    parser.add_argument("--torque-order", type=str, default="random",
                        choices=["random", "share", "age"],
                        help="Label processing order for sequential torque")
    parser.add_argument("--no-deviation", action="store_true",
                        help="Disable deviation detection (all gravity_factors=1.0)")
    parser.add_argument("--no-stress", action="store_true",
                        help="Disable stress equilibrium")
    parser.add_argument("--window-steps", type=int, default=50,
                        help="Steps per window (default=50)")
    args = parser.parse_args()

    grav_tag = "noG" if args.no_gravity else "G"
    dev_tag = "noD" if args.no_deviation else "D"
    stress_tag = "noS" if args.no_stress else "S"
    print(f"\n  ESDE v9.3 Step-Level Probe")
    print(f"  seed={args.seed} interval={args.feedback_interval} "
          f"gamma={args.gamma} gravity={'OFF' if args.no_gravity else 'ON'} "
          f"order={args.torque_order} deviation={'OFF' if args.no_deviation else 'ON'} "
          f"stress={'OFF' if args.no_stress else 'ON'} "
          f"steps/win={args.window_steps}")
    print(f"  windows={args.windows} detail_start={args.detail_start}\n")

    step_log, engine = run_step_probe(
        seed=args.seed,
        feedback_interval=args.feedback_interval,
        n_windows=args.windows,
        detail_start=args.detail_start,
        gamma=args.gamma,
        semantic_gravity=not args.no_gravity,
        torque_order=args.torque_order,
        deviation_enabled=not args.no_deviation,
        window_steps=args.window_steps,
        stress_enabled=not args.no_stress)

    # Save
    outdir = Path(f"diag_v93_stepprobe_s{args.window_steps}_int{args.feedback_interval}_{grav_tag}_{args.torque_order}_{dev_tag}_{stress_tag}")
    outdir.mkdir(parents=True, exist_ok=True)
    outpath = outdir / f"step_log_seed{args.seed}.json"
    with open(outpath, "w") as f:
        json.dump(step_log, f)

    print(f"\n  Step log: {len(step_log)} entries → {outpath}")

    # Quick summary
    if step_log:
        print(f"\n  --- Quick Summary ---")
        print(f"  Total steps: {len(step_log)}")
        torque_steps = [s for s in step_log if s["torque_applied"] > 0]
        print(f"  Torque steps: {len(torque_steps)}")

        # GPT §5: Temporal decomposition
        # A = torque step (steps_since_torque == 0)
        # B = +1 step after torque
        # C = +2 to +3 steps after torque
        # D = +4 or more steps after torque
        classes = {
            "A_torque":    [s for s in step_log if s["steps_since_torque"] == 0],
            "B_after+1":   [s for s in step_log if s["steps_since_torque"] == 1],
            "C_after+2-3": [s for s in step_log if s["steps_since_torque"] in (2, 3)],
            "D_late_drift": [s for s in step_log if s["steps_since_torque"] >= 4],
        }

        print(f"\n  --- Temporal Decomposition (GPT §5) ---")
        print(f"  {'class':>15} {'n':>5} {'|shift|':>10} {'link_delta':>11} {'theta_std_chg':>14}")
        print(f"  {'-'*58}")
        for cname, entries in classes.items():
            if not entries:
                print(f"  {cname:>15} {'—':>5}")
                continue
            shifts = [abs(e["theta_shift"]) for e in entries]
            ld = [e["link_delta"] for e in entries]
            std_chg = [e["post_torque_theta_std"] - e["pre_theta_std"] for e in entries]
            print(f"  {cname:>15} {len(entries):>5} "
                  f"{np.mean(shifts):>10.8f} "
                  f"{np.mean(ld):>+10.2f} "
                  f"{np.mean(std_chg):>+13.8f}")

        # GPT P4: Link quality by temporal class
        print(f"\n  --- Link Quality by Temporal Class (P4: what dies?) ---")
        print(f"  {'class':>15} {'n_lost':>7} {'n_gained':>8} {'S_lost':>8} {'S_all':>8} "
              f"{'R+_count':>9} {'R+_lost':>8}")
        print(f"  {'-'*66}")
        for cname, entries in classes.items():
            if not entries:
                print(f"  {cname:>15} {'—':>7}")
                continue
            nl = [e["n_lost"] for e in entries]
            ng = [e["n_gained"] for e in entries]
            sl = [e["mean_S_lost"] for e in entries if e["mean_S_lost"] > 0]
            sa = [e["mean_S_all"] for e in entries]
            rp = [e["R_plus_count"] for e in entries]
            rl = [e["lost_R_plus"] for e in entries]
            print(f"  {cname:>15} {np.mean(nl):>7.1f} {np.mean(ng):>+7.1f} "
                  f"{np.mean(sl):>8.4f} " if sl else f"  {cname:>15} {np.mean(nl):>7.1f} {np.mean(ng):>+7.1f} {'—':>8} ",
                  end="")
            print(f"{np.mean(sa):>8.4f} {np.mean(rp):>9.0f} {np.mean(rl):>8.2f}")

        # P2: Per-cycle net effect
        if args.feedback_interval < 50 and args.feedback_interval >= 1:
            cycle_len = args.feedback_interval
            by_pos = {}
            for s in step_log:
                pos = s["steps_since_torque"]
                if pos > 90:
                    continue
                if pos not in by_pos:
                    by_pos[pos] = {"shifts": [], "link_deltas": [],
                                   "n_lost": [], "mean_S_lost": [],
                                   "lost_R_plus": []}
                by_pos[pos]["shifts"].append(abs(s["theta_shift"]))
                by_pos[pos]["link_deltas"].append(s["link_delta"])
                by_pos[pos]["n_lost"].append(s["n_lost"])
                by_pos[pos]["mean_S_lost"].append(s["mean_S_lost"])
                by_pos[pos]["lost_R_plus"].append(s["lost_R_plus"])

            print(f"\n  --- Per-Cycle Profile (interval={cycle_len}) ---")
            print(f"  {'pos':>5} {'n':>5} {'|shift|':>10} {'link_d':>7} "
                  f"{'n_lost':>7} {'S_lost':>8} {'R+_lost':>8}")
            print(f"  {'-'*52}")
            net_link = 0
            for pos in sorted(by_pos.keys()):
                if pos >= cycle_len:
                    break
                d = by_pos[pos]
                ld = np.mean(d['link_deltas'])
                net_link += ld
                sl_vals = [v for v in d['mean_S_lost'] if v > 0]
                print(f"  {pos:>5} {len(d['shifts']):>5} "
                      f"{np.mean(d['shifts']):>10.8f} "
                      f"{ld:>+6.2f} "
                      f"{np.mean(d['n_lost']):>7.1f} "
                      f"{np.mean(sl_vals):>8.4f} " if sl_vals else f"  {pos:>5} {len(d['shifts']):>5} {np.mean(d['shifts']):>10.8f} {ld:>+6.2f} {np.mean(d['n_lost']):>7.1f} {'—':>8} ",
                      end="")
                print(f"{np.mean(d['lost_R_plus']):>8.2f}")
            print(f"\n  Cycle NET link_delta: {net_link:>+.2f}")
            print(f"  (negative = torque cycle net destroys links)")
            print(f"  (positive = torque cycle net builds links)")


if __name__ == "__main__":
    main()
