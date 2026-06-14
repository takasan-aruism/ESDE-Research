#!/usr/bin/env python3
"""v12 Atomset cid_align — STEP 1: minimal cid_align construction (offline, post-process)

## 観察対象注釈ブロック (Code A 自己強制ハードル, 実装着手前に明示)

### 認識の核 (Taka 2026-06-15, 全段階で手放さない)
- Atom も CID も「10 軸 × 下位 levels = 48」の *大枠* は共有するが、下位 level の厳密な
  1-1 対応は無い (両端とも人為的投影、神経-言語の関係同様)。
- 一致率の *絶対値を信じない*。見るのは大枠の寄り方・行き先の方向・往復の頻度。
- (本 STEP では一致率はまだ測らない。cid_align ベクトルの構築のみ。)

### 観察対象
- per-CID per-10step の cid_align ベクトル (経験で寄る Atom 空間座標)。
- 物理 (θ/S/R/E/phase_sig/label.nodes) には一切書かない。本ファイルは v107 ログを
  読んで parquet を書くだけ (post-process, engine を回さない)。

### 何を作り何を作らないか (STEP 1 範囲)
- 作る: v106 build_cid_vector のエンコーダで、v107 source_events の *_pre state を
  48 次元化し、経験列で cid_align ← normalize(cid_align + α·f·exp_vec) と更新。
- STEP 1 で使う軸 (実データで写ると確認できた範囲のみ, 適当解釈禁止):
  * temporal      (lifespan_so_far → temporal_vector)         DIRECT ✓
  * scale         (n_core_member  → scale_vector)             DIRECT ✓
  * interconnection (n_alphas_pre → interconnection_vector)   DIRECT ✓
  * resonance     (C_pre          → resonance_vector)         DIRECT ✓
  * ontological   (Q_pre/v14_q0, n_alphas_pre, n_core, C_pre) 4/5 近似 △
                  (informational=v14_virtual_familiarity_entries は v107 に無く 0 で renormalize)
- STEP 1 で使わない軸 (実データで写らない or partial, 報告に明記):
  * epistemological: R_familiarity_pre は count でなく ratio (-5.79〜20) で v106 の
    count 境界 [10,30,60,150] と非整合 → 写さない (境界を作り直すと簡易 vec48 の罠)。
  * symmetry/lawfulness/experience/value_generation: 必要 field が v107 に無い → 0。

### crown 禁止
- 「個性化成立」「会話に繋がる」は書かない。本 STEP は cid_align ベクトルを作るのみ。
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

REPO = Path('/home/takasan/esde/ESDE-Research')
SRC_DIR = REPO / 'developmental/v107/outputs/main'
OUT_DIR = REPO / 'unified/v12_atomset/run_step1'
OUT_DIR.mkdir(parents=True, exist_ok=True)

N_PER_CHUNK = 10          # per-10step (STEP 0 で確認した v1114 と同じ粒度)
ALPHA = 0.3               # 寄る速さ (prototype と同じ定数)
MAD_C = 1.4826            # robust z の MAD scale
Z_CLIP = 4.0              # robust z のクリップ
K_MIN = 3                 # robust z を立てるのに要る履歴長 (それ未満は f=0)

# 48 次元レイアウト (v106 build_cid_vector と同一の軸順・幅)
#  temporal 7 | scale 6 | epistemological 5 | ontological 5 | interconnection 5 |
#  resonance 4 | symmetry 5 | lawfulness 4 | experience 3 | value_generation 4  = 48
AX = {
    'temporal':        (0, 7),
    'scale':           (7, 6),
    'epistemological': (13, 5),
    'ontological':     (18, 5),
    'interconnection': (23, 5),
    'resonance':       (28, 4),
    # 32-47 は STEP 1 で未使用 (0)
}


# ===== v106 のエンコーダ (developmental/v106/v106_post_process.py から逐語コピー) =====
def _gradient_distribute(value, boundaries, n_levels):
    levels = [0.0] * n_levels
    if value <= boundaries[0]:
        levels[0] = 1.0
        return levels
    for i in range(len(boundaries) - 1):
        lo, hi = boundaries[i], boundaries[i + 1]
        if lo < value <= hi:
            frac = (value - lo) / (hi - lo)
            levels[i] = 1.0 - frac
            levels[i + 1] = frac
            return levels
    levels[-1] = 1.0
    return levels


def temporal_vector(lifespan_steps):
    return _gradient_distribute(lifespan_steps, [100, 500, 2000, 5000, 10000, 15000], 7)


def scale_vector(n_core):
    levels = [0.0] * 6
    n = int(round(n_core))
    if n <= 2:
        levels[0] = 1.0
    elif n == 3:
        levels[1] = 1.0
    elif n == 4:
        levels[2] = 1.0
    elif n == 5:
        levels[3] = 1.0
    elif n == 6:
        levels[4] = 1.0
    else:
        levels[5] = 1.0
    return levels


def interconnection_vector(n_alphas):
    val = n_alphas if not pd.isna(n_alphas) else 0
    return _gradient_distribute(float(val), [1.5, 5.5, 20.5, 50.5], 5)


def resonance_vector(c_value):
    val = c_value if not pd.isna(c_value) else 0
    return _gradient_distribute(float(val), [5, 15, 30], 4)


def ontological_vector_approx(row, seed_max):
    """v106 ontological_vector の 4/5 近似.
    informational (= v14_virtual_familiarity_entries) は v107 に無いため 0、残り 4 で renormalize。
    material は v106 が v14_q_remaining/q0 だが v107 では Q_pre/v14_q0 (Q_pre = q remaining pre-event)。
    relational は n_alphas_currently → n_alphas_pre、semantic は C_at_run_end → C_pre。
    """
    q0 = max(float(row.get('v14_q0', 0) or 0), 1.0)
    material = float(row.get('Q_pre', 0) or 0) / q0
    informational = 0.0  # v107 に field 無し (近似で 0)
    relational = float(row.get('n_alphas_pre', 0) or 0) / max(seed_max.get('n_alphas_max', 1), 1)
    n_core = row.get('n_core_member')
    if pd.isna(n_core):
        n_core = 0
    structural = float(n_core) / 7.0
    semantic = float(row.get('C_pre', 0) or 0) / max(seed_max.get('C_max_seed', 1), 1)
    raw = [material, informational, relational, structural, semantic]
    raw = [max(0.0, min(1.0, v)) for v in raw]
    s = sum(raw)
    if s > 0:
        return [v / s for v in raw]
    return [0.2] * 5


def exp_vec48(row, seed_max):
    """v107 *_pre state row → 48 次元 (STEP 1 で写る軸のみ非ゼロ)。"""
    v = np.zeros(48, dtype=np.float64)
    t0, _ = AX['temporal'];        v[t0:t0 + 7] = temporal_vector(float(row.get('lifespan_so_far', 0) or 0))
    s0, _ = AX['scale'];           v[s0:s0 + 6] = scale_vector(row.get('n_core_member', 2))
    # epistemological: 写さない (R_familiarity_pre が ratio で v106 count 境界と非整合) → 0
    o0, _ = AX['ontological'];     v[o0:o0 + 5] = ontological_vector_approx(row, seed_max)
    i0, _ = AX['interconnection']; v[i0:i0 + 5] = interconnection_vector(row.get('n_alphas_pre', 0))
    r0, _ = AX['resonance'];       v[r0:r0 + 4] = resonance_vector(row.get('C_pre', 0))
    return v


def compute_seed_max(df):
    """seed_max を v107 全ストリームの max から offline 計算 (Code A crux:
    v106 build_cid_vector が live で死んだ run-end 依存を offline で解消)。"""
    def mx(col):
        if col not in df.columns:
            return 1.0
        m = pd.to_numeric(df[col], errors='coerce').max()
        return float(m) if m and m > 0 else 1.0
    return {'n_alphas_max': mx('n_alphas_pre'), 'C_max_seed': mx('C_pre')}


def robust_z_series(vecs):
    """各 event の「いつもと違う度」f = robust_z(||v_t - runmean||) (prototype と同じ)。"""
    rm = np.zeros(vecs.shape[1])
    vals = []
    for t in range(len(vecs)):
        vals.append(np.linalg.norm(vecs[t] - rm) if t > 0 else 0.0)
        rm = rm + (vecs[t] - rm) / (t + 1)
    vals = np.array(vals)
    fs = np.zeros(len(vals))
    for t in range(len(vals)):
        if t >= K_MIN:
            w = vals[:t]
            med = np.median(w)
            mad = np.median(np.abs(w - med)) * MAD_C
            fs[t] = np.clip((vals[t] - med) / max(mad, 1e-3), -Z_CLIP, Z_CLIP)
    return np.abs(fs)


def process_seed(seed):
    df = pd.read_parquet(SRC_DIR / f'source_events_seed{seed}.parquet').sort_values('timestamp')
    seed_max = compute_seed_max(df)
    rows = []
    for cid, g in df.groupby('source_cid'):
        g = g.sort_values('timestamp').reset_index(drop=True)
        vecs = np.array([exp_vec48(r, seed_max) for _, r in g.iterrows()])
        fs = robust_z_series(vecs)
        align = vecs[0] / (np.linalg.norm(vecs[0]) + 1e-9)
        chunks = (g['timestamp'].values // N_PER_CHUNK).astype(int)
        # event 列で align を更新、各 chunk の最後の event 後の状態を記録
        last_chunk = None
        n_in_chunk = 0
        for t in range(len(g)):
            ev = vecs[t] / (np.linalg.norm(vecs[t]) + 1e-9)
            align = align + ALPHA * fs[t] * ev
            align = align / (np.linalg.norm(align) + 1e-9)
            ch = int(chunks[t])
            if last_chunk is not None and ch != last_chunk:
                # 前 chunk を確定 (= 直前の event 後の状態を記録済みにするため flush)
                pass
            if ch == last_chunk:
                n_in_chunk += 1
            else:
                n_in_chunk = 1
            # この event 後の align を当該 chunk の暫定状態として上書き
            if rows and rows[-1]['seed'] == seed and rows[-1]['cid'] == int(cid) and rows[-1]['chunk'] == ch:
                rows[-1].update({f'a{j:02d}': float(align[j]) for j in range(48)})
                rows[-1]['n_events'] = n_in_chunk
            else:
                rec = {'seed': seed, 'cid': int(cid), 'chunk': ch, 'gstep': ch * N_PER_CHUNK,
                       'n_events': n_in_chunk, 'n_core': int(g['n_core_member'].iloc[t])
                       if not pd.isna(g['n_core_member'].iloc[t]) else 0}
                rec.update({f'a{j:02d}': float(align[j]) for j in range(48)})
                rows.append(rec)
            last_chunk = ch
    return rows


def main():
    seeds = list(range(24))
    all_rows = []
    for seed in seeds:
        r = process_seed(seed)
        all_rows.extend(r)
        n_cid = len({(x['seed'], x['cid']) for x in r})
        print(f'seed{seed}: {len(r)} chunk-records, {n_cid} CIDs')
    out = pd.DataFrame(all_rows)
    path = OUT_DIR / 'cid_align_step1.parquet'
    out.to_parquet(path, index=False)
    print(f'\n=== STEP 1 完了 ===')
    print(f'保存: {path.relative_to(REPO)}')
    print(f'総 chunk-records: {len(out)}')
    print(f'総 CID (seed×cid): {out.groupby(["seed","cid"]).ngroups}')
    print(f'n_core 分布: {out.groupby(["seed","cid"]).first()["n_core"].value_counts().sort_index().to_dict()}')
    print(f'CID あたり chunk-records 中央値: {out.groupby(["seed","cid"]).size().median():.0f}')
    # 非ゼロ軸の確認 (どの軸が実際に populate されたか)
    acols = [f'a{j:02d}' for j in range(48)]
    nz = (out[acols].abs().sum(axis=0) > 1e-9).values
    populated = [j for j in range(48) if nz[j]]
    print(f'非ゼロ次元: {len(populated)}/48 (idx {populated[0]}..{populated[-1]})')
    for name, (st, w) in AX.items():
        frac = float((out[[f'a{j:02d}' for j in range(st, st + w)]].abs().sum(axis=1) > 1e-9).mean())
        print(f'  軸 {name:<16} idx[{st}:{st+w}]: 非ゼロ row 割合 {frac:.0%}')


if __name__ == '__main__':
    main()
