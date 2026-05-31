#!/usr/bin/env python3
"""第 4 段階 Step B — 改修小 smoke (条件をあれこれ変動して loop への影響を見る)

Web Claude 指示準拠:
- 温度感「あれこれ試して結果を見る」、精緻に詰めない
- A (現状) vs B (変動) で loop への影響観察
- 改修小の条件 (maturation_alpha / stress / semantic_pressure) から
- 神の手回避: loop 崩れる条件を狙わず、変動の結果を観察

観察:
- CID 層 (engine.virtual.labels): 寿命、n_core 分布 (v10.4 ベースライン比較)、CID 数推移
- loop: labels_active 振動、torque_events、alive_l

5 conditions × 5 windows × N=5000 (約 20-25 分)
外部接続なし、純粋な engine 動作 (第 3 段階の inject ループとは別)
"""
import sys, json, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
STAGE4 = REPO / 'unified/stage4_loop'
OUT_DIR = STAGE4 / 'run_smoke'
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
from esde_v43_engine import SemanticPressureParams
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9

SEED = 42
MATURATION_WINDOWS = 3
TRACKING_WINDOWS = 2
WINDOW_STEPS = 100
N_NODES = V82_N

# Conditions: あれこれ試す (改修小から)
CONDITIONS = [
    ('A_baseline',          {'maturation_alpha': 0.10, 'stress_enabled': False,
                              'pressure_prob': 0.005, 'inject_amount': 0.6}),
    ('B1_mat_alpha_low',    {'maturation_alpha': 0.05, 'stress_enabled': False,
                              'pressure_prob': 0.005, 'inject_amount': 0.6}),
    ('B2_mat_alpha_high',   {'maturation_alpha': 0.20, 'stress_enabled': False,
                              'pressure_prob': 0.005, 'inject_amount': 0.6}),
    ('B3_stress_on',        {'maturation_alpha': 0.10, 'stress_enabled': True,
                              'pressure_prob': 0.005, 'inject_amount': 0.6}),
    ('B4_pressure_high',    {'maturation_alpha': 0.10, 'stress_enabled': False,
                              'pressure_prob': 0.05,  'inject_amount': 0.6}),
    ('B5_inject_amount_low',{'maturation_alpha': 0.10, 'stress_enabled': False,
                              'pressure_prob': 0.005, 'inject_amount': 0.2}),
]


def build_engine(seed, cfg):
    """各 condition の engine を起動 (補足の起動手順準拠)"""
    encap = V82EncapsulationParams(stress_enabled=cfg['stress_enabled'],
                                    virtual_enabled=True)
    engine = V82Engine(seed=seed, N=N_NODES, encap_params=encap,
                        maturation_alpha=cfg['maturation_alpha'])
    # pressure_params 上書き
    engine.pressure_params = SemanticPressureParams(
        pressure_prob=cfg['pressure_prob'])
    # inject_amount 上書き (physics.params)
    engine.physics.params.inject_amount = cfg['inject_amount']
    # VirtualLayerV9 で置換
    engine.virtual = VirtualLayerV9(feedback_gamma=0.10,
                                     feedback_clamp=(0.8, 1.2),
                                     maturation_alpha=cfg['maturation_alpha'])
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True
    engine.run_injection()
    return engine


def label_snapshot(engine, window_idx):
    """label (CID 層) 全体 + n_core 分布 snapshot"""
    macro = set(engine.virtual.macro_nodes)
    non_macro_labels = {lid: lab for lid, lab in engine.virtual.labels.items()
                        if lid not in macro}
    # n_core 分布 (label の nodes frozenset サイズ)
    n_core_list = [len(lab['nodes']) for lab in non_macro_labels.values()]
    # share 分布 (label の現存度)
    share_list = [lab['share'] for lab in non_macro_labels.values()]
    # age 分布 (window_count - born)
    age_list = [window_idx - lab['born'] for lab in non_macro_labels.values()]

    n_core_counter = {}
    for n in n_core_list:
        n_core_counter[n] = n_core_counter.get(n, 0) + 1

    total = len(non_macro_labels)
    return {
        'labels_total': total,
        'n_core_mean': float(np.mean(n_core_list)) if n_core_list else 0.0,
        'n_core_median': float(np.median(n_core_list)) if n_core_list else 0.0,
        'n_core_max': max(n_core_list) if n_core_list else 0,
        'pct_n_core_2': (n_core_counter.get(2, 0) / max(total, 1)) * 100,
        'pct_n_core_3': (n_core_counter.get(3, 0) / max(total, 1)) * 100,
        'pct_n_core_4plus': (sum(c for n, c in n_core_counter.items() if n >= 4)
                              / max(total, 1)) * 100,
        'pct_n_core_5plus': (sum(c for n, c in n_core_counter.items() if n >= 5)
                              / max(total, 1)) * 100,
        'share_mean': float(np.mean(share_list)) if share_list else 0.0,
        'share_max': float(max(share_list)) if share_list else 0.0,
        'age_mean': float(np.mean(age_list)) if age_list else 0.0,
        'age_max': max(age_list) if age_list else 0,
    }


def global_snapshot(engine):
    vs = engine.virtual_stats or {}
    ss = engine.stress_stats or {}
    return {
        'alive_n_count': len(engine.state.alive_n),
        'alive_l_count': len(engine.state.alive_l),
        'labels_active': vs.get('labels_active', 0),
        'labels_born': vs.get('labels_born', 0),
        'labels_died': vs.get('labels_died', 0),
        'torque_events': vs.get('torque_events', 0),
        'mean_omega': float(ss.get('mean_omega', 0.0)),
        'stressed': ss.get('stressed', 0),
        'stress_intensity': float(ss.get('stress_intensity', 1.0)),
    }


def run_condition(seed, name, cfg):
    """1 condition で 5 windows 走らせて、CID 寿命/n_core 分布/loop 動態を記録"""
    print(f'\n=== {name} === cfg={cfg}')
    t0 = time.time()
    engine = build_engine(seed, cfg)
    print(f'  run_injection done ({time.time()-t0:.1f}s) '
          f'alive_n={len(engine.state.alive_n)} '
          f'alive_l={len(engine.state.alive_l)}')

    rows = []
    total_w = MATURATION_WINDOWS + TRACKING_WINDOWS
    for w in range(total_w):
        engine.step_window(steps=WINDOW_STEPS)
        ls = label_snapshot(engine, w)
        gs = global_snapshot(engine)
        row = {'condition': name, 'window': w,
               **ls,
               **{f'g_{k}': v for k, v in gs.items()}}
        rows.append(row)
        print(f'  w={w} labels={ls["labels_total"]} '
              f'n_core_mean={ls["n_core_mean"]:.2f} '
              f'pct_2={ls["pct_n_core_2"]:.1f}% '
              f'pct_5plus={ls["pct_n_core_5plus"]:.1f}% '
              f'share_max={ls["share_max"]:.3f} '
              f'age_max={ls["age_max"]} '
              f'g_alive_l={gs["alive_l_count"]} '
              f'g_torque={gs["torque_events"]}')

    elapsed = time.time() - t0
    print(f'  done ({elapsed:.1f}s)')
    return pd.DataFrame(rows), elapsed


def main():
    print('=== 第 4 段階 Step B smoke (改修小 5-6 conditions) ===\n')
    t_main = time.time()
    all_rows = []
    timing = {}
    for name, cfg in CONDITIONS:
        df, dt = run_condition(SEED, name, cfg)
        all_rows.append(df)
        timing[name] = dt

    full = pd.concat(all_rows, ignore_index=True)
    full.to_parquet(OUT_DIR / 'smoke_full.parquet', index=False)

    # 比較サマリ (最終 window)
    print('\n=== 最終 window 比較 ===')
    METRICS = ['labels_total', 'n_core_mean', 'pct_n_core_2', 'pct_n_core_5plus',
               'share_mean', 'share_max', 'age_mean', 'age_max',
               'g_alive_l_count', 'g_labels_active', 'g_torque_events',
               'g_stress_intensity']
    last_rows = []
    for name, _ in CONDITIONS:
        sub = full[full['condition'] == name].iloc[-1]
        d = {'condition': name}
        for m in METRICS:
            d[m] = float(sub[m])
        last_rows.append(d)
    last_df = pd.DataFrame(last_rows)
    last_df.to_parquet(OUT_DIR / 'smoke_last_window.parquet', index=False)
    print(last_df.to_string(index=False))

    # v10.4 ベースライン (n_core=2 が 76%, n_core=5 が 12% Integration では 51%)
    print('\n=== v10.4 ベースライン (24 seeds × 50 windows × 5224 cid) との比較 ===')
    print('  v10.4: n_core=2 = 76%, n_core=3 = 5.5%, n_core=5 = 12.2% (Integration では 51%)')
    print(f'  本 smoke A_baseline 最終 window:')
    base = last_df[last_df['condition'] == 'A_baseline'].iloc[0]
    print(f'    n_core=2: {base["pct_n_core_2"]:.1f}%')
    print(f'    n_core=5+: {base["pct_n_core_5plus"]:.1f}%')

    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'seed': SEED, 'N': N_NODES,
        'maturation_windows': MATURATION_WINDOWS,
        'tracking_windows': TRACKING_WINDOWS,
        'window_steps': WINDOW_STEPS,
        'conditions': [c[0] for c in CONDITIONS],
        'timing_sec': timing,
        'total_sec': time.time() - t_main,
        'n_rows': len(full),
    }
    (OUT_DIR / 'smoke_run_summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))

    print(f'\n=== smoke 完了 total {time.time()-t_main:.1f}s ===')
    print(f'  -> {OUT_DIR}/smoke_full.parquet ({len(full)} rows)')
    print(f'  -> {OUT_DIR}/smoke_last_window.parquet')
    print(f'  -> {OUT_DIR}/smoke_run_summary.json')


if __name__ == '__main__':
    main()
