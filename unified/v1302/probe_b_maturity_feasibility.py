#!/usr/bin/env python3
"""v1302 (B) 成熟期移植 feasibility — read-only。成熟 window(age_r≥τ link 閉路数最大)がログ範囲に在るか・has_cycle が誕生時 tree から立つか。

【観察対象注釈ブロック / 同系・異系宣言】
- 同系内: 親 seed0 CID 縮小子系の (B) 移植元(成熟期)を検討。異系対応でない。
- 読=frozen: persistence(label_member_persistence, link_snapshot_log[window,link_id,age_r_current], per_label) / per_subject。親 read-only。
- 書=unified/v1302/(本 feasibility md・stdout)。child run なし(前処理点検)。親 physics/inject/ledger/state 非書込。
- 成熟 window 選択は全 CID 一律規則(age_r≥τ link の閉路ランク最大 window)=ESDE 自己判定、観察者が個別に選ばない(神の手回避)。τ は候補 10/50/100 を並列計算(label 誕生 τ の確定は実装前に要確認)。
"""
import re
from collections import defaultdict
from pathlib import Path
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
PAR = REPO / 'primitive/v918/diag_v918_main'
STRATA = ['2', '4', '5']
TAUS = [10, 50, 100]


def parse(lid):
    a, b = re.findall(r'\d+', str(lid))
    return (int(a), int(b))


def find(uf, x):
    while uf[x] != x:
        uf[x] = uf[uf[x]]; x = uf[x]
    return x


def cycle_rank(nodes, links):
    """E - V + C (独立閉路数)。"""
    if not links:
        return 0
    V = set(nodes); uf = {v: v for v in V}
    E = 0
    for (i, j) in links:
        if i in uf and j in uf:
            E += 1
            ri, rj = find(uf, i), find(uf, j)
            if ri != rj:
                uf[ri] = rj
    C = len(set(find(uf, v) for v in V))
    return E - len(V) + C


def main():
    lmp = pd.read_csv(PAR / 'persistence/label_member_persistence_seed0.csv')
    lsl = pd.read_csv(PAR / 'persistence/link_snapshot_log_seed0.csv')
    plab = pd.read_csv(PAR / 'labels/per_label_seed0.csv')
    sub = pd.read_csv(PAR / 'subjects/per_subject_seed0.csv')
    sub['cognitive_id'] = pd.to_numeric(sub['cognitive_id'], errors='coerce')
    wmin, wmax = int(lsl.window.min()), int(lsl.window.max())

    # window -> list of (i,j,age_r)
    snap = defaultdict(list)
    for w, lid, ar in zip(lsl.window, lsl.link_id, lsl.age_r_current):
        snap[int(w)].append((*parse(lid), float(ar)))

    bw_map = dict(zip(plab.label_id, plab.birth_window))
    core_map = defaultdict(list)
    for lid, link in zip(lmp.label_id, lmp.link_id):
        core_map[int(lid)].append(parse(link))

    def field_at(cid, n_core, w, tau=None):
        """window w での field(core から BFS max_hops n_core+1)。tau 指定時は age_r>=tau link のみで判定。"""
        core_links = core_map[cid]
        core = set(n for e in core_links for n in e)
        edges = [(i, j, ar) for (i, j, ar) in snap.get(w, [])]
        if tau is not None:
            edges = [(i, j, ar) for (i, j, ar) in edges if ar >= tau]
        adj = defaultdict(set)
        for (i, j, ar) in edges:
            adj[i].add(j); adj[j].add(i)
        visited = set(core); frontier = set(core)
        for _ in range(n_core + 1):
            nf = set()
            for n in frontier:
                for nb in adj.get(n, set()):
                    if nb not in visited:
                        visited.add(nb); nf.add(nb)
            frontier = nf
            if not nf:
                break
        flinks = [(i, j) for (i, j, ar) in edges if i in visited and j in visited]
        return visited, flinks

    rows = []
    for nc in STRATA:
        n_core = int(nc)
        cids = [int(c) for c in sub[sub.v11_m_c_n_core == nc].cognitive_id.dropna() if int(c) in core_map]
        for cid in cids:
            bw = min(max(int(bw_map.get(cid, wmin)), wmin), wmax)
            # 誕生時(全 link) has_cycle
            bn, bl = field_at(cid, n_core, bw, tau=None)
            birth_rank = cycle_rank(bn, bl)
            rec = dict(cid=cid, stratum=nc, n_core=n_core, birth_window=bw,
                       birth_field_nodes=len(bn), birth_rank=birth_rank)
            for tau in TAUS:
                # 全 window で age_r>=tau link の閉路ランク最大を探す(一律規則)
                best_w, best_mrank = None, -1
                for w in range(wmin, wmax + 1):
                    mn, ml = field_at(cid, n_core, w, tau=tau)
                    mr = cycle_rank(mn, ml)
                    if mr > best_mrank:
                        best_mrank, best_w = mr, w
                # 成熟 window での「全 link」field has_cycle(移植する field の閉路)
                fn, fl = field_at(cid, n_core, best_w, tau=None) if best_w is not None else (set(), [])
                rec[f'mat_w_tau{tau}'] = best_w
                rec[f'mat_mrank_tau{tau}'] = best_mrank          # 成熟 link の閉路ランク
                rec[f'mat_full_rank_tau{tau}'] = cycle_rank(fn, fl)  # 移植 field(全link)の閉路ランク
                rec[f'mat_field_nodes_tau{tau}'] = len(fn)
            rows.append(rec)

    df = pd.DataFrame(rows)
    df.to_parquet(REPO / 'unified/v1302/cw_v1302_B_maturity_feasibility.parquet', index=False)
    print(f'=== (B) 成熟期 feasibility (CID={len(df)}, window 範囲 {wmin}-{wmax}) ===')
    print('age_r は link_snapshot_log.age_r_current に直接在り(復元不要)。')
    for nc in STRATA:
        s = df[df.stratum == nc]
        print(f'\n--- n{nc} (CID={len(s)}) 誕生時 has_cycle={int((s.birth_rank>0).sum())}/{len(s)} ---')
        for tau in TAUS:
            mw = s[f'mat_w_tau{tau}']
            mat_has = (s[f'mat_mrank_tau{tau}'] > 0)        # age_r>=tau link が閉路を成す CID
            full_has = (s[f'mat_full_rank_tau{tau}'] > 0)   # 移植 field(全link)に閉路
            in_range = mw.notna().mean()
            # 成熟 window が範囲端(69)に張り付く割合=真のピークが範囲外の疑い
            at_edge = (mw == wmax).mean()
            print(f'  τ={tau:>3}: age_r≥τ閉路ありCID={int(mat_has.sum())}/{len(s)} '
                  f'| 移植field has_cycle={int(full_has.sum())}/{len(s)} '
                  f'| 成熟w中央値={int(mw.median()) if mw.notna().any() else "-"} '
                  f'| w==69張付={at_edge:.0%}')


if __name__ == '__main__':
    main()
