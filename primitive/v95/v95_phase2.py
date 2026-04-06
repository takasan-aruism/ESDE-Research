#!/usr/bin/env python3
"""
ESDE v9.5 — Cognitive Layer Phase 2: φ + Attention Map
========================================================
Phase 1: φ (cognitive phase) — tracks structural world direction.
Phase 2: attention map — remembers where structural connections occur.

Each label gets:
  - φ: float (from Phase 1)
  - attention: {node_id: float} — decays × 0.99 each step,
    +1 for nodes in structural set

Existence layer: ZERO changes. Pure additive layer.
Spatial: once per window. Structural + φ + attention: every step.

USAGE:
  python v95_phase2.py --seed 42
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
# COGNITIVE LAYER (Phase 2: φ + Attention Map)
# ================================================================
ATTENTION_DECAY = 0.99   # half-life ≈ 69 steps (Gemini ruling)

class CognitiveLayer:
    """Cognitive layer with φ (Phase 1) + attention map (Phase 2)."""

    def __init__(self, attention_decay=ATTENTION_DECAY):
        # Phase 1: φ
        self.phi = {}           # {lid: float}
        self.prev_phi = {}      # {lid: float}
        # Phase 2: attention map
        self.attention = {}     # {lid: {node_id: float}}
        self.attention_decay = attention_decay

    def init_label(self, lid, phase_sig):
        self.phi[lid] = phase_sig
        self.prev_phi[lid] = phase_sig
        self.attention[lid] = {}

    def ensure_label(self, lid, phase_sig):
        if lid not in self.phi:
            self.init_label(lid, phase_sig)

    # ── Phase 1: φ update ──
    def update_phi(self, lid, mean_theta_structural, mean_S_structural):
        if lid not in self.phi:
            return
        self.prev_phi[lid] = self.phi[lid]
        alpha = 0.1 * (1.0 - max(0.0, min(1.0, mean_S_structural)))
        self.phi[lid] += alpha * math.sin(
            mean_theta_structural - self.phi[lid])
        while self.phi[lid] > math.pi:
            self.phi[lid] -= 2 * math.pi
        while self.phi[lid] < -math.pi:
            self.phi[lid] += 2 * math.pi

    def get_phi_drift(self, lid):
        if lid not in self.phi or lid not in self.prev_phi:
            return 0.0
        d = self.phi[lid] - self.prev_phi[lid]
        while d > math.pi: d -= 2 * math.pi
        while d < -math.pi: d += 2 * math.pi
        return d

    # ── Phase 2: attention map update ──
    def update_attention(self, lid, structural_set, core):
        """Update attention map. +1 for structural nodes, decay all."""
        if lid not in self.attention:
            return

        att = self.attention[lid]

        # Decay all existing entries
        to_remove = []
        for n in att:
            att[n] *= self.attention_decay
            if att[n] < 0.01:  # prune negligible entries
                to_remove.append(n)
        for n in to_remove:
            del att[n]

        # +1 for nodes in structural set (excluding core)
        for n in structural_set:
            if n not in core:
                att[n] = att.get(n, 0.0) + 1.0

    def get_attention_stats(self, lid):
        """Return summary stats for label's attention map."""
        att = self.attention.get(lid, {})
        if not att:
            return {"n_nodes": 0, "max": 0.0, "mean": 0.0,
                    "entropy": 0.0, "top5": []}

        vals = list(att.values())
        n = len(vals)
        mx = max(vals)
        mn = np.mean(vals)

        # Entropy (normalized)
        total = sum(vals)
        if total > 0:
            probs = [v / total for v in vals]
            entropy = -sum(p * math.log(p) for p in probs if p > 0)
            max_entropy = math.log(n) if n > 1 else 1.0
            norm_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
        else:
            norm_entropy = 0.0

        top5 = sorted(att.items(), key=lambda x: x[1], reverse=True)[:5]

        return {"n_nodes": n, "max": round(mx, 2), "mean": round(mn, 2),
                "entropy": round(norm_entropy, 4),
                "top5": [(node, round(val, 2)) for node, val in top5]}

    def remove_label(self, lid):
        self.phi.pop(lid, None)
        self.prev_phi.pop(lid, None)
        self.attention.pop(lid, None)


# ================================================================
# STRUCTURAL HELPERS
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


def structural_stats(state, struct_set, phase_sig):
    if len(struct_set) < 2:
        return phase_sig, 0.0
    thetas = [float(state.theta[n]) for n in struct_set]
    sin_s = sum(math.sin(t) for t in thetas)
    cos_s = sum(math.cos(t) for t in thetas)
    mean_theta = math.atan2(sin_s, cos_s)
    n_links = 0
    s_sum = 0.0
    for lk in state.alive_l:
        if lk[0] in struct_set and lk[1] in struct_set:
            n_links += 1
            s_sum += state.S.get(lk, 0.0)
    mean_S = s_sum / max(1, n_links)
    return mean_theta, mean_S


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


def circular_diff(a, b):
    d = a - b
    while d > math.pi: d -= 2 * math.pi
    while d < -math.pi: d += 2 * math.pi
    return d


# ================================================================
# MAIN
# ================================================================
def run(seed=42, maturation_windows=20, tracking_windows=10,
        window_steps=500, case_labels=None, top_k=10):

    if case_labels is None:
        case_labels = [87, 101, 112]

    print(f"\n{'='*65}")
    print(f"  ESDE v9.5 — Cognitive Layer Phase 2: φ + Attention Map")
    print(f"  seed={seed} mat={maturation_windows} track={tracking_windows}")
    print(f"  steps/win={window_steps} top_k={top_k}")
    print(f"  attention_decay={ATTENTION_DECAY} (half-life ≈ "
          f"{int(math.log(0.5)/math.log(ATTENTION_DECAY))} steps)")
    print(f"{'='*65}\n")

    t_start = time.time()
    N = V82_N
    torus_sub = build_torus_substrate(N)

    # Engine setup
    encap_params = V82EncapsulationParams(
        stress_enabled=False, virtual_enabled=True)
    engine = V82Engine(seed=seed, N=N, encap_params=encap_params)
    engine.virtual = VirtualLayerV9(
        feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True

    # Cognitive layer (Phase 2)
    cog = CognitiveLayer()

    engine.run_injection()
    print(f"  Injection done. links={len(engine.state.alive_l)}")

    # Maturation
    print(f"  Maturation ({maturation_windows} windows)...")
    for w in range(maturation_windows):
        engine.step_window(steps=window_steps)
        for lid, lab in engine.virtual.labels.items():
            if lid not in engine.virtual.macro_nodes:
                cog.ensure_label(lid, lab["phase_sig"])
        if w % 5 == 0:
            print(f"    w={w} links={len(engine.state.alive_l)} "
                  f"vLb={len(engine.virtual.labels)}")
    print(f"  Maturation done. labels={len(engine.virtual.labels)}\n")

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

    # Logs: sample every 50 steps for timeline
    timeline_log = defaultdict(list)
    bg_prob = BASE_PARAMS["background_injection_prob"]

    for tw in range(tracking_windows):
        w = maturation_windows + tw
        t0 = time.time()

        # Spatial: once per window
        node_to_label = {}
        for lid, lab in vl.labels.items():
            if lid not in vl.macro_nodes:
                for n in lab["nodes"]:
                    node_to_label[n] = lid

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

            # ── Cognitive update (every step) ──
            link_adj = build_link_adj(engine.state)

            for lid in list(spatial_fields.keys()):
                if lid not in vl.labels:
                    continue
                sp_set, core, max_hops = spatial_fields[lid]
                label = vl.labels[lid]

                struct_set = compute_structural(
                    core, max_hops, link_adj, engine.state.alive_n)

                mean_theta, mean_S = structural_stats(
                    engine.state, struct_set, label["phase_sig"])

                # Phase 1: φ
                cog.ensure_label(lid, label["phase_sig"])
                cog.update_phi(lid, mean_theta, mean_S)

                # Phase 2: attention map
                cog.update_attention(lid, struct_set, core)

                # Record every 50 steps
                if step % 50 == 0:
                    phase_sig = label["phase_sig"]
                    delta = circular_diff(phase_sig, mean_theta)
                    att_stats = cog.get_attention_stats(lid)

                    timeline_log[lid].append({
                        "w": w, "step": step,
                        "phi": round(cog.phi[lid], 4),
                        "sig_phi_diff": round(
                            circular_diff(phase_sig, cog.phi[lid]), 4),
                        "delta_phase": round(delta, 4),
                        "abs_delta": round(abs(delta), 4),
                        "st_total": len(struct_set),
                        "st_mean_S": round(mean_S, 4),
                        "att_n_nodes": att_stats["n_nodes"],
                        "att_max": att_stats["max"],
                        "att_mean": att_stats["mean"],
                        "att_entropy": att_stats["entropy"],
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

        for lid, lab in vl.labels.items():
            if lid not in vl.macro_nodes:
                cog.ensure_label(lid, lab["phase_sig"])
        dead = [lid for lid in cog.phi if lid not in vl.labels]
        for lid in dead:
            cog.remove_label(lid)

        sec = time.time() - t0
        # Window summary
        att_sizes = []
        for lid in tracked:
            if lid in cog.attention:
                att_sizes.append(len(cog.attention[lid]))
        mean_att = np.mean(att_sizes) if att_sizes else 0
        print(f"  w={w:>3} links={len(engine.state.alive_l):>5} "
              f"vLb={len(vl.labels):>3} "
              f"att_nodes={mean_att:.0f} {sec:.0f}s")

    # ════════════════════════════════════════════════════════
    # ANALYSIS
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*65}")
    print(f"  ATTENTION MAP ANALYSIS")
    print(f"{'='*65}")

    for lid in sorted(tracked):
        att = cog.attention.get(lid, {})
        if not att:
            continue

        vals = sorted(att.values(), reverse=True)
        n = len(vals)

        # Convergence-attention correlation
        # Check if high-attention nodes have near-phase θ
        label = vl.labels.get(lid)
        if label is None:
            continue
        phase_sig = label["phase_sig"]

        near_att = []
        far_att = []
        for node, val in att.items():
            if node in engine.state.alive_n:
                theta = float(engine.state.theta[node])
                d = abs(circular_diff(phase_sig, theta))
                if d < math.pi / 4:
                    near_att.append(val)
                else:
                    far_att.append(val)

        mean_near = np.mean(near_att) if near_att else 0
        mean_far = np.mean(far_att) if far_att else 0

        print(f"\n  --- Label {lid} ---")
        print(f"    Attention map: {n} nodes tracked")
        top5 = sorted(att.items(), key=lambda x: x[1], reverse=True)[:5]
        top5_str = [(node, round(v, 1)) for node, v in top5]
        print(f"    Top 5: {top5_str}")
        print(f"    Value distribution: max={vals[0]:.1f} "
              f"p75={vals[n//4]:.1f} p50={vals[n//2]:.1f} "
              f"p25={vals[3*n//4]:.1f} min={vals[-1]:.2f}")

        # Entropy
        total = sum(vals)
        if total > 0:
            probs = [v / total for v in vals]
            entropy = -sum(p * math.log(p) for p in probs if p > 0)
            max_ent = math.log(n) if n > 1 else 1.0
            norm_ent = entropy / max_ent if max_ent > 0 else 0.0
            print(f"    Entropy: {norm_ent:.4f} "
                  f"({'concentrated' if norm_ent < 0.7 else 'spread'})")

        # Near-phase bias in attention
        print(f"    Near-phase attention: mean={mean_near:.2f} "
              f"({len(near_att)} nodes)")
        print(f"    Far-phase attention:  mean={mean_far:.2f} "
              f"({len(far_att)} nodes)")
        if mean_far > 0:
            ratio = mean_near / mean_far
            print(f"    Near/Far ratio: {ratio:.2f}x")
            if ratio > 1.3:
                print(f"    → BIAS DETECTED: attention favors "
                      f"near-phase nodes")

    # ── Case Study Timelines ──
    print(f"\n{'='*65}")
    print(f"  CASE STUDY TIMELINES")
    print(f"{'='*65}")

    for lid in case_labels:
        entries = timeline_log.get(lid, [])
        if not entries:
            print(f"\n  Label {lid}: NOT FOUND")
            continue

        print(f"\n  --- Label {lid} ---")
        print(f"  {'step':>5} {'φ':>7} {'|Δ|':>6} {'st':>4} "
              f"{'att_n':>5} {'att_mx':>6} {'att_mn':>6} {'ent':>6}")
        print(f"  {'-'*50}")

        prev_w = None
        for e in entries:
            if e["w"] != prev_w:
                prev_w = e["w"]
                print(f"  {'--- window ' + str(e['w']) + ' ---':^50}")
            print(f"  {e['step']:>5} {e['phi']:>7.3f} "
                  f"{e['abs_delta']:>6.3f} {e['st_total']:>4} "
                  f"{e['att_n_nodes']:>5} {e['att_max']:>6.1f} "
                  f"{e['att_mean']:>6.2f} {e['att_entropy']:>6.4f}")

    # ── Attention map overlap between labels ──
    print(f"\n{'='*65}")
    print(f"  ATTENTION OVERLAP BETWEEN LABELS")
    print(f"{'='*65}\n")

    # Top-attention nodes per label (attention > median)
    label_hotspots = {}
    for lid in tracked:
        att = cog.attention.get(lid, {})
        if len(att) < 5:
            continue
        median_val = np.median(list(att.values()))
        hotspots = {n for n, v in att.items() if v > median_val}
        label_hotspots[lid] = hotspots

    if len(label_hotspots) >= 2:
        lids = sorted(label_hotspots.keys())
        pairs = []
        for i, a in enumerate(lids):
            for b in lids[i+1:]:
                inter = len(label_hotspots[a] & label_hotspots[b])
                if inter > 0:
                    pairs.append((a, b, inter))
        pairs.sort(key=lambda x: x[2], reverse=True)
        print(f"  Pairs sharing attention hotspots:")
        for a, b, inter in pairs[:15]:
            print(f"    L{a} ↔ L{b}: {inter} shared hotspot nodes")
        if not pairs:
            print(f"    No shared hotspots between any label pair")

    t_total = time.time() - t_start
    print(f"\n  Total time: {t_total/60:.1f} min")

    # ── Save ──
    outdir = Path(f"diag_v95_phase2_seed{seed}")
    outdir.mkdir(exist_ok=True)

    # Attention maps (top 100 per label)
    att_save = {}
    for lid in tracked:
        att = cog.attention.get(lid, {})
        if att:
            top100 = sorted(att.items(), key=lambda x: x[1],
                             reverse=True)[:100]
            att_save[str(lid)] = {
                "total_nodes": len(att),
                "top100": {str(n): round(v, 4) for n, v in top100},
            }
    with open(outdir / "attention_maps.json", "w") as f:
        json.dump(att_save, f, indent=2)

    # Timeline
    tl_save = {str(lid): entries for lid, entries in timeline_log.items()}
    with open(outdir / "timeline.json", "w") as f:
        json.dump(tl_save, f)

    # Summary
    summary = {}
    for lid in tracked:
        att = cog.attention.get(lid, {})
        entries = timeline_log.get(lid, [])
        if not att or not entries:
            continue
        vals = list(att.values())
        summary[str(lid)] = {
            "phi_final": round(cog.phi.get(lid, 0), 4),
            "attention_nodes": len(att),
            "attention_max": round(max(vals), 2),
            "attention_mean": round(np.mean(vals), 2),
            "attention_entropy": round(
                cog.get_attention_stats(lid)["entropy"], 4),
        }
    with open(outdir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"  Saved: {outdir}/attention_maps.json")
    print(f"  Saved: {outdir}/timeline.json")
    print(f"  Saved: {outdir}/summary.json")
    print(f"\n{'='*65}")
    print(f"  END Cognitive Phase 2")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.5 Cognitive Layer Phase 2: φ + Attention Map")
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
