#!/usr/bin/env python3
"""
ESDE Genesis v1.6 — Reaction Yield Asymmetry Sweep
=====================================================
Synthesis yields energy, Autocatalysis yields less (or zero).
Goal: increase cycle-type diversity while keeping η≥0.8.

Usage:
  python v16_yield_sweep.py --sanity
  python v16_yield_sweep.py --syn 0.08 --auto 0.00 --seed 42
  python v16_yield_sweep.py                    # full sweep (sequential)
  python v16_yield_sweep.py --aggregate-only

  # Parallel (Ryzen):
  parallel -j 20 python v16_yield_sweep.py --syn {1} --auto {2} --seed {3} \
    ::: 0.05 0.08 0.12 0.16 ::: 0.00 0.01 0.03 \
    ::: 42 123 456 789 2024 7 314 999 55 1337
  python v16_yield_sweep.py --aggregate-only
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

N_NODES=200; C_MAX=1.0; INJECTION_STEPS=300; INJECT_INTERVAL=3
QUIET_STEPS=5000; BETA=1.0; NODE_DECAY=0.005; BIAS=0.7; WINDOW=200
S_DOM=0.30
STRENGTH_BINS=[(0,0.05),(0.05,0.1),(0.1,0.2),(0.2,0.3),(0.3,1.01)]
STATE_NAMES={0:"Dust",1:"A",2:"B",3:"C"}

PARAMS={"reaction_energy_threshold":0.26,"link_death_threshold":0.007,
    "background_injection_prob":0.003,"exothermic_release_amount":0.17,
    "p_link_birth":0.010,"latent_to_active_threshold":0.07,
    "latent_refresh_rate":0.003,"auto_growth_rate":0.03}

SYN_GRID=[0.05,0.08,0.12,0.16]
AUTO_GRID=[0.00,0.01,0.03]
ALL_SEEDS=[42,123,456,789,2024,7,314,999,55,1337]
OUTPUT_DIR=Path("outputs_v16")


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


def find_islands(state):
    adj=defaultdict(set)
    for k in state.alive_l:
        if state.S[k]>=S_DOM: adj[k[0]].add(k[1]); adj[k[1]].add(k[0])
    visited=set(); islands=[]
    for s in adj:
        if s in visited: continue
        q=[s]; comp=set()
        while q:
            n=q.pop()
            if n in visited: continue
            visited.add(n); comp.add(n)
            for nb in adj[n]:
                if nb not in visited: q.append(nb)
        if len(comp)>=3: islands.append(comp)
    return islands


def shannon(counts):
    t=sum(counts)
    if t==0: return 0.0
    ps=[c/t for c in counts if c>0]
    return -sum(p*np.log2(p) for p in ps)


def run_one(seed, e_syn, e_auto, quiet_steps=QUIET_STEPS):
    p=PARAMS
    state=GenesisState(N_NODES,C_MAX,seed)
    physics=GenesisPhysics(PhysicsParams(exclusion_enabled=True,resonance_enabled=True,
        phase_enabled=True,beta=BETA,decay_rate_node=NODE_DECAY,K_sync=0.1,alpha=0.0,gamma=1.0))
    cp=ChemistryParams(enabled=True,E_thr=p["reaction_energy_threshold"],
        exothermic_release=p["exothermic_release_amount"],
        E_yield_syn=e_syn, E_yield_auto=e_auto)
    chem=ChemistryEngine(cp)
    rp=RealizationParams(enabled=True,p_link_birth=p["p_link_birth"],
        latent_to_active_threshold=p["latent_to_active_threshold"],
        latent_refresh_rate=p["latent_refresh_rate"])
    realizer=RealizationOperator(rp)
    grower=AutoGrowthEngine(AutoGrowthParams(enabled=True,auto_growth_rate=p["auto_growth_rate"]))
    state.EXTINCTION=p["link_death_threshold"]
    tracker=CT(); g_scores=np.zeros(N_NODES)
    t0=time.time()

    # Injection
    for step in range(INJECTION_STEPS):
        if step%INJECT_INTERVAL==0:
            tgts=physics.inject(state); chem.seed_on_injection(state,tgts or[])
        physics.step_pre_chemistry(state); chem.step(state)
        cd=physics.step_resonance(state); grower.step(state)
        physics.step_decay_exclusion(state); tracker.rec(state,state.step-1)

    # Quiet
    syn_count=0; auto_count=0
    spr_v=[]; s_hists=[]; min_l=99999
    island_counts=[]; e_medians=[]
    island_prev=set()  # for turnover
    boundary_crossings=0; island_births=0; island_deaths=0

    # Runaway detection
    runaway=False

    for step in range(quiet_steps):
        realizer.step(state); physics.step_pre_chemistry(state)
        rxns=chem.step(state)
        for r in rxns:
            if r.rule==1: syn_count+=1
            elif r.rule==2: auto_count+=1
        cd=physics.step_resonance(state)
        g_scores[:]=0; grower.step(state)
        for k in state.alive_l:
            r=state.R.get(k,0.0)
            if r>0:
                a=min(grower.params.auto_growth_rate*r,max(state.get_latent(k[0],k[1]),0))
                if a>0: g_scores[k[0]]+=a; g_scores[k[1]]+=a
        gz=float(g_scores.sum())
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

        # Window metrics
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

            islands=find_islands(state)
            island_counts.append(len(islands))

            # Island turnover
            cur_sets={frozenset(isl) for isl in islands}
            new_isls=cur_sets-island_prev
            dead_isls=island_prev-cur_sets
            island_births+=len(new_isls)
            island_deaths+=len(dead_isls)
            island_prev=cur_sets

            # Energy median
            e_vals=[state.E[i] for i in state.alive_n]
            med_e=float(np.median(e_vals)) if e_vals else 0
            e_medians.append(med_e)

            # Runaway check
            if med_e>=0.80:
                runaway=True
                print(f"    RUNAWAY: med_E={med_e:.3f} at step {step+1}", flush=True)

        if step%1000==999:
            print(f"      q{step+1}: L={len(state.alive_l):>4} "
                  f"syn={syn_count} auto={auto_count} ({time.time()-t0:.0f}s)",flush=True)

    # Post-run
    all_cycles=tracker.find()
    type_counts=Counter(c["type"] for c in all_cycles)
    n_types=len(type_counts)
    type_ent=shannon(list(type_counts.values()))
    top1=type_counts.most_common(1)[0][1]/len(all_cycles) if all_cycles else 0
    spr=np.mean(spr_v) if spr_v else 0
    coex_rate=sum(1 for ic in island_counts if ic>=2)/max(len(island_counts),1)

    # X
    if s_hists:
        mh=np.mean(s_hists,axis=0); t=mh.sum()
        if t>0: pp=mh/t; pp=pp[pp>0]; H=-np.sum(pp*np.log2(pp)); C=1-H/np.log2(5)
        else: C=0
    else: C=0
    X=round(C+spr,4)

    ts=quiet_steps
    elapsed=time.time()-t0
    total_rxn=syn_count+auto_count
    sa_ratio=syn_count/max(auto_count,1)

    return {
        "seed":int(seed),"e_syn":e_syn,"e_auto":e_auto,
        "cycles":len(all_cycles),
        "cycles_per_1k":round(len(all_cycles)/(ts/1000),3),
        "cycle_type_count":n_types,
        "cycle_type_entropy":round(type_ent,4),
        "top1_share":round(top1,4),
        "syn_count":syn_count,"auto_count":auto_count,
        "syn_auto_ratio":round(sa_ratio,3),
        "mean_island":round(np.mean(island_counts),2) if island_counts else 0,
        "coexistence_rate":round(coex_rate,4),
        "island_births":island_births,"island_deaths":island_deaths,
        "spr":round(spr,4),"X":X,
        "min_links":min_l if min_l<99999 else 0,
        "runaway":runaway,
        "elapsed":round(elapsed,1),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--syn",type=float,default=None)
    parser.add_argument("--auto",type=float,default=None)
    parser.add_argument("--seed",type=int,default=None)
    parser.add_argument("--aggregate-only",action="store_true")
    parser.add_argument("--sanity",action="store_true")
    parser.add_argument("--quiet-steps",type=int,default=QUIET_STEPS)
    args=parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)

    if args.aggregate_only:
        aggregate(); return

    if args.sanity:
        print("  SANITY: syn=0.08 auto=0.00 seed=42, 300 quiet")
        r=run_one(42,0.08,0.00,300)
        print(f"  cyc={r['cycles']} types={r['cycle_type_count']} "
              f"syn={r['syn_count']} auto={r['auto_count']} "
              f"runaway={r['runaway']}")
        print("  OK" if not r["runaway"] else "  WARNING: runaway!")
        return

    qs=args.quiet_steps
    syn_list=[args.syn] if args.syn is not None else SYN_GRID
    auto_list=[args.auto] if args.auto is not None else AUTO_GRID
    seeds=[args.seed] if args.seed else ALL_SEEDS

    for es in syn_list:
        for ea in auto_list:
            for seed in seeds:
                tag=f"syn{es:.2f}_auto{ea:.2f}"
                out_dir=OUTPUT_DIR/tag
                out_dir.mkdir(parents=True,exist_ok=True)
                rf=out_dir/f"seed_{seed}.json"
                if rf.exists():
                    print(f"  {tag} seed={seed}: skip"); continue
                print(f"  {tag} seed={seed}...",flush=True)
                r=run_one(seed,es,ea,qs)
                with open(rf,"w") as f:
                    json.dump(r,f,indent=2)
                print(f"    → cyc={r['cycles']} types={r['cycle_type_count']} "
                      f"s/a={r['syn_count']}/{r['auto_count']} ({r['elapsed']:.0f}s)")

    if args.syn is None and args.auto is None and args.seed is None:
        aggregate()


def aggregate():
    rows=[]
    for d in sorted(OUTPUT_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("."): continue
        for f in sorted(d.glob("seed_*.json")):
            with open(f) as fh: rows.append(json.load(fh))

    if not rows: print("  No results."); return

    with open(OUTPUT_DIR/"v16_yield_sweep_summary.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

    # Aggregate per grid point
    agg=[]
    for es in SYN_GRID:
        for ea in AUTO_GRID:
            sub=[r for r in rows if abs(r["e_syn"]-es)<0.001 and abs(r["e_auto"]-ea)<0.001]
            if not sub: continue
            agg.append({
                "e_syn":es,"e_auto":ea,"n_seeds":len(sub),
                "med_cyc_1k":round(np.median([r["cycles_per_1k"] for r in sub]),3),
                "med_types":round(np.median([r["cycle_type_count"] for r in sub]),1),
                "med_type_ent":round(np.median([r["cycle_type_entropy"] for r in sub]),4),
                "med_top1":round(np.median([r["top1_share"] for r in sub]),4),
                "med_sa_ratio":round(np.median([r["syn_auto_ratio"] for r in sub]),3),
                "med_island":round(np.median([r["mean_island"] for r in sub]),2),
                "med_coex":round(np.median([r["coexistence_rate"] for r in sub]),4),
                "med_X":round(np.median([r["X"] for r in sub]),4),
                "min_links_worst":min(r["min_links"] for r in sub),
                "any_runaway":any(r["runaway"] for r in sub),
                "seeds_cyc":sum(1 for r in sub if r["cycles"]>0),
            })

    with open(OUTPUT_DIR/"v16_yield_sweep_aggregate.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=agg[0].keys()); w.writeheader(); w.writerows(agg)

    print(f"\n{'='*70}")
    print(f"  v1.6 YIELD ASYMMETRY RESULTS ({len(rows)} runs)")
    print(f"{'='*70}")
    print(f"\n  {'syn':>5} {'auto':>5} {'cyc/1k':>7} {'types':>6} {'H_type':>7} "
          f"{'top1':>5} {'s/a':>6} {'isl':>5} {'X':>6} {'run':>4}")
    for a in agg:
        print(f"  {a['e_syn']:>5.2f} {a['e_auto']:>5.2f} {a['med_cyc_1k']:>7.1f} "
              f"{a['med_types']:>6.1f} {a['med_type_ent']:>7.3f} "
              f"{a['med_top1']:>5.3f} {a['med_sa_ratio']:>6.1f} "
              f"{a['med_island']:>5.1f} {a['med_X']:>6.4f} "
              f"{'!' if a['any_runaway'] else '.'}")

    # Plots
    fig,axes=plt.subplots(2,3,figsize=(20,12))
    fig.suptitle("ESDE Genesis v1.6 — Reaction Yield Asymmetry",
                 fontsize=14,fontweight="bold")

    def hm(ax,key,title,cmap="viridis",vmin=None,vmax=None):
        grid=np.zeros((len(SYN_GRID),len(AUTO_GRID)))
        for a in agg:
            si=SYN_GRID.index(a["e_syn"]); ai=AUTO_GRID.index(a["e_auto"])
            grid[si,ai]=a[key]
        im=ax.imshow(grid,aspect="auto",origin="lower",cmap=cmap,vmin=vmin,vmax=vmax)
        ax.set_xticks(range(len(AUTO_GRID))); ax.set_xticklabels([f"{v:.2f}" for v in AUTO_GRID])
        ax.set_yticks(range(len(SYN_GRID))); ax.set_yticklabels([f"{v:.2f}" for v in SYN_GRID])
        ax.set_xlabel("E_yield_auto"); ax.set_ylabel("E_yield_syn")
        ax.set_title(title)
        for i in range(len(SYN_GRID)):
            for j in range(len(AUTO_GRID)):
                ax.text(j,i,f"{grid[i,j]:.2f}",ha="center",va="center",fontsize=10,
                        color="white" if grid[i,j]<(vmax or grid.max())*0.5 else "black")
        plt.colorbar(im,ax=ax,shrink=0.8)

    hm(axes[0][0],"med_cyc_1k","Cycles/1k","YlOrRd")
    hm(axes[0][1],"med_types","Cycle Types","Greens",0,5)
    hm(axes[0][2],"med_type_ent","Type Entropy","plasma",0,2)
    hm(axes[1][0],"med_sa_ratio","Syn/Auto Ratio","coolwarm")
    hm(axes[1][1],"med_X","Explainability X","viridis")
    hm(axes[1][2],"med_coex","Coexistence Rate","Blues",0,1)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/"v16_yield_sweep_plots.png",dpi=150,bbox_inches="tight")
    print(f"\n  Plot: {OUTPUT_DIR/'v16_yield_sweep_plots.png'}")

    # Conclusion
    best_div=max(agg,key=lambda a:a["med_type_ent"]) if agg else None
    best_cyc=max(agg,key=lambda a:a["med_cyc_1k"]) if agg else None
    achieved_3=any(a["med_types"]>=3 for a in agg)

    txt=f"""ESDE Genesis v1.6 — Yield Asymmetry Conclusion
=================================================
Grid: E_yield_syn={SYN_GRID} × E_yield_auto={AUTO_GRID}
Seeds: {len(ALL_SEEDS)} | Quiet: {QUIET_STEPS}

Goal: ≥3 cycle types with η≥0.8?  {'YES' if achieved_3 else 'NO'}

Best diversity:
  syn={best_div['e_syn']} auto={best_div['e_auto']}
  types={best_div['med_types']} entropy={best_div['med_type_ent']}
  cycles/1k={best_div['med_cyc_1k']}

Best cycles:
  syn={best_cyc['e_syn']} auto={best_cyc['e_auto']}
  cycles/1k={best_cyc['med_cyc_1k']} types={best_cyc['med_types']}

Runaway flags: {sum(1 for a in agg if a['any_runaway'])} grid points
"""
    with open(OUTPUT_DIR/"v16_conclusion.txt","w") as f: f.write(txt)
    print(txt)


if __name__=="__main__":
    main()
