#!/usr/bin/env python3
"""(I) start-end 文法木の構築 — 10 start × 中間 × 3 end の経路を木構造化"""
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
OUT = REPO / 'unified/grammar_exploration'

START_ATOMS = {'COG.enlightenment', 'PRP.shallow', 'TIM.moment', 'PRP.deep',
                'ECO.withdraw', 'EXS.being', 'FND.timeless', 'FND.logic',
                'PER.see', 'ACT.make'}
END_ATOMS = {'ACT.stand', 'TIM.appear', 'CHG.grow'}


def main():
    hist = pd.read_parquet(REPO/'unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet')

    # 各 event の start → end 経路を抽出 (stuck 開始前まで)
    paths = []
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn').reset_index(drop=True)
        stuck = grp_sorted['stuck_at_turn'].iloc[0]
        atoms = grp_sorted['atom_top1'].tolist()
        start = atoms[0]
        if start not in START_ATOMS:
            continue
        # stuck 直前の atom が end (停まる直前)
        if pd.notna(stuck):
            stuck_t = int(stuck)
            end_idx = min(stuck_t, len(atoms) - 1)
        else:
            end_idx = len(atoms) - 1
        end = atoms[end_idx]
        if end not in END_ATOMS:
            continue
        # 中間 (start と end の間)
        middle = atoms[1:end_idx]
        paths.append({
            'start': start, 'end': end,
            'path': '|'.join(a if a else '' for a in middle),
            'path_length': len(middle),
            'middle_unique': len(set(a for a in middle if a)),
        })

    df = pd.DataFrame(paths)
    df.to_parquet(OUT/'I_grammar_paths.parquet', index=False)
    print(f'start → end 経路: {len(df):,} events')
    print(f'\nstart × end 組み合わせ集計:')
    se = df.groupby(['start', 'end']).size().unstack(fill_value=0)
    print(se.to_string())

    # 文法的 production rule: start → middle pattern → end
    print('\n--- production rule top 10 (start → end の経路パターン) ---')
    rules = df.groupby(['start', 'end']).agg(
        n=('path', 'count'),
        path_length_mean=('path_length', 'mean'),
        path_length_min=('path_length', 'min'),
        path_length_max=('path_length', 'max'),
        unique_paths=('path', lambda x: x.nunique()),
    ).reset_index().sort_values('n', ascending=False)
    print(rules.round(2).to_string(index=False))

    # 各 start から到達できる end 集合 (文法的接続性)
    print('\n--- start atom 別の到達 end 集合 ---')
    for start in sorted(START_ATOMS):
        sub = df[df['start'] == start]
        if len(sub) == 0:
            continue
        end_dist = sub['end'].value_counts(normalize=True).to_dict()
        print(f'  {start:25s} n={len(sub):4d} ends: {sorted(end_dist.items(), key=lambda x: -x[1])}')

    # 経路の意味的「中間 atom 頻出」
    print('\n--- 経路中間に頻出する atom (= 文法的 conjunction/operator 候補) ---')
    middle_count = Counter()
    for p in df['path']:
        for a in p.split('|'):
            if a:
                middle_count[a] += 1
    top_mid = sorted(middle_count.items(), key=lambda x: -x[1])[:10]
    for a, c in top_mid:
        print(f'  {a:30s} count={c}')


if __name__ == '__main__':
    main()
