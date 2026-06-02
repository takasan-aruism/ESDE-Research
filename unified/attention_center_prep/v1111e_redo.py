#!/usr/bin/env python3
"""v1111e 作り直し — 足 2 (Atom→Other 注入) も phase 一致率に

Web Claude 指示準拠 (2026-06-02):
- 現 v1111e の重大欠陥: 足 2 で targets_in (Atom node) を Other に inject = 番号コピー
- 修正: 足 2 で Other 自身の label を tp_in 一致率で重み付け、Other 自身 core node を inject
- 3 本足すべて phase 一致率、ID をまたがせない

3 本足の左右対称チェック (§1):
| 項目 | 足 1 | 足 2 | 足 3 | 揃う? |
|---|---|---|---|---|
| 渡すもの | tp_in | tp_in | Other phase 分布 | ✓ 番号なし |
| 照合 | phase cdist | phase cdist | phase cdist | ✓ |
| カーネル | exp(-λd) | exp(-λd) | exp(-λd) | ✓ |
| inject 先 | Atom (self) | Other 自身 | Atom 自身 | ✓ |
| λ 出所 | state (center) | state (other) | state (other) | ✓ |

→ 全足揃う、赤信号なし

他は現 v1111e のまま:
- ATOM_SEEDS=[1000-1023]
- W_INJECT=2 固定、タイミング固定
- 3 参照点 (主役 §2.1、§2.2/§2.3 記録のみ判定不使用)
- 二段手順遵守
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
OUT_DIR = STAGE5 / 'run_v1111e_redo'
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

ATOM_SEEDS = list(range(1000, 1024))
CENTER_SEEDS = list(range(2000, 2024))
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

    def derive_theme_phase_point(eng, K=K_TARGET):
        """top-K E node の theta 円周平均 (一点、テーマ)"""
        alive = sorted(eng.state.alive_n)
        if not alive: return None
        ev = {n: float(eng.state.E.get(n, 0.0)) for n in alive}
        topk = sorted(alive, key=lambda n: -ev[n])[:K]
        th = [float(eng.state.theta[n]) for n in topk]
        if not th: return None
        cs = sum(math.cos(t) for t in th); ss_ = sum(math.sin(t) for t in th)
        return math.atan2(ss_/len(th), cs/len(th)) % (2*math.pi)

    def lam_dyn(eng):
        """state 由来 λ"""
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
        """eng (Atom or Other) の各 label について exp(-λ·d(label, theme))
        eng=atom なら Atom 用、eng=other なら Other 用 (足 2 で流用)"""
        macro = set(eng.virtual.macro_nodes)
        w = {}
        for lid, lab in eng.virtual.labels.items():
            if lid in macro: continue
            d = cdist(lab['phase_sig'], theme_phase)
            w[lid] = {'w': math.exp(-lam*d), 'nodes': list(lab['nodes'])}
        return w

    def label_excitations_dist(atom, other, lam_out):
        """v1111d 出口分布: Σ_n E[n]·exp(-λ·d(label, θ[n]))"""
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
        """v1111d shuffled: random phase 分布"""
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
        """top-K w label の core nodes (eng=atom or other で各系自身の node)"""
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
                # 足 1: center → Atom 読み (テーマ phase tp_in を計算)
                tp_in = derive_theme_phase_point(center, K_TARGET)
                if tp_in is not None:
                    if cond == 'injected_self':
                        # injected_self: center → Atom に直接 (足 2/3 なし)
                        lam_in = lam_dyn(center)
                        weights_in = label_weights_point(atom, tp_in, lam_in)
                        targets_in = targets_from_w(weights_in, atom, K_TARGET)
                        if targets_in:
                            atom.physics.inject(atom.state, target_nodes=targets_in)
                    elif cond == 'injected_other':
                        # ★ 足 2 (修正): テーマ phase を Other に渡し、Other 自身の node を立てる
                        lam_in_other = lam_dyn(other)
                        weights_in_other = label_weights_point(other, tp_in, lam_in_other)
                        targets_in_other = targets_from_w(weights_in_other, other, K_TARGET)
                        # ↑ targets_in_other は Other 自身の core node (Atom の node でない)
                        if targets_in_other:
                            other.physics.inject(other.state, target_nodes=targets_in_other)
                            other.step_window(steps=OTHER_STEPS)
                            # 足 3: 出口 phase 分布 (v1111d、変更なし)
                            lam_out = lam_dyn(other)
                            weights_out = label_excitations_dist(atom, other, lam_out)
                            targets_out = targets_from_w(weights_out, atom, K_TARGET)
                            if targets_out:
                                atom.physics.inject(atom.state, target_nodes=targets_out)
                    elif cond == 'shuffled_other':
                        # ★ 足 2 (修正、injected_other と同じ): 入口揃え
                        lam_in_other = lam_dyn(other)
                        weights_in_other = label_weights_point(other, tp_in, lam_in_other)
                        targets_in_other = targets_from_w(weights_in_other, other, K_TARGET)
                        if targets_in_other:
                            other.physics.inject(other.state, target_nodes=targets_in_other)
                            other.step_window(steps=OTHER_STEPS)
                            # 足 3: 出口の phase だけ random (中身捨て、v1111d)
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
    n1 = float(np.linalg.norm(dp1)); n2 = float(np.linalg.norm(dp2)) if False else float(np.linalg.norm(dp2))
    if n1 < 1e-12 or n2 < 1e-12:
        return {'cos': 1.0 if (n1 + n2) > 0 else 0.0}
    cos = 1.0 - float(np.dot(dp1, dp2) / (n1 * n2))
    return {'cos': cos}


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


def compute_atom_consistency_cos(V_per_atom):
    atoms = sorted(V_per_atom.keys())
    cos_pairs = []
    for i in range(len(atoms)):
        for j in range(i+1, len(atoms)):
            d = distance_pair(V_per_atom[atoms[i]], V_per_atom[atoms[j]])
            cos_pairs.append(d['cos'])
    return {
        'cos_mean': float(np.mean(cos_pairs)),
        'cos_median': float(np.median(cos_pairs)),
        'cos_std': float(np.std(cos_pairs)),
        'cos_min': float(min(cos_pairs)),
        'cos_max': float(max(cos_pairs)),
        'n_pairs': len(cos_pairs),
    }


def main():
    print('=== v1111e 作り直し — 足 2 phase 一致率化 (3 本足対称) ===\n')
    print(f'  ATOM_SEEDS: {ATOM_SEEDS[0]}-{ATOM_SEEDS[-1]} ({len(ATOM_SEEDS)} seeds)')
    tasks = make_tasks()
    print(f'  Tasks: {len(tasks)} (24 atom × 8 conditions)')
    print(f'  並列: Pool(24) × 8 Wave、推定 ~1.5-2 時間\n')

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

    # §2.1 atom 横断一貫性 (主役)
    print('\n=== §2.1 atom 横断一貫性 (主役、24 atom × 276 pairs) ===')
    consistency_records = {}
    for cond in ['injected_other', 'shuffled_other']:
        consistency_records[cond] = {}
        for so in OTHER_SEEDS:
            V_per_atom = {}
            for sa in ATOM_SEEDS:
                dp_other = next(d['dp'] for d in dp_records
                                  if d['atom_seed']==sa and d['condition']==cond
                                  and d['other_seed']==so)
                V_per_atom[sa] = np.array(dp_other) - np.array(dp_self[sa])
            stats = compute_atom_consistency_cos(V_per_atom)
            consistency_records[cond][so] = stats
            print(f'  [{cond}] Other={so}: cos mean={stats["cos_mean"]:.4f} '
                  f'median={stats["cos_median"]:.4f} std={stats["cos_std"]:.4f}')

    # inversion 判定
    print('\n=== Inversion 判定 (injected_cos < shuffled_cos) ===')
    n_inversion = 0
    inversion_records = []
    for so in OTHER_SEEDS:
        inj = consistency_records['injected_other'][so]['cos_mean']
        shuf = consistency_records['shuffled_other'][so]['cos_mean']
        inversion = bool(inj < shuf)
        gap = shuf - inj
        if inversion: n_inversion += 1
        marker = '★' if inversion else ' '
        print(f'  {marker} Other={so}: injected={inj:.4f} vs shuffled={shuf:.4f} '
              f'gap={gap:+.4f} inversion={inversion}')
        inversion_records.append({
            'other_seed': so, 'injected_cos': inj, 'shuffled_cos': shuf,
            'gap': gap, 'inversion': inversion,
        })
    print(f'\n  3 Other 中の inversion 数: {n_inversion}/3')
    if n_inversion == 3:
        print(f'  → 強再現性 (3/3): 共通土台確定候補 → 第二段へ')
    elif n_inversion == 2:
        print(f'  → 中再現性 (2/3)')
    elif n_inversion == 1:
        print(f'  → 弱再現性 (1/3)')
    else:
        print(f'  → 不再現 (0/3)')

    # サブグループ確認
    print('\n=== サブグループ確認 (8 atom × 3 group) ===')
    GROUPS = [ATOM_SEEDS[0:8], ATOM_SEEDS[8:16], ATOM_SEEDS[16:24]]
    subgroup_inversions = []
    for g_idx, g_atoms in enumerate(GROUPS):
        for so in OTHER_SEEDS:
            inj_V = {sa: np.array(next(d['dp'] for d in dp_records
                                          if d['atom_seed']==sa
                                          and d['condition']=='injected_other'
                                          and d['other_seed']==so)) - np.array(dp_self[sa])
                      for sa in g_atoms}
            shuf_V = {sa: np.array(next(d['dp'] for d in dp_records
                                          if d['atom_seed']==sa
                                          and d['condition']=='shuffled_other'
                                          and d['other_seed']==so)) - np.array(dp_self[sa])
                      for sa in g_atoms}
            inj_s = compute_atom_consistency_cos(inj_V)
            shuf_s = compute_atom_consistency_cos(shuf_V)
            inv = bool(inj_s['cos_mean'] < shuf_s['cos_mean'])
            subgroup_inversions.append({
                'group': g_idx, 'other_seed': so,
                'injected_cos': inj_s['cos_mean'], 'shuffled_cos': shuf_s['cos_mean'],
                'inversion': inv,
            })
    sub_df = pd.DataFrame(subgroup_inversions)
    sub_df.to_parquet(OUT_DIR / 'subgroups.parquet', index=False)
    n_inv_sub = int(sub_df['inversion'].sum())
    print(f'  9 サブグループ inversion: {n_inv_sub}/9')

    # cos 弱さ
    print('\n=== cos 絶対値 (弱さ、判定不使用) ===')
    overall_inj_cos = np.mean([consistency_records['injected_other'][so]['cos_mean']
                                 for so in OTHER_SEEDS])
    overall_shuf_cos = np.mean([consistency_records['shuffled_other'][so]['cos_mean']
                                  for so in OTHER_SEEDS])
    print(f'  injected_other 全 Other 平均 cos: {overall_inj_cos:.4f}')
    print(f'  shuffled_other  全 Other 平均 cos: {overall_shuf_cos:.4f}')
    print(f'  gap: {overall_shuf_cos - overall_inj_cos:+.4f}')

    # v1111e (足 2 番号コピー) との比較
    print('\n=== v1111e (足 2 番号コピー) との比較 ===')
    print(f'  v1111e 旧: injected 1.0039 / shuffled 1.0030 / gap -0.0009 / inv 1/3')
    print(f'  v1111e 新: injected {overall_inj_cos:.4f} / shuffled {overall_shuf_cos:.4f} '
          f'/ gap {overall_shuf_cos - overall_inj_cos:+.4f} / inv {n_inversion}/3')

    # §2.2 / §2.3 は parquet 記録のみ
    between_records = []
    for cond in ['injected_other', 'shuffled_other']:
        for sa in ATOM_SEEDS:
            dp_per_so = {so: np.array(next(d['dp'] for d in dp_records
                                              if d['atom_seed']==sa
                                              and d['condition']==cond
                                              and d['other_seed']==so))
                          for so in OTHER_SEEDS}
            seeds = sorted(dp_per_so.keys())
            cos_pairs = []
            for i in range(len(seeds)):
                for j in range(i+1, len(seeds)):
                    d = distance_pair(dp_per_so[seeds[i]], dp_per_so[seeds[j]])
                    cos_pairs.append(d['cos'])
            between_records.append({
                'atom_seed': sa, 'condition': cond,
                'd_between_cos_mean': float(np.mean(cos_pairs)),
            })
    pd.DataFrame(between_records).to_parquet(OUT_DIR / 'between_recorded_only.parquet', index=False)

    self_floor_records = []
    for sa in ATOM_SEEDS:
        for cond in ['injected_other', 'shuffled_other']:
            for so in OTHER_SEEDS:
                dp_other = next(d['dp'] for d in dp_records
                                  if d['atom_seed']==sa and d['condition']==cond
                                  and d['other_seed']==so)
                d = distance_pair(dp_other, dp_self[sa])
                self_floor_records.append({
                    'atom_seed': sa, 'condition': cond, 'other_seed': so,
                    'cos_from_self': d['cos'],
                })
    pd.DataFrame(self_floor_records).to_parquet(OUT_DIR / 'self_floor_recorded_only.parquet', index=False)
    print(f'\n  §2.2, §2.3 を parquet 保存 (判定不使用、二段手順)')

    # 主役 parquet
    cons_rows = []
    for cond in ['injected_other', 'shuffled_other']:
        for so in OTHER_SEEDS:
            stats = consistency_records[cond][so]
            cons_rows.append({'condition': cond, 'other_seed': so, **stats})
    pd.DataFrame(cons_rows).to_parquet(OUT_DIR / 'consistency.parquet', index=False)
    pd.DataFrame(inversion_records).to_parquet(OUT_DIR / 'inversion.parquet', index=False)

    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'fix': 'fix2_phase_match_rate (Atom node番号コピー→Other自身nodeをtp_in一致率で立てる)',
        'ATOM_SEEDS': ATOM_SEEDS, 'OTHER_SEEDS': OTHER_SEEDS,
        'W_INJECT': W_INJECT, 'K_OBSERVE': K_OBSERVE,
        'n_tasks': len(tasks),
        'n_inversion_main': n_inversion,
        'n_inversion_subgroups': n_inv_sub,
        'injected_cos_mean_overall': overall_inj_cos,
        'shuffled_cos_mean_overall': overall_shuf_cos,
        'gap_overall': overall_shuf_cos - overall_inj_cos,
        'total_sec': time.time() - t_main,
    }
    (OUT_DIR / 'summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n=== v1111e 作り直し 完了 total {time.time()-t_main:.1f}s ===')


if __name__ == '__main__':
    main()
