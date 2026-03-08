#!/usr/bin/env python3
"""
ESDE Genesis v1.9e — Follow-up Observations
=============================================
A) Island scale refinement (D1 vs D2 detector, strong_ratio binning)
B) Competitive band deep-dive (rate≈0.001 switch analysis)
C) Reproducibility/stability check

Postprocess on v18O2 raw features. No physics changes.

Usage:
  python v19e_observations.py --input-dir ../v18O2_deploy/outputs_v18O2
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import csv, json, argparse
from collections import Counter, defaultdict
from pathlib import Path

LAMBDA=1.0; MU=0.5; K_LEVELS=[0,1,2,3,4]
R_BITS_KEYS=["000","001","010","011","100","101","110","111"]
OUTPUT_DIR=Path("outputs_v19e")
RATE_FOCUS=[0.0005,0.001,0.002]
RATE_ALL=[0.0,0.0005,0.001,0.002,0.005]


def shannon(c):
    t=sum(c)
    if t==0: return 0.0
    return -sum((x/t)*np.log2(x/t) for x in c if x>0)


def reconstruct_nodes(row):
    nodes=[]
    for rb in R_BITS_KEYS:
        n=int(row.get(f"r_{rb}",0))
        for _ in range(n): nodes.append({"r_bits":rb})
    if not nodes: return nodes
    bd1=int(row.get("bd_1",0)); sz1=int(row.get("sz_1",0))
    f1=int(row.get("f_1",0))
    i1=int(row.get("intr_1",0)); i2=int(row.get("intr_2p",0))
    for i,nd in enumerate(nodes):
        nd["boundary_mid"]=1 if i<bd1 else 0
        nd["size_mid_bin"]=1 if i<sz1 else 0
        nd["fert_bin"]=1 if i<f1 else 0
        nd["intrusion_bin"]=2 if i<i2 else (1 if i<i2+i1 else 0)
    return nodes


# ================================================================
# DETECTOR D1: Current (r_bits based)
# ================================================================
def label_D1(ctx, k):
    if k==0: return "C"
    rb=ctx.get("r_bits","000")
    s=int(rb[0]); m=int(rb[1]) if len(rb)>=2 else 0; w=int(rb[2]) if len(rb)>=3 else 0
    res="High" if s else ("Mid" if m else "Low")
    if k==1: return f"C_{res}"
    bd="Edge" if ctx.get("boundary_mid",0)==1 else "Core"
    if k==2: return f"C_{res}_{bd}"
    if s: scale="Strong"
    elif m: scale="Mid"
    elif w: scale="WeakOnly"
    else: scale="None"
    if k==3: return f"C_{res}_{bd}_{scale}"
    ie="1p" if ctx.get("intrusion_bin",0)>=1 else "0"
    return f"C_{res}_{bd}_{scale}_{ie}"


# ================================================================
# DETECTOR D2: strong_ratio based
# ================================================================
def label_D2(ctx, k):
    """D2: island defined by weak membership, classified by strong_ratio."""
    if k==0: return "C"
    rb=ctx.get("r_bits","000")
    s=int(rb[0]); m=int(rb[1]) if len(rb)>=2 else 0; w=int(rb[2]) if len(rb)>=3 else 0
    res="High" if s else ("Mid" if m else "Low")
    if k==1: return f"C_{res}"
    bd="Edge" if ctx.get("boundary_mid",0)==1 else "Core"
    if k==2: return f"C_{res}_{bd}"
    # D2: island membership from weak graph, classify by strong presence
    in_any = s or m or w
    if not in_any:
        scale="None"
    elif s==0 and m==0:  # weak only, no strong edges
        scale="WeakOnly"
    elif s==1:  # strong island presence → strong_ratio likely >= 0.20
        scale="Strong"
    else:  # mid but not strong → 0 < strong_ratio < 0.20
        scale="Mid"
    if k==3: return f"C_{res}_{bd}_{scale}"
    ie="1p" if ctx.get("intrusion_bin",0)>=1 else "0"
    return f"C_{res}_{bd}_{scale}_{ie}"


def drift_jsd(n1, n2, k, labeler):
    if not n1 or not n2: return None
    l1=Counter(labeler(n,k) for n in n1); l2=Counter(labeler(n,k) for n in n2)
    al=set(l1)|set(l2); t1=sum(l1.values()); t2=sum(l2.values())
    if t1==0 or t2==0: return None
    p=np.array([l1.get(l,0)/t1 for l in al]); q=np.array([l2.get(l,0)/t2 for l in al])
    m_=(p+q)/2
    kl=lambda a,b: sum(a[i]*np.log2(a[i]/b[i]) for i in range(len(a)) if a[i]>0 and b[i]>0)
    return round(float(np.sqrt((kl(p,m_)+kl(q,m_))/2)),4)


def compute_metrics(nodes, prev, k, labeler):
    labels=[labeler(n,k) for n in nodes]
    counts=Counter(labels); tc=len(counts); H=shannon(list(counts.values()))
    drift=drift_jsd(prev,nodes,k,labeler) if prev else None
    tD=LAMBDA*drift if drift else 0
    J=H+tD-MU*np.log2(tc+1)
    return {"tc":tc,"H":round(H,4),"drift":drift,"J":round(J,4)}


def get_scale_dist(nodes, labeler):
    """Get island scale distribution for C nodes."""
    sc=Counter()
    for n in nodes:
        lab=labeler(n,3)  # k=3 label
        for s in ["None","WeakOnly","Mid","Strong"]:
            if s in lab: sc[s]+=1; break
    return sc


def load_data(d):
    wd=defaultdict(list)
    for sd in sorted(d.iterdir()):
        if not sd.is_dir(): continue
        for f in sorted(sd.glob("*_window_raw.csv")):
            with open(f) as fh:
                for r in csv.DictReader(fh): wd[(float(r["rate"]),int(r["seed"]))].append(r)
    return wd


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input-dir",default="../v18O2_deploy/outputs_v18O2")
    args=parser.parse_args()
    inp=Path(args.input_dir); OUTPUT_DIR.mkdir(parents=True,exist_ok=True)

    print(f"  Loading from {inp}...")
    wd=load_data(inp)
    print(f"  Loaded: {len(wd)} runs, {sum(len(v) for v in wd.values())} windows")

    # ================================================================
    # Process all windows with both detectors
    # ================================================================
    all_metrics=[]; switch_events=[]; k3_quality=[]

    for (rate,seed),windows in sorted(wd.items()):
        prev_D1=None; prev_D2=None
        prev_k_D1=None
        for wi,row in enumerate(windows):
            nodes=reconstruct_nodes(row)
            if not nodes:
                prev_D1=None; prev_D2=None; prev_k_D1=None; continue

            nt=len(nodes)
            # Compute for both detectors
            m_D1={k:compute_metrics(nodes,prev_D1,k,label_D1) for k in K_LEVELS}
            m_D2={k:compute_metrics(nodes,prev_D2,k,label_D2) for k in K_LEVELS}
            ks_D1=max(K_LEVELS,key=lambda k:m_D1[k]["J"])
            ks_D2=max(K_LEVELS,key=lambda k:m_D2[k]["J"])

            # Scale distributions
            sc_D1=get_scale_dist(nodes,label_D1)
            sc_D2=get_scale_dist(nodes,label_D2)

            none_r=sc_D1.get("None",0)/max(nt,1)
            mid_r=(sc_D1.get("Mid",0))/max(nt,1)
            strong_r=sc_D1.get("Strong",0)/max(nt,1)
            weak_r=sc_D1.get("WeakOnly",0)/max(nt,1)

            row_out={
                "seed":seed,"rate":rate,"window":wi+1,"n_C":nt,
                "k_star_D1":ks_D1,"k_star_D2":ks_D2,
                "J3_D1":m_D1[3]["J"],"J3_D2":m_D2[3]["J"],
                "J4_D1":m_D1[4]["J"],"J4_D2":m_D2[4]["J"],
                "H3_D1":m_D1[3]["H"],"H3_D2":m_D2[3]["H"],
                "H2_D1":m_D1[2]["H"],
                "dH32_D1":round(m_D1[3]["H"]-m_D1[2]["H"],4),
                "dH32_D2":round(m_D2[3]["H"]-m_D2[2]["H"],4),
                "dJ34_D1":round(m_D1[4]["J"]-m_D1[3]["J"],4),
                "none_ratio":round(none_r,4),
                "mid_share":round(mid_r,4),
                "strong_share":round(strong_r,4),
                "weak_share":round(weak_r,4),
                "none_D2":sc_D2.get("None",0),
                "weak_D2":sc_D2.get("WeakOnly",0),
                "mid_D2":sc_D2.get("Mid",0),
                "strong_D2":sc_D2.get("Strong",0),
            }
            all_metrics.append(row_out)

            # Task B: Switch events (D1)
            if prev_k_D1 is not None and ks_D1!=prev_k_D1:
                # Compute intrusion split drift
                hit_n=[n for n in nodes if n.get("intrusion_bin",0)>=1]
                nohit_n=[n for n in nodes if n.get("intrusion_bin",0)==0]
                frac_hit=len(hit_n)/max(nt,1)

                switch_events.append({
                    "seed":seed,"rate":rate,"window":wi+1,
                    "from_k":prev_k_D1,"to_k":ks_D1,
                    "dJ34":row_out["dJ34_D1"],
                    "dH34":round(m_D1[4]["H"]-m_D1[3]["H"],4),
                    "none_ratio":row_out["none_ratio"],
                    "mid_share":row_out["mid_share"],
                    "strong_share":row_out["strong_share"],
                    "frac_hit":round(frac_hit,4),
                })

            # Task A/C: k=3 quality (D1)
            if ks_D1==3:
                k3_quality.append({
                    "seed":seed,"rate":rate,"window":wi+1,
                    "J3":m_D1[3]["J"],"H3":m_D1[3]["H"],
                    "none_ratio":row_out["none_ratio"],
                    "mid_share":row_out["mid_share"],
                    "strong_share":row_out["strong_share"],
                    "weak_share":row_out["weak_share"],
                    "n_C":nt,
                })

            prev_D1=nodes; prev_D2=nodes; prev_k_D1=ks_D1

    # ================================================================
    # Save CSVs
    # ================================================================
    with open(OUTPUT_DIR/"k_metrics_per_window.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=all_metrics[0].keys()); w.writeheader(); w.writerows(all_metrics)

    if switch_events:
        with open(OUTPUT_DIR/"switch_events.csv","w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=switch_events[0].keys()); w.writeheader(); w.writerows(switch_events)

    if k3_quality:
        with open(OUTPUT_DIR/"k3_wins_quality_v19e.csv","w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=k3_quality[0].keys()); w.writeheader(); w.writerows(k3_quality)

    # ================================================================
    # ANALYSIS
    # ================================================================
    print(f"\n{'='*60}")
    print(f"  TASK A: Island Scale Refinement (D1 vs D2)")
    print(f"{'='*60}")

    for det,kcol in [("D1","k_star_D1"),("D2","k_star_D2")]:
        kd=Counter(r[kcol] for r in all_metrics)
        print(f"\n  {det} k* distribution:")
        for k in K_LEVELS:
            print(f"    k={k}: {kd.get(k,0)} ({kd.get(k,0)/max(len(all_metrics),1)*100:.1f}%)")

    # D1 vs D2 per rate
    print(f"\n  Per-rate dominant k*:")
    for rate in RATE_ALL:
        sub=[r for r in all_metrics if abs(r["rate"]-rate)<1e-6]
        if not sub: continue
        d1=Counter(r["k_star_D1"] for r in sub).most_common(1)[0]
        d2=Counter(r["k_star_D2"] for r in sub).most_common(1)[0]
        dH_D1=np.mean([r["dH32_D1"] for r in sub])
        dH_D2=np.mean([r["dH32_D2"] for r in sub])
        print(f"    rate={rate}: D1→k*={d1[0]}({d1[1]}) D2→k*={d2[0]}({d2[1]}) "
              f"ΔH32: D1={dH_D1:.4f} D2={dH_D2:.4f}")

    # k=3 quality
    print(f"\n  k=3 Quality (D1):")
    if k3_quality:
        nr=[r["none_ratio"] for r in k3_quality]
        ms=[r["mid_share"]+r["strong_share"] for r in k3_quality]
        j3=[r["J3"] for r in k3_quality]
        corr=np.corrcoef(nr,j3)[0,1] if len(nr)>5 and np.std(nr)>0 and np.std(j3)>0 else 0
        print(f"    Windows: {len(k3_quality)}")
        print(f"    None ratio: mean={np.mean(nr):.3f} med={np.median(nr):.3f}")
        print(f"    Mid+Strong: mean={np.mean(ms):.3f}")
        print(f"    Corr(J3, none_ratio): {corr:.3f}")
        print(f"    Winning empty (None>95%): {'YES ⚠' if np.median(nr)>0.95 else 'NO ✓'}")

    print(f"\n{'='*60}")
    print(f"  TASK B: Competitive Band (Switch Events)")
    print(f"{'='*60}")

    if switch_events:
        # Split by direction
        sw_34=[r for r in switch_events if r["from_k"]==3 and r["to_k"]==4]
        sw_43=[r for r in switch_events if r["from_k"]==4 and r["to_k"]==3]
        print(f"  3→4 switches: {len(sw_34)}")
        print(f"  4→3 switches: {len(sw_43)}")

        for label,sub in [("3→4",sw_34),("4→3",sw_43)]:
            if not sub: continue
            print(f"\n  Direction {label}:")
            print(f"    ΔJ34: mean={np.mean([r['dJ34'] for r in sub]):.4f} "
                  f"med={np.median([r['dJ34'] for r in sub]):.4f}")
            print(f"    none_ratio: mean={np.mean([r['none_ratio'] for r in sub]):.3f}")
            print(f"    mid+strong: mean={np.mean([r['mid_share']+r['strong_share'] for r in sub]):.3f}")
            print(f"    frac_hit: mean={np.mean([r['frac_hit'] for r in sub]):.3f}")

    print(f"\n{'='*60}")
    print(f"  TASK C: Reproducibility Check")
    print(f"{'='*60}")

    for rate in RATE_FOCUS:
        sub_seeds=defaultdict(list)
        for r in all_metrics:
            if abs(r["rate"]-rate)<1e-6:
                sub_seeds[r["seed"]].append(r["k_star_D1"])
        if not sub_seeds: continue
        dom_per_seed=[Counter(v).most_common(1)[0][0] for v in sub_seeds.values()]
        majority=Counter(dom_per_seed).most_common(1)[0]
        agree=majority[1]/len(dom_per_seed)*100

        # Switch rate per seed
        sw_rates=[]
        for s,ks_list in sub_seeds.items():
            sw=sum(1 for i in range(1,len(ks_list)) if ks_list[i]!=ks_list[i-1])
            sw_rates.append(sw/max(len(ks_list)/100,1))

        # k=3 quality subset
        k3_sub=[r for r in k3_quality if abs(r["rate"]-rate)<1e-6]
        nr_sub=[r["none_ratio"] for r in k3_sub] if k3_sub else [0]

        print(f"  rate={rate}: k*={majority[0]} agree={agree:.0f}% "
              f"sw/100={np.median(sw_rates):.1f} "
              f"k3_none_med={np.median(nr_sub):.3f} "
              f"{'✓' if agree>=80 and np.median(nr_sub)<0.95 and np.median(sw_rates)<20 else '⚠'}")

    # ================================================================
    # PLOTS
    # ================================================================
    fig,axes=plt.subplots(2,3,figsize=(20,12))
    fig.suptitle("ESDE Genesis v1.9e — Follow-up Observations",fontsize=14,fontweight="bold")

    # A) ΔH(k3-k2) D1 vs D2
    ax=axes[0][0]
    d1_dh=[r["dH32_D1"] for r in all_metrics]
    d2_dh=[r["dH32_D2"] for r in all_metrics]
    ax.hist(d1_dh,bins=30,alpha=0.6,label="D1",color="#3498db")
    ax.hist(d2_dh,bins=30,alpha=0.6,label="D2",color="#e74c3c")
    ax.axvline(x=0.05,color="green",ls=":",label="target 0.05")
    ax.set_title("ΔH(k3−k2): D1 vs D2"); ax.legend(); ax.grid(True,alpha=0.2)

    # B) ΔJ34 by switch direction
    ax=axes[0][1]
    if switch_events:
        sw_34=[r["dJ34"] for r in switch_events if r["from_k"]==3 and r["to_k"]==4]
        sw_43=[r["dJ34"] for r in switch_events if r["from_k"]==4 and r["to_k"]==3]
        if sw_34: ax.hist(sw_34,bins=25,alpha=0.6,label="3→4",color="#e74c3c")
        if sw_43: ax.hist(sw_43,bins=25,alpha=0.6,label="4→3",color="#2ecc71")
    ax.axvline(x=0,color="black",ls="--")
    ax.set_title("ΔJ₃₄ by Switch Direction"); ax.legend(); ax.grid(True,alpha=0.2)

    # C) J3 vs None ratio with regression
    ax=axes[0][2]
    if k3_quality:
        nr=[r["none_ratio"] for r in k3_quality]; j3=[r["J3"] for r in k3_quality]
        ax.scatter(nr,j3,alpha=0.3,s=15,color="#3498db")
        if len(nr)>2:
            z=np.polyfit(nr,j3,1); p=np.poly1d(z)
            xs=np.linspace(min(nr),max(nr),50)
            ax.plot(xs,p(xs),"r-",lw=2,label=f"slope={z[0]:.2f}")
        ax.legend()
    ax.set_title("J₃ vs None Ratio"); ax.set_xlabel("None ratio"); ax.grid(True,alpha=0.2)

    # D) k* distribution per rate (D1)
    ax=axes[1][0]
    width=0.15
    for ki,k in enumerate(K_LEVELS):
        vals=[]
        for rate in RATE_ALL:
            sub=[r for r in all_metrics if abs(r["rate"]-rate)<1e-6]
            vals.append(sum(1 for r in sub if r["k_star_D1"]==k)/max(len(sub),1)*100)
        colors=["#95a5a6","#2ecc71","#3498db","#e67e22","#e74c3c"]
        ax.bar([i+ki*width for i in range(len(RATE_ALL))],vals,width,
               label=f"k={k}",color=colors[ki],alpha=0.8)
    ax.set_xticks([i+0.3 for i in range(len(RATE_ALL))])
    ax.set_xticklabels([str(r) for r in RATE_ALL],fontsize=8)
    ax.set_title("k* % by Rate (D1)"); ax.legend(fontsize=7); ax.grid(True,alpha=0.2)

    # E) Island scale in k=3 windows per rate
    ax=axes[1][1]
    for ri,rate in enumerate(RATE_ALL):
        sub=[r for r in all_metrics if abs(r["rate"]-rate)<1e-6 and r["k_star_D1"]==3]
        if not sub: continue
        nn=np.mean([r["none_ratio"] for r in sub])
        wk=np.mean([r["weak_share"] for r in sub])
        md=np.mean([r["mid_share"] for r in sub])
        st=np.mean([r["strong_share"] for r in sub])
        ax.bar(ri,[nn,wk,md,st],bottom=[0,nn,nn+wk,nn+wk+md],
               color=["#95a5a6","#3498db","#e67e22","#e74c3c"],width=0.7)
    ax.set_xticks(range(len(RATE_ALL))); ax.set_xticklabels([str(r) for r in RATE_ALL],fontsize=8)
    ax.set_title("Scale in k*=3 Windows"); ax.grid(True,alpha=0.2)

    # F) Seed agreement per rate
    ax=axes[1][2]
    agrees=[]
    for rate in RATE_ALL:
        sub_s=defaultdict(list)
        for r in all_metrics:
            if abs(r["rate"]-rate)<1e-6: sub_s[r["seed"]].append(r["k_star_D1"])
        if not sub_s: agrees.append(0); continue
        doms=[Counter(v).most_common(1)[0][0] for v in sub_s.values()]
        maj=Counter(doms).most_common(1)[0][1]
        agrees.append(maj/len(doms)*100)
    ax.bar(range(len(RATE_ALL)),agrees,color="#2ecc71",alpha=0.7)
    ax.axhline(y=80,color="red",ls="--",alpha=0.5)
    ax.set_xticks(range(len(RATE_ALL))); ax.set_xticklabels([str(r) for r in RATE_ALL],fontsize=8)
    ax.set_title("Seed Agreement (%)"); ax.set_ylabel("%"); ax.grid(True,alpha=0.2)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/"v19e_plots.png",dpi=150,bbox_inches="tight")
    print(f"\n  Plot: {OUTPUT_DIR/'v19e_plots.png'}")

    # ================================================================
    # REPORT
    # ================================================================
    kd_D1=Counter(r["k_star_D1"] for r in all_metrics)
    kd_D2=Counter(r["k_star_D2"] for r in all_metrics)

    report=f"""# ESDE Genesis v1.9e — Follow-up Observation Report

## Summary

| Rate | D1 k* | D2 k* | ΔH32 D1 | ΔH32 D2 | Seed Agree |
|------|-------|-------|---------|---------|------------|
"""
    for ri,rate in enumerate(RATE_ALL):
        sub=[r for r in all_metrics if abs(r["rate"]-rate)<1e-6]
        if not sub: continue
        d1=Counter(r["k_star_D1"] for r in sub).most_common(1)[0][0]
        d2=Counter(r["k_star_D2"] for r in sub).most_common(1)[0][0]
        dh1=np.mean([r["dH32_D1"] for r in sub])
        dh2=np.mean([r["dH32_D2"] for r in sub])
        report+=f"| {rate} | k={d1} | k={d2} | {dh1:.4f} | {dh2:.4f} | {agrees[ri]:.0f}% |\n"

    report+=f"""
## Task A: D1 vs D2

D1 k* distribution: {dict(kd_D1)}
D2 k* distribution: {dict(kd_D2)}
D2 {'improves' if kd_D2.get(3,0)>kd_D1.get(3,0) else 'does not improve'} k=3 selection.

## Task B: Switch Events

Total switches: {len(switch_events)}
3→4: {sum(1 for r in switch_events if r['from_k']==3 and r['to_k']==4)}
4→3: {sum(1 for r in switch_events if r['from_k']==4 and r['to_k']==3)}

## Task C: Reproducibility

k=3 quality: none_ratio median = {np.median([r['none_ratio'] for r in k3_quality]):.3f}
Corr(J3, none_ratio) = {corr:.3f}
Winning empty: {'YES' if np.median([r['none_ratio'] for r in k3_quality])>0.95 else 'NO'}
"""
    with open(OUTPUT_DIR/"v19e_report.md","w") as f: f.write(report)
    print(f"  Report: {OUTPUT_DIR/'v19e_report.md'}")


if __name__=="__main__":
    main()
