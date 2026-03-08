"""
ESDE Genesis v1.3 — Ridge Refinement
=======================================
Is the ridge a point or a band?
Fine grid: plb={0.006..0.010} × bg={0.001,0.003,0.007}
+ sanity refs at plb=0.004 (conservative) and plb=0.012 (degraded)
Same code as v1.2. No logic changes.
"""

import numpy as np
import matplotlib.pyplot as plt
import csv, time
from collections import Counter, defaultdict

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger
from chemistry import ChemistryEngine, ChemistryParams
from realization import RealizationOperator, RealizationParams
from autogrowth import AutoGrowthEngine, AutoGrowthParams

N_NODES=200; C_MAX=1.0; INJECTION_STEPS=300; INJECT_INTERVAL=3
BETA=1.0; NODE_DECAY=0.005; BIAS=0.7
STRENGTH_BINS=[(0,0.05),(0.05,0.1),(0.1,0.2),(0.2,0.3),(0.3,1.01)]
BASE={"reaction_energy_threshold":0.26,"link_death_threshold":0.007,
    "background_injection_prob":0.003,"exothermic_release_amount":0.17,
    "p_link_birth":0.007,"latent_to_active_threshold":0.07,
    "latent_refresh_rate":0.003,"auto_growth_rate":0.03}

SEEDS=[42,789,2024]
QUIET=400

# Fine grid + sanity refs
P_GRID=[0.004, 0.006,0.007,0.008,0.010, 0.012]
BG_GRID=[0.001,0.003,0.007]


class CT:
    def __init__(self): self.h=defaultdict(list)
    def rec(self,state,step):
        for i in state.alive_n:
            z=int(state.Z[i]); h=self.h[i]
            if not h or h[-1][1]!=z: h.append((step,z))
    def count(self):
        n=0
        for nid,h in self.h.items():
            ss=[s for _,s in h]
            for i in range(len(ss)-3):
                if ss[i]==3 and ss[i+1]==0 and ss[i+2] in(1,2):
                    for j in range(i+3,len(ss)):
                        if ss[j]==3: n+=1; break
        return n


def run_one(seed,plb,bgi):
    p=dict(BASE); p["p_link_birth"]=plb; p["background_injection_prob"]=bgi
    state=GenesisState(N_NODES,C_MAX,seed)
    physics=GenesisPhysics(PhysicsParams(exclusion_enabled=True,resonance_enabled=True,
        phase_enabled=True,beta=BETA,decay_rate_node=NODE_DECAY,K_sync=0.1,alpha=0.0,gamma=1.0))
    cp=ChemistryParams(enabled=True,E_thr=p["reaction_energy_threshold"],
        exothermic_release=p["exothermic_release_amount"])
    chem=ChemistryEngine(cp)
    rp=RealizationParams(enabled=True,p_link_birth=plb,
        latent_to_active_threshold=p["latent_to_active_threshold"],
        latent_refresh_rate=p["latent_refresh_rate"])
    realizer=RealizationOperator(rp)
    grower=AutoGrowthEngine(AutoGrowthParams(enabled=True,auto_growth_rate=p["auto_growth_rate"]))
    state.EXTINCTION=p["link_death_threshold"]
    tracker=CT(); g_scores=np.zeros(N_NODES)

    for step in range(INJECTION_STEPS):
        if step%INJECT_INTERVAL==0:
            tgts=physics.inject(state); chem.seed_on_injection(state,tgts or[])
        physics.step_pre_chemistry(state); chem.step(state)
        cd=physics.step_resonance(state); grower.step(state)
        physics.step_decay_exclusion(state); tracker.rec(state,state.step-1)

    tot_opp=0;tot_nm=0;miss=Counter();spr_v=[];s_hists=[];min_l=9999
    for step in range(QUIET):
        realizer.step(state); physics.step_pre_chemistry(state)
        rxns=chem.step(state); cd=physics.step_resonance(state)
        g_scores[:]=0; grower.step(state)
        for k in state.alive_l:
            r=state.R.get(k,0.0)
            if r>0:
                a=min(grower.params.auto_growth_rate*r,max(state.get_latent(k[0],k[1]),0))
                if a>0: g_scores[k[0]]+=a; g_scores[k[1]]+=a
        gz=float(g_scores.sum())
        physics.step_decay_exclusion(state); tracker.rec(state,state.step-1)

        al=list(state.alive_n); na=len(al)
        if na>0:
            aa=np.array(al)
            if BIAS>0 and gz>0:
                ga=g_scores[aa]; gs=ga.sum()
                if gs>0: pg=ga/gs; pd=(1-BIAS)*(np.ones(na)/na)+BIAS*pg; pd/=pd.sum()
                else: pd=np.ones(na)/na
            else: pd=np.ones(na)/na
            mk=state.rng.random(na)<bgi
            for idx in range(na):
                if mk[idx]:
                    t=int(state.rng.choice(aa,p=pd))
                    state.E[t]=min(1.0,state.E[t]+0.3)
                    if state.Z[t]==0 and state.rng.random()<0.5:
                        state.Z[t]=1 if state.rng.random()<0.5 else 2

        if step%50==49:
            nl=len(state.alive_l); min_l=min(min_l,nl)
            ss=[state.S[k] for k in state.alive_l]
            ll=sum(1 for k in state.alive_l if state.R.get(k,0)>0)
            spr_v.append(ll/max(nl,1))
            h=[0]*5
            for s in ss:
                for bi,(lo,hi) in enumerate(STRENGTH_BINS):
                    if lo<=s<hi: h[bi]+=1; break
            s_hists.append(h)
            for k in state.alive_l:
                i,j=k; s=state.S[k]
                cs=s>=0.3; ce=state.E[i]>=cp.E_thr and state.E[j]>=cp.E_thr
                ct=int(state.Z[i])in(1,2)or int(state.Z[j])in(1,2)
                cy=np.cos(state.theta[j]-state.theta[i])>=0.7
                nm=sum([cs,ce,ct,cy])
                if nm==4: tot_opp+=1
                elif nm==3:
                    tot_nm+=1
                    if not cs:miss["strong"]+=1
                    if not ce:miss["energy"]+=1
                    if not ct:miss["state"]+=1
                    if not cy:miss["sync"]+=1

    cyc=tracker.count(); ts=INJECTION_STEPS+QUIET
    s03=sum(1 for k in state.alive_l if state.S[k]>=0.3)
    mx_s=max((state.S[k] for k in state.alive_l),default=0)
    if s_hists:
        mh=np.mean(s_hists,axis=0); t=mh.sum()
        if t>0: pp=mh/t; pp=pp[pp>0]; H=-np.sum(pp*np.log2(pp)); C=1-H/np.log2(5)
        else: C=0;H=0
    else: C=0;H=0
    spr=np.mean(spr_v) if spr_v else 0
    sep_n=set();sep_ab=0
    for k in state.alive_l:
        if state.S[k]>=0.3:
            sep_n.add(k[0]);sep_n.add(k[1])
            if int(state.Z[k[0]])in(1,2):sep_ab+=1
            if int(state.Z[k[1]])in(1,2):sep_ab+=1
    cov=sep_ab/(max(len(sep_n)*2,1)) if sep_n else 0
    X=round(C+spr+0.01*cyc/(ts/1000),4)
    return {"cycles":cyc,"cyc_rate":round(cyc/(ts/1000),3),
        "opp_rate":round(tot_opp/max(QUIET/50,1),3),
        "min_links":min_l if min_l<9999 else 0,
        "s03":s03,"max_s":round(mx_s,4),"spr":round(spr,4),
        "compress":round(C,4),"X":X,
        "strong_cov":round(cov,4),
        "miss_strong":round(miss.get("strong",0)/max(tot_nm,1),3),
        "miss_energy":round(miss.get("energy",0)/max(tot_nm,1),3),
        "miss_state":round(miss.get("state",0)/max(tot_nm,1),3),
        "miss_sync":round(miss.get("sync",0)/max(tot_nm,1),3)}


def main():
    print("="*70)
    print("  ESDE Genesis v1.3 — Ridge Refinement")
    print(f"  plb={P_GRID} × bg={BG_GRID}")
    print(f"  {len(SEEDS)} seeds × {QUIET} quiet steps")
    print("="*70)

    # Baselines
    print("\n  Computing baselines...")
    bl={}
    for s in SEEDS:
        r=run_one(s,BASE["p_link_birth"],BASE["background_injection_prob"])
        bl[s]=r; print(f"    s={s}: X={r['X']:.4f} cyc={r['cycles']}")

    rows=[]; t0=time.time()
    for plb in P_GRID:
        for bgi in BG_GRID:
            seed_res=[]
            for seed in SEEDS:
                r=run_one(seed,plb,bgi)
                xb=bl[seed]["X"]; eta=r["X"]/xb if xb>0.01 else 0
                col=r["min_links"]==0 or eta<0.6
                row={"plb":plb,"bgi":bgi,"seed":seed,
                    "cyc_rate":r["cyc_rate"],"opp_rate":r["opp_rate"],
                    "eta":round(eta,4),"X":r["X"],
                    "compress":r["compress"],"spr":r["spr"],
                    "min_links":r["min_links"],"s03":r["s03"],"max_s":r["max_s"],
                    "strong_cov":r["strong_cov"],
                    "miss_strong":r["miss_strong"],"miss_energy":r["miss_energy"],
                    "miss_state":r["miss_state"],"miss_sync":r["miss_sync"],
                    "collapse":col}
                rows.append(row); seed_res.append(row)
            me=np.median([r["eta"] for r in seed_res])
            mc=np.median([r["cyc_rate"] for r in seed_res])
            nc=sum(1 for r in seed_res if r["collapse"])
            tag="C" if me<0.6 or nc>=3 else "D" if me<0.8 else "S"
            is_ridge="*" if plb in [0.006,0.007,0.008,0.009,0.010] else " "
            print(f" {is_ridge}plb={plb:.3f} bg={bgi:.3f}: "
                  f"η={me:.3f} cyc={mc:.2f} [{tag}] "
                  f"({time.time()-t0:.0f}s)")

    with open("ridge_refine_summary.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

    # Aggregate
    agg=[]
    for plb in P_GRID:
        for bgi in BG_GRID:
            sub=[r for r in rows if r["plb"]==plb and r["bgi"]==bgi]
            agg.append({
                "plb":plb,"bgi":bgi,
                "med_cyc":round(np.median([r["cyc_rate"] for r in sub]),3),
                "mean_cyc":round(np.mean([r["cyc_rate"] for r in sub]),3),
                "med_eta":round(np.median([r["eta"] for r in sub]),3),
                "med_X":round(np.median([r["X"] for r in sub]),4),
                "med_cov":round(np.median([r["strong_cov"] for r in sub]),4),
                "pct_col":round(sum(1 for r in sub if r["collapse"])/len(sub)*100,0),
                "min_links_worst":min(r["min_links"] for r in sub),
                "seeds_cyc":sum(1 for r in sub if r["cyc_rate"]>0),
            })
    with open("ridge_refine_aggregate.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=agg[0].keys()); w.writeheader(); w.writerows(agg)

    # Print results table
    print(f"\n{'='*70}")
    print(f"  AGGREGATE")
    print(f"{'='*70}")
    print(f"  {'plb':>6} {'bg':>6} {'cyc':>6} {'η':>6} {'X':>6} "
          f"{'col%':>5} {'minL':>5} {'s/cyc':>5}")
    for a in agg:
        print(f"  {a['plb']:>6.3f} {a['bgi']:>6.3f} {a['med_cyc']:>6.2f} "
              f"{a['med_eta']:>6.3f} {a['med_X']:>6.4f} "
              f"{a['pct_col']:>5.0f} {a['min_links_worst']:>5} "
              f"{a['seeds_cyc']:>5}/{len(SEEDS)}")

    # Identify band
    stable_cyc=[a for a in agg if a["med_eta"]>=0.8 and a["pct_col"]==0 and a["med_cyc"]>0]
    stable_all=[a for a in agg if a["med_eta"]>=0.8 and a["pct_col"]==0]

    # Heatmaps
    fig,axes=plt.subplots(2,2,figsize=(18,14))
    fig.suptitle("ESDE Genesis v1.3 — Ridge Refinement\np_link_birth × bg_inject (fine grid)",
                 fontsize=14,fontweight="bold",y=0.99)

    def hm(ax,key,title,cmap="viridis",vmin=None,vmax=None):
        grid=np.zeros((len(P_GRID),len(BG_GRID)))
        for a in agg:
            pi=P_GRID.index(a["plb"]); bi=BG_GRID.index(a["bgi"])
            grid[pi,bi]=a[key]
        im=ax.imshow(grid,aspect="auto",origin="lower",cmap=cmap,vmin=vmin,vmax=vmax)
        ax.set_xticks(range(len(BG_GRID)))
        ax.set_xticklabels([f"{v:.3f}" for v in BG_GRID],fontsize=9)
        ax.set_yticks(range(len(P_GRID)))
        ax.set_yticklabels([f"{v:.3f}" for v in P_GRID],fontsize=9)
        ax.set_xlabel("bg_inject"); ax.set_ylabel("p_link_birth")
        ax.set_title(title,fontsize=10)
        for i in range(len(P_GRID)):
            for j in range(len(BG_GRID)):
                ax.text(j,i,f"{grid[i,j]:.2f}",ha="center",va="center",fontsize=9,
                        color="white" if grid[i,j]<(vmax or grid.max())*0.5 else "black")
        plt.colorbar(im,ax=ax,shrink=0.8)

    hm(axes[0][0],"med_cyc","Median Cycles/1k","YlOrRd")
    hm(axes[0][1],"med_eta","Median η","RdYlGn",0.4,1.3)
    hm(axes[1][0],"med_X","Median X","plasma")

    # Seeds with cycles heatmap
    grid_sc=np.zeros((len(P_GRID),len(BG_GRID)))
    for a in agg:
        pi=P_GRID.index(a["plb"]); bi=BG_GRID.index(a["bgi"])
        grid_sc[pi,bi]=a["seeds_cyc"]
    ax=axes[1][1]
    im=ax.imshow(grid_sc,aspect="auto",origin="lower",cmap="Greens",vmin=0,vmax=len(SEEDS))
    ax.set_xticks(range(len(BG_GRID)))
    ax.set_xticklabels([f"{v:.3f}" for v in BG_GRID],fontsize=9)
    ax.set_yticks(range(len(P_GRID)))
    ax.set_yticklabels([f"{v:.3f}" for v in P_GRID],fontsize=9)
    ax.set_xlabel("bg_inject"); ax.set_ylabel("p_link_birth")
    ax.set_title(f"Seeds with Cycles (/{len(SEEDS)})",fontsize=10)
    for i in range(len(P_GRID)):
        for j in range(len(BG_GRID)):
            ax.text(j,i,f"{int(grid_sc[i,j])}",ha="center",va="center",fontsize=12,fontweight="bold")
    plt.colorbar(im,ax=ax,shrink=0.8)

    plt.tight_layout(rect=[0,0,1,0.96])
    plt.savefig("heatmap_refine.png",dpi=150,bbox_inches="tight")
    print(f"\n  Plot: heatmap_refine.png")

    # Conclusion
    if stable_cyc:
        band_plbs=sorted(set(a["plb"] for a in stable_cyc))
        best=max(stable_cyc,key=lambda a:a["med_cyc"])
        band_str=f"plb ∈ [{min(band_plbs)}, {max(band_plbs)}]"
    else:
        band_plbs=[]
        best=max(agg,key=lambda a:a["med_cyc"]) if agg else None
        band_str="No stable cycling band found"

    txt=f"""ESDE Genesis v1.3 — Ridge Refinement Conclusion
=================================================
Grid: plb={P_GRID} × bg={BG_GRID}
Seeds: {len(SEEDS)} per point | Quiet: {QUIET} steps

Ridge Analysis:
  Stable cycling cells (η≥0.8, col=0%, cyc>0): {len(stable_cyc)}
  Stable non-cycling cells: {len(stable_all)-len(stable_cyc)}

{'Band: ' + band_str if band_plbs else band_str}
{'Best point: plb='+str(best['plb'])+' bg='+str(best['bgi'])+' cyc='+str(best['med_cyc'])+' η='+str(best['med_eta']) if best else ''}

Ridge character: {'BAND (stable over multiple plb values)' if len(band_plbs)>=2 else 'POINT (single plb value)' if len(band_plbs)==1 else 'NONE'}

Stable cycling region:
{chr(10).join(f"  plb={a['plb']} bg={a['bgi']}: cyc={a['med_cyc']} η={a['med_eta']} seeds_cyc={a['seeds_cyc']}/{len(SEEDS)}" for a in stable_cyc) if stable_cyc else '  None'}

All stable region (η≥0.8, col=0%):
{chr(10).join(f"  plb={a['plb']} bg={a['bgi']}: cyc={a['med_cyc']} η={a['med_eta']}" for a in stable_all)}

Recommended defaults:
  p_link_birth: {f'[{min(band_plbs)}, {max(band_plbs)}]' if band_plbs else 'needs longer runs'}
  bg_inject: [0.001, 0.007] (all values stable)
"""
    with open("v13_ridge_refine_conclusion.txt","w") as f: f.write(txt)
    print(txt)
    print(f"  Total elapsed: {time.time()-t0:.0f}s")


if __name__=="__main__":
    main()
