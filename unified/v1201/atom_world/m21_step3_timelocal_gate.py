#!/usr/bin/env python3
"""v12 Atomset STEP 3 — time-local 版 GATE 診断 (観察事実のみ、判定しない)

## 自己規律: ③判定はTaka(success/fail置かない) ④集約語なし.
STEP2 GATE 4項目 + 時間版固有:
 A. 0.96 が下がるか: time-local rare↔common の collapsed pair 相関 (STEP2 は 0.96)。
 B. 静的版との差: time-local main(層/窓畳み) vs STEP2 静的 main の rank相関・新規対割合。
 C. 時間で網が動くか: window 別 pair-weight の連続窓相関・top対の窓間 Jaccard。
 D. センター拾う基準 (Taka留保「Atom が接続されたことが意味になっていない」):
    pair の weight 時系列に spike/急変/偏りが在るか (1窓集中度・新規辺の誕生が特定窓に偏るか)。
 E. STEP2同様: 再描画(vs sim_matrix静的共起)・whiteout(node集中/profile相関)・分布の幅(層数)。
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
AW = REPO / 'unified/v1201/atom_world'
TL = AW / 'timelocal'
SM_DIR = REPO / 'developmental/v106/outputs/main'
TOPK = 5


def static_cooc(seed):
    sm = pd.read_parquet(SM_DIR / f'cid_atom_sim_matrix_seed{seed}.parquet')
    cols = [c for c in sm.columns if c not in ('seed', 'cid')]
    M = sm[cols].values.astype(float)
    top = np.argsort(-M, axis=1)[:, :TOPK]
    from collections import Counter
    cnt = Counter()
    for i in range(len(top)):
        ats = sorted(set(int(j) for j in top[i] if M[i, j] > 0))
        for a in range(len(ats)):
            for b in range(a + 1, len(ats)):
                cnt[(cols[ats[a]], cols[ats[b]])] += 1
    return pd.Series(cnt).rename_axis(['atom_i', 'atom_j']).rename('static').reset_index()


def pair_collapse(df):
    return df.groupby(['atom_i', 'atom_j'])['weight'].sum()


def diag(seed):
    tl = pd.read_parquet(TL / f'atom_edges_tl_seed{seed}.parquet')
    tlc = pd.read_parquet(TL / f'common_layer_edges_tl_seed{seed}.parquet')
    st = pd.read_parquet(AW / f'atom_edges_seed{seed}.parquet')      # STEP2 静的
    cooc = static_cooc(seed)
    o = {'seed': seed}

    # A. 0.96 下がるか (time-local rare↔common)
    tlm = pair_collapse(tl).rename('m').reset_index()
    tcm = pair_collapse(tlc).rename('c').reset_index()
    j = tlm.merge(tcm, on=['atom_i', 'atom_j'], how='outer').fillna(0)
    o['A_spearman_tl_main_common'] = float(spearmanr(j['m'], j['c']).correlation)

    # B. 静的版との差 (time-local main vs STEP2 静的 main)
    stm = pair_collapse(st).rename('s').reset_index()
    j2 = tlm.merge(stm, on=['atom_i', 'atom_j'], how='outer').fillna(0)
    o['B_spearman_tl_vs_step2static'] = float(spearmanr(j2['m'], j2['s']).correlation)
    o['B_n_pairs_tl'] = int((j2['m'] > 0).sum()); o['B_n_pairs_step2'] = int((j2['s'] > 0).sum())
    o['B_frac_tl_pairs_new_vs_step2'] = float(((j2['m'] > 0) & (j2['s'] == 0)).sum() / max((j2['m'] > 0).sum(), 1))

    # C. 時間で網が動くか (window 別 pair-weight)
    pw = tl.groupby(['atom_i', 'atom_j', 'window'])['weight'].sum().reset_index()
    wins = sorted(pw['window'].unique())
    mat = pw.pivot_table(index=['atom_i', 'atom_j'], columns='window', values='weight', fill_value=0)
    # 連続窓の相関 (網の形が窓で変わるか)
    consec = []
    for a, b in zip(wins[:-1], wins[1:]):
        if a in mat.columns and b in mat.columns:
            x, y = mat[a].values, mat[b].values
            if x.std() > 0 and y.std() > 0:
                consec.append(np.corrcoef(x, y)[0, 1])
    o['C_consecutive_window_corr_median'] = float(np.median(consec)) if consec else None
    # top20 pair の窓間 Jaccard (連続窓)
    def top20(w):
        return set(mat[w].sort_values(ascending=False).head(20).index) if w in mat.columns else set()
    jacs = []
    for a, b in zip(wins[:-1], wins[1:]):
        A, B = top20(a), top20(b)
        if A or B:
            jacs.append(len(A & B) / len(A | B))
    o['C_top20_consecutive_jaccard_median'] = float(np.median(jacs)) if jacs else None
    o['C_n_windows'] = len(wins)

    # D. センター拾う基準 (spike/急変/偏り)
    # 各 pair の weight 時系列の 1窓集中度 (max窓 share)。高=spike的(その窓で急に繋がった)
    rowsum = mat.sum(axis=1).values
    rowmax = mat.max(axis=1).values
    spike = rowmax / (rowsum + 1e-12)
    o['D_pair_max_window_share_median'] = float(np.median(spike))
    o['D_frac_pairs_spike_above_0.8'] = float((spike > 0.8).mean())   # 1窓にほぼ集中=event的
    # 新規辺の誕生窓の偏り: 各 pair の初出 window 分布のエントロピー的広がり
    first_win = pw.sort_values('window').groupby(['atom_i', 'atom_j'])['window'].first()
    fw_counts = first_win.value_counts(normalize=True)
    o['D_edge_birth_window_top1_share'] = float(fw_counts.max())
    o['D_n_distinct_birth_windows'] = int(first_win.nunique())

    # E. 再描画 / whiteout / 幅
    j3 = tlm.merge(cooc, on=['atom_i', 'atom_j'], how='outer').fillna(0)
    o['E_spearman_tl_vs_cooc'] = float(spearmanr(j3['m'], j3['static']).correlation)
    tl['layer'] = tl['path'] + '|' + tl['channel'] + '|' + tl['n_core_bin'] + '|w' + tl['window'].astype(str)
    npl = tl.groupby(['atom_i', 'atom_j'])['layer'].nunique()
    o['E_pair_n_layers_median'] = float(npl.median())
    # node 集中
    a = tl[['atom_i', 'weight']].rename(columns={'atom_i': 'a'}); b = tl[['atom_j', 'weight']].rename(columns={'atom_j': 'a'})
    nw = pd.concat([a, b]).groupby('a')['weight'].sum().sort_values(ascending=False)
    o['E_n_nodes'] = int(len(nw)); o['E_node_top1_share'] = float(nw.iloc[0] / nw.sum())
    o['E_node_top5_share'] = float(nw.iloc[:5].sum() / nw.sum())
    return o


def main():
    seeds = [0, 1, 2]
    rows = [diag(s) for s in seeds]
    print('=== STEP 3 time-local GATE (観察事実、判定しない。STEP2 静的との対比) ===\n')
    for o in rows:
        print(f"--- seed{o['seed']} ---")
        print(f"  A. 0.96下がるか: time-local rare↔common = {o['A_spearman_tl_main_common']:.3f} (STEP2 静的は 0.96)")
        print(f"  B. 静的版との差: tl↔STEP2静的 rank相関 = {o['B_spearman_tl_vs_step2static']:.3f} | "
              f"tl対数={o['B_n_pairs_tl']} STEP2={o['B_n_pairs_step2']} | tl の新規対 {o['B_frac_tl_pairs_new_vs_step2']:.0%}")
        print(f"  C. 時間で動くか: 連続窓 pair相関 中央={o['C_consecutive_window_corr_median']:.3f} | "
              f"top20 連続窓Jaccard 中央={o['C_top20_consecutive_jaccard_median']:.3f} | 窓数={o['C_n_windows']}")
        print(f"  D. 拾う基準(spike): pair の最大窓share 中央={o['D_pair_max_window_share_median']:.3f} | "
              f"1窓集中(>0.8)割合={o['D_frac_pairs_spike_above_0.8']:.0%} | "
              f"辺誕生窓 top1share={o['D_edge_birth_window_top1_share']:.0%}(誕生窓数{o['D_n_distinct_birth_windows']})")
        print(f"  E. 再描画 tl↔共起={o['E_spearman_tl_vs_cooc']:.3f} | 層数中央={o['E_pair_n_layers_median']:.0f} | "
              f"node {o['E_n_nodes']} top1={o['E_node_top1_share']:.0%} top5={o['E_node_top5_share']:.0%}")
        print()
    pd.DataFrame(rows).to_json(TL / 'gate_timelocal.json', orient='records', indent=2, force_ascii=False)
    print('保存: timelocal/gate_timelocal.json')


if __name__ == '__main__':
    main()
