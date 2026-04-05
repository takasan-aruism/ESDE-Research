#!/usr/bin/env python3
"""
ESDE v9.4+ — Step-Level World Change Log v2
=============================================
Spatial perception: once per window (fixed landscape).
Structural perception: every step (dynamic relationships).

Tracks GPT §4.1-4.4:
  4.1 spatial-only persistence
  4.2 structural emergence (spatial-only → structural)
  4.3 structural disappearance (structural → gone)
  4.4 spatial-structural gap

USAGE:
  python v94_worldlog.py --seed 42
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
# SPATIAL PERCEPTION (once per window)
# ================================================================
def compute_spatial(state, label, torus_sub, max_hops):
    """BFS on torus. Returns set of visible nodes."""
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
# STRUCTURAL PERCEPTION (every step)
# ================================================================
def compute_structural(core, max_hops, link_adj, alive_n):
    """BFS on alive links. Returns set of reachable nodes."""
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
    """Build alive link adjacency dict."""
    adj = defaultdict(set)
    for lk in state.alive_l:
        n1, n2 = lk
        adj[n1].add(n2)
        adj[n2].add(n1)
    return adj


# ================================================================
# FIELD ANALYSIS
# ================================================================
def analyze_structural(state, struct_set, core, phase_sig, node_to_label, lid):
    """Quick stats for structural field."""
    if not struct_set:
        return {"total": 0, "n_seen": 0, "wild": 0,
                "near_phase_ratio": 0.0, "n_links": 0, "mean_S": 0.0}

    wild = 0
    other_labels = set()
    for n in struct_set:
        if n in core:
            continue
        owner = node_to_label.get(n)
        if owner is not None and owner != lid:
            other_labels.add(owner)
        else:
            wild += 1

    # Phase
    near = 0
    for n in struct_set:
        d = abs(float(state.theta[n]) - phase_sig)
        if d > math.pi:
            d = 2 * math.pi - d
        if d < math.pi / 4:
            near += 1

    # Links within structural field
    n_links = 0
    s_sum = 0.0
    for lk in state.alive_l:
        if lk[0] in struct_set and lk[1] in struct_set:
            n_links += 1
            s_sum += state.S.get(lk, 0.0)

    return {
        "total": len(struct_set),
        "n_seen": len(other_labels),
        "other_labels": sorted(other_labels),
        "wild": wild,
        "near_phase_ratio": round(near / max(1, len(struct_set)), 4),
        "n_links": n_links,
        "mean_S": round(s_sum / max(1, n_links), 4),
    }


# ================================================================
# MAIN
# ================================================================
def run(seed=42, maturation_windows=20, tracking_windows=5,
        window_steps=500, case_labels=None, top_k=10):

    if case_labels is None:
        case_labels = [87, 101, 112]

    print(f"\n{'='*65}")
    print(f"  ESDE v9.4+ — Step-Level World Change Log v2")
    print(f"  seed={seed} mat={maturation_windows} track={tracking_windows}")
    print(f"  steps/win={window_steps} top_k={top_k}")
    print(f"  spatial=1/window  structural=every step")
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

    engine.run_injection()
    print(f"  Injection done. links={len(engine.state.alive_l)}")

    # Maturation
    print(f"  Maturation ({maturation_windows} windows)...")
    for w in range(maturation_windows):
        engine.step_window(steps=window_steps)
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

    step_log = defaultdict(list)
    bg_prob = BASE_PARAMS["background_injection_prob"]

    for tw in range(tracking_windows):
        w = maturation_windows + tw
        t0 = time.time()

        # ── Spatial perception: once at window start ──
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

        # ── Step-by-step physics + structural perception ──
        prev_structural = {}

        for step in range(window_steps):
            global_step = tw * window_steps + step

            # Physics step (canon-compliant)
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

            # ── Structural perception (every step) ──
            link_adj = build_link_adj(engine.state)

            for lid in list(spatial_fields.keys()):
                if lid not in vl.labels:
                    continue
                sp_set, core, max_hops = spatial_fields[lid]
                struct_set = compute_structural(
                    core, max_hops, link_adj, engine.state.alive_n)

                # §4.1-4.3: Spatial-structural transitions
                sp_only = sp_set - struct_set
                st_only = struct_set - sp_set
                overlap = sp_set & struct_set

                emerged = set()
                disappeared = set()
                if lid in prev_structural:
                    prev_st = prev_structural[lid]
                    emerged = struct_set - prev_st
                    disappeared = prev_st - struct_set

                stats = analyze_structural(
                    engine.state, struct_set, core,
                    vl.labels[lid]["phase_sig"], node_to_label, lid)

                step_log[lid].append({
                    "w": w, "step": step,
                    "sp_total": len(sp_set),
                    "st_total": stats["total"],
                    "overlap": len(overlap),
                    "sp_only": len(sp_only),
                    "st_only": len(st_only),
                    "emerged": len(emerged),
                    "disappeared": len(disappeared),
                    "st_n_seen": stats["n_seen"],
                    "st_near_phase": stats["near_phase_ratio"],
                    "st_links": stats["n_links"],
                    "st_mean_S": stats["mean_S"],
                })

                prev_structural[lid] = struct_set

        # ── End of window: virtual layer step ──
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

        sec = time.time() - t0
        total_emerged = sum(e["emerged"] for lid in spatial_fields
                            for e in step_log[lid] if e["w"] == w)
        total_disappeared = sum(e["disappeared"] for lid in spatial_fields
                                for e in step_log[lid] if e["w"] == w)

        print(f"  w={w:>3} links={len(engine.state.alive_l):>5} "
              f"vLb={len(vl.labels):>3} "
              f"emerged={total_emerged} disappeared={total_disappeared} "
              f"{sec:.0f}s")

    # ════════════════════════════════════════════════════════
    # ANALYSIS
    # ════════════════════════════════════════════════════════
    print(f"\n{'='*65}")
    print(f"  SPATIAL-STRUCTURAL ANALYSIS")
    print(f"{'='*65}")

    for lid in sorted(tracked):
        entries = step_log.get(lid, [])
        if len(entries) < 10:
            continue

        sp_totals = [e["sp_total"] for e in entries]
        st_totals = [e["st_total"] for e in entries]
        overlaps = [e["overlap"] for e in entries]
        sp_onlys = [e["sp_only"] for e in entries]
        st_onlys = [e["st_only"] for e in entries]
        emerged = [e["emerged"] for e in entries]
        disappeared = [e["disappeared"] for e in entries]
        st_seen = [e["st_n_seen"] for e in entries]
        gaps = [sp - st for sp, st in zip(sp_totals, st_totals)]

        print(f"\n  --- Label {lid} ({len(entries)} steps) ---")
        print(f"    Spatial (fixed): {np.mean(sp_totals):.0f}")
        print(f"    Structural: mean={np.mean(st_totals):.0f} "
              f"std={np.std(st_totals):.0f} "
              f"min={min(st_totals)} max={max(st_totals)}")
        print(f"    §4.4 Gap: mean={np.mean(gaps):.0f} "
              f"({np.mean(gaps)/np.mean(sp_totals)*100:.0f}% of spatial)")
        print(f"    Overlap: mean={np.mean(overlaps):.0f}")
        print(f"    sp_only: mean={np.mean(sp_onlys):.0f}")
        print(f"    st_only: mean={np.mean(st_onlys):.0f}")
        print(f"    §4.2 Emerged/step: mean={np.mean(emerged):.1f} "
              f"max={max(emerged)}")
        print(f"    §4.3 Disappeared/step: mean={np.mean(disappeared):.1f} "
              f"max={max(disappeared)}")
        print(f"    Structural n_seen: mean={np.mean(st_seen):.1f}")

        if len(st_totals) >= 2:
            diffs = [abs(st_totals[i] - st_totals[i-1])
                     for i in range(1, len(st_totals))]
            print(f"    Step-to-step Δstructural: mean={np.mean(diffs):.1f} "
                  f"max={max(diffs)}")

    # ── Case Study Timelines ──
    print(f"\n{'='*65}")
    print(f"  CASE STUDY STEP TIMELINES (first 30 steps per window)")
    print(f"{'='*65}")

    for lid in case_labels:
        entries = step_log.get(lid, [])
        if not entries:
            print(f"\n  Label {lid}: NOT FOUND")
            continue

        print(f"\n  --- Label {lid} ---")
        print(f"  {'step':>5} {'sp':>4} {'st':>4} {'ovlp':>4} "
              f"{'spO':>4} {'stO':>4} {'emrg':>4} {'disp':>4} "
              f"{'seen':>4} {'near%':>6}")
        print(f"  {'-'*50}")

        shown = 0
        prev_w = None
        for e in entries:
            if e["w"] != prev_w:
                prev_w = e["w"]
                shown = 0
                if prev_w > maturation_windows:
                    print(f"  {'--- window ' + str(e['w']) + ' ---':^50}")
            if shown < 30:
                print(f"  {e['step']:>5} {e['sp_total']:>4} "
                      f"{e['st_total']:>4} {e['overlap']:>4} "
                      f"{e['sp_only']:>4} {e['st_only']:>4} "
                      f"{e['emerged']:>4} {e['disappeared']:>4} "
                      f"{e['st_n_seen']:>4} "
                      f"{e['st_near_phase']*100:>5.1f}%")
                shown += 1

    t_total = time.time() - t_start
    print(f"\n  Total time: {t_total/60:.1f} min")

    # ── Save ──
    outdir = Path(f"diag_v94_worldlog_seed{seed}")
    outdir.mkdir(exist_ok=True)

    save_log = {str(lid): entries for lid, entries in step_log.items()}
    with open(outdir / "step_log.json", "w") as f:
        json.dump(save_log, f)

    summary = {}
    for lid in tracked:
        entries = step_log.get(lid, [])
        if not entries:
            continue
        summary[str(lid)] = {
            "n_steps": len(entries),
            "spatial_mean": round(np.mean([e["sp_total"] for e in entries]), 1),
            "structural_mean": round(np.mean([e["st_total"] for e in entries]), 1),
            "structural_std": round(np.std([e["st_total"] for e in entries]), 1),
            "gap_mean": round(np.mean([e["sp_total"] - e["st_total"]
                                        for e in entries]), 1),
            "emerged_mean": round(np.mean([e["emerged"] for e in entries]), 2),
            "disappeared_mean": round(np.mean([e["disappeared"] for e in entries]), 2),
            "structural_n_seen_mean": round(
                np.mean([e["st_n_seen"] for e in entries]), 2),
        }
    with open(outdir / "label_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"  Saved: {outdir}/step_log.json")
    print(f"  Saved: {outdir}/label_summary.json")
    print(f"\n{'='*65}")
    print(f"  END World Change Log v2")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESDE v9.4+ Step-Level World Change Log v2")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--maturation-windows", type=int, default=20)
    parser.add_argument("--tracking-windows", type=int, default=5)
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
