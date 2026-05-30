#!/usr/bin/env python3
"""v1109b Step C — 検証 1: shuffle baseline 4 種

shuffle で #L65 兆候が消えるか検証。
- sequence order shuffle (turn 順序ランダム化)
- within-turn shuffle (turn 内 atom 順序ランダム化、本主題では atom_top 順)
- atom label shuffle (atom ラベルランダム化)
- counterfactual shuffle (P_t 維持、サンプリング順序のみランダム化)
"""
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1108A = REPO / 'unified/v1108a/outputs/main'
V1109B = REPO / 'unified/v1109b/outputs/main'

N_SHUFFLE = 10
RNG_SEED = 42

START_ATOMS = {'COG.enlightenment', 'PRP.shallow', 'TIM.moment', 'PRP.deep',
                'ECO.withdraw', 'EXS.being', 'FND.timeless', 'FND.logic',
                'PER.see', 'ACT.make'}
END_ATOMS = {'ACT.stand', 'TIM.appear', 'CHG.grow'}
ATOM_TOPK = 10


def compute_signs(events):
    """events: list of {'atoms': [...], 'stuck_t': ...}
    指標: start_in_starts, end_in_ends, npmi_strong_count, role_switch_decisive_pct"""
    # 1. start/end 分離
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

    # turn 0 (start) で出現するatom の数 (元の START_ATOMS と一致するか)
    start_match = sum(1 for a in start_count if a in START_ATOMS) / max(len(start_count), 1)
    end_match = sum(1 for a in end_count if a in END_ATOMS) / max(len(end_count), 1)

    # 2. 順序 PMI (npmi > 0.5 ペア数)
    pair_count = Counter()
    atom_count = Counter()
    n_singles = 0
    n_pairs = 0
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

    # 3. PER.see → TIM.appear 経路率
    per_paths = [p for p in paths if p[0] == 'PER.see']
    per_to_tim = sum(1 for p in per_paths if p[1] == 'TIM.appear') / max(len(per_paths), 1)

    # 4. 役割切替決定論性 (ACT.stand で prev 別の terminal_rate range)
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


def load_events(hist):
    events = []
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn').reset_index(drop=True)
        atoms = grp_sorted['atom_top1'].tolist()
        stuck = grp_sorted['stuck_at_turn'].iloc[0]
        events.append({
            'seed': int(sd), 'start_cid': int(sc),
            'atoms': atoms,
            'stuck_t': int(stuck) if pd.notna(stuck) else None,
            'atom_top_arr': grp_sorted[[f'atom_top{i+1}' for i in range(ATOM_TOPK)]].values,
            'prob_top_arr': grp_sorted[[f'prob_top{i+1}' for i in range(ATOM_TOPK)]].values.astype(np.float64),
        })
    return events


def main():
    print('=== v1109b Step C — 検証 1: shuffle baseline 4 種 ===\n')
    import time
    t0 = time.time()

    hist = pd.read_parquet(V1108A / 'self_dialogue_with_atom_probs.parquet')
    events = load_events(hist)
    print(f'events: {len(events)}')

    # 真の指標 (現状の Grammar Exploration #L65)
    true_signs = compute_signs(events)
    print(f'\n--- 真 ---')
    for k, v in true_signs.items():
        print(f'  {k}: {v:.4f}')

    rng = np.random.default_rng(RNG_SEED)
    shuffle_results = {st: [] for st in ['sequence_order', 'within_turn', 'atom_label', 'counterfactual']}

    print(f'\n--- shuffle baseline ({N_SHUFFLE} 回 × 4 種) ---')

    # 1. sequence order shuffle: 各 event の turn 順序ランダム化
    for it in range(N_SHUFFLE):
        shuf_events = []
        for ev in events:
            atoms = ev['atoms'][:]
            perm = rng.permutation(len(atoms))
            shuf_events.append({
                'atoms': [atoms[p] for p in perm],
                'stuck_t': ev['stuck_t'],
            })
        shuffle_results['sequence_order'].append(compute_signs(shuf_events))

    # 2. within-turn shuffle: 各 turn の top-K を別の top-K で置換 (top1 を top_k から random pick)
    for it in range(N_SHUFFLE):
        shuf_events = []
        for ev in events:
            new_atoms = []
            for t in range(len(ev['atoms'])):
                top_arr = ev['atom_top_arr'][t] if t < len(ev['atom_top_arr']) else None
                if top_arr is not None:
                    valid = [a for a in top_arr if a is not None]
                    new_atoms.append(rng.choice(valid) if valid else None)
                else:
                    new_atoms.append(None)
            shuf_events.append({'atoms': new_atoms, 'stuck_t': ev['stuck_t']})
        shuffle_results['within_turn'].append(compute_signs(shuf_events))

    # 3. atom label shuffle: 全 atom のラベルを permutation
    all_atoms = list({a for ev in events for a in ev['atoms'] if a})
    for it in range(N_SHUFFLE):
        perm = rng.permutation(all_atoms)
        label_map = dict(zip(all_atoms, perm))
        shuf_events = []
        for ev in events:
            shuf_events.append({
                'atoms': [label_map.get(a, a) for a in ev['atoms']],
                'stuck_t': ev['stuck_t'],
            })
        shuffle_results['atom_label'].append(compute_signs(shuf_events))

    # 4. counterfactual shuffle: P_t 維持、確率サンプリング
    for it in range(N_SHUFFLE):
        shuf_events = []
        for ev in events:
            new_atoms = []
            for t in range(len(ev['atoms'])):
                if t < len(ev['atom_top_arr']):
                    atoms_t = ev['atom_top_arr'][t]
                    probs_t = ev['prob_top_arr'][t]
                    valid_mask = np.array([a is not None for a in atoms_t])
                    if valid_mask.any() and probs_t[valid_mask].sum() > 0:
                        valid_atoms = atoms_t[valid_mask]
                        valid_probs = probs_t[valid_mask]
                        valid_probs = valid_probs / valid_probs.sum()
                        new_atoms.append(rng.choice(valid_atoms, p=valid_probs))
                    else:
                        new_atoms.append(None)
                else:
                    new_atoms.append(None)
            shuf_events.append({'atoms': new_atoms, 'stuck_t': ev['stuck_t']})
        shuffle_results['counterfactual'].append(compute_signs(shuf_events))

    # 集計
    rows = []
    for shuf_type, runs in shuffle_results.items():
        means = {k: np.mean([r[k] for r in runs]) for k in runs[0]}
        stds = {k: np.std([r[k] for r in runs]) for k in runs[0]}
        for k in means:
            z = (true_signs[k] - means[k]) / stds[k] if stds[k] > 0 else 0
            rows.append({
                'shuffle_type': shuf_type, 'sign': k,
                'true': true_signs[k],
                'shuf_mean': means[k], 'shuf_std': stds[k],
                'z_score': z,
                'beats_shuffle': z > 2.0,
            })
    df = pd.DataFrame(rows)
    df.to_parquet(V1109B / 'verification_1_shuffle.parquet', index=False)

    print('\n--- shuffle 比較結果 ---')
    pivot = df.pivot_table(index='sign', columns='shuffle_type', values='z_score').round(2)
    print(pivot.to_string())

    print(f'\n--- 各 sign が beats shuffle (z>2) する shuffle 数 ---')
    beats_count = df.groupby('sign')['beats_shuffle'].sum().to_dict()
    for sign, n in beats_count.items():
        print(f'  {sign}: {n}/4 shuffle で beats')

    # 全 shuffle で beats する sign = 強い証拠
    strong = df.groupby('sign')['beats_shuffle'].all().to_dict()
    print(f'\n--- 全 shuffle 通過 (本物候補) ---')
    for sign, ok in strong.items():
        print(f'  {sign}: {"✓ 全 shuffle 通過" if ok else "✗ 一部 shuffle で消える"}')

    print(f'\n=== Step C 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
