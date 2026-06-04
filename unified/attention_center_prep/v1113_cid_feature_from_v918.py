#!/usr/bin/env python3
"""v1113 CID 特性ベクトル共鳴測定 — 案 B 実装 (過去 v918 main run output 流用)

経緯:
- 案 A (v1113_cid_feature_resonance.py) で V82Engine.cog を仮定して FAIL
- 実際の CID layer は v918_memory_readout.run() 内で SubjectLayer() ローカル変数として並走
- Taka 判断: B で様子見、A を次に
- 案 B = 過去 v918 main run output (seed 0-23 全 24 seed) を読み込んで CID 特性化

過去資産:
- primitive/v918/diag_v918_main/subjects/per_subject_seed{0-23}.csv (CID 単位)
- developmental/v107/outputs/main/source_events_seed{0-23}.parquet (event 単位、集約)

特性ベクトル設計 (15 次元、node ID free、per_subject + source_events 結合):
- per_subject から: original_phase_sig (cos/sin 展開)、last_n_partners、last_familiarity_max、
  last_attention_size、ttl_bonus、current_social、current_stability、current_spread、
  current_familiarity
- source_events から (cid 別に最終 event 集約): n_core_member、v14_q0、C_at_window_end、
  Q_remaining_at_window_end、lifespan_so_far

seed 割り当て (過去 v918 main run の seed 番号は独立):
- ATOM_SEEDS = [0, 1, 2]
- OTHER_SEED_FIXED = 23
- NULL_OTHER_SEEDS = [18, 19, 20, 21, 22]

不変規律:
- node ID 完全排他 (cognitive_id は集合間で意味なし、特性ベクトル化には使うが ID は渡さない)
- state なし観察 (parquet read-only)
- 自然進化 (過去 main run = 注入なし、規律準拠)
- factor なし、大小のみ
- 報告言葉縛り (crown 禁止)

測定器点検 (§3.1-§3.4):
- §3.1 恒等性 sim(v, v) = 1.0
- §3.2 揺らした自己 > 乱数 (kernel 機能)
- §3.3 実機 CID 自己 > 乱数 (atom_seed=0 features で)
- §3.4 shuffle 構造破壊で sim 低下
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'
import sys, json, time, math
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
STAGE5 = REPO / 'unified/attention_center_prep'
OUT_DIR = STAGE5 / 'run_v1113'
OUT_DIR.mkdir(parents=True, exist_ok=True)

PER_SUBJECT_DIR = REPO / 'primitive/v918/diag_v918_main/subjects'
SOURCE_EVENTS_DIR = REPO / 'developmental/v107/outputs/main'

ATOM_SEEDS = [0, 1, 2]
OTHER_SEED_FIXED = 23
NULL_OTHER_SEEDS = [18, 19, 20, 21, 22]
ALL_SEEDS_USED = ATOM_SEEDS + [OTHER_SEED_FIXED] + NULL_OTHER_SEEDS

FEATURE_KEYS = [
    'phase_sig_cos',          # original_phase_sig → cos
    'phase_sig_sin',          # original_phase_sig → sin
    'n_core',                 # source_events: n_core_member (mean over events per cid)
    'lifespan',               # source_events: max(lifespan_so_far) per cid
    'Q0',                     # source_events: max(v14_q0) per cid (= 生誕時値)
    'Q_remaining',            # source_events: last Q_remaining_at_window_end per cid
    'C',                      # source_events: last C_at_window_end per cid
    'last_familiarity_max',   # per_subject: last_familiarity_max
    'last_n_partners',        # per_subject: last_n_partners
    'last_attention_size',    # per_subject: last_attention_size
    'ttl_bonus',              # per_subject: ttl_bonus
    'current_social',         # per_subject
    'current_stability',      # per_subject
    'current_spread',         # per_subject
    'current_familiarity',    # per_subject
]


def load_features_for_seed(seed, system_label):
    """seed の per_subject CSV + source_events parquet を読み込んで CID 単位特性ベクトル化

    Returns:
        list of dict, 各 dict は {cid, system, **FEATURE_KEYS}
    """
    ps_path = PER_SUBJECT_DIR / f'per_subject_seed{seed}.csv'
    se_path = SOURCE_EVENTS_DIR / f'source_events_seed{seed}.parquet'

    if not ps_path.exists():
        raise FileNotFoundError(f'per_subject CSV not found: {ps_path}')
    if not se_path.exists():
        raise FileNotFoundError(f'source_events parquet not found: {se_path}')

    ps_df = pd.read_csv(ps_path)
    se_df = pd.read_parquet(se_path)

    # source_events を cid 別に集約 (CID 単位特性)
    se_agg = se_df.groupby('source_cid').agg(
        n_core=('n_core_member', 'mean'),
        lifespan=('lifespan_so_far', 'max'),
        Q0=('v14_q0', 'max'),
        Q_remaining=('Q_remaining_at_window_end', 'last'),
        C=('C_at_window_end', 'last'),
    ).reset_index().rename(columns={'source_cid': 'cognitive_id'})

    # per_subject と source_events を cognitive_id で merge (inner)
    merged = ps_df.merge(se_agg, on='cognitive_id', how='inner')

    # phase_sig を cos/sin 展開
    phase_sig = merged['original_phase_sig'].fillna(0.0).astype(float).values
    merged['phase_sig_cos'] = np.cos(phase_sig)
    merged['phase_sig_sin'] = np.sin(phase_sig)

    # 欠損値を 0 で埋める
    for col in FEATURE_KEYS:
        if col not in merged.columns:
            merged[col] = 0.0
        merged[col] = merged[col].fillna(0.0).astype(float)

    features = []
    for _, row in merged.iterrows():
        feat = {
            'cid': int(row['cognitive_id']),
            'system': system_label,
            'seed': seed,
        }
        for k in FEATURE_KEYS:
            feat[k] = float(row[k])
        features.append(feat)
    return features


def features_to_matrix(features_list):
    if len(features_list) == 0:
        return np.zeros((0, len(FEATURE_KEYS)), dtype=float)
    return np.array([[f[k] for k in FEATURE_KEYS] for f in features_list], dtype=float)


def z_score_normalize(matrix):
    if matrix.shape[0] == 0:
        return matrix, np.zeros(matrix.shape[1]), np.ones(matrix.shape[1])
    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0)
    std_safe = np.where(std < 1e-9, 1.0, std)
    return (matrix - mean) / std_safe, mean, std_safe


def cosine_sim_matrix(A, B):
    if A.shape[0] == 0 or B.shape[0] == 0:
        return np.zeros((A.shape[0], B.shape[0]))
    A_norm = np.linalg.norm(A, axis=1, keepdims=True)
    B_norm = np.linalg.norm(B, axis=1, keepdims=True)
    A_norm_safe = np.where(A_norm < 1e-9, 1.0, A_norm)
    B_norm_safe = np.where(B_norm < 1e-9, 1.0, B_norm)
    return (A / A_norm_safe) @ (B / B_norm_safe).T


# === 測定器点検 ===

def precheck_identity():
    print('[precheck §3.1] 恒等性 sim(v, v) = 1.0 ...')
    rng = np.random.RandomState(42)
    v = rng.normal(0, 1, size=len(FEATURE_KEYS))
    sim = cosine_sim_matrix(v.reshape(1, -1), v.reshape(1, -1))[0, 0]
    if abs(sim - 1.0) > 1e-9:
        raise RuntimeError(f'§3.1 FAIL: sim(v, v) = {sim} != 1.0')
    print(f'  sim(v, v) = {sim:.6f} OK')


def precheck_kernel_function():
    print('[precheck §3.2] kernel 機能 (揺らした自己 > 乱数)...')
    rng = np.random.RandomState(42)
    n_trials = 10
    n_dim = len(FEATURE_KEYS)
    failed = 0
    for _ in range(n_trials):
        v = rng.normal(0, 1, size=n_dim)
        v_pert = v + rng.normal(0, 0.05, size=n_dim)
        v_rand = rng.normal(0, 1, size=n_dim)
        sim_pert = cosine_sim_matrix(v.reshape(1, -1), v_pert.reshape(1, -1))[0, 0]
        sim_rand = cosine_sim_matrix(v.reshape(1, -1), v_rand.reshape(1, -1))[0, 0]
        if not (sim_pert > sim_rand):
            failed += 1
    if failed > n_trials // 3:
        raise RuntimeError(f'§3.2 FAIL: {failed}/{n_trials} で 揺らした自己 ≤ 乱数')
    print(f'  揺らした自己 > 乱数: {n_trials - failed}/{n_trials} OK')


def precheck_real_self_vs_random(features):
    print('[precheck §3.3] 実機 CID 自己 > 乱数...')
    if len(features) == 0:
        raise RuntimeError('§3.3 FAIL: features 0 個')
    matrix = features_to_matrix(features)
    matrix_z, _, _ = z_score_normalize(matrix)
    rng = np.random.RandomState(999)
    n_dim = matrix_z.shape[1]
    failed = 0
    for i in range(len(features)):
        v = matrix_z[i:i+1]
        v_random = rng.normal(0, 1, size=(1, n_dim))
        sim_self = cosine_sim_matrix(v, v)[0, 0]
        sim_rand = cosine_sim_matrix(v, v_random)[0, 0]
        if not (sim_self > sim_rand):
            failed += 1
    if failed > 0:
        raise RuntimeError(f'§3.3 FAIL: {failed}/{len(features)} CID で 自己 ≤ 乱数')
    print(f'  全 {len(features)} CID で 自己 > 乱数 OK')


def precheck_shuffle_structure(features):
    print('[precheck §3.4] shuffle 構造破壊で sim 低下...')
    if len(features) < 3:
        print(f'  features {len(features)} 個、scaffold check skip')
        return
    matrix = features_to_matrix(features)
    matrix_z, _, _ = z_score_normalize(matrix)
    sim_self = cosine_sim_matrix(matrix_z, matrix_z)
    np.fill_diagonal(sim_self, np.nan)
    sim_self_mean = float(np.nanmean(sim_self))

    rng = np.random.RandomState(7777)
    shuffled = matrix_z.copy()
    for col in range(shuffled.shape[1]):
        shuffled[:, col] = shuffled[rng.permutation(shuffled.shape[0]), col]
    sim_shuf = cosine_sim_matrix(matrix_z, shuffled)
    sim_shuf_mean = float(sim_shuf.mean())

    print(f'  自己 mean sim = {sim_self_mean:.4f}, shuffled mean sim = {sim_shuf_mean:.4f}')
    if sim_self_mean <= sim_shuf_mean:
        raise RuntimeError(
            f'§3.4 FAIL: 自己 sim ({sim_self_mean:.4f}) ≤ shuffled sim ({sim_shuf_mean:.4f})'
        )
    print(f'  自己 > shuffled OK')


def main():
    print('=== v1113 案 B 実装 — 過去 v918 main run output 流用 ===\n')
    print(f'  ATOM_SEEDS={ATOM_SEEDS}')
    print(f'  OTHER_SEED_FIXED={OTHER_SEED_FIXED} (real)')
    print(f'  NULL_OTHER_SEEDS={NULL_OTHER_SEEDS}')
    print(f'  特性ベクトル次元: {len(FEATURE_KEYS)} ({FEATURE_KEYS})')
    print(f'  入力: per_subject_seed{{N}}.csv + source_events_seed{{N}}.parquet\n')

    # === 前半 precheck (ダミー、即時) ===
    print('=' * 60)
    print('測定器点検 前半 (ダミー、即時)')
    print('=' * 60)
    precheck_identity()
    precheck_kernel_function()
    print('前半 precheck PASS\n')

    # === 全 system の features を読み込み ===
    print('=' * 60)
    print('特性読み込み (過去 main run output)')
    print('=' * 60)
    all_features = []
    system_label_map = {}
    for sa in ATOM_SEEDS:
        label = f'atom_{sa}'
        feats = load_features_for_seed(sa, label)
        all_features.extend(feats)
        system_label_map[label] = sa
        print(f'  {label}: {len(feats)} CIDs')
    label = 'real_other'
    feats = load_features_for_seed(OTHER_SEED_FIXED, label)
    all_features.extend(feats)
    system_label_map[label] = OTHER_SEED_FIXED
    print(f'  {label} (seed={OTHER_SEED_FIXED}): {len(feats)} CIDs')
    for ns in NULL_OTHER_SEEDS:
        label = f'null_other_{ns}'
        feats = load_features_for_seed(ns, label)
        all_features.extend(feats)
        system_label_map[label] = ns
        print(f'  {label}: {len(feats)} CIDs')
    print(f'\n  全 {len(all_features)} CIDs across {len(system_label_map)} systems\n')

    # === 後半 precheck §3.3, §3.4 ===
    print('=' * 60)
    print('測定器点検 後半 (実機 features で)')
    print('=' * 60)
    atom0_feats = [f for f in all_features if f['system'] == f'atom_{ATOM_SEEDS[0]}']
    precheck_real_self_vs_random(atom0_feats)
    precheck_shuffle_structure(atom0_feats)
    print('後半 precheck PASS\n')

    # === parquet 保存 ===
    df_rows = []
    for f in all_features:
        df_rows.append({**f})
    features_df = pd.DataFrame(df_rows)
    features_df.to_parquet(OUT_DIR / 'cid_features_all.parquet', index=False)
    print(f'保存: cid_features_all.parquet ({len(df_rows)} 行)\n')

    # === z-score 標準化 (全 system 結合) ===
    all_matrix = features_to_matrix(all_features)
    all_matrix_z, z_mean, z_std = z_score_normalize(all_matrix)
    print(f'z-score 標準化: 全 {all_matrix.shape[0]} CIDs × {all_matrix.shape[1]} dims')
    print(f'  z_mean: {z_mean}')
    print(f'  z_std:  {z_std}\n')

    # system 別行列
    system_matrix = {}
    cursor = 0
    for label in [f'atom_{sa}' for sa in ATOM_SEEDS] + ['real_other'] + \
                 [f'null_other_{ns}' for ns in NULL_OTHER_SEEDS]:
        n = sum(1 for f in all_features if f['system'] == label)
        system_matrix[label] = all_matrix_z[cursor:cursor + n]
        cursor += n

    # === 観察: real vs null (per atom) ===
    print('=' * 60)
    print('観察事実: real sim vs null 分布 (per atom)')
    print('=' * 60)
    n_atom = len(ATOM_SEEDS)
    judgments = []
    real_other_matrix = system_matrix['real_other']
    for sa in ATOM_SEEDS:
        atom_matrix = system_matrix[f'atom_{sa}']
        sim_real = cosine_sim_matrix(atom_matrix, real_other_matrix)
        real_mean = float(sim_real.mean()) if sim_real.size > 0 else 0.0

        null_means = []
        for ns in NULL_OTHER_SEEDS:
            null_matrix = system_matrix[f'null_other_{ns}']
            sim_null = cosine_sim_matrix(atom_matrix, null_matrix)
            null_means.append(float(sim_null.mean()) if sim_null.size > 0 else 0.0)

        null_max = max(null_means)
        null_mean = float(np.mean(null_means))
        gap = real_mean - null_mean
        rank = sum(1 for n in null_means if real_mean > n)
        above_max = bool(real_mean > null_max)

        print(f'\n  [atom={sa}] n_cids={atom_matrix.shape[0]}, real_other n_cids={real_other_matrix.shape[0]}')
        print(f'    real_sim_mean = {real_mean:.4f}')
        print(f'    null_sim_means = {[f"{n:.4f}" for n in null_means]}')
        print(f'    null_max = {null_max:.4f}, null_mean = {null_mean:.4f}')
        print(f'    gap (real - null_mean) = {gap:+.4f}')
        print(f'    rank (real > null_i) = {rank}/{len(NULL_OTHER_SEEDS)}')
        print(f'    above_null_max = {above_max}')

        judgments.append({
            'atom_seed': sa, 'real_sim_mean': real_mean,
            'null_sim_means': null_means, 'null_max': null_max,
            'null_mean': null_mean, 'gap': gap, 'rank': rank,
            'above_null_max': above_max,
            'n_atom_cids': int(atom_matrix.shape[0]),
            'n_real_other_cids': int(real_other_matrix.shape[0]),
        })

    sim_summary_df = pd.DataFrame([
        {
            'atom_seed': j['atom_seed'],
            'real_sim_mean': j['real_sim_mean'],
            'null_max': j['null_max'], 'null_mean': j['null_mean'],
            'gap': j['gap'], 'rank': j['rank'],
            'above_null_max': j['above_null_max'],
        }
        for j in judgments
    ])
    sim_summary_df.to_parquet(OUT_DIR / 'sim_summary.parquet', index=False)

    # === 観察事実 (言葉縛り) ===
    print('\n' + '=' * 60)
    print('観察事実 (Taka 言葉縛り)')
    print('=' * 60)
    n_above_max = sum(1 for j in judgments if j['above_null_max'])
    n_full_rank = sum(1 for j in judgments if j['rank'] == len(NULL_OTHER_SEEDS))
    print(f'\n  3 atom 共通で real > null_max: {n_above_max}/{n_atom}')
    print(f'  3 atom 共通で rank = 5/5:      {n_full_rank}/{n_atom}')

    if n_full_rank == n_atom and n_above_max == n_atom:
        print('  → 偶然より特に似てる組が観察された (3 atom 共通、構造的)')
    elif n_full_rank > 0 or n_above_max > 0:
        print(f'  → 一部 atom ({n_full_rank}/{n_atom} で rank=5/5) のみ、atom 依存の観察')
    else:
        print('  → 偶然より似てるとは言えない (どの atom も null 分布内)')

    summary_json = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'design': 'v1113_cid_feature_from_v918 (案 B)',
        'ATOM_SEEDS': ATOM_SEEDS,
        'OTHER_SEED_FIXED': OTHER_SEED_FIXED,
        'NULL_OTHER_SEEDS': NULL_OTHER_SEEDS,
        'FEATURE_KEYS': FEATURE_KEYS,
        'z_mean': z_mean.tolist(),
        'z_std': z_std.tolist(),
        'judgments': [
            {**j, 'null_sim_means': [float(x) for x in j['null_sim_means']]}
            for j in judgments
        ],
        'n_above_max': n_above_max,
        'n_full_rank': n_full_rank,
    }
    (OUT_DIR / 'summary.json').write_text(
        json.dumps(summary_json, indent=2, ensure_ascii=False))
    print('\n=== v1113 案 B 完了 ===')


if __name__ == '__main__':
    main()
