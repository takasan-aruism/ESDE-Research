#!/usr/bin/env python3
"""探索 (b): 中間 atom の役割切替

案 1 で発見した中間 11 atom (0.05 < terminal_rate < 0.95) について、
どの文脈で終端、どの文脈で非終端になるかを詳細追跡。
直前 atom (prev) と次 atom (next) を見て役割切替パターンを抽出。
"""
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
OUT = REPO / 'unified/grammar_exploration'


def main():
    # case 1 の中間 atom を取得
    df1 = pd.read_parquet(OUT/'case_1_terminal_rates.parquet')
    mid = df1[(df1['terminal_rate'] > 0.05) & (df1['terminal_rate'] < 0.95)]
    print(f'中間 atom: {len(mid)}')
    print(mid[['atom', 'terminal_rate']].round(3).to_string(index=False))
    mid_atoms = set(mid['atom'])

    hist = pd.read_parquet(REPO/'unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet')

    # 各 event で stuck 開始 turn を取得
    rows = []
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn').reset_index(drop=True)
        stuck = grp_sorted['stuck_at_turn'].iloc[0]
        atoms = grp_sorted['atom_top1'].tolist()
        if pd.isna(stuck):
            continue
        stuck_t = int(stuck)
        for t in range(len(atoms)):
            a = atoms[t]
            if a not in mid_atoms:
                continue
            prev = atoms[t-1] if t > 0 else None
            nxt = atoms[t+1] if t < len(atoms) - 1 else None
            is_terminal = t >= stuck_t
            rows.append({
                'atom': a,
                'prev': prev,
                'next': nxt,
                'is_terminal': is_terminal,
            })

    df = pd.DataFrame(rows)
    print(f'\n中間 atom 出現: {len(df):,}')

    # 各中間 atom について、prev 別の終端率
    print('\n--- 中間 atom × prev 別終端率 (役割切替) ---')
    for atom in sorted(mid_atoms):
        sub = df[df['atom'] == atom]
        if len(sub) < 20:
            continue
        prev_summary = sub.groupby('prev')['is_terminal'].agg(['mean', 'count']).reset_index()
        prev_summary = prev_summary[prev_summary['count'] >= 5].sort_values('mean', ascending=False)
        if len(prev_summary) < 2:
            continue
        # 終端率の variance
        rate_range = prev_summary['mean'].max() - prev_summary['mean'].min()
        if rate_range < 0.15:
            continue  # 役割切替が弱い
        print(f'\n  {atom} (total {len(sub)} obs, range {rate_range:.2f}):')
        for _, r in prev_summary.head(5).iterrows():
            tag = '終' if r['mean'] > 0.5 else '通'
            print(f'    prev={str(r["prev"]):28s} terminal_rate={r["mean"]:.3f} ({tag}) n={int(r["count"])}')

    # 上位「役割切替の強い」中間 atom 集計
    print('\n--- 役割切替の強さ (prev 別終端率 range) ---')
    switch_strength = []
    for atom in sorted(mid_atoms):
        sub = df[df['atom'] == atom]
        if len(sub) < 30:
            continue
        prev_summary = sub.groupby('prev')['is_terminal'].agg(['mean', 'count']).reset_index()
        prev_summary = prev_summary[prev_summary['count'] >= 5]
        if len(prev_summary) < 2:
            continue
        switch_strength.append({
            'atom': atom,
            'n_total': len(sub),
            'n_distinct_prev': len(prev_summary),
            'terminal_rate_range': float(prev_summary['mean'].max() - prev_summary['mean'].min()),
            'terminal_rate_std': float(prev_summary['mean'].std()),
        })
    ss_df = pd.DataFrame(switch_strength).sort_values('terminal_rate_range', ascending=False)
    ss_df.to_parquet(OUT/'b_role_switching.parquet', index=False)
    print(ss_df.to_string(index=False))

    # 結論: 文脈で終端/非終端が切り替わる atom = 文法的に重要候補
    strong_switchers = ss_df[ss_df['terminal_rate_range'] > 0.30]
    print(f'\n  強い役割切替 (range > 0.30): {len(strong_switchers)}')
    if len(strong_switchers) > 0:
        print(f'  → 文法的に「文脈で機能を変える」atom 候補: {strong_switchers["atom"].tolist()}')


if __name__ == '__main__':
    main()
