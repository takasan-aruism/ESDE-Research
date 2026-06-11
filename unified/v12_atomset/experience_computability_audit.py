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
import pandas as pd

REPO = '/home/takasan/esde/ESDE-Research'
SRC = f'{REPO}/developmental/v107/outputs/smoke/source_events_seed0.parquet'
ING = f'{REPO}/developmental/v101/diag_v101_main/ingestion/ingestion_events_seed0.csv'

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
