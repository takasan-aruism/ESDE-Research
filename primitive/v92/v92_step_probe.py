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
                   local_amplitude=0.3, gamma=0.1):
    """Run with step-level instrumentation within detail windows."""

    N = V82_N
    window_steps = V82_WINDOW  # 50

    encap_params = V82EncapsulationParams(
        stress_enabled=True, virtual_enabled=True)

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

    engine.run_injection()
    print(f"  Injection done. interval={feedback_interval} gamma={gamma}")

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

            for step in range(window_steps):
                # Record BEFORE physics step
                pre_theta_mean = float(np.mean(
                    [float(engine.state.theta[n]) for n in engine.state.alive_n]))
                pre_theta_std = float(np.std(
                    [float(engine.state.theta[n]) for n in engine.state.alive_n]))
                pre_links = len(engine.state.alive_l)

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
                })

            # End of detail window: run stress + observation + virtual.step
            # Stress
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
                isl_for_vl = {}
                for iid, info in isl_m.items():
                    isl_for_vl[iid] = info
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
    args = parser.parse_args()

    print(f"\n  ESDE v9.2 Step-Level Probe")
    print(f"  seed={args.seed} interval={args.feedback_interval} "
          f"gamma={args.gamma}")
    print(f"  windows={args.windows} detail_start={args.detail_start}\n")

    step_log, engine = run_step_probe(
        seed=args.seed,
        feedback_interval=args.feedback_interval,
        n_windows=args.windows,
        detail_start=args.detail_start,
        gamma=args.gamma)

    # Save
    outdir = Path(f"diag_v92_stepprobe_int{args.feedback_interval}")
    outdir.mkdir(parents=True, exist_ok=True)
    outpath = outdir / f"step_log_seed{args.seed}.json"
    with open(outpath, "w") as f:
        json.dump(step_log, f)

    print(f"\n  Step log: {len(step_log)} entries → {outpath}")

    # Quick summary
    if step_log:
        torque_steps = [s for s in step_log if s["torque_applied"] > 0]
        no_torque = [s for s in step_log if s["torque_applied"] == 0]
        print(f"\n  --- Quick Summary ---")
        print(f"  Steps with torque: {len(torque_steps)}")
        print(f"  Steps without:     {len(no_torque)}")
        if torque_steps:
            shifts = [abs(s["theta_shift"]) for s in torque_steps]
            print(f"  |theta_shift| at torque steps: "
                  f"mean={np.mean(shifts):.8f} max={max(shifts):.8f}")
        if no_torque:
            shifts = [abs(s["theta_shift"]) for s in no_torque]
            print(f"  |theta_shift| at non-torque:   "
                  f"mean={np.mean(shifts):.8f} max={max(shifts):.8f}")

        # Link change around torque
        if torque_steps:
            link_deltas = [s["post_torque_links"] - s["post_physics_links"]
                           for s in torque_steps]
            print(f"  Link change at torque: "
                  f"mean={np.mean(link_deltas):.2f} "
                  f"(torque doesn't directly change links)")


if __name__ == "__main__":
    main()
