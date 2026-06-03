#!/usr/bin/env python3
"""v1113 CID 特性ベクトル共鳴測定 — 地面が在るか (Taka 指示 2026-06-04)

全体の流れ (v1113_overall_roadmap.md):
1. v1113 = 地面確認 (今回)
2. Stage 2: 足場を一個置く (Center が単位として束ねる、別実験)
3. Stage 3: 床になる (異なる自我、別実験)
4. Stage 4: 会話の芽 (応答の向き、別実験)

v1113 の問い (一点だけ):
別 seed の二系 (Atom 系 / Other 系) の CID 集合に、「皆同じだから似てる」を引き算した上で、
特に似てる組が在るか。

実装:
- CID 真の情報 (15 次元、node ID 排他) で特性ベクトル化
- z-score 標準化 + cosine similarity
- null = 別 seed の Other 系 5 個 (NULL_OTHER_SEEDS) との sim 分布
- 判定: real sim が null 分布より明確に高いか (rank, gap)

不変規律:
- node ID 完全排他 (絶対): nodes/member_nodes/attention[cid][node_id] 使わない
- state なし観察 (両系を read-only で読むだけ、書き戻しなし)
- 自然進化 (注入なし)
- 過去標準スケール (500 step × 30 windows)
- factor なし、大小のみ
- 報告言葉縛り (crown 禁止、観察事実のみ)

教訓 (v1110-v1112、[[code-a-blind-spots]]):
- §11: 集計指標が処置と独立 → 主指標は処置 sensitive に
- §12: null = 自身 shuffle では「皆同じだから似てる」を引き算できない → 別 seed 別系を複数
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

import sys, json, time, math
from pathlib import Path
from multiprocessing import Pool
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
STAGE5 = REPO / 'unified/attention_center_prep'
OUT_DIR = STAGE5 / 'run_v1113'
OUT_DIR.mkdir(parents=True, exist_ok=True)

PATHS = [
    REPO / 'primitive/v910',
    REPO / 'autonomy/v82',
    REPO / 'cognition/semantic_injection/v4_pipeline/v43',
    REPO / 'cognition/semantic_injection/v4_pipeline/v41',
    REPO / 'ecology/engine',
]
for p in PATHS:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# === 構成 (smoke = 3 atom、本実行 = 24 atom) ===
ATOM_SEEDS = [42, 100, 200]  # smoke、24 seeds 1 バッチは別 run で
OTHER_SEED_FIXED = 999  # real other (atom と別 seed)
NULL_OTHER_SEEDS = [12345, 54321, 7777, 11111, 33333]  # 別系 null 5 個 (atom/real_other と非重複)
WINDOW_STEPS = 500
WINDOWS = 30  # 過去標準
N_BINS_NOT_USED = 64  # phase 空間は使わない (痩せた表現を捨てた)


# === module level: engine 構築 / 特性抽出 / similarity ===

def _import_engine():
    from esde_v82_engine import V82Engine, V82EncapsulationParams, V82_N
    from virtual_layer_v9 import VirtualLayer as VirtualLayerV9
    return V82Engine, V82EncapsulationParams, V82_N, VirtualLayerV9


def _build_engine_local(seed):
    V82Engine, V82EncapsulationParams, V82_N, VirtualLayerV9 = _import_engine()
    encap = V82EncapsulationParams(stress_enabled=True, virtual_enabled=True)
    engine = V82Engine(seed=seed, N=V82_N, encap_params=encap)
    engine.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True
    engine.run_injection()
    return engine


def angle_to_xy(theta):
    """circular phase (-π..π) を (cos, sin) に展開"""
    return float(math.cos(theta)), float(math.sin(theta))


# 15 次元 特性ベクトル (node ID free 属性のみ)
FEATURE_KEYS = [
    'phase_sig_cos',          # 生誕時平均θ (cos)
    'phase_sig_sin',          # 生誕時平均θ (sin)
    'phi_cos',                # 現在の内的基準軸θ (cos)
    'phi_sin',                # 現在の内的基準軸θ (sin)
    'n_core',                 # 生誕時メンバー数 (node ID でなく数)
    'lifespan',               # window 単位寿命
    'Q0',                     # 生誕時認知資源
    'Q_remaining',            # 残存 Q
    'C',                      # 意識資源
    'familiarity_n',          # 他 cid への familiarity 記憶数 (cid 数、node ID なし)
    'v10_pulse_count',        # 総 pulse fired 数
    'v11_n_captured',         # 捕捉確定 pulse 数
    'v11_b_gen',              # Genesis Budget
    'cid_ttl_bonus',          # TTL 延長累積
    'v18_birth_v_unified_concentration',  # 生誕時 unity concentration
]


def _safe_get(d, key, default=0.0):
    """dict-like or attr-like から安全に取得"""
    if d is None:
        return default
    if hasattr(d, 'get'):
        v = d.get(key, default)
    elif hasattr(d, key):
        v = getattr(d, key, default)
    else:
        v = default
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def extract_cid_features(engine, system_label, window_now):
    """30 windows 後の engine から CID 特性 (node ID free) を抽出

    Returns:
        list of dict, 各 dict は { 'cid': int, 'system': str, **FEATURE_KEYS }
    """
    cog = engine.cog
    vl = engine.virtual
    features = []

    # cog.current_lid: {cid: lid or None}
    current_lid = getattr(cog, 'current_lid', {})
    # cog の各 dict (取れないものは default 0)
    born_at = getattr(cog, 'born_at', {})
    phi_dict = getattr(cog, 'phi', {})
    original_phase_sig_dict = getattr(cog, 'original_phase_sig', {})
    Q_dict = getattr(cog, 'Q', {})
    C_dict = getattr(cog, 'C', {})
    ghost_Q_dict = getattr(cog, 'ghost_residual_Q', {})
    familiarity_dict = getattr(cog, 'familiarity', {})
    cid_ttl_bonus_dict = getattr(cog, 'cid_ttl_bonus', {})
    v11_b_gen_dict = getattr(cog, 'v11_b_gen', {})
    v11_n_pulses_eval_dict = getattr(cog, 'v11_n_pulses_eval', {})
    v11_n_captured_dict = getattr(cog, 'v11_n_captured', {})
    v10_pulse_count_dict = getattr(cog, 'v10_pulse_count', {})
    # v918 CidSelfBuffer
    v915_buffers = getattr(cog, 'v915_buffers', {})

    # vl.labels: {lid: label_dict or label_obj}
    labels = getattr(vl, 'labels', {})

    for cid, lid in current_lid.items():
        if lid is None:
            continue  # ghost (active でない)

        # phase_sig (生誕時、original_phase_sig 優先、なければ label.phase_sig)
        original_phase_sig = _safe_get(original_phase_sig_dict, cid, 0.0)
        ps_cos, ps_sin = angle_to_xy(original_phase_sig)

        # phi (現在の内的基準軸)
        phi = _safe_get(phi_dict, cid, 0.0)
        phi_cos, phi_sin = angle_to_xy(phi)

        # n_core (buffer.n_core 優先、なければ familiarity 数で近似)
        buf = v915_buffers.get(cid) if isinstance(v915_buffers, dict) else None
        if buf is not None and hasattr(buf, 'n_core'):
            n_core = float(buf.n_core)
        else:
            fam = familiarity_dict.get(cid, {}) if isinstance(familiarity_dict, dict) else {}
            n_core = float(len(fam))  # 近似 (familiarity 数)

        # lifespan
        lifespan = float(window_now - _safe_get(born_at, cid, window_now))

        # Q0, Q_remaining
        if buf is not None and hasattr(buf, 'Q0'):
            Q0 = float(getattr(buf, 'Q0', 0))
        else:
            Q0 = _safe_get(Q_dict, cid, 0.0)
        if buf is not None and hasattr(buf, 'Q_remaining'):
            Q_rem = float(getattr(buf, 'Q_remaining', 0))
        else:
            Q_rem = _safe_get(Q_dict, cid, 0.0)

        # C (意識資源)
        C_val = _safe_get(C_dict, cid, 0.0)

        # familiarity 数
        fam = familiarity_dict.get(cid, {}) if isinstance(familiarity_dict, dict) else {}
        fam_n = float(len(fam))

        # pulse / capture
        v10_pulse = _safe_get(v10_pulse_count_dict, cid, 0.0)
        v11_captured = _safe_get(v11_n_captured_dict, cid, 0.0)
        v11_b = _safe_get(v11_b_gen_dict, cid, 0.0)  # 文字列 "unformed" は 0 に

        # cid_ttl_bonus
        ttl_bonus = _safe_get(cid_ttl_bonus_dict, cid, 0.0)

        # v18 unity (buffer 経由)
        if buf is not None and hasattr(buf, 'v18_v_unified_concentration_birth'):
            v18_uc = float(getattr(buf, 'v18_v_unified_concentration_birth', 0) or 0)
        else:
            v18_uc = 0.0

        feat = {
            'cid': cid,
            'system': system_label,
            'phase_sig_cos': ps_cos,
            'phase_sig_sin': ps_sin,
            'phi_cos': phi_cos,
            'phi_sin': phi_sin,
            'n_core': n_core,
            'lifespan': lifespan,
            'Q0': Q0,
            'Q_remaining': Q_rem,
            'C': C_val,
            'familiarity_n': fam_n,
            'v10_pulse_count': v10_pulse,
            'v11_n_captured': v11_captured,
            'v11_b_gen': v11_b,
            'cid_ttl_bonus': ttl_bonus,
            'v18_birth_v_unified_concentration': v18_uc,
        }
        features.append(feat)
    return features


def features_to_matrix(features_list):
    """list of dict → np.ndarray (n_cids, n_features)"""
    if len(features_list) == 0:
        return np.zeros((0, len(FEATURE_KEYS)), dtype=float)
    return np.array([
        [f[k] for k in FEATURE_KEYS]
        for f in features_list
    ], dtype=float)


def z_score_normalize(matrix_all_systems):
    """全 system 結合行列で z-score 標準化 (列ごと)"""
    if matrix_all_systems.shape[0] == 0:
        return matrix_all_systems, np.zeros(matrix_all_systems.shape[1]), np.ones(matrix_all_systems.shape[1])
    mean = matrix_all_systems.mean(axis=0)
    std = matrix_all_systems.std(axis=0)
    std_safe = np.where(std < 1e-9, 1.0, std)
    return (matrix_all_systems - mean) / std_safe, mean, std_safe


def cosine_sim_matrix(A, B):
    """A の全 row と B の全 row のペアごと cosine similarity
    A: shape (n_a, d), B: shape (n_b, d)
    return: shape (n_a, n_b)
    """
    if A.shape[0] == 0 or B.shape[0] == 0:
        return np.zeros((A.shape[0], B.shape[0]))
    A_norm = np.linalg.norm(A, axis=1, keepdims=True)
    B_norm = np.linalg.norm(B, axis=1, keepdims=True)
    A_norm_safe = np.where(A_norm < 1e-9, 1.0, A_norm)
    B_norm_safe = np.where(B_norm < 1e-9, 1.0, B_norm)
    A_u = A / A_norm_safe
    B_u = B / B_norm_safe
    return A_u @ B_u.T


# === 測定器点検 (Taka 必須、本実行前) ===

def precheck_identity():
    """§3.1: sim(v, v) = 1.0 (恒等性、コードバグ検出)"""
    print('[precheck §3.1] 恒等性 sim(v, v) = 1.0 ...')
    rng = np.random.RandomState(42)
    v = rng.normal(0, 1, size=len(FEATURE_KEYS))
    sim = cosine_sim_matrix(v.reshape(1, -1), v.reshape(1, -1))[0, 0]
    if abs(sim - 1.0) > 1e-9:
        raise RuntimeError(f'§3.1 FAIL: sim(v, v) = {sim} != 1.0')
    print(f'  sim(v, v) = {sim:.6f} OK')


def precheck_kernel_function():
    """§3.2: 揺らした自己 > 乱数 (kernel 機能、ダミーで即時)"""
    print('[precheck §3.2] kernel 機能 (揺らした自己 > 乱数)...')
    rng = np.random.RandomState(42)
    n_trials = 10
    n_dim = len(FEATURE_KEYS)
    failed = 0
    for t in range(n_trials):
        v = rng.normal(0, 1, size=n_dim)
        noise = rng.normal(0, 0.05, size=n_dim)  # 5% noise
        v_perturbed = v + noise
        v_random = rng.normal(0, 1, size=n_dim)
        sim_pert = cosine_sim_matrix(v.reshape(1, -1), v_perturbed.reshape(1, -1))[0, 0]
        sim_rand = cosine_sim_matrix(v.reshape(1, -1), v_random.reshape(1, -1))[0, 0]
        if not (sim_pert > sim_rand):
            failed += 1
    if failed > n_trials // 3:
        raise RuntimeError(
            f'§3.2 FAIL: {failed}/{n_trials} trial で揺らした自己 ≤ 乱数 — kernel 機能せず'
        )
    print(f'  揺らした自己 > 乱数: {n_trials - failed}/{n_trials} trial OK')


# === Worker (Pool で起動) ===

def _worker(args):
    seed, system_label = args
    pid = os.getpid()
    print(f'  [PID {pid}] start {system_label} seed={seed}', flush=True)
    t0 = time.time()
    for p in PATHS:
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))

    engine = _build_engine_local(seed)
    for w in range(WINDOWS):
        engine.step_window(steps=WINDOW_STEPS)

    features = extract_cid_features(engine, system_label, WINDOWS)
    dt = time.time() - t0
    print(f'  [PID {pid}] done {system_label} seed={seed} ({dt:.0f}s) '
          f'n_cids={len(features)}', flush=True)
    return {'seed': seed, 'system': system_label, 'features': features}


def make_tasks():
    tasks = []
    for sa in ATOM_SEEDS:
        tasks.append((sa, f'atom_{sa}'))
    tasks.append((OTHER_SEED_FIXED, 'real_other'))
    for ns in NULL_OTHER_SEEDS:
        tasks.append((ns, f'null_other_{ns}'))
    return tasks


# === Stage 1 後点検 (本実行 features を使った §3.3, §3.4) ===

def precheck_real_self_vs_random(features_one_system):
    """§3.3: 実機 CID の自己 sim > 乱数 sim (各 CID で確認)"""
    print('[precheck §3.3] 実機 CID 自己 sim > 乱数 sim...')
    if len(features_one_system) == 0:
        raise RuntimeError('§3.3 FAIL: features 0 個、CID 取得できず')
    matrix = features_to_matrix(features_one_system)
    # 全 CID 集合で z-score 標準化 (system 内のみ)
    matrix_z, _, _ = z_score_normalize(matrix)

    rng = np.random.RandomState(999)
    n_dim = matrix_z.shape[1]
    failed = 0
    n_total = len(features_one_system)
    for i in range(n_total):
        v = matrix_z[i:i+1]  # 自己
        v_random = rng.normal(0, 1, size=(1, n_dim))
        sim_self = cosine_sim_matrix(v, v)[0, 0]  # = 1.0
        sim_rand = cosine_sim_matrix(v, v_random)[0, 0]
        if not (sim_self > sim_rand):
            failed += 1
    if failed > 0:
        raise RuntimeError(
            f'§3.3 FAIL: {failed}/{n_total} CID で 自己 ≤ 乱数'
        )
    print(f'  全 {n_total} CID で 自己 > 乱数 OK')


def precheck_shuffle_structure(features_one_system):
    """§3.4: 自身行列 shuffle で sim が下がる (特性ベクトル構造の確認)"""
    print('[precheck §3.4] shuffle 構造破壊で sim 低下...')
    if len(features_one_system) < 3:
        print(f'  features {len(features_one_system)} 個、scaffold check skip')
        return
    matrix = features_to_matrix(features_one_system)
    matrix_z, _, _ = z_score_normalize(matrix)

    # 自己 sim (= 全 CID ペア、対角を除く)
    sim_self = cosine_sim_matrix(matrix_z, matrix_z)
    np.fill_diagonal(sim_self, np.nan)
    sim_self_mean = np.nanmean(sim_self)

    # 各次元独立 shuffle (構造破壊)
    rng = np.random.RandomState(7777)
    matrix_shuffled = matrix_z.copy()
    for col in range(matrix_shuffled.shape[1]):
        matrix_shuffled[:, col] = matrix_shuffled[rng.permutation(matrix_shuffled.shape[0]), col]

    sim_shuffled = cosine_sim_matrix(matrix_z, matrix_shuffled)
    sim_shuffled_mean = np.mean(sim_shuffled)

    print(f'  sim(自己 vs 自己) mean = {sim_self_mean:.4f}')
    print(f'  sim(自己 vs shuffled) mean = {sim_shuffled_mean:.4f}')
    if sim_self_mean <= sim_shuffled_mean:
        raise RuntimeError(
            f'§3.4 FAIL: 自己 sim ({sim_self_mean:.4f}) ≤ shuffled sim ({sim_shuffled_mean:.4f}) — '
            f'特性ベクトルが構造を持たない'
        )
    print(f'  自己 sim > shuffled sim OK')


def main():
    print('=== v1113 CID 特性ベクトル共鳴測定 — 地面が在るか ===\n')
    print(f'  ATOM_SEEDS={ATOM_SEEDS}')
    print(f'  OTHER_SEED_FIXED={OTHER_SEED_FIXED} (real)')
    print(f'  NULL_OTHER_SEEDS={NULL_OTHER_SEEDS}')
    print(f'  WINDOW_STEPS={WINDOW_STEPS}, WINDOWS={WINDOWS}')
    print(f'  特性ベクトル次元: {len(FEATURE_KEYS)}')
    print(f'  実装規律: node ID 排他、state なし、自然進化\n')

    # === precheck 前半 (即時、ダミー) ===
    print('=' * 60)
    print('測定器点検 前半 (ダミー、即時)')
    print('=' * 60)
    precheck_identity()
    precheck_kernel_function()
    print('前半 precheck PASS\n')

    # === Pool で 9 systems 並列 build_engine + step_window ===
    tasks = make_tasks()
    print(f'Tasks: {len(tasks)} systems '
          f'= {len(ATOM_SEEDS)} atom + 1 real_other + {len(NULL_OTHER_SEEDS)} null_others')
    n_workers = min(len(tasks), 9)
    print(f'並列: Pool({n_workers}) で 1 Wave\n')

    t_main = time.time()
    with Pool(processes=n_workers) as pool:
        results = pool.map(_worker, tasks)

    print(f'\n全 system 完了 ({time.time() - t_main:.1f}s)')

    # === 後半 precheck §3.3, §3.4 (実機 features で) ===
    print('\n' + '=' * 60)
    print('測定器点検 後半 (実機 features で)')
    print('=' * 60)
    # 最初の atom system (=42) で点検
    atom42_features = [r['features'] for r in results if r['system'] == f'atom_{ATOM_SEEDS[0]}'][0]
    print(f'  atom_{ATOM_SEEDS[0]} features = {len(atom42_features)} CIDs')
    precheck_real_self_vs_random(atom42_features)
    precheck_shuffle_structure(atom42_features)
    print('後半 precheck PASS\n')

    # === 全 features を保存 ===
    all_features_rows = []
    for r in results:
        for f in r['features']:
            row = {'seed': r['seed'], **f}
            all_features_rows.append(row)
    features_df = pd.DataFrame(all_features_rows)
    features_df.to_parquet(OUT_DIR / 'cid_features_all.parquet', index=False)
    print(f'保存: cid_features_all.parquet ({len(all_features_rows)} 行)\n')

    # === 全 system 結合 z-score 標準化 ===
    all_matrix = features_to_matrix(
        [r_f for r in results for r_f in r['features']]
    )
    all_matrix_z, z_mean, z_std = z_score_normalize(all_matrix)
    print(f'z-score 標準化: 全 {all_matrix.shape[0]} CIDs × {all_matrix.shape[1]} dims')
    print(f'  z_mean: {z_mean}')
    print(f'  z_std:  {z_std}\n')

    # system 別 z-normalized 行列
    system_matrix = {}
    cursor = 0
    for r in results:
        n = len(r['features'])
        system_matrix[r['system']] = all_matrix_z[cursor:cursor+n]
        cursor += n

    # === 各 atom について real vs null 比較 ===
    print('=' * 60)
    print('観察事実: real sim vs null 分布 (per atom)')
    print('=' * 60)
    n_atom = len(ATOM_SEEDS)
    judgments = []
    sim_summary_rows = []
    for sa in ATOM_SEEDS:
        atom_label = f'atom_{sa}'
        atom_matrix = system_matrix[atom_label]
        real_other_matrix = system_matrix['real_other']

        # real sim
        sim_real = cosine_sim_matrix(atom_matrix, real_other_matrix)
        real_mean = float(sim_real.mean()) if sim_real.size > 0 else 0.0
        real_top5 = float(np.percentile(sim_real.flatten(), 95)) if sim_real.size > 0 else 0.0
        real_top5_count = int((sim_real > real_top5).sum()) if sim_real.size > 0 else 0

        # null sim (5 系)
        null_means = []
        null_top5s = []
        for ns in NULL_OTHER_SEEDS:
            null_label = f'null_other_{ns}'
            null_matrix = system_matrix[null_label]
            sim_null = cosine_sim_matrix(atom_matrix, null_matrix)
            null_means.append(float(sim_null.mean()) if sim_null.size > 0 else 0.0)
            null_top5s.append(float(np.percentile(sim_null.flatten(), 95)) if sim_null.size > 0 else 0.0)

        null_max = max(null_means) if null_means else 0.0
        null_mean = float(np.mean(null_means)) if null_means else 0.0
        gap = real_mean - null_mean
        rank = sum(1 for n in null_means if real_mean > n)
        above_max = bool(real_mean > null_max)

        print(f'\n  [atom={sa}] n_cids={atom_matrix.shape[0]}, real_other n_cids={real_other_matrix.shape[0]}')
        print(f'    real_sim_mean   = {real_mean:.4f}')
        print(f'    null_sim_means  = {[f"{n:.4f}" for n in null_means]}')
        print(f'    null_max        = {null_max:.4f}')
        print(f'    null_mean       = {null_mean:.4f}')
        print(f'    gap (real - null_mean) = {gap:+.4f}')
        print(f'    rank (real > null_i)   = {rank}/{len(NULL_OTHER_SEEDS)}')
        print(f'    above_null_max         = {above_max}')

        judgments.append({
            'atom_seed': sa,
            'real_sim_mean': real_mean,
            'null_sim_means': null_means,
            'null_max': null_max,
            'null_mean': null_mean,
            'gap': gap,
            'rank': rank,
            'above_null_max': above_max,
            'n_atom_cids': int(atom_matrix.shape[0]),
            'n_real_other_cids': int(real_other_matrix.shape[0]),
        })
        sim_summary_rows.append({
            'atom_seed': sa,
            'real_sim_mean': real_mean,
            'null_max': null_max,
            'null_mean': null_mean,
            'gap': gap,
            'rank': rank,
            'above_null_max': above_max,
        })

    sim_df = pd.DataFrame(sim_summary_rows)
    sim_df.to_parquet(OUT_DIR / 'sim_summary.parquet', index=False)

    # === 観察事実 (判定置かない、言葉縛り) ===
    print('\n' + '=' * 60)
    print('観察事実 (Taka 言葉縛り: 偶然より似たペアが出た / 出ない、だけ)')
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
        'design': 'v1113_cid_feature_resonance',
        'ATOM_SEEDS': ATOM_SEEDS,
        'OTHER_SEED_FIXED': OTHER_SEED_FIXED,
        'NULL_OTHER_SEEDS': NULL_OTHER_SEEDS,
        'WINDOW_STEPS': WINDOW_STEPS, 'WINDOWS': WINDOWS,
        'FEATURE_KEYS': FEATURE_KEYS,
        'z_mean': z_mean.tolist(),
        'z_std': z_std.tolist(),
        'judgments': [
            {**j, 'null_sim_means': [float(x) for x in j['null_sim_means']]}
            for j in judgments
        ],
        'n_above_max': n_above_max,
        'n_full_rank': n_full_rank,
        'total_sec': time.time() - t_main,
    }
    (OUT_DIR / 'summary.json').write_text(
        json.dumps(summary_json, indent=2, ensure_ascii=False))
    print(f'\n=== v1113 完了 total {time.time() - t_main:.1f}s ===')


if __name__ == '__main__':
    main()
