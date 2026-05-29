#!/usr/bin/env python3
"""v1108a Step D — 観察 2: ρ_FH Familiarity-Entropy 連動曲率

各 event × turn ペアで:
  ΔF_t = F_{t+1} - F_t
  ΔH_t = H(P_{t+1}) - H(P_t)
  H(P_t) = -Σ P_t(A_i) log P_t(A_i)  (top-10 で近似、確率正規化)
ρ_FH = Corr(ΔF, ΔH) — 全 event 集約 + event 別 + final_state 別

入力:
- unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet

出力:
- unified/v1108a/outputs/main/observation_2_rho_FH.parquet
- unified/v1108a/outputs/main/observation_2_summary.parquet
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import pearsonr

REPO = Path('/home/takasan/esde/ESDE-Research')
V1108A_MAIN = REPO / 'unified/v1108a/outputs/main'

ATOM_TOPK = 10


def entropy(probs):
    p = probs[probs > 0]
    if len(p) == 0:
        return 0.0
    p = p / p.sum()  # 正規化
    return float(-np.sum(p * np.log(p)))


def main():
    print('=== v1108a Step D — 観察 2: ρ_FH Familiarity-Entropy 連動 ===\n')
    t0 = time.time()

    hist = pd.read_parquet(V1108A_MAIN / 'self_dialogue_with_atom_probs.parquet')
    prob_cols = [f'prob_top{i+1}' for i in range(ATOM_TOPK)]
    print(f'  rows: {len(hist):,}')

    # 各 turn でエントロピー計算
    print('\n[1] 各 turn のエントロピー H(P_t) 計算')
    probs_arr = hist[prob_cols].values.astype(np.float64)
    # 正規化 (top-10 合計を 1 にする)
    row_sums = probs_arr.sum(axis=1, keepdims=True)
    probs_norm = np.where(row_sums > 0, probs_arr / row_sums, 0)
    # entropy per row
    eps = 1e-12
    log_p = np.where(probs_norm > 0, np.log(probs_norm + eps), 0)
    ent = -np.sum(probs_norm * log_p, axis=1)
    hist['entropy'] = ent
    print(f'  entropy mean={ent.mean():.4f}, std={ent.std():.4f}')

    # ΔF, ΔH per event
    print('\n[2] event × turn pair で ΔF, ΔH 計算')
    pair_rows = []
    for (sd, sc), grp in hist.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn').reset_index(drop=True)
        fam = grp_sorted['last_familiarity_max'].values
        ent = grp_sorted['entropy'].values
        final_state = grp_sorted['final_state'].iloc[0]
        for t in range(len(grp_sorted) - 1):
            f_t = fam[t]; f_tp = fam[t+1]
            e_t = ent[t]; e_tp = ent[t+1]
            if f_t is None or f_tp is None or pd.isna(f_t) or pd.isna(f_tp):
                continue
            pair_rows.append({
                'seed': sd, 'start_cid': sc, 'turn': t,
                'final_state': final_state,
                'F_t': float(f_t), 'F_tp1': float(f_tp),
                'H_t': float(e_t), 'H_tp1': float(e_tp),
                'delta_F': float(f_tp - f_t),
                'delta_H': float(e_tp - e_t),
            })
    pair_df = pd.DataFrame(pair_rows)
    print(f'  pairs: {len(pair_df):,}')

    # (3) 全体 ρ_FH
    print('\n[3] 全体 ρ_FH 計算')
    rho_overall, p_overall = pearsonr(pair_df['delta_F'].values, pair_df['delta_H'].values)
    print(f'  ρ_FH overall: {rho_overall:.4f} (p={p_overall:.2e})')

    # final_state 別 ρ_FH
    print('\n[4] final_state 別 ρ_FH')
    fs_rhos = []
    for fs in pair_df['final_state'].unique():
        sub = pair_df[pair_df['final_state'] == fs]
        if len(sub) < 10:
            continue
        rho, p = pearsonr(sub['delta_F'].values, sub['delta_H'].values)
        fs_rhos.append({
            'final_state': fs,
            'n_pairs': len(sub),
            'rho_FH': float(rho),
            'p_value': float(p),
        })
    fs_df = pd.DataFrame(fs_rhos)
    print(fs_df.round(4).to_string(index=False))

    # event 別 ρ_FH (少なくとも 5 pair 以上の event)
    print('\n[5] event 別 ρ_FH (5+ pair の event のみ)')
    event_rhos = []
    for (sd, sc), grp in pair_df.groupby(['seed', 'start_cid']):
        if len(grp) < 5:
            continue
        try:
            rho, p = pearsonr(grp['delta_F'].values, grp['delta_H'].values)
            if not np.isnan(rho):
                event_rhos.append({
                    'seed': sd, 'start_cid': sc,
                    'n_pairs': len(grp),
                    'rho_FH': float(rho),
                    'final_state': grp['final_state'].iloc[0],
                })
        except Exception:
            continue
    event_rho_df = pd.DataFrame(event_rhos)
    print(f'  events with valid ρ: {len(event_rho_df):,}')
    if len(event_rho_df) > 0:
        rho_vals = event_rho_df['rho_FH'].values
        print(f'  ρ_FH per event: mean={rho_vals.mean():.4f}, '
              f'median={np.median(rho_vals):.4f}, std={rho_vals.std():.4f}')
        print(f'  ρ > 0: {(rho_vals > 0).sum()}, ρ < 0: {(rho_vals < 0).sum()}')

    # 出力
    pair_df.to_parquet(V1108A_MAIN / 'observation_2_rho_FH.parquet', index=False)
    event_rho_df.to_parquet(V1108A_MAIN / 'observation_2_event_rhos.parquet', index=False)

    # 構造ラベル判定
    significant = abs(rho_overall) > 0.05 and p_overall < 0.001
    label = 'familiarity_entropy_coupled' if significant else 'familiarity_entropy_independent'

    sum_df = pd.DataFrame([{
        'n_pairs_total': len(pair_df),
        'rho_FH_overall': float(rho_overall),
        'p_value_overall': float(p_overall),
        'rho_FH_significant': bool(significant),
        'structural_label': label,
        'n_events_with_valid_rho': len(event_rho_df),
        'event_rho_mean': float(event_rho_df['rho_FH'].mean()) if len(event_rho_df) > 0 else 0.0,
        'event_rho_positive_rate': float((event_rho_df['rho_FH'] > 0).mean()) if len(event_rho_df) > 0 else 0.0,
        'elapsed_sec': round(time.time() - t0, 2),
    }])
    sum_df.to_parquet(V1108A_MAIN / 'observation_2_summary.parquet', index=False)

    print(f'\n--- 構造ラベル判定 ---')
    print(f'  ρ_FH overall: {rho_overall:.4f} (p={p_overall:.2e})')
    print(f'  significant (|ρ| > 0.05 AND p < 0.001): {significant}')
    print(f'  構造ラベル: {label}')

    print(f'\n=== Step D 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
