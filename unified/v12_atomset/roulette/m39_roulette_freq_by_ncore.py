#!/usr/bin/env python3
"""課題#1 — n_core を変えてルーレット選択+頻度グラフ (n_core 別に広げる, 既定 n_core=2)

## 自己規律 (Code A)
①過去引用: m35(連続ルーレット: 各(cid,t)で max(.,0)→正規化→default_rng([0,cid,t]) 一様乱数1つの累積ルーレット,
  n_core=5 の21CID)、m37(頻度グラフ = picks の value_counts の素カウント, 表示は並べ替え/色のみ)、
  m36(ghost は step10 が host_lost で打ち切られ各reaped境界1点で退化)、#30(指標/閾値/濃度の数値化禁止・
  レア消すな)、spec「n_core 別に後で広げられる構造にする(今は n_core=5 のみ)」.
②Taka逐語(原文): 「これは n_core=5 かな? 2の場合はどうなる?」.
③成否判定はTaka(success/fail置かない, 観察事実のみ) ④集約語なし.

## やること: m35/m37 と同一アルゴリズム(seed=default_rng([0,cid,t]) も同一)で母集団を n_core==N に変えて再実行し、
##   picks を記録 + 引かれた回数の頻度グラフ(HTML)を出す。N は引数(既定 2)。
## やらないこと: 新指標/閾値/濃度/集中度/正規化表示/n_core 間の差の数値化・「2は5より○○」等の解釈 — 一切しない。
## 一方向: 読=full_cosine_step10_seed0(m31) / source_events, 書=roulette/ のみ. physics 非書込.
## ※seed は (cid,t) の純関数で n_core 非依存 → n_core=5 を本スクリプトで回すと m35 の picks と一致(広げても既存不変).
usage: python m39_roulette_freq_by_ncore.py [n_core=2]
"""
import sys, time, json
from pathlib import Path
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

SEED = 0   # m35 と同一。各(cid,t) draw = default_rng([SEED,cid,t]).random() (n_core 非依存)
N_CORE = int(sys.argv[1]) if len(sys.argv) > 1 else 2

REPO = Path('/home/takasan/esde/ESDE-Research')
FC = REPO / 'unified/v12_atomset/full_cosine_probe/full_cosine_step10_seed0.parquet'
SE = REPO / 'developmental/v107/outputs/main/source_events_seed0.parquet'
OUT = REPO / 'unified/v12_atomset/roulette'
OUT.mkdir(parents=True, exist_ok=True)
PALETTE = px.colors.qualitative.Dark24 + px.colors.qualitative.Light24


def roulette(n_core):
    """m35 と同一の連続ルーレット(母集団のみ n_core==n_core)。out(picks) と諸数を返す。"""
    fc = pd.read_parquet(FC)
    atoms = [c for c in fc.columns if c not in ('cid', 't')]
    A = np.array(atoms)
    se = pd.read_parquet(SE)
    g = se.groupby('source_cid').agg(n_core=('n_core_member', 'max'),
                                     host_lost=('host_lost_step', 'first')).reset_index()
    nN = g[g.n_core == n_core]
    cids = sorted(int(c) for c in nN.source_cid)
    host_lost = {int(r.source_cid): (float(r.host_lost) if pd.notna(r.host_lost) else np.nan)
                 for _, r in nN.iterrows()}
    d = fc[fc.cid.isin(cids)].sort_values(['cid', 't']).reset_index(drop=True)
    R = len(d)
    cid_arr = d['cid'].values.astype(int)
    t_arr = d['t'].values.astype(int)
    M = d[atoms].values.astype(np.float64)
    hl_arr = np.array([host_lost[c] for c in cid_arr])
    is_ghost = np.where(np.isnan(hl_arr), False, t_arr >= hl_arr)

    Mc = np.maximum(M, 0.0)                          # 負のみ0 (正の下位は残す=レア消さない)
    rowsum = Mc.sum(axis=1)
    zero_rows = int((rowsum == 0).sum())
    safe = rowsum.copy(); safe[safe == 0] = 1.0
    P = Mc / safe[:, None]
    if zero_rows:
        P[rowsum == 0] = 1.0 / len(atoms)
    C = np.cumsum(P, axis=1); C[:, -1] = 1.0
    picked = np.empty(R, dtype=np.int64)
    for r in range(R):
        u = float(np.random.default_rng([SEED, int(cid_arr[r]), int(t_arr[r])]).random())
        picked[r] = np.searchsorted(C[r], u, side='right')
    picked = np.clip(picked, 0, len(atoms) - 1)
    picked_cos = M[np.arange(R), picked]
    picked_prob = P[np.arange(R), picked]
    rank_of_picked = (M > picked_cos[:, None]).sum(axis=1) + 1
    out = pd.DataFrame({'cid': cid_arr, 't': t_arr, 'is_ghost': is_ghost, 'picked_atom': A[picked],
                        'picked_atom_cosine': picked_cos.astype(np.float32),
                        'picked_atom_prob': picked_prob.astype(np.float32),
                        'rank_of_picked': rank_of_picked.astype(np.int32)})
    return out, len(cids), len(atoms), zero_rows


def viz(out, freq, n_core, n_cids, n_atoms_total):
    """m37 と同一デザインの頻度グラフ(上位30具体名 + 全引かれ atom を頻度順・カテゴリ色)。"""
    n_draws = len(out); n_ghost = int(out.is_ghost.sum())
    cats = sorted(freq['cat'].unique())
    cmap = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(cats)}
    freq = freq.assign(color=freq['cat'].map(cmap))
    fig = make_subplots(
        rows=2, cols=1, row_heights=[0.42, 0.58], vertical_spacing=0.1,
        subplot_titles=('① 上位30 atom (具体名・引かれた回数の素のカウント)',
                        f'② 全{n_atoms_total} atom 中 引かれた {len(freq)} 種 (頻度順・色=接頭カテゴリ・hoverで名前/回数)'))
    top = freq.head(30).iloc[::-1]
    fig.add_trace(go.Bar(x=top['count'], y=top['atom'], orientation='h', marker_color=top['color'],
                         text=top['count'], textposition='outside', showlegend=False,
                         hovertemplate='%{y}: %{x} 回<extra></extra>'), row=1, col=1)
    for c in cats:
        sub = freq[freq['cat'] == c]
        fig.add_trace(go.Bar(x=sub['atom'], y=sub['count'], name=c, marker_color=cmap[c],
                             hovertemplate='%{x} (' + c + '): %{y} 回<extra></extra>'), row=2, col=1)
    fig.update_xaxes(categoryorder='array', categoryarray=freq['atom'].tolist(),
                     showticklabels=False, title_text='atom (頻度順, 左=最多)', row=2, col=1)
    fig.update_yaxes(title_text='引かれた回数', row=2, col=1)
    fig.update_xaxes(title_text='引かれた回数', row=1, col=1)
    fig.update_layout(
        height=1150, width=1400, barmode='stack',
        legend=dict(title='接頭カテゴリ', font=dict(size=9), y=0.5),
        title=(f'課題#1 ルーレットで引かれた atom の頻度 — n_core={n_core} (step10 seed0, {n_cids}CID, '
               f'{n_draws:,} draw / ghost {n_ghost}) — 引かれた回数の素のカウントのみ (正規化/濃度/集中度/閾値なし)'))
    return fig, n_ghost


def main():
    t0 = time.time()
    out, n_cids, n_atoms, zero_rows = roulette(N_CORE)
    sfx = f'_ncore{N_CORE}'
    out.to_parquet(OUT / f'roulette_picks_step10_seed0{sfx}.parquet', index=False)

    freq = out['picked_atom'].value_counts().rename_axis('atom').reset_index(name='count')
    freq['cat'] = freq['atom'].str.split('.').str[0]
    freq.rename(columns={'count': 'picked_count'}).to_csv(OUT / f'picked_atom_freq{sfx}.csv', index=False)
    out['rank_of_picked'].value_counts().sort_index().rename_axis('rank').reset_index(name='count')\
        .to_csv(OUT / f'rank_of_picked_dist{sfx}.csv', index=False)
    out[~out.is_ghost]['rank_of_picked'].value_counts().sort_index().rename_axis('rank')\
        .reset_index(name='count').to_csv(OUT / f'rank_of_picked_dist_alive{sfx}.csv', index=False)
    out[out.is_ghost]['rank_of_picked'].value_counts().sort_index().rename_axis('rank')\
        .reset_index(name='count').to_csv(OUT / f'rank_of_picked_dist_ghost{sfx}.csv', index=False)

    fig, n_ghost = viz(out, freq, N_CORE, n_cids, n_atoms)   # freq 列 = atom/count/cat
    hp = OUT / f'm39_atom_freq{sfx}.html'
    fig.write_html(str(hp))

    cost = {'n_core': N_CORE, 'n_cids': n_cids, 'n_draws': int(len(out)), 'n_ghost': n_ghost,
            'n_atoms_picked': int(out.picked_atom.nunique()), 'n_atoms_total': n_atoms,
            'zero_prob_rows': zero_rows, 'total_s': round(time.time() - t0, 2),
            'seed': f'default_rng([{SEED},cid,t]) per (cid,t)'}
    (OUT / f'cost{sfx}.json').write_text(json.dumps(cost, indent=2, ensure_ascii=False))

    print(f'=== n_core={N_CORE}: {n_cids} CID, {len(out):,} draw (ghost {n_ghost}), '
          f'引かれた atom {out.picked_atom.nunique()}/{n_atoms} 種 ===')
    print(f'  count: max {freq["count"].max()} / median {int(freq["count"].median())} / min {freq["count"].min()}')
    print('  上位8:', ', '.join(f'{r.atom} {r.count}' for r in freq.head(8).itertuples()))
    print('  下位8:', ', '.join(f'{r.atom} {r.count}' for r in freq.tail(8).itertuples()))
    print(f'  rank_of_picked: min {int(out.rank_of_picked.min())} / median {int(out.rank_of_picked.median())} / '
          f'mean {out.rank_of_picked.mean():.1f} / max {int(out.rank_of_picked.max())}')
    print(f'  → {hp.relative_to(REPO)}')


if __name__ == '__main__':
    main()
