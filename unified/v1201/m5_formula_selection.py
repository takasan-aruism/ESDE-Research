#!/usr/bin/env python3
"""v12 Atomset M5 (post-process) — 特徴度の式をデータから選ぶ工程

## 目的 (Taka/GPT 2026-06-11 確定)
机上で式を決めると Gemini 4次元説の轍 (推測) になる。**既存ログ (新 run ゼロ) で
候補式を比較し、頻度の裏口を最も塞ぐ式をデータで選ぶ。** post-process が成功条件を
満たすまで live M5 hook に入らない。

## 成功条件 (GPT、これが判定基準)
「CID 間に差が出た」だけでは成功でない。
  corr(contact数, experience bonus) が十分低い  かつ  特徴度分散が非ゼロ。
相関が高ければ M4 の event_count 問題が contact_count に名を変えて再発しただけ。
**差は出たが接触数で説明できない、が成功。**

## 設計
- 状態空間 = seed ごと z 正規化した cid_vec 7 軸 (atom 射影は使わない、有効ランク 5-7 の健全空間):
  lifespan_so_far / n_core_member / R_familiarity_pre / Q_pre / C_pre / n_alphas_pre / n_observed_pre
- 自己系の値 = ‖v_t − その CID の過去平均(historical_self)‖  (pulse/α/β/c_conv、ingestion 除く)
- 出会い系の値 = ‖self_vec − partner_vec‖  at contact (E3_contact 主 + ingestion 別 type)
  partner 状態は接触時刻で merge_asof backward (= pre-event 凍結, GPT 指摘充足)
- 特徴度 = standardize(値, その CID の履歴);  new_rate = old_rate × (1+特徴度) を反復
- 安全策: n<K → 特徴度=0 (立ち上がり);  scale floor (σ/MAD);  z clip

## 候補式 (full-history per-CID 標準化で比較。live は pre-event expanding)
  1 linear_z   : f=|x−μ|/σ          ; bonus=Π(1+f)−1        ← Taka 原案 (絶対値)
  2 clipped_z  : f=min(|x−μ|/σ, Z)  ; bonus=Π(1+f)−1
  3 logcount_z : f=|x−μ|/σ          ; bonus=Σf / log(1+n)   ← count 正規化累積
  4 signed_mr  : f=clip((x−μ)/σ,±Z) ; bonus=Π(1+α·f)−1      ← 符号付き平均回帰
  5 robust_z   : f=clip((x−m)/MAD±Z); bonus=Π(1+α·f)−1      ← 推奨 (median/MAD, quantization 強)

## 出力 (新 run なし)
  run_m5/formula_selection.json + 標準出力の比較表 + 8 診断
"""
import os, sys, json, glob
os.environ['OMP_NUM_THREADS'] = '1'
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import pearsonr, spearmanr

REPO = Path('/home/takasan/esde/ESDE-Research')
V107 = REPO / 'developmental/v107/outputs/main'
OTHER = REPO / 'primitive/v917/diag_v917_main/selfread'
ING = REPO / 'developmental/v101/diag_v101_main/ingestion'
OUT = REPO / 'unified/v1201/run_m5'
OUT.mkdir(parents=True, exist_ok=True)

DIMS = ['lifespan_so_far', 'n_core_member', 'R_familiarity_pre', 'Q_pre',
        'C_pre', 'n_alphas_pre', 'n_observed_pre']
K_MIN = 3          # n<K_MIN の CID/履歴浅は特徴度=0 (立ち上がり対策)
Z_CLIP = 4.0       # 特徴度 clip
SCALE_FLOOR = 1e-6 # σ/MAD floor (div-by-zero, quantization の偽∞ 回避)
ALPHA = 0.5        # 符号付き式の倍率係数 (1+α·f が負にならない範囲)
MAD_C = 1.4826


# ----------------------------------------------------------------------
# データ構築
# ----------------------------------------------------------------------
def load_state_table(seed):
    """v107 全 event を z 正規化した状態テーブル (距離空間)。self/partner 共通。"""
    df = pd.read_parquet(V107 / f'source_events_seed{seed}.parquet')
    df = df[['source_cid', 'timestamp', 'event_source_type'] + DIMS].copy()
    for d in DIMS:
        df[d] = pd.to_numeric(df[d], errors='coerce')
    df = df.dropna(subset=DIMS)
    # per-seed z 正規化 (self も partner も同じ正規化)
    for d in DIMS:
        mu, sd = df[d].mean(), df[d].std()
        df[d] = (df[d] - mu) / (sd if sd > 1e-9 else 1.0)
    return df


def self_values(state):
    """自己系の値 = ‖v_t − その CID の過去平均‖ (ingestion 除く)。"""
    df = state[state['event_source_type'] != 'ingestion'].copy()
    df = df.sort_values(['source_cid', 'timestamp']).reset_index(drop=True)
    g = df.groupby('source_cid')
    order = g.cumcount()
    sq = np.zeros(len(df))
    for d in DIMS:
        prior_sum = g[d].cumsum() - df[d]
        prior_mean = prior_sum / order.replace(0, np.nan)   # 過去平均 (pre-event)
        sq += (df[d].values - prior_mean.values) ** 2
    df['value'] = np.sqrt(sq)
    df['cid'] = df['source_cid']
    out = df[['cid', 'timestamp', 'value']].dropna(subset=['value'])
    out = out.rename(columns={'timestamp': 't'})
    out['etype'] = 'self'
    return out


def _asof_state(events, state, cid_col, t_col):
    """events の (cid_col, t_col) に state を merge_asof backward で添付 (pre-event)。"""
    st = state[['source_cid', 'timestamp'] + DIMS].sort_values('timestamp')
    ev = events.sort_values(t_col)
    m = pd.merge_asof(ev, st.rename(columns={'source_cid': cid_col, 'timestamp': '_st'}),
                      left_on=t_col, right_on='_st', by=cid_col, direction='backward')
    return m


def encounter_values(seed, state):
    """出会い系の値 = ‖self_vec − partner_vec‖。E3_contact(主) + ingestion(別 type)。"""
    rows = []
    # --- E3_contact (v917 other_records, 主チャネル) ---
    o = pd.read_csv(OTHER / f'other_records_seed{seed}.csv',
                    usecols=['cid_id', 'other_cid_id', 'step'])
    o = o.rename(columns={'cid_id': 'cid', 'other_cid_id': 'partner', 'step': 't'})
    rows.append(_dist_pair(o, state, 'E3_contact'))
    # --- ingestion (v101, 別 type、希少サブタイプとして保持) ---
    g = pd.read_csv(ING / f'ingestion_events_seed{seed}.csv',
                    usecols=['observer_cid', 'ghost_cid', 'global_step'])
    g = g.rename(columns={'observer_cid': 'cid', 'ghost_cid': 'partner', 'global_step': 't'})
    rows.append(_dist_pair(g, state, 'ingestion'))
    return pd.concat(rows, ignore_index=True)


def _dist_pair(ev, state, etype):
    # self 状態
    s = _asof_state(ev[['cid', 'partner', 't']].copy(), state, 'cid', 't')
    self_v = s[DIMS].copy()
    # partner 状態 (同時刻、別 cid)
    p = _asof_state(ev[['cid', 'partner', 't']].rename(columns={'partner': 'pcid'}).copy(),
                    state, 'pcid', 't')
    part_v = p[DIMS].copy()
    valid = self_v.notna().all(axis=1).values & part_v.notna().all(axis=1).values
    dist = np.sqrt(((self_v.values - part_v.values) ** 2).sum(axis=1))
    out = pd.DataFrame({'cid': s['cid'].values, 't': s['t'].values,
                        'value': dist, 'etype': etype})
    return out[valid].dropna(subset=['value'])


# ----------------------------------------------------------------------
# 特徴度 → bonus (5 候補式)。full-history per-CID 標準化で比較。
# ----------------------------------------------------------------------
def per_cid_stats(values):
    n = len(values)
    if n < K_MIN:
        return None
    mu, sd = values.mean(), values.std()
    m = np.median(values)
    mad = np.median(np.abs(values - m)) * MAD_C
    return dict(n=n, mu=mu, sd=max(sd, SCALE_FLOOR), med=m, mad=max(mad, SCALE_FLOOR))


def feat_and_bonus(values, formula):
    """1 CID の値列 → (特徴度配列, bonus scalar)。n<K_MIN は (zeros, 0)。"""
    st = per_cid_stats(values)
    if st is None:
        return np.zeros(len(values)), 0.0, np.zeros(len(values))
    x = values
    if formula in ('linear_z', 'clipped_z', 'logcount_z'):
        f = np.abs(x - st['mu']) / st['sd']
        if formula == 'clipped_z':
            f = np.minimum(f, Z_CLIP)
    elif formula == 'signed_mr':
        f = np.clip((x - st['mu']) / st['sd'], -Z_CLIP, Z_CLIP)
    elif formula == 'robust_z':
        f = np.clip((x - st['med']) / st['mad'], -Z_CLIP, Z_CLIP)
    else:
        raise ValueError(formula)
    # 倍率と累積
    if formula == 'logcount_z':
        mult = 1.0 + f                       # 参考 (倍率)
        bonus = float(f.sum() / np.log(1 + st['n']))
    elif formula in ('signed_mr', 'robust_z'):
        mult = np.clip(1.0 + ALPHA * f, 0.1, None)
        bonus = float(np.prod(mult) - 1.0)
    else:  # linear_z, clipped_z
        mult = 1.0 + f
        bonus = float(np.prod(mult) - 1.0)
    return f, bonus, mult


# ----------------------------------------------------------------------
# 評価 (成功条件 + 8 診断)
# ----------------------------------------------------------------------
FORMULAS = ['linear_z', 'clipped_z', 'logcount_z', 'signed_mr', 'robust_z']


def evaluate_system(ev, system_name, per_seed_corr=None):
    """ev: columns [cid, t, value, etype, seed]。formula ごとに per-CID bonus を出し成功条件評価。"""
    results = {}
    # contact 数 (= per-CID event 数) : 頻度の代理
    counts = ev.groupby(['seed', 'cid']).size().rename('count')
    for formula in FORMULAS:
        feats_all = []
        bonus_rows = []
        mult_typical = []   # |倍率−1|<0.05 の割合用
        for (seed, cid), sub in ev.sort_values('t').groupby(['seed', 'cid']):
            vals = sub['value'].values
            f, bonus, mult = feat_and_bonus(vals, formula)
            feats_all.append(f)
            bonus_rows.append((seed, cid, len(vals), bonus))
            if formula != 'logcount_z':
                mult_typical.append(np.abs(mult - 1.0) < 0.05)
        bdf = pd.DataFrame(bonus_rows, columns=['seed', 'cid', 'count', 'bonus'])
        feats = np.concatenate(feats_all) if feats_all else np.array([0.0])
        # --- 成功条件 ---
        active = bdf[bdf['bonus'] != 0]
        if len(active) >= 3 and active['count'].std() > 0 and active['bonus'].std() > 0:
            pear = float(pearsonr(active['count'], active['bonus'])[0])
            spear = float(spearmanr(active['count'], active['bonus'])[0])
        else:
            pear = spear = float('nan')
        var_feat = float(np.var(feats))
        # --- 8 診断 ---
        typ_frac = float(np.mean(np.concatenate(mult_typical))) if mult_typical else float('nan')
        # 高接触 CID (上位10%) の bonus 独占度
        if len(active) >= 10:
            thr = active['count'].quantile(0.9)
            top = active[active['count'] >= thr]
            share_bonus = float(top['bonus'].abs().sum() / active['bonus'].abs().sum())
            share_count = float(len(top) / len(active))
        else:
            share_bonus = share_count = float('nan')
        zero_frac = float((bdf['bonus'] == 0).mean())   # n<K で 0 扱いになった率
        # seed 間 corr 再現
        if per_seed_corr is not None:
            sc = []
            for sd_, g in active.groupby('seed'):
                if len(g) >= 3 and g['count'].std() > 0 and g['bonus'].std() > 0:
                    sc.append(spearmanr(g['count'], g['bonus'])[0])
            seed_corr_mean = float(np.nanmean(sc)) if sc else float('nan')
            seed_corr_std = float(np.nanstd(sc)) if sc else float('nan')
        else:
            seed_corr_mean = seed_corr_std = float('nan')
        ab = active['bonus'].abs()
        results[formula] = dict(
            pearson_count_bonus=pear, spearman_count_bonus=spear, var_feat=var_feat,
            typical_mult_near1_frac=typ_frac, top10pct_bonus_share=share_bonus,
            top10pct_count_share=share_count, zero_bonus_frac=zero_frac,
            seed_spearman_mean=seed_corr_mean, seed_spearman_std=seed_corr_std,
            n_active=int(len(active)), bonus_mean=float(active['bonus'].mean()) if len(active) else 0.0,
            bonus_median=float(ab.median()) if len(active) else 0.0,
            bonus_p90=float(ab.quantile(0.9)) if len(active) else 0.0,
            bonus_p99=float(ab.quantile(0.99)) if len(active) else 0.0,
        )
    return results, bdf if 'bdf' in dir() else None


# ----------------------------------------------------------------------
def main():
    seeds = [int(s) for s in sys.argv[1:]] if len(sys.argv) > 1 else list(range(24))
    print(f'=== M5 post-process 式選定 — seeds={seeds} (新 run なし) ===\n')

    self_parts, enc_parts = [], []
    for seed in seeds:
        state = load_state_table(seed)
        sv = self_values(state); sv['seed'] = seed
        ev = encounter_values(seed, state); ev['seed'] = seed
        self_parts.append(sv); enc_parts.append(ev)
        print(f'  seed{seed}: self_events={len(sv)}, encounter={len(ev)} '
              f'(E3={int((ev.etype=="E3_contact").sum())}, ing={int((ev.etype=="ingestion").sum())})')
    self_ev = pd.concat(self_parts, ignore_index=True)
    enc_ev = pd.concat(enc_parts, ignore_index=True)

    print('\n--- 評価 ---')
    out = {}
    for name, ev, etypes in [
        ('self', self_ev, ['self']),
        ('encounter_E3', enc_ev[enc_ev.etype == 'E3_contact'], ['E3_contact']),
        ('encounter_ingestion', enc_ev[enc_ev.etype == 'ingestion'], ['ingestion']),
    ]:
        res, _ = evaluate_system(ev, name, per_seed_corr=True)
        out[name] = res
        print(f'\n### {name}  (events={len(ev)}, CIDs={ev.cid.nunique()})')
        print(f'{"formula":11s} {"|corr|count↓":>12s} {"spear↓":>8s} {"var_feat↑":>10s} '
              f'{"typ→1":>7s} {"top10%bonus":>11s} {"(count share)":>13s} {"zero%":>7s} {"seed_sp±":>14s}')
        for fm in FORMULAS:
            r = res[fm]
            print(f'{fm:11s} {r["pearson_count_bonus"]:>12.3f} {r["spearman_count_bonus"]:>8.3f} '
                  f'{r["var_feat"]:>10.3f} {r["typical_mult_near1_frac"]:>7.2f} '
                  f'{r["top10pct_bonus_share"]:>11.2f} {r["top10pct_count_share"]:>13.2f} '
                  f'{r["zero_bonus_frac"]:>7.2f} {r["seed_spearman_mean"]:>7.2f}±{r["seed_spearman_std"]:.2f}')

    # 自己 vs 出会い の支配 (合成時どちらか一方が支配しないか) — robust_z で代表比較
    print('\n### 自己系 vs 出会い系 bonus magnitude (robust_z, 支配チェック #7)')
    print(f'  {"system":22s} {"median":>10s} {"p90":>10s} {"p99":>12s} {"mean":>12s}')
    for name in ['self', 'encounter_E3', 'encounter_ingestion']:
        r = out[name]['robust_z']
        print(f'  {name:22s} {r["bonus_median"]:>10.3f} {r["bonus_p90"]:>10.3f} '
              f'{r["bonus_p99"]:>12.3f} {r["bonus_mean"]:>12.3f}')

    (OUT / 'formula_selection.json').write_text(json.dumps(
        {'seeds': seeds, 'results': out,
         'success_criterion': 'low |corr(count,bonus)| AND nonzero var_feat',
         'params': dict(K_MIN=K_MIN, Z_CLIP=Z_CLIP, ALPHA=ALPHA, dims=DIMS)},
        indent=2, ensure_ascii=False))
    print(f'\n保存: {OUT/"formula_selection.json"}')
    print('=== 完了 (live M5 hook は未着手、式確定後) ===')


if __name__ == '__main__':
    main()
