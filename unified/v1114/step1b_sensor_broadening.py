#!/usr/bin/env python3
"""v1114 Step 1b 強化版 — 過去 CID 研究の不足 3 軸を足して percept を完成 (差し替え)

## 観察対象注釈ブロック (実装着手前に明示、Code A 自己強制ハードル)

### 観察対象の本質
- 同じ系内 (Center 単体)
- Step 1 + cid id + cid_birth/death に、**過去 CID 研究 (v10.2 / v10.10) で重要と明記されている 3 軸**
  (formation_relation / pulse 反応 / lifecycle phase) を percept に追加
- **発見テストではない**: 過去データが既に出してる構造 (n_core 別の寿命差等) を新発見と主張しない
- 目的: Step 2 で使える、欠けのない percept を作ること

### 過去成功事例との照合 (Web Claude 2026-06-06 網羅参照)
- v10.2: n_core 最重要軸 (n_core=2→5 で寿命 8 倍、意識 25 倍、C 4 倍)
- v10.2 detailed: bulk(2)=短命/単発 pulse 反応、hub(5)=長命/反復/C 豊富
- v10.10 §3.4: bulk は pulse で反応、hub は C で反応 (反応 type 分業、必須参照)
- v10.10 規律 38: formation_relation が応答性の決定因子、形成完了後は応答性消失
- v10.2: lifecycle phase が決定的 (誕生 Q0 でなく、いつ起きたか)

### 過去失敗パターン回避
- v1110-v1113 = 異なる系の対応関係発想で 4 連続失敗
- 本実装は Center 単体、cid id = 認知 ID (node ID でない)

### 残さないもの (Taka 規律「取れないなら落とす・すり替えない」)
- node ID / 座標 (phase_sig / θ) / 不透明 float ベクトル
- 判定数値 (z-score / EWMA) - 発火判定にのみ使用、レコード/summary に残さない
- 設計パラメータ - summary に残さない
- 差・有意差の測定値 - 報告は「percept が 3 軸含んで完成し、溜まって、多様か」だけ
- **周辺の大きさ list (familiarity 相手の n_core list)**: v918 output 取得不可、Step 2/3 で取得経路検討
- **近似値の擦り替え**: pulse_reactivity は本物の pulse event 実数 (last_attention_size は使わない、二重 NG)、
  lifecycle_phase は死んだ CID のみ (生存中は偽の全寿命で埋めず "unknown")、
  n_core は source_event がない CID は "unknown" (近似で埋めない)

### 残すフィールド (実機確認済み、本物のみ、近似なし)
- cid (認知 ID、node ID でない)
- point: n_core / lifespan / **lifecycle_phase** / **formation_relation** / **pulse_reactivity** / C / Q_remaining
- neighborhood: familiarity_n

### 引き金 7 種 (Step 1 と同じ、独立監視、合成しない)
- 既存 5 種 (source_events): pulse / ingestion / alpha_formation / beta_formation / c_conversion
- 新規 2 種 (per_subject 構築): cid_birth / cid_death

### 実機確認結果 (2026-06-06)
- pulse 反応: source_events の pulse event の source_cid = pulse 発火 CID、228 CID 全てで発火実数取得可
- formation_relation: alpha_formation event の source_cid + timestamp、129 CID で α 形成あり (99 CID は no_alpha)
- lifecycle phase: 228 CID 中 191 死亡確定 (reaped 143 + ghost 48)、37 生存中 (hosted = censored → "unknown")

### 出口 (Web Claude 設計 §5、Taka 規律「古いことを新発見と言わない」)
- percept が 3 軸を含んで完成し、溜まって、それらの軸で多様か (だけ)
- 「bulk は短命だった」「pulse で反応した」等の構造発見は書かない (v10.2/v10.10 が既に出してる)
- crown 禁止 + 再発見禁止
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
WINDOW_STEPS = 500
FORMATION_RELATION_THRESHOLD = 100  # after_0_100 と after_100plus の境界 (step 単位)

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
    print('=== v1114 Step 1b 強化版 — 過去 CID 研究の不足 3 軸を足して percept 完成 ===\n')
    print(f'  Center seed: {CENTER_SEED}')
    print(f'  per-{N_PER_CHUNK}step 観察')
    print(f'  追加 3 軸 (Web Claude 2026-06-06 設計):')
    print(f'    formation_relation (記号、規律 38): before / after_0_100 / after_100plus / no_alpha')
    print(f'    pulse_reactivity (実数、本物): source_cid 一致 pulse event 件数')
    print(f'    lifecycle_phase (比率、v10.2): 年齢/全寿命、死亡確定 CID のみ、生存中は "unknown"')
    print(f'  Taka 規律:')
    print(f'    pulse_reactivity は本物の pulse event 実数 (last_attention_size 近似でない)')
    print(f'    lifecycle_phase は死亡 CID のみ (生存中は偽全寿命で埋めず "unknown")')
    print(f'    n_core 不明は "unknown" (近似で埋めない)')
    print(f'  目的: Step 2 で使える欠けのない percept、過去既出構造の再発見ではない\n')

    if not (PER_SUBJECT_PATH.exists() and SOURCE_EVENTS_PATH.exists()):
        print(f'ERROR: 入力ファイル不在')
        sys.exit(1)

    subj_df = pd.read_csv(PER_SUBJECT_PATH)
    events_df = pd.read_parquet(SOURCE_EVENTS_PATH)

    # === 各 CID の pre-compute (本物の数、近似なし) ===
    # ★ 補正 (2026-06-06、Web Claude/Taka 承認): 時計を tracking step で揃える
    # 旧: per_subject の birth_window × WINDOW_STEPS = absolute step (起点が違う)
    # 新: source_events 内部の birth_step / host_lost_step を直接使う (tracking step)
    # 根拠: v107 event_aggregator line 241 で window_value = (timestamp // 500) + 19
    #       per_subject の birth_window と source_events の timestamp は +19 window オフセット
    # 補正は時計を揃えるだけ、percept の中身 (n_core/C/Q/familiarity 等) はいじらない

    # n_core (生誕固定、どの source_event からでも取れる、不明なら "unknown")
    n_core_by_cid = (events_df.dropna(subset=['n_core_member'])
                     .groupby('source_cid')['n_core_member'].first().astype(int).to_dict())

    # pulse_reactivity (本物: source_cid 一致 pulse event 件数)
    pulse_count_by_cid = (events_df[events_df['event_source_type'] == 'pulse']
                          .groupby('source_cid').size().to_dict())

    # alpha_formation 最早 timestamp (各 CID の α 形成時刻、なければ None)
    alpha_time_by_cid = (events_df[events_df['event_source_type'] == 'alpha_formation']
                         .groupby('source_cid')['timestamp'].min().to_dict())

    # ★ birth_step: source_events 内部の birth_step フィールドを直接使う (tracking step、時計揃う)
    birth_step_by_cid = (events_df.dropna(subset=['birth_step'])
                         .groupby('source_cid')['birth_step'].first().astype(int).to_dict())

    # ★ death_step: source_events 内部の host_lost_step を直接使う (tracking step、時計揃う)
    death_step_by_cid = (events_df.dropna(subset=['host_lost_step'])
                         .groupby('source_cid')['host_lost_step'].first().astype(int).to_dict())

    print(f'pre-compute 結果 (時計補正後、全て tracking step):')
    print(f'  n_core 取得 CID 数: {len(n_core_by_cid)} (= source_events を持つ CID)')
    print(f'  pulse_reactivity 取得 CID 数: {len(pulse_count_by_cid)}')
    print(f'  alpha_time 取得 CID 数: {len(alpha_time_by_cid)} (残り {len(subj_df) - len(alpha_time_by_cid)} は no_alpha)')
    print(f'  birth_step 取得 CID 数: {len(birth_step_by_cid)} (source_events 内部 birth_step 使用)')
    print(f'  death_step 取得 CID 数: {len(death_step_by_cid)} (source_events 内部 host_lost_step 使用、'
          f'残り {len(n_core_by_cid) - len(death_step_by_cid)} は censored)\n')

    subj_by_cid = {safe_int(row['cognitive_id']): row for _, row in subj_df.iterrows()}

    # === formation_relation の判定関数 ===
    def get_formation_relation(cid, attention_time):
        if cid not in alpha_time_by_cid:
            return 'no_alpha'
        alpha_time = alpha_time_by_cid[cid]
        delta = attention_time - alpha_time
        if delta < 0:
            return 'before'
        elif delta <= FORMATION_RELATION_THRESHOLD:
            return 'after_0_100'
        else:
            return 'after_100plus'

    # === lifecycle_phase の判定関数 (死亡確定 CID のみ、生存中は "unknown") ===
    # Web Claude 指摘 (2026-06-06): 負値バグ修正
    # 根本原因: per_subject の birth_window (cog.born_at[cid]) と source_events の
    # timestamp で整合性が取れない (228 CID 中 225 件で min_event_ts < birth_step)
    # → age < 0 (誕生前) や age > total (死後) のケースが発生
    # 修正: 範囲外は "unknown" 明示、偽の比率で埋めない (Taka 規律「すり替えない」)
    def get_lifecycle_phase(cid, attention_time):
        if cid not in birth_step_by_cid:
            return 'unknown'  # 誕生時刻不明
        birth = birth_step_by_cid[cid]
        if cid not in death_step_by_cid:
            return 'unknown'  # censored (生存中)、偽全寿命で埋めない
        death = death_step_by_cid[cid]
        total = death - birth
        if total <= 0:
            return 'unknown'
        age = attention_time - birth
        if age < 0 or age > total:
            # 誕生前 or 死後 = phase 計算不能 (per_subject vs source_events の整合性問題)
            return 'unknown'
        return round(age / total, 3)

    # === 引き金 7 種 = 既存 5 + 新規 (cid_birth / cid_death) ===
    # ★ 補正 (2026-06-06): cid_birth / cid_death event の timestamp も tracking step で構築
    # 旧: per_subject の birth_window × WINDOW_STEPS = absolute step (起点違い)
    # 新: source_events 内部の birth_step / host_lost_step を直接 timestamp に使う (時計揃う)
    # 結果: 既存 5 種引き金と cid_birth/death が同じ時計 (tracking step) で揃う
    new_events_rows = []
    for cid, birth_step in birth_step_by_cid.items():
        new_events_rows.append({
            'event_source_type': 'cid_birth',
            'source_cid': cid,
            'timestamp': birth_step,
        })
    for cid, death_step in death_step_by_cid.items():
        new_events_rows.append({
            'event_source_type': 'cid_death',
            'source_cid': cid,
            'timestamp': death_step,
        })
    new_events_df = pd.DataFrame(new_events_rows)

    events_combined = pd.concat([
        events_df[['event_source_type', 'source_cid', 'timestamp']],
        new_events_df[['event_source_type', 'source_cid', 'timestamp']],
    ], ignore_index=True)

    events_combined['chunk'] = (events_combined['timestamp'] // N_PER_CHUNK).astype(int)
    max_chunk = int(events_combined['chunk'].max())
    event_types = sorted(events_combined['event_source_type'].unique())

    print(f'動学の長さ: {max_chunk + 1} chunks (= {(max_chunk + 1) * N_PER_CHUNK} steps)')
    print(f'引き金 7 種 (独立 running 統計、合成しない):')
    for et in event_types:
        n = len(events_combined[events_combined['event_source_type'] == et])
        print(f'  {et}: {n} events')
    print()

    counts_per_chunk = events_combined.groupby(['chunk', 'event_source_type']).size().unstack(fill_value=0)
    full_chunks = pd.DataFrame(index=range(max_chunk + 1), columns=event_types, data=0)
    for et in event_types:
        if et in counts_per_chunk.columns:
            full_chunks[et] = counts_per_chunk[et].reindex(full_chunks.index, fill_value=0)

    # === 独立 EWMA + z-score、alert で percept レコード生成 ===
    running_stats = {et: {'mean': 0.0, 'var': 1.0, 'count': 0} for et in event_types}
    records = []
    order = 0

    # source_events の各行の {source_cid, timestamp} -> row index map (state 取得用)
    events_by_cid_ts = {}
    for idx, row in events_df.iterrows():
        cid = safe_int(row['source_cid'])
        ts = int(row['timestamp'])
        events_by_cid_ts.setdefault((cid, ts), idx)

    for chunk_idx in range(max_chunk + 1):
        for et in event_types:
            n = int(full_chunks.loc[chunk_idx, et])
            z = ewma_update(running_stats[et], float(n))
            if abs(z) <= Z_NOTICE:
                continue
            chunk_events_of_type = events_combined[
                (events_combined['chunk'] == chunk_idx) &
                (events_combined['event_source_type'] == et)
            ]
            if len(chunk_events_of_type) == 0:
                continue
            e = chunk_events_of_type.sort_values('timestamp').iloc[0]
            cid = safe_int(e['source_cid'])
            cid_subj = subj_by_cid.get(cid)
            attention_time = int(e['timestamp'])

            # n_core: 生誕固定、source_event ある CID なら取れる、なければ "unknown"
            n_core_val = n_core_by_cid.get(cid, 'unknown')

            # lifespan: source_events から取れれば取る (既存 5 種は取れる、新規 2 種は計算)
            if et in ('cid_birth', 'cid_death'):
                if cid in birth_step_by_cid:
                    lifespan_steps = attention_time - birth_step_by_cid[cid]
                    lifespan_val = max(0, lifespan_steps)
                else:
                    lifespan_val = 0
            else:
                # 既存 5 種: source_events に lifespan_so_far がある
                orig_idx = events_by_cid_ts.get((cid, attention_time))
                if orig_idx is not None:
                    lifespan_val = safe_int(events_df.loc[orig_idx, 'lifespan_so_far'])
                else:
                    lifespan_val = 0

            # C, Q_remaining: 既存 5 種は source_events から、cid_birth/death は event 時点で source_events 対応なし
            if et in ('cid_birth', 'cid_death'):
                # cid_birth/death では C, Q_remaining 不明 (近似で埋めない、"unknown" を明示)
                C_val = 'unknown'
                Q_rem_val = 'unknown'
            else:
                orig_idx = events_by_cid_ts.get((cid, attention_time))
                if orig_idx is not None:
                    C_val = safe_int(events_df.loc[orig_idx, 'C_at_window_end'])
                    Q_rem_val = safe_int(events_df.loc[orig_idx, 'Q_remaining_at_window_end'])
                else:
                    C_val = 'unknown'
                    Q_rem_val = 'unknown'

            # 過去研究の不足 3 軸 (新規追加)
            formation_relation = get_formation_relation(cid, attention_time)
            pulse_reactivity = pulse_count_by_cid.get(cid, 0)  # 本物の pulse event 実数
            lifecycle_phase = get_lifecycle_phase(cid, attention_time)

            point = {
                'n_core': n_core_val,
                'lifespan': lifespan_val,
                'lifecycle_phase': lifecycle_phase,  # 死亡 CID は比率、生存中は "unknown"
                'formation_relation': formation_relation,  # 記号
                'pulse_reactivity': pulse_reactivity,  # 本物の実数
                'C': C_val,
                'Q_remaining': Q_rem_val,
            }
            neighborhood = {
                'familiarity_n': safe_int(cid_subj['last_n_partners']) if cid_subj is not None else 0,
            }
            record = {
                'order': order,
                'cid': cid,  # 認知 ID、node ID でない
                'trigger': et,  # 記号
                'point': point,
                'neighborhood': neighborhood,
            }
            records.append(record)
            order += 1

    # === 報告 (Web Claude 設計 §5: percept が 3 軸含んで完成・溜まって・多様か、だけ) ===
    print('=' * 60)
    print('Step 1b 強化版 観察 (percept 完成 + 溜まったか + 多様か)')
    print('=' * 60)
    print(f'\nレコード数: {len(records)}')

    if len(records) == 0:
        print('\n→ レコード溜まらず')
        (OUT_DIR / 'summary.json').write_text(json.dumps({
            'design': 'v1114_step1b_v2',
            'records_total': 0,
        }, indent=2, ensure_ascii=False))
        return

    # 引き金 7 種分布
    trigger_dist = Counter(r['trigger'] for r in records)
    print(f'\n引き金 (記号、7 種) の分布:')
    for trig in event_types:
        cnt = trigger_dist.get(trig, 0)
        marker = ' ★ 新規' if trig in ('cid_birth', 'cid_death') else ''
        print(f'  {trig}: {cnt}{marker}')

    # 点の n_core 分布 (unknown 含む)
    n_core_dist = Counter(str(r['point']['n_core']) for r in records)
    print(f'\n点の n_core 分布:')
    for nc in sorted(n_core_dist.keys(), key=lambda x: (x == 'unknown', x)):
        cnt = n_core_dist[nc]
        marker = ''
        try:
            ncv = int(nc)
            if ncv == 2: marker = ' ← bulk'
            elif ncv >= 4: marker = ' ← hub'
        except ValueError:
            pass
        print(f'  n_core={nc}: {cnt}{marker}')

    # formation_relation 分布 (新規軸)
    fr_dist = Counter(r['point']['formation_relation'] for r in records)
    print(f'\nformation_relation 分布 (新規軸、規律 38、記号):')
    for fr in ['before', 'after_0_100', 'after_100plus', 'no_alpha']:
        print(f'  {fr}: {fr_dist.get(fr, 0)}')

    # pulse_reactivity 分布 (新規軸、本物)
    pr_dist = Counter(r['point']['pulse_reactivity'] for r in records)
    print(f'\npulse_reactivity 分布 (新規軸、本物の pulse event 実数、上位 10):')
    sorted_pr = sorted(pr_dist.items())
    pr_bins = [(0, 1), (1, 50), (50, 200), (200, 500), (500, 5000)]
    for lo, hi in pr_bins:
        c = sum(1 for r in records if lo <= r['point']['pulse_reactivity'] < hi)
        if c > 0:
            print(f'  pulse_reactivity [{lo:>4}, {hi:>5}): {c}')

    # lifecycle_phase 分布 (新規軸、unknown / 比率帯)
    print(f'\nlifecycle_phase 分布 (新規軸、unknown = 生存中、比率 = 死亡 CID):')
    unknown_count = sum(1 for r in records if r['point']['lifecycle_phase'] == 'unknown')
    print(f'  unknown (生存中、censored): {unknown_count}')
    phase_bins = [(0.0, 0.1), (0.1, 0.3), (0.3, 0.7), (0.7, 0.95), (0.95, 1.01)]
    for lo, hi in phase_bins:
        c = sum(1 for r in records
                if r['point']['lifecycle_phase'] != 'unknown'
                and lo <= r['point']['lifecycle_phase'] < hi)
        if c > 0:
            print(f'  phase [{lo:.2f}, {hi:.2f}): {c}')

    # cid id の多様性
    unique_cids = set(r['cid'] for r in records)
    cid_visit_counts = Counter(r['cid'] for r in records)
    revisit_dist = Counter(cid_visit_counts.values())
    print(f'\n注意が落ちた CID のユニーク数: {len(unique_cids)}')
    print(f'CID あたりの注意回数分布 (Step 2 で同 CID 戻り/別 CID 移動判定材料):')
    for n_visits, n_cids in sorted(revisit_dist.items()):
        print(f'  {n_visits}回注意: {n_cids} CID')

    # 引き金 × n_core 二次元
    print(f'\n引き金 × n_core 二次元:')
    cross = defaultdict(lambda: defaultdict(int))
    for r in records:
        cross[r['trigger']][str(r['point']['n_core'])] += 1
    n_cores_sorted = sorted({nc for ncs in cross.values() for nc in ncs},
                            key=lambda x: (x == 'unknown', x))
    header = '  trigger\\\\n_core ' + ' '.join(f'{nc:>5}' for nc in n_cores_sorted)
    print(header)
    for trig in event_types:
        row = f'  {trig:<18}' + ' '.join(f'{cross[trig].get(nc, 0):>5}' for nc in n_cores_sorted)
        print(row)

    # === 出力 ===
    (OUT_DIR / 'attention_records.json').write_text(
        json.dumps(records, indent=2, ensure_ascii=False))
    summary = {
        'design': 'v1114_step1b_v2_sensor_broadening',
        'center_seed': CENTER_SEED,
        'trigger_types': event_types,
        'records_total': len(records),
        'unique_cids_attended': len(unique_cids),
        'trigger_distribution': dict(trigger_dist),
        'n_core_distribution': {str(k): v for k, v in n_core_dist.items()},
        'formation_relation_distribution': dict(fr_dist),
        'lifecycle_phase_unknown_count': unknown_count,
        'cid_revisit_distribution': {int(k): v for k, v in revisit_dist.items()},
        # 判定数値・パラメータ・差は含めない (Taka 念押し)
    }
    (OUT_DIR / 'summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n保存: attention_records.json ({len(records)} レコード) + summary.json')
    print(f'\n=== Step 1b 強化版 完了 ===')
    print(f'percept が 3 軸 (formation_relation / pulse_reactivity / lifecycle_phase) を含んで完成、')
    print(f'溜まって、多様か = 上記分布で確認 (差は測らない、過去既出構造の再発見でない)')


if __name__ == '__main__':
    main()
