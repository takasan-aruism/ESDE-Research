#!/usr/bin/env python3
"""v1302 (A) 懐疑再点検 — 「transfer r=0.62」を Code A の生 parquet から崩す read-only 検証。

問い(Taka): Code A は何を何と比較してこの統計を出したか。平均化の罠はないか。

確定: transfer r = n_core 層ごとの CID×CID 距離行列 2 枚の Mantel 相関。
  Dp = 親 (s_avg, r_core, conc) z標準化 3次元のペア距離
  Dc = 子 late署名6指標(seed平均してから)のペア距離
  「成立」= A の Mantel(0.62) ≫ canon の Mantel(0.13/0.01/0.03)

本スクリプトは engine を回さず cw_v1302_A_full_signatures.parquet だけを読む。
3つの検証で #CW7 トートロジー留保が「半ば」でなく「plb スカラを超えた残差はゼロ」であることを示す。
"""
import numpy as np, pandas as pd
from pathlib import Path
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr

HERE = Path(__file__).parent
SIG = ['n_labels', 'mean_size', 'std_size', 'share_gini', 'mean_age', 'lifecycle_events']


def _z(A):
    A = np.asarray(A, float)
    return (A - A.mean(0)) / (A.std(0) + 1e-9)


def _pd(M):
    return squareform(pdist(M, 'euclidean'))


def mantel_r(Dp, Dc, k=999, seed=20260623):
    rng = np.random.default_rng(seed)
    iu = np.triu_indices(Dp.shape[0], 1)
    a, b = Dp[iu], Dc[iu]
    r = float(np.corrcoef(a, b)[0, 1])
    n = Dp.shape[0]
    null = np.array([np.corrcoef(Dp[np.ix_(p, p)][iu], b)[0, 1]
                     for p in (rng.permutation(n) for _ in range(k))])
    return r, (np.sum(null >= r) + 1) / (k + 1)


def resid(y, x):
    X = np.column_stack([np.ones_like(x), x])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    return y - X @ b


def cid_avg(sub):
    return sub.groupby('cid').agg(
        **{f'late_{s}': (f'late_{s}', 'mean') for s in SIG},
        **{c: (c, 'first') for c in ['s_avg', 'r_core', 'conc', 'plb']}).reset_index()


def main():
    df = pd.read_parquet(HERE / 'cw_v1302_A_full_signatures.parquet')

    print('=== 検証1: 「3軸の継承」か「仕込んだ1スカラ(plb)」か ===')
    for nc in ['2', '4', '5']:
        g = cid_avg(df[(df.stratum == nc) & (df.cond == 'A')])
        if len(g) < 5:
            continue
        Dp = _pd(_z(np.column_stack([g.s_avg, g.r_core, g.conc])))
        Dc = _pd(_z(g[[f'late_{s}' for s in SIG]].values))
        Dplb = _pd(g[['plb']].values)
        r3, p3 = mantel_r(Dp, Dc)
        rplb, pplb = mantel_r(Dplb, Dc)
        iu = np.triu_indices(len(g), 1)
        rc = np.corrcoef(resid(Dc[iu], Dplb[iu]), resid(Dp[iu], Dplb[iu]))[0, 1]
        print(f'  n{nc} A | Mantel(3軸)={r3:.3f} p={p3:.3f} | Mantel(plbのみ)={rplb:.3f} p={pplb:.3f} '
              f'| plb除去後の3軸残差↔child残差 r={rc:+.3f}')
    for nc in ['2', '4', '5']:
        g = cid_avg(df[(df.stratum == nc) & (df.cond == 'canon')])
        Dp = _pd(_z(np.column_stack([g.s_avg, g.r_core, g.conc])))
        Dc = _pd(_z(g[[f'late_{s}' for s in SIG]].values))
        r3, p3 = mantel_r(Dp, Dc)
        print(f'  n{nc} canon | Mantel(3軸)={r3:.3f} p={p3:.3f}  (plb一定の対照)')

    print('\n=== 検証2: seed平均化が r を底上げしているか (n2 A) ===')
    sub = df[(df.stratum == '2') & (df.cond == 'A')]
    single = []
    for sd in sorted(sub.seed.unique()):
        g = sub[sub.seed == sd].set_index('cid')
        Dp = _pd(_z(np.column_stack([g.s_avg, g.r_core, g.conc])))
        Dc = _pd(_z(g[[f'late_{x}' for x in SIG]].values))
        single.append(mantel_r(Dp, Dc)[0])
    print(f'  単一seed r: {[round(x, 3) for x in single]}  中央値={np.median(single):.3f}')
    for k in [1, 2, 3, 5]:
        g = cid_avg(sub[sub.seed < k])
        Dp = _pd(_z(np.column_stack([g.s_avg, g.r_core, g.conc])))
        Dc = _pd(_z(g[[f'late_{s}' for s in SIG]].values))
        r, p = mantel_r(Dp, Dc)
        print(f'  {k}-seed平均 r={r:.3f} p={p:.3f}')

    print('\n=== 検証3: late署名は plb の機械的読み出しか (n2 A, CID平均, Spearman) ===')
    g = df[(df.stratum == '2') & (df.cond == 'A')].groupby('cid').agg(
        **{f'late_{s}': (f'late_{s}', 'mean') for s in SIG}, plb=('plb', 'first')).reset_index()
    for s in SIG:
        rho, p = spearmanr(g.plb, g[f'late_{s}'])
        print(f'  plb ↔ late_{s:18}: rho={rho:+.3f} p={p:.3g}')


if __name__ == '__main__':
    main()
