#!/usr/bin/env python3
"""課題#1 — 全326(valid325) cosine の直感グラフ3種 (生 cosine のみ・計算は足さない)

## 自己規律 (Code A)
①過去引用: m31(full_cosine_step10_seed0 = argmax 前の全325 cosine)、#30(気まぐれ指標禁止・Ghost分離・
  生き物的統計)、m27監査(is_ghost = t>=host_lost_step, reaped の死後相も含む)。
②Taka逐語(原文): 「m31 で出した全 cosine をそのまま可視化するだけ」「濃度・spike・Δ・分布・閾値・集中度
  などの計算は一切しない(色/線/棒に載せるのは生の cosine のみ)」「CIDを選出してしまうとおもろくない、
  選べるように」「だいたい5ノード系が多様性ある」「Ghost 区間を見分けられるように(伏せない)」.
③判定はTaka(success/fail置かない) ④集約語なし.

## 範囲: n_core=5(seed0) の CID を引数で選び、生 cosine を A:ヒートマップ B:重ね折れ線
  C:立ち方プロファイル(t スライダ) で描く。Ghost 区間を網掛け。計算(濃度/spike/Δ/閾値)は一切なし。
## 一方向: 読=frozen(full_cosine/source_events), 書=cosine_viz/ のみ. physics 非書込.
usage: python m33_cosine_viz.py [cid ...]   (無引数ならサンプル set)
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
import plotly.graph_objects as go
from plotly.subplots import make_subplots

REPO = Path('/home/takasan/esde/ESDE-Research')
FC = REPO / 'unified/v12_atomset/full_cosine_probe/full_cosine_step10_seed0.parquet'
SE = REPO / 'developmental/v107/outputs/main/source_events_seed0.parquet'
OUT = REPO / 'unified/v12_atomset/cosine_viz'
OUT.mkdir(parents=True, exist_ok=True)
SAMPLE = [0, 42, 26, 107, 178]   # 26 は reaped(Ghost相在), 他 hosted

_fc = pd.read_parquet(FC)
ATOMS = [c for c in _fc.columns if c not in ('cid', 't')]
_se = pd.read_parquet(SE)
_death = _se.groupby('source_cid').agg(n_core=('n_core_member', 'max'),
                                       host_lost=('host_lost_step', 'first'),
                                       final=('final_state', 'first')).reset_index()


def n5_list():
    g = _se.groupby('source_cid').agg(n_core=('n_core_member', 'max'), birth=('birth_step', 'first'),
                                      host_lost=('host_lost_step', 'first'), reaped=('reaped_step', 'first'),
                                      final=('final_state', 'first'), n_events=('event_id', 'size')).reset_index()
    g['lifespan'] = g.apply(lambda r: (r.host_lost if pd.notna(r.host_lost) else
                                       (r.reaped if pd.notna(r.reaped) else 25000)) - r.birth, axis=1)
    n5 = g[g.n_core == 5].sort_values('lifespan', ascending=False)
    n5[['source_cid', 'n_core', 'lifespan', 'n_events', 'final']].to_csv(OUT / 'n_core5_cid_list.csv', index=False)
    return n5


def ghost_t(cid):
    r = _death[_death.source_cid == cid]
    hl = r['host_lost'].iloc[0] if len(r) else np.nan
    return hl   # host_lost_step (= alive→ghost 境界), nan なら ghost 区間なし


def viz_cid(cid):
    d = _fc[_fc.cid == cid].sort_values('t').reset_index(drop=True)
    if d.empty:
        print(f'  cid {cid}: full_cosine に無し'); return None
    ts = d['t'].values
    M = d[ATOMS].values.astype(np.float32)          # (T, 325) 生 cosine
    hl = ghost_t(cid)
    has_ghost = pd.notna(hl) and (ts >= hl).any()
    # 表示用 atom 選択 (生 cosine の最大で並べる=表示の選択, 新指標でない)
    amax = M.max(axis=0)
    order = np.argsort(-amax)
    top_subset = order[:40]                          # ヒートB用 (上位40 atom)
    top_lines = order[:10]                           # 折れ線用 (上位10)

    fig = make_subplots(rows=4, cols=1, row_heights=[0.28, 0.22, 0.22, 0.28],
                        subplot_titles=(
                            f'A1. ヒートマップ 全325 atom (縦=atom, 横=t, 色=生cosine) — cid {cid}',
                            'A2. ヒートマップ 上位40 atom (潰れ対策, 値は生のまま)',
                            'B. 重ね折れ線 上位10 atom (生cosine, いつ立ち上がり/沈み/入替)',
                            'C. 立ち方プロファイル (選んだ t で325 atom を cosine 値順, スライダ)'),
                        vertical_spacing=0.07)
    # A1 全325
    fig.add_trace(go.Heatmap(z=M.T, x=ts, y=list(range(len(ATOMS))), colorscale='Viridis',
                             colorbar=dict(title='cosine', len=0.22, y=0.9), zmin=0, zmax=float(M.max())), row=1, col=1)
    # A2 上位40 (atom 名で)
    fig.add_trace(go.Heatmap(z=M[:, top_subset].T, x=ts, y=[ATOMS[j] for j in top_subset],
                             colorscale='Viridis', showscale=False, zmin=0, zmax=float(M.max())), row=2, col=1)
    # B 折れ線
    for j in top_lines:
        fig.add_trace(go.Scatter(x=ts, y=M[:, j], mode='lines', name=ATOMS[j],
                                 line=dict(width=1)), row=3, col=1)
    # C プロファイル (スライダ) — 等間隔 + ghost 区間の t も含めて数コマ
    snap_idx = np.linspace(0, len(ts) - 1, min(12, len(ts))).astype(int)
    base = len(fig.data)
    for k, si in enumerate(snap_idx):
        row = M[si]
        o = np.argsort(-row)
        fig.add_trace(go.Bar(x=[ATOMS[j] for j in o], y=row[o], visible=(k == 0),
                             marker_color='steelblue', name=f't={ts[si]}',
                             hovertext=[ATOMS[j] for j in o]), row=4, col=1)
    steps = []
    for k, si in enumerate(snap_idx):
        vis = [True] * base + [kk == k for kk in range(len(snap_idx))]
        gtag = ' [Ghost]' if (has_ghost and ts[si] >= hl) else ''
        steps.append(dict(method='update', label=f't={ts[si]}{gtag}',
                          args=[{'visible': vis}]))
    fig.update_layout(sliders=[dict(active=0, currentvalue={'prefix': 'C profile @ '},
                                    steps=steps, y=-0.02, len=0.9)],
                      height=1500, width=1200, showlegend=True,
                      legend=dict(y=0.5, font=dict(size=8)),
                      title=f'cid {cid} (n_core=5, final={_death[_death.source_cid==cid].final.iloc[0]}, '
                            f'{"Ghost相在(host_lost="+str(int(hl))+")" if has_ghost else "Ghost相なし(hosted)"}) '
                            f'— 生 cosine のみ, 計算なし')
    # Ghost 網掛け (host_lost 以降) + 遷移マーカー: A1/A2/B の x 範囲に vrect/vline
    if has_ghost:
        for r in (1, 2, 3):
            fig.add_vrect(x0=float(hl), x1=float(ts.max()), fillcolor='red', opacity=0.12,
                          line_width=0, row=r, col=1,
                          annotation_text='Ghost' if r == 1 else None, annotation_position='top left')
            fig.add_vline(x=float(hl), line=dict(color='red', dash='dash', width=1), row=r, col=1)
    p = OUT / f'cosine_viz_cid{cid}.html'
    fig.write_html(str(p))
    return p, has_ghost


def main():
    n5 = n5_list()
    print(f'n_core=5 CID: {len(n5)} 個 (seed0), 一覧 → n_core5_cid_list.csv')
    cids = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else SAMPLE
    made = []
    for cid in cids:
        if cid not in set(n5.source_cid):
            print(f'  cid {cid}: n_core=5 でない (スキップ可、描画は試行)')
        r = viz_cid(cid)
        if r:
            p, hg = r
            print(f'  cid {cid}: {p.name} (Ghost相={"在" if hg else "なし"})')
            made.append((cid, p.name, hg))
    # index
    rows = ''.join(f'<li><a href="{n}">cid {c}</a> {"[Ghost相在]" if hg else "[hosted]"}</li>' for c, n, hg in made)
    listrows = n5[['source_cid', 'lifespan', 'n_events', 'final']].to_html(index=False)
    (OUT / 'index.html').write_text(
        f'<h2>課題#1 cosine 可視化 (n_core=5, seed0, 生cosine のみ)</h2>'
        f'<p>引数で任意の cid を選べる: python m33_cosine_viz.py &lt;cid&gt;</p>'
        f'<h3>描画済</h3><ul>{rows}</ul><h3>n_core=5 CID 一覧</h3>{listrows}')
    print(f'  index → cosine_viz/index.html')


if __name__ == '__main__':
    main()
