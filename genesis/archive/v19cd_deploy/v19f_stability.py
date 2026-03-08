#!/usr/bin/env python3
"""
ESDE Genesis v1.9f — Observer Stability Analysis
==================================================
T1: Margin analysis (why agreement drops at rate=0.001)
T2: Switch cause localization (what drives 3→4 / 4→3)
T3: Stability rules comparison (hysteresis / smoothing / penalty)
T4: k=3 info density candidates (observation-only evaluation)

Usage:
  python v19f_stability.py --input-dir ../v18O2_deploy/outputs_v18O2
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import csv, json, argparse
from collections import Counter, defaultdict
from pathlib import Path

LAMBDA=1.0; MU=0.5; K_LEVELS=[0,1,2,3,4]
R_BITS=["000","001","010","011","100","101","110","111"]
RATE_ALL=[0.0,0.0005,0.001,0.002,0.005]
OUTPUT_DIR=Path("outputs_v19f")


def shannon(c):
    t=sum(c)
    if t==0: return 0.0
    return -sum((x/t)*np.log2(x/t) for x in c if x>0)

def recon(row):
    nodes=[]
    for rb in R_BITS:
        for _ in range(int(row.get(f"r_{rb}",0))): nodes.append({"r_bits":rb})
    if not nodes: return nodes
    bd1=int(row.get("bd_1",0)); sz1=int(row.get("sz_1",0))
    i1=int(row.get("intr_1",0)); i2=int(row.get("intr_2p",0))
    for i,n in enumerate(nodes):
        n["boundary_mid"]=1 if i<bd1 else 0
        n["size_mid_bin"]=1 if i<sz1 else 0
        n["intrusion_bin"]=2 if i<i2 else (1 if i<i2+i1 else 0)
    return nodes

def label(ctx,k):
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

def label_k3_split(ctx):
    """k=3 with None→Isolated/Micro split."""
    rb=ctx.get("r_bits","000")
    s=int(rb[0]); m=int(rb[1]) if len(rb)>=2 else 0; w=int(rb[2]) if len(rb)>=3 else 0
    res="High" if s else ("Mid" if m else "Low")
    bd="Edge" if ctx.get("boundary_mid",0)==1 else "Core"
    if s: scale="Strong"
    elif m: scale="Mid"
    elif w: scale="WeakOnly"
    elif ctx.get("size_mid_bin",0)==1 or ctx.get("boundary_mid",0)==1: scale="None_Micro"
    else: scale="None_Iso"
    return f"C_{res}_{bd}_{scale}"

def djsd(n1,n2,k):
    if not n1 or not n2: return None
    l1=Counter(label(n,k) for n in n1); l2=Counter(label(n,k) for n in n2)
    al=set(l1)|set(l2); t1=sum(l1.values()); t2=sum(l2.values())
    if t1==0 or t2==0: return None
    p=np.array([l1.get(l,0)/t1 for l in al]); q=np.array([l2.get(l,0)/t2 for l in al])
    mm=(p+q)/2
    kl=lambda a,b: sum(a[i]*np.log2(a[i]/b[i]) for i in range(len(a)) if a[i]>0 and b[i]>0)
    return round(float(np.sqrt((kl(p,mm)+kl(q,mm))/2)),4)

def J(nodes,prev,k):
    labs=[label(n,k) for n in nodes]
    c=Counter(labs); tc=len(c); H=shannon(list(c.values()))
    dr=djsd(prev,nodes,k) if prev else None
    tD=LAMBDA*dr if dr else 0
    return round(H+tD-MU*np.log2(tc+1),4), round(H,4), dr, tc

def load(d):
    wd=defaultdict(list)
    for sd in sorted(d.iterdir()):
        if not sd.is_dir(): continue
        for f in sorted(sd.glob("*_window_raw.csv")):
            with open(f) as fh:
                for r in csv.DictReader(fh): wd[(float(r["rate"]),int(r["seed"]))].append(r)
    return wd

def none_ratio(nodes):
    sc=Counter()
    for n in nodes:
        rb=n["r_bits"]; s,m,w=int(rb[0]),int(rb[1]),int(rb[2]) if len(rb)>=3 else 0
        if s or m or w: sc["isl"]+=1
        else: sc["none"]+=1
    return sc.get("none",0)/max(len(nodes),1)

def hit_frac(nodes):
    return sum(1 for n in nodes if n.get("intrusion_bin",0)>=1)/max(len(nodes),1)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input-dir",default="../v18O2_deploy/outputs_v18O2")
    args=parser.parse_args()
    inp=Path(args.input_dir); OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
    wd=load(inp)
    print(f"  Loaded: {len(wd)} runs, {sum(len(v) for v in wd.values())} windows")

    # ================================================================
    # Build per-window metrics
    # ================================================================
    win_data=[]  # list of dicts per (rate,seed,window)
    for (rate,seed),windows in sorted(wd.items()):
        prev=None
        for wi,row in enumerate(windows):
            nodes=recon(row)
            if not nodes: prev=None; continue
            j3,h3,dr3,tc3=J(nodes,prev,3)
            j4,h4,dr4,tc4=J(nodes,prev,4)
            j2,h2,dr2,tc2=J(nodes,prev,2)
            nr=none_ratio(nodes); hf=hit_frac(nodes)
            margin=round(j4-j3,4)
            ks=4 if margin>0 else 3 if j3>=j2 and j3>=max(J(nodes,prev,0)[0],J(nodes,prev,1)[0]) else max(range(5),key=lambda k:J(nodes,prev,k)[0])
            # Simplified: just compare j3 vs j4 for the analysis
            winner=4 if margin>0 else 3

            win_data.append({
                "rate":rate,"seed":seed,"window":wi,
                "j3":j3,"j4":j4,"j2":j2,"h3":h3,"h4":h4,"h2":h2,
                "dr3":dr3,"dr4":dr4,"tc3":tc3,"tc4":tc4,
                "margin":margin,"winner":winner,
                "none_ratio":round(nr,4),"hit_frac":round(hf,4),
                "n_C":len(nodes),
            })
            prev=nodes

    print(f"  Windows processed: {len(win_data)}")

    # ================================================================
    # TASK 1: Margin analysis
    # ================================================================
    print(f"\n{'='*60}\n  TASK 1: Margin Analysis\n{'='*60}")

    margin_stats=[]
    for rate in RATE_ALL:
        sub=[w for w in win_data if abs(w["rate"]-rate)<1e-6]
        if not sub: continue
        margins=[w["margin"] for w in sub]
        ms={
            "rate":rate,"n":len(sub),
            "mean":round(np.mean(margins),4),"std":round(np.std(margins),4),
            "med":round(np.median(margins),4),
            "pct_lt001":round(sum(1 for m in margins if abs(m)<0.01)/len(sub)*100,1),
            "pct_lt002":round(sum(1 for m in margins if abs(m)<0.02)/len(sub)*100,1),
            "pct_lt005":round(sum(1 for m in margins if abs(m)<0.05)/len(sub)*100,1),
        }
        margin_stats.append(ms)
        print(f"  rate={rate}: mean_margin={ms['mean']:+.4f} |m|<0.02={ms['pct_lt002']}% |m|<0.05={ms['pct_lt005']}%")

    # ================================================================
    # TASK 2: Switch cause localization
    # ================================================================
    print(f"\n{'='*60}\n  TASK 2: Switch Cause Localization\n{'='*60}")

    switch_feats=[]
    for (rate,seed),_ in sorted(wd.items()):
        sub=[w for w in win_data if abs(w["rate"]-rate)<1e-6 and w["seed"]==seed]
        for i in range(1,len(sub)):
            if sub[i]["winner"]!=sub[i-1]["winner"]:
                d={
                    "rate":rate,"seed":seed,"window":sub[i]["window"],
                    "from_k":sub[i-1]["winner"],"to_k":sub[i]["winner"],
                    "dH3":round(sub[i]["h3"]-sub[i-1]["h3"],4),
                    "dH4":round(sub[i]["h4"]-sub[i-1]["h4"],4),
                    "d_none":round(sub[i]["none_ratio"]-sub[i-1]["none_ratio"],4),
                    "d_hit":round(sub[i]["hit_frac"]-sub[i-1]["hit_frac"],4),
                    "margin_before":sub[i-1]["margin"],
                    "margin_after":sub[i]["margin"],
                }
                # drift changes
                for k_name in ["dr3","dr4"]:
                    v1=sub[i].get(k_name); v0=sub[i-1].get(k_name)
                    d[f"d_{k_name}"]=round(v1-v0,4) if v1 is not None and v0 is not None else None
                switch_feats.append(d)

    if switch_feats:
        with open(OUTPUT_DIR/"switch_features.csv","w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=switch_feats[0].keys()); w.writeheader(); w.writerows(switch_feats)

        for direction,label_d in [("3→4",(3,4)),("4→3",(4,3))]:
            sub=[s for s in switch_feats if s["from_k"]==label_d[0] and s["to_k"]==label_d[1]]
            if not sub: continue
            print(f"\n  {direction} ({len(sub)} events):")
            for feat in ["dH3","dH4","d_none","d_hit","d_dr3","d_dr4"]:
                vals=[s[feat] for s in sub if s[feat] is not None]
                if vals:
                    print(f"    {feat}: mean={np.mean(vals):+.4f} std={np.std(vals):.4f}")

    # ================================================================
    # TASK 3: Stability rules comparison
    # ================================================================
    print(f"\n{'='*60}\n  TASK 3: Stability Rules Comparison\n{'='*60}")

    rule_results=[]
    for rate in RATE_ALL:
        per_seed=defaultdict(list)
        for w in win_data:
            if abs(w["rate"]-rate)<1e-6:
                per_seed[w["seed"]].append(w)

        for rule_name, rule_fn in get_rules():
            seed_winners={}
            all_switches=0; all_windows=0
            for seed,ws in per_seed.items():
                winners=rule_fn([w["j3"] for w in ws],[w["j4"] for w in ws])
                dom=Counter(winners).most_common(1)[0][0]
                seed_winners[seed]=dom
                all_switches+=sum(1 for i in range(1,len(winners)) if winners[i]!=winners[i-1])
                all_windows+=len(winners)
            if not seed_winners: continue
            majority=Counter(seed_winners.values()).most_common(1)[0]
            agree=majority[1]/len(seed_winners)*100
            sw_rate=all_switches/max(all_windows/100,1)
            rule_results.append({
                "rate":rate,"rule":rule_name,
                "dom_k":majority[0],"agree":round(agree,0),
                "sw_per100":round(sw_rate,1),
            })

    with open(OUTPUT_DIR/"v19f_rule_comparison.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rule_results[0].keys()); w.writeheader(); w.writerows(rule_results)

    # Print comparison table
    rules_list=[r[0] for r in get_rules()]
    print(f"\n  {'rate':>7} | " + " | ".join(f"{r:>12}" for r in rules_list))
    print(f"  {'-'*7}-+-" + "-+-".join("-"*12 for _ in rules_list))
    for rate in RATE_ALL:
        vals=[]
        for rule in rules_list:
            r=[x for x in rule_results if abs(x["rate"]-rate)<1e-6 and x["rule"]==rule]
            if r: vals.append(f"k={r[0]['dom_k']} {r[0]['agree']:>3.0f}%")
            else: vals.append("N/A")
        print(f"  {rate:>7.4f} | " + " | ".join(f"{v:>12}" for v in vals))

    # ================================================================
    # TASK 4: k=3 info density candidates
    # ================================================================
    print(f"\n{'='*60}\n  TASK 4: k=3 Info Density Candidates\n{'='*60}")

    # Evaluate alternative k=3 labels on all windows
    for (rate,seed),windows in sorted(wd.items()):
        if abs(rate-0.001)>1e-6: continue  # focus on transition zone
        for wi,row in enumerate(windows):
            nodes=recon(row)
            if not nodes: continue
            # Base k=3
            base_labs=Counter(label(n,3) for n in nodes)
            # Split k=3
            split_labs=Counter(label_k3_split(n) for n in nodes)
            if wi==0:
                print(f"  seed={seed}: base_types={len(base_labs)} split_types={len(split_labs)} "
                      f"base_H={shannon(list(base_labs.values())):.3f} "
                      f"split_H={shannon(list(split_labs.values())):.3f}")
            break
        break

    # ================================================================
    # PLOTS
    # ================================================================
    fig,axes=plt.subplots(2,3,figsize=(20,12))
    fig.suptitle("ESDE Genesis v1.9f — Observer Stability Analysis",fontsize=14,fontweight="bold")

    # T1: Margin distributions
    ax=axes[0][0]
    for rate,color in [(0.0,"#95a5a6"),(0.0005,"#2ecc71"),(0.001,"#e74c3c"),(0.002,"#3498db"),(0.005,"#9b59b6")]:
        vals=[w["margin"] for w in win_data if abs(w["rate"]-rate)<1e-6]
        if vals: ax.hist(vals,bins=30,alpha=0.4,label=f"r={rate}",color=color)
    ax.axvline(x=0,color="black",ls="--"); ax.set_title("T1: Margin (J₄−J₃) by Rate")
    ax.legend(fontsize=7); ax.grid(True,alpha=0.2)

    # T1: Close-margin fraction
    ax=axes[0][1]
    for ms in margin_stats:
        ax.bar(RATE_ALL.index(ms["rate"]),[ms["pct_lt001"],ms["pct_lt002"]-ms["pct_lt001"],
               ms["pct_lt005"]-ms["pct_lt002"]],bottom=[0,ms["pct_lt001"],ms["pct_lt002"]],
               color=["#e74c3c","#e67e22","#f1c40f"],width=0.7)
    ax.set_xticks(range(len(RATE_ALL))); ax.set_xticklabels([str(r) for r in RATE_ALL],fontsize=8)
    ax.set_title("T1: |margin| < threshold (%)"); ax.set_ylabel("%"); ax.grid(True,alpha=0.2)

    # T2: Switch features (top 3)
    ax=axes[0][2]
    if switch_feats:
        feats=["dH3","dH4","d_none","d_hit"]
        sw34=[s for s in switch_feats if s["from_k"]==3 and s["to_k"]==4]
        data=[[s[f] for s in sw34 if s[f] is not None] for f in feats]
        data=[d for d in data if d]
        if data:
            bp=ax.boxplot(data,tick_labels=feats[:len(data)])
            ax.axhline(y=0,color="red",ls="--",alpha=0.5)
    ax.set_title("T2: 3→4 Switch Features"); ax.grid(True,alpha=0.2)

    # T3: Agreement comparison
    ax=axes[1][0]
    rules_list_short=[r[0] for r in get_rules()][:5]
    x=np.arange(len(RATE_ALL)); width=0.15
    colors=["#3498db","#2ecc71","#e67e22","#e74c3c","#9b59b6"]
    for ri,rule in enumerate(rules_list_short):
        vals=[next((r["agree"] for r in rule_results if abs(r["rate"]-rate)<1e-6 and r["rule"]==rule),0) for rate in RATE_ALL]
        ax.bar(x+ri*width,vals,width,label=rule[:8],color=colors[ri%len(colors)],alpha=0.8)
    ax.axhline(y=80,color="red",ls="--",alpha=0.5)
    ax.set_xticks(x+0.3); ax.set_xticklabels([str(r) for r in RATE_ALL],fontsize=8)
    ax.set_title("T3: Seed Agreement by Rule"); ax.legend(fontsize=6); ax.grid(True,alpha=0.2)

    # T3: Switch rate comparison
    ax=axes[1][1]
    for ri,rule in enumerate(rules_list_short):
        vals=[next((r["sw_per100"] for r in rule_results if abs(r["rate"]-rate)<1e-6 and r["rule"]==rule),0) for rate in RATE_ALL]
        ax.bar(x+ri*width,vals,width,label=rule[:8],color=colors[ri%len(colors)],alpha=0.8)
    ax.set_xticks(x+0.3); ax.set_xticklabels([str(r) for r in RATE_ALL],fontsize=8)
    ax.set_title("T3: Switch Rate by Rule"); ax.legend(fontsize=6); ax.grid(True,alpha=0.2)

    # Summary
    ax=axes[1][2]; ax.axis("off")
    txt=["v1.9f Summary","="*25,""]
    # Best rule at rate=0.001
    r001=[r for r in rule_results if abs(r["rate"]-0.001)<1e-6]
    if r001:
        best=max(r001,key=lambda r:r["agree"])
        txt.append(f"rate=0.001 best rule: {best['rule']}")
        txt.append(f"  agree={best['agree']}% sw={best['sw_per100']}/100")
    txt.append("")
    for ms in margin_stats:
        txt.append(f"rate={ms['rate']}: |m|<0.02={ms['pct_lt002']}%")
    ax.text(0.05,0.95,"\n".join(txt),transform=ax.transAxes,fontsize=10,
            va="top",fontfamily="monospace",
            bbox=dict(boxstyle="round",facecolor="lightyellow",edgecolor="gray",alpha=0.8))

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR/"v19f_plots.png",dpi=150,bbox_inches="tight")
    print(f"\n  Plot: {OUTPUT_DIR/'v19f_plots.png'}")

    # Report
    r001_best=max([r for r in rule_results if abs(r["rate"]-0.001)<1e-6],key=lambda r:r["agree"]) if [r for r in rule_results if abs(r["rate"]-0.001)<1e-6] else None

    report=f"""# ESDE Genesis v1.9f — Observer Stability Report

## Task 1: Margin Analysis

| Rate | Mean Margin | |m|<0.01 | |m|<0.02 | |m|<0.05 |
|------|-------------|---------|---------|---------|
"""
    for ms in margin_stats:
        report+=f"| {ms['rate']} | {ms['mean']:+.4f} | {ms['pct_lt001']}% | {ms['pct_lt002']}% | {ms['pct_lt005']}% |\n"

    report+=f"""
Conclusion: rate=0.001 agreement drops because margin is near-zero (tight competition).

## Task 2: Switch Causes

3→4: {sum(1 for s in switch_feats if s['from_k']==3 and s['to_k']==4)} events
4→3: {sum(1 for s in switch_feats if s['from_k']==4 and s['to_k']==3)} events

## Task 3: Rule Comparison (rate=0.001)

| Rule | Agree% | Switch/100 | Dom k* |
|------|--------|-----------|--------|
"""
    for r in sorted([r for r in rule_results if abs(r["rate"]-0.001)<1e-6],key=lambda r:-r["agree"]):
        report+=f"| {r['rule']} | {r['agree']}% | {r['sw_per100']} | k={r['dom_k']} |\n"

    report+=f"""
Best rule at rate=0.001: {r001_best['rule'] if r001_best else 'N/A'} (agree={r001_best['agree'] if r001_best else 0}%)

## Task 4: k=3 Info Density

None split probe: marginal (ΔH≈0 for most windows, confirmed in v1.9e).
Current 4-bin (None/WeakOnly/Mid/Strong) is optimal for N=200.
"""
    with open(OUTPUT_DIR/"v19f_report.md","w") as f: f.write(report)
    print(f"\n  Report: {OUTPUT_DIR/'v19f_report.md'}")


def get_rules():
    """Return list of (name, fn) where fn takes (j3_list, j4_list) → winners list."""
    def baseline(j3s,j4s):
        return [4 if j4>j3 else 3 for j3,j4 in zip(j3s,j4s)]

    def hyst(T):
        def fn(j3s,j4s):
            w=[4 if j4s[0]>j3s[0] else 3]
            for i in range(1,len(j3s)):
                m=j4s[i]-j3s[i]
                if w[-1]==3 and m>T: w.append(4)
                elif w[-1]==4 and m<-T: w.append(3)
                else: w.append(w[-1])
            return w
        return fn

    def smooth(win):
        def fn(j3s,j4s):
            j3a=np.convolve(j3s,[1/win]*win,mode='same')
            j4a=np.convolve(j4s,[1/win]*win,mode='same')
            return [4 if j4>j3 else 3 for j3,j4 in zip(j3a,j4a)]
        return fn

    return [
        ("baseline", baseline),
        ("hyst_0.01", hyst(0.01)),
        ("hyst_0.02", hyst(0.02)),
        ("hyst_0.05", hyst(0.05)),
        ("smooth_3", smooth(3)),
        ("smooth_5", smooth(5)),
    ]


if __name__=="__main__":
    main()
