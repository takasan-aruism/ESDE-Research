#!/usr/bin/env python3
"""v1302 (B) structural-field 抽出前処理 — 親(seed0) persistence から CID のコア+周辺 structural field(配線)を復元。

【観察対象注釈ブロック / 同系・異系宣言】
- 同系内: 親 seed0 CID 縮小子系の (B) 移植元を作る。異系対応でない。
- 読=frozen: per_subject_seed0 / persistence(label_member_persistence, link_snapshot_log) / per_label。親 read-only。
- 書=unified/v1302/ のみ(field キャッシュ parquet)。親 physics/inject/ledger/state 非書込。実験 child run を含まない(前処理)。
- shape-only: 復元するのは node 対の配線(topology)のみ。S/E は frozen に無く移植時 fresh(genesis canon inject 値)で埋める。
- window 選択: birth_window の snapshot(link_snapshot_log は window20-69 のみゆえ <20 は 20 にクランプ)。誕生時 field は多くが acyclic(R は run 中に発達)=報告で明示。
"""
import re
from collections import defaultdict
from pathlib import Path
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
PAR = REPO / 'primitive/v918/diag_v918_main'


def _parse(lid):
    a, b = re.findall(r'\d+', str(lid))
    return (int(a), int(b))


def build_fields(strata=('2', '5')):
    """{cid: dict(n_core, stratum, field_nodes(list), field_links(list[(i,j)]), n_core_links, has_cycle)} を返す。"""
    lmp = pd.read_csv(PAR / 'persistence/label_member_persistence_seed0.csv')
    lsl = pd.read_csv(PAR / 'persistence/link_snapshot_log_seed0.csv')
    plab = pd.read_csv(PAR / 'labels/per_label_seed0.csv')
    sub = pd.read_csv(PAR / 'subjects/per_subject_seed0.csv')
    sub['cognitive_id'] = pd.to_numeric(sub['cognitive_id'], errors='coerce')
    wmin, wmax = int(lsl.window.min()), int(lsl.window.max())

    # window -> adjacency(set of (i,j))
    snap = defaultdict(set)
    for w, lid in zip(lsl.window, lsl.link_id):
        snap[int(w)].add(_parse(lid))

    bw_map = dict(zip(plab.label_id, plab.birth_window))
    core_links_map = defaultdict(list)
    for lid, link in zip(lmp.label_id, lmp.link_id):
        core_links_map[int(lid)].append(_parse(link))

    out = {}
    for nc in strata:
        n_core = int(nc)
        max_hops = n_core + 1  # 確定: 閉路が CID 境界をまたぐため1段広げる
        cids = [int(c) for c in sub[sub.v11_m_c_n_core == nc].cognitive_id.dropna()]
        for cid in cids:
            if cid not in core_links_map:
                continue  # persistence にコアリンク無し→(B)不可、intersection から除外
            core_links = core_links_map[cid]
            core = set(n for e in core_links for n in e)
            w = min(max(int(bw_map.get(cid, wmin)), wmin), wmax)
            adj = defaultdict(set)
            for (i, j) in snap.get(w, set()):
                adj[i].add(j); adj[j].add(i)
            visited = set(core); frontier = set(core)
            for _ in range(max_hops):
                nf = set()
                for n in frontier:
                    for nb in adj.get(n, set()):
                        if nb not in visited:
                            visited.add(nb); nf.add(nb)
                frontier = nf
                if not nf:
                    break
            flinks = [(i, j) for (i, j) in snap.get(w, set()) if i in visited and j in visited]
            has_cycle = len(flinks) >= len(visited) and len(visited) > 0
            out[cid] = dict(n_core=n_core, stratum=nc, field_nodes=sorted(visited),
                            field_links=flinks, n_core_links=len(core_links),
                            snap_window=w, has_cycle=has_cycle)
    return out


if __name__ == '__main__':
    f = build_fields(('2', '5'))
    rows = []
    for cid, d in f.items():
        rows.append(dict(cid=cid, stratum=d['stratum'], n_core=d['n_core'], snap_window=d['snap_window'],
                         n_core_links=d['n_core_links'], field_nodes=len(d['field_nodes']),
                         field_links=len(d['field_links']), has_cycle=d['has_cycle']))
    df = pd.DataFrame(rows)
    out = REPO / 'unified/v1302/cw_v1302_field_validation.parquet'
    df.to_parquet(out, index=False)
    print(f'=== structural-field 抽出検証 ({len(df)} CID) ===')
    for nc in ['2', '5']:
        s = df[df.stratum == nc]
        print(f'  n{nc}: CID={len(s)} field_nodes med={int(s.field_nodes.median())} '
              f'(min{int(s.field_nodes.min())}/max{int(s.field_nodes.max())}) '
              f'field_links med={int(s.field_links.median())} 閉路有={int(s.has_cycle.sum())}/{len(s)}')
    print(f'保存: {out}')
