#!/usr/bin/env python3
"""v1111 Step 1 — diff トレース (3 seeds × 3 conditions × reach 段階 × k 系列)

Web Claude v1111 §4 やる順 2-3:
- diff トレース機構 (同 seed で baseline vs injected_self vs injected_other を 1 注入で比較)
- 3 conditions × 3 seeds = 9 並列タスク
- 段階化 reach (空間 / 構造 / 出口) × k=1, 3, 5, 10 windows
- 単一 seed crown しない、self/other 相対基準
- 固定値ゼロ (ε 使わず Δ ≠ 0 で全集計、self 条件を相対基準に)

注入: w_inject=2 で 1 回のみ (ATTENTION 半減期 0.69w 超、まだ初期)
観察: w_inject 後 k=1, 3, 5, 10 windows (FAMILIARITY 半減期 3.46w × ~3 で k=10 まで)
総 windows: 2 + 10 = 12
"""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

import sys, json, time, math
from pathlib import Path
from multiprocessing import Pool
from collections import deque
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
STAGE5 = REPO / 'unified/attention_center_prep'
OUT_DIR = STAGE5 / 'run_v1111_step1'
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

# seed sets (Other=100 固定で Atom のみ変動、Other seed の特異性反省)
SEED_SETS = [
    {'atom': 42,  'center': 99,  'other': 100},
    {'atom': 100, 'center': 157, 'other': 100},
    {'atom': 200, 'center': 217, 'other': 100},
]
W_INJECT = 2  # ATTENTION 半減期 0.69w 超
K_LIST = [1, 3, 5, 10]  # 観察 windows
WINDOWS = W_INJECT + max(K_LIST) + 1  # 13 windows (w_inject + k_max + buffer)
WINDOW_STEPS = 100
OTHER_STEPS = 5
K_TARGET = 5
N_BINS = 64


def _worker(args):
    seed_set, cond = args
    sa = seed_set['atom']; sc = seed_set['center']; so = seed_set['other']
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

    def should_attend(c):
        if not c.state.alive_n: return False, {}
        E = np.array([c.state.E.get(n, 0.0) for n in c.state.alive_n])
        if len(E) < 2: return False, {}
        m = float(E.mean()); s = float(E.std())
        if s < 1e-9: return False, {}
        z = (float(E.max()) - m) / s
        st = float((c.stress_stats or {}).get('stress_intensity', 1.0))
        return z > st, {'z_score': z, 'stress': st}

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

    def snapshot(atom):
        """各 window 末の state snapshot"""
        return {
            'E': dict(atom.state.E),
            'theta': atom.state.theta.copy(),
            'alive_n': set(atom.state.alive_n),
            'alive_l': set(atom.state.alive_l),
            'labels_nodes': {lid: frozenset(lab['nodes'])
                              for lid, lab in atom.virtual.labels.items()},
            'labels_phase_sig': {lid: lab['phase_sig']
                                  for lid, lab in atom.virtual.labels.items()},
            'labels_share': {lid: lab['share']
                              for lid, lab in atom.virtual.labels.items()},
            'occupancy': list(atom.virtual.occupancy),
        }

    # メイン処理: 12 windows、w_inject=W_INJECT で 1 回だけ inject
    atom = build_engine(sa)
    center = build_engine(sc)
    other = build_engine(so) if cond == 'injected_other' else None

    snapshots = []
    injected_target_nodes = None  # 注入 node 記録 (構造 reach 用)
    target_phase_at_inject = None

    for w in range(WINDOWS):
        atom.step_window(steps=WINDOW_STEPS)
        center.step_window(steps=WINDOW_STEPS)
        # 1 回だけ注入 (w == W_INJECT)
        if w == W_INJECT and cond in ('injected_self', 'injected_other'):
            fire, _ = should_attend(center)
            if fire:
                tp = derive_tp(center, K_TARGET)
                if tp is not None:
                    lam = lam_dyn(center)
                    weights = label_weights(atom, tp, lam)
                    targets = targets_from_w(weights, atom, K_TARGET)
                    if targets:
                        target_phase_at_inject = float(tp)
                        if cond == 'injected_other':
                            other.physics.inject(other.state, target_nodes=list(targets))
                            other.step_window(steps=OTHER_STEPS)
                            new_targets = trans_other(other, K_TARGET)
                        else:
                            new_targets = targets
                        if new_targets:
                            atom.physics.inject(atom.state, target_nodes=new_targets)
                            injected_target_nodes = list(new_targets)
        snapshots.append(snapshot(atom))

    dt = time.time() - t0
    print(f'  [PID {pid}] done atom={sa} cond={cond} ({dt:.0f}s)', flush=True)

    return {
        'seed_atom': sa, 'condition': cond,
        'injected_target_nodes': injected_target_nodes,
        'target_phase_at_inject': target_phase_at_inject,
        'snapshots': snapshots,
    }


def bfs_hops(alive_n_set, neighbors_fn, source_nodes, max_hops=15):
    """注入 node からの最短 link ホップ距離 BFS
    alive_n_set: 生存 node の set
    neighbors_fn: (n) -> [nb1, nb2, ...] の関数
    """
    hops = {n: 0 for n in source_nodes if n in alive_n_set}
    frontier = list(hops.keys())
    for h in range(1, max_hops + 1):
        next_frontier = []
        for n in frontier:
            for nb in neighbors_fn(n):
                if nb in alive_n_set and nb not in hops:
                    hops[nb] = h
                    next_frontier.append(nb)
        if not next_frontier: break
        frontier = next_frontier
    return hops


def build_neighbors_from_alive_l(alive_l):
    """alive_l (set of (i,j)) から隣接リスト構築"""
    nb = {}
    for (i, j) in alive_l:
        nb.setdefault(i, set()).add(j)
        nb.setdefault(j, set()).add(i)
    def get_nb(n):
        return nb.get(n, set())
    return get_nb


def circular_distance(a, b):
    d = abs(a - b) % (2*math.pi)
    return min(d, 2*math.pi - d)


def compute_reach_metrics(baseline_snap, injected_snap, target_nodes,
                            target_phase, k_window):
    """3 reach 段階の指標を計算 (固定値ゼロ、ε 使わず Δ ≠ 0 で集計)"""
    # 入口 reach: E の差分
    dE = {}
    for n in injected_snap['alive_n']:
        b_e = baseline_snap['E'].get(n, 0.0)
        i_e = injected_snap['E'].get(n, 0.0)
        d = i_e - b_e
        if d != 0.0:  # ε 使わず、Δ ≠ 0 で全集計
            dE[n] = d
    n_nonzero = len(dE)
    sum_abs_dE = sum(abs(v) for v in dE.values())

    # 空間 reach: BFS hops 分布
    # alive_l は injected 側の alive_l を使う (注入で増えた link を含む)
    nb_fn = build_neighbors_from_alive_l(injected_snap['alive_l'])
    hops_map = bfs_hops(injected_snap['alive_n'], nb_fn, target_nodes or [])
    # ΔE ≠ 0 node の hops 分布
    hop_distrib = {}
    for n, d in dE.items():
        h = hops_map.get(n)
        if h is not None:
            hop_distrib[h] = hop_distrib.get(h, 0.0) + abs(d)
    # hop 中央値 (重み付き)
    if dE:
        sorted_hops = sorted([(hops_map.get(n, -1), abs(d)) for n, d in dE.items()
                                if hops_map.get(n) is not None])
        if sorted_hops:
            total = sum(w for _, w in sorted_hops)
            cum = 0
            median_hop = -1
            for h, w in sorted_hops:
                cum += w
                if cum >= total / 2:
                    median_hop = h
                    break
        else:
            median_hop = -1
    else:
        median_hop = -1
    max_hop_with_change = max(hop_distrib.keys()) if hop_distrib else -1

    # 構造 reach: 同一/結合 CID 内の |dE| 割合
    target_set = set(target_nodes or [])
    # 注入 node の所属 label (injected_snap 側)
    same_or_linked_lids = set()
    if target_set:
        for lid, nodes in injected_snap['labels_nodes'].items():
            if nodes & target_set:
                same_or_linked_lids.add(lid)
        # 結合 CID = phase_sig が circular_distance < BIN_WIDTH × 3 (state 由来基準)
        if same_or_linked_lids and target_phase is not None:
            bin_width = 2 * math.pi / N_BINS
            threshold_phase = bin_width * 3  # 3 bins 範囲 (Web Claude K_NEAR と整合)
            target_phase_sigs = [injected_snap['labels_phase_sig'][lid]
                                  for lid in same_or_linked_lids]
            for lid, ps in injected_snap['labels_phase_sig'].items():
                if lid in same_or_linked_lids: continue
                for tps in target_phase_sigs:
                    if circular_distance(ps, tps) < threshold_phase:
                        same_or_linked_lids.add(lid)
                        break
    # 同一/結合 CID 内の node 集合
    cid_in_nodes = set()
    for lid in same_or_linked_lids:
        cid_in_nodes |= injected_snap['labels_nodes'][lid]
    sum_abs_dE_cid = sum(abs(v) for n, v in dE.items() if n in cid_in_nodes)
    struct_survival_ratio = (sum_abs_dE_cid / sum_abs_dE) if sum_abs_dE > 0 else 0.0

    # 出口 reach: 注入位相帯外の occ 差分絶対値和
    if target_phase is not None and injected_snap['occupancy'] and baseline_snap['occupancy']:
        bin_width = 2 * math.pi / N_BINS
        target_bin = min(int(target_phase / bin_width), N_BINS - 1)
        K_NEAR = 3
        injected_band = set((target_bin + d) % N_BINS for d in range(-K_NEAR, K_NEAR + 1))
        docc = [(i - b) for i, b in zip(injected_snap['occupancy'],
                                          baseline_snap['occupancy'])]
        outer_abs_docc_sum = sum(abs(docc[b]) for b in range(N_BINS) if b not in injected_band)
        inner_abs_docc_sum = sum(abs(docc[b]) for b in range(N_BINS) if b in injected_band)
        total_abs_docc = sum(abs(d) for d in docc)
    else:
        outer_abs_docc_sum = 0.0
        inner_abs_docc_sum = 0.0
        total_abs_docc = 0.0

    return {
        'k': k_window,
        'n_nonzero_dE': n_nonzero,
        'sum_abs_dE': sum_abs_dE,
        'median_hop': median_hop,
        'max_hop_with_change': max_hop_with_change,
        'hop_distrib_str': json.dumps({int(h): float(v) for h, v in hop_distrib.items()}),
        'n_cid_in_nodes': len(cid_in_nodes),
        'n_same_or_linked_lids': len(same_or_linked_lids),
        'sum_abs_dE_cid': sum_abs_dE_cid,
        'struct_survival_ratio': struct_survival_ratio,
        'outer_abs_docc_sum': outer_abs_docc_sum,
        'inner_abs_docc_sum': inner_abs_docc_sum,
        'total_abs_docc': total_abs_docc,
    }


def main():
    print('=== v1111 Step 1 — diff トレース 9 並列 ===\n')
    print(f'  3 seeds × 3 conditions = 9 tasks, W_INJECT={W_INJECT}, K={K_LIST}, WINDOWS={WINDOWS}\n')
    t_main = time.time()

    tasks = []
    for ss in SEED_SETS:
        for cond in ['baseline', 'injected_self', 'injected_other']:
            tasks.append((ss, cond))

    with Pool(processes=9) as pool:
        results = pool.map(_worker, tasks)

    # 結果を seed×condition で索引化
    result_dict = {}
    for r in results:
        sa = r['seed_atom']; cond = r['condition']
        result_dict[(sa, cond)] = r

    # reach 計算 (各 seed × condition × k で baseline と比較)
    print('\n=== reach 計算 (各 seed × condition × k) ===')
    rows = []
    for sa in [s['atom'] for s in SEED_SETS]:
        baseline_r = result_dict.get((sa, 'baseline'))
        if baseline_r is None: continue
        for cond in ['injected_self', 'injected_other']:
            injected_r = result_dict.get((sa, cond))
            if injected_r is None: continue
            target_nodes = injected_r.get('injected_target_nodes')
            target_phase = injected_r.get('target_phase_at_inject')
            for k in K_LIST:
                w_obs = W_INJECT + k
                if w_obs >= len(baseline_r['snapshots']): continue
                baseline_snap = baseline_r['snapshots'][w_obs]
                injected_snap = injected_r['snapshots'][w_obs]
                metrics = compute_reach_metrics(
                    baseline_snap, injected_snap, target_nodes, target_phase, k)
                rows.append({
                    'seed_atom': sa, 'condition': cond, 'k': k,
                    'target_phase': target_phase,
                    'n_target': len(target_nodes) if target_nodes else 0,
                    **metrics,
                })
                print(f'  atom={sa} {cond} k={k}: '
                      f'n_nonzero_dE={metrics["n_nonzero_dE"]} '
                      f'sum_|dE|={metrics["sum_abs_dE"]:.4f} '
                      f'median_hop={metrics["median_hop"]} '
                      f'max_hop={metrics["max_hop_with_change"]} '
                      f'struct_ratio={metrics["struct_survival_ratio"]:.3f} '
                      f'outer_|docc|={metrics["outer_abs_docc_sum"]:.4f}')
    rdf = pd.DataFrame(rows)
    rdf.to_parquet(OUT_DIR / 'reach_metrics.parquet', index=False)

    # other/self 相対 (Web Claude §2.4 (b))
    print('\n=== other/self 相対比較 (seed × k) ===')
    rel_rows = []
    for sa in [s['atom'] for s in SEED_SETS]:
        for k in K_LIST:
            self_r = rdf[(rdf['seed_atom']==sa) & (rdf['condition']=='injected_self')
                          & (rdf['k']==k)]
            other_r = rdf[(rdf['seed_atom']==sa) & (rdf['condition']=='injected_other')
                            & (rdf['k']==k)]
            if len(self_r) == 0 or len(other_r) == 0: continue
            s = self_r.iloc[0]; o = other_r.iloc[0]
            KEYS = ['n_nonzero_dE', 'sum_abs_dE', 'max_hop_with_change',
                    'struct_survival_ratio', 'outer_abs_docc_sum',
                    'total_abs_docc']
            r = {'seed_atom': sa, 'k': k}
            for kf in KEYS:
                sv = float(s[kf]); ov = float(o[kf])
                ratio_oth_to_slf = ov / (abs(sv) + 1e-9)
                r[f'{kf}_self'] = sv
                r[f'{kf}_other'] = ov
                r[f'{kf}_other_over_self'] = ratio_oth_to_slf
                r[f'{kf}_other_gt_self'] = bool(ov > sv)
            rel_rows.append(r)
    rel_df = pd.DataFrame(rel_rows)
    rel_df.to_parquet(OUT_DIR / 'reach_relative.parquet', index=False)

    print('\n=== other/self relative ratios (k=1, 3, 5, 10) ===')
    for k in K_LIST:
        sub = rel_df[rel_df['k']==k]
        if len(sub) == 0: continue
        print(f'\n  --- k={k} ---')
        for kf in ['n_nonzero_dE', 'sum_abs_dE', 'max_hop_with_change',
                   'struct_survival_ratio', 'outer_abs_docc_sum']:
            col = f'{kf}_other_over_self'
            mean = sub[col].mean()
            n_other_gt = sub[f'{kf}_other_gt_self'].sum()
            print(f'    {kf:30s} other/self mean={mean:.3f}, '
                  f'other>self in {int(n_other_gt)}/{len(sub)} seeds')

    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'seed_sets': SEED_SETS, 'W_INJECT': W_INJECT, 'K_LIST': K_LIST,
        'WINDOWS': WINDOWS, 'WINDOW_STEPS': WINDOW_STEPS,
        'total_sec': time.time() - t_main,
    }
    (OUT_DIR / 'step1_summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n=== Step 1 完了 total {time.time()-t_main:.1f}s ===')


if __name__ == '__main__':
    main()
