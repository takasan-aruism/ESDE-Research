#!/usr/bin/env python3
"""v1109b Step D — 検証 2: self-fulfilling 5 条件

top1 chain でだけ出る兆候か?
- top1 (現状)
- top2 (各 turn の atom_top2 を遷移先として使用)
- top3
- probability sampling (atom_top1-10 から prob で sampling)
- seed holdout (別 seed でも同じ構造)
"""
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1108A = REPO / 'unified/v1108a/outputs/main'
V1109B = REPO / 'unified/v1109b/outputs/main'

RNG_SEED = 42
ATOM_TOPK = 10

START_ATOMS = {'COG.enlightenment', 'PRP.shallow', 'TIM.moment', 'PRP.deep',
                'ECO.withdraw', 'EXS.being', 'FND.timeless', 'FND.logic',
                'PER.see', 'ACT.make'}
END_ATOMS = {'ACT.stand', 'TIM.appear', 'CHG.grow'}


def compute_signs(events):
    """Step C と同じ指標計算"""
    start_count = Counter()
    end_count = Counter()
    paths = []
    for ev in events:
        atoms = ev['atoms']
        if not atoms: continue
        start = atoms[0]
        stuck_t = ev.get('stuck_t')
        end_idx = (stuck_t if stuck_t is not None else len(atoms) - 1)
        end_idx = min(end_idx, len(atoms) - 1)
        end = atoms[end_idx]
        if start: start_count[start] += 1
        if end: end_count[end] += 1
        paths.append((start, end))
    start_match = sum(1 for a in start_count if a in START_ATOMS) / max(len(start_count), 1)
    end_match = sum(1 for a in end_count if a in END_ATOMS) / max(len(end_count), 1)

    pair_count = Counter()
    atom_count = Counter()
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
        if total >= 5:
            rates.append(c['terminal'] / total)
    role_range = max(rates) - min(rates) if len(rates) >= 2 else 0

    return {
        'start_match_rate': start_match,
        'end_match_rate': end_match,
        'npmi_strong_pairs': npmi_strong,
        'per_to_tim_rate': per_to_tim,
        'role_switch_range': role_range,
    }


def main():
    print('=== v1109b Step D — 検証 2: self-fulfilling 5 条件 ===\n')
    import time
    t0 = time.time()

    hist = pd.read_parquet(V1108A / 'self_dialogue_with_atom_probs.parquet')
    rng = np.random.default_rng(RNG_SEED)

    results = {}

    # 1. top1 (現状)
    events_top1 = []
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn')
        events_top1.append({
            'atoms': grp_sorted['atom_top1'].tolist(),
            'stuck_t': int(grp_sorted['stuck_at_turn'].iloc[0])
                if pd.notna(grp_sorted['stuck_at_turn'].iloc[0]) else None,
        })
    results['top1'] = compute_signs(events_top1)
    print(f'top1 (現状): {results["top1"]}')

    # 2. top2
    events_top2 = []
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn')
        events_top2.append({
            'atoms': grp_sorted['atom_top2'].tolist(),
            'stuck_t': int(grp_sorted['stuck_at_turn'].iloc[0])
                if pd.notna(grp_sorted['stuck_at_turn'].iloc[0]) else None,
        })
    results['top2'] = compute_signs(events_top2)
    print(f'top2: {results["top2"]}')

    # 3. top3
    events_top3 = []
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn')
        events_top3.append({
            'atoms': grp_sorted['atom_top3'].tolist(),
            'stuck_t': int(grp_sorted['stuck_at_turn'].iloc[0])
                if pd.notna(grp_sorted['stuck_at_turn'].iloc[0]) else None,
        })
    results['top3'] = compute_signs(events_top3)
    print(f'top3: {results["top3"]}')

    # 4. probability sampling
    events_prob = []
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn').reset_index(drop=True)
        atoms_arr = grp_sorted[[f'atom_top{i+1}' for i in range(ATOM_TOPK)]].values
        probs_arr = grp_sorted[[f'prob_top{i+1}' for i in range(ATOM_TOPK)]].values.astype(np.float64)
        new_atoms = []
        for t in range(len(grp_sorted)):
            valid_mask = np.array([a is not None for a in atoms_arr[t]])
            if valid_mask.any() and probs_arr[t][valid_mask].sum() > 0:
                va = atoms_arr[t][valid_mask]
                vp = probs_arr[t][valid_mask]
                vp = vp / vp.sum()
                new_atoms.append(rng.choice(va, p=vp))
            else:
                new_atoms.append(None)
        events_prob.append({
            'atoms': new_atoms,
            'stuck_t': int(grp_sorted['stuck_at_turn'].iloc[0])
                if pd.notna(grp_sorted['stuck_at_turn'].iloc[0]) else None,
        })
    results['probability_sampling'] = compute_signs(events_prob)
    print(f'probability_sampling: {results["probability_sampling"]}')

    # 5. seed holdout (seeds 12-23 のみ)
    events_holdout = [ev for (sd, sc), grp in hist.groupby(['seed', 'start_cid']) if sd >= 12
                       for ev in [{
                            'atoms': grp.sort_values('turn')['atom_top1'].tolist(),
                            'stuck_t': int(grp.sort_values('turn')['stuck_at_turn'].iloc[0])
                                if pd.notna(grp.sort_values('turn')['stuck_at_turn'].iloc[0]) else None,
                        }]]
    results['seed_holdout'] = compute_signs(events_holdout)
    print(f'seed_holdout: {results["seed_holdout"]}')

    # DataFrame
    rows = []
    for cond, signs in results.items():
        for sign, val in signs.items():
            rows.append({'condition': cond, 'sign': sign, 'value': float(val)})
    df = pd.DataFrame(rows)
    df.to_parquet(V1109B / 'verification_2_self_fulfilling.parquet', index=False)

    print('\n--- 集計 (top1 vs others) ---')
    pivot = df.pivot(index='sign', columns='condition', values='value').round(4)
    print(pivot.to_string())

    # top1 で出るが top2/3/sampling で消える sign の検出
    print('\n--- top1 固定問題: top1 vs sampling ---')
    for sign in pivot.index:
        v_top1 = pivot.loc[sign, 'top1']
        v_top2 = pivot.loc[sign, 'top2']
        v_top3 = pivot.loc[sign, 'top3']
        v_samp = pivot.loc[sign, 'probability_sampling']
        v_hold = pivot.loc[sign, 'seed_holdout']
        # top1 で出るが他で消える = top1 固定
        is_top1_only = v_top1 > 2 * max(v_top2, v_top3, v_samp) if v_top1 > 0 else False
        is_persistent = (v_top2 > 0.5 * v_top1) and (v_samp > 0.5 * v_top1) if v_top1 > 0 else False
        marker = '★ top1 固定の疑い' if is_top1_only else ('✓ sampling でも残る' if is_persistent else '中間')
        print(f'  {sign}: top1={v_top1:.3f}, top2={v_top2:.3f}, top3={v_top3:.3f}, '
              f'samp={v_samp:.3f}, hold={v_hold:.3f}  {marker}')

    print(f'\n=== Step D 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
