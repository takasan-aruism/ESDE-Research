#!/usr/bin/env python3
"""v12 M5 core Long(tracking50) 観測 — 多レンズ個別軌跡 (Taka 測定哲学: 単一指標で分類しない)
観測は理解のため。型を軌跡から見つける。crown も「しぼんだ」も言わず、一側面と留保。"""
import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
R = 'unified/v1201/run_m5_core_long'; S = range(8); WMAX = 51
def rec(cond, s): return pd.read_parquet(f'{R}/core_st1/{cond}/seed{s}/records.parquet')


def feats(cond):
    rows = []
    for s in S:
        d = rec(cond, s); d = d[d.n_core == 2]
        for cid, g in d.groupby('cid'):
            g = g.sort_values('window'); dr = g.atom_rate.values; wins = g.window.values
            onset = int(wins[np.argmax(dr > 0.05)]) if (dr > 0.05).any() else -1
            rows.append(dict(seed=s, cid=int(cid), maxdrift=dr.max(), onset=onset,
                             survived=int(g.window.max() >= WMAX - 1), atom=g.atom.iloc[0]))
    return pd.DataFrame(rows)


fc = feats('C'); ff = feats('F')
print('=== Long(tracking50) n_core=2 観測: 軌跡の型 (単一指標でなく型) ===\n')
print('(A) 型分布: (核drift 有無) × (生存末まで) — real(C) vs shuffle(F)')
for name, f in [('C(real)  ', fc), ('F(shuffle)', ff)]:
    dr = f.maxdrift > 0.1
    print(f'  {name} n={len(f)}: drift有→生存{int((dr&(f.survived==1)).sum()):3d} drift有→死{int((dr&(f.survived==0)).sum()):3d} '
          f'drift無→生存{int((~dr&(f.survived==1)).sum()):3d} drift無→死{int((~dr&(f.survived==0)).sum()):3d}')
    if dr.sum() > 0:
        print(f'              drift有 生存率{100*f[dr].survived.mean():.0f}% / drift無 生存率{100*f[~dr].survived.mean():.0f}%')

print('\n(B) 個性化 vs 淘汰: 生存者(末まで)の多様性 (収束=淘汰, 多様=個性化)')
def diversity(cond):
    atoms = []; degs = []; nps = []
    for s in S:
        sur = rec(cond, s); sur = sur[sur.window >= WMAX - 1]
        for cid, g in sur.groupby('cid'):
            atoms.append(g.atom.iloc[0]); degs.append(g.degree.mean()); nps.append(g.n_partner_cids.mean())
    vc = pd.Series(atoms).value_counts(normalize=True); ent = float(-(vc * np.log2(vc)).sum())
    return len(atoms), ent, float(np.std(degs)), float(np.std(nps))
for cond in ['A', 'C', 'F']:
    n, ent, ds, nps = diversity(cond)
    print(f'  {cond}: 生存者={n}, atom entropy={ent:.2f}, degree spread={ds:.2f}, n_partner spread={nps:.2f}')

print('\n(C) 同一CID C vs F 分岐 (同seed、両条件、核drift後に運命分岐)')
tot = 0; div = 0; cdie = 0; csur = 0
for s in S:
    c = rec('C', s); f = rec('F', s)
    cc = c[c.n_core == 2].groupby('cid').agg(sv=('window', 'max'), dr=('atom_rate', 'max'))
    ff2 = f[f.n_core == 2].groupby('cid').agg(sv=('window', 'max'), dr=('atom_rate', 'max'))
    for cid in cc.index.intersection(ff2.index):
        if cc.loc[cid, 'dr'] > 0.1 or ff2.loc[cid, 'dr'] > 0.1:
            tot += 1
            cs = cc.loc[cid, 'sv'] >= WMAX - 1; fs = ff2.loc[cid, 'sv'] >= WMAX - 1
            if cs != fs: div += 1
            if (not cs) and fs: cdie += 1
            if cs and (not fs): csur += 1
print(f'  核drift 同一CID {tot}個中、C/Fで生存運命分岐 {div} ({100*div/max(tot,1):.0f}%)')
print(f'    C死&F生(自分の経験で死)={cdie}, C生&F死(自分の経験で生)={csur}')

# 軌跡データ保存 (Web Claude プロット用)
rows = []
for cond in ['C', 'F', 'A']:
    for s in S:
        d = rec(cond, s); d = d[d.n_core == 2]
        for r in d.itertuples():
            rows.append(dict(cond=cond, seed=s, cid=int(r.cid), window=int(r.window),
                             drift=float(r.atom_rate), exc=float(r.exc), degree=int(r.degree),
                             n_partner=int(r.n_partner_cids), atom=r.atom))
pd.DataFrame(rows).to_parquet('unified/v1201/traj_out/core_long_ncore2_trajectories.parquet')
print(f'\n  保存: traj_out/core_long_ncore2_trajectories.parquet ({len(rows)}行)')
