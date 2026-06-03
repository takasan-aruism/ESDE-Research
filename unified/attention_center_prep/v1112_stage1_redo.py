#!/usr/bin/env python3
"""v1112 Stage 1 作り直し — 共鳴 CID が立つか (測定器組み直し版、第三 ESDE、両床対照)

Web Claude / Taka 指示 (2026-06-03 + 06-04 両床指示) 準拠:
- 前回 Stage 1 は主指標 total_cooc / N_rcid が bin shift と数学的に独立 = 測れていない
- 今回は測定器を組み直して、まだ測っていないものを初めて測る
- 一様乱数 occ は実機 sparse occ と閾値挙動が桁違いで床として機能しなかった (前 §2.4 FAIL)
- → 両床 (案 A: bin permute、案 B: k 個 random) を併設、precheck PASS 床のみで本実行

組み直し 3 点:
1. 主指標 = diagonal_mass(M, delta) = Σ M[i, (i+d) mod N] over d ∈ [-delta, +delta]
   - 複数 δ (0, 1, 3) で測る、固定値なし
   - total_cooc / N_rcid は判定外、parquet 記録のみ
2. OTHER_SEED_FIXED = 999 (ATOM_SEEDS=[42,100,200] のどれとも別、同 seed 並走排除)
3. self 床 = 両床併設、precheck PASS 床のみで本実行
   - 案 A: self_permute_floor = 実機 atom occ の bin 順序を state 由来 random で permute
     (値分布・sparsity・閾値挙動が実機と完全一致、phase 帯対応だけ破壊)
   - 案 B: self_krandom_floor = 実機 atom active bin 数 k に合わせて k 個 random 非ゼロ
     (active bin 数を実機に揃えた lighter な床)
   - Active が両床を超えれば床選択に依存せず「両系で立つ」が言える
   - 片方だけなら差を観察事実に

実装前測定器点検 (main 内で本実行前に必須):
- §2.1 shift 動性: ダミー行列で diagonal_mass が np.roll で値が動くか
- §2.2 同 seed なし: OTHER_SEED_FIXED not in ATOM_SEEDS
- §2.3 床 seed 多様: window 間で重複なし
- §2.4 両床構造性: 実機 baseline occ で Active × Other > 各床、両床評価
  - 両床 FAIL → raise (本実行に進まない)
  - 片床 PASS → PASS 床のみで本実行
  - 両床 PASS → 両床で本実行

不変 (前回 Stage 1 のまま):
- 第三 ESDE = state なし観察体 (ResonanceObserver、両系 read-only、書き戻しなし)
- node ID 排他 (phase 空間 64 bin のみ)
- 案 3+4 (Kuramoto 同期 + 確率累積)
- 過去標準スケール (500 step × 30 windows、自然進化、注入なし)
- 3 atom × N conditions = (3 ~ 12) tasks、Pool() 1 Wave

報告言葉縛り: 出ても「ループの外に独立軸が立つ候補が観察された」まで。
「Unified 完成」「成立」「同期した」は書かない。
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

import sys, json, time
from pathlib import Path
from multiprocessing import Pool
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
STAGE5 = REPO / 'unified/attention_center_prep'
OUT_DIR = STAGE5 / 'run_v1112_stage1_redo'
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

ATOM_SEEDS = [42, 100, 200]
OTHER_SEED_FIXED = 999  # 変更: ATOM_SEEDS のどれとも別 seed (同 seed 並走排除)
WINDOW_STEPS = 500
MATURATION_WINDOWS = 10
TRACKING_WINDOWS = 20
WINDOWS = MATURATION_WINDOWS + TRACKING_WINDOWS  # 30
N_BINS = 64
HISTORY_LEN = 10
DELTAS = [0, 1, 3]  # 近傍幅 (複数で測る、固定値なし)

CONDITIONS_BASE = ['active_pair', 'self_permute_floor', 'self_krandom_floor', 'phase_shifted']
# precheck §2.4 で各 self 床が PASS したものだけ本実行に進む (active_pair / phase_shifted は常に実行)


# === module level: build_engine / observer / helpers ===
# precheck (main 内) と worker (別 process) で共通利用するため module level

def _import_engine():
    """V82Engine / VirtualLayerV9 を import (sys.path 経由)"""
    from esde_v82_engine import V82Engine, V82EncapsulationParams, V82_N
    from virtual_layer_v9 import VirtualLayer as VirtualLayerV9
    return V82Engine, V82EncapsulationParams, V82_N, VirtualLayerV9


def _build_engine_local(seed):
    """build_engine の実体 (precheck / worker 両方で使用)"""
    V82Engine, V82EncapsulationParams, V82_N, VirtualLayerV9 = _import_engine()
    encap = V82EncapsulationParams(stress_enabled=True, virtual_enabled=True)
    engine = V82Engine(seed=seed, N=V82_N, encap_params=encap)
    engine.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True
    engine.run_injection()
    return engine


def permute_phase_occupancy(occ_real, state_seed):
    """案 A self 床: 実機 occ の bin 順序を state 由来 random で permute
    値分布・sparsity・閾値挙動 (mean) が実機と完全一致、phase 帯対応だけ破壊
    """
    rng = np.random.RandomState(int(state_seed))
    perm = rng.permutation(len(occ_real))
    return np.asarray(occ_real, dtype=float)[perm]


def krandom_phase_occupancy(occ_real, state_seed, n_bins=N_BINS):
    """案 B self 床: 実機 active bin 数 k に合わせ k 個 random 位置で非ゼロ
    active 値は実機 active bin の平均値 (実機の閾値超え動態に揃える)
    """
    occ_real = np.asarray(occ_real, dtype=float)
    th = float(occ_real.mean())
    active_bins_real = np.where(occ_real > th)[0]
    k = len(active_bins_real)
    occ_k = np.zeros(n_bins, dtype=float)
    if k == 0:
        return occ_k
    rng = np.random.RandomState(int(state_seed))
    random_bins = rng.choice(n_bins, size=k, replace=False)
    active_mean_value = float(occ_real[active_bins_real].mean())
    occ_k[random_bins] = active_mean_value
    return occ_k


def diagonal_mass(M, delta=0):
    """主指標: 対角 + 近傍 ±delta bin の mass
    bin shift (= 列 rotate) の下で値が変わる空間構造指標
    """
    n = M.shape[0]
    s = 0
    for i in range(n):
        for d in range(-delta, delta + 1):
            s += M[i, (i + d) % n]
    return float(s)


class ResonanceObserver:
    """第三 ESDE = state なし観察体 (両系を read-only で観察、書き戻しなし)

    node ID 完全排他: 渡るのは bin index (0-63) のみ
    """
    def __init__(self, n_bins=N_BINS):
        self.N_BINS = n_bins
        self.cooc_count = np.zeros((n_bins, n_bins), dtype=np.int64)
        self.history = []
        self.diag_per_window = []  # window 単位 diagonal 推移 (delta=0)

    def observe(self, occ_a, occ_o):
        """両系 occupancy を読んで同時立ち累積
        ※ node ID なし、bin index のみ
        """
        occ_a = np.asarray(occ_a, dtype=float)
        occ_o = np.asarray(occ_o, dtype=float)
        th_a = float(occ_a.mean())
        th_o = float(occ_o.mean())
        active_a = np.where(occ_a > th_a)[0]
        active_o = np.where(occ_o > th_o)[0]
        cooc_set = set()
        for a in active_a:
            for b in active_o:
                self.cooc_count[a, b] += 1
                cooc_set.add((int(a), int(b)))
        self.history.append(cooc_set)
        if len(self.history) > HISTORY_LEN:
            self.history.pop(0)
        # window 単位 diagonal (delta=0) 推移
        self.diag_per_window.append(diagonal_mass(self.cooc_count, delta=0))

    def summary(self):
        """主指標 (diagonal) + 参考指標 (total_cooc 等、判定外記録のみ)"""
        nonzero = self.cooc_count[self.cooc_count > 0]
        out = {
            # 主指標 (Stage 1 出口判定に使う)
            'diag_d0': diagonal_mass(self.cooc_count, delta=0),
            'diag_d1': diagonal_mass(self.cooc_count, delta=1),
            'diag_d3': diagonal_mass(self.cooc_count, delta=3),
            # 参考指標 (記録のみ、判定外)
            'total_cooc': int(self.cooc_count.sum()),
            'n_active_pairs': int(np.sum(self.cooc_count > 0)),
            'max_cooc': int(self.cooc_count.max()) if self.cooc_count.size > 0 else 0,
            'mean_cooc_nonzero': float(nonzero.mean()) if len(nonzero) > 0 else 0.0,
            # window 推移
            'diag_per_window': self.diag_per_window,
        }
        return out


# === 測定器点検 (main 内で本実行前に必須) ===

def precheck_shift_sensitivity():
    """§2.1: ダミー行列で diagonal_mass が np.roll で値が動くか"""
    print('[precheck §2.1] ダミー行列 shift 動性...')
    rng = np.random.RandomState(42)
    M = rng.randint(0, 10, (N_BINS, N_BINS))
    for delta in DELTAS:
        d_orig = diagonal_mass(M, delta=delta)
        d_shift = diagonal_mass(np.roll(M, N_BINS // 2, axis=1), delta=delta)
        if d_orig == d_shift:
            raise RuntimeError(
                f'§2.1 FAIL: delta={delta} で diagonal_mass が shift 不変 '
                f'({d_orig}=={d_shift}) — 主指標が壊れている、止める'
            )
        print(f'  delta={delta}: orig={d_orig:.0f} shifted={d_shift:.0f} '
              f'diff={d_orig - d_shift:+.0f} OK')


def precheck_no_same_seed():
    """§2.2: OTHER_SEED_FIXED が ATOM_SEEDS と重複しないか"""
    print('[precheck §2.2] 同 seed 並走なし...')
    if OTHER_SEED_FIXED in ATOM_SEEDS:
        raise RuntimeError(
            f'§2.2 FAIL: OTHER_SEED_FIXED={OTHER_SEED_FIXED} が '
            f'ATOM_SEEDS={ATOM_SEEDS} に含まれる — 同 seed 並走汚染、止める'
        )
    print(f'  OTHER_SEED_FIXED={OTHER_SEED_FIXED}, ATOM_SEEDS={ATOM_SEEDS} OK')


def precheck_seed_diversity():
    """§2.3: 床 seed が window 間で多様か"""
    print('[precheck §2.3] 床 seed 多様性...')
    for sa in ATOM_SEEDS:
        seeds = [sa * 100003 + w * 7919 for w in range(WINDOWS)]
        if len(set(seeds)) != WINDOWS:
            raise RuntimeError(
                f'§2.3 FAIL: atom={sa} で window 間床 seed が重複 '
                f'({len(set(seeds))} unique / {WINDOWS}) — 床の独立性なし'
            )
        print(f'  atom={sa}: {WINDOWS} unique seeds OK')


# precheck §2.4 用: 統計安定性のため複数 atom で実機 occ を取得
PROBE_N_WINDOWS = 3  # 各 atom で点検 windows 数 (raw 値の安定性向上)


def precheck_floor_structures():
    """§2.4: 両床 (permute, krandom) が Active × Other より低くなるか、
    実機 baseline occupancy で点検。3 atom × PROBE_N_WINDOWS で統計安定化。

    返り値: floor_pass = {'self_permute_floor': bool, 'self_krandom_floor': bool}
    """
    print(f'[precheck §2.4] 両床構造性 (実機 baseline occ で点検、'
          f'{len(ATOM_SEEDS)} atom × {PROBE_N_WINDOWS} windows)...')
    t0 = time.time()

    # Other は 1 つの probe を全 atom で共用
    print(f'  build_engine(other_seed={OTHER_SEED_FIXED}) ...')
    other_probe = _build_engine_local(OTHER_SEED_FIXED)
    # 3 windows ぶん Other を進化させて occ snapshot を取得
    other_occs = []
    for w in range(PROBE_N_WINDOWS):
        other_probe.step_window(steps=WINDOW_STEPS)
        other_occs.append(np.asarray(other_probe.virtual.occupancy, dtype=float))

    # 累積 cooc (4 種類: aa, ao, ap, ak) を全 atom × window で集計
    o_aa = ResonanceObserver()  # Active 自己 (上限)
    o_ao = ResonanceObserver()  # Active × Other
    o_ap = ResonanceObserver()  # Active × permute 床
    o_ak = ResonanceObserver()  # Active × krandom 床

    for sa in ATOM_SEEDS:
        print(f'  build_engine(atom_seed={sa}) ...')
        atom_probe = _build_engine_local(sa)
        for w in range(PROBE_N_WINDOWS):
            atom_probe.step_window(steps=WINDOW_STEPS)
            occ_a = np.asarray(atom_probe.virtual.occupancy, dtype=float)
            occ_o = other_occs[w]
            state_seed = sa * 100003 + w * 7919
            occ_perm = permute_phase_occupancy(occ_a, state_seed)
            occ_kr = krandom_phase_occupancy(occ_a, state_seed)
            # 閾値挙動 (atom=ATOM_SEEDS[0] の w=0 のみ詳細表示)
            if sa == ATOM_SEEDS[0] and w == 0:
                print(f'    [atom={sa} w={w}] 閾値挙動:')
                print(f'      実機 Atom:  mean={occ_a.mean():.4f}, '
                      f'n_above_mean={int((occ_a > occ_a.mean()).sum())}/{N_BINS}')
                print(f'      実機 Other: mean={occ_o.mean():.4f}, '
                      f'n_above_mean={int((occ_o > occ_o.mean()).sum())}/{N_BINS}')
                print(f'      permute:    mean={occ_perm.mean():.4f}, '
                      f'n_above_mean={int((occ_perm > occ_perm.mean()).sum())}/{N_BINS}')
                print(f'      krandom:    mean={occ_kr.mean():.4f}, '
                      f'n_above_mean={int((occ_kr > occ_kr.mean()).sum())}/{N_BINS}')
            o_aa.observe(occ_a, occ_a)
            o_ao.observe(occ_a, occ_o)
            o_ap.observe(occ_a, occ_perm)
            o_ak.observe(occ_a, occ_kr)

    diag_aa = diagonal_mass(o_aa.cooc_count, delta=0)
    diag_ao = diagonal_mass(o_ao.cooc_count, delta=0)
    diag_ap = diagonal_mass(o_ap.cooc_count, delta=0)
    diag_ak = diagonal_mass(o_ak.cooc_count, delta=0)

    print(f'  累積 cooc (3 atom × {PROBE_N_WINDOWS} windows):')
    print(f'    diag_aa (Active 自己、上限)        = {diag_aa}')
    print(f'    diag_ao (Active × Other 別 seed)   = {diag_ao}')
    print(f'    diag_ap (Active × permute、案 A 床)= {diag_ap}')
    print(f'    diag_ak (Active × krandom、案 B 床)= {diag_ak}')

    # 構造的不可能チェック (床が Active 自己を超えるのは observe バグ)
    if diag_ap >= diag_aa:
        raise RuntimeError(
            f'§2.4 FAIL: permute 床 ({diag_ap}) >= Active 自己 ({diag_aa}) — '
            f'構造的に不可能、observe / diagonal_mass / permute 関数バグ。'
        )
    if diag_ak >= diag_aa:
        raise RuntimeError(
            f'§2.4 FAIL: krandom 床 ({diag_ak}) >= Active 自己 ({diag_aa}) — '
            f'構造的に不可能、observe / diagonal_mass / krandom 関数バグ。'
        )

    # 各床の PASS 判定 (Active × Other > 各床、strict less)
    floor_pass = {
        'self_permute_floor': diag_ap < diag_ao,
        'self_krandom_floor': diag_ak < diag_ao,
    }
    print(f'  床 PASS 判定:')
    print(f'    self_permute_floor: diag_ap ({diag_ap}) < diag_ao ({diag_ao}) = '
          f'{floor_pass["self_permute_floor"]}')
    print(f'    self_krandom_floor: diag_ak ({diag_ak}) < diag_ao ({diag_ao}) = '
          f'{floor_pass["self_krandom_floor"]}')

    if not any(floor_pass.values()):
        raise RuntimeError(
            f'§2.4 FAIL: 両床とも機能しない '
            f'(permute={diag_ap}, krandom={diag_ak}, Active×Other={diag_ao}) — '
            f'self 床設計を再考、本実行に進まない。'
        )

    pass_floors = [k for k, v in floor_pass.items() if v]
    print(f'  [precheck §2.4] PASS 床: {pass_floors} ({time.time()-t0:.1f}s)')
    return floor_pass


def run_all_prechecks():
    """全 precheck を実行 (致命的 FAIL なら raise、§2.4 は床ごと PASS dict 返す)"""
    print('=' * 60)
    print('v1112 Stage 1 redo — 測定器点検 (本実行前必須)')
    print('=' * 60)
    precheck_shift_sensitivity()
    precheck_no_same_seed()
    precheck_seed_diversity()
    floor_pass = precheck_floor_structures()
    print('=' * 60)
    print(f'全 precheck PASS — 本実行に進む (PASS 床: '
          f'{[k for k, v in floor_pass.items() if v]})')
    print('=' * 60)
    return floor_pass


# === Worker (Pool で起動) ===

def _worker(args):
    sa, cond = args
    pid = os.getpid()
    print(f'  [PID {pid}] start atom={sa} cond={cond}', flush=True)
    t0 = time.time()
    for p in PATHS:
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))

    observer = ResonanceObserver()

    if cond == 'active_pair':
        # 独立 seed Atom + Other 並走、両系 occupancy
        atom = _build_engine_local(sa)
        other = _build_engine_local(OTHER_SEED_FIXED)
        for w in range(WINDOWS):
            atom.step_window(steps=WINDOW_STEPS)
            other.step_window(steps=WINDOW_STEPS)
            occ_a = list(atom.virtual.occupancy)
            occ_o = list(other.virtual.occupancy)
            observer.observe(occ_a, occ_o)

    elif cond == 'self_permute_floor':
        # 案 A: Atom + 実機 occ の bin permute 床 (値分布保持、phase 帯対応破壊)
        atom = _build_engine_local(sa)
        for w in range(WINDOWS):
            atom.step_window(steps=WINDOW_STEPS)
            occ_a_np = np.asarray(atom.virtual.occupancy, dtype=float)
            state_seed = sa * 100003 + w * 7919
            occ_p = list(permute_phase_occupancy(occ_a_np, state_seed))
            observer.observe(list(occ_a_np), occ_p)

    elif cond == 'self_krandom_floor':
        # 案 B: Atom + k 個 random 非ゼロ床 (active bin 数を実機に揃える)
        atom = _build_engine_local(sa)
        for w in range(WINDOWS):
            atom.step_window(steps=WINDOW_STEPS)
            occ_a_np = np.asarray(atom.virtual.occupancy, dtype=float)
            state_seed = sa * 100003 + w * 7919
            occ_kr = list(krandom_phase_occupancy(occ_a_np, state_seed))
            observer.observe(list(occ_a_np), occ_kr)

    elif cond == 'phase_shifted':
        # 独立 seed Atom + Other、Other occ を bin π shift (位相反転対照)
        atom = _build_engine_local(sa)
        other = _build_engine_local(OTHER_SEED_FIXED)
        for w in range(WINDOWS):
            atom.step_window(steps=WINDOW_STEPS)
            other.step_window(steps=WINDOW_STEPS)
            occ_a = list(atom.virtual.occupancy)
            occ_o_raw = list(other.virtual.occupancy)
            occ_o_shifted = list(np.roll(occ_o_raw, N_BINS // 2))
            observer.observe(occ_a, occ_o_shifted)
    else:
        raise ValueError(f'Unknown cond: {cond}')

    summary = observer.summary()
    dt = time.time() - t0
    print(f'  [PID {pid}] done atom={sa} cond={cond} ({dt:.0f}s) '
          f'diag_d0={summary["diag_d0"]:.0f} '
          f'diag_d1={summary["diag_d1"]:.0f} '
          f'diag_d3={summary["diag_d3"]:.0f}',
          flush=True)
    return {
        'atom_seed': sa, 'condition': cond,
        'cooc_count_flat': observer.cooc_count.flatten().tolist(),
        **summary,
    }


def make_tasks(conditions):
    tasks = []
    for sa in ATOM_SEEDS:
        for cond in conditions:
            tasks.append((sa, cond))
    return tasks


def main():
    print('=== v1112 Stage 1 作り直し — 共鳴 CID が立つか (測定器組み直し版、両床対照) ===\n')
    print(f'  ATOM_SEEDS={ATOM_SEEDS}, OTHER_SEED_FIXED={OTHER_SEED_FIXED} (別 seed)')
    print(f'  WINDOW_STEPS={WINDOW_STEPS}, WINDOWS={WINDOWS}')
    print(f'  conditions base: {CONDITIONS_BASE}')
    print(f'  主指標: diagonal_mass(delta={DELTAS}) (近傍含む)')
    print(f'  参考指標: total_cooc, N_rcid, max_cooc (判定外、記録のみ)')

    # === 測定器点検 (本実行前必須) ===
    floor_pass = run_all_prechecks()

    # PASS した床のみ本実行に含める (active_pair と phase_shifted は常に含む)
    conditions = ['active_pair'] + \
                 [f for f in ['self_permute_floor', 'self_krandom_floor'] if floor_pass[f]] + \
                 ['phase_shifted']
    tasks = make_tasks(conditions)
    n_atom = len(ATOM_SEEDS)
    n_cond = len(conditions)
    print(f'\nTasks: {len(tasks)} = {n_atom} atom × {n_cond} conditions ({conditions})')
    n_workers = min(len(tasks), 12)
    print(f'並列: Pool({n_workers}) で 1 Wave\n')

    t_main = time.time()
    with Pool(processes=n_workers) as pool:
        results = pool.map(_worker, tasks)

    # === 集計 ===
    summary_rows = []
    for r in results:
        summary_rows.append({
            'atom_seed': r['atom_seed'],
            'condition': r['condition'],
            # 主指標
            'diag_d0': r['diag_d0'],
            'diag_d1': r['diag_d1'],
            'diag_d3': r['diag_d3'],
            # 参考指標
            'total_cooc': r['total_cooc'],
            'n_active_pairs': r['n_active_pairs'],
            'max_cooc': r['max_cooc'],
            'mean_cooc_nonzero': r['mean_cooc_nonzero'],
        })
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_parquet(OUT_DIR / 'summary.parquet', index=False)

    # cooc 行列
    cooc_rows = [{'atom_seed': r['atom_seed'], 'condition': r['condition'],
                  'cooc_count_flat': r['cooc_count_flat']} for r in results]
    pd.DataFrame(cooc_rows).to_parquet(OUT_DIR / 'cooc_matrix.parquet', index=False)

    # window 推移 (diagonal_d0)
    prog_rows = []
    for r in results:
        for w, d in enumerate(r['diag_per_window']):
            prog_rows.append({
                'atom_seed': r['atom_seed'], 'condition': r['condition'],
                'window': w, 'diag_d0': d,
            })
    pd.DataFrame(prog_rows).to_parquet(OUT_DIR / 'progression.parquet', index=False)

    # === 観察事実 (主指標 diagonal、3 条件大小、factor なし) ===
    print('\n=== 主指標 diagonal_d0 (同 bin 同期、対角 raw) ===')
    pivot_d0 = summary_df.pivot(index='atom_seed', columns='condition', values='diag_d0')
    print(pivot_d0.to_string())
    print('\n=== 主指標 diagonal_d1 (±1 bin 近傍含む) ===')
    pivot_d1 = summary_df.pivot(index='atom_seed', columns='condition', values='diag_d1')
    print(pivot_d1.to_string())
    print('\n=== 主指標 diagonal_d3 (±3 bin 近傍含む) ===')
    pivot_d3 = summary_df.pivot(index='atom_seed', columns='condition', values='diag_d3')
    print(pivot_d3.to_string())

    # 参考指標 (判定外、記録のみ)
    print('\n=== 参考: total_cooc (shift 不変、判定外) ===')
    print(summary_df.pivot(index='atom_seed', columns='condition',
                           values='total_cooc').to_string())

    # === Stage 1 出口判定 (主指標 diagonal、大小のみ、factor なし) ===
    print('\n=== Stage 1 出口判定 (主指標 diagonal、大小、factor なし) ===')
    n_atom = len(ATOM_SEEDS)
    # PASS 床を判定対象に
    floor_conds = [f for f in ['self_permute_floor', 'self_krandom_floor']
                   if f in conditions]
    judgments = {}
    for delta_label, pivot in [('d0', pivot_d0), ('d1', pivot_d1), ('d3', pivot_d3)]:
        gt_shifted_count = 0
        gt_floor_counts = {f: 0 for f in floor_conds}
        per_atom = []
        for sa in ATOM_SEEDS:
            active = float(pivot.loc[sa, 'active_pair'])
            shifted = float(pivot.loc[sa, 'phase_shifted'])
            floors = {f: float(pivot.loc[sa, f]) for f in floor_conds}
            gt_shifted = active > shifted
            gt_floors = {f: active > floors[f] for f in floor_conds}
            if gt_shifted: gt_shifted_count += 1
            for f in floor_conds:
                if gt_floors[f]: gt_floor_counts[f] += 1
            per_atom.append({
                'atom_seed': sa, 'active': active, 'shifted': shifted,
                **{f'floor_{f}': floors[f] for f in floor_conds},
                'gt_shifted': gt_shifted,
                **{f'gt_{f}': gt_floors[f] for f in floor_conds},
            })
            floor_str = ' '.join(f'{f}={floors[f]:.0f}({gt_floors[f]})' for f in floor_conds)
            print(f'  [diag_{delta_label}] atom={sa}: '
                  f'active={active:.0f} shifted={shifted:.0f} {floor_str} '
                  f'active>shifted={gt_shifted}')
        judgments[delta_label] = {
            'gt_shifted': gt_shifted_count,
            **{f'gt_{f}': gt_floor_counts[f] for f in floor_conds},
            'per_atom': per_atom,
        }
        floor_summary = ' '.join(f'active>{f}: {gt_floor_counts[f]}/{n_atom}'
                                  for f in floor_conds)
        print(f'  [diag_{delta_label}] active>shifted: {gt_shifted_count}/{n_atom}, '
              f'{floor_summary}')

    # 全 δ で全床判定が 3/3 揃うか
    all_delta_3_3 = all(
        judgments[d]['gt_shifted'] == n_atom and
        all(judgments[d][f'gt_{f}'] == n_atom for f in floor_conds)
        for d in ['d0', 'd1', 'd3']
    )
    print(f'\n  全 δ ({DELTAS}) × 全床 ({floor_conds}) で 3/3 揃う: {all_delta_3_3}')
    if all_delta_3_3:
        print('  → ループの外に独立軸が立つ候補が観察された (言葉縛り遵守)')
    else:
        # 床ごとの揃い具合を確認
        per_floor_3_3 = {}
        for f in floor_conds:
            per_floor_3_3[f] = all(
                judgments[d]['gt_shifted'] == n_atom and
                judgments[d][f'gt_{f}'] == n_atom
                for d in ['d0', 'd1', 'd3']
            )
        passed_floors = [f for f, ok in per_floor_3_3.items() if ok]
        if passed_floors:
            print(f'  → 揃う床: {passed_floors} (床選択依存、観察事実として記録)')
        else:
            print('  → 揃わず = Stage 1 不成立 (測れた上での不成立、構造事実として記録)')

    # atom=100 突出読み (Taka 詰め 2)
    print('\n=== atom 別 diagonal_d0 (active_pair) 相対比較 (Taka 詰め 2) ===')
    diag_per_atom = pivot_d0['active_pair'].to_dict()
    print(f'  atom=42: {diag_per_atom[42]:.0f}')
    print(f'  atom=100: {diag_per_atom[100]:.0f}')
    print(f'  atom=200: {diag_per_atom[200]:.0f}')
    if diag_per_atom[100] > 2 * max(diag_per_atom[42], diag_per_atom[200]):
        print('  → atom=100 が他 atom より明確に突出 = 別の構造的原因 (同 seed 並走でない)')
    elif diag_per_atom[100] > 1.5 * np.mean([diag_per_atom[42], diag_per_atom[200]]):
        print('  → atom=100 がやや突出 (1.5x 程度)')
    else:
        print('  → atom=100 が他 atom と同程度 = 同 seed 並走汚染が原因だったことが確認')

    summary_json = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'design': 'v1112_stage1_redo',
        'ATOM_SEEDS': ATOM_SEEDS, 'OTHER_SEED_FIXED': OTHER_SEED_FIXED,
        'WINDOW_STEPS': WINDOW_STEPS, 'WINDOWS': WINDOWS,
        'DELTAS': DELTAS,
        'conditions_run': conditions,
        'floor_pass_precheck': {k: bool(v) for k, v in floor_pass.items()},
        'judgments': judgments,
        'all_delta_3_3': bool(all_delta_3_3),
        'atom_100_diag_d0': float(diag_per_atom.get(100, 0)),
        'atom_other_diag_d0_mean': float(np.mean([diag_per_atom.get(42, 0),
                                                   diag_per_atom.get(200, 0)])),
        'total_sec': time.time() - t_main,
    }
    (OUT_DIR / 'summary.json').write_text(
        json.dumps(summary_json, indent=2, ensure_ascii=False))
    print(f'\n=== v1112 Stage 1 redo 完了 total {time.time()-t_main:.1f}s ===')


if __name__ == '__main__':
    main()
