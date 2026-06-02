#!/usr/bin/env python3
"""v1111f 案 B (完全自然、注入タイミングランダム化) — ESDE 本来の動態で測定

Taka 整理 2026-06-03:
- 「実験条件がそもそも想定されていたものと異なる状態で 1111d まで来てしまった」
- 「音痴の素人と同じ状態 (あえて音を外すプロの歌手とは意味が違う)」
- 「研究者としては反省すべき結果」
- 案 B (完全自然) = ESDE 本来の動態 (state-driven 自然発火、複数回注入可) で測定

過去遺産流用 ([[reference-legacy-treasures]]、[[feedback-index-first]] 遵守):
- v9.18 main run スケール: WINDOW_STEPS=500, mat 10 + track 20 = 30 windows
- v10.7 自然発火 event 哲学: state-driven、固定 timing でない (= 案 B)
- v10.2 n_core 別層化: 集団平均の罠回避
- v1111e_redo 修正版継承: 3 本足 phase 一致率 + Other.step_window
- Code A 盲点 #3 対策: ATOM_SEEDS=[42, 100, 200] (v1111d 直接比較)
- CPU 24 cores 整合: 3 atom × 8 cond = 24 tasks Pool(24) 1 Wave

構成:
- 3 atom × 8 conditions = 24 tasks
- 各 task 5.4 時間、Pool(24) で 1 Wave 完了
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
OUT_DIR = STAGE5 / 'run_v1111f_natural'
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

# 3 atom (CPU 24 cores 整合、v1111d 直接比較)
ATOM_SEEDS = [42, 100, 200]
CENTER_SEEDS = [99, 157, 217]
OTHER_SEEDS = [100, 101, 102]

# v9.18 main run 過去標準スケール
WINDOW_STEPS = 500
MATURATION_WINDOWS = 10
TRACKING_WINDOWS = 20
WINDOWS = MATURATION_WINDOWS + TRACKING_WINDOWS  # 30
OTHER_STEPS = 25  # window 5 倍に対応 (smoke 5→ 過去標準 25)
K_TARGET = 5
N_BINS = 64

# 自然発火開始 (maturation 中は注入しない、tracking に入ってから判定)
NATURAL_FIRE_START = MATURATION_WINDOWS  # window 10 から発火判定開始


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
        if not c.state.alive_n: return False, None, None
        E = np.array([c.state.E.get(n, 0.0) for n in c.state.alive_n])
        if len(E) < 2: return False, None, None
        m = float(E.mean()); s = float(E.std())
        if s < 1e-9: return False, None, None
        z = (float(E.max()) - m) / s
        st = float((c.stress_stats or {}).get('stress_intensity', 1.0))
        return z > st, z, st

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

    def label_excitations_dist_shuf(atom, other, lam_out, sa_, so_, w_idx):
        """shuffled: random theta、window ごとに違う seed (累積で random さを確保)"""
        alive = sorted(other.state.alive_n)
        if not alive: return {}
        E_arr = np.array([float(other.state.E.get(n, 0.0)) for n in alive])
        sf_seed = (sa_ * 13 + so_ + 7 + w_idx * 31) % (2**32)  # window 別
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

    def ncore_dist(eng):
        macro = set(eng.virtual.macro_nodes)
        return [len(lab['nodes']) for lid, lab in eng.virtual.labels.items()
                if lid not in macro]

    def snapshot(atom, w):
        """毎 window の観察 (n_core 別層化 + occupancy + 物理層)"""
        ncores = ncore_dist(atom)
        shares = [lab['share'] for lid, lab in atom.virtual.labels.items()
                  if lid not in atom.virtual.macro_nodes]
        return {
            'window': w,
            'alive_n': len(atom.state.alive_n),
            'alive_l': len(atom.state.alive_l),
            'labels_total': len(ncores),
            'n_core_2': sum(1 for n in ncores if n == 2),
            'n_core_3': sum(1 for n in ncores if n == 3),
            'n_core_4': sum(1 for n in ncores if n == 4),
            'n_core_5plus': sum(1 for n in ncores if n >= 5),
            'n_core_mean': float(np.mean(ncores)) if ncores else 0.0,
            'n_core_max': max(ncores) if ncores else 0,
            'share_max': float(max(shares)) if shares else 0.0,
            'share_mean': float(np.mean(shares)) if shares else 0.0,
            'occupancy': list(atom.virtual.occupancy),
        }

    atom = build_engine(sa)
    center = None; other = None
    if cond in ('injected_self', 'injected_other', 'shuffled_other'):
        center = build_engine(sc)
    if cond in ('injected_other', 'shuffled_other'):
        other = build_engine(so)

    # window 進行 + 毎 window 観察 + 自然発火注入
    snapshots = []
    inject_events = []  # 自然発火 event log (v10.7 流用)

    for w in range(WINDOWS):
        atom.step_window(steps=WINDOW_STEPS)
        if center is not None:
            center.step_window(steps=WINDOW_STEPS)
        if other is not None:
            other.step_window(steps=WINDOW_STEPS)

        # === 案 B 完全自然: 毎 window で should_attend 判定、発火するたび注入 ===
        if cond != 'baseline' and w >= NATURAL_FIRE_START:
            fire, z, st = should_attend(center)
            if fire:
                tp_in = derive_theme_phase_point(center, K_TARGET)
                if tp_in is not None:
                    ev = {'window': w, 'z': z, 'stress': st, 'tp_in': float(tp_in)}
                    if cond == 'injected_self':
                        lam_in = lam_dyn(center)
                        weights_in = label_weights_point(atom, tp_in, lam_in)
                        targets_in = targets_from_w(weights_in, atom, K_TARGET)
                        if targets_in:
                            pre_n = len(atom.state.alive_n)
                            pre_l = len(atom.state.alive_l)
                            atom.physics.inject(atom.state, target_nodes=targets_in)
                            ev.update({'targets_n': len(targets_in),
                                        'd_alive_n': len(atom.state.alive_n) - pre_n,
                                        'd_alive_l': len(atom.state.alive_l) - pre_l})
                            inject_events.append(ev)
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
                                ev.update({'targets_n': len(targets_out),
                                            'd_alive_n': len(atom.state.alive_n) - pre_n,
                                            'd_alive_l': len(atom.state.alive_l) - pre_l})
                                inject_events.append(ev)
                    elif cond == 'shuffled_other':
                        lam_in_other = lam_dyn(other)
                        weights_in_other = label_weights_point(other, tp_in, lam_in_other)
                        targets_in_other = targets_from_w(weights_in_other, other, K_TARGET)
                        if targets_in_other:
                            other.physics.inject(other.state, target_nodes=targets_in_other)
                            other.step_window(steps=OTHER_STEPS)
                            lam_out = lam_dyn(other)
                            weights_out = label_excitations_dist_shuf(
                                atom, other, lam_out, sa, so, w)
                            targets_out = targets_from_w(weights_out, atom, K_TARGET)
                            if targets_out:
                                pre_n = len(atom.state.alive_n)
                                pre_l = len(atom.state.alive_l)
                                atom.physics.inject(atom.state, target_nodes=targets_out)
                                ev.update({'targets_n': len(targets_out),
                                            'd_alive_n': len(atom.state.alive_n) - pre_n,
                                            'd_alive_l': len(atom.state.alive_l) - pre_l})
                                inject_events.append(ev)

        # 毎 window snapshot (集団平均回避、層化解析の素材)
        snapshots.append(snapshot(atom, w))

    dt = time.time() - t0
    print(f'  [PID {pid}] done atom={sa} cond={cond} other={so} ({dt:.0f}s) '
          f'fire={len(inject_events)}/{WINDOWS-NATURAL_FIRE_START}', flush=True)
    return {
        'atom_seed': sa, 'condition': cond,
        'other_seed': so if so is not None else -1,
        'snapshots': snapshots,
        'inject_events': inject_events,
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
    print('=== v1111f 案 B — 完全自然 (注入タイミング ESDE 標準) ===\n')
    print(f'  ATOM_SEEDS={ATOM_SEEDS} (3 atom、CPU 24 cores 整合)')
    print(f'  OTHER_SEEDS={OTHER_SEEDS}')
    print(f'  WINDOW_STEPS={WINDOW_STEPS}, MAT={MATURATION_WINDOWS}, TRACK={TRACKING_WINDOWS}')
    print(f'  自然発火開始: window {NATURAL_FIRE_START} (maturation 後)')
    tasks = make_tasks()
    print(f'  Tasks: {len(tasks)} = 3 atom × 8 conditions')
    print(f'  並列: Pool(24) で 1 Wave、推定 ~5.4 時間\n')

    t_main = time.time()
    with Pool(processes=24) as pool:
        results = pool.map(_worker, tasks)

    # snapshots を long format で保存
    snap_rows = []
    for r in results:
        for s in r['snapshots']:
            snap_rows.append({
                'atom_seed': r['atom_seed'], 'condition': r['condition'],
                'other_seed': r['other_seed'], **s,
            })
    snap_df = pd.DataFrame(snap_rows)
    snap_df.to_parquet(OUT_DIR / 'snapshots.parquet', index=False)

    # inject events (v10.7 source_event 流用)
    ev_rows = []
    for r in results:
        for ev in r['inject_events']:
            ev_rows.append({
                'atom_seed': r['atom_seed'], 'condition': r['condition'],
                'other_seed': r['other_seed'], **ev,
            })
    ev_df = pd.DataFrame(ev_rows)
    if len(ev_df) > 0:
        ev_df.to_parquet(OUT_DIR / 'inject_events.parquet', index=False)

    # 簡易サマリ
    print('\n=== 自然発火サマリ ===')
    n_fire_per_task = pd.DataFrame([
        {'atom_seed': r['atom_seed'], 'condition': r['condition'],
         'other_seed': r['other_seed'], 'n_fire': len(r['inject_events'])}
        for r in results])
    print(n_fire_per_task.to_string(index=False))
    print(f'\n  全 task の発火回数: total={n_fire_per_task["n_fire"].sum()}')
    print(f'  per cond (mean fire per task):')
    print(n_fire_per_task.groupby('condition')['n_fire'].mean().to_string())

    print('\n=== n_core 分布 (最終 window、cond 別、3 atom 平均) ===')
    last = snap_df[snap_df['window'] == WINDOWS - 1]
    last_avg = last.groupby('condition')[
        ['labels_total', 'n_core_2', 'n_core_3', 'n_core_4', 'n_core_5plus',
         'n_core_mean', 'share_max']].mean()
    print(last_avg.to_string())

    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'design': 'natural_fire_v1111f',
        'ATOM_SEEDS': ATOM_SEEDS, 'OTHER_SEEDS': OTHER_SEEDS,
        'WINDOW_STEPS': WINDOW_STEPS, 'WINDOWS': WINDOWS,
        'NATURAL_FIRE_START': NATURAL_FIRE_START,
        'total_sec': time.time() - t_main,
        'n_tasks': len(tasks),
    }
    (OUT_DIR / 'summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n=== v1111f 案 B 完了 total {time.time()-t_main:.1f}s ===')


if __name__ == '__main__':
    main()
