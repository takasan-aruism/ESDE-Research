#!/usr/bin/env python3
"""v1302 §1-2 — step-0 transfer のチャネル分解。既存 cw_step0 signatures の read-only 再解析（新規 child run なし・stdout のみ）。

【観察対象注釈ブロック / 同系・異系宣言】
- 同系内: step-0(親 seed0 CID 縮小子系)の既存出力を再解析するだけ。異系対応でない。
- 読=frozen: unified/v1301/cw_step0_signatures.parquet（step-0 が生成済の child 署名）。書込なし(stdout)。
- これは smoke でも実験 run でもない: child を1体も走らせない。既存の D_parent 行列から1チャネル抜いて Mantel を引き直すだけ。
- D_child は step-0 で全チャネル稼働下に得た署名で固定。ablate は D_parent 側(親記述子)を1つ抜く association 分解。
  ∴「K_sync の源 r_core を抜いても r 不変 → r_core 類似が署名類似を予測しない → K_sync チャネルは署名痕を残さなかった(幻)」と読む。共線は別途 corr で併記。
- 親 physics/inject/ledger/state 非書込。判定は置かない。
"""
import numpy as np, pandas as pd
from scipy.spatial.distance import pdist, squareform
REPO='/home/takasan/esde/ESDE-Research'
SIG=['n_labels','mean_size','std_size','share_gini','mean_age','lifecycle_events']
MANTEL_K=999

def zstd(A):
    A=np.asarray(A,float); return (A-A.mean(0))/(A.std(0)+1e-9)
def pdm(M):
    return squareform(pdist(M,'euclidean'))
def mantel(Dp,Dc,k,rng):
    iu=np.triu_indices(Dp.shape[0],1); a,b=Dp[iu],Dc[iu]
    r=float(np.corrcoef(a,b)[0,1]); n=Dp.shape[0]; null=np.empty(k)
    for i in range(k):
        p=rng.permutation(n); null[i]=np.corrcoef(Dp[np.ix_(p,p)][iu],b)[0,1]
    return r, float((np.sum(null>=r)+1)/(k+1))

d=pd.read_parquet(f'{REPO}/unified/v1301/cw_step0_signatures.parquet')

# 親記述子→チャネル: N<-b_gen / plb<-s_avg / K_sync<-r_core / theta<-phase_sig
def cols_for(g, drop=None):
    ph=g.phase_sig.values
    parts={'N':[g.b_gen.values],'plb':[g.s_avg.values],'Ksync':[g.r_core.values],
           'theta':[np.cos(ph),np.sin(ph)]}
    out=[]
    for ch,arrs in parts.items():
        if ch==drop: continue
        out+=arrs
    return np.column_stack(out)

for nc in [2,4,5]:
    real=d[(d.stratum==nc)&(d.control=='real')]
    g=real.groupby('cid').agg(**{s:(s,'mean') for s in SIG},
        **{c:(c,'first') for c in ['b_gen','s_avg','r_core','phase_sig']}).reset_index()
    if len(g)<5:
        print(f'n{nc}: cid={len(g)} Mantel 不能'); continue
    rng=np.random.default_rng(20260623)
    Dc=pdm(zstd(g[SIG].values))
    print(f'=== n{nc} (cid={len(g)}) チャネル ablate Mantel (D_child 固定) ===')
    # full 4ch
    rf,pf=mantel(pdm(zstd(cols_for(g))),Dc,MANTEL_K,rng)
    print(f'  full(N+plb+Ksync+theta): r={rf:.3f} p={pf:.3f}')
    for drop in ['N','plb','Ksync','theta']:
        rr,pp=mantel(pdm(zstd(cols_for(g,drop=drop))),Dc,MANTEL_K,rng)
        print(f'  −{drop:<6}: r={rr:.3f} p={pp:.3f}  (Δr={rr-rf:+.3f})')
    # 単独チャネル
    print('  -- 単独チャネル --')
    for only in ['N','plb','Ksync','theta']:
        keep=[c for c in ['N','plb','Ksync','theta'] if c!=only]
        M=cols_for(g, drop=None)
        # build single: drop all but 'only'
        ph=g.phase_sig.values
        single={'N':np.column_stack([g.b_gen]),'plb':np.column_stack([g.s_avg]),
                'Ksync':np.column_stack([g.r_core]),'theta':np.column_stack([np.cos(ph),np.sin(ph)])}[only]
        rs,ps=mantel(pdm(zstd(single)),Dc,MANTEL_K,rng)
        print(f'  only {only:<6}: r={rs:.3f} p={ps:.3f}')
    # 共線 (親記述子間 corr)
    cc=g[['b_gen','s_avg','r_core','phase_sig']].corr()
    print('  -- 親記述子間 corr (共線注意) --')
    print('   ', {f'{a}/{b}':round(float(cc.loc[a,b]),2) for a,b in [('b_gen','s_avg'),('b_gen','r_core'),('s_avg','r_core'),('r_core','phase_sig')]})
    print()
