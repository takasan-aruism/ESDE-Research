#!/usr/bin/env python3
"""v1111b — 出口偏りの形が Other 次第で変わるか (Unified / 会話の分岐点)

Web Claude v1111b 主題設計準拠:
- 駆動 1 文: Atom 系の出口層 (phase 分布) の偏りの形が Other 次第で変わるか
- struct_survival_ratio を降ろし、新主指標 = 出口層 phase 分布の偏りの「形」
- Other を振る (100/101/102 × 2 W_INJECT 反復) + self を床
- 入れ子判定 (factor 不要、生の大小のみ)
- shuffled_other sanity (中身由来 vs seed 差ノイズの切り分け)
- 3 atom seeds (+64% 教訓)

Tasks: 3 atom seeds × 14 conditions = 42 unique tasks
Pool(24) で 2 Wave 並列、推定 ~40-50 分

反復ブレ δ_repeat (Code A 提案):
- engine は完全決定的 (Step 0 で bit-identical 確認済)
- 同 seed・同 Other・同 W_INJECT で 2 回 = ΔP 完全同一 (δ_repeat=0 自明)
- Code A 推奨: rep_a=W_INJECT 2, rep_b=W_INJECT 3 (timing 自然なブレ)
- Web Claude 判断要、本実装は (a) で進める
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
OUT_DIR = STAGE5 / 'run_v1111b'
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

# 3 atom seeds (+64% 教訓で単一視しない)
ATOM_SEEDS = [42, 100, 200]
CENTER_SEEDS = [99, 157, 217]  # atom seed と一意に対応
OTHER_SEEDS = [100, 101, 102]
W_INJECT_LIST = [2, 3]  # 反復ブレ (Code A 提案 (a))
K_OBSERVE = 5  # k=5 のみ (v1111b は形の Other 次第性が主、k は副次)
WINDOWS = max(W_INJECT_LIST) + K_OBSERVE + 1  # 9
WINDOW_STEPS = 100
OTHER_STEPS = 5
K_TARGET = 5
N_BINS = 64


def _worker(args):
    sa, sc, cond, so, wi = args
    pid = os.getpid()
    print(f'  [PID {pid}] start atom={sa} cond={cond} other={so} wi={wi}', flush=True)
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

    def shuffled_targets(atom, sa, so_, K=K_TARGET):
        """shuffled_other = alive_n からランダム K (中身を捨てる、sanity check)
        shuffle seed = (atom_seed × 13 + other_seed + 7) で state 由来"""
        alive = sorted(atom.state.alive_n)
        if len(alive) <= K: return alive
        sf_seed = (sa * 13 + so_ + 7) % (2**32)
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
    for w in range(WINDOWS):
        atom.step_window(steps=WINDOW_STEPS)
        if center is not None:
            center.step_window(steps=WINDOW_STEPS)
        # 注入 (w == wi == W_INJECT)
        if cond != 'baseline' and wi is not None and w == wi:
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
                        # 中身を捨てて alive_n からランダム K
                        targets = shuffled_targets(atom, sa, so, K_TARGET)
                        if targets:
                            atom.physics.inject(atom.state, target_nodes=targets)
        # k=K_OBSERVE の window で出口偏り snapshot
        if cond != 'baseline':
            target_w = wi + K_OBSERVE if wi is not None else None
        else:
            target_w = W_INJECT_LIST[0] + K_OBSERVE  # baseline は wi=2 相当で観察
        if w == target_w:
            # この時点の occupancy を記録
            occ_at_observe = list(atom.virtual.occupancy)
            labels_total = sum(1 for lid in atom.virtual.labels
                                if lid not in atom.virtual.macro_nodes)
            alive_l_count = len(atom.state.alive_l)
            share_max = max([lab['share'] for lid, lab in atom.virtual.labels.items()
                              if lid not in atom.virtual.macro_nodes], default=0.0)
            break

    if 'occ_at_observe' not in dir():
        occ_at_observe = list(atom.virtual.occupancy)
        labels_total = 0
        alive_l_count = 0
        share_max = 0.0

    dt = time.time() - t0
    print(f'  [PID {pid}] done atom={sa} cond={cond} other={so} wi={wi} ({dt:.0f}s)',
          flush=True)
    return {
        'atom_seed': sa, 'condition': cond,
        'other_seed': so if so is not None else -1,
        'w_inject': wi if wi is not None else -1,
        'target_phase': target_phase if target_phase is not None else -999,
        'labels_total': labels_total,
        'alive_l_count': alive_l_count,
        'share_max': share_max,
        'occupancy': occ_at_observe,
    }


def make_tasks():
    """42 unique tasks: 3 atom × 14 conditions"""
    tasks = []
    for sa, sc in zip(ATOM_SEEDS, CENTER_SEEDS):
        # baseline (Other 不要、wi 不要)
        tasks.append((sa, sc, 'baseline', None, None))
        # injected_self (Other 不要、wi=2 固定)
        tasks.append((sa, sc, 'injected_self', None, 2))
        # injected_other (Other × W_INJECT)
        for so in OTHER_SEEDS:
            for wi in W_INJECT_LIST:
                tasks.append((sa, sc, 'injected_other', so, wi))
        # shuffled_other (Other × W_INJECT)
        for so in OTHER_SEEDS:
            for wi in W_INJECT_LIST:
                tasks.append((sa, sc, 'shuffled_other', so, wi))
    return tasks


def distance_pair(dp1, dp2):
    dp1 = np.asarray(dp1, dtype=float); dp2 = np.asarray(dp2, dtype=float)
    eu = float(np.linalg.norm(dp1 - dp2))
    n1 = float(np.linalg.norm(dp1)); n2 = float(np.linalg.norm(dp2))
    if n1 < 1e-12 or n2 < 1e-12:
        cos = 1.0 if (n1 + n2) > 0 else 0.0
    else:
        cos = 1.0 - float(np.dot(dp1, dp2) / (n1 * n2))
    return {'eu': eu, 'cos': cos}


def main():
    print('=== v1111b — 出口偏りの形 × Other 次第性 ===\n')
    tasks = make_tasks()
    print(f'  Tasks: {len(tasks)} unique')
    print(f'  ATOM_SEEDS={ATOM_SEEDS}, OTHER_SEEDS={OTHER_SEEDS}')
    print(f'  W_INJECT_LIST={W_INJECT_LIST}, K_OBSERVE={K_OBSERVE}, WINDOWS={WINDOWS}')
    print(f'  並列: Pool(24)\n')

    t_main = time.time()
    with Pool(processes=24) as pool:
        results = pool.map(_worker, tasks)
    results_df = pd.DataFrame([{
        'atom_seed': r['atom_seed'], 'condition': r['condition'],
        'other_seed': r['other_seed'], 'w_inject': r['w_inject'],
        'target_phase': r['target_phase'],
        'labels_total': r['labels_total'],
        'alive_l_count': r['alive_l_count'],
        'share_max': r['share_max'],
    } for r in results])
    results_df.to_parquet(OUT_DIR / 'tasks_results.parquet', index=False)

    # ΔP = occupancy_injected - occupancy_baseline (per atom)
    occ_by_key = {}
    for r in results:
        key = (r['atom_seed'], r['condition'], r['other_seed'], r['w_inject'])
        occ_by_key[key] = np.array(r['occupancy'])

    baseline_occ_per_atom = {}
    for sa in ATOM_SEEDS:
        baseline_occ_per_atom[sa] = occ_by_key[(sa, 'baseline', -1, -1)]

    # ΔP 計算
    dp_records = []
    for r in results:
        if r['condition'] == 'baseline':
            continue
        sa = r['atom_seed']
        dp = occ_by_key[(sa, r['condition'], r['other_seed'], r['w_inject'])] \
              - baseline_occ_per_atom[sa]
        dp_records.append({
            'atom_seed': sa, 'condition': r['condition'],
            'other_seed': r['other_seed'], 'w_inject': r['w_inject'],
            'dp_norm': float(np.linalg.norm(dp)),
            'dp_sum_abs': float(np.abs(dp).sum()),
            'dp': dp.tolist(),
        })
    dp_df = pd.DataFrame([{k: v for k, v in d.items() if k != 'dp'}
                           for d in dp_records])
    dp_df.to_parquet(OUT_DIR / 'dp_records.parquet', index=False)

    # 入れ子判定 (per atom)
    print('\n=== 入れ子判定 (per atom) ===')
    nesting = []
    for sa in ATOM_SEEDS:
        # injected_other の dp を Other ごとに 2 reps 集める
        dp_per_other = {}
        for so in OTHER_SEEDS:
            reps = [d['dp'] for d in dp_records
                     if d['atom_seed'] == sa and d['condition'] == 'injected_other'
                     and d['other_seed'] == so]
            if len(reps) == 2:
                dp_per_other[so] = reps

        # 内ブレ δ_repeat (per Other、cos)
        delta_repeats = []
        for so, reps in dp_per_other.items():
            d = distance_pair(reps[0], reps[1])
            delta_repeats.append({'other': so, 'eu': d['eu'], 'cos': d['cos']})

        # 間距離 d_between (Other ペア)
        dp_per_other_mean = {so: np.mean(reps, axis=0)
                              for so, reps in dp_per_other.items()}
        d_betweens = []
        seeds = list(dp_per_other.keys())
        for i in range(len(seeds)):
            for j in range(i + 1, len(seeds)):
                d = distance_pair(dp_per_other_mean[seeds[i]],
                                   dp_per_other_mean[seeds[j]])
                d_betweens.append({'pair': f'{seeds[i]}_vs_{seeds[j]}',
                                    'eu': d['eu'], 'cos': d['cos']})

        # self 床
        self_dp = next(d['dp'] for d in dp_records
                        if d['atom_seed'] == sa and d['condition'] == 'injected_self')
        d_self_to_other = [distance_pair(self_dp, dp_per_other_mean[so])['cos']
                            for so in dp_per_other_mean]

        # 入れ子: max(δ_repeat_cos) < min(d_between_cos)
        repeat_cos = [d['cos'] for d in delta_repeats]
        between_cos = [d['cos'] for d in d_betweens]
        nested_strict = (max(repeat_cos) < min(between_cos)) if repeat_cos and between_cos else False
        nested_mean = (np.mean(repeat_cos) < np.mean(between_cos)) if repeat_cos and between_cos else False

        # shuffled_other の同じ計算 (sanity)
        dp_per_other_shuf = {}
        for so in OTHER_SEEDS:
            reps = [d['dp'] for d in dp_records
                     if d['atom_seed'] == sa and d['condition'] == 'shuffled_other'
                     and d['other_seed'] == so]
            if len(reps) == 2:
                dp_per_other_shuf[so] = reps
        delta_repeats_shuf = []
        for so, reps in dp_per_other_shuf.items():
            d = distance_pair(reps[0], reps[1])
            delta_repeats_shuf.append(d['cos'])
        dp_per_other_shuf_mean = {so: np.mean(reps, axis=0)
                                    for so, reps in dp_per_other_shuf.items()}
        d_betweens_shuf = []
        seeds_shuf = list(dp_per_other_shuf.keys())
        for i in range(len(seeds_shuf)):
            for j in range(i + 1, len(seeds_shuf)):
                d = distance_pair(dp_per_other_shuf_mean[seeds_shuf[i]],
                                   dp_per_other_shuf_mean[seeds_shuf[j]])
                d_betweens_shuf.append(d['cos'])
        nested_strict_shuf = (max(delta_repeats_shuf) < min(d_betweens_shuf)) \
                              if delta_repeats_shuf and d_betweens_shuf else False
        nested_mean_shuf = (np.mean(delta_repeats_shuf) < np.mean(d_betweens_shuf)) \
                            if delta_repeats_shuf and d_betweens_shuf else False

        record = {
            'atom_seed': sa,
            'delta_repeat_cos_mean': float(np.mean(repeat_cos)) if repeat_cos else 0.0,
            'delta_repeat_cos_max': float(max(repeat_cos)) if repeat_cos else 0.0,
            'd_between_cos_mean': float(np.mean(between_cos)) if between_cos else 0.0,
            'd_between_cos_min': float(min(between_cos)) if between_cos else 0.0,
            'nested_strict': bool(nested_strict),
            'nested_mean': bool(nested_mean),
            'd_self_to_other_cos_mean': float(np.mean(d_self_to_other))
                                          if d_self_to_other else 0.0,
            # shuffled sanity
            'delta_repeat_cos_mean_shuf': float(np.mean(delta_repeats_shuf))
                                            if delta_repeats_shuf else 0.0,
            'd_between_cos_mean_shuf': float(np.mean(d_betweens_shuf))
                                        if d_betweens_shuf else 0.0,
            'nested_strict_shuf': bool(nested_strict_shuf),
            'nested_mean_shuf': bool(nested_mean_shuf),
        }
        nesting.append(record)
        print(f'\n  [atom={sa}]')
        print(f'    injected_other:')
        print(f'      δ_repeat (cos): mean={record["delta_repeat_cos_mean"]:.4f} '
              f'max={record["delta_repeat_cos_max"]:.4f}')
        print(f'      d_between (cos): mean={record["d_between_cos_mean"]:.4f} '
              f'min={record["d_between_cos_min"]:.4f}')
        print(f'      nested_strict (max_δ < min_d): {nested_strict}')
        print(f'      nested_mean  (mean_δ < mean_d): {nested_mean}')
        print(f'      d_self_to_other (cos): {record["d_self_to_other_cos_mean"]:.4f}')
        print(f'    shuffled_other (sanity):')
        print(f'      δ_repeat_shuf (cos): mean={record["delta_repeat_cos_mean_shuf"]:.4f}')
        print(f'      d_between_shuf (cos): mean={record["d_between_cos_mean_shuf"]:.4f}')
        print(f'      nested_strict_shuf: {nested_strict_shuf}')
        print(f'      nested_mean_shuf:   {nested_mean_shuf}')

    nesting_df = pd.DataFrame(nesting)
    nesting_df.to_parquet(OUT_DIR / 'nesting.parquet', index=False)

    # 3 atom seeds 共通: 入れ子が全 atom で True か (再現性)
    print('\n=== 3 atom seeds 共通の足跡 ===')
    n_strict_main = sum(1 for r in nesting if r['nested_strict'])
    n_mean_main = sum(1 for r in nesting if r['nested_mean'])
    n_strict_shuf = sum(1 for r in nesting if r['nested_strict_shuf'])
    n_mean_shuf = sum(1 for r in nesting if r['nested_mean_shuf'])
    print(f'  injected_other nested_strict: {n_strict_main}/{len(nesting)} atoms')
    print(f'  injected_other nested_mean:   {n_mean_main}/{len(nesting)} atoms')
    print(f'  shuffled_other nested_strict: {n_strict_shuf}/{len(nesting)} atoms')
    print(f'  shuffled_other nested_mean:   {n_mean_shuf}/{len(nesting)} atoms')

    # Web Claude §2.4 切り分け: shuffled で nesting 消えれば中身由来、出れば seed 差ノイズ
    print('\n=== Web Claude §2.4 sanity 切り分け ===')
    if n_mean_main >= 2 and n_mean_shuf < n_mean_main:
        print(f'  shuffled で nesting が消える方向 → 中身由来候補 (Unified の核成立候補)')
    elif n_mean_main >= 2 and n_mean_shuf >= n_mean_main:
        print(f'  shuffled でも nesting が同等以上 → seed 差ノイズ疑い')
    elif n_mean_main < 2:
        print(f'  injected_other 自体に nesting なし → Other の中身が出口層に届かず')

    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'ATOM_SEEDS': ATOM_SEEDS, 'OTHER_SEEDS': OTHER_SEEDS,
        'W_INJECT_LIST': W_INJECT_LIST, 'K_OBSERVE': K_OBSERVE,
        'WINDOWS': WINDOWS, 'WINDOW_STEPS': WINDOW_STEPS,
        'n_tasks': len(tasks),
        'total_sec': time.time() - t_main,
    }
    (OUT_DIR / 'summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n=== v1111b 完了 total {time.time()-t_main:.1f}s ===')


if __name__ == '__main__':
    main()
