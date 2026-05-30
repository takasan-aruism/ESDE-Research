#!/usr/bin/env python3
"""v1109b Step E — 検証 3: loop 区別 5 条件

#L65 兆候が loop の裏返しでないか:
- all (現状)
- non-self (A_t != A_{t+1} のみ)
- CID changed (cid_t != cid_{t+1} のみ)
- loop-excluded (stuck より前のみ)
- first-visit (各 event で初出 atom のみの遷移)
"""
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1108A = REPO / 'unified/v1108a/outputs/main'
V1109B = REPO / 'unified/v1109b/outputs/main'

START_ATOMS = {'COG.enlightenment', 'PRP.shallow', 'TIM.moment', 'PRP.deep',
                'ECO.withdraw', 'EXS.being', 'FND.timeless', 'FND.logic',
                'PER.see', 'ACT.make'}
END_ATOMS = {'ACT.stand', 'TIM.appear', 'CHG.grow'}


def compute_signs(events):
    """Step C/D と同じ計算"""
    start_count = Counter(); end_count = Counter(); paths = []
    for ev in events:
        atoms = ev['atoms']
        if not atoms: continue
        start = atoms[0]
        stuck_t = ev.get('stuck_t')
        end_idx = min(stuck_t if stuck_t is not None else len(atoms) - 1, len(atoms) - 1)
        end = atoms[end_idx]
        if start: start_count[start] += 1
        if end: end_count[end] += 1
        paths.append((start, end))
    start_match = sum(1 for a in start_count if a in START_ATOMS) / max(len(start_count), 1)
    end_match = sum(1 for a in end_count if a in END_ATOMS) / max(len(end_count), 1)

    pair_count = Counter(); atom_count = Counter()
    n_singles = 0; n_pairs = 0
    for ev in events:
        for a in ev['atoms']:
            if a: atom_count[a] += 1; n_singles += 1
        for t in range(len(ev['atoms']) - 1):
            a, b = ev['atoms'][t], ev['atoms'][t+1]
            if a and b: pair_count[(a, b)] += 1; n_pairs += 1
    npmi_strong = 0
    for (a, b), c in pair_count.items():
        if c < 5: continue
        p_ab = c / n_pairs if n_pairs else 0
        p_a = atom_count[a] / n_singles if n_singles else 0
        p_b = atom_count[b] / n_singles if n_singles else 0
        if p_a > 0 and p_b > 0 and p_ab > 0:
            pmi = np.log(p_ab / (p_a * p_b))
            npmi = pmi / -np.log(p_ab) if p_ab < 1 else 0
            if npmi > 0.5: npmi_strong += 1

    per_paths = [p for p in paths if p[0] == 'PER.see']
    per_to_tim = sum(1 for p in per_paths if p[1] == 'TIM.appear') / max(len(per_paths), 1)

    role_data = defaultdict(lambda: {'terminal': 0, 'transit': 0})
    for ev in events:
        atoms = ev['atoms']
        stuck_t = ev.get('stuck_t')
        if stuck_t is None: continue
        for t in range(len(atoms)):
            a = atoms[t]
            if a != 'ACT.stand': continue
            prev = atoms[t-1] if t > 0 else 'START'
            role = 'terminal' if t >= stuck_t else 'transit'
            role_data[prev][role] += 1
    rates = []
    for prev, c in role_data.items():
        total = c['terminal'] + c['transit']
        if total >= 5: rates.append(c['terminal'] / total)
    role_range = max(rates) - min(rates) if len(rates) >= 2 else 0

    return {
        'start_match_rate': start_match,
        'end_match_rate': end_match,
        'npmi_strong_pairs': npmi_strong,
        'per_to_tim_rate': per_to_tim,
        'role_switch_range': role_range,
        'n_events': len(events),
        'n_transitions': n_pairs,
    }


def main():
    print('=== v1109b Step E — 検証 3: loop 区別 5 条件 ===\n')
    import time
    t0 = time.time()

    hist = pd.read_parquet(V1108A / 'self_dialogue_with_atom_probs.parquet')
    results = {}

    # 1. all (現状)
    events_all = []
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn').reset_index(drop=True)
        events_all.append({
            'atoms': grp_sorted['atom_top1'].tolist(),
            'cids': grp_sorted['cid'].tolist(),
            'stuck_t': int(grp_sorted['stuck_at_turn'].iloc[0])
                if pd.notna(grp_sorted['stuck_at_turn'].iloc[0]) else None,
        })
    results['all'] = compute_signs(events_all)

    # 2. non-self (A_t != A_{t+1} のみ)
    events_nonself = []
    for ev in events_all:
        atoms = ev['atoms']
        new_atoms = [atoms[0]]
        for t in range(1, len(atoms)):
            if atoms[t] != atoms[t-1] or atoms[t] is None:
                new_atoms.append(atoms[t])
        events_nonself.append({'atoms': new_atoms, 'stuck_t': None})
    results['non_self'] = compute_signs(events_nonself)

    # 3. CID changed turns only
    events_cidchg = []
    for ev in events_all:
        atoms = ev['atoms']; cids = ev['cids']
        new_atoms = [atoms[0]]
        for t in range(1, len(atoms)):
            if cids[t] != cids[t-1]:
                new_atoms.append(atoms[t])
        events_cidchg.append({'atoms': new_atoms, 'stuck_t': None})
    results['cid_changed'] = compute_signs(events_cidchg)

    # 4. loop-excluded (stuck より前のみ)
    events_le = []
    for ev in events_all:
        atoms = ev['atoms']
        st = ev['stuck_t']
        if st is not None:
            events_le.append({'atoms': atoms[:st], 'stuck_t': None})
        else:
            events_le.append({'atoms': atoms, 'stuck_t': None})
    results['loop_excluded'] = compute_signs(events_le)

    # 5. first-visit only
    events_fv = []
    for ev in events_all:
        atoms = ev['atoms']
        seen = set(); new_atoms = []
        for a in atoms:
            if a not in seen:
                new_atoms.append(a)
                if a: seen.add(a)
        events_fv.append({'atoms': new_atoms, 'stuck_t': None})
    results['first_visit'] = compute_signs(events_fv)

    rows = []
    for cond, signs in results.items():
        for sign, val in signs.items():
            rows.append({'condition': cond, 'sign': sign, 'value': float(val)})
    df = pd.DataFrame(rows)
    df.to_parquet(V1109B / 'verification_3_loop.parquet', index=False)

    print('--- 各条件での #L65 兆候 ---')
    pivot = df.pivot(index='sign', columns='condition', values='value').round(4)
    print(pivot.to_string())

    # loop 除外で消えるかチェック
    print('\n--- loop 除外で消えるか? ---')
    signs_check = ['start_match_rate', 'end_match_rate', 'npmi_strong_pairs',
                     'per_to_tim_rate', 'role_switch_range']
    for s in signs_check:
        v_all = pivot.loc[s, 'all']
        v_ne = pivot.loc[s, 'non_self']
        v_cc = pivot.loc[s, 'cid_changed']
        v_le = pivot.loc[s, 'loop_excluded']
        v_fv = pivot.loc[s, 'first_visit']
        # 全部の loop 除外で v_all の 50% 以上維持 = 残る
        persists = all(v > 0.5 * v_all for v in [v_ne, v_cc, v_le, v_fv]) if v_all > 0 else False
        marker = '✓ loop 除外でも残る' if persists else '✗ loop 除外で減衰'
        print(f'  {s}: all={v_all:.3f}, non_self={v_ne:.3f}, cid_chg={v_cc:.3f}, '
              f'loop_excl={v_le:.3f}, first_visit={v_fv:.3f}  {marker}')

    print(f'\n=== Step E 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
