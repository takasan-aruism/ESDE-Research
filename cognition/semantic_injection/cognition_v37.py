#!/usr/bin/env python3
"""
ESDE Cognition v3.7 — Semantic Erosion & Internal Alteration
==============================================================
Phase : Cognition (v3.7)
Role  : Claude (Implementation)
Arch  : Gemini | Audit: GPT (Approved)

PURPOSE
-------
v3.6 proved transport exists. v3.7 asks: does transport reshape topology?

ZERO physics changes. New observation arrays track:
  1. Phase drift: per-node θ shift toward foreign concept over windows
  2. Erosion depth: how deep into concept territory drift penetrates
     (uncapped BFS — v3.6's 3-hop limit removed)
  3. Boundary hardening: local connectivity change at boundaries
  4. Core preservation: fraction of deep-core nodes unaffected

GPT-recommended layered measurement:
  - boundary drift (nodes with cross-concept neighbors)
  - near-core drift (1-2 hops from boundary into own territory)
  - deep-core drift (3+ hops from boundary)

USAGE
-----
  python cognition_v37.py --sanity
  parallel -j 20 python cognition_v37.py --seed {1} ::: $(seq 1 20)
  python cognition_v37.py --aggregate
"""

import numpy as np
import sys; from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parent.parent.parent / "ecology" / "engine"))

import engine_accel
from genesis_state import GenesisState as _GS
assert getattr(_GS.link_strength_sum, "__name__", "") == "_fast_link_strength_sum"
del _GS

import matplotlib; matplotlib.use("Agg")
import csv, json, time, argparse, math
from collections import Counter, defaultdict
from pathlib import Path
from dataclasses import asdict

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from chemistry import ChemistryEngine, ChemistryParams
from realization import RealizationOperator, RealizationParams
from autogrowth import AutoGrowthEngine, AutoGrowthParams
from intrusion import BoundaryIntrusionOperator, find_islands_sets

from v19g_canon import (
    OBSERVER_POLICY, HYST_THRESHOLD, LAMBDA, MU,
    K_LEVELS, WINDOW, QUIET_STEPS, BASE_PARAMS, ALL_SEEDS,
    INJECTION_STEPS, INJECT_INTERVAL, BETA, NODE_DECAY, BIAS, C_MAX,
    E_YIELD_SYN, E_YIELD_AUTO, TOPO_VAR,
    ctx_label, shannon, compute_J, select_k_star, SwitchEvent, init_fert,
)

# ================================================================
COG_N = 5000; COG_PLB = 0.007; COG_RATE = 0.002
COG_SEEDS = list(range(1, 21))
N_CONCEPTS = 3; PHASE_SPREAD = 0.3
CONCEPT_NAMES = {0: "A", 1: "B", 2: "C"}
DIFFUSION_PROB = 0.005; DIFFUSION_STRENGTH = 0.3
BOUNDARY_LINK_BOOST = 1.5; BRIDGE_S_THR = 0.15
GRID_ROWS = 2; GRID_COLS = 2; N_REGIONS = 4
MIN_C_NODES_FOR_VALID = 5
SCALE_THRESHOLDS = [0.10, 0.15, 0.20, 0.25, 0.30]
# v3.7: erosion threshold
DRIFT_EPSILON = 0.05  # minimum Δθ to count as "drifted"
OUTPUT_DIR = Path("outputs_v37")


# ================================================================
# STANDARD FUNCTIONS (unchanged)
# ================================================================
def assign_concepts(N):
    side = int(math.ceil(math.sqrt(N))); cm = {}; third = side/3.0
    for i in range(N):
        col = i % side
        cm[i] = 0 if col < third else (2 if col < 2*third else 1)
    return cm

def inject_concept_phases(state, cm):
    centers = {0: np.pi/4, 1: 3*np.pi/4, 2: np.pi/2}
    for nid, cid in cm.items():
        if nid < state.n_nodes:
            state.theta[nid] = (centers[cid] + state.rng.uniform(-PHASE_SPREAD, PHASE_SPREAD)) % (2*np.pi)
    return centers

def assign_regions(N):
    side = int(math.ceil(math.sqrt(N))); rm = {}
    for i in range(N):
        r, c = i//side, i%side
        rm[i] = min(r*GRID_ROWS//side, GRID_ROWS-1)*GRID_COLS + min(c*GRID_COLS//side, GRID_COLS-1)
    return rm

def compute_local_observer(nodes, prev, cur_k):
    if len(nodes) < MIN_C_NODES_FOR_VALID: return None, {}, {}, len(nodes)
    js = {k: compute_J(nodes, prev, k)[0] for k in K_LEVELS}
    return select_k_star(js, cur_k), js, {}, len(nodes)

def find_concept_boundary_nodes(state, cm):
    bnd = set()
    for n in state.alive_n:
        cn = cm.get(n, -1)
        for nb in state.neighbors(n):
            if nb in state.alive_n and cm.get(nb, -1) != cn: bnd.add(n); break
    return bnd


# ================================================================
# v3.7: CONCEPT DEPTH MAP
# ================================================================
def compute_concept_depth(N, cm, state):
    """
    For each node, compute its topological depth INTO its own concept
    territory, measured as shortest BFS distance from any cross-concept
    boundary. depth=0 means boundary node, depth=1 means 1 hop inside, etc.
    Uncapped — measures true depth.
    """
    bnd = find_concept_boundary_nodes(state, cm)
    depth = {i: -1 for i in range(N)}
    # BFS from boundary nodes inward
    queue = list(bnd)
    for n in queue:
        depth[n] = 0
    visited = set(bnd)
    d = 0
    while queue:
        next_q = []
        d += 1
        for n in queue:
            cn = cm.get(n, -1)
            for nb in state.neighbors(n):
                if nb not in visited and nb in state.alive_n and cm.get(nb, -1) == cn:
                    depth[nb] = d
                    visited.add(nb)
                    next_q.append(nb)
        queue = next_q
    return depth


# ================================================================
# DIFFUSION (v3.6 style — uncapped penetration)
# ================================================================
def apply_diffusion_tracked(state, cm, centers, bnd, rng):
    events = 0; flow = Counter()
    depth_hist = Counter()  # uncapped depth histogram
    chain_events = 0
    recent = {}
    for n in bnd:
        if rng.random() > DIFFUSION_PROB: continue
        cn = cm.get(n, -1)
        if cn < 0: continue
        dnb = [nb for nb in state.neighbors(n)
               if nb in state.alive_n and cm.get(nb,-1) >= 0 and cm.get(nb,-1) != cn]
        if not dnb: continue
        tnb = dnb[rng.randint(len(dnb))]
        tc = cm[tnb]
        d = (centers[tc] - state.theta[n] + np.pi) % (2*np.pi) - np.pi
        state.theta[n] = (state.theta[n] + DIFFUSION_STRENGTH * d) % (2*np.pi)
        events += 1; flow[(cn, tc)] += 1; recent[n] = (cn, tc)
        # Uncapped penetration BFS
        depth = 1; visited = {n}; frontier = {n}
        while True:
            nf = set()
            for fn in frontier:
                for nb in state.neighbors(fn):
                    if nb not in visited and nb in state.alive_n and cm.get(nb,-1) == tc:
                        if nb in bnd: nf.add(nb); visited.add(nb)
            if not nf: break
            depth += 1; frontier = nf
            if depth > 10: break  # safety cap (well beyond v3.6's 3)
        depth_hist[depth] += 1
    # Chain detection
    for n, (fc, tc) in recent.items():
        if tc == 2:
            for nb in state.neighbors(n):
                if nb in recent:
                    fc2, tc2 = recent[nb]
                    if fc2 == 2 and tc2 != fc and tc2 != 2: chain_events += 1
    return events, flow, depth_hist, chain_events


def boosted_seeding(state, cm, bnd, gs, gz, rng):
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
        p = min(bp*BOUNDARY_LINK_BOOST, 1.0) if al[idx] in bnd else bp
        if rng.random() < p:
            t = int(rng.choice(aa, p=pd))
            state.E[t] = min(1.0, state.E[t]+0.3)
            if state.Z[t]==0 and rng.random()<0.5:
                state.Z[t] = 1 if rng.random()<0.5 else 2


# ================================================================
# CONCEPT WINDOW METRICS (v3.4 base)
# ================================================================
def compute_concept_window(state, cm, rmap, islands_m):
    nc = N_CONCEPTS
    ci_count = {c:0 for c in range(nc)}; labeled = []
    for isl in islands_m:
        cn_isl = [n for n in isl if n in state.alive_n and int(state.Z[n])==3]
        if len(cn_isl) < 3: continue
        cc = Counter(cm.get(n,-1) for n in cn_isl); t = sum(cc.values())
        if t == 0: continue
        for c in range(nc):
            if cc.get(c,0)/t > 0.5:
                ci_count[c] += 1
                labeled.append((c, frozenset(n for n in isl if n in state.alive_n))); break
    tripartite = 0
    for isl in islands_m:
        cn_isl = [n for n in isl if n in state.alive_n and int(state.Z[n])==3]
        if len(cn_isl) < 3: continue
        cc = Counter(cm.get(n,-1) for n in cn_isl)
        if all(cc.get(c,0) > 0 for c in range(nc)): tripartite += 1
    bnd_l = 0; bnd_w = 0.0
    for (i,j) in state.alive_l:
        if cm.get(i,-1) != cm.get(j,-1): bnd_l += 1; bnd_w += state.S[(i,j)]
    all_c = [n for n in state.alive_n if int(state.Z[n])==3]
    cdist = Counter(cm.get(n,-1) for n in all_c); t = sum(cdist.values())
    ent = -sum(v/t*np.log2(v/t) for v in cdist.values() if v>0) if t>0 else 0
    obs = {}
    for r in range(N_REGIONS):
        rn = [n for n in all_c if rmap.get(n)==r]
        if not rn: obs[r]=-1; continue
        rc = Counter(cm.get(n,-1) for n in rn); b = rc.most_common(1)[0]
        obs[r] = b[0] if b[1]>len(rn)*0.3 else -1
    return {"ci_count": ci_count, "bnd_links": bnd_l, "bnd_weight": round(bnd_w,4),
            "entropy": round(ent,4), "obs": obs, "labeled": labeled,
            "tripartite": tripartite, "n_C": len(all_c)}

def compute_bridges(state, cm, prev):
    curr = {}
    for (i,j) in state.alive_l:
        if state.S[(i,j)] < BRIDGE_S_THR: continue
        if cm.get(i,-1) != cm.get(j,-1): curr[(i,j)] = state.S[(i,j)]
    ul = {}; pc = 0
    for k in curr:
        if k in prev: ul[k] = prev[k]+1; pc += 1
        else: ul[k] = 1
    ls = list(ul.values())
    return ul, {"n": len(curr), "persist": pc,
        "mean_life": round(np.mean(ls),2) if ls else 0,
        "max_life": max(ls) if ls else 0}


# ================================================================
# v3.7: EROSION & DRIFT ANALYSIS
# ================================================================
def compute_erosion_metrics(state, cm, centers, depth_map, theta_initial):
    """
    Compute per-concept erosion metrics by comparing current θ with initial θ.

    Returns per-concept dict with:
      drift_boundary: mean |Δθ| for depth=0 nodes
      drift_near_core: mean |Δθ| for depth 1-2
      drift_deep_core: mean |Δθ| for depth 3+
      erosion_depth: max depth where mean |Δθ| > DRIFT_EPSILON
      core_preservation: fraction of depth>=3 nodes with |Δθ| < DRIFT_EPSILON
      boundary_k_mean: mean link count for boundary nodes
    """
    results = {}
    for c in range(N_CONCEPTS):
        cn = CONCEPT_NAMES[c]
        target_center = centers[c]
        # Gather alive nodes of this concept
        nodes_by_depth = defaultdict(list)
        for n in state.alive_n:
            if cm.get(n, -1) != c: continue
            d = depth_map.get(n, -1)
            if d < 0: continue
            # Drift = angular distance from INITIAL θ
            dtheta = abs((state.theta[n] - theta_initial[n] + np.pi) % (2*np.pi) - np.pi)
            nodes_by_depth[d].append((n, dtheta))

        # Layered drift
        bnd_drifts = [dt for _, dt in nodes_by_depth.get(0, [])]
        near_drifts = [dt for d in [1, 2] for _, dt in nodes_by_depth.get(d, [])]
        deep_drifts = [dt for d in nodes_by_depth if d >= 3 for _, dt in nodes_by_depth[d]]

        drift_bnd = round(np.mean(bnd_drifts), 6) if bnd_drifts else 0
        drift_near = round(np.mean(near_drifts), 6) if near_drifts else 0
        drift_deep = round(np.mean(deep_drifts), 6) if deep_drifts else 0

        # Erosion depth: max depth where mean drift > epsilon
        erosion_d = 0
        for d in sorted(nodes_by_depth.keys()):
            dts = [dt for _, dt in nodes_by_depth[d]]
            if dts and np.mean(dts) > DRIFT_EPSILON:
                erosion_d = d

        # Core preservation: fraction of deep nodes unaffected
        if deep_drifts:
            core_pres = round(sum(1 for dt in deep_drifts if dt < DRIFT_EPSILON) / len(deep_drifts), 4)
        else:
            core_pres = 1.0

        # Boundary k (mean link count for boundary nodes)
        bnd_k_vals = []
        for n, _ in nodes_by_depth.get(0, []):
            lc = sum(1 for nb in state.neighbors(n) if nb in state.alive_n
                     and state.key(n, nb) in state.alive_l)
            bnd_k_vals.append(lc)
        bnd_k_mean = round(np.mean(bnd_k_vals), 2) if bnd_k_vals else 0

        results[cn] = {
            "drift_boundary": drift_bnd,
            "drift_near_core": drift_near,
            "drift_deep_core": drift_deep,
            "erosion_depth": erosion_d,
            "core_preservation": core_pres,
            "boundary_k_mean": bnd_k_mean,
            "n_boundary": len(bnd_drifts),
            "n_near_core": len(near_drifts),
            "n_deep_core": len(deep_drifts),
        }
    return results


# ================================================================
# MAIN SIMULATION
# ================================================================
def run_cognition(seed, N=COG_N, plb=COG_PLB, rate=COG_RATE, quiet_steps=QUIET_STEPS):
    p = dict(BASE_PARAMS); p["p_link_birth"] = plb
    state = GenesisState(N, C_MAX, seed)
    init_fert(state, TOPO_VAR, seed)
    cm = assign_concepts(N); centers = inject_concept_phases(state, cm)
    rmap = assign_regions(N)

    physics = GenesisPhysics(PhysicsParams(exclusion_enabled=True, resonance_enabled=True,
        phase_enabled=True, beta=BETA, decay_rate_node=NODE_DECAY, K_sync=0.1, alpha=0.0, gamma=1.0))
    chem = ChemistryEngine(ChemistryParams(enabled=True, E_thr=p["reaction_energy_threshold"],
        exothermic_release=p["exothermic_release_amount"], E_yield_syn=E_YIELD_SYN, E_yield_auto=E_YIELD_AUTO))
    realizer = RealizationOperator(RealizationParams(enabled=True, p_link_birth=plb,
        latent_to_active_threshold=p["latent_to_active_threshold"], latent_refresh_rate=p["latent_refresh_rate"]))
    grower = AutoGrowthEngine(AutoGrowthParams(enabled=True, auto_growth_rate=p["auto_growth_rate"]))
    intruder = BoundaryIntrusionOperator(intrusion_rate=rate)
    state.EXTINCTION = p["link_death_threshold"]

    gs = np.zeros(N); t0 = time.time(); node_intr = Counter()
    tot_diff = 0; tot_flow = Counter(); tot_depth = Counter(); tot_chains = 0

    # Injection
    for step in range(INJECTION_STEPS):
        if step % INJECT_INTERVAL == 0:
            tgts = physics.inject(state); chem.seed_on_injection(state, tgts or [])
        physics.step_pre_chemistry(state); chem.step(state)
        physics.step_resonance(state); grower.step(state)
        physics.step_decay_exclusion(state)

    # v3.7: record initial θ AFTER injection (this is the baseline)
    theta_initial = state.theta.copy()

    ks=[]; sw_ev=[]; marg=[]; png=None; ckg=None
    pnr={r:None for r in range(N_REGIONS)}; ckr={r:None for r in range(N_REGIONS)}
    rks={r:[] for r in range(N_REGIONS)}
    c_wisl={c:0 for c in range(N_CONCEPTS)}; c_mstr={c:0 for c in range(N_CONCEPTS)}
    c_str={c:0 for c in range(N_CONCEPTS)}
    pbr={}; tot_tri=0; wlogs=[]; clogs=[]
    # v3.7: erosion snapshots per window
    erosion_logs = []

    _t0=time.time(); _tw=quiet_steps//WINDOW

    for step in range(quiet_steps):
        realizer.step(state); physics.step_pre_chemistry(state)
        chem.step(state); physics.step_resonance(state)
        gs[:]=0; grower.step(state)
        for k in state.alive_l:
            r=state.R.get(k,0.0)
            if r>0:
                a=min(grower.params.auto_growth_rate*r, max(state.get_latent(k[0],k[1]),0))
                if a>0: gs[k[0]]+=a; gs[k[1]]+=a
        gz=float(gs.sum())
        pre_S={k:state.S[k] for k in state.alive_l}
        intruder.step(state)
        for k in state.alive_l:
            if k in pre_S and abs(state.S[k]-pre_S[k])>0.001:
                node_intr[k[0]]+=1; node_intr[k[1]]+=1
        physics.step_decay_exclusion(state)

        bnd = find_concept_boundary_nodes(state, cm)
        nd, sf, dh, nc = apply_diffusion_tracked(state, cm, centers, bnd, state.rng)
        tot_diff += nd; tot_flow += sf; tot_chains += nc
        for d in dh: tot_depth[d] += dh[d]

        boosted_seeding(state, cm, bnd, gs, gz, state.rng)

        if (step+1) % WINDOW == 0:
            wi = (step+1)//WINDOW
            _el = time.time()-_t0
            if wi > 0:
                _pw=_el/wi; _rem=_pw*(_tw-wi)
                if wi%5==0 or wi==_tw:
                    print(f"    win {wi}/{_tw} el={_el:.0f}s ETA={_rem:.0f}s", flush=True)

            isl_m = find_islands_sets(state, 0.20)
            isl_s = find_islands_sets(state, 0.30)
            isl_w = find_islands_sets(state, 0.10)
            nms={n:1 for i in isl_s for n in i}; nmm={n:1 for i in isl_m for n in i}
            nmw={n:1 for i in isl_w for n in i}
            bm=set()
            for isl in isl_m:
                for n in isl:
                    if n not in state.alive_n: continue
                    for nb in state.neighbors(n):
                        if nb in state.alive_n and nb not in isl: bm.add(n); break

            an=[]; ani=[]
            for i in state.alive_n:
                if int(state.Z[i])!=3: continue
                s=1 if i in nms else 0; m=1 if i in nmm else 0; w=1 if i in nmw else 0
                ctx={"r_bits":f"{s}{m}{w}","boundary_mid":1 if i in bm else 0,
                     "intrusion_bin":min(node_intr.get(i,0),2)}
                an.append(ctx); ani.append({"node_id":i,**ctx})
            nC=len(an)

            if an:
                jg={k:compute_J(an,png,k)[0] for k in K_LEVELS}
                nkg=select_k_star(jg,ckg)
                if ckg is not None and nkg!=ckg:
                    sw_ev.append(SwitchEvent(seed=seed,N=N,window=wi,step=step+1,
                        prev_k=ckg,new_k=nkg,margin=round(jg.get(nkg,0)-jg.get(ckg,0),6),
                        threshold=HYST_THRESHOLD,j3=round(jg.get(3,0),6),j4=round(jg.get(4,0),6),h3=0.,h4=0.))
                ckg=nkg; ks.append(nkg)
                mg=max(jg.values())-sorted(jg.values())[-2] if len(jg)>1 else 0
                marg.append(mg); png=an
            else: ks.append(ckg or 0); marg.append(0)

            wl={"seed":seed,"window":wi,"global_k":ckg or 0,"n_C":nC}
            df=0
            for r in range(N_REGIONS):
                rn=[nd for nd in ani if rmap.get(nd["node_id"])==r]
                rc=[{k:v for k,v in nd.items() if k!="node_id"} for nd in rn]
                nkr,_,_,rnc=compute_local_observer(rc,pnr[r],ckr[r])
                if nkr is not None: ckr[r]=nkr; pnr[r]=rc
                rks[r].append(ckr[r] or 0); wl[f"r{r}_k"]=ckr[r] or 0
                if (ckr[r] or 0)!=(ckg or 0): df=1
            wl["div"]=df

            cmet=compute_concept_window(state,cm,rmap,isl_m)
            tot_tri+=cmet["tripartite"]
            pbr,bs=compute_bridges(state,cm,pbr)
            for c in range(N_CONCEPTS):
                if cmet["ci_count"][c]>0:
                    c_str[c]+=1; c_wisl[c]+=1; c_mstr[c]=max(c_mstr[c],c_str[c])
                else: c_str[c]=0

            # v3.7: erosion measurement
            depth_map = compute_concept_depth(N, cm, state)
            eros = compute_erosion_metrics(state, cm, centers, depth_map, theta_initial)

            cl={"seed":seed,"win":wi,"tri":cmet["tripartite"],
                "bnd_links":cmet["bnd_links"],"ent":cmet["entropy"],
                "n_br":bs["n"],"persist_br":bs["persist"],"br_max":bs["max_life"],
                "gk":ckg or 0,"div":df}
            for c in range(N_CONCEPTS):
                cn=CONCEPT_NAMES[c]; cl[f"{cn}_isl"]=cmet["ci_count"][c]
                e = eros[cn]
                cl[f"{cn}_drift_bnd"]=e["drift_boundary"]
                cl[f"{cn}_drift_near"]=e["drift_near_core"]
                cl[f"{cn}_drift_deep"]=e["drift_deep_core"]
                cl[f"{cn}_erosion_d"]=e["erosion_depth"]
                cl[f"{cn}_core_pres"]=e["core_preservation"]
                cl[f"{cn}_bnd_k"]=e["boundary_k_mean"]
            clogs.append(cl); wlogs.append(wl)
            erosion_logs.append(eros)

    elapsed=time.time()-t0; nw=len(ks)
    kc=Counter(ks); dk=kc.most_common(1)[0][0] if kc else 0
    swc=sum(1 for i in range(1,len(ks)) if ks[i]!=ks[i-1])
    sw100=round(swc/max(nw-1,1)*100,1)
    dvf=[w.get("div",0) for w in wlogs]
    dr=round(sum(dvf)/max(len(dvf),1),4)

    cs={}
    for c in range(N_CONCEPTS):
        cn=CONCEPT_NAMES[c]
        cs[cn]={"persist":round(c_wisl[c]/max(nw,1),4),"max_streak":c_mstr[c]}

    obs_dom={}
    for r in range(N_REGIONS):
        rc_ctr=Counter()
        for cl in clogs:
            obs_c = None
            cmet_obs = None
            # Use last window's observer info
        # Simpler: use concept window obs from last window
    # Recompute from clogs not stored — use region k seqs
    # For simplicity, use final-window cmet
    if erosion_logs:
        final_eros = erosion_logs[-1]
    else:
        final_eros = {cn: {} for cn in CONCEPT_NAMES.values()}

    # Flow stats
    fac=tot_flow.get((0,2),0)+tot_flow.get((2,0),0)
    fbc=tot_flow.get((1,2),0)+tot_flow.get((2,1),0)
    fab=tot_flow.get((0,1),0)+tot_flow.get((1,0),0)
    mrat=round((fac+fbc)/max(fab,1),4)

    # Depth distribution
    dep_total=sum(tot_depth.values())
    dep_pct={}
    for d in sorted(tot_depth.keys()):
        dep_pct[d]=round(tot_depth[d]/max(dep_total,1)*100,2)
    mean_dep=round(sum(d*tot_depth[d] for d in tot_depth)/max(dep_total,1),3) if dep_total>0 else 0

    # v3.7: erosion summary (mean across windows for last 5 windows — late-run signal)
    late_windows = erosion_logs[-5:] if len(erosion_logs) >= 5 else erosion_logs
    erosion_summary = {}
    for cn in ["A","B","C"]:
        vals = [ew[cn] for ew in late_windows if cn in ew]
        if not vals:
            erosion_summary[cn] = {}; continue
        erosion_summary[cn] = {
            "drift_boundary": round(np.mean([v["drift_boundary"] for v in vals]),6),
            "drift_near_core": round(np.mean([v["drift_near_core"] for v in vals]),6),
            "drift_deep_core": round(np.mean([v["drift_deep_core"] for v in vals]),6),
            "erosion_depth": max(v["erosion_depth"] for v in vals),
            "core_preservation": round(np.mean([v["core_preservation"] for v in vals]),4),
            "boundary_k_mean": round(np.mean([v["boundary_k_mean"] for v in vals]),2),
        }

    # v3.7: drift progression (first vs last window)
    drift_progression = {}
    if len(erosion_logs) >= 2:
        first = erosion_logs[0]; last = erosion_logs[-1]
        for cn in ["A","B","C"]:
            if cn in first and cn in last:
                drift_progression[cn] = {
                    "bnd_first": first[cn]["drift_boundary"],
                    "bnd_last": last[cn]["drift_boundary"],
                    "bnd_delta": round(last[cn]["drift_boundary"] - first[cn]["drift_boundary"], 6),
                    "deep_first": first[cn]["drift_deep_core"],
                    "deep_last": last[cn]["drift_deep_core"],
                    "deep_delta": round(last[cn]["drift_deep_core"] - first[cn]["drift_deep_core"], 6),
                }

    result = {
        "N":N,"seed":int(seed),"quiet_steps":quiet_steps,"n_windows":nw,
        "global_dominant_k":dk,"global_sw100":sw100,"divergence_ratio":dr,
        "concept_summary":cs,
        "mean_entropy":round(np.mean([cl["ent"] for cl in clogs]),4),
        "total_tripartite":tot_tri,"total_diffusion":tot_diff,
        "flow_AC":fac,"flow_BC":fbc,"flow_AB":fab,"mediation_ratio":mrat,
        "depth_hist":{str(k):v for k,v in sorted(tot_depth.items())},
        "depth_pct":dep_pct,"mean_penetration_depth":mean_dep,
        "transport_chains":tot_chains,
        "mean_bridges":round(np.mean([cl["n_br"] for cl in clogs]),1),
        "max_bridge_life":max(cl["br_max"] for cl in clogs) if clogs else 0,
        # v3.7: erosion
        "erosion_summary":erosion_summary,
        "drift_progression":drift_progression,
        "elapsed":round(elapsed,1),
    }
    return result, wlogs, clogs, [asdict(se) for se in sw_ev]


# ================================================================
# AGGREGATE
# ================================================================
def aggregate():
    results=[]
    for f in sorted(OUTPUT_DIR.glob("seed_*.json")):
        if "_" in f.stem.split("seed_")[1]: continue
        with open(f) as fh: results.append(json.load(fh))
    if not results: print("  No results."); return
    n=len(results)

    print(f"\n{'='*80}")
    print(f"  ESDE Cognition v3.7 — Aggregate ({n} seeds)")
    print(f"{'='*80}")

    gk=Counter(r["global_dominant_k"] for r in results)
    print(f"\n  Ecology: k*={dict(gk)}")
    print(f"  Entropy: {np.mean([r['mean_entropy'] for r in results]):.4f}")
    tp=[r["total_tripartite"] for r in results]
    print(f"  Tripartite: mean={np.mean(tp):.1f}")

    print(f"\n  Flow Penetration (uncapped):")
    md=[r["mean_penetration_depth"] for r in results]
    print(f"    Mean depth: {np.mean(md):.3f}")
    # Aggregate depth distribution
    agg_depth = Counter()
    for r in results:
        for d, v in r["depth_hist"].items():
            agg_depth[int(d)] += v
    dtot = sum(agg_depth.values())
    print(f"    Distribution: " + " ".join(
        f"{d}hop={agg_depth[d]/dtot*100:.1f}%" for d in sorted(agg_depth.keys())))
    tc=[r["transport_chains"] for r in results]
    print(f"    Chains: mean={np.mean(tc):.1f}")

    print(f"\n  === EROSION ANALYSIS (v3.7 core) ===")
    for cn in ["A","B","C"]:
        print(f"\n  Concept {cn}:")
        # Late-window erosion
        db=[r["erosion_summary"][cn]["drift_boundary"] for r in results if cn in r["erosion_summary"] and r["erosion_summary"][cn]]
        dn=[r["erosion_summary"][cn]["drift_near_core"] for r in results if cn in r["erosion_summary"] and r["erosion_summary"][cn]]
        dd=[r["erosion_summary"][cn]["drift_deep_core"] for r in results if cn in r["erosion_summary"] and r["erosion_summary"][cn]]
        ed=[r["erosion_summary"][cn]["erosion_depth"] for r in results if cn in r["erosion_summary"] and r["erosion_summary"][cn]]
        cp=[r["erosion_summary"][cn]["core_preservation"] for r in results if cn in r["erosion_summary"] and r["erosion_summary"][cn]]
        bk=[r["erosion_summary"][cn]["boundary_k_mean"] for r in results if cn in r["erosion_summary"] and r["erosion_summary"][cn]]
        if db:
            print(f"    Drift boundary:  {np.mean(db):.6f} ± {np.std(db):.6f}")
            print(f"    Drift near-core: {np.mean(dn):.6f} ± {np.std(dn):.6f}")
            print(f"    Drift deep-core: {np.mean(dd):.6f} ± {np.std(dd):.6f}")
            print(f"    Erosion depth:   mean={np.mean(ed):.1f} max={max(ed)}")
            print(f"    Core preserved:  {np.mean(cp):.4f}")
            print(f"    Boundary k:      {np.mean(bk):.2f}")

        # Progression
        prog=[r["drift_progression"].get(cn,{}) for r in results]
        bnd_d=[p["bnd_delta"] for p in prog if "bnd_delta" in p]
        deep_d=[p["deep_delta"] for p in prog if "deep_delta" in p]
        if bnd_d:
            print(f"    Progression (first→last window):")
            print(f"      Boundary Δ: {np.mean(bnd_d):+.6f}")
            print(f"      Deep-core Δ: {np.mean(deep_d):+.6f}")

    # CSV
    rows=[]
    for r in results:
        row={"seed":r["seed"],"gk":r["global_dominant_k"],
            "sw100":r["global_sw100"],"div":r["divergence_ratio"],
            "entropy":r["mean_entropy"],"tri":r["total_tripartite"],
            "depth_mean":r["mean_penetration_depth"],"chains":r["transport_chains"]}
        for cn in ["A","B","C"]:
            es=r["erosion_summary"].get(cn,{})
            row[f"{cn}_drift_bnd"]=es.get("drift_boundary",0)
            row[f"{cn}_drift_near"]=es.get("drift_near_core",0)
            row[f"{cn}_drift_deep"]=es.get("drift_deep_core",0)
            row[f"{cn}_erosion_d"]=es.get("erosion_depth",0)
            row[f"{cn}_core_pres"]=es.get("core_preservation",0)
            row[f"{cn}_bnd_k"]=es.get("boundary_k_mean",0)
            dp=r["drift_progression"].get(cn,{})
            row[f"{cn}_bnd_delta"]=dp.get("bnd_delta",0)
            row[f"{cn}_deep_delta"]=dp.get("deep_delta",0)
        rows.append(row)
    csv_path=OUTPUT_DIR/"cognition_v37_summary.csv"
    with open(csv_path,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print(f"\n  CSV: {csv_path}")


# ================================================================
# MAIN
# ================================================================
def main():
    parser=argparse.ArgumentParser(description="ESDE Cognition v3.7 — Semantic Erosion")
    parser.add_argument("--seed",type=int,default=None)
    parser.add_argument("--N",type=int,default=COG_N)
    parser.add_argument("--plb",type=float,default=COG_PLB)
    parser.add_argument("--rate",type=float,default=COG_RATE)
    parser.add_argument("--quiet-steps",type=int,default=QUIET_STEPS)
    parser.add_argument("--aggregate",action="store_true")
    parser.add_argument("--sanity",action="store_true")
    args=parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)

    if args.sanity:
        print(f"  SANITY: N={args.N} seed=42 quiet=500")
        res,_,clogs,_=run_cognition(42,args.N,args.plb,args.rate,500)
        print(f"  k*={res['global_dominant_k']} ent={res['mean_entropy']:.4f}")
        print(f"  Tri={res['total_tripartite']} Depth={res['mean_penetration_depth']:.3f}")
        for cn in ["A","B","C"]:
            es=res["erosion_summary"].get(cn,{})
            if es:
                print(f"  {cn}: drift_bnd={es['drift_boundary']:.6f} "
                      f"drift_deep={es['drift_deep_core']:.6f} "
                      f"erosion_d={es['erosion_depth']} "
                      f"core_pres={es['core_preservation']:.4f} "
                      f"bnd_k={es['boundary_k_mean']:.2f}")
        print(f"  elapsed={res['elapsed']:.0f}s")
        print("  SANITY OK"); return

    if args.aggregate: aggregate(); return

    seeds=[args.seed] if args.seed else COG_SEEDS
    for seed in seeds:
        rf=OUTPUT_DIR/f"seed_{seed}.json"
        if rf.exists(): print(f"  seed={seed}: skip"); continue
        print(f"  seed={seed}...",flush=True)
        result,_,clogs,sw=run_cognition(seed,args.N,args.plb,args.rate,args.quiet_steps)
        with open(rf,"w") as f: json.dump(result,f,indent=2)
        if clogs:
            with open(OUTPUT_DIR/f"seed_{seed}_concept.csv","w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=clogs[0].keys()); w.writeheader(); w.writerows(clogs)
        if sw:
            with open(OUTPUT_DIR/f"seed_{seed}_switches.json","w") as f: json.dump(sw,f,indent=2)
        es=result["erosion_summary"]
        print(f"    k*={result['global_dominant_k']} "
              f"depth={result['mean_penetration_depth']:.3f} "
              f"A_eros_d={es.get('A',{}).get('erosion_depth',0)} "
              f"B_eros_d={es.get('B',{}).get('erosion_depth',0)} "
              f"C_eros_d={es.get('C',{}).get('erosion_depth',0)} "
              f"({result['elapsed']:.0f}s)")

if __name__=="__main__": main()
