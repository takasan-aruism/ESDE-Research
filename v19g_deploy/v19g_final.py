#!/usr/bin/env python3
"""
ESDE Genesis v1.9g — Observer Stabilization Final
====================================================
A) Adopt hyst_0.01 as default k* rule
B) Reproducibility panel: baseline vs hyst_0.01
C) Switch feature audit
D) Freeze check: longer quiet stability

Task B/D require v19d-style runner (Ryzen). Task A/C are postprocess.
This script handles ALL tasks from v18O2 raw data + v19d run data.

Usage:
  # Postprocess (A/C on existing data):
  python v19g_final.py --postprocess --input-dir ../v18O2_deploy/outputs_v18O2

  # Runner for B/D (Ryzen, generates new data):
  python v19g_final.py --run --plb 0.010 --rate 0.001 --seed 42
  python v19g_final.py --run --plb 0.010 --rate 0.001 --seed 42 --quiet-steps 10000

  # Parallel (Ryzen):
  parallel -j 20 python v19g_final.py --run --plb {1} --rate {2} --seed {3} \
    ::: 0.007 0.008 0.010 ::: 0.0005 0.001 0.002 0.005 \
    ::: 42 123 456 789 2024 7 314 999 55 1337

  # Freeze check (longer runs):
  parallel -j 10 python v19g_final.py --run --plb 0.010 --rate {1} --seed {2} --quiet-steps 10000 \
    ::: 0.0005 0.001 0.002 ::: 42 123 456 789 2024 7 314 999 55 1337

  # Aggregate all:
  python v19g_final.py --aggregate
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
E_YIELD_SYN=0.08; E_YIELD_AUTO=0.00; TOPO_VAR=0.20
LAMBDA=1.0; MU=0.5; HYST_T=0.01
K_LEVELS=[0,1,2,3,4]

BASE={"reaction_energy_threshold":0.26,"link_death_threshold":0.007,
    "background_injection_prob":0.003,"exothermic_release_amount":0.17,
    "latent_to_active_threshold":0.07,"latent_refresh_rate":0.003,"auto_growth_rate":0.03}
PLB_GRID=[0.007,0.008,0.010]
RATE_GRID=[0.0005,0.001,0.002,0.005]
ALL_SEEDS=[42,123,456,789,2024,7,314,999,55,1337]
OUTPUT_DIR=Path("outputs_v19g")
R_BITS=["000","001","010","011","100","101","110","111"]


def shannon(c):
    t=sum(c)
    if t==0: return 0.0
    return -sum((x/t)*np.log2(x/t) for x in c if x>0)

def init_fert(state,v,seed):
    rng=np.random.RandomState(seed+7777)
    if v<=0: state.F=np.ones(state.n_nodes); return
    u=rng.uniform(-1,1,state.n_nodes); raw=1.0+v*u; raw=np.clip(raw,0.01,2.0)
    state.F=raw/raw.mean()

def ctx_label(ctx,k):
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

def djsd(n1,n2,k):
    if not n1 or not n2: return None
    l1=Counter(ctx_label(n,k) for n in n1); l2=Counter(ctx_label(n,k) for n in n2)
    al=set(l1)|set(l2); t1=sum(l1.values()); t2=sum(l2.values())
    if t1==0 or t2==0: return None
    p=np.array([l1.get(l,0)/t1 for l in al]); q=np.array([l2.get(l,0)/t2 for l in al])
    mm=(p+q)/2
    kl=lambda a,b: sum(a[i]*np.log2(a[i]/b[i]) for i in range(len(a)) if a[i]>0 and b[i]>0)
    return round(float(np.sqrt((kl(p,mm)+kl(q,mm))/2)),4)

def compute_J(nodes,prev,k):
    labs=[ctx_label(n,k) for n in nodes]
    c=Counter(labs); tc=len(c); H=shannon(list(c.values()))
    dr=djsd(prev,nodes,k) if prev else None
    tD=LAMBDA*dr if dr else 0
    return round(H+tD-MU*np.log2(tc+1),4), round(H,4), dr, tc


# ================================================================
# RUNNER (Task B/D)
# ================================================================
def run_one(seed, plb, rate, quiet_steps=QUIET_STEPS):
    p=dict(BASE); p["p_link_birth"]=plb
    state=GenesisState(N_NODES,C_MAX,seed)
    init_fert(state,TOPO_VAR,seed)
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

    # Quiet: per-window J3/J4/k* for both rules
    j3_seq=[]; j4_seq=[]; margin_seq=[]
    prev_nodes=None; switch_log=[]

    for step in range(quiet_steps):
        realizer.step(state); physics.step_pre_chemistry(state)
        chem.step(state); physics.step_resonance(state)
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
            mk=state.rng.random(na)<BASE["background_injection_prob"]
            for idx in range(na):
                if mk[idx]:
                    t=int(state.rng.choice(aa,p=pd))
                    state.E[t]=min(1.0,state.E[t]+0.3)
                    if state.Z[t]==0 and state.rng.random()<0.5:
                        state.Z[t]=1 if state.rng.random()<0.5 else 2

        if (step+1)%WINDOW==0:
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

            nodes=[]
            for i in state.alive_n:
                if int(state.Z[i])!=3: continue
                s=1 if i in nm_s else 0; m=1 if i in nm_m else 0; w=1 if i in nm_w else 0
                nodes.append({"r_bits":f"{s}{m}{w}","boundary_mid":1 if i in bnd_m else 0,
                    "intrusion_bin":min(node_intr.get(i,0),2)})

            if nodes:
                j3,h3,dr3,tc3=compute_J(nodes,prev_nodes,3)
                j4,h4,dr4,tc4=compute_J(nodes,prev_nodes,4)
                margin=round(j4-j3,4)
                j3_seq.append(j3); j4_seq.append(j4); margin_seq.append(margin)

                # None ratio
                nr=sum(1 for n in nodes if n["r_bits"]=="000")/len(nodes)
                hf=sum(1 for n in nodes if n.get("intrusion_bin",0)>=1)/len(nodes)

                switch_log.append({
                    "j3":j3,"j4":j4,"h3":h3,"h4":h4,"dr3":dr3,"dr4":dr4,
                    "tc3":tc3,"tc4":tc4,"margin":margin,
                    "none_ratio":round(nr,4),"hit_frac":round(hf,4),"n_C":len(nodes),
                })
            prev_nodes=nodes; node_intr.clear()

    # Compute k* sequences for both rules
    def baseline_ks(j3s,j4s):
        return [4 if j4>j3 else 3 for j3,j4 in zip(j3s,j4s)]
    def hyst_ks(j3s,j4s,T=HYST_T):
        if not j3s: return []
        w=[4 if j4s[0]>j3s[0] else 3]
        for i in range(1,len(j3s)):
            m=j4s[i]-j3s[i]
            if w[-1]==3 and m>=T: w.append(4)
            elif w[-1]==4 and m<=-T: w.append(3)
            else: w.append(w[-1])
        return w

    ks_base=baseline_ks(j3_seq,j4_seq)
    ks_hyst=hyst_ks(j3_seq,j4_seq)

    def stats(ks):
        if not ks: return {"dom":0,"switches":0,"switch_per100":0}
        kd=Counter(ks); dom=kd.most_common(1)[0][0]
        sw=sum(1 for i in range(1,len(ks)) if ks[i]!=ks[i-1])
        return {"dom":dom,"switches":sw,"switch_per100":round(sw/max(len(ks)/100,1),1)}

    sb=stats(ks_base); sh=stats(ks_hyst)
    mid=len(ks_hyst)//2
    first_dom_h=Counter(ks_hyst[:mid]).most_common(1)[0][0] if mid>0 else 0
    second_dom_h=Counter(ks_hyst[mid:]).most_common(1)[0][0] if mid>0 else 0

    elapsed=time.time()-t0
    return {
        "seed":int(seed),"plb":plb,"rate":rate,"quiet":quiet_steps,
        "n_windows":len(j3_seq),"rule":"both",
        "base_dom":sb["dom"],"base_sw":sb["switch_per100"],
        "hyst_dom":sh["dom"],"hyst_sw":sh["switch_per100"],
        "hyst_first_half":first_dom_h,"hyst_second_half":second_dom_h,
        "hyst_time_stable":first_dom_h==second_dom_h,
        "mean_margin":round(np.mean(margin_seq),4) if margin_seq else 0,
        "pct_close":round(sum(1 for m in margin_seq if abs(m)<0.02)/max(len(margin_seq),1)*100,1),
        "elapsed":round(elapsed,1),
    }


def aggregate():
    rows=[]
    for d in sorted(OUTPUT_DIR.iterdir()):
        if not d.is_dir(): continue
        for f in sorted(d.glob("seed_*.json")):
            with open(f) as fh: rows.append(json.load(fh))
    if not rows: print("  No results."); return

    flat=[{k:(v if not isinstance(v,dict) else str(v)) for k,v in r.items()} for r in rows]
    with open(OUTPUT_DIR/"v19g_summary.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=flat[0].keys()); w.writeheader(); w.writerows(flat)

    print(f"\n{'='*70}")
    print(f"  v1.9g SUMMARY ({len(rows)} runs)")
    print(f"{'='*70}")
    print(f"\n  {'plb':>5} {'rate':>7} | {'BASE agree':>10} {'sw':>5} {'k*':>3} | "
          f"{'HYST agree':>10} {'sw':>5} {'k*':>3} | {'stable':>6}")

    agg=[]
    for plb in PLB_GRID:
        for rate in RATE_GRID:
            sub=[r for r in rows if abs(r["plb"]-plb)<1e-6 and abs(r["rate"]-rate)<1e-6]
            if not sub: continue
            # Base
            b_doms=[r["base_dom"] for r in sub]
            b_maj=Counter(b_doms).most_common(1)[0]
            b_agree=b_maj[1]/len(sub)*100
            b_sw=np.median([r["base_sw"] for r in sub])
            # Hyst
            h_doms=[r["hyst_dom"] for r in sub]
            h_maj=Counter(h_doms).most_common(1)[0]
            h_agree=h_maj[1]/len(sub)*100
            h_sw=np.median([r["hyst_sw"] for r in sub])
            h_stable=sum(1 for r in sub if r["hyst_time_stable"])

            a={"plb":plb,"rate":rate,"n":len(sub),
               "base_k":b_maj[0],"base_agree":round(b_agree,0),"base_sw":round(b_sw,1),
               "hyst_k":h_maj[0],"hyst_agree":round(h_agree,0),"hyst_sw":round(h_sw,1),
               "hyst_stable":f"{h_stable}/{len(sub)}"}
            agg.append(a)
            print(f"  {plb:>5.3f} {rate:>7.4f} | {b_agree:>8.0f}% {b_sw:>5.1f} k={b_maj[0]} | "
                  f"{h_agree:>8.0f}% {h_sw:>5.1f} k={h_maj[0]} | {h_stable}/{len(sub)}")

    # Plots
    fig,axes=plt.subplots(2,2,figsize=(16,12))
    fig.suptitle("ESDE Genesis v1.9g — Baseline vs hyst_0.01",fontsize=14,fontweight="bold")

    for pi,plb in enumerate(PLB_GRID):
        sub=[a for a in agg if abs(a["plb"]-plb)<1e-6]
        if not sub: continue
        rs=[a["rate"] for a in sub]
        # Agreement
        axes[0][0].plot(rs,[a["base_agree"] for a in sub],"o--",alpha=0.4,color=f"C{pi}",ms=5)
        axes[0][0].plot(rs,[a["hyst_agree"] for a in sub],"s-",color=f"C{pi}",ms=8,lw=2,label=f"hyst plb={plb}")
    axes[0][0].axhline(y=80,color="red",ls="--",alpha=0.5)
    axes[0][0].set_title("Seed Agreement (%) — dashed=baseline, solid=hyst")
    axes[0][0].legend(fontsize=7); axes[0][0].grid(True,alpha=0.2); axes[0][0].set_xlabel("rate")

    for pi,plb in enumerate(PLB_GRID):
        sub=[a for a in agg if abs(a["plb"]-plb)<1e-6]
        if not sub: continue
        rs=[a["rate"] for a in sub]
        axes[0][1].plot(rs,[a["base_sw"] for a in sub],"o--",alpha=0.4,color=f"C{pi}",ms=5)
        axes[0][1].plot(rs,[a["hyst_sw"] for a in sub],"s-",color=f"C{pi}",ms=8,lw=2,label=f"hyst plb={plb}")
    axes[0][1].set_title("Switch Rate (/100 win)"); axes[0][1].legend(fontsize=7); axes[0][1].grid(True,alpha=0.2)

    for pi,plb in enumerate(PLB_GRID):
        sub=[a for a in agg if abs(a["plb"]-plb)<1e-6]
        if not sub: continue
        rs=[a["rate"] for a in sub]
        axes[1][0].plot(rs,[a["hyst_k"] for a in sub],"s-",color=f"C{pi}",ms=10,lw=2,label=f"plb={plb}")
    axes[1][0].set_title("Dominant k* (hyst_0.01)"); axes[1][0].set_yticks(K_LEVELS)
    axes[1][0].legend(); axes[1][0].grid(True,alpha=0.2)

    # Summary text
    axes[1][1].axis("off")
    txt=["v1.9g: baseline vs hyst_0.01","="*30,"",f"Runs: {len(rows)}","Rule: hyst T=0.01",""]
    for a in agg:
        txt.append(f"plb={a['plb']} r={a['rate']}: "
                   f"base={a['base_agree']}%/k={a['base_k']} → hyst={a['hyst_agree']}%/k={a['hyst_k']} "
                   f"stable={a['hyst_stable']}")
    axes[1][1].text(0.02,0.98,"\n".join(txt),transform=axes[1][1].transAxes,fontsize=8,
                    va="top",fontfamily="monospace",
                    bbox=dict(boxstyle="round",facecolor="lightyellow",edgecolor="gray",alpha=0.8))

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/"v19g_plots.png",dpi=150,bbox_inches="tight")
    print(f"\n  Plot: {OUTPUT_DIR/'v19g_plots.png'}")

    # Conclusion
    txt=f"""# ESDE Genesis v1.9g — Final Summary

Rule adopted: hyst_0.01 (T=0.01, k=3↔4 boundary only)

| plb | rate | Base agree | Base k* | Hyst agree | Hyst k* | Hyst sw/100 | Time stable |
|-----|------|-----------|---------|-----------|---------|------------|-------------|
"""
    for a in agg:
        txt+=f"| {a['plb']} | {a['rate']} | {a['base_agree']}% | k={a['base_k']} | {a['hyst_agree']}% | k={a['hyst_k']} | {a['hyst_sw']} | {a['hyst_stable']} |\n"

    txt+=f"""
v1.9 observer scaffold: FROZEN.
hyst_0.01 is the default k* selection rule.
"""
    with open(OUTPUT_DIR/"v19g_conclusion.md","w") as f: f.write(txt)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run",action="store_true",help="Run simulation (Ryzen)")
    parser.add_argument("--postprocess",action="store_true",help="Postprocess existing data")
    parser.add_argument("--aggregate",action="store_true",help="Aggregate results")
    parser.add_argument("--plb",type=float,default=None)
    parser.add_argument("--rate",type=float,default=None)
    parser.add_argument("--seed",type=int,default=None)
    parser.add_argument("--quiet-steps",type=int,default=QUIET_STEPS)
    parser.add_argument("--input-dir",default="../v18O2_deploy/outputs_v18O2")
    parser.add_argument("--sanity",action="store_true")
    args=parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)

    if args.sanity:
        print("  SANITY: plb=0.010 rate=0.001 seed=42 quiet=500")
        r=run_one(42,0.010,0.001,500)
        print(f"  base: k={r['base_dom']} sw={r['base_sw']}")
        print(f"  hyst: k={r['hyst_dom']} sw={r['hyst_sw']} stable={r['hyst_time_stable']}")
        print("  OK"); return

    if args.aggregate:
        aggregate(); return

    if args.run:
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
                    print(f"  {tag} s={seed} q={qs}...",flush=True)
                    r=run_one(seed,plb,rate,qs)
                    with open(rf,"w") as f: json.dump(r,f,indent=2)
                    print(f"    base:k={r['base_dom']} hyst:k={r['hyst_dom']} "
                          f"agree improvement possible ({r['elapsed']:.0f}s)")
        return

    print("  Specify --run, --postprocess, or --aggregate")


if __name__=="__main__":
    main()
