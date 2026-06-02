#!/usr/bin/env python3
"""v1111e_redo の異常 (全 6 ペアで cos mean 0.9993 完全同一) の診断

Taka 指示「これまでの ESDE 実装とかけ離れていないか確認」に従い:
- v1111d と同じ Atom/Center seed で短時間 run (Center seed 2000+ が原因か切り分け)
- worker に診断情報追加 (inject 実行確認 + 前後 alive_n/alive_l + weights_out 分布 + targets_out)

仮説:
- (A) Center seed=2000-2023 で should_attend が常に False → inject 走らず
- (B) 足 2 修正自体に問題 (logic) → 同 seed でも 0/3
- (C) weights_out が均等で targets_out が injected/shuffled で同じ → 結果同一

stage3_step_b_smoke の inject_to_engine パターン (pre/post alive_n, E mean) を参考に
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
OUT_DIR = STAGE5 / 'run_v1111e_diag'
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

# 診断用: v1111d と完全同じ seed (Center seed 2000+ が原因かを切り分け)
ATOM_SEEDS = [42, 100, 200]
CENTER_SEEDS = [99, 157, 217]
OTHER_SEEDS = [100, 101, 102]
W_INJECT = 2
K_OBSERVE = 5
WINDOWS = W_INJECT + K_OBSERVE + 1
WINDOW_STEPS = 100
OTHER_STEPS = 5
K_TARGET = 5
N_BINS = 64


def _worker(args):
    sa, sc, cond, so = args
    pid = os.getpid()
    print(f'[PID {pid}] start atom={sa} cond={cond} other={so}', flush=True)
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
        if not c.state.alive_n: return False, {'reason': 'no_alive'}
        E = np.array([c.state.E.get(n, 0.0) for n in c.state.alive_n])
        if len(E) < 2: return False, {'reason': 'too_few'}
        m = float(E.mean()); s = float(E.std())
        if s < 1e-9: return False, {'reason': 'no_std'}
        z = (float(E.max()) - m) / s
        st = float((c.stress_stats or {}).get('stress_intensity', 1.0))
        return z > st, {'z': z, 'stress': st, 'mean_E': m, 'max_E': float(E.max())}

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

    def w_stats(weights):
        if not weights: return {'n': 0, 'max': 0, 'min': 0, 'mean': 0, 'std': 0}
        vals = np.array([v['w'] for v in weights.values()])
        return {'n': len(vals), 'max': float(vals.max()), 'min': float(vals.min()),
                'mean': float(vals.mean()), 'std': float(vals.std())}

    atom = build_engine(sa)
    center = None; other = None
    if cond in ('injected_self', 'injected_other', 'shuffled_other'):
        center = build_engine(sc)
    if cond in ('injected_other', 'shuffled_other'):
        other = build_engine(so)

    diag = {'cond': cond, 'sa': sa, 'sc': sc, 'so': so, 'attended': False,
             'tp_in': None, 'lam_in': None, 'lam_in_other': None,
             'weights_in_other_stats': None, 'targets_in_other_n': 0,
             'weights_out_stats': None, 'targets_out_n': 0,
             'inject_atom_pre_alive_n': 0, 'inject_atom_post_alive_n': 0,
             'inject_atom_pre_alive_l': 0, 'inject_atom_post_alive_l': 0,
             'targets_out_sample': []}

    occ_at_observe = None
    target_w = W_INJECT + K_OBSERVE

    for w in range(WINDOWS):
        atom.step_window(steps=WINDOW_STEPS)
        if center is not None:
            center.step_window(steps=WINDOW_STEPS)
        if w == W_INJECT and cond != 'baseline':
            fire, fi = should_attend(center)
            diag['attended'] = fire
            diag['attend_info'] = fi
            if fire:
                tp_in = derive_theme_phase_point(center, K_TARGET)
                diag['tp_in'] = float(tp_in) if tp_in is not None else None
                if tp_in is not None:
                    if cond == 'injected_self':
                        lam_in = lam_dyn(center)
                        diag['lam_in'] = float(lam_in)
                        weights_in = label_weights_point(atom, tp_in, lam_in)
                        targets_in = targets_from_w(weights_in, atom, K_TARGET)
                        diag['targets_in_n'] = len(targets_in)
                        if targets_in:
                            diag['inject_atom_pre_alive_n'] = len(atom.state.alive_n)
                            diag['inject_atom_pre_alive_l'] = len(atom.state.alive_l)
                            atom.physics.inject(atom.state, target_nodes=targets_in)
                            diag['inject_atom_post_alive_n'] = len(atom.state.alive_n)
                            diag['inject_atom_post_alive_l'] = len(atom.state.alive_l)
                    elif cond in ('injected_other', 'shuffled_other'):
                        lam_in_other = lam_dyn(other)
                        diag['lam_in_other'] = float(lam_in_other)
                        weights_in_other = label_weights_point(other, tp_in, lam_in_other)
                        diag['weights_in_other_stats'] = w_stats(weights_in_other)
                        targets_in_other = targets_from_w(weights_in_other, other, K_TARGET)
                        diag['targets_in_other_n'] = len(targets_in_other)
                        if targets_in_other:
                            other.physics.inject(other.state, target_nodes=targets_in_other)
                            other.step_window(steps=OTHER_STEPS)
                            lam_out = lam_dyn(other)
                            diag['lam_out'] = float(lam_out)
                            if cond == 'injected_other':
                                weights_out = label_excitations_dist(atom, other, lam_out)
                            else:
                                weights_out = label_excitations_dist_shuf(
                                    atom, other, lam_out, sa, so)
                            diag['weights_out_stats'] = w_stats(weights_out)
                            targets_out = targets_from_w(weights_out, atom, K_TARGET)
                            diag['targets_out_n'] = len(targets_out)
                            diag['targets_out_sample'] = targets_out[:K_TARGET]
                            if targets_out:
                                diag['inject_atom_pre_alive_n'] = len(atom.state.alive_n)
                                diag['inject_atom_pre_alive_l'] = len(atom.state.alive_l)
                                atom.physics.inject(atom.state, target_nodes=targets_out)
                                diag['inject_atom_post_alive_n'] = len(atom.state.alive_n)
                                diag['inject_atom_post_alive_l'] = len(atom.state.alive_l)
        if w == target_w:
            occ_at_observe = list(atom.virtual.occupancy)
            break

    if occ_at_observe is None:
        occ_at_observe = list(atom.virtual.occupancy)

    dt = time.time() - t0
    print(f'[PID {pid}] done atom={sa} cond={cond} other={so} ({dt:.0f}s) diag={diag}',
          flush=True)
    return {
        'atom_seed': sa, 'condition': cond,
        'other_seed': so if so is not None else -1,
        'occupancy': occ_at_observe,
        'diag': diag,
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
    print('=== v1111e 異常診断 — 3 atom × 3 conditions、Center seed v1111d 同じ ===\n')
    tasks = make_tasks()
    print(f'  Tasks: {len(tasks)} = 3 atom × 8 conditions = 24')
    print(f'  ATOM_SEEDS={ATOM_SEEDS}, CENTER_SEEDS={CENTER_SEEDS}, OTHER_SEEDS={OTHER_SEEDS}')
    print(f'  並列: Pool(24) で 1 Wave\n')

    t_main = time.time()
    with Pool(processes=24) as pool:
        results = pool.map(_worker, tasks)

    # 診断データ収集
    diag_rows = []
    for r in results:
        d = r['diag']
        diag_rows.append({
            'sa': d['sa'], 'sc': d['sc'], 'so': d['so'], 'cond': d['cond'],
            'attended': d.get('attended', False),
            'tp_in': d.get('tp_in'),
            'lam_in_other': d.get('lam_in_other'),
            'lam_out': d.get('lam_out'),
            'targets_in_other_n': d.get('targets_in_other_n', 0),
            'targets_out_n': d.get('targets_out_n', 0),
            'inject_atom_pre_alive_n': d.get('inject_atom_pre_alive_n', 0),
            'inject_atom_post_alive_n': d.get('inject_atom_post_alive_n', 0),
            'inject_atom_pre_alive_l': d.get('inject_atom_pre_alive_l', 0),
            'inject_atom_post_alive_l': d.get('inject_atom_post_alive_l', 0),
            'targets_out_sample': str(d.get('targets_out_sample', [])),
            'weights_in_max': (d.get('weights_in_other_stats') or {}).get('max'),
            'weights_in_min': (d.get('weights_in_other_stats') or {}).get('min'),
            'weights_in_mean': (d.get('weights_in_other_stats') or {}).get('mean'),
            'weights_out_max': (d.get('weights_out_stats') or {}).get('max'),
            'weights_out_min': (d.get('weights_out_stats') or {}).get('min'),
            'weights_out_mean': (d.get('weights_out_stats') or {}).get('mean'),
            'weights_out_std': (d.get('weights_out_stats') or {}).get('std'),
        })
    diag_df = pd.DataFrame(diag_rows)
    diag_df.to_parquet(OUT_DIR / 'diag.parquet', index=False)

    print('\n=== 診断サマリ ===')
    # 注入は実行されたか?
    n_attended = diag_df[diag_df['cond'] != 'baseline']['attended'].sum()
    n_total_inj = len(diag_df[diag_df['cond'] != 'baseline'])
    print(f'\n  should_attend=True: {n_attended}/{n_total_inj}')

    # targets_out が空でないか
    n_inject_done = diag_df[diag_df['targets_out_n'] > 0].shape[0]
    print(f'  targets_out > 0 (実際に inject): {n_inject_done}/{n_total_inj}')

    # alive_n / alive_l に変化はあったか
    print('\n  Atom inject 前後の変化:')
    for cond in ['injected_self', 'injected_other', 'shuffled_other']:
        sub = diag_df[diag_df['cond'] == cond]
        if len(sub) == 0: continue
        d_alive_n = (sub['inject_atom_post_alive_n'] - sub['inject_atom_pre_alive_n']).mean()
        d_alive_l = (sub['inject_atom_post_alive_l'] - sub['inject_atom_pre_alive_l']).mean()
        print(f'    {cond}: Δalive_n mean={d_alive_n:.2f}, Δalive_l mean={d_alive_l:.2f}')

    # targets_out が injected_other と shuffled_other で同じか?
    print('\n  targets_out 比較 (同 atom × 同 Other で injected vs shuffled):')
    for sa in ATOM_SEEDS:
        for so in OTHER_SEEDS:
            inj_t = diag_df[(diag_df['sa']==sa) & (diag_df['cond']=='injected_other')
                              & (diag_df['so']==so)]
            shuf_t = diag_df[(diag_df['sa']==sa) & (diag_df['cond']=='shuffled_other')
                               & (diag_df['so']==so)]
            if len(inj_t) > 0 and len(shuf_t) > 0:
                inj_s = inj_t.iloc[0]['targets_out_sample']
                shuf_s = shuf_t.iloc[0]['targets_out_sample']
                same = (inj_s == shuf_s)
                print(f'    atom={sa} Other={so}: '
                      f'inj={inj_s} / shuf={shuf_s} same={same}')

    # weights_out の分布 (均等なら問題)
    print('\n  weights_out 分布 (max/min/mean/std):')
    for cond in ['injected_other', 'shuffled_other']:
        sub = diag_df[diag_df['cond'] == cond]
        if len(sub) == 0: continue
        print(f'    {cond}: max mean={sub["weights_out_max"].mean():.2e}, '
              f'min mean={sub["weights_out_min"].mean():.2e}, '
              f'std mean={sub["weights_out_std"].mean():.2e}')
        # max/min ratio が小さければ均等分布
        ratios = sub['weights_out_max'] / (sub['weights_out_min'] + 1e-12)
        print(f'      max/min ratio mean={ratios.mean():.2f} '
              f'(1.0 = 均等、大きいほど集中)')

    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'n_tasks': len(tasks),
        'n_attended': int(n_attended),
        'n_inject_done': int(n_inject_done),
        'total_sec': time.time() - t_main,
    }
    (OUT_DIR / 'summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n=== 診断 run 完了 total {time.time()-t_main:.1f}s ===')


if __name__ == '__main__':
    main()
