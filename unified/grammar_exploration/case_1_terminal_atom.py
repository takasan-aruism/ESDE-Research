#!/usr/bin/env python3
"""案 1: 終端 atom の特定 — 文法の終端記号候補を探る

v1108a 自己対話 681 events で stuck_at_turn の atom = 終端候補
通過 atom (途中で出現するが終端にならない) との差を見る
"""
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
OUT = REPO / 'unified/grammar_exploration'
OUT.mkdir(parents=True, exist_ok=True)


def main():
    hist = pd.read_parquet(REPO/'unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet')
    print(f'events: {hist[["seed","start_cid"]].drop_duplicates().shape[0]}')

    # 各 event の stuck 開始 turn の atom
    terminal_counts = Counter()
    transit_counts = Counter()
    n_events = 0
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp = grp.sort_values('turn').reset_index(drop=True)
        stuck = grp['stuck_at_turn'].iloc[0]
        n_events += 1
        if pd.notna(stuck):
            stuck_t = int(stuck)
            # 終端候補: stuck 後の atom (繰り返している atom)
            for i in range(stuck_t, len(grp)):
                a = grp.iloc[i]['atom_top1']
                if a is not None:
                    terminal_counts[a] += 1
            # 通過: stuck 前の atom
            for i in range(stuck_t):
                a = grp.iloc[i]['atom_top1']
                if a is not None:
                    transit_counts[a] += 1

    # atom 別の終端率 (terminal / (terminal + transit))
    all_atoms = set(terminal_counts) | set(transit_counts)
    rows = []
    for a in all_atoms:
        t = terminal_counts[a]
        p = transit_counts[a]
        total = t + p
        if total < 5:
            continue
        rows.append({
            'atom': a, 'category': a.split('.')[0],
            'terminal_count': t,
            'transit_count': p,
            'total': total,
            'terminal_rate': t / total,
        })
    df = pd.DataFrame(rows).sort_values('terminal_rate', ascending=False)
    df.to_parquet(OUT/'case_1_terminal_rates.parquet', index=False)

    print(f'\nn_events: {n_events}')
    print(f'unique atoms (≥5 出現): {len(df)}')

    print('\n--- 終端率高 (終端記号候補) top 15 ---')
    print(df.head(15).to_string(index=False))

    print('\n--- 終端率低 (非終端 = 通過記号候補) top 15 ---')
    print(df.tail(15).to_string(index=False))

    # 終端 vs 非終端の category 別傾向
    print('\n--- category 別 平均終端率 ---')
    cat_summary = df.groupby('category').agg(
        n_atoms=('atom', 'count'),
        terminal_rate_mean=('terminal_rate', 'mean'),
        total_obs=('total', 'sum'),
    ).round(4).sort_values('terminal_rate_mean', ascending=False)
    print(cat_summary.head(15).to_string())

    # 完全終端 (rate=1.0) と完全通過 (rate=0.0)
    extreme_terminal = (df['terminal_rate'] >= 0.95).sum()
    extreme_transit = (df['terminal_rate'] <= 0.05).sum()
    mixed = ((df['terminal_rate'] > 0.05) & (df['terminal_rate'] < 0.95)).sum()
    print(f'\n  完全終端 (≥0.95): {extreme_terminal}')
    print(f'  完全通過 (≤0.05): {extreme_transit}')
    print(f'  中間 (mixed): {mixed}')


if __name__ == '__main__':
    main()
