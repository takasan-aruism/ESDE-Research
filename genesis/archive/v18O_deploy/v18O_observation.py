#!/usr/bin/env python3
"""
ESDE Genesis v1.8-O — C′ Contextual Diversity Observation
============================================================
Same engine as v1.8. No physics changes.
C is relabeled by local context: resolution membership, island size, boundary exposure.

C′ = "C|r=XYZ|sz=N|bd=B" where XYZ = in_strong/mid/weak, N=size_bin, B=boundary

Usage:
  python v18O_observation.py --sanity
  python v18O_observation.py --rate 0.002 --seed 42
  python v18O_observation.py --aggregate-only

  # Parallel:
  parallel -j 20 python v18O_observation.py --rate {1} --seed {2} \
    ::: 0.0 0.0005 0.001 0.002 0.005 \
    ::: 42 123 456 789 2024 7 314 999 55 1337
  python v18O_observation.py --aggregate-only
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
STATE_NAMES={0:"Dust",1:"A",2:"B",3:"C"}
STRENGTH_BINS=[(0,0.05),(0.05,0.1),(0.1,0.2),(0.2,0.3),(0.3,1.01)]

PARAMS={"reaction_energy_threshold":0.26,"link_death_threshold":0.007,
    "background_injection_prob":0.003,"exothermic_release_amount":0.17,
    "p_link_birth":0.010,"latent_to_active_threshold":0.07,
    "latent_refresh_rate":0.003,"auto_growth_rate":0.03}
E_YIELD_SYN=0.08; E_YIELD_AUTO=0.00; TOPO_VAR=0.20
RATE_GRID=[0.0, 0.0005, 0.001, 0.002, 0.005]
ALL_SEEDS=[42,123,456,789,2024,7,314,999,55,1337]
OUTPUT_DIR=Path("outputs_v18O")


def init_fertility(state, variance, seed):
    rng=np.random.RandomState(seed+7777)
    if variance<=0: state.F=np.ones(state.n_nodes); return
    u=rng.uniform(-1,1,state.n_nodes); raw=1.0+variance*u
    raw=np.clip(raw,0.01,2.0); state.F=raw/raw.mean()


def shannon(counts):
    t=sum(counts)
    if t==0: return 0.0
    ps=[c/t for c in counts if c>0]
    return -sum(p*np.log2(p) for p in ps)


def compute_cprime_labels(state, islands_strong, islands_mid, islands_weak):
    """Compute C′ label for every C-state node. Returns dict node_id -> label string."""
    # Build node→island mappings
    def node_map(islands):
        nm={}
        for idx,isl in enumerate(islands):
            for n in isl: nm[n]=(idx,len(isl))
        return nm

    nm_s=node_map(islands_strong)
    nm_m=node_map(islands_mid)
    nm_w=node_map(islands_weak)

    # Boundary nodes at MID: nodes in mid-island with neighbor outside
    boundary_mid=set()
    for n,(iid,_) in nm_m.items():
        if n not in state.alive_n: continue
        for nb in state.neighbors(n):
            if nb in state.alive_n:
                nb_iid=nm_m.get(nb,(None,0))[0]
                if nb_iid!=iid:
                    boundary_mid.add(n); break

    # Fertility median
    fert_med=float(np.median(state.F))

    labels={}
    for i in state.alive_n:
        if int(state.Z[i])!=3: continue
        in_s=1 if i in nm_s else 0
        in_m=1 if i in nm_m else 0
        in_w=1 if i in nm_w else 0
        sz_bin=1 if (i in nm_m and nm_m[i][1]>=6) else 0
        bd=1 if i in boundary_mid else 0
        f_hi=1 if state.F[i]>=fert_med else 0

        label=f"C|r={in_s}{in_m}{in_w}|sz={sz_bin}|bd={bd}|f={f_hi}"
        labels[i]=label

    return labels


class CycleTrackerPrime:
    """Track cycles with C′ context at start and end."""
    def __init__(self):
        self.history=defaultdict(list)  # node_id -> [(step, state_int)]
        self.cprime_snapshots={}  # (node_id, step) -> C′ label

    def record(self, state, step):
        for i in state.alive_n:
            z=int(state.Z[i]); h=self.history[i]
            if not h or h[-1][1]!=z: h.append((step,z))

    def record_cprime(self, labels, step):
        """Record C′ labels for C-state nodes at this step."""
        for nid, label in labels.items():
            self.cprime_snapshots[(nid, step)]=label

    def _get_cprime(self, nid, step):
        """Get C′ label for node at step. Search nearby steps if exact not found."""
        if (nid, step) in self.cprime_snapshots:
            return self.cprime_snapshots[(nid, step)]
        # Search within ±WINDOW
        for ds in range(1, WINDOW+1):
            for s in [step-ds, step+ds]:
                if (nid, s) in self.cprime_snapshots:
                    return self.cprime_snapshots[(nid, s)]
        return "C|unknown"

    def find_cycles(self):
        cycles=[]
        for nid,h in self.history.items():
            ss=[s for _,s in h]
            for i in range(len(ss)-3):
                if ss[i]==3 and ss[i+1]==0 and ss[i+2] in(1,2):
                    for j in range(i+3,len(ss)):
                        if ss[j]==3:
                            start_step=h[i][0]; end_step=h[j][0]
                            mid="A" if ss[i+2]==1 else "B"
                            start_cp=self._get_cprime(nid, start_step)
                            end_cp=self._get_cprime(nid, end_step)
                            cycles.append({
                                "node":nid,"start":start_step,"end":end_step,
                                "mid":mid,"start_cp":start_cp,"end_cp":end_cp,
                                "sig":f"{start_cp}→{mid}→{end_cp}",
                                "drifted": start_cp!=end_cp,
                            })
                            break
        return cycles


def run_one(seed, rate, quiet_steps=QUIET_STEPS):
    p=PARAMS
    state=GenesisState(N_NODES,C_MAX,seed)
    init_fertility(state,TOPO_VAR,seed)
    physics=GenesisPhysics(PhysicsParams(exclusion_enabled=True,resonance_enabled=True,
        phase_enabled=True,beta=BETA,decay_rate_node=NODE_DECAY,K_sync=0.1,alpha=0.0,gamma=1.0))
    cp=ChemistryParams(enabled=True,E_thr=p["reaction_energy_threshold"],
        exothermic_release=p["exothermic_release_amount"],
        E_yield_syn=E_YIELD_SYN,E_yield_auto=E_YIELD_AUTO)
    chem=ChemistryEngine(cp)
    rp=RealizationParams(enabled=True,p_link_birth=p["p_link_birth"],
        latent_to_active_threshold=p["latent_to_active_threshold"],
        latent_refresh_rate=p["latent_refresh_rate"])
    realizer=RealizationOperator(rp)
    grower=AutoGrowthEngine(AutoGrowthParams(enabled=True,auto_growth_rate=p["auto_growth_rate"]))
    intruder=BoundaryIntrusionOperator(intrusion_rate=rate)
    state.EXTINCTION=p["link_death_threshold"]
    tracker=CycleTrackerPrime(); g_scores=np.zeros(N_NODES)
    t0=time.time()

    # Injection
    for step in range(INJECTION_STEPS):
        if step%INJECT_INTERVAL==0:
            tgts=physics.inject(state); chem.seed_on_injection(state,tgts or[])
        physics.step_pre_chemistry(state); chem.step(state)
        cd=physics.step_resonance(state); grower.step(state)
        physics.step_decay_exclusion(state); tracker.record(state,state.step-1)

    # Quiet
    spr_v=[]; s_hists=[]; min_l=99999
    win_cprime_metrics=[]; all_cprime_window_counts=[]

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
        intruder.step(state)
        physics.step_decay_exclusion(state); tracker.record(state,state.step-1)

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

        # C′ snapshot every WINDOW/2 steps (twice per window for cycle coverage)
        if (step+1)%(WINDOW//2)==0:
            isl_s=find_islands_sets(state,0.30)
            isl_m=find_islands_sets(state,0.20)
            isl_w=find_islands_sets(state,0.10)
            labels=compute_cprime_labels(state,isl_s,isl_m,isl_w)
            actual_step=INJECTION_STEPS+step
            tracker.record_cprime(labels,actual_step)

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

            # C′ diversity in this window
            isl_s=find_islands_sets(state,0.30)
            isl_m=find_islands_sets(state,0.20)
            isl_w=find_islands_sets(state,0.10)
            labels=compute_cprime_labels(state,isl_s,isl_m,isl_w)
            actual_step=INJECTION_STEPS+step
            tracker.record_cprime(labels,actual_step)

            cp_counts=Counter(labels.values())
            cp_type_count=len(cp_counts)
            cp_ent=shannon(list(cp_counts.values()))
            cp_top1=max(cp_counts.values())/sum(cp_counts.values()) if cp_counts else 0
            # Coexistence: >=2 types with >=5 each
            nontrivial=sum(1 for c in cp_counts.values() if c>=5)
            cp_coex=1 if nontrivial>=2 else 0

            win_cprime_metrics.append({
                "cp_types":cp_type_count,"cp_ent":round(cp_ent,4),
                "cp_top1":round(cp_top1,4),"cp_coex":cp_coex,
                "n_C":sum(cp_counts.values()),
            })
            all_cprime_window_counts.append(dict(cp_counts))

        if step%1000==999:
            print(f"      q{step+1}: L={nl:>4} cp_types={win_cprime_metrics[-1]['cp_types'] if win_cprime_metrics else 0} "
                  f"({time.time()-t0:.0f}s)",flush=True)

    # Post-run
    all_cycles=tracker.find_cycles()
    # Classic type counts
    classic_types=Counter(c["mid"] for c in all_cycles)
    # C′ signatures
    sig_counts=Counter(c["sig"] for c in all_cycles)
    n_sigs=len(sig_counts)
    sig_ent=shannon(list(sig_counts.values()))
    drift_count=sum(1 for c in all_cycles if c["drifted"])
    drift_frac=drift_count/len(all_cycles) if all_cycles else 0

    # Aggregate window C′ metrics
    mean_cp_types=np.mean([m["cp_types"] for m in win_cprime_metrics]) if win_cprime_metrics else 0
    mean_cp_ent=np.mean([m["cp_ent"] for m in win_cprime_metrics]) if win_cprime_metrics else 0
    mean_cp_coex=np.mean([m["cp_coex"] for m in win_cprime_metrics]) if win_cprime_metrics else 0

    # X
    spr=np.mean(spr_v) if spr_v else 0
    if s_hists:
        mh=np.mean(s_hists,axis=0); t=mh.sum()
        if t>0: pp=mh/t; pp=pp[pp>0]; C_sc=1-(-np.sum(pp*np.log2(pp)))/np.log2(5)
        else: C_sc=0
    else: C_sc=0
    X=round(C_sc+spr,4)

    elapsed=time.time()-t0
    return {
        "seed":int(seed),"rate":rate,
        "cycles":len(all_cycles),
        "cycles_per_1k":round(len(all_cycles)/(quiet_steps/1000),3),
        "classic_types":len(classic_types),
        "cprime_sig_count":n_sigs,
        "cprime_sig_entropy":round(sig_ent,4),
        "drift_fraction":round(drift_frac,4),
        "drift_count":drift_count,
        "mean_cp_types":round(mean_cp_types,2),
        "mean_cp_entropy":round(mean_cp_ent,4),
        "mean_cp_coexistence":round(mean_cp_coex,4),
        "spr":round(spr,4),"X":X,
        "min_links":min_l if min_l<99999 else 0,
        "elapsed":round(elapsed,1),
        "top_sigs":dict(sig_counts.most_common(10)),
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
        print("  SANITY: rate=0.002 seed=42, 500 quiet")
        r=run_one(42,0.002,500)
        print(f"  cyc={r['cycles']} sigs={r['cprime_sig_count']} "
              f"drift={r['drift_fraction']:.3f} cp_types={r['mean_cp_types']:.1f}")
        if r["top_sigs"]:
            print(f"  Top sigs: {list(r['top_sigs'].items())[:5]}")
        print("  OK")
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
            with open(rf,"w") as f: json.dump(r,f,indent=2)
            print(f"    → cyc={r['cycles']} sigs={r['cprime_sig_count']} "
                  f"drift={r['drift_fraction']:.3f} ({r['elapsed']:.0f}s)")

    if args.rate is None and args.seed is None: aggregate()


def aggregate():
    rows=[]
    for d in sorted(OUTPUT_DIR.iterdir()):
        if not d.is_dir(): continue
        for f in sorted(d.glob("seed_*.json")):
            with open(f) as fh: rows.append(json.load(fh))
    if not rows: print("  No results."); return

    flat=[{k:v for k,v in r.items() if k!="top_sigs"} for r in rows]
    with open(OUTPUT_DIR/"v18O_summary.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=flat[0].keys()); w.writeheader(); w.writerows(flat)

    agg=[]
    for rate in RATE_GRID:
        sub=[r for r in rows if abs(r["rate"]-rate)<1e-6]
        if not sub: continue
        agg.append({
            "rate":rate,"n":len(sub),
            "med_cyc":round(np.median([r["cycles_per_1k"] for r in sub]),2),
            "med_sigs":round(np.median([r["cprime_sig_count"] for r in sub]),1),
            "med_sig_ent":round(np.median([r["cprime_sig_entropy"] for r in sub]),4),
            "med_drift":round(np.median([r["drift_fraction"] for r in sub]),4),
            "med_cp_types":round(np.median([r["mean_cp_types"] for r in sub]),2),
            "med_cp_ent":round(np.median([r["mean_cp_entropy"] for r in sub]),4),
            "med_cp_coex":round(np.median([r["mean_cp_coexistence"] for r in sub]),4),
            "med_X":round(np.median([r["X"] for r in sub]),4),
            "min_links":min(r["min_links"] for r in sub),
        })

    with open(OUTPUT_DIR/"v18O_aggregate.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=agg[0].keys()); w.writeheader(); w.writerows(agg)

    # Collect all signatures
    all_sigs=Counter()
    for r in rows:
        for s,c in r.get("top_sigs",{}).items(): all_sigs[s]+=c

    print(f"\n{'='*70}")
    print(f"  v1.8-O C′ OBSERVATION RESULTS ({len(rows)} runs)")
    print(f"{'='*70}")
    print(f"\n  {'rate':>7} {'cyc':>6} {'sigs':>5} {'H_sig':>6} {'drift':>6} "
          f"{'cp_t':>5} {'cp_H':>6} {'cp_coex':>7} {'X':>6}")
    for a in agg:
        print(f"  {a['rate']:>7.4f} {a['med_cyc']:>6.1f} {a['med_sigs']:>5.1f} "
              f"{a['med_sig_ent']:>6.3f} {a['med_drift']:>6.3f} "
              f"{a['med_cp_types']:>5.2f} {a['med_cp_ent']:>6.3f} "
              f"{a['med_cp_coex']:>7.3f} {a['med_X']:>6.4f}")

    print(f"\n  Global C′-cycle signatures: {len(all_sigs)}")
    for s,c in all_sigs.most_common(15):
        print(f"    {s}: {c}")

    # Plots
    fig,axes=plt.subplots(2,3,figsize=(20,12))
    fig.suptitle("ESDE Genesis v1.8-O — C′ Contextual Diversity",fontsize=14,fontweight="bold")
    rs=[a["rate"] for a in agg]

    def pl(ax,key,title,c="#2ecc71",hline=None):
        ax.plot(rs,[a[key] for a in agg],"o-",color=c,ms=8,lw=2)
        if hline: ax.axhline(y=hline,color="red",ls="--",alpha=0.5)
        ax.set_title(title); ax.set_xlabel("intrusion_rate"); ax.grid(True,alpha=0.2)

    pl(axes[0][0],"med_cp_types","C′ Types per Window","#2ecc71",hline=3)
    pl(axes[0][1],"med_cp_ent","C′ Entropy per Window","#9b59b6")
    pl(axes[0][2],"med_sigs","Unique C′-Cycle Signatures","#e67e22")
    pl(axes[1][0],"med_sig_ent","C′-Cycle Signature Entropy","#3498db")
    pl(axes[1][1],"med_drift","Context Drift Fraction","#e74c3c")
    pl(axes[1][2],"med_cyc","Cycles/1k (reference)","gray")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/"v18O_plots.png",dpi=150,bbox_inches="tight")
    print(f"\n  Plot: {OUTPUT_DIR/'v18O_plots.png'}")

    achieved=any(a["med_cp_types"]>=3 for a in agg)
    has_drift=any(a["med_drift"]>0 for a in agg)
    best=max(agg,key=lambda a:a["med_sig_ent"])

    txt=f"""ESDE Genesis v1.8-O — C′ Observation Conclusion
=================================================
Sweep: intrusion_rate={RATE_GRID}
Seeds: {len(ALL_SEEDS)} | Quiet: {QUIET_STEPS}

C′ type_count ≥ 3?  {'YES' if achieved else 'NO'}
Context drift occurs?  {'YES' if has_drift else 'NO'}

Best signature diversity: rate={best['rate']}
  C′ signatures={best['med_sigs']}  entropy={best['med_sig_ent']}
  drift fraction={best['med_drift']}
  C′ types/window={best['med_cp_types']}  C′ entropy={best['med_cp_ent']}

Global unique signatures: {len(all_sigs)}
Top signatures:
{chr(10).join(f'  {s}: {c}' for s,c in all_sigs.most_common(10))}

Interpretation:
- C′ types ≥ 3 means multiple structural contexts for C coexist
- drift > 0 means nodes change C′ category across cycles (context evolution)
- signature diversity > 2 means the system generates functionally distinct cycle paths
  even with only 2 chemical elements (A/B)
"""
    with open(OUTPUT_DIR/"v18O_conclusion.txt","w") as f: f.write(txt)
    print(txt)


if __name__=="__main__":
    main()
