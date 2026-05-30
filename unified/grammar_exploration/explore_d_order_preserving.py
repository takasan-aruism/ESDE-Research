#!/usr/bin/env python3
"""探索 (d): 順序情報を保つ集計

「順序考慮で 6 ペア、非順序で 0 ペア」の差を作っている要因を探る。
順序考慮の PMI と非順序 PMI の差を取り、最大の差が出るペアを見る。
「順序があると現れる文法性」を可視化。
"""
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
OUT = REPO / 'unified/grammar_exploration'


def main():
    hist = pd.read_parquet(REPO/'unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet')

    # 順序考慮 (forward)
    forward_count = Counter()
    backward_count = Counter()
    single_count = Counter()
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        atoms = grp.sort_values('turn')['atom_top1'].tolist()
        for a in atoms:
            if a:
                single_count[a] += 1
        for t in range(len(atoms) - 1):
            if atoms[t] and atoms[t+1]:
                forward_count[(atoms[t], atoms[t+1])] += 1

    n_singles = sum(single_count.values())
    n_pairs = sum(forward_count.values())

    # 順序ペア (A→B) の正反対 (B→A) との比較
    print('--- 順序非対称性 (A→B vs B→A) ---')
    rows = []
    seen = set()
    for (a, b), c_ab in forward_count.items():
        if (b, a) in seen or a == b:
            continue
        seen.add((a, b))
        c_ba = forward_count.get((b, a), 0)
        if c_ab < 5 and c_ba < 5:
            continue
        total = c_ab + c_ba
        # 順序非対称性指標: |c_ab - c_ba| / (c_ab + c_ba)
        asym = abs(c_ab - c_ba) / total if total > 0 else 0
        rows.append({
            'pair': f'{a} <=> {b}',
            'a': a, 'b': b,
            'a_to_b': c_ab,
            'b_to_a': c_ba,
            'total': total,
            'asymmetry': asym,
            'direction': 'a→b' if c_ab > c_ba else 'b→a',
        })
    df = pd.DataFrame(rows).sort_values(['asymmetry', 'total'], ascending=[False, False])
    df.to_parquet(OUT/'d_order_asymmetry.parquet', index=False)

    print(f'\n  pairs: {len(df):,}')
    print(f'\n--- 強い順序非対称性 top 20 (asymmetry > 0.5 AND total >= 5) ---')
    strong = df[(df['asymmetry'] > 0.5) & (df['total'] >= 5)].head(20)
    print(strong[['a', 'b', 'a_to_b', 'b_to_a', 'total', 'asymmetry', 'direction']
                ].to_string(index=False))

    # 「順序非対称性」の意味的特徴: cat 別集計
    print('\n--- category × category 別の順序非対称性 ---')
    strong['cat_a'] = strong['a'].str.split('.').str[0]
    strong['cat_b'] = strong['b'].str.split('.').str[0]
    cat_pair = strong.groupby(['cat_a', 'cat_b']).size().reset_index(name='n_pairs').sort_values('n_pairs', ascending=False)
    print(cat_pair.head(15).to_string(index=False))

    # 順序情報を保つために重要な「位置」: turn 0 と turn N の atom 分布の差
    print('\n--- turn 位置別 atom 分布 (順序情報の現れ) ---')
    pos_atoms = {'turn_0': Counter(), 'turn_mid': Counter(), 'turn_end': Counter()}
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        atoms = grp.sort_values('turn')['atom_top1'].tolist()
        n = len(atoms)
        if atoms[0]:
            pos_atoms['turn_0'][atoms[0]] += 1
        mid = n // 2
        if atoms[mid]:
            pos_atoms['turn_mid'][atoms[mid]] += 1
        if atoms[-1]:
            pos_atoms['turn_end'][atoms[-1]] += 1

    rows = []
    all_pos_atoms = set()
    for pos, c in pos_atoms.items():
        all_pos_atoms.update(c.keys())
    for a in all_pos_atoms:
        rows.append({
            'atom': a,
            'cat': a.split('.')[0],
            'count_turn_0': pos_atoms['turn_0'].get(a, 0),
            'count_turn_mid': pos_atoms['turn_mid'].get(a, 0),
            'count_turn_end': pos_atoms['turn_end'].get(a, 0),
        })
    pdf = pd.DataFrame(rows)
    pdf['total'] = pdf['count_turn_0'] + pdf['count_turn_mid'] + pdf['count_turn_end']
    pdf = pdf[pdf['total'] >= 10]
    # 位置別の出現率
    for col in ['count_turn_0', 'count_turn_mid', 'count_turn_end']:
        pdf[col + '_pct'] = pdf[col] / pdf['total']
    pdf.to_parquet(OUT/'d_position_distribution.parquet', index=False)

    # turn_0 で多い (start atom 候補)
    print('\n  turn 0 (start) 偏重 atom top 10:')
    pdf_sorted = pdf.sort_values('count_turn_0_pct', ascending=False)
    for _, r in pdf_sorted.head(10).iterrows():
        print(f'    {r["atom"]:25s} 0/mid/end = '
              f'{r["count_turn_0_pct"]:.2f}/{r["count_turn_mid_pct"]:.2f}/{r["count_turn_end_pct"]:.2f}')

    print('\n  turn end (final) 偏重 atom top 10:')
    for _, r in pdf.sort_values('count_turn_end_pct', ascending=False).head(10).iterrows():
        print(f'    {r["atom"]:25s} 0/mid/end = '
              f'{r["count_turn_0_pct"]:.2f}/{r["count_turn_mid_pct"]:.2f}/{r["count_turn_end_pct"]:.2f}')

    # 結論: 順序情報を保存するなら「位置別 atom 分布」が文法的役割を示す
    print(f'\n  atoms with strong position preference (max_pct > 0.6): '
          f'{((pdf[["count_turn_0_pct","count_turn_mid_pct","count_turn_end_pct"]].max(axis=1)) > 0.6).sum()}')


if __name__ == '__main__':
    main()
