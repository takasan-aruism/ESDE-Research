#!/usr/bin/env python3
"""
ESDE v9.4 — Cognitive Layer Phase 1: Cognitive Phase φ
========================================================
Each label gets a cognitive phase φ that tracks the mean theta
direction of its structural world. φ starts at phase_sig (birth)
and drifts toward the structural world's mean theta.

  φ += α × sin(mean_theta_structural - φ)
  α = 0.1 × (1.0 - mean_S_structural)

Existence layer: ZERO changes. Pure additive layer.
Spatial: once per window. Structural + φ: every step.

USAGE:
  python v94_phase1.py --seed 42
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

from esde_v82_engine import (V82Engine, V82EncapsulationParams, V82_N,
                              find_islands_sets)
from v19g_canon import BASE_PARAMS, BIAS
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9


# ================================================================
# TORUS SUBSTRATE
# ================================================================
def build_torus_substrate(N):
    side = int(math.ceil(math.sqrt(N)))
    adj = {}
    for i in range(N):
        r, c = i // side, i % side
        nbs = []
        nbs.append(((r - 1) % side) * side + c)
        nbs.append(((r + 1) % side) * side + c)
        nbs.append(r * side + ((c - 1) % side))
        nbs.append(r * side + ((c + 1) % side))
        adj[i] = [nb for nb in nbs if nb < N]
    return adj


# ================================================================
# COGNITIVE LAYER (Phase 1: φ only)
# ================================================================
class CognitivePhase:
    """Cognitive phase φ for each label. Pure additive layer."""

    def __init__(self):
        self.phi = {}           # {lid: float}
        self.prev_phi = {}      # {lid: float} for dφ/dt

    def init_label(self, lid, phase_sig):
        """Initialize φ = phase_sig at birth."""
        self.phi[lid] = phase_sig
        self.prev_phi[lid] = phase_sig

    def ensure_label(self, lid, phase_sig):
        """Ensure label has φ. Initialize if new."""
        if lid not in self.phi:
            self.init_label(lid, phase_sig)

    def update(self, lid, mean_theta_structural, mean_S_structural):
        """Update φ toward structural world's mean theta.
        α = 0.1 × (1.0 - mean_S_structural)
        Gemini ruling: α depends on structural stability."""
        if lid not in self.phi:
            return
        self.prev_phi[lid] = self.phi[lid]
        alpha = 0.1 * (1.0 - max(0.0, min(1.0, mean_S_structural)))
        self.phi[lid] += alpha * math.sin(mean_theta_structural - self.phi[lid])
        # Keep in [-π, π]
        while self.phi[lid] > math.pi:
            self.phi[lid] -= 2 * math.pi
        while self.phi[lid] < -math.pi:
            self.phi[lid] += 2 * math.pi

    def get_drift(self, lid):
        """Return dφ from previous step."""
        if lid not in self.phi or lid not in self.prev_phi:
            return 0.0
        d = self.phi[lid] - self.prev_phi[lid]
        while d > math.pi: d -= 2 * math.pi
        while d < -math.pi: d += 2 * math.pi
        return d

    def remove_label(self, lid):
        self.phi.pop(lid, None)
        self.prev_phi.pop(lid, None)


# ================================================================
# STRUCTURAL PERCEPTION
# ================================================================
def compute_structural(core, max_hops, link_adj, alive_n):
    if not core:
        return set()
    visited = set(core)
    frontier = set(n for n in core if n in alive_n)
    for hop in range(1, max_hops + 1):
        nf = set()
        for n in frontier:
            for nb in link_adj.get(n, set()):
                if nb not in visited and nb in alive_n:
                    visited.add(nb)
                    nf.add(nb)
        frontier = nf
        if not frontier:
            break
    return visited


def build_link_adj(state):
    adj = defaultdict(set)
    for lk in state.alive_l:
        adj[lk[0]].add(lk[1])
        adj[lk[1]].add(lk[0])
    return adj


def structural_stats(state, struct_set, core, phase_sig):
    """Compute mean_theta and mean_S for structural field."""
    if len(struct_set) < 2:
        return phase_sig, 0.0, 0

    thetas = [float(state.theta[n]) for n in struct_set]
    sin_s = sum(math.sin(t) for t in thetas)
    cos_s = sum(math.cos(t) for t in thetas)
    mean_theta = math.atan2(sin_s, cos_s)

    # Mean S of links within structural field
    n_links = 0
    s_sum = 0.0
    for lk in state.alive_l:
        if lk[0] in struct_set and lk[1] in struct_set:
            n_links += 1
            s_sum += state.S.get(lk, 0.0)
    mean_S = s_sum / max(1, n_links)

    return mean_theta, mean_S, n_links


def compute_spatial(state, label, torus_sub, max_hops):
    core = frozenset(n for n in label["nodes"] if n in state.alive_n)
    if not core:
        return set(), core
    visited = set(core)
    frontier = set(core)
    for hop in range(1, max_hops + 1):
        nf = set()
        for n in frontier:
            for nb in torus_sub.get(n, []):
                if nb not in visited and nb in state.alive_n:
                    visited.add(nb)
                    nf.add(nb)
        frontier = nf
        if not frontier:
            break
    return visited, core


# ================================================================
# MAIN
# ================================================================
def run(seed=42, maturation_windows=20, tracking_windows=10,
        window_steps=500, case_labels=None, top_k=10):

    if case_labels is None:
        case_labels = [87, 101, 112]

    print(f"\n{'='*65}")
    print(f"  ESDE v9.4 — Cognitive Layer Phase 1: φ")
    print(f"  seed={seed} mat={maturation_windows} track={tracking_windows}")
    print(f"  steps/win={window_steps} top_k={top_k}")
    print(f"  α = 0.1 × (1 - mean_S_structural)")
    print(f"{'='*65}\n")

    t_start = time.time()
    N = V82_N
    torus_sub = build_torus_substrate(N)

    # Engine setup (standard v9.3 conditions)
    encap_params = V82EncapsulationParams(
        stress_enabled=False, virtual_enabled=True)
    engine = V82Engine(seed=seed, N=N, encap_params=encap_params)
    engine.virtual = VirtualLayerV9(
        feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True

    # Cognitive layer
    cog = CognitivePhase()

    engine.run_injection()
    print(f"  Injection done. links={len(engine.state.alive_l)}")

    # Maturation
    print(f"  Maturation ({maturation_windows} windows)...")
    for w in range(maturation_windows):
        engine.step_window(steps=window_steps)
        # Initialize φ for new labels
        for lid, lab in engine.virtual.labels.items():
            if lid not in engine.virtual.macro_nodes:
                cog.ensure_label(lid, lab["phase_sig"])
        if w % 5 == 0:
            print(f"    w={w} links={len(engine.state.alive_l)} "
                  f"vLb={len(engine.virtual.labels)}")
    print(f"  Maturation done. labels={len(engine.virtual.labels)}")
    print(f"  φ initialized for {len(cog.phi)} labels\n")

    # Select tracked labels
    vl = engine.virtual
    all_labels = [(lid, lab["share"]) for lid, lab in vl.labels.items()
                  if lid not in vl.macro_nodes]
    all_labels.sort(key=lambda x: x[1], reverse=True)
    tracked = set(lid for lid, _ in all_labels[:top_k])
    for cl in case_labels:
        if cl in vl.labels:
            tracked.add(cl)
    print(f"  Tracking {len(tracked)} labels: {sorted(tracked)}")

    # ── Tracking Phase ──
    print(f"\n  --- Tracking Phase ({tracking_windows} windows "
          f"× {window_steps} steps) ---\n")

    phi_log = defaultdict(list)  # {lid: [{step data}]}
    bg_prob = BASE_PARAMS["background_injection_prob"]

    for tw in range(tracking_windows):
        w = maturation_windows + tw
        t0 = time.time()

        # Spatial: once per window
        spatial_fields = {}
        for lid in tracked:
            if lid not in vl.labels:
                continue
            label = vl.labels[lid]
            core_alive = sum(1 for n in label["nodes"]
                             if n in engine.state.alive_n)
            if core_alive == 0:
                continue
            sp_set, core = compute_spatial(
                engine.state, label, torus_sub, core_alive)
            spatial_fields[lid] = (sp_set, core, core_alive)

        # Step-by-step
        for step in range(window_steps):
            # Physics (canon)
            engine.realizer.step(engine.state)
            engine.physics.step_pre_chemistry(engine.state)
            engine.chem.step(engine.state)
            engine.physics.step_resonance(engine.state)

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
            gz = float(engine._g_scores.sum())

            engine.intruder.step(engine.state)
            engine.physics.step_decay_exclusion(engine.state)

            # BG seeding (canon)
            al = list(engine.state.alive_n)
            na = len(al)
            if na > 0:
                aa = np.array(al)
                if BIAS > 0 and gz > 0:
                    ga = engine._g_scores[aa]
                    gs = ga.sum()
                    if gs > 0:
                        pg = ga / gs
                        pd = (1 - BIAS) * (np.ones(na) / na) + BIAS * pg
                        pd /= pd.sum()
                    else:
                        pd = np.ones(na) / na
                else:
                    pd = np.ones(na) / na
                mk = engine.state.rng.random(na) < bg_prob
                for idx in range(na):
                    if mk[idx]:
                        t = int(engine.state.rng.choice(aa, p=pd))
                        if t in engine.state.alive_n:
                            engine.state.E[t] = min(
                                1.0, engine.state.E[t] + 0.3)
                            if engine.state.Z[t] == 0 and \
                               engine.state.rng.random() < 0.5:
                                engine.state.Z[t] = 1 if \
                                    engine.state.rng.random() < 0.5 else 2

            # ── Structural perception + φ update (every step) ──
            link_adj = build_link_adj(engine.state)

            for lid in list(spatial_fields.keys()):
                if lid not in vl.labels:
                    continue
                sp_set, core, max_hops = spatial_fields[lid]
                label = vl.labels[lid]

                struct_set = compute_structural(
                    core, max_hops, link_adj, engine.state.alive_n)

                mean_theta, mean_S, n_links = structural_stats(
                    engine.state, struct_set, core, label["phase_sig"])

                # Update φ
                cog.ensure_label(lid, label["phase_sig"])
                cog.update(lid, mean_theta, mean_S)

                drift = cog.get_drift(lid)
                phi = cog.phi[lid]
                phase_sig = label["phase_sig"]

                # Phase_sig - φ (circular)
                sig_phi_diff = phase_sig - phi
                while sig_phi_diff > math.pi: sig_phi_diff -= 2 * math.pi
                while sig_phi_diff < -math.pi: sig_phi_diff += 2 * math.pi

                # Record (every 10 steps to control output size)
                if step % 10 == 0:
                    phi_log[lid].append({
                        "w": w,
                        "step": step,
                        "phi": round(phi, 6),
                        "phase_sig": round(phase_sig, 4),
                        "sig_phi_diff": round(sig_phi_diff, 6),
                        "drift": round(drift, 6),
                        "alpha": round(0.1 * (1.0 - mean_S), 4),
                        "st_total": len(struct_set),
                        "st_mean_theta": round(mean_theta, 4),
                        "st_mean_S": round(mean_S, 4),
                        "st_links": n_links,
                    })

        # Window end: virtual layer step
        isl_m = find_islands_sets(engine.state, 0.20)
        class _Isl:
            pass
        islands_dict = {}
        for i, isl in enumerate(isl_m):
            obj = _Isl()
            obj.nodes = isl
            islands_dict[i] = obj

        vs = vl.step(engine.state, engine.window_count,
                      islands=islands_dict, substrate=engine.substrate)
        engine.virtual_stats = vs
        engine.window_count += 1

        # Ensure φ for newly born labels
        for lid, lab in vl.labels.items():
            if lid not in vl.macro_nodes:
                cog.ensure_label(lid, lab["phase_sig"])
        # Remove dead labels
        dead = [lid for lid in cog.phi if lid not in vl.labels]
        for lid in dead:
            cog.remove_label(lid)

        sec = time.time() - t0

        # Window summary: mean |sig-φ| for tracked
        diffs = []
        for lid in tracked:
            if lid in cog.phi and lid in vl.labels:
                d = abs(vl.labels[lid]["phase_sig"] - cog.phi[lid])
                if d > math.pi: d = 2 * math.pi - d
                diffs.append(d)

        mean_diff = np.mean(diffs) if diffs else 0
        print(f"  w={w:>3} links={len(engine.state.alive_l):>5} "
              f"vLb={len(vl.labels):>3} "
              f"mean|sig-φ|={mean_diff:.4f} {sec:.0f}s")

    # ════════════════════════════════════════════════════════
    # ANALYSIS
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*65}")
    print(f"  COGNITIVE PHASE φ ANALYSIS")
    print(f"{'='*65}")

    for lid in sorted(tracked):
        entries = phi_log.get(lid, [])
        if len(entries) < 5:
            continue

        phis = [e["phi"] for e in entries]
        diffs = [e["sig_phi_diff"] for e in entries]
        drifts = [e["drift"] for e in entries]
        alphas = [e["alpha"] for e in entries]
        st_totals = [e["st_total"] for e in entries]

        abs_diffs = [abs(d) for d in diffs]
        abs_drifts = [abs(d) for d in drifts]

        print(f"\n  --- Label {lid} ({len(entries)} samples) ---")
        print(f"    phase_sig: {entries[0]['phase_sig']}")
        print(f"    φ range: [{min(phis):.4f}, {max(phis):.4f}]")
        print(f"    |sig-φ| drift: mean={np.mean(abs_diffs):.4f} "
              f"max={max(abs_diffs):.4f}")
        print(f"    |dφ/dt|: mean={np.mean(abs_drifts):.6f} "
              f"max={max(abs_drifts):.6f}")
        print(f"    α: mean={np.mean(alphas):.4f} "
              f"range=[{min(alphas):.4f}, {max(alphas):.4f}]")
        print(f"    structural: mean={np.mean(st_totals):.0f} "
              f"std={np.std(st_totals):.0f}")

        # φ stability classification
        if np.mean(abs_diffs) < 0.1:
            phi_type = "ANCHORED (φ ≈ phase_sig)"
        elif np.mean(abs_diffs) < 0.5:
            phi_type = "DRIFTING (φ moving away from phase_sig)"
        else:
            phi_type = "DETACHED (φ far from phase_sig)"
        print(f"    φ type: {phi_type}")

    # ── Case Study Timelines ──
    print(f"\n{'='*65}")
    print(f"  CASE STUDY φ TIMELINES")
    print(f"{'='*65}")

    for lid in case_labels:
        entries = phi_log.get(lid, [])
        if not entries:
            print(f"\n  Label {lid}: NOT FOUND")
            continue

        print(f"\n  --- Label {lid} (phase_sig={entries[0]['phase_sig']}) ---")
        print(f"  {'step':>5} {'φ':>8} {'sig-φ':>8} {'dφ':>8} "
              f"{'α':>6} {'st':>4} {'st_S':>6}")
        print(f"  {'-'*48}")

        # Show 30 samples per window
        shown = 0
        prev_w = None
        for e in entries:
            if e["w"] != prev_w:
                prev_w = e["w"]
                shown = 0
                if prev_w > maturation_windows:
                    print(f"  {'--- window ' + str(e['w']) + ' ---':^48}")
            if shown < 30:
                print(f"  {e['step']:>5} {e['phi']:>8.4f} "
                      f"{e['sig_phi_diff']:>8.4f} {e['drift']:>8.5f} "
                      f"{e['alpha']:>6.4f} {e['st_total']:>4} "
                      f"{e['st_mean_S']:>6.4f}")
                shown += 1

    # ── φ comparison between labels ──
    print(f"\n{'='*65}")
    print(f"  INTER-LABEL φ COMPARISON (final window)")
    print(f"{'='*65}\n")

    final_phis = {}
    for lid in tracked:
        entries = phi_log.get(lid, [])
        if entries:
            final_phis[lid] = entries[-1]["phi"]

    if len(final_phis) >= 2:
        lids = sorted(final_phis.keys())
        print(f"  {'A':>5} {'B':>5} {'φ_A':>8} {'φ_B':>8} {'|φ_A-φ_B|':>10}")
        print(f"  {'-'*40}")
        pairs = []
        for i, a in enumerate(lids):
            for b in lids[i+1:]:
                d = abs(final_phis[a] - final_phis[b])
                if d > math.pi: d = 2 * math.pi - d
                pairs.append((a, b, d))
        pairs.sort(key=lambda x: x[2])
        for a, b, d in pairs[:15]:
            print(f"  {a:>5} {b:>5} {final_phis[a]:>8.4f} "
                  f"{final_phis[b]:>8.4f} {d:>10.4f}")

    t_total = time.time() - t_start
    print(f"\n  Total time: {t_total/60:.1f} min")

    # ── Save ──
    outdir = Path(f"diag_v94_phase1_seed{seed}")
    outdir.mkdir(exist_ok=True)

    save_log = {str(lid): entries for lid, entries in phi_log.items()}
    with open(outdir / "phi_log.json", "w") as f:
        json.dump(save_log, f)

    # Summary
    summary = {}
    for lid in tracked:
        entries = phi_log.get(lid, [])
        if not entries:
            continue
        abs_diffs = [abs(e["sig_phi_diff"]) for e in entries]
        abs_drifts = [abs(e["drift"]) for e in entries]
        summary[str(lid)] = {
            "phase_sig": entries[0]["phase_sig"],
            "phi_final": entries[-1]["phi"],
            "sig_phi_diff_mean": round(np.mean(abs_diffs), 6),
            "sig_phi_diff_max": round(max(abs_diffs), 6),
            "drift_mean": round(np.mean(abs_drifts), 6),
            "alpha_mean": round(np.mean([e["alpha"] for e in entries]), 4),
            "structural_mean": round(np.mean([e["st_total"] for e in entries]), 1),
        }
    with open(outdir / "phi_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"  Saved: {outdir}/phi_log.json")
    print(f"  Saved: {outdir}/phi_summary.json")
    print(f"\n{'='*65}")
    print(f"  END Cognitive Phase 1")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.4 Cognitive Layer Phase 1: φ")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--maturation-windows", type=int, default=20)
    parser.add_argument("--tracking-windows", type=int, default=10)
    parser.add_argument("--window-steps", type=int, default=500)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--case-labels", type=str, default="87,101,112")
    args = parser.parse_args()

    cases = [int(x) for x in args.case_labels.split(",")]
    run(seed=args.seed,
        maturation_windows=args.maturation_windows,
        tracking_windows=args.tracking_windows,
        window_steps=args.window_steps,
        case_labels=cases,
        top_k=args.top_k)
