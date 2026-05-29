#!/usr/bin/env python3
"""v1108a Step E — 観察 3: 時間軸シャッフル baseline 比較 (基準 A)

Step C ですでに 10 回シャッフルしている。本 Step では:
- 観察 1 ΔC_ij の z スコア集計
- 上位 ΔC ペアが shuffle でも同様に出るか確認
- 観察 2 ρ_FH を shuffle baseline と比較
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import pearsonr

REPO = Path('/home/takasan/esde/ESDE-Research')
V1108A_MAIN = REPO / 'unified/v1108a/outputs/main'

N_SHUFFLE = 10
RNG_SEED = 42


def main():
    print('=== v1108a Step E — 観察 3: 時間軸シャッフル baseline 比較 ===\n')
    t0 = time.time()

    # (1) Step C ΔC_ij z スコア分布
    print('[1] Step C ΔC_ij z スコア分布')
    delta = pd.read_parquet(V1108A_MAIN / 'observation_1_delta_C.parquet')
    z_significant = (delta['z_score'] > 2).sum()
    z_high = (delta['z_score'] > 5).sum()
    print(f'  全ペア: {len(delta):,}, z>2: {z_significant:,} ({z_significant/len(delta)*100:.2f}%)')
    print(f'  z>5: {z_high:,}, z>10: {(delta["z_score"]>10).sum()}, z>50: {(delta["z_score"]>50).sum()}')

    # (2) 観察 2 ρ_FH shuffle baseline
    print('\n[2] ρ_FH shuffle baseline 比較')
    pair_df = pd.read_parquet(V1108A_MAIN / 'observation_2_rho_FH.parquet')
    # 真の ρ
    rho_true, p_true = pearsonr(pair_df['delta_F'].values, pair_df['delta_H'].values)
    # ΔF or ΔH のいずれかをシャッフル
    rng = np.random.default_rng(RNG_SEED)
    shuf_rhos = []
    for it in range(N_SHUFFLE):
        df_shuf = pair_df.copy()
        df_shuf['delta_H_shuf'] = rng.permutation(df_shuf['delta_H'].values)
        rho_s, _ = pearsonr(df_shuf['delta_F'].values, df_shuf['delta_H_shuf'].values)
        shuf_rhos.append(rho_s)
    shuf_arr = np.array(shuf_rhos)
    z_rho = (rho_true - shuf_arr.mean()) / shuf_arr.std() if shuf_arr.std() > 0 else 0
    print(f'  真 ρ_FH: {rho_true:.4f} (p={p_true:.2e})')
    print(f'  shuffle ρ_FH: mean={shuf_arr.mean():.4f}, std={shuf_arr.std():.4f}')
    print(f'  z スコア (真 vs shuffle): {z_rho:.2f}')

    # (3) 構造ラベル判定 (基準 A)
    asymmetric_pass = (
        z_significant / len(delta) > 0.05  # 5% 以上が z>2
        and abs(z_rho) > 2
    )
    label = 'temporal_asymmetric_binding_observed' if asymmetric_pass else 'temporal_symmetric_only'

    sum_df = pd.DataFrame([{
        'n_pairs_total': len(delta),
        'n_z_gt_2': int(z_significant),
        'pct_z_gt_2': float(z_significant / len(delta)),
        'rho_FH_true': float(rho_true),
        'rho_FH_shuf_mean': float(shuf_arr.mean()),
        'rho_FH_shuf_std': float(shuf_arr.std()),
        'rho_FH_z_vs_shuffle': float(z_rho),
        'criterion_a_pass': bool(asymmetric_pass),
        'structural_label': label,
        'elapsed_sec': round(time.time() - t0, 2),
    }])
    sum_df.to_parquet(V1108A_MAIN / 'observation_3_summary.parquet', index=False)

    print(f'\n--- 基準 A 判定 ---')
    print(f'  pct z>2: {z_significant/len(delta)*100:.2f}% (threshold 5%)')
    print(f'  rho_FH vs shuffle z: {z_rho:.2f} (threshold 2)')
    print(f'  基準 A PASS: {asymmetric_pass}')
    print(f'  構造ラベル: {label}')

    print(f'\n=== Step E 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
