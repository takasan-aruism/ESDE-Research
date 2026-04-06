#!/usr/bin/env python3
"""
ESDE v9.6 — Large-Scale Cognitive Baseline (single seed runner)
================================================================
Runs one seed with full Phase 1-4 cognitive layer. No feedback.
Designed for GNU parallel execution across 48 seeds.

3-layer logging:
  Layer A: per_window CSV (global aggregates)
  Layer B: per_label CSV (label summaries)
  Layer C: representative JSON (top labels only)

Extra measurements:
  - convergence near_phase bias (seed-level)
  - death vs disposition correlation
  - familiarity reciprocity distribution
  - attention hotspot overlap between labels
  - new label integration speed
  - structural volatility vs survival

USAGE:
  # Single seed
  python v96_baseline.py --seed 42 --tracking-windows 10

  # 48 seeds, short run (Run A)
  seq 0 47 | parallel -j24 python v96_baseline.py --seed {} --tracking-windows 10

  # 5 seeds, long run (Run B)
  seq 0 4 | parallel -j5 python v96_baseline.py --seed {} --tracking-windows 50 --tag long
"""

import sys, math, time, json, csv, argparse
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_V82_DIR = _REPO_ROOT / "autonomy" / "v82"
_V43_DIR = _REPO_ROOT / "cognition" / "semantic_injection" / "v4_pipeline" / "v43"
_V41_DIR = _V43_DIR.parent / "v41"
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_SCRIPT_DIR), str(_V82_DIR), str(_V43_DIR), str(_V41_DIR), str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

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
CONVERGENCE_THRESHOLD = 0.3
N_REPRESENTATIVES = 8


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
# COGNITIVE LAYER (Phase 1-3)
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
        return float(np.mean(list(fam.values())))

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


def circular_diff(a, b):
    d = a - b
    while d > math.pi: d -= 2 * math.pi
    while d < -math.pi: d += 2 * math.pi
    return d


# ================================================================
# MAIN
# ================================================================
def run(seed=42, maturation_windows=20, tracking_windows=10,
        window_steps=500, tag="short"):

    t_start = time.time()
    N = V82_N
    torus_sub = build_torus_substrate(N)

    outdir = Path(f"diag_v96_baseline_{tag}")
    outdir.mkdir(exist_ok=True)
    for sub in ["aggregates", "labels", "representatives", "network"]:
        (outdir / sub).mkdir(exist_ok=True)

    # Engine
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

    # Maturation
    for w in range(maturation_windows):
        engine.step_window(steps=window_steps)
        for lid, lab in engine.virtual.labels.items():
            if lid not in engine.virtual.macro_nodes:
                cog.ensure_label(lid, lab["phase_sig"])

    vl = engine.virtual
    print(f"  seed={seed} mat done. labels={len(vl.labels)} "
          f"links={len(engine.state.alive_l)}")

    # Track ALL non-macro labels
    tracked = set()
    for lid in vl.labels:
        if lid not in vl.macro_nodes:
            tracked.add(lid)

    # Storage
    bg_prob = BASE_PARAMS["background_injection_prob"]
    window_rows = []       # Layer A
    label_records = {}     # Layer B: {lid: record}
    repr_timelines = {}    # Layer C: {lid: [entries]}
    all_deaths = []
    all_births_after_mat = []

    # Convergence bias tracking (seed-level)
    conv_near_ratios = []
    div_near_ratios = []

    # Per-label accumulators
    label_meta = {}  # {lid: {birth_w, death_w, ...}}
    for lid in tracked:
        lab = vl.labels[lid]
        label_meta[lid] = {
            "birth_w": lab["born"],
            "death_w": None,
            "lifespan": 0,
            "phase_sig": lab["phase_sig"],
            "n_core": len([n for n in lab["nodes"]
                           if n in engine.state.alive_n]),
        }

    # ── Tracking Phase ──
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

        window_st_sizes = defaultdict(list)

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

                # Convergence bias (sample every 10 steps)
                if step % 10 == 0 and len(struct_set) >= 2:
                    phase_sig = label["phase_sig"]
                    delta = circular_diff(phase_sig, mean_theta)
                    thetas = [float(engine.state.theta[n])
                              for n in struct_set]
                    near = sum(1 for t in thetas
                               if abs(circular_diff(phase_sig, t)) < math.pi/4)
                    near_ratio = near / len(struct_set)

                    if abs(delta) < CONVERGENCE_THRESHOLD:
                        conv_near_ratios.append(near_ratio)
                    elif abs(delta) > 2.5:
                        div_near_ratios.append(near_ratio)

        # ── End of window: disposition + aggregates ──
        alive_tracked = [lid for lid in tracked if lid in vl.labels
                         and lid in cog.phi]
        max_partners = max(
            (cog.get_n_partners(lid) for lid in alive_tracked),
            default=1)
        max_partners = max(max_partners, 1)

        # Per-label disposition
        socials = []
        stabilities = []
        spreads = []
        familiarities = []
        n_social = 0
        n_isolated = 0
        n_deeply = 0

        for lid in alive_tracked:
            st_sizes = window_st_sizes.get(lid, [])
            st_mean = np.mean(st_sizes) if st_sizes else 0
            st_std = np.std(st_sizes) if st_sizes else 0

            d_social = cog.get_n_partners(lid) / max_partners
            d_stability = 1.0 / (1.0 + st_std / (st_mean + EPS))
            d_spread = cog.get_attention_entropy(lid)
            d_fam = cog.get_familiarity_mean(lid)

            socials.append(d_social)
            stabilities.append(d_stability)
            spreads.append(d_spread)
            familiarities.append(d_fam)

            if d_social > 0.5:
                n_social += 1
            elif d_social < 0.15:
                n_isolated += 1
            if d_fam > 10:
                n_deeply += 1

            # Update label_meta
            if lid not in label_meta:
                label_meta[lid] = {
                    "birth_w": w, "death_w": None,
                    "phase_sig": vl.labels[lid]["phase_sig"],
                    "n_core": len([n for n in vl.labels[lid]["nodes"]
                                   if n in engine.state.alive_n]),
                }
            label_meta[lid]["lifespan"] = w - label_meta[lid]["birth_w"]
            label_meta[lid]["last_social"] = d_social
            label_meta[lid]["last_stability"] = d_stability
            label_meta[lid]["last_spread"] = d_spread
            label_meta[lid]["last_familiarity"] = d_fam
            label_meta[lid]["last_partners"] = cog.get_n_partners(lid)
            label_meta[lid]["last_st_mean"] = round(st_mean, 1)
            label_meta[lid]["last_st_std"] = round(st_std, 1)
            label_meta[lid]["last_fam_max"] = round(
                max(cog.familiarity.get(lid, {}).values(), default=0), 2)
            label_meta[lid]["last_att_nodes"] = len(
                cog.attention.get(lid, {}))

            # Representative timeline (stored in memory, saved later)
            if lid not in repr_timelines:
                repr_timelines[lid] = []
            repr_timelines[lid].append({
                "w": w,
                "d_social": round(d_social, 4),
                "d_stability": round(d_stability, 4),
                "d_spread": round(d_spread, 4),
                "d_familiarity": round(d_fam, 4),
                "n_partners": cog.get_n_partners(lid),
                "st_mean": round(st_mean, 1),
                "st_std": round(st_std, 1),
            })

        # Familiarity network stats
        reciprocal_count = 0
        asymmetric_count = 0
        symmetry_vals = []
        for lid_a in alive_tracked:
            fam_a = cog.familiarity.get(lid_a, {})
            for lid_b in alive_tracked:
                if lid_b <= lid_a:
                    continue
                fa = fam_a.get(lid_b, 0.0)
                fb = cog.familiarity.get(lid_b, {}).get(lid_a, 0.0)
                if fa > 1.0 and fb > 1.0:
                    reciprocal_count += 1
                    sym = min(fa, fb) / max(fa, fb)
                    symmetry_vals.append(sym)
                elif fa > 1.0 or fb > 1.0:
                    asymmetric_count += 1

        # Attention overlap
        att_overlaps = []
        att_hotspots = {}
        for lid in alive_tracked:
            att = cog.attention.get(lid, {})
            if len(att) >= 5:
                median_val = np.median(list(att.values()))
                att_hotspots[lid] = {n for n, v in att.items()
                                      if v > median_val}
        for lid_a in list(att_hotspots.keys()):
            for lid_b in list(att_hotspots.keys()):
                if lid_b <= lid_a:
                    continue
                inter = len(att_hotspots[lid_a] & att_hotspots[lid_b])
                if inter > 0:
                    att_overlaps.append(inter)

        # Layer A: window row
        window_rows.append({
            "seed": seed,
            "window": w,
            "links": len(engine.state.alive_l),
            "v_labels": len(vl.labels),
            "alive_tracked": len(alive_tracked),
            "mean_social": round(np.mean(socials), 4) if socials else 0,
            "mean_stability": round(np.mean(stabilities), 4) if stabilities else 0,
            "mean_spread": round(np.mean(spreads), 4) if spreads else 0,
            "mean_familiarity": round(np.mean(familiarities), 4) if familiarities else 0,
            "count_social": n_social,
            "count_isolated": n_isolated,
            "count_deeply_connected": n_deeply,
            "reciprocal_pairs": reciprocal_count,
            "asymmetric_pairs": asymmetric_count,
            "fam_symmetry_mean": round(np.mean(symmetry_vals), 4) if symmetry_vals else 0,
            "fam_symmetry_std": round(np.std(symmetry_vals), 4) if symmetry_vals else 0,
            "att_overlap_mean": round(np.mean(att_overlaps), 1) if att_overlaps else 0,
            "att_overlap_pairs": len(att_overlaps),
        })

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

        # New labels
        for lid, lab in vl.labels.items():
            if lid not in vl.macro_nodes:
                cog.ensure_label(lid, lab["phase_sig"])
                if lid not in tracked:
                    tracked.add(lid)
                    all_births_after_mat.append({"lid": lid, "w": w})
                    label_meta[lid] = {
                        "birth_w": w, "death_w": None,
                        "phase_sig": lab["phase_sig"],
                        "n_core": len([n for n in lab["nodes"]
                                       if n in engine.state.alive_n]),
                    }

        # Dead labels
        for lid in list(cog.phi.keys()):
            if lid not in vl.labels and lid in tracked:
                label_meta[lid]["death_w"] = w
                all_deaths.append({"lid": lid, "w": w})
                cog.remove_label(lid)

        sec = time.time() - t0
        print(f"  seed={seed} w={w} vLb={len(vl.labels)} "
              f"recip={reciprocal_count} {sec:.0f}s")

    # ════════════════════════════════════════════════════════
    # SAVE Layer A: per_window CSV
    # ════════════════════════════════════════════════════════
    csv_a = outdir / "aggregates" / f"per_window_seed{seed}.csv"
    if window_rows:
        with open(csv_a, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=window_rows[0].keys())
            writer.writeheader()
            writer.writerows(window_rows)

    # ════════════════════════════════════════════════════════
    # SAVE Layer B: per_label CSV
    # ════════════════════════════════════════════════════════
    label_rows = []
    for lid, meta in label_meta.items():
        # Classify trajectory type
        traits = []
        ls = meta.get("last_social", 0)
        lst = meta.get("last_stability", 0)
        lsp = meta.get("last_spread", 0)
        lf = meta.get("last_familiarity", 0)

        if ls > 0.5: traits.append("social")
        elif ls < 0.15: traits.append("isolated")
        if lst > 0.5: traits.append("stable")
        if lsp > 0.85: traits.append("wide_att")
        elif lsp < 0.8: traits.append("focused_att")
        if lf > 10: traits.append("deep_conn")
        if meta["death_w"] is not None: traits.append("dead")

        label_rows.append({
            "seed": seed,
            "label_id": lid,
            "birth_window": meta["birth_w"],
            "death_window": meta.get("death_w", ""),
            "lifespan": meta.get("lifespan", 0),
            "alive": meta["death_w"] is None,
            "phase_sig": round(meta.get("phase_sig", 0), 4),
            "n_core": meta.get("n_core", 0),
            "last_social": round(meta.get("last_social", 0), 4),
            "last_stability": round(meta.get("last_stability", 0), 4),
            "last_spread": round(meta.get("last_spread", 0), 4),
            "last_familiarity": round(meta.get("last_familiarity", 0), 4),
            "last_partners": meta.get("last_partners", 0),
            "last_st_mean": meta.get("last_st_mean", 0),
            "last_st_std": meta.get("last_st_std", 0),
            "last_fam_max": meta.get("last_fam_max", 0),
            "last_att_nodes": meta.get("last_att_nodes", 0),
            "trajectory_type": "|".join(traits),
        })

    csv_b = outdir / "labels" / f"per_label_seed{seed}.csv"
    if label_rows:
        with open(csv_b, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=label_rows[0].keys())
            writer.writeheader()
            writer.writerows(label_rows)

    # ════════════════════════════════════════════════════════
    # SAVE Layer C: representative JSON
    # ════════════════════════════════════════════════════════
    # Select representatives
    repr_lids = set()

    # Highest social
    by_social = sorted(label_meta.items(),
                        key=lambda x: x[1].get("last_social", 0),
                        reverse=True)
    if by_social:
        repr_lids.add(by_social[0][0])

    # Lowest social (alive)
    by_social_alive = [(lid, m) for lid, m in label_meta.items()
                        if m["death_w"] is None and m.get("last_social") is not None]
    if by_social_alive:
        repr_lids.add(min(by_social_alive,
                           key=lambda x: x[1]["last_social"])[0])

    # Highest familiarity
    by_fam = sorted(label_meta.items(),
                     key=lambda x: x[1].get("last_familiarity", 0),
                     reverse=True)
    if by_fam:
        repr_lids.add(by_fam[0][0])

    # Longest survivor
    by_life = sorted(label_meta.items(),
                      key=lambda x: x[1].get("lifespan", 0),
                      reverse=True)
    if by_life:
        repr_lids.add(by_life[0][0])

    # Early death
    dead_sorted = sorted(all_deaths, key=lambda x: x["w"])
    if dead_sorted:
        repr_lids.add(dead_sorted[0]["lid"])

    # Focused attention
    by_spread = sorted(label_meta.items(),
                        key=lambda x: x[1].get("last_spread", 1.0))
    if by_spread:
        repr_lids.add(by_spread[0][0])

    # Wide attention
    if by_spread:
        repr_lids.add(by_spread[-1][0])

    # Most partners
    by_part = sorted(label_meta.items(),
                      key=lambda x: x[1].get("last_partners", 0),
                      reverse=True)
    if by_part:
        repr_lids.add(by_part[0][0])

    for lid in list(repr_lids)[:N_REPRESENTATIVES]:
        tl = repr_timelines.get(lid, [])
        if tl:
            rpath = outdir / "representatives" / f"seed{seed}_label{lid}.json"
            with open(rpath, "w") as f:
                json.dump({"label_id": lid,
                           "meta": label_meta.get(lid, {}),
                           "trajectory": tl}, f, indent=2, default=str)

    # ════════════════════════════════════════════════════════
    # SAVE Network: familiarity edges
    # ════════════════════════════════════════════════════════
    edge_rows = []
    alive_final = [lid for lid in tracked if lid in vl.labels
                   and lid in cog.familiarity]
    for lid_a in alive_final:
        fam_a = cog.familiarity.get(lid_a, {})
        for lid_b, val in fam_a.items():
            if val > 0.5:
                edge_rows.append({
                    "seed": seed,
                    "from": lid_a,
                    "to": lid_b,
                    "familiarity": round(val, 4),
                })

    csv_net = outdir / "network" / f"fam_edges_seed{seed}.csv"
    if edge_rows:
        with open(csv_net, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=edge_rows[0].keys())
            writer.writeheader()
            writer.writerows(edge_rows)

    # ════════════════════════════════════════════════════════
    # SAVE convergence bias
    # ════════════════════════════════════════════════════════
    conv_bias = {
        "seed": seed,
        "conv_near_mean": round(np.mean(conv_near_ratios), 4) if conv_near_ratios else None,
        "div_near_mean": round(np.mean(div_near_ratios), 4) if div_near_ratios else None,
        "conv_count": len(conv_near_ratios),
        "div_count": len(div_near_ratios),
        "ratio": round(
            np.mean(conv_near_ratios) / max(np.mean(div_near_ratios), 0.001), 2
        ) if conv_near_ratios and div_near_ratios else None,
    }

    meta_path = outdir / "aggregates" / f"conv_bias_seed{seed}.json"
    with open(meta_path, "w") as f:
        json.dump(conv_bias, f, indent=2)

    t_total = time.time() - t_start
    print(f"  seed={seed} DONE. {t_total/60:.1f} min. "
          f"deaths={len(all_deaths)} births={len(all_births_after_mat)} "
          f"conv_bias={conv_bias.get('ratio', 'N/A')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.6 Large-Scale Cognitive Baseline")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--maturation-windows", type=int, default=20)
    parser.add_argument("--tracking-windows", type=int, default=10)
    parser.add_argument("--window-steps", type=int, default=500)
    parser.add_argument("--tag", type=str, default="short",
                        help="Run tag: 'short' or 'long'")
    args = parser.parse_args()

    run(seed=args.seed,
        maturation_windows=args.maturation_windows,
        tracking_windows=args.tracking_windows,
        window_steps=args.window_steps,
        tag=args.tag)
