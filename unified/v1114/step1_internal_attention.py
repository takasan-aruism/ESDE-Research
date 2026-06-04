#!/usr/bin/env python3
"""v1114 Step 1 — Center 内部注意生成 (最小機能、過去成功事例の組合せ)

## 観察対象注釈ブロック (実装着手前に明示、Code A 自己強制ハードル)

### 観察対象の本質
- 同じ系内 / 異なる系の対応関係: **同じ系内** (Center ESDE 単体、Atom なし)
- 具体: Center が自身の動学の中で、変化が起きた CID に注意が落ちる
- 範囲: per-10step での source_event 発生率の running 統計、z>2σ で注意

### 過去成功事例との照合 (新規実験設計時の必須参照)
- v10.7 (`developmental/v107/`): 同じ系内 source_event 5 種 (pulse / ingestion /
  α_formation / β_formation / c_conversion)、94% 有意差で source-specific 性
- v9.18 (`primitive/v918/`): 同じ系内 動的平衡指標 V_unified / theta_distance
- v9.11 (`primitive/v911/v911_cognitive_capture.py`): SubjectLayer の familiarity
  dict 構造 (相手 cid の数 = node ID 不要)
- 過去成功は全て「同じ系内構造」、本実装もこれに沿う

### 過去失敗パターン回避 (4 連続失敗の枠組み)
- v1110-v1113 = 全て「異なる系の対応関係」発想で失敗
- 本実装は Center 単体 (Atom なし) → 異なる系の対応関係を含まない
- node ID コピー / 別系の occupancy cooc / 別系の CID 特性 cosine は採用しない

### 残さないもの (Web Claude 設計 §2、Taka 規律)
- node ID / member_nodes / attention[node_id]: 別系で意味を持たない、本実装は単系だが規律として遵守
- phase_sig / θ: 座標、統計に出ない、構造でない
- 不透明 float ベクトル: 形を数値に潰すと解読が必要、ループに戻る
- 判定数値 (z-score, EWMA): 発火判定には使うがレコードに残さない (Taka 念押し (a))
- 差・有意差の測定値: 研究者視点、本実装は「溜まったか + 多様か」を見るのみ (Taka 念押し (b))

### 何を測れば何が言えるか
- 溜まった + 多様: Center が自身の動学で変化点に注意を落とせた = 内部注意の最小機構成立
- 溜まらない or 全て同じ形: 引き金検出 (running 統計) か周辺取得を見直す
- crown 禁止: 「異なる自我」「会話」「Unified 成立」は書かない

### Step 1 範囲 (Web Claude 設計 §5、Taka 規律)
- 残すだけ。照合・差測定・模倣・応答は Step 2/3 以降
- α/β は v918 main run の枠組みでは取れない (Task A 実機確認結果)、familiarity 中心
- α/β を足す道は Step 2/3 に残す

## 実装方針 (現実解)
- v918 main run の既存 output (per_subject_seed0.csv + source_events_seed0.parquet) を Center の動学とする
- post-process で per-10step を再構築、EWMA + z-score で発火判定
- Center が「リアルタイムに per-10step で観察してる」と等価な観察結果が得られる
- Step 2 でリアルタイム + 擦り戻しに移行する時は枠組みを変える
"""
import os, sys, json
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')

# === 構成 ===
CENTER_SEED = 0  # Center ESDE は seed=0 (v918 main run 既存 output 流用)
N_PER_CHUNK = 10  # per-10step monitoring (= 1 step ≈ 0.43s → 1 chunk ≈ 4.3s)
EWMA_ALPHA = 0.2  # EWMA 係数 (0.2 = 過去 5 chunk の重み 67%)
Z_NOTICE = 2.0  # 注意発火閾値 (z > 2σ)
Z_ANOMALY = 3.0  # 異常発火閾値 (z > 3σ)
WARMUP_CHUNKS = 10  # EWMA warmup 期間

PER_SUBJECT_PATH = REPO / f'primitive/v918/diag_v918_main/subjects/per_subject_seed{CENTER_SEED}.csv'
SOURCE_EVENTS_PATH = REPO / f'developmental/v107/outputs/main/source_events_seed{CENTER_SEED}.parquet'
OUT_DIR = REPO / 'unified/v1114/run_step1'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_int(v, default=0):
    if pd.isna(v):
        return default
    try:
        return int(v)
    except (ValueError, TypeError):
        return default


def safe_float(v, default=0.0):
    if pd.isna(v):
        return default
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


def ewma_update(stat, value, alpha=EWMA_ALPHA):
    """EWMA で mean/var を更新し、z-score を返す
    stat: dict {'mean': float, 'var': float, 'count': int}
    """
    stat['count'] += 1
    if stat['count'] <= WARMUP_CHUNKS:
        # warmup: 単純平均で初期化
        n = stat['count']
        stat['mean'] = (stat['mean'] * (n - 1) + value) / n
        stat['var'] = max(stat['var'], 0.1)  # 最小分散で過敏判定を防ぐ
        return 0.0  # warmup 中は z=0 (発火しない)
    delta = value - stat['mean']
    stat['mean'] += alpha * delta
    stat['var'] = (1 - alpha) * (stat['var'] + alpha * delta ** 2)
    std = np.sqrt(stat['var'])
    z = delta / std if std > 1e-9 else 0.0
    return z


def main():
    print('=== v1114 Step 1 — Center 内部注意生成 ===\n')
    print(f'  Center seed: {CENTER_SEED}')
    print(f'  per-{N_PER_CHUNK}step 観察')
    print(f'  EWMA α={EWMA_ALPHA}, warmup={WARMUP_CHUNKS} chunks')
    print(f'  注意発火: z > {Z_NOTICE}σ、異常発火: z > {Z_ANOMALY}σ')
    print(f'  Taka 規律: 判定数値 (z, EWMA) はレコードに残さない、引き金は記号のみ\n')

    # === 入力読み込み ===
    if not PER_SUBJECT_PATH.exists():
        print(f'ERROR: {PER_SUBJECT_PATH} が存在しない')
        sys.exit(1)
    if not SOURCE_EVENTS_PATH.exists():
        print(f'ERROR: {SOURCE_EVENTS_PATH} が存在しない')
        sys.exit(1)

    subj_df = pd.read_csv(PER_SUBJECT_PATH)
    events_df = pd.read_parquet(SOURCE_EVENTS_PATH)
    print(f'入力:')
    print(f'  per_subject: {len(subj_df)} CIDs')
    print(f'  source_events: {len(events_df)} events')
    print(f'  event 種別: {events_df["event_source_type"].unique().tolist()}\n')

    # CID → per_subject row のマップ (高速参照用)
    subj_by_cid = {}
    for _, row in subj_df.iterrows():
        subj_by_cid[safe_int(row['cognitive_id'])] = row

    # === per-10step に event を集計 ===
    events_df['chunk'] = (events_df['timestamp'] // N_PER_CHUNK).astype(int)
    max_chunk = int(events_df['chunk'].max())
    event_types = sorted(events_df['event_source_type'].unique())

    print(f'動学の長さ: {max_chunk + 1} chunks (= {(max_chunk + 1) * N_PER_CHUNK} steps)')
    print(f'監視メトリック (引き金候補): {event_types}\n')

    # event 種別ごとに per-chunk 発生数
    counts_per_chunk = events_df.groupby(['chunk', 'event_source_type']).size().unstack(fill_value=0)

    # 全 chunk × event_type を埋める
    full_chunks = pd.DataFrame(
        index=range(max_chunk + 1),
        columns=event_types,
        data=0,
    )
    for et in event_types:
        if et in counts_per_chunk.columns:
            full_chunks[et] = counts_per_chunk[et].reindex(full_chunks.index, fill_value=0)

    # === EWMA + z-score で alert 判定 (判定数値はレコードに残さない) ===
    running_stats = {et: {'mean': 0.0, 'var': 1.0, 'count': 0} for et in event_types}
    records = []
    order = 0

    for chunk_idx in range(max_chunk + 1):
        for et in event_types:
            n = int(full_chunks.loc[chunk_idx, et])
            z = ewma_update(running_stats[et], float(n))
            # 発火判定 (内部、レコードに残さない)
            if abs(z) <= Z_NOTICE:
                continue
            # 注意発火 - この chunk の et 種の event から代表 CID を取る
            chunk_events_of_type = events_df[
                (events_df['chunk'] == chunk_idx) &
                (events_df['event_source_type'] == et)
            ]
            if len(chunk_events_of_type) == 0:
                continue
            # 代表 event: 最初の event (timestamp 順)
            e = chunk_events_of_type.sort_values('timestamp').iloc[0]
            cid = safe_int(e['source_cid'])
            cid_subj = subj_by_cid.get(cid)

            # === レコード生成 (記号 + 構造、判定数値は残さない、Taka 念押し (a)) ===
            point = {
                'n_core': safe_int(e['n_core_member']),
                'lifespan': safe_int(e['lifespan_so_far']),
                'C': safe_int(e['C_at_window_end']),
                'Q_remaining': safe_int(e['Q_remaining_at_window_end']),
                # pulse 活動 (近似: source_events に v10_pulse_count 直接ない、
                # per_subject の last_attention_size を近似値として使う)
                'pulse_activity': safe_int(cid_subj['last_attention_size']) if cid_subj is not None else 0,
            }
            neighborhood = {
                # familiarity 数 = 近似: per_subject の last_n_partners
                'familiarity_n': safe_int(cid_subj['last_n_partners']) if cid_subj is not None else 0,
                # 周辺の大きさ list は v918 output からは取れない (Task A 実機確認結果)、
                # Step 1 では落とす (Step 2/3 で取得経路を検討)
            }
            record = {
                'order': order,
                'trigger': et,  # 記号のみ (z や count は残さない)
                'point': point,
                'neighborhood': neighborhood,
            }
            records.append(record)
            order += 1

    # === 報告 (Taka 念押し (b): 「溜まったか + 多様か」、差は測らない) ===
    print('=' * 60)
    print('Step 1 観察 (Taka 念押し: 溜まったか + 多様か、差なし)')
    print('=' * 60)
    print(f'\nレコード数: {len(records)}')

    if len(records) == 0:
        print('\n→ レコード溜まらず。引き金検出 (running 統計) を見直す必要')
        summary = {
            'design': 'v1114_step1_internal_attention',
            'records_total': 0,
            'note': 'records_empty - check trigger detection',
        }
        (OUT_DIR / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False))
        return

    # 多様性: 引き金 (記号) の分布
    trigger_dist = Counter(r['trigger'] for r in records)
    print(f'\n引き金 (記号) の分布:')
    for trig, cnt in trigger_dist.most_common():
        print(f'  {trig}: {cnt}')

    # 多様性: 点の n_core 分布
    n_core_dist = Counter(r['point']['n_core'] for r in records)
    print(f'\n点の n_core 分布 (= 「大きさ」):')
    for nc, cnt in sorted(n_core_dist.items()):
        print(f'  n_core={nc}: {cnt}')

    # 多様性: 点の lifespan 帯
    lifespan_bins = [(0, 100), (100, 500), (500, 2000), (2000, 10000), (10000, 100000)]
    print(f'\n点の lifespan 帯分布:')
    for lo, hi in lifespan_bins:
        c = sum(1 for r in records if lo <= r['point']['lifespan'] < hi)
        if c > 0:
            print(f'  [{lo:>5}, {hi:>6}): {c}')

    # 多様性: 周辺 familiarity 数
    fam_dist = Counter(r['neighborhood']['familiarity_n'] for r in records)
    print(f'\n周辺 familiarity 数の分布:')
    for fn, cnt in sorted(fam_dist.items())[:15]:
        print(f'  familiarity_n={fn}: {cnt}')

    # 引き金 × n_core の二次元観察 (溜まったレコードの形)
    print(f'\n引き金 × n_core 二次元分布:')
    cross = defaultdict(lambda: defaultdict(int))
    for r in records:
        cross[r['trigger']][r['point']['n_core']] += 1
    triggers_sorted = sorted(cross.keys())
    n_cores_sorted = sorted({nc for ncs in cross.values() for nc in ncs})
    header = '  trigger\\\\n_core ' + ' '.join(f'{nc:>4}' for nc in n_cores_sorted)
    print(header)
    for trig in triggers_sorted:
        row = f'  {trig:<18}' + ' '.join(f'{cross[trig].get(nc, 0):>4}' for nc in n_cores_sorted)
        print(row)

    # === ファイル出力 ===
    # records (パターン、json 可読)
    records_path = OUT_DIR / 'attention_records.json'
    records_path.write_text(json.dumps(records, indent=2, ensure_ascii=False))
    print(f'\n保存: {records_path.relative_to(REPO)} ({len(records)} レコード)')

    # サマリ
    summary = {
        'design': 'v1114_step1_internal_attention',
        'center_seed': CENTER_SEED,
        'n_per_chunk': N_PER_CHUNK,
        'ewma_alpha': EWMA_ALPHA,
        'z_notice': Z_NOTICE,
        'z_anomaly': Z_ANOMALY,
        'warmup_chunks': WARMUP_CHUNKS,
        'animation_chunks': max_chunk + 1,
        'animation_steps': (max_chunk + 1) * N_PER_CHUNK,
        'records_total': len(records),
        'trigger_distribution': dict(trigger_dist),
        'n_core_distribution': {int(k): v for k, v in n_core_dist.items()},
        'familiarity_n_distribution': {int(k): v for k, v in fam_dist.items()},
        # 注: z 値、EWMA mean/var、その他判定数値は意図的に summary に含めない
        # (Taka 念押し (a) 判定と記録の混同を防ぐ)
    }
    summary_path = OUT_DIR / 'summary.json'
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'保存: {summary_path.relative_to(REPO)}')

    print(f'\n=== Step 1 完了 ===')
    print(f'レコードが「溜まったか + 多様か」を判断材料として上記分布を確認してください。')
    print(f'差・有意差は測っていません (Taka 念押し (b))。')


if __name__ == '__main__':
    main()
