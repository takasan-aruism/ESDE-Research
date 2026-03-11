#!/usr/bin/env python3
"""
ESDE Cognition v3.5 — Heterogeneous Loop Tension
==================================================
Phase : Cognition (v3.5)
Role  : Claude (Implementation)
Arch  : Gemini | Audit: GPT (Approved with Caution)

PURPOSE
-------
v3.4: tripartite loops exist but bridges die in 1 window.
Bottleneck is RETENTION, not formation.

v3.5 introduces decay dampening for links in resonant loops with
phase gradient (heterogeneous loops). This is a pure topological
physics adjustment — no concept-specific rules.

MECHANISM
---------
After standard physics decay, links qualifying as "heterogeneous loop
members" receive a partial strength recovery:

  Qualification: R_ij > 0 (in a cycle) AND cos(Δθ) < PHASE_GRAD_THR
  (i.e., endpoints are not phase-aligned — cross-concept or mixed)

  Recovery: S_ij is boosted to compensate (1 - dampen_factor) of decay.
  Effectively: decay_eff *= dampen_factor for qualifying links.

  dampen_factor sweep: 1.00 (baseline), 0.95 (mild), 0.90 (target)

ENGINE IS NOT MODIFIED. Dampening is applied as a post-decay correction
in the cognition loop.

USAGE
-----
  python cognition_v35.py --sanity
  python cognition_v35.py --sanity --dampen 0.90

  # Parameter sweep (GPT mandated)
  parallel -j 20 python cognition_v35.py --dampen {1} --seed {2} \
    ::: 1.00 0.95 0.90 ::: $(seq 1 20)

  python cognition_v35.py --aggregate
"""

import numpy as np
import sys; from pathlib import Path as _P  # noqa
sys.path.insert(0, str(_P(__file__).resolve().parent.parent.parent / "ecology" / "engine"))

import engine_accel
from genesis_state import GenesisState as _GS
assert getattr(_GS.link_strength_sum, "__name__", "") == "_fast_link_strength_sum", \
    "FATAL: engine_accel not loaded."
del _GS

import matplotlib
matplotlib.use("Agg")
import csv, json, time, argparse, math
from collections import Counter, defaultdict
from pathlib import Path
from dataclasses import dataclass, asdict

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from chemistry import ChemistryEngine, ChemistryParams
from realization import RealizationOperator, RealizationParams
from autogrowth import AutoGrowthEngine, AutoGrowthParams
from intrusion import BoundaryIntrusionOperator, find_islands_sets

from v19g_canon import (
    OBSERVER_POLICY, HYST_THRESHOLD, LAMBDA, MU,
    K_LEVELS, WINDOW, QUIET_STEPS,
    BASE_PARAMS, ALL_SEEDS,
    INJECTION_STEPS, INJECT_INTERVAL, BETA, NODE_DECAY, BIAS, C_MAX,
    E_YIELD_SYN, E_YIELD_AUTO, TOPO_VAR,
    ctx_label, shannon, compute_J, select_k_star, SwitchEvent,
    init_fert,
)

# ================================================================
# CONSTANTS
# ================================================================
COG_N           = 5000
COG_PLB         = 0.007
COG_RATE        = 0.002
COG_SEEDS_SMALL = list(range(1, 21))
N_CONCEPTS      = 3
PHASE_SPREAD    = 0.3
CONCEPT_NAMES   = {0: "A", 1: "B", 2: "C"}

DIFFUSION_PROB      = 0.005
DIFFUSION_STRENGTH  = 0.3
BOUNDARY_LINK_BOOST = 1.5

MERGE_WEIGHT_THR    = 5.0
MERGE_PHASE_THR     = 0.5
SPLIT_MIN_COMP_SIZE = 3
BRIDGE_S_THR        = 0.15

# v3.5: Heterogeneous Loop Tension
DAMPEN_BASELINE     = 1.00   # no change
DAMPEN_MILD         = 0.95
DAMPEN_TARGET       = 0.90
PHASE_GRAD_THR      = 0.8    # cos(Δθ) < this = "phase gradient present"
DECAY_RATE_LINK     = 0.05   # must match engine PhysicsParams default

GRID_ROWS = 2
GRID_COLS = 2
N_REGIONS = GRID_ROWS * GRID_COLS
MIN_C_NODES_FOR_VALID = 5

OUTPUT_DIR = Path("outputs_v35")


# ================================================================
# CONCEPT/REGION/OBSERVER (unchanged from v3.4)
# ================================================================
def assign_concepts(N):
    side = int(math.ceil(math.sqrt(N)))
    concept_map = {}
    third = side / 3.0
    for i in range(N):
        col = i % side
        if col < third:
            concept_map[i] = 0
        elif col < 2 * third:
            concept_map[i] = 2
        else:
            concept_map[i] = 1
    return concept_map

def inject_concept_phases(state, concept_map):
    centers = {0: np.pi / 4, 1: 3 * np.pi / 4, 2: np.pi / 2}
    for nid, cid in concept_map.items():
        if nid < state.n_nodes:
            state.theta[nid] = (centers[cid]
                + state.rng.uniform(-PHASE_SPREAD, PHASE_SPREAD)) % (2 * np.pi)
    return centers

def concept_zone_summary(cmap):
    c = Counter(cmap.values())
    return ", ".join(f"{CONCEPT_NAMES.get(k,'?')}={c[k]}" for k in sorted(c))

def assign_regions(N):
    side = int(math.ceil(math.sqrt(N)))
    rm = {}
    for i in range(N):
        r, c = i // side, i % side
        rm[i] = min(r * GRID_ROWS // side, GRID_ROWS-1) * GRID_COLS + min(c * GRID_COLS // side, GRID_COLS-1)
    return rm

def compute_local_observer(nodes, prev, cur_k):
    if len(nodes) < MIN_C_NODES_FOR_VALID:
        return None, {}, {}, len(nodes)
    js = {k: compute_J(nodes, prev, k)[0] for k in K_LEVELS}
    return select_k_star(js, cur_k), js, {}, len(nodes)

def find_concept_boundary_nodes(state, cmap):
    bnd = set()
    for n in state.alive_n:
        cn = cmap.get(n, -1)
        for nb in state.neighbors(n):
            if nb in state.alive_n and cmap.get(nb, -1) != cn:
                bnd.add(n); break
    return bnd


# ================================================================
# DIFFUSION + SEEDING (v3.2+)
# ================================================================
def apply_semantic_diffusion(state, cmap, centers, bnd_nodes, rng):
    events = 0; flow = Counter()
    for n in bnd_nodes:
        if rng.random() > DIFFUSION_PROB: continue
        cn = cmap.get(n, -1)
        if cn < 0: continue
        dnb = [nb for nb in state.neighbors(n)
               if nb in state.alive_n and cmap.get(nb,-1) != cn and cmap.get(nb,-1) >= 0]
        if not dnb: continue
        tnb = dnb[rng.randint(len(dnb))]
        tc = cmap[tnb]
        d = (centers[tc] - state.theta[n] + np.pi) % (2*np.pi) - np.pi
        state.theta[n] = (state.theta[n] + DIFFUSION_STRENGTH * d) % (2*np.pi)
        events += 1; flow[(cn, tc)] += 1
    return events, flow

def boosted_seeding(state, cmap, bnd, gs, gz, rng):
    al = list(state.alive_n); na = len(al)
    if na == 0: return
    aa = np.array(al)
    if BIAS > 0 and gz > 0:
        ga = gs[aa]; s = ga.sum()
        pd = ((1-BIAS)/na + BIAS*ga/s) if s > 0 else np.ones(na)/na
        if isinstance(pd, np.ndarray): pd /= pd.sum()
        else: pd = np.ones(na)/na
    else: pd = np.ones(na)/na
    bp = BASE_PARAMS["background_injection_prob"]
    for idx in range(na):
        p = min(bp * BOUNDARY_LINK_BOOST, 1.0) if al[idx] in bnd else bp
        if rng.random() < p:
            t = int(rng.choice(aa, p=pd))
            state.E[t] = min(1.0, state.E[t] + 0.3)
            if state.Z[t] == 0 and rng.random() < 0.5:
                state.Z[t] = 1 if rng.random() < 0.5 else 2


# ================================================================
# v3.5: HETEROGENEOUS LOOP TENSION (post-decay correction)
# ================================================================
def apply_loop_tension(state, dampen_factor):
    """
    For links with R_ij > 0 and phase gradient (cos(Δθ) < PHASE_GRAD_THR),
    partially reverse decay to simulate reduced effective decay rate.

    Standard decay: S *= (1 - eff)  where eff = decay_rate / (1 + beta * R)
    Target:         S *= (1 - eff * dampen)
    Correction:     S *= (1 - eff * dampen) / (1 - eff)

    Returns: count of dampened links.
    """
    if dampen_factor >= 1.0:
        return 0

    count = 0
    for k in state.alive_l:
        r_ij = state.R.get(k, 0.0)
        if r_ij <= 0:
            continue
        i, j = k
        cos_dt = np.cos(state.theta[j] - state.theta[i])
        if cos_dt >= PHASE_GRAD_THR:
            continue  # same-phase loop, no dampening needed

        eff = DECAY_RATE_LINK / (1.0 + BETA * r_ij)
        if eff <= 0 or eff >= 1:
            continue

        correction = (1.0 - eff * dampen_factor) / (1.0 - eff)
        state.S[k] *= correction
        state.S[k] = min(state.S[k], 1.0)  # cap
        count += 1

    return count


# ================================================================
# CONCEPT WINDOW METRICS (v3.4)
# ================================================================
def compute_concept_window(state, cmap, rmap, islands_m):
    nc = N_CONCEPTS
    ci_count = {c: 0 for c in range(nc)}
    ci_nodes = {c: 0 for c in range(nc)}
    labeled = []
    for isl in islands_m:
        cn_isl = [n for n in isl if n in state.alive_n and int(state.Z[n])==3]
        if len(cn_isl) < 3: continue
        cc = Counter(cmap.get(n,-1) for n in cn_isl)
        t = sum(cc.values())
        if t == 0: continue
        for c in range(nc):
            if cc.get(c,0)/t > 0.5:
                ci_count[c] += 1; ci_nodes[c] += cc[c]
                labeled.append((c, frozenset(n for n in isl if n in state.alive_n)))
                break
    tripartite = 0
    for isl in islands_m:
        cn_isl = [n for n in isl if n in state.alive_n and int(state.Z[n])==3]
        if len(cn_isl) < 3: continue
        cc = Counter(cmap.get(n,-1) for n in cn_isl)
        if all(cc.get(c,0) > 0 for c in range(nc)):
            tripartite += 1
    bnd_links = 0; bnd_weight = 0.0
    for (i,j) in state.alive_l:
        if cmap.get(i,-1) != cmap.get(j,-1):
            bnd_links += 1; bnd_weight += state.S[(i,j)]
    all_c = [n for n in state.alive_n if int(state.Z[n])==3]
    cdist = Counter(cmap.get(n,-1) for n in all_c)
    t = sum(cdist.values())
    ent = -sum(v/t*np.log2(v/t) for v in cdist.values() if v > 0) if t > 0 else 0
    obs = {}
    for r in range(N_REGIONS):
        rn = [n for n in all_c if rmap.get(n)==r]
        if not rn: obs[r] = -1; continue
        rc = Counter(cmap.get(n,-1) for n in rn)
        b = rc.most_common(1)[0]
        obs[r] = b[0] if b[1] > len(rn)*0.3 else -1
    return {"ci_count": ci_count, "ci_nodes": ci_nodes, "bnd_links": bnd_links,
            "bnd_weight": round(bnd_weight,4), "entropy": round(ent,4),
            "obs": obs, "labeled": labeled, "tripartite": tripartite,
            "n_C": len(all_c), "cc": dict(cdist)}

def compute_bridges(state, cmap, prev):
    curr = {}
    for (i,j) in state.alive_l:
        if state.S[(i,j)] < BRIDGE_S_THR: continue
        if cmap.get(i,-1) != cmap.get(j,-1):
            curr[(i,j)] = state.S[(i,j)]
    ul = {}; nc = 0; pc = 0
    for k in curr:
        if k in prev: ul[k] = prev[k]+1; pc += 1
        else: ul[k] = 1; nc += 1
    tw = sum(curr.values())
    ls = list(ul.values())
    pb = Counter()
    for (i,j) in curr:
        p = (min(cmap[i],cmap[j]), max(cmap[i],cmap[j]))
        pb[p] += 1
    return ul, {"n": len(curr), "new": nc, "persist": pc,
        "weight": round(tw,4), "mean_life": round(np.mean(ls),2) if ls else 0,
        "max_life": max(ls) if ls else 0, "pairs": dict(pb)}

def detect_merge_split(state, cmap, prev_lab, curr_lab):
    merges = []; splits = []
    for i,(ci,ni) in enumerate(curr_lab):
        for j,(cj,nj) in enumerate(curr_lab):
            if j<=i or ci==cj: continue
            cw=0; cc=0; pd=[]
            for n in ni:
                for nb in state.neighbors(n):
                    if nb in nj:
                        k=state.key(n,nb)
                        if k in state.alive_l:
                            cw+=state.S[k]; cc+=1
                            pd.append(state.theta[nb]-state.theta[n])
            if cw>=MERGE_WEIGHT_THR and pd:
                mc=float(np.mean(np.cos(pd)))
                if mc>MERGE_PHASE_THR:
                    merges.append({"c":(ci,cj),"w":round(cw,4),"cos":round(mc,4)})
    if prev_lab:
        ca=defaultdict(set)
        for(a,b)in state.alive_l:
            if state.S[(a,b)]>=0.20: ca[a].add(b); ca[b].add(a)
        for pc,pn in prev_lab:
            ap=frozenset(n for n in pn if n in state.alive_n)
            if len(ap)<SPLIT_MIN_COMP_SIZE*2: continue
            vis=set(); comps=[]
            for n in ap:
                if n in vis: continue
                c=set(); q=[n]
                while q:
                    nd=q.pop()
                    if nd in vis or nd not in ap: continue
                    vis.add(nd); c.add(nd)
                    for nb in ca.get(nd,set()):
                        if nb in ap and nb not in vis: q.append(nb)
                comps.append(c)
            sig=[c for c in comps if len(c)>=SPLIT_MIN_COMP_SIZE]
            if len(sig)>=2:
                splits.append({"c":pc,"frags":len(sig),
                    "sizes":sorted([len(c) for c in sig],reverse=True)})
    return merges, splits


# ================================================================
# MAIN SIMULATION
# ================================================================
def run_cognition(seed, N=COG_N, plb=COG_PLB, rate=COG_RATE,
                  quiet_steps=QUIET_STEPS, dampen=DAMPEN_TARGET):
    p = dict(BASE_PARAMS); p["p_link_birth"] = plb
    state = GenesisState(N, C_MAX, seed)
    init_fert(state, TOPO_VAR, seed)
    cmap = assign_concepts(N)
    centers = inject_concept_phases(state, cmap)
    rmap = assign_regions(N)

    physics = GenesisPhysics(PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True,
        phase_enabled=True, beta=BETA, decay_rate_node=NODE_DECAY,
        K_sync=0.1, alpha=0.0, gamma=1.0))
    chem = ChemistryEngine(ChemistryParams(enabled=True,
        E_thr=p["reaction_energy_threshold"],
        exothermic_release=p["exothermic_release_amount"],
        E_yield_syn=E_YIELD_SYN, E_yield_auto=E_YIELD_AUTO))
    realizer = RealizationOperator(RealizationParams(enabled=True,
        p_link_birth=plb,
        latent_to_active_threshold=p["latent_to_active_threshold"],
        latent_refresh_rate=p["latent_refresh_rate"]))
    grower = AutoGrowthEngine(AutoGrowthParams(enabled=True,
        auto_growth_rate=p["auto_growth_rate"]))
    intruder = BoundaryIntrusionOperator(intrusion_rate=rate)
    state.EXTINCTION = p["link_death_threshold"]

    gs = np.zeros(N); t0 = time.time()
    node_intr = Counter(); tot_diff = 0; tot_flow = Counter()
    tot_tension = 0  # v3.5: dampened link count

    for step in range(INJECTION_STEPS):
        if step % INJECT_INTERVAL == 0:
            tgts = physics.inject(state)
            chem.seed_on_injection(state, tgts or [])
        physics.step_pre_chemistry(state); chem.step(state)
        physics.step_resonance(state); grower.step(state)
        physics.step_decay_exclusion(state)

    ks = []; sw_ev = []; marg = []; png = None; ckg = None; isls = []
    pnr = {r: None for r in range(N_REGIONS)}
    ckr = {r: None for r in range(N_REGIONS)}
    rks = {r: [] for r in range(N_REGIONS)}
    c_str = {c:0 for c in range(N_CONCEPTS)}
    c_mstr = {c:0 for c in range(N_CONCEPTS)}
    c_wisl = {c:0 for c in range(N_CONCEPTS)}
    plab = []; tot_m = 0; tot_s = 0; pbr = {}
    tot_tri = 0; wlogs = []; clogs = []

    _t0 = time.time(); _tw = quiet_steps // WINDOW

    for step in range(quiet_steps):
        realizer.step(state); physics.step_pre_chemistry(state)
        chem.step(state); physics.step_resonance(state)
        gs[:] = 0; grower.step(state)
        for k in state.alive_l:
            r = state.R.get(k, 0.0)
            if r > 0:
                a = min(grower.params.auto_growth_rate * r,
                        max(state.get_latent(k[0], k[1]), 0))
                if a > 0: gs[k[0]] += a; gs[k[1]] += a
        gz = float(gs.sum())
        pre_S = {k: state.S[k] for k in state.alive_l}
        intruder.step(state)
        for k in state.alive_l:
            if k in pre_S and abs(state.S[k]-pre_S[k]) > 0.001:
                node_intr[k[0]] += 1; node_intr[k[1]] += 1
        physics.step_decay_exclusion(state)

        # v3.5: HETEROGENEOUS LOOP TENSION (post-decay correction)
        tot_tension += apply_loop_tension(state, dampen)

        bnd = find_concept_boundary_nodes(state, cmap)
        nd, sf = apply_semantic_diffusion(state, cmap, centers, bnd, state.rng)
        tot_diff += nd; tot_flow += sf
        boosted_seeding(state, cmap, bnd, gs, gz, state.rng)

        if (step+1) % WINDOW == 0:
            wi = (step+1) // WINDOW
            _el = time.time() - _t0
            if wi > 0:
                _pw = _el / wi; _rem = _pw * (_tw - wi)
                if wi % 5 == 0 or wi == _tw:
                    print(f"    win {wi}/{_tw} el={_el:.0f}s ETA={_rem:.0f}s", flush=True)

            isl_m = find_islands_sets(state, 0.20)
            isl_s = find_islands_sets(state, 0.30)
            isl_w = find_islands_sets(state, 0.10)
            nms = {n:1 for i in isl_s for n in i}
            nmm = {n:1 for i in isl_m for n in i}
            nmw = {n:1 for i in isl_w for n in i}
            bm = set()
            for isl in isl_m:
                for n in isl:
                    if n not in state.alive_n: continue
                    for nb in state.neighbors(n):
                        if nb in state.alive_n and nb not in isl: bm.add(n); break

            an = []; ani = []
            for i in state.alive_n:
                if int(state.Z[i]) != 3: continue
                s = 1 if i in nms else 0; m = 1 if i in nmm else 0; w = 1 if i in nmw else 0
                ctx = {"r_bits": f"{s}{m}{w}", "boundary_mid": 1 if i in bm else 0,
                       "intrusion_bin": min(node_intr.get(i,0), 2)}
                an.append(ctx); ani.append({"node_id": i, **ctx})
            nC = len(an)

            if an:
                jg = {k: compute_J(an, png, k)[0] for k in K_LEVELS}
                nkg = select_k_star(jg, ckg)
                if ckg is not None and nkg != ckg:
                    sw_ev.append(SwitchEvent(seed=seed, N=N, window=wi, step=step+1,
                        prev_k=ckg, new_k=nkg,
                        margin=round(jg.get(nkg,0)-jg.get(ckg,0),6),
                        threshold=HYST_THRESHOLD,
                        j3=round(jg.get(3,0),6), j4=round(jg.get(4,0),6), h3=0., h4=0.))
                ckg = nkg; ks.append(nkg)
                mg = max(jg.values()) - sorted(jg.values())[-2] if len(jg)>1 else 0
                marg.append(mg); png = an
            else:
                ks.append(ckg or 0); marg.append(0)
            isls.append({"n_C": nC, "n_isl": len(isl_m)})

            wl = {"seed": seed, "window": wi, "global_k": ckg or 0, "n_C": nC}
            df = 0
            for r in range(N_REGIONS):
                rn = [nd for nd in ani if rmap.get(nd["node_id"])==r]
                rc = [{k:v for k,v in nd.items() if k!="node_id"} for nd in rn]
                nkr, _, _, rnc = compute_local_observer(rc, pnr[r], ckr[r])
                if nkr is not None: ckr[r] = nkr; pnr[r] = rc
                rks[r].append(ckr[r] or 0)
                wl[f"r{r}_k"] = ckr[r] or 0
                if (ckr[r] or 0) != (ckg or 0): df = 1
            wl["div"] = df

            cm = compute_concept_window(state, cmap, rmap, isl_m)
            tot_tri += cm["tripartite"]
            cl = cm["labeled"]
            me, se = detect_merge_split(state, cmap, plab, cl)
            tot_m += len(me); tot_s += len(se); plab = cl
            pbr, bs = compute_bridges(state, cmap, pbr)

            for c in range(N_CONCEPTS):
                if cm["ci_count"][c] > 0:
                    c_str[c] += 1; c_wisl[c] += 1
                    c_mstr[c] = max(c_mstr[c], c_str[c])
                else: c_str[c] = 0

            cl_row = {"seed": seed, "win": wi, "tri": cm["tripartite"],
                "bnd_links": cm["bnd_links"], "bnd_w": cm["bnd_weight"],
                "ent": cm["entropy"], "n_br": bs["n"], "persist_br": bs["persist"],
                "br_life": bs["mean_life"], "br_max": bs["max_life"],
                "br_AC": bs["pairs"].get((0,2),0), "br_BC": bs["pairs"].get((1,2),0),
                "br_AB": bs["pairs"].get((0,1),0),
                "gk": ckg or 0, "div": df, "merge": len(me), "split": len(se)}
            for c in range(N_CONCEPTS):
                cl_row[f"{CONCEPT_NAMES[c]}_isl"] = cm["ci_count"][c]
            for r in range(N_REGIONS):
                cl_row[f"r{r}_c"] = CONCEPT_NAMES.get(cm["obs"][r], "?")
            clogs.append(cl_row); wlogs.append(wl)

    elapsed = time.time() - t0; nw = len(ks)
    kc = Counter(ks); dk = kc.most_common(1)[0][0] if kc else 0
    swc = sum(1 for i in range(1,len(ks)) if ks[i]!=ks[i-1])
    sw100 = round(swc/max(nw-1,1)*100, 1)
    dvf = [w.get("div",0) for w in wlogs]
    dr = round(sum(dvf)/max(len(dvf),1), 4)

    cs = {}
    for c in range(N_CONCEPTS):
        cn = CONCEPT_NAMES[c]
        cs[cn] = {"persist": round(c_wisl[c]/max(nw,1),4), "max_streak": c_mstr[c],
            "mean_isl": round(np.mean([cl[f"{cn}_isl"] for cl in clogs]),2)}

    obs_dom = {}
    for r in range(N_REGIONS):
        rc = Counter(cl[f"r{r}_c"] for cl in clogs)
        obs_dom[f"r{r}"] = rc.most_common(1)[0][0] if rc else "?"

    # Flow
    fac = tot_flow.get((0,2),0)+tot_flow.get((2,0),0)
    fbc = tot_flow.get((1,2),0)+tot_flow.get((2,1),0)
    fab = tot_flow.get((0,1),0)+tot_flow.get((1,0),0)
    mrat = round((fac+fbc)/max(fab,1), 4)

    bn = [cl["n_br"] for cl in clogs]
    bp = [cl["persist_br"] for cl in clogs]
    bl = [cl["br_life"] for cl in clogs]
    bm = [cl["br_max"] for cl in clogs]

    # v3.5: retention gain vs v3.4 baseline
    v34_bridge_life = 1.0  # v3.4 observed baseline
    retention_gain = round(np.mean(bl) - v34_bridge_life, 4) if bl else 0

    result = {
        "N": N, "seed": int(seed), "dampen_factor": dampen,
        "quiet_steps": quiet_steps, "n_windows": nw,
        "global_dominant_k": dk, "global_sw100": sw100,
        "divergence_ratio": dr,
        "concept_summary": cs,
        "mean_entropy": round(np.mean([cl["ent"] for cl in clogs]),4),
        "observer_dominant": obs_dom,
        "merge_count": tot_m, "split_count": tot_s,
        "total_tripartite": tot_tri,
        "mean_tripartite": round(np.mean([cl["tri"] for cl in clogs]),2),
        "total_diffusion": tot_diff,
        "flow_AC": fac, "flow_BC": fbc, "flow_AB": fab,
        "mediation_ratio": mrat,
        "mean_bridges": round(np.mean(bn),1),
        "mean_persist_bridges": round(np.mean(bp),1),
        "mean_bridge_life": round(np.mean(bl),2),
        "max_bridge_life": max(bm) if bm else 0,
        "mean_bridges_AC": round(np.mean([cl["br_AC"] for cl in clogs]),1),
        "mean_bridges_BC": round(np.mean([cl["br_BC"] for cl in clogs]),1),
        "mean_bridges_AB": round(np.mean([cl["br_AB"] for cl in clogs]),1),
        "total_tension_events": tot_tension,
        "retention_gain": retention_gain,
        "elapsed": round(elapsed,1),
    }
    return result, wlogs, clogs, [asdict(se) for se in sw_ev]


# ================================================================
# AGGREGATE
# ================================================================
def aggregate():
    results = []
    for f in sorted(OUTPUT_DIR.glob("seed_*.json")):
        if "_" in f.stem.split("seed_")[1]: continue
        with open(f) as fh: results.append(json.load(fh))
    if not results: print("  No results."); return

    # Group by dampen factor
    by_d = defaultdict(list)
    for r in results: by_d[r["dampen_factor"]].append(r)

    print(f"\n{'='*80}")
    print(f"  ESDE Cognition v3.5 — Aggregate ({len(results)} runs)")
    print(f"{'='*80}")

    for d in sorted(by_d):
        rs = by_d[d]; n = len(rs)
        print(f"\n  --- dampen_factor = {d} ({n} seeds) ---")
        gk = Counter(r["global_dominant_k"] for r in rs)
        print(f"  Ecology: k*={dict(gk)}")
        print(f"  Entropy: {np.mean([r['mean_entropy'] for r in rs]):.4f}")
        for cn in ["A","B","C"]:
            p = [r["concept_summary"][cn]["persist"] for r in rs]
            print(f"  {cn}_persist: {np.mean(p):.3f}±{np.std(p):.3f}")
        tp = [r["total_tripartite"] for r in rs]
        print(f"  Tripartite: mean={np.mean(tp):.1f} max={max(tp)} >0: {sum(1 for x in tp if x>0)}/{n}")
        pb = [r["mean_persist_bridges"] for r in rs]
        ml = [r["mean_bridge_life"] for r in rs]
        mx = [r["max_bridge_life"] for r in rs]
        rg = [r["retention_gain"] for r in rs]
        print(f"  Bridges: persist={np.mean(pb):.1f} life={np.mean(ml):.2f} "
              f"max={max(mx)} retention_gain={np.mean(rg):.4f}")
        mc = [r["merge_count"] for r in rs]
        sc = [r["split_count"] for r in rs]
        print(f"  Merge={sum(mc)} Split={sum(sc)}")
        te = [r["total_tension_events"] for r in rs]
        print(f"  Tension events: {np.mean(te):.0f}/run")

    # CSV (all conditions)
    rows = []
    for r in results:
        row = {"seed": r["seed"], "dampen": r["dampen_factor"],
            "gk": r["global_dominant_k"], "sw100": r["global_sw100"],
            "div": r["divergence_ratio"], "entropy": r["mean_entropy"],
            "merge": r["merge_count"], "split": r["split_count"],
            "tri": r["total_tripartite"], "diffusion": r["total_diffusion"],
            "bridges": r["mean_bridges"], "persist_br": r["mean_persist_bridges"],
            "br_life": r["mean_bridge_life"], "br_max": r["max_bridge_life"],
            "br_AC": r["mean_bridges_AC"], "br_BC": r["mean_bridges_BC"],
            "br_AB": r["mean_bridges_AB"],
            "tension": r["total_tension_events"], "retain_gain": r["retention_gain"]}
        for cn in ["A","B","C"]:
            row[f"{cn}_persist"] = r["concept_summary"][cn]["persist"]
        for ri in range(N_REGIONS):
            row[f"r{ri}_c"] = r["observer_dominant"][f"r{ri}"]
        rows.append(row)
    csv_path = OUTPUT_DIR / "cognition_v35_summary.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"\n  CSV: {csv_path}")


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(description="ESDE Cognition v3.5")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--N", type=int, default=COG_N)
    parser.add_argument("--plb", type=float, default=COG_PLB)
    parser.add_argument("--rate", type=float, default=COG_RATE)
    parser.add_argument("--quiet-steps", type=int, default=QUIET_STEPS)
    parser.add_argument("--dampen", type=float, default=DAMPEN_TARGET)
    parser.add_argument("--aggregate", action="store_true")
    parser.add_argument("--sanity", action="store_true")
    args = parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.sanity:
        print(f"  SANITY: N={args.N} dampen={args.dampen} seed=42 quiet=500")
        cmap = assign_concepts(args.N)
        print(f"  Zones: {concept_zone_summary(cmap)}")
        res,_,_,_ = run_cognition(42, args.N, args.plb, args.rate, 500, args.dampen)
        print(f"  k*={res['global_dominant_k']} ent={res['mean_entropy']:.4f}")
        for cn in ["A","B","C"]:
            print(f"  {cn}: persist={res['concept_summary'][cn]['persist']:.2f}")
        print(f"  Tri={res['total_tripartite']} "
              f"Bridges: persist={res['mean_persist_bridges']:.1f} "
              f"life={res['mean_bridge_life']:.2f} max={res['max_bridge_life']}")
        print(f"  Tension={res['total_tension_events']} "
              f"Retain_gain={res['retention_gain']:.4f}")
        print(f"  Merge={res['merge_count']} Split={res['split_count']}")
        print(f"  elapsed={res['elapsed']:.0f}s")
        print("  SANITY OK")
        return

    if args.aggregate: aggregate(); return

    seeds = [args.seed] if args.seed else COG_SEEDS_SMALL
    for seed in seeds:
        rf = OUTPUT_DIR / f"seed_{seed}.json"
        if rf.exists(): print(f"  seed={seed}: skip"); continue
        print(f"  seed={seed} dampen={args.dampen}...", flush=True)
        result,_,clogs,sw = run_cognition(
            seed, args.N, args.plb, args.rate, args.quiet_steps, args.dampen)
        with open(rf, "w") as f: json.dump(result, f, indent=2)
        if clogs:
            with open(OUTPUT_DIR / f"seed_{seed}_concept.csv", "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=clogs[0].keys())
                w.writeheader(); w.writerows(clogs)
        if sw:
            with open(OUTPUT_DIR / f"seed_{seed}_switches.json", "w") as f:
                json.dump(sw, f, indent=2)
        print(f"    k*={result['global_dominant_k']} tri={result['total_tripartite']} "
              f"persist_br={result['mean_persist_bridges']:.1f} "
              f"max_life={result['max_bridge_life']} "
              f"tension={result['total_tension_events']} "
              f"({result['elapsed']:.0f}s)")

if __name__ == "__main__":
    main()
