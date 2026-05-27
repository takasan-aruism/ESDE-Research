#!/usr/bin/env python3
"""v1106b Step F — 観察 3: 局所共鳴 event の特性

Step L verification_a (3,300 events) の cos_sim 分布から:
- 上位 5% / 下位 5% / 中間 event を抽出
- 高 event vs 低 event の input_atom 偏り
- 高 event の word 分布が Step M 全体頻出 word と異なるか
- 高 event の CID 物理量特性

入力 (read-only):
- unified/v1106a/outputs/main/verification_a_cid_word_alignment.parquet
- unified/v1106a/outputs/main/observation_Y_word_distributions.parquet
- developmental/v105/diag_v105_main/subjects/per_subject_seed{N}.csv

出力:
- unified/v1106b/outputs/main/observation_3_high_low_events.parquet (event 別分類 + 統計)
- unified/v1106b/outputs/main/observation_3_input_atom_bias.parquet (input_atom 偏り)
- unified/v1106b/outputs/main/observation_3_word_distribution.parquet (高/低 event の word 分布)
"""
from __future__ import annotations
import time
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'
V1106B_MAIN = REPO / 'unified/v1106b/outputs/main'
V105_SUB = REPO / 'developmental/v105/diag_v105_main/subjects'

HIGH_PCT = 0.05  # 上位 5%
LOW_PCT = 0.05   # 下位 5%


def get_cid_props_all():
    rows = []
    for sd in range(24):
        fp = V105_SUB / f'per_subject_seed{sd}.csv'
        if not fp.exists():
            continue
        df = pd.read_csv(fp, usecols=['cognitive_id', 'final_state',
                                        'last_familiarity_max', 'n_alphas_currently',
                                        'current_stability', 'current_social'])
        df = df.rename(columns={'cognitive_id': 'cid'})
        df['seed'] = sd
        rows.append(df)
    return pd.concat(rows, ignore_index=True)


def main():
    print('=== v1106b Step F — 観察 3: 局所共鳴 event 特性 ===\n')
    t0 = time.time()

    # (1) verification_a データ読み込み
    print('[1] verification_a 読み込み')
    align = pd.read_parquet(V1106A_MAIN / 'verification_a_cid_word_alignment.parquet')
    print(f'  events: {len(align):,}')
    print(f'  cid_word_cos_sim: mean={align["cid_word_cos_sim"].mean():.4f}, '
          f'std={align["cid_word_cos_sim"].std():.4f}, '
          f'min={align["cid_word_cos_sim"].min():.4f}, '
          f'max={align["cid_word_cos_sim"].max():.4f}')

    # (2) 上位 5% / 下位 5% / 中間 抽出
    print('\n[2] 上位 5% / 下位 5% / 中間 event 分類')
    high_thresh = align['cid_word_cos_sim'].quantile(1 - HIGH_PCT)
    low_thresh = align['cid_word_cos_sim'].quantile(LOW_PCT)
    print(f'  high threshold (top {HIGH_PCT*100:.0f}%): {high_thresh:.4f}')
    print(f'  low threshold (bottom {LOW_PCT*100:.0f}%): {low_thresh:.4f}')

    align['event_class'] = 'mid'
    align.loc[align['cid_word_cos_sim'] >= high_thresh, 'event_class'] = 'high'
    align.loc[align['cid_word_cos_sim'] <= low_thresh, 'event_class'] = 'low'

    # CID 物理量を merge
    cid_props = get_cid_props_all()
    align = align.merge(cid_props[['seed', 'cid', 'final_state', 'last_familiarity_max',
                                       'n_alphas_currently', 'current_stability',
                                       'current_social']],
                          on=['seed', 'cid'], how='left')
    out1 = V1106B_MAIN / 'observation_3_high_low_events.parquet'
    align.to_parquet(out1, index=False)
    print(f'  wrote {out1.name} ({len(align)} rows)')

    # 各 class の集計
    print(f'\n  class 別 event 数 + 特性:')
    for cls in ['high', 'mid', 'low']:
        sub = align[align['event_class'] == cls]
        print(f'    {cls}: n={len(sub)}, '
              f'cos_sim mean={sub["cid_word_cos_sim"].mean():.4f}, '
              f'fam mean={sub["last_familiarity_max"].mean():.2f}')

    # (3) input_atom 偏り (高 vs 低)
    print('\n[3] input_atom 偏り (高 vs 低)')
    iatom_rows = []
    for cls in ['high', 'mid', 'low']:
        sub = align[align['event_class'] == cls]
        cnt = sub['input_atom'].value_counts()
        total = len(sub)
        for atom, n in cnt.head(15).items():
            iatom_rows.append({
                'event_class': cls, 'input_atom': atom,
                'n_events': int(n), 'pct': round(n / total, 4),
            })
    iatom_df = pd.DataFrame(iatom_rows)
    out2 = V1106B_MAIN / 'observation_3_input_atom_bias.parquet'
    iatom_df.to_parquet(out2, index=False)
    print(f'  wrote {out2.name}')

    print('\n  --- 高 event input_atom top 10 ---')
    print(iatom_df[iatom_df['event_class'] == 'high'].head(10).to_string(index=False))
    print('\n  --- 低 event input_atom top 10 ---')
    print(iatom_df[iatom_df['event_class'] == 'low'].head(10).to_string(index=False))

    # 全体 input_atom 分布との対比
    overall_iatom = align['input_atom'].value_counts() / len(align)
    print(f'\n  全 event 平均 input_atom top 5:')
    for atom, pct in overall_iatom.head(5).items():
        print(f'    {atom}: {pct:.4f}')

    # (4) 高/低 event の word 分布
    print('\n[4] 高/低 event の word 分布 (案 Y output から抽出)')
    dist = pd.read_parquet(V1106A_MAIN / 'observation_Y_word_distributions.parquet')
    s7 = dist[dist['series_id'] == 's7_48d_raw_k5']
    # 各 event の word top 20 を抽出
    word_rows = []
    for cls in ['high', 'low']:
        events_cls = align[align['event_class'] == cls][['seed', 'event_id']]
        keys = set(zip(events_cls['seed'], events_cls['event_id']))
        sub = s7[s7[['seed','event_id']].apply(tuple, axis=1).isin(keys)]
        # 集約: word 別 total prob
        agg = sub.groupby('candidate_word')['probability'].sum().sort_values(ascending=False)
        n_events_cls = len(events_cls)
        for rank, (w, p) in enumerate(agg.head(30).items(), 1):
            word_rows.append({
                'event_class': cls,
                'rank': rank,
                'candidate_word': w,
                'total_prob': float(p),
                'mean_prob_per_event': float(p / n_events_cls),
                'n_events_cls': n_events_cls,
            })
    word_df = pd.DataFrame(word_rows)
    out3 = V1106B_MAIN / 'observation_3_word_distribution.parquet'
    word_df.to_parquet(out3, index=False)
    print(f'  wrote {out3.name}')

    print(f'\n  --- 高 event word top 15 ---')
    high_words = word_df[word_df['event_class'] == 'high'].head(15)
    for _, r in high_words.iterrows():
        print(f'    {int(r["rank"]):2}. {r["candidate_word"]:25s} '
              f'mean_p_per_event={r["mean_prob_per_event"]:.4f}')

    print(f'\n  --- 低 event word top 15 ---')
    low_words = word_df[word_df['event_class'] == 'low'].head(15)
    for _, r in low_words.iterrows():
        print(f'    {int(r["rank"]):2}. {r["candidate_word"]:25s} '
              f'mean_p_per_event={r["mean_prob_per_event"]:.4f}')

    # (5) 高 vs 低 event の CID 物理量比較
    print('\n[5] 高 vs 低 event の CID 物理量比較')
    for col in ['last_familiarity_max', 'n_alphas_currently', 'current_stability',
                  'current_social']:
        print(f'\n  --- {col} ---')
        for cls in ['high', 'mid', 'low']:
            sub = align[align['event_class'] == cls].dropna(subset=[col])
            if len(sub) > 0:
                print(f'    {cls}: n={len(sub)}, mean={sub[col].mean():.3f}, '
                      f'median={sub[col].median():.3f}, '
                      f'std={sub[col].std():.3f}')

    # final_state 分布
    print('\n  --- final_state 分布 (event_class 別) ---')
    fs_pivot = align.groupby(['event_class', 'final_state'],
                              observed=True).size().reset_index(name='n')
    print(fs_pivot.to_string(index=False))

    print(f'\n=== Step F 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
