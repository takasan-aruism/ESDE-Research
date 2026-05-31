#!/usr/bin/env python3
"""注意センター Step C — 多 seed で帰属差分 +64% の再現確認

Taka 指示 (2026-06-01): 「多 seed で +64% の再現を先に固める」

設計:
- 3 seeds × 3 conditions × 15 windows
- 各 seed で Atom / Center / Other を別 instance (重複なし)
- 各 condition の最終 high_low_ratio を seed 横断で集計
- 帰属差分 (center_other - center_no_other) の 3 seeds 平均 + std

Step C smoke の rel +64.34% が再現するか。
"""
import sys, json, time, math
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
STAGE5 = REPO / 'unified/attention_center_prep'
OUT_DIR = STAGE5 / 'run_smoke_c_multiseed'
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

# 3 seed sets (全 9 seeds 異なる、重複なし)
SEED_SETS = [
    {'atom': 42,  'center': 99,  'other': 101},
    {'atom': 100, 'center': 157, 'other': 158},
    {'atom': 200, 'center': 217, 'other': 218},
]
WINDOWS = 15
WINDOW_STEPS = 100
OTHER_STEPS = 5
K_TARGET = 5
K_NEAR = 3
N_BINS = 64


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


def should_attend(center_engine):
    if not center_engine.state.alive_n:
        return False, {'z_score': 0.0, 'stress': 0.0}
    E_vals = np.array([center_engine.state.E.get(n, 0.0)
                        for n in center_engine.state.alive_n])
    if len(E_vals) < 2:
        return False, {'z_score': 0.0, 'stress': 0.0}
    mean_E = float(E_vals.mean()); std_E = float(E_vals.std())
    if std_E < 1e-9:
        return False, {'z_score': 0.0, 'stress': 0.0}
    max_E = float(E_vals.max())
    z_score = (max_E - mean_E) / std_E
    ss = center_engine.stress_stats or {}
    stress = float(ss.get('stress_intensity', 1.0))
    return z_score > stress, {'z_score': z_score, 'stress': stress}


def derive_center_target_phase(center_engine, K=K_TARGET):
    alive = sorted(center_engine.state.alive_n)
    if not alive: return None
    e_vals = {n: float(center_engine.state.E.get(n, 0.0)) for n in alive}
    top_K = sorted(alive, key=lambda n: -e_vals[n])[:K]
    thetas = [float(center_engine.state.theta[n]) for n in top_K]
    if not thetas: return None
    cos_sum = sum(math.cos(t) for t in thetas)
    sin_sum = sum(math.sin(t) for t in thetas)
    tp = math.atan2(sin_sum / len(thetas), cos_sum / len(thetas))
    return tp % (2 * math.pi)


def compute_lambda_dynamic(center_engine):
    macro = set(center_engine.virtual.macro_nodes)
    phase_sigs = [lab['phase_sig'] for lid, lab in center_engine.virtual.labels.items()
                  if lid not in macro]
    if len(phase_sigs) < 2: return 1.0
    cos_mean = float(np.mean([math.cos(p) for p in phase_sigs]))
    sin_mean = float(np.mean([math.sin(p) for p in phase_sigs]))
    r = math.sqrt(cos_mean**2 + sin_mean**2)
    if r < 1e-9: circular_std = math.pi
    else: circular_std = math.sqrt(-2 * math.log(max(r, 1e-9)))
    return 1.0 / (circular_std + 1e-9)


def circular_distance(a, b):
    d = abs(a - b) % (2 * math.pi)
    return min(d, 2 * math.pi - d)


def compute_label_weights(atom_engine, target_phase, lambda_dyn):
    macro = set(atom_engine.virtual.macro_nodes)
    weights = {}
    for lid, lab in atom_engine.virtual.labels.items():
        if lid in macro: continue
        d = circular_distance(lab['phase_sig'], target_phase)
        weights[lid] = {'w': math.exp(-lambda_dyn * d), 'nodes': list(lab['nodes'])}
    return weights


def derive_targets_from_weights(weights, atom_engine, K=K_TARGET):
    if not weights: return []
    sorted_lids = sorted(weights.keys(), key=lambda l: -weights[l]['w'])
    cands = []
    for lid in sorted_lids[:max(K, 3)]:
        for n in weights[lid]['nodes']:
            if n in atom_engine.state.alive_n:
                cands.append(n)
    cands = list(set(cands))
    if not cands: return []
    e_vals = {n: float(atom_engine.state.E.get(n, 0.0)) for n in cands}
    return sorted(cands, key=lambda n: -e_vals[n])[:K]


def translate_other_to_atom(other_engine, K=K_TARGET):
    alive = sorted(other_engine.state.alive_n)
    if not alive: return []
    e_vals = {n: float(other_engine.state.E.get(n, 0.0)) for n in alive}
    return sorted(alive, key=lambda n: -e_vals[n])[:K]


def run_attention_loop(center, atom, other, w, use_other):
    fire, fi = should_attend(center)
    info = {'window': w, 'fired': False, 'target_phase': None, 'max_w': 0.0,
            'use_other': use_other, **fi}
    if not fire: return info
    tp = derive_center_target_phase(center, K_TARGET)
    if tp is None:
        info['fired'] = True
        return info
    lam = compute_lambda_dynamic(center)
    weights = compute_label_weights(atom, tp, lam)
    max_w = max((wt['w'] for wt in weights.values()), default=0.0)
    targets = derive_targets_from_weights(weights, atom, K_TARGET)
    info.update({'fired': True, 'target_phase': float(tp),
                  'lambda_dyn': float(lam), 'max_w': float(max_w)})
    if not targets: return info
    if use_other:
        other.physics.inject(other.state, target_nodes=list(targets))
        other.step_window(steps=OTHER_STEPS)
        new_targets = translate_other_to_atom(other, K_TARGET)
    else:
        new_targets = targets
    if new_targets:
        atom.physics.inject(atom.state, target_nodes=new_targets)
    return info


def update_contact_map(contact_map, tp, K_NEAR=K_NEAR):
    if tp is None: return
    BIN_WIDTH = 2 * math.pi / N_BINS
    tb = int(tp / BIN_WIDTH); tb = min(tb, N_BINS - 1)
    for d in range(-K_NEAR, K_NEAR + 1):
        contact_map[(tb + d) % N_BINS] += 1


def stratify(occ, contact_map, top_q=0.25):
    if not occ or len(occ) != N_BINS:
        return {'high_occ_sum': 0.0, 'low_occ_sum': 0.0,
                'high_low_ratio': 0.0}
    sb = np.argsort(-contact_map)
    n_top = max(1, int(N_BINS * top_q))
    high = set(sb[:n_top].tolist())
    low = set(sb[-n_top:].tolist())
    hsum = sum(occ[b] for b in high)
    lsum = sum(occ[b] for b in low)
    return {'high_occ_sum': float(hsum), 'low_occ_sum': float(lsum),
            'high_low_ratio': float(hsum / (lsum + 1e-9))}


def observe(atom, contact_map):
    macro = set(atom.virtual.macro_nodes)
    non_macro = [lab for lid, lab in atom.virtual.labels.items()
                  if lid not in macro]
    occ = atom.virtual.occupancy or []
    vs = atom.virtual_stats or {}
    obs = {
        'labels_total': len(non_macro),
        'alive_l_count': len(atom.state.alive_l),
        'torque_events': vs.get('torque_events', 0),
        'share_max': max([lab['share'] for lab in non_macro], default=0.0),
    }
    obs.update(stratify(occ, contact_map, 0.25))
    return obs


def run_condition_for_seed(seed_set, cond):
    sa = seed_set['atom']; sc = seed_set['center']; so = seed_set['other']
    t0 = time.time()
    atom = build_engine(sa)
    center = None; other = None
    if cond in ('center_no_other', 'center_other'):
        center = build_engine(sc)
    if cond == 'center_other':
        other = build_engine(so)
    contact_map = np.zeros(N_BINS)
    rows = []
    for w in range(WINDOWS):
        atom.step_window(steps=WINDOW_STEPS)
        if center is not None:
            center.step_window(steps=WINDOW_STEPS)
            use_other = (cond == 'center_other')
            li = run_attention_loop(center, atom, other, w, use_other)
            if li['fired'] and li['target_phase'] is not None:
                update_contact_map(contact_map, li['target_phase'], K_NEAR)
        obs = observe(atom, contact_map)
        rows.append({'seed_atom': sa, 'condition': cond, 'window': w, **obs})
    dt = time.time() - t0
    print(f'    {cond} (atom={sa}): done {dt:.0f}s, '
          f'final ratio={rows[-1]["high_low_ratio"]:.3f}')
    return pd.DataFrame(rows), dt


def main():
    print('=== 注意センター Step C 多 seed 再現確認 ===\n')
    print(f'  3 seed sets × 3 conditions × {WINDOWS} windows')
    t_main = time.time()
    all_rows = []
    timing = {}
    for idx, seed_set in enumerate(SEED_SETS):
        print(f'\n--- seed_set {idx}: atom={seed_set["atom"]}, '
              f'center={seed_set["center"]}, other={seed_set["other"]} ---')
        for cond in ['no_center', 'center_no_other', 'center_other']:
            df, dt = run_condition_for_seed(seed_set, cond)
            all_rows.append(df)
            timing[f'seed{idx}_{cond}'] = dt
    full = pd.concat(all_rows, ignore_index=True)
    full.to_parquet(OUT_DIR / 'multiseed_full.parquet', index=False)

    # seed 横断集計
    print('\n=== 最終 window の seed 横断集計 ===')
    last_df = full[full['window'] == WINDOWS - 1].copy()
    print('\n[各 seed の最終 high_low_ratio]')
    pivot = last_df.pivot(index='seed_atom', columns='condition',
                            values='high_low_ratio')
    print(pivot.to_string())

    # 帰属差分 (center_other - center_no_other) per seed
    print('\n[帰属差分 high_low_ratio (center_other - center_no_other)]')
    KEYS = ['high_low_ratio', 'high_occ_sum', 'low_occ_sum',
            'labels_total', 'torque_events', 'share_max', 'alive_l_count']
    diff_rows = []
    for sa in [s['atom'] for s in SEED_SETS]:
        co = last_df[(last_df['seed_atom'] == sa) &
                      (last_df['condition'] == 'center_other')].iloc[0]
        cn = last_df[(last_df['seed_atom'] == sa) &
                      (last_df['condition'] == 'center_no_other')].iloc[0]
        row = {'seed_atom': sa}
        for k in KEYS:
            d = float(co[k]) - float(cn[k])
            rel = d / (abs(float(cn[k])) + 1e-9)
            row[f'{k}_delta'] = d
            row[f'{k}_rel'] = rel
        diff_rows.append(row)
    diff_df = pd.DataFrame(diff_rows)
    diff_df.to_parquet(OUT_DIR / 'multiseed_diffs.parquet', index=False)
    print(diff_df[['seed_atom'] + [f'{k}_rel' for k in KEYS]].to_string(index=False))

    # 3 seeds 平均 + std
    print('\n[3 seeds 帰属差分の平均 ± std]')
    for k in KEYS:
        rel_col = f'{k}_rel'
        mean = diff_df[rel_col].mean()
        std = diff_df[rel_col].std()
        # 再現性: 3 seeds で同方向か
        signs = np.sign(diff_df[rel_col].values)
        same_sign = bool(len(set(signs)) == 1)
        marker = '★' if same_sign and abs(mean) > 0.05 else ' '
        print(f'  {marker} {k:20s} rel = {mean*100:+.2f}% ± {std*100:.2f}% '
              f'(same_sign={same_sign})')

    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'seed_sets': SEED_SETS, 'windows': WINDOWS, 'N': V82_N,
        'window_steps': WINDOW_STEPS, 'K_target': K_TARGET, 'K_near': K_NEAR,
        'timing_sec': timing,
        'total_sec': time.time() - t_main,
    }
    (OUT_DIR / 'multiseed_run_summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n=== 多 seed 再現確認 完了 total {time.time()-t_main:.1f}s ===')


if __name__ == '__main__':
    main()
