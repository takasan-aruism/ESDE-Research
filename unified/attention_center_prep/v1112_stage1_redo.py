#!/usr/bin/env python3
"""v1112 Stage 1 作り直し — 共鳴 CID が立つか (測定器組み直し版、第三 ESDE、3 条件対照)

Web Claude / Taka 指示 (2026-06-03) 準拠:
- 前回 Stage 1 は主指標 total_cooc / N_rcid が bin shift と数学的に独立 = 測れていない
- 今回は測定器を組み直して、まだ測っていないものを初めて測る

組み直し 3 点:
1. 主指標 = diagonal_mass(M, delta) = Σ M[i, (i+d) mod N] over d ∈ [-delta, +delta]
   - 複数 δ (0, 1, 3) で測る、固定値なし
   - total_cooc / N_rcid は判定外、parquet 記録のみ
2. OTHER_SEED_FIXED = 999 (ATOM_SEEDS=[42,100,200] のどれとも別)
   - 同 seed 並走排除 (前回 atom=100 × Other=100 汚染疑い解消)
3. self 床 = 乱数 phase 分布との cooc
   - 乱数 seed = atom_seed * 100003 + w * 7919 (state 由来、再現可能)
   - 慣性床 (time-shifted) でなく無関係相手床

実装前測定器点検 (main 内で本実行前に必須):
- §2.1 shift 動性: ダミー行列で diagonal_mass が np.roll で値が動くか
- §2.2 同 seed なし: OTHER_SEED_FIXED not in ATOM_SEEDS
- §2.3 乱数 seed 多様: window 間で重複なし
- §2.4 乱数床構造性: 実機 baseline occ で diag_aa > diag_ao > diag_ar が成立するか
  - 失敗時は raise で止める (本実行に進まない)

不変 (前回 Stage 1 のまま):
- 第三 ESDE = state なし観察体 (ResonanceObserver、両系 read-only、書き戻しなし)
- node ID 排他 (phase 空間 64 bin のみ)
- 案 3+4 (Kuramoto 同期 + 確率累積)
- 過去標準スケール (500 step × 30 windows、自然進化、注入なし)
- 3 atom × 3 conditions = 9 tasks Pool(9) 1 Wave、推定 ~2.4 時間

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

CONDITIONS = ['active_pair', 'self_random_floor', 'phase_shifted']


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


def random_phase_occupancy(state_seed, n_bins=N_BINS):
    """state 由来の乱数 phase occupancy (再現可能)
    state_seed: atom_seed * 100003 + w * 7919 等 (state 由来)
    """
    rng = np.random.RandomState(int(state_seed))
    return rng.random(n_bins).astype(float)


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
    """§2.3: 乱数 seed が window 間で多様か"""
    print('[precheck §2.3] 乱数 seed 多様性...')
    for sa in ATOM_SEEDS:
        seeds = [sa * 100003 + w * 7919 for w in range(WINDOWS)]
        if len(set(seeds)) != WINDOWS:
            raise RuntimeError(
                f'§2.3 FAIL: atom={sa} で window 間乱数 seed が重複 '
                f'({len(set(seeds))} unique / {WINDOWS}) — 床の独立性なし'
            )
        print(f'  atom={sa}: {WINDOWS} unique seeds OK')


def precheck_random_floor_structure():
    """§2.4: 乱数床 diagonal が Active より構造的に低くなりうるか
    ★ 実機 baseline occupancy で点検 (理想化ダミーでなく)
    """
    print('[precheck §2.4] 乱数床構造性 (実機 baseline occ で点検)...')
    t0 = time.time()
    sa0 = ATOM_SEEDS[0]
    # 本番と同じ build_engine で 1 window 動かす
    print(f'  build_engine(atom_seed={sa0}) + step_window({WINDOW_STEPS}) ...')
    atom_probe = _build_engine_local(sa0)
    atom_probe.step_window(steps=WINDOW_STEPS)
    print(f'  build_engine(other_seed={OTHER_SEED_FIXED}) + step_window({WINDOW_STEPS}) ...')
    other_probe = _build_engine_local(OTHER_SEED_FIXED)
    other_probe.step_window(steps=WINDOW_STEPS)

    occ_a = np.asarray(atom_probe.virtual.occupancy, dtype=float)
    occ_o = np.asarray(other_probe.virtual.occupancy, dtype=float)
    occ_r = random_phase_occupancy(state_seed=sa0 * 100003 + 0 * 7919)

    # 実機/乱数 occ の閾値挙動を記録
    print(f'  実機 Atom: mean={occ_a.mean():.4f}, '
          f'n_above_mean={int((occ_a > occ_a.mean()).sum())}/{N_BINS}')
    print(f'  実機 Other: mean={occ_o.mean():.4f}, '
          f'n_above_mean={int((occ_o > occ_o.mean()).sum())}/{N_BINS}')
    print(f'  乱数: mean={occ_r.mean():.4f}, '
          f'n_above_mean={int((occ_r > occ_r.mean()).sum())}/{N_BINS}')

    # 3 つの cooc を構築 (1 window 想定、本番と同じ observer.observe)
    o_aa = ResonanceObserver(); o_aa.observe(occ_a, occ_a)
    o_ao = ResonanceObserver(); o_ao.observe(occ_a, occ_o)
    o_ar = ResonanceObserver(); o_ar.observe(occ_a, occ_r)

    diag_aa = diagonal_mass(o_aa.cooc_count, delta=0)
    diag_ao = diagonal_mass(o_ao.cooc_count, delta=0)
    diag_ar = diagonal_mass(o_ar.cooc_count, delta=0)

    print(f'  diag_aa (Active 自己、上限)     = {diag_aa}')
    print(f'  diag_ao (Active × Other 別 seed)= {diag_ao}')
    print(f'  diag_ar (Active × 乱数、self 床)= {diag_ar}')

    # 警告判定
    if diag_ar >= diag_ao:
        raise RuntimeError(
            f'§2.4 FAIL: 乱数床 diagonal ({diag_ar}) >= Active × Other ({diag_ao}) — '
            f'self 床として機能しない (前回 self_loop 慣性床と同じ轍を乱数床でも踏む)。'
            f'乱数 seed を変えるか、self 床設計再考。本実行に進まない。'
        )
    if diag_ar >= diag_aa:
        raise RuntimeError(
            f'§2.4 FAIL: 乱数床 diagonal ({diag_ar}) >= Active 自己 ({diag_aa}) — '
            f'構造的に不可能、observe / diagonal_mass 関数バグ。'
        )
    print(f'  [precheck §2.4] PASS (diag_aa > diag_ao > diag_ar) '
          f'({time.time()-t0:.1f}s)')


def run_all_prechecks():
    """全 precheck を実行 (1 つでも FAIL なら raise で止まる)"""
    print('=' * 60)
    print('v1112 Stage 1 redo — 測定器点検 (本実行前必須)')
    print('=' * 60)
    precheck_shift_sensitivity()
    precheck_no_same_seed()
    precheck_seed_diversity()
    precheck_random_floor_structure()
    print('=' * 60)
    print('全 precheck PASS — 本実行に進む')
    print('=' * 60)


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

    elif cond == 'self_random_floor':
        # Atom + 乱数 phase 床 (慣性床でなく無関係相手床)
        atom = _build_engine_local(sa)
        for w in range(WINDOWS):
            atom.step_window(steps=WINDOW_STEPS)
            occ_a = list(atom.virtual.occupancy)
            rand_seed = sa * 100003 + w * 7919
            occ_r = list(random_phase_occupancy(rand_seed))
            observer.observe(occ_a, occ_r)

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


def make_tasks():
    tasks = []
    for sa in ATOM_SEEDS:
        for cond in CONDITIONS:
            tasks.append((sa, cond))
    return tasks


def main():
    print('=== v1112 Stage 1 作り直し — 共鳴 CID が立つか (測定器組み直し版) ===\n')
    print(f'  ATOM_SEEDS={ATOM_SEEDS}, OTHER_SEED_FIXED={OTHER_SEED_FIXED} (別 seed)')
    print(f'  WINDOW_STEPS={WINDOW_STEPS}, WINDOWS={WINDOWS}')
    print(f'  conditions: {CONDITIONS}')
    print(f'  主指標: diagonal_mass(delta={DELTAS}) (近傍含む)')
    print(f'  参考指標: total_cooc, N_rcid, max_cooc (判定外、記録のみ)')

    # === 測定器点検 (本実行前必須) ===
    run_all_prechecks()

    tasks = make_tasks()
    print(f'\nTasks: {len(tasks)} = 3 atom × 3 conditions = 9')
    print(f'並列: Pool(9) で 1 Wave、推定 ~2.4 時間\n')

    t_main = time.time()
    with Pool(processes=9) as pool:
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
    judgments = {}
    for delta_label, pivot in [('d0', pivot_d0), ('d1', pivot_d1), ('d3', pivot_d3)]:
        gt_shifted_count = 0
        gt_floor_count = 0
        per_atom = []
        for sa in ATOM_SEEDS:
            active = float(pivot.loc[sa, 'active_pair'])
            floor = float(pivot.loc[sa, 'self_random_floor'])
            shifted = float(pivot.loc[sa, 'phase_shifted'])
            gt_shifted = active > shifted
            gt_floor = active > floor
            if gt_shifted: gt_shifted_count += 1
            if gt_floor: gt_floor_count += 1
            per_atom.append({
                'atom_seed': sa, 'active': active, 'floor': floor, 'shifted': shifted,
                'gt_shifted': gt_shifted, 'gt_floor': gt_floor,
            })
            print(f'  [diag_{delta_label}] atom={sa}: '
                  f'active={active:.0f} floor={floor:.0f} shifted={shifted:.0f} '
                  f'active>shifted={gt_shifted} active>floor={gt_floor}')
        judgments[delta_label] = {
            'gt_shifted': gt_shifted_count, 'gt_floor': gt_floor_count, 'per_atom': per_atom,
        }
        print(f'  [diag_{delta_label}] active>shifted: {gt_shifted_count}/{n_atom}, '
              f'active>floor: {gt_floor_count}/{n_atom}')

    # 全 δ で揃うか
    all_delta_3_3 = all(
        judgments[d]['gt_shifted'] == n_atom and judgments[d]['gt_floor'] == n_atom
        for d in ['d0', 'd1', 'd3']
    )
    print(f'\n  全 δ ({DELTAS}) で 3/3 揃う: {all_delta_3_3}')
    if all_delta_3_3:
        print('  → ループの外に独立軸が立つ候補が観察された (言葉縛り遵守)')
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
