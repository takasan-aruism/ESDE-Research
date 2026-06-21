#!/usr/bin/env python3
"""v12 Atomset STEP 4 — drift 網 GATE (観察事実のみ、判定しない)

## 自己規律: ③判定はTaka(success/fail置かない) ④集約語なし.
A. Main↔対照A(均等): drift で結ぶ atom が変わるか (collapsed 相関・新規対).
B. Main↔対照B(drift shuffle): 特定 target の drift が効くか (違えば yes).
C. rare↔common: Main の rare↔common 相関 (STEP2 0.96/STEP3 0.925 から下がるか. 下げ幅だけでは
   何も言えない=Taka留保, 対照差が本体).
D. センター拾う基準: Main の辺が ctrlA より時間集中(変化窓に偏る)か (per-pair max窓share 対比).
E. STEP3同様: sim_matrix共起相関(再描画)・層数(幅)・node集中(whiteout).
量=C(v1指示)/Rfam(Code A追加). 物理書込ゼロ(parquet 読むのみ).
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
from scipy.stats import spearmanr

REPO = Path('/home/takasan/esde/ESDE-Research')
TD = REPO / 'unified/v1201/atom_world/timelocal_delta'
SM_DIR = REPO / 'developmental/v106/outputs/main'
QUANTS = ['C', 'Rfam']


def cooc(seed):
    sm = pd.read_parquet(SM_DIR / f'cid_atom_sim_matrix_seed{seed}.parquet')
    cols = [c for c in sm.columns if c not in ('seed', 'cid')]
    M = sm[cols].values.astype(float); top = np.argsort(-M, axis=1)[:, :5]
    from collections import Counter
    cnt = Counter()
    for i in range(len(top)):
        ats = sorted(set(int(j) for j in top[i] if M[i, j] > 0))
        for a in range(len(ats)):
            for b in range(a + 1, len(ats)):
                cnt[(cols[ats[a]], cols[ats[b]])] += 1
    return pd.Series(cnt).rename_axis(['atom_i', 'atom_j']).rename('cooc').reset_index()


def pc(df):
    return df.groupby(['atom_i', 'atom_j'])['weight'].sum()


def sp(x, y):
    return float(spearmanr(x, y).correlation)


def maxwin_share(df):
    pw = df.groupby(['atom_i', 'atom_j', 'window'])['weight'].sum().reset_index()
    g = pw.groupby(['atom_i', 'atom_j'])['weight']
    return (g.max() / g.sum()).median()


def diag(seed):
    ctrlA = pd.read_parquet(TD / f'atom_edges_ctrlA_seed{seed}.parquet')
    co = cooc(seed)
    cA = pc(ctrlA).rename('A').reset_index()
    o = {'seed': seed, 'ctrlA_pairs': int(ctrlA[['atom_i', 'atom_j']].drop_duplicates().shape[0]),
         'ctrlA_maxwin_share': float(maxwin_share(ctrlA))}
    for q in QUANTS:
        m = pd.read_parquet(TD / f'atom_edges_main_{q}_seed{seed}.parquet')
        bB = pd.read_parquet(TD / f'atom_edges_ctrlB_{q}_seed{seed}.parquet')
        cm = pd.read_parquet(TD / f'common_edges_main_{q}_seed{seed}.parquet')
        mm = pc(m).rename('m').reset_index()
        o[f'{q}_main_pairs'] = int(m[['atom_i', 'atom_j']].drop_duplicates().shape[0])
        # A. Main vs ctrlA
        jA = mm.merge(cA, on=['atom_i', 'atom_j'], how='outer').fillna(0)
        o[f'{q}_A_spearman_main_ctrlA'] = sp(jA['m'], jA['A'])
        o[f'{q}_A_frac_main_new_vs_ctrlA'] = float(((jA['m'] > 0) & (jA['A'] == 0)).sum() / max((jA['m'] > 0).sum(), 1))
        # B. Main vs ctrlB (shuffle)
        jb = mm.merge(pc(bB).rename('b').reset_index(), on=['atom_i', 'atom_j'], how='outer').fillna(0)
        o[f'{q}_B_spearman_main_ctrlB'] = sp(jb['m'], jb['b'])
        o[f'{q}_B_frac_main_new_vs_ctrlB'] = float(((jb['m'] > 0) & (jb['b'] == 0)).sum() / max((jb['m'] > 0).sum(), 1))
        # C. rare↔common
        jc = mm.merge(pc(cm).rename('c').reset_index(), on=['atom_i', 'atom_j'], how='outer').fillna(0)
        o[f'{q}_C_spearman_rare_common'] = sp(jc['m'], jc['c'])
        # D. 時間集中 (Main の max窓share vs ctrlA)
        o[f'{q}_D_main_maxwin_share'] = float(maxwin_share(m))
        # E. 再描画/幅/whiteout
        je = mm.merge(co, on=['atom_i', 'atom_j'], how='outer').fillna(0)
        o[f'{q}_E_spearman_main_cooc'] = sp(je['m'], je['cooc'])
        m['layer'] = m['path'] + '|' + m['channel'] + '|' + m['n_core_bin'] + '|w' + m['window'].astype(str)
        o[f'{q}_E_layers_median'] = float(m.groupby(['atom_i', 'atom_j'])['layer'].nunique().median())
        a = m[['atom_i', 'weight']].rename(columns={'atom_i': 'a'}); b = m[['atom_j', 'weight']].rename(columns={'atom_j': 'a'})
        nw = pd.concat([a, b]).groupby('a')['weight'].sum().sort_values(ascending=False)
        o[f'{q}_E_nodes'] = int(len(nw)); o[f'{q}_E_node_top1'] = float(nw.iloc[0] / nw.sum())
    return o


def main():
    rows = [diag(s) for s in [0, 1, 2]]
    print('=== STEP 4 drift GATE (観察事実、判定しない。量= C(v1指示) / Rfam(Code A 追加)) ===\n')
    for o in rows:
        print(f"--- seed{o['seed']} | ctrlA(均等) {o['ctrlA_pairs']}pairs maxwin_share={o['ctrlA_maxwin_share']:.3f} ---")
        for q in QUANTS:
            print(f"  [{q}] main {o[f'{q}_main_pairs']}pairs")
            print(f"     A Main↔ctrlA: spearman={o[f'{q}_A_spearman_main_ctrlA']:.3f} 新規対={o[f'{q}_A_frac_main_new_vs_ctrlA']:.0%}")
            print(f"     B Main↔ctrlB(shuf): spearman={o[f'{q}_B_spearman_main_ctrlB']:.3f} 新規対={o[f'{q}_B_frac_main_new_vs_ctrlB']:.0%}")
            print(f"     C rare↔common: spearman={o[f'{q}_C_spearman_rare_common']:.3f} (STEP2 0.96/STEP3 0.925)")
            print(f"     D 時間集中 maxwin_share={o[f'{q}_D_main_maxwin_share']:.3f} (ctrlA {o['ctrlA_maxwin_share']:.3f})")
            print(f"     E 再描画↔共起={o[f'{q}_E_spearman_main_cooc']:.3f} 層数中央={o[f'{q}_E_layers_median']:.0f} node {o[f'{q}_E_nodes']} top1={o[f'{q}_E_node_top1']:.0%}")
        print()
    pd.DataFrame(rows).to_json(TD / 'gate_step4.json', orient='records', indent=2, force_ascii=False)
    print('保存: timelocal_delta/gate_step4.json')


if __name__ == '__main__':
    main()
