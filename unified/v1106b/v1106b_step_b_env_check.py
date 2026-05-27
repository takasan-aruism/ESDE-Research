#!/usr/bin/env python3
"""v1106b Step B — 環境準備 + 開始 CID 選定

目的:
1. リソース load 確認 (v1103/v106/mapper_output/v105/v1106a)
2. CID 物理量集約 (24 seeds × per_subject)
3. final_state × familiarity bin で 8 bin 分類
4. 開始 CID 選定 (各 seed 40 CID 目標、960 CID 全体)
5. 不足時の代替案検討

Bin 構成:
- hosted × familiarity low/mid/high = 3 bin × 5 CID = 15 CID
- ghost × familiarity low/mid/high = 3 bin × 5 CID = 15 CID
- reaped × familiarity low/mid = 2 bin × 5 CID = 10 CID
- 合計 8 bin × 5 = 40 CID/seed × 24 seeds = 960 CID 目標

familiarity bin 境界 (Code A 提案):
- low: familiarity < 10
- mid: 10 <= familiarity < 50
- high: familiarity >= 50

入力 (read-only):
- developmental/v105/diag_v105_main/subjects/per_subject_seed{N}.csv
- developmental/v106/outputs/main/cid_structure_profile_seed{N}.csv

出力:
- unified/v1106b/outputs/main/env_check_cid_props.parquet (全 CID 物理量集約)
- unified/v1106b/outputs/main/env_check_bin_counts.parquet (seed × bin 別 CID 数)
- unified/v1106b/outputs/main/env_check_selected_cids.parquet (選定 CID リスト)
- unified/v1106b/v1106b_step_b_env_check_summary.md (報告書)
"""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V105_SUB = REPO / 'developmental/v105/diag_v105_main/subjects'
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V1103_MAIN = REPO / 'unified/v1103/outputs/main'
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'
MAPPER_DIR = REPO / 'language/lexicon/data/mapper_output'
V1106B_MAIN = REPO / 'unified/v1106b/outputs/main'

FAM_LOW_THRESH = 10.0
FAM_HIGH_THRESH = 50.0

# 案 E 採用 (Taka 2026-05-28 承認): bin 再設計
# - hosted/ghost low は ESDE 構造上希少のため除外
# - reaped high を追加 (per_seed 平均 65 個で余裕)
# - ghost は per_seed 3 CID に減 (CID 数限界)
SELECT_BINS_E = [
    ('hosted', 'mid', 5),
    ('hosted', 'high', 5),
    ('ghost', 'mid', 3),   # ghost mid は per_seed 平均 2-3 で 3 CID 確保
    ('ghost', 'high', 5),
    ('reaped', 'low', 5),
    ('reaped', 'mid', 5),
    ('reaped', 'high', 5),  # 新規追加
]
TARGET_CIDS_PER_SEED = sum(n for _, _, n in SELECT_BINS_E)  # 33
TARGET_TOTAL = 24 * TARGET_CIDS_PER_SEED  # 792


def main():
    V1106B_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106b Step B — 環境準備 + 開始 CID 選定 ===\n')
    t0 = time.time()

    # (1) リソース存在確認
    print('[1] リソース存在確認')
    resources = {
        'v1103 atom_centroids_48d_raw': V1103_MAIN / 'atom_centroids_48d_raw.parquet',
        'v106 axes_metadata': V106_MAIN / 'axes_metadata.json',
        'v1106a verification_a': V1106A_MAIN / 'verification_a_cid_word_alignment.parquet',
    }
    for k, p in resources.items():
        print(f'  {k}: {"存在" if p.exists() else "不在"}')
        assert p.exists(), f'{k} not found'

    # per_seed リソース
    print('\n  per-seed リソース:')
    missing_seeds = {'per_subject': [], 'cid_structure_profile': [],
                      'cid_atom_sim_matrix': []}
    for sd in range(24):
        if not (V105_SUB / f'per_subject_seed{sd}.csv').exists():
            missing_seeds['per_subject'].append(sd)
        if not (V106_MAIN / f'cid_structure_profile_seed{sd}.csv').exists():
            missing_seeds['cid_structure_profile'].append(sd)
        if not (V106_MAIN / f'cid_atom_sim_matrix_seed{sd}.parquet').exists():
            missing_seeds['cid_atom_sim_matrix'].append(sd)
    for k, v in missing_seeds.items():
        if v:
            print(f'    {k}: 不在 seeds = {v}')
        else:
            print(f'    {k}: 全 24 seeds 存在')

    # mapper_output
    n_mapper = len(list(MAPPER_DIR.glob('*_a1.jsonl')))
    print(f'  mapper_output: {n_mapper} files (期待 325)')

    # (2) CID 物理量集約
    print('\n[2] CID 物理量集約 (24 seeds × per_subject)')
    rows = []
    for sd in range(24):
        fp = V105_SUB / f'per_subject_seed{sd}.csv'
        if not fp.exists():
            continue
        df = pd.read_csv(fp, usecols=['seed', 'cognitive_id', 'final_state',
                                        'last_familiarity_max', 'n_alphas_currently',
                                        'current_stability', 'current_social'])
        df = df.rename(columns={'cognitive_id': 'cid'})
        rows.append(df)
    cid_props = pd.concat(rows, ignore_index=True)
    print(f'  total CID rows: {len(cid_props):,}')

    # cid_structure_profile に存在する CID のみ採用 (CID 48d vec が必要)
    valid_cids = set()
    for sd in range(24):
        fp = V106_MAIN / f'cid_structure_profile_seed{sd}.csv'
        if not fp.exists():
            continue
        df = pd.read_csv(fp, usecols=['seed', 'cid'])
        for _, r in df.iterrows():
            valid_cids.add((int(r['seed']), int(r['cid'])))
    cid_props['has_48d_vec'] = cid_props.apply(
        lambda r: (int(r['seed']), int(r['cid'])) in valid_cids, axis=1)
    cid_props = cid_props[cid_props['has_48d_vec']].copy()
    print(f'  with 48d vec: {len(cid_props):,}')

    # familiarity bin
    cid_props['fam_bin'] = pd.cut(
        cid_props['last_familiarity_max'],
        bins=[-np.inf, FAM_LOW_THRESH, FAM_HIGH_THRESH, np.inf],
        labels=['low', 'mid', 'high'])
    cid_props['final_state'] = cid_props['final_state'].astype(str)
    out1 = V1106B_MAIN / 'env_check_cid_props.parquet'
    cid_props.to_parquet(out1, index=False)
    print(f'  wrote {out1.name}')

    # (3) seed × bin 別 CID 数集計
    print('\n[3] seed × bin 別 CID 数集計')
    bin_counts = cid_props.groupby(['seed', 'final_state', 'fam_bin'],
                                     observed=True).size().reset_index(name='n_cid')
    pivot = bin_counts.pivot_table(index=['seed'],
                                    columns=['final_state', 'fam_bin'],
                                    values='n_cid', fill_value=0, observed=True)
    print('\n  各 seed の (final_state × fam_bin) CID 数 (最初 5 seed):')
    print(pivot.head(5).to_string())
    print(f'\n  最小値 (seed × bin で最少): {pivot.min().min()}')
    print(f'  bin 全体平均: {pivot.mean().mean():.1f}')

    out2 = V1106B_MAIN / 'env_check_bin_counts.parquet'
    pivot.to_parquet(out2)
    print(f'\n  wrote {out2.name}')

    # (4) 開始 CID 選定 (案 E、7 bin × per_bin CID 数指定 = 33 CID/seed)
    print(f'\n[4] 開始 CID 選定 (案 E、各 seed {TARGET_CIDS_PER_SEED} CID 目標)')
    print(f'  対象 bin (7 bin、per_bin CID 数指定):')
    for fs, fb, n in SELECT_BINS_E:
        print(f'    ({fs}, {fb}): {n} CID')

    selected = []
    underfill = []  # (seed, bin, available, target)
    np.random.seed(42)  # 再現性

    for sd in range(24):
        sub = cid_props[cid_props['seed'] == sd]
        for fs, fb, n_target in SELECT_BINS_E:
            cands = sub[(sub['final_state'] == fs) & (sub['fam_bin'] == fb)]
            if len(cands) >= n_target:
                chosen = cands.sample(n=n_target, random_state=42)
            else:
                chosen = cands  # 全部採用
                underfill.append({
                    'seed': sd, 'final_state': fs, 'fam_bin': fb,
                    'available': len(cands), 'target': n_target,
                })
            for _, r in chosen.iterrows():
                selected.append({
                    'seed': int(r['seed']), 'cid': int(r['cid']),
                    'final_state': fs, 'fam_bin': fb,
                    'last_familiarity_max': float(r['last_familiarity_max']) if not pd.isna(r['last_familiarity_max']) else None,
                    'n_alphas_currently': float(r['n_alphas_currently']) if not pd.isna(r['n_alphas_currently']) else None,
                })

    sel_df = pd.DataFrame(selected)
    print(f'\n  選定 CID 数 (全体): {len(sel_df):,} (目標 {TARGET_TOTAL})')

    # seed 別 CID 数
    seed_counts = sel_df.groupby('seed').size().reset_index(name='n_cid')
    print(f'  seed 別 CID 数:')
    print(f'    min={seed_counts["n_cid"].min()}, max={seed_counts["n_cid"].max()}, '
          f'mean={seed_counts["n_cid"].mean():.1f}')

    # 不足 bin
    if underfill:
        print(f'\n  不足 bin: {len(underfill)} 件')
        underfill_df = pd.DataFrame(underfill)
        print(underfill_df.head(15).to_string(index=False))
    else:
        print(f'\n  不足 bin: なし、全 24 seeds × 8 bin で {N_PER_BIN} CID 確保')

    out3 = V1106B_MAIN / 'env_check_selected_cids.parquet'
    sel_df.to_parquet(out3, index=False)
    print(f'\n  wrote {out3.name}')

    if underfill:
        out4 = V1106B_MAIN / 'env_check_underfill.parquet'
        pd.DataFrame(underfill).to_parquet(out4, index=False)
        print(f'  wrote {out4.name}')

    # (5) 結果サマリ + 代替案 (不足時)
    print(f'\n=== Step B 完了、elapsed {time.time()-t0:.1f}s ===\n')

    summary = {
        'total_selected': len(sel_df),
        'target_total': TARGET_TOTAL,
        'shortfall': TARGET_TOTAL - len(sel_df),
        'shortfall_rate': (TARGET_TOTAL - len(sel_df)) / TARGET_TOTAL,
        'n_underfill_bins': len(underfill),
        'n_total_bins': 24 * 8,
    }

    print(f'--- 選定 CID 数集計 ---')
    print(f'  目標: {TARGET_TOTAL}')
    print(f'  実際: {len(sel_df)}')
    print(f'  不足: {TARGET_TOTAL - len(sel_df)} ({summary["shortfall_rate"]*100:.1f}%)')
    print(f'  不足 bin 数: {len(underfill)} / {24*8} bins')

    # final_state × fam_bin 別の選定数
    print(f'\n--- 選定 CID の final_state × fam_bin 分布 ---')
    fs_fb_counts = sel_df.groupby(['final_state', 'fam_bin'], observed=True).size().reset_index(name='n_cid')
    print(fs_fb_counts.to_string(index=False))

    # 代替案 (不足 ≥ 10% で提示)
    if summary['shortfall_rate'] >= 0.1:
        print(f'\n--- 代替案 (不足 {summary["shortfall_rate"]*100:.1f}%) ---')
        print(f'  案 A: reaped high を採用 bin に追加 (8 bin → 9 bin)')
        # reaped high の CID 数集計
        reaped_high = cid_props[(cid_props['final_state']=='reaped') & (cid_props['fam_bin']=='high')]
        print(f'    reaped high 全体 CID 数: {len(reaped_high)} (per_seed 平均 {len(reaped_high)/24:.1f})')

        print(f'  案 B: 各 bin の per_seed CID 数を増やす (5 → 7 / 8 等)')

        print(f'  案 C: 不足 bin の不足分を他 bin で補填 (例: hosted high 不足 → ghost high で補填)')

        print(f'  案 D: 目標を 960 から実数 {len(sel_df)} に変更 (smoke で問題なければ妥当)')

    return summary


if __name__ == '__main__':
    main()
