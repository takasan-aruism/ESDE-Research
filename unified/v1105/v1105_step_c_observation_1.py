#!/usr/bin/env python3
"""v1105 Step C — 観察 1: 段 4-b 地形 (連想を辿る)

Genesis 側: v1104+v1104a の追加調整 1 出力 (observation_2_scope_stratified)
            から scope × n_size × shuffle × self-loop の lift_C を継承
Language 側: v1103 proposals.json の B_COUPLE 6 pair から endpoint atoms 12 を抽出、
            response_atom_distribution.parquet の candidate_atom が endpoint atoms に
            接触する頻度を scope × 粒度 (receiver_bin) 別に集計

注記 (Step C 着手前修正、2026-05-24):
  v1103 response_atom_distribution の `is_couple_link` 列は全 False (start_atom と
  candidate_atom の両方が couple pair として登録されている場合のみ True にする厳しい
  判定、該当 0 件)。設計書 §2.2 文面「候補 atom が Couple endpoint に接触」は
  解釈 A (candidate_atom が 12 endpoint atoms に含まれる) を採用する。これは
  Step A 認識確認 §1.5 の粗集計 (237/5670 = 4.18%) と一致する。
  is_couple_link 列は使わず、candidate_atom.isin(couple_endpoints) で判定する。

出力:
  - unified/v1105/outputs/main/observation_1_terrain_4b.parquet
    (per (receiver_bin, change_metric_type) で lift_C + couple_hit_rate 2 種 + scope ラベル)
"""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1103_MAIN = REPO_ROOT / 'unified/v1103/outputs/main'
V1104A_MAIN = REPO_ROOT / 'unified/v1104a/outputs/main'
V1105_MAIN = REPO_ROOT / 'unified/v1105/outputs/main'


def scope_of_receiver_bin(rb: str) -> str:
    if rb.startswith('CID_n='): return 'CID'
    if rb.startswith('alpha_'): return 'alpha'
    if rb.startswith('beta_'): return 'beta'
    if rb.startswith('ESDE_'): return 'ESDE'
    return 'other'


def main():
    V1105_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1105 Step C 観察 1: 段 4-b 地形 (連想を辿る) ===')
    t0 = time.time()

    # ---- (1) Genesis 側: predecessor lift_C (v1104a observation_2_scope_stratified) ----
    print('\n[1] Genesis: predecessor lift_C (v1104a 継承)')
    o2s = pd.read_parquet(V1104A_MAIN / 'observation_2_scope_stratified.parquet')
    # shuffle_type='C' のみ抽出、scope/n_size_bin/is_full_self_loop 別の lift_mean
    g = o2s[o2s['shuffle_type'] == 'C'].copy()
    print(f'  observation_2_scope_stratified shuffle=C: {len(g)} rows')

    # ---- (2) Language 側: Couple endpoint atoms + candidate 接触判定 ----
    print('\n[2] Language: Couple endpoint atoms + response candidate 接触')
    with open(V1103_MAIN / 'proposals.json') as f:
        p = json.load(f)
    couple_endpoints = set()
    for c in p['proposals']:
        if c['pattern'] == 'B_COUPLE':
            couple_endpoints.add(c['atom_a'])
            couple_endpoints.add(c['atom_b'])
    print(f'  B_COUPLE endpoint atoms: {len(couple_endpoints)}')

    rad = pd.read_parquet(V1103_MAIN / 'response_atom_distribution.parquet')
    rad['scope'] = rad['receiver_bin'].apply(scope_of_receiver_bin)
    rad['cand_is_couple_endpoint'] = rad['candidate_atom'].isin(couple_endpoints)
    # 設計書 §2.2 解釈 A: candidate_atom が endpoint set に含まれるかで判定
    # is_couple_link 列は使わない (v1103 で全 False)
    print(f'  rad rows: {len(rad)}, cand_is_couple_endpoint True: '
          f'{rad["cand_is_couple_endpoint"].sum()} ({100*rad["cand_is_couple_endpoint"].mean():.2f}%)')

    # per (receiver_bin, change_metric_type) で couple_hit_rate 2 種計算
    couple_rows = []
    for (rb, mt), grp in rad.groupby(['receiver_bin', 'change_metric_type']):
        n_total = len(grp)
        n_hits = int(grp['cand_is_couple_endpoint'].sum())
        prob_sum = grp['response_prob'].sum()
        prob_hits = float((grp['response_prob'] * grp['cand_is_couple_endpoint']).sum())
        couple_rows.append({
            'receiver_bin': rb,
            'change_metric_type': mt,
            'scope': scope_of_receiver_bin(rb),
            'n_candidates': n_total,
            'n_couple_hits': n_hits,
            'couple_hit_rate_unweighted': n_hits / n_total if n_total else np.nan,
            'couple_hit_rate_prob_weighted': prob_hits / prob_sum if prob_sum else np.nan,
        })
    cr = pd.DataFrame(couple_rows)
    print(f'  couple_hit_rate per (receiver_bin, metric): {len(cr)} rows')

    # ---- (3) Genesis lift_C を receiver_bin 形に合わせて並列保持 ----
    # observation_2_scope_stratified の change_scope/n_size_bin から receiver_bin への
    # 対応は v1104a と v1102/v1101a で命名規則が一致 (CID_n=2..6+ / ESDE_event 等)
    # alpha/beta は alpha_n=N / beta_n=N (gini なし) でなく
    # alpha_n=N / gini=X (v1102 命名) なので、v1104a side は n_size_bin (alpha_n=1..4+ / beta_n=1..4+)
    # で集約済。alpha/beta は n_size_bin だけで scope 集約 (gini 軸は v1105 で組まない、軸追加禁止)
    g_lift_c = g.rename(columns={'change_scope': 'scope_genesis',
                                   'n_size_bin': 'receiver_bin_or_proxy'})
    # receiver_bin プロキシ:
    #  - CID: n_size_bin = CID_n=2..5+ (v1104a) ≒ CID_n=2..6+ (v1102/Language)、CID_n=5+ ↔ CID_n=5/6+ は別扱い
    #  - alpha/beta: n_size_bin = alpha_n=N / beta_n=N (v1104a) と alpha_n=N / gini=X (v1102)
    #               は異なる命名、scope 集約値として整理 (scope-level couple_hit_rate と並べる)
    #  - ESDE: n_size_bin = ESDE_event/step10/window (v1104a) と Language receiver_bin 同名

    # scope-level Genesis lift_C 集計 (self-loop 別)
    lc_scope = g.groupby(['change_scope', 'is_full_self_loop']).agg(
        lift_C_mean=('lift_mean', 'mean'),
        lift_C_n_chains=('n_chains', 'sum'),
    ).reset_index()
    print(f'\n[3] Genesis lift_C scope × self-loop: {len(lc_scope)} rows')
    print(lc_scope.to_string(index=False))

    # ---- (4) scope-level couple_hit_rate (Language 側集約) ----
    cr_scope = cr.groupby('scope').agg(
        n_candidates_total=('n_candidates', 'sum'),
        n_couple_hits_total=('n_couple_hits', 'sum'),
        couple_hit_rate_unweighted_mean=('couple_hit_rate_unweighted', 'mean'),
        couple_hit_rate_prob_weighted_mean=('couple_hit_rate_prob_weighted', 'mean'),
    ).reset_index()
    cr_scope['couple_hit_rate_unweighted_pooled'] = (
        cr_scope['n_couple_hits_total'] / cr_scope['n_candidates_total'])
    print(f'\n[4] Language couple_hit_rate scope 集約:')
    print(cr_scope.to_string(index=False))

    # ---- (5) ESDE 3 解像度別 (粒度感度) ----
    esde = cr[cr['scope'] == 'ESDE']
    esde_grp = esde.groupby('receiver_bin').agg(
        n_candidates=('n_candidates', 'sum'),
        n_couple_hits=('n_couple_hits', 'sum'),
        couple_hit_rate_unweighted=('couple_hit_rate_unweighted', 'mean'),
        couple_hit_rate_prob_weighted=('couple_hit_rate_prob_weighted', 'mean'),
    ).reset_index()
    print(f'\n[5] ESDE 3 解像度別 couple_hit_rate:')
    print(esde_grp.to_string(index=False))

    # ---- (6) CID n_size_bin × Language couple_hit_rate + Genesis lift_C 別レイヤー並列 ----
    # Language: receiver_bin = CID_n=2..6+ 別
    # Genesis: n_size_bin = CID_n=2..5+ 別 (v1104a 命名差異)
    cid_lang = cr[cr['scope'] == 'CID'].groupby('receiver_bin').agg(
        n_candidates=('n_candidates', 'sum'),
        n_couple_hits=('n_couple_hits', 'sum'),
        couple_hit_rate_unweighted=('couple_hit_rate_unweighted', 'mean'),
        couple_hit_rate_prob_weighted=('couple_hit_rate_prob_weighted', 'mean'),
    ).reset_index()
    cid_lang['cid_n_label'] = cid_lang['receiver_bin']
    print(f'\n[6] CID n_size_bin 別 Language couple_hit_rate:')
    print(cid_lang.to_string(index=False))

    # Genesis 側 CID 全 self-loop (Step B 確認済 100%)
    cid_gen = g[g['change_scope'] == 'CID'].groupby(['n_size_bin', 'is_full_self_loop']).agg(
        lift_C_mean=('lift_mean', 'mean'),
        n_chains=('n_chains', 'sum'),
    ).reset_index()
    print(f'\n[7] CID n_size_bin 別 Genesis lift_C (shuffle=C):')
    print(cid_gen.to_string(index=False))

    # ---- (8) 統合表: receiver_bin (Language 側 27 種) を行、別レイヤーで Genesis lift_C と Language couple_hit_rate を持つ ----
    # Genesis 側は scope-level 値を receiver_bin の scope に応じて join
    # (v1104a scope_stratified の n_size_bin と Language の receiver_bin は命名差異あり、
    #  ここでは scope-level 集約値を Genesis 列として持ち、receiver_bin 単位で Language 値と並べる)
    integrated_rows = []
    # Genesis scope-level lift_C (shuffle=C、self-loop 別)
    gen_scope_self = lc_scope.set_index(['change_scope', 'is_full_self_loop'])
    for _, row in cr.iterrows():
        rb = row['receiver_bin']; sc = row['scope']
        if sc == 'CID':
            # CID は 100% self-loop なので is_full_self_loop=True
            gen_self = gen_scope_self.loc[('CID', True), 'lift_C_mean'] if ('CID', True) in gen_scope_self.index else np.nan
            gen_nonself = np.nan
        elif sc in ('alpha', 'beta'):
            gen_self = gen_scope_self.loc[(sc, True), 'lift_C_mean'] if (sc, True) in gen_scope_self.index else np.nan
            gen_nonself = gen_scope_self.loc[(sc, False), 'lift_C_mean'] if (sc, False) in gen_scope_self.index else np.nan
        elif sc == 'ESDE':
            esde_key = rb  # ESDE_event/step10/window 直接 match
            gen_self = gen_scope_self.loc[(esde_key, True), 'lift_C_mean'] if (esde_key, True) in gen_scope_self.index else np.nan
            gen_nonself = gen_scope_self.loc[(esde_key, False), 'lift_C_mean'] if (esde_key, False) in gen_scope_self.index else np.nan
        else:
            gen_self = np.nan; gen_nonself = np.nan
        integrated_rows.append({
            'receiver_bin': rb,
            'change_metric_type': row['change_metric_type'],
            'scope': sc,
            # Genesis side
            'genesis_lift_C_self_loop': float(gen_self) if not pd.isna(gen_self) else np.nan,
            'genesis_lift_C_non_self_loop': float(gen_nonself) if not pd.isna(gen_nonself) else np.nan,
            # Language side
            'language_couple_hit_rate_unweighted': row['couple_hit_rate_unweighted'],
            'language_couple_hit_rate_prob_weighted': row['couple_hit_rate_prob_weighted'],
            'language_n_candidates': row['n_candidates'],
            'language_n_couple_hits': row['n_couple_hits'],
        })
    integrated = pd.DataFrame(integrated_rows)
    out = V1105_MAIN / 'observation_1_terrain_4b.parquet'
    integrated.to_parquet(out, index=False)
    print(f'\n[8] integrated 段 4-b 地形: {len(integrated)} rows wrote {out.name}')

    print(f'\n=== Step C 観察 1 完了、elapsed {time.time()-t0:.1f}s ===')

    # ---- サマリ ----
    print('\n--- scope × 段 4-b 地形 サマリ (別レイヤー、judgment 回避) ---')
    s = integrated.groupby('scope').agg(
        n_cells=('receiver_bin', 'nunique'),
        genesis_lift_C_self=('genesis_lift_C_self_loop', 'mean'),
        genesis_lift_C_nonself=('genesis_lift_C_non_self_loop', 'mean'),
        couple_hit_rate_u=('language_couple_hit_rate_unweighted', 'mean'),
        couple_hit_rate_pw=('language_couple_hit_rate_prob_weighted', 'mean'),
    ).round(4)
    print(s.to_string())


if __name__ == '__main__':
    main()
