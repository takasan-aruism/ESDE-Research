#!/usr/bin/env python3
"""v12 M5 — CID-Atomset 干渉の検査 (D−E が見えない原因の切り分け: 埋もれ vs 干渉)

Taka 指摘: 経験を CID の物理 state.E に直接書く現設計は、CID の物理(本来の作者)と
Atomset(経験)が同じ state.E を取り合う。D−E 不可視は (a)slight で埋もれ か
(b)演算的干渉で scramble か、切り分けずに over-drive へ行くべきでない。

検査: C(経験on,入力なし) vs A(baseline) 同 seed 決定論 fork。
"""
import pandas as pd, numpy as np
from pathlib import Path

ROOT = Path('/home/takasan/esde/ESDE-Research/unified/v1201/run_m5_substrate')
SEEDS = [0, 1, 2]


def main():
    print('=== CID-Atomset 干渉検査 (C vs A 同 seed fork) ===\n')
    # (a) 注入量 exp_E と 効果 |Δexc| の比例性 (比例=効く / ≤0=cid情報が効果に伝わらず scramble)
    print('(a) corr(exp_E 注入量, |Δexc| 効果) per-cid:')
    for s in SEEDS:
        a = pd.read_parquet(ROOT/f'A/seed{s}/records.parquet').groupby('cid').exc.mean()
        c = pd.read_parquet(ROOT/f'C/seed{s}/records.parquet')
        ce = c.groupby('cid').exc.mean(); ee = c.groupby('cid').exp_E.sum()
        common = a.index.intersection(ce.index)
        dexc = (ce[common]-a[common]).abs(); inj = ee[common]; mask = inj > 0
        if mask.sum() > 2:
            r = np.corrcoef(inj[mask], dexc[mask])[0, 1]
            print(f'  seed{s}: r={r:+.3f} (注入>0 cid={int(mask.sum())}, |Δexc|平均={dexc[mask].mean():.1f})')
    # (b) cap 吸収リスク: 経験圧 self_boost が活発 cid (exc_A 高) に集中するか
    print('\n(b) corr(self_boost 経験圧, exc_A 自然な活発さ) [正=cap吸収risk]:')
    for s in SEEDS:
        a = pd.read_parquet(ROOT/f'A/seed{s}/records.parquet').groupby('cid').exc.mean()
        c = pd.read_parquet(ROOT/f'C/seed{s}/records.parquet')
        sb = c.groupby('cid').self_boost.max()
        common = a.index.intersection(sb.index); mask = sb[common] > 0
        if mask.sum() > 2:
            r = np.corrcoef(sb[common][mask], a[common][mask])[0, 1]
            print(f'  seed{s}: r={r:+.3f} (boost>0 cid={int(mask.sum())})')
    # (c) C-A 乖離は育つ(効く・摂動大)か 飽和(吸収)か
    print('\n(c) |C-A| per-window 乖離 (育つ=摂動大で埋もれてない):')
    for s in SEEDS:
        a = pd.read_parquet(ROOT/f'A/seed{s}/records.parquet').groupby('window').exc.mean()
        c = pd.read_parquet(ROOT/f'C/seed{s}/records.parquet').groupby('window').exc.mean()
        w = sorted(set(a.index) & set(c.index))
        print(f'  seed{s}:', [f'{abs(c[x]-a[x]):.0f}' for x in w])
    # (2) per-Atom pooling: 1 atom が束ねる cid 数 (橋 input_E>0)
    print('\n(2) per-Atom pooling (橋 1 atom が束ねる cid 数 = 文化共有の規模):')
    for s in SEEDS:
        d = pd.read_parquet(ROOT/f'D/seed{s}/records.parquet')
        nhit = (d.groupby('cid').input_E.sum() > 0).sum()
        print(f'  seed{s}: input_E>0 cid={int(nhit)} (2 atom 入力 → ~{nhit} cid に到達)')
    print('\n判定: (c)摂動大かつ(a)効果が注入に非比例≤0 = 埋もれでなく cid 情報が物理に scramble')
    print('      = CID(物理) と Atomset(経験) が同じ state.E を取り合う干渉。over-drive では解けない。')


if __name__ == '__main__':
    main()
