#!/usr/bin/env python3
"""v12 Atomset — 経験(特徴度ベース一致率更新)の計算可能性 監査 (調査のみ、M5 実装なし)

Taka 案の検証: 『新しい一致率 = 元の一致率 ×(1 + 特徴度)』、
特徴度 = |今回の値 − その CID のいつもの平均| / その CID の標準偏差。
出会い系(ingestion/contact)と自己系(pulse/α/β/c_conv)の両方。

本スクリプトは「実コード・実データで確認」(memory: 推測でなく実測)のための再現器。
新しい run は回さない。既存の v107 source_events と v101 ingestion_events を読むだけ。

確認項目:
  (1) per-CID 過去蓄積が system 別に取れるか (= イベント数の per-CID 分布)
  (2) バラつきゼロ問題の深刻度 (= n<=2 の CID 割合)
  (4) pre-event snapshot が既に在るか (v107 *_pre 列)
  出会い相手の特定可能性は v101 ingestion_events の observer_cid/ghost_cid で確認。
"""
import sys, glob
import numpy as np
import pandas as pd
from collections import Counter

REPO = '/home/takasan/esde/ESDE-Research'
SRC = f'{REPO}/developmental/v107/outputs/smoke/source_events_seed0.parquet'
ING = f'{REPO}/developmental/v101/diag_v101_main/ingestion/ingestion_events_seed0.csv'


def rev2_main_scale():
    """Rev2: 本番 24 seeds で出会い系の真のサンプル数・σ定義可能率を取り直す。
    Rev1 の誤り: (a) seed0 一本 (b) ingestion(完食)チャネルだけ。
    正しい出会い = E3_contact (v917 other_records, 100,432件)。"""
    print('=== Rev2: 本番 24 seeds 再監査 (新 run なし) ===\n')

    # (A) 自己系 + ingestion(完食) を v107 main 24 seeds で集計
    files = sorted(glob.glob(f'{REPO}/developmental/v107/outputs/main/source_events_seed*.parquet'))
    SELF = ['pulse', 'alpha_formation', 'beta_formation', 'c_conversion']
    sd = Counter(); ge1 = Counter()
    enc_all = [0, 0]; self_all = [0, 0]
    for f in files:
        df = pd.read_parquet(f); N = df.source_cid.nunique()
        for et in SELF + ['ingestion']:
            s = df[df.event_source_type == et].groupby('source_cid').size()
            ge1[et] += s.shape[0]; sd[et] += int((s >= 3).sum())
        ing = df[df.event_source_type == 'ingestion'].groupby('source_cid').size()
        slf = df[df.event_source_type.isin(SELF)].groupby('source_cid').size()
        enc_all[0] += N; enc_all[1] += int((ing >= 3).sum())
        self_all[0] += N; self_all[1] += int((slf >= 3).sum())
    print(f'v107 main: {len(files)} seeds')
    print('  per type: with>=1 -> with>=3 (σ定義可能, % of present)')
    for et in SELF + ['ingestion']:
        print(f'    {et:16s}: >=1={ge1[et]:5d} >=3={sd[et]:5d} ({100*sd[et]/ge1[et]:.1f}%)')
    print(f'  ingestion(完食): σ定義可能 {enc_all[1]}/{enc_all[0]} = {100*enc_all[1]/enc_all[0]:.1f}% of ALL CIDs ← Rev1 が見た sparse チャネル')
    print(f'  pulse+abc(自己): σ定義可能 {self_all[1]}/{self_all[0]} = {100*self_all[1]/self_all[0]:.1f}% of ALL CIDs')

    # (B) 正しい出会い = E3_contact (v917 other_records, 100k)
    print()
    of = sorted(glob.glob(f'{REPO}/primitive/v917/diag_v917_main/selfread/other_records_seed*.csv'))
    tot = 0; nt = 0; n3 = 0; counts = []; partners = []
    for f in of:
        df = pd.read_csv(f, usecols=lambda c: c in ('cid_id', 'other_cid_id'))
        tot += len(df); g = df.groupby('cid_id')
        cnt = g.size(); up = g['other_cid_id'].nunique()
        nt += cnt.shape[0]; n3 += int((cnt >= 3).sum())
        counts += cnt.tolist(); partners += up.tolist()
    counts = np.array(counts); partners = np.array(partners)
    print(f'E3_contact (v917 other_records, 正しい出会いチャネル): {tot:,} 件 / {len(of)} seeds')
    print(f'  接触する CID: {nt}/5224')
    print(f'  contacts/CID: min={counts.min()} 中央値={int(np.median(counts))} 平均={counts.mean():.1f} max={counts.max()}')
    print(f'  σ定義可能(>=3 接触): {n3}/{nt} = {100*n3/nt:.1f}% of 接触CID  ← Rev1 の 7%/9.6% を撤回')
    print(f'  distinct partner>=3 (出会い距離分布が定義可能): {int((partners>=3).sum())}/{nt} = {100*(partners>=3).sum()/nt:.1f}%')
    print()
    print('  §3 頻度の裏口(本番): 出会い contacts/CID の広がり max/中央値 = '
          f'{counts.max()}/{int(np.median(counts))} ≈ {counts.max()//max(1,int(np.median(counts)))}倍 '
          '→ ×(1+z) を接触数だけ掛けると高接触CIDが圧倒 = near-universal 再発リスク')


if '--rev2' in sys.argv:
    rev2_main_scale()
    sys.exit(0)

df = pd.read_parquet(SRC)
N = df.source_cid.nunique()
print(f'=== v107 source_events smoke seed0: {len(df)} events, {N} CIDs ===\n')

SELF = ['pulse', 'alpha_formation', 'beta_formation', 'c_conversion']
ENC = ['ingestion']  # + contact(E3) が将来加わる

print('(1)+(2) per-CID イベント数分布と zero-variance 深刻度:')
print(f'{"system/type":18s} {"total":>6s} {"CIDs>=1":>8s} {"CIDs==1":>8s} {"CIDs<=2":>8s} {"CIDs>=3":>8s}')
for et in SELF + ENC:
    s = df[df.event_source_type == et].groupby('source_cid').size()
    print(f'{et:18s} {s.sum():6d} {s.shape[0]:8d} {(s==1).sum():8d} {(s<=2).sum():8d} {(s>=3).sum():8d}')

enc = df[df.event_source_type.isin(ENC)].groupby('source_cid').size()
slf = df[df.event_source_type.isin(SELF)].groupby('source_cid').size()
print(f'\n  ENCOUNTER 全体: 蓄積>=3 の CID = {(enc>=3).sum():3d}/{N}  '
      f'(全く出会わない CID = {N-enc.shape[0]})')
print(f'  SELF      全体: 蓄積>=3 の CID = {(slf>=3).sum():3d}/{N}  '
      f'(pulse min/CID = {df[df.event_source_type=="pulse"].groupby("source_cid").size().min()})')

print('\n(4) pre-event snapshot は既に v107 に在るか:')
pre = [c for c in df.columns if c.endswith('_pre')] + \
      ['lifespan_so_far', 'n_core_member', 'C_at_window_end', 'Q_remaining_at_window_end']
print('  既存 *_pre / 状態列:', pre)

print('\n(出会い相手) v101 ingestion_events の partner 列:')
ing = pd.read_csv(ING)
partner_cols = [c for c in ing.columns if c in ('observer_cid', 'ghost_cid', 'link_id')]
print('  ', partner_cols, '  rows:', len(ing))
print('  → observer_cid (eater) と ghost_cid (相手) が両方記録済 = 出会い相手 特定可能')
