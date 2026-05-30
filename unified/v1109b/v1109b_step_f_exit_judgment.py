#!/usr/bin/env python3
"""v1109b Step F — 出口 4 分岐判定 (A/B/C/D)"""
from pathlib import Path
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1109B = REPO / 'unified/v1109b/outputs/main'


def main():
    print('=== v1109b Step F — 出口 4 分岐判定 ===\n')

    # 検証結果読み込み
    shuf = pd.read_parquet(V1109B / 'verification_1_shuffle.parquet')
    sf = pd.read_parquet(V1109B / 'verification_2_self_fulfilling.parquet')
    loop = pd.read_parquet(V1109B / 'verification_3_loop.parquet')

    signs = ['start_match_rate', 'end_match_rate', 'npmi_strong_pairs',
              'per_to_tim_rate', 'role_switch_range']

    judgments = []
    for sign in signs:
        # 検証 1: shuffle - 全 4 shuffle で beats
        s_sub = shuf[shuf['sign'] == sign]
        beats_all = bool(s_sub['beats_shuffle'].all())
        beats_count = int(s_sub['beats_shuffle'].sum())

        # 検証 2: self-fulfilling - top1 vs sampling
        sf_pivot = sf[sf['sign'] == sign].set_index('condition')['value']
        v_top1 = float(sf_pivot.get('top1', 0))
        v_top2 = float(sf_pivot.get('top2', 0))
        v_samp = float(sf_pivot.get('probability_sampling', 0))
        v_hold = float(sf_pivot.get('seed_holdout', 0))
        # top1 固定: top1 が他より圧倒的に大
        is_top1_only = v_top1 > 0 and v_top1 > 2 * max(v_top2, v_samp)
        # sampling で残る: samp が top1 の 50% 以上
        sampling_persists = v_samp > 0.5 * v_top1 if v_top1 > 0 else True
        holdout_persists = v_hold > 0.5 * v_top1 if v_top1 > 0 else True

        # 検証 3: loop - loop 除外で残る
        l_pivot = loop[loop['sign'] == sign].set_index('condition')['value']
        v_all = float(l_pivot.get('all', 0))
        v_ne = float(l_pivot.get('non_self', 0))
        v_cc = float(l_pivot.get('cid_changed', 0))
        v_le = float(l_pivot.get('loop_excluded', 0))
        v_fv = float(l_pivot.get('first_visit', 0))
        loop_persists = (v_all > 0
                          and all(v > 0.5 * v_all for v in [v_ne, v_cc, v_le, v_fv]))

        # 出口判定
        if beats_all and sampling_persists and loop_persists:
            exit_label = 'A'
            desc = '全 shuffle 通過 + sampling でも残る + loop 除外でも残る → 本物'
        elif beats_count >= 2 and sampling_persists and not loop_persists:
            exit_label = 'B'
            desc = 'shuffle 通過するが loop 除外で消える → loop の裏返し'
        elif beats_count >= 2 and is_top1_only:
            exit_label = 'C'
            desc = 'top1 では出るが sampling で消える → top1 固定の副産物'
        elif beats_count == 0:
            exit_label = 'D'
            desc = 'shuffle と区別できない → 見かけの偏り'
        else:
            exit_label = 'B/C 混合'
            desc = '部分的に loop/top1 由来'

        judgments.append({
            'sign': sign,
            'beats_shuffle_count': beats_count,
            'sampling_persists': sampling_persists,
            'is_top1_only': is_top1_only,
            'loop_persists': loop_persists,
            'exit_label': exit_label,
            'description': desc,
        })

    jdf = pd.DataFrame(judgments)
    jdf.to_parquet(V1109B / 'verification_summary.parquet', index=False)

    print('--- 各兆候の出口判定 ---')
    for _, r in jdf.iterrows():
        print(f'\n{r["sign"]}:')
        print(f'  shuffle beat: {r["beats_shuffle_count"]}/4')
        print(f'  sampling 残る: {r["sampling_persists"]}, top1 固定: {r["is_top1_only"]}, loop 残る: {r["loop_persists"]}')
        print(f'  → 出口 {r["exit_label"]}: {r["description"]}')

    # 全体集約
    print('\n--- 出口別集計 ---')
    print(jdf['exit_label'].value_counts().to_string())

    # 全 sign で A 通過 = grammar の方向に進む条件
    all_A = (jdf['exit_label'] == 'A').sum()
    n_total = len(jdf)
    print(f'\n  出口 A 通過: {all_A}/{n_total}')
    if all_A == n_total:
        print(f'  → position-aware weight layer へ進める')
    else:
        print(f'  → position-aware weight layer に進む条件を満たさない')
        print(f'  → #L65 は loop / top1 / 見かけの偏りの混合、文法方向は時期尚早')


if __name__ == '__main__':
    main()
