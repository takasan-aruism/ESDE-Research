#!/usr/bin/env python3
"""第 3 段階 Step B — smoke (起動 Genesis + 外部接続統合 + 主体性検証 兆候確認)

設定:
- 1 seed (42)、maturation 3、tracking 1、window_steps 100、N=5000
- 2 conditions:
    genesis_driven: target = 最大 label core node の E top-K (案 α)
    shuffled:      target = alive_n からランダム K=5
- 各 window 末で physics.inject(state, target_nodes=...) で戻し実効化
- attribute (_stage3_external_inputs) も併用 (観察用)
- 比較指標: labels_active / alive_l / torque_events の進化

物理層 frozen:
- 新規 engine instance に inject、既存物理層 (developmental/v105 等) は 1 byte も触らず
- 出力 unified/stage3_subjectivity/run_smoke/ 配下のみ
"""
import sys, json, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
STAGE3 = REPO / 'unified/stage3_subjectivity'
OUT_DIR = STAGE3 / 'run_smoke'
SANDBOX = STAGE3 / 'sandbox_smoke'
OUT_DIR.mkdir(parents=True, exist_ok=True)
SANDBOX.mkdir(parents=True, exist_ok=True)

PATHS = [
    REPO / 'primitive/v910',  # 先頭: VirtualLayerV9 (feedback_gamma kwargs 版、v918 経路)
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

SEED = 42
MATURATION_WINDOWS = 3
TRACKING_WINDOWS = 1
WINDOW_STEPS = 100
N_NODES = V82_N  # 5000
K_TARGET = 5     # top-K target nodes


def build_engine(seed):
    """補足で確認した起動手順 (v918_memory_readout.py run 関数準拠)"""
    encap = V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)
    engine = V82Engine(seed=seed, N=N_NODES, encap_params=encap)
    engine.virtual = VirtualLayerV9(feedback_gamma=0.10,
                                     feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True
    engine.run_injection()
    return engine


def derive_action_genesis_driven(engine, K=K_TARGET):
    """案 α: 最大 label の core node から E top-K を選ぶ"""
    labels = engine.virtual.labels
    macro_set = set(engine.virtual.macro_nodes)
    non_macro = {lid: lab for lid, lab in labels.items() if lid not in macro_set}
    if not non_macro:
        return []
    largest_lid = max(non_macro, key=lambda l: len(non_macro[l]['nodes']))
    core_nodes = [n for n in non_macro[largest_lid]['nodes']
                  if n in engine.state.alive_n]
    if not core_nodes:
        return []
    sorted_nodes = sorted(core_nodes,
                          key=lambda n: -float(engine.state.E.get(n, 0.0)))
    return sorted_nodes[:K]


def derive_action_shuffled_random(engine, rng, K=K_TARGET):
    """shuffle: alive_n から無作為 K 個"""
    alive = list(engine.state.alive_n)
    if len(alive) <= K:
        return alive
    idx = rng.choice(len(alive), size=K, replace=False)
    return [alive[i] for i in idx]


def read_genesis_state(engine, iter_id, condition):
    """Genesis 低レイヤー状態を読む"""
    vs = engine.virtual_stats or {}
    ss = engine.stress_stats or {}
    macro_set = set(engine.virtual.macro_nodes)
    non_macro_labels = [lid for lid in engine.virtual.labels
                        if lid not in macro_set]
    return {
        'condition': condition,
        'iter': iter_id,
        'window_count': engine.window_count,
        'alive_n_count': len(engine.state.alive_n),
        'alive_l_count': len(engine.state.alive_l),
        'labels_total': len(engine.virtual.labels),
        'labels_non_macro': len(non_macro_labels),
        'labels_active': vs.get('labels_active', 0),
        'labels_born': vs.get('labels_born', 0),
        'labels_died': vs.get('labels_died', 0),
        'torque_events': vs.get('torque_events', 0),
        'torque_total': float(vs.get('torque_total', 0.0)),
        'mean_omega': float(ss.get('mean_omega', 0.0)),
        'mean_E': float(np.mean([engine.state.E.get(i, 0.0)
                                  for i in engine.state.alive_n])
                        if engine.state.alive_n else 0.0),
    }


def write_external(target_nodes, condition, iter_id):
    """ESDE → 外部 (sandbox に書く)"""
    payload = {
        'timestamp': time.time(),
        'condition': condition,
        'iter': iter_id,
        'target_nodes': [int(n) for n in target_nodes],
    }
    fpath = SANDBOX / f'state_{condition}_iter{iter_id}.json'
    fpath.write_text(json.dumps(payload, indent=2))
    return payload


def read_external_identity(payload):
    """外部処理 = identity (恒等、第 3 段階確定)"""
    return payload


def build_source_event(iter_id, condition, external_payload):
    """source_event 変換 (簡易、第 2 段階互換 + target_nodes 追加)"""
    return {
        'condition': condition,
        'iter': iter_id,
        'event_id': f'{condition}_iter_{iter_id}',
        'timestamp': external_payload['timestamp'],
        'target_nodes': external_payload['target_nodes'],
    }


def inject_to_engine(engine, source_event):
    """physics.inject で戻し実効 + attribute 保持併用 (Step A §5)"""
    target = source_event['target_nodes']
    if not target:
        return {'injected_count': 0, 'pre_alive_n': len(engine.state.alive_n),
                'pre_alive_l': len(engine.state.alive_l)}
    pre_alive_n = len(engine.state.alive_n)
    pre_alive_l = len(engine.state.alive_l)
    pre_E_target = [float(engine.state.E.get(n, 0.0)) for n in target]
    # 公式インターフェース
    returned = engine.physics.inject(engine.state, target_nodes=list(target))
    post_E_target = [float(engine.state.E.get(n, 0.0)) for n in target]
    # attribute 併用 (観察用)
    if not hasattr(engine, '_stage3_external_inputs'):
        engine._stage3_external_inputs = []
    engine._stage3_external_inputs.append(source_event)
    return {
        'injected_count': len(returned) if returned else 0,
        'pre_alive_n': pre_alive_n,
        'pre_alive_l': pre_alive_l,
        'post_alive_n': len(engine.state.alive_n),
        'post_alive_l': len(engine.state.alive_l),
        'pre_E_mean_target': float(np.mean(pre_E_target)) if pre_E_target else 0.0,
        'post_E_mean_target': float(np.mean(post_E_target)) if post_E_target else 0.0,
    }


def run_condition(seed, condition):
    """1 condition (genesis_driven or shuffled) を 1 seed で走らせる"""
    print(f'\n=== condition={condition} seed={seed} ===')
    t0 = time.time()
    engine = build_engine(seed)
    print(f'  run_injection done ({time.time()-t0:.1f}s) '
          f'alive_n={len(engine.state.alive_n)} '
          f'alive_l={len(engine.state.alive_l)}')

    # shuffle 用 RNG (engine.rng と分離、補足の capture_rng パターン)
    shuffle_rng = np.random.default_rng(seed ^ 0xDEADBEEF)

    rows = []
    inject_rows = []

    total_w = MATURATION_WINDOWS + TRACKING_WINDOWS
    for w in range(total_w):
        # step_window で物理進める
        engine.step_window(steps=WINDOW_STEPS)

        # Genesis 状態読み取り (pre-inject)
        state_pre = read_genesis_state(engine, w, condition)

        # derive_action (condition 別)
        if condition == 'genesis_driven':
            target = derive_action_genesis_driven(engine, K=K_TARGET)
        elif condition == 'shuffled_random_nodes':
            target = derive_action_shuffled_random(engine, shuffle_rng, K=K_TARGET)
        else:
            raise ValueError(condition)

        # 外部書き込み + identity 戻し
        ext = write_external(target, condition, w)
        read_back = read_external_identity(ext)
        new_event = build_source_event(w, condition, read_back)

        # physics.inject で戻し実効
        inject_info = inject_to_engine(engine, new_event)

        row = {**state_pre,
               'target_nodes': str(target),
               'n_target': len(target),
               **{f'inject_{k}': v for k, v in inject_info.items()}}
        rows.append(row)
        inject_rows.append({
            'condition': condition,
            'iter': w,
            **inject_info,
            'target_first': target[0] if target else -1,
        })

        print(f'  w={w} non_macro_labels={state_pre["labels_non_macro"]} '
              f'alive_l={state_pre["alive_l_count"]} '
              f'target_n={len(target)} '
              f'inject_dE={inject_info.get("post_E_mean_target", 0) - inject_info.get("pre_E_mean_target", 0):.4f}')

    elapsed = time.time() - t0
    print(f'  condition done ({elapsed:.1f}s)')
    return pd.DataFrame(rows), pd.DataFrame(inject_rows), elapsed


def main():
    print('=== 第 3 段階 Step B smoke ===\n')
    t_main = time.time()

    all_rows = []
    all_inject = []
    timing = {}
    for condition in ['genesis_driven', 'shuffled_random_nodes']:
        df_state, df_inject, dt = run_condition(SEED, condition)
        all_rows.append(df_state)
        all_inject.append(df_inject)
        timing[condition] = dt

    state_df = pd.concat(all_rows, ignore_index=True)
    inject_df = pd.concat(all_inject, ignore_index=True)
    state_df.to_parquet(OUT_DIR / 'smoke_state.parquet', index=False)
    inject_df.to_parquet(OUT_DIR / 'smoke_inject.parquet', index=False)

    # 簡易比較サマリ (兆候用、smoke なので確定でなく兆候)
    print('\n--- 兆候比較 (条件別、最終 iter) ---')
    METRICS = ['alive_n_count', 'alive_l_count', 'labels_non_macro',
               'labels_active', 'torque_events', 'mean_omega', 'mean_E']
    summary_rows = []
    for cond in ['genesis_driven', 'shuffled_random_nodes']:
        sub = state_df[state_df['condition'] == cond]
        last = sub.iloc[-1]
        print(f'  {cond:25s} ' +
              ' '.join(f'{m}={last[m]:.3f}' if isinstance(last[m], (int, float))
                       else f'{m}={last[m]}' for m in METRICS))
        for m in METRICS:
            summary_rows.append({'condition': cond, 'metric': m,
                                  'value_last': float(last[m])})
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_parquet(OUT_DIR / 'smoke_summary.parquet', index=False)

    # 差の兆候
    print('\n--- 差 (genesis_driven - shuffled), 最終 iter ---')
    diffs = {}
    g_last = state_df[state_df['condition'] == 'genesis_driven'].iloc[-1]
    s_last = state_df[state_df['condition'] == 'shuffled_random_nodes'].iloc[-1]
    for m in METRICS:
        d = float(g_last[m]) - float(s_last[m])
        diffs[m] = d
        print(f'  {m:25s} Δ = {d:+.4f}')

    summary_json = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'seed': SEED, 'N': N_NODES,
        'maturation_windows': MATURATION_WINDOWS,
        'tracking_windows': TRACKING_WINDOWS,
        'window_steps': WINDOW_STEPS,
        'K_target': K_TARGET,
        'timing_sec': timing,
        'total_sec': time.time() - t_main,
        'diffs_final_iter': diffs,
        'n_state_rows': len(state_df),
        'n_inject_rows': len(inject_df),
    }
    (OUT_DIR / 'smoke_run_summary.json').write_text(
        json.dumps(summary_json, indent=2, ensure_ascii=False))

    print(f'\n=== smoke 完了 total {time.time()-t_main:.1f}s ===')
    print(f'  -> {OUT_DIR}/smoke_state.parquet')
    print(f'  -> {OUT_DIR}/smoke_inject.parquet')
    print(f'  -> {OUT_DIR}/smoke_summary.parquet')
    print(f'  -> {OUT_DIR}/smoke_run_summary.json')


if __name__ == '__main__':
    main()
