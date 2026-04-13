"""
v9.11 Pbirth / B 試算スクリプト (audit 用、使い捨て)

式:
  Pbirth = (1 / C(5000, n_core)) * rho^(n-1) * r_core^(n-1) * S_avg^(n-1)
  B = -log10(Pbirth)
  rho = links_total / C(5000, 2)
"""

import csv
import math
from pathlib import Path

N = 5000
C_N_2 = N * (N - 1) // 2  # 12,497,500

def comb(n, k):
    return math.comb(n, k)

src = Path(__file__).parent / "v911_genesis_budget_raw.csv"
dst_csv = Path(__file__).parent / "v911_pbirth_computed.csv"

rows = []
with open(src) as f:
    reader = csv.DictReader(f)
    for r in reader:
        nc = int(r["n_core"])
        s_avg = float(r["s_avg"])
        r_core = float(r["r_core"])
        links_total = int(r["links_total"])
        rho = links_total / C_N_2

        exp = nc - 1
        c_n_nc = comb(N, nc)
        pbirth = (1.0 / c_n_nc) * (rho ** exp) * (r_core ** exp) * (s_avg ** exp)

        if pbirth > 0:
            B = -math.log10(pbirth)
        else:
            B = float("inf")

        rows.append({
            "seed": r["seed"],
            "window": r["window"],
            "lid": r["lid"],
            "n_core": nc,
            "s_avg": s_avg,
            "r_core": r_core,
            "rho": round(rho, 6),
            "links_total": links_total,
            "log10_pbirth": round(math.log10(pbirth), 4) if pbirth > 0 else None,
            "B": round(B, 4) if B != float("inf") else "inf",
            "b_gen_old": r["b_gen"],
        })

# Write CSV
with open(dst_csv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)

# ---- Statistics ----
Bs = [float(r["B"]) for r in rows if r["B"] != "inf"]
Bs.sort()

def pct(arr, p):
    idx = int(len(arr) * p / 100)
    idx = min(idx, len(arr) - 1)
    return arr[idx]

print(f"=== B 全体分布 (n={len(Bs)}) ===")
print(f"  min  = {Bs[0]:.4f}")
print(f"  p10  = {pct(Bs, 10):.4f}")
print(f"  p25  = {pct(Bs, 25):.4f}")
print(f"  p50  = {pct(Bs, 50):.4f}")
print(f"  p75  = {pct(Bs, 75):.4f}")
print(f"  p90  = {pct(Bs, 90):.4f}")
print(f"  max  = {Bs[-1]:.4f}")
print(f"  mean = {sum(Bs)/len(Bs):.4f}")

# n_core 別
from collections import defaultdict
by_nc = defaultdict(list)
for r in rows:
    if r["B"] != "inf":
        by_nc[int(r["n_core"])].append(float(r["B"]))

print(f"\n=== n_core 別 B 分布 ===")
for nc in sorted(by_nc):
    arr = sorted(by_nc[nc])
    n = len(arr)
    print(f"  n_core={nc} (n={n}): min={arr[0]:.2f}  p10={pct(arr,10):.2f}  p50={pct(arr,50):.2f}  p90={pct(arr,90):.2f}  max={arr[-1]:.2f}  mean={sum(arr)/n:.2f}")

# 具体例
print(f"\n=== 具体例 ===")
# 2ノード最強 (B最小)
nc2 = [(float(r["B"]), i, r) for i, r in enumerate(rows) if int(r["n_core"]) == 2 and r["B"] != "inf"]
nc2.sort()
best2 = nc2[0][2]
print(f"  2-node 最強 (B最小): lid={best2['lid']} B={best2['B']} s_avg={best2['s_avg']} r_core={best2['r_core']} rho={best2['rho']}")

# 5ノード最強
nc5 = [(float(r["B"]), i, r) for i, r in enumerate(rows) if int(r["n_core"]) == 5 and r["B"] != "inf"]
nc5.sort()
best5 = nc5[0][2]
print(f"  5-node 最強 (B最小): lid={best5['lid']} B={best5['B']} s_avg={best5['s_avg']} r_core={best5['r_core']} rho={best5['rho']}")

# 5ノード最弱
worst5 = nc5[-1][2]
print(f"  5-node 最弱 (B最大): lid={worst5['lid']} B={worst5['B']} s_avg={worst5['s_avg']} r_core={worst5['r_core']} rho={worst5['rho']}")

# PI 試算 (方向性のみ)
print(f"\n=== PI 試算 (方向性) ===")
print(f"  B range: [{Bs[0]:.2f}, {Bs[-1]:.2f}]")
print(f"  B_ref 候補 (p50): {pct(Bs, 50):.2f}")
print(f"  PI = clamp(B_ref / B, 0.1, 5.0) の場合:")
B_ref = pct(Bs, 50)
for label, val in [("2-node best", float(best2["B"])), ("5-node best", float(best5["B"])), ("5-node worst", float(worst5["B"])), ("median", B_ref)]:
    pi = max(0.1, min(5.0, B_ref / val))
    print(f"    {label}: B={val:.2f} -> PI={pi:.3f}")
