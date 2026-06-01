#!/usr/bin/env python3
"""v1111d — 出口を phase 分布の形で運ぶ (全体の癖でゆるく繋ぐ)

Web Claude v1111d 設計準拠:
- v1111c の出口 (一点平均) を分布の形に拡張
- 励起度 = Σ_n E[n]·exp(-λ·d(label.phase_sig, θ[n]))
- 入口は一点 (狙い)、出口は分布 (中身) = 粒度の意図的非対称
- 原理 (phase/exp(-λd)/λ state 由来/テーマ) は揃う

左右対称チェック (§2、Code A 認識確認 ✓):
| 項目 | 入口 | 出口 v1111d | 対称? |
|---|---|---|---|
| 照合 | phase | phase | ✓ |
| カーネル | exp(-λd) | exp(-λd) | ✓ |
| λ 出所 | state (center) | state (other) | ✓ |
| 渡すもの | テーマ phase | テーマ phase 分布 | ✓ |
| 粒度 | 一点 (狙い) | **分布 (中身)** | 意図的非対称 |

v1111c → v1111d 変更点:
- 出口: 一点平均 → Σ_n E[n]·exp(-λ·d(label, θ[n])) 分布の和
- shuffled: random theme phase 1 つ → random phase 分布全 active node
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
OUT_DIR = STAGE5 / 'run_v1111d'
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

    # ===== 入口: 一点 (center → Atom 狙い) =====
    def derive_theme_phase_point(eng, K=K_TARGET):
        """入口用: top-K E node の theta 円周平均 (一点)"""
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

    # 入口の一致率 (一点版、v1111c 流用)
    def label_weights_point(atom, theme_phase, lam):
        macro = set(atom.virtual.macro_nodes)
        w = {}
        for lid, lab in atom.virtual.labels.items():
            if lid in macro: continue
            d = cdist(lab['phase_sig'], theme_phase)
            w[lid] = {'w': math.exp(-lam*d), 'nodes': list(lab['nodes'])}
        return w

    # ===== 出口: 分布 (Other → Atom 中身) =====
    def label_excitations_dist(atom, other, lam_out):
        """各 Atom label の励起度 = Σ_n E[n]·exp(-λ·d(label, θ[n]))
        v1111d 核心: 一点版を「和」に広げる、numpy vectorize"""
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
        """shuffled: Other の phase 分布を random phase に置換、E 重みは Other 由来"""
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

    # メイン処理
    atom = build_engine(sa)
    center = None; other = None
    if cond in ('injected_self', 'injected_other', 'shuffled_other'):
        center = build_engine(sc)
    if cond in ('injected_other', 'shuffled_other'):
        other = build_engine(so)

    occ_at_observe = None
    target_w = W_INJECT + K_OBSERVE

    for w in range(WINDOWS):
        atom.step_window(steps=WINDOW_STEPS)
        if center is not None:
            center.step_window(steps=WINDOW_STEPS)
        if w == W_INJECT and cond != 'baseline':
            if should_attend(center):
                # 入口: 一点 (狙い、変更なし)
                tp_in = derive_theme_phase_point(center, K_TARGET)
                if tp_in is not None:
                    lam_in = lam_dyn(center)
                    weights_in = label_weights_point(atom, tp_in, lam_in)
                    targets_in = targets_from_w(weights_in, atom, K_TARGET)
                    if cond == 'injected_self':
                        if targets_in:
                            atom.physics.inject(atom.state, target_nodes=targets_in)
                    elif cond == 'injected_other':
                        if targets_in:
                            other.physics.inject(other.state, target_nodes=list(targets_in))
                            other.step_window(steps=OTHER_STEPS)
                            # ★ v1111d 出口: 分布 (中身)
                            lam_out = lam_dyn(other)
                            weights_out = label_excitations_dist(atom, other, lam_out)
                            targets_out = targets_from_w(weights_out, atom, K_TARGET)
                            if targets_out:
                                atom.physics.inject(atom.state, target_nodes=targets_out)
                    elif cond == 'shuffled_other':
                        if targets_in:
                            other.physics.inject(other.state, target_nodes=list(targets_in))
                            other.step_window(steps=OTHER_STEPS)
                            # ★ v1111d shuffled 出口: random phase 分布 (中身捨て、機構通す)
                            lam_out = lam_dyn(other)
                            weights_out = label_excitations_dist_shuf(
                                atom, other, lam_out, sa, so)
                            targets_out = targets_from_w(weights_out, atom, K_TARGET)
                            if targets_out:
                                atom.physics.inject(atom.state, target_nodes=targets_out)
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
    print('=== v1111d — 出口を phase 分布の形で運ぶ ===\n')
    print(f'  W_INJECT={W_INJECT}, K_OBSERVE={K_OBSERVE}')
    tasks = make_tasks()
    print(f'  Tasks: {len(tasks)} (3 atom × 8 conditions)\n')

    t_main = time.time()
    with Pool(processes=24) as pool:
        results = pool.map(_worker, tasks)

    occ_by_key = {}
    for r in results:
        key = (r['atom_seed'], r['condition'], r['other_seed'])
        occ_by_key[key] = np.array(r['occupancy'])

    baseline_per_atom = {sa: occ_by_key[(sa, 'baseline', -1)] for sa in ATOM_SEEDS}

    dp_records = []
    for r in results:
        if r['condition'] == 'baseline':
            continue
        sa = r['atom_seed']
        dp = occ_by_key[(sa, r['condition'], r['other_seed'])] - baseline_per_atom[sa]
        dp_records.append({
            'atom_seed': sa, 'condition': r['condition'],
            'other_seed': r['other_seed'],
            'dp': dp.tolist(),
        })

    dp_self = {sa: next(d['dp'] for d in dp_records
                          if d['atom_seed']==sa and d['condition']=='injected_self')
                for sa in ATOM_SEEDS}

    # === §2.1 atom 横断一貫性 (主役) ===
    print('\n=== §2.1 atom 横断一貫性 (主役、cos 小 = 一貫) ===')
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

    # === §2.2 real vs shuffled d_between ===
    print('\n=== §2.2 real vs shuffled (atom ごと、d_between cos) ===')
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
            print(f'    {cond}: d_between cos mean={row["d_between_cos_mean"]:.4f}')
    between_df = pd.DataFrame(between_rows)
    between_df.to_parquet(OUT_DIR / 'between.parquet', index=False)

    # === §2.3 self 床からの離れ方 ===
    print('\n=== §2.3 self 床からの離れ方 ===')
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
    for cond in ['injected_other', 'shuffled_other']:
        sub = sf_df[sf_df['condition']==cond]
        print(f'  [{cond}] cos from self: mean={sub["cos_from_self"].mean():.4f}, '
              f'std={sub["cos_from_self"].std():.4f}')

    # === まとめ ===
    print('\n=== 3 切り分け まとめ (v1111d) ===')
    print('\n  §2.1 atom 横断一貫性 (主役、cos 小 = 一貫):')
    for cond in ['injected_other', 'shuffled_other']:
        sub = consistency_df[consistency_df['condition']==cond]
        print(f'    {cond:20s} cos_mean mean={sub["cos_mean"].mean():.4f} '
              f'min={sub["cos_min"].min():.4f}')
    print('\n  §2.2 real vs shuffled d_between:')
    for cond in ['injected_other', 'shuffled_other']:
        sub = between_df[between_df['condition']==cond]
        print(f'    {cond:20s} d_between cos_mean mean={sub["d_between_cos_mean"].mean():.4f}')
    real_d = between_df[between_df['condition']=='injected_other']['d_between_cos_mean'].mean()
    shuf_d = between_df[between_df['condition']=='shuffled_other']['d_between_cos_mean'].mean()
    print(f'\n    real - shuffled = {real_d - shuf_d:+.4f}')

    # v1111b → v1111c → v1111d 進展比較
    print('\n  v1111b/c/d 進展:')
    print(f'    §2.1 cos_mean (injected_other): v1111b 修正 1.074 → v1111c 1.001 → v1111d {consistency_df[consistency_df["condition"]=="injected_other"]["cos_mean"].mean():.4f}')
    print(f'    §2.2 real - shuffled: v1111b 修正 +0.005 → v1111c +0.061 → v1111d {real_d - shuf_d:+.4f}')

    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'W_INJECT': W_INJECT, 'K_OBSERVE': K_OBSERVE,
        'ATOM_SEEDS': ATOM_SEEDS, 'OTHER_SEEDS': OTHER_SEEDS,
        'n_tasks': len(tasks),
        'total_sec': time.time() - t_main,
    }
    (OUT_DIR / 'summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n=== v1111d 完了 total {time.time()-t_main:.1f}s ===')


if __name__ == '__main__':
    main()
