#!/usr/bin/env python3
"""v12 Projection Audit (設計書 §3/§9-A) — 投影側か記帳側か判定 (実装に入らず測るだけ)

焦点 (Gemini の 4 次元説は取り違え、10 軸前提で):
 - v106 build_cid_vector の 10 軸が M4 CID 間で実際に分散しているか / どの軸が定数同然か
 - 投影後 48 次元の有効ランク (PCA)、CID 間 cosine 距離
 - 326(325) atom 類似度の margin(top1-top2) / entropy / top-k 重複
 - cosine が大きさを消していないか、phase_sig が本体 cid_vector に入っているか
 - 記帳条件 (現コードに match gate があるか) を明示

注: 動態の bonus 対象を実際に決めるのは M2-M4 の **簡易版** compute_rank_1_atom (scale+phase)。
   v106 本体 build_cid_vector (10 軸, phase_sig なし) は post-hoc 解析用。両方を測って区別する。
"""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
sys.path.insert(0, str(REPO / 'developmental/v106'))
import v106_post_process as v106

OUT = REPO / 'unified/v12_atomset/run_m4/projection_audit.json'
ATOM_CENTROIDS = REPO / 'unified/v1103/outputs/main/atom_centroids_48d_normalized.parquet'
DIAG = {c: Path(f'/tmp/v12_m4_{c}_seed0/diag_v105_v12_m4_{c}_seed0') for c in ('off', 'small')}

# 10 軸の dim 範囲 (build_cid_vector の順)
AXIS_BLOCKS = [
    ('temporal', 0, 7), ('scale', 7, 13), ('epistemological', 13, 18),
    ('ontological', 18, 23), ('interconnection', 23, 28), ('resonance', 28, 32),
    ('symmetry', 32, 37), ('lawfulness', 37, 41), ('experience', 41, 44),
    ('value_generation', 44, 48),
]
RUN_END = 2500  # smoke: 5 window × 500


def load_m4_cids(cond):
    subj = pd.read_csv(DIAG[cond] / 'subjects/per_subject_seed0.csv')
    audit = pd.read_csv(DIAG[cond] / 'audit/per_subject_audit_seed0.csv')
    acols = [c for c in ['cid', 'n_core_member', 'v14_q0', 'v14_q_remaining', 'v14_q_spent',
                         'v14_virtual_familiarity_entries', 'v14_virtual_familiarity_sum']
             if c in audit.columns]
    df = subj.merge(audit[acols], how='left', left_on='cognitive_id', right_on='cid', suffixes=('', '_a'))
    # smoke 用 lifespan_steps (window×500)
    end_w = df['host_lost_window'].fillna(5)
    df['lifespan_steps'] = (end_w - df['birth_window']).clip(lower=1) * 500.0
    return df


def load_atoms():
    a = pd.read_parquet(ATOM_CENTROIDS)
    names = a['atom'].tolist()
    cols = [c for c in a.columns if c not in ('atom', 'n_words')]
    M = a[cols].values.astype(np.float64)
    n = np.linalg.norm(M, axis=1, keepdims=True); n[n < 1e-9] = 1.0
    return names, M / n


def simplified_rank1(n_core, phase_sig, atom_names, atom_unit):
    """M2-M4 の動態で実際に使われる簡易版 (scale + phase)"""
    vec = np.zeros(48); scale_start = 7
    n = int(round(n_core)) if not pd.isna(n_core) else 2
    idx = 0 if n <= 2 else min(n - 2, 5)
    vec[scale_start + idx] = 1.0
    if not pd.isna(phase_sig):
        npz = abs(float(phase_sig)) / np.pi
        placed = False
        for i, lo in enumerate([0, 1/7, 2/7, 3/7, 4/7, 5/7, 6/7]):
            if lo <= npz < lo + 1/7:
                vec[i] = 1.0; placed = True; break
        if not placed:
            vec[6] = 1.0
    nv = np.linalg.norm(vec)
    if nv < 1e-9:
        return None, None
    sims = atom_unit @ (vec / nv)
    j = int(np.argmax(sims))
    return atom_names[j], float(sims[j])


def cosine_dists(V):
    Vn = V / np.clip(np.linalg.norm(V, axis=1, keepdims=True), 1e-12, None)
    S = Vn @ Vn.T
    iu = np.triu_indices(len(V), 1)
    d = 1 - S[iu]
    return float(d.mean()), float(d.min()), float(d.max())


def effective_rank(V):
    Vc = V - V.mean(0)
    if len(V) < 2:
        return 1, []
    u, s, vt = np.linalg.svd(Vc, full_matrices=False)
    var = s**2; var = var / var.sum() if var.sum() > 0 else var
    # effective rank = exp(entropy of normalized singular values)
    p = var[var > 1e-12]
    eff = float(np.exp(-(p * np.log(p)).sum())) if len(p) else 1.0
    numrank = int((s > 1e-9 * s[0]).sum()) if s[0] > 0 else 0
    return eff, numrank, [round(float(x), 4) for x in var[:8]]


def atom_margins(V, atom_unit, atom_names):
    Vn = V / np.clip(np.linalg.norm(V, axis=1, keepdims=True), 1e-12, None)
    S = Vn @ atom_unit.T  # (ncid, natom)
    out = []
    top1_atoms = []
    top3_sets = []
    for i in range(len(V)):
        order = np.argsort(-S[i])
        t1, t2 = S[i, order[0]], S[i, order[1]]
        # entropy of similarity profile (shift to positive)
        p = S[i] - S[i].min() + 1e-9; p = p / p.sum()
        ent = float(-(p * np.log(p)).sum())
        out.append({'top1_atom': atom_names[order[0]], 'top1': round(float(t1), 4),
                    'margin_12': round(float(t1 - t2), 4), 'entropy': round(ent, 3)})
        top1_atoms.append(atom_names[order[0]])
        top3_sets.append(set(atom_names[j] for j in order[:3]))
    # top-3 重複率 (CID ペア平均 Jaccard)
    jac = []
    for i in range(len(top3_sets)):
        for j in range(i+1, len(top3_sets)):
            a, b = top3_sets[i], top3_sets[j]
            jac.append(len(a & b) / len(a | b))
    return out, top1_atoms, (float(np.mean(jac)) if jac else 0.0)


def audit_condition(cond, atom_names, atom_unit):
    df = load_m4_cids(cond)
    seed_max = v106.compute_seed_max(df)
    V = np.vstack([v106.build_cid_vector(r, seed_max) for _, r in df.iterrows()])
    cids = df['cognitive_id'].astype(int).tolist()
    res = {'cond': cond, 'n_cid': len(df)}

    # 軸ごとの分散 (どの軸が定数同然か)
    axis_disp = {}
    for name, lo, hi in AXIS_BLOCKS:
        block = V[:, lo:hi]
        # 各軸ブロックの「CID 間でどれだけ動くか」= 平均次元分散の総和 + ブロック内 argmax の多様性
        var_sum = float(block.var(axis=0).sum())
        # one-hot 系は argmax の distinct 数で多様性
        distinct = int(len(np.unique(block.argmax(axis=1)))) if block.shape[1] > 1 else 1
        axis_disp[name] = {'var_sum': round(var_sum, 5), 'distinct_buckets': distinct,
                           'near_constant': bool(var_sum < 1e-4)}
    res['axis_dispersion'] = axis_disp
    res['near_constant_axes'] = [k for k, v in axis_disp.items() if v['near_constant']]
    res['active_axes'] = [k for k, v in axis_disp.items() if not v['near_constant']]

    # 有効ランク
    eff, numrank, topvar = effective_rank(V)
    res['effective_rank'] = round(eff, 3)
    res['numerical_rank'] = numrank
    res['pca_explained_top8'] = topvar

    # CID 間 cosine 距離
    mean_d, min_d, max_d = cosine_dists(V)
    res['cid_cosine_dist'] = {'mean': round(mean_d, 4), 'min': round(min_d, 4), 'max': round(max_d, 4)}

    # 大きさ vs 方向
    mags = np.linalg.norm(V, axis=1)
    res['magnitude'] = {'mean': round(float(mags.mean()), 4), 'std': round(float(mags.std()), 4),
                        'cv': round(float(mags.std() / max(mags.mean(), 1e-9)), 4)}

    # atom margin / entropy / top-k 重複 (v106 full vector)
    margins, top1_atoms, top3_jac = atom_margins(V, atom_unit, atom_names)
    res['atom_margin_mean'] = round(float(np.mean([m['margin_12'] for m in margins])), 4)
    res['atom_margin_min'] = round(float(np.min([m['margin_12'] for m in margins])), 4)
    res['atom_entropy_mean'] = round(float(np.mean([m['entropy'] for m in margins])), 3)
    res['v106_top1_distinct'] = int(len(set(top1_atoms)))
    res['v106_top1_atoms'] = dict(pd.Series(top1_atoms).value_counts().head(8).items())
    res['v106_top3_jaccard_mean'] = round(top3_jac, 4)

    # 簡易版 (動態で実使用) rank_1 の分布
    simp = []
    for _, r in df.iterrows():
        a, s = simplified_rank1(r.get('n_core_member', r.get('v11_m_c_n_core', 2)),
                                r.get('original_phase_sig'), atom_names, atom_unit)
        simp.append(a)
    res['simplified_top1_distinct'] = int(len(set(x for x in simp if x)))
    res['simplified_top1_atoms'] = dict(pd.Series(simp).value_counts().head(8).items())

    return res, df, V


def main():
    print('=== v12 Projection Audit (投影側 vs 記帳側、10 軸前提) ===\n')
    atom_names, atom_unit = load_atoms()
    print(f'atom_centroids: {atom_unit.shape} (動態 M2-M4 が使う atom set)')
    print('phase_sig in build_cid_vector inputs:', 'NO (実コードで確認: temporal=lifespan, scale=n_core, ... phase_sig 不使用)')

    report = {'note': 'Projection Audit. v106 build_cid_vector(10軸, phase_sig無) を M4 CID に適用。'
                      '動態の bonus 対象を実決定するのは簡易版 compute_rank_1_atom(scale+phase)。',
              'phase_sig_in_v106_vector': False, 'cosine_used': True}
    for cond in ('off', 'small'):
        res, df, V = audit_condition(cond, atom_names, atom_unit)
        report[cond] = res
        print(f'\n--- {cond} (n_cid={res["n_cid"]}) ---')
        print(f'  active 軸: {res["active_axes"]}')
        print(f'  near-constant 軸: {res["near_constant_axes"]}')
        print(f'  軸別分散: ' + ', '.join(f'{k}={v["var_sum"]}(d{v["distinct_buckets"]})' for k,v in res['axis_dispersion'].items()))
        print(f'  有効ランク={res["effective_rank"]} / 数値ランク={res["numerical_rank"]} / PCA top8={res["pca_explained_top8"]}')
        print(f'  CID 間 cosine 距離: mean={res["cid_cosine_dist"]["mean"]} min={res["cid_cosine_dist"]["min"]}')
        print(f'  大きさ ‖V‖: mean={res["magnitude"]["mean"]} std={res["magnitude"]["std"]} CV={res["magnitude"]["cv"]}')
        print(f'  atom margin(top1-top2): mean={res["atom_margin_mean"]} min={res["atom_margin_min"]} / entropy={res["atom_entropy_mean"]}')
        print(f'  v106 top1 distinct atom={res["v106_top1_distinct"]} top3 Jaccard={res["v106_top3_jaccard_mean"]} dist={res["v106_top1_atoms"]}')
        print(f'  簡易版(動態) top1 distinct atom={res["simplified_top1_distinct"]} dist={res["simplified_top1_atoms"]}')

    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    print(f'\n保存: {OUT}')


if __name__ == '__main__':
    main()
