#!/usr/bin/env python3
"""
ESDE Genesis v1.8-O2 — Raw Feature Logging for Variable-Resolution C′
========================================================================
Logs raw context features so that k=0..K C′ labels can be computed post-hoc.
No engine changes. Observation/logging expansion only.

Raw context per C-node: (r_bits, boundary_mid, size_mid_bin, fert_bin, intrusion_bin)
Stored as aggregate counts per window + per-cycle context pairs.

Usage:
  python v18O2_rawlog.py --sanity
  python v18O2_rawlog.py --rate 0.002 --seed 42
  parallel -j 20 python v18O2_rawlog.py --rate {1} --seed {2} \
    ::: 0.0 0.0005 0.001 0.002 0.005 \
    ::: 42 123 456 789 2024 7 314 999 55 1337
  python v18O2_rawlog.py --aggregate-only
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
OUTPUT_DIR=Path("outputs_v18O2")

# r_bits categories
R_BITS_KEYS=["000","001","010","011","100","101","110","111"]


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


def compute_raw_context(state, isl_s, isl_m, isl_w, node_intrusion_counts):
    """Compute raw context tuple for every alive node. Returns dict node_id -> tuple."""
    def nm(islands):
        m={}
        for idx,isl in enumerate(islands):
            for n in isl: m[n]=(idx,len(isl))
        return m

    nm_s=nm(isl_s); nm_m=nm(isl_m); nm_w=nm(isl_w)

    # Boundary at MID
    boundary_mid=set()
    for n,(iid,_) in nm_m.items():
        if n not in state.alive_n: continue
        for nb in state.neighbors(n):
            if nb in state.alive_n and nm_m.get(nb,(None,0))[0]!=iid:
                boundary_mid.add(n); break

    fert_med=float(np.median(state.F))

    contexts={}
    for i in state.alive_n:
        in_s=1 if i in nm_s else 0
        in_m=1 if i in nm_m else 0
        in_w=1 if i in nm_w else 0
        r_bits=f"{in_s}{in_m}{in_w}"
        bd=1 if i in boundary_mid else 0
        sz=1 if (i in nm_m and nm_m[i][1]>=6) else 0
        f_hi=1 if state.F[i]>=fert_med else 0
        intr_raw=node_intrusion_counts.get(i,0)
        intr_bin=0 if intr_raw==0 else (1 if intr_raw==1 else 2)

        contexts[i]={
            "r_bits":r_bits, "boundary_mid":bd, "size_mid_bin":sz,
            "fert_bin":f_hi, "intrusion_bin":intr_bin,
        }
    return contexts


def context_to_tuple(ctx):
    """Convert context dict to hashable tuple string for cycle tracking."""
    return json.dumps(ctx, sort_keys=True)


class CycleTrackerRaw:
    """Track cycles with raw context at start and end."""
    def __init__(self):
        self.history=defaultdict(list)
        self.context_snapshots={}  # (node_id, step) -> context dict

    def record(self, state, step):
        for i in state.alive_n:
            z=int(state.Z[i]); h=self.history[i]
            if not h or h[-1][1]!=z: h.append((step,z))

    def record_contexts(self, contexts, step):
        for nid, ctx in contexts.items():
            self.context_snapshots[(nid, step)]=ctx

    def _get_ctx(self, nid, step):
        if (nid,step) in self.context_snapshots:
            return self.context_snapshots[(nid,step)]
        for ds in range(1,WINDOW+1):
            for s in [step-ds, step+ds]:
                if (nid,s) in self.context_snapshots:
                    return self.context_snapshots[(nid,s)]
        return None

    def find_cycles(self):
        cycles=[]
        for nid,h in self.history.items():
            ss=[s for _,s in h]
            for i in range(len(ss)-3):
                if ss[i]==3 and ss[i+1]==0 and ss[i+2] in(1,2):
                    for j in range(i+3,len(ss)):
                        if ss[j]==3:
                            start_ctx=self._get_ctx(nid, h[i][0])
                            end_ctx=self._get_ctx(nid, h[j][0])
                            mid="A" if ss[i+2]==1 else "B"
                            cycles.append({
                                "node":nid,"start":h[i][0],"end":h[j][0],
                                "mid":mid,
                                "start_ctx":start_ctx,
                                "end_ctx":end_ctx,
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
    tracker=CycleTrackerRaw(); g_scores=np.zeros(N_NODES)
    t0=time.time()

    # Per-node intrusion exposure (reset per window)
    node_intrusion_window=Counter()

    # Injection
    for step in range(INJECTION_STEPS):
        if step%INJECT_INTERVAL==0:
            tgts=physics.inject(state); chem.seed_on_injection(state,tgts or[])
        physics.step_pre_chemistry(state); chem.step(state)
        cd=physics.step_resonance(state); grower.step(state)
        physics.step_decay_exclusion(state); tracker.record(state,state.step-1)

    # Quiet
    window_features=[]; min_l=99999; spr_v=[]; s_hists=[]
    win_id=0

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

        # Intrusion + track which nodes were affected
        pre_S={k:state.S[k] for k in state.alive_l}
        intruder.step(state)
        # Detect nodes whose link strengths changed
        for k in state.alive_l:
            if k in pre_S and abs(state.S[k]-pre_S[k])>0.001:
                node_intrusion_window[k[0]]+=1
                node_intrusion_window[k[1]]+=1

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

        # Context snapshot every WINDOW/2
        if (step+1)%(WINDOW//2)==0:
            isl_s=find_islands_sets(state,0.30)
            isl_m=find_islands_sets(state,0.20)
            isl_w=find_islands_sets(state,0.10)
            ctxs=compute_raw_context(state,isl_s,isl_m,isl_w,node_intrusion_window)
            tracker.record_contexts(ctxs, INJECTION_STEPS+step)

        # Window boundary
        if (step+1)%WINDOW==0:
            win_id+=1
            nl=len(state.alive_l); min_l=min(min_l,nl)
            ss_vals=[state.S[k] for k in state.alive_l]
            ll=sum(1 for k in state.alive_l if state.R.get(k,0)>0)
            spr_v.append(ll/max(nl,1))
            h=[0]*5
            for s in ss_vals:
                for bi,(lo,hi) in enumerate(STRENGTH_BINS):
                    if lo<=s<hi: h[bi]+=1; break
            s_hists.append(h)

            # Compute full context for all C nodes
            isl_s=find_islands_sets(state,0.30)
            isl_m=find_islands_sets(state,0.20)
            isl_w=find_islands_sets(state,0.10)
            ctxs=compute_raw_context(state,isl_s,isl_m,isl_w,node_intrusion_window)
            tracker.record_contexts(ctxs, INJECTION_STEPS+step)

            # Aggregate raw features for C-nodes only
            c_ctxs=[ctxs[i] for i in ctxs if int(state.Z[i])==3]
            r_counts=Counter(c["r_bits"] for c in c_ctxs)
            bd_counts=Counter(c["boundary_mid"] for c in c_ctxs)
            sz_counts=Counter(c["size_mid_bin"] for c in c_ctxs)
            f_counts=Counter(c["fert_bin"] for c in c_ctxs)
            intr_counts=Counter(c["intrusion_bin"] for c in c_ctxs)

            row={"seed":seed,"window":win_id,"rate":rate,"n_C":len(c_ctxs)}
            for rb in R_BITS_KEYS: row[f"r_{rb}"]=r_counts.get(rb,0)
            row["bd_0"]=bd_counts.get(0,0); row["bd_1"]=bd_counts.get(1,0)
            row["sz_0"]=sz_counts.get(0,0); row["sz_1"]=sz_counts.get(1,0)
            row["f_0"]=f_counts.get(0,0); row["f_1"]=f_counts.get(1,0)
            row["intr_0"]=intr_counts.get(0,0)
            row["intr_1"]=intr_counts.get(1,0)
            row["intr_2p"]=intr_counts.get(2,0)

            # Quick C′ diversity (full resolution)
            full_labels=Counter(context_to_tuple(c) for c in c_ctxs)
            row["cp_full_types"]=len(full_labels)
            row["cp_full_entropy"]=round(shannon(list(full_labels.values())),4)

            window_features.append(row)
            node_intrusion_window.clear()

            if win_id%5==0:
                print(f"      W{win_id}: n_C={len(c_ctxs)} cp_types={len(full_labels)} "
                      f"({time.time()-t0:.0f}s)",flush=True)

    # Post-run: cycle context pairs
    all_cycles=tracker.find_cycles()
    cycle_pairs=[]
    for c in all_cycles:
        sc=c["start_ctx"]; ec=c["end_ctx"]
        if sc is None: sc={"r_bits":"???","boundary_mid":0,"size_mid_bin":0,"fert_bin":0,"intrusion_bin":0}
        if ec is None: ec={"r_bits":"???","boundary_mid":0,"size_mid_bin":0,"fert_bin":0,"intrusion_bin":0}
        cycle_pairs.append({
            "seed":seed,"rate":rate,
            "start_ctx":json.dumps(sc,sort_keys=True),
            "end_ctx":json.dumps(ec,sort_keys=True),
            "mid":c["mid"],
            "drifted":sc!=ec,
        })

    # Aggregate
    spr=np.mean(spr_v) if spr_v else 0
    if s_hists:
        mh=np.mean(s_hists,axis=0); t=mh.sum()
        if t>0: pp=mh/t; pp=pp[pp>0]; C_sc=1-(-np.sum(pp*np.log2(pp)))/np.log2(5)
        else: C_sc=0
    else: C_sc=0
    X=round(C_sc+spr,4)

    n_drift=sum(1 for cp in cycle_pairs if cp["drifted"])
    unique_sigs=len(set((cp["start_ctx"],cp["mid"],cp["end_ctx"]) for cp in cycle_pairs))

    elapsed=time.time()-t0
    summary={
        "seed":int(seed),"rate":rate,
        "cycles":len(all_cycles),
        "cycles_per_1k":round(len(all_cycles)/(quiet_steps/1000),3),
        "unique_sigs":unique_sigs,
        "drift_count":n_drift,
        "drift_frac":round(n_drift/max(len(all_cycles),1),4),
        "mean_cp_types":round(np.mean([w["cp_full_types"] for w in window_features]),2) if window_features else 0,
        "mean_cp_entropy":round(np.mean([w["cp_full_entropy"] for w in window_features]),4) if window_features else 0,
        "X":X,"spr":round(spr,4),
        "min_links":min_l if min_l<99999 else 0,
        "elapsed":round(elapsed,1),
    }

    return summary, window_features, cycle_pairs


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
        s,wf,cp=run_one(42,0.002,500)
        print(f"  cyc={s['cycles']} sigs={s['unique_sigs']} "
              f"drift={s['drift_frac']:.3f} cp_types={s['mean_cp_types']:.1f}")
        print(f"  window features: {len(wf)} rows, cols={list(wf[0].keys())[:8]}...")
        print(f"  cycle pairs: {len(cp)}")
        print("  OK")
        return

    qs=args.quiet_steps
    rates=[args.rate] if args.rate is not None else RATE_GRID
    seeds=[args.seed] if args.seed else ALL_SEEDS

    for rate in rates:
        for seed in seeds:
            tag=f"rate{rate:.4f}"
            out_dir=OUTPUT_DIR/tag; out_dir.mkdir(parents=True,exist_ok=True)
            sf=out_dir/f"seed_{seed}_summary.json"
            if sf.exists(): print(f"  {tag} s={seed}: skip"); continue
            print(f"  {tag} s={seed}...",flush=True)

            summ,wf,cp=run_one(seed,rate,qs)

            with open(sf,"w") as f: json.dump(summ,f,indent=2)

            # Window features
            wf_path=out_dir/f"seed_{seed}_window_raw.csv"
            if wf:
                with open(wf_path,"w",newline="") as f:
                    w=csv.DictWriter(f,fieldnames=wf[0].keys()); w.writeheader(); w.writerows(wf)

            # Cycle context pairs
            cp_path=out_dir/f"seed_{seed}_cycle_pairs.csv"
            if cp:
                with open(cp_path,"w",newline="") as f:
                    w=csv.DictWriter(f,fieldnames=cp[0].keys()); w.writeheader(); w.writerows(cp)

            print(f"    → cyc={summ['cycles']} sigs={summ['unique_sigs']} "
                  f"drift={summ['drift_frac']:.3f} ({summ['elapsed']:.0f}s)")

    if args.rate is None and args.seed is None: aggregate()


def aggregate():
    summaries=[]
    all_wf=[]; all_cp=[]
    for d in sorted(OUTPUT_DIR.iterdir()):
        if not d.is_dir(): continue
        for f in sorted(d.glob("*_summary.json")):
            with open(f) as fh: summaries.append(json.load(fh))
        for f in sorted(d.glob("*_window_raw.csv")):
            with open(f) as fh:
                for row in csv.DictReader(fh): all_wf.append(row)
        for f in sorted(d.glob("*_cycle_pairs.csv")):
            with open(f) as fh:
                for row in csv.DictReader(fh): all_cp.append(row)

    if not summaries: print("  No results."); return

    # Save merged files
    if all_wf:
        with open(OUTPUT_DIR/"v18O2_window_raw_features.csv","w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=all_wf[0].keys()); w.writeheader(); w.writerows(all_wf)
        print(f"  Window features: {len(all_wf)} rows")

    if all_cp:
        with open(OUTPUT_DIR/"v18O2_cycle_context_pairs.csv","w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=all_cp[0].keys()); w.writeheader(); w.writerows(all_cp)
        print(f"  Cycle pairs: {len(all_cp)} rows")

    # Per-rate aggregate
    agg=[]
    for rate in RATE_GRID:
        sub=[s for s in summaries if abs(s["rate"]-rate)<1e-6]
        if not sub: continue
        agg.append({
            "rate":rate,"n":len(sub),
            "med_cyc":round(np.median([s["cycles_per_1k"] for s in sub]),2),
            "med_sigs":round(np.median([s["unique_sigs"] for s in sub]),1),
            "med_drift":round(np.median([s["drift_frac"] for s in sub]),4),
            "med_cp_types":round(np.median([s["mean_cp_types"] for s in sub]),2),
            "med_cp_ent":round(np.median([s["mean_cp_entropy"] for s in sub]),4),
            "med_X":round(np.median([s["X"] for s in sub]),4),
            "min_links":min(s["min_links"] for s in sub),
        })

    with open(OUTPUT_DIR/"v18O2_aggregate.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=agg[0].keys()); w.writeheader(); w.writerows(agg)

    print(f"\n{'='*70}")
    print(f"  v1.8-O2 RAW FEATURE RESULTS ({len(summaries)} runs)")
    print(f"{'='*70}")
    print(f"\n  {'rate':>7} {'cyc':>6} {'sigs':>5} {'drift':>6} {'cp_t':>5} {'cp_H':>6} {'X':>6}")
    for a in agg:
        print(f"  {a['rate']:>7.4f} {a['med_cyc']:>6.1f} {a['med_sigs']:>5.1f} "
              f"{a['med_drift']:>6.3f} {a['med_cp_types']:>5.2f} "
              f"{a['med_cp_ent']:>6.3f} {a['med_X']:>6.4f}")

    # Check raw feature coverage
    feature_cols=[c for c in all_wf[0].keys() if c.startswith("r_") or c.startswith("bd_")
                  or c.startswith("sz_") or c.startswith("f_") or c.startswith("intr_")]

    txt=f"""ESDE Genesis v1.8-O2 — Raw Feature Logging Conclusion
=======================================================
Runs: {len(summaries)} | Window features: {len(all_wf)} rows | Cycle pairs: {len(all_cp)} rows

Raw feature columns collected:
  {', '.join(feature_cols)}

Coverage:
  r_bits (8 categories): {'OK' if any(c.startswith('r_') for c in feature_cols) else 'MISSING'}
  boundary_mid (2 bins): {'OK' if 'bd_0' in feature_cols else 'MISSING'}
  size_mid_bin (2 bins): {'OK' if 'sz_0' in feature_cols else 'MISSING'}
  fert_bin (2 bins): {'OK' if 'f_0' in feature_cols else 'MISSING'}
  intrusion_bin (3 bins): {'OK' if 'intr_0' in feature_cols else 'MISSING'}

Cycle context pairs format:
  start_ctx and end_ctx stored as JSON strings (full raw tuple)
  Post-hoc k-selection: parse JSON, select subset of keys, hash → C′(k) label

Per-rate summary:
{chr(10).join(f'  rate={a["rate"]}: sigs={a["med_sigs"]:.0f} drift={a["med_drift"]:.3f} cp_types={a["med_cp_types"]:.1f}' for a in agg)}
"""
    with open(OUTPUT_DIR/"v18O2_conclusion.txt","w") as f: f.write(txt)
    print(txt)


if __name__=="__main__":
    main()
