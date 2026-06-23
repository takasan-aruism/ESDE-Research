#!/usr/bin/env python3
"""v1302 (B) 成熟期 topology 移植 smoke — 誕生時(tree)でなく age_r≥τ link 閉路ランク最大の成熟 window field を移植。

【観察対象注釈ブロック / 同系・異系宣言】
- 同系内: 親 seed0 CID 縮小子系。異系対応でない。読=frozen per_subject/persistence/engine、書=unified/v1302/ のみ。親 read-only・物理層 frozen。移植は子 in-memory state への add_link のみ。
- (i) 移植 field 定義: 選択=age_r≥τ link の閉路ランク最大 window(全 CID 一律 argmax)/移植中身=その window の全 link 一式(コア+周辺、age_r フィルタ無し)。成熟リンクだけに絞らない。
- (ii) τ∈{10,50,100} 全部で回し transfer の τ 頑健性を見る(label 誕生 τ 特定不能ゆえ1つ選ぶと神の手化)。
- (iii) n2 の N 交絡を切る N 固定 canon 対照(Nfix)を追加。canon/A は A_full(5seed 確証済)を再利用。
- 移植レシピ=前 smoke 不変(alive_n 登録+E/θ fresh canon inject 値 S0.3/E0.6→add_link、R 内生)。2点署名(t0 fingerprint で loops/maxR が立つか+late35k)。null=Mantel 行列置換(無料)。判定なし(Taka)。
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
from cw_v1302_abx import (make_engine, signature, phys_fingerprint, transplant,
                          mantel, _pd, _z, SIG, EARLY_LEN, BASE_PLB)
from cw_v1302_field import build_mature_fields

RUN_LEN = int(os.environ.get('CW_RUNLEN', '35000'))
STRATA = ['2', '4', '5']
TAUS = [10, 50, 100]
N_SEEDS = int(os.environ.get('CW_SEEDS', '3'))
MANTEL_K = 999
N_WORKERS = max(1, (os.cpu_count() or 4) - 2)
OUT = REPO / 'unified/v1302'


def load_parents():
    d = pd.read_csv(REPO / 'primitive/v918/diag_v918_main/subjects/per_subject_seed0.csv')
    d['cognitive_id'] = pd.to_numeric(d['cognitive_id'], errors='coerce')
    fields = {tau: build_mature_fields(tuple(STRATA), tau=tau) for tau in TAUS}
    covered = set.intersection(*[set(fields[t].keys()) for t in TAUS])  # 3τ 共通(=persistence あり)
    par = {}
    for nc in STRATA:
        s = d[d['v11_m_c_n_core'] == nc].copy()
        for c in ['v11_b_gen', 'v11_m_c_s_avg', 'v11_m_c_r_core', 'v18_v_unified_concentration_birth']:
            s[c] = pd.to_numeric(s[c], errors='coerce')
        s['v18_v_unified_concentration_birth'] = s['v18_v_unified_concentration_birth'].fillna(s['v18_v_unified_concentration_birth'].median())
        for _, r in s.iterrows():
            cid = int(r.cognitive_id)
            if cid in covered:
                par[cid] = dict(stratum=nc, cid=cid, b_gen=float(r.v11_b_gen), s_avg=float(r.v11_m_c_s_avg),
                                r_core=float(r.v11_m_c_r_core), conc=float(r.v18_v_unified_concentration_birth))
    n2_Nfixed = int(round(np.median([round(p['b_gen'] * 10) for p in par.values() if p['stratum'] == '2'])))
    return par, fields, n2_Nfixed


def worker(task):
    p = task['p']; cond = task['cond']
    if cond.startswith('B_t'):
        field = task['field']
        N = int(max(round(p['b_gen'] * 10), len(field['field_nodes']) + 1))
        eng = make_engine(N, BASE_PLB, task['run_seed'])
        transplant(eng, field)                       # run_injection skip → 成熟 field 移植
        fn_extra = dict(mat_window=field['mat_window'], mat_cycle_rank=field['mat_cycle_rank'],
                        field_nodes=len(field['field_nodes']), field_links=len(field['field_links']),
                        full_has_cycle=field['full_has_cycle'])
    else:  # Nfix(n2 N 固定 canon)
        N = task['N_fixed']
        eng = make_engine(N, BASE_PLB, task['run_seed'])
        eng.run_injection()
        fn_extra = dict(mat_window=-1, mat_cycle_rank=-1, field_nodes=0, field_links=0, full_has_cycle=False)
    fp = phys_fingerprint(eng)
    for _ in range(EARLY_LEN // 500):
        eng.step_window(steps=500)
    sig_e = {f'early_{k}': v for k, v in signature(eng).items()}
    for _ in range((RUN_LEN - EARLY_LEN) // 500):
        eng.step_window(steps=500)
    sig_l = {f'late_{k}': v for k, v in signature(eng).items()}
    keep = dict(stratum=p['stratum'], cond=cond, cid=p['cid'], seed=task['seed'], N=N,
                b_gen=p['b_gen'], s_avg=p['s_avg'], r_core=p['r_core'], conc=p['conc'])
    return {**keep, **fn_extra, **fp, **sig_e, **sig_l}


def build_tasks(par, fields, n2_Nfixed):
    tasks = []
    for cid, p in par.items():
        for tau in TAUS:
            for s in range(N_SEEDS):
                tasks.append(dict(p=p, cond=f'B_t{tau}', field=fields[tau][cid], seed=s,
                                  run_seed=cid * 1000 + 300 + tau + s))
        if p['stratum'] == '2':
            for s in range(N_SEEDS):
                tasks.append(dict(p=p, cond='Nfix', N_fixed=n2_Nfixed, seed=s, run_seed=cid * 1000 + 700 + s))
    return tasks


def mantel_on(g_sig, g_par, rng):
    if len(g_sig) < 5:
        return dict(n_cid=len(g_sig), note='Mantel 不能(<5)')
    Dp = _pd(_z(np.column_stack([g_par['s_avg'], g_par['r_core'], g_par['conc']])))
    Dc = _pd(_z(g_sig.values))
    r, p = mantel(Dp, Dc, MANTEL_K, rng)
    return dict(n_cid=len(g_sig), r=r, p=p)


def analyse(resB, parmap):
    """B(各τ) を cyclic 部分集合で Mantel。canon/A は A_full から同 CID 集合に制限して取り直す。"""
    rng = np.random.default_rng(20260623)
    af = pd.read_parquet(OUT / 'cw_v1302_A_full_signatures.parquet')   # canon/A 再利用(5seed 確証)
    rep = {}
    for nc in STRATA:
        rep[f'n{nc}'] = {}
        # --- B 各 τ (cyclic 部分集合) ---
        for tau in TAUS:
            sub = resB[(resB.stratum == nc) & (resB.cond == f'B_t{tau}') & (resB.full_has_cycle == True)]
            if len(sub) == 0:
                rep[f'n{nc}'][f'B_t{tau}'] = dict(n_cid=0, note='cyclic CID なし')
                continue
            g = sub.groupby('cid').agg(**{f'late_{s}': (f'late_{s}', 'mean') for s in SIG},
                                       **{c: (c, 'first') for c in ['s_avg', 'r_core', 'conc']},
                                       t0_loops=('t0_loops', 'mean'), t0_maxR=('t0_maxR', 'mean'),
                                       mat_window=('mat_window', 'mean')).reset_index()
            ent = mantel_on(g[[f'late_{s}' for s in SIG]], g, rng)
            ent['t0_loops'] = round(float(g.t0_loops.mean()), 2)
            ent['t0_maxR'] = round(float(g.t0_maxR.mean()), 2)
            ent['mat_window_med'] = round(float(g.mat_window.median()), 1)
            cyc_cids = set(g.cid)
            # canon/A を同 cyclic CID 集合で取り直す
            for cc in ['canon', 'A']:
                a = af[(af.stratum.astype(str) == nc) & (af.cond == cc) & (af.cid.isin(cyc_cids))]
                ga = a.groupby('cid').agg(**{f'late_{s}': (f'late_{s}', 'mean') for s in SIG},
                                          **{c: (c, 'first') for c in ['s_avg', 'r_core', 'conc']}).reset_index()
                ent[f'{cc}_same_cid'] = mantel_on(ga[[f'late_{s}' for s in SIG]], ga, rng)
            rep[f'n{nc}'][f'B_t{tau}'] = ent
        # --- (iii) Nfix vs A vs canon (n2 のみ・全 covered CID) ---
        if nc == '2':
            nf = resB[(resB.stratum == '2') & (resB.cond == 'Nfix')]
            cids = set(nf.cid)
            gn = nf.groupby('cid').agg(**{f'late_{s}': (f'late_{s}', 'mean') for s in SIG},
                                       **{c: (c, 'first') for c in ['s_avg', 'r_core', 'conc']}).reset_index()
            rep['n2']['Nfix'] = mantel_on(gn[[f'late_{s}' for s in SIG]], gn, rng)
            for cc in ['canon', 'A']:
                a = af[(af.stratum.astype(str) == '2') & (af.cond == cc) & (af.cid.isin(cids))]
                ga = a.groupby('cid').agg(**{f'late_{s}': (f'late_{s}', 'mean') for s in SIG},
                                          **{c: (c, 'first') for c in ['s_avg', 'r_core', 'conc']}).reset_index()
                rep['n2'][f'{cc}_Nfix_cidset'] = mantel_on(ga[[f'late_{s}' for s in SIG]], ga, rng)
    return rep


def bit_identity(par, fields):
    global RUN_LEN
    saved = RUN_LEN; RUN_LEN = EARLY_LEN
    sample = list(par.values())[:3]
    res = {}
    for p in sample:
        t = dict(p=p, cond='B_t50', field=fields[50][p['cid']], seed=0, run_seed=p['cid'] * 1000 + 350)
        r1, r2 = worker(t), worker(t)
        k1 = hashlib.md5(json.dumps({s: r1[f'late_{s}'] for s in SIG}, sort_keys=True).encode()).hexdigest()[:8]
        k2 = hashlib.md5(json.dumps({s: r2[f'late_{s}'] for s in SIG}, sort_keys=True).encode()).hexdigest()[:8]
        res[f'cid{p["cid"]}_B_t50'] = (k1 == k2, k1)
    RUN_LEN = saved
    return res


def main():
    t0 = time.time()
    mode = sys.argv[1] if len(sys.argv) > 1 else 'smoke'
    par, fields, n2_Nfixed = load_parents()
    n_by = {nc: sum(1 for p in par.values() if p['stratum'] == nc) for nc in STRATA}
    cyc = {tau: {nc: sum(1 for cid in par if par[cid]['stratum'] == nc and fields[tau][cid]['full_has_cycle']) for nc in STRATA} for tau in TAUS}
    print(f'=== v1302 (B)成熟期 {mode}: covered CID {n_by} | τ別 cyclic {cyc} | N_fixed(n2)={n2_Nfixed} seeds={N_SEEDS} ===', flush=True)

    if mode == 'reanalyse':
        resB = pd.read_parquet(OUT / 'cw_v1302_B_mature_signatures.parquet')
        rep = analyse(resB, par)
        meta = dict(design='v1302_B_mature', taus=TAUS, run_len=RUN_LEN, n_seeds=N_SEEDS, strata=STRATA,
                    covered=n_by, cyclic_by_tau=cyc, n2_Nfixed=n2_Nfixed, report=rep)
        json.dump(meta, open(OUT / 'cw_v1302_B_mature_summary.json', 'w'), indent=2, ensure_ascii=False)
        for nc in STRATA:
            print(f'--- n{nc} ---')
            for tau in TAUS:
                e = rep[f'n{nc}'].get(f'B_t{tau}', {})
                if 'r' in e:
                    cs = e.get('canon_same_cid', {}); As = e.get('A_same_cid', {})
                    print(f'  B_t{tau}(cyc={e["n_cid"]}): late r={e["r"]} p={e["p"]} t0loops={e["t0_loops"]} matW={e["mat_window_med"]} || canon(同cid) r={cs.get("r")} A(同cid) r={As.get("r")}', flush=True)
                else:
                    print(f'  B_t{tau}: {e.get("note")}', flush=True)
            if nc == '2':
                r = rep['n2']
                print(f'  (iii) Nfix r={r["Nfix"].get("r")} | canon(同cid) r={r.get("canon_Nfix_cidset",{}).get("r")} | A(同cid) r={r.get("A_Nfix_cidset",{}).get("r")}', flush=True)
        return

    if mode == 'bitid':
        bi = bit_identity(par, fields)
        for k, (ok, h) in bi.items():
            print(f'  {k}: {"一致" if ok else "不一致!!"} ({h})')
        json.dump({k: [bool(v[0]), v[1]] for k, v in bi.items()}, open(OUT / 'cw_v1302_B_mature_bitid.json', 'w'), indent=2)
        return

    tasks = build_tasks(par, fields, n2_Nfixed)
    print(f'  tasks={len(tasks)} (B×3τ + Nfix(n2)、canon/A は A_full 再利用)', flush=True)
    with mp.Pool(N_WORKERS, maxtasksperchild=2) as pool:
        rows = pool.map(worker, tasks)
    resB = pd.DataFrame(rows)
    resB.to_parquet(OUT / 'cw_v1302_B_mature_signatures.parquet', index=False)
    rep = analyse(resB, par)
    meta = dict(design='v1302_B_mature', taus=TAUS, run_len=RUN_LEN, n_seeds=N_SEEDS, strata=STRATA,
                covered=n_by, cyclic_by_tau=cyc, n2_Nfixed=n2_Nfixed, total_s=round(time.time() - t0, 1), report=rep)
    json.dump(meta, open(OUT / 'cw_v1302_B_mature_summary.json', 'w'), indent=2, ensure_ascii=False)
    print(f'=== 完了 {len(resB)} child(B+Nfix), {time.time()-t0:.0f}s ===', flush=True)
    for nc in STRATA:
        print(f'--- n{nc} ---')
        for tau in TAUS:
            e = rep[f'n{nc}'].get(f'B_t{tau}', {})
            if 'r' in e:
                cs = e.get('canon_same_cid', {}); As = e.get('A_same_cid', {})
                print(f'  B_t{tau} (cyc cid={e["n_cid"]}): late r={e["r"]} p={e["p"]} | t0 loops={e["t0_loops"]} maxR={e["t0_maxR"]} matW={e["mat_window_med"]} '
                      f'|| same-cid canon r={cs.get("r")} A r={As.get("r")}', flush=True)
            else:
                print(f'  B_t{tau}: {e.get("note")}', flush=True)
        if nc == '2' and 'Nfix' in rep['n2']:
            print(f'  (iii) n2 Nfix r={rep["n2"]["Nfix"].get("r")} | canon(同cid) r={rep["n2"].get("canon_Nfix_cidset",{}).get("r")} | A(同cid) r={rep["n2"].get("A_Nfix_cidset",{}).get("r")}', flush=True)


if __name__ == '__main__':
    main()
