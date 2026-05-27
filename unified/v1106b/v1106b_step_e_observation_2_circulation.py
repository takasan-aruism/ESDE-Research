#!/usr/bin/env python3
"""v1106b Step E — 観察 2: 循環構造 attractor 検出

観察 1 (Step D) の familiarity_trajectory データを再集計:
- 各 start_cid の turn 別 cid 軌跡 → 既訪 CID 復帰 turn 検出
- unique CID 数、復帰率
- attractor 候補抽出: 複数 start_cid から到達される CID、stuck 終端 CID

入力 (read-only):
- unified/v1106b/outputs/main/observation_1_familiarity_trajectory.parquet

出力:
- unified/v1106b/outputs/main/observation_2_circulation.parquet (per start_cid 集計)
- unified/v1106b/outputs/main/observation_2_attractors.parquet (attractor 候補)
- unified/v1106b/outputs/main/observation_2_aggregate.parquet (final_state × fam_bin 別集計)
"""
from __future__ import annotations
import time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1106B_MAIN = REPO / 'unified/v1106b/outputs/main'


def main():
    print('=== v1106b Step E — 観察 2: 循環構造 attractor 検出 ===\n')
    t0 = time.time()

    # (1) 軌跡データ読み込み
    print('[1] observation_1_familiarity_trajectory 読み込み')
    hist = pd.read_parquet(V1106B_MAIN / 'observation_1_familiarity_trajectory.parquet')
    print(f'  rows: {len(hist):,}')
    print(f'  start_cids: {hist[["seed","start_cid"]].drop_duplicates().shape[0]}')

    # (2) per start_cid 循環構造集計
    print('\n[2] per start_cid 循環構造集計')
    circ_rows = []
    visit_count = defaultdict(int)  # (seed, cid) → 総訪問回数 (全 start_cid 横断)
    arrival_count = defaultdict(set)  # (seed, cid) → どの start_cid から到達したか
    stuck_terminal = defaultdict(int)  # (seed, cid) → ここで stuck 終端した start_cid 数

    for (sd, start_cid), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn')
        cids = grp_sorted['cid'].tolist()
        n_turn = len(cids)

        # 既訪 CID 復帰 turn (最初に復帰した turn)
        seen = set()
        first_revisit_turn = None
        for i, c in enumerate(cids):
            if c in seen and first_revisit_turn is None:
                first_revisit_turn = i
            seen.add(c)
            visit_count[(sd, c)] += 1
            arrival_count[(sd, c)].add(start_cid)

        # 軌跡末尾の CID (stuck 終端)
        terminal_cid = cids[-1]
        # stuck_at_turn が記録されていれば終端 stuck と判定
        stuck_at = grp_sorted['stuck_at_turn'].iloc[0]
        if pd.notna(stuck_at):
            stuck_terminal[(sd, terminal_cid)] += 1

        # 復帰 CID 集合 (turn 軌跡内で 2 回以上出現)
        cnt = defaultdict(int)
        for c in cids:
            cnt[c] += 1
        repeated_cids = [c for c, n in cnt.items() if n >= 2]
        max_revisit = max(cnt.values()) if cnt else 0

        circ_rows.append({
            'seed': sd, 'start_cid': start_cid,
            'n_turns': n_turn,
            'n_unique_cid': len(set(cids)),
            'n_repeated_cid': len(repeated_cids),
            'max_revisit_count': max_revisit,
            'first_revisit_turn': first_revisit_turn,
            'terminal_cid': terminal_cid,
            'start_final_state': grp_sorted['start_final_state'].iloc[0],
            'start_fam_bin': grp_sorted['start_fam_bin'].iloc[0],
        })
    circ_df = pd.DataFrame(circ_rows)
    out1 = V1106B_MAIN / 'observation_2_circulation.parquet'
    circ_df.to_parquet(out1, index=False)
    print(f'  wrote {out1.name} ({len(circ_df)} rows)')

    # (3) attractor 候補
    print('\n[3] attractor 候補抽出')
    attractor_rows = []
    for (sd, c), v_cnt in visit_count.items():
        n_arrival = len(arrival_count[(sd, c)])
        n_stuck = stuck_terminal[(sd, c)]
        attractor_rows.append({
            'seed': sd, 'cid': c,
            'total_visits': v_cnt,
            'n_distinct_start_cid_arrival': n_arrival,
            'n_stuck_terminal': n_stuck,
        })
    att_df = pd.DataFrame(attractor_rows)
    att_df = att_df.sort_values(['n_distinct_start_cid_arrival', 'n_stuck_terminal'],
                                 ascending=False).reset_index(drop=True)
    out2 = V1106B_MAIN / 'observation_2_attractors.parquet'
    att_df.to_parquet(out2, index=False)
    print(f'  wrote {out2.name} ({len(att_df)} rows)')

    # (4) final_state × fam_bin 別集計
    print('\n[4] final_state × fam_bin 別循環構造集計')
    agg = circ_df.groupby(['start_final_state', 'start_fam_bin'], observed=True).agg(
        n_start=('start_cid', 'count'),
        unique_cid_mean=('n_unique_cid', 'mean'),
        unique_cid_median=('n_unique_cid', 'median'),
        repeated_cid_mean=('n_repeated_cid', 'mean'),
        max_revisit_mean=('max_revisit_count', 'mean'),
        first_revisit_turn_median=('first_revisit_turn', 'median'),
        revisit_within_15turn_rate=('first_revisit_turn',
                                      lambda x: x.notna().mean()),
    ).round(3).reset_index()
    out3 = V1106B_MAIN / 'observation_2_aggregate.parquet'
    agg.to_parquet(out3, index=False)
    print(f'  wrote {out3.name}')

    print(f'\n=== Step E 完了、elapsed {time.time()-t0:.1f}s ===\n')

    # サマリ
    print('--- 全体循環構造 ---')
    print(f'  n_start_cids: {len(circ_df)}')
    print(f'  unique CID per start: mean={circ_df["n_unique_cid"].mean():.2f}, '
          f'median={circ_df["n_unique_cid"].median():.0f}')
    print(f'  repeated CID per start (2+ 回訪問 CID 数): '
          f'mean={circ_df["n_repeated_cid"].mean():.2f}')
    print(f'  max revisit count per start: mean={circ_df["max_revisit_count"].mean():.2f}')
    print(f'  first revisit turn: median={circ_df["first_revisit_turn"].median():.0f}, '
          f'count notna={circ_df["first_revisit_turn"].notna().sum()}/{len(circ_df)}')

    print('\n--- final_state × fam_bin 別 ---')
    print(agg.to_string(index=False))

    # attractor top 10 (n_distinct_start_cid_arrival 順)
    print('\n--- attractor top 10 (n_distinct_start_cid_arrival 順) ---')
    top_att = att_df.head(10)
    print(top_att.to_string(index=False))

    # 自己 attractor (start_cid 自身が終端 attractor になっているか)
    print('\n--- 高 attractor CID (5+ start から到達) の集計 ---')
    high_att = att_df[att_df['n_distinct_start_cid_arrival'] >= 5]
    print(f'  count: {len(high_att)} / {len(att_df)}')
    if len(high_att) > 0:
        print(f'  per_seed 分布:')
        print(high_att.groupby('seed').size().describe().to_string())


if __name__ == '__main__':
    main()
