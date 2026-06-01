#!/usr/bin/env python3
"""v1111 Step 0 — diff 法の成立確認 (baseline 2 回 run で完全一致確認)

Web Claude v1111 §4.1: 「Step 0 で崩れたら先に進まない」

設計:
- 同 seed (atom=42, center=99, other=100)
- baseline 2 回連続実行 (シングルプロセス、multiprocessing 不使用)
- 各 window で E / theta / alive_l / labels.share が完全一致するか確認
- 完全一致 → diff 法成立 → v1111 本実装に進める
- 不一致 → 先に進まない、原因調査
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

import sys, json, time, math
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
STAGE5 = REPO / 'unified/attention_center_prep'
OUT_DIR = STAGE5 / 'run_v1111_step0'
OUT_DIR.mkdir(parents=True, exist_ok=True)

PATHS = [
    REPO / 'primitive/v910',
    REPO / 'autonomy/v82',
    REPO / 'cognition/semantic_injection/v4_pipeline/v43',
    REPO / 'cognition/semantic_injection/v4_pipeline/v41',
    REPO / 'ecology/engine',
]
for p in PATHS:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from esde_v82_engine import V82Engine, V82EncapsulationParams, V82_N
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9

SEED_ATOM = 42
SEED_CENTER = 99
SEED_OTHER = 100
WINDOWS = 5  # Step 0 は短い (一致確認のみ)
WINDOW_STEPS = 100


def build_engine(seed):
    encap = V82EncapsulationParams(stress_enabled=True, virtual_enabled=True)
    engine = V82Engine(seed=seed, N=V82_N, encap_params=encap)
    engine.virtual = VirtualLayerV9(feedback_gamma=0.10,
                                     feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True
    engine.run_injection()
    return engine


def snapshot_state(atom):
    """Atom 系の state スナップショット (差分比較用)"""
    return {
        'E': dict(atom.state.E),
        'theta': atom.state.theta.copy(),
        'alive_n': set(atom.state.alive_n),
        'alive_l': set(atom.state.alive_l),
        'S': dict(atom.state.S),
        'labels_share': {lid: lab['share']
                          for lid, lab in atom.virtual.labels.items()},
        'labels_phase_sig': {lid: lab['phase_sig']
                              for lid, lab in atom.virtual.labels.items()},
        'occupancy': list(atom.virtual.occupancy),
    }


def run_baseline(label):
    """baseline 1 回分の run、各 window 末で snapshot"""
    print(f'\n--- {label} 起動 ---')
    t0 = time.time()
    atom = build_engine(SEED_ATOM)
    center = build_engine(SEED_CENTER)
    other = build_engine(SEED_OTHER)
    print(f'  3 instance 起動 ({time.time()-t0:.1f}s)')
    snapshots = []
    for w in range(WINDOWS):
        atom.step_window(steps=WINDOW_STEPS)
        center.step_window(steps=WINDOW_STEPS)
        other.step_window(steps=WINDOW_STEPS)
        # 注入なし
        snapshots.append(snapshot_state(atom))
        print(f'  w={w} alive_n={len(atom.state.alive_n)} '
              f'alive_l={len(atom.state.alive_l)} '
              f'labels={len(atom.virtual.labels)}')
    print(f'  done ({time.time()-t0:.1f}s)')
    return snapshots


def compare_snapshots(s1, s2, window_idx):
    """1 window の snapshot を完全比較"""
    # E (dict): 全 key が一致 + 全 value が完全一致
    e_keys_match = set(s1['E'].keys()) == set(s2['E'].keys())
    e_values_match = True
    e_max_diff = 0.0
    if e_keys_match:
        for n in s1['E']:
            d = abs(s1['E'][n] - s2['E'][n])
            if d > e_max_diff:
                e_max_diff = d
            if s1['E'][n] != s2['E'][n]:
                e_values_match = False

    # theta (ndarray)
    theta_match = np.array_equal(s1['theta'], s2['theta'])
    theta_max_diff = float(np.abs(s1['theta'] - s2['theta']).max())

    # alive_n / alive_l (set)
    alive_n_match = s1['alive_n'] == s2['alive_n']
    alive_n_diff_size = len(s1['alive_n'] ^ s2['alive_n'])
    alive_l_match = s1['alive_l'] == s2['alive_l']
    alive_l_diff_size = len(s1['alive_l'] ^ s2['alive_l'])

    # S (dict)
    s_keys_match = set(s1['S'].keys()) == set(s2['S'].keys())
    s_values_match = True
    s_max_diff = 0.0
    if s_keys_match:
        for k in s1['S']:
            d = abs(s1['S'][k] - s2['S'][k])
            if d > s_max_diff:
                s_max_diff = d
            if s1['S'][k] != s2['S'][k]:
                s_values_match = False

    # labels.share
    label_keys_match = set(s1['labels_share'].keys()) == set(s2['labels_share'].keys())
    label_share_match = True
    label_share_max_diff = 0.0
    if label_keys_match:
        for lid in s1['labels_share']:
            d = abs(s1['labels_share'][lid] - s2['labels_share'][lid])
            if d > label_share_max_diff:
                label_share_max_diff = d
            if s1['labels_share'][lid] != s2['labels_share'][lid]:
                label_share_match = False

    # occupancy (list of 64 bins)
    occ_match = s1['occupancy'] == s2['occupancy']
    occ_max_diff = float(np.abs(np.array(s1['occupancy']) - np.array(s2['occupancy'])).max())

    return {
        'window': window_idx,
        'e_keys_match': e_keys_match,
        'e_values_match': e_values_match,
        'e_max_diff': e_max_diff,
        'theta_match': theta_match,
        'theta_max_diff': theta_max_diff,
        'alive_n_match': alive_n_match,
        'alive_n_diff_size': alive_n_diff_size,
        'alive_l_match': alive_l_match,
        'alive_l_diff_size': alive_l_diff_size,
        's_keys_match': s_keys_match,
        's_values_match': s_values_match,
        's_max_diff': s_max_diff,
        'label_keys_match': label_keys_match,
        'label_share_match': label_share_match,
        'label_share_max_diff': label_share_max_diff,
        'occ_match': occ_match,
        'occ_max_diff': occ_max_diff,
    }


def main():
    print('=== v1111 Step 0 — diff 法の成立確認 ===\n')
    print(f'  WINDOWS={WINDOWS}, atom={SEED_ATOM}, center={SEED_CENTER}, other={SEED_OTHER}\n')
    t_main = time.time()

    # 2 回 baseline 連続実行
    snapshots_1 = run_baseline('baseline_1')
    snapshots_2 = run_baseline('baseline_2')

    # 各 window 比較
    print('\n=== 完全一致確認 (window ごと) ===')
    results = []
    all_match = True
    for w in range(WINDOWS):
        cmp = compare_snapshots(snapshots_1[w], snapshots_2[w], w)
        results.append(cmp)
        all_fields = ['e_values_match', 'theta_match', 'alive_n_match',
                       'alive_l_match', 's_values_match',
                       'label_share_match', 'occ_match']
        win_match = all(cmp[f] for f in all_fields)
        if not win_match:
            all_match = False
        print(f'  w={w}: all_match={win_match}')
        print(f'    E: keys={cmp["e_keys_match"]} values={cmp["e_values_match"]} '
              f'max_diff={cmp["e_max_diff"]:.2e}')
        print(f'    theta: match={cmp["theta_match"]} max_diff={cmp["theta_max_diff"]:.2e}')
        print(f'    alive_n: match={cmp["alive_n_match"]} '
              f'diff_size={cmp["alive_n_diff_size"]}')
        print(f'    alive_l: match={cmp["alive_l_match"]} '
              f'diff_size={cmp["alive_l_diff_size"]}')
        print(f'    S: keys={cmp["s_keys_match"]} values={cmp["s_values_match"]} '
              f'max_diff={cmp["s_max_diff"]:.2e}')
        print(f'    labels: keys={cmp["label_keys_match"]} '
              f'share={cmp["label_share_match"]} max_diff={cmp["label_share_max_diff"]:.2e}')
        print(f'    occ: match={cmp["occ_match"]} max_diff={cmp["occ_max_diff"]:.2e}')

    results_df = pd.DataFrame(results)
    results_df.to_parquet(OUT_DIR / 'step0_compare.parquet', index=False)

    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'seeds': {'atom': SEED_ATOM, 'center': SEED_CENTER, 'other': SEED_OTHER},
        'WINDOWS': WINDOWS, 'WINDOW_STEPS': WINDOW_STEPS,
        'all_windows_match': bool(all_match),
        'total_sec': time.time() - t_main,
        'verdict': 'diff_method_valid' if all_match else 'diff_method_BROKEN',
    }
    (OUT_DIR / 'step0_summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))

    print(f'\n=== 出口 ===')
    print(f'  all_windows_match: {all_match}')
    print(f'  verdict: {summary["verdict"]}')
    if all_match:
        print('\n  ✓ diff 法成立: baseline 2 回が完全一致 → injected - baseline が因果足跡')
        print('    → v1111 本実装に進める')
    else:
        print('\n  ✗ diff 法不成立: baseline 不一致 → injected - baseline が信頼できない')
        print('    → 先に進まない、原因調査必要')

    print(f'\n=== Step 0 完了 total {time.time()-t_main:.1f}s ===')


if __name__ == '__main__':
    main()
