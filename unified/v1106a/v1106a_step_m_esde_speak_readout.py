#!/usr/bin/env python3
"""v1106a Step M — ESDE が何を語っているか読み取り (B-1)

3,300 events の word 分布から ESDE の "発話" を複数切り口で集計:
  1. sample events の top-10 word (人間が読める形式)
  2. 全体頻出 word ranking (全 3,300 events 集約)
  3. input_atom 別の代表 word (atom が指す word top)
  4. CID 特性別の傾向 (lifespan/n_core_member/last_familiarity_max)
  5. seed 別の頻出 word (seed 間の個性)

入力 (read-only):
  - unified/v1106a/outputs/main/observation_Y_word_distributions.parquet (案 Y)
  - unified/v1105a/outputs/main/trial_step2_associations.parquet (event ↔ CID)
  - developmental/v105/diag_v105_main/per_subject_seed*.csv (CID 物理量)

出力:
  - unified/v1106a/outputs/main/esde_speak_sample_events.csv
  - unified/v1106a/outputs/main/esde_speak_global_top_words.csv
  - unified/v1106a/outputs/main/esde_speak_by_input_atom.csv
  - unified/v1106a/outputs/main/esde_speak_by_cid_property.csv
  - unified/v1106a/outputs/main/esde_speak_by_seed.csv
"""
from __future__ import annotations
import time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V105_MAIN = REPO / 'unified/v1105a/outputs/main'
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'
V105_DIAG = REPO / 'developmental/v105/diag_v105_main/subjects'


def get_cid_props():
    """全 seed の per_subject から CID 物理量を集約"""
    rows = []
    for sd in range(24):
        fp = V105_DIAG / f'per_subject_seed{sd}.csv'
        if not fp.exists():
            continue
        df = pd.read_csv(fp)
        if 'cognitive_id' not in df.columns:
            continue
        cols = ['cognitive_id']
        for c in ['last_familiarity_max', 'last_attention_size',
                  'n_alphas_currently', 'C_at_run_end',
                  'current_social', 'current_stability', 'current_spread',
                  'current_familiarity']:
            if c in df.columns:
                cols.append(c)
        sub = df[cols].copy()
        sub['seed'] = sd
        sub = sub.rename(columns={'cognitive_id': 'cid'})
        rows.append(sub)
    if not rows:
        return pd.DataFrame(columns=['seed', 'cid'])
    return pd.concat(rows, ignore_index=True)


def main():
    V1106A_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106a Step M — ESDE 発話読み取り (B-1) ===')
    t0 = time.time()

    # データ読み込み
    print('[1] データ読み込み')
    dist = pd.read_parquet(V1106A_MAIN / 'observation_Y_word_distributions.parquet')
    s7 = dist[dist['series_id'] == 's7_48d_raw_k5'].copy()
    print(f'  s7 word 分布 rows: {len(s7):,}, events: {s7.groupby(["seed","event_id"]).ngroups:,}')

    assoc = pd.read_parquet(V105_MAIN / 'trial_step2_associations.parquet',
                             columns=['seed', 'event_id', 'source_cid', 'input_atom'])
    event_cid = assoc.drop_duplicates(['seed', 'event_id', 'source_cid', 'input_atom'])
    print(f'  event-cid mapping: {len(event_cid):,}')

    cid_props = get_cid_props()
    print(f'  cid 物理量: {len(cid_props):,} rows, columns: {list(cid_props.columns)}')

    # rank per (event, series)
    s7 = s7.sort_values(['seed', 'event_id', 'probability'], ascending=[True, True, False])
    s7['rank'] = s7.groupby(['seed', 'event_id']).cumcount() + 1

    # ===== B-1-a: sample events の top-10 word =====
    print('\n[2] B-1-a: sample events の top-10 word')
    # input_atom が多様になるよう sample 抽出 (各 seed から最初の 5 event)
    sample_evt = s7.drop_duplicates(['seed', 'event_id'])[['seed', 'event_id', 'input_atom']]
    # 各 seed の最初 2 event
    sample_evt = sample_evt.groupby('seed').head(2).head(30)
    sample_keys = set(zip(sample_evt['seed'], sample_evt['event_id']))

    sample_top = s7[s7[['seed','event_id']].apply(tuple, axis=1).isin(sample_keys)]
    sample_top = sample_top[sample_top['rank'] <= 10].copy()
    sample_top = sample_top.merge(event_cid, on=['seed', 'event_id', 'input_atom'], how='left')
    sample_top = sample_top[['seed', 'event_id', 'source_cid', 'input_atom',
                              'rank', 'candidate_word', 'probability']]
    out1 = V1106A_MAIN / 'esde_speak_sample_events.csv'
    sample_top.to_csv(out1, index=False, float_format='%.4f')
    print(f'  wrote {out1.name} ({len(sample_top)} rows、{len(sample_keys)} events × 10 word)')

    # 人間が読める表示も
    print('\n--- sample event 発話 (3 event 分) ---')
    shown = 0
    for (sd, eid), grp in sample_top.groupby(['seed', 'event_id']):
        if shown >= 3: break
        ia = grp['input_atom'].iloc[0]
        cid = grp['source_cid'].iloc[0]
        print(f'\n  seed={sd}, event={eid}, CID={cid}, input_atom={ia}:')
        for _, r in grp.iterrows():
            print(f'    {r["rank"]:2}. {r["candidate_word"]:25s} (p={r["probability"]:.4f})')
        shown += 1

    # ===== B-1-b: 全体頻出 word ranking =====
    print('\n[3] B-1-b: 全体頻出 word (全 event 確率総和)')
    # 各 word の合計確率 (event 数で正規化、event 重み付き出現確率)
    n_events = s7[['seed','event_id']].drop_duplicates().shape[0]
    word_freq = s7.groupby('candidate_word').agg(
        total_prob=('probability', 'sum'),
        n_events_appeared=('probability', 'count'),
        mean_prob_when_appeared=('probability', 'mean'),
        max_prob=('probability', 'max'),
    ).reset_index()
    word_freq['mean_prob_per_event'] = word_freq['total_prob'] / n_events
    word_freq['event_coverage'] = word_freq['n_events_appeared'] / n_events
    word_freq = word_freq.sort_values('total_prob', ascending=False).reset_index(drop=True)
    word_freq.insert(0, 'rank', word_freq.index + 1)
    out2 = V1106A_MAIN / 'esde_speak_global_top_words.csv'
    word_freq.to_csv(out2, index=False, float_format='%.6f')
    print(f'  wrote {out2.name} ({len(word_freq):,} unique words)')

    print('\n--- ESDE が最もよく使う word top-20 ---')
    for _, r in word_freq.head(20).iterrows():
        print(f'  {int(r["rank"]):2}. {r["candidate_word"]:25s} '
              f'total_p={r["total_prob"]:8.2f}, coverage={r["event_coverage"]*100:5.1f}%, '
              f'mean_p_per_event={r["mean_prob_per_event"]:.4f}')

    # ===== B-1-c: input_atom 別の代表 word =====
    print('\n[4] B-1-c: input_atom 別の代表 word')
    # 各 input_atom について、その atom が input になった event 群での word 平均
    iatom_word = s7.groupby(['input_atom', 'candidate_word']).agg(
        total_prob=('probability', 'sum'),
        n_events=('probability', 'count'),
    ).reset_index()
    iatom_event_count = s7.groupby('input_atom')[['seed','event_id']].apply(
        lambda x: x.drop_duplicates().shape[0]).reset_index(name='n_events_with_this_atom')
    iatom_word = iatom_word.merge(iatom_event_count, on='input_atom')
    iatom_word['mean_prob_per_event'] = iatom_word['total_prob'] / iatom_word['n_events_with_this_atom']
    iatom_word = iatom_word.sort_values(['input_atom', 'total_prob'], ascending=[True, False])
    iatom_word['rank_in_atom'] = iatom_word.groupby('input_atom').cumcount() + 1
    iatom_top = iatom_word[iatom_word['rank_in_atom'] <= 10]
    out3 = V1106A_MAIN / 'esde_speak_by_input_atom.csv'
    iatom_top.to_csv(out3, index=False, float_format='%.6f')
    print(f'  wrote {out3.name} ({len(iatom_top)} rows、'
          f'{iatom_top["input_atom"].nunique()} atoms × top-10)')

    # よく登場する input_atom top 5 を見る
    print('\n--- 頻出 input_atom 別の代表 word ---')
    top_iatoms = iatom_event_count.nlargest(5, 'n_events_with_this_atom')
    for _, r in top_iatoms.iterrows():
        ia = r['input_atom']
        n = r['n_events_with_this_atom']
        words = iatom_top[iatom_top['input_atom'] == ia].head(5)
        word_list = ', '.join([f'{w["candidate_word"]}({w["mean_prob_per_event"]:.3f})'
                                for _, w in words.iterrows()])
        print(f'  {ia} (n_events={n}): {word_list}')

    # ===== B-1-d: CID 特性別の傾向 =====
    print('\n[5] B-1-d: CID 特性別 (lifespan / n_core_member) の word 傾向')
    # event を CID 特性で分類
    s7_evt = s7.drop_duplicates(['seed', 'event_id'])[['seed', 'event_id', 'input_atom']]
    s7_evt = s7_evt.merge(event_cid[['seed', 'event_id', 'source_cid']],
                            on=['seed', 'event_id'], how='left')
    s7_evt = s7_evt.merge(cid_props, left_on=['seed', 'source_cid'],
                            right_on=['seed', 'cid'], how='left')
    # 3 binning する物理量
    bin_targets = [c for c in ['last_familiarity_max', 'n_alphas_currently',
                                'current_stability', 'current_familiarity']
                    if c in s7_evt.columns]
    print(f'  bin candidates: {bin_targets}')

    cid_word_rows = []
    for prop in bin_targets:
        valid = s7_evt.dropna(subset=[prop]).copy()
        if len(valid) < 30:
            continue
        try:
            valid['bin'] = pd.qcut(valid[prop].rank(method='first'),
                                    q=3, labels=['low', 'mid', 'high'], duplicates='drop')
        except ValueError:
            continue
        for bin_label in ['low', 'mid', 'high']:
            evts = valid[valid['bin'] == bin_label][['seed', 'event_id']]
            if len(evts) == 0: continue
            keys = set(zip(evts['seed'], evts['event_id']))
            sub = s7[s7[['seed', 'event_id']].apply(tuple, axis=1).isin(keys)]
            agg = sub.groupby('candidate_word')['probability'].sum().sort_values(ascending=False)
            for rank, (w, p) in enumerate(agg.head(15).items(), 1):
                cid_word_rows.append({
                    'cid_property': prop,
                    'bin': bin_label,
                    'n_events': len(evts),
                    'rank': rank,
                    'candidate_word': w,
                    'total_prob': float(p),
                    'mean_prob_per_event': float(p / len(evts)),
                })

    cid_word_df = pd.DataFrame(cid_word_rows)
    out4 = V1106A_MAIN / 'esde_speak_by_cid_property.csv'
    cid_word_df.to_csv(out4, index=False, float_format='%.6f')
    print(f'  wrote {out4.name} ({len(cid_word_df)} rows)')

    for prop in cid_word_df['cid_property'].unique():
        print(f'\n--- CID {prop} 別 top-10 word ---')
        for bin_label in ['low', 'mid', 'high']:
            sub = cid_word_df[(cid_word_df['cid_property'] == prop)
                                & (cid_word_df['bin'] == bin_label)].head(10)
            if len(sub) == 0: continue
            words = ', '.join([r["candidate_word"] for _, r in sub.iterrows()])
            print(f'  {prop}={bin_label} (n={int(sub["n_events"].iloc[0])}): {words}')

    # ===== B-1-e: seed 別の頻出 word =====
    print('\n[6] B-1-e: seed 別の頻出 word (seed 個性)')
    seed_word_rows = []
    for sd in s7['seed'].unique():
        sub = s7[s7['seed'] == sd]
        n_evt = sub[['event_id']].drop_duplicates().shape[0]
        agg = sub.groupby('candidate_word')['probability'].sum().sort_values(ascending=False)
        for rank, (w, p) in enumerate(agg.head(20).items(), 1):
            seed_word_rows.append({
                'seed': int(sd), 'n_events': n_evt, 'rank': rank,
                'candidate_word': w, 'total_prob': float(p),
                'mean_prob_per_event': float(p / n_evt),
            })
    seed_word_df = pd.DataFrame(seed_word_rows)
    out5 = V1106A_MAIN / 'esde_speak_by_seed.csv'
    seed_word_df.to_csv(out5, index=False, float_format='%.6f')
    print(f'  wrote {out5.name} ({len(seed_word_df)} rows、24 seeds × top-20)')

    print(f'\n=== Step M 完了、elapsed {time.time()-t0:.1f}s ===')

    # 出力 summary
    print('\n--- 出力ファイル一覧 ---')
    print(f'  1. {out1.name}: sample event 別 top-10 word (人間が読む)')
    print(f'  2. {out2.name}: 全体頻出 word ranking')
    print(f'  3. {out3.name}: input_atom 別代表 word')
    print(f'  4. {out4.name}: CID 特性別 (lifespan/n_core)')
    print(f'  5. {out5.name}: seed 別頻出 word')


if __name__ == '__main__':
    main()
