#!/usr/bin/env python3
"""v12 Atomset cid_align — STEP 2: 関門 = 準・循環性チェック (選択肢 C)

## 目的 (指示書 v2 STEP 2, 最重要)
cid_align が v1114 既存入力 (生イベントカウント) の遅延コピー (自明) でなく、独立な
新情報 (経験の累積=往復の履歴) かを確認する。ここで落ちたら本実装しない。

## 認識の核 (手放さない)
- cid_align は event stream の TRANSFORM (cumulative + 状態 + f重み + 正規化 + 48次元方向)。
  問うのは「自明な遅延コピー(R²高)」か「非自明な累積(R²低)」か。R² の絶対値でなく分布で見る。

## 方法 (選択肢 C: per-CID 主 + 系全体 副, 集約一個で判定しない=絶対格言#4)
- per-CID (主): cid_align 変化量 = 1 - cosine(align_t, align_{t-1}) を目的変数、その CID 自身の
  per-10step 生イベントカウント 5 種 (pulse/alpha_formation/beta_formation/ingestion/c_conversion)
  を説明変数にした重回帰 R²。R² を個別 CID 分布 + n_core 別で出す。単相関も。
- 系全体 (副): cid_align 変化量を系全体に集約した版と、v1114 実発火入力(系全体カウント)の相関。

## 判定線 (Web Claude 固定)
- per-CID R² 中央値 < 0.3 が過半 → 独立 → 関門通過 (STEP 3 へ)
- per-CID R² 中央値 > 0.7 が過半 → 遅延コピー=自明 → 停止 (本実装しない)
- 中間 (0.3-0.7 が過半) → 高/低 R² の CID を個別精査, Web Claude/Taka 判断

## crown 禁止: 「独立確認=個性化成立」と書かない。独立は必要条件で個性化の証明でない。
物理書込ゼロ (parquet を読んで分析するのみ)。
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

REPO = Path('/home/takasan/esde/ESDE-Research')
ALIGN = REPO / 'unified/v1201/run_step1b/cid_align_step1b.parquet'
SRC_DIR = REPO / 'developmental/v107/outputs/main'
OUT_DIR = REPO / 'unified/v1201/run_step2'
OUT_DIR.mkdir(parents=True, exist_ok=True)

N_PER_CHUNK = 10
MIN_CHUNKS = 12  # R² に要る最小 chunk 数 (>> 説明変数 5)
EVENT_TYPES = ['pulse', 'alpha_formation', 'beta_formation', 'ingestion', 'c_conversion']
ACOLS = [f'a{j:02d}' for j in range(48)]


def r2_ols(X, y):
    """切片付き OLS の R²。"""
    n = len(y)
    if n < MIN_CHUNKS:
        return np.nan
    ss_tot = ((y - y.mean()) ** 2).sum()
    if ss_tot < 1e-12:
        return np.nan
    X1 = np.column_stack([np.ones(n), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    yhat = X1 @ beta
    ss_res = ((y - yhat) ** 2).sum()
    return float(1 - ss_res / ss_tot)


def main():
    d = pd.read_parquet(ALIGN)
    per_cid = []
    sys_change_all = []   # 系全体 (副) 用
    sys_counts_all = []

    for seed in range(24):
        src = pd.read_parquet(SRC_DIR / f'source_events_seed{seed}.parquet')
        src['chunk'] = (src['timestamp'] // N_PER_CHUNK).astype(int)
        # per (cid, chunk, type) カウント
        cnt = (src.groupby(['source_cid', 'chunk', 'event_source_type']).size()
               .unstack(fill_value=0))
        for et in EVENT_TYPES:
            if et not in cnt.columns:
                cnt[et] = 0
        cnt = cnt[EVENT_TYPES]
        ds = d[d['seed'] == seed]

        # 系全体 (副): chunk ごとの align 平均変化量 と系全体カウント
        sys_cnt_chunk = src.groupby(['chunk', 'event_source_type']).size().unstack(fill_value=0)
        for et in EVENT_TYPES:
            if et not in sys_cnt_chunk.columns:
                sys_cnt_chunk[et] = 0

        for cid, g in ds.groupby('cid'):
            g = g.sort_values('chunk').reset_index(drop=True)
            if len(g) < MIN_CHUNKS + 1:
                continue
            A = g[ACOLS].values
            A = A / (np.linalg.norm(A, axis=1, keepdims=True) + 1e-12)
            change = 1.0 - np.sum(A[1:] * A[:-1], axis=1)   # 1-cosine, len = n-1
            chunks = g['chunk'].values[1:]                  # change[t] は chunk t の event 由来
            # その CID の chunk ごとカウント
            try:
                cc = cnt.loc[cid]
            except KeyError:
                continue
            X = np.array([[float(cc.loc[ch, et]) if ch in cc.index else 0.0
                           for et in EVENT_TYPES] for ch in chunks])
            r2 = r2_ols(X, change)
            if np.isnan(r2):
                continue
            # 単相関 (どのカウントと紛れやすいか)
            corrs = {}
            for k, et in enumerate(EVENT_TYPES):
                xc = X[:, k]
                corrs[et] = float(np.corrcoef(xc, change)[0, 1]) if xc.std() > 1e-9 else np.nan
            per_cid.append({
                'seed': seed, 'cid': int(cid), 'n_core': int(g['n_core'].iloc[0]),
                'n_chunks': len(change), 'r2': max(0.0, r2),
                **{f'corr_{et}': corrs[et] for et in EVENT_TYPES},
            })
            sys_change_all.append((seed, chunks, change))

    pc = pd.DataFrame(per_cid)
    pc.to_parquet(OUT_DIR / 'step2_per_cid_r2.parquet', index=False)

    # ===== 報告 (集約一個で判定しない: 分布 + n_core 別) =====
    print('=== STEP 2 関門: 準・循環性 (per-CID R²) ===\n')
    print(f'対象 CID (n_chunks>={MIN_CHUNKS}): {len(pc)} / 全 5224')
    r2 = pc['r2'].values
    print(f'\nper-CID R² 分布:')
    print(f'  中央値={np.median(r2):.3f} 平均={r2.mean():.3f} '
          f'25%={np.percentile(r2,25):.3f} 75%={np.percentile(r2,75):.3f}')
    bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01]
    h, _ = np.histogram(r2, bins=bins)
    print(f'  ヒストグラム:')
    for i in range(len(bins) - 1):
        bar = '#' * int(40 * h[i] / max(h.max(), 1))
        print(f'    [{bins[i]:.1f},{bins[i+1]:.1f}): {h[i]:>5} {bar}')
    lo = float((r2 < 0.3).mean()); mid = float(((r2 >= 0.3) & (r2 <= 0.7)).mean()); hi = float((r2 > 0.7).mean())
    print(f'\n  R²<0.3: {lo:.0%} | 0.3-0.7: {mid:.0%} | R²>0.7: {hi:.0%}')

    print(f'\nn_core 別 R² 中央値 (集団平均の罠を避ける層化):')
    for nc, gg in pc.groupby('n_core'):
        if len(gg) >= 5:
            print(f'  n_core={nc} (n={len(gg)}): median R²={gg["r2"].median():.3f} '
                  f'[<0.3:{(gg["r2"]<0.3).mean():.0%} >0.7:{(gg["r2"]>0.7).mean():.0%}]')

    print(f'\n単相関 (cid_align変化量 vs 各カウント) の中央値:')
    for et in EVENT_TYPES:
        c = pc[f'corr_{et}'].dropna()
        print(f'  {et:<16}: median |corr|={c.abs().median():.3f} (n={len(c)})')

    # 判定線
    med = np.median(r2)
    print(f'\n=== 判定 ===')
    if med < 0.3:
        verdict = '通過候補: per-CID R² 中央値 < 0.3 → 生カウントで説明できない独立次元'
    elif med > 0.7:
        verdict = '停止候補: per-CID R² 中央値 > 0.7 → 遅延コピー=自明'
    else:
        verdict = '中間: 0.3-0.7 → 高/低 R² の CID を個別精査要 (Web Claude/Taka 判断)'
    print(f'  per-CID R² 中央値 = {med:.3f} → {verdict}')
    print(f'\n(crown 禁止: 独立は必要条件、個性化の証明でない。判定は Taka。)')

    # 系全体 (副)
    print(f'\n=== 系全体 (副): align 平均変化量 vs 系全体カウント ===')
    # seed ごとに chunk-align平均変化量 と 系全体カウントの相関 (per-CID と食い違うか)
    sys_r2s = []
    for seed in range(24):
        rows = [(ch, cv) for s, chs, cvs in sys_change_all if s == seed for ch, cv in zip(chs, cvs)]
        if not rows:
            continue
        sdf = pd.DataFrame(rows, columns=['chunk', 'change']).groupby('chunk')['change'].mean()
        src = pd.read_parquet(SRC_DIR / f'source_events_seed{seed}.parquet')
        src['chunk'] = (src['timestamp'] // N_PER_CHUNK).astype(int)
        sc = src.groupby(['chunk', 'event_source_type']).size().unstack(fill_value=0)
        for et in EVENT_TYPES:
            if et not in sc.columns:
                sc[et] = 0
        common = sdf.index.intersection(sc.index)
        if len(common) < MIN_CHUNKS:
            continue
        X = sc.loc[common, EVENT_TYPES].values
        y = sdf.loc[common].values
        sys_r2s.append(r2_ols(X, y))
    sys_r2s = [x for x in sys_r2s if not np.isnan(x)]
    if sys_r2s:
        print(f'  系全体 R² (seed別) 中央値={np.median(sys_r2s):.3f} (n={len(sys_r2s)} seeds)')
        print(f'  per-CID 中央値({med:.3f}) と系全体中央値({np.median(sys_r2s):.3f}) の食い違い: '
              f'{"あり=集約で像が変わる(絶対格言#4の実例)" if abs(med-np.median(sys_r2s))>0.2 else "小"}')


if __name__ == '__main__':
    main()
