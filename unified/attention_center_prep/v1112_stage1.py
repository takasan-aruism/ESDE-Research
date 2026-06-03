#!/usr/bin/env python3
"""v1112 Stage 1 — 共鳴 CID が立つか (第三 ESDE、3 条件対照)

Web Claude v1112 Stage 1 設計準拠:
- 第三 ESDE = state なし観察体 (ResonanceObserver class)、両系を 1 bit も書き換えない
- 案 3+4: Kuramoto 同期 (phase 空間 64 bin) + 確率累積で共鳴 CID 化
- 3 条件: Active Pair / Self Loop / Phase Shifted (位相 π ずらし)
- **node ID 完全排他**: 両系から渡るのは bin index のみ
- 対照比較: 3 条件の大小のみ、factor なし
- 過去標準スケール: 500 step × 30 windows、自然進化 (注入なし、書き戻しなし)

過去遺産流用 ([[reference-legacy-treasures]]):
- v10.2 n_core 別層化哲学 (集団平均回避、layered observation)
- v9.18 main run スケール (500 × 30)
- VirtualLayer occupancy (64 bins = phase 空間)
- kuramoto_order_parameter 哲学 (phase 同期検出)

構成:
- 3 atom × 3 conditions = 9 tasks Pool(9) 1 Wave、推定 ~3.5 時間
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
OUT_DIR = STAGE5 / 'run_v1112_stage1'
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
OTHER_SEED_FIXED = 100  # Stage 1 smoke は Other=100 固定 (条件別比較が主)
WINDOW_STEPS = 500
MATURATION_WINDOWS = 10
TRACKING_WINDOWS = 20
WINDOWS = MATURATION_WINDOWS + TRACKING_WINDOWS  # 30
N_BINS = 64
HISTORY_LEN = 10  # 履歴 (累積判定用)、過去標準で 10 windows ぶん


def _worker(args):
    sa, cond = args
    pid = os.getpid()
    print(f'  [PID {pid}] start atom={sa} cond={cond}', flush=True)
    t0 = time.time()
    for p in PATHS:
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    from esde_v82_engine import V82Engine, V82EncapsulationParams, V82_N
    from virtual_layer_v9 import VirtualLayer as VirtualLayerV9

    def build_engine(seed):
        encap = V82EncapsulationParams(stress_enabled=True, virtual_enabled=True)
        engine = V82Engine(seed=seed, N=V82_N, encap_params=encap)
        engine.virtual = VirtualLayerV9(feedback_gamma=0.10,
                                         feedback_clamp=(0.8, 1.2))
        engine.virtual.torque_order = "age"
        engine.virtual.deviation_enabled = True
        engine.virtual.semantic_gravity_enabled = True
        engine.run_injection()
        return engine

    # === 第三 ESDE = 軽量観察体 (state なし、両系を read-only) ===
    class ResonanceObserver:
        """phase 空間 (64 bin) のみで両系の同時立ちを観察、累積カウンタ"""
        def __init__(self, n_bins=N_BINS):
            self.N_BINS = n_bins
            # cooc_count[a, b] = bin a (Atom) と bin b (Other) の同時立ち累積回数
            self.cooc_count = np.zeros((n_bins, n_bins), dtype=np.int64)
            # 履歴 (確率累積用)
            self.history = []
            # window 別 N_rcid 推移 (Stage 1 で時系列観察)
            self.n_rcid_per_window = []

        def observe(self, occ_a, occ_o):
            """両系 occupancy を読んで同時立ち累積
            occ_a, occ_o: list/array of N_BINS floats
            ※ node ID なし、bin index のみ
            """
            occ_a = np.asarray(occ_a, dtype=float)
            occ_o = np.asarray(occ_o, dtype=float)
            # 各系の閾値は state 由来 (mean occupancy)
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
            # 現時点での N_rcid (累積>=1 の bin pair 数、生)
            n_rcid = int(np.sum(self.cooc_count > 0))
            self.n_rcid_per_window.append(n_rcid)

        def summary(self):
            nonzero = self.cooc_count[self.cooc_count > 0]
            return {
                'total_cooc': int(self.cooc_count.sum()),  # N_rcid raw (大小用)
                'n_active_pairs': int(np.sum(self.cooc_count > 0)),  # 立った bin pair 数
                'max_cooc': int(self.cooc_count.max()) if self.cooc_count.size > 0 else 0,
                'mean_cooc_nonzero': float(nonzero.mean()) if len(nonzero) > 0 else 0.0,
                'n_rcid_per_window': self.n_rcid_per_window,
            }

    observer = ResonanceObserver()

    # ★ 3 条件の進化と観察 ===
    if cond == 'active_pair':
        # 独立 seed の Atom + Other を毎 window 並走、両系の occupancy で観察
        atom = build_engine(sa)
        other = build_engine(OTHER_SEED_FIXED)
        for w in range(WINDOWS):
            atom.step_window(steps=WINDOW_STEPS)
            other.step_window(steps=WINDOW_STEPS)
            occ_a = list(atom.virtual.occupancy)
            occ_o = list(other.virtual.occupancy)
            observer.observe(occ_a, occ_o)
    elif cond == 'self_loop':
        # Atom 系のみ。time-shifted self で「Atom 内の時間的自己同期」を見る
        atom = build_engine(sa)
        occ_history = []
        for w in range(WINDOWS):
            atom.step_window(steps=WINDOW_STEPS)
            occ_current = list(atom.virtual.occupancy)
            occ_history.append(occ_current)
            if w >= 1:
                # 前 window occ と現在 occ の cooc (= 自己時間 1 step 同期)
                observer.observe(occ_history[w-1], occ_current)
    elif cond == 'phase_shifted':
        # 独立 seed の Atom + Other、ただし Other occupancy を bin shift (π 位相反転)
        atom = build_engine(sa)
        other = build_engine(OTHER_SEED_FIXED)
        for w in range(WINDOWS):
            atom.step_window(steps=WINDOW_STEPS)
            other.step_window(steps=WINDOW_STEPS)
            occ_a = list(atom.virtual.occupancy)
            occ_o_raw = list(other.virtual.occupancy)
            # bin shift で位相 π 反転 (Phase Shifted、最重要対照)
            occ_o_shifted = list(np.roll(occ_o_raw, N_BINS // 2))
            observer.observe(occ_a, occ_o_shifted)
    else:
        raise ValueError(f'Unknown cond: {cond}')

    summary = observer.summary()
    dt = time.time() - t0
    print(f'  [PID {pid}] done atom={sa} cond={cond} ({dt:.0f}s) '
          f'N_rcid={summary["n_active_pairs"]} total_cooc={summary["total_cooc"]}',
          flush=True)
    return {
        'atom_seed': sa, 'condition': cond,
        'cooc_count_flat': observer.cooc_count.flatten().tolist(),
        **summary,
    }


def make_tasks():
    tasks = []
    for sa in ATOM_SEEDS:
        for cond in ['active_pair', 'self_loop', 'phase_shifted']:
            tasks.append((sa, cond))
    return tasks


def main():
    print('=== v1112 Stage 1 — 共鳴 CID が立つか (3 条件対照) ===\n')
    print(f'  ATOM_SEEDS={ATOM_SEEDS}, OTHER (固定)={OTHER_SEED_FIXED}')
    print(f'  WINDOW_STEPS={WINDOW_STEPS}, WINDOWS={WINDOWS}')
    print(f'  conditions: active_pair / self_loop / phase_shifted')
    tasks = make_tasks()
    print(f'  Tasks: {len(tasks)} = 3 atom × 3 conditions = 9')
    print(f'  並列: Pool(9) で 1 Wave、推定 ~3.5 時間\n')

    t_main = time.time()
    with Pool(processes=9) as pool:
        results = pool.map(_worker, tasks)

    # 集計
    summary_rows = []
    for r in results:
        summary_rows.append({
            'atom_seed': r['atom_seed'],
            'condition': r['condition'],
            'total_cooc': r['total_cooc'],
            'n_active_pairs': r['n_active_pairs'],
            'max_cooc': r['max_cooc'],
            'mean_cooc_nonzero': r['mean_cooc_nonzero'],
        })
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_parquet(OUT_DIR / 'summary.parquet', index=False)

    # cooc_count 行列保存
    cooc_rows = []
    for r in results:
        cooc_rows.append({
            'atom_seed': r['atom_seed'],
            'condition': r['condition'],
            'cooc_count_flat': r['cooc_count_flat'],
        })
    cooc_df = pd.DataFrame(cooc_rows)
    cooc_df.to_parquet(OUT_DIR / 'cooc_matrix.parquet', index=False)

    # window 別 N_rcid 推移
    prog_rows = []
    for r in results:
        for w, n in enumerate(r['n_rcid_per_window']):
            prog_rows.append({
                'atom_seed': r['atom_seed'],
                'condition': r['condition'],
                'window': w, 'n_rcid': n,
            })
    prog_df = pd.DataFrame(prog_rows)
    prog_df.to_parquet(OUT_DIR / 'progression.parquet', index=False)

    # === 観察事実 (判定置かない、3 条件大小のみ) ===
    print('\n=== 3 条件の大小比較 (atom 別、N_rcid raw、factor なし) ===')
    pivot = summary_df.pivot(index='atom_seed', columns='condition',
                              values='total_cooc')
    print(pivot.to_string())
    print()
    pivot_n = summary_df.pivot(index='atom_seed', columns='condition',
                                values='n_active_pairs')
    print('立った bin pair 数 (n_active_pairs):')
    print(pivot_n.to_string())

    # Stage 1 出口判定 (大小のみ、factor なし)
    print('\n=== Stage 1 出口判定 (大小、factor なし) ===')
    n_atom = len(ATOM_SEEDS)
    n_active_gt_shifted = 0
    n_active_gt_self = 0
    for sa in ATOM_SEEDS:
        active = float(pivot.loc[sa, 'active_pair'])
        self_v = float(pivot.loc[sa, 'self_loop'])
        shifted = float(pivot.loc[sa, 'phase_shifted'])
        gt_shifted = active > shifted
        gt_self = active > self_v
        if gt_shifted: n_active_gt_shifted += 1
        if gt_self: n_active_gt_self += 1
        print(f'  atom={sa}: active={active:.0f} self={self_v:.0f} '
              f'shifted={shifted:.0f} '
              f'active>shifted={gt_shifted} active>self={gt_self}')
    print(f'\n  3 atom 共通で active > phase_shifted: {n_active_gt_shifted}/{n_atom}')
    print(f'  3 atom 共通で active > self_loop:     {n_active_gt_self}/{n_atom}')
    if n_active_gt_shifted == n_atom and n_active_gt_self == n_atom:
        print('  → 3/3 揃う = ループの外に独立軸が立つ候補が観察された')
    else:
        print('  → 揃わず = Stage 1 出口不成立 (構造事実として記録)')

    summary_json = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'design': 'v1112_stage1',
        'ATOM_SEEDS': ATOM_SEEDS, 'OTHER_SEED_FIXED': OTHER_SEED_FIXED,
        'WINDOW_STEPS': WINDOW_STEPS, 'WINDOWS': WINDOWS,
        'n_active_gt_shifted': n_active_gt_shifted,
        'n_active_gt_self': n_active_gt_self,
        'total_sec': time.time() - t_main,
    }
    (OUT_DIR / 'summary.json').write_text(
        json.dumps(summary_json, indent=2, ensure_ascii=False))
    print(f'\n=== v1112 Stage 1 完了 total {time.time()-t_main:.1f}s ===')


if __name__ == '__main__':
    main()
