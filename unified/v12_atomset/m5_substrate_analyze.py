#!/usr/bin/env python3
"""v12 M5 substrate 並行試行 解析 — 2×2+shuffle 対比 + lag 解析（GPT/Gemini の二穴に答える）

成功条件: 経験が本物（間接混線でない）= D−E が cid 対応で有意 かつ lag2+ で shuffle に消える。
slight: Δlinks/Δalive/θ_nan。seed 3 で符号一致。
同 seed = 決定論 fork（経験/入力の適用まで同一）→ cid を跨条件で照合し因果効果を測る。
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path('/home/takasan/esde/ESDE-Research/unified/v12_atomset/run_m5_substrate')
CONDS = ['A', 'B', 'C', 'D', 'E']
SEEDS = [0, 1, 2]
LAG_EXCLUDE = 1


def load(cond, seed):
    d = ROOT / cond / f'seed{seed}'
    rec = pd.read_parquet(d / 'records.parquet')
    summ = json.loads((d / 'summary.json').read_text())
    return rec, summ


# ---- 1. slight 監視 + 規模 (cond 別、seed 平均) ----
print('=== 1. slight 監視 + 規模 (seed 平均) ===')
print(f'{"cond":4s} {"θ_div":6s} {"Δlinks%":>8s} {"Δalive%":>8s} {"Σinput_E":>9s} {"Σexp_E":>8s} {"Σexp_L":>8s} {"exc_std":>8s}')
agg = {}
for c in CONDS:
    rows = [load(c, s)[1] for s in SEEDS]
    div = any(r['theta_diverged'] for r in rows)
    dl = np.mean([r['delta_links_pct'] for r in rows]); da = np.mean([r['delta_alive_pct'] for r in rows])
    ie = np.mean([r['sum_input_E'] for r in rows]); ee = np.mean([r['sum_exp_E'] for r in rows])
    el = np.mean([r['sum_exp_L'] for r in rows]); es = np.mean([r['exc_std_across_cid'] for r in rows])
    agg[c] = dict(dl=dl, da=da, ie=ie, ee=ee, el=el, es=es)
    print(f'{c:4s} {str(div):6s} {dl:>8.2f} {da:>8.2f} {ie:>9.3f} {ee:>8.3f} {el:>8.4f} {es:>8.3f}')

# ---- 2. fork 因果効果: 同 seed で cid 照合し Δexc (条件差) ----
# C−A=経験単独, D−B=入力に経験追加, D−E=cid対応が本物, B−A=橋の反射
def matched_exc(cond, seed):
    """per-cid の mean exc (最終 window 群)。"""
    rec, _ = load(cond, seed)
    return rec.groupby('cid')['exc'].mean()


def contrast(c1, c2):
    """同 seed で cid 照合、|exc_c1 - exc_c2| の平均 (seed 平均±std) と符号一致。"""
    vals = []
    for s in SEEDS:
        a = matched_exc(c1, s); b = matched_exc(c2, s)
        common = a.index.intersection(b.index)
        if len(common) == 0:
            vals.append((0.0, 0.0, 0)); continue
        d = (a[common] - b[common])
        vals.append((float(d.mean()), float(d.abs().mean()), len(common)))
    means = [v[0] for v in vals]; absmeans = [v[1] for v in vals]; ncids = [v[2] for v in vals]
    sign_agree = all(m > 0 for m in means) or all(m < 0 for m in means)
    return dict(mean_diff=np.mean(means), abs_diff=np.mean(absmeans),
                per_seed_mean=means, n_cids=ncids, sign_agree=sign_agree)


print('\n=== 2. fork 因果効果 (同 seed cid 照合、Δexc=出力励起の条件差) ===')
print('  対比         |Δexc|平均   Δexc(符号付)  per-seed符号一致   n_cids(共通)')
for name, c1, c2 in [('B−A 橋反射', 'B', 'A'), ('C−A 経験単独', 'C', 'A'),
                     ('D−B 入力+経験', 'D', 'B'), ('D−E cid対応', 'D', 'E')]:
    r = contrast(c1, c2)
    print(f'  {name:14s} {r["abs_diff"]:>9.3f}  {r["mean_diff"]:>11.3f}   '
          f'{str(r["sign_agree"]):>8s}  {r["per_seed_mean"]}  {r["n_cids"]}')

# ---- 3. lag 解析: 経験効果が lag2+ で出るか、shuffle で消えるか ----
# D と E で、lag bucket 別に「exp を持つ cid の exc」が A 比でどれだけ動くか
print('\n=== 3. lag 解析 (反射 lag0-1 vs 経験 lag2+、D vs E=shuffle) ===')
def lag_effect(cond):
    """各 seed で、lag bucket 別に exc の cid 間分散 (個性化代理) を測る。"""
    out = {'reflex': [], 'exp': []}
    for s in SEEDS:
        rec, _ = load(cond, s)
        for bucket, mask in [('reflex', rec.lag_since_input <= LAG_EXCLUDE),
                             ('exp', rec.lag_since_input >= LAG_EXCLUDE + 1)]:
            sub = rec[mask]
            if len(sub) > 1:
                out[bucket].append(float(sub.groupby('cid')['exc'].mean().std()))
    return {k: (np.mean(v) if v else float('nan'), len(v)) for k, v in out.items()}

for c in ['B', 'C', 'D', 'E']:
    le = lag_effect(c)
    print(f'  {c}: reflex(lag0-1) exc_std={le["reflex"][0]:.3f} (n={le["reflex"][1]}), '
          f'lag2+ exc_std={le["exp"][0]:.3f} (n={le["exp"][1]})')

# lag window 数の確認
print('\n  lag 分布 (D seed0):', dict(load('D', 0)[0].lag_since_input.value_counts().sort_index()))

# ---- 4. 判定 ----
print('\n=== 4. 判定材料 ===')
ca = contrast('C', 'A'); de = contrast('D', 'E')
print(f'  経験単独 C−A: |Δexc|={ca["abs_diff"]:.3f}, 符号一致={ca["sign_agree"]}')
print(f'  cid対応 D−E: |Δexc|={de["abs_diff"]:.3f}, 符号一致={de["sign_agree"]}')
print(f'  → 経験が本物の条件: C−A と D−E が非ゼロ・seed 符号一致・lag2+ で出る')
print(f'  → slight: 全 cond θ_div=False, Δlinks<±5%, Δalive<±10% を上表で確認')
