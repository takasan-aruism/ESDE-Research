#!/usr/bin/env python3
"""v12 Atomset (atom×atom 関係網) STEP 2 — 網形成のみ

## 自己規律 (Code A)
①過去引用: STEP1調査 m15 (Q1 経路で到達CID変わる/Q2 sim_matrix membership/Q3 source_events
  だけで rarity_z/Q4 書込禁止先/Q5 event駆動 atom網は過去に無し), relation_paths_seed0(851154,
  event_id join 確認), ingestion≡c_conversion 完全一致(152,検証済), sim_matrix coverage 100%.
②Taka逐語(原文): 「atom×atom 網を育てるまで」「辺を単一スカラーにしない(揺れの幅・whiteout回避)」
  「s 内 atom 同士は結ばない」「物理書込ゼロ」「post-process。読むのは frozen、書くのは atom_world/ のみ」.
③判定はTaka (success/fail/Full/Partial 置かない、観察事実のみ).
④集約語なし.

## 辺の作り方 (設計書 concrete)
- チャネル: {pulse, alpha_formation, beta_formation, ingestion_cc}。ingestion と c_conversion は
  同一(cid,t)→ ingestion を ingestion_cc に、c_conversion は dedup で drop。
- 珍しさゲート: rare {ingestion_cc, beta_formation, alpha_formation} だけ辺を張る (main)。
  pulse は held-back common 層 (除去対照、別ファイル)。
- 辺は cross-CID のみ: gated event(event_id) の各経路 p の到達 target_cid (relation_paths)、
  source s の atom(top-k) × target c の atom(top-k) の cross product。i==j 除去。無向 canonical。
  s 内 atom 同士は結ばない (cross-CID のみ)。
- 単一スカラーにしない: (path × channel × n_core_bin) で層別したセルに貯める。
## knob (Taka 上書き可、Code A は勝手に変えない)
- D1 membership top-k=5、各 atom に sim score 重み。 D2 ゲート=type ベース、各辺に rarity_z tag
  (source_cid 履歴の n_observed_pre robust_z=MAD-DT、ゲートには使わず分布tag)。 D3 n_core_bin=2/3-4/5+。

## 一方向保証: 読む=frozen(source_events/relation_paths/sim_matrix), 書く=atom_world/ のみ。
  physics.inject/ledger/CIDテーブルに書かない。
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

REPO = Path('/home/takasan/esde/ESDE-Research')
SE_DIR = REPO / 'developmental/v107/outputs/main'
SM_DIR = REPO / 'developmental/v106/outputs/main'
OUT_DIR = REPO / 'atom_world'
OUT_DIR.mkdir(parents=True, exist_ok=True)

TOPK = 5
RARE = ['ingestion_cc', 'beta_formation', 'alpha_formation']  # main 層 (ゲート通過)
PATHS = ['familiarity', 'attention_via_salience', 'integration_alpha',
         'integration_beta', 'temporal_coactivation']
MAD_C = 1.4826
RARITY_Z_CLIP = 5.0  # MAD=0 (定数 n_observed_pre) で robust_z が爆発するのを抑える clip


def n_core_bin(n):
    if n <= 2: return '2'
    if n <= 4: return '3-4'
    return '5+'


def membership_long(sm):
    """各 CID の top-k atom (atom_idx + sim weight)。"""
    atom_cols = [c for c in sm.columns if c not in ('seed', 'cid')]
    M = sm[atom_cols].values.astype(np.float64)
    cids = sm['cid'].values
    top = np.argsort(-M, axis=1)[:, :TOPK]
    rows = []
    for i, cid in enumerate(cids):
        for j in top[i]:
            w = M[i, j]
            if w > 0:
                rows.append((int(cid), int(j), float(w)))
    return pd.DataFrame(rows, columns=['cid', 'atom_idx', 'w']), atom_cols


def rarity_z_map(se):
    """各 event の per-CID surprise = source_cid 履歴の n_observed_pre の robust_z (MAD-DT)。"""
    z = np.zeros(len(se))
    for cid, idx in se.groupby('source_cid').groups.items():
        x = pd.to_numeric(se.loc[idx, 'n_observed_pre'], errors='coerce').values.astype(float)
        med = np.median(x); mad = np.median(np.abs(x - med)) * MAD_C
        zz = (x - med) / max(mad, 1e-3)
        z[se.index.get_indexer(idx)] = np.clip(zz, -RARITY_Z_CLIP, RARITY_Z_CLIP)
    return z


def expand_and_agg(events, rp, memb, chunk=4000):
    """events(event_id,source_cid,channel,n_core_bin,rarity_z) を relation_paths と join し
    source/target の atom cross product を層別集計。memory のため event を chunk 分割。"""
    aggs = []
    ev_ids = events['event_id'].values
    for k in range(0, len(events), chunk):
        ev = events.iloc[k:k + chunk]
        long = ev.merge(rp[['event_id', 'target_cid', 'relation_path_type']], on='event_id')
        long = long.rename(columns={'relation_path_type': 'path', 'source_cid': 's', 'target_cid': 'c'})
        long = long.merge(memb.rename(columns={'cid': 's', 'atom_idx': 'ai', 'w': 'wi'}), on='s')
        long = long.merge(memb.rename(columns={'cid': 'c', 'atom_idx': 'aj', 'w': 'wj'}), on='c')
        long = long[long['ai'] != long['aj']]
        if long.empty:
            continue
        ai = long['ai'].values; aj = long['aj'].values
        long['atom_i'] = np.minimum(ai, aj); long['atom_j'] = np.maximum(ai, aj)
        long['weight'] = long['wi'].values * long['wj'].values
        g = long.groupby(['atom_i', 'atom_j', 'path', 'channel', 'n_core_bin'], observed=True).agg(
            weight=('weight', 'sum'), n_events=('weight', 'size'),
            rarity_z_sum=('rarity_z', 'sum')).reset_index()
        aggs.append(g)
    if not aggs:
        return pd.DataFrame(columns=['atom_i', 'atom_j', 'path', 'channel', 'n_core_bin',
                                     'weight', 'n_events', 'rarity_z_sum'])
    allg = pd.concat(aggs, ignore_index=True)
    final = allg.groupby(['atom_i', 'atom_j', 'path', 'channel', 'n_core_bin'], observed=True).agg(
        weight=('weight', 'sum'), n_events=('n_events', 'sum'),
        rarity_z_sum=('rarity_z_sum', 'sum')).reset_index()
    final['rarity_z_mean'] = final['rarity_z_sum'] / final['n_events']
    return final.drop(columns='rarity_z_sum')


def process_seed(seed):
    se = pd.read_parquet(SE_DIR / f'source_events_seed{seed}.parquet').reset_index(drop=True)
    rp = pd.read_parquet(SE_DIR / f'relation_paths_seed{seed}.parquet')
    sm = pd.read_parquet(SM_DIR / f'cid_atom_sim_matrix_seed{seed}.parquet')
    memb, atom_cols = membership_long(sm)
    sm_cids = set(memb['cid'].unique())
    se['rarity_z'] = rarity_z_map(se)
    # channel map: ingestion->ingestion_cc, c_conversion drop(dedup), pulse->common, else 同名
    se['channel'] = se['event_source_type'].map(
        {'ingestion': 'ingestion_cc', 'alpha_formation': 'alpha_formation',
         'beta_formation': 'beta_formation', 'pulse': 'pulse'})
    se = se[se['event_source_type'] != 'c_conversion']        # dedup drop
    se['n_core_bin'] = se['n_core_member'].apply(n_core_bin)
    cols = ['event_id', 'source_cid', 'channel', 'n_core_bin', 'rarity_z']
    main_ev = se[se['channel'].isin(RARE)][cols]
    common_ev = se[se['channel'] == 'pulse'][cols]

    main = expand_and_agg(main_ev, rp, memb)
    common = expand_and_agg(common_ev, rp, memb)
    for df in (main, common):
        df.insert(0, 'seed', seed)
        df['atom_i'] = df['atom_i'].map(lambda j: atom_cols[j])
        df['atom_j'] = df['atom_j'].map(lambda j: atom_cols[j])

    # nodes rollup (main のみ)
    a = main[['atom_i', 'weight']].rename(columns={'atom_i': 'atom_id'})
    b = main[['atom_j', 'weight']].rename(columns={'atom_j': 'atom_id'})
    nw = pd.concat([a, b]).groupby('atom_id')['weight'].sum()
    pa = main.groupby('atom_i')['atom_j'].apply(set)
    pb = main.groupby('atom_j')['atom_i'].apply(set)
    partners = {}
    for at in set(pa.index) | set(pb.index):
        partners[at] = len(pa.get(at, set()) | pb.get(at, set()))
    nodes = pd.DataFrame({'atom_id': list(nw.index),
                          'total_weight': nw.values,
                          'n_distinct_partners': [partners.get(a, 0) for a in nw.index]})
    nodes.insert(0, 'seed', seed)

    main.to_parquet(OUT_DIR / f'atom_edges_seed{seed}.parquet', index=False)
    common.to_parquet(OUT_DIR / f'common_layer_edges_seed{seed}.parquet', index=False)
    nodes.to_parquet(OUT_DIR / f'atom_nodes_seed{seed}.parquet', index=False)

    # coverage (membership 被覆)
    gated_src = set(se[se['channel'].isin(RARE)]['source_cid'].unique())
    tgt = set(rp[rp['event_id'].isin(se[se['channel'].isin(RARE)]['event_id'])]['target_cid'].unique())
    cov = {'seed': seed,
           'n_cid_in_sim_matrix': len(sm_cids),
           'gated_source_cid_coverage': len(gated_src & sm_cids) / max(len(gated_src), 1),
           'gated_target_cid_coverage': len(tgt & sm_cids) / max(len(tgt), 1),
           'n_main_edge_cells': int(len(main)), 'n_common_edge_cells': int(len(common)),
           'n_distinct_atom_pairs_main': int(main[['atom_i', 'atom_j']].drop_duplicates().shape[0]),
           'n_nodes': int(len(nodes))}
    (OUT_DIR / f'coverage_seed{seed}.json').write_text(json.dumps(cov, indent=2, ensure_ascii=False))
    return cov


def main():
    covs = []
    for seed in range(24):
        c = process_seed(seed)
        covs.append(c)
        print(f"seed{seed}: main_cells={c['n_main_edge_cells']} "
              f"distinct_pairs={c['n_distinct_atom_pairs_main']} nodes={c['n_nodes']} "
              f"common_cells={c['n_common_edge_cells']} "
              f"src_cov={c['gated_source_cid_coverage']:.0%} tgt_cov={c['gated_target_cid_coverage']:.0%}")
    print('\n=== STEP 2 網形成 完了 (atom_world/) ===')


if __name__ == '__main__':
    main()
