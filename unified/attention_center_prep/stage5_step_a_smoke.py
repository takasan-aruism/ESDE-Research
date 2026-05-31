#!/usr/bin/env python3
"""注意センター ESDE — 機能設計 v1 確定後 smoke (Step A)

確定アーキ (機能設計 v1 §1):
- Atom 系: V82Engine(N=5000, seed=42) + VirtualLayerV9 (cog なし、簡素化)
- センター: V82Engine(N=5000, seed=99) + VirtualLayerV9 (cog なし、常駐)
- 別系: V82Engine(N=5000, seed=100) + VirtualLayerV9 (cog なし、素)

注: 機能設計 v1 確定 ② は「cog/Atom 上っぱりだけ外す、物理切らない」。
Atom 系の cog は本実装で外す (simplification、CID = labels で代用、Web Claude 確認可)。

2 conditions:
- no_center: Atom 系のみ走らせる baseline
- with_center: 機能 1-3 で 1 往復、source_event 1 本

観察 (機能設計 v1 §3):
- (a) CID 構造: labels 数 / n_core 分布 (Atom 系 labels[lid]["nodes"] から)
- (b) Integration 入口: (Integration は v104 別実装、本 smoke では未統合)
- (c) phase 分布: virtual_stats / phase_snapshots

dynamic_threshold (本 smoke 案 A、両辺 state-dependent):
  should_attend = z_score_of_max_E > stress_intensity

判定置かない (Web Claude §5 不変条件): 観察事実のみ記録、success/fail なし
"""
import sys, json, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
STAGE5 = REPO / 'unified/attention_center_prep'
OUT_DIR = STAGE5 / 'run_smoke_a'
SANDBOX = STAGE5 / 'sandbox_a'
OUT_DIR.mkdir(parents=True, exist_ok=True)
SANDBOX.mkdir(parents=True, exist_ok=True)

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
OTHER_STEPS = 5  # 別系の数 step (1 往復で進める)
K_TARGET = 5     # 翻訳 K


def build_engine(seed, tag):
    """同型 V82Engine + VirtualLayerV9 (機能設計 v1 §1)、cog なし"""
    encap = V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)
    engine = V82Engine(seed=seed, N=V82_N, encap_params=encap)
    engine.virtual = VirtualLayerV9(feedback_gamma=0.10,
                                     feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True
    engine.run_injection()
    return engine


# ========================================================
# dynamic_threshold (案 A、両辺 state-dependent、固定値なし)
# ========================================================
def should_attend(center_engine):
    """センター state から発火判定 (z_score_of_max_E > stress_intensity)"""
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


def derive_attention_targets(center_engine, K=K_TARGET):
    """センター state.E top-K (state 由来)"""
    alive = sorted(center_engine.state.alive_n)
    if not alive:
        return []
    e_vals = {n: float(center_engine.state.E.get(n, 0.0)) for n in alive}
    return sorted(alive, key=lambda n: -e_vals[n])[:K]


def map_to_atom_cids(atom_engine, target_node_ids):
    """センターが指した node ID 集合 → Atom 系 label との overlap"""
    macro = set(atom_engine.virtual.macro_nodes)
    pointed = []
    target_set = set(target_node_ids)
    for lid, lab in atom_engine.virtual.labels.items():
        if lid in macro:
            continue
        overlap = set(lab['nodes']) & target_set
        if overlap:
            pointed.append({
                'lid': lid,
                'overlap_count': len(overlap),
                'overlap_nodes': list(overlap),
                'label_n_core': len(lab['nodes']),
            })
    return pointed


def translate_other_to_atom(other_engine, K=K_TARGET):
    """別系 state.E top-K → Atom 系へ書き戻す target_nodes"""
    alive = sorted(other_engine.state.alive_n)
    if not alive:
        return []
    e_vals = {n: float(other_engine.state.E.get(n, 0.0)) for n in alive}
    return sorted(alive, key=lambda n: -e_vals[n])[:K]


def run_attention_loop(center_engine, atom_engine, other_engine, w):
    """1 往復 (機能 3、Web Claude §2 確定フロー)"""
    fire, fire_info = should_attend(center_engine)
    if not fire:
        return {'window': w, 'fired': False, **fire_info,
                'overlap_n_labels': 0, 'overlap_n_nodes': 0,
                'other_step_done': False, 'atom_inject_n': 0}
    # 機能 2: 向き先
    target_ids = derive_attention_targets(center_engine, K=K_TARGET)
    if not target_ids:
        return {'window': w, 'fired': True, **fire_info,
                'overlap_n_labels': 0, 'overlap_n_nodes': 0,
                'other_step_done': False, 'atom_inject_n': 0}
    # 機能 3: Atom 系の overlap
    pointed = map_to_atom_cids(atom_engine, target_ids)
    overlap_nodes = []
    for p in pointed:
        overlap_nodes.extend(p['overlap_nodes'])
    overlap_nodes = list(set(overlap_nodes))  # 重複除去
    if not overlap_nodes:
        # overlap なくても target_ids を別系へ inject (target がそのまま)
        overlap_nodes = target_ids
    # 別系へ source_event で inject
    other_engine.physics.inject(other_engine.state,
                                 target_nodes=list(overlap_nodes))
    other_engine.step_window(steps=OTHER_STEPS)
    other_step_done = True
    # 別系結果を翻訳
    new_targets = translate_other_to_atom(other_engine, K=K_TARGET)
    if not new_targets:
        return {'window': w, 'fired': True, **fire_info,
                'overlap_n_labels': len(pointed),
                'overlap_n_nodes': len(overlap_nodes),
                'other_step_done': other_step_done, 'atom_inject_n': 0}
    # Atom 系へ書き戻し (source_event 1 本)
    atom_engine.physics.inject(atom_engine.state, target_nodes=new_targets)
    return {'window': w, 'fired': True, **fire_info,
            'overlap_n_labels': len(pointed),
            'overlap_n_nodes': len(overlap_nodes),
            'other_step_done': other_step_done,
            'atom_inject_n': len(new_targets)}


# ========================================================
# 観察 ((a) CID 構造、(c) phase 分布)
# ========================================================
def observe_atom(atom_engine, window_idx):
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

    # phase 分布 (c)、VirtualLayer occupancy / history
    occ = atom_engine.virtual.occupancy or []
    occ_max = max(occ) if occ else 0.0
    occ_mean = float(np.mean(occ)) if occ else 0.0
    occ_nonzero = sum(1 for v in occ if v > 0.001)

    vs = atom_engine.virtual_stats or {}
    return {
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
        # phase 分布 (c)
        'occ_max': occ_max,
        'occ_mean': occ_mean,
        'occ_nonzero': occ_nonzero,
    }


def run_no_center():
    print('\n=== no_center: Atom 系のみ ===')
    t0 = time.time()
    atom = build_engine(SEED_ATOM, 'atom')
    print(f'  Atom 起動 ({time.time()-t0:.1f}s) alive_l={len(atom.state.alive_l)}')
    rows = []
    for w in range(WINDOWS):
        atom.step_window(steps=WINDOW_STEPS)
        obs = observe_atom(atom, w)
        rows.append({'condition': 'no_center', 'window': w, **obs})
        print(f'  w={w} labels={obs["labels_total"]} '
              f'pct_2={obs["pct_n_core_2"]:.1f}% '
              f'occ_nonzero={obs["occ_nonzero"]} '
              f'alive_l={obs["alive_l_count"]} '
              f'torque={obs["torque_events"]}')
    print(f'  done ({time.time()-t0:.1f}s)')
    return pd.DataFrame(rows), time.time() - t0


def run_with_center():
    print('\n=== with_center: 3 instance (Atom + Center + Other) ===')
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
        # センター + 別系 + Atom 系を同期 step (window 1 つずつ)
        center.step_window(steps=WINDOW_STEPS)
        atom.step_window(steps=WINDOW_STEPS)
        # 1 往復 (発火判定込み)
        loop_info = run_attention_loop(center, atom, other, w)
        loop_log.append(loop_info)
        # Atom 系を観察 (inject 後)
        obs = observe_atom(atom, w)
        rows.append({'condition': 'with_center', 'window': w,
                      **obs,
                      'fired': loop_info['fired'],
                      'overlap_n_labels': loop_info['overlap_n_labels'],
                      'atom_inject_n': loop_info['atom_inject_n']})
        print(f'  w={w} labels={obs["labels_total"]} '
              f'pct_2={obs["pct_n_core_2"]:.1f}% '
              f'occ_nonzero={obs["occ_nonzero"]} '
              f'fired={loop_info["fired"]} '
              f'overlap_labels={loop_info["overlap_n_labels"]} '
              f'inject_n={loop_info["atom_inject_n"]}')
    print(f'  done ({time.time()-t0:.1f}s)')
    return pd.DataFrame(rows), pd.DataFrame(loop_log), time.time() - t0


def main():
    print('=== 注意センター ESDE smoke (Step A) ===\n')
    t_main = time.time()

    # no_center baseline
    df_no, dt_no = run_no_center()

    # with_center
    df_with, df_loop, dt_with = run_with_center()

    # 結合
    full = pd.concat([df_no, df_with], ignore_index=True, sort=False)
    full.to_parquet(OUT_DIR / 'smoke_a_full.parquet', index=False)
    df_loop.to_parquet(OUT_DIR / 'smoke_a_loop_log.parquet', index=False)

    # 観察事実 (判定置かない、§5 不変条件)
    print('\n=== 観察事実 (最終 window、判定置かない) ===')
    KEYS = ['labels_total', 'n_core_mean', 'pct_n_core_2', 'pct_n_core_5plus',
            'share_mean', 'share_max', 'age_mean',
            'alive_n_count', 'alive_l_count', 'labels_active', 'torque_events',
            'occ_max', 'occ_mean', 'occ_nonzero']
    for cond in ['no_center', 'with_center']:
        last = full[full['condition'] == cond].iloc[-1]
        print(f'\n  [{cond}]')
        for k in KEYS:
            print(f'    {k}: {last[k]:.3f}' if isinstance(last[k], (int, float))
                  else f'    {k}: {last[k]}')

    print('\n--- 差 (with_center - no_center)、最終 window ---')
    nc = full[full['condition'] == 'no_center'].iloc[-1]
    wc = full[full['condition'] == 'with_center'].iloc[-1]
    diffs = {}
    for k in KEYS:
        d = float(wc[k]) - float(nc[k])
        rel = abs(d) / (abs(float(nc[k])) + 1e-9)
        diffs[k] = d
        print(f'  {k:20s} Δ = {d:+.4f}  (rel {rel:.2%})')

    # 発火回数
    n_fired = int(df_loop['fired'].sum())
    print(f'\n  発火回数: {n_fired}/{len(df_loop)}')

    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'seeds': {'atom': SEED_ATOM, 'center': SEED_CENTER, 'other': SEED_OTHER},
        'N': V82_N, 'windows': WINDOWS, 'window_steps': WINDOW_STEPS,
        'other_steps': OTHER_STEPS, 'K_target': K_TARGET,
        'timing_no_center_sec': dt_no,
        'timing_with_center_sec': dt_with,
        'total_sec': time.time() - t_main,
        'n_fired_total': n_fired,
        'diffs_final_window': diffs,
    }
    (OUT_DIR / 'smoke_a_run_summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))

    print(f'\n=== smoke (Step A) 完了 total {time.time()-t_main:.1f}s ===')
    print(f'  -> {OUT_DIR}/smoke_a_full.parquet ({len(full)} rows)')
    print(f'  -> {OUT_DIR}/smoke_a_loop_log.parquet ({len(df_loop)} rows)')
    print(f'  -> {OUT_DIR}/smoke_a_run_summary.json')


if __name__ == '__main__':
    main()
