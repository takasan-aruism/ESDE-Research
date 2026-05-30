#!/usr/bin/env python3
"""探索 (c): 文脈依存 atom の深掘り

案 3 で文脈依存判定された ACT.stand / TIM.appear / CHG.grow について、
- 直前 atom 別に「次に何が来るか」のパターン
- 周囲の意味的文脈
- 役割の切替方
を詳細追跡。
"""
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
OUT = REPO / 'unified/grammar_exploration'

TARGET_ATOMS = ['ACT.stand', 'TIM.appear', 'CHG.grow']


def main():
    hist = pd.read_parquet(REPO/'unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet')

    # 各 target atom の周囲 (prev, target, next) を全部集める
    print(f'文脈依存 atom 詳細: {TARGET_ATOMS}\n')

    results = []
    for target in TARGET_ATOMS:
        print(f'\n=== {target} ===')
        # (prev → target → next) の分布
        triples = []
        for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
            atoms = grp.sort_values('turn')['atom_top1'].tolist()
            for t in range(1, len(atoms) - 1):
                if atoms[t] == target:
                    triples.append({
                        'prev': atoms[t-1], 'cur': atoms[t], 'next': atoms[t+1],
                    })
        tdf = pd.DataFrame(triples)
        print(f'  出現数: {len(tdf):,}')

        # prev 別に next の分布を見る
        for prev_val in tdf['prev'].value_counts().head(5).index:
            sub = tdf[tdf['prev'] == prev_val]
            next_dist = sub['next'].value_counts(normalize=True).head(3)
            print(f'\n  prev={prev_val} (n={len(sub)}):')
            for n, p in next_dist.items():
                print(f'    next={n:25s} p={p:.3f}')

        # next 別に prev を見る (逆向き)
        print(f'\n  ★ 「{target} → X」で X 別の prev 分布:')
        for next_val in tdf['next'].value_counts().head(3).index:
            sub = tdf[tdf['next'] == next_val]
            prev_dist = sub['prev'].value_counts(normalize=True).head(3)
            print(f'\n  next={next_val} (n={len(sub)}):')
            for p, freq in prev_dist.items():
                print(f'    prev={p:25s} freq={freq:.3f}')

        # 「prev=A の時の next 分布」と「prev=B の時の next 分布」が大きく違うペア
        prev_top5 = tdf['prev'].value_counts().head(5).index.tolist()
        print(f'\n  ★ prev 間で next 分布差が大きい組:')
        # 各 next について、どの prev で多く出るか
        next_by_prev = defaultdict(dict)
        for prev_val in prev_top5:
            sub = tdf[tdf['prev'] == prev_val]
            n_dist = sub['next'].value_counts(normalize=True)
            for n, p in n_dist.items():
                next_by_prev[n][prev_val] = p
        # range 大の next
        ranged = []
        for n, prev_probs in next_by_prev.items():
            if len(prev_probs) >= 2:
                vals = list(prev_probs.values())
                rng = max(vals) - min(vals)
                if rng > 0.20:
                    ranged.append((n, rng, prev_probs))
        ranged.sort(key=lambda x: -x[1])
        for n, rng, probs in ranged[:5]:
            print(f'    next={n} range={rng:.3f}: {dict(list(probs.items())[:3])}')

        results.append({'atom': target, 'n_obs': len(tdf),
                          'unique_prev': tdf['prev'].nunique(),
                          'unique_next': tdf['next'].nunique()})

    pd.DataFrame(results).to_parquet(OUT/'c_context_depth.parquet', index=False)


if __name__ == '__main__':
    main()
