#!/usr/bin/env python3
"""v1302 (B) 交絡除去 smoke — 元(B)移植の null は「topology 非transfer」でなく「injection skip で空エンジン再成長」の交絡。
それを切り分ける Bov(overlay) を追加する。

【懐疑チェックで判明した交絡】
- 元(B): worker が run_injection() を丸ごと skip し transplant() で field_nodes だけ alive 登録。
  → t0_alive_n が n2:120→19 / n5:338→44 と canon の ~16-20% しか alive でない「空エンジン」start。
  → late 署名は N(=b_gen×10)と汎用 plb による再成長に支配され、19/120 の移植 topology は希釈・上書きされる。
  → B の Mantel≈0 を「topology は identity を運ばない」と解釈できない(空start再成長の washout と交絡)。

【観察対象注釈ブロック / 同系・異系宣言】
- 同系内: 親 seed0 CID 縮小子系。異系対応でない。読=frozen per_subject/persistence/engine。親 read-only・物理層 frozen。
- 3条件を同一 make_engine/RUN_LEN/seed で並走:
    canon : run_injection() のみ(canonical baseline, plb=BASE_PLB)。
    B     : 元レシピ = run_injection skip + transplant(置換)。交絡あり版を継続性のため保持。
    Bov   : run_injection()(canon と同一 baseline)+ 親 topology を add_link で overlay(grafting)。
            E/θ は触らない(baseline を壊さない)。t0_alive_n が canon と一致するのが交絡除去の証。
- これで「canon と同一 baseline 上で親 topology を上乗せすると親→子 transfer が canon を超えて増えるか」を isolate。
    Bov ≈ canon ≈ 0 → topology は baseline 固定でも非transfer(元結論を交絡抜きで補強)。
    Bov > canon       → topology は identity を一部運ぶ(元 null は空start artifact)。
- topology source=mature field τ=50(成熟 window・閉路あり、元 smoke で唯一正blip を出した τ)。
- null=Mantel 行列置換(無料)。層化 n2 主+n5 補助。判定なし(Taka)。
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
                          mantel, _pd, _z, SIG, EARLY_LEN, BASE_PLB, S_FRESH)
from cw_v1302_field import build_mature_fields

RUN_LEN = int(os.environ.get('CW_RUNLEN', '35000'))
STRATA = ['2', '5']
TAU = 50
N_SEEDS = int(os.environ.get('CW_SEEDS', '3'))
CONDS = ['canon', 'B', 'Bov']
MANTEL_K = 999
N_WORKERS = max(1, (os.cpu_count() or 4) - 2)
OUT = REPO / 'unified/v1302'


def transplant_overlay(eng, field):
    """(Bov): run_injection 済みエンジンの生きた node に親 topology を grafting。
    親 field_nodes を「現在 alive な node」へ写像し add_link のみ(E/θ 不変=baseline 保持)。"""
    nodes = field['field_nodes']
    alive = sorted(eng.state.alive_n)
    if len(alive) < len(nodes):                                   # 足りなければ未生 id で補完
        alive = alive + [i for i in range(eng.state.n_nodes) if i not in eng.state.alive_n]
    remap = {pn: alive[idx] for idx, pn in enumerate(nodes)}      # 親 node → 子 alive node
    added = 0
    for (a, b) in field['field_links']:
        if a in remap and b in remap:
            if eng.state.add_link(remap[a], remap[b], S_FRESH):
                added += 1
    return added


def load():
    d = pd.read_csv(REPO / 'primitive/v918/diag_v918_main/subjects/per_subject_seed0.csv')
    d['cognitive_id'] = pd.to_numeric(d['cognitive_id'], errors='coerce')
    fields = build_mature_fields(tuple(STRATA), tau=TAU)
    par = {}
    for nc in STRATA:
        s = d[d['v11_m_c_n_core'] == nc].copy()
        for c in ['v11_b_gen', 'v11_m_c_s_avg', 'v11_m_c_r_core', 'v18_v_unified_concentration_birth']:
            s[c] = pd.to_numeric(s[c], errors='coerce')
        s['v18_v_unified_concentration_birth'] = s['v18_v_unified_concentration_birth'].fillna(
            s['v18_v_unified_concentration_birth'].median())
        for _, r in s.iterrows():
            cid = int(r.cognitive_id)
            if cid in fields:
                par[cid] = dict(stratum=nc, cid=cid, b_gen=float(r.v11_b_gen), s_avg=float(r.v11_m_c_s_avg),
                                r_core=float(r.v11_m_c_r_core), conc=float(r.v18_v_unified_concentration_birth),
                                field=fields[cid])
    return par


def worker(task):
    p = task['p']; cond = task['cond']; field = p['field']
    N = int(max(round(p['b_gen'] * 10), len(field['field_nodes']) + 1))
    eng = make_engine(N, BASE_PLB, task['run_seed'])
    if cond == 'canon':
        eng.run_injection()
        added = 0
    elif cond == 'B':                          # 元レシピ: injection skip + 置換移植(交絡あり)
        transplant(eng, field)
        added = len(field['field_links'])
    else:                                      # Bov: canon baseline + 親 topology overlay
        eng.run_injection()
        added = transplant_overlay(eng, field)
    fp = phys_fingerprint(eng)
    for _ in range(EARLY_LEN // 500):
        eng.step_window(steps=500)
    sig_e = {f'early_{k}': v for k, v in signature(eng).items()}
    for _ in range((RUN_LEN - EARLY_LEN) // 500):
        eng.step_window(steps=500)
    sig_l = {f'late_{k}': v for k, v in signature(eng).items()}
    keep = dict(stratum=p['stratum'], cond=cond, cid=p['cid'], seed=task['seed'], N=N,
                b_gen=p['b_gen'], s_avg=p['s_avg'], r_core=p['r_core'], conc=p['conc'],
                field_nodes=len(field['field_nodes']), field_links=len(field['field_links']),
                links_added=added, full_has_cycle=field['full_has_cycle'])
    return {**keep, **fp, **sig_e, **sig_l}


def build_tasks(par):
    tasks = []
    off = {'canon': 0, 'B': 100, 'Bov': 200}
    for cid, p in par.items():
        for cond in CONDS:
            for s in range(N_SEEDS):
                tasks.append(dict(p=p, cond=cond, seed=s, run_seed=cid * 1000 + 400 + off[cond] + s))
    return tasks


def mantel_on(g_sig, g_par, rng):
    if len(g_sig) < 5:
        return dict(n_cid=len(g_sig), note='Mantel 不能(<5)')
    Dp = _pd(_z(np.column_stack([g_par['s_avg'], g_par['r_core'], g_par['conc']])))
    Dc = _pd(_z(g_sig.values))
    r, p = mantel(Dp, Dc, MANTEL_K, rng)
    return dict(n_cid=len(g_sig), r=r, p=p)


def analyse(res):
    rng = np.random.default_rng(20260624)
    rep = {}
    for nc in STRATA:
        rep[f'n{nc}'] = {}
        base = res[res.stratum == nc]
        for cond in CONDS:
            sub = base[base.cond == cond]
            g = sub.groupby('cid').agg(**{f'late_{s}': (f'late_{s}', 'mean') for s in SIG},
                                       **{c: (c, 'first') for c in ['s_avg', 'r_core', 'conc']},
                                       t0_alive_n=('t0_alive_n', 'mean'), t0_loops=('t0_loops', 'mean'),
                                       t0_maxR=('t0_maxR', 'mean'), links_added=('links_added', 'mean')).reset_index()
            ent = mantel_on(g[[f'late_{s}' for s in SIG]], g, rng)
            ent['t0_alive_n'] = round(float(g.t0_alive_n.mean()), 1)
            ent['t0_loops'] = round(float(g.t0_loops.mean()), 2)
            ent['t0_maxR'] = round(float(g.t0_maxR.mean()), 3)
            ent['links_added'] = round(float(g.links_added.mean()), 1)
            rep[f'n{nc}'][cond] = ent
    return rep


def bit_identity(par):
    global RUN_LEN
    saved = RUN_LEN; RUN_LEN = EARLY_LEN
    res = {}
    for p in list(par.values())[:2]:
        for cond in ['B', 'Bov']:
            t = dict(p=p, cond=cond, seed=0, run_seed=p['cid'] * 1000 + 400 + (100 if cond == 'B' else 200))
            r1, r2 = worker(t), worker(t)
            k1 = hashlib.md5(json.dumps({s: r1[f'late_{s}'] for s in SIG}, sort_keys=True).encode()).hexdigest()[:8]
            k2 = hashlib.md5(json.dumps({s: r2[f'late_{s}'] for s in SIG}, sort_keys=True).encode()).hexdigest()[:8]
            res[f'cid{p["cid"]}_{cond}'] = (k1 == k2, k1)
    RUN_LEN = saved
    return res


def main():
    t0 = time.time()
    mode = sys.argv[1] if len(sys.argv) > 1 else 'smoke'
    par = load()
    n_by = {nc: sum(1 for p in par.values() if p['stratum'] == nc) for nc in STRATA}
    cyc = {nc: sum(1 for cid in par if par[cid]['stratum'] == nc and par[cid]['field']['full_has_cycle']) for nc in STRATA}
    print(f'=== v1302 (B)overlay {mode}: covered {n_by} | cyclic {cyc} | τ={TAU} seeds={N_SEEDS} run_len={RUN_LEN} ===', flush=True)

    if mode == 'bitid':
        for k, (ok, h) in bit_identity(par).items():
            print(f'  {k}: {"一致" if ok else "不一致!!"} ({h})')
        return

    tasks = build_tasks(par)
    print(f'  tasks={len(tasks)} (canon/B/Bov × {sum(n_by.values())}cid × {N_SEEDS}seed)', flush=True)
    with mp.Pool(N_WORKERS, maxtasksperchild=2) as pool:
        rows = pool.map(worker, tasks)
    res = pd.DataFrame(rows)
    res.to_parquet(OUT / 'cw_v1302_B_overlay_signatures.parquet', index=False)
    rep = analyse(res)
    meta = dict(design='v1302_B_overlay', tau=TAU, conds=CONDS, run_len=RUN_LEN, n_seeds=N_SEEDS,
                strata=STRATA, covered=n_by, cyclic=cyc, total_s=round(time.time() - t0, 1), report=rep)
    json.dump(meta, open(OUT / 'cw_v1302_B_overlay_summary.json', 'w'), indent=2, ensure_ascii=False)
    print(f'=== 完了 {len(res)} child, {time.time()-t0:.0f}s ===', flush=True)
    for nc in STRATA:
        print(f'--- n{nc} (cid={n_by[nc]}) ---', flush=True)
        for cond in CONDS:
            e = rep[f'n{nc}'][cond]
            print(f'  {cond:5}: late r={e.get("r")} p={e.get("p")} | t0 alive_n={e["t0_alive_n"]} '
                  f'loops={e["t0_loops"]} maxR={e["t0_maxR"]} +links={e["links_added"]}', flush=True)


if __name__ == '__main__':
    main()
