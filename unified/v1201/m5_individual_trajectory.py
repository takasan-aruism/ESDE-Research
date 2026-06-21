#!/usr/bin/env python3
"""v12 M5 — CID 個別軌跡を一個ずつ見る (Taka: 集約禁止、保存で止めない、個別を開く)
A: 同一CID の C(自分の経験で核drift) vs F(他人の) を時間軸で重ね、どの時期にどれだけ違うか
B: 物理層の既存多様性 vs Atom drift 幅 (Atom が物理に埋もれてるか届いてるか の切り分け)
"""
import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
R = 'unified/v1201/run_m5_core_long'; S = range(8); WMAX = 51
def rec(cond, s): return pd.read_parquet(f'{R}/core_st1/{cond}/seed{s}/records.parquet')

print('=== A. CID 個別軌跡: 同一CID C vs F を時間軸で (集約せず一個ずつ) ===')
# 核drift が大きい CID を代表に (両条件に居る n_core=2)
cands = []
for s in S:
    c = rec('C', s); f = rec('F', s)
    cc = c[c.n_core == 2].groupby('cid').agg(dr=('atom_rate', 'max'), life=('window', 'nunique'))
    ff = set(f[f.n_core == 2].cid)
    for cid in cc.index:
        if cid in ff and cc.loc[cid, 'dr'] > 0.2 and cc.loc[cid, 'life'] >= 8:
            cands.append((s, cid, cc.loc[cid, 'dr']))
cands.sort(key=lambda x: -x[2])
print(f'  代表候補 (drift>0.2, life>=8, 両条件): {len(cands)}個。上位4個の軌跡:\n')
for s, cid, _ in cands[:4]:
    c = rec('C', s); f = rec('F', s)
    gc = {r.window: r for r in c[c.cid == cid].sort_values('window').itertuples()}
    gf = {r.window: r for r in f[f.cid == cid].sort_values('window').itertuples()}
    wins = sorted(set(gc) | set(gf))
    # 分岐点 = drift が C で初めて動いた window
    onset = next((w for w in wins if gc.get(w) and gc[w].atom_rate > 0.05), None)
    print(f'  --- seed{s} CID{cid} (drift onset=win{onset}) ---')
    print(f'    {"win":>3s}|{"driftC":>7s}{"driftF":>7s}|{"excC":>6s}{"excF":>6s}|{"degC":>4s}{"degF":>4s}|{"npC":>3s}{"npF":>3s}|aliv')
    for w in wins:
        rc = gc.get(w); rf = gf.get(w); al = ('C' if rc else '.') + ('F' if rf else '.')
        mark = ' <' if (rc and rf and abs(rc.exc - rf.exc) > 30) else ''
        print(f'    {w:>3d}|{rc.atom_rate if rc else 0:>7.3f}{rf.atom_rate if rf else 0:>7.3f}|'
              f'{rc.exc if rc else 0:>6.0f}{rf.exc if rf else 0:>6.0f}|{rc.degree if rc else 0:>4.0f}{rf.degree if rf else 0:>4.0f}|'
              f'{rc.n_partner_cids if rc else 0:>3.0f}{rf.n_partner_cids if rf else 0:>3.0f}|{al}{mark}')
    print()

print('=== B. 物理層の既存多様性 vs Atom drift 幅 (埋もれてるか届いてるか) ===')
# (i) baseline A の CID 間多様性 (既にある多様性 = 物理由来)
ex = []; dg = []; npr = []
for s in S:
    a = rec('A', s)
    g = a.groupby('cid').agg(e=('exc', 'mean'), d=('degree', 'mean'), n=('n_partner_cids', 'mean'))
    ex += g.e.tolist(); dg += g.d.tolist(); npr += g.n.tolist()
print(f'  (i) baseline A の CID 間分散 (既存多様性): exc std={np.std(ex):.1f}, degree std={np.std(dg):.2f}, n_partner std={np.std(npr):.2f}')
# (ii) Atom 効果: 同一CID の C vs F でどれだけ exc が変わるか (= Atom drift が動かす量)
dex = []; drifts = []
for s in S:
    c = rec('C', s); f = rec('F', s)
    ce = c[c.n_core == 2].groupby('cid').agg(e=('exc', 'mean'), dr=('atom_rate', 'max'))
    fe = f[f.n_core == 2].groupby('cid').exc.mean()
    com = ce.index.intersection(fe.index)
    for cid in com:
        if ce.loc[cid, 'dr'] > 0.1:
            dex.append(abs(ce.loc[cid, 'e'] - fe[cid])); drifts.append(ce.loc[cid, 'dr'])
print(f'  (ii) Atom 効果 (drift>0.1 の同一CID |exc_C - exc_F|): mean={np.mean(dex):.1f}, median={np.median(dex):.1f}, max={np.max(dex):.1f}')
print(f'  (iii) 核 drift 幅 (phase 移動 rad): mean={np.mean(drifts):.3f}, max={np.max(drifts):.3f} (MAX_DRIFT=0.5)')
print()
print(f'  ★切り分け: Atom効果(同一CID exc差 mean {np.mean(dex):.1f}) vs 既存多様性(CID間 exc std {np.std(ex):.1f})')
ratio = np.mean(dex) / max(np.std(ex), 1e-9)
print(f'    比 = {ratio:.2f}  → <<1 なら Atom は物理に埋もれてる / ~1 なら届いてる')
