#!/usr/bin/env python3
"""v1302 (A) フル run 追認 — 前 smoke で効いた scalar→plb を全 CID(n2/n4/n5)・seed 増で追認。設計変更なし。

【観察対象注釈ブロック / 同系・異系宣言】
- 同系内: 親 seed0 CID 縮小子系。異系対応でない。
- 読=frozen: per_subject_seed0 / engine。親 read-only。書=unified/v1302/ のみ。親 physics/inject/ledger/state 非書込。
- (A) の structural-strength=S/R/conc 等重み z→tanh→初期 plb は cw_v1302_abx.strength_plb をそのまま import(同一性担保・設計変更なし)。
- canon(plb一定) を対照に並走。field 不要(移植しない)ゆえ全 stratum 全 CID を使う(n5 を 7→17 に戻し小標本を補強)。
- K_sync/θ canon 固定・null=Mantel 行列置換(無料)・n_core 層化・2点署名は smoke と共通。判定なし(Taka)。
"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1'); os.environ.setdefault('MKL_NUM_THREADS', '1'); os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import sys, time, json, warnings
from pathlib import Path
import numpy as np, pandas as pd
import multiprocessing as mp
warnings.filterwarnings('ignore')
REPO = Path('/home/takasan/esde/ESDE-Research')
for p in ['autonomy/v82', 'ecology/engine', 'primitive/v910', 'cognition/semantic_injection/v4_pipeline/v43', 'unified/v1302']:
    sys.path.insert(0, str(REPO / p))
# 前 smoke の設計をそのまま再利用(同一性担保)
from cw_v1302_abx import (strength_plb, make_engine, signature, phys_fingerprint,
                          mantel, _pd, _z, SIG, EARLY_LEN, BASE_PLB)

RUN_LEN = int(os.environ.get('CW_RUNLEN', '35000'))
STRATA = ['2', '4', '5']                                 # n4 追加
N_SEEDS = int(os.environ.get('CW_SEEDS', '5'))           # smoke 2 → 追認 5
CONDS = ['canon', 'A']
MANTEL_K = 999
N_WORKERS = max(1, (os.cpu_count() or 4) - 2)
OUT = REPO / 'unified/v1302'


def load_all():
    """全 stratum 全 CID(field 不要)。conc 欠損は層内中央値補完。"""
    d = pd.read_csv(REPO / 'primitive/v918/diag_v918_main/subjects/per_subject_seed0.csv')
    d['cognitive_id'] = pd.to_numeric(d['cognitive_id'], errors='coerce')
    cols = ['v11_b_gen', 'v11_m_c_s_avg', 'v11_m_c_r_core', 'v18_v_unified_concentration_birth']
    cids, stats = [], {}
    for nc in STRATA:
        s = d[d['v11_m_c_n_core'] == nc].copy()
        for c in cols:
            s[c] = pd.to_numeric(s[c], errors='coerce')
        s = s.dropna(subset=['v11_b_gen', 'v11_m_c_s_avg', 'v11_m_c_r_core'])
        s['v18_v_unified_concentration_birth'] = s['v18_v_unified_concentration_birth'].fillna(
            s['v18_v_unified_concentration_birth'].median())
        st = {c: (float(s[c].mean()), float(s[c].std() + 1e-9)) for c in cols}
        stats[nc] = st
        for _, r in s.iterrows():
            cids.append(dict(stratum=nc, cid=int(r.cognitive_id), b_gen=float(r.v11_b_gen),
                             s_avg=float(r.v11_m_c_s_avg), r_core=float(r.v11_m_c_r_core),
                             conc=float(r.v18_v_unified_concentration_birth)))
    return cids, stats


def child_N(c):
    return int(round(c['b_gen'] * 10))


def worker(task):
    c = task['c']; cond = task['cond']
    N = child_N(c)
    plb = strength_plb(c, task['stats'][c['stratum']]) if cond == 'A' else BASE_PLB
    eng = make_engine(N, plb, task['run_seed'])
    eng.run_injection()
    fp = phys_fingerprint(eng)
    for _ in range(EARLY_LEN // 500):
        eng.step_window(steps=500)
    sig_e = {f'early_{k}': v for k, v in signature(eng).items()}
    for _ in range((RUN_LEN - EARLY_LEN) // 500):
        eng.step_window(steps=500)
    sig_l = {f'late_{k}': v for k, v in signature(eng).items()}
    keep = dict(stratum=c['stratum'], cond=cond, cid=c['cid'], seed=task['seed'], N=N,
                plb=round(plb, 6), b_gen=c['b_gen'], s_avg=c['s_avg'], r_core=c['r_core'], conc=c['conc'])
    return {**keep, **fp, **sig_e, **sig_l}


def analyse(res):
    rng = np.random.default_rng(20260623)
    rep = {}
    for nc in STRATA:
        rep[f'n{nc}'] = {}
        base = res[res.stratum == nc]
        for cond in CONDS:
            sub = base[base.cond == cond]
            g = sub.groupby('cid').agg(**{f'late_{s}': (f'late_{s}', 'mean') for s in SIG},
                                       **{c: (c, 'first') for c in ['s_avg', 'r_core', 'conc']}).reset_index()
            entry = dict(n_cid=len(g))
            if len(g) >= 5:
                Dp = _pd(_z(np.column_stack([g.s_avg, g.r_core, g.conc])))
                Dc = _pd(_z(g[[f'late_{s}' for s in SIG]].values))
                entry['mantel_late'] = dict(zip(['r', 'p'], mantel(Dp, Dc, MANTEL_K, rng)))
            else:
                entry['note'] = 'Mantel 不能(<5)'
            rep[f'n{nc}'][cond] = entry
    return rep


def main():
    t0 = time.time()
    cids, stats = load_all()
    n_by = {nc: sum(1 for c in cids if c['stratum'] == nc) for nc in STRATA}
    print(f'=== v1302 (A) full: CID {n_by} | conds={CONDS} seeds={N_SEEDS} run_len={RUN_LEN} workers={N_WORKERS} ===', flush=True)
    tasks = [dict(c=c, cond=cond, stats=stats, seed=s,
                  run_seed=c['cid'] * 1000 + (0 if cond == 'canon' else 1) * 100 + s)
             for c in cids for cond in CONDS for s in range(N_SEEDS)]
    print(f'  tasks={len(tasks)}', flush=True)
    with mp.Pool(N_WORKERS, maxtasksperchild=2) as pool:
        rows = pool.map(worker, tasks)
    res = pd.DataFrame(rows)
    res.to_parquet(OUT / 'cw_v1302_A_full_signatures.parquet', index=False)
    rep = analyse(res)
    meta = dict(design='v1302_A_full', conds=CONDS, run_len=RUN_LEN, n_seeds=N_SEEDS,
                strata=STRATA, n_by=n_by, total_s=round(time.time() - t0, 1), report=rep)
    json.dump(meta, open(OUT / 'cw_v1302_A_full_summary.json', 'w'), indent=2, ensure_ascii=False)
    print(f'=== 完了 {len(res)} child, {time.time()-t0:.0f}s ===', flush=True)
    for nc in STRATA:
        for cond in CONDS:
            e = rep[f'n{nc}'][cond]
            print(f'  n{nc} {cond:5}(cid={e["n_cid"]}): Mantel late {e.get("mantel_late", e.get("note"))}', flush=True)


if __name__ == '__main__':
    main()
