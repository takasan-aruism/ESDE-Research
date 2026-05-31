#!/usr/bin/env python3
"""注意センター Step C — Other seed 影響度 4 runs 並列 (再現 + abc)

Taka 指示 (2026-06-01):
- 多 seed +64% 再現せず、原因 = Other seed が 100→101 に変わっていた
- 再現確認 + abc 全て実施

4 runs:
- Run 1 再現確認: (atom=42, center=99, other=100) で +64% が再現するか
- Run 2 案 a: Other = Atom + 58 (規則化、3 seed_sets)
- Run 3 案 b: Other = 100 固定 (3 seed_sets で Atom/Center 変動、Other 固定)
- Run 4 案 c: Atom=42, Center=99 固定、Other = 100/101/102 で影響度直接観察

Unique task 数:
- Run 1: 3 tasks (no/cn/co、atom=42, center=99, other=100)
- Run 2: 9 (Run 1 と seed_set_0 重複 3 → +6 unique)
- Run 3: 9 (Run 1 と seed_set_0 重複 3 → +6 unique)
- Run 4: 5 (Run 1 と 3 重複 → +2 unique: other=101, 102)
- Total unique = 17 tasks

並列: Pool(17) で 24 cores 中の 17 並列
推定 ~20 分 (Step C multi seed 並列と同等)
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
OUT_DIR = STAGE5 / 'run_other_seed_4runs'
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

WINDOWS = 15
WINDOW_STEPS = 100
OTHER_STEPS = 5
K_TARGET = 5
K_NEAR = 3
N_BINS = 64


def _worker(args):
    sa, sc, so, cond = args
    pid = os.getpid()
    print(f'  [PID {pid}] start a={sa} c={sc} o={so} cond={cond}', flush=True)
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
        if not c.state.alive_n: return False, {'z_score': 0.0, 'stress': 0.0}
        E = np.array([c.state.E.get(n, 0.0) for n in c.state.alive_n])
        if len(E) < 2: return False, {'z_score': 0.0, 'stress': 0.0}
        m = float(E.mean()); s = float(E.std())
        if s < 1e-9: return False, {'z_score': 0.0, 'stress': 0.0}
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

    def att_loop(center, atom, other, w, use_other):
        fire, fi = should_attend(center)
        info = {'window': w, 'fired': False, 'target_phase': None, **fi}
        if not fire: return info
        tp = derive_tp(center, K_TARGET)
        if tp is None:
            info['fired'] = True; return info
        lam = lam_dyn(center)
        wts = label_weights(atom, tp, lam)
        tgts = targets_from_w(wts, atom, K_TARGET)
        info.update({'fired': True, 'target_phase': float(tp)})
        if not tgts: return info
        if use_other:
            other.physics.inject(other.state, target_nodes=list(tgts))
            other.step_window(steps=OTHER_STEPS)
            nt = trans_other(other, K_TARGET)
        else:
            nt = tgts
        if nt:
            atom.physics.inject(atom.state, target_nodes=nt)
        return info

    def update_cm(cm, tp, KN=K_NEAR):
        if tp is None: return
        bw = 2*math.pi / N_BINS
        tb = min(int(tp/bw), N_BINS-1)
        for d in range(-KN, KN+1):
            cm[(tb+d) % N_BINS] += 1

    def stratify(occ, cm, top_q=0.25):
        if not occ or len(occ) != N_BINS:
            return {'high_occ_sum': 0.0, 'low_occ_sum': 0.0, 'high_low_ratio': 0.0}
        sb = np.argsort(-cm)
        nt = max(1, int(N_BINS*top_q))
        high = set(sb[:nt].tolist()); low = set(sb[-nt:].tolist())
        hs = sum(occ[b] for b in high); ls = sum(occ[b] for b in low)
        return {'high_occ_sum': float(hs), 'low_occ_sum': float(ls),
                'high_low_ratio': float(hs/(ls+1e-9))}

    def obs_fn(atom, cm):
        macro = set(atom.virtual.macro_nodes)
        nm = [l for lid, l in atom.virtual.labels.items() if lid not in macro]
        occ = atom.virtual.occupancy or []
        vs = atom.virtual_stats or {}
        o = {
            'labels_total': len(nm),
            'alive_l_count': len(atom.state.alive_l),
            'torque_events': vs.get('torque_events', 0),
            'share_max': max([l['share'] for l in nm], default=0.0),
        }
        o.update(stratify(occ, cm, 0.25))
        return o

    atom = build_engine(sa)
    center = None; other = None
    if cond in ('center_no_other', 'center_other'):
        center = build_engine(sc)
    if cond == 'center_other':
        other = build_engine(so)
    cm = np.zeros(N_BINS)
    rows = []
    for w in range(WINDOWS):
        atom.step_window(steps=WINDOW_STEPS)
        if center is not None:
            center.step_window(steps=WINDOW_STEPS)
            uo = (cond == 'center_other')
            li = att_loop(center, atom, other, w, uo)
            if li['fired'] and li['target_phase'] is not None:
                update_cm(cm, li['target_phase'], K_NEAR)
        o = obs_fn(atom, cm)
        rows.append({'seed_atom': sa, 'seed_center': sc, 'seed_other': so,
                      'condition': cond, 'window': w, **o})
    dt = time.time() - t0
    print(f'  [PID {pid}] done a={sa} c={sc} o={so} cond={cond} ({dt:.0f}s) '
          f'final ratio={rows[-1]["high_low_ratio"]:.3f}', flush=True)
    return pd.DataFrame(rows)


def make_unique_tasks():
    """4 runs を統合し unique tasks を返す"""
    raw = []
    # Run 1: 再現確認 (atom=42, center=99, other=100)
    for cond in ['no_center', 'center_no_other', 'center_other']:
        raw.append((42, 99, 100, cond))
    # Run 2 案 a: Other = Atom + 58
    for sa, sc in [(42, 99), (100, 157), (200, 217)]:
        for cond in ['no_center', 'center_no_other', 'center_other']:
            raw.append((sa, sc, sa+58, cond))
    # Run 3 案 b: Other = 100 固定
    for sa, sc in [(42, 99), (100, 157), (200, 217)]:
        for cond in ['no_center', 'center_no_other', 'center_other']:
            raw.append((sa, sc, 100, cond))
    # Run 4 案 c: Atom=42, Center=99 固定、Other 変動
    for cond in ['no_center', 'center_no_other']:
        raw.append((42, 99, 100, cond))  # Other は使わないが key 用
    for o in [100, 101, 102]:
        raw.append((42, 99, o, 'center_other'))

    # unique 削減
    unique = []
    seen = set()
    for k in raw:
        if k not in seen:
            seen.add(k)
            unique.append(k)
    return unique, raw


def main():
    print('=== Other seed 4 runs 並列実行 (再現 + abc) ===\n')
    unique, raw = make_unique_tasks()
    print(f'  Raw tasks: {len(raw)}, Unique tasks: {len(unique)}')
    print(f'  WINDOWS={WINDOWS}, K_NEAR={K_NEAR}')
    print(f'  並列数: {min(len(unique), 24)} processes\n')

    t_main = time.time()
    n_par = min(len(unique), 24)
    with Pool(processes=n_par) as pool:
        results = pool.map(_worker, unique)
    full = pd.concat(results, ignore_index=True)
    full.to_parquet(OUT_DIR / 'other_seed_4runs_full.parquet', index=False)

    # 集計: 最終 window の (seed_atom, seed_center, seed_other, condition) -> high_low_ratio
    last = full[full['window'] == WINDOWS - 1].copy()
    print('\n=== 最終 window high_low_ratio (a, c, o, cond) ===')
    print(last[['seed_atom', 'seed_center', 'seed_other', 'condition',
                 'high_low_ratio', 'labels_total', 'torque_events',
                 'share_max']].to_string(index=False))

    # 4 runs 個別集計
    print('\n\n========== Run 1: 再現確認 (atom=42, center=99, other=100) ==========')
    for cond in ['no_center', 'center_no_other', 'center_other']:
        r = last[(last['seed_atom']==42) & (last['seed_center']==99) &
                  (last['seed_other']==100) & (last['condition']==cond)]
        if len(r) > 0:
            row = r.iloc[0]
            print(f'  {cond:20s} ratio={row["high_low_ratio"]:.4f} '
                  f'labels={int(row["labels_total"])} '
                  f'share_max={row["share_max"]:.4f}')
    # 帰属差分 (Run 1)
    co = last[(last['seed_atom']==42) & (last['seed_other']==100) &
               (last['condition']=='center_other')]
    cn = last[(last['seed_atom']==42) & (last['seed_other']==100) &
               (last['condition']=='center_no_other')]
    if len(co) > 0 and len(cn) > 0:
        d = float(co.iloc[0]['high_low_ratio']) - float(cn.iloc[0]['high_low_ratio'])
        rel = d / (abs(float(cn.iloc[0]['high_low_ratio'])) + 1e-9)
        print(f'  Run 1 帰属差分 high_low_ratio rel = {rel*100:+.2f}% (smoke 期待 +64.34%)')

    print('\n\n========== Run 2: 案 a Other=Atom+58 (3 seed_sets) ==========')
    KEYS = ['high_low_ratio', 'labels_total', 'torque_events', 'share_max']
    rows = []
    for sa, sc in [(42, 99), (100, 157), (200, 217)]:
        so = sa + 58
        co = last[(last['seed_atom']==sa) & (last['seed_other']==so) &
                   (last['condition']=='center_other')]
        cn = last[(last['seed_atom']==sa) & (last['seed_other']==so) &
                   (last['condition']=='center_no_other')]
        if len(co) > 0 and len(cn) > 0:
            r = {'seed_atom': sa, 'seed_other': so}
            for k in KEYS:
                d = float(co.iloc[0][k]) - float(cn.iloc[0][k])
                rel = d / (abs(float(cn.iloc[0][k])) + 1e-9)
                r[f'{k}_rel'] = rel * 100
            rows.append(r)
    df2 = pd.DataFrame(rows)
    print(df2.to_string(index=False))
    print('  3 seeds 平均 ± std:')
    for k in KEYS:
        col = f'{k}_rel'
        mean = df2[col].mean(); std = df2[col].std()
        signs = np.sign(df2[col].values)
        ss = bool(len(set(signs)) == 1)
        marker = '★' if ss and abs(mean) > 5 else ' '
        print(f'    {marker} {k:20s} = {mean:+.2f}% ± {std:.2f}% (same_sign={ss})')

    print('\n\n========== Run 3: 案 b Other=100 固定 (3 seed_sets) ==========')
    rows = []
    for sa, sc in [(42, 99), (100, 157), (200, 217)]:
        co = last[(last['seed_atom']==sa) & (last['seed_other']==100) &
                   (last['condition']=='center_other')]
        cn = last[(last['seed_atom']==sa) & (last['seed_other']==100) &
                   (last['condition']=='center_no_other')]
        if len(co) > 0 and len(cn) > 0:
            r = {'seed_atom': sa, 'seed_other': 100}
            for k in KEYS:
                d = float(co.iloc[0][k]) - float(cn.iloc[0][k])
                rel = d / (abs(float(cn.iloc[0][k])) + 1e-9)
                r[f'{k}_rel'] = rel * 100
            rows.append(r)
    df3 = pd.DataFrame(rows)
    print(df3.to_string(index=False))
    print('  3 seeds 平均 ± std:')
    for k in KEYS:
        col = f'{k}_rel'
        mean = df3[col].mean(); std = df3[col].std()
        signs = np.sign(df3[col].values)
        ss = bool(len(set(signs)) == 1)
        marker = '★' if ss and abs(mean) > 5 else ' '
        print(f'    {marker} {k:20s} = {mean:+.2f}% ± {std:.2f}% (same_sign={ss})')

    print('\n\n========== Run 4: 案 c Other 影響度 (atom=42, center=99, Other 変動) ==========')
    cn = last[(last['seed_atom']==42) & (last['seed_other']==100) &
               (last['condition']=='center_no_other')]
    if len(cn) > 0:
        cn_ratio = float(cn.iloc[0]['high_low_ratio'])
        cn_labels = float(cn.iloc[0]['labels_total'])
        cn_torque = float(cn.iloc[0]['torque_events'])
        cn_share = float(cn.iloc[0]['share_max'])
        print(f'  center_no_other (atom=42, other=100): '
              f'ratio={cn_ratio:.4f} labels={int(cn_labels)} '
              f'torque={int(cn_torque)} share_max={cn_share:.4f}')
        for o in [100, 101, 102]:
            co = last[(last['seed_atom']==42) & (last['seed_other']==o) &
                       (last['condition']=='center_other')]
            if len(co) > 0:
                row = co.iloc[0]
                d_r = float(row['high_low_ratio']) - cn_ratio
                rel_r = d_r / (abs(cn_ratio) + 1e-9) * 100
                d_l = float(row['labels_total']) - cn_labels
                rel_l = d_l / (abs(cn_labels) + 1e-9) * 100
                print(f'  center_other (other={o}):')
                print(f'    ratio={row["high_low_ratio"]:.4f} (Δrel={rel_r:+.2f}%)')
                print(f'    labels={int(row["labels_total"])} (Δrel={rel_l:+.2f}%)')
                print(f'    torque={int(row["torque_events"])} share_max={row["share_max"]:.4f}')

    summary = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'n_unique_tasks': len(unique),
        'n_raw_tasks': len(raw),
        'total_sec': time.time() - t_main,
    }
    (OUT_DIR / 'other_seed_4runs_summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n=== 4 runs 並列 完了 total {time.time()-t_main:.1f}s ===')


if __name__ == '__main__':
    main()
