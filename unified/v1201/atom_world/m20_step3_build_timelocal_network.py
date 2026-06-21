#!/usr/bin/env python3
"""v12 Atomset STEP 3 — 時間局所 membership 版 atom×atom 網

## 自己規律 (Code A)
①過去引用: STEP2 m16(辺ロジック), m18(main↔common0.96=出来事が網を方向づけてない),
  m19土台調査(時間局所は4粒度在/rank1のみ/top5は再計算可・v105logs+atom_profiles_cache 全在),
  STEP3 cid_align で確認の atom_profiles_cache slot_keys 整合(v1103アルファベット順は使わない).
②Taka逐語(原文): 「全部読んで変える系なら何やったって変化しないに決まってる。時間の概念をいれるなら
  それが Step なり Window なり」「変えるのは membership の時間性だけ」「Atom が接続されたことが意味に
  なっていない／センターはなぜそれを受け取ったのか」「全部やってみて。他は任せる」.
③判定はTaka(success/fail置かない) ④集約語なし.

## 変更点 (STEP2 から membership の時間性だけ)
- membership: run終わり sim_matrix → t時点の time-local top-5 (build_step10_cid_vector を t行で
  再計算 → atom_profiles_cache と cosine → top-5, sim重み). 粒度=step10(10step).
- 辺ロジックは STEP2 不変: cross-CID のみ・rare ゲート・(path×channel×n_core)層別・i≠j・無向 canonical.
- 出力に window 列追加 (event の t//500). 「いつ どの atom がつながったか」を残す.

## 一方向保証: 読=frozen(v105 diag logs/relation_paths/source_events/atom_profiles_cache),
  書=atom_world/timelocal/ のみ. physics.inject/ledger/CID 非書込.
"""
import sys, json, time
from pathlib import Path
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

REPO = Path('/home/takasan/esde/ESDE-Research')
sys.path.insert(0, str(REPO / 'developmental/v106'))
import v106_step10_trajectory as T   # build_step10_table, build_step10_cid_vector, compute_seed_max

SE_DIR = REPO / 'developmental/v107/outputs/main'
OUT_DIR = REPO / 'unified/v1201/atom_world/timelocal'
OUT_DIR.mkdir(parents=True, exist_ok=True)

TOPK = 5
RARE = ['ingestion_cc', 'beta_formation', 'alpha_formation']
MAD_C = 1.4826
RARITY_Z_CLIP = 5.0
WIN = 500  # 出力 window 列の time bin (step)

_cache = np.load(REPO / 'developmental/v106/outputs/main/atom_profiles_cache.npz', allow_pickle=False)
ATOM_NAMES = _cache['atom_names']
_prof = _cache['profiles'].astype(np.float64)
_valid = _cache['valid_mask']
_prof[~_valid] = 0.0
_PROFN = _prof / (np.linalg.norm(_prof, axis=1, keepdims=True) + 1e-12)


def n_core_bin(n):
    if pd.isna(n): return '2'
    n = int(n)
    return '2' if n <= 2 else ('3-4' if n <= 4 else '5+')


def timelocal_membership(seed):
    """各 (cid, t=10step) の top-5 atom (idx, sim重み) を build_step10_cid_vector 再計算で。"""
    tbl = T.build_step10_table(seed)
    if tbl.empty:
        return pd.DataFrame(columns=['cid', 't', 'atom_idx', 'w'])
    smax = T.compute_seed_max(tbl)
    vecs = np.empty((len(tbl), 48), dtype=np.float64)
    for i, (_, r) in enumerate(tbl.iterrows()):
        vecs[i] = T.build_step10_cid_vector(r, smax)
    vn = vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12)
    sims = vn @ _PROFN.T              # (N, 326)
    sims[:, ~_valid] = -np.inf
    top = np.argpartition(-sims, TOPK, axis=1)[:, :TOPK]
    cids = tbl['cognitive_id'].values.astype(int)
    ts = tbl['t'].values.astype(int)
    rows = []
    for i in range(len(tbl)):
        for j in top[i]:
            w = sims[i, j]
            if w > 0:
                rows.append((cids[i], ts[i], int(j), float(w)))
    return pd.DataFrame(rows, columns=['cid', 't', 'atom_idx', 'w'])


def rarity_z_map(se):
    z = np.zeros(len(se))
    for cid, idx in se.groupby('source_cid').groups.items():
        x = pd.to_numeric(se.loc[idx, 'n_observed_pre'], errors='coerce').values.astype(float)
        med = np.median(x); mad = np.median(np.abs(x - med)) * MAD_C
        z[se.index.get_indexer(idx)] = np.clip((x - med) / max(mad, 1e-3), -RARITY_Z_CLIP, RARITY_Z_CLIP)
    return z


def asof_grid(ev_keys, memb_times, cid_col, t_out):
    """ev_keys[cid_col, t_event] に対し memb_times(cid,t) から backward asof で grid t を付与。"""
    mt = memb_times.rename(columns={'cid': cid_col, 't': t_out}).sort_values(t_out)
    e = ev_keys.sort_values('t_event')
    m = pd.merge_asof(e, mt, left_on='t_event', right_on=t_out, by=cid_col, direction='backward')
    return m


def build_layer(events, rp, memb, memb_times, chunk=3000):
    """events(event_id,s,c... は無し; ここでは event 単位) を relation_paths と join し
    s/c の time-local membership で atom cross product。"""
    aggs = []
    for k in range(0, len(events), chunk):
        ev = events.iloc[k:k + chunk]
        long = ev.merge(rp[['event_id', 'target_cid', 'relation_path_type']], on='event_id')
        long = long.rename(columns={'relation_path_type': 'path', 'source_cid': 's', 'target_cid': 'c'})
        if long.empty:
            continue
        # time-local grid for s and c at t_event
        src_keys = long[['s', 't_event']].drop_duplicates()
        src_keys = asof_grid(src_keys, memb_times, 's', 't_src')
        tgt_keys = long[['c', 't_event']].drop_duplicates()
        tgt_keys = asof_grid(tgt_keys, memb_times, 'c', 't_tgt')
        long = long.merge(src_keys, on=['s', 't_event']).merge(tgt_keys, on=['c', 't_event'])
        long = long.dropna(subset=['t_src', 't_tgt'])
        if long.empty:
            continue
        long = long.merge(memb.rename(columns={'cid': 's', 't': 't_src', 'atom_idx': 'ai', 'w': 'wi'}),
                          on=['s', 't_src'])
        long = long.merge(memb.rename(columns={'cid': 'c', 't': 't_tgt', 'atom_idx': 'aj', 'w': 'wj'}),
                          on=['c', 't_tgt'])
        long = long[long['ai'] != long['aj']]
        if long.empty:
            continue
        ai = long['ai'].values; aj = long['aj'].values
        long['atom_i'] = np.minimum(ai, aj); long['atom_j'] = np.maximum(ai, aj)
        long['weight'] = long['wi'].values * long['wj'].values
        g = long.groupby(['atom_i', 'atom_j', 'path', 'channel', 'n_core_bin', 'window'], observed=True).agg(
            weight=('weight', 'sum'), n_events=('weight', 'size'),
            rarity_z_sum=('rarity_z', 'sum')).reset_index()
        aggs.append(g)
    if not aggs:
        return pd.DataFrame(columns=['atom_i', 'atom_j', 'path', 'channel', 'n_core_bin', 'window',
                                     'weight', 'n_events', 'rarity_z_sum'])
    allg = pd.concat(aggs, ignore_index=True)
    f = allg.groupby(['atom_i', 'atom_j', 'path', 'channel', 'n_core_bin', 'window'], observed=True).agg(
        weight=('weight', 'sum'), n_events=('n_events', 'sum'), rarity_z_sum=('rarity_z_sum', 'sum')).reset_index()
    f['rarity_z_mean'] = f['rarity_z_sum'] / f['n_events']
    return f.drop(columns='rarity_z_sum')


def process_seed(seed):
    t0 = time.time()
    memb = timelocal_membership(seed)
    memb_times = memb[['cid', 't']].drop_duplicates()
    se = pd.read_parquet(SE_DIR / f'source_events_seed{seed}.parquet').reset_index(drop=True)
    rp = pd.read_parquet(SE_DIR / f'relation_paths_seed{seed}.parquet')
    se['rarity_z'] = rarity_z_map(se)
    se['channel'] = se['event_source_type'].map(
        {'ingestion': 'ingestion_cc', 'alpha_formation': 'alpha_formation',
         'beta_formation': 'beta_formation', 'pulse': 'pulse'})
    se = se[se['event_source_type'] != 'c_conversion']
    se['n_core_bin'] = se['n_core_member'].apply(n_core_bin)
    se['t_event'] = se['timestamp'].astype(int)
    se['window'] = (se['t_event'] // WIN).astype(int)
    cols = ['event_id', 'source_cid', 'channel', 'n_core_bin', 'rarity_z', 't_event', 'window']
    main_ev = se[se['channel'].isin(RARE)][cols]
    common_ev = se[se['channel'] == 'pulse'][cols]

    main = build_layer(main_ev, rp, memb, memb_times)
    common = build_layer(common_ev, rp, memb, memb_times)
    for df in (main, common):
        df.insert(0, 'seed', seed)
        df['atom_i'] = df['atom_i'].map(lambda j: ATOM_NAMES[j])
        df['atom_j'] = df['atom_j'].map(lambda j: ATOM_NAMES[j])
    main.to_parquet(OUT_DIR / f'atom_edges_tl_seed{seed}.parquet', index=False)
    common.to_parquet(OUT_DIR / f'common_layer_edges_tl_seed{seed}.parquet', index=False)

    cov = {'seed': seed, 'n_main_cells': int(len(main)), 'n_common_cells': int(len(common)),
           'n_distinct_pairs_main': int(main[['atom_i', 'atom_j']].drop_duplicates().shape[0]),
           'n_windows_main': int(main['window'].nunique()),
           'n_memb_grid_rows': int(len(memb)),
           'elapsed_s': round(time.time() - t0, 1)}
    (OUT_DIR / f'coverage_tl_seed{seed}.json').write_text(json.dumps(cov, indent=2, ensure_ascii=False))
    return cov


def main():
    seeds = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(24))
    for seed in seeds:
        c = process_seed(seed)
        print(f"seed{seed}: main_cells={c['n_main_cells']} pairs={c['n_distinct_pairs_main']} "
              f"windows={c['n_windows_main']} common_cells={c['n_common_cells']} "
              f"memb_rows={c['n_memb_grid_rows']} ({c['elapsed_s']}s)")
    print('=== STEP 3 time-local 網形成 完了 (atom_world/timelocal/) ===')


if __name__ == '__main__':
    main()
