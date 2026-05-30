#!/usr/bin/env python3
"""第 2 段階 Step C+D+E — 外部接続完全ループ

統合実装:
- Step C: V82Engine 常駐ループ + Genesis 状態読み取り
- Step D: 外部ツール (sandbox/state.json) 読み書き
- Step E: 外部結果を engine 入力に反映 (固定ルール、後で主体性差し替え可能な構造)

物理層 frozen:
- 既存 developmental/v105 等は 1 byte も読まない
- 書込み unified/stage2_external_loop/ 配下のみ
- engine は新規 instantiation、既存物理層と独立
"""
import sys, json, time
from pathlib import Path
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
STAGE2_DIR = REPO / 'unified/stage2_external_loop'
OUT_DIR = STAGE2_DIR / 'outputs/main'
SANDBOX_DIR = STAGE2_DIR / 'sandbox'
OUT_DIR.mkdir(parents=True, exist_ok=True)
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

# V82Engine PATH
PATHS = [
    REPO / 'autonomy/v82',
    REPO / 'cognition/semantic_injection/v4_pipeline/v43',
    REPO / 'cognition/semantic_injection/v4_pipeline/v41',
    REPO / 'ecology/engine',
]
for p in PATHS:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from esde_v82_engine import V82Engine, V82EncapsulationParams

N_LOOP_ITER = 30  # 常駐ループ回数
STEPS_PER_WINDOW = 10  # 1 window あたり step
N_NODES = 500  # smoke 用に小さく
SEED = 42

EXTERNAL_STATE_FILE = SANDBOX_DIR / 'state.json'
SOURCE_EVENT_LOG = OUT_DIR / 'source_events.parquet'


def read_genesis_state(engine, iter_id):
    """[Step C] Genesis low layer から状態を読む"""
    state = engine.state
    vs = engine.virtual_stats
    ss = engine.stress_stats
    return {
        'iter': iter_id,
        'window_count': engine.window_count,
        'alive_n': len(state.alive_n) if hasattr(state, 'alive_n') else 0,
        'alive_l': len(state.alive_l) if hasattr(state, 'alive_l') else 0,
        'labels_active': vs.get('labels_active', 0),
        'labels_born': vs.get('labels_born', 0),
        'labels_died': vs.get('labels_died', 0),
        'torque_events': vs.get('torque_events', 0),
        'stressed': ss.get('stressed', 0),
        'mean_omega': float(ss.get('mean_omega', 0.0)),
    }


def write_external(state_dict):
    """[Step D] ESDE → 外部 (sandbox/state.json)"""
    payload = {
        'timestamp': time.time(),
        'esde_state': state_dict,
    }
    EXTERNAL_STATE_FILE.write_text(json.dumps(payload, indent=2))
    return payload


def read_external():
    """[Step D] 外部 → ESDE (sandbox/state.json から読む)"""
    if not EXTERNAL_STATE_FILE.exists():
        return None
    return json.loads(EXTERNAL_STATE_FILE.read_text())


def build_source_event(iter_id, external_payload):
    """[Step E] 外部結果 → source_event スキーマ (簡易版)

    実 source_event スキーマは v107_source_events と同型を目指すが、
    第 2 段階最小実証では「外部ループが回った記録」のみ。
    """
    es = external_payload['esde_state']
    return {
        'iter': iter_id,
        'event_id': f'ext_loop_{iter_id}',
        'source_cid': iter_id,  # 仮 cid 番号
        'timestamp': external_payload['timestamp'],
        'esde_alive_n': es['alive_n'],
        'esde_alive_l': es['alive_l'],
        'esde_labels_active': es['labels_active'],
        'esde_mean_omega': es['mean_omega'],
        'external_loop_completed': True,
    }


def inject_to_engine(engine, source_event):
    """[Step E] source_event を engine に戻す (固定ルール、第 3 段階で差し替え可能)

    V82Engine は直接的な source_event 受信機構を持たないので、
    第 2 段階では「engine の外部 attribute に追加保持」で技術的成立を示す。
    第 3 段階で実体的な engine 入力 (next torque, next seed 等) に差し替え可能。
    """
    if not hasattr(engine, '_stage2_external_inputs'):
        engine._stage2_external_inputs = []
    engine._stage2_external_inputs.append(source_event)
    return True


def main():
    print('=== 第 2 段階 Step C+D+E 完全外部接続ループ ===\n')
    t0 = time.time()

    # engine 起動 (Step C 起点)
    print(f'[Step C] V82Engine 起動 (N={N_NODES}, seed={SEED})')
    engine = V82Engine(seed=SEED, N=N_NODES)
    print(f'  engine 作成 OK ({time.time()-t0:.2f}s)')

    # 常駐ループ
    print(f'\n[Step C+D+E] 常駐ループ {N_LOOP_ITER} 回開始')
    loop_log = []
    source_events_log = []
    for i in range(N_LOOP_ITER):
        # ESDE step
        t_step = time.time()
        engine.step_window(steps=STEPS_PER_WINDOW)
        step_time = time.time() - t_step

        # [Step C] Genesis 状態読み取り
        state = read_genesis_state(engine, i)

        # [Step D] 外部に書く
        external_payload = write_external(state)

        # [Step D] 外部から読む (ファイル読み書き = 最小外部ツール)
        read_back = read_external()
        external_ok = read_back is not None

        # [Step E] 外部結果を source_event に変換
        new_event = build_source_event(i, read_back)

        # [Step E] engine に戻す
        injected = inject_to_engine(engine, new_event)

        loop_log.append({
            **state,
            'step_time_sec': step_time,
            'external_write_read_ok': external_ok,
            'event_injected': injected,
        })
        source_events_log.append(new_event)

        if (i + 1) % 10 == 0:
            print(f'  iter {i+1}/{N_LOOP_ITER}: window_count={engine.window_count}, '
                  f'alive_n={state["alive_n"]}, alive_l={state["alive_l"]}, '
                  f'labels_active={state["labels_active"]}')

    elapsed = time.time() - t0
    print(f'\n  常駐ループ {N_LOOP_ITER} 回完了 ({elapsed:.2f}s)')

    # 出力
    loop_df = pd.DataFrame(loop_log)
    loop_df.to_parquet(OUT_DIR / 'loop_log.parquet', index=False)
    src_df = pd.DataFrame(source_events_log)
    src_df.to_parquet(SOURCE_EVENT_LOG, index=False)
    print(f'\nwrote loop_log.parquet ({len(loop_df)} rows)')
    print(f'wrote source_events.parquet ({len(src_df)} rows)')

    # engine に inject された events 確認
    print(f'\n[Step E 確認] engine._stage2_external_inputs: {len(engine._stage2_external_inputs)} events')
    print(f'  sample first: {engine._stage2_external_inputs[0]}')
    print(f'  sample last: {engine._stage2_external_inputs[-1]}')

    # サマリ
    print(f'\n--- 常駐ループ集計 ---')
    print(f'  total iter: {len(loop_df)}')
    print(f'  external write/read OK: {loop_df["external_write_read_ok"].sum()}/{len(loop_df)}')
    print(f'  event inject OK: {loop_df["event_injected"].sum()}/{len(loop_df)}')
    print(f'  alive_n 最終: {loop_df["alive_n"].iloc[-1]}')
    print(f'  alive_l 最終: {loop_df["alive_l"].iloc[-1]}')
    print(f'  labels_active 最終: {loop_df["labels_active"].iloc[-1]}')
    print(f'  total step time: {loop_df["step_time_sec"].sum():.2f}s')

    # external_state.json 中身確認
    if EXTERNAL_STATE_FILE.exists():
        print(f'\n--- 最終 external_state.json ---')
        last_payload = json.loads(EXTERNAL_STATE_FILE.read_text())
        print(f'  {json.dumps(last_payload, indent=2)[:300]}')


if __name__ == '__main__':
    main()
