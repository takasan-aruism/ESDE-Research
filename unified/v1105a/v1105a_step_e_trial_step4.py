#!/usr/bin/env python3
"""v1105a Step E — 試行 Step 4: 段 4-d 機構 + 構造ラベル付与

設計書 v3 §1.1 + §2.5 通り、Step D で計算済の rank-based 確率分布を v1103 機構
(動的計算 100% カバレッジ、Step D 内で実装済) と整合させ、全 60,000 events ×
7 系列に構造ラベルを付与。

構造ラベル (§1.1、Code A Step A 確認要請 11 / Taka 承認):
- candidate_empty: n_candidates_after == 0
- distribution_degenerate: max_prob ≥ 0.999 OR prob_ge_0.999_count > 0
- distribution_valid: max_prob < 0.999 AND entropy > 0
- pipeline_complete: distribution_valid 達成 (candidate_empty / degenerate でない)

入力 (read-only):
  - unified/v1105a/outputs/main/trial_step3_distributions.parquet (Step D 出力、4,800 events × 7 系列)
  - developmental/v112/outputs/main/atom_introduction_events_v108_standard_seed{N}.parquet
    (全 60,000 events、Step D で通過しなかった 55,200 events を candidate_empty として記録)

出力:
  - unified/v1105a/outputs/main/trial_step4_labels.parquet
    (per (seed, event_id, series_id) で構造ラベル + max_prob + entropy + reduction_ratio 等)
  - unified/v1105a/outputs/main/trial_step4_distributions.parquet
    (Step D 出力に構造ラベル列を追加した最終確率分布)
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V112_MAIN = REPO / 'developmental/v112/outputs/main'
V1105A_MAIN = REPO / 'unified/v1105a/outputs/main'

SERIES_IDS = [
    's1_raw_density_raw',
    's2_raw_density_norm',
    's3_qweighted_density_raw',
    's4_qweighted_density_norm',
    's5_const_adjusted_density_raw',
    's6_const_adjusted_density_norm',
    's7_48d_raw_k5',
]
MAX_PROB_THRESH = 0.999


def assign_label(n_after: int, max_prob: float, entropy: float, prob_ge_count: int) -> str:
    """構造ラベル付与 (§1.1)"""
    if n_after == 0:
        return 'candidate_empty'
    if max_prob >= MAX_PROB_THRESH or prob_ge_count > 0:
        return 'distribution_degenerate'
    if max_prob < MAX_PROB_THRESH and entropy > 0:
        return 'distribution_valid'  # = pipeline_complete
    return 'candidate_empty'  # fallback


def main():
    V1105A_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1105a Step E 試行 Step 4 (構造ラベル付与) ===')
    t0 = time.time()

    # Step D 出力読み込み
    dist = pd.read_parquet(V1105A_MAIN / 'trial_step3_distributions.parquet')
    print(f'Step D distributions: {len(dist):,} rows, {dist["event_id"].nunique()} events × 7 系列')

    # 全 60,000 events 取得
    all_events = []
    for sd in range(24):
        p = V112_MAIN / f'atom_introduction_events_v108_standard_seed{sd}.parquet'
        d = pd.read_parquet(p, columns=['event_id', 'atom_id', 'source_cid',
                                          'n_core_member', 'n_core_bin'])
        d['seed'] = sd
        all_events.append(d)
    all_events_df = pd.concat(all_events, ignore_index=True)
    print(f'全 60,000 events: {len(all_events_df):,} rows')

    # per (seed, event_id, series_id) で確率分布計算
    print('per (seed, event_id, series_id) 集計...')

    # Step D を per (seed, event_id, series_id) で集約
    def calc_metrics(grp):
        probs = grp['probability'].values
        n = len(probs)
        max_p = float(probs.max()) if n > 0 else 0.0
        p_nz = probs[probs > 0]
        ent = float(-np.sum(p_nz * np.log(p_nz))) if len(p_nz) > 0 else 0.0
        prob_ge_count = int(np.sum(probs >= MAX_PROB_THRESH))
        top_idx = np.argsort(-probs)
        top1 = grp.iloc[top_idx[0]]['candidate_atom'] if n > 0 else None
        top5 = grp.iloc[top_idx[:5]]['candidate_atom'].tolist()
        input_atom = grp['input_atom'].iloc[0]
        return pd.Series({
            'n_candidates_after': n,
            'max_prob': max_p,
            'entropy': ent,
            'prob_ge_0.999_count': prob_ge_count,
            'top1_atom': top1,
            'top5_atoms': '|'.join(map(str, top5)),
            'input_atom_in_top1': bool(input_atom == top1),
            'input_atom_in_top5': bool(input_atom in top5),
            'b_high_in_top5_count': int(grp.iloc[top_idx[:5]]['b_high'].sum()),
        })

    # input_atom はキーに含めず、calc_metrics 内で参照可能なように残す
    grouped = dist.groupby(['seed', 'event_id', 'series_id'])
    labels_partial = grouped.apply(calc_metrics).reset_index()
    print(f'計算済 events × 7 系列: {len(labels_partial):,} rows')

    # 全 60,000 events × 7 系列 にラベル付与
    print('全 events × 7 系列 構造ラベル付与...')
    label_rows = []
    # 計算済を dict 化
    calc_map = {}
    for _, row in labels_partial.iterrows():
        key = (row['seed'], row['event_id'], row['series_id'])
        calc_map[key] = row

    for _, ev in all_events_df.iterrows():
        for series_id in SERIES_IDS:
            key = (ev['seed'], ev['event_id'], series_id)
            if key in calc_map:
                m = calc_map[key]
                n_after = int(m['n_candidates_after'])
                max_p = float(m['max_prob'])
                ent = float(m['entropy'])
                pge = int(m['prob_ge_0.999_count'])
                label = assign_label(n_after, max_p, ent, pge)
                label_rows.append({
                    'seed': ev['seed'],
                    'event_id': ev['event_id'],
                    'input_atom': ev['atom_id'],
                    'source_cid': int(ev['source_cid']),
                    'n_core_bin': ev['n_core_bin'],
                    'series_id': series_id,
                    'structural_label': label,
                    'n_candidates_after': n_after,
                    'max_prob': max_p,
                    'entropy': ent,
                    'prob_ge_0.999_count': pge,
                    'top1_atom': m['top1_atom'],
                    'top5_atoms': m['top5_atoms'],
                    'input_atom_in_top1': m['input_atom_in_top1'],
                    'input_atom_in_top5': m['input_atom_in_top5'],
                    'b_high_in_top5_count': int(m['b_high_in_top5_count']),
                })
            else:
                # candidate_empty (Step D で通過しなかった)
                label_rows.append({
                    'seed': ev['seed'],
                    'event_id': ev['event_id'],
                    'input_atom': ev['atom_id'],
                    'source_cid': int(ev['source_cid']),
                    'n_core_bin': ev['n_core_bin'],
                    'series_id': series_id,
                    'structural_label': 'candidate_empty',
                    'n_candidates_after': 0,
                    'max_prob': np.nan,
                    'entropy': np.nan,
                    'prob_ge_0.999_count': 0,
                    'top1_atom': None,
                    'top5_atoms': None,
                    'input_atom_in_top1': False,
                    'input_atom_in_top5': False,
                    'b_high_in_top5_count': 0,
                })

    labels_df = pd.DataFrame(label_rows)
    out_labels = V1105A_MAIN / 'trial_step4_labels.parquet'
    labels_df.to_parquet(out_labels, index=False)
    print(f'wrote {out_labels.name} ({len(labels_df):,} rows = 60,000 events × 7 系列)')

    # Step D に構造ラベル列追加 (per-row mapping)
    print('Step D 分布に構造ラベル列追加...')
    label_lookup = labels_df.set_index(['seed', 'event_id', 'series_id'])['structural_label'].to_dict()
    dist['structural_label'] = dist.apply(
        lambda r: label_lookup.get((r['seed'], r['event_id'], r['series_id']), 'unknown'),
        axis=1)
    out_dist = V1105A_MAIN / 'trial_step4_distributions.parquet'
    dist.to_parquet(out_dist, index=False)
    print(f'wrote {out_dist.name} ({len(dist):,} rows、構造ラベル付き分布)')

    print(f'\n=== Step E 完了、elapsed {time.time()-t0:.1f}s ===')

    # --- サマリ ---
    print('\n--- series_id × 構造ラベル 件数 (全 60,000 events) ---')
    pv = labels_df.groupby(['series_id', 'structural_label']).size().unstack(fill_value=0)
    pv['total'] = pv.sum(axis=1)
    pv['valid_rate'] = (pv.get('distribution_valid', 0) / pv['total']).round(4)
    pv['empty_rate'] = (pv.get('candidate_empty', 0) / pv['total']).round(4)
    pv['degenerate_rate'] = (pv.get('distribution_degenerate', 0) / pv['total']).round(4)
    print(pv.to_string())

    print('\n--- n_core_bin × series_id × valid_rate ---')
    pv2 = labels_df[labels_df['structural_label'] == 'distribution_valid'].groupby(
        ['n_core_bin', 'series_id']).size().unstack(fill_value=0)
    totals = labels_df.groupby('n_core_bin').size() / 7  # per bin 単位 events 数
    for series in SERIES_IDS:
        pv2[series] = (pv2[series] / totals).round(4)
    print(pv2.to_string())

    print('\n--- input_atom × series_id × valid_rate (top 5 input_atom) ---')
    s = labels_df.groupby(['input_atom', 'series_id'])['structural_label'].apply(
        lambda x: (x == 'distribution_valid').mean()).unstack(fill_value=0).round(3)
    # 全 series valid_rate 平均で top 5
    s['mean_valid_rate'] = s.mean(axis=1)
    print(s.sort_values('mean_valid_rate', ascending=False).head(5).to_string())


if __name__ == '__main__':
    main()
