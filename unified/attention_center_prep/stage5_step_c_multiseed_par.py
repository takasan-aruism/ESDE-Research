#!/usr/bin/env python3
"""注意センター Step C — 多 seed 再現確認 (24 cores 並列版)

Taka 指示 (2026-06-01): 「24コア並列で可能な範囲の処理を」

設計:
- 3 seeds × 3 conditions = 9 タスク独立
- multiprocessing.Pool で 9 並列実行
- 各 worker で OMP_NUM_THREADS=1 (thread 競合回避)
- 推定 35-40 分 (1 タスク時間)
"""
import os
# multiprocessing import 前に thread を制限
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

import sys, json, time, math
from pathlib import Path
from multiprocessing import Pool
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


def _worker(args):
    """Pool worker: 1 condition for 1 seed_set 実行
    各 worker で engine module を再 import + run"""
    seed_set, cond = args
    sa = seed_set['atom']; sc = seed_set['center']; so = seed_set['other']
    pid = os.getpid()
    print(f'  [PID {pid}] start {cond} atom={sa}', flush=True)
    t0 = time.time()

    # worker 内で path 再設定 + import
    for p in PATHS:
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    from esde_v82_engine import V82Engine, V82EncapsulationParams, V82_N
    from virtual_layer_v9 import VirtualLayer as VirtualLayerV9

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
        z = (max_E - mean_E) / std_E
        ss = center_engine.stress_stats or {}
        stress = float(ss.get('stress_intensity', 1.0))
        return z > stress, {'z_score': z, 'stress': stress}

    def derive_center_target_phase(center_engine, K=K_TARGET):
        alive = sorted(center_engine.state.alive_n)
        if not alive: return None
        e_vals = {n: float(center_engine.state.E.get(n, 0.0)) for n in alive}
        top_K = sorted(alive, key=lambda n: -e_vals[n])[:K]
        thetas = [float(center_engine.state.theta[n]) for n in top_K]
        if not thetas: return None
        cs = sum(math.cos(t) for t in thetas)
        ss_ = sum(math.sin(t) for t in thetas)
        tp = math.atan2(ss_ / len(thetas), cs / len(thetas))
        return tp % (2 * math.pi)

    def compute_lambda_dynamic(center_engine):
        macro = set(center_engine.virtual.macro_nodes)
        ps = [lab['phase_sig'] for lid, lab in center_engine.virtual.labels.items()
              if lid not in macro]
        if len(ps) < 2: return 1.0
        cm = float(np.mean([math.cos(p) for p in ps]))
        sm = float(np.mean([math.sin(p) for p in ps]))
        r = math.sqrt(cm**2 + sm**2)
        cs_std = math.pi if r < 1e-9 else math.sqrt(-2 * math.log(max(r, 1e-9)))
        return 1.0 / (cs_std + 1e-9)

    def circular_distance(a, b):
        d = abs(a - b) % (2 * math.pi)
        return min(d, 2 * math.pi - d)

    def compute_label_weights(atom_engine, tp, lam):
        macro = set(atom_engine.virtual.macro_nodes)
        weights = {}
        for lid, lab in atom_engine.virtual.labels.items():
            if lid in macro: continue
            d = circular_distance(lab['phase_sig'], tp)
            weights[lid] = {'w': math.exp(-lam * d), 'nodes': list(lab['nodes'])}
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
        info = {'window': w, 'fired': False, 'target_phase': None, **fi}
        if not fire: return info
        tp = derive_center_target_phase(center, K_TARGET)
        if tp is None:
            info['fired'] = True
            return info
        lam = compute_lambda_dynamic(center)
        weights = compute_label_weights(atom, tp, lam)
        targets = derive_targets_from_weights(weights, atom, K_TARGET)
        info.update({'fired': True, 'target_phase': float(tp)})
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
            return {'high_occ_sum': 0.0, 'low_occ_sum': 0.0, 'high_low_ratio': 0.0}
        sb = np.argsort(-contact_map)
        n_top = max(1, int(N_BINS * top_q))
        high = set(sb[:n_top].tolist())
        low = set(sb[-n_top:].tolist())
        hs = sum(occ[b] for b in high); ls = sum(occ[b] for b in low)
        return {'high_occ_sum': float(hs), 'low_occ_sum': float(ls),
                'high_low_ratio': float(hs / (ls + 1e-9))}

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

    # メイン処理
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
    print(f'  [PID {pid}] done {cond} atom={sa} ({dt:.0f}s) '
          f'final ratio={rows[-1]["high_low_ratio"]:.3f}', flush=True)
    return pd.DataFrame(rows)


def main():
    print('=== 注意センター Step C 多 seed 再現確認 (並列版) ===\n')
    print(f'  3 seed sets × 3 conditions = 9 並列タスク, WINDOWS={WINDOWS}\n')
    t_main = time.time()

    tasks = []
    for seed_set in SEED_SETS:
        for cond in ['no_center', 'center_no_other', 'center_other']:
            tasks.append((seed_set, cond))

    print(f'  起動: {len(tasks)} processes\n')
    # 9 並列実行
    with Pool(processes=9) as pool:
        results = pool.map(_worker, tasks)

    full = pd.concat(results, ignore_index=True)
    full.to_parquet(OUT_DIR / 'multiseed_full.parquet', index=False)

    # 集計
    print('\n=== 最終 window の seed 横断集計 ===')
    last_df = full[full['window'] == WINDOWS - 1].copy()
    pivot = last_df.pivot(index='seed_atom', columns='condition',
                            values='high_low_ratio')
    print('\n[各 seed の最終 high_low_ratio]')
    print(pivot.to_string())

    # 帰属差分
    print('\n[帰属差分 (center_other - center_no_other) per seed]')
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

    print('\n[3 seeds 帰属差分の平均 ± std]')
    for k in KEYS:
        rel_col = f'{k}_rel'
        mean = diff_df[rel_col].mean()
        std = diff_df[rel_col].std()
        signs = np.sign(diff_df[rel_col].values)
        same_sign = bool(len(set(signs)) == 1)
        marker = '★' if same_sign and abs(mean) > 0.05 else ' '
        print(f'  {marker} {k:20s} rel = {mean*100:+.2f}% ± {std*100:.2f}% '
              f'(same_sign={same_sign})')

    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'seed_sets': SEED_SETS, 'windows': WINDOWS, 'N': 5000,
        'window_steps': WINDOW_STEPS, 'K_target': K_TARGET, 'K_near': K_NEAR,
        'total_sec': time.time() - t_main, 'parallel': True,
    }
    (OUT_DIR / 'multiseed_run_summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n=== 多 seed 並列再現確認 完了 total {time.time()-t_main:.1f}s ===')


if __name__ == '__main__':
    main()
