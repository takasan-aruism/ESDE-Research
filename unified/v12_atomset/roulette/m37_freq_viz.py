#!/usr/bin/env python3
"""課題#1 — ルーレットで引かれた atom の頻度グラフ (素のカウントのみ・HTML)

## 自己規律 (Code A)
①過去引用: m35(連続ルーレットで各(cid,t)1回引いた picked_atom を記録)、m36(全325 atom が≥1回, min8/max201)、
  #30(気まぐれ指標禁止・濃度/集中度の数値化禁止)、m33(可視化は表示の選択=並べ替え/色 のみ, 指標でない)。
②Taka逐語(原文): 「今回どんな Atom がどれくらいの頻度で選ばれたのかをグラフで表示して」「html形式でいい」.
③判定はTaka(success/fail置かない) ④集約語なし.

## やること: m35 の picks を value_counts(=素の頻度)し、上位30(具体名) + 全325(頻度順・接頭カテゴリ色)を棒で描く。
## やらないこと: 正規化/濃度/集中度/エントロピー/閾値/「目立ち」判定/解釈 — 一切しない(載せるのは生のカウント)。
## 一方向: 読=roulette_picks_step10_seed0.parquet(m35出力), 書=roulette/ のみ. physics 非書込.
"""
from pathlib import Path
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

REPO = Path('/home/takasan/esde/ESDE-Research')
OUT = REPO / 'unified/v12_atomset/roulette'
PICKS = OUT / 'roulette_picks_step10_seed0.parquet'

PALETTE = px.colors.qualitative.Dark24 + px.colors.qualitative.Light24   # 48 色 (カテゴリ用)


def main():
    o = pd.read_parquet(PICKS)
    n_draws = len(o)
    n_ghost = int(o.is_ghost.sum())

    # 素の頻度 (何回引かれたか) を降順に. 接頭カテゴリは atom 名の '.' 前(表示の色分け用, 指標でない)
    freq = o['picked_atom'].value_counts().rename_axis('atom').reset_index(name='count')
    freq['cat'] = freq['atom'].str.split('.').str[0]
    cats = sorted(freq['cat'].unique())
    cmap = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(cats)}
    freq['color'] = freq['cat'].map(cmap)
    freq['freq_rank'] = range(1, len(freq) + 1)   # 頻度順位(1=最多), 表示用の並び

    fig = make_subplots(
        rows=2, cols=1, row_heights=[0.42, 0.58], vertical_spacing=0.1,
        subplot_titles=(
            f'① 上位30 atom (具体名・引かれた回数の素のカウント)',
            f'② 全325 atom (頻度順・色=atom接頭カテゴリ・hoverで名前/回数) — 長い尾まで'))

    # ① 上位30 (横棒, 名前が読める. 最多を上に)
    top = freq.head(30).iloc[::-1]
    fig.add_trace(go.Bar(
        x=top['count'], y=top['atom'], orientation='h',
        marker_color=top['color'], text=top['count'], textposition='outside',
        showlegend=False,
        hovertemplate='%{y}: %{x} 回<extra></extra>'), row=1, col=1)

    # ② 全325 (縦棒, 頻度順. カテゴリ毎の trace = 凡例トグル可)
    for c in cats:
        sub = freq[freq['cat'] == c]
        fig.add_trace(go.Bar(
            x=sub['atom'], y=sub['count'], name=c, marker_color=cmap[c],
            hovertemplate='%{x} ('+c+'): %{y} 回<extra></extra>'), row=2, col=1)
    # x を全体の頻度順に固定 (カテゴリ別 trace でも並びは一本の降順)
    fig.update_xaxes(categoryorder='array', categoryarray=freq['atom'].tolist(),
                     showticklabels=False, title_text='atom (頻度順, 左=最多)', row=2, col=1)
    fig.update_yaxes(title_text='引かれた回数', row=2, col=1)
    fig.update_xaxes(title_text='引かれた回数', row=1, col=1)

    fig.update_layout(
        height=1150, width=1400, barmode='stack',
        legend=dict(title='接頭カテゴリ', font=dict(size=9), y=0.5),
        title=(f'課題#1 ルーレットで引かれた atom の頻度 (step10 seed0, n_core=5 の21CID, '
               f'{n_draws:,} 回 draw / うち ghost {n_ghost}) — 載せたのは引かれた回数の素のカウントのみ '
               f'(正規化/濃度/集中度/閾値なし)'))

    p = OUT / 'm37_atom_freq.html'
    fig.write_html(str(p))

    # おまけ: 最多/最少を print (報告貼付用, 素のまま)
    print(f'=== atom 頻度グラフ → {p.relative_to(REPO)} ===')
    print(f'  draw {n_draws:,} 回 (ghost {n_ghost}), 引かれた atom {len(freq)}/325 種, カテゴリ {len(cats)} 種')
    print(f'  count: max {freq["count"].max()} / median {int(freq["count"].median())} / min {freq["count"].min()}')
    print('  上位8:', ', '.join(f'{r.atom} {r.count}' for r in freq.head(8).itertuples()))
    print('  下位8:', ', '.join(f'{r.atom} {r.count}' for r in freq.tail(8).itertuples()))


if __name__ == '__main__':
    main()
