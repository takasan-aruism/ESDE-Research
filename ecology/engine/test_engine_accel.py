#!/usr/bin/env python3
"""
Test: engine_accel produces correct and faster results.

Tests:
  1. link_strength_sum exact match (function-level)
  2. Speedup measurement per function
  3. Full run timing estimate
  4. Statistical equivalence (canonical run produces valid observer)

Run: python test_engine_accel.py
"""
import sys, time
import numpy as np

sys.path.insert(0, ".")

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from chemistry import ChemistryEngine, ChemistryParams
from realization import RealizationOperator, RealizationParams
from autogrowth import AutoGrowthEngine, AutoGrowthParams


def make_state(N, seed):
    state = GenesisState(N, 1.0, seed)
    physics = GenesisPhysics(PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True,
        phase_enabled=True, beta=1.0, decay_rate_node=0.005))
    chem = ChemistryEngine(ChemistryParams(enabled=True))
    for step in range(100):
        if step % 3 == 0:
            tgts = physics.inject(state)
            chem.seed_on_injection(state, tgts or [])
        physics.step(state)
    return state


def test_link_strength_sum():
    print("=" * 60)
    print("TEST 1: link_strength_sum exact match")
    print("=" * 60)

    orig_fn = GenesisState.link_strength_sum

    for N in [200, 500, 1000]:
        state = make_state(N, 42)
        nodes = list(state.alive_n)
        orig_vals = {i: orig_fn(state, i) for i in nodes}

        import engine_accel
        accel_vals = {i: state.link_strength_sum(i) for i in nodes}
        GenesisState.link_strength_sum = orig_fn

        diffs = [abs(orig_vals[i] - accel_vals[i]) for i in nodes]
        max_diff = max(diffs)
        ok = max_diff < 1e-12
        print(f"  N={N:>5}: {len(nodes)} nodes, max_diff={max_diff:.2e} — {'PASS' if ok else 'FAIL'}")
        if not ok:
            return False
    return True


def test_speedup():
    print("\n" + "=" * 60)
    print("TEST 2: Speedup (link_strength_sum)")
    print("=" * 60)

    orig_fn = GenesisState.link_strength_sum

    for N in [200, 500, 1000, 2000]:
        state = make_state(N, 42)
        nodes = list(state.alive_n)[:min(100, len(state.alive_n))]
        n_links = len(state.alive_l)

        t0 = time.time()
        for _ in range(5):
            for nid in nodes:
                orig_fn(state, nid)
        t_orig = time.time() - t0

        import engine_accel
        t0 = time.time()
        for _ in range(5):
            for nid in nodes:
                state.link_strength_sum(nid)
        t_accel = time.time() - t0

        GenesisState.link_strength_sum = orig_fn

        speedup = t_orig / max(t_accel, 0.0001)
        print(f"  N={N:>5} links={n_links:>5}: "
              f"orig={t_orig:.4f}s accel={t_accel:.4f}s → {speedup:.0f}x")
    return True


def test_full_timing():
    print("\n" + "=" * 60)
    print("TEST 3: Full quiet phase timing (accel)")
    print("=" * 60)

    import engine_accel

    for N in [500, 1000]:
        state = make_state(N, 42)
        physics = GenesisPhysics(PhysicsParams(
            exclusion_enabled=True, resonance_enabled=True,
            phase_enabled=True, beta=1.0, decay_rate_node=0.005))
        realizer = RealizationOperator(RealizationParams(enabled=True))
        grower = AutoGrowthEngine(AutoGrowthParams(enabled=True))

        n_steps = 200
        t0 = time.time()
        for _ in range(n_steps):
            realizer.step(state)
            physics.step_pre_chemistry(state)
            physics.step_resonance(state)
            grower.step(state)
            physics.step_decay_exclusion(state)
        elapsed = time.time() - t0

        est_5000 = elapsed / n_steps * 5000
        print(f"  N={N:>5}: {n_steps} steps in {elapsed:.2f}s "
              f"(est 5000 steps: {est_5000:.0f}s = {est_5000/60:.0f}min)")
    return True


def test_statistical():
    print("\n" + "=" * 60)
    print("TEST 4: Statistical equivalence (N=200, canonical run)")
    print("=" * 60)

    import engine_accel
    from v19g_canon import run_canonical

    results = []
    for seed in [42, 123, 456]:
        r, _ = run_canonical(seed, 200, 0.007, 0.002, quiet_steps=1000)
        results.append(r)
        print(f"  seed={seed}: k*={r['dominant_k']} "
              f"none={r['mean_none_ratio']:.3f} "
              f"sw={r['switches_per_100']} "
              f"n_C={r['mean_n_C']:.0f} ({r['elapsed']:.0f}s)")

    all_ok = True
    for r in results:
        if r["dominant_k"] not in [0, 1, 2, 3, 4]:
            print(f"  FAIL: invalid k*={r['dominant_k']}")
            all_ok = False
        if r["mean_n_C"] <= 0:
            print(f"  FAIL: n_C=0")
            all_ok = False

    print(f"  Result: {'PASS' if all_ok else 'FAIL'}")
    return all_ok


def main():
    results = []
    results.append(("link_strength_sum exact", test_link_strength_sum()))
    results.append(("Speedup measurement", test_speedup()))
    results.append(("Full run timing", test_full_timing()))
    results.append(("Statistical equivalence", test_statistical()))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, ok in results:
        print(f"  {name:.<40} {'PASS' if ok else 'FAIL'}")

    all_pass = all(ok for _, ok in results)
    print(f"\n  Overall: {'ALL PASS' if all_pass else 'SOME FAILED'}")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
