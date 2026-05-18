#!/usr/bin/env python3
"""v1101a 段階 2 Step C — 観察 A/B/C 算出

設計書 §2.2-2.4 + 認識確認 §3:
- 観察 A: 注意候補数の収束/発散 (qc_regime cog→csc 切替 t0 前後の
  attention_candidate_id ユニーク数推移)
- 観察 B: 波及先 cid 集合の隣接時点 Jaccard (構造単位別並列、留保 #L4 整合)
- 観察 C: 注意候補の予測可能性 (実測 vs (i) 完全 shuffle baseline per-seed
  × 100 回 permutation、100% 未満確認は観察事実として必ず記録)

入力: 段階 1 attention_emit_*.parquet + attention_propagation_*.parquet
書き込み: unified/v1101a/outputs/{smoke,main}/ 配下のみ
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1101A_ROOT = REPO_ROOT / 'unified/v1101a'
OUT_MAIN = V1101A_ROOT / 'outputs/main'
OUT_SMOKE = V1101A_ROOT / 'outputs/smoke'

N_SHUFFLE = 100  # 完全 shuffle baseline、per-seed × scope × metric_type で 100 回
SHUFFLE_RNG_SEED = 42  # 神の手回避 #9: 固定 seed で再現性確保


# ───────────────────────────────────────────────────────────────────
# 観察 A — 注意候補数の収束/発散
# ───────────────────────────────────────────────────────────────────
def observation_a(emit: pd.DataFrame) -> pd.DataFrame:
    """qc_regime cog→csc 切替 t0 前後で attention_candidate_id ユニーク数推移
    per (seed, change_scope, change_metric_type) で全 cid 集計。"""
    rows = []
    for (seed, scope, mt), sub in emit.groupby(['seed', 'change_scope', 'change_metric_type']):
        sub = sub.sort_values(['scope_id', 'window']).reset_index(drop=True)
        # per scope_id で cog→csc 切替点を特定し、t0 前後の attention_candidate_id を集計
        for sid, ssub in sub.groupby('scope_id'):
            ssub = ssub.sort_values('window').reset_index(drop=True)
            # cog→csc transition の窓を探す
            regimes = ssub['qc_regime'].tolist()
            for i in range(1, len(regimes)):
                if regimes[i-1] == 'cognitive_dominant' and regimes[i] == 'conscious_dominant':
                    t0 = int(ssub.iloc[i]['window'])
                    # t0 以後の最初 5 window で attention_candidate_id のユニーク集合
                    csc_window = ssub[(ssub['window'] >= t0) & (ssub['window'] <= t0 + 4)]
                    csc_unique = csc_window['attention_candidate_id'].dropna().astype(int).nunique()
                    # t0 直前 5 window (cog)
                    cog_window = ssub[(ssub['window'] < t0) & (ssub['window'] >= t0 - 5)]
                    cog_unique = cog_window['attention_candidate_id'].dropna().astype(int).nunique()
                    rows.append({
                        'seed': seed, 'change_scope': scope, 'change_metric_type': mt,
                        'scope_id': sid, 't0_window': t0,
                        'n_unique_cog_pre_5w': cog_unique, 'n_unique_csc_post_5w': csc_unique,
                        'delta_unique': csc_unique - cog_unique,
                    })
                    break  # 各 scope_id で最初の cog→csc 切替のみ
    return pd.DataFrame(rows)


# ───────────────────────────────────────────────────────────────────
# 観察 B — 波及先 cid 集合の隣接時点 Jaccard
# ───────────────────────────────────────────────────────────────────
def observation_b(emit: pd.DataFrame, propag: pd.DataFrame) -> pd.DataFrame:
    """attention_propagation の (window, attention_candidate_id) ごとに
    その中心 atom と一致した周辺 cid 集合を取り、隣接 window の Jaccard を算出。
    ここでは center_atom_t0 を基盤として、cid_state_ledger 由来でなく
    段階 1 propagation 出力 (n_peripheral_cids_alive, influence_candidate_count)
    と段階 1 v10.6 window_trajectory との結合で観察を行う。
    実装簡略化: 隣接 window で qc_regime 同じかつ attention_candidate_id が
    同 cid のレコードの influence_candidate_count から「波及先集合」を概算する。
    """
    # 段階 1 で center_atom_t0 が同じ (window, scope_id, metric_type) 同士の
    # influence_candidate_count を時間方向に比較するのが Jaccard の代替。
    # 厳密 Jaccard は段階 1 出力にない (波及先 cid id 集合は raw 保存していない)、
    # よって観察 B は「中心 atom_t0 の時間方向の重なり度合い」を代替指標として記録。
    rows = []
    for (seed, scope, mt, regime), sub in propag.groupby(
        ['seed', 'change_scope', 'change_metric_type', 'qc_regime']
    ):
        sub = sub.sort_values(['scope_id', 'window']).reset_index(drop=True)
        # per scope_id で隣接 window 間で center_atom_t0 一致を Jaccard 代替指標とする
        for sid, ssub in sub.groupby('scope_id'):
            ssub = ssub.sort_values('window').reset_index(drop=True)
            if len(ssub) < 2:
                continue
            atoms = ssub['center_atom_t0'].tolist()
            n_same = sum(1 for i in range(1, len(atoms))
                         if atoms[i] is not None and atoms[i] == atoms[i-1])
            n_diff = sum(1 for i in range(1, len(atoms))
                         if atoms[i] is not None and atoms[i-1] is not None and atoms[i] != atoms[i-1])
            n_pairs = n_same + n_diff
            if n_pairs > 0:
                rows.append({
                    'seed': seed, 'change_scope': scope, 'change_metric_type': mt,
                    'qc_regime': regime, 'scope_id': sid,
                    'n_window_pairs': n_pairs,
                    'n_same_center_atom': n_same,
                    'jaccard_proxy_frac': n_same / n_pairs,
                })
    return pd.DataFrame(rows)


# ───────────────────────────────────────────────────────────────────
# 観察 C — 注意候補の予測可能性 (shuffle baseline 比較)
# ───────────────────────────────────────────────────────────────────
def observation_c(emit: pd.DataFrame, n_shuffle: int = N_SHUFFLE,
                   rng_seed: int = SHUFFLE_RNG_SEED) -> pd.DataFrame:
    """
    予測可能性の定義:
        per (seed, scope, mt, qc_regime=conscious_dominant) で
        t → t+1 遷移について、t+1 の attention_candidate が
        t の predecessor_attention_ref (箱 1) と一致するか。
        一致率 = 実測予測可能性。
    Shuffle baseline:
        同 seed・scope・mt 内で attention_candidate_id を完全 permutation し
        同様の一致率を 100 回算出した平均。
    100% 未満であることの確認も観察事実として記録 (Aruism 対称性、箱 3)。
    """
    rng = np.random.default_rng(rng_seed)
    rows = []
    csc = emit[emit['qc_regime'] == 'conscious_dominant'].copy()
    csc = csc[csc['predecessor_attention_ref'].notna()].copy()
    csc['predecessor_attention_ref'] = csc['predecessor_attention_ref'].astype(int)
    csc['attention_candidate_id'] = csc['attention_candidate_id'].astype(int)

    for (seed, scope, mt), sub in csc.groupby(['seed', 'change_scope', 'change_metric_type']):
        sub = sub.sort_values(['scope_id', 'window']).reset_index(drop=True)
        # 実測: predecessor が現候補と一致する割合 = 「直前の認知固定への参照が
        # 同じ cid に向かう」の頻度。これが基本ベースラインを予測可能性として測る
        n_total = len(sub)
        if n_total == 0:
            continue
        actual_match = (sub['attention_candidate_id'] == sub['predecessor_attention_ref']).sum()
        actual_rate = actual_match / n_total
        # Shuffle baseline: attention_candidate_id 列を permutation
        cand_ids = sub['attention_candidate_id'].to_numpy()
        pred_ids = sub['predecessor_attention_ref'].to_numpy()
        baseline_rates = []
        for _ in range(n_shuffle):
            shuffled = rng.permutation(cand_ids)
            baseline_rates.append((shuffled == pred_ids).mean())
        baseline_mean = float(np.mean(baseline_rates))
        baseline_std = float(np.std(baseline_rates))
        # Aruism 対称性: 100% 未満確認
        is_below_100 = bool(actual_rate < 1.0)
        rows.append({
            'seed': seed, 'change_scope': scope, 'change_metric_type': mt,
            'n_total_pairs': n_total,
            'actual_predict_rate': float(actual_rate),
            'baseline_shuffle_mean': baseline_mean,
            'baseline_shuffle_std': baseline_std,
            'lift_over_baseline': float(actual_rate - baseline_mean),
            'is_below_100pct': is_below_100,  # 箱 3 / Aruism 対称性確認
        })
    return pd.DataFrame(rows)


def parse_seeds(spec: str) -> list[int]:
    if '..' in spec:
        lo, hi = spec.split('..')
        return list(range(int(lo), int(hi) + 1))
    return [int(s) for s in spec.split(',')]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--smoke-or-main', default='main', choices=['smoke', 'main'])
    args = ap.parse_args()

    src_dir = OUT_SMOKE if args.smoke_or_main == 'smoke' else OUT_MAIN
    out_dir = src_dir

    print(f'=== v1101a 段階 2 Step C — 観察 A/B/C ===')
    print(f'src/out: {out_dir}')

    emit_path = src_dir / 'attention_emit_all.parquet'
    propag_path = src_dir / 'attention_propagation_all.parquet'
    if not emit_path.exists():
        # smoke で all がない場合 seed0 単独
        emit_path = src_dir / 'attention_emit_seed0.parquet'
        propag_path = src_dir / 'attention_propagation_seed0.parquet'

    print(f'loading {emit_path.name}, {propag_path.name}')
    emit = pd.read_parquet(emit_path)
    propag = pd.read_parquet(propag_path)
    print(f'emit: {len(emit):,} rows, propag: {len(propag):,} rows')

    t0 = time.time()
    print('観察 A (注意候補数の収束/発散)...', flush=True)
    df_a = observation_a(emit)
    print(f'  rows={len(df_a)}, elapsed={time.time()-t0:.1f}s')

    t1 = time.time()
    print('観察 B (波及先 cid 集合の隣接時点 Jaccard 代替指標)...', flush=True)
    df_b = observation_b(emit, propag)
    print(f'  rows={len(df_b)}, elapsed={time.time()-t1:.1f}s')

    t2 = time.time()
    print(f'観察 C (予測可能性 + shuffle baseline ×{N_SHUFFLE})...', flush=True)
    df_c = observation_c(emit)
    print(f'  rows={len(df_c)}, elapsed={time.time()-t2:.1f}s')

    df_a.to_parquet(out_dir / 'observation_a_candidate_count.parquet', index=False)
    df_b.to_parquet(out_dir / 'observation_b_jaccard_proxy.parquet', index=False)
    df_c.to_parquet(out_dir / 'observation_c_predictability.parquet', index=False)
    print(f'\nwrote 3 parquet to {out_dir}')
    print(f'total elapsed {time.time()-t0:.1f}s')


if __name__ == '__main__':
    main()
