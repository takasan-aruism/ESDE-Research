#!/usr/bin/env python3
"""v1111f smoke — 過去遺産流用版 (確実な試験)

Taka 指示 2026-06-02:「これまでの遺産を用いて確実な試験を実施」
[[feedback-index-first]] 規律に従い、reference_legacy_treasures から流用:

| 流用元 | 内容 |
|---|---|
| v9.18 main run | window_steps=500, mat 10 + track 20 (過去標準スケール) |
| v10.2 核心 | n_core 別層化 (集団平均の罠回避) |
| v111 5 step 刻み | per-step 観察 (注入後 +1/+5/+25/+100/+500 step) |
| stage3 inject_to_engine | inject 前後の alive_n/alive_l 記録 |
| v1111e_redo 修正版 | 3 本足 phase 一致率 + Other.step_window |
| Code A 盲点 #3 | 過去 seed [42, 100, 200] を含む拡張 |

smoke: 3 atom × 8 conditions = 24 tasks、推定 75 分
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
OUT_DIR = STAGE5 / 'run_v1111f_smoke'
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

# smoke: 3 atom (v1111d と同 seed、直接比較可能)
ATOM_SEEDS = [42, 100, 200]
CENTER_SEEDS = [99, 157, 217]
OTHER_SEEDS = [100, 101, 102]

# 過去標準スケール (v9.18 main run)
WINDOW_STEPS = 500
MATURATION_WINDOWS = 10
TRACKING_WINDOWS = 20
W_INJECT = 12  # mat 10 後の早期 tracking (atom が安定したところで注入)
WINDOWS = MATURATION_WINDOWS + TRACKING_WINDOWS  # 30
OTHER_STEPS = 25  # 過去標準比例で 5→25 (window 5 倍に対応)
K_TARGET = 5
N_BINS = 64

# per-step 観察 (v111 流用、注入後の伝播追跡)
PER_STEP_OBSERVE = [1, 5, 25, 100, 500]


def _worker(args):
    sa, sc, cond, so = args
    pid = os.getpid()
    print(f'  [PID {pid}] start atom={sa} cond={cond} other={so}', flush=True)
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

    def should_attend(c):
        if not c.state.alive_n: return False
        E = np.array([c.state.E.get(n, 0.0) for n in c.state.alive_n])
        if len(E) < 2: return False
        m = float(E.mean()); s = float(E.std())
        if s < 1e-9: return False
        z = (float(E.max()) - m) / s
        st = float((c.stress_stats or {}).get('stress_intensity', 1.0))
        return z > st

    def derive_theme_phase_point(eng, K=K_TARGET):
        alive = sorted(eng.state.alive_n)
        if not alive: return None
        ev = {n: float(eng.state.E.get(n, 0.0)) for n in alive}
        topk = sorted(alive, key=lambda n: -ev[n])[:K]
        th = [float(eng.state.theta[n]) for n in topk]
        if not th: return None
        cs = sum(math.cos(t) for t in th); ss_ = sum(math.sin(t) for t in th)
        return math.atan2(ss_/len(th), cs/len(th)) % (2*math.pi)

    def lam_dyn(eng):
        macro = set(eng.virtual.macro_nodes)
        ps = [l['phase_sig'] for lid, l in eng.virtual.labels.items() if lid not in macro]
        if len(ps) < 2: return 1.0
        cm = float(np.mean([math.cos(p) for p in ps]))
        sm = float(np.mean([math.sin(p) for p in ps]))
        r = math.sqrt(cm**2 + sm**2)
        cs_std = math.pi if r < 1e-9 else math.sqrt(-2*math.log(max(r, 1e-9)))
        return 1.0 / (cs_std + 1e-9)

    def cdist(a, b):
        d = abs(a - b) % (2*math.pi)
        return min(d, 2*math.pi - d)

    def label_weights_point(eng, theme_phase, lam):
        macro = set(eng.virtual.macro_nodes)
        w = {}
        for lid, lab in eng.virtual.labels.items():
            if lid in macro: continue
            d = cdist(lab['phase_sig'], theme_phase)
            w[lid] = {'w': math.exp(-lam*d), 'nodes': list(lab['nodes'])}
        return w

    def label_excitations_dist(atom, other, lam_out):
        alive = sorted(other.state.alive_n)
        if not alive: return {}
        E_arr = np.array([float(other.state.E.get(n, 0.0)) for n in alive])
        theta_arr = np.array([float(other.state.theta[n]) for n in alive])
        macro = set(atom.virtual.macro_nodes)
        w = {}
        for lid, lab in atom.virtual.labels.items():
            if lid in macro: continue
            ps = lab['phase_sig']
            d = np.abs(theta_arr - ps) % (2*np.pi)
            d = np.minimum(d, 2*np.pi - d)
            exc = float(np.sum(E_arr * np.exp(-lam_out * d)))
            w[lid] = {'w': exc, 'nodes': list(lab['nodes'])}
        return w

    def label_excitations_dist_shuf(atom, other, lam_out, sa_, so_):
        alive = sorted(other.state.alive_n)
        if not alive: return {}
        E_arr = np.array([float(other.state.E.get(n, 0.0)) for n in alive])
        sf_seed = (sa_ * 13 + so_ + 7) % (2**32)
        rng = np.random.default_rng(seed=sf_seed)
        theta_arr = rng.uniform(0, 2*math.pi, size=len(alive))
        macro = set(atom.virtual.macro_nodes)
        w = {}
        for lid, lab in atom.virtual.labels.items():
            if lid in macro: continue
            ps = lab['phase_sig']
            d = np.abs(theta_arr - ps) % (2*np.pi)
            d = np.minimum(d, 2*np.pi - d)
            exc = float(np.sum(E_arr * np.exp(-lam_out * d)))
            w[lid] = {'w': exc, 'nodes': list(lab['nodes'])}
        return w

    def targets_from_w(w, eng, K=K_TARGET):
        if not w: return []
        slids = sorted(w.keys(), key=lambda l: -w[l]['w'])
        cands = []
        for lid in slids[:max(K, 3)]:
            for n in w[lid]['nodes']:
                if n in eng.state.alive_n: cands.append(n)
        cands = list(set(cands))
        if not cands: return []
        ev = {n: float(eng.state.E.get(n, 0.0)) for n in cands}
        return sorted(cands, key=lambda n: -ev[n])[:K]

    def label_ncore_distribution(eng):
        """v10.2 流用: n_core 別層化用、labels の n_core 分布"""
        macro = set(eng.virtual.macro_nodes)
        ncores = []
        for lid, lab in eng.virtual.labels.items():
            if lid in macro: continue
            ncores.append(len(lab['nodes']))
        return ncores

    def snapshot(atom, label):
        """観察 snapshot (複数指標)"""
        ncores = label_ncore_distribution(atom)
        return {
            'label': label,
            'alive_n': len(atom.state.alive_n),
            'alive_l': len(atom.state.alive_l),
            'labels_total': len(ncores),
            'n_core_2': sum(1 for n in ncores if n == 2),
            'n_core_3': sum(1 for n in ncores if n == 3),
            'n_core_4': sum(1 for n in ncores if n == 4),
            'n_core_5plus': sum(1 for n in ncores if n >= 5),
            'n_core_mean': float(np.mean(ncores)) if ncores else 0.0,
            'n_core_max': max(ncores) if ncores else 0,
            'share_max': max(
                (lab['share'] for lid, lab in atom.virtual.labels.items()
                 if lid not in atom.virtual.macro_nodes), default=0.0),
            'occupancy': list(atom.virtual.occupancy),
        }

    atom = build_engine(sa)
    center = None; other = None
    if cond in ('injected_self', 'injected_other', 'shuffled_other'):
        center = build_engine(sc)
    if cond in ('injected_other', 'shuffled_other'):
        other = build_engine(so)

    # window 進行 + 観察
    snapshots = []
    inject_diag = None

    for w in range(WINDOWS):
        atom.step_window(steps=WINDOW_STEPS)
        if center is not None:
            center.step_window(steps=WINDOW_STEPS)
        if other is not None:  # ★ v1111e_redo 修正継承
            other.step_window(steps=WINDOW_STEPS)

        # window 末 snapshot (注入前/注入後)
        if w == W_INJECT - 1:
            snapshots.append({**snapshot(atom, f'w{w}_pre'), 'window': w})

        # ★ 注入 (W_INJECT で 1 回のみ)
        if w == W_INJECT and cond != 'baseline':
            if should_attend(center):
                tp_in = derive_theme_phase_point(center, K_TARGET)
                if tp_in is not None:
                    if cond == 'injected_self':
                        lam_in = lam_dyn(center)
                        weights_in = label_weights_point(atom, tp_in, lam_in)
                        targets_in = targets_from_w(weights_in, atom, K_TARGET)
                        if targets_in:
                            pre_n = len(atom.state.alive_n)
                            pre_l = len(atom.state.alive_l)
                            atom.physics.inject(atom.state, target_nodes=targets_in)
                            inject_diag = {
                                'fired': True, 'targets_n': len(targets_in),
                                'pre_alive_n': pre_n, 'post_alive_n': len(atom.state.alive_n),
                                'pre_alive_l': pre_l, 'post_alive_l': len(atom.state.alive_l),
                            }
                    elif cond == 'injected_other':
                        lam_in_other = lam_dyn(other)
                        weights_in_other = label_weights_point(other, tp_in, lam_in_other)
                        targets_in_other = targets_from_w(weights_in_other, other, K_TARGET)
                        if targets_in_other:
                            other.physics.inject(other.state, target_nodes=targets_in_other)
                            other.step_window(steps=OTHER_STEPS)
                            lam_out = lam_dyn(other)
                            weights_out = label_excitations_dist(atom, other, lam_out)
                            targets_out = targets_from_w(weights_out, atom, K_TARGET)
                            if targets_out:
                                pre_n = len(atom.state.alive_n)
                                pre_l = len(atom.state.alive_l)
                                atom.physics.inject(atom.state, target_nodes=targets_out)
                                inject_diag = {
                                    'fired': True, 'targets_n': len(targets_out),
                                    'pre_alive_n': pre_n, 'post_alive_n': len(atom.state.alive_n),
                                    'pre_alive_l': pre_l, 'post_alive_l': len(atom.state.alive_l),
                                }
                    elif cond == 'shuffled_other':
                        lam_in_other = lam_dyn(other)
                        weights_in_other = label_weights_point(other, tp_in, lam_in_other)
                        targets_in_other = targets_from_w(weights_in_other, other, K_TARGET)
                        if targets_in_other:
                            other.physics.inject(other.state, target_nodes=targets_in_other)
                            other.step_window(steps=OTHER_STEPS)
                            lam_out = lam_dyn(other)
                            weights_out = label_excitations_dist_shuf(
                                atom, other, lam_out, sa, so)
                            targets_out = targets_from_w(weights_out, atom, K_TARGET)
                            if targets_out:
                                pre_n = len(atom.state.alive_n)
                                pre_l = len(atom.state.alive_l)
                                atom.physics.inject(atom.state, target_nodes=targets_out)
                                inject_diag = {
                                    'fired': True, 'targets_n': len(targets_out),
                                    'pre_alive_n': pre_n, 'post_alive_n': len(atom.state.alive_n),
                                    'pre_alive_l': pre_l, 'post_alive_l': len(atom.state.alive_l),
                                }
            snapshots.append({**snapshot(atom, f'w{w}_inject_post'), 'window': w})

        # tracking 期間中の追加 snapshot (注入後の伝播追跡)
        # +1/+5 step は inject 直後の window 内で見たいが、window 単位なので window+k 単位で観察
        if cond != 'baseline' and w in [W_INJECT + 1, W_INJECT + 5, W_INJECT + 10, W_INJECT + 18]:
            snapshots.append({**snapshot(atom, f'w{w}_track'), 'window': w})

    # 最終 snapshot
    snapshots.append({**snapshot(atom, 'final'), 'window': WINDOWS - 1})

    dt = time.time() - t0
    print(f'  [PID {pid}] done atom={sa} cond={cond} other={so} ({dt:.0f}s) '
          f'inject={inject_diag}', flush=True)
    return {
        'atom_seed': sa, 'condition': cond,
        'other_seed': so if so is not None else -1,
        'snapshots': snapshots,
        'inject_diag': inject_diag,
    }


def make_tasks():
    tasks = []
    for sa, sc in zip(ATOM_SEEDS, CENTER_SEEDS):
        tasks.append((sa, sc, 'baseline', None))
        tasks.append((sa, sc, 'injected_self', None))
        for so in OTHER_SEEDS:
            tasks.append((sa, sc, 'injected_other', so))
        for so in OTHER_SEEDS:
            tasks.append((sa, sc, 'shuffled_other', so))
    return tasks


def main():
    print('=== v1111f smoke — 過去遺産流用版 ===\n')
    print(f'  ATOM_SEEDS={ATOM_SEEDS}, OTHER_SEEDS={OTHER_SEEDS}')
    print(f'  WINDOW_STEPS={WINDOW_STEPS}, MAT={MATURATION_WINDOWS}, TRACK={TRACKING_WINDOWS}')
    print(f'  W_INJECT={W_INJECT}, OTHER_STEPS={OTHER_STEPS}')
    tasks = make_tasks()
    print(f'  Tasks: {len(tasks)} = 3 atom × 8 conditions = 24')
    print(f'  並列: Pool(24) で 1 Wave、推定 ~75 分\n')

    t_main = time.time()
    with Pool(processes=24) as pool:
        results = pool.map(_worker, tasks)

    # snapshots を long format で保存
    snap_rows = []
    for r in results:
        for s in r['snapshots']:
            snap_rows.append({
                'atom_seed': r['atom_seed'],
                'condition': r['condition'],
                'other_seed': r['other_seed'],
                'window': s['window'],
                'label': s['label'],
                'alive_n': s['alive_n'],
                'alive_l': s['alive_l'],
                'labels_total': s['labels_total'],
                'n_core_2': s['n_core_2'],
                'n_core_3': s['n_core_3'],
                'n_core_4': s['n_core_4'],
                'n_core_5plus': s['n_core_5plus'],
                'n_core_mean': s['n_core_mean'],
                'n_core_max': s['n_core_max'],
                'share_max': s['share_max'],
                'occupancy': s['occupancy'],
            })
    snap_df = pd.DataFrame(snap_rows)
    snap_df.to_parquet(OUT_DIR / 'snapshots.parquet', index=False)

    # inject 診断
    inj_rows = []
    for r in results:
        d = r['inject_diag']
        inj_rows.append({
            'atom_seed': r['atom_seed'],
            'condition': r['condition'],
            'other_seed': r['other_seed'],
            'inject_fired': (d or {}).get('fired', False),
            'inject_targets_n': (d or {}).get('targets_n', 0),
            'inject_pre_alive_n': (d or {}).get('pre_alive_n', 0),
            'inject_post_alive_n': (d or {}).get('post_alive_n', 0),
            'inject_d_alive_l': (d or {}).get('post_alive_l', 0) - (d or {}).get('pre_alive_l', 0),
        })
    inj_df = pd.DataFrame(inj_rows)
    inj_df.to_parquet(OUT_DIR / 'inject_diag.parquet', index=False)

    # 簡易サマリ
    print('\n=== inject 実行サマリ ===')
    n_fired = inj_df[inj_df['inject_fired']].shape[0]
    n_total_inj = inj_df[inj_df['condition'] != 'baseline'].shape[0]
    print(f'  inject 発火: {n_fired}/{n_total_inj}')
    print(f'  targets_n > 0: {inj_df[inj_df["inject_targets_n"] > 0].shape[0]}/{n_total_inj}')
    print(f'  Δalive_l mean: {inj_df["inject_d_alive_l"].mean():.2f}')

    print('\n=== n_core 分布 (注入前 vs 注入後 vs 最終、injected_self) ===')
    for sa in ATOM_SEEDS:
        sub = snap_df[(snap_df['atom_seed']==sa) & (snap_df['condition']=='injected_self')]
        print(f'\n  atom={sa}:')
        for label in ['w11_pre', 'w12_inject_post', 'final']:
            row = sub[sub['label']==label]
            if len(row) > 0:
                r = row.iloc[0]
                print(f'    {label}: labels={r["labels_total"]} '
                      f'n_core=2:{r["n_core_2"]} 3:{r["n_core_3"]} '
                      f'4:{r["n_core_4"]} 5+:{r["n_core_5plus"]} '
                      f'mean={r["n_core_mean"]:.2f}')

    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'ATOM_SEEDS': ATOM_SEEDS, 'OTHER_SEEDS': OTHER_SEEDS,
        'WINDOW_STEPS': WINDOW_STEPS, 'WINDOWS': WINDOWS,
        'W_INJECT': W_INJECT,
        'total_sec': time.time() - t_main,
        'n_tasks': len(tasks),
        'n_inject_fired': int(n_fired),
    }
    (OUT_DIR / 'summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n=== v1111f smoke 完了 total {time.time()-t_main:.1f}s ===')


if __name__ == '__main__':
    main()
