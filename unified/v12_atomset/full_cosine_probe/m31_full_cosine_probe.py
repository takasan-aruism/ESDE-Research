#!/usr/bin/env python3
"""課題#1 下準備2 — 全326 atom cosine を捨てずに出す (サンプル確認のみ・計算しない)

## 自己規律 (Code A)
①過去引用: m30(sim は N×326 で計算され rank_1 以外捨てている, run_seed_step10:256-262)、#30(気まぐれ
  指標禁止)、m20(build_step10_table/build_step10_cid_vector/atom_profiles_cache slot_keys 整合)。
②Taka逐語(原文): 「各時点で計算され捨てられている全 326 atom の cosine を捨てずに出力して実物を見るだけ」
  「演算・指標・閾値・濃度・spike・Δ・位相化・分布の計算は一切しない」「取れることを確認するのが目的」.
③判定はTaka(success/fail置かない) ④集約語なし.

## やること: 343-348(argmax)で潰す前の sim(N×326) をそのまま保存。新計算を足さない。step10 seed0 のみ。
## やらないこと: 濃度/spike/Δ/分布/エントロピー/閾値/網/投影/位相化 — 一切しない。
## 一方向: 読=frozen, 書=full_cosine_probe/ のみ. physics 非書込.
"""
import sys, time, json
from pathlib import Path
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
from sklearn.metrics.pairwise import cosine_similarity

REPO = Path('/home/takasan/esde/ESDE-Research')
sys.path.insert(0, str(REPO / 'developmental/v106'))
import v106_step10_trajectory as T   # build_step10_table, build_step10_cid_vector, compute_seed_max

OUT_DIR = REPO / 'unified/v12_atomset/full_cosine_probe'
OUT_DIR.mkdir(parents=True, exist_ok=True)
_c = np.load(REPO / 'developmental/v106/outputs/main/atom_profiles_cache.npz', allow_pickle=False)
ATOM_NAMES = np.array([str(x) for x in _c['atom_names']])
PROF = _c['profiles'].astype(np.float64)
VALID = _c['valid_mask']
VALID_NAMES = ATOM_NAMES[VALID]      # 325 valid atom 名


def main():
    seed = 0
    t0 = time.time()
    tbl = T.build_step10_table(seed)
    smax = T.compute_seed_max(tbl)
    t_tbl = time.time() - t0
    # CID 48次元ベクトル (m30 の build_step10_cid_vector, run_seed_step10 と同じ)
    t1 = time.time()
    vecs = np.empty((len(tbl), 48), dtype=np.float64)
    for i, (_, r) in enumerate(tbl.iterrows()):
        vecs[i] = T.build_step10_cid_vector(r, smax)
    t_vec = time.time() - t1
    # 全 valid atom の cosine (run_seed_step10:258 と同じ。argmax で潰さずそのまま)
    t2 = time.time()
    sim = cosine_similarity(vecs, PROF[VALID]).astype(np.float32)   # (N, 325)
    t_cos = time.time() - t2

    cids = tbl['cognitive_id'].values.astype(int)
    ts = tbl['t'].values.astype(int)
    N = len(tbl)

    # --- 全量 wide を保存 (取れることの確認 + サイズ実測) ---
    t3 = time.time()
    wide = pd.DataFrame(sim, columns=VALID_NAMES)
    wide.insert(0, 't', ts); wide.insert(0, 'cid', cids)
    full_path = OUT_DIR / 'full_cosine_step10_seed0.parquet'
    wide.to_parquet(full_path, index=False)
    t_save = time.time() - t3
    full_size_mb = full_path.stat().st_size / 1e6

    # --- 人間可読サンプル: 3つの (cid,t) で 326 atom の cosine の並び (上位/中位/下位) ---
    sample_lines = []
    rng_rows = [N // 4, N // 2, (3 * N) // 4]
    for ri in rng_rows:
        row = sim[ri]
        cid, t = cids[ri], ts[ri]
        order = np.argsort(-row)
        top = [(VALID_NAMES[j], round(float(row[j]), 4)) for j in order[:8]]
        mid = [(VALID_NAMES[j], round(float(row[j]), 4)) for j in order[160:163]]
        bot = [(VALID_NAMES[j], round(float(row[j]), 4)) for j in order[-3:]]
        sample_lines.append({'cid': int(cid), 't': int(t),
                             'top8': top, 'mid(160-162位)': mid, 'bottom3': bot,
                             'cosine_min': round(float(row.min()), 4),
                             'cosine_max': round(float(row.max()), 4),
                             'cosine_mean': round(float(row.mean()), 4)})
    (OUT_DIR / 'sample_rows.json').write_text(json.dumps(sample_lines, indent=2, ensure_ascii=False))

    cost = {
        'seed': seed, 'grain': 'step10', 'n_rows': int(N), 'n_atoms_valid': int(VALID.sum()),
        'build_table_s': round(t_tbl, 1), 'build_vecs_s': round(t_vec, 1),
        'cosine_s': round(t_cos, 2), 'save_s': round(t_save, 1),
        'total_s': round(time.time() - t0, 1), 'full_parquet_MB': round(full_size_mb, 1),
    }
    (OUT_DIR / 'cost.json').write_text(json.dumps(cost, indent=2, ensure_ascii=False))

    print('=== 全326(valid325) atom cosine 出力 (step10 seed0, 計算を足さず argmax 前の sim を保存) ===')
    print(f"  行数 (cid,t): {N}, atom 列: {int(VALID.sum())} (valid)")
    print(f"  cost: build_table {t_tbl:.1f}s / build_vecs {t_vec:.1f}s / cosine {t_cos:.2f}s / save {t_save:.1f}s / 計 {cost['total_s']}s")
    print(f"  全量 parquet サイズ: {full_size_mb:.1f} MB ({full_path.relative_to(REPO)})")
    print(f"  概算: 4粒度×24seed なら ~{full_size_mb*4*24/1000:.1f} GB / 時間 ~{cost['total_s']*4*24/60:.0f}分 (粒度で行数違うので粗概算)")
    print('\n  サンプル (3 (cid,t) で 326 atom がどんな cosine 値で並んでいるか):')
    for s in sample_lines:
        print(f"  --- cid {s['cid']} t {s['t']}: min={s['cosine_min']} mean={s['cosine_mean']} max={s['cosine_max']}")
        print(f"      上位8: {s['top8']}")
        print(f"      中位(160-162): {s['mid(160-162位)']}  下位3: {s['bottom3']}")


if __name__ == '__main__':
    main()
