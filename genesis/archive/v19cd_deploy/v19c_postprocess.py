#!/usr/bin/env python3
"""
ESDE Genesis v1.9c — k=3 Tightened (Mid/Strong Split)
========================================================
k=3 bins: None / WeakOnly / Mid / Strong
Split using r_bits directly:
  None:     not in any island at any threshold (r=000)
  WeakOnly: in weak island only (r=001)
  Mid:      in mid island but not strong (r=01x)
  Strong:   in strong island (r=1xx)

Postprocess on existing v18O2 data.

Usage:
  python v19c_postprocess.py --input-dir outputs_v18O2
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import csv, json, argparse
from collections import Counter, defaultdict
from pathlib import Path

LAMBDA=1.0; MU=0.5; K_LEVELS=[0,1,2,3,4]
RATE_GRID=[0.0,0.0005,0.001,0.002,0.005]
R_BITS_KEYS=["000","001","010","011","100","101","110","111"]
OUTPUT_DIR=Path("outputs_v19c")


def shannon(c):
    t=sum(c);
    if t==0: return 0.0
    return -sum((x/t)*np.log2(x/t) for x in c if x>0)


def ctx_to_label(ctx, k):
    if k==0: return "C"
    rb=ctx.get("r_bits","000")
    s=int(rb[0]); m=int(rb[1]) if len(rb)>=2 else 0; w=int(rb[2]) if len(rb)>=3 else 0
    # k>=1: Resonance
    res="High" if s else ("Mid" if m else "Low")
    if k==1: return f"C_{res}"
    # k>=2: Boundary
    bd="Edge" if ctx.get("boundary_mid",0)==1 else "Core"
    if k==2: return f"C_{res}_{bd}"
    # k>=3: Island Scale (v1.9c: 4 bins)
    if s==1:        scale="Strong"
    elif m==1:      scale="Mid"
    elif w==1:      scale="WeakOnly"
    else:           scale="None"
    if k==3: return f"C_{res}_{bd}_{scale}"
    # k>=4: Intrusion
    ie="1p" if ctx.get("intrusion_bin",0)>=1 else "0"
    return f"C_{res}_{bd}_{scale}_{ie}"


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


def drift_jsd(n1,n2,k):
    l1=Counter(ctx_to_label(n,k) for n in n1)
    l2=Counter(ctx_to_label(n,k) for n in n2)
    al=set(l1)|set(l2); t1=sum(l1.values()); t2=sum(l2.values())
    if t1==0 or t2==0 or not al: return None
    p=np.array([l1.get(l,0)/t1 for l in al])
    q=np.array([l2.get(l,0)/t2 for l in al])
    m=(p+q)/2
    kl=lambda a,b: sum(a[i]*np.log2(a[i]/b[i]) for i in range(len(a)) if a[i]>0 and b[i]>0)
    return round(float(np.sqrt((kl(p,m)+kl(q,m))/2)),4)


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
    parser.add_argument("--input-dir",default="outputs_v18O2")
    args=parser.parse_args()
    inp=Path(args.input_dir); OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
    wd=load_data(inp)
    print(f"  Loaded: {len(wd)} runs, {sum(len(v) for v in wd.values())} windows")

    comp=[]; opt=[]; k3d=[]; qa_scale=Counter()

    for (rate,seed),wins in sorted(wd.items()):
        prev=None
        for wi,row in enumerate(wins):
            nodes=reconstruct_nodes(row)
            if not nodes: prev=None; continue

            # QA scale distribution
            for n in nodes:
                rb=n["r_bits"]; s,m,w=int(rb[0]),int(rb[1]),int(rb[2]) if len(rb)>=3 else 0
                if s: qa_scale["Strong"]+=1
                elif m: qa_scale["Mid"]+=1
                elif w: qa_scale["WeakOnly"]+=1
                else: qa_scale["None"]+=1

            for k in K_LEVELS:
                labels=[ctx_to_label(n,k) for n in nodes]
                counts=Counter(labels); tc=len(counts); H=shannon(list(counts.values()))
                drift=drift_jsd(prev,nodes,k) if prev else None
                tH=round(H,4); tD=round(LAMBDA*drift,4) if drift else 0
                tP=round(-MU*np.log2(tc+1),4)
                J=round(tH+tD+tP,4)
                comp.append({"seed":seed,"window":wi+1,"rate":rate,"k":k,
                    "tc":tc,"H":tH,"drift":drift,"J":J,"tH":tH,"tD":tD,"tP":tP})

            best=max(comp[-5:],key=lambda r:r["J"]); ks=best["k"]
            for r in comp[-5:]: r["k_star"]=ks
            opt.append({"seed":seed,"window":wi+1,"rate":rate,"k_star":ks,
                        "J":best["J"],"tc":best["tc"],"H":best["H"]})

            # k=3 vs k=2
            H2=[r for r in comp[-5:] if r["k"]==2][0]["H"]
            H3=[r for r in comp[-5:] if r["k"]==3][0]["H"]
            J2=[r for r in comp[-5:] if r["k"]==2][0]["J"]
            J3=[r for r in comp[-5:] if r["k"]==3][0]["J"]
            k3d.append({"seed":seed,"window":wi+1,"rate":rate,
                        "H2":H2,"H3":H3,"dH":round(H3-H2,4),"J2":J2,"J3":J3})
            prev=nodes

    # Save
    with open(OUTPUT_DIR/"v19c_k_metrics.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=comp[0].keys()); w.writeheader(); w.writerows(comp)
    with open(OUTPUT_DIR/"v19c_optimal_k.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=opt[0].keys()); w.writeheader(); w.writerows(opt)
    with open(OUTPUT_DIR/"v19c_k3_diag.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=k3d[0].keys()); w.writeheader(); w.writerows(k3d)

    # Analysis
    kd=Counter(r["k_star"] for r in opt)
    print(f"\n  v1.9c k* Distribution (k=3: None/WeakOnly/Mid/Strong):")
    for k in K_LEVELS:
        print(f"    k={k}: {kd.get(k,0)} ({kd.get(k,0)/max(len(opt),1)*100:.1f}%)")
    print(f"  Island Scale: {dict(qa_scale)}")

    # Per-rate
    ra=[]
    for rate in RATE_GRID:
        sub=[r for r in opt if abs(r["rate"]-rate)<1e-6]
        if not sub: continue
        d=Counter(r["k_star"] for r in sub)
        dom=d.most_common(1)[0][0]
        mJ=np.mean([r["J"] for r in sub])
        ra.append({"rate":rate,"dom":dom,"dist":dict(d),"mJ":round(mJ,4)})
        print(f"    rate={rate}: k*={dom} dist={dict(d)} J={mJ:.3f}")

    # k=3 analysis
    print(f"\n  k=3 Diagnosis (v1.9c):")
    for rate in RATE_GRID:
        sub=[r for r in k3d if abs(r["rate"]-rate)<1e-6]
        if not sub: continue
        mdH=np.mean([r["dH"] for r in sub])
        k3w=sum(1 for r in opt if abs(r["rate"]-rate)<1e-6 and r["k_star"]==3)
        print(f"    rate={rate}: ΔH={mdH:.4f} k=3 wins={k3w}")

    # Plots
    fig,axes=plt.subplots(2,3,figsize=(20,12))
    fig.suptitle("ESDE Genesis v1.9c — k=3 Tightened (None/WeakOnly/Mid/Strong)",
                 fontsize=13,fontweight="bold")
    colors=["#95a5a6","#2ecc71","#3498db","#e67e22","#e74c3c"]

    ax=axes[0][0]
    ax.bar(K_LEVELS,[kd.get(k,0) for k in K_LEVELS],color=colors)
    ax.set_title("k* Distribution"); ax.set_xlabel("k"); ax.grid(True,alpha=0.2)

    ax=axes[0][1]
    if ra: ax.plot([a["rate"] for a in ra],[a["dom"] for a in ra],"o-",color="#e67e22",ms=10,lw=2)
    ax.set_title("Dominant k* vs Rate"); ax.set_yticks(K_LEVELS); ax.grid(True,alpha=0.2)

    ax=axes[0][2]
    dhs=[r["dH"] for r in k3d]
    ax.hist(dhs,bins=40,color="#e67e22",alpha=0.7,edgecolor="white")
    ax.axvline(x=0,color="red",ls="--"); ax.axvline(x=0.05,color="green",ls=":",label="target")
    ax.set_title("ΔH(k3−k2)"); ax.legend(); ax.grid(True,alpha=0.2)

    ax=axes[1][0]
    for k in K_LEVELS:
        vals=[r["J"] for r in comp if r["k"]==k]
        if vals: ax.bar(k,np.mean(vals),color=colors[k],alpha=0.7)
    ax.set_title("Mean J per k"); ax.set_xlabel("k"); ax.grid(True,alpha=0.2)

    ax=axes[1][1]
    ax.bar(["None","WeakOnly","Mid","Strong"],
           [qa_scale.get(k,0) for k in ["None","WeakOnly","Mid","Strong"]],
           color=["#95a5a6","#3498db","#e67e22","#e74c3c"])
    ax.set_title("Island Scale Distribution"); ax.grid(True,alpha=0.2)

    # Type count by k
    ax=axes[1][2]
    for k in K_LEVELS:
        tc=[r["tc"] for r in comp if r["k"]==k]
        if tc: ax.boxplot([tc],positions=[k],widths=0.6)
    ax.set_title("Type Count by k"); ax.set_xlabel("k"); ax.grid(True,alpha=0.2)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/"v19c_plots.png",dpi=150,bbox_inches="tight")

    # Conclusion
    k3_met=any(np.mean([r["dH"] for r in k3d if abs(r["rate"]-rt)<1e-6])>0.05
               for rt in RATE_GRID if [r for r in k3d if abs(r["rate"]-rt)<1e-6])
    k3_win_pct=kd.get(3,0)/max(len(opt),1)*100

    txt=f"""ESDE Genesis v1.9c — k=3 Tightened Conclusion
================================================
k=3 bins: None / WeakOnly / Mid / Strong
Scale dist: {dict(qa_scale)}

k* Distribution:
{chr(10).join(f'  k={k}: {kd.get(k,0)} ({kd.get(k,0)/max(len(opt),1)*100:.1f}%)' for k in K_LEVELS)}

k=3 wins: {kd.get(3,0)} ({k3_win_pct:.1f}%)
ΔH(k3-k2) > 0.05 target met: {'YES' if k3_met else 'NO'}

Per-rate:
{chr(10).join(f'  rate={a["rate"]}: k*={a["dom"]} J={a["mJ"]:.3f}' for a in ra)}
"""
    with open(OUTPUT_DIR/"v19c_conclusion.txt","w") as f: f.write(txt)
    print(txt)


if __name__=="__main__":
    main()
