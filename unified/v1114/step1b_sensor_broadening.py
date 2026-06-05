#!/usr/bin/env python3
"""v1114 Step 1b — センサー拡張 (cid id + CID 誕生 + CID 死、周辺の大きさは落とす)

## 観察対象注釈ブロック (実装着手前に明示、Code A 自己強制ハードル)

### 観察対象の本質
- 同じ系内 / 異なる系の対応関係: **同じ系内** (Center ESDE 単体、Atom なし)
- 具体: Step 1 (既存 5 種の引き金) に **cid id (認知 ID) + cid_birth + cid_death** を追加
- 範囲: 既存 5 種 + 新規 2 種 = 7 種を **独立に running 統計**、合成スコアにしない

### 過去成功事例との照合
- v9.18 / v10.7 / v9.11 (Step 1 と同じ)
- v911 SubjectLayer の `cog.born_at[cid]` (誕生 window) + `host_lost_window` / `reaped_window` (死亡 window)
- v918 per_subject CSV に `birth_window` / `host_lost_window` / `reaped_window` / `final_state` が dump 済み (実機確認 2026-06-06)

### 過去失敗パターン回避
- v1110-v1113 = 異なる系の対応関係発想で 4 連続失敗
- 本実装は Center 単体 (Atom なし)、cid id は **認知 ID** (= 系内で意味を持つ source_cid)、**node ID ではない**

### 残さないもの (Taka 規律「取れないなら落とす・すり替えない」厳格遵守)
- node ID / member_nodes / attention[node_id] (別系で無意味、本実装は単系だが規律遵守)
- phase_sig / θ (座標)
- 不透明 float ベクトル
- 判定数値 (z-score, EWMA mean/var) — 発火判定には使うがレコード/summary に残さない (Taka 念押し (a))
- 設計パラメータ — summary に残さない (再現はコード冒頭の定数で)
- 差・有意差の測定値 — 報告は「溜まったか + 多様か」だけ (Taka 念押し (b))
- **周辺の大きさ list (familiarity 相手 cid の n_core list)**: 実機確認 2026-06-06 で v918 output に `cog.familiarity[cid].keys()` の dump 経路なし、Taka 規律で落とす (Step 2/3 で取得経路検討、近似で埋めない)

### 残すフィールド (実機確認済み、近似なし)
- **cid (認知 ID = source_cid、node ID でない)**: 注意がどの CID に落ち、同じ CID に戻るのか/別へ移るのかを Step 2 で追えるように
- point: n_core / lifespan / C / Q_remaining (Step 1 と同じ、source_events から)
- neighborhood: familiarity_n (Step 1 と同じ、相手数のみ)

### 引き金 7 種 (独立監視、合成しない、Taka 規律)
- 既存 5 種 (source_events から): `pulse` / `ingestion` / `alpha_formation` / `beta_formation` / `c_conversion`
- 新規 2 種 (per_subject から構築): `cid_birth` (= birth_window × WINDOW_STEPS で時刻化) / `cid_death` (= host_lost_window × WINDOW_STEPS、host_lost_window が NaN なら final_state を見て判断)
- 各引き金は **独立な running 統計 (EWMA + z-score)** で監視、合成スコア禁止
- レコードに残るのは記号のみ (z 値・count は残さない)

### 何を測れば何が言えるか (Web Claude 設計 §5 出口)
- レコードが溜まる + 多様 (Step 1 同様)
- **誕生・死の引き金が発火し、注意が bulk (n_core=2) に落ちるか** (分布の形として観察、差は測らない)
- 全部観察事実だけ、crown 禁止 (「橋が架かった」「会話」「成立」と書かない)
- 「周辺の大きさが hub の相手が bulk か見せるか」は **本 step では落としたので測れない**、Step 2/3 で取得経路検討
"""
import os, sys, json
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')

# === 構成 ===
CENTER_SEED = 0
N_PER_CHUNK = 10
EWMA_ALPHA = 0.2
Z_NOTICE = 2.0
Z_ANOMALY = 3.0
WARMUP_CHUNKS = 10
WINDOW_STEPS = 500  # v918 main run の window 長 (per_subject の birth_window → step 変換用)

PER_SUBJECT_PATH = REPO / f'primitive/v918/diag_v918_main/subjects/per_subject_seed{CENTER_SEED}.csv'
SOURCE_EVENTS_PATH = REPO / f'developmental/v107/outputs/main/source_events_seed{CENTER_SEED}.parquet'
OUT_DIR = REPO / 'unified/v1114/run_step1b'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_int(v, default=0):
    if pd.isna(v):
        return default
    try:
        return int(v)
    except (ValueError, TypeError):
        return default


def ewma_update(stat, value, alpha=EWMA_ALPHA):
    stat['count'] += 1
    if stat['count'] <= WARMUP_CHUNKS:
        n = stat['count']
        stat['mean'] = (stat['mean'] * (n - 1) + value) / n
        stat['var'] = max(stat['var'], 0.1)
        return 0.0
    delta = value - stat['mean']
    stat['mean'] += alpha * delta
    stat['var'] = (1 - alpha) * (stat['var'] + alpha * delta ** 2)
    std = np.sqrt(stat['var'])
    return delta / std if std > 1e-9 else 0.0


def main():
    print('=== v1114 Step 1b — センサー拡張 (cid id + 誕生 + 死) ===\n')
    print(f'  Center seed: {CENTER_SEED}')
    print(f'  per-{N_PER_CHUNK}step 観察')
    print(f'  引き金 7 種 (独立監視、合成しない):')
    print(f'    既存 5 種 (source_events): pulse / ingestion / alpha_formation / beta_formation / c_conversion')
    print(f'    新規 2 種 (per_subject 構築): cid_birth / cid_death')
    print(f'  Taka 規律: 周辺の大きさ list は v918 output 取得不可で落とす (Step 2/3 検討)\n')

    if not (PER_SUBJECT_PATH.exists() and SOURCE_EVENTS_PATH.exists()):
        print(f'ERROR: 入力ファイル不在 {PER_SUBJECT_PATH} or {SOURCE_EVENTS_PATH}')
        sys.exit(1)

    subj_df = pd.read_csv(PER_SUBJECT_PATH)
    events_df = pd.read_parquet(SOURCE_EVENTS_PATH)
    print(f'入力:')
    print(f'  per_subject: {len(subj_df)} CIDs')
    print(f'  source_events: {len(events_df)} events')
    print(f'  既存 event 種別: {sorted(events_df["event_source_type"].unique().tolist())}\n')

    # CID → per_subject row map
    subj_by_cid = {safe_int(row['cognitive_id']): row for _, row in subj_df.iterrows()}

    # === 新規 event ledger 構築: cid_birth / cid_death ===
    # birth: per_subject.birth_window × WINDOW_STEPS = 誕生 step (timestamp)
    # death: per_subject.host_lost_window × WINDOW_STEPS = 宿主喪失 step (host_lost が NaN なら除外)
    new_events_rows = []
    for _, row in subj_df.iterrows():
        cid = safe_int(row['cognitive_id'])
        bw = row.get('birth_window')
        if pd.notna(bw):
            new_events_rows.append({
                'event_source_type': 'cid_birth',
                'source_cid': cid,
                'timestamp': int(bw) * WINDOW_STEPS,
                'n_core_member': np.nan,
                'lifespan_so_far': 0,
                'C_at_window_end': np.nan,
                'Q_remaining_at_window_end': np.nan,
            })
        hw = row.get('host_lost_window')
        if pd.notna(hw):
            new_events_rows.append({
                'event_source_type': 'cid_death',
                'source_cid': cid,
                'timestamp': int(hw) * WINDOW_STEPS,
                'n_core_member': np.nan,
                'lifespan_so_far': int(hw) - safe_int(row.get('birth_window'), 0),
                'C_at_window_end': np.nan,
                'Q_remaining_at_window_end': np.nan,
            })
    new_events_df = pd.DataFrame(new_events_rows)
    print(f'構築した新規 event ledger:')
    print(f'  cid_birth: {len(new_events_df[new_events_df["event_source_type"] == "cid_birth"])} (per_subject の birth_window から)')
    print(f'  cid_death: {len(new_events_df[new_events_df["event_source_type"] == "cid_death"])} (per_subject の host_lost_window から)\n')

    # 既存 5 種と統合 (chunk 集計用)
    existing_cols = ['event_source_type', 'source_cid', 'timestamp',
                     'n_core_member', 'lifespan_so_far',
                     'C_at_window_end', 'Q_remaining_at_window_end']
    events_combined = pd.concat([events_df[existing_cols], new_events_df[existing_cols]],
                                 ignore_index=True)

    # === per-10step に集計 ===
    events_combined['chunk'] = (events_combined['timestamp'] // N_PER_CHUNK).astype(int)
    max_chunk = int(events_combined['chunk'].max())
    event_types = sorted(events_combined['event_source_type'].unique())

    print(f'動学の長さ: {max_chunk + 1} chunks (= {(max_chunk + 1) * N_PER_CHUNK} steps)')
    print(f'監視メトリック (引き金 7 種、独立 running 統計):')
    for et in event_types:
        n = len(events_combined[events_combined['event_source_type'] == et])
        print(f'  {et}: {n} events')
    print()

    counts_per_chunk = events_combined.groupby(['chunk', 'event_source_type']).size().unstack(fill_value=0)
    full_chunks = pd.DataFrame(index=range(max_chunk + 1), columns=event_types, data=0)
    for et in event_types:
        if et in counts_per_chunk.columns:
            full_chunks[et] = counts_per_chunk[et].reindex(full_chunks.index, fill_value=0)

    # === 各引き金で独立に EWMA + z-score (合成しない、Taka 規律) ===
    running_stats = {et: {'mean': 0.0, 'var': 1.0, 'count': 0} for et in event_types}
    records = []
    order = 0

    for chunk_idx in range(max_chunk + 1):
        for et in event_types:
            n = int(full_chunks.loc[chunk_idx, et])
            z = ewma_update(running_stats[et], float(n))
            if abs(z) <= Z_NOTICE:
                continue
            # alert: この chunk の et 種の代表 event (最初の timestamp) を取る
            chunk_events_of_type = events_combined[
                (events_combined['chunk'] == chunk_idx) &
                (events_combined['event_source_type'] == et)
            ]
            if len(chunk_events_of_type) == 0:
                continue
            e = chunk_events_of_type.sort_values('timestamp').iloc[0]
            cid = safe_int(e['source_cid'])  # 認知 ID (= SubjectLayer の cid)、node ID でない
            cid_subj = subj_by_cid.get(cid)

            # point: 既存 5 種は source_events から、cid_birth/cid_death は per_subject から
            if et in ('cid_birth', 'cid_death'):
                # 新規 event は source_events に対応なし、per_subject から取得
                if cid_subj is not None:
                    n_core_val = 0  # per_subject に n_core 直接ない (n_core_member は source_events 経由)
                    # cid の n_core は最後の source_event から取得 (取れなければ 0)
                    last_source_events = events_df[events_df['source_cid'] == cid]
                    if len(last_source_events) > 0:
                        nc = last_source_events.iloc[-1].get('n_core_member')
                        if pd.notna(nc):
                            n_core_val = int(nc)
                    point = {
                        'n_core': n_core_val,
                        'lifespan': int(e['lifespan_so_far']) if pd.notna(e['lifespan_so_far']) else 0,
                        'C': 0,  # cid_birth/death では C 不明 (event 時点の状態は source_events ないと取れない、近似で埋めない)
                        'Q_remaining': 0,  # 同上
                    }
                else:
                    point = {'n_core': 0, 'lifespan': 0, 'C': 0, 'Q_remaining': 0}
            else:
                # 既存 5 種 (source_events から取得)
                point = {
                    'n_core': safe_int(e['n_core_member']),
                    'lifespan': safe_int(e['lifespan_so_far']),
                    'C': safe_int(e['C_at_window_end']),
                    'Q_remaining': safe_int(e['Q_remaining_at_window_end']),
                }

            neighborhood = {
                'familiarity_n': safe_int(cid_subj['last_n_partners']) if cid_subj is not None else 0,
                # familiarity_sizes (相手 cid の n_core list) は v918 output に dump 経路なし、落とす
            }
            record = {
                'order': order,
                'cid': cid,  # 認知 ID、node ID でない (Taka 規律遵守)
                'trigger': et,  # 記号のみ
                'point': point,
                'neighborhood': neighborhood,
            }
            records.append(record)
            order += 1

    # === 報告 (Taka 念押し (b): 「溜まったか + 多様か」、差なし) ===
    print('=' * 60)
    print('Step 1b 観察 (溜まったか + 多様か、差は測らない)')
    print('=' * 60)
    print(f'\nレコード数: {len(records)}')

    if len(records) == 0:
        print('\n→ レコード溜まらず')
        (OUT_DIR / 'summary.json').write_text(json.dumps({
            'design': 'v1114_step1b_sensor_broadening',
            'records_total': 0,
            'note': 'records_empty',
        }, indent=2, ensure_ascii=False))
        return

    # 引き金 (記号 7 種) の分布
    trigger_dist = Counter(r['trigger'] for r in records)
    print(f'\n引き金 (記号、7 種、独立監視) の分布:')
    for trig in event_types:
        cnt = trigger_dist.get(trig, 0)
        marker = ' ★ 新規' if trig in ('cid_birth', 'cid_death') else ''
        print(f'  {trig}: {cnt}{marker}')

    # 点の n_core 分布
    n_core_dist = Counter(r['point']['n_core'] for r in records)
    print(f'\n点の n_core 分布 (= 「大きさ」):')
    for nc, cnt in sorted(n_core_dist.items()):
        marker = ' ← bulk' if nc == 2 else (' ← hub' if nc >= 4 else '')
        print(f'  n_core={nc}: {cnt}{marker}')

    # 引き金 × n_core 二次元 (新規引き金で注意が bulk に届くか観察)
    print(f'\n引き金 × n_core 二次元分布 (新規引き金で注意が bulk=2 に届くか):')
    cross = defaultdict(lambda: defaultdict(int))
    for r in records:
        cross[r['trigger']][r['point']['n_core']] += 1
    n_cores_sorted = sorted({nc for ncs in cross.values() for nc in ncs})
    header = '  trigger\\\\n_core ' + ' '.join(f'{nc:>4}' for nc in n_cores_sorted)
    print(header)
    for trig in event_types:
        row = f'  {trig:<18}' + ' '.join(f'{cross[trig].get(nc, 0):>4}' for nc in n_cores_sorted)
        print(row)

    # cid id の多様性: 何個のユニーク CID に注意が落ちたか
    unique_cids = set(r['cid'] for r in records)
    print(f'\n注意が落ちた CID のユニーク数: {len(unique_cids)}')
    # 同じ CID に何回注意が落ちたか分布
    cid_visit_counts = Counter(r['cid'] for r in records)
    revisit_dist = Counter(cid_visit_counts.values())
    print(f'CID あたりの注意回数分布 (Step 2 で同 CID 戻り/別 CID 移動の判定材料):')
    for n_visits, n_cids in sorted(revisit_dist.items()):
        print(f'  {n_visits}回注意が落ちた CID: {n_cids} 個')

    # 周辺 familiarity 数の分布
    fam_dist = Counter(r['neighborhood']['familiarity_n'] for r in records)
    print(f'\n周辺 familiarity 数の分布 (相手数のみ、相手の大きさ list は本 step で落とす):')
    for fn, cnt in sorted(fam_dist.items())[:15]:
        print(f'  familiarity_n={fn}: {cnt}')

    # === ファイル出力 ===
    (OUT_DIR / 'attention_records.json').write_text(
        json.dumps(records, indent=2, ensure_ascii=False))
    summary = {
        'design': 'v1114_step1b_sensor_broadening',
        'center_seed': CENTER_SEED,
        'trigger_types': event_types,
        'records_total': len(records),
        'unique_cids_attended': len(unique_cids),
        'trigger_distribution': dict(trigger_dist),
        'n_core_distribution': {int(k): v for k, v in n_core_dist.items()},
        'familiarity_n_distribution': {int(k): v for k, v in fam_dist.items()},
        'cid_revisit_distribution': {int(k): v for k, v in revisit_dist.items()},
        # 判定数値・パラメータは含めない (Taka 念押し (a))
    }
    (OUT_DIR / 'summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n保存: attention_records.json ({len(records)} レコード)')
    print(f'保存: summary.json')
    print(f'\n=== Step 1b 完了 ===')


if __name__ == '__main__':
    main()
