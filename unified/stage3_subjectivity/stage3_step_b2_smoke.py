#!/usr/bin/env python3
"""第 3 段階 Step B2 — 2nd smoke (徹底観察 + 期待/結果比較 + 層 1/2 判定)

Web Claude 2nd smoke 設計準拠:
- 観察スケール徹底 (局所 + 全体)
- 出し方 3 種 × K 2 種 = 6 conditions
- 期待を事前明示 (stage3_step_b2_expectations.md)
- 層 1 (戻し機能) + 層 2 (出し方で系違うか) 判定

V82 step_window 制約:
- step_window(steps=N) を 1 window として呼ぶ (semantics 維持)
- per-window 処理 (virtual.step/stress/observation/window_count++) 暴走防止
- 代替: inject 前後の state スナップショット + 局所 (radius 8) 集計
"""
import sys, json, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
STAGE3 = REPO / 'unified/stage3_subjectivity'
OUT_DIR = STAGE3 / 'run_smoke2'
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

SEED = 42
MATURATION_WINDOWS = 3
TRACKING_WINDOWS = 2
WINDOW_STEPS = 100
N_NODES = V82_N
INJECT_RADIUS = 8

CONDITIONS = [
    ('genesis_driven', 5),
    ('shuffled_state_E', 5),
    ('shuffled_random_nodes', 5),
    ('genesis_driven', 50),
    ('shuffled_state_E', 50),
    ('shuffled_random_nodes', 50),
]


def build_engine(seed):
    encap = V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)
    engine = V82Engine(seed=seed, N=N_NODES, encap_params=encap)
    engine.virtual = VirtualLayerV9(feedback_gamma=0.10,
                                     feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True
    engine.run_injection()
    return engine


def derive_genesis_driven(engine, K):
    """案 α: 最大 label の core node から E top-K"""
    labels = engine.virtual.labels
    macro = set(engine.virtual.macro_nodes)
    non_macro = {lid: lab for lid, lab in labels.items() if lid not in macro}
    if not non_macro:
        return []
    largest = max(non_macro, key=lambda l: len(non_macro[l]['nodes']))
    core = [n for n in non_macro[largest]['nodes'] if n in engine.state.alive_n]
    if not core:
        return []
    return sorted(core,
                  key=lambda n: -float(engine.state.E.get(n, 0.0)))[:K]


def derive_shuffled_state_E(engine, rng, K):
    """state_E の値を全 alive node 間で permute してから top-K を選ぶ
    (高 E 値で同じ集中度を保ち、空間位置だけ Genesis 構造から切り離す)"""
    alive = sorted(engine.state.alive_n)
    if len(alive) <= K:
        return alive
    e_vals = np.array([engine.state.E.get(n, 0.0) for n in alive])
    perm = rng.permutation(len(alive))
    e_shuffled = e_vals[perm]
    # top-K E_shuffled の indices
    top_idx = np.argsort(-e_shuffled)[:K]
    return [alive[i] for i in top_idx]


def derive_shuffled_random_nodes(engine, rng, K):
    """alive_n から無作為 K"""
    alive = sorted(engine.state.alive_n)
    if len(alive) <= K:
        return alive
    idx = rng.choice(len(alive), size=K, replace=False)
    return [alive[i] for i in idx]


def local_snapshot(engine, target_nodes, radius):
    """target_nodes と radius 内近傍の集計 (局所メトリクス)"""
    if not target_nodes:
        return {
            'n_target': 0, 'n_local_pool': 0,
            'local_mean_E': 0.0, 'local_alive_count': 0,
            'local_link_count': 0, 'local_link_S_sum': 0.0,
        }
    # ノード ID は連続整数、radius は torus 距離でなく ID 距離 (v82 のいなれを inject_pair_radius=8 で踏襲)
    local_pool = set()
    for t in target_nodes:
        for offset in range(-radius, radius + 1):
            cand = t + offset
            if 0 <= cand < N_NODES:
                local_pool.add(cand)
    local_pool_list = sorted(local_pool)
    alive_local = [n for n in local_pool_list if n in engine.state.alive_n]
    local_E = [float(engine.state.E.get(n, 0.0)) for n in local_pool_list]
    # local links: 両端が local pool 内
    local_link_count = 0
    local_link_S = 0.0
    pool_set = set(local_pool_list)
    for lk in engine.state.alive_l:
        if lk[0] in pool_set and lk[1] in pool_set:
            local_link_count += 1
            local_link_S += float(engine.state.S.get(lk, 0.0))
    return {
        'n_target': len(target_nodes),
        'n_local_pool': len(local_pool_list),
        'local_mean_E': float(np.mean(local_E)) if local_E else 0.0,
        'local_alive_count': len(alive_local),
        'local_link_count': local_link_count,
        'local_link_S_sum': local_link_S,
    }


def global_snapshot(engine):
    """全体集計 (1st smoke と互換)"""
    vs = engine.virtual_stats or {}
    ss = engine.stress_stats or {}
    macro = set(engine.virtual.macro_nodes)
    non_macro = [lid for lid in engine.virtual.labels if lid not in macro]
    return {
        'alive_n_count': len(engine.state.alive_n),
        'alive_l_count': len(engine.state.alive_l),
        'labels_total': len(engine.virtual.labels),
        'labels_non_macro': len(non_macro),
        'labels_active': vs.get('labels_active', 0),
        'labels_born': vs.get('labels_born', 0),
        'labels_died': vs.get('labels_died', 0),
        'torque_events': vs.get('torque_events', 0),
        'torque_total': float(vs.get('torque_total', 0.0)),
        'mean_omega': float(ss.get('mean_omega', 0.0)),
        'mean_E_global': float(np.mean([engine.state.E.get(i, 0.0)
                                         for i in engine.state.alive_n])
                               if engine.state.alive_n else 0.0),
    }


def run_condition(seed, condition, K):
    """1 condition × 1 K で 5 windows 走らせる"""
    tag = f'{condition}_K{K}'
    print(f'\n=== {tag} ===')
    t0 = time.time()
    engine = build_engine(seed)
    print(f'  run_injection done ({time.time()-t0:.1f}s) '
          f'alive_n={len(engine.state.alive_n)} '
          f'alive_l={len(engine.state.alive_l)}')

    shuffle_rng = np.random.default_rng(seed ^ 0xDEADBEEF ^ hash(tag) % (2**32))

    rows = []
    total_w = MATURATION_WINDOWS + TRACKING_WINDOWS
    for w in range(total_w):
        engine.step_window(steps=WINDOW_STEPS)

        # 全体 snapshot (inject 前)
        g_pre = global_snapshot(engine)

        # derive target
        if condition == 'genesis_driven':
            target = derive_genesis_driven(engine, K)
        elif condition == 'shuffled_state_E':
            target = derive_shuffled_state_E(engine, shuffle_rng, K)
        elif condition == 'shuffled_random_nodes':
            target = derive_shuffled_random_nodes(engine, shuffle_rng, K)
        else:
            raise ValueError(condition)

        # 局所 snapshot (inject 前)
        l_pre = local_snapshot(engine, target, INJECT_RADIUS)

        # inject
        returned = engine.physics.inject(engine.state, target_nodes=list(target))
        n_injected = len(returned) if returned else 0

        # 局所 snapshot (inject 直後、同じ近傍)
        l_post = local_snapshot(engine, target, INJECT_RADIUS)

        # 全体 snapshot (inject 直後)
        g_post = global_snapshot(engine)

        row = {
            'condition': condition, 'K': K, 'tag': tag, 'window': w,
            'n_injected': n_injected,
            'target_first': target[0] if target else -1,
            # 全体 (inject 前)
            **{f'g_pre_{k}': v for k, v in g_pre.items()},
            # 全体 (inject 後)
            **{f'g_post_{k}': v for k, v in g_post.items()},
            # 局所 (inject 前)
            **{f'l_pre_{k}': v for k, v in l_pre.items()},
            # 局所 (inject 後)
            **{f'l_post_{k}': v for k, v in l_post.items()},
            # 差分
            'd_local_mean_E': l_post['local_mean_E'] - l_pre['local_mean_E'],
            'd_local_alive': l_post['local_alive_count'] - l_pre['local_alive_count'],
            'd_local_link_count': l_post['local_link_count'] - l_pre['local_link_count'],
            'd_local_link_S': l_post['local_link_S_sum'] - l_pre['local_link_S_sum'],
        }
        rows.append(row)

        print(f'  w={w} target_n={len(target)} '
              f'l_pre_E={l_pre["local_mean_E"]:.3f} '
              f'l_post_E={l_post["local_mean_E"]:.3f} '
              f'd_E={row["d_local_mean_E"]:+.4f} '
              f'd_link={row["d_local_link_count"]:+d} '
              f'g_alive_l={g_post["alive_l_count"]}')

    elapsed = time.time() - t0
    print(f'  done ({elapsed:.1f}s)')
    return pd.DataFrame(rows), elapsed


def main():
    print('=== 第 3 段階 Step B2 — 2nd smoke ===\n')
    print(f'Conditions: {len(CONDITIONS)}, windows: {MATURATION_WINDOWS+TRACKING_WINDOWS}')
    t_main = time.time()
    timing = {}
    all_rows = []
    for cond, K in CONDITIONS:
        df, dt = run_condition(SEED, cond, K)
        timing[f'{cond}_K{K}'] = dt
        all_rows.append(df)

    full_df = pd.concat(all_rows, ignore_index=True)
    full_df.to_parquet(OUT_DIR / 'smoke2_full.parquet', index=False)

    # 期待 vs 結果 比較 (最終 window 末)
    print('\n--- 兆候比較 (最終 window 末、global) ---')
    GLOBAL_METRICS = ['g_post_alive_l_count', 'g_post_labels_non_macro',
                      'g_post_labels_active', 'g_post_torque_events',
                      'g_post_mean_E_global']
    LOCAL_METRICS = ['l_post_local_mean_E', 'l_post_local_alive_count',
                     'l_post_local_link_count', 'l_post_local_link_S_sum',
                     'd_local_mean_E', 'd_local_link_count']

    last_rows = []
    for (cond, K) in CONDITIONS:
        sub = full_df[(full_df['condition'] == cond) & (full_df['K'] == K)]
        last = sub.iloc[-1]
        row = {'condition': cond, 'K': K}
        for m in GLOBAL_METRICS + LOCAL_METRICS:
            row[m] = float(last[m])
        last_rows.append(row)
    last_df = pd.DataFrame(last_rows)
    last_df.to_parquet(OUT_DIR / 'smoke2_last_window.parquet', index=False)

    # 差比較 (genesis_driven - shuffled、K=5 と K=50 で別)
    print('\n=== K 別、出し方差 (genesis_driven vs shuffled) ===')
    diff_rows = []
    for K in [5, 50]:
        g_row = last_df[(last_df['condition'] == 'genesis_driven') & (last_df['K'] == K)].iloc[0]
        for other in ['shuffled_state_E', 'shuffled_random_nodes']:
            o_row = last_df[(last_df['condition'] == other) & (last_df['K'] == K)].iloc[0]
            print(f'\n  K={K} genesis_driven - {other}')
            for m in GLOBAL_METRICS + LOCAL_METRICS:
                d = float(g_row[m]) - float(o_row[m])
                rel = abs(d) / (abs(float(g_row[m])) + 1e-9)
                marker = '★' if rel > 0.05 else ' '
                print(f'    {marker} {m:35s} Δ = {d:+.4f}  (rel {rel:.2%})')
                diff_rows.append({'K': K, 'comparison': f'genesis_vs_{other}',
                                  'metric': m, 'delta': d, 'rel': rel})
    diff_df = pd.DataFrame(diff_rows)
    diff_df.to_parquet(OUT_DIR / 'smoke2_diffs.parquet', index=False)

    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'seed': SEED, 'N': N_NODES,
        'maturation_windows': MATURATION_WINDOWS,
        'tracking_windows': TRACKING_WINDOWS,
        'window_steps': WINDOW_STEPS,
        'inject_radius': INJECT_RADIUS,
        'conditions': [f'{c}_K{k}' for c, k in CONDITIONS],
        'timing_sec': timing,
        'total_sec': time.time() - t_main,
        'n_full_rows': len(full_df),
        'n_diff_rows': len(diff_df),
    }
    (OUT_DIR / 'smoke2_run_summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))

    print(f'\n=== smoke2 完了 total {time.time()-t_main:.1f}s ===')
    print(f'  -> {OUT_DIR}/smoke2_full.parquet ({len(full_df)} rows)')
    print(f'  -> {OUT_DIR}/smoke2_last_window.parquet')
    print(f'  -> {OUT_DIR}/smoke2_diffs.parquet')
    print(f'  -> {OUT_DIR}/smoke2_run_summary.json')


if __name__ == '__main__':
    main()
