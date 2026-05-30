#!/usr/bin/env python3
"""(II) 役割切替 atom の規則化 — ACT.stand 等の prev → role mapping を厳密化"""
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
OUT = REPO / 'unified/grammar_exploration'

TARGETS = ['ACT.stand', 'TIM.appear', 'CHG.grow', 'CHG.begin', 'PER.see']


def main():
    hist = pd.read_parquet(REPO/'unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet')

    rules = []
    for target in TARGETS:
        observations = []
        for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
            grp_sorted = grp.sort_values('turn').reset_index(drop=True)
            stuck = grp_sorted['stuck_at_turn'].iloc[0]
            if pd.isna(stuck): continue
            stuck_t = int(stuck)
            atoms = grp_sorted['atom_top1'].tolist()
            for t in range(len(atoms)):
                if atoms[t] != target:
                    continue
                prev = atoms[t-1] if t > 0 else 'START'
                role = 'terminal' if t >= stuck_t else 'transit'
                observations.append({'target': target, 'prev': prev, 'role': role})

        odf = pd.DataFrame(observations)
        if len(odf) == 0: continue
        # prev × role の分布
        cross = odf.groupby(['prev', 'role']).size().unstack(fill_value=0)
        cross['total'] = cross.sum(axis=1)
        cross = cross[cross['total'] >= 5]
        if 'terminal' in cross.columns and 'transit' in cross.columns:
            cross['terminal_rate'] = cross['terminal'] / cross['total']
            # 厳密な切替 rule: prev によって rate が明確に分かれる
            for prev_val, row in cross.iterrows():
                # rule_type: prev が terminal_rate を強く決める
                if row['terminal_rate'] >= 0.7:
                    rule_type = 'STRONG_TERMINAL'
                elif row['terminal_rate'] <= 0.3:
                    rule_type = 'STRONG_TRANSIT'
                else:
                    rule_type = 'MIXED'
                rules.append({
                    'target': target,
                    'prev': prev_val,
                    'n_total': int(row['total']),
                    'terminal_rate': float(row['terminal_rate']),
                    'rule_type': rule_type,
                })

    rdf = pd.DataFrame(rules).sort_values(['target', 'terminal_rate'], ascending=[True, False])
    rdf.to_parquet(OUT/'II_role_rules.parquet', index=False)

    print(f'役割切替ルール (5+ obs):  {len(rdf)}')
    print(f'\nrule_type 分布:')
    print(rdf['rule_type'].value_counts().to_string())

    print('\n--- 役割切替ルール詳細 ---')
    for target in TARGETS:
        sub = rdf[rdf['target'] == target]
        if len(sub) == 0:
            continue
        n_strong_term = (sub['rule_type'] == 'STRONG_TERMINAL').sum()
        n_strong_trans = (sub['rule_type'] == 'STRONG_TRANSIT').sum()
        n_mixed = (sub['rule_type'] == 'MIXED').sum()
        print(f'\n  {target}:')
        print(f'    STRONG_TERMINAL: {n_strong_term} prev')
        print(f'    STRONG_TRANSIT: {n_strong_trans} prev')
        print(f'    MIXED: {n_mixed} prev')
        if n_strong_trans > 0:
            print(f'    → 非終端化 prev (transit): '
                  f'{sub[sub["rule_type"]=="STRONG_TRANSIT"]["prev"].tolist()[:5]}')

    # 全体: 役割が明確に決まる prev の数
    strong_pct = (rdf['rule_type'] != 'MIXED').mean()
    print(f'\n  全体: 明確 (STRONG_*) 比率 {strong_pct*100:.1f}%')
    print(f'  → 役割が prev で決まる文法的規則性 = {strong_pct*100:.1f}%')


if __name__ == '__main__':
    main()
