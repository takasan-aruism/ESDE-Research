#!/usr/bin/env python3
"""
ESDE Genesis v1.9d — k* Reproducibility Test (Ryzen Runner)
==============================================================
Runs v18O2-style data collection at 3 plb × 5 rates × 10 seeds,
then postprocesses with v1.9c labels and reports k* stability.

Usage:
  python v19d_repro.py --sanity
  python v19d_repro.py --plb 0.010 --rate 0.002 --seed 42
  python v19d_repro.py --aggregate-only

  # Parallel (Ryzen):
  parallel -j 20 python v19d_repro.py --plb {1} --rate {2} --seed {3} \
    ::: 0.007 0.008 0.010 ::: 0.0 0.0005 0.001 0.002 0.005 \
    ::: 42 123 456 789 2024 7 314 999 55 1337
  python v19d_repro.py --aggregate-only
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
STRENGTH_BINS=[(0,0.05),(0.05,0.1),(0.1,0.2),(0.2,0.3),(0.3,1.01)]
R_BITS_KEYS=["000","001","010","011","100","101","110","111"]
STATE_NAMES={0:"Dust",1:"A",2:"B",3:"C"}
E_YIELD_SYN=0.08; E_YIELD_AUTO=0.00; TOPO_VAR=0.20
LAMBDA=1.0; MU=0.5; K_LEVELS=[0,1,2,3,4]

BASE={"reaction_energy_threshold":0.26,"link_death_threshold":0.007,
    "background_injection_prob":0.003,"exothermic_release_amount":0.17,
    "latent_to_active_threshold":0.07,"latent_refresh_rate":0.003,"auto_growth_rate":0.03}

PLB_GRID=[0.007,0.008,0.010]
RATE_GRID=[0.0,0.0005,0.001,0.002,0.005]
ALL_SEEDS=[42,123,456,789,2024,7,314,999,55,1337]
OUTPUT_DIR=Path("outputs_v19d")


def init_fertility(state,v,seed):
    rng=np.random.RandomState(seed+7777)
    if v<=0: state.F=np.ones(state.n_nodes); return
    u=rng.uniform(-1,1,state.n_nodes); raw=1.0+v*u; raw=np.clip(raw,0.01,2.0)
    state.F=raw/raw.mean()


def shannon(c):
    t=sum(c); return -sum((x/t)*np.log2(x/t) for x in c if x>0) if t>0 else 0.0


def ctx_to_label(ctx,k):
    if k==0: return "C"
    rb=ctx.get("r_bits","000")
    s=int(rb[0]); m=int(rb[1]) if len(rb)>=2 else 0; w=int(rb[2]) if len(rb)>=3 else 0
    res="High" if s else ("Mid" if m else "Low")
    if k==1: return f"C_{res}"
    bd="Edge" if ctx.get("boundary_mid",0)==1 else "Core"
    if k==2: return f"C_{res}_{bd}"
    scale="Strong" if s else ("Mid" if m else ("WeakOnly" if w else "None"))
    if k==3: return f"C_{res}_{bd}_{scale}"
    ie="1p" if ctx.get("intrusion_bin",0)>=1 else "0"
    return f"C_{res}_{bd}_{scale}_{ie}"


def drift_jsd(n1,n2,k):
    if not n1 or not n2: return None
    l1=Counter(ctx_to_label(n,k) for n in n1); l2=Counter(ctx_to_label(n,k) for n in n2)
    al=set(l1)|set(l2); t1=sum(l1.values()); t2=sum(l2.values())
    if t1==0 or t2==0: return None
    p=np.array([l1.get(l,0)/t1 for l in al]); q=np.array([l2.get(l,0)/t2 for l in al])
    m=(p+q)/2
    kl=lambda a,b: sum(a[i]*np.log2(a[i]/b[i]) for i in range(len(a)) if a[i]>0 and b[i]>0)
    return round(float(np.sqrt((kl(p,m)+kl(q,m))/2)),4)


def run_one(seed, plb, rate, quiet_steps=QUIET_STEPS):
    p=dict(BASE); p["p_link_birth"]=plb
    state=GenesisState(N_NODES,C_MAX,seed)
    init_fertility(state,TOPO_VAR,seed)
    physics=GenesisPhysics(PhysicsParams(exclusion_enabled=True,resonance_enabled=True,
        phase_enabled=True,beta=BETA,decay_rate_node=NODE_DECAY,K_sync=0.1,alpha=0.0,gamma=1.0))
    cp=ChemistryParams(enabled=True,E_thr=p["reaction_energy_threshold"],
        exothermic_release=p["exothermic_release_amount"],E_yield_syn=E_YIELD_SYN,E_yield_auto=E_YIELD_AUTO)
    chem=ChemistryEngine(cp)
    rp=RealizationParams(enabled=True,p_link_birth=plb,latent_to_active_threshold=p["latent_to_active_threshold"],
        latent_refresh_rate=p["latent_refresh_rate"])
    realizer=RealizationOperator(rp)
    grower=AutoGrowthEngine(AutoGrowthParams(enabled=True,auto_growth_rate=p["auto_growth_rate"]))
    intruder=BoundaryIntrusionOperator(intrusion_rate=rate)
    state.EXTINCTION=p["link_death_threshold"]
    g_scores=np.zeros(N_NODES); t0=time.time()
    node_intr=Counter()

    for step in range(INJECTION_STEPS):
        if step%INJECT_INTERVAL==0:
            tgts=physics.inject(state); chem.seed_on_injection(state,tgts or[])
        physics.step_pre_chemistry(state); chem.step(state)
        cd=physics.step_resonance(state); grower.step(state)
        physics.step_decay_exclusion(state)

    # Quiet: collect per-window k* sequence
    k_star_seq=[]; prev_nodes=None

    for step in range(quiet_steps):
        realizer.step(state); physics.step_pre_chemistry(state)
        chem.step(state); cd=physics.step_resonance(state)
        g_scores[:]=0; grower.step(state)
        for k in state.alive_l:
            r=state.R.get(k,0.0)
            if r>0:
                a=min(grower.params.auto_growth_rate*r,max(state.get_latent(k[0],k[1]),0))
                if a>0: g_scores[k[0]]+=a; g_scores[k[1]]+=a
        gz=float(g_scores.sum())
        pre_S={k:state.S[k] for k in state.alive_l}
        intruder.step(state)
        for k in state.alive_l:
            if k in pre_S and abs(state.S[k]-pre_S[k])>0.001:
                node_intr[k[0]]+=1; node_intr[k[1]]+=1
        physics.step_decay_exclusion(state)

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
            # Build node contexts for C-nodes
            isl_s=find_islands_sets(state,0.30); isl_m=find_islands_sets(state,0.20); isl_w=find_islands_sets(state,0.10)
            nm_s={n:1 for isl in isl_s for n in isl}
            nm_m={n:1 for isl in isl_m for n in isl}
            nm_w={n:1 for isl in isl_w for n in isl}
            bnd_m=set()
            for isl in isl_m:
                for n in isl:
                    if n not in state.alive_n: continue
                    for nb in state.neighbors(n):
                        if nb in state.alive_n and nb not in isl: bnd_m.add(n); break
            fmed=float(np.median(state.F))

            nodes=[]
            for i in state.alive_n:
                if int(state.Z[i])!=3: continue
                s=1 if i in nm_s else 0; m=1 if i in nm_m else 0; w=1 if i in nm_w else 0
                nodes.append({"r_bits":f"{s}{m}{w}","boundary_mid":1 if i in bnd_m else 0,
                    "intrusion_bin":min(node_intr.get(i,0),2)})

            if nodes:
                best_J=-999; best_k=0
                for k in K_LEVELS:
                    labels=[ctx_to_label(n,k) for n in nodes]
                    counts=Counter(labels); tc=len(counts); H=shannon(list(counts.values()))
                    drift=drift_jsd(prev_nodes,nodes,k) if prev_nodes else None
                    tD=LAMBDA*drift if drift else 0
                    J=H+tD-MU*np.log2(tc+1)
                    if J>best_J: best_J=J; best_k=k
                k_star_seq.append(best_k)
            else:
                k_star_seq.append(0)

            prev_nodes=nodes
            node_intr.clear()

    # Compute stability metrics
    switches=sum(1 for i in range(1,len(k_star_seq)) if k_star_seq[i]!=k_star_seq[i-1])
    kd=Counter(k_star_seq)
    dom_k=kd.most_common(1)[0][0] if kd else 0
    # First half vs second half
    mid=len(k_star_seq)//2
    first_dom=Counter(k_star_seq[:mid]).most_common(1)[0][0] if mid>0 else 0
    second_dom=Counter(k_star_seq[mid:]).most_common(1)[0][0] if mid>0 else 0

    return {
        "seed":int(seed),"plb":plb,"rate":rate,"quiet":quiet_steps,
        "dom_k":dom_k,"k_dist":dict(kd),
        "switches":switches,"switch_rate_per100":round(switches/max(len(k_star_seq)/100,1),2),
        "first_half_dom":first_dom,"second_half_dom":second_dom,
        "stable":first_dom==second_dom,
        "n_windows":len(k_star_seq),
        "elapsed":round(time.time()-t0,1),
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--plb",type=float,default=None)
    parser.add_argument("--rate",type=float,default=None)
    parser.add_argument("--seed",type=int,default=None)
    parser.add_argument("--aggregate-only",action="store_true")
    parser.add_argument("--sanity",action="store_true")
    parser.add_argument("--quiet-steps",type=int,default=QUIET_STEPS)
    args=parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)

    if args.aggregate_only: aggregate(); return
    if args.sanity:
        print("  SANITY: plb=0.010 rate=0.002 seed=42 quiet=500")
        r=run_one(42,0.010,0.002,500)
        print(f"  dom_k={r['dom_k']} switches={r['switches']} stable={r['stable']} ({r['elapsed']:.0f}s)")
        print("  OK"); return

    qs=args.quiet_steps
    plbs=[args.plb] if args.plb else PLB_GRID
    rates=[args.rate] if args.rate is not None else RATE_GRID
    seeds=[args.seed] if args.seed else ALL_SEEDS

    for plb in plbs:
        for rate in rates:
            for seed in seeds:
                tag=f"plb{plb:.3f}_rate{rate:.4f}"
                od=OUTPUT_DIR/tag; od.mkdir(parents=True,exist_ok=True)
                rf=od/f"seed_{seed}.json"
                if rf.exists(): print(f"  {tag} s={seed}: skip"); continue
                print(f"  {tag} s={seed}...",flush=True)
                r=run_one(seed,plb,rate,qs)
                with open(rf,"w") as f: json.dump(r,f,indent=2)
                print(f"    → k*={r['dom_k']} sw={r['switches']} ({r['elapsed']:.0f}s)")

    if args.plb is None and args.rate is None and args.seed is None: aggregate()


def aggregate():
    rows=[]
    for d in sorted(OUTPUT_DIR.iterdir()):
        if not d.is_dir(): continue
        for f in sorted(d.glob("seed_*.json")):
            with open(f) as fh: rows.append(json.load(fh))
    if not rows: print("  No results."); return

    flat=[{k:(v if not isinstance(v,dict) else str(v)) for k,v in r.items()} for r in rows]
    with open(OUTPUT_DIR/"v19d_repro_summary.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=flat[0].keys()); w.writeheader(); w.writerows(flat)

    print(f"\n{'='*70}")
    print(f"  v1.9d REPRODUCIBILITY ({len(rows)} runs)")
    print(f"{'='*70}")

    # Per plb × rate
    agg=[]
    for plb in PLB_GRID:
        for rate in RATE_GRID:
            sub=[r for r in rows if abs(r["plb"]-plb)<1e-6 and abs(r["rate"]-rate)<1e-6]
            if not sub: continue
            kds=[r["dom_k"] for r in sub]
            majority=Counter(kds).most_common(1)[0]
            agree=majority[1]/len(sub)*100
            sw_rates=[r["switch_rate_per100"] for r in sub]
            stab=sum(1 for r in sub if r["stable"])
            agg.append({"plb":plb,"rate":rate,"n":len(sub),
                "majority_k":majority[0],"agree_pct":round(agree,0),
                "med_sw":round(np.median(sw_rates),2),
                "time_stable":f"{stab}/{len(sub)}"})
            print(f"  plb={plb} rate={rate}: k*={majority[0]} agree={agree:.0f}% "
                  f"sw={np.median(sw_rates):.1f}/100 stable={stab}/{len(sub)}")

    # Plots
    fig,axes=plt.subplots(2,2,figsize=(16,12))
    fig.suptitle("ESDE Genesis v1.9d — k* Reproducibility",fontsize=14,fontweight="bold")

    for pi,plb in enumerate(PLB_GRID):
        sub=[a for a in agg if abs(a["plb"]-plb)<1e-6]
        if not sub: continue
        rs=[a["rate"] for a in sub]; ks=[a["majority_k"] for a in sub]
        axes[0][0].plot(rs,ks,"o-",label=f"plb={plb}",ms=8,lw=2)
    axes[0][0].set_title("Dominant k* vs Rate (per plb)")
    axes[0][0].set_yticks(K_LEVELS); axes[0][0].legend(); axes[0][0].grid(True,alpha=0.2)

    for pi,plb in enumerate(PLB_GRID):
        sub=[a for a in agg if abs(a["plb"]-plb)<1e-6]
        if not sub: continue
        rs=[a["rate"] for a in sub]; ag=[a["agree_pct"] for a in sub]
        axes[0][1].plot(rs,ag,"s-",label=f"plb={plb}",ms=8,lw=2)
    axes[0][1].set_title("Seed Agreement (%)"); axes[0][1].legend(); axes[0][1].grid(True,alpha=0.2)
    axes[0][1].axhline(y=80,color="red",ls="--",alpha=0.5)

    for pi,plb in enumerate(PLB_GRID):
        sub=[a for a in agg if abs(a["plb"]-plb)<1e-6]
        if not sub: continue
        rs=[a["rate"] for a in sub]; sw=[a["med_sw"] for a in sub]
        axes[1][0].plot(rs,sw,"^-",label=f"plb={plb}",ms=8,lw=2)
    axes[1][0].set_title("Switch Rate (per 100 windows)"); axes[1][0].legend(); axes[1][0].grid(True,alpha=0.2)

    axes[1][1].axis("off")
    txt=["v1.9d Reproducibility","="*25,""]
    for a in agg:
        txt.append(f"plb={a['plb']} r={a['rate']}: k*={a['majority_k']} "
                   f"agree={a['agree_pct']}% sw={a['med_sw']}")
    axes[1][1].text(0.05,0.95,"\n".join(txt),transform=axes[1][1].transAxes,fontsize=9,
                    va="top",fontfamily="monospace",
                    bbox=dict(boxstyle="round",facecolor="lightyellow",edgecolor="gray",alpha=0.8))

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/"v19d_plots.png",dpi=150,bbox_inches="tight")
    print(f"\n  Plot: {OUTPUT_DIR/'v19d_plots.png'}")

    txt=f"""ESDE Genesis v1.9d — k* Reproducibility Conclusion
=====================================================
Grid: plb={PLB_GRID} × rate={RATE_GRID} × seeds={len(ALL_SEEDS)}
Quiet: {QUIET_STEPS} | Window: {WINDOW}

{'chr(10)'.join(f'plb={a["plb"]} rate={a["rate"]}: k*={a["majority_k"]} agree={a["agree_pct"]}% sw={a["med_sw"]}/100 time_stable={a["time_stable"]}' for a in agg)}

Qualitative rule holds: {'YES' if all(a['majority_k']<=2 for a in agg if a['rate']<=0.001) and all(a['majority_k']>=3 for a in agg if a['rate']>=0.002) else 'PARTIAL — check details'}
"""
    with open(OUTPUT_DIR/"v19d_conclusion.txt","w") as f: f.write(txt)


if __name__=="__main__":
    main()
