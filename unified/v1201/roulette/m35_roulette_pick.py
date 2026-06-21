#!/usr/bin/env python3
"""課題#1 — cosine 分布の確率的選択 (連続ルーレット・レア消さない・全CID×全時点・記録のみ)

## 自己規律 (Code A)
①過去引用: m31(full_cosine_step10_seed0 = argmax 前の全325 cosine, 既存値を読むだけ)、m30(sim=cosine(CID48,
  atom48) の argmax のみ出力で残り325-1は捨てている)、#30(気まぐれ指標禁止・レアを消すな・Ghost分離)、
  m27/m33(is_ghost = t>=host_lost_step, source_events groupby 'first', reaped の死後相も含む)、
  m34(n_core=5 seed0 = 21 CID, n_core5_cid_list.csv)。
②Taka逐語(原文): 「cosine 分布を確率的選択という別の表現にしたとき何が見えるか」「意味づけは足さない、選ばれた
  atom を記録するだけ」「負・極小を0クリップ→合計1正規化(確率=cosine/合計)→0〜1一様乱数1つで累積確率ルーレット」
  「整数の桁合わせはしない=連続」「上位は当たりやすく下位は天文学的に低いがゼロにしない(レアを消すのは雑)」
  「各(cid,t)で1回だけ引く」「seed0 n_core=5 の全21CID, 各CIDの全step10時点(hosted/reaped両方, 寿命問わず全部)」
  「seed固定(再現可能, コード冒頭に明示)」「Ghost区間も引くがフラグで分離」「picked_atom と rank_of_picked を
  記録、引かれた atom の素の頻度表 + rank_of_picked の素の分布を dump」.
③成否判定はTaka(success/fail置かない, 観察事実のみ) ④集約語なし.

## やること: 各(cid,t)で全325cosineを確率比例(連続)で1回ルーレット選択。picked_atom と rank_of_picked を記録。
##   付帯=picked頻度表 + rank分布の素の dump(集計であって指標化でない)。
## やらないこと: 「意味あるレア」の判定/閾値、spike/Δ/濃度/エントロピー/集中度/目立ち度の数値化、
##   atom×atom網/CID投影/センター接続/effect_size/位相化/複数CID目立ちの合成、「こういう意味」の解釈 — 一切しない。
## 一方向: 読=frozen(full_cosine_step10_seed0 / source_events), 書=roulette/ のみ. physics/inject/ledger 非書込.
usage: python m35_roulette_pick.py
"""
import sys, time, json
from pathlib import Path
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# ===== 乱数 seed (固定・再現可能・コード冒頭に明示) =====
SEED = 0   # 各(cid,t)の draw = np.random.default_rng([SEED, cid, t]).random() の純関数。
           #  → 同じ config を何度回しても同一(Web Claude が検証可)。
           #  → 後で n_core を広げ別CIDが増えても、既存(cid,t)の draw は不変(順序非依存)。

REPO = Path('/home/takasan/esde/ESDE-Research')
FC = REPO / 'unified/v1201/full_cosine_probe/full_cosine_step10_seed0.parquet'  # m31 生成(非commit)
SE = REPO / 'developmental/v107/outputs/main/source_events_seed0.parquet'             # 生死(host_lost)
OUT = REPO / 'unified/v1201/roulette'
OUT.mkdir(parents=True, exist_ok=True)


def main():
    t0 = time.time()
    if not FC.exists():
        sys.exit(f'[STOP] {FC} が無い。先に full_cosine_probe/m31_full_cosine_probe.py を実行して再生成 (~3.5s)。')

    # --- 読む: 全325 atom cosine (m31 既存値, 新規計算しない) ---
    fc = pd.read_parquet(FC)
    atoms = [c for c in fc.columns if c not in ('cid', 't')]   # 325 valid atom 名
    A = np.array(atoms)

    # --- 母集団: n_core=5 (seed0) の 21 CID を source_events から導出 (m33 n5_list と同じ groupby) ---
    se = pd.read_parquet(SE)
    g = se.groupby('source_cid').agg(n_core=('n_core_member', 'max'),
                                     host_lost=('host_lost_step', 'first')).reset_index()
    n5 = g[g.n_core == 5]
    cids = sorted(int(c) for c in n5.source_cid)
    host_lost = {int(r.source_cid): (float(r.host_lost) if pd.notna(r.host_lost) else np.nan)
                 for _, r in n5.iterrows()}

    # --- 各CIDの全step10時点を取り、行順を (cid,t) で固定 ---
    d = fc[fc.cid.isin(cids)].sort_values(['cid', 't']).reset_index(drop=True)
    R = len(d)
    cid_arr = d['cid'].values.astype(int)
    t_arr = d['t'].values.astype(int)
    M = d[atoms].values.astype(np.float64)        # (R, 325) 生 cosine

    # --- Ghost フラグ: is_ghost = t >= host_lost_step (m27/m33 定義. hosted=host_lost NaN → 常に False) ---
    hl_arr = np.array([host_lost[c] for c in cid_arr])
    is_ghost = np.where(np.isnan(hl_arr), False, t_arr >= hl_arr)

    # --- 確率化 (roulette の最低限の前処理) ---
    #  負(極小)→0 クリップ。正の下位は一切残す(=レアを消さない, 正値に閾値かけない)。
    Mc = np.maximum(M, 0.0)
    rowsum = Mc.sum(axis=1)
    zero_rows = int((rowsum == 0).sum())          # 全atom非正の行(実物では 0 のはず)
    safe = rowsum.copy(); safe[safe == 0] = 1.0
    P = Mc / safe[:, None]                          # (R,325) 確率 = clip(cosine)/合計, 連続(桁合わせなし)
    if zero_rows:
        P[rowsum == 0] = 1.0 / len(atoms)           # 退避(全非正なら一様): 実発生時のみ
    C = np.cumsum(P, axis=1)
    C[:, -1] = 1.0                                  # float端数で u≈1 が外れぬよう末尾を1に固定

    # --- 連続ルーレット: 各(cid,t)で u~U[0,1) を1つ, 累積確率で当たり atom (seed=(SEED,cid,t)) ---
    picked = np.empty(R, dtype=np.int64)
    u_all = np.empty(R, dtype=np.float64)
    for r in range(R):
        u = float(np.random.default_rng([SEED, int(cid_arr[r]), int(t_arr[r])]).random())
        u_all[r] = u
        picked[r] = np.searchsorted(C[r], u, side='right')
    picked = np.clip(picked, 0, len(atoms) - 1)

    picked_cos = M[np.arange(R), picked]            # 生 cosine(引かれた atom)
    picked_prob = P[np.arange(R), picked]           # 正規化後の確率
    # rank_of_picked = cosine 降順で何位か(1始まり, 厳密に上の atom 数 +1)。記録であって閾値判定でない。
    rank_of_picked = (M > picked_cos[:, None]).sum(axis=1) + 1

    # --- 出力(記録のみ) ---
    out = pd.DataFrame({
        'cid': cid_arr, 't': t_arr, 'is_ghost': is_ghost,
        'picked_atom': A[picked],
        'picked_atom_cosine': picked_cos.astype(np.float32),
        'picked_atom_prob': picked_prob.astype(np.float32),
        'rank_of_picked': rank_of_picked.astype(np.int32),
    })
    pick_path = OUT / 'roulette_picks_step10_seed0.parquet'
    out.to_parquet(pick_path, index=False)

    # --- 付帯 dump (集計のみ, 指標化しない) ---
    freq = out['picked_atom'].value_counts().rename_axis('atom').reset_index(name='picked_count')
    freq.to_csv(OUT / 'picked_atom_freq.csv', index=False)                        # 何回引かれたか(素)
    rdist = out['rank_of_picked'].value_counts().sort_index().rename_axis('rank').reset_index(name='count')
    rdist.to_csv(OUT / 'rank_of_picked_dist.csv', index=False)                    # rank の素の分布
    # alive / ghost を分けて置く (#30 分離。判定はせず, ただ分ける)
    out[~out.is_ghost]['rank_of_picked'].value_counts().sort_index().rename_axis('rank')\
        .reset_index(name='count').to_csv(OUT / 'rank_of_picked_dist_alive.csv', index=False)
    out[out.is_ghost]['rank_of_picked'].value_counts().sort_index().rename_axis('rank')\
        .reset_index(name='count').to_csv(OUT / 'rank_of_picked_dist_ghost.csv', index=False)

    # --- 人間可読サンプル(記録の実物。判定しない): rank が最大=最も下位が顔を出した picks を数行 ---
    rare = out.sort_values('rank_of_picked', ascending=False).head(10)
    sample = [{'cid': int(x.cid), 't': int(x.t), 'is_ghost': bool(x.is_ghost),
               'picked_atom': x.picked_atom, 'cosine': round(float(x.picked_atom_cosine), 4),
               'prob': round(float(x.picked_atom_prob), 6), 'rank_of_picked': int(x.rank_of_picked)}
              for x in rare.itertuples()]
    (OUT / 'sample_rare_picks.json').write_text(json.dumps(sample, indent=2, ensure_ascii=False))

    # --- コスト + 拡張概算 ---
    pick_size = pick_path.stat().st_size / 1e6
    total_s = time.time() - t0
    full_rows_step10 = int(len(fc))                # 全 n_core (step10 seed0) の行数
    n_ghost = int(is_ghost.sum())
    cost = {
        'seed_scheme': f'np.random.default_rng([{SEED}, cid, t]).random() per (cid,t)',
        'grain': 'step10', 'data_seed': 0,
        'n_cids_ncore5': len(cids), 'n_rows_drawn': int(R),
        'n_rows_alive': int(R - n_ghost), 'n_rows_ghost': n_ghost,
        'n_atoms': len(atoms), 'zero_prob_rows': zero_rows,
        'total_s': round(total_s, 2), 'picks_parquet_MB': round(pick_size, 3),
        'full_rows_step10_all_ncore': full_rows_step10,
        'est_all_ncore_step10_1seed_rows': full_rows_step10,
        'est_all_ncore_4grain_24seed_rows_approx': full_rows_step10 * 24,  # 粗(粒度で行数違う), m31/m32 と同方針
    }
    (OUT / 'cost.json').write_text(json.dumps(cost, indent=2, ensure_ascii=False))

    # --- print ---
    print('=== 課題#1 連続ルーレット選択 (step10 seed0, n_core=5 の 21CID, 記録のみ) ===')
    print(f'  母集団: {len(cids)} CID (n_core=5), 引いた (cid,t): {R} 行 (alive {R-n_ghost} / ghost {n_ghost})')
    print(f'  seed: np.random.default_rng([{SEED}, cid, t]) per row (固定・再現可能・順序非依存)')
    print(f'  確率化: max(cosine,0) → /合計 (正の下位は残す=レア消さない). zero-prob 行: {zero_rows}')
    print(f'  cost: {total_s:.2f}s, picks parquet {pick_size:.3f} MB')
    print(f'  picked_atom ユニーク: {out.picked_atom.nunique()} / {len(atoms)} atom')
    print(f'  rank_of_picked: min {int(out.rank_of_picked.min())} / median {int(out.rank_of_picked.median())} / '
          f'mean {out.rank_of_picked.mean():.1f} / max {int(out.rank_of_picked.max())}')
    print('  --- picked 頻度 上位8 (素のカウント) ---')
    for rr in freq.head(8).itertuples():
        print(f'      {rr.atom}: {rr.picked_count}')
    print('  --- rank_of_picked 素の分布 (頭8) ---')
    for rr in rdist.head(8).itertuples():
        print(f'      rank {rr.rank}: {rr.count}')
    print('  --- 最も下位が顔を出した picks (rank 最大 上位5, 記録の実物) ---')
    for s in sample[:5]:
        gt = ' [Ghost]' if s['is_ghost'] else ''
        print(f"      cid {s['cid']} t {s['t']}{gt}: {s['picked_atom']} (cosine {s['cosine']}, "
              f"prob {s['prob']}, rank {s['rank_of_picked']})")
    print(f'  out: {pick_path.relative_to(REPO)} + picked_atom_freq.csv + rank_of_picked_dist(_alive/_ghost).csv + cost.json')


if __name__ == '__main__':
    main()
