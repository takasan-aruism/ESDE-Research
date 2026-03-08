#!/usr/bin/env python3
"""
ESDE Genesis v1.8 — Boundary Intrusion Sweep
===============================================
Micro-perturbation at island boundaries to reshape closure geometry.

intrusion_rate ∈ {0.0, 0.0005, 0.001, 0.002, 0.005}
No chemistry expansion. One new operator. One knob.

Usage:
  python v18_intrusion.py --sanity
  python v18_intrusion.py --rate 0.001 --seed 42
  python v18_intrusion.py --aggregate-only

  # Parallel:
  parallel -j 20 python v18_intrusion.py --rate {1} --seed {2} \
    ::: 0.0 0.0005 0.001 0.002 0.005 \
    ::: 42 123 456 789 2024 7 314 999 55 1337
  python v18_intrusion.py --aggregate-only
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import csv, json, time, argparse
from collections import Counter, defaultdict
from pathlib import Path

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger
from chemistry import ChemistryEngine, ChemistryParams
from realization import RealizationOperator, RealizationParams
from autogrowth import AutoGrowthEngine, AutoGrowthParams
from intrusion import BoundaryIntrusionOperator, find_islands_sets

N_NODES=200; C_MAX=1.0; INJECTION_STEPS=300; INJECT_INTERVAL=3
QUIET_STEPS=5000; BETA=1.0; NODE_DECAY=0.005; BIAS=0.7; WINDOW=200
S_DOM=0.30
STRENGTH_BINS=[(0,0.05),(0.05,0.1),(0.1,0.2),(0.2,0.3),(0.3,1.01)]
STATE_NAMES={0:"Dust",1:"A",2:"B",3:"C"}

PARAMS={"reaction_energy_threshold":0.26,"link_death_threshold":0.007,
    "background_injection_prob":0.003,"exothermic_release_amount":0.17,
    "p_link_birth":0.010,"latent_to_active_threshold":0.07,
    "latent_refresh_rate":0.003,"auto_growth_rate":0.03}

E_YIELD_SYN=0.08; E_YIELD_AUTO=0.00; TOPO_VAR=0.20  # best from v1.7
RATE_GRID=[0.0, 0.0005, 0.001, 0.002, 0.005]
ALL_SEEDS=[42,123,456,789,2024,7,314,999,55,1337]
OUTPUT_DIR=Path("outputs_v18")


def init_fertility(state, variance, seed):
    rng=np.random.RandomState(seed+7777)
    if variance<=0: state.F=np.ones(state.n_nodes); return
    u=rng.uniform(-1,1,state.n_nodes)
    raw=1.0+variance*u; raw=np.clip(raw,0.01,2.0)
    state.F=raw/raw.mean()


class CT:
    def __init__(self): self.h=defaultdict(list)
    def rec(self,state,step):
        for i in state.alive_n:
            z=int(state.Z[i]); h=self.h[i]
            if not h or h[-1][1]!=z: h.append((step,z))
    def find(self):
        cycles=[]
        for nid,h in self.h.items():
            ss=[s for _,s in h]
            for i in range(len(ss)-3):
                if ss[i]==3 and ss[i+1]==0 and ss[i+2] in(1,2):
                    for j in range(i+3,len(ss)):
                        if ss[j]==3:
                            tp="→".join(STATE_NAMES[s] for s in ss[i:j+1])
                            cycles.append({"node":nid,"start":h[i][0],"end":h[j][0],"type":tp})
                            break
        return cycles


def shannon(counts):
    t=sum(counts); 
    if t==0: return 0.0
    ps=[c/t for c in counts if c>0]
    return -sum(p*np.log2(p) for p in ps)


def run_one(seed, rate, quiet_steps=QUIET_STEPS):
    p=PARAMS
    state=GenesisState(N_NODES,C_MAX,seed)
    init_fertility(state, TOPO_VAR, seed)
    physics=GenesisPhysics(PhysicsParams(exclusion_enabled=True,resonance_enabled=True,
        phase_enabled=True,beta=BETA,decay_rate_node=NODE_DECAY,K_sync=0.1,alpha=0.0,gamma=1.0))
    cp=ChemistryParams(enabled=True,E_thr=p["reaction_energy_threshold"],
        exothermic_release=p["exothermic_release_amount"],
        E_yield_syn=E_YIELD_SYN, E_yield_auto=E_YIELD_AUTO)
    chem=ChemistryEngine(cp)
    rp=RealizationParams(enabled=True,p_link_birth=p["p_link_birth"],
        latent_to_active_threshold=p["latent_to_active_threshold"],
        latent_refresh_rate=p["latent_refresh_rate"])
    realizer=RealizationOperator(rp)
    grower=AutoGrowthEngine(AutoGrowthParams(enabled=True,auto_growth_rate=p["auto_growth_rate"]))
    intruder=BoundaryIntrusionOperator(intrusion_rate=rate)
    state.EXTINCTION=p["link_death_threshold"]
    tracker=CT(); g_scores=np.zeros(N_NODES)
    t0=time.time()

    for step in range(INJECTION_STEPS):
        if step%INJECT_INTERVAL==0:
            tgts=physics.inject(state); chem.seed_on_injection(state,tgts or[])
        physics.step_pre_chemistry(state); chem.step(state)
        cd=physics.step_resonance(state); grower.step(state)
        physics.step_decay_exclusion(state); tracker.rec(state,state.step-1)

    spr_v=[]; s_hists=[]; min_l=99999
    island_counts_strong=[]; island_counts_mid=[]; prev_islands_strong=[]; prev_islands_mid=[]
    island_births=0; island_deaths=0
    turnover_strong_vals=[]; turnover_mid_vals=[]
    boundary_events_strong=0; boundary_events_all=0; swap_total=0
    island_lifetimes={}  # frozenset → window count (Fix A)
    dead_lifetimes=[]
    runaway=False
    # Intrusion counters per window
    win_counters=[]

    for step in range(quiet_steps):
        realizer.step(state); physics.step_pre_chemistry(state)
        rxns=chem.step(state); cd=physics.step_resonance(state)
        g_scores[:]=0; grower.step(state)
        for k in state.alive_l:
            r=state.R.get(k,0.0)
            if r>0:
                a=min(grower.params.auto_growth_rate*r,max(state.get_latent(k[0],k[1]),0))
                if a>0: g_scores[k[0]]+=a; g_scores[k[1]]+=a
        gz=float(g_scores.sum())

        # v1.8: Boundary Intrusion (AFTER auto-growth, BEFORE decay+exclusion)
        swap_total += intruder.step(state)

        physics.step_decay_exclusion(state); tracker.rec(state,state.step-1)

        # Seeding
        al=list(state.alive_n); na=len(al)
        if na>0:
            aa=np.array(al)
            if BIAS>0 and gz>0:
                ga=g_scores[aa]; gs=ga.sum()
                if gs>0: pg=ga/gs; pd=(1-BIAS)*(np.ones(na)/na)+BIAS*pg; pd/=pd.sum()
                else: pd=np.ones(na)/na
            else: pd=np.ones(na)/na
            mk=state.rng.random(na)<p["background_injection_prob"]
            for idx in range(na):
                if mk[idx]:
                    t=int(state.rng.choice(aa,p=pd))
                    state.E[t]=min(1.0,state.E[t]+0.3)
                    if state.Z[t]==0 and state.rng.random()<0.5:
                        state.Z[t]=1 if state.rng.random()<0.5 else 2

        if (step+1)%WINDOW==0:
            nl=len(state.alive_l); min_l=min(min_l,nl)
            ss=[state.S[k] for k in state.alive_l]
            ll=sum(1 for k in state.alive_l if state.R.get(k,0)>0)
            spr_v.append(ll/max(nl,1))
            h=[0]*5
            for s in ss:
                for bi,(lo,hi) in enumerate(STRENGTH_BINS):
                    if lo<=s<hi: h[bi]+=1; break
            s_hists.append(h)

            # B) Dual threshold islands
            cur_strong=find_islands_sets(state, 0.30)
            cur_mid=find_islands_sets(state, 0.20)
            island_counts_strong.append(len(cur_strong))
            island_counts_mid.append(len(cur_mid))

            # Turnover helper
            def compute_turnover(cur_list, prev_list):
                cur_s=set(cur_list); prev_s=set(prev_list)
                matched_c=set(); matched_p=set(); pairs=[]
                for ci in cur_s:
                    best=None; best_ov=0
                    for pj in prev_s:
                        ov=len(ci&pj)
                        if ov>best_ov: best_ov=ov; best=pj
                    if best and best_ov>=2:
                        pairs.append((ci,best)); matched_c.add(ci); matched_p.add(best)
                births=len(cur_s-matched_c); deaths=len(prev_s-matched_p)
                turns=[]
                for ci,pj in pairs:
                    j=len(ci&pj)/len(ci|pj) if ci|pj else 1
                    turns.append(1-j)
                return births, deaths, turns, pairs, matched_c, matched_p

            b_s, d_s, t_s, pairs_s, mc_s, mp_s = compute_turnover(cur_strong, prev_islands_strong)
            b_m, d_m, t_m, _, _, _ = compute_turnover(cur_mid, prev_islands_mid)
            island_births += b_s; island_deaths += d_s
            turnover_strong_vals.extend(t_s)
            turnover_mid_vals.extend(t_m)

            # A) Fix: island lifetime tracking with frozenset keys
            new_active={}
            for ci in set(cur_strong):
                if ci in mc_s:
                    for c2,p2 in pairs_s:
                        if c2==ci:
                            new_active[ci]=island_lifetimes.get(p2,0)+1
                            break
                else:
                    new_active[ci]=1
            for pj in set(prev_islands_strong)-mp_s:
                dead_lifetimes.append(island_lifetimes.get(pj,1))
            island_lifetimes=new_active

            # D) Boundary crossing: strong + all
            all_isl_nodes=set()
            for isl in cur_strong: all_isl_nodes|=isl
            bc_s=sum(1 for k in state.alive_l if state.S[k]>=S_DOM
                     and bool(k[0] in all_isl_nodes)!=bool(k[1] in all_isl_nodes))
            bc_all=sum(1 for k in state.alive_l
                       if bool(k[0] in all_isl_nodes)!=bool(k[1] in all_isl_nodes))
            boundary_events_strong+=bc_s
            boundary_events_all+=bc_all

            prev_islands_strong=cur_strong
            prev_islands_mid=cur_mid

            # C) Log intrusion counters then reset for next window
            win_counters.append(intruder.get_counters())
            intruder.reset_counters()

            e_vals=[state.E[i] for i in state.alive_n]
            if e_vals and np.median(e_vals)>=0.80: runaway=True

        if step%1000==999:
            print(f"      q{step+1}: L={len(state.alive_l):>4} "
                  f"isl={island_counts_strong[-1] if island_counts_strong else 0}/{island_counts_mid[-1] if island_counts_mid else 0} "
                  f"swaps={swap_total} ({time.time()-t0:.0f}s)",flush=True)

    all_cycles=tracker.find()
    type_counts=Counter(c["type"] for c in all_cycles)
    n_types=len(type_counts)
    type_ent=shannon(list(type_counts.values()))
    top1=type_counts.most_common(1)[0][1]/len(all_cycles) if all_cycles else 0
    spr=np.mean(spr_v) if spr_v else 0
    coex_strong=sum(1 for ic in island_counts_strong if ic>=2)/max(len(island_counts_strong),1)
    coex_mid=sum(1 for ic in island_counts_mid if ic>=2)/max(len(island_counts_mid),1)
    mean_turn_strong=np.mean(turnover_strong_vals) if turnover_strong_vals else 0
    mean_turn_mid=np.mean(turnover_mid_vals) if turnover_mid_vals else 0
    med_life=np.median(dead_lifetimes) if dead_lifetimes else (
        np.median(list(island_lifetimes.values())) if island_lifetimes else 0)
    rigidity=float(med_life/(1+mean_turn_strong)) if (1+mean_turn_strong)>0 else 0

    if s_hists:
        mh=np.mean(s_hists,axis=0); t=mh.sum()
        if t>0: pp=mh/t; pp=pp[pp>0]; H=-np.sum(pp*np.log2(pp)); C=1-H/np.log2(5)
        else: C=0
    else: C=0
    X=round(C+spr,4)

    # Aggregate intrusion counters
    total_attempts=sum(c["attempts"] for c in win_counters)
    total_success=sum(c["success"] for c in win_counters)
    total_fail_intra=sum(c["fail_no_intra"] for c in win_counters)
    total_fail_outside=sum(c["fail_no_outside"] for c in win_counters)
    mean_bnd_nodes=np.mean([c["boundary_nodes"] for c in win_counters]) if win_counters else 0

    elapsed=time.time()-t0
    return {
        "seed":int(seed),"intrusion_rate":rate,
        "cycles":len(all_cycles),
        "cycles_per_1k":round(len(all_cycles)/(quiet_steps/1000),3),
        "cycle_type_count":n_types,
        "cycle_type_entropy":round(type_ent,4),
        "top1_share":round(top1,4),
        "mean_island_strong":round(np.mean(island_counts_strong),2) if island_counts_strong else 0,
        "mean_island_mid":round(np.mean(island_counts_mid),2) if island_counts_mid else 0,
        "coexistence_strong":round(coex_strong,4),
        "coexistence_mid":round(coex_mid,4),
        "island_births_1k":round(island_births/(quiet_steps/1000),2),
        "island_deaths_1k":round(island_deaths/(quiet_steps/1000),2),
        "turnover_strong":round(mean_turn_strong,4),
        "turnover_mid":round(mean_turn_mid,4),
        "boundary_crossing_strong_1k":round(boundary_events_strong/(quiet_steps/1000),2),
        "boundary_crossing_all_1k":round(boundary_events_all/(quiet_steps/1000),2),
        "rigidity_index":round(rigidity,3),
        "intrusion_attempts":total_attempts,
        "intrusion_success":total_success,
        "intrusion_fail_intra":total_fail_intra,
        "intrusion_fail_outside":total_fail_outside,
        "mean_boundary_nodes":round(mean_bnd_nodes,1),
        "swap_events":swap_total,
        "spr":round(spr,4),"X":X,
        "min_links":min_l if min_l<99999 else 0,
        "runaway":bool(runaway),
        "elapsed":round(elapsed,1),
        "type_detail":dict(type_counts),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--rate",type=float,default=None)
    parser.add_argument("--seed",type=int,default=None)
    parser.add_argument("--aggregate-only",action="store_true")
    parser.add_argument("--sanity",action="store_true")
    parser.add_argument("--quiet-steps",type=int,default=QUIET_STEPS)
    args=parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)

    if args.aggregate_only: aggregate(); return
    if args.sanity:
        print("  SANITY: rate=0.001 seed=42, 300 quiet")
        r=run_one(42,0.001,300)
        print(f"  cyc={r['cycles']} types={r['cycle_type_count']} "
              f"swaps={r['swap_events']} rig={r['rigidity_index']:.2f} run={r['runaway']}")
        print("  OK" if not r["runaway"] else "  RUNAWAY!")
        return

    qs=args.quiet_steps
    rates=[args.rate] if args.rate is not None else RATE_GRID
    seeds=[args.seed] if args.seed else ALL_SEEDS

    for rate in rates:
        for seed in seeds:
            tag=f"rate{rate:.4f}"
            out_dir=OUTPUT_DIR/tag; out_dir.mkdir(parents=True,exist_ok=True)
            rf=out_dir/f"seed_{seed}.json"
            if rf.exists(): print(f"  {tag} s={seed}: skip"); continue
            print(f"  {tag} s={seed}...",flush=True)
            r=run_one(seed,rate,qs)
            # Serialize safely
            safe_r = {}
            for k,v in r.items():
                if isinstance(v,(np.integer,np.floating)): safe_r[k]=float(v)
                elif isinstance(v,np.bool_): safe_r[k]=bool(v)
                else: safe_r[k]=v
            with open(rf,"w") as f: json.dump(safe_r,f,indent=2)
            print(f"    → cyc={r['cycles']} types={r['cycle_type_count']} "
                  f"swaps={r['swap_events']} rig={r['rigidity_index']:.2f} ({r['elapsed']:.0f}s)")

    if args.rate is None and args.seed is None: aggregate()


def aggregate():
    rows=[]
    for d in sorted(OUTPUT_DIR.iterdir()):
        if not d.is_dir(): continue
        for f in sorted(d.glob("seed_*.json")):
            with open(f) as fh: rows.append(json.load(fh))
    if not rows: print("  No results."); return

    # Save flat summary (without type_detail dict)
    flat=[{k:v for k,v in r.items() if k!="type_detail"} for r in rows]
    with open(OUTPUT_DIR/"v18_intrusion_sweep_summary.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=flat[0].keys()); w.writeheader(); w.writerows(flat)

    agg=[]
    for rate in RATE_GRID:
        sub=[r for r in rows if abs(r["intrusion_rate"]-rate)<1e-6]
        if not sub: continue
        agg.append({
            "rate":rate,"n":len(sub),
            "med_cyc":round(np.median([r["cycles_per_1k"] for r in sub]),2),
            "med_types":round(np.median([r["cycle_type_count"] for r in sub]),1),
            "med_ent":round(np.median([r["cycle_type_entropy"] for r in sub]),4),
            "med_top1":round(np.median([r["top1_share"] for r in sub]),4),
            "med_island_strong":round(np.median([r["mean_island_strong"] for r in sub]),2),
            "med_island_mid":round(np.median([r["mean_island_mid"] for r in sub]),2),
            "med_coex_strong":round(np.median([r["coexistence_strong"] for r in sub]),4),
            "med_turnover_strong":round(np.median([r["turnover_strong"] for r in sub]),4),
            "med_turnover_mid":round(np.median([r["turnover_mid"] for r in sub]),4),
            "med_rigidity":round(np.median([r["rigidity_index"] for r in sub]),3),
            "med_bnd_strong":round(np.median([r["boundary_crossing_strong_1k"] for r in sub]),2),
            "med_bnd_all":round(np.median([r["boundary_crossing_all_1k"] for r in sub]),2),
            "med_X":round(np.median([r["X"] for r in sub]),4),
            "min_links_worst":min(r["min_links"] for r in sub),
            "any_runaway":any(r["runaway"] for r in sub),
            "med_attempts":round(np.median([r["intrusion_attempts"] for r in sub]),0),
            "med_success":round(np.median([r["intrusion_success"] for r in sub]),0),
            "med_bnd_nodes":round(np.median([r["mean_boundary_nodes"] for r in sub]),1),
        })

    with open(OUTPUT_DIR/"v18_intrusion_aggregate.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=agg[0].keys()); w.writeheader(); w.writerows(agg)

    # Collect all type details
    all_types=Counter()
    for r in rows:
        td=r.get("type_detail",{})
        for t,c in td.items(): all_types[t]+=c

    print(f"\n{'='*70}")
    print(f"  v1.8 BOUNDARY INTRUSION RESULTS ({len(rows)} runs)")
    print(f"{'='*70}")
    print(f"\n  {'rate':>7} {'cyc':>6} {'typ':>4} {'H':>6} {'top1':>5} {'isl_s':>5} {'isl_m':>5} "
          f"{'to_s':>6} {'to_m':>6} {'rig':>5} {'bnd_a':>6} {'X':>6} {'att':>5} {'suc':>5}")
    for a in agg:
        print(f"  {a['rate']:>7.4f} {a['med_cyc']:>6.1f} {a['med_types']:>4.1f} "
              f"{a['med_ent']:>6.3f} {a['med_top1']:>5.3f} {a['med_island_strong']:>5.2f} "
              f"{a['med_island_mid']:>5.2f} "
              f"{a['med_turnover_strong']:>6.3f} {a['med_turnover_mid']:>6.3f} "
              f"{a['med_rigidity']:>5.2f} "
              f"{a['med_bnd_all']:>6.1f} {a['med_X']:>6.4f} "
              f"{a['med_attempts']:>5.0f} {a['med_success']:>5.0f}")

    print(f"\n  Global cycle types: {len(all_types)}")
    for t,c in all_types.most_common(10):
        print(f"    {t}: {c}")

    # Plots
    fig,axes=plt.subplots(2,3,figsize=(20,12))
    fig.suptitle("ESDE Genesis v1.8 — Boundary Intrusion",fontsize=14,fontweight="bold")
    rs=[a["rate"] for a in agg]

    def pl(ax,key,title,c="#2ecc71",hline=None):
        ax.plot(rs,[a[key] for a in agg],"o-",color=c,ms=8,lw=2)
        if hline: ax.axhline(y=hline,color="red",ls="--",alpha=0.5)
        ax.set_title(title); ax.set_xlabel("intrusion_rate"); ax.grid(True,alpha=0.2)

    pl(axes[0][0],"med_cyc","Cycles/1k","#e74c3c")
    pl(axes[0][1],"med_types","Cycle Types","#2ecc71",hline=3)
    pl(axes[0][2],"med_ent","Type Entropy","#9b59b6")
    pl(axes[1][0],"med_turnover_mid","Island Turnover (MID S≥0.20)","#3498db")
    pl(axes[1][1],"med_rigidity","Rigidity Index","#e67e22")
    pl(axes[1][2],"med_X","Explainability X","#1abc9c")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/"v18_intrusion_plots.png",dpi=150,bbox_inches="tight")
    print(f"\n  Plot: {OUTPUT_DIR/'v18_intrusion_plots.png'}")

    achieved_3=any(a["med_types"]>=3 for a in agg)
    best_div=max(agg,key=lambda a:a["med_ent"])
    safe=[a for a in agg if a["min_links_worst"]>0 and not a["any_runaway"]]

    txt=f"""ESDE Genesis v1.8 — Boundary Intrusion Conclusion (FIXED)
=================================================
Sweep: intrusion_rate={RATE_GRID}
Seeds: {len(ALL_SEEDS)} | Quiet: {QUIET_STEPS}
Topography: var={TOPO_VAR} | Yield: syn={E_YIELD_SYN}
Fixes applied: A(lifetime keys), B(dual threshold), C(counters), D(all-edge boundary)

Goal: ≥3 cycle types?  {'YES' if achieved_3 else 'NO'}

Best diversity: rate={best_div['rate']}
  types={best_div['med_types']} entropy={best_div['med_ent']}
  cycles/1k={best_div['med_cyc']}
  turnover_strong={best_div['med_turnover_strong']} turnover_mid={best_div['med_turnover_mid']}
  rigidity={best_div['med_rigidity']}
  attempts={best_div['med_attempts']:.0f} success={best_div['med_success']:.0f}

Global cycle types observed: {len(all_types)}
{chr(10).join(f'  {t}: {c}' for t,c in all_types.most_common(10))}

Intrusion execution (per rate):
{chr(10).join(f'  rate={a["rate"]}: att={a["med_attempts"]:.0f} suc={a["med_success"]:.0f} bnd_nodes={a["med_bnd_nodes"]:.0f} to_mid={a["med_turnover_mid"]:.3f} rig={a["med_rigidity"]:.2f}' for a in agg)}

Safe (no runaway, links>0): {[a['rate'] for a in safe]}
"""
    with open(OUTPUT_DIR/"v18_conclusion.txt","w") as f: f.write(txt)
    print(txt)


if __name__=="__main__":
    main()
