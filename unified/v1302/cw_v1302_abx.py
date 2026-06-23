#!/usr/bin/env python3
"""v1302 (A)+(B)+canon 並走 smoke — 「誕生時に親の何を子に仕込むか」3条件を同一 step-0 枠で並走比較。

【観察対象注釈ブロック / 同系・異系宣言】
- 同系内: 親 seed0 CID の縮小子系(N≈B_gen×10, V82+V43 物理+VirtualLayerV9, stress/pressure OFF)。異系対応でない。
- 読=frozen: per_subject_seed0 / persistence(field 抽出は cw_v1302_field) / engine。親 read-only。
- 書=unified/v1302/ のみ(署名 parquet・summary)。親 physics/inject/ledger/state 非書込。移植は子 in-memory state への add_link のみ。
- 3条件: canon=fresh run_injection / (A)scalar=structural-strength(S/R/conc 等重み z→tanh)を初期 plb に / (B)topology=親コア+周辺 field(max_hops n_core+1)を add_link 移植(shape-only, S=0.3/E=0.6 fresh, θ既定, R内生)。
- K_sync/θ は3条件 canon 固定(seed_audit: 幻/雑音)。null=Mantel 行列置換(無料)。層化 n2 主+n5 補助。判定なし(Taka)。
"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1'); os.environ.setdefault('MKL_NUM_THREADS', '1'); os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import sys, time, json, hashlib, warnings
from pathlib import Path
import numpy as np, pandas as pd
import multiprocessing as mp
warnings.filterwarnings('ignore')
REPO = Path('/home/takasan/esde/ESDE-Research')
for p in ['autonomy/v82', 'ecology/engine', 'primitive/v910', 'cognition/semantic_injection/v4_pipeline/v43', 'unified/v1302']:
    sys.path.insert(0, str(REPO / p))
from esde_v82_engine import V82Engine, V82EncapsulationParams
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9
from cw_v1302_field import build_fields

RUN_LEN = int(os.environ.get('CW_RUNLEN', '35000'))   # step-0 並み
EARLY_LEN = 2000                                       # 早期署名(移植痕を残す時点)
BASE_PLB = 0.007
S_STR = 0.3                                            # plb 写像幅(step-0 と同形)
S_FRESH, E_FRESH = 0.3, 0.6                            # canon inject 値(B の shape-only fresh 埋め)
STRATA = ['2', '5']                                    # n2 主 + n5 補助
N_SEEDS = int(os.environ.get('CW_SEEDS', '2'))
CONDS = ['canon', 'A', 'B']
MANTEL_K = 999
N_WORKERS = max(1, (os.cpu_count() or 4) - 2)
OUT = REPO / 'unified/v1302'
SIG = ['n_labels', 'mean_size', 'std_size', 'share_gini', 'mean_age', 'lifecycle_events']


def gini(x):
    x = np.sort(np.asarray(x, float))
    if x.size == 0 or x.sum() <= 0:
        return 0.0
    n = x.size
    return float((2 * np.sum((np.arange(1, n + 1)) * x) - (n + 1) * x.sum()) / (n * x.sum()))


def load():
    """intersection CID(persistence あり)を集め、親値 + structural-strength + field を返す。"""
    d = pd.read_csv(REPO / 'primitive/v918/diag_v918_main/subjects/per_subject_seed0.csv')
    d['cognitive_id'] = pd.to_numeric(d['cognitive_id'], errors='coerce')
    fields = build_fields(tuple(STRATA))
    cols = ['v11_b_gen', 'v11_m_c_s_avg', 'v11_m_c_r_core', 'v18_v_unified_concentration_birth']
    cids, stats = [], {}
    for nc in STRATA:
        s = d[d['v11_m_c_n_core'] == nc].copy()
        for c in cols:
            s[c] = pd.to_numeric(s[c], errors='coerce')
        s = s[s['cognitive_id'].isin(fields.keys())]            # intersection
        # conc 欠損は層内中央値で補完(A を全 intersection で回す)
        s['v18_v_unified_concentration_birth'] = s['v18_v_unified_concentration_birth'].fillna(s['v18_v_unified_concentration_birth'].median())
        st = {c: (float(s[c].mean()), float(s[c].std() + 1e-9)) for c in cols}
        stats[nc] = st
        for _, r in s.iterrows():
            cid = int(r.cognitive_id)
            cids.append(dict(stratum=nc, cid=cid, b_gen=float(r.v11_b_gen),
                             s_avg=float(r.v11_m_c_s_avg), r_core=float(r.v11_m_c_r_core),
                             conc=float(r.v18_v_unified_concentration_birth), field=fields[cid]))
    return cids, stats


def strength_plb(c, st):
    """(A): S/R/conc を層内 z 標準化し等重み平均→tanh→plb 域(step-0 と同形)。"""
    z = []
    for col, key in [('v11_m_c_s_avg', 's_avg'), ('v11_m_c_r_core', 'r_core'), ('v18_v_unified_concentration_birth', 'conc')]:
        mu, sd = st[col]
        z.append((c[key] - mu) / sd)
    z_strength = float(np.mean(z))
    return BASE_PLB * (1 + S_STR * np.tanh(z_strength))


def child_N(c):
    return int(max(round(c['b_gen'] * 10), len(c['field']['field_nodes']) + 1))


def make_engine(N, plb, run_seed):
    encap = V82EncapsulationParams(stress_enabled=False, virtual_enabled=True)
    eng = V82Engine(seed=run_seed, N=N, plb=plb, encap_params=encap)
    eng.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    for a, v in [('torque_order', 'age'), ('deviation_enabled', True), ('semantic_gravity_enabled', True)]:
        if hasattr(eng.virtual, a):
            setattr(eng.virtual, a, v)
    eng.pressure_params.pressure_prob = 0.0
    return eng


def transplant(eng, field):
    """(B): 親 field(配線)を子 local id に remap して移植。確定レシピ: alive_n 登録+E/θ fresh→add_link。"""
    nodes = field['field_nodes']
    remap = {pn: i for i, pn in enumerate(nodes)}      # 親 node id → 子 local 0..k-1
    for i in remap.values():
        eng.state.alive_n.add(i)
        eng.state.E[i] = E_FRESH                        # θ は構築時 uniform 既定(上書きしない)
    for (a, b) in field['field_links']:
        if a in remap and b in remap:
            eng.state.add_link(remap[a], remap[b], S_FRESH)


def phys_fingerprint(eng):
    st = eng.state
    cyc = st.find_all_cycles(eng.physics.params.max_cycle_length)
    loops = sum(len(v) for v in cyc.values())
    Rs = [st.R.get(k, 0.0) for k in st.alive_l]
    return dict(t0_alive_n=len(st.alive_n), t0_alive_l=len(st.alive_l),
                t0_loops=loops, t0_maxR=round(float(np.max(Rs)), 3) if Rs else 0.0)


def signature(eng):
    v = eng.virtual
    labs = list(v.labels.values())
    sizes = [len(l['nodes']) for l in labs]
    shares = [l['share'] for l in labs]
    wc = int(getattr(eng, 'window_count', 0))
    ages = [wc - l['born'] for l in labs]
    return dict(n_labels=len(labs),
                mean_size=float(np.mean(sizes)) if sizes else 0.0,
                std_size=float(np.std(sizes)) if sizes else 0.0,
                share_gini=gini(shares),
                mean_age=float(np.mean(ages)) if ages else 0.0,
                lifecycle_events=int(len(getattr(v, 'lifecycle_log', []))))


def worker(task):
    c = task['c']; cond = task['cond']
    N = child_N(c)
    plb = strength_plb(c, task['stats'][c['stratum']]) if cond == 'A' else BASE_PLB
    eng = make_engine(N, plb, task['run_seed'])
    if cond == 'B':
        transplant(eng, c['field'])           # run_injection skip → 親構造を初期条件に
    else:
        eng.run_injection()                   # canon/(A): fresh init
    fp = phys_fingerprint(eng)                # t0(移植直後 / injection 直後)
    # early 署名
    for _ in range(EARLY_LEN // 500):
        eng.step_window(steps=500)
    sig_e = {f'early_{k}': v for k, v in signature(eng).items()}
    # late 署名
    for _ in range((RUN_LEN - EARLY_LEN) // 500):
        eng.step_window(steps=500)
    sig_l = {f'late_{k}': v for k, v in signature(eng).items()}
    keep = dict(stratum=c['stratum'], cond=cond, cid=c['cid'], seed=task['seed'],
                N=N, plb=round(plb, 6), b_gen=c['b_gen'], s_avg=c['s_avg'],
                r_core=c['r_core'], conc=c['conc'],
                field_nodes=len(c['field']['field_nodes']), field_links=len(c['field']['field_links']),
                field_has_cycle=c['field']['has_cycle'])
    return {**keep, **fp, **sig_e, **sig_l}


def build_tasks(cids, stats):
    tasks = []
    for c in cids:
        for cond in CONDS:
            for s in range(N_SEEDS):
                tasks.append(dict(c=c, cond=cond, stats=stats, seed=s,
                                  run_seed=c['cid'] * 1000 + (0 if cond == 'canon' else 1 if cond == 'A' else 2) * 100 + s))
    return tasks


# ---------- 解析 ----------
def _pd(M):
    from scipy.spatial.distance import pdist, squareform
    return squareform(pdist(M, 'euclidean'))


def _z(A):
    A = np.asarray(A, float)
    return (A - A.mean(0)) / (A.std(0) + 1e-9)


def mantel(Dp, Dc, k, rng):
    iu = np.triu_indices(Dp.shape[0], 1)
    a, b = Dp[iu], Dc[iu]
    r = float(np.corrcoef(a, b)[0, 1])
    n = Dp.shape[0]
    null = np.empty(k)
    for i in range(k):
        perm = rng.permutation(n)
        null[i] = np.corrcoef(Dp[np.ix_(perm, perm)][iu], b)[0, 1]
    return round(r, 3), round(float((np.sum(null >= r) + 1) / (k + 1)), 4)


def analyse(res):
    rng = np.random.default_rng(20260623)
    rep = {}
    for nc in STRATA:
        rep[f'n{nc}'] = {}
        base = res[res.stratum == nc]
        for cond in CONDS:
            sub = base[base.cond == cond]
            g = sub.groupby('cid').agg(**{f'late_{s}': (f'late_{s}', 'mean') for s in SIG},
                                       **{f'early_{s}': (f'early_{s}', 'mean') for s in SIG},
                                       **{c: (c, 'first') for c in ['s_avg', 'r_core', 'conc', 'b_gen']}).reset_index()
            ncid = len(g)
            entry = dict(n_cid=ncid)
            if ncid >= 5:
                Dp = _pd(_z(np.column_stack([g.s_avg, g.r_core, g.conc])))   # 親 structural 距離
                Dc_l = _pd(_z(g[[f'late_{s}' for s in SIG]].values))
                Dc_e = _pd(_z(g[[f'early_{s}' for s in SIG]].values))
                entry['mantel_late'] = dict(zip(['r', 'p'], mantel(Dp, Dc_l, MANTEL_K, rng)))
                entry['mantel_early'] = dict(zip(['r', 'p'], mantel(Dp, Dc_e, MANTEL_K, rng)))
                # 早期→晩期 署名変化(減衰): 各 cid の early vs late 署名 z 距離平均
                el = _z(g[[f'early_{s}' for s in SIG]].values)
                ll = _z(g[[f'late_{s}' for s in SIG]].values)
                entry['early_to_late_drift'] = round(float(np.mean(np.linalg.norm(el - ll, axis=1))), 3)
            else:
                entry['note'] = 'Mantel 不能(<5)'
            # t0 fingerprint 平均
            entry['t0'] = {k: round(float(sub[k].mean()), 2) for k in ['t0_alive_n', 't0_alive_l', 't0_loops', 't0_maxR']}
            rep[f'n{nc}'][cond] = entry
    return rep


def bit_identity(cids, stats):
    """同 seed 2回 run で署名一致(MD5)を確認。代表 3 cid × 3 cond を短 run(EARLY_LEN)で。"""
    global RUN_LEN
    saved = RUN_LEN; RUN_LEN = EARLY_LEN  # 短縮
    sample = cids[:3]
    res = {}
    for c in sample:
        for cond in CONDS:
            t = dict(c=c, cond=cond, stats=stats, seed=0,
                     run_seed=c['cid'] * 1000 + (0 if cond == 'canon' else 1 if cond == 'A' else 2) * 100)
            r1 = worker(t); r2 = worker(t)
            k1 = hashlib.md5(json.dumps({s: r1[f'late_{s}'] for s in SIG}, sort_keys=True).encode()).hexdigest()[:8]
            k2 = hashlib.md5(json.dumps({s: r2[f'late_{s}'] for s in SIG}, sort_keys=True).encode()).hexdigest()[:8]
            res[f'cid{c["cid"]}_{cond}'] = (k1 == k2, k1)
    RUN_LEN = saved
    return res


def main():
    t0 = time.time()
    mode = sys.argv[1] if len(sys.argv) > 1 else 'smoke'
    cids, stats = load()
    n_by = {nc: sum(1 for c in cids if c['stratum'] == nc) for nc in STRATA}
    print(f'=== v1302 abx {mode}: CID intersection {n_by} | conds={CONDS} seeds={N_SEEDS} run_len={RUN_LEN} workers={N_WORKERS} ===', flush=True)

    if mode == 'bitid':
        bi = bit_identity(cids, stats)
        print('=== bit-identity (同seed2回 署名一致) ===')
        for k, (ok, h) in bi.items():
            print(f'  {k}: {"一致" if ok else "不一致!!"} ({h})')
        json.dump({k: [bool(v[0]), v[1]] for k, v in bi.items()}, open(OUT / 'cw_v1302_abx_bitid.json', 'w'), indent=2)
        return

    tasks = build_tasks(cids, stats)
    print(f'  tasks={len(tasks)} (= {len(cids)}cid × {len(CONDS)}cond × {N_SEEDS}seed)', flush=True)
    with mp.Pool(N_WORKERS, maxtasksperchild=2) as pool:
        rows = pool.map(worker, tasks)
    res = pd.DataFrame(rows)
    res.to_parquet(OUT / 'cw_v1302_abx_signatures.parquet', index=False)
    rep = analyse(res)
    meta = dict(design='v1302_abx_parallel', conds=CONDS, run_len=RUN_LEN, early_len=EARLY_LEN,
                n_seeds=N_SEEDS, strata=STRATA, n_by=n_by, signature=SIG, mantel_K=MANTEL_K,
                fresh=dict(S=S_FRESH, E=E_FRESH), total_s=round(time.time() - t0, 1), report=rep)
    json.dump(meta, open(OUT / 'cw_v1302_abx_summary.json', 'w'), indent=2, ensure_ascii=False)
    print(f'=== 完了 {len(res)} child, {time.time()-t0:.0f}s ===', flush=True)
    for nc in STRATA:
        print(f'--- n{nc} (cid={n_by[nc]}) ---')
        for cond in CONDS:
            e = rep[f'n{nc}'][cond]
            ml = e.get('mantel_late', {}); me = e.get('mantel_early', {})
            print(f'  {cond:5}: Mantel late r={ml.get("r")} p={ml.get("p")} | early r={me.get("r")} p={me.get("p")} '
                  f'| early→late drift={e.get("early_to_late_drift")} | t0 {e["t0"]}', flush=True)


if __name__ == '__main__':
    main()
