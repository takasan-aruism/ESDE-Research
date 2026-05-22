#!/usr/bin/env python3
"""v1104 Step E — 観察 4: 際立ち掬い取り B の現状確認

設計書 §2.4 + GPT 修正必須 C (selector 化禁止):
- B primary 化した場合の仮想順位・仮想候補集合を post-process で算出のみ
- ESDE 内部 (attention_emit / salience / cid_state_ledger) に一切書き戻さない
- 「B に選ばせる」は次主題以降の別判断
- 書込み unified/v1104/outputs/ 配下のみ

入力:
- v10.5 salience_event_log (candidate_mass)
- v1101a attention_emit (change_metric_value / change_rank_within_type / qc_ratio)
- v1102 outstanding_cells (A primary 結果、81 cells × outstanding_score)
- v1101a Step G stratified_observation (Integration 構成層化)

出力: observation_4_b_overlap.parquet
書込み: unified/v1104/outputs/main/ のみ
"""
from __future__ import annotations
import argparse, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V105_SAL = REPO_ROOT / 'developmental/v105/diag_v105_main/salience'
V1101A_MAIN = REPO_ROOT / 'unified/v1101a/outputs/main'
V1102_MAIN = REPO_ROOT / 'unified/v1102/outputs/main'
OUT_MAIN = REPO_ROOT / 'unified/v1104/outputs/main'

WINDOW_RANGE = list(range(20, 70))


def category_of(atom: str) -> str:
    return atom.split('.')[0] if isinstance(atom, str) and '.' in atom else 'UNK'


def compute_b_emit_per_cell() -> pd.DataFrame:
    """ESDE 自身の emit (B) を per cell に集約"""
    t0 = time.time()
    rows_b = []
    for sd in range(24):
        # 1. v10.5 salience_event_log
        sal_p = V105_SAL / f'salience_event_log_seed{sd}.csv'
        sal = pd.read_csv(sal_p)
        # candidate_cid 単位で mass 合計 (per cid の重要性 emit)
        cid_mass = sal.groupby('candidate_cid')['candidate_mass'].agg(['mean', 'sum', 'count']).reset_index()
        cid_mass.columns = ['cognitive_id', 'sal_mass_mean', 'sal_mass_sum', 'sal_event_count']
        cid_mass['seed'] = sd

        # 2. v1101a attention_emit
        em_p = V1101A_MAIN / f'attention_emit_seed{sd}.parquet'
        em = pd.read_parquet(em_p, columns=['seed','window','change_scope','scope_id',
                                              'change_metric_type','change_metric_value',
                                              'change_rank_within_type','qc_ratio',
                                              'attention_candidate_id'])
        em = em[em['window'].isin(WINDOW_RANGE)]

        # per (change_scope, scope_id, change_metric_type) で B 指標集約
        agg = em.groupby(['change_scope','scope_id','change_metric_type']).agg(
            cmv_mean=('change_metric_value', 'mean'),
            cmv_max=('change_metric_value', 'max'),
            crank_mean=('change_rank_within_type', 'mean'),  # 低いほど際立ち
            qc_ratio_mean=('qc_ratio', 'mean'),
            qc_ratio_std=('qc_ratio', 'std'),
            n_records=('change_metric_value', 'count'),
        ).reset_index()
        agg['seed'] = sd

        # attention_candidate_id を介して salience mass を join (per cid level)
        em_cid = em[['seed','change_scope','scope_id','change_metric_type','attention_candidate_id']]
        em_cid = em_cid.dropna(subset=['attention_candidate_id'])
        em_cid['attention_candidate_id'] = em_cid['attention_candidate_id'].astype(int)
        em_cid = em_cid.merge(cid_mass.rename(columns={'cognitive_id': 'attention_candidate_id'}),
                                on=['seed','attention_candidate_id'], how='left')

        sal_per_cell = em_cid.groupby(['change_scope','scope_id','change_metric_type']).agg(
            sal_mass_mean_via_cand=('sal_mass_mean', 'mean'),
            sal_mass_sum_via_cand=('sal_mass_sum', 'mean'),
            sal_event_count_mean=('sal_event_count', 'mean'),
        ).reset_index()

        merged = agg.merge(sal_per_cell, on=['change_scope','scope_id','change_metric_type'], how='left')
        rows_b.append(merged)

    df_b = pd.concat(rows_b, ignore_index=True)
    print(f'B emit per (seed, scope, scope_id, metric): {len(df_b):,} records, elapsed {time.time()-t0:.1f}s')
    return df_b


def aggregate_b_to_receiver_bin(df_b: pd.DataFrame) -> pd.DataFrame:
    """per (scope, scope_id) を v1102 receiver_bin × change_metric_type に集約"""
    comp_a = pd.read_parquet(V1101A_MAIN / 'integration_composition_alpha.parquet')
    comp_b = pd.read_parquet(V1101A_MAIN / 'integration_composition_beta.parquet')

    cid_ncore_rows = []
    for sd in range(24):
        p = REPO_ROOT / 'developmental/v106/outputs/main/window_trajectory' / f'window_cid_alignment_seed{sd}.csv'
        df = pd.read_csv(p, usecols=['cognitive_id', 'n_core_member'])
        g = df.groupby('cognitive_id')['n_core_member'].max()
        for cid, n in g.items():
            cid_ncore_rows.append({'seed': sd, 'scope_id': int(cid), 'n_core_member': int(n)})
    cid_ncore = pd.DataFrame(cid_ncore_rows)

    def cid_bin(n):
        if pd.isna(n): return 'NA'
        n = int(n)
        if n == 2: return 'CID_n=2'
        if n == 3: return 'CID_n=3'
        if n == 4: return 'CID_n=4'
        if n == 5: return 'CID_n=5'
        return 'CID_n=6+'
    def n_alpha_bin(n):
        if pd.isna(n): return 'NA'
        n = int(n)
        return 'alpha_n=1' if n==1 else ('alpha_n=2' if n==2 else ('alpha_n=3' if n==3 else 'alpha_n=4+'))
    def n_beta_bin(n):
        if pd.isna(n): return 'NA'
        n = int(n)
        return 'beta_n=1' if n==1 else ('beta_n=2' if n==2 else ('beta_n=3' if n==3 else 'beta_n=4+'))
    def gini_bin(g):
        if pd.isna(g): return 'NA'
        if g < 0.05: return 'gini=low'
        if g < 0.20: return 'gini=mid'
        return 'gini=high'

    parts = []
    sub = df_b[df_b['change_scope'] == 'alpha'].copy()
    sub = sub.merge(comp_a.rename(columns={'alpha_id': 'scope_id'}), on=['seed','scope_id'], how='left')
    sub['receiver_bin'] = sub['n_members'].apply(n_alpha_bin) + ' / ' + sub['qc_gini_mean'].apply(gini_bin)
    parts.append(sub)
    sub = df_b[df_b['change_scope'] == 'beta'].copy()
    sub = sub.merge(comp_b.rename(columns={'beta_id': 'scope_id'}), on=['seed','scope_id'], how='left')
    sub['receiver_bin'] = sub['n_members'].apply(n_beta_bin) + ' / ' + sub['qc_gini_mean'].apply(gini_bin)
    parts.append(sub)
    sub = df_b[df_b['change_scope'] == 'CID'].copy()
    sub = sub.merge(cid_ncore, on=['seed','scope_id'], how='left')
    sub['receiver_bin'] = sub['n_core_member'].apply(cid_bin)
    parts.append(sub)
    sub = df_b[df_b['change_scope'].isin(['ESDE_event','ESDE_step10','ESDE_window'])].copy()
    sub['receiver_bin'] = sub['change_scope']
    parts.append(sub)
    full = pd.concat(parts, ignore_index=True)

    # per (receiver_bin, change_metric_type) で B emit 集約
    cols = ['cmv_mean','cmv_max','crank_mean','qc_ratio_mean','qc_ratio_std',
            'sal_mass_mean_via_cand','sal_mass_sum_via_cand','sal_event_count_mean']
    agg = full.groupby(['receiver_bin','change_metric_type']).agg(
        **{c: (c, 'mean') for c in cols},
        n_subrecords=('cmv_mean', 'count'),
    ).reset_index()
    return agg


def main():
    OUT_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1104 Step E 観察 4 (際立ち掬い取り B 現状確認) ===')

    t_start = time.time()
    df_b = compute_b_emit_per_cell()
    print(f'\nB emit per cell 集約 (receiver_bin × metric)...')
    b_cell = aggregate_b_to_receiver_bin(df_b)
    print(f'B cells: {len(b_cell)}')

    # v1102 A primary (outstanding_cells)
    print(f'A primary (v1102 outstanding_cells) load...')
    a_cell = pd.read_parquet(V1102_MAIN / 'outstanding_cells.parquet')
    print(f'A cells: {len(a_cell)}')

    # join: A + B
    merged = a_cell.merge(b_cell, on=['receiver_bin','change_metric_type'], how='outer',
                            suffixes=('_a','_b'))
    print(f'A+B merged cells: {len(merged)}')

    # B 指標で per cell 仮想スコア算出 (post-process のみ、ESDE 内部に書き戻さない)
    # B score 候補:
    # - cmv_mean (高いほど際立ち)
    # - crank_mean (低いほど際立ち、逆方向)
    # - sal_mass_mean_via_cand (高いほど salience 強い)
    # - qc_ratio_std (規律変動の幅)
    valid = merged.dropna(subset=['cmv_mean','crank_mean','sal_mass_mean_via_cand']).copy()
    if len(valid) > 0:
        # Top 10% で B 際立ち判定 (構造的閾値、神の手回避)
        from scipy.stats import spearmanr, pearsonr
        thresh_cmv = valid['cmv_mean'].quantile(0.90)
        thresh_sal = valid['sal_mass_mean_via_cand'].quantile(0.90)
        thresh_crank_low = valid['crank_mean'].quantile(0.10)  # 低いほど際立ち

        valid['B_outstanding_cmv'] = valid['cmv_mean'] >= thresh_cmv
        valid['B_outstanding_sal'] = valid['sal_mass_mean_via_cand'] >= thresh_sal
        valid['B_outstanding_crank'] = valid['crank_mean'] <= thresh_crank_low
        # B 際立ちスコア (3 指標のいずれか)
        valid['B_outstanding_score'] = (valid['B_outstanding_cmv'].astype(int) +
                                          valid['B_outstanding_sal'].astype(int) +
                                          valid['B_outstanding_crank'].astype(int))
        # A 際立ちスコア (v1102 outstanding_score)
        valid['A_outstanding_high'] = valid['outstanding_score'] >= 3

        # A と B の重なり (Jaccard / Recall)
        a_cells = set(valid[valid['A_outstanding_high']].index)
        b_cells_any = set(valid[valid['B_outstanding_score'] >= 1].index)
        b_cells_strong = set(valid[valid['B_outstanding_score'] >= 2].index)

        ab_inter = len(a_cells & b_cells_any)
        ab_union = len(a_cells | b_cells_any)
        jaccard_ab = ab_inter / ab_union if ab_union > 0 else 0.0
        recall_b_to_a = ab_inter / len(a_cells) if a_cells else 0.0
        precision_b_to_a = ab_inter / len(b_cells_any) if b_cells_any else 0.0

        # 相関
        rp_cmv, pp_cmv = pearsonr(valid['cmv_mean'], valid['outstanding_score'])
        rs_cmv, ps_cmv = spearmanr(valid['cmv_mean'], valid['outstanding_score'])
        rp_sal, pp_sal = pearsonr(valid['sal_mass_mean_via_cand'], valid['outstanding_score'])
        rs_sal, ps_sal = spearmanr(valid['sal_mass_mean_via_cand'], valid['outstanding_score'])

        out = OUT_MAIN / 'observation_4_b_overlap.parquet'
        valid.to_parquet(out, index=False)
        print(f'\nwrote {out} ({len(valid):,} cells)')

        print(f'\n=== B 指標と A primary outstanding_score の相関 ===')
        print(f'  cmv_mean × A_score: Pearson r={rp_cmv:.4f} (p={pp_cmv:.2e})、Spearman r={rs_cmv:.4f}')
        print(f'  sal_mass × A_score: Pearson r={rp_sal:.4f} (p={pp_sal:.2e})、Spearman r={rs_sal:.4f}')
        print(f'\n=== A 際立ち vs B 際立ち 重なり ===')
        print(f'  A 際立ち cells (outstanding_score>=3): {len(a_cells)}')
        print(f'  B 際立ち cells (B_score>=1): {len(b_cells_any)}')
        print(f'  B 際立ち cells (B_score>=2): {len(b_cells_strong)}')
        print(f'  intersection: {ab_inter}, union: {ab_union}')
        print(f'  Jaccard (A,B>=1): {jaccard_ab:.4f}')
        print(f'  Recall (B>=1 covers A): {recall_b_to_a:.4f}')
        print(f'  Precision (B>=1 is A): {precision_b_to_a:.4f}')

        print(f'\n=== B 際立ち cell の receiver_bin 分布 (post-process 仮想) ===')
        rb_b = valid[valid['B_outstanding_score'] >= 2]
        if len(rb_b) > 0:
            print(rb_b.groupby('receiver_bin').size().sort_values(ascending=False).head(10).to_string())

    print(f'\n=== 規律遵守 ===')
    print(f'  selector 化禁止: B primary 化は post-process 仮想評価のみ、ESDE 内部書き戻し: なし')
    print(f'  書込み: {OUT_MAIN} 配下のみ')

    print(f'\ntotal elapsed: {time.time()-t_start:.1f}s')


if __name__ == '__main__':
    main()
