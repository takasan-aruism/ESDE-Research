#!/usr/bin/env python3
"""
ESDE v9.5 — Cognitive Layer Phase 4: Full Disposition Vector
==============================================================
Phase 1: φ (cognitive phase)
Phase 2: attention map (contact memory)
Phase 3: partner familiarity (social memory)
Phase 4: disposition vector (character quantification)

Disposition = [d_social, d_stability, d_attention_spread, d_familiarity]
  d_social = n_partners / max_partners_across_labels
  d_stability = 1 / (1 + st_std / (st_mean + eps))  (GPT ruling)
  d_attention_spread = attention entropy (normalized)
  d_familiarity = mean familiarity strength

Computed per window. Dead labels keep their pre-death trajectory.
Existence layer: ZERO changes.

USAGE:
  python v95_phase4.py --seed 42
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
# CONSTANTS
# ================================================================
ATTENTION_DECAY = 0.99
FAMILIARITY_DECAY = 0.998
EPS = 1e-6


# ================================================================
# TORUS
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
# COGNITIVE LAYER (Phase 1-3, unchanged)
# ================================================================
class CognitiveLayer:
    def __init__(self):
        self.phi = {}
        self.prev_phi = {}
        self.attention = {}
        self.familiarity = {}

    def init_label(self, lid, phase_sig):
        self.phi[lid] = phase_sig
        self.prev_phi[lid] = phase_sig
        self.attention[lid] = {}
        self.familiarity[lid] = {}

    def ensure_label(self, lid, phase_sig):
        if lid not in self.phi:
            self.init_label(lid, phase_sig)

    def update_phi(self, lid, mean_theta, mean_S):
        if lid not in self.phi:
            return
        self.prev_phi[lid] = self.phi[lid]
        alpha = 0.1 * (1.0 - max(0.0, min(1.0, mean_S)))
        self.phi[lid] += alpha * math.sin(mean_theta - self.phi[lid])
        while self.phi[lid] > math.pi:
            self.phi[lid] -= 2 * math.pi
        while self.phi[lid] < -math.pi:
            self.phi[lid] += 2 * math.pi

    def update_attention(self, lid, structural_set, core):
        if lid not in self.attention:
            return
        att = self.attention[lid]
        to_remove = []
        for n in att:
            att[n] *= ATTENTION_DECAY
            if att[n] < 0.01:
                to_remove.append(n)
        for n in to_remove:
            del att[n]
        for n in structural_set:
            if n not in core:
                att[n] = att.get(n, 0.0) + 1.0

    def update_familiarity(self, lid, structural_set, core,
                            node_to_label, macro_nodes):
        if lid not in self.familiarity:
            return
        fam = self.familiarity[lid]
        to_remove = []
        for other in fam:
            fam[other] *= FAMILIARITY_DECAY
            if fam[other] < 0.01:
                to_remove.append(other)
        for other in to_remove:
            del fam[other]
        seen = set()
        for n in structural_set:
            if n in core:
                continue
            owner = node_to_label.get(n)
            if owner is not None and owner != lid and owner not in macro_nodes:
                seen.add(owner)
        for other in seen:
            fam[other] = fam.get(other, 0.0) + 1.0

    def get_attention_entropy(self, lid):
        att = self.attention.get(lid, {})
        if len(att) < 2:
            return 0.0
        vals = list(att.values())
        total = sum(vals)
        if total <= 0:
            return 0.0
        probs = [v / total for v in vals]
        entropy = -sum(p * math.log(p) for p in probs if p > 0)
        return entropy / math.log(len(vals))

    def get_familiarity_mean(self, lid):
        fam = self.familiarity.get(lid, {})
        if not fam:
            return 0.0
        return np.mean(list(fam.values()))

    def get_n_partners(self, lid):
        return len(self.familiarity.get(lid, {}))

    def remove_label(self, lid):
        self.phi.pop(lid, None)
        self.prev_phi.pop(lid, None)
        self.attention.pop(lid, None)
        self.familiarity.pop(lid, None)


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
    return mean_theta, s_sum / max(1, n_links)


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
    print(f"  ESDE v9.5 — Cognitive Layer Phase 4: Disposition Vector")
    print(f"  seed={seed} mat={maturation_windows} track={tracking_windows}")
    print(f"  steps/win={window_steps} top_k={top_k}")
    print(f"{'='*65}\n")

    t_start = time.time()
    N = V82_N
    torus_sub = build_torus_substrate(N)

    encap_params = V82EncapsulationParams(
        stress_enabled=False, virtual_enabled=True)
    engine = V82Engine(seed=seed, N=N, encap_params=encap_params)
    engine.virtual = VirtualLayerV9(
        feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True

    cog = CognitiveLayer()

    engine.run_injection()
    print(f"  Injection done. links={len(engine.state.alive_l)}")

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

    vl = engine.virtual
    all_labels = [(lid, lab["share"]) for lid, lab in vl.labels.items()
                  if lid not in vl.macro_nodes]
    all_labels.sort(key=lambda x: x[1], reverse=True)
    tracked = set(lid for lid, _ in all_labels[:top_k])
    for cl in case_labels:
        if cl in vl.labels:
            tracked.add(cl)
    print(f"  Tracking {len(tracked)} labels: {sorted(tracked)}")

    # ── Tracking ──
    print(f"\n  --- Tracking Phase ---\n")

    bg_prob = BASE_PARAMS["background_injection_prob"]

    # Per-label per-window: structural sizes for d_stability
    window_st_sizes = defaultdict(list)  # {lid: [st_sizes this window]}

    # Disposition trajectories
    disposition_traj = defaultdict(list)  # {lid: [{w, d_social, ...}]}

    # Track which labels are alive at each window
    alive_at_window = {}

    for tw in range(tracking_windows):
        w = maturation_windows + tw
        t0 = time.time()

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

        # Reset window st_sizes
        for lid in tracked:
            window_st_sizes[lid] = []

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

            # Cognitive update
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

                cog.ensure_label(lid, label["phase_sig"])
                cog.update_phi(lid, mean_theta, mean_S)
                cog.update_attention(lid, struct_set, core)
                cog.update_familiarity(
                    lid, struct_set, core,
                    node_to_label, vl.macro_nodes)

                window_st_sizes[lid].append(len(struct_set))

        # ── End of window: compute disposition ──
        alive_this_window = set()
        max_partners = max(
            (cog.get_n_partners(lid) for lid in tracked
             if lid in cog.familiarity), default=1)
        max_partners = max(max_partners, 1)

        for lid in tracked:
            if lid not in vl.labels:
                continue
            if lid not in cog.phi:
                continue

            alive_this_window.add(lid)

            st_sizes = window_st_sizes.get(lid, [])
            if st_sizes:
                st_mean = np.mean(st_sizes)
                st_std = np.std(st_sizes)
            else:
                st_mean = 0.0
                st_std = 0.0

            d_social = cog.get_n_partners(lid) / max_partners
            d_stability = 1.0 / (1.0 + st_std / (st_mean + EPS))
            d_attention_spread = cog.get_attention_entropy(lid)
            d_familiarity = cog.get_familiarity_mean(lid)

            disposition_traj[lid].append({
                "w": w,
                "d_social": round(d_social, 4),
                "d_stability": round(d_stability, 4),
                "d_attention_spread": round(d_attention_spread, 4),
                "d_familiarity": round(d_familiarity, 4),
                "n_partners": cog.get_n_partners(lid),
                "st_mean": round(st_mean, 1),
                "st_std": round(st_std, 1),
                "att_nodes": len(cog.attention.get(lid, {})),
                "fam_max": round(max(cog.familiarity.get(lid, {}).values(),
                                      default=0), 2),
                "alive": True,
            })

        alive_at_window[w] = alive_this_window

        # VL step
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

        # Mark dead labels
        newly_dead = []
        for lid in list(cog.phi.keys()):
            if lid not in vl.labels and lid in tracked:
                newly_dead.append(lid)
                # Mark last entry as death
                if disposition_traj[lid]:
                    disposition_traj[lid][-1]["alive"] = False
                    disposition_traj[lid][-1]["death_window"] = w
                cog.remove_label(lid)

        sec = time.time() - t0
        dead_str = f" dead={newly_dead}" if newly_dead else ""
        print(f"  w={w:>3} links={len(engine.state.alive_l):>5} "
              f"vLb={len(vl.labels):>3}{dead_str} {sec:.0f}s")

    # ════════════════════════════════════════════════════════
    # ANALYSIS
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*65}")
    print(f"  DISPOSITION VECTOR ANALYSIS")
    print(f"{'='*65}")

    # Summary table
    print(f"\n  --- Final / Last Disposition ---\n")
    print(f"  {'lid':>5} {'social':>7} {'stabil':>7} {'spread':>7} "
          f"{'famil':>7} {'part':>5} {'status':>8}")
    print(f"  {'-'*50}")

    for lid in sorted(disposition_traj.keys()):
        traj = disposition_traj[lid]
        if not traj:
            continue
        last = traj[-1]
        status = "ALIVE" if last["alive"] else f"DEAD@w{last.get('death_window', '?')}"
        print(f"  {lid:>5} {last['d_social']:>7.3f} {last['d_stability']:>7.3f} "
              f"{last['d_attention_spread']:>7.4f} {last['d_familiarity']:>7.2f} "
              f"{last['n_partners']:>5} {status:>8}")

    # ── Trajectory Types ──
    print(f"\n{'='*65}")
    print(f"  TRAJECTORY TYPE CLASSIFICATION")
    print(f"{'='*65}\n")

    for lid in sorted(disposition_traj.keys()):
        traj = disposition_traj[lid]
        if len(traj) < 2:
            continue

        socials = [e["d_social"] for e in traj]
        stabilities = [e["d_stability"] for e in traj]
        spreads = [e["d_attention_spread"] for e in traj]
        familiarities = [e["d_familiarity"] for e in traj]

        # Classify
        traits = []
        if np.mean(socials) > 0.5:
            traits.append("social")
        elif np.mean(socials) < 0.15:
            traits.append("isolated")

        if np.mean(stabilities) > 0.5:
            traits.append("stable")
        elif np.mean(stabilities) < 0.3:
            traits.append("turbulent")

        if np.mean(spreads) > 0.85:
            traits.append("wide_attention")
        elif np.mean(spreads) < 0.8:
            traits.append("focused_attention")

        if np.mean(familiarities) > 10:
            traits.append("deeply_connected")
        elif np.mean(familiarities) < 3:
            traits.append("shallow_connections")

        alive = traj[-1]["alive"]
        if not alive:
            traits.append("died")

        trait_str = " | ".join(traits) if traits else "neutral"

        # Trend
        if len(socials) >= 3:
            social_trend = socials[-1] - socials[0]
            trend_str = "↑" if social_trend > 0.1 else ("↓" if social_trend < -0.1 else "→")
        else:
            trend_str = "?"

        print(f"  L{lid}: {trait_str} (social trend: {trend_str})")

    # ── Case Study Trajectories ──
    print(f"\n{'='*65}")
    print(f"  CASE STUDY DISPOSITION TRAJECTORIES")
    print(f"{'='*65}")

    for lid in case_labels:
        traj = disposition_traj.get(lid, [])
        if not traj:
            print(f"\n  Label {lid}: NO DATA (never tracked)")
            continue

        print(f"\n  --- Label {lid} ---")
        print(f"  {'w':>4} {'social':>7} {'stabil':>7} {'spread':>7} "
              f"{'famil':>7} {'part':>5} {'st_m':>5} {'st_s':>5} {'status':>6}")
        print(f"  {'-'*55}")

        for e in traj:
            status = "alive" if e["alive"] else "DEAD"
            print(f"  {e['w']:>4} {e['d_social']:>7.3f} "
                  f"{e['d_stability']:>7.3f} "
                  f"{e['d_attention_spread']:>7.4f} "
                  f"{e['d_familiarity']:>7.2f} "
                  f"{e['n_partners']:>5} "
                  f"{e['st_mean']:>5.0f} {e['st_std']:>5.0f} "
                  f"{status:>6}")

    # ── Disposition Space ──
    print(f"\n{'='*65}")
    print(f"  DISPOSITION SPACE (final window, alive labels)")
    print(f"{'='*65}\n")

    # Find labels alive at last window
    last_w = maturation_windows + tracking_windows - 1
    alive_final = alive_at_window.get(last_w, set())

    if len(alive_final) >= 2:
        # Pairwise disposition distance
        pairs = []
        for lid_a in sorted(alive_final):
            traj_a = disposition_traj.get(lid_a, [])
            if not traj_a:
                continue
            da = traj_a[-1]
            for lid_b in sorted(alive_final):
                if lid_b <= lid_a:
                    continue
                traj_b = disposition_traj.get(lid_b, [])
                if not traj_b:
                    continue
                db = traj_b[-1]
                dist = math.sqrt(
                    (da["d_social"] - db["d_social"])**2 +
                    (da["d_stability"] - db["d_stability"])**2 +
                    (da["d_attention_spread"] - db["d_attention_spread"])**2 +
                    (da["d_familiarity"] - db["d_familiarity"])**2)
                pairs.append((lid_a, lid_b, dist))

        pairs.sort(key=lambda x: x[2])
        print(f"  Most similar characters:")
        for a, b, d in pairs[:5]:
            print(f"    L{a} ↔ L{b}: distance={d:.4f}")
        print(f"\n  Most different characters:")
        for a, b, d in pairs[-5:]:
            print(f"    L{a} ↔ L{b}: distance={d:.4f}")

    t_total = time.time() - t_start
    print(f"\n  Total time: {t_total/60:.1f} min")

    # ── Save ──
    outdir = Path(f"diag_v95_phase4_seed{seed}")
    outdir.mkdir(exist_ok=True)

    traj_save = {str(lid): traj for lid, traj in disposition_traj.items()}
    with open(outdir / "disposition_trajectories.json", "w") as f:
        json.dump(traj_save, f, indent=2)

    # Summary
    summary = {}
    for lid, traj in disposition_traj.items():
        if not traj:
            continue
        last = traj[-1]
        summary[str(lid)] = {
            "final_disposition": {
                "d_social": last["d_social"],
                "d_stability": last["d_stability"],
                "d_attention_spread": last["d_attention_spread"],
                "d_familiarity": last["d_familiarity"],
            },
            "n_windows": len(traj),
            "alive": last["alive"],
            "death_window": last.get("death_window"),
        }
    with open(outdir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"  Saved: {outdir}/disposition_trajectories.json")
    print(f"  Saved: {outdir}/summary.json")
    print(f"\n{'='*65}")
    print(f"  END Cognitive Phase 4: Disposition Vector")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.5 Cognitive Phase 4: Disposition Vector")
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
