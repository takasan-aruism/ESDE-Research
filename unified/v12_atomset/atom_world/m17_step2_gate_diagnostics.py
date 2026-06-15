#!/usr/bin/env python3
"""v12 Atomset STEP 2 — GATE 診断 (CID 投影の前、Taka に出す観察事実、判定しない)

## 自己規律: ③判定はTaka (success/fail 置かない) ④集約語なし。観察事実(数値)のみ。
設計書 GATE 4項目:
1. v106 再描画度: 網の辺(層畳み weight) vs sim_matrix の atom 共起 の rank 相関。
2. 除去対照: main(rare-gated) vs common(pulse) vs static(sim_matrix 共起) の相関、
   path別 weight 比 (temporal=timing 由来 vs attn/fam=run-wide 静的)。
3. 分布の幅: 辺が (path×channel×n_core) で別パターンを持つか (層あたり集中度 HHI)、
   層を畳むと同形か。
4. whiteout: 層プロファイルが1支配相関に潰れるか (pair プロファイル間の相関分布)、node 集中度。
物理書込ゼロ (parquet 読むのみ)。
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
from scipy.stats import spearmanr

REPO = Path('/home/takasan/esde/ESDE-Research')
AW = REPO / 'unified/v12_atomset/atom_world'
SM_DIR = REPO / 'developmental/v106/outputs/main'
TOPK = 5


def static_cooccurrence(seed):
    """sim_matrix top-k membership から atom 対の within-CID 共起カウント (v106 静的集約)。"""
    sm = pd.read_parquet(SM_DIR / f'cid_atom_sim_matrix_seed{seed}.parquet')
    atom_cols = [c for c in sm.columns if c not in ('seed', 'cid')]
    M = sm[atom_cols].values.astype(np.float64)
    top = np.argsort(-M, axis=1)[:, :TOPK]
    from collections import Counter
    cnt = Counter()
    for i in range(len(top)):
        atoms = sorted(set(int(j) for j in top[i] if M[i, j] > 0))
        for a in range(len(atoms)):
            for b in range(a + 1, len(atoms)):
                cnt[(atom_cols[atoms[a]], atom_cols[atoms[b]])] += 1
    return cnt


def collapsed_pair_weight(edges):
    """層を畳んだ atom 対あたり weight。"""
    return edges.groupby(['atom_i', 'atom_j'])['weight'].sum()


def diag_seed(seed):
    main = pd.read_parquet(AW / f'atom_edges_seed{seed}.parquet')
    common = pd.read_parquet(AW / f'common_layer_edges_seed{seed}.parquet')
    nodes = pd.read_parquet(AW / f'atom_nodes_seed{seed}.parquet')
    cooc = static_cooccurrence(seed)
    cooc_df = pd.Series(cooc).rename_axis(['atom_i', 'atom_j']).rename('static').reset_index()

    out = {'seed': seed}

    # --- (1)+(2) 再描画度 / 除去対照: main/common/static の rank 相関 ---
    mw = collapsed_pair_weight(main).rename('main').reset_index()
    cw = collapsed_pair_weight(common).rename('common').reset_index()
    j = mw.merge(cw, on=['atom_i', 'atom_j'], how='outer').merge(cooc_df, on=['atom_i', 'atom_j'], how='outer').fillna(0)
    out['n_pairs_main'] = int((j['main'] > 0).sum())
    out['n_pairs_common'] = int((j['common'] > 0).sum())
    out['n_pairs_static'] = int((j['static'] > 0).sum())
    out['spearman_main_static'] = float(spearmanr(j['main'], j['static']).correlation)
    out['spearman_common_static'] = float(spearmanr(j['common'], j['static']).correlation)
    out['spearman_main_common'] = float(spearmanr(j['main'], j['common']).correlation)
    # main にあって static に無い対 (網が静的共起に無い辺を作るか) = cross-CID の効果
    out['frac_main_pairs_not_in_static'] = float(((j['main'] > 0) & (j['static'] == 0)).sum() / max((j['main'] > 0).sum(), 1))

    # --- (2) path別 weight 比 (timing vs run-wide static) ---
    pw = main.groupby('path')['weight'].sum()
    tot = pw.sum()
    out['path_weight_share'] = {k: round(v / tot, 3) for k, v in pw.items()}

    # --- (3) 分布の幅: atom 対が何層に跨るか, 層あたり集中度(HHI) ---
    main['layer'] = main['path'] + '|' + main['channel'] + '|' + main['n_core_bin']
    per_pair = main.groupby(['atom_i', 'atom_j'])
    n_layers = per_pair['layer'].nunique()
    def hhi(g):
        w = g['weight'].values; s = w.sum()
        return float(((w / s) ** 2).sum()) if s > 0 else 1.0
    hhis = per_pair.apply(hhi)
    out['pair_n_layers_median'] = float(n_layers.median())
    out['pair_n_layers_max'] = int(n_layers.max())
    out['frac_pairs_single_layer'] = float((n_layers == 1).mean())
    out['pair_layer_HHI_median'] = float(hhis.median())  # 1=1層に集中, 低=層に分散

    # --- (4) whiteout: node 集中度 + 層プロファイル相関 ---
    nw = nodes.sort_values('total_weight', ascending=False)
    tw = nw['total_weight'].sum()
    out['node_top1_share'] = float(nw['total_weight'].iloc[0] / tw)
    out['node_top5_share'] = float(nw['total_weight'].iloc[:5].sum() / tw)
    out['n_nodes'] = int(len(nodes))
    # 層プロファイル whiteout: 上位 pair の (layer) profile を相関 (全 pair は重いので top200)
    top_pairs = collapsed_pair_weight(main).sort_values(ascending=False).head(200).index
    layers = sorted(main['layer'].unique())
    lidx = {l: i for i, l in enumerate(layers)}
    P = np.zeros((len(top_pairs), len(layers)))
    pmap = {(r.atom_i, r.atom_j): k for k, r in enumerate(pd.DataFrame(list(top_pairs), columns=['atom_i', 'atom_j']).itertuples())}
    sub = main[main.set_index(['atom_i', 'atom_j']).index.isin(top_pairs)]
    for r in sub.itertuples():
        if (r.atom_i, r.atom_j) in pmap:
            P[pmap[(r.atom_i, r.atom_j)], lidx[r.layer]] += r.weight
    Pn = P / (np.linalg.norm(P, axis=1, keepdims=True) + 1e-12)
    C = Pn @ Pn.T
    iu = np.triu_indices(len(top_pairs), k=1)
    cc = C[iu]
    out['pair_profile_corr_median'] = float(np.median(cc))
    out['pair_profile_corr_frac_above_0.95'] = float((cc > 0.95).mean())
    return out


def main():
    seeds = [0, 1, 2]
    rows = [diag_seed(s) for s in seeds]
    print('=== STEP 2 GATE 診断 (観察事実、判定しない) ===\n')
    for r in rows:
        print(f"--- seed{r['seed']} ---")
        print(f"  (1)(2) 再描画/除去対照 rank相関: main↔static={r['spearman_main_static']:.3f}  "
              f"common↔static={r['spearman_common_static']:.3f}  main↔common={r['spearman_main_common']:.3f}")
        print(f"        main の対のうち static に無い割合: {r['frac_main_pairs_not_in_static']:.1%} "
              f"(対数 main={r['n_pairs_main']} static={r['n_pairs_static']})")
        print(f"  (2) path別 weight 比: {r['path_weight_share']}")
        print(f"  (3) 分布の幅: 対あたり層数 中央={r['pair_n_layers_median']:.0f} max={r['pair_n_layers_max']} "
              f"単層のみ={r['frac_pairs_single_layer']:.1%} 層HHI中央={r['pair_layer_HHI_median']:.3f}(1=1層集中)")
        print(f"  (4) whiteout: node数={r['n_nodes']} top1={r['node_top1_share']:.1%} top5={r['node_top5_share']:.1%} "
              f"| pairプロファイル相関 中央={r['pair_profile_corr_median']:.3f} >0.95割合={r['pair_profile_corr_frac_above_0.95']:.1%}")
        print()
    pd.DataFrame(rows).to_json(AW / 'gate_diagnostics.json', orient='records', indent=2, force_ascii=False)
    print('保存: atom_world/gate_diagnostics.json')


if __name__ == '__main__':
    main()
