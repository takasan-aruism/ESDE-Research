#!/usr/bin/env python3
"""v1109 Step E — holdout 検証 (turn / seed / category 3 種)

自己成就回避の核心 (GPT 監査):
- train データで W 蓄積、test データで W 適用 + 予測精度測定
- baseline hit_rate を test データで再計算 (Step D で baseline=1.0 になった問題を修正)

3 種類の holdout:
- turn holdout: 各 event の turn 0-19 で W 蓄積、turn 20-39 で適用
- seed holdout: seeds 0-11 で W 蓄積、seeds 12-23 で適用
- category holdout: cluster_0 cat で W 蓄積、cluster_1 cat で適用

入力:
- unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet
- unified/v1109/outputs/main/atom_universe.parquet
- unified/v1109/outputs/main/holdout_splits.parquet

出力:
- unified/v1109/outputs/main/observation_E_holdout_results.parquet
- unified/v1109/outputs/main/observation_E_summary.parquet
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V1108A_MAIN = REPO / 'unified/v1108a/outputs/main'
V1109_MAIN = REPO / 'unified/v1109/outputs/main'

ATOM_TOPK = 10
ALPHA = 0.5
N_SHUFFLE = 5
TURN_SPLIT = 20


def build_W(events_train, n_atoms, condition='observed', rng=None):
    """train events から W を構築"""
    W = np.zeros((n_atoms, n_atoms))
    if condition == 'baseline':
        return W
    if condition == 'frequency':
        freq = np.zeros(n_atoms)
        for ev in events_train:
            for i in ev['atoms_idx']:
                if i >= 0:
                    freq[i] += 1
        total = freq.sum()
        return np.outer(freq, freq) / total if total > 0 else W
    for ev in events_train:
        idx = ev['atoms_idx']
        n = len(idx)
        if n < 2: continue
        if condition == 'shuffled':
            order = rng.permutation(n)
            idx = idx[order]
        for t in range(n - 1):
            i, j = idx[t], idx[t+1]
            if i < 0 or j < 0: continue
            W[i, j] += 1.0
    # 行毎正規化
    row_sums = W.sum(axis=1, keepdims=True)
    W = np.where(row_sums > 0, W / row_sums, W)
    return W


def evaluate_holdout(events_test, W, atom_to_idx, atoms, n_atoms,
                      turn_start=0, turn_end=None):
    """test events で予測精度測定"""
    hits = 0
    total = 0
    entropy_changes = []
    max_prob_changes = []
    atom_top_cols = [f'atom_top{i+1}' for i in range(ATOM_TOPK)]
    prob_top_cols = [f'prob_top{i+1}' for i in range(ATOM_TOPK)]

    for ev in events_test:
        df = ev['data']
        df_sorted = df.sort_values('turn').reset_index(drop=True)
        n = len(df_sorted)
        t_start = turn_start
        t_end = (turn_end if turn_end is not None else n) - 1
        for t in range(t_start, min(t_end, n-1)):
            prev_atom = df_sorted.iloc[t]['atom_top1']
            if prev_atom is None or prev_atom not in atom_to_idx:
                continue
            prev_idx = atom_to_idx[prev_atom]
            cand_atoms = df_sorted.iloc[t+1][atom_top_cols].values
            cand_probs = df_sorted.iloc[t+1][prob_top_cols].values.astype(np.float64)
            cand_idx = np.array([atom_to_idx.get(a, -1) for a in cand_atoms], dtype=np.int32)
            actual = df_sorted.iloc[t+1]['atom_top1']

            # 重み参照
            w_vec = np.zeros(ATOM_TOPK)
            for k in range(ATOM_TOPK):
                if cand_idx[k] >= 0:
                    w_vec[k] = W[prev_idx, cand_idx[k]]

            # 適用
            p_new = cand_probs * (1 + ALPHA * w_vec)
            p_new = p_new / p_new.sum() if p_new.sum() > 0 else cand_probs
            top1 = cand_atoms[int(np.argmax(p_new))]
            if top1 == actual:
                hits += 1
            total += 1

            # entropy/max_prob 変化
            p_orig = cand_probs / cand_probs.sum() if cand_probs.sum() > 0 else cand_probs
            p_n = p_new
            eps = 1e-12
            e_orig = -np.sum(p_orig * np.log(p_orig + eps)) if p_orig.sum() > 0 else 0
            e_new = -np.sum(p_n * np.log(p_n + eps))
            entropy_changes.append(e_new - e_orig)
            max_prob_changes.append(p_n.max() - p_orig.max())

    hit_rate = hits / total if total > 0 else 0
    return {
        'hit_rate': hit_rate,
        'n_predictions': total,
        'entropy_change_mean': float(np.mean(entropy_changes)) if entropy_changes else 0,
        'max_prob_change_mean': float(np.mean(max_prob_changes)) if max_prob_changes else 0,
    }


def split_events_by_turn(hist, atom_to_idx, train_turn_end=TURN_SPLIT):
    """各 event の turn を train/test に分割"""
    train_events = []
    test_events = []
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn').reset_index(drop=True)
        train_part = grp_sorted[grp_sorted['turn'] < train_turn_end]
        test_part = grp_sorted[grp_sorted['turn'] >= train_turn_end]
        if len(train_part) >= 2:
            atoms = train_part['atom_top1'].values
            idx = np.array([atom_to_idx.get(a, -1) for a in atoms], dtype=np.int32)
            train_events.append({'seed': int(sd), 'start_cid': int(sc), 'atoms_idx': idx})
        if len(test_part) >= 2:
            test_events.append({'seed': int(sd), 'start_cid': int(sc), 'data': test_part})
    return train_events, test_events


def split_events_by_seed(hist, atom_to_idx, train_seeds, test_seeds):
    train_events = []
    test_events = []
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn').reset_index(drop=True)
        atoms = grp_sorted['atom_top1'].values
        idx = np.array([atom_to_idx.get(a, -1) for a in atoms], dtype=np.int32)
        if sd in train_seeds and len(grp_sorted) >= 2:
            train_events.append({'seed': int(sd), 'start_cid': int(sc), 'atoms_idx': idx})
        elif sd in test_seeds and len(grp_sorted) >= 2:
            test_events.append({'seed': int(sd), 'start_cid': int(sc), 'data': grp_sorted})
    return train_events, test_events


def split_events_by_category(hist, atom_to_idx, train_cats, test_cats):
    train_events = []
    test_events = []
    # event の top1_cat (turn 0)
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn').reset_index(drop=True)
        top1_t0 = grp_sorted.iloc[0]['atom_top1']
        cat = top1_t0.split('.')[0] if top1_t0 else None
        atoms = grp_sorted['atom_top1'].values
        idx = np.array([atom_to_idx.get(a, -1) for a in atoms], dtype=np.int32)
        if cat in train_cats and len(grp_sorted) >= 2:
            train_events.append({'seed': int(sd), 'start_cid': int(sc), 'atoms_idx': idx})
        elif cat in test_cats and len(grp_sorted) >= 2:
            test_events.append({'seed': int(sd), 'start_cid': int(sc), 'data': grp_sorted})
    return train_events, test_events


def main():
    print('=== v1109 Step E — holdout 検証 (3 種) ===\n')
    t0 = time.time()

    atom_df = pd.read_parquet(V1109_MAIN / 'atom_universe.parquet')
    atoms = atom_df['atom_full'].tolist()
    atom_to_idx = dict(zip(atoms, atom_df['atom_idx']))
    n_atoms = len(atoms)

    hist = pd.read_parquet(V1108A_MAIN / 'self_dialogue_with_atom_probs.parquet')

    rng = np.random.default_rng(42)

    holdout_results = []

    # (1) turn holdout
    print('[1] turn holdout (前半 0-19 で W 蓄積、後半 20-39 で適用)')
    train_evt, test_evt = split_events_by_turn(hist, atom_to_idx, train_turn_end=TURN_SPLIT)
    print(f'  train events: {len(train_evt)}, test events: {len(test_evt)}')
    for cond in ['baseline', 'observed', 'shuffled', 'frequency']:
        rng2 = np.random.default_rng(42)
        W = build_W(train_evt, n_atoms, condition=cond, rng=rng2)
        result = evaluate_holdout(test_evt, W, atom_to_idx, atoms, n_atoms)
        result.update({'holdout_type': 'turn', 'condition': cond})
        holdout_results.append(result)
        print(f'  {cond}: hit_rate={result["hit_rate"]:.4f}, '
              f'entropy_change={result["entropy_change_mean"]:+.4f}')

    # (2) seed holdout
    print('\n[2] seed holdout (seeds 0-11 で蓄積、12-23 で適用)')
    train_evt, test_evt = split_events_by_seed(hist, atom_to_idx,
                                                  train_seeds=set(range(12)),
                                                  test_seeds=set(range(12, 24)))
    print(f'  train events: {len(train_evt)}, test events: {len(test_evt)}')
    for cond in ['baseline', 'observed', 'shuffled', 'frequency']:
        rng2 = np.random.default_rng(42)
        W = build_W(train_evt, n_atoms, condition=cond, rng=rng2)
        result = evaluate_holdout(test_evt, W, atom_to_idx, atoms, n_atoms)
        result.update({'holdout_type': 'seed', 'condition': cond})
        holdout_results.append(result)
        print(f'  {cond}: hit_rate={result["hit_rate"]:.4f}, '
              f'entropy_change={result["entropy_change_mean"]:+.4f}')

    # (3) category holdout
    print('\n[3] category holdout (cluster_0 cat で蓄積、cluster_1 cat で適用)')
    cluster_0_cats = {'EXS', 'FND', 'REL', 'LOG', 'VAL', 'WLD', 'COG', 'COM',
                       'ABS', 'SPC', 'CHG', 'TIM'}
    cluster_1_cats = {'BOD', 'PER', 'PRP', 'BEI', 'NAT', 'MAT', 'ACT', 'ELM',
                       'ECO', 'EMO', 'SOC', 'STA'}
    train_evt, test_evt = split_events_by_category(hist, atom_to_idx,
                                                       cluster_0_cats, cluster_1_cats)
    print(f'  train events: {len(train_evt)}, test events: {len(test_evt)}')
    for cond in ['baseline', 'observed', 'shuffled', 'frequency']:
        rng2 = np.random.default_rng(42)
        W = build_W(train_evt, n_atoms, condition=cond, rng=rng2)
        result = evaluate_holdout(test_evt, W, atom_to_idx, atoms, n_atoms)
        result.update({'holdout_type': 'category', 'condition': cond})
        holdout_results.append(result)
        print(f'  {cond}: hit_rate={result["hit_rate"]:.4f}, '
              f'entropy_change={result["entropy_change_mean"]:+.4f}')

    result_df = pd.DataFrame(holdout_results)
    result_df.to_parquet(V1109_MAIN / 'observation_E_holdout_results.parquet', index=False)

    # (4) heldout_lift 計算 (observed - baseline)
    print('\n[4] heldout_lift = observed_hit_rate - baseline_hit_rate')
    lift_rows = []
    for ho_type in ['turn', 'seed', 'category']:
        sub = result_df[result_df['holdout_type'] == ho_type]
        baseline_hr = sub[sub['condition']=='baseline']['hit_rate'].iloc[0]
        observed_hr = sub[sub['condition']=='observed']['hit_rate'].iloc[0]
        shuffled_hr = sub[sub['condition']=='shuffled']['hit_rate'].iloc[0]
        frequency_hr = sub[sub['condition']=='frequency']['hit_rate'].iloc[0]
        observed_lift = observed_hr - baseline_hr
        shuffled_lift = shuffled_hr - baseline_hr
        frequency_lift = frequency_hr - baseline_hr
        # sequence_specific 判定: observed_lift > shuffled_lift × 2
        sequence_specific = (observed_lift > shuffled_lift * 2 and observed_lift > frequency_lift)
        lift_rows.append({
            'holdout_type': ho_type,
            'baseline_hit_rate': baseline_hr,
            'observed_lift': observed_lift,
            'shuffled_lift': shuffled_lift,
            'frequency_lift': frequency_lift,
            'sequence_specific': sequence_specific,
        })
        print(f'  {ho_type}: observed={observed_lift:+.4f}, shuffled={shuffled_lift:+.4f}, '
              f'frequency={frequency_lift:+.4f}, sequence_specific={sequence_specific}')

    lift_df = pd.DataFrame(lift_rows)
    lift_df.to_parquet(V1109_MAIN / 'observation_E_summary.parquet', index=False)

    # 構造ラベル判定
    n_pass = lift_df['sequence_specific'].sum()
    if n_pass == 3:
        label = 'weight_accumulation_generalizes'
    elif n_pass >= 1:
        label = 'weight_accumulation_sequence_specific'
    else:
        label = 'weight_accumulation_mechanical_effect'
    print(f'\n  holdout 通過数: {n_pass}/3')
    print(f'  構造ラベル: {label}')

    print(f'\n=== Step E 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
