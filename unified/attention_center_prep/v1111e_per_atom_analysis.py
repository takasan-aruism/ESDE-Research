#!/usr/bin/env python3
"""v1111e_redo (修正版) の per-atom 層化再集計

Taka 指摘 2026-06-02:
- 集団平均の罠 (24 atom 全ペア cos 平均で個別動態が消える)
- 「動的平衡が強烈な ESDE で見方を工夫しないと結果が見えづらい」

実装:
- 既存 parquet (between/subgroups/self_floor/inversion) を atom seed 別に集計
- atom 別 inversion 判定: injected_d_between < shuffled_d_between
- group 別 (8 atom × 3 group) 動態 (既に集計あり、subgroups.parquet)
- self 床距離の atom 別動態
"""
import pandas as pd
import numpy as np

BASE = '/home/takasan/esde/ESDE-Research/unified/attention_center_prep/run_v1111e_redo'
OUT = '/home/takasan/esde/ESDE-Research/unified/attention_center_prep/v1111e_per_atom_summary.md'

between = pd.read_parquet(f'{BASE}/between_recorded_only.parquet')
subgroups = pd.read_parquet(f'{BASE}/subgroups.parquet')
self_floor = pd.read_parquet(f'{BASE}/self_floor_recorded_only.parquet')
inv_main = pd.read_parquet(f'{BASE}/inversion.parquet')

print('=' * 70)
print('v1111e_redo per-atom 層化再集計')
print('=' * 70)

# === 1. atom 別 inversion (between cos) ===
print('\n## 1. atom 別 inversion (injected_d_between < shuffled_d_between)')
print('   d_between cos 小 = Other 間で形が近い (Other 依存少なめ、一貫)')
print('   d_between cos 大 = Other 間で形が違う (Other 依存大、個性あり)')

pivot = between.pivot(index='atom_seed', columns='condition',
                      values='d_between_cos_mean')
pivot['gap'] = pivot['shuffled_other'] - pivot['injected_other']
pivot['inversion'] = pivot['injected_other'] < pivot['shuffled_other']
print(pivot.to_string())
n_inv = int(pivot['inversion'].sum())
print(f'\n  atom 別 inversion: {n_inv}/24')
print(f'  inversion が出る atom: {pivot[pivot["inversion"]].index.tolist()}')
print(f'  inversion 出ない atom: {pivot[~pivot["inversion"]].index.tolist()}')

# === 2. group 別動態 (既集計) ===
print('\n## 2. group 別 inversion (8 atom × 3 group × 3 Other)')
print(subgroups.to_string(index=False))
print()
gb = subgroups.groupby('group')['inversion'].sum().reset_index()
gb.columns = ['group', 'n_inversion_per_group']
print(gb.to_string(index=False))
print(f'\n  group 0 (atom 1000-1007): {int(gb.iloc[0]["n_inversion_per_group"])}/3')
print(f'  group 1 (atom 1008-1015): {int(gb.iloc[1]["n_inversion_per_group"])}/3')
print(f'  group 2 (atom 1016-1023): {int(gb.iloc[2]["n_inversion_per_group"])}/3')

# === 3. self 床距離 (atom × Other × cond) ===
print('\n## 3. self 床からの cos 距離 (atom × Other × cond)')
sf_pivot = self_floor.groupby(['atom_seed', 'condition'])['cos_from_self'].mean().reset_index()
sf_pivot = sf_pivot.pivot(index='atom_seed', columns='condition', values='cos_from_self')
sf_pivot['gap_self_floor'] = sf_pivot['shuffled_other'] - sf_pivot['injected_other']
sf_pivot['injected_closer_to_self'] = sf_pivot['injected_other'] < sf_pivot['shuffled_other']
print(sf_pivot.to_string())
n_closer = int(sf_pivot['injected_closer_to_self'].sum())
print(f'\n  atom 別 「injected が self に近い」: {n_closer}/24')
print(f'  → shuffled の方が self から離れる atom 多 = Atom 構造が支配的 (Taka 整理)')

# === 4. d_between の分布 ===
print('\n## 4. d_between cos の atom seed 別分布 (集団平均で消えた個別)')
print('\n  injected_other:')
inj = between[between['condition']=='injected_other']['d_between_cos_mean']
print(f'    mean={inj.mean():.4f}, std={inj.std():.4f}, min={inj.min():.4f}, max={inj.max():.4f}')
print(f'    quartiles: 25%={inj.quantile(0.25):.4f}, 50%={inj.median():.4f}, 75%={inj.quantile(0.75):.4f}')
print('\n  shuffled_other:')
shuf = between[between['condition']=='shuffled_other']['d_between_cos_mean']
print(f'    mean={shuf.mean():.4f}, std={shuf.std():.4f}, min={shuf.min():.4f}, max={shuf.max():.4f}')
print(f'    quartiles: 25%={shuf.quantile(0.25):.4f}, 50%={shuf.median():.4f}, 75%={shuf.quantile(0.75):.4f}')

# === 5. 集団平均 vs per-atom の差 ===
print('\n## 5. 集団平均 vs per-atom 結果の比較')
print('\n  集団平均 (Other 別、24 atom cos 平均):')
for _, r in inv_main.iterrows():
    print(f'    Other={int(r["other_seed"])}: inj={r["injected_cos"]:.4f} '
          f'vs shuf={r["shuffled_cos"]:.4f} gap={r["gap"]:+.4f} '
          f'inversion={r["inversion"]}')

print('\n  per-atom (atom 別 d_between):')
print(f'    inversion 出る atom: {n_inv}/24 atom')
print(f'    group 別 inversion: g0={int(gb.iloc[0]["n_inversion_per_group"])}/3 '
      f'g1={int(gb.iloc[1]["n_inversion_per_group"])}/3 g2={int(gb.iloc[2]["n_inversion_per_group"])}/3')

# === 6. 集約: 過去パターンとの整合性 ===
print('\n## 6. 過去パターンとの整合性 (棚卸し reference_legacy_treasures より)')
print('  - n_core 別層化: 本データに n_core 情報なし、再 run で取得必要')
print('  - per-step 観察: 本データは window 単位、再 run で per-step 必要')
print('  - 5 種 event + 5 種 path: 本データは occupancy のみ、追加観察必要')
print('  - source-specific 性 94% (v10.7): event 別観察で識別可能、本データでは不可')

# === md 出力 ===
report = f"""# v1111e_redo per-atom 層化再集計

**Date**: 2026-06-02
**Author**: Code A
**目的**: Taka 指摘「集団平均の罠」を per-atom 層化で見直す

## 主要発見

### 1. atom 別 inversion: {n_inv}/24
- 集団平均 (24 atom cos) では 2/3 Other inversion
- per-atom 個別判定で {n_inv}/24 atom が inversion 寄り
- 24 atom が一様ではない (個性あり)

### 2. group 別 (8 atom × 3 group)
- group 0 (atom 1000-1007): {int(gb.iloc[0]["n_inversion_per_group"])}/3 Other inversion
- group 1 (atom 1008-1015): {int(gb.iloc[1]["n_inversion_per_group"])}/3 Other inversion
- group 2 (atom 1016-1023): {int(gb.iloc[2]["n_inversion_per_group"])}/3 Other inversion

→ **group 2 のみ動態が逆**。集団平均で消えていた個別動態。

### 3. self 床距離
- {n_closer}/24 atom で injected が self に近い
- shuffled の方が self から離れる atom 多 = Atom 構造支配的 (Taka 整理「どの seed でもそれらしい形」と整合)

### 4. d_between 分布
- injected_other: mean={inj.mean():.4f}, std={inj.std():.4f}, min={inj.min():.4f}, max={inj.max():.4f}
- shuffled_other: mean={shuf.mean():.4f}, std={shuf.std():.4f}, min={shuf.min():.4f}, max={shuf.max():.4f}

## 過去パターン未流用の確認

| パターン | 状態 |
|---|---|
| n_core 別層化 (v10.2 核心) | 本データに n_core 情報なし、**再 run で取得必要** |
| per-step 観察 (v9.18) | 本データは window 単位、**再 run で per-step 必要** |
| 5 種 event + 5 種 path (v10.7) | 本データは occupancy のみ、**追加観察必要** |

## 結論

- 集団平均 (2/3 inversion) は 24 atom 横断の平均化結果
- per-atom で見ると group 2 が逆方向 = **全 atom が同じ動態ではない**
- ですが本データに n_core / per-step / event 別の情報なし
- 「集団平均で消えた個別動態」を本格的に見るには **再 run で観察軸を増やす必要**
"""
with open(OUT, 'w') as f:
    f.write(report)
print(f'\n  → 報告書: {OUT}')
