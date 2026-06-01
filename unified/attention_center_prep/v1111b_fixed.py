#!/usr/bin/env python3
"""v1111b 計測修正 — δ_repeat を捨て、系が出す参照点で測り直す

Web Claude v1111b 計測修正設計準拠:
- タイミング固定 (全条件 W_INJECT=2)、δ_repeat 作らない
- 3 参照点: self 床 / shuffled_other / atom 横断一貫性
- 3 切り分け:
  §2.1 atom 横断一貫性 (V_other = ΔP_other - ΔP_self が atom またいで一貫か)
  §2.2 real vs shuffled (d_between 比較)
  §2.3 self 床からの離れ方

Main: W_INJECT=2 で 24 tasks
ロバスト性: W_INJECT=3 別 run (本実装は main のみ、結果見て追加)
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
OUT_DIR = STAGE5 / 'run_v1111b_fixed'
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
CENTER_SEEDS = [99, 157, 217]
OTHER_SEEDS = [100, 101, 102]
W_INJECT = 2  # タイミング固定 (δ_repeat 作らない、Web Claude §1)
K_OBSERVE = 5
WINDOWS = W_INJECT + K_OBSERVE + 1  # 8
WINDOW_STEPS = 100
OTHER_STEPS = 5
K_TARGET = 5
N_BINS = 64


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

    def derive_tp(c, K=K_TARGET):
        a = sorted(c.state.alive_n)
        if not a: return None
        ev = {n: float(c.state.E.get(n, 0.0)) for n in a}
        topk = sorted(a, key=lambda n: -ev[n])[:K]
        th = [float(c.state.theta[n]) for n in topk]
        if not th: return None
        cs = sum(math.cos(t) for t in th); ss_ = sum(math.sin(t) for t in th)
        return math.atan2(ss_/len(th), cs/len(th)) % (2*math.pi)

    def lam_dyn(c):
        macro = set(c.virtual.macro_nodes)
        ps = [l['phase_sig'] for lid, l in c.virtual.labels.items() if lid not in macro]
        if len(ps) < 2: return 1.0
        cm = float(np.mean([math.cos(p) for p in ps]))
        sm = float(np.mean([math.sin(p) for p in ps]))
        r = math.sqrt(cm**2 + sm**2)
        cs_std = math.pi if r < 1e-9 else math.sqrt(-2*math.log(max(r, 1e-9)))
        return 1.0 / (cs_std + 1e-9)

    def cdist(a, b):
        d = abs(a - b) % (2*math.pi)
        return min(d, 2*math.pi - d)

    def label_weights(atom, tp, lam):
        macro = set(atom.virtual.macro_nodes)
        w = {}
        for lid, lab in atom.virtual.labels.items():
            if lid in macro: continue
            d = cdist(lab['phase_sig'], tp)
            w[lid] = {'w': math.exp(-lam*d), 'nodes': list(lab['nodes'])}
        return w

    def targets_from_w(w, atom, K=K_TARGET):
        if not w: return []
        slids = sorted(w.keys(), key=lambda l: -w[l]['w'])
        cands = []
        for lid in slids[:max(K, 3)]:
            for n in w[lid]['nodes']:
                if n in atom.state.alive_n: cands.append(n)
        cands = list(set(cands))
        if not cands: return []
        ev = {n: float(atom.state.E.get(n, 0.0)) for n in cands}
        return sorted(cands, key=lambda n: -ev[n])[:K]

    def trans_other(o, K=K_TARGET):
        a = sorted(o.state.alive_n)
        if not a: return []
        ev = {n: float(o.state.E.get(n, 0.0)) for n in a}
        return sorted(a, key=lambda n: -ev[n])[:K]

    def shuffled_targets(atom, sa_, so_, K=K_TARGET):
        """shuffled: alive_n からランダム K (中身捨てる)、seed state 由来"""
        alive = sorted(atom.state.alive_n)
        if len(alive) <= K: return alive
        sf_seed = (sa_ * 13 + so_ + 7) % (2**32)
        rng = np.random.default_rng(seed=sf_seed)
        idx = rng.choice(len(alive), size=K, replace=False)
        return [alive[i] for i in idx]

    # メイン処理
    atom = build_engine(sa)
    center = None; other = None
    if cond in ('injected_self', 'injected_other', 'shuffled_other'):
        center = build_engine(sc)
    if cond == 'injected_other':
        other = build_engine(so)

    target_phase = None
    occ_at_observe = None
    target_w = W_INJECT + K_OBSERVE

    for w in range(WINDOWS):
        atom.step_window(steps=WINDOW_STEPS)
        if center is not None:
            center.step_window(steps=WINDOW_STEPS)
        # 注入 (タイミング固定 W_INJECT)
        if cond != 'baseline' and w == W_INJECT:
            if should_attend(center):
                tp = derive_tp(center, K_TARGET)
                if tp is not None:
                    target_phase = float(tp)
                    if cond == 'injected_self':
                        lam = lam_dyn(center)
                        weights = label_weights(atom, tp, lam)
                        targets = targets_from_w(weights, atom, K_TARGET)
                        if targets:
                            atom.physics.inject(atom.state, target_nodes=targets)
                    elif cond == 'injected_other':
                        lam = lam_dyn(center)
                        weights = label_weights(atom, tp, lam)
                        targets = targets_from_w(weights, atom, K_TARGET)
                        if targets:
                            other.physics.inject(other.state, target_nodes=list(targets))
                            other.step_window(steps=OTHER_STEPS)
                            new_targets = trans_other(other, K_TARGET)
                            if new_targets:
                                atom.physics.inject(atom.state, target_nodes=new_targets)
                    elif cond == 'shuffled_other':
                        targets = shuffled_targets(atom, sa, so, K_TARGET)
                        if targets:
                            atom.physics.inject(atom.state, target_nodes=targets)
        if w == target_w:
            occ_at_observe = list(atom.virtual.occupancy)
            break

    if occ_at_observe is None:
        occ_at_observe = list(atom.virtual.occupancy)

    dt = time.time() - t0
    print(f'  [PID {pid}] done atom={sa} cond={cond} other={so} ({dt:.0f}s)', flush=True)
    return {
        'atom_seed': sa, 'condition': cond,
        'other_seed': so if so is not None else -1,
        'target_phase': target_phase if target_phase is not None else -999,
        'occupancy': occ_at_observe,
    }


def distance_pair(dp1, dp2):
    dp1 = np.asarray(dp1, dtype=float); dp2 = np.asarray(dp2, dtype=float)
    eu = float(np.linalg.norm(dp1 - dp2))
    n1 = float(np.linalg.norm(dp1)); n2 = float(np.linalg.norm(dp2))
    if n1 < 1e-12 or n2 < 1e-12:
        cos = 1.0 if (n1 + n2) > 0 else 0.0
    else:
        cos = 1.0 - float(np.dot(dp1, dp2) / (n1 * n2))
    return {'eu': eu, 'cos': cos}


def make_tasks():
    """24 unique tasks: 3 atom × 8 conditions (per W_INJECT)"""
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
    print('=== v1111b 計測修正 — タイミング固定 + 3 参照点 ===\n')
    print(f'  W_INJECT={W_INJECT} (固定、δ_repeat 作らない)')
    tasks = make_tasks()
    print(f'  Tasks: {len(tasks)} (3 atom × 8 conditions)')
    print(f'  並列: Pool(24)\n')

    t_main = time.time()
    with Pool(processes=24) as pool:
        results = pool.map(_worker, tasks)

    # 結果索引化
    occ_by_key = {}
    for r in results:
        key = (r['atom_seed'], r['condition'], r['other_seed'])
        occ_by_key[key] = np.array(r['occupancy'])

    # baseline per atom
    baseline_per_atom = {sa: occ_by_key[(sa, 'baseline', -1)] for sa in ATOM_SEEDS}

    # ΔP per (atom, condition, other)
    dp_records = []
    for r in results:
        if r['condition'] == 'baseline':
            continue
        sa = r['atom_seed']
        dp = occ_by_key[(sa, r['condition'], r['other_seed'])] - baseline_per_atom[sa]
        dp_records.append({
            'atom_seed': sa, 'condition': r['condition'],
            'other_seed': r['other_seed'],
            'dp_norm': float(np.linalg.norm(dp)),
            'dp': dp.tolist(),
        })

    # ΔP_self per atom
    dp_self = {sa: next(d['dp'] for d in dp_records
                          if d['atom_seed']==sa and d['condition']=='injected_self')
                for sa in ATOM_SEEDS}

    # === §2.1 atom 横断一貫性 ===
    # 各 Other について、V_other = ΔP_other - ΔP_self を 3 atom で比較
    print('\n=== §2.1 atom 横断一貫性 (Other ごと、V = ΔP_other - ΔP_self の atom 間 cos 距離) ===')
    consistency = []
    for cond in ['injected_other', 'shuffled_other']:
        print(f'\n  [{cond}]')
        for so in OTHER_SEEDS:
            V_per_atom = {}
            for sa in ATOM_SEEDS:
                dp_other = next(d['dp'] for d in dp_records
                                  if d['atom_seed']==sa and d['condition']==cond
                                  and d['other_seed']==so)
                V_per_atom[sa] = np.array(dp_other) - np.array(dp_self[sa])
            # 3 atom pairs
            cos_pairs = []
            atoms = list(V_per_atom.keys())
            for i in range(len(atoms)):
                for j in range(i+1, len(atoms)):
                    d = distance_pair(V_per_atom[atoms[i]], V_per_atom[atoms[j]])
                    cos_pairs.append(d['cos'])
            row = {
                'condition': cond, 'other_seed': so,
                'cos_mean': float(np.mean(cos_pairs)),
                'cos_max': float(max(cos_pairs)),
                'cos_min': float(min(cos_pairs)),
            }
            consistency.append(row)
            print(f'    Other={so}: cos mean={row["cos_mean"]:.4f} '
                  f'min={row["cos_min"]:.4f} max={row["cos_max"]:.4f}')
    consistency_df = pd.DataFrame(consistency)
    consistency_df.to_parquet(OUT_DIR / 'consistency.parquet', index=False)

    # === §2.2 real vs shuffled (d_between) ===
    print('\n=== §2.2 real vs shuffled (atom ごと、Other 間 d_between cos) ===')
    between_rows = []
    for sa in ATOM_SEEDS:
        print(f'\n  [atom={sa}]')
        for cond in ['injected_other', 'shuffled_other']:
            dp_per_other = {so: next(d['dp'] for d in dp_records
                                      if d['atom_seed']==sa and d['condition']==cond
                                      and d['other_seed']==so)
                            for so in OTHER_SEEDS}
            cos_pairs = []
            seeds = sorted(dp_per_other.keys())
            for i in range(len(seeds)):
                for j in range(i+1, len(seeds)):
                    d = distance_pair(dp_per_other[seeds[i]], dp_per_other[seeds[j]])
                    cos_pairs.append(d['cos'])
            row = {
                'atom_seed': sa, 'condition': cond,
                'd_between_cos_mean': float(np.mean(cos_pairs)),
                'd_between_cos_min': float(min(cos_pairs)),
            }
            between_rows.append(row)
            print(f'    {cond}: d_between cos mean={row["d_between_cos_mean"]:.4f} '
                  f'min={row["d_between_cos_min"]:.4f}')
    between_df = pd.DataFrame(between_rows)
    between_df.to_parquet(OUT_DIR / 'between.parquet', index=False)

    # === §2.3 self 床からの離れ方 ===
    print('\n=== §2.3 self 床からの離れ方 (各 Other × atom) ===')
    self_floor = []
    for sa in ATOM_SEEDS:
        for cond in ['injected_other', 'shuffled_other']:
            for so in OTHER_SEEDS:
                dp_other = next(d['dp'] for d in dp_records
                                  if d['atom_seed']==sa and d['condition']==cond
                                  and d['other_seed']==so)
                d = distance_pair(dp_other, dp_self[sa])
                self_floor.append({
                    'atom_seed': sa, 'condition': cond, 'other_seed': so,
                    'cos_from_self': d['cos'], 'eu_from_self': d['eu'],
                })
    sf_df = pd.DataFrame(self_floor)
    sf_df.to_parquet(OUT_DIR / 'self_floor.parquet', index=False)
    # 集計
    for cond in ['injected_other', 'shuffled_other']:
        sub = sf_df[sf_df['condition']==cond]
        print(f'\n  [{cond}] cos from self: '
              f'mean={sub["cos_from_self"].mean():.4f}, '
              f'std={sub["cos_from_self"].std():.4f}')

    # === 3 切り分け まとめ ===
    print('\n=== 3 切り分け まとめ ===')
    # §2.1 比較: injected_other vs shuffled_other の cos_mean
    print('\n  §2.1 atom 横断一貫性 (cos 小 = 一貫、Other 中身署名):')
    for cond in ['injected_other', 'shuffled_other']:
        sub = consistency_df[consistency_df['condition']==cond]
        print(f'    {cond:20s} cos_mean mean={sub["cos_mean"].mean():.4f} '
              f'min={sub["cos_min"].min():.4f}')
    # §2.2 比較: real d_between vs shuffled d_between
    print('\n  §2.2 real vs shuffled d_between (大 = 形差大):')
    for cond in ['injected_other', 'shuffled_other']:
        sub = between_df[between_df['condition']==cond]
        print(f'    {cond:20s} d_between cos_mean mean={sub["d_between_cos_mean"].mean():.4f}')
    # 比較: real > shuffled で「中身が構造足す」候補
    real_d = between_df[between_df['condition']=='injected_other']['d_between_cos_mean'].mean()
    shuf_d = between_df[between_df['condition']=='shuffled_other']['d_between_cos_mean'].mean()
    print(f'\n    real - shuffled = {real_d - shuf_d:+.4f} '
          f'({"real > shuffled (中身候補)" if real_d > shuf_d else "real ≈ shuffled (ノイズ寄り)"})')

    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'W_INJECT': W_INJECT, 'K_OBSERVE': K_OBSERVE,
        'ATOM_SEEDS': ATOM_SEEDS, 'OTHER_SEEDS': OTHER_SEEDS,
        'n_tasks': len(tasks),
        'total_sec': time.time() - t_main,
    }
    (OUT_DIR / 'summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n=== v1111b 計測修正 完了 total {time.time()-t_main:.1f}s ===')


if __name__ == '__main__':
    main()
