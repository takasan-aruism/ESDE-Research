#!/usr/bin/env python3
"""
ESDE Genesis v1.7 — Latent Topography (Thin Heterogeneity)
=============================================================
Static node fertility F_i modulates latent refresh.
Goal: increase cycle-type diversity via spatial niche formation.

Audit corrections applied:
  - E_yield_syn=0.08, E_yield_auto=0.00 (conservative)
  - topography_variance sweep: {0.0, 0.10, 0.20, 0.35, 0.50}

Usage:
  python v17_topography.py --sanity
  python v17_topography.py --var 0.20 --seed 42
  python v17_topography.py --aggregate-only

  # Parallel (Ryzen):
  parallel -j 20 python v17_topography.py --var {1} --seed {2} \
    ::: 0.0 0.10 0.20 0.35 0.50 \
    ::: 42 123 456 789 2024 7 314 999 55 1337
  python v17_topography.py --aggregate-only
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

# Audit: conservative yields
E_YIELD_SYN=0.08; E_YIELD_AUTO=0.00
VAR_GRID=[0.0, 0.10, 0.20, 0.35, 0.50]
ALL_SEEDS=[42,123,456,789,2024,7,314,999,55,1337]
OUTPUT_DIR=Path("outputs_v17")


def init_fertility(state, variance, seed):
    """Generate static fertility field. Mean=1.0, spread=variance."""
    rng = np.random.RandomState(seed + 7777)
    if variance <= 0:
        state.F = np.ones(state.n_nodes)
        return
    u = rng.uniform(-1, 1, state.n_nodes)
    raw = 1.0 + variance * u
    raw = np.clip(raw, 0.01, 2.0)  # safety floor
    state.F = raw / raw.mean()  # normalize mean=1.0


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
                            cycles.append({"node":nid,"start":h[i][0],"end":h[j][0],
                                           "type":tp,"rule":2 if ss[i+2]==1 else 1})
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
        if len(comp)>=3: islands.append(frozenset(comp))
    return islands


def shannon(counts):
    t=sum(counts)
    if t==0: return 0.0
    ps=[c/t for c in counts if c>0]
    return -sum(p*np.log2(p) for p in ps)


def run_one(seed, variance, quiet_steps=QUIET_STEPS):
    p=PARAMS
    state=GenesisState(N_NODES,C_MAX,seed)
    init_fertility(state, variance, seed)

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
    island_counts=[]; prev_islands=[]
    island_births=0; island_deaths=0
    turnover_vals=[]; boundary_events=0
    island_lifetimes=defaultdict(int)  # island_id -> window count
    dead_lifetimes=[]
    runaway=False
    # Track per-node reaction types for fertility correlation
    node_syn=Counter(); node_auto=Counter()

    for step in range(quiet_steps):
        realizer.step(state); physics.step_pre_chemistry(state)
        rxns=chem.step(state)
        for r in rxns:
            if r.rule==1:
                syn_count+=1; node_syn[r.node_i]+=1; node_syn[r.node_j]+=1
            elif r.rule==2:
                auto_count+=1; node_auto[r.node_i]+=1; node_auto[r.node_j]+=1
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

        # Window
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

            cur_islands=find_islands(state)
            island_counts.append(len(cur_islands))

            # Taka lens: births/deaths/turnover
            cur_set=set(cur_islands)
            prev_set=set(prev_islands)
            # Match by max overlap
            matched_cur=set(); matched_prev=set()
            pairs=[]
            for ci in cur_set:
                best_j=None; best_ov=0
                for pj in prev_set:
                    ov=len(ci&pj)
                    if ov>best_ov: best_ov=ov; best_j=pj
                if best_j and best_ov>=2:
                    pairs.append((ci,best_j))
                    matched_cur.add(ci); matched_prev.add(best_j)

            new_births=len(cur_set-matched_cur)
            new_deaths=len(prev_set-matched_prev)
            island_births+=new_births; island_deaths+=new_deaths

            # Turnover: Jaccard between matched pairs
            for ci,pj in pairs:
                j=len(ci&pj)/len(ci|pj) if ci|pj else 1
                turnover_vals.append(1-j)

            # Island lifetime tracking
            new_active={}
            for ci in cur_set:
                iid=id(ci)  # use hash as proxy
                if ci in matched_cur:
                    # Find matching prev
                    for c2,p2 in pairs:
                        if c2==ci:
                            old_id=id(p2)
                            new_active[iid]=island_lifetimes.get(old_id,0)+1
                            break
                else:
                    new_active[iid]=1
            for pid in prev_set-matched_prev:
                dead_lifetimes.append(island_lifetimes.get(id(pid),1))
            island_lifetimes=new_active

            # Boundary crossing: strong links between island and non-island nodes
            all_island_nodes=set()
            for isl in cur_islands: all_island_nodes|=isl
            bc=sum(1 for k in state.alive_l if state.S[k]>=S_DOM
                   and bool(k[0] in all_island_nodes) != bool(k[1] in all_island_nodes))
            boundary_events+=bc

            prev_islands=cur_islands

            # Runaway check
            e_vals=[state.E[i] for i in state.alive_n]
            if e_vals and np.median(e_vals)>=0.80:
                runaway=True

        if step%1000==999:
            print(f"      q{step+1}: L={len(state.alive_l):>4} "
                  f"isl={island_counts[-1] if island_counts else 0} "
                  f"syn={syn_count} auto={auto_count} ({time.time()-t0:.0f}s)",flush=True)

    # Post-run
    all_cycles=tracker.find()
    type_counts=Counter(c["type"] for c in all_cycles)
    n_types=len(type_counts)
    type_ent=shannon(list(type_counts.values()))
    top1=type_counts.most_common(1)[0][1]/len(all_cycles) if all_cycles else 0
    spr=np.mean(spr_v) if spr_v else 0
    coex=sum(1 for ic in island_counts if ic>=2)/max(len(island_counts),1)
    mean_turn=np.mean(turnover_vals) if turnover_vals else 0
    med_life=np.median(dead_lifetimes) if dead_lifetimes else (np.median(list(island_lifetimes.values())) if island_lifetimes else 0)
    rigidity=med_life/(1+mean_turn) if (1+mean_turn)>0 else 0

    # X
    if s_hists:
        mh=np.mean(s_hists,axis=0); t=mh.sum()
        if t>0: pp=mh/t; pp=pp[pp>0]; H=-np.sum(pp*np.log2(pp)); C=1-H/np.log2(5)
        else: C=0
    else: C=0
    X=round(C+spr,4)

    # Fertility correlation
    fert_syn=[]; fert_auto=[]
    for nid in range(N_NODES):
        if node_syn[nid]>0: fert_syn.append((state.F[nid], node_syn[nid]))
        if node_auto[nid]>0: fert_auto.append((state.F[nid], node_auto[nid]))
    if len(fert_syn)>5:
        fs,cs=zip(*fert_syn)
        if np.std(fs)>0 and np.std(cs)>0:
            fert_corr_syn=round(float(np.corrcoef(fs,cs)[0,1]),4)
        else: fert_corr_syn=0
    else: fert_corr_syn=0
    if len(fert_auto)>5:
        fa,ca=zip(*fert_auto)
        if np.std(fa)>0 and np.std(ca)>0:
            fert_corr_auto=round(float(np.corrcoef(fa,ca)[0,1]),4)
        else: fert_corr_auto=0
    else: fert_corr_auto=0

    n_win=max(len(island_counts),1)
    elapsed=time.time()-t0

    return {
        "seed":int(seed),"variance":variance,
        "cycles":len(all_cycles),
        "cycles_per_1k":round(len(all_cycles)/(quiet_steps/1000),3),
        "cycle_type_count":n_types,
        "cycle_type_entropy":round(type_ent,4),
        "top1_share":round(top1,4),
        "syn_count":syn_count,"auto_count":auto_count,
        "mean_island":round(np.mean(island_counts),2) if island_counts else 0,
        "max_island":max(island_counts) if island_counts else 0,
        "coexistence_rate":round(coex,4),
        "island_births_per_1k":round(island_births/(quiet_steps/1000),2),
        "island_deaths_per_1k":round(island_deaths/(quiet_steps/1000),2),
        "mean_turnover":round(mean_turn,4),
        "boundary_crossing_per_1k":round(boundary_events/(quiet_steps/1000),2),
        "rigidity_index":round(rigidity,3),
        "fert_corr_syn":fert_corr_syn,"fert_corr_auto":fert_corr_auto,
        "spr":round(spr,4),"X":X,
        "min_links":min_l if min_l<99999 else 0,
        "runaway":bool(runaway),
        "elapsed":round(elapsed,1),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--var",type=float,default=None)
    parser.add_argument("--seed",type=int,default=None)
    parser.add_argument("--aggregate-only",action="store_true")
    parser.add_argument("--sanity",action="store_true")
    parser.add_argument("--quiet-steps",type=int,default=QUIET_STEPS)
    args=parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)

    if args.aggregate_only: aggregate(); return
    if args.sanity:
        print("  SANITY: var=0.20 seed=42, 300 quiet")
        r=run_one(42,0.20,300)
        print(f"  cyc={r['cycles']} types={r['cycle_type_count']} "
              f"isl={r['mean_island']:.1f} run={r['runaway']}")
        print("  OK" if not r["runaway"] else "  RUNAWAY!")
        return

    qs=args.quiet_steps
    vars_list=[args.var] if args.var is not None else VAR_GRID
    seeds=[args.seed] if args.seed else ALL_SEEDS

    for v in vars_list:
        for seed in seeds:
            tag=f"var{v:.2f}"
            out_dir=OUTPUT_DIR/tag; out_dir.mkdir(parents=True,exist_ok=True)
            rf=out_dir/f"seed_{seed}.json"
            if rf.exists(): print(f"  {tag} s={seed}: skip"); continue
            print(f"  {tag} s={seed}...",flush=True)
            r=run_one(seed,v,qs)
            with open(rf,"w") as f: json.dump(r,f,indent=2)
            print(f"    → cyc={r['cycles']} types={r['cycle_type_count']} "
                  f"isl={r['mean_island']:.1f} rig={r['rigidity_index']:.2f} "
                  f"({r['elapsed']:.0f}s)")

    if args.var is None and args.seed is None: aggregate()


def aggregate():
    rows=[]
    for d in sorted(OUTPUT_DIR.iterdir()):
        if not d.is_dir(): continue
        for f in sorted(d.glob("seed_*.json")):
            with open(f) as fh: rows.append(json.load(fh))
    if not rows: print("  No results."); return

    with open(OUTPUT_DIR/"v17_summary.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

    agg=[]
    for v in VAR_GRID:
        sub=[r for r in rows if abs(r["variance"]-v)<0.001]
        if not sub: continue
        agg.append({
            "variance":v,"n":len(sub),
            "med_cyc":round(np.median([r["cycles_per_1k"] for r in sub]),2),
            "med_types":round(np.median([r["cycle_type_count"] for r in sub]),1),
            "med_type_ent":round(np.median([r["cycle_type_entropy"] for r in sub]),4),
            "med_top1":round(np.median([r["top1_share"] for r in sub]),4),
            "med_island":round(np.median([r["mean_island"] for r in sub]),2),
            "med_coex":round(np.median([r["coexistence_rate"] for r in sub]),4),
            "med_turnover":round(np.median([r["mean_turnover"] for r in sub]),4),
            "med_rigidity":round(np.median([r["rigidity_index"] for r in sub]),3),
            "med_fert_syn":round(np.median([r["fert_corr_syn"] for r in sub]),4),
            "med_fert_auto":round(np.median([r["fert_corr_auto"] for r in sub]),4),
            "med_X":round(np.median([r["X"] for r in sub]),4),
            "min_links_worst":min(r["min_links"] for r in sub),
            "any_runaway":any(r["runaway"] for r in sub),
        })

    with open(OUTPUT_DIR/"v17_aggregate.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=agg[0].keys()); w.writeheader(); w.writerows(agg)

    print(f"\n{'='*70}")
    print(f"  v1.7 LATENT TOPOGRAPHY RESULTS ({len(rows)} runs)")
    print(f"{'='*70}")
    print(f"\n  {'var':>5} {'cyc':>6} {'typ':>4} {'H':>6} {'isl':>5} {'coex':>6} "
          f"{'turn':>6} {'rig':>5} {'f_syn':>6} {'f_auto':>7} {'X':>6}")
    for a in agg:
        print(f"  {a['variance']:>5.2f} {a['med_cyc']:>6.1f} {a['med_types']:>4.1f} "
              f"{a['med_type_ent']:>6.3f} {a['med_island']:>5.2f} {a['med_coex']:>6.3f} "
              f"{a['med_turnover']:>6.3f} {a['med_rigidity']:>5.2f} "
              f"{a['med_fert_syn']:>6.3f} {a['med_fert_auto']:>7.3f} {a['med_X']:>6.4f}")

    # Plots
    fig,axes=plt.subplots(2,3,figsize=(20,12))
    fig.suptitle("ESDE Genesis v1.7 — Latent Topography",fontsize=14,fontweight="bold")
    vs=[a["variance"] for a in agg]

    def pl(ax,key,title,color="#2ecc71",hline=None):
        ax.plot(vs,[a[key] for a in agg],"o-",color=color,ms=8,lw=2)
        if hline is not None: ax.axhline(y=hline,color="red",ls="--",alpha=0.5)
        ax.set_title(title); ax.set_xlabel("topography_variance"); ax.grid(True,alpha=0.2)

    pl(axes[0][0],"med_cyc","Cycles/1k","#e74c3c")
    pl(axes[0][1],"med_types","Cycle Types","#2ecc71",hline=3)
    pl(axes[0][2],"med_type_ent","Type Entropy","#9b59b6")
    pl(axes[1][0],"med_coex","Coexistence Rate","#3498db")
    pl(axes[1][1],"med_rigidity","Rigidity Index","#e67e22")

    # Fertility correlation
    ax=axes[1][2]
    ax.plot(vs,[a["med_fert_syn"] for a in agg],"o-",label="syn~F",color="#e74c3c",ms=6)
    ax.plot(vs,[a["med_fert_auto"] for a in agg],"s-",label="auto~F",color="#3498db",ms=6)
    ax.axhline(y=0,color="gray",ls=":",alpha=0.5)
    ax.set_title("Fertility-Reaction Correlation"); ax.legend(); ax.grid(True,alpha=0.2)
    ax.set_xlabel("topography_variance")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/"v17_topography_plots.png",dpi=150,bbox_inches="tight")
    print(f"\n  Plot: {OUTPUT_DIR/'v17_topography_plots.png'}")

    # Conclusion
    achieved_3=any(a["med_types"]>=3 for a in agg)
    best_div=max(agg,key=lambda a:a["med_type_ent"])
    safe=[a for a in agg if a["min_links_worst"]>0 and not a["any_runaway"]]

    txt=f"""ESDE Genesis v1.7 — Latent Topography Conclusion
=================================================
Sweep: topography_variance={VAR_GRID}
Seeds: {len(ALL_SEEDS)} | Quiet: {QUIET_STEPS} | E_yield_syn={E_YIELD_SYN}

Goal: ≥3 cycle types?  {'YES' if achieved_3 else 'NO'}

Best diversity: var={best_div['variance']}
  types={best_div['med_types']} entropy={best_div['med_type_ent']}
  cycles/1k={best_div['med_cyc']} coexistence={best_div['med_coex']}

Fertility correlation (median across seeds):
  Synthesis ~ F: {best_div['med_fert_syn']} (positive = furnaces prefer fertile zones)
  Autocatalysis ~ F: {best_div['med_fert_auto']}

Rigidity vs Diversity:
{chr(10).join(f"  var={a['variance']}: rigidity={a['med_rigidity']:.2f} types={a['med_types']}" for a in agg)}

Safe band (no runaway, links>0): {[a['variance'] for a in safe]}
Runaway flags: {sum(1 for a in agg if a['any_runaway'])} variance points
"""
    with open(OUTPUT_DIR/"v17_conclusion.txt","w") as f: f.write(txt)
    print(txt)


if __name__=="__main__":
    main()
