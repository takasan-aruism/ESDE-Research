#!/usr/bin/env python3
"""第 2 段階 Step B — V82Engine smoke 起動

最小設定で V82Engine を import + instantiate + step_window 実行できるか確認。
物理層 frozen 維持 (既存 developmental/v105 等は読まない、書込みは unified/stage2_external_loop/ のみ)。
"""
import sys, time
from pathlib import Path

REPO = Path('/home/takasan/esde/ESDE-Research')
STAGE2_DIR = REPO / 'unified/stage2_external_loop'
RUN_DIR = STAGE2_DIR / 'run_smoke'
RUN_DIR.mkdir(parents=True, exist_ok=True)

# V82Engine PATH 設定 (esde_v82_engine.py の設定をコピー)
PATHS = [
    REPO / 'autonomy/v82',
    REPO / 'cognition/semantic_injection/v4_pipeline/v43',
    REPO / 'cognition/semantic_injection/v4_pipeline/v41',
    REPO / 'ecology/engine',
]
for p in PATHS:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

print('=== V82Engine smoke 起動 ===\n')
print('[1] import 試行')
t0 = time.time()
try:
    from esde_v82_engine import V82Engine, V82EncapsulationParams, V82_N, V82_WINDOW
    print(f'  ✓ V82Engine import OK ({time.time()-t0:.2f}s)')
    print(f'  V82_N (default node 数): {V82_N}')
    print(f'  V82_WINDOW (default step/window): {V82_WINDOW}')
except Exception as e:
    print(f'  ✗ ERROR: {e}')
    sys.exit(1)

print('\n[2] V82Engine instantiation (smoke: N=100)')
t1 = time.time()
try:
    engine = V82Engine(seed=42, N=100)  # 小さく
    print(f'  ✓ engine 作成 OK ({time.time()-t1:.2f}s)')
    print(f'  engine.window_count: {engine.window_count}')
    print(f'  has engine.state: {hasattr(engine, "state")}')
    print(f'  has engine.virtual: {hasattr(engine, "virtual")}')
    print(f'  has engine.island_tracker: {hasattr(engine, "island_tracker")}')
except Exception as e:
    print(f'  ✗ ERROR: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

print('\n[3] step_window 1 回実行 (steps=5)')
t2 = time.time()
try:
    engine.step_window(steps=5)
    print(f'  ✓ step_window 完了 ({time.time()-t2:.2f}s)')
    print(f'  window_count: {engine.window_count}')
    print(f'  virtual_stats keys: {list(engine.virtual_stats.keys())[:5]}')
    print(f'  stress_stats keys: {list(engine.stress_stats.keys())[:5]}')
except Exception as e:
    print(f'  ✗ ERROR: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

print('\n[4] step_window 数回繰り返し (常駐ループの最小版)')
t3 = time.time()
try:
    for i in range(3):
        engine.step_window(steps=5)
    print(f'  ✓ 3 回完了 ({time.time()-t3:.2f}s)')
    print(f'  最終 window_count: {engine.window_count}')
except Exception as e:
    print(f'  ✗ ERROR: {e}')
    sys.exit(1)

print('\n[5] Genesis 状態読み出し試行 (low layer)')
try:
    state = engine.state
    # alive_n, alive_l (基本物理量)
    if hasattr(state, 'alive_n'):
        print(f'  alive_n count: {len(state.alive_n)}')
    if hasattr(state, 'alive_l'):
        print(f'  alive_l count: {len(state.alive_l)}')
    # state attributes 一覧
    attrs = [a for a in dir(state) if not a.startswith('_')]
    print(f'  state attrs (top 10): {attrs[:10]}')
    print(f'  total state attrs: {len(attrs)}')
except Exception as e:
    print(f'  ✗ ERROR: {e}')

print(f'\n=== Step B smoke 完了、total {time.time()-t0:.2f}s ===')
print('\n→ V82Engine が動く、常駐ループ + 状態読み出し可能')
print('→ 案 C (真の常駐) 実装に進める')
