#!/usr/bin/env python3
"""
ESDE Cognition v3.8 — Flow Amplification & Stress Test
========================================================
Phase : Cognition (v3.8)
Role  : Claude (Implementation)
Arch  : Gemini | Audit: GPT (Approved)

PURPOSE
-------
v3.7 confirmed semantic erosion: flow leaves structural traces deep into
concept cores. v3.8 stress-tests to find the collapse threshold — where
does controlled plasticity become structural collapse?

METHOD
------
Amplify diffusion_prob by multiplier sweep: 1x, 2x, 4x, 8x baseline.
(baseline = 0.005 → sweep = 0.005, 0.01, 0.02, 0.04)

Monitor for collapse:
  - core_preservation → 0
  - entropy spike (deviation from ~1.54)
  - k* shift from 4
  - erosion_depth runaway

Auto-flag collapse: if core_preservation < 0.01 for ALL concepts
AND entropy deviation > 0.1 from baseline.

USAGE
-----
  python cognition_v38.py --sanity --amp 1.0
  python cognition_v38.py --sanity --amp 8.0

  # Full sweep: 4 amplifications × 20 seeds
  parallel -j 20 python cognition_v38.py --amp {1} --seed {2} \
    ::: 1.0 2.0 4.0 8.0 ::: $(seq 1 20)

  python cognition_v38.py --aggregate
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
DIFFUSION_PROB_BASE = 0.005; DIFFUSION_STRENGTH = 0.3
BOUNDARY_LINK_BOOST = 1.5; BRIDGE_S_THR = 0.15
GRID_ROWS = 2; GRID_COLS = 2; N_REGIONS = 4
MIN_C_NODES_FOR_VALID = 5
DRIFT_EPSILON = 0.05
# v3.8: amplification sweep values
AMP_LEVELS = [1.0, 2.0, 4.0, 8.0]
ENTROPY_BASELINE = 1.54  # from v3.4-v3.7
COLLAPSE_ENTROPY_DEV = 0.1
OUTPUT_DIR = Path("outputs_v38")


# ================================================================
# STANDARD (unchanged)
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

def compute_concept_depth(N, cm, state):
    bnd = find_concept_boundary_nodes(state, cm)
    depth = {i: -1 for i in range(N)}
    queue = list(bnd)
    for n in queue: depth[n] = 0
    visited = set(bnd); d = 0
    while queue:
        next_q = []; d += 1
        for n in queue:
            cn = cm.get(n, -1)
            for nb in state.neighbors(n):
                if nb not in visited and nb in state.alive_n and cm.get(nb, -1) == cn:
                    depth[nb] = d; visited.add(nb); next_q.append(nb)
        queue = next_q
    return depth


# ================================================================
# DIFFUSION (v3.8: amplified probability)
# ================================================================
def apply_diffusion_amplified(state, cm, centers, bnd, rng, diff_prob):
    events = 0; flow = Counter(); depth_hist = Counter()
    for n in bnd:
        if rng.random() > diff_prob: continue
        cn = cm.get(n, -1)
        if cn < 0: continue
        dnb = [nb for nb in state.neighbors(n)
               if nb in state.alive_n and cm.get(nb,-1) >= 0 and cm.get(nb,-1) != cn]
        if not dnb: continue
        tnb = dnb[rng.randint(len(dnb))]; tc = cm[tnb]
        d = (centers[tc] - state.theta[n] + np.pi) % (2*np.pi) - np.pi
        state.theta[n] = (state.theta[n] + DIFFUSION_STRENGTH * d) % (2*np.pi)
        events += 1; flow[(cn, tc)] += 1
        # Penetration (uncapped, safety 10)
        dep = 1; visited = {n}; frontier = {n}
        while dep < 10:
            nf = set()
            for fn in frontier:
                for nb in state.neighbors(fn):
                    if nb not in visited and nb in state.alive_n and cm.get(nb,-1) == tc:
                        if nb in bnd: nf.add(nb); visited.add(nb)
            if not nf: break
            dep += 1; frontier = nf
        depth_hist[dep] += 1
    return events, flow, depth_hist


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
# EROSION METRICS (v3.7)
# ================================================================
def compute_erosion_metrics(state, cm, centers, depth_map, theta_initial):
    results = {}
    for c in range(N_CONCEPTS):
        cn = CONCEPT_NAMES[c]
        nodes_by_depth = defaultdict(list)
        for n in state.alive_n:
            if cm.get(n, -1) != c: continue
            d = depth_map.get(n, -1)
            if d < 0: continue
            dtheta = abs((state.theta[n] - theta_initial[n] + np.pi) % (2*np.pi) - np.pi)
            nodes_by_depth[d].append(dtheta)
        bnd_d = nodes_by_depth.get(0, [])
        near_d = [dt for d in [1,2] for dt in nodes_by_depth.get(d, [])]
        deep_d = [dt for d in nodes_by_depth if d >= 3 for dt in nodes_by_depth[d]]
        erosion_d = 0
        for d in sorted(nodes_by_depth.keys()):
            dts = nodes_by_depth[d]
            if dts and np.mean(dts) > DRIFT_EPSILON: erosion_d = d
        core_pres = round(sum(1 for dt in deep_d if dt < DRIFT_EPSILON)/len(deep_d), 4) if deep_d else 1.0
        bnd_k_vals = []
        for n in state.alive_n:
            if cm.get(n,-1)!=c or depth_map.get(n,-1)!=0: continue
            bnd_k_vals.append(sum(1 for nb in state.neighbors(n) if nb in state.alive_n and state.key(n,nb) in state.alive_l))
        results[cn] = {
            "drift_boundary": round(np.mean(bnd_d),6) if bnd_d else 0,
            "drift_near_core": round(np.mean(near_d),6) if near_d else 0,
            "drift_deep_core": round(np.mean(deep_d),6) if deep_d else 0,
            "erosion_depth": erosion_d,
            "core_preservation": core_pres,
            "boundary_k_mean": round(np.mean(bnd_k_vals),2) if bnd_k_vals else 0,
        }
    return results


# ================================================================
# CONCEPT WINDOW (compact)
# ================================================================
def compute_concept_window(state, cm, rmap, islands_m):
    nc = N_CONCEPTS
    ci_count = {c:0 for c in range(nc)}
    for isl in islands_m:
        cn_isl = [n for n in isl if n in state.alive_n and int(state.Z[n])==3]
        if len(cn_isl) < 3: continue
        cc = Counter(cm.get(n,-1) for n in cn_isl); t = sum(cc.values())
        if t == 0: continue
        for c in range(nc):
            if cc.get(c,0)/t > 0.5: ci_count[c] += 1; break
    tripartite = 0
    for isl in islands_m:
        cn_isl = [n for n in isl if n in state.alive_n and int(state.Z[n])==3]
        if len(cn_isl) < 3: continue
        cc = Counter(cm.get(n,-1) for n in cn_isl)
        if all(cc.get(c,0) > 0 for c in range(nc)): tripartite += 1
    all_c = [n for n in state.alive_n if int(state.Z[n])==3]
    cdist = Counter(cm.get(n,-1) for n in all_c); t = sum(cdist.values())
    ent = -sum(v/t*np.log2(v/t) for v in cdist.values() if v>0) if t>0 else 0
    return {"ci_count": ci_count, "entropy": round(ent,4),
            "tripartite": tripartite, "n_C": len(all_c)}


# ================================================================
# MAIN SIMULATION
# ================================================================
def run_cognition(seed, N=COG_N, plb=COG_PLB, rate=COG_RATE,
                  quiet_steps=QUIET_STEPS, amp=1.0):
    diff_prob = min(DIFFUSION_PROB_BASE * amp, 1.0)

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
    tot_diff = 0; tot_flow = Counter(); tot_depth = Counter()

    for step in range(INJECTION_STEPS):
        if step % INJECT_INTERVAL == 0:
            tgts = physics.inject(state); chem.seed_on_injection(state, tgts or [])
        physics.step_pre_chemistry(state); chem.step(state)
        physics.step_resonance(state); grower.step(state)
        physics.step_decay_exclusion(state)

    theta_initial = state.theta.copy()

    ks=[]; sw_ev=[]; png=None; ckg=None
    pnr={r:None for r in range(N_REGIONS)}; ckr={r:None for r in range(N_REGIONS)}
    rks={r:[] for r in range(N_REGIONS)}
    c_wisl={c:0 for c in range(N_CONCEPTS)}; c_mstr={c:0 for c in range(N_CONCEPTS)}
    c_str={c:0 for c in range(N_CONCEPTS)}
    tot_tri=0; wlogs=[]; clogs=[]; erosion_logs=[]

    # v3.8: per-window entropy for variance tracking
    entropy_series = []

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

        # v3.8: amplified diffusion
        bnd = find_concept_boundary_nodes(state, cm)
        nd, sf, dh = apply_diffusion_amplified(state, cm, centers, bnd, state.rng, diff_prob)
        tot_diff += nd; tot_flow += sf
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
                ckg=nkg; ks.append(nkg); png=an
            else: ks.append(ckg or 0)

            cmet=compute_concept_window(state,cm,rmap,isl_m)
            tot_tri+=cmet["tripartite"]
            entropy_series.append(cmet["entropy"])

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

            for c in range(N_CONCEPTS):
                if cmet["ci_count"][c]>0:
                    c_str[c]+=1; c_wisl[c]+=1; c_mstr[c]=max(c_mstr[c],c_str[c])
                else: c_str[c]=0

            # Erosion
            depth_map = compute_concept_depth(N, cm, state)
            eros = compute_erosion_metrics(state, cm, centers, depth_map, theta_initial)

            cl={"seed":seed,"win":wi,"tri":cmet["tripartite"],
                "ent":cmet["entropy"],"gk":ckg or 0,"div":df,"nC":nC}
            for c in range(N_CONCEPTS):
                cn=CONCEPT_NAMES[c]; e=eros[cn]
                cl[f"{cn}_drift_bnd"]=e["drift_boundary"]
                cl[f"{cn}_drift_deep"]=e["drift_deep_core"]
                cl[f"{cn}_erosion_d"]=e["erosion_depth"]
                cl[f"{cn}_core_pres"]=e["core_preservation"]
                cl[f"{cn}_bnd_k"]=e["boundary_k_mean"]
            clogs.append(cl); wlogs.append(wl); erosion_logs.append(eros)

    elapsed=time.time()-t0; nw=len(ks)
    kc=Counter(ks); dk=kc.most_common(1)[0][0] if kc else 0
    swc=sum(1 for i in range(1,len(ks)) if ks[i]!=ks[i-1])
    sw100=round(swc/max(nw-1,1)*100,1)
    dvf=[w.get("div",0) for w in wlogs]
    dr=round(sum(dvf)/max(len(dvf),1),4)

    # Entropy variance
    ent_mean=round(np.mean(entropy_series),4) if entropy_series else 0
    ent_std=round(np.std(entropy_series),4) if entropy_series else 0
    ent_dev_from_baseline=round(abs(ent_mean - ENTROPY_BASELINE),4)

    # Late-window erosion (last 5)
    late = erosion_logs[-5:] if len(erosion_logs)>=5 else erosion_logs
    erosion_summary = {}
    for cn in ["A","B","C"]:
        vals=[ew[cn] for ew in late if cn in ew]
        if not vals: erosion_summary[cn]={}; continue
        erosion_summary[cn]={
            "drift_boundary":round(np.mean([v["drift_boundary"] for v in vals]),6),
            "drift_deep_core":round(np.mean([v["drift_deep_core"] for v in vals]),6),
            "erosion_depth":max(v["erosion_depth"] for v in vals),
            "core_preservation":round(np.mean([v["core_preservation"] for v in vals]),4),
            "boundary_k_mean":round(np.mean([v["boundary_k_mean"] for v in vals]),2),
        }

    # v3.8: collapse detection
    all_core_gone = all(
        erosion_summary.get(cn,{}).get("core_preservation",1.0) < 0.01
        for cn in ["A","B","C"] if erosion_summary.get(cn))
    entropy_collapsed = ent_dev_from_baseline > COLLAPSE_ENTROPY_DEV
    k_collapsed = dk != 4
    collapse_flag = all_core_gone and (entropy_collapsed or k_collapsed)

    # Depth distribution
    dep_total=sum(tot_depth.values())
    mean_dep=round(sum(d*tot_depth[d] for d in tot_depth)/max(dep_total,1),3) if dep_total>0 else 0

    result={
        "N":N,"seed":int(seed),"amp":amp,"diff_prob":round(diff_prob,4),
        "quiet_steps":quiet_steps,"n_windows":nw,
        "global_dominant_k":dk,"global_sw100":sw100,"divergence_ratio":dr,
        "mean_entropy":ent_mean,"entropy_std":ent_std,
        "entropy_dev_from_baseline":ent_dev_from_baseline,
        "total_tripartite":tot_tri,"total_diffusion":tot_diff,
        "mean_penetration_depth":mean_dep,
        "erosion_summary":erosion_summary,
        "collapse_flag":collapse_flag,
        "collapse_detail":{"core_gone":all_core_gone,"entropy_dev":entropy_collapsed,"k_shift":k_collapsed},
        "elapsed":round(elapsed,1),
    }
    return result, wlogs, clogs, [asdict(se) for se in sw_ev]


# ================================================================
# AGGREGATE
# ================================================================
def aggregate():
    results=[]
    for f in sorted(OUTPUT_DIR.glob("seed_*_amp*.json")):
        if "_concept" in f.name or "_switches" in f.name: continue
        with open(f) as fh: results.append(json.load(fh))
    if not results: print("  No results."); return

    by_amp=defaultdict(list)
    for r in results: by_amp[r["amp"]].append(r)

    print(f"\n{'='*80}")
    print(f"  ESDE Cognition v3.8 — Stress Test ({len(results)} runs)")
    print(f"{'='*80}")

    for amp in sorted(by_amp):
        rs=by_amp[amp]; n=len(rs)
        print(f"\n  {'='*60}")
        print(f"  AMP = {amp}x  (diff_prob={rs[0]['diff_prob']})  [{n} seeds]")
        print(f"  {'='*60}")

        gk=Counter(r["global_dominant_k"] for r in rs)
        print(f"  Ecology: k*={dict(gk)}")
        em=[r["mean_entropy"] for r in rs]
        es=[r["entropy_std"] for r in rs]
        print(f"  Entropy: mean={np.mean(em):.4f} std={np.mean(es):.4f} "
              f"dev_from_baseline={np.mean([r['entropy_dev_from_baseline'] for r in rs]):.4f}")
        td=[r["total_diffusion"] for r in rs]
        print(f"  Diffusion: {np.mean(td):.0f}/run")
        md=[r["mean_penetration_depth"] for r in rs]
        print(f"  Penetration depth: {np.mean(md):.3f}")
        tp=[r["total_tripartite"] for r in rs]
        print(f"  Tripartite: mean={np.mean(tp):.1f}")

        print(f"\n  Erosion (late-window):")
        for cn in ["A","B","C"]:
            db=[r["erosion_summary"][cn]["drift_boundary"] for r in rs if cn in r["erosion_summary"] and r["erosion_summary"][cn]]
            dd=[r["erosion_summary"][cn]["drift_deep_core"] for r in rs if cn in r["erosion_summary"] and r["erosion_summary"][cn]]
            ed=[r["erosion_summary"][cn]["erosion_depth"] for r in rs if cn in r["erosion_summary"] and r["erosion_summary"][cn]]
            cp=[r["erosion_summary"][cn]["core_preservation"] for r in rs if cn in r["erosion_summary"] and r["erosion_summary"][cn]]
            if db:
                print(f"    {cn}: drift_bnd={np.mean(db):.4f} drift_deep={np.mean(dd):.4f} "
                      f"erosion_d={np.mean(ed):.1f} core_pres={np.mean(cp):.4f}")

        # Collapse
        collapsed=[r for r in rs if r["collapse_flag"]]
        print(f"\n  Collapse: {len(collapsed)}/{n} seeds flagged")
        if collapsed:
            for r in collapsed[:3]:
                print(f"    seed={r['seed']}: k*={r['global_dominant_k']} "
                      f"ent={r['mean_entropy']:.4f} detail={r['collapse_detail']}")

    # CSV
    rows=[]
    for r in results:
        row={"seed":r["seed"],"amp":r["amp"],"diff_prob":r["diff_prob"],
            "gk":r["global_dominant_k"],"sw100":r["global_sw100"],
            "div":r["divergence_ratio"],"entropy":r["mean_entropy"],
            "entropy_std":r["entropy_std"],"entropy_dev":r["entropy_dev_from_baseline"],
            "diffusion":r["total_diffusion"],"depth_mean":r["mean_penetration_depth"],
            "tri":r["total_tripartite"],"collapse":int(r["collapse_flag"])}
        for cn in ["A","B","C"]:
            es=r["erosion_summary"].get(cn,{})
            row[f"{cn}_drift_bnd"]=es.get("drift_boundary",0)
            row[f"{cn}_drift_deep"]=es.get("drift_deep_core",0)
            row[f"{cn}_erosion_d"]=es.get("erosion_depth",0)
            row[f"{cn}_core_pres"]=es.get("core_preservation",0)
            row[f"{cn}_bnd_k"]=es.get("boundary_k_mean",0)
        rows.append(row)
    csv_path=OUTPUT_DIR/"cognition_v38_summary.csv"
    with open(csv_path,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print(f"\n  CSV: {csv_path}")


# ================================================================
# MAIN
# ================================================================
def main():
    parser=argparse.ArgumentParser(description="ESDE Cognition v3.8 — Stress Test")
    parser.add_argument("--seed",type=int,default=None)
    parser.add_argument("--N",type=int,default=COG_N)
    parser.add_argument("--plb",type=float,default=COG_PLB)
    parser.add_argument("--rate",type=float,default=COG_RATE)
    parser.add_argument("--quiet-steps",type=int,default=QUIET_STEPS)
    parser.add_argument("--amp",type=float,default=1.0)
    parser.add_argument("--aggregate",action="store_true")
    parser.add_argument("--sanity",action="store_true")
    args=parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)

    if args.sanity:
        dp=min(DIFFUSION_PROB_BASE*args.amp,1.0)
        print(f"  SANITY: N={args.N} amp={args.amp}x diff_prob={dp:.4f} seed=42 quiet=500")
        res,_,_,_=run_cognition(42,args.N,args.plb,args.rate,500,args.amp)
        print(f"  k*={res['global_dominant_k']} ent={res['mean_entropy']:.4f}±{res['entropy_std']:.4f}")
        print(f"  Diffusion: {res['total_diffusion']}")
        for cn in ["A","B","C"]:
            es=res["erosion_summary"].get(cn,{})
            if es:
                print(f"  {cn}: drift_bnd={es['drift_boundary']:.4f} "
                      f"drift_deep={es['drift_deep_core']:.4f} "
                      f"erosion_d={es['erosion_depth']} "
                      f"core_pres={es['core_preservation']:.4f}")
        print(f"  Collapse={res['collapse_flag']} {res['collapse_detail']}")
        print(f"  elapsed={res['elapsed']:.0f}s")
        print("  SANITY OK"); return

    if args.aggregate: aggregate(); return

    seeds=[args.seed] if args.seed else COG_SEEDS
    atag=f"amp{args.amp:.1f}".replace(".","p")  # e.g. amp2p0
    for seed in seeds:
        rf=OUTPUT_DIR/f"seed_{seed}_{atag}.json"
        if rf.exists(): print(f"  seed={seed} {atag}: skip"); continue
        print(f"  seed={seed} amp={args.amp}x...",flush=True)
        result,_,clogs,sw=run_cognition(seed,args.N,args.plb,args.rate,args.quiet_steps,args.amp)
        with open(rf,"w") as f: json.dump(result,f,indent=2)
        if clogs:
            with open(OUTPUT_DIR/f"seed_{seed}_{atag}_concept.csv","w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=clogs[0].keys()); w.writeheader(); w.writerows(clogs)
        if sw:
            with open(OUTPUT_DIR/f"seed_{seed}_{atag}_switches.json","w") as f: json.dump(sw,f,indent=2)
        es=result["erosion_summary"]
        cp_min=min(es.get(cn,{}).get("core_preservation",1.0) for cn in ["A","B","C"] if es.get(cn))
        print(f"    k*={result['global_dominant_k']} ent={result['mean_entropy']:.4f} "
              f"diff={result['total_diffusion']} core_min={cp_min:.4f} "
              f"collapse={'YES' if result['collapse_flag'] else 'no'} "
              f"({result['elapsed']:.0f}s)")

if __name__=="__main__": main()
