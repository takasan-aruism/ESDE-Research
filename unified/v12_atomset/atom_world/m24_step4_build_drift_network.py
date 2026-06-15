#!/usr/bin/env python3
"""v12 Atomset STEP 4 — event 下流帰結(delta)で辺を重み付け/選別 + 対照 A/B

## 自己規律 (Code A)
①過去引用: STEP3 m20(辺ロジック/time-local membership)・m22(時間版でも rare↔common 0.925=event は
  出入り判定だけ)・m23(delta は per-(event,target_cid)・hop±1)、v107_baseline_constructor 読了
  (delta=target c の単独状態の event後窓 drift, pairwise でない)、v108(familiarity が atom 識別).
②Taka逐語(原文): 「意味のある信号は状態変化であって atom 同士の共起ではない」「下がること自体は目的でない
  ＝ランダム化でも下がる、対照との差が要る」「全部読んで変える系なら何やったって変化しないに決まってる」.
③判定はTaka(success/fail置かない) ④集約語なし.

## 実装前に data が正した2点 (報告に明記)
- D4 baseline: 設計の per-(event,path) は不可(hop=-1 の path は baseline 種別で実 path と別=0%重複)。
  hop=-1 は同 event_id を全共有 → baseline_med は **per-event_id** で引く(補正)。
- D2=delta_C_medium は |Δ|>0 が 1.7% のみ(疎)。R_familiarity_medium 68%/n_observed_medium 51% が密。
  → v1 は指示どおり C で実装(勝手に変えない)、疎性は報告で明示、D2 再knob は Taka 判断。

## 変える一点 (STEP3 から): event の実 target を均等に使うのをやめ、target c を drift で重み付け
- Main: edge_weight = (wi×wj) × d_norm(e,c),  d_norm = max(|delta_C_medium| − baseline_med(event), 0),
  d_norm=0 は drop (D3). 辺ロジック(cross-CID/time-local top5/(path×channel×n_core×window)層別/i≠j/無向)不変.
- 対照A: 均等 (wi×wj, STEP3 と同じ). 対照B: d_norm を同(event,path)内で target 間シャッフル.
## knob (Taka 上書き可): D1 top5/D2 drift量=delta_C_medium/D3 d_norm>0/D4 baseline per-event ON/D5 step10,win500.
## 一方向: 読=frozen, 書=timelocal_delta/ のみ. physics非書込.
"""
import sys, json, time
from pathlib import Path
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

REPO = Path('/home/takasan/esde/ESDE-Research')
AWDIR = REPO / 'unified/v12_atomset/atom_world'
sys.path.insert(0, str(AWDIR))
import m20_step3_build_timelocal_network as M20   # timelocal_membership, asof_grid, n_core_bin, ATOM_NAMES, rarity_z_map

SE_DIR = REPO / 'developmental/v107/outputs/main'
OUT_DIR = AWDIR / 'timelocal_delta'
OUT_DIR.mkdir(parents=True, exist_ok=True)
RARE = ['ingestion_cc', 'beta_formation', 'alpha_formation']
WIN = 500
# D2: primary=delta_C_medium(指示 v1, 疎 1.7%), secondary=delta_R_familiarity_medium(Code A 追加, 密 68%,
# v108「familiarity が atom 識別」と整合). v1 は変えず, secondary はラベル明示の追加(判定は Taka).
DRIFT_QUANTS = {'C': 'delta_C_medium', 'Rfam': 'delta_R_familiarity_medium'}
_RNG = np.random.default_rng(0)


def drift_table(seed):
    """per-(event_id, target_cid, path) の各 drift 量の d_norm(baseline per-event引き) と d_shuf(対照B)。"""
    b = pd.read_parquet(SE_DIR / f'baselines_with_delta_seed{seed}.parquet')
    cols = list(DRIFT_QUANTS.values())
    act = b[b['hop_distance'] == 1][['event_id', 'target_cid', 'relation_path_type'] + cols].copy()
    act = act.groupby(['event_id', 'target_cid', 'relation_path_type'], as_index=False)[cols].mean()  # dedup
    base = b[b['hop_distance'] == -1]

    def shuf(x):
        v = x.values.copy()
        if len(v) > 1:
            _RNG.shuffle(v)
        return pd.Series(v, index=x.index)

    keep = ['event_id', 'target_cid', 'relation_path_type']
    for tag, col in DRIFT_QUANTS.items():
        bm = base.groupby('event_id')[col].apply(lambda x: x.abs().median()).rename('bm')
        a = act.merge(bm, on='event_id', how='left')
        dn = (act[col].abs() - a['bm'].fillna(0.0)).clip(lower=0)
        act[f'dnorm_{tag}'] = dn.values
        act[f'dshuf_{tag}'] = act.groupby(['event_id', 'relation_path_type'])[f'dnorm_{tag}'].transform(shuf)
        keep += [f'dnorm_{tag}', f'dshuf_{tag}']
    return act[keep]


KEYS = ['atom_i', 'atom_j', 'path', 'channel', 'n_core_bin', 'window']


def build_layer(events, rp, memb, memb_times, drift, chunk=3000):
    """ctrlA(均等) + 各 drift 量の main(d_norm)/ctrlB(d_shuf) を層別集計。"""
    versions = ['ctrlA'] + [f'main_{t}' for t in DRIFT_QUANTS] + [f'ctrlB_{t}' for t in DRIFT_QUANTS]
    accs = {v: [] for v in versions}
    dcols = sum(([f'dnorm_{t}', f'dshuf_{t}'] for t in DRIFT_QUANTS), [])
    for k in range(0, len(events), chunk):
        ev = events.iloc[k:k + chunk]
        long = ev.merge(rp[['event_id', 'target_cid', 'relation_path_type']], on='event_id')
        long = long.rename(columns={'relation_path_type': 'path', 'source_cid': 's', 'target_cid': 'c'})
        long = long.merge(drift.rename(columns={'target_cid': 'c', 'relation_path_type': 'path'}),
                          on=['event_id', 'c', 'path'], how='left')
        for dc in dcols:
            long[dc] = long[dc].fillna(0.0)
        if long.empty:
            continue
        sk = M20.asof_grid(long[['s', 't_event']].drop_duplicates(), memb_times, 's', 't_src')
        tk = M20.asof_grid(long[['c', 't_event']].drop_duplicates(), memb_times, 'c', 't_tgt')
        long = long.merge(sk, on=['s', 't_event']).merge(tk, on=['c', 't_event']).dropna(subset=['t_src', 't_tgt'])
        if long.empty:
            continue
        long = long.merge(memb.rename(columns={'cid': 's', 't': 't_src', 'atom_idx': 'ai', 'w': 'wi'}), on=['s', 't_src'])
        long = long.merge(memb.rename(columns={'cid': 'c', 't': 't_tgt', 'atom_idx': 'aj', 'w': 'wj'}), on=['c', 't_tgt'])
        long = long[long['ai'] != long['aj']]
        if long.empty:
            continue
        ai = long['ai'].values; aj = long['aj'].values
        long['atom_i'] = np.minimum(ai, aj); long['atom_j'] = np.maximum(ai, aj)
        wbase = long['wi'].values * long['wj'].values
        long['w_ctrlA'] = wbase
        for t in DRIFT_QUANTS:
            long[f'w_main_{t}'] = wbase * long[f'dnorm_{t}'].values
            long[f'w_ctrlB_{t}'] = wbase * long[f'dshuf_{t}'].values
        for ver in versions:
            wc = 'w_' + ver
            dn = 'dnorm_' + ver.split('_')[-1] if ver != 'ctrlA' else None
            sub = long if ver == 'ctrlA' else long[long[wc] > 0]
            if sub.empty:
                continue
            agg = {'weight': (wc, 'sum'), 'n_events': (wc, 'size')}
            if dn:
                agg['drift_mean'] = (dn, 'mean')
            accs[ver].append(sub.groupby(KEYS, observed=True).agg(**agg).reset_index())
    out = {}
    for ver, lst in accs.items():
        if not lst:
            out[ver] = pd.DataFrame(columns=KEYS + ['weight', 'n_events'])
            continue
        a = pd.concat(lst, ignore_index=True)
        agg = {'weight': ('weight', 'sum'), 'n_events': ('n_events', 'sum')}
        if 'drift_mean' in a.columns:
            agg['drift_mean'] = ('drift_mean', 'mean')
        out[ver] = a.groupby(KEYS, observed=True).agg(**agg).reset_index()
    return out


def process_seed(seed):
    t0 = time.time()
    memb = M20.timelocal_membership(seed)
    memb_times = memb[['cid', 't']].drop_duplicates()
    drift = drift_table(seed)
    se = pd.read_parquet(SE_DIR / f'source_events_seed{seed}.parquet').reset_index(drop=True)
    rp = pd.read_parquet(SE_DIR / f'relation_paths_seed{seed}.parquet')
    se['rarity_z'] = M20.rarity_z_map(se)
    se['channel'] = se['event_source_type'].map({'ingestion': 'ingestion_cc', 'alpha_formation': 'alpha_formation',
                                                 'beta_formation': 'beta_formation', 'pulse': 'pulse'})
    se = se[se['event_source_type'] != 'c_conversion']
    se['n_core_bin'] = se['n_core_member'].apply(M20.n_core_bin)
    se['t_event'] = se['timestamp'].astype(int); se['window'] = (se['t_event'] // WIN).astype(int)
    cols = ['event_id', 'source_cid', 'channel', 'n_core_bin', 't_event', 'window']
    rare_ev = se[se['channel'].isin(RARE)][cols]
    common_ev = se[se['channel'] == 'pulse'][cols]

    rare = build_layer(rare_ev, rp, memb, memb_times, drift)
    common = build_layer(common_ev, rp, memb, memb_times, drift)

    def finalize(df):
        df = df.copy(); df.insert(0, 'seed', seed)
        df['atom_i'] = df['atom_i'].map(lambda j: M20.ATOM_NAMES[j])
        df['atom_j'] = df['atom_j'].map(lambda j: M20.ATOM_NAMES[j])
        return df
    finalize(rare['ctrlA']).to_parquet(OUT_DIR / f'atom_edges_ctrlA_seed{seed}.parquet', index=False)
    for t in DRIFT_QUANTS:
        finalize(rare[f'main_{t}']).to_parquet(OUT_DIR / f'atom_edges_main_{t}_seed{seed}.parquet', index=False)
        finalize(rare[f'ctrlB_{t}']).to_parquet(OUT_DIR / f'atom_edges_ctrlB_{t}_seed{seed}.parquet', index=False)
        finalize(common[f'main_{t}']).to_parquet(OUT_DIR / f'common_edges_main_{t}_seed{seed}.parquet', index=False)

    cov = {'seed': seed, 'drift_quants': DRIFT_QUANTS, 'ctrlA_cells': int(len(rare['ctrlA'])),
           'ctrlA_pairs': int(rare['ctrlA'][['atom_i', 'atom_j']].drop_duplicates().shape[0]),
           'elapsed_s': round(time.time() - t0, 1)}
    for t in DRIFT_QUANTS:
        cov[f'main_{t}_cells'] = int(len(rare[f'main_{t}']))
        cov[f'main_{t}_pairs'] = int(rare[f'main_{t}'][['atom_i', 'atom_j']].drop_duplicates().shape[0])
        cov[f'frac_moved_{t}'] = float((drift[f'dnorm_{t}'] > 0).mean())
    (OUT_DIR / f'coverage_seed{seed}.json').write_text(json.dumps(cov, indent=2, ensure_ascii=False))
    return cov


def main():
    seeds = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(24))
    for seed in seeds:
        c = process_seed(seed)
        msg = f"seed{seed}: ctrlA={c['ctrlA_pairs']}pairs"
        for t in DRIFT_QUANTS:
            msg += f" | {t}: main={c[f'main_{t}_pairs']}pairs/{c[f'main_{t}_cells']}c moved={c[f'frac_moved_{t}']:.0%}"
        print(msg + f" ({c['elapsed_s']}s)")
    print('=== STEP 4 drift 網形成 完了 (timelocal_delta/) ===')


if __name__ == '__main__':
    main()
