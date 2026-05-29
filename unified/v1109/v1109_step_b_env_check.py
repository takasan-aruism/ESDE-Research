#!/usr/bin/env python3
"""v1109 Step B — 環境準備

入力データ確認 + atom universe 確定 + holdout 分割準備 + before baseline 記録。

物理層 frozen 厳密維持: v1106b/v1108a/v1108b は read-only、書込み v1109/ 配下のみ。

入力 (read-only):
- unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet
- unified/v1108a/outputs/main/observation_1_delta_C.parquet (before baseline)
- unified/v1108a/outputs/main/observation_1_asymmetry.parquet (非対称性 baseline)
- developmental/v106/outputs/main/cid_atom_sim_matrix_seed{N}.parquet (Gemini ブレーキ 3)

出力:
- unified/v1109/outputs/main/env_check_summary.parquet
- unified/v1109/outputs/main/atom_universe.parquet
- unified/v1109/outputs/main/event_metadata.parquet
- unified/v1109/outputs/main/before_baseline.parquet
- unified/v1109/outputs/main/holdout_splits.parquet
"""
from __future__ import annotations
import hashlib, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V1108A_MAIN = REPO / 'unified/v1108a/outputs/main'
V1109_MAIN = REPO / 'unified/v1109/outputs/main'

ATOM_TOPK = 10
N_TURN_HALF = 20  # turn holdout: 前半 0-19、後半 20-39


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main():
    V1109_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1109 Step B — 環境準備 ===\n')
    t0 = time.time()

    # (1) リソース存在 + frozen hash
    print('[1] リソース存在 + frozen hash')
    resources = {
        'v1108a self_dialogue': V1108A_MAIN / 'self_dialogue_with_atom_probs.parquet',
        'v1108a delta_C (#L57 baseline)': V1108A_MAIN / 'observation_1_delta_C.parquet',
        'v1108a asymmetry': V1108A_MAIN / 'observation_1_asymmetry.parquet',
    }
    rsrc_rows = []
    for k, p in resources.items():
        ok = p.exists()
        h = sha(p) if ok else None
        size = p.stat().st_size if ok else 0
        print(f'  {k}: {"✓" if ok else "✗"} hash={h}')
        rsrc_rows.append({'resource': k, 'exists': ok, 'size_bytes': size, 'sha256_16': h})

    # v106 cid_atom_sim_matrix per seed (Gemini ブレーキ 3 用)
    n_cid_sim = sum(1 for sd in range(24)
                     if (V106_MAIN / f'cid_atom_sim_matrix_seed{sd}.parquet').exists())
    print(f'  v106 cid_atom_sim_matrix: {n_cid_sim}/24')

    pd.DataFrame(rsrc_rows).to_parquet(V1109_MAIN / 'env_check_summary.parquet', index=False)

    # (2) self_dialogue 読み込み + atom universe 確定
    print('\n[2] atom universe 確定')
    hist = pd.read_parquet(V1108A_MAIN / 'self_dialogue_with_atom_probs.parquet')
    print(f'  self_dialogue rows: {len(hist):,}')
    print(f'  unique events: {hist[["seed","start_cid"]].drop_duplicates().shape[0]}')

    atom_universe = set()
    for i in range(1, ATOM_TOPK + 1):
        atom_universe.update(hist[f'atom_top{i}'].dropna().unique())
    atoms = sorted(atom_universe)
    print(f'  unique atoms in atom_top1..10: {len(atoms)}')

    # atom → idx + category
    atom_df = pd.DataFrame({
        'atom_idx': range(len(atoms)),
        'atom_full': atoms,
        'category': [a.split('.')[0] for a in atoms],
    })
    atom_df.to_parquet(V1109_MAIN / 'atom_universe.parquet', index=False)
    print(f'  category 数: {atom_df["category"].nunique()}')
    print(f'  W 行列サイズ: {len(atoms)} × {len(atoms)} = {len(atoms)**2:,} cells')

    # (3) event メタデータ
    print('\n[3] event メタデータ')
    event_meta = hist.drop_duplicates(['seed', 'start_cid'])[
        ['seed', 'start_cid', 'final_state', 'start_final_state', 'start_fam_bin']
    ].copy()
    event_meta['top1_cat'] = hist.groupby(['seed', 'start_cid'])['atom_top1'].first(
        ).str.split('.').str[0].reset_index(drop=True).values[:len(event_meta)]
    # turn 数
    turn_counts = hist.groupby(['seed', 'start_cid']).size().reset_index(name='n_turn')
    event_meta = event_meta.merge(turn_counts, on=['seed', 'start_cid'])
    event_meta.to_parquet(V1109_MAIN / 'event_metadata.parquet', index=False)
    print(f'  events: {len(event_meta):,}')
    print(f'  final_state 分布: {event_meta["final_state"].value_counts().to_dict()}')

    # (4) before baseline 記録 (v1108a #L57)
    print('\n[4] before baseline 記録 (v1108a #L57)')
    delta_C = pd.read_parquet(V1108A_MAIN / 'observation_1_delta_C.parquet')
    asym = pd.read_parquet(V1108A_MAIN / 'observation_1_asymmetry.parquet')
    baseline_delta_C_max = float(delta_C['delta_C'].abs().max())
    baseline_asymmetry_max = float(asym['asymmetry'].max())
    print(f'  delta_C max abs: {baseline_delta_C_max:.6f}')
    print(f'  asymmetry max: {baseline_asymmetry_max:.6f}')
    print(f'  → 設計書 §10 「max 0.000161」は asymmetry の方、Step B で 2 値を別途記録')

    baseline_df = pd.DataFrame([{
        'source': 'v1108a observation_1',
        'delta_C_max_abs': baseline_delta_C_max,
        'asymmetry_max': baseline_asymmetry_max,
        'asymmetry_mean': float(asym['asymmetry'].mean()),
        'n_pairs': len(delta_C),
        'n_z_gt_2': int((delta_C['z_score'] > 2).sum()),
        'note': 'v1109 重み層適用後の値と比較する before baseline',
    }])
    baseline_df.to_parquet(V1109_MAIN / 'before_baseline.parquet', index=False)

    # (5) holdout 分割準備
    print('\n[5] holdout 分割準備 (3 種)')
    # turn holdout: 前半 0-19、後半 20-39
    print(f'  turn holdout: 前半 turn 0-{N_TURN_HALF-1}、後半 turn {N_TURN_HALF}-39')

    # seed holdout: 0-11 蓄積、12-23 適用
    seeds_train = list(range(12))
    seeds_test = list(range(12, 24))
    print(f'  seed holdout: train seeds {seeds_train[:3]}.. test seeds {seeds_test[:3]}..')

    # category holdout: cluster_0 cat で蓄積、cluster_1 cat で適用 (v1108 cluster ベース)
    # 既知 cluster_0: EXS, FND + v1107c で REL/LOG/VAL/WLD 等
    # cluster_1: BOD/PER/PRP + ACT/NAT/MAT/ELM 等
    # event の top1_cat ベース
    cluster_0_cats = {'EXS', 'FND', 'REL', 'LOG', 'VAL', 'WLD', 'COG', 'COM', 'ABS', 'SPC', 'CHG', 'TIM'}
    cluster_1_cats = {'BOD', 'PER', 'PRP', 'BEI', 'NAT', 'MAT', 'ACT', 'ELM', 'ECO', 'EMO', 'SOC', 'STA'}

    holdout_rows = []
    for _, ev in event_meta.iterrows():
        top1_cat = ev['top1_cat'] if not pd.isna(ev['top1_cat']) else None
        cat_split = ('cluster_0' if top1_cat in cluster_0_cats
                      else 'cluster_1' if top1_cat in cluster_1_cats else 'other')
        seed_split = 'train' if int(ev['seed']) < 12 else 'test'
        holdout_rows.append({
            'seed': int(ev['seed']),
            'start_cid': int(ev['start_cid']),
            'top1_cat': top1_cat,
            'seed_split': seed_split,
            'cat_split': cat_split,
        })
    holdout_df = pd.DataFrame(holdout_rows)
    holdout_df.to_parquet(V1109_MAIN / 'holdout_splits.parquet', index=False)
    print(f'  seed split: train {(holdout_df["seed_split"]=="train").sum()}, '
          f'test {(holdout_df["seed_split"]=="test").sum()}')
    print(f'  cat split: cluster_0 {(holdout_df["cat_split"]=="cluster_0").sum()}, '
          f'cluster_1 {(holdout_df["cat_split"]=="cluster_1").sum()}, '
          f'other {(holdout_df["cat_split"]=="other").sum()}')

    print(f'\n=== Step B 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
