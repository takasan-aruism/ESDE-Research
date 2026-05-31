#!/usr/bin/env python3
"""注意センター ESDE — Step B smoke (phase 向き先 + 選択性 + 狙い撃ち判別)

Web Claude Step B 機能設計準拠:
- 機能 2 作り直し: phase 連続一致率 w = exp(-λ·circular_distance(label.phase_sig, center_target_phase))
- 発火両辺 state 動的化: stress_enabled=True で stress_intensity 動的
- 観察: 近傍/遠方分解 (phase bin)
- 不変条件: 物理層 frozen / source_event 1 本 / 判定置かない / 同型 3 instance
"""
import sys, json, time, math
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
STAGE5 = REPO / 'unified/attention_center_prep'
OUT_DIR = STAGE5 / 'run_smoke_b'
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
WINDOWS = 5
WINDOW_STEPS = 100
OTHER_STEPS = 5
K_TARGET = 5
K_NEAR = 3  # ±3 bins → 7 bins ≈ 39°


def build_engine(seed, tag):
    """Step B: stress_enabled=True に変更 (両辺 state 動的化)"""
    encap = V82EncapsulationParams(stress_enabled=True,  # ← Step A から変更
                                    virtual_enabled=True)
    engine = V82Engine(seed=seed, N=V82_N, encap_params=encap)
    engine.virtual = VirtualLayerV9(feedback_gamma=0.10,
                                     feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True
    engine.run_injection()
    return engine


# ========================================================
# 発火 (案 A、両辺 state-dependent、stress_enabled=True で stress 動的)
# ========================================================
def should_attend(center_engine):
    if not center_engine.state.alive_n:
        return False, {'reason': 'no_alive_n', 'z_score': 0.0, 'stress': 0.0}
    E_vals = np.array([center_engine.state.E.get(n, 0.0)
                        for n in center_engine.state.alive_n])
    if len(E_vals) < 2:
        return False, {'reason': 'too_few', 'z_score': 0.0, 'stress': 0.0}
    mean_E = float(E_vals.mean())
    std_E = float(E_vals.std())
    if std_E < 1e-9:
        return False, {'reason': 'no_std', 'z_score': 0.0, 'stress': 0.0}
    max_E = float(E_vals.max())
    z_score = (max_E - mean_E) / std_E
    ss = center_engine.stress_stats or {}
    stress = float(ss.get('stress_intensity', 1.0))  # 動的 (stress_enabled=True)
    fire = z_score > stress
    return fire, {'z_score': z_score, 'stress': stress,
                  'mean_E': mean_E, 'std_E': std_E, 'max_E': max_E}


# ========================================================
# 機能 2 (作り直し): phase 連続一致率
# ========================================================
def derive_center_target_phase(center_engine, K=K_TARGET):
    """センター E top-K node の theta から円周平均 phase を計算 (state 由来)"""
    alive = sorted(center_engine.state.alive_n)
    if not alive:
        return None, []
    e_vals = {n: float(center_engine.state.E.get(n, 0.0)) for n in alive}
    top_K = sorted(alive, key=lambda n: -e_vals[n])[:K]
    thetas = [float(center_engine.state.theta[n]) for n in top_K]
    if not thetas:
        return None, []
    # 円周平均 (kuramoto order parameter)
    cos_sum = sum(math.cos(t) for t in thetas)
    sin_sum = sum(math.sin(t) for t in thetas)
    target_phase = math.atan2(sin_sum / len(thetas), cos_sum / len(thetas))
    # 0..2π に正規化
    target_phase = target_phase % (2 * math.pi)
    return target_phase, top_K


def compute_lambda_dynamic(atom_engine):
    """λ を Atom 系 labels の phase 分散から導出 (state 由来)"""
    macro = set(atom_engine.virtual.macro_nodes)
    phase_sigs = [lab['phase_sig'] for lid, lab in atom_engine.virtual.labels.items()
                  if lid not in macro]
    if len(phase_sigs) < 2:
        return 1.0
    cos_mean = float(np.mean([math.cos(p) for p in phase_sigs]))
    sin_mean = float(np.mean([math.sin(p) for p in phase_sigs]))
    r = math.sqrt(cos_mean**2 + sin_mean**2)
    if r < 1e-9:
        circular_std = math.pi
    else:
        circular_std = math.sqrt(-2 * math.log(max(r, 1e-9)))
    return 1.0 / (circular_std + 1e-9)


def circular_distance(a, b):
    """円周距離 (0..π)"""
    d = abs(a - b) % (2 * math.pi)
    return min(d, 2 * math.pi - d)


def compute_label_weights(atom_engine, target_phase, lambda_dyn):
    """exp(-λ·d) で全 label に連続重み"""
    macro = set(atom_engine.virtual.macro_nodes)
    weights = {}
    for lid, lab in atom_engine.virtual.labels.items():
        if lid in macro:
            continue
        d = circular_distance(lab['phase_sig'], target_phase)
        w = math.exp(-lambda_dyn * d)
        weights[lid] = {'w': w, 'd': d, 'phase_sig': lab['phase_sig'],
                         'nodes': list(lab['nodes'])}
    return weights


def derive_targets_from_weights(weights, atom_engine, K=K_TARGET):
    """top-K w labels の core nodes から target_nodes 抽出"""
    if not weights:
        return [], 0
    sorted_lids = sorted(weights.keys(), key=lambda l: -weights[l]['w'])
    # 上位 label の core nodes を集めて E top-K で選ぶ
    candidate_nodes = []
    for lid in sorted_lids[:max(K, 3)]:
        for n in weights[lid]['nodes']:
            if n in atom_engine.state.alive_n:
                candidate_nodes.append(n)
    candidate_nodes = list(set(candidate_nodes))
    if not candidate_nodes:
        return [], 0
    e_vals = {n: float(atom_engine.state.E.get(n, 0.0)) for n in candidate_nodes}
    top_K = sorted(candidate_nodes, key=lambda n: -e_vals[n])[:K]
    return top_K, len(candidate_nodes)


def translate_other_to_atom(other_engine, K=K_TARGET):
    alive = sorted(other_engine.state.alive_n)
    if not alive:
        return []
    e_vals = {n: float(other_engine.state.E.get(n, 0.0)) for n in alive}
    return sorted(alive, key=lambda n: -e_vals[n])[:K]


# ========================================================
# 近傍/遠方分解 (Web Claude §3)
# ========================================================
def phase_near_far(atom_engine, target_phase, K_NEAR=K_NEAR):
    target_bin = atom_engine.virtual._phase_bin(target_phase)
    occ = atom_engine.virtual.occupancy or []
    N_BINS = atom_engine.virtual.N_BINS
    if not occ or len(occ) != N_BINS:
        return {'target_bin': target_bin, 'near_occ_sum': 0.0,
                'far_occ_sum': 0.0, 'near_occ_mean': 0.0, 'far_occ_mean': 0.0}
    near_bins = set((target_bin + d) % N_BINS for d in range(-K_NEAR, K_NEAR + 1))
    near_sum = sum(occ[b] for b in near_bins)
    far_sum = sum(occ[b] for b in range(N_BINS) if b not in near_bins)
    n_near = len(near_bins)
    n_far = N_BINS - n_near
    return {
        'target_bin': int(target_bin),
        'near_occ_sum': float(near_sum),
        'far_occ_sum': float(far_sum),
        'near_occ_mean': float(near_sum / n_near),
        'far_occ_mean': float(far_sum / n_far),
        'near_far_ratio': float(near_sum / (far_sum + 1e-9)),
    }


def run_attention_loop_b(center_engine, atom_engine, other_engine, w):
    """Step B: phase 向き先 1 往復"""
    fire, fire_info = should_attend(center_engine)
    if not fire:
        return {'window': w, 'fired': False, **fire_info,
                'target_phase': None, 'lambda_dyn': None,
                'max_w': 0.0, 'overlap_n_nodes': 0, 'atom_inject_n': 0}
    # phase 向き先
    target_phase, center_top_nodes = derive_center_target_phase(center_engine, K_TARGET)
    if target_phase is None:
        return {'window': w, 'fired': True, **fire_info,
                'target_phase': None, 'lambda_dyn': None,
                'max_w': 0.0, 'overlap_n_nodes': 0, 'atom_inject_n': 0}
    # λ_dynamic
    lambda_dyn = compute_lambda_dynamic(atom_engine)
    # weights
    weights = compute_label_weights(atom_engine, target_phase, lambda_dyn)
    max_w = max((wt['w'] for wt in weights.values()), default=0.0)
    # 別系へ inject
    target_nodes, n_candidates = derive_targets_from_weights(weights, atom_engine, K_TARGET)
    if not target_nodes:
        return {'window': w, 'fired': True, **fire_info,
                'target_phase': target_phase, 'lambda_dyn': lambda_dyn,
                'max_w': max_w, 'overlap_n_nodes': 0, 'atom_inject_n': 0}
    other_engine.physics.inject(other_engine.state, target_nodes=list(target_nodes))
    other_engine.step_window(steps=OTHER_STEPS)
    new_targets = translate_other_to_atom(other_engine, K_TARGET)
    if new_targets:
        atom_engine.physics.inject(atom_engine.state, target_nodes=new_targets)
    return {'window': w, 'fired': True, **fire_info,
            'target_phase': float(target_phase),
            'lambda_dyn': float(lambda_dyn),
            'max_w': float(max_w),
            'overlap_n_nodes': len(target_nodes),
            'atom_inject_n': len(new_targets),
            'n_candidates': n_candidates}


def observe_atom(atom_engine, window_idx, target_phase=None):
    macro = set(atom_engine.virtual.macro_nodes)
    non_macro = {lid: lab for lid, lab in atom_engine.virtual.labels.items()
                  if lid not in macro}
    n_core_list = [len(lab['nodes']) for lab in non_macro.values()]
    share_list = [lab['share'] for lab in non_macro.values()]
    age_list = [window_idx - lab['born'] for lab in non_macro.values()]
    n_core_counter = {}
    for n in n_core_list:
        n_core_counter[n] = n_core_counter.get(n, 0) + 1
    total = len(non_macro)
    occ = atom_engine.virtual.occupancy or []
    occ_max = max(occ) if occ else 0.0
    occ_mean = float(np.mean(occ)) if occ else 0.0
    occ_nonzero = sum(1 for v in occ if v > 0.001)
    vs = atom_engine.virtual_stats or {}
    ss = atom_engine.stress_stats or {}
    obs = {
        'labels_total': total,
        'n_core_mean': float(np.mean(n_core_list)) if n_core_list else 0.0,
        'pct_n_core_2': (n_core_counter.get(2, 0) / max(total, 1)) * 100,
        'pct_n_core_5plus': (sum(c for n, c in n_core_counter.items() if n >= 5)
                              / max(total, 1)) * 100,
        'share_mean': float(np.mean(share_list)) if share_list else 0.0,
        'share_max': float(max(share_list)) if share_list else 0.0,
        'age_mean': float(np.mean(age_list)) if age_list else 0.0,
        'alive_n_count': len(atom_engine.state.alive_n),
        'alive_l_count': len(atom_engine.state.alive_l),
        'labels_active': vs.get('labels_active', 0),
        'torque_events': vs.get('torque_events', 0),
        'stress_intensity': float(ss.get('stress_intensity', 1.0)),
        'occ_max': occ_max,
        'occ_mean': occ_mean,
        'occ_nonzero': occ_nonzero,
    }
    # 近傍/遠方分解 (target_phase が与えられた場合)
    if target_phase is not None:
        nf = phase_near_far(atom_engine, target_phase, K_NEAR)
        obs.update({f'near_far_{k}': v for k, v in nf.items()})
    return obs


def run_no_center():
    print('\n=== no_center: Atom 系のみ (stress_enabled=True) ===')
    t0 = time.time()
    atom = build_engine(SEED_ATOM, 'atom')
    print(f'  Atom 起動 ({time.time()-t0:.1f}s)')
    rows = []
    for w in range(WINDOWS):
        atom.step_window(steps=WINDOW_STEPS)
        # no_center でも近傍/遠方分解の比較のため、dummy target_phase = 0 で集計
        obs = observe_atom(atom, w, target_phase=0.0)
        rows.append({'condition': 'no_center', 'window': w, **obs})
        print(f'  w={w} labels={obs["labels_total"]} '
              f'pct_5+={obs["pct_n_core_5plus"]:.2f}% '
              f'occ_max={obs["occ_max"]:.3f} '
              f'stress={obs["stress_intensity"]:.3f} '
              f'near={obs["near_far_near_occ_sum"]:.3f} '
              f'far={obs["near_far_far_occ_sum"]:.3f}')
    print(f'  done ({time.time()-t0:.1f}s)')
    return pd.DataFrame(rows), time.time() - t0


def run_with_center():
    print('\n=== with_center: 3 instance (phase 向き先) ===')
    t0 = time.time()
    atom = build_engine(SEED_ATOM, 'atom')
    print(f'  Atom 起動 ({time.time()-t0:.1f}s)')
    t1 = time.time()
    center = build_engine(SEED_CENTER, 'center')
    print(f'  Center 起動 ({time.time()-t1:.1f}s)')
    t2 = time.time()
    other = build_engine(SEED_OTHER, 'other')
    print(f'  Other 起動 ({time.time()-t2:.1f}s)')
    print(f'  3 instance 起動 計 ({time.time()-t0:.1f}s)')

    rows = []
    loop_log = []
    for w in range(WINDOWS):
        center.step_window(steps=WINDOW_STEPS)
        atom.step_window(steps=WINDOW_STEPS)
        loop_info = run_attention_loop_b(center, atom, other, w)
        loop_log.append(loop_info)
        tp = loop_info.get('target_phase')
        obs = observe_atom(atom, w, target_phase=tp if tp is not None else 0.0)
        rows.append({'condition': 'with_center', 'window': w, **obs,
                      'fired': loop_info['fired'],
                      'target_phase': tp,
                      'lambda_dyn': loop_info.get('lambda_dyn'),
                      'max_w': loop_info.get('max_w', 0.0),
                      'atom_inject_n': loop_info['atom_inject_n']})
        print(f'  w={w} labels={obs["labels_total"]} '
              f'pct_5+={obs["pct_n_core_5plus"]:.2f}% '
              f'occ_max={obs["occ_max"]:.3f} '
              f'stress={obs["stress_intensity"]:.3f} '
              f'fire={loop_info["fired"]} max_w={loop_info.get("max_w", 0):.3f} '
              f'tp={tp:.2f if tp is not None else 0:.2f} '
              f'near={obs["near_far_near_occ_sum"]:.3f} '
              f'far={obs["near_far_far_occ_sum"]:.3f}')
    print(f'  done ({time.time()-t0:.1f}s)')
    return pd.DataFrame(rows), pd.DataFrame(loop_log), time.time() - t0


def main():
    print('=== 注意センター Step B smoke (phase 向き先 + stress=True + 近傍遠方) ===\n')
    t_main = time.time()

    df_no, dt_no = run_no_center()
    df_with, df_loop, dt_with = run_with_center()

    full = pd.concat([df_no, df_with], ignore_index=True, sort=False)
    full.to_parquet(OUT_DIR / 'smoke_b_full.parquet', index=False)
    df_loop.to_parquet(OUT_DIR / 'smoke_b_loop_log.parquet', index=False)

    # 観察事実 (Web Claude §5 不変条件: 判定置かない)
    print('\n=== 観察事実 (最終 window、判定置かない) ===')
    KEYS = ['labels_total', 'n_core_mean', 'pct_n_core_2', 'pct_n_core_5plus',
            'share_mean', 'share_max', 'alive_l_count', 'labels_active',
            'torque_events', 'stress_intensity',
            'occ_max', 'occ_mean', 'occ_nonzero',
            'near_far_near_occ_sum', 'near_far_far_occ_sum',
            'near_far_near_far_ratio']
    for cond in ['no_center', 'with_center']:
        sub = full[full['condition'] == cond]
        if len(sub) == 0:
            continue
        last = sub.iloc[-1]
        print(f'\n  [{cond}]')
        for k in KEYS:
            v = last.get(k)
            if v is None or (isinstance(v, float) and np.isnan(v)):
                continue
            if isinstance(v, (int, float)):
                print(f'    {k}: {v:.4f}')
            else:
                print(f'    {k}: {v}')

    print('\n--- 差 (with_center - no_center)、最終 window ---')
    nc = full[full['condition'] == 'no_center'].iloc[-1]
    wc = full[full['condition'] == 'with_center'].iloc[-1]
    diffs = {}
    for k in KEYS:
        try:
            d = float(wc[k]) - float(nc[k])
            rel = abs(d) / (abs(float(nc[k])) + 1e-9)
            diffs[k] = d
            marker = '★' if rel > 0.05 else ' '
            print(f'  {marker} {k:30s} Δ = {d:+.4f}  (rel {rel:.2%})')
        except (KeyError, TypeError, ValueError):
            pass

    n_fired = int(df_loop['fired'].sum())
    print(f'\n  発火回数: {n_fired}/{len(df_loop)}')

    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'seeds': {'atom': SEED_ATOM, 'center': SEED_CENTER, 'other': SEED_OTHER},
        'N': V82_N, 'windows': WINDOWS, 'window_steps': WINDOW_STEPS,
        'other_steps': OTHER_STEPS, 'K_target': K_TARGET, 'K_near': K_NEAR,
        'timing_no_center_sec': dt_no,
        'timing_with_center_sec': dt_with,
        'total_sec': time.time() - t_main,
        'n_fired_total': n_fired,
        'diffs_final_window': diffs,
    }
    (OUT_DIR / 'smoke_b_run_summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))

    print(f'\n=== smoke B 完了 total {time.time()-t_main:.1f}s ===')


if __name__ == '__main__':
    main()
