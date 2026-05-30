#!/usr/bin/env python3
"""(IV) 文脈依存性の全 atom 拡張 — 出現する全 atom で network 構築"""
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

REPO = Path('/home/takasan/esde/ESDE-Research')
OUT = REPO / 'unified/grammar_exploration'


def main():
    hist = pd.read_parquet(REPO/'unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet')

    triples = []
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        atoms = grp.sort_values('turn')['atom_top1'].tolist()
        for t in range(1, len(atoms) - 1):
            if atoms[t-1] and atoms[t] and atoms[t+1]:
                triples.append((atoms[t-1], atoms[t], atoms[t+1]))
    print(f'triples: {len(triples):,}')

    # 全 A_t について chi2 検定 (≥10 obs)
    cur_counts = Counter(cur for _, cur, _ in triples)
    qualifying = [a for a, c in cur_counts.items() if c >= 10]
    print(f'A_t candidates (≥10): {len(qualifying)}')

    results = []
    for A in qualifying:
        prev_groups = defaultdict(Counter)
        for prev, cur, nxt in triples:
            if cur == A:
                prev_groups[prev][nxt] += 1
        valid_prevs = [p for p, c in prev_groups.items() if sum(c.values()) >= 3]
        if len(valid_prevs) < 2:
            continue
        all_next = set()
        for p in valid_prevs:
            all_next.update(prev_groups[p].keys())
        next_list = sorted(all_next)
        if len(next_list) < 2:
            continue
        contingency = np.array([[prev_groups[p].get(n, 0) for n in next_list] for p in valid_prevs])
        try:
            chi2, pval, dof, _ = chi2_contingency(contingency)
            n = contingency.sum()
            v = np.sqrt(chi2 / (n * (min(contingency.shape) - 1))) if n > 0 else 0
            results.append({
                'A_t': A, 'category': A.split('.')[0],
                'n_obs': int(contingency.sum()),
                'n_prev_groups': len(valid_prevs),
                'chi2': float(chi2), 'p_value': float(pval),
                'cramers_v': float(v),
                'context_dependent_strict': pval < 0.001 and v > 0.2,
                'context_dependent_loose': pval < 0.05 and v > 0.1,
            })
        except Exception:
            continue

    df = pd.DataFrame(results).sort_values('cramers_v', ascending=False)
    df.to_parquet(OUT/'IV_full_context_dependent.parquet', index=False)

    print(f'\nA_t tested: {len(df)}')
    print(f'context-dependent STRICT (p<0.001 AND V>0.2): {df["context_dependent_strict"].sum()} '
          f'({df["context_dependent_strict"].mean()*100:.1f}%)')
    print(f'context-dependent LOOSE (p<0.05 AND V>0.1): {df["context_dependent_loose"].sum()} '
          f'({df["context_dependent_loose"].mean()*100:.1f}%)')

    print('\n--- 文脈依存性 STRICT 通過 atom ---')
    strict = df[df['context_dependent_strict']]
    print(strict[['A_t', 'n_obs', 'cramers_v', 'p_value']].round(4).to_string(index=False))

    print('\n--- category 別 文脈依存率 ---')
    cat = df.groupby('category').agg(
        n_atoms=('A_t', 'count'),
        strict_rate=('context_dependent_strict', 'mean'),
        loose_rate=('context_dependent_loose', 'mean'),
        v_mean=('cramers_v', 'mean'),
    ).round(4).sort_values('v_mean', ascending=False)
    print(cat.to_string())


if __name__ == '__main__':
    main()
