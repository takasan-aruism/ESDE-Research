#!/usr/bin/env python3
"""v12 — cid_align プロトタイプ (Web Claude 案を「実際こうなりました」で検証)
核心: cid_align は物理(θ)から独立した48次元Atom空間座標 → 物理を回さず経験ストリームから
offline で計算できる(decouple の証明そのもの)。経験で Atom に寄るか、real vs shuffle で違うかを
個別 CID で見る。生存でなく Atom 一致率= cosine(cid_align, atom_centroid)。
データ: v107 source_events (per-CID 経験ストリーム、*_pre 状態)。新規発明なし、既存に乗せる。
"""
import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
from pathlib import Path
REPO = Path('/home/takasan/esde/ESDE-Research')
ATOM = pd.read_parquet(REPO / 'unified/v1103/outputs/main/atom_centroids_48d_normalized.parquet')
ANAMES = ATOM['atom'].tolist()
AM = ATOM[[c for c in ATOM.columns if c not in ('atom', 'n_words')]].values.astype(np.float64)
AM = AM / (np.linalg.norm(AM, axis=1, keepdims=True) + 1e-9)
ALPHA = 0.3; K_MIN = 3; MAD_C = 1.4826; Z = 4.0

# v107 *_pre → 48次元 (cid_full_vec と同じ semantic 領域マップ)
def vec48(row):
    v = np.zeros(48)
    n = int(row['n_core_member']) if not pd.isna(row['n_core_member']) else 2
    v[7 + min(max(n - 2, 0), 5)] = 1.0  # scale
    def grad(val, lo, hi, base, nl):
        t = min(max((val - lo) / (hi - lo + 1e-9), 0), 1); v[base + min(int(t * nl), nl - 1)] = 1.0
    grad(row.get('lifespan_so_far', 0), 0, 25000, 0, 7)        # temporal
    grad(row.get('R_familiarity_pre', 0), -1, 1, 13, 5)        # epistemological
    grad(row.get('C_pre', 0), 0, 20, 18, 5)                    # ontological
    grad(row.get('n_alphas_pre', 0), 0, 5, 23, 5)              # interconnection
    grad(row.get('n_observed_pre', 0), 0, 10, 28, 4)           # resonance
    return v


def run_cid(vecs, fvals):
    """cid_align を経験列で更新、各 step の Atom 一致率(最寄り atom cosine)を返す。"""
    align = vecs[0] / (np.linalg.norm(vecs[0]) + 1e-9)
    matches = []
    for t in range(len(vecs)):
        f = fvals[t]
        ev = vecs[t] / (np.linalg.norm(vecs[t]) + 1e-9)
        align = align + ALPHA * f * ev
        align = align / (np.linalg.norm(align) + 1e-9)
        matches.append(float(np.max(AM @ align)))  # 最寄り atom への一致率
    return matches


def build_streams(seed):
    df = pd.read_parquet(REPO / f'developmental/v107/outputs/main/source_events_seed{seed}.parquet')
    df = df.sort_values('timestamp')
    streams = {}
    for cid, g in df.groupby('source_cid'):
        if len(g) < K_MIN + 2: continue
        vs = np.array([vec48(r) for _, r in g.iterrows()])
        # f = robust_z of ||v - runmean|| (いつもと違う度)
        rm = np.zeros(48); fs = []
        vals = []
        for t in range(len(vs)):
            value = np.linalg.norm(vs[t] - rm) if t > 0 else 0.0
            vals.append(value); rm = rm + (vs[t] - rm) / (t + 1)
        vals = np.array(vals)
        for t in range(len(vals)):
            if t >= K_MIN:
                w = vals[:t]; med = np.median(w); mad = np.median(np.abs(w - med)) * MAD_C
                fs.append(float(np.clip((vals[t] - med) / max(mad, 1e-3), -Z, Z)))
            else: fs.append(0.0)
        streams[int(cid)] = (vs, np.abs(fs))
    return streams


print('=== cid_align プロトタイプ: 経験で Atom 一致率が上がるか (物理を回さず offline) ===')
print('  decouple の証明: cid_align は θ と独立 → 経験ストリームだけで計算できる\n')
rng = np.random.default_rng(0)
for seed in [0, 1, 2]:
    st = build_streams(seed)
    cids = list(st.keys())
    # real: 自分の経験。 shuffle: cid X の align を cid Y の経験で
    real_gain = []; shuf_gain = []
    perm = list(cids); rng.shuffle(perm)
    for i, cid in enumerate(cids):
        vs, fs = st[cid]
        m_real = run_cid(vs, fs)
        vs2, fs2 = st[perm[i]]                       # 他人の経験
        m_shuf = run_cid(vs2[:len(vs)] if len(vs2) >= len(vs) else vs2, fs2[:len(vs)] if len(fs2) >= len(vs) else fs2)
        real_gain.append(m_real[-1] - m_real[0])     # 一致率の上がり (最終-初期)
        shuf_gain.append(m_shuf[-1] - m_shuf[0])
    real_gain = np.array(real_gain); shuf_gain = np.array(shuf_gain)
    print(f'seed{seed}: {len(cids)} CID | Atom一致率の上がり(最終-初期): real mean={real_gain.mean():+.4f}, shuffle mean={shuf_gain.mean():+.4f}')
    print(f'         real>0 の CID: {int((real_gain>0).sum())}/{len(cids)} ({100*(real_gain>0).mean():.0f}%) | real>shuffle: {int((real_gain>shuf_gain).sum())}/{len(cids)}')
    # 個別 CID 3個の一致率時間遷移 (集約でなく)
    if seed == 0:
        print('  個別 CID の Atom 一致率 時間遷移 (経験を積むほど上がるか):')
        for cid in cids[:3]:
            vs, fs = st[cid]; m = run_cid(vs, fs)
            print(f'    CID{cid} ({len(m)}event): {[round(x,3) for x in m[::max(1,len(m)//8)]]}')
