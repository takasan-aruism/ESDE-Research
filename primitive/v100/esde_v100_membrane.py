#!/usr/bin/env python3
"""
ESDE v10.0a — Synaptic Membrane Coupling Sanity Check
=======================================================
Two independent ecologies (A: 0-4999, B: 5000-9999) on a 1-State
N=10,000 universe. Mature independently, then connect via Sparse
Membrane (20 pairs, S_init=0.05). Monitor coupling.

Conditions (fixed by design memo):
  - 1-State, N=10000
  - Horizontal grid connection (A right edge ↔ B left edge)
  - 20 sparse membrane pairs
  - S_init = 0.05 for membrane links
  - Mature-then-Connect (案C)
  - 500 step/window, Stress OFF, age order, deviation ON
  - Two independent VirtualLayers (island claim filtered by seed range)

USAGE:
  python esde_v100_membrane.py --seed 42
"""

import sys, math, time, json, argparse
import numpy as np
from pathlib import Path
from collections import defaultdict

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_V82_DIR = _REPO_ROOT / "autonomy" / "v82"
_V43_DIR = _REPO_ROOT / "cognition" / "semantic_injection" / "v4_pipeline" / "v43"
_V41_DIR = _V43_DIR.parent / "v41"
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_SCRIPT_DIR), str(_V82_DIR), str(_V43_DIR), str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from esde_v82_engine import V82Engine, V82EncapsulationParams, V82_N
from v19g_canon import BASE_PARAMS
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9

# ================================================================
# CONSTANTS
# ================================================================
N_PER_SEED = 5000
N_TOTAL = N_PER_SEED * 2
SIDE = int(math.ceil(math.sqrt(N_PER_SEED)))  # 71
MEMBRANE_PAIRS = 20
MEMBRANE_S_INIT = 0.05
MATURATION_WINDOWS = 20
COUPLED_WINDOWS = 10
WINDOW_STEPS = 500


# ================================================================
# DUAL SUBSTRATE
# ================================================================
def build_dual_substrate(n_per_seed=N_PER_SEED, membrane_pairs=MEMBRANE_PAIRS):
    """Build two independent 71×71 grids + sparse membrane connections.

    Grid A: nodes 0 to n_per_seed-1 (71×71, row-major)
    Grid B: nodes n_per_seed to 2*n_per_seed-1 (71×71, row-major)
    Membrane: A's right edge (col=SIDE-1) ↔ B's left edge (col=0)
    """
    side = int(math.ceil(math.sqrt(n_per_seed)))
    total = n_per_seed * 2
    adj = {}

    # Grid A
    for i in range(n_per_seed):
        r, c = i // side, i % side
        nbs = []
        if r > 0:
            nb = (r - 1) * side + c
            if nb < n_per_seed: nbs.append(nb)
        if r < side - 1:
            nb = (r + 1) * side + c
            if nb < n_per_seed: nbs.append(nb)
        if c > 0:
            nbs.append(r * side + (c - 1))
        if c < side - 1:
            nbs.append(r * side + (c + 1))
        adj[i] = nbs

    # Grid B (offset by n_per_seed)
    for i in range(n_per_seed):
        node_id = n_per_seed + i
        r, c = i // side, i % side
        nbs = []
        if r > 0:
            nb = n_per_seed + (r - 1) * side + c
            if nb < total: nbs.append(nb)
        if r < side - 1:
            nb = n_per_seed + (r + 1) * side + c
            if nb < total: nbs.append(nb)
        if c > 0:
            nbs.append(n_per_seed + r * side + (c - 1))
        if c < side - 1:
            nbs.append(n_per_seed + r * side + (c + 1))
        adj[node_id] = nbs

    # Membrane: A's right edge ↔ B's left edge (sparse, evenly spaced)
    a_right = [r * side + (side - 1) for r in range(side)]
    b_left = [n_per_seed + r * side for r in range(side)]

    if membrane_pairs >= side:
        pairs = list(zip(a_right, b_left))
    else:
        step = side / membrane_pairs
        indices = [int(i * step) for i in range(membrane_pairs)]
        pairs = [(a_right[i], b_left[i]) for i in indices]

    return adj, pairs


def activate_membrane(state, substrate, pairs, s_init=MEMBRANE_S_INIT):
    """Add membrane connections to substrate and create active links."""
    created = 0
    for a, b in pairs:
        # Add to substrate adjacency (bidirectional)
        if b not in substrate[a]:
            substrate[a].append(b)
        if a not in substrate[b]:
            substrate[b].append(a)

        # Create active link
        key = state.key(a, b)
        if key not in state.alive_l:
            state.alive_l[key] = True
            state.S[key] = s_init
            state.R[key] = 0.0
            created += 1

    return created


# ================================================================
# DUAL VIRTUAL LAYER (wrapper)
# ================================================================
class DualVirtualLayer:
    """Wraps two VirtualLayerV9 instances, one per seed.
    Filters islands by node range before delegating.
    Exposes merged stats for engine compatibility."""

    def __init__(self, vl_a, vl_b, n_per_seed=N_PER_SEED):
        self.vl_a = vl_a
        self.vl_b = vl_b
        self.n = n_per_seed
        # Expose attributes engine may access
        self.feedback_gamma = vl_a.feedback_gamma
        self.feedback_clamp = vl_a.feedback_clamp
        self.warmup_windows = vl_a.warmup_windows
        self.labels = {}  # merged view (read-only, for logging)
        self.macro_nodes = {}

    def _filter_islands(self, islands, lo, hi):
        """Split islands by node range. Cross-boundary islands get split."""
        if islands is None:
            return None
        filtered = []
        for isl in islands:
            if hasattr(isl, 'nodes'):
                # island_tracker island object
                subset = frozenset(n for n in isl.nodes if lo <= n < hi)
            else:
                # frozenset or set
                subset = frozenset(n for n in isl if lo <= n < hi)
            if len(subset) >= 2:
                filtered.append(subset)
        return filtered

    def step(self, state, window_count, islands=None, substrate=None):
        isl_a = self._filter_islands(islands, 0, self.n)
        isl_b = self._filter_islands(islands, self.n, self.n * 2)

        stats_a = self.vl_a.step(state, window_count,
                                  islands=isl_a, substrate=substrate)
        stats_b = self.vl_b.step(state, window_count,
                                  islands=isl_b, substrate=substrate)

        # Merge stats (sum numeric values)
        merged = {}
        for k in stats_a:
            va, vb = stats_a.get(k, 0), stats_b.get(k, 0)
            if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
                merged[k] = va + vb
            else:
                merged[k] = va
        # Keep individual counts for reporting
        merged["_a_labels"] = stats_a.get("labels_active", 0)
        merged["_b_labels"] = stats_b.get("labels_active", 0)

        self.labels = {**self.vl_a.labels, **self.vl_b.labels}
        return merged

    def apply_torque_only(self, state, window_count, substrate=None):
        ea = self.vl_a.apply_torque_only(state, window_count, substrate=substrate)
        eb = self.vl_b.apply_torque_only(state, window_count, substrate=substrate)
        return ea + eb

    def get(self, key, default=None):
        """For engine.virtual_stats compatibility (dict-like access)."""
        return default


# ================================================================
# MEMBRANE MONITOR
# ================================================================
def measure_membrane(state, pairs, prev_S=None):
    """Measure membrane link health and boundary activity."""
    alive = 0
    total_S = 0.0
    total_R = 0.0
    s_values = []

    for a, b in pairs:
        key = state.key(a, b)
        if key in state.alive_l:
            alive += 1
            s = state.S.get(key, 0.0)
            r = state.R.get(key, 0.0)
            total_S += s
            total_R += r
            s_values.append(s)

    # Boundary node theta stats
    a_nodes = [a for a, b in pairs]
    b_nodes = [b for a, b in pairs]
    a_thetas = [float(state.theta[n]) for n in a_nodes if n in state.alive_n]
    b_thetas = [float(state.theta[n]) for n in b_nodes if n in state.alive_n]

    # Phase difference across membrane
    phase_diffs = []
    for a, b in pairs:
        if a in state.alive_n and b in state.alive_n:
            d = abs(float(state.theta[a]) - float(state.theta[b]))
            if d > math.pi:
                d = 2 * math.pi - d
            phase_diffs.append(d)

    return {
        "alive": alive,
        "total": len(pairs),
        "survival_rate": alive / len(pairs) if pairs else 0,
        "mean_S": total_S / max(1, alive),
        "mean_R": total_R / max(1, alive),
        "mean_phase_diff": sum(phase_diffs) / max(1, len(phase_diffs)),
        "min_S": min(s_values) if s_values else 0,
        "max_S": max(s_values) if s_values else 0,
    }


# ================================================================
# MAIN
# ================================================================
def run(seed=42):
    print(f"\n{'='*65}")
    print(f"  ESDE v10.0a — Synaptic Membrane Coupling Sanity Check")
    print(f"  seed={seed} N={N_TOTAL} membrane={MEMBRANE_PAIRS} pairs")
    print(f"  S_init={MEMBRANE_S_INIT} steps/win={WINDOW_STEPS}")
    print(f"  maturation={MATURATION_WINDOWS} win, coupled={COUPLED_WINDOWS} win")
    print(f"{'='*65}\n")

    t_start = time.time()

    # ── 1. Build substrate (no membrane yet) ──
    substrate_no_membrane, membrane_pairs = build_dual_substrate()
    # Deep copy for pre-membrane phase
    substrate = {k: list(v) for k, v in substrate_no_membrane.items()}
    print(f"  Substrate built: {len(substrate)} nodes, "
          f"membrane pairs={len(membrane_pairs)}")
    print(f"  Sample pair: A node {membrane_pairs[0][0]} ↔ B node {membrane_pairs[0][1]}")

    # ── 2. Create engine with N=10000 ──
    encap_params = V82EncapsulationParams(
        stress_enabled=False,   # Stress OFF
        virtual_enabled=True,
    )
    engine = V82Engine(seed=seed, N=N_TOTAL, encap_params=encap_params)
    # Override substrate
    engine.substrate = substrate
    # Need to resize _g_scores for N=10000
    engine._g_scores = np.zeros(N_TOTAL)

    # ── 3. Install Dual VirtualLayer ──
    vl_a = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    vl_a.torque_order = "age"
    vl_a.deviation_enabled = True
    vl_a.semantic_gravity_enabled = True

    vl_b = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    vl_b.torque_order = "age"
    vl_b.deviation_enabled = True
    vl_b.semantic_gravity_enabled = True

    engine.virtual = DualVirtualLayer(vl_a, vl_b)

    # ── 4. Injection ──
    print(f"  Injection...", flush=True)
    engine.run_injection()
    t_inj = time.time() - t_start
    print(f"  Injection done ({t_inj:.0f}s). "
          f"links={len(engine.state.alive_l)}")

    # ── 5. Maturation (no membrane) ──
    print(f"\n  --- Maturation Phase ({MATURATION_WINDOWS} windows × "
          f"{WINDOW_STEPS} steps) ---")

    for w in range(MATURATION_WINDOWS):
        t0 = time.time()
        frame = engine.step_window(steps=WINDOW_STEPS)
        sec = time.time() - t0

        vl = engine.virtual_stats if hasattr(engine, 'virtual_stats') else {}
        links = len(engine.state.alive_l)
        la = vl.get("_a_labels", "?")
        lb = vl.get("_b_labels", "?")
        total_labels = vl.get("labels_active", 0)

        if w % 5 == 0 or w == MATURATION_WINDOWS - 1:
            print(f"  w={w:>3} links={links:>5} "
                  f"vLb={total_labels}(A:{la}/B:{lb}) "
                  f"{sec:.0f}s")

    links_pre = len(engine.state.alive_l)
    # Count links per seed
    links_a = sum(1 for lk in engine.state.alive_l
                  if lk[0] < N_PER_SEED and lk[1] < N_PER_SEED)
    links_b = sum(1 for lk in engine.state.alive_l
                  if lk[0] >= N_PER_SEED and lk[1] >= N_PER_SEED)
    print(f"\n  Maturation complete. "
          f"links={links_pre} (A:{links_a} B:{links_b})")
    print(f"  Labels A: {len(vl_a.labels)}  Labels B: {len(vl_b.labels)}")

    # ── 6. ACTIVATE MEMBRANE ──
    print(f"\n  {'='*50}")
    print(f"  ★ MEMBRANE ACTIVATION ★")
    created = activate_membrane(engine.state, engine.substrate,
                                 membrane_pairs, MEMBRANE_S_INIT)
    print(f"  Created {created} membrane links (S={MEMBRANE_S_INIT})")
    print(f"  Total links after: {len(engine.state.alive_l)}")

    # Baseline membrane measurement
    m0 = measure_membrane(engine.state, membrane_pairs)
    print(f"  Initial membrane: alive={m0['alive']}/{m0['total']} "
          f"mean_S={m0['mean_S']:.4f} "
          f"mean_phase_diff={m0['mean_phase_diff']:.4f}")
    print(f"  {'='*50}\n")

    # ── 7. Coupled Phase (with monitoring) ──
    print(f"  --- Coupled Phase ({COUPLED_WINDOWS} windows × "
          f"{WINDOW_STEPS} steps) ---\n")

    membrane_log = [{"window": "pre", **m0}]

    for w in range(COUPLED_WINDOWS):
        t0 = time.time()
        win_num = MATURATION_WINDOWS + w

        # Run window
        frame = engine.step_window(steps=WINDOW_STEPS)
        sec = time.time() - t0

        # Membrane measurement
        m = measure_membrane(engine.state, membrane_pairs)
        m["window"] = win_num
        membrane_log.append(m)

        vl = engine.virtual_stats if hasattr(engine, 'virtual_stats') else {}
        links = len(engine.state.alive_l)
        la = vl.get("_a_labels", "?")
        lb = vl.get("_b_labels", "?")

        # Count links per seed
        links_a = sum(1 for lk in engine.state.alive_l
                      if lk[0] < N_PER_SEED and lk[1] < N_PER_SEED)
        links_b = sum(1 for lk in engine.state.alive_l
                      if lk[0] >= N_PER_SEED and lk[1] >= N_PER_SEED)
        links_cross = links - links_a - links_b

        print(f"  w={win_num:>3} links={links:>5}(A:{links_a} B:{links_b} "
              f"cross:{links_cross}) "
              f"vLb(A:{la}/B:{lb}) "
              f"membrane={m['alive']}/{m['total']} "
              f"S={m['mean_S']:.4f} "
              f"Δθ={m['mean_phase_diff']:.3f} "
              f"{sec:.0f}s")

    # ── 8. Summary ──
    print(f"\n{'='*65}")
    print(f"  SUMMARY")
    print(f"{'='*65}")

    m_final = membrane_log[-1]
    print(f"\n  Membrane survival: {m_final['alive']}/{m_final['total']} "
          f"({m_final['survival_rate']:.0%})")
    print(f"  Mean S: {m0['mean_S']:.4f} → {m_final['mean_S']:.4f}")
    print(f"  Mean phase diff: {m0['mean_phase_diff']:.4f} → "
          f"{m_final['mean_phase_diff']:.4f}")
    print(f"  Mean R: {m_final['mean_R']:.4f}")

    # Did membrane links strengthen or weaken?
    if m_final['mean_S'] > m0['mean_S']:
        trend = "STRENGTHENING"
    elif m_final['alive'] == 0:
        trend = "ALL DEAD"
    elif m_final['mean_S'] < m0['mean_S'] * 0.5:
        trend = "WEAKENING"
    else:
        trend = "STABLE"
    print(f"  Trend: {trend}")

    # Links change
    links_final = len(engine.state.alive_l)
    print(f"\n  Total links: {links_pre} → {links_final} "
          f"(Δ={links_final - links_pre:+d})")

    t_total = time.time() - t_start
    print(f"\n  Total time: {t_total/60:.1f} min")

    # Save log
    outdir = Path(f"diag_v100a_membrane_seed{seed}")
    outdir.mkdir(exist_ok=True)
    with open(outdir / "membrane_log.json", "w") as f:
        json.dump(membrane_log, f, indent=2)
    print(f"  Log saved: {outdir}/membrane_log.json")

    print(f"\n{'='*65}")
    print(f"  END v10.0a Sanity Check")
    print(f"{'='*65}\n")

    return membrane_log, engine


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v10.0a Membrane Coupling Sanity Check")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--membrane-pairs", type=int, default=MEMBRANE_PAIRS)
    parser.add_argument("--s-init", type=float, default=MEMBRANE_S_INIT)
    parser.add_argument("--maturation-windows", type=int, default=MATURATION_WINDOWS)
    parser.add_argument("--coupled-windows", type=int, default=COUPLED_WINDOWS)
    parser.add_argument("--window-steps", type=int, default=WINDOW_STEPS)
    args = parser.parse_args()

    # Override globals
    MEMBRANE_PAIRS = args.membrane_pairs
    MEMBRANE_S_INIT = args.s_init
    MATURATION_WINDOWS = args.maturation_windows
    COUPLED_WINDOWS = args.coupled_windows
    WINDOW_STEPS = args.window_steps

    run(seed=args.seed)
