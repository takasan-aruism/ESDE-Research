#!/usr/bin/env python3
"""v12 M5 — 生存(survival)で測り直す (Taka: exc はカオス支配、test を疑う)

A/B トレースで判明: 介入は「どの cid が生き延びるか」を変える(CID26 は Base で win6 死亡、
Atomset で win16 生存)。exc 同cid照合はこの生存分岐を捨てていた。
生存=構造的・安定 metric で測り直す。confound (cid_vec に lifespan 軸が在る→循環) を点検。
"""
import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
R = 'unified/v12_atomset/run_m5_atom'; S = [0, 1, 2]


def rec(tag, cond, s): return pd.read_parquet(f'{R}/{tag}/{cond}/seed{s}/records.parquet')
def life(df):
    return df.groupby('cid').agg(life=('window', 'nunique'), last=('window', 'max'),
                                 ar=('atom_rate', 'max'), applied=('applied', 'max'),
                                 atom=('atom', 'first'))


print('=== 生存で測り直し (確認: 介入は生存を変えるか / 文化と cid 特異か) ===\n')

print('(1) 介入は生存を実際に変えたか (A vs C 同seed fork、cid 数)')
for tag in ['torque_st1', 'torque_st3']:
    tot_chg = 0; tot = 0
    for s in S:
        a = life(rec('torque_st1', 'A', s)); c = life(rec(tag, 'C', s))
        com = a.index.intersection(c.index)
        dl = c.loc[com, 'life'] - a.loc[com, 'life']
        tot_chg += (dl != 0).sum(); tot += len(com)
    print(f'  {tag}: 生存が変わった cid = {tot_chg}/{tot} ({100*tot_chg/tot:.0f}%)')

print('\n(2) cid 特異性: Δlife_C と Δlife_F が同じ cid を動かすか')
print('    corr(Δlife_C, Δlife_F) 低 → real と shuffle で違う cid が動く = pairing が効く(cid 特異)')
print('    高 → どの割当でも同じ cid が動く = 一般的摂動(cid 特異でない)')
for tag, ftag in [('torque_st1', 'torque_st1'), ('torque_st3', 'torque_st3')]:
    rs = []
    for s in S:
        a = life(rec('torque_st1', 'A', s)); c = life(rec(tag, 'C', s)); f = life(rec(ftag, 'F', s))
        com = a.index.intersection(c.index).intersection(f.index)
        dlc = c.loc[com, 'life'] - a.loc[com, 'life']
        dlf = f.loc[com, 'life'] - a.loc[com, 'life']
        if len(com) > 3 and dlc.std() > 0 and dlf.std() > 0:
            rs.append(np.corrcoef(dlc, dlf)[0, 1])
    print(f'  {tag}: corr(Δlife_C, Δlife_F) = {np.nanmean(rs):+.3f}')

print('\n(3) confound 点検: 文化(atom_rate)は lifespan 軸を含む→循環の疑い')
print('    対策: applied(torque_factor、効いた係数) と Δlife の corr を C/F で比較')
print('    C で正 かつ F で消える/弱る → 効いた文化が cid 特異に生存を変えた(本物)')
for tag in ['torque_st1', 'torque_st3']:
    rc = []; rf = []
    for s in S:
        a = life(rec('torque_st1', 'A', s))
        for cond, acc in [('C', rc), ('F', rf)]:
            x = life(rec(tag, cond, s)); com = a.index.intersection(x.index)
            dl = x.loc[com, 'life'] - a.loc[com, 'life']; ap = x.loc[com, 'applied'] - 1.0
            m = ap.abs() > 1e-6
            if m.sum() > 3 and ap[m].std() > 0 and dl[m].std() > 0:
                acc.append(np.corrcoef(ap[m], dl[m])[0, 1])
    print(f'  {tag}: corr(applied係数, Δlife) C(real)={np.nanmean(rc):+.3f}  F(shuffle)={np.nanmean(rf):+.3f}')

print('\n(4) 生存分布 A vs C vs F (平均 lifespan、最終生存数)')
for tag, cond in [('torque_st1', 'A'), ('torque_st1', 'C'), ('torque_st1', 'F'),
                  ('torque_st3', 'C'), ('torque_st3', 'F')]:
    ml = []; fin = []; nb = []
    for s in S:
        g = life(rec(tag, cond, s)); ml.append(g.life.mean())
        fin.append(int((g.last >= 15).sum())); nb.append(len(g))
    print(f'  {tag}/{cond}: 平均lifespan={np.mean(ml):.2f}  最終生存cid={np.mean(fin):.1f}  総cid={np.mean(nb):.0f}')

print('\n判定: (1)生存が変わる=効いてる (2)corr(ΔlC,ΔlF)低=cid特異 (3)applied corr C>F=本物 (4)分布が違う')
