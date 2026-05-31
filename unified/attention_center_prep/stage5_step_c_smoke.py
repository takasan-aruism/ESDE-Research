#!/usr/bin/env python3
"""注意センター ESDE — Step C smoke (繰り返し接触 → 差分的残留、時間が主軸)

Web Claude Step C 機能設計準拠:
- 駆動 1 文: 繰り返し接触の中で別系に関係するものが選択的に残るか
- windows を長く (decay 半減期基準): FAMILIARITY 半減期 ~3.5 window × ~4 = 15 windows
- 3 conditions: no_center / center_no_other / center_other (別系帰属の最小対比)
- 接触頻度マップ (phase bin 64 ごとの累積接触回数)
- 残留カーブ (よく触れた bin vs 触れてない bin の occupancy 時系列)
- 増減の向きは記録、成功基準にしない (Taka 指示)

Step B からの変更:
- WINDOWS 5 → 15 (decay 根拠)
- conditions 2 → 3 (no_center / center_no_other / center_other)
- 接触頻度マップ追加
- 残留カーブ追加 (接触頻度で層化)
"""
import sys, json, time, math
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
STAGE5 = REPO / 'unified/attention_center_prep'
OUT_DIR = STAGE5 / 'run_smoke_c'
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
# decay 半減期根拠 (primitive/v910/v910_pulse_model.py:99-100):
# ATTENTION_DECAY=0.99 → 半減期 ~69 step ≈ 0.69 window
# FAMILIARITY_DECAY=0.998 → 半減期 ~346 step ≈ 3.46 window
# Code A 提案: FAMILIARITY 半減期 × 4 ≈ 14 → 15 windows (累積効果が出る長さ)
WINDOWS = 15
WINDOW_STEPS = 100
OTHER_STEPS = 5
K_TARGET = 5
K_NEAR = 3
N_BINS = 64  # virtual_layer_v9 N_BINS


def build_engine(seed, tag):
    encap = V82EncapsulationParams(stress_enabled=True, virtual_enabled=True)
    engine = V82Engine(seed=seed, N=V82_N, encap_params=encap)
    engine.virtual = VirtualLayerV9(feedback_gamma=0.10,
                                     feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True
    engine.run_injection()
    return engine


# ========================================================
# 機能 (Step B から流用、変更なし)
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
    stress = float(ss.get('stress_intensity', 1.0))
    fire = z_score > stress
    return fire, {'z_score': z_score, 'stress': stress,
                  'mean_E': mean_E, 'std_E': std_E, 'max_E': max_E}


def derive_center_target_phase(center_engine, K=K_TARGET):
    alive = sorted(center_engine.state.alive_n)
    if not alive:
        return None
    e_vals = {n: float(center_engine.state.E.get(n, 0.0)) for n in alive}
    top_K = sorted(alive, key=lambda n: -e_vals[n])[:K]
    thetas = [float(center_engine.state.theta[n]) for n in top_K]
    if not thetas:
        return None
    cos_sum = sum(math.cos(t) for t in thetas)
    sin_sum = sum(math.sin(t) for t in thetas)
    target_phase = math.atan2(sin_sum / len(thetas), cos_sum / len(thetas))
    return target_phase % (2 * math.pi)


def compute_lambda_dynamic(center_engine):
    """λ を center 側 labels の phase 分散から (Taka 2026-06-01 指示)"""
    macro = set(center_engine.virtual.macro_nodes)
    phase_sigs = [lab['phase_sig'] for lid, lab in center_engine.virtual.labels.items()
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
    d = abs(a - b) % (2 * math.pi)
    return min(d, 2 * math.pi - d)


def compute_label_weights(atom_engine, target_phase, lambda_dyn):
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
    if not weights:
        return []
    sorted_lids = sorted(weights.keys(), key=lambda l: -weights[l]['w'])
    candidate_nodes = []
    for lid in sorted_lids[:max(K, 3)]:
        for n in weights[lid]['nodes']:
            if n in atom_engine.state.alive_n:
                candidate_nodes.append(n)
    candidate_nodes = list(set(candidate_nodes))
    if not candidate_nodes:
        return []
    e_vals = {n: float(atom_engine.state.E.get(n, 0.0)) for n in candidate_nodes}
    return sorted(candidate_nodes, key=lambda n: -e_vals[n])[:K]


def translate_other_to_atom(other_engine, K=K_TARGET):
    alive = sorted(other_engine.state.alive_n)
    if not alive:
        return []
    e_vals = {n: float(other_engine.state.E.get(n, 0.0)) for n in alive}
    return sorted(alive, key=lambda n: -e_vals[n])[:K]


# ========================================================
# Step C: 1 往復 (use_other = False で別系飛ばし)
# ========================================================
def run_attention_loop_c(center_engine, atom_engine, other_engine, w, use_other):
    fire, fire_info = should_attend(center_engine)
    info = {'window': w, 'fired': False, 'target_phase': None,
            'lambda_dyn': None, 'max_w': 0.0, 'atom_inject_n': 0,
            'use_other': use_other, **fire_info}
    if not fire:
        return info
    target_phase = derive_center_target_phase(center_engine, K_TARGET)
    if target_phase is None:
        info['fired'] = True
        return info
    lambda_dyn = compute_lambda_dynamic(center_engine)
    weights = compute_label_weights(atom_engine, target_phase, lambda_dyn)
    max_w = max((wt['w'] for wt in weights.values()), default=0.0)
    target_nodes = derive_targets_from_weights(weights, atom_engine, K_TARGET)
    info.update({'fired': True, 'target_phase': float(target_phase),
                  'lambda_dyn': float(lambda_dyn), 'max_w': float(max_w)})
    if not target_nodes:
        return info
    if use_other:
        # center_other: フルループ (別系を通す)
        other_engine.physics.inject(other_engine.state,
                                     target_nodes=list(target_nodes))
        other_engine.step_window(steps=OTHER_STEPS)
        new_targets = translate_other_to_atom(other_engine, K_TARGET)
    else:
        # center_no_other: 別系飛ばし、狙った node をそのまま書き戻し
        new_targets = target_nodes
    if new_targets:
        atom_engine.physics.inject(atom_engine.state, target_nodes=new_targets)
        info['atom_inject_n'] = len(new_targets)
    return info


# ========================================================
# 接触頻度マップ + 残留カーブ (Web Claude §2)
# ========================================================
def update_contact_map(contact_map, target_phase, K_NEAR=K_NEAR):
    """target_phase 近傍 (±K_NEAR bins) の接触回数を累積"""
    if target_phase is None:
        return
    # virtual_layer_v9._phase_bin 相当
    BIN_WIDTH = 2 * math.pi / N_BINS
    target_bin = int(target_phase / BIN_WIDTH)
    target_bin = min(target_bin, N_BINS - 1)
    for d in range(-K_NEAR, K_NEAR + 1):
        b = (target_bin + d) % N_BINS
        contact_map[b] += 1


def stratify_occupancy_by_contact(occ, contact_map, top_q=0.25):
    """occupancy を接触頻度で層化:
       high_contact = 接触上位 top_q (デフォルト 25%) bin
       low_contact = 接触下位 top_q bin
       remaining = 中間
    """
    if not occ or len(occ) != N_BINS:
        return {'high_occ_sum': 0.0, 'low_occ_sum': 0.0, 'mid_occ_sum': 0.0,
                'n_high': 0, 'n_low': 0,
                'high_occ_mean': 0.0, 'low_occ_mean': 0.0,
                'high_low_ratio': 0.0}
    sorted_bins = np.argsort(-contact_map)  # 降順
    n_top = max(1, int(N_BINS * top_q))
    high_bins = set(sorted_bins[:n_top].tolist())
    low_bins = set(sorted_bins[-n_top:].tolist())
    high_sum = sum(occ[b] for b in high_bins)
    low_sum = sum(occ[b] for b in low_bins)
    mid_sum = sum(occ[b] for b in range(N_BINS)
                  if b not in high_bins and b not in low_bins)
    return {
        'high_occ_sum': float(high_sum),
        'low_occ_sum': float(low_sum),
        'mid_occ_sum': float(mid_sum),
        'n_high': int(len(high_bins)),
        'n_low': int(len(low_bins)),
        'high_occ_mean': float(high_sum / len(high_bins)) if high_bins else 0.0,
        'low_occ_mean': float(low_sum / len(low_bins)) if low_bins else 0.0,
        'high_low_ratio': float(high_sum / (low_sum + 1e-9)),
    }


# ========================================================
# 観察
# ========================================================
def observe_atom(atom_engine, window_idx, contact_map):
    macro = set(atom_engine.virtual.macro_nodes)
    non_macro = {lid: lab for lid, lab in atom_engine.virtual.labels.items()
                  if lid not in macro}
    n_core_list = [len(lab['nodes']) for lab in non_macro.values()]
    share_list = [lab['share'] for lab in non_macro.values()]
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
        'pct_n_core_5plus': (sum(1 for n in n_core_list if n >= 5)
                              / max(total, 1)) * 100,
        'share_mean': float(np.mean(share_list)) if share_list else 0.0,
        'share_max': float(max(share_list)) if share_list else 0.0,
        'alive_l_count': len(atom_engine.state.alive_l),
        'labels_active': vs.get('labels_active', 0),
        'torque_events': vs.get('torque_events', 0),
        'stress_intensity': float(ss.get('stress_intensity', 1.0)),
        'occ_max': occ_max,
        'occ_mean': occ_mean,
        'occ_nonzero': occ_nonzero,
    }
    # 残留カーブ用層化
    strat = stratify_occupancy_by_contact(occ, contact_map, top_q=0.25)
    obs.update({f'strat_{k}': v for k, v in strat.items()})
    return obs


def run_condition(cond_name):
    """1 condition を 15 windows 走らせる"""
    print(f'\n=== {cond_name} ===')
    t0 = time.time()
    atom = build_engine(SEED_ATOM, 'atom')
    print(f'  Atom 起動 ({time.time()-t0:.1f}s)')
    center = None
    other = None
    if cond_name in ('center_no_other', 'center_other'):
        t1 = time.time()
        center = build_engine(SEED_CENTER, 'center')
        print(f'  Center 起動 ({time.time()-t1:.1f}s)')
    if cond_name == 'center_other':
        t2 = time.time()
        other = build_engine(SEED_OTHER, 'other')
        print(f'  Other 起動 ({time.time()-t2:.1f}s)')
    print(f'  起動 計 ({time.time()-t0:.1f}s)')

    # 接触頻度マップ (この condition で進行とともに累積)
    contact_map = np.zeros(N_BINS)
    rows = []
    loop_log = []
    for w in range(WINDOWS):
        atom.step_window(steps=WINDOW_STEPS)
        if center is not None:
            center.step_window(steps=WINDOW_STEPS)
            use_other = (cond_name == 'center_other')
            loop_info = run_attention_loop_c(center, atom, other, w, use_other)
            loop_log.append({'condition': cond_name, **loop_info})
            if loop_info['fired'] and loop_info['target_phase'] is not None:
                update_contact_map(contact_map, loop_info['target_phase'], K_NEAR)
        # 観察 (window 末、その時点の contact_map で層化)
        obs = observe_atom(atom, w, contact_map)
        rows.append({'condition': cond_name, 'window': w,
                      'contact_map_sum': float(contact_map.sum()),
                      'contact_map_max': float(contact_map.max()),
                      **obs})
        print(f'  w={w} labels={obs["labels_total"]} '
              f'high_occ={obs["strat_high_occ_sum"]:.3f} '
              f'low_occ={obs["strat_low_occ_sum"]:.3f} '
              f'ratio={obs["strat_high_low_ratio"]:.3f} '
              f'contact_max={contact_map.max():.0f}')
    elapsed = time.time() - t0
    print(f'  done ({elapsed:.1f}s)')
    return pd.DataFrame(rows), pd.DataFrame(loop_log), elapsed, contact_map


def main():
    print('=== 注意センター Step C smoke (繰り返し接触 → 差分的残留) ===\n')
    print(f'  WINDOWS={WINDOWS} (FAMILIARITY 半減期 ~3.5 window × ~4)\n')
    t_main = time.time()
    all_rows = []
    all_loops = []
    timing = {}
    contact_maps = {}
    for cond in ['no_center', 'center_no_other', 'center_other']:
        df, df_loop, dt, cm = run_condition(cond)
        all_rows.append(df)
        all_loops.append(df_loop)
        timing[cond] = dt
        contact_maps[cond] = cm.tolist()

    full = pd.concat(all_rows, ignore_index=True, sort=False)
    full.to_parquet(OUT_DIR / 'smoke_c_full.parquet', index=False)
    if all_loops:
        loop_df = pd.concat(all_loops, ignore_index=True, sort=False)
        loop_df.to_parquet(OUT_DIR / 'smoke_c_loop_log.parquet', index=False)

    # 観察事実 (Web Claude §5 不変条件: 判定置かない)
    # 最終 window の対比 + 時系列で差が開いたか
    print('\n=== 観察事実 (時間方向の差分的残留、判定置かない) ===')
    for cond in ['no_center', 'center_no_other', 'center_other']:
        sub = full[full['condition'] == cond]
        if len(sub) == 0:
            continue
        first = sub.iloc[0]
        last = sub.iloc[-1]
        print(f'\n  [{cond}]')
        print(f'    final labels: {int(last["labels_total"])}')
        print(f'    final high_occ_sum: {last["strat_high_occ_sum"]:.4f}')
        print(f'    final low_occ_sum: {last["strat_low_occ_sum"]:.4f}')
        print(f'    final high_low_ratio: {last["strat_high_low_ratio"]:.4f}')
        # 時間変化: 最初と最後の比
        first_ratio = float(first["strat_high_low_ratio"])
        last_ratio = float(last["strat_high_low_ratio"])
        d_ratio = last_ratio - first_ratio
        print(f'    Δ high_low_ratio (last - first): {d_ratio:+.4f}')

    # 別系帰属の最終差分
    print('\n--- 帰属差分 (center_other - center_no_other)、最終 window ---')
    if 'center_other' in full['condition'].values and \
       'center_no_other' in full['condition'].values:
        co = full[full['condition'] == 'center_other'].iloc[-1]
        cn = full[full['condition'] == 'center_no_other'].iloc[-1]
        KEYS = ['labels_total', 'pct_n_core_5plus', 'share_max',
                'torque_events', 'alive_l_count',
                'strat_high_occ_sum', 'strat_low_occ_sum',
                'strat_high_low_ratio']
        for k in KEYS:
            try:
                d = float(co[k]) - float(cn[k])
                rel = abs(d) / (abs(float(cn[k])) + 1e-9)
                marker = '★' if rel > 0.05 else ' '
                print(f'  {marker} {k:30s} Δ = {d:+.4f}  (rel {rel:.2%})')
            except Exception:
                pass

    # 発火集計
    if all_loops:
        for cond in ['center_no_other', 'center_other']:
            ll = loop_df[loop_df['condition'] == cond]
            n_fire = int(ll['fired'].sum())
            print(f'\n  [{cond}] 発火: {n_fire}/{len(ll)}')

    # contact_map (どこを触れたか) を json で保存
    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'seeds': {'atom': SEED_ATOM, 'center': SEED_CENTER, 'other': SEED_OTHER},
        'N': V82_N, 'windows': WINDOWS, 'window_steps': WINDOW_STEPS,
        'other_steps': OTHER_STEPS, 'K_target': K_TARGET, 'K_near': K_NEAR,
        'timing_sec': timing,
        'total_sec': time.time() - t_main,
        'contact_maps': contact_maps,
    }
    (OUT_DIR / 'smoke_c_run_summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))

    print(f'\n=== smoke C 完了 total {time.time()-t_main:.1f}s ===')


if __name__ == '__main__':
    main()
