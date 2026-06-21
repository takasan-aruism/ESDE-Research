#!/usr/bin/env python3
"""v12 Atomset cid_align — STEP 3 (あ): 行き先 Atom (argmax) + null 2種, raw/norm 両方

## 致命的修正 (この STEP で直した軸整合バグ)
v1103 atom_centroids の48列はアルファベット順 (epistemological.creation..)。cid_align は
v106 AXES_ORDER (=slot_keys, temporal 先頭・level は意味順) で組む。両者の列順が違うため、
v1103 parquet を *そのまま* cosine すると軸 scramble = 行き先が無意味 (prototype のバグ)。
→ v1103 raw/norm を slot_keys() 順に *並べ替えてから* cosine する。これで軸整合。

## 認識の核 (手放さない)
- 下位 level の Atom-CID 厳密対応は無い (人為的投影、神経-言語同様)。一致率の*絶対値*を信じない
  (projection_audit: margin 0.09 平坦)。主指標は *行き先の方向* (argmax の atom)、一致率は副。
- raw=潜在(未定義軸=見えてない) / norm=顕在(足場の上の値), D.92。両並列で観察 (Δ0.208 反転 #L17)。

## 観察 (判定しない, crown 禁止)
- 主指標: 行き先 Atom = argmax cosine(cid_align_final, atom)。raw/norm 別々。
- null-A = 別 seed の経験ストリーム (cid_align は stream のみで決まるので, 別個体の行き先と一致するか)。
  → 「皆同じ atom に潰れる(個体差なし)」か「経験で別 atom に分かれる」かを per-CID で。
- null-B = 同一 CID の経験順序 shuffle (f=robust_z は履歴依存なので順序で変わる)。
  → 行き先が「順序/履歴」依存か「経験集合」だけで決まるか。
- 個別 CID・n_core 層化。density (候補群の mean pairwise cosine)。物理書込ゼロ。
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

REPO = Path('/home/takasan/esde/ESDE-Research')
sys.path.insert(0, str(REPO / 'developmental/v106'))
from v106_pulse_trajectory import (  # noqa: E402
    temporal_vec, scale_vec, epistemological_vec, ontological_vec,
    interconnection_vec, resonance_vec, lawfulness_vec, experience_vec,
    value_generation_vec,
)
from v106_post_process import slot_keys  # noqa: E402

SRC_DIR = REPO / 'developmental/v107/outputs/main'
OUT_DIR = REPO / 'unified/v1201/run_step3'
OUT_DIR.mkdir(parents=True, exist_ok=True)
ALPHA = 0.3; MAD_C = 1.4826; Z_CLIP = 4.0; K_MIN = 3; SYM_W = 5
SK = slot_keys()


def load_atoms(kind):
    a = pd.read_parquet(REPO / f'unified/v1103/outputs/main/atom_centroids_48d_{kind}.parquet')
    M = a[SK].values.astype(np.float64)               # slot_keys 順に並べ替え (軸整合)
    valid = ~np.isnan(M).any(axis=1) & (np.linalg.norm(M, axis=1) > 1e-9)
    Mn = np.zeros_like(M)
    Mn[valid] = M[valid] / np.linalg.norm(M[valid], axis=1, keepdims=True)
    return a['atom'].values, Mn, valid


def build_vec48(row, smax):
    parts = []
    parts += temporal_vec(row['lifespan_so_far'])
    parts += scale_vec(row['n_core_member'])
    parts += epistemological_vec(row['R_familiarity'])
    parts += ontological_vec(row, smax)
    parts += interconnection_vec(row['cumulative_n_alphas'])
    parts += resonance_vec(row['C_at_window_end'])
    parts += [0.0] * SYM_W
    parts += lawfulness_vec(row['pulse_density_so_far'])
    parts += experience_vec(row)
    parts += value_generation_vec(row, smax)
    return np.array(parts, dtype=np.float64)


def robust_z(vecs):
    rm = np.zeros(vecs.shape[1]); vals = []
    for t in range(len(vecs)):
        vals.append(np.linalg.norm(vecs[t] - rm) if t > 0 else 0.0)
        rm = rm + (vecs[t] - rm) / (t + 1)
    vals = np.array(vals); fs = np.zeros(len(vals))
    for t in range(K_MIN, len(vals)):
        w = vals[:t]; med = np.median(w); mad = np.median(np.abs(w - med)) * MAD_C
        fs[t] = np.clip((vals[t] - med) / max(mad, 1e-3), -Z_CLIP, Z_CLIP)
    return np.abs(fs)


def accumulate(vecs, order):
    """指定 order で cid_align を累積し最終ベクトルを返す。f は order に沿って再計算。"""
    vv = vecs[order]
    fs = robust_z(vv)
    align = vv[0] / (np.linalg.norm(vv[0]) + 1e-9)
    for t in range(len(vv)):
        ev = vv[t] / (np.linalg.norm(vv[t]) + 1e-9)
        align = align + ALPHA * fs[t] * ev
        align = align / (np.linalg.norm(align) + 1e-9)
    return align


def cid_vecs(g, smax):
    g = g.sort_values('timestamp').reset_index(drop=True)
    cnt = {'pulse': 0, 'alpha_formation': 0, 'beta_formation': 0, 'ingestion': 0}
    out = []
    for _, e in g.iterrows():
        et = e['event_source_type']
        if et in cnt: cnt[et] += 1
        ls = float(e['lifespan_so_far']) if not pd.isna(e['lifespan_so_far']) else 1.0
        row = {'lifespan_so_far': ls, 'n_core_member': e['n_core_member'],
               'R_familiarity': e.get('R_familiarity_pre', 0) or 0, 'v14_q0': e.get('v14_q0', 0) or 0,
               'Q_remaining_at_window_end': e.get('Q_remaining_at_window_end', 0) or 0,
               'C_at_window_end': e.get('C_at_window_end', 0) or 0,
               'cumulative_n_alphas': cnt['alpha_formation'], 'cumulative_n_betas': cnt['beta_formation'],
               'cumulative_n_ingestions': cnt['ingestion'], 'cumulative_pulse_count': cnt['pulse'],
               'cumulative_q_spend_events': 0, 'pulse_density_so_far': cnt['pulse'] / max(ls, 1.0)}
        out.append(build_vec48(row, smax))
    return np.array(out)


def dest(align, Mn, valid, names):
    sims = Mn @ (align / (np.linalg.norm(align) + 1e-9))
    sims[~valid] = -np.inf
    i = int(np.argmax(sims))
    return names[i], float(sims[i])


def main():
    rng = np.random.default_rng(0)
    names_raw, Mraw, vraw = load_atoms('raw')
    names_nrm, Mnrm, vnrm = load_atoms('normalized')
    recs = []
    aligns_by_seed = {}   # null-A 用に final align を貯める
    for seed in range(24):
        df = pd.read_parquet(SRC_DIR / f'source_events_seed{seed}.parquet')
        tot = df.groupby('source_cid')['event_source_type'].value_counts().unstack(fill_value=0)
        smax = {'cumulative_pulse_max': float(max(tot.get('pulse', pd.Series([1])).max(), 1)),
                'cumulative_n_alphas_max': float(max(tot.get('alpha_formation', pd.Series([1])).max(), 1)),
                'cumulative_n_betas_max': float(max(tot.get('beta_formation', pd.Series([1])).max(), 1)),
                'cumulative_n_ingestions_max': float(max(tot.get('ingestion', pd.Series([1])).max(), 1)),
                'C_max_seed': float(max(pd.to_numeric(df['C_at_window_end'], errors='coerce').max(), 1))}
        aligns_by_seed[seed] = {}
        for cid, g in df.groupby('source_cid'):
            if len(g) < K_MIN + 2:
                continue
            vecs = cid_vecs(g, smax)
            n = len(vecs)
            a_real = accumulate(vecs, np.arange(n))
            a_shuf = accumulate(vecs, rng.permutation(n))   # null-B 順序shuffle
            dr_raw, sr_raw = dest(a_real, Mraw, vraw, names_raw)
            dr_nrm, sr_nrm = dest(a_real, Mnrm, vnrm, names_nrm)
            db_raw, _ = dest(a_shuf, Mraw, vraw, names_raw)
            db_nrm, _ = dest(a_shuf, Mnrm, vnrm, names_nrm)
            nc = int(g['n_core_member'].iloc[-1]) if not pd.isna(g['n_core_member'].iloc[-1]) else 0
            rec = {'seed': seed, 'cid': int(cid), 'n_core': nc, 'n_events': n,
                   'dest_raw': dr_raw, 'sim_raw': sr_raw, 'dest_nrm': dr_nrm, 'sim_nrm': sr_nrm,
                   'destB_raw': db_raw, 'destB_nrm': db_nrm}
            recs.append(rec)
            aligns_by_seed[seed][int(cid)] = (dr_raw, dr_nrm)
    R = pd.DataFrame(recs)
    # null-A: 別 seed の同 index 個体の行き先と一致するか
    donorA_raw, donorA_nrm = [], []
    for _, r in R.iterrows():
        ds = (r['seed'] + 1) % 24
        pool = list(aligns_by_seed.get(ds, {}).items())
        if pool:
            _, (draw, dnrm) = pool[int(r['cid']) % len(pool)]
        else:
            draw, dnrm = None, None
        donorA_raw.append(draw); donorA_nrm.append(dnrm)
    R['destA_raw'] = donorA_raw; R['destA_nrm'] = donorA_nrm
    R.to_parquet(OUT_DIR / 'step3_destinations.parquet', index=False)

    # ===== 観察報告 (集約一個でない: 個別分布 + n_core 別, crown 禁止) =====
    print('=== STEP 3: 行き先 Atom (argmax) + null 2種, raw/norm 両方 ===\n')
    print(f'対象 CID: {len(R)} (n_events>={K_MIN+2})\n')
    for kind, dcol, bcol, acol in [('raw', 'dest_raw', 'destB_raw', 'destA_raw'),
                                   ('norm', 'dest_nrm', 'destB_nrm', 'destA_nrm')]:
        print(f'--- {kind} centroid ---')
        nd = R[dcol].nunique()
        print(f'  行き先 atom の多様性: {nd} 種 (全 {len(R)} CID, valid atom 325)')
        top = R[dcol].value_counts().head(5)
        print(f'  行き先 top5: {dict(top)}')
        # null-B: 順序で行き先が変わるか
        sameB = (R[dcol] == R[bcol]).mean()
        print(f'  real==null-B(順序shuffle) 一致率: {sameB:.1%} '
              f'→ {"行き先は経験集合で決まる(順序不問)" if sameB>0.8 else "順序/履歴で変わる" if sameB<0.5 else "中間"}')
        # null-A: 別個体と同じ atom に行くか (潰れてないか)
        va = R[R[acol].notna()]
        sameA = (va[dcol] == va[acol]).mean()
        print(f'  real==null-A(別seed個体) 一致率: {sameA:.1%} '
              f'→ {"皆同じatomに潰れる(個体差なし)" if sameA>0.5 else "別個体とは別atom(経験で分かれる)"}')
        print(f'  一致率(max cosine) 中央値: {R[("sim_raw" if kind=="raw" else "sim_nrm")].median():.3f} (副指標, 絶対値信じない)')
        print(f'  n_core 別 行き先多様性: ' +
              ', '.join(f'n{nc}:{gg[dcol].nunique()}種/{len(gg)}CID' for nc, gg in R.groupby('n_core') if len(gg) >= 5))
        print()


if __name__ == '__main__':
    main()
