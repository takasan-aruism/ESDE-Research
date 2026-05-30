#!/usr/bin/env python3
"""探索 (a): 連鎖の探索 — 高 PMI ペアから 3 連鎖 4 連鎖を辿る

「FND.logic → ECO.withdraw」のような高 PMI ペアを起点に、
A → B → C の 3 連鎖、A → B → C → D の 4 連鎖を集計。
文法的フレーズ候補を抽出。
"""
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
OUT = REPO / 'unified/grammar_exploration'


def main():
    hist = pd.read_parquet(REPO/'unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet')

    # 3 連鎖 (A, B, C)
    triple_count = Counter()
    pair_count = Counter()
    single_count = Counter()
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        atoms = grp.sort_values('turn')['atom_top1'].tolist()
        for t in range(len(atoms)):
            if atoms[t]:
                single_count[atoms[t]] += 1
        for t in range(len(atoms) - 1):
            if atoms[t] and atoms[t+1]:
                pair_count[(atoms[t], atoms[t+1])] += 1
        for t in range(len(atoms) - 2):
            if atoms[t] and atoms[t+1] and atoms[t+2]:
                triple_count[(atoms[t], atoms[t+1], atoms[t+2])] += 1

    n_singles = sum(single_count.values())
    n_pairs = sum(pair_count.values())
    n_triples = sum(triple_count.values())
    print(f'singles: {n_singles:,}, pairs: {n_pairs:,}, triples: {n_triples:,}')

    # 3 連鎖の expected vs observed (独立仮定)
    rows = []
    for (a, b, c), n_abc in triple_count.items():
        if n_abc < 5:
            continue
        p_a = single_count[a] / n_singles
        p_b = single_count[b] / n_singles
        p_c = single_count[c] / n_singles
        # 1 次マルコフ predict: P(a) × P(b|a) × P(c|b)
        ab = pair_count[(a, b)] / n_pairs
        bc = pair_count[(b, c)] / n_pairs
        # expected = P(a→b) × P(b→c)
        if pair_count[(a, b)] > 0 and pair_count[(b, c)] > 0:
            p_b_given_a = pair_count[(a, b)] / single_count[a]
            p_c_given_b = pair_count[(b, c)] / single_count[b]
            markov_expected = p_b_given_a * p_c_given_b * single_count[a]
        else:
            markov_expected = 0
        # 観察 / マルコフ期待
        ratio = n_abc / markov_expected if markov_expected > 0 else float('inf')
        rows.append({
            'a': a, 'b': b, 'c': c,
            'observed': n_abc,
            'markov_expected': markov_expected,
            'log_lift': float(np.log(ratio)) if ratio > 0 and not np.isinf(ratio) else 0,
            'cat_a': a.split('.')[0],
            'cat_b': b.split('.')[0],
            'cat_c': c.split('.')[0],
        })
    df3 = pd.DataFrame(rows).sort_values('log_lift', ascending=False)
    df3.to_parquet(OUT/'a_triples_lift.parquet', index=False)

    print(f'\n3 連鎖 (≥5 obs): {len(df3):,}')
    print('\n--- マルコフを超える 3 連鎖 top 20 (log_lift 順) ---')
    print(df3.head(20)[['a', 'b', 'c', 'observed', 'markov_expected', 'log_lift']
                          ].round(2).to_string(index=False))

    # 高 PMI ペアからの連鎖
    print('\n--- 高 PMI ペア起点の連鎖 ---')
    high_pmi_pairs = [
        ('FND.logic', 'ECO.withdraw'),
        ('COG.learn', 'TIM.moment'),
        ('FND.logic', 'COG.learn'),
        ('CHG.grow', 'CHG.begin'),
        ('CHG.begin', 'CHG.grow'),
    ]
    for (a, b) in high_pmi_pairs:
        print(f'\n  {a} → {b} →...:')
        following = df3[(df3['a']==a) & (df3['b']==b)].sort_values('observed', ascending=False).head(5)
        if len(following) > 0:
            for _, r in following.iterrows():
                print(f'    → {r["c"]:25s} obs={int(r["observed"])} markov={r["markov_expected"]:.1f} lift={r["log_lift"]:+.2f}')
        else:
            print(f'    (5+ 観測の続きなし)')

    # マルコフ超え (lift > 1.0) と マルコフ通り (lift ≈ 0) の比較
    print(f'\n  log_lift > 1.0 (マルコフ超え): {(df3["log_lift"] > 1.0).sum()}')
    print(f'  log_lift > 2.0: {(df3["log_lift"] > 2.0).sum()}')
    print(f'  log_lift < -1.0 (マルコフ未満): {(df3["log_lift"] < -1.0).sum()}')

    # 4 連鎖も
    print('\n4 連鎖 (A→B→C→D)')
    quad_count = Counter()
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        atoms = grp.sort_values('turn')['atom_top1'].tolist()
        for t in range(len(atoms) - 3):
            if atoms[t] and atoms[t+1] and atoms[t+2] and atoms[t+3]:
                quad_count[tuple(atoms[t:t+4])] += 1
    print(f'  unique 4-chains: {len(quad_count):,}')
    print(f'  total 4-chains: {sum(quad_count.values()):,}')
    print(f'  4-chains with ≥5 obs: {sum(1 for c in quad_count.values() if c >= 5)}')
    top4 = sorted(quad_count.items(), key=lambda x: -x[1])[:15]
    print('\n  --- 高頻度 4 連鎖 top 15 ---')
    for q, c in top4:
        print(f'    {c:4d} : {q[0]:18s} → {q[1]:18s} → {q[2]:18s} → {q[3]:18s}')


if __name__ == '__main__':
    main()
