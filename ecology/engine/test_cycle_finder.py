#!/usr/bin/env python3
"""
Test: C cycle finder produces identical output to Python version.

Run:  python test_cycle_finder.py

Tests:
  1. Small known graph (manual verification)
  2. Random graph (N=50, cross-check Python vs C)
  3. Larger graph (N=200, cross-check + timing)
  4. Edge cases (empty graph, no cycles, single triangle)
"""

import time
import sys
import numpy as np
from collections import defaultdict

from genesis_state import GenesisState

# Import C extension (will monkey-patch GenesisState)
try:
    from _cycle_finder import find_all_cycles_c
    HAS_C = True
except ImportError:
    HAS_C = False
    print("WARNING: C extension not built. Run 'python build_cycle_finder.py' first.")
    print("         Only Python tests will run.\n")

import cycle_finder  # loads the wrapper


def sort_cycles(cycle_dict):
    """Sort cycle lists for deterministic comparison."""
    return {k: sorted(tuple(c) for c in v) for k, v in cycle_dict.items()}


def build_adjacency(state):
    """Build flat adjacency arrays for C function."""
    n = state.n_nodes
    if state._nbr_dirty:
        state._rebuild_nbr()

    adj_flat = []
    adj_off = [0] * n
    adj_sz = [0] * n
    offset = 0
    for i in range(n):
        nbrs = state._nbr.get(i, [])
        adj_off[i] = offset
        adj_sz[i] = len(nbrs)
        adj_flat.extend(nbrs)
        offset += len(nbrs)
    return adj_flat, adj_off, adj_sz


def run_python(state, max_length=5):
    """Run the original Python find_all_cycles."""
    return state._python_find_all_cycles(max_length)


def run_c(state, max_length=5):
    """Run the C find_all_cycles."""
    adj_flat, adj_off, adj_sz = build_adjacency(state)
    edges = list(state.alive_l)
    return find_all_cycles_c(adj_flat, adj_off, adj_sz,
                              edges, state.n_nodes, max_length)


def compare(py_result, c_result, label=""):
    """Compare two cycle dicts. Returns True if identical."""
    py_sorted = sort_cycles(py_result)
    c_sorted = sort_cycles(c_result)

    all_keys = sorted(set(py_sorted.keys()) | set(c_sorted.keys()))
    ok = True
    for k in all_keys:
        py_set = set(py_sorted.get(k, []))
        c_set = set(c_sorted.get(k, []))
        if py_set != c_set:
            print(f"  MISMATCH at k={k}: Python={len(py_set)} C={len(c_set)}")
            only_py = py_set - c_set
            only_c = c_set - py_set
            if only_py:
                print(f"    Only in Python: {list(only_py)[:5]}")
            if only_c:
                print(f"    Only in C:      {list(only_c)[:5]}")
            ok = False
        else:
            print(f"  k={k}: {len(py_set)} cycles — MATCH")
    return ok


# ================================================================
# TEST 1: Known small graph (triangle + square)
# ================================================================
def test_known_graph():
    print("=" * 60)
    print("TEST 1: Known graph (triangle 0-1-2, square 2-3-4-5)")
    print("=" * 60)

    state = GenesisState(10, seed=42)
    # Triangle: 0-1, 1-2, 0-2
    state.add_link(0, 1, 0.5)
    state.add_link(1, 2, 0.5)
    state.add_link(0, 2, 0.5)
    # Square: 2-3, 3-4, 4-5, 5-2
    state.add_link(2, 3, 0.5)
    state.add_link(3, 4, 0.5)
    state.add_link(4, 5, 0.5)
    state.add_link(5, 2, 0.5)
    state.enforce_extinction()

    py = run_python(state)
    print(f"  Python: {', '.join(f'k={k}: {len(v)}' for k, v in sorted(py.items()))}")

    if HAS_C:
        c = run_c(state)
        print(f"  C:      {', '.join(f'k={k}: {len(v)}' for k, v in sorted(c.items()))}")
        ok = compare(py, c)
        print(f"  Result: {'PASS' if ok else 'FAIL'}")
        return ok
    else:
        print("  (C not available, skipping comparison)")
        return True


# ================================================================
# TEST 2: Random graph (N=50)
# ================================================================
def test_random_small():
    print("\n" + "=" * 60)
    print("TEST 2: Random graph N=50")
    print("=" * 60)

    state = GenesisState(50, seed=123)
    rng = np.random.RandomState(123)

    # Add ~80 random links
    for _ in range(80):
        i, j = rng.randint(0, 50, 2)
        if i != j:
            state.add_link(int(i), int(j), rng.uniform(0.1, 0.5))
    state.enforce_extinction()
    print(f"  Links: {len(state.alive_l)}")

    t0 = time.time()
    py = run_python(state)
    t_py = time.time() - t0

    total_py = sum(len(v) for v in py.values())
    print(f"  Python: {total_py} cycles ({t_py:.4f}s)")

    if HAS_C:
        t0 = time.time()
        c = run_c(state)
        t_c = time.time() - t0
        total_c = sum(len(v) for v in c.values())
        print(f"  C:      {total_c} cycles ({t_c:.4f}s)")
        if t_py > 0.001:
            print(f"  Speedup: {t_py/t_c:.1f}x")

        ok = compare(py, c)
        print(f"  Result: {'PASS' if ok else 'FAIL'}")
        return ok
    return True


# ================================================================
# TEST 3: Larger graph (N=200)
# ================================================================
def test_random_medium():
    print("\n" + "=" * 60)
    print("TEST 3: Random graph N=200 (timing focus)")
    print("=" * 60)

    state = GenesisState(200, seed=456)
    rng = np.random.RandomState(456)

    for _ in range(400):
        i, j = rng.randint(0, 200, 2)
        if i != j:
            state.add_link(int(i), int(j), rng.uniform(0.1, 0.5))
    state.enforce_extinction()
    print(f"  Links: {len(state.alive_l)}")

    t0 = time.time()
    py = run_python(state)
    t_py = time.time() - t0
    total_py = sum(len(v) for v in py.values())
    print(f"  Python: {total_py} cycles ({t_py:.3f}s)")

    if HAS_C:
        t0 = time.time()
        c = run_c(state)
        t_c = time.time() - t0
        total_c = sum(len(v) for v in c.values())
        print(f"  C:      {total_c} cycles ({t_c:.4f}s)")
        if t_c > 0:
            print(f"  Speedup: {t_py/t_c:.1f}x")

        ok = compare(py, c)
        print(f"  Result: {'PASS' if ok else 'FAIL'}")
        return ok
    return True


# ================================================================
# TEST 4: Edge cases
# ================================================================
def test_edge_cases():
    print("\n" + "=" * 60)
    print("TEST 4: Edge cases")
    print("=" * 60)

    all_ok = True

    # 4a: Empty graph
    state = GenesisState(10, seed=1)
    state.enforce_extinction()
    py = run_python(state)
    total = sum(len(v) for v in py.values())
    ok = (total == 0)
    print(f"  4a Empty graph: {total} cycles — {'PASS' if ok else 'FAIL'}")
    if HAS_C:
        c = run_c(state)
        ok2 = sum(len(v) for v in c.values()) == 0
        print(f"      C: {'PASS' if ok2 else 'FAIL'}")
        all_ok &= ok2
    all_ok &= ok

    # 4b: Chain (no cycles)
    state = GenesisState(5, seed=2)
    state.add_link(0, 1, 0.5)
    state.add_link(1, 2, 0.5)
    state.add_link(2, 3, 0.5)
    state.enforce_extinction()
    py = run_python(state)
    total = sum(len(v) for v in py.values())
    ok = (total == 0)
    print(f"  4b Chain (no cycles): {total} cycles — {'PASS' if ok else 'FAIL'}")
    if HAS_C:
        c = run_c(state)
        ok2 = sum(len(v) for v in c.values()) == 0
        print(f"      C: {'PASS' if ok2 else 'FAIL'}")
        all_ok &= ok2
    all_ok &= ok

    # 4c: Single triangle
    state = GenesisState(3, seed=3)
    state.add_link(0, 1, 0.5)
    state.add_link(1, 2, 0.5)
    state.add_link(0, 2, 0.5)
    state.enforce_extinction()
    py = run_python(state)
    py3 = len(py.get(3, []))
    print(f"  4c Single triangle: k=3 has {py3} cycles")
    if HAS_C:
        c = run_c(state)
        ok2 = compare(py, c, "triangle")
        all_ok &= ok2

    # 4d: Complete graph K5 (lots of cycles)
    state = GenesisState(5, seed=4)
    for i in range(5):
        for j in range(i+1, 5):
            state.add_link(i, j, 0.5)
    state.enforce_extinction()
    py = run_python(state)
    total = sum(len(v) for v in py.values())
    print(f"  4d K5 complete: {total} total cycles "
          f"({', '.join(f'k={k}:{len(v)}' for k, v in sorted(py.items()))})")
    if HAS_C:
        c = run_c(state)
        ok2 = compare(py, c, "K5")
        all_ok &= ok2

    return all_ok


# ================================================================
# TEST 5: Simulated Genesis run (realistic topology)
# ================================================================
def test_genesis_realistic():
    print("\n" + "=" * 60)
    print("TEST 5: Simulated Genesis topology (N=200, injection+quiet)")
    print("=" * 60)

    from genesis_physics import GenesisPhysics, PhysicsParams
    from chemistry import ChemistryEngine, ChemistryParams
    from realization import RealizationOperator, RealizationParams
    from autogrowth import AutoGrowthEngine, AutoGrowthParams

    state = GenesisState(200, 1.0, seed=42)
    physics = GenesisPhysics(PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True,
        phase_enabled=True, beta=1.0, decay_rate_node=0.005))
    chem = ChemistryEngine(ChemistryParams(enabled=True))
    realizer = RealizationOperator(RealizationParams(enabled=True))
    grower = AutoGrowthEngine(AutoGrowthParams(enabled=True))

    # Injection (use Python cycles)
    for step in range(100):
        if step % 3 == 0:
            tgts = physics.inject(state)
            chem.seed_on_injection(state, tgts or [])
        physics.step_pre_chemistry(state)
        chem.step(state)
        physics.step_resonance(state)
        grower.step(state)
        physics.step_decay_exclusion(state)

    # Short quiet
    for step in range(200):
        realizer.step(state)
        physics.step_pre_chemistry(state)
        chem.step(state)
        physics.step_resonance(state)
        grower.step(state)
        physics.step_decay_exclusion(state)

    print(f"  Links: {len(state.alive_l)}, Nodes: {len(state.alive_n)}")

    t0 = time.time()
    py = run_python(state)
    t_py = time.time() - t0
    total_py = sum(len(v) for v in py.values())
    print(f"  Python: {total_py} cycles ({t_py:.4f}s)")

    if HAS_C:
        t0 = time.time()
        c = run_c(state)
        t_c = time.time() - t0
        total_c = sum(len(v) for v in c.values())
        print(f"  C:      {total_c} cycles ({t_c:.4f}s)")
        if t_c > 0:
            print(f"  Speedup: {t_py/max(t_c, 0.0001):.1f}x")

        ok = compare(py, c)
        print(f"  Result: {'PASS' if ok else 'FAIL'}")
        return ok
    return True


# ================================================================
# MAIN
# ================================================================
def main():
    results = []

    results.append(("Known graph", test_known_graph()))
    results.append(("Random N=50", test_random_small()))
    results.append(("Random N=200", test_random_medium()))
    results.append(("Edge cases", test_edge_cases()))
    results.append(("Genesis realistic", test_genesis_realistic()))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_pass = True
    for name, ok in results:
        status = "PASS" if ok else "FAIL"
        print(f"  {name:.<40} {status}")
        all_pass &= ok

    print(f"\n  Overall: {'ALL PASS' if all_pass else 'SOME FAILED'}")
    if HAS_C and all_pass:
        print("  C extension is verified — safe to use.")
    elif not HAS_C:
        print("  C extension not tested (not built).")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
