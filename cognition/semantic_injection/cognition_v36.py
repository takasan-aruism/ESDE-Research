#!/usr/bin/env python3
"""
ESDE Cognition v3.6 — Semantic Flow & Multi-Scale Observation
===============================================================
Phase : Cognition (v3.6)
Role  : Claude (Implementation)
Arch  : Gemini | Audit: GPT (Approved)

PURPOSE
-------
v3.5 proved: bridge instability is caused by phase geometry, not decay.
v3.6 shifts from static bridge analysis to dynamic semantic flow.

ZERO physics changes. All additions are observation/instrumentation.

NEW OBSERVABLES
----------------
  1. flow_penetration_depth: how many hops a diffusion event travels
     across a concept boundary before encountering same-concept territory
  2. transport_chain_count: A→C→B multi-step mediation chains
  3. flow_retention_profile: histogram of 1-step, 2-step, 3+ step penetration
  4. scale_variance_index: island boundary divergence across S thresholds
     (0.10, 0.15, 0.20, 0.25, 0.30) — do islands shift with resolution?

USAGE
-----
  python cognition_v36.py --sanity
  parallel -j 20 python cognition_v36.py --seed {1} ::: $(seq 1 20)
  python cognition_v36.py --aggregate
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
BOUNDARY_LINK_BOOST = 1.5
BRIDGE_S_THR = 0.15
GRID_ROWS = 2; GRID_COLS = 2; N_REGIONS = 4
MIN_C_NODES_FOR_VALID = 5
# v3.6: multi-scale thresholds
SCALE_THRESHOLDS = [0.10, 0.15, 0.20, 0.25, 0.30]
OUTPUT_DIR = Path("outputs_v36")

# ================================================================
# STANDARD FUNCTIONS (unchanged from v3.4)
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
        p = min(bp * BOUNDARY_LINK_BOOST, 1.0) if al[idx] in bnd else bp
        if rng.random() < p:
            t = int(rng.choice(aa, p=pd))
            state.E[t] = min(1.0, state.E[t]+0.3)
            if state.Z[t]==0 and rng.random()<0.5:
                state.Z[t] = 1 if rng.random()<0.5 else 2


# ================================================================
# v3.6: DIFFUSION WITH PENETRATION TRACKING
# ================================================================
def apply_diffusion_with_tracking(state, cm, centers, bnd, rng):
    """
    Same diffusion as v3.2+, but also tracks penetration depth:
    after a diffusion event at node n, count how many hops into
    the target concept's territory the chain extends (BFS along
    same-target-concept neighbors that are also boundary nodes).

    Returns: (n_events, flow_counter, depth_histogram, chain_count)
    depth_histogram: {1: count, 2: count, 3: count} (3 = 3+)
    chain_count: number of A→C→B or B→C→A complete chains detected
    """
    events = 0; flow = Counter()
    depth_hist = {1: 0, 2: 0, 3: 0}  # 3 means 3+
    chain_events = 0  # A→C→B chains

    # Track recent diffusion targets for chain detection
    # A diffusion at node n (concept cn → target tc) is recorded.
    # If tc=C and there's a recent C→B diffusion neighbor, that's a chain.
    recent_diffusions = {}  # node_id -> (from_c, to_c) from this step

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
        events += 1; flow[(cn, tc)] += 1
        recent_diffusions[n] = (cn, tc)

        # Penetration depth: BFS from n into tc's territory
        depth = 1
        visited = {n}
        frontier = {n}
        for _ in range(2):  # check 2 more hops (total depth up to 3)
            next_front = set()
            for fn in frontier:
                for nb in state.neighbors(fn):
                    if nb not in visited and nb in state.alive_n and cm.get(nb,-1) == tc:
                        if nb in bnd:  # still at boundary = influence propagating
                            next_front.add(nb)
                            visited.add(nb)
            if not next_front: break
            depth += 1
            frontier = next_front
        depth_hist[min(depth, 3)] += 1

    # Chain detection: look for A→C + C→B (or symmetric)
    for n, (fc, tc) in recent_diffusions.items():
        if tc == 2:  # diffused toward C
            # Check if any neighbor of n also diffused C→other
            for nb in state.neighbors(n):
                if nb in recent_diffusions:
                    fc2, tc2 = recent_diffusions[nb]
                    if fc2 == 2 and tc2 != fc and tc2 != 2:
                        chain_events += 1

    return events, flow, depth_hist, chain_events


# ================================================================
# v3.6: MULTI-SCALE ISLAND ANALYSIS
# ================================================================
def compute_scale_variance(state, cm):
    """
    Detect islands at multiple S thresholds and measure how island
    boundaries and concept composition shift across scales.

    Returns: {threshold: {"n_islands": int, "concept_dist": Counter,
              "mean_size": float}} and scale_variance_index.
    """
    scale_data = {}
    for thr in SCALE_THRESHOLDS:
        islands = find_islands_sets(state, thr)
        # Concept composition of each island
        cdists = []
        sizes = []
        for isl in islands:
            cn_in = [n for n in isl if n in state.alive_n and int(state.Z[n]) == 3]
            if len(cn_in) < 3: continue
            cc = Counter(cm.get(n, -1) for n in cn_in)
            cdists.append(cc)
            sizes.append(len(cn_in))
        # How many islands are concept-dominated vs mixed?
        dominated = 0
        mixed = 0
        for cc in cdists:
            total = sum(cc.values())
            if total == 0: continue
            max_frac = max(cc.values()) / total
            if max_frac > 0.6: dominated += 1
            else: mixed += 1
        scale_data[thr] = {
            "n_islands": len(islands),
            "n_concept_islands": dominated,
            "n_mixed_islands": mixed,
            "mean_size": round(np.mean(sizes), 1) if sizes else 0,
        }

    # Scale variance index: how much does n_concept_islands change across thresholds?
    counts = [scale_data[t]["n_concept_islands"] for t in SCALE_THRESHOLDS]
    svi = round(np.std(counts) / max(np.mean(counts), 0.01), 4) if counts else 0

    return scale_data, svi


# ================================================================
# CONCEPT WINDOW METRICS (v3.4 base)
# ================================================================
def compute_concept_window(state, cm, rmap, islands_m):
    nc = N_CONCEPTS
    ci_count = {c: 0 for c in range(nc)}; ci_nodes = {c: 0 for c in range(nc)}
    labeled = []
    for isl in islands_m:
        cn_isl = [n for n in isl if n in state.alive_n and int(state.Z[n])==3]
        if len(cn_isl) < 3: continue
        cc = Counter(cm.get(n,-1) for n in cn_isl); t = sum(cc.values())
        if t == 0: continue
        for c in range(nc):
            if cc.get(c,0)/t > 0.5:
                ci_count[c] += 1; ci_nodes[c] += cc[c]
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
    return {"ci_count": ci_count, "ci_nodes": ci_nodes, "bnd_links": bnd_l,
            "bnd_weight": round(bnd_w,4), "entropy": round(ent,4),
            "obs": obs, "labeled": labeled, "tripartite": tripartite,
            "n_C": len(all_c)}


# ================================================================
# BRIDGE TRACKING (v3.3+)
# ================================================================
def compute_bridges(state, cm, prev):
    curr = {}
    for (i,j) in state.alive_l:
        if state.S[(i,j)] < BRIDGE_S_THR: continue
        if cm.get(i,-1) != cm.get(j,-1): curr[(i,j)] = state.S[(i,j)]
    ul = {}; nc = 0; pc = 0
    for k in curr:
        if k in prev: ul[k] = prev[k]+1; pc += 1
        else: ul[k] = 1; nc += 1
    ls = list(ul.values())
    pb = Counter()
    for (i,j) in curr: pb[(min(cm[i],cm[j]),max(cm[i],cm[j]))] += 1
    return ul, {"n": len(curr), "persist": pc,
        "mean_life": round(np.mean(ls),2) if ls else 0,
        "max_life": max(ls) if ls else 0, "pairs": dict(pb)}


# ================================================================
# MAIN SIMULATION
# ================================================================
def run_cognition(seed, N=COG_N, plb=COG_PLB, rate=COG_RATE, quiet_steps=QUIET_STEPS):
    p = dict(BASE_PARAMS); p["p_link_birth"] = plb
    state = GenesisState(N, C_MAX, seed)
    init_fert(state, TOPO_VAR, seed)
    cm = assign_concepts(N)
    centers = inject_concept_phases(state, cm)
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
    tot_diff = 0; tot_flow = Counter()
    tot_depth = {1:0, 2:0, 3:0}; tot_chains = 0

    for step in range(INJECTION_STEPS):
        if step % INJECT_INTERVAL == 0:
            tgts = physics.inject(state); chem.seed_on_injection(state, tgts or [])
        physics.step_pre_chemistry(state); chem.step(state)
        physics.step_resonance(state); grower.step(state)
        physics.step_decay_exclusion(state)

    ks=[]; sw_ev=[]; marg=[]; png=None; ckg=None; isls=[]
    pnr={r:None for r in range(N_REGIONS)}; ckr={r:None for r in range(N_REGIONS)}
    rks={r:[] for r in range(N_REGIONS)}
    c_wisl={c:0 for c in range(N_CONCEPTS)}; c_mstr={c:0 for c in range(N_CONCEPTS)}
    c_str={c:0 for c in range(N_CONCEPTS)}
    pbr={}; tot_tri=0; wlogs=[]; clogs=[]
    # v3.6: scale data per window
    scale_logs = []

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

        # v3.6: diffusion with penetration tracking
        bnd = find_concept_boundary_nodes(state, cm)
        nd, sf, dh, nc = apply_diffusion_with_tracking(state, cm, centers, bnd, state.rng)
        tot_diff += nd; tot_flow += sf; tot_chains += nc
        for d in dh: tot_depth[d] += dh[d]

        boosted_seeding(state, cm, bnd, gs, gz, state.rng)

        if (step+1) % WINDOW == 0:
            wi = (step+1)//WINDOW
            _el = time.time()-_t0
            if wi > 0:
                _pw = _el/wi; _rem = _pw*(_tw-wi)
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
                rks[r].append(ckr[r] or 0)
                wl[f"r{r}_k"]=ckr[r] or 0
                if (ckr[r] or 0)!=(ckg or 0): df=1
            wl["div"]=df

            cmet=compute_concept_window(state,cm,rmap,isl_m)
            tot_tri+=cmet["tripartite"]
            pbr,bs=compute_bridges(state,cm,pbr)

            for c in range(N_CONCEPTS):
                if cmet["ci_count"][c]>0:
                    c_str[c]+=1; c_wisl[c]+=1; c_mstr[c]=max(c_mstr[c],c_str[c])
                else: c_str[c]=0

            # v3.6: multi-scale analysis
            sd, svi = compute_scale_variance(state, cm)

            cl={"seed":seed,"win":wi,"tri":cmet["tripartite"],
                "bnd_links":cmet["bnd_links"],"bnd_w":cmet["bnd_weight"],
                "ent":cmet["entropy"],"n_br":bs["n"],"persist_br":bs["persist"],
                "br_life":bs["mean_life"],"br_max":bs["max_life"],
                "gk":ckg or 0,"div":df,"svi":svi}
            for c in range(N_CONCEPTS): cl[f"{CONCEPT_NAMES[c]}_isl"]=cmet["ci_count"][c]
            for r in range(N_REGIONS): cl[f"r{r}_c"]=CONCEPT_NAMES.get(cmet["obs"][r],"?")
            # scale data
            for thr in SCALE_THRESHOLDS:
                sd_t = sd[thr]
                cl[f"isl_{thr:.2f}"] = sd_t["n_islands"]
                cl[f"cisl_{thr:.2f}"] = sd_t["n_concept_islands"]
                cl[f"mix_{thr:.2f}"] = sd_t["n_mixed_islands"]
            clogs.append(cl); wlogs.append(wl)
            scale_logs.append(sd)

    elapsed=time.time()-t0; nw=len(ks)
    kc=Counter(ks); dk=kc.most_common(1)[0][0] if kc else 0
    swc=sum(1 for i in range(1,len(ks)) if ks[i]!=ks[i-1])
    sw100=round(swc/max(nw-1,1)*100,1)
    dvf=[w.get("div",0) for w in wlogs]
    dr=round(sum(dvf)/max(len(dvf),1),4)

    cs={}
    for c in range(N_CONCEPTS):
        cn=CONCEPT_NAMES[c]
        cs[cn]={"persist":round(c_wisl[c]/max(nw,1),4),"max_streak":c_mstr[c],
            "mean_isl":round(np.mean([cl[f"{cn}_isl"] for cl in clogs]),2)}

    obs_dom={}
    for r in range(N_REGIONS):
        rc=Counter(cl[f"r{r}_c"] for cl in clogs)
        obs_dom[f"r{r}"]=rc.most_common(1)[0][0] if rc else "?"

    fac=tot_flow.get((0,2),0)+tot_flow.get((2,0),0)
    fbc=tot_flow.get((1,2),0)+tot_flow.get((2,1),0)
    fab=tot_flow.get((0,1),0)+tot_flow.get((1,0),0)
    mrat=round((fac+fbc)/max(fab,1),4)

    # v3.6: mean scale variance
    svi_list = [cl["svi"] for cl in clogs]
    mean_svi = round(np.mean(svi_list), 4) if svi_list else 0

    # v3.6: flow profile
    depth_total = sum(tot_depth.values())
    depth_pct = {d: round(tot_depth[d]/max(depth_total,1)*100, 1) for d in [1,2,3]}
    mean_depth = round(
        sum(d * tot_depth[d] for d in [1,2,3]) / max(depth_total, 1), 3)

    result = {
        "N":N,"seed":int(seed),"quiet_steps":quiet_steps,"n_windows":nw,
        "global_dominant_k":dk,"global_sw100":sw100,"divergence_ratio":dr,
        "concept_summary":cs,
        "mean_entropy":round(np.mean([cl["ent"] for cl in clogs]),4),
        "observer_dominant":obs_dom,
        "total_tripartite":tot_tri,
        "total_diffusion":tot_diff,
        "flow_AC":fac,"flow_BC":fbc,"flow_AB":fab,"mediation_ratio":mrat,
        # v3.6: flow penetration
        "depth_hist":tot_depth,"depth_pct":depth_pct,
        "mean_penetration_depth":mean_depth,
        "transport_chains":tot_chains,
        # v3.6: scale variance
        "mean_svi":mean_svi,
        # bridges
        "mean_bridges":round(np.mean([cl["n_br"] for cl in clogs]),1),
        "mean_persist_bridges":round(np.mean([cl["persist_br"] for cl in clogs]),1),
        "max_bridge_life":max(cl["br_max"] for cl in clogs) if clogs else 0,
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
    print(f"  ESDE Cognition v3.6 — Aggregate ({n} seeds)")
    print(f"{'='*80}")

    gk=Counter(r["global_dominant_k"] for r in results)
    print(f"\n  Ecology: k*={dict(gk)}")
    print(f"  Entropy: {np.mean([r['mean_entropy'] for r in results]):.4f}")

    print(f"\n  Concept Persistence:")
    for cn in ["A","B","C"]:
        p=[r["concept_summary"][cn]["persist"] for r in results]
        print(f"    {cn}: {np.mean(p):.3f}±{np.std(p):.3f}")

    tp=[r["total_tripartite"] for r in results]
    print(f"\n  Tripartite: mean={np.mean(tp):.1f} max={max(tp)} >0:{sum(1 for x in tp if x>0)}/{n}")

    print(f"\n  Flow Penetration:")
    md=[r["mean_penetration_depth"] for r in results]
    print(f"    Mean depth: {np.mean(md):.3f}")
    d1=[r["depth_pct"]["1"] for r in results]
    d2=[r["depth_pct"]["2"] for r in results]
    d3=[r["depth_pct"]["3"] for r in results]
    print(f"    Profile: 1-step={np.mean(d1):.1f}% 2-step={np.mean(d2):.1f}% 3+step={np.mean(d3):.1f}%")
    tc=[r["transport_chains"] for r in results]
    print(f"    Transport chains (A→C→B): mean={np.mean(tc):.1f} max={max(tc)}")

    print(f"\n  Scale Variance:")
    sv=[r["mean_svi"] for r in results]
    print(f"    Mean SVI: {np.mean(sv):.4f}±{np.std(sv):.4f}")

    print(f"\n  Mediation: ratio={np.mean([r['mediation_ratio'] for r in results]):.2f}")

    print(f"\n  Observer Mapping:")
    for ri in range(N_REGIONS):
        rk=f"r{ri}"; mp=Counter(r["observer_dominant"][rk] for r in results)
        print(f"    {rk}: {dict(mp)}")

    rows=[]
    for r in results:
        row={"seed":r["seed"],"gk":r["global_dominant_k"],"sw100":r["global_sw100"],
            "div":r["divergence_ratio"],"entropy":r["mean_entropy"],
            "tri":r["total_tripartite"],"diffusion":r["total_diffusion"],
            "flow_AC":r["flow_AC"],"flow_BC":r["flow_BC"],"flow_AB":r["flow_AB"],
            "med_ratio":r["mediation_ratio"],
            "depth_mean":r["mean_penetration_depth"],
            "depth_1pct":r["depth_pct"]["1"],"depth_2pct":r["depth_pct"]["2"],
            "depth_3pct":r["depth_pct"]["3"],
            "chains":r["transport_chains"],"svi":r["mean_svi"],
            "bridges":r["mean_bridges"],"persist_br":r["mean_persist_bridges"],
            "br_max":r["max_bridge_life"]}
        for cn in ["A","B","C"]: row[f"{cn}_persist"]=r["concept_summary"][cn]["persist"]
        for ri in range(N_REGIONS): row[f"r{ri}_c"]=r["observer_dominant"][f"r{ri}"]
        rows.append(row)
    csv_path=OUTPUT_DIR/"cognition_v36_summary.csv"
    with open(csv_path,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print(f"\n  CSV: {csv_path}")


# ================================================================
# MAIN
# ================================================================
def main():
    parser=argparse.ArgumentParser(description="ESDE Cognition v3.6")
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
        res,_,_,_=run_cognition(42,args.N,args.plb,args.rate,500)
        print(f"  k*={res['global_dominant_k']} ent={res['mean_entropy']:.4f}")
        for cn in ["A","B","C"]:
            print(f"  {cn}: persist={res['concept_summary'][cn]['persist']:.2f}")
        print(f"  Tri={res['total_tripartite']}")
        print(f"  Depth: mean={res['mean_penetration_depth']:.3f} "
              f"profile={res['depth_pct']}")
        print(f"  Chains={res['transport_chains']} SVI={res['mean_svi']:.4f}")
        print(f"  Bridges: persist={res['mean_persist_bridges']:.1f} max={res['max_bridge_life']}")
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
        print(f"    k*={result['global_dominant_k']} tri={result['total_tripartite']} "
              f"depth={result['mean_penetration_depth']:.3f} chains={result['transport_chains']} "
              f"svi={result['mean_svi']:.4f} ({result['elapsed']:.0f}s)")

if __name__=="__main__": main()
