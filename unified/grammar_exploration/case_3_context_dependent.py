#!/usr/bin/env python3
"""案 3: 文脈依存遷移検出 — 1 次マルコフを超えるか

P(A_{t+1} | A_t) (1 次マルコフ) vs P(A_{t+1} | A_t, A_{t-1}) (2 次)
2 つが有意に異なれば文脈依存性あり = 文法構造の萌芽
"""
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

REPO = Path('/home/takasan/esde/ESDE-Research')
OUT = REPO / 'unified/grammar_exploration'


def main():
    hist = pd.read_parquet(REPO/'unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet')

    # 各 event で (A_{t-1}, A_t, A_{t+1}) のトリプル
    triples = []
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp = grp.sort_values('turn').reset_index(drop=True)
        atoms = grp['atom_top1'].tolist()
        for t in range(1, len(atoms) - 1):
            if atoms[t-1] and atoms[t] and atoms[t+1]:
                triples.append((atoms[t-1], atoms[t], atoms[t+1]))
    print(f'triples (A_{{t-1}}, A_t, A_{{t+1}}): {len(triples):,}')

    # 1 次マルコフ: P(next | A_t)
    pair_next = defaultdict(Counter)
    for prev, cur, nxt in triples:
        pair_next[cur][nxt] += 1

    # 2 次: P(next | A_t, A_{t-1})
    triple_next = defaultdict(Counter)
    for prev, cur, nxt in triples:
        triple_next[(prev, cur)][nxt] += 1

    # 各 A_t について、異なる A_{t-1} で P(next | A_t, prev) が異なるか chi2 検定
    A_t_counts = Counter(cur for prev, cur, nxt in triples)
    qualifying = [a for a, c in A_t_counts.items() if c >= 30]
    print(f'A_t candidates (≥30 occurrences): {len(qualifying)}')

    results = []
    for A in qualifying:
        # この A_t を含むトリプル
        prev_groups = defaultdict(Counter)
        for prev, cur, nxt in triples:
            if cur == A:
                prev_groups[prev][nxt] += 1
        # ≥2 種類 prev が必要、各 prev で ≥10 obs
        valid_prevs = [p for p, c in prev_groups.items() if sum(c.values()) >= 10]
        if len(valid_prevs) < 2:
            continue
        # contingency table: prev × next
        all_next = set()
        for p in valid_prevs:
            all_next.update(prev_groups[p].keys())
        next_list = sorted(all_next)
        if len(next_list) < 2:
            continue
        contingency = []
        for p in valid_prevs:
            row = [prev_groups[p].get(n, 0) for n in next_list]
            contingency.append(row)
        contingency = np.array(contingency)
        try:
            chi2, pval, dof, _ = chi2_contingency(contingency)
            # 効果量 (Cramér's V)
            n = contingency.sum()
            v = np.sqrt(chi2 / (n * (min(contingency.shape) - 1))) if n > 0 else 0
            results.append({
                'A_t': A,
                'category': A.split('.')[0],
                'n_obs': int(contingency.sum()),
                'n_prev_groups': len(valid_prevs),
                'n_next_atoms': len(next_list),
                'chi2': float(chi2),
                'p_value': float(pval),
                'cramers_v': float(v),
                'context_dependent': pval < 0.001 and v > 0.2,
            })
        except Exception:
            continue

    df = pd.DataFrame(results).sort_values('cramers_v', ascending=False)
    df.to_parquet(OUT/'case_3_context_dependent.parquet', index=False)

    print(f'\nA_t tested: {len(df)}')
    n_dep = df['context_dependent'].sum()
    print(f'context-dependent (p<0.001 AND Cramér V > 0.2): {n_dep}/{len(df)} ({n_dep/len(df)*100:.1f}%)')

    print('\n--- 文脈依存性 top 15 (Cramér V 順) ---')
    print(df.head(15)[['A_t', 'n_obs', 'n_prev_groups', 'n_next_atoms',
                          'p_value', 'cramers_v', 'context_dependent']
                        ].round(4).to_string(index=False))

    print('\n--- 文脈非依存 (1 次マルコフで足りる) top 10 ---')
    print(df.tail(10)[['A_t', 'n_obs', 'cramers_v', 'p_value']].round(4).to_string(index=False))

    # 全体集約
    print('\n--- 全体集約 ---')
    print(f'  Cramér V mean: {df["cramers_v"].mean():.4f}, median: {df["cramers_v"].median():.4f}')
    print(f'  p_value < 0.001 比率: {(df["p_value"] < 0.001).mean()*100:.1f}%')


if __name__ == '__main__':
    main()
