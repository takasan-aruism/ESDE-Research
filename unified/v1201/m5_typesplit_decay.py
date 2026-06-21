#!/usr/bin/env python3
"""v12 Atomset M5 (post-process 2) — 経験を種類で分けて別軸を育てる + 衰退

## 設計転換 (Taka 2026-06-11、相談役 忖度なし合意)
前回の「累積をどう抑えるか」は見当違い＝経験を種類で混ぜたバグ。分ければ消える。
- (1) 種類で分けて性格の別部分を育てる:
    出会い系(E3_contact/ingestion) → 他者・関係軸 (OTHER)
    自己系(pulse/α/β/c_conv)       → 自己の動き軸 (SELF)
    混ぜない ⇒ 自己系500回が出会い系数十回を埋もれさせる問題が起きない (累積 bound 不要)
- (2) 衰退: 使わない方向の一致率は徐々に低下 (使う方向は伸び使わない方向は退く＝個性が分かれる)
- (3) 平衡を先に目指さない・過度に振らせて波及を観察。発散抑制を目的化しない。
    技術的一線: θ が NaN/inf で記録が死ぬ域だけ回避。
    ※ post-process では θ は観測不能。代理 = match_rate 自体が inf/nan に発散する (α,λ) 域
      (rate inf → torque inf → θ NaN の上流原因)。live はこの「rate 有限域」内で振らせる。

式は robust_z 確定のまま。種類分けで「どの経験がどの軸を robust_z で動かすか」を分ける。

## 軸割り当て (10/48 軸の意味から自然対応)
  SELF  : lifespan_so_far(temporal) / n_core_member(scale) / Q_pre(ontological) / C_pre(resonance)
  OTHER : R_familiarity_pre(epistemological) / n_alphas_pre(interconnection) / n_observed_pre(experience)

## 機構 (per-CID, per-axis match rate r_a, 初期 1)
  時刻順に event を処理。各 event で:
    1. 全軸 decay:           r_a ← 1 + (r_a − 1)·λ
    2. その event 種が触る軸だけ: f_a = clip((val_a − med)/MAD, ±Z)   (robust_z, full-history per cid-axis)
       r_a ← r_a · clip(1 + α·f_a, 0.1, ∞)
  自己 event は SELF 軸のみ、出会い event は OTHER 軸のみ更新。

## 観察 (新 run なし、既存ログ。(α,λ) を sweep)
  ① 種類分けで自己系と出会い系が別軸に効くか (SELF集約 vs OTHER集約 の CID 間相関 → 低=独立)
  ② 衰退で個性が分かれるか (CID 間の軸プロファイル多様性、λ=1 vs λ<1)
  ③ θ が記録不能になる過度域 (match_rate が inf/nan に発散する (α,λ))
  + 自己が出会いを支配しないこと (別軸なので magnitude 比較が commensurate)
"""
import os, sys, json, glob
os.environ['OMP_NUM_THREADS'] = '1'
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import pearsonr

REPO = Path('/home/takasan/esde/ESDE-Research')
V107 = REPO / 'developmental/v107/outputs/main'
OTHER_DIR = REPO / 'primitive/v917/diag_v917_main/selfread'
ING = REPO / 'developmental/v101/diag_v101_main/ingestion'
OUT = REPO / 'unified/v1201/run_m5'
OUT.mkdir(parents=True, exist_ok=True)

SELF_AXES = ['lifespan_so_far', 'n_core_member', 'Q_pre', 'C_pre']
OTHER_AXES = ['R_familiarity_pre', 'n_alphas_pre', 'n_observed_pre']
AXES = SELF_AXES + OTHER_AXES
SELF_IDX = list(range(len(SELF_AXES)))
OTHER_IDX = list(range(len(SELF_AXES), len(AXES)))

K_MIN = 3
Z_CLIP = 4.0
SCALE_FLOOR = 1e-6
MAD_C = 1.4826
OVERFLOW = 1e300   # これを超えたら「記録が死ぬ」(inf 化) とみなす

# sweep: gain α と decay λ (per-event)。α を高くして「記録が死ぬ域」を探す。
ALPHAS = [0.5, 1.0, 2.0, 4.0, 8.0]
LAMBDAS = [1.0, 0.99, 0.95, 0.90]   # 1.0 = 衰退なし
STRESS_LOG10 = 6.0    # rate>1e6: torque 過大 (record-stress 代理)
DEAD_LOG10 = 300.0    # rate>1e300: inf 化 (記録が死ぬ)


def load_state(seed):
    df = pd.read_parquet(V107 / f'source_events_seed{seed}.parquet')
    df = df[['source_cid', 'timestamp', 'event_source_type'] + AXES].copy()
    for d in AXES:
        df[d] = pd.to_numeric(df[d], errors='coerce')
    df = df.dropna(subset=AXES)
    for d in AXES:
        mu, sd = df[d].mean(), df[d].std()
        df[d] = (df[d] - mu) / (sd if sd > 1e-9 else 1.0)
    return df


def self_axis_values(state):
    """自己 event の SELF 軸 per-dim value = |v_a − その CID の平均_a| (ingestion 除く)。"""
    df = state[state['event_source_type'] != 'ingestion'].copy()
    df = df.sort_values(['source_cid', 'timestamp'])
    g = df.groupby('source_cid')
    out = pd.DataFrame({'cid': df['source_cid'].values, 't': df['timestamp'].values})
    for a in SELF_AXES:
        cidmean = g[a].transform('mean')
        out[a] = np.abs(df[a].values - cidmean.values)
    out['etype'] = 'self'
    return out


def _asof(ev, state, cidcol):
    st = state[['source_cid', 'timestamp'] + AXES].sort_values('timestamp')
    m = pd.merge_asof(ev.sort_values('t'),
                      st.rename(columns={'source_cid': cidcol, 'timestamp': '_st'}),
                      left_on='t', right_on='_st', by=cidcol, direction='backward')
    return m


def encounter_axis_values(seed, state):
    """出会い event の OTHER 軸 per-dim value = |self_a − partner_a| at contact。"""
    rows = []
    o = pd.read_csv(OTHER_DIR / f'other_records_seed{seed}.csv',
                    usecols=['cid_id', 'other_cid_id', 'step']).rename(
        columns={'cid_id': 'cid', 'other_cid_id': 'partner', 'step': 't'})
    rows.append(_enc_dist(o, state, 'E3_contact'))
    g = pd.read_csv(ING / f'ingestion_events_seed{seed}.csv',
                    usecols=['observer_cid', 'ghost_cid', 'global_step']).rename(
        columns={'observer_cid': 'cid', 'ghost_cid': 'partner', 'global_step': 't'})
    rows.append(_enc_dist(g, state, 'ingestion'))
    return pd.concat(rows, ignore_index=True)


def _enc_dist(ev, state, etype):
    base = ev[['cid', 'partner', 't']].copy()
    s = _asof(base.copy(), state, 'cid')
    p = _asof(base.rename(columns={'partner': 'pcid'}).copy(), state, 'pcid')
    self_v = s[OTHER_AXES].values
    part_v = p[OTHER_AXES].values
    valid = ~np.isnan(self_v).any(axis=1) & ~np.isnan(part_v).any(axis=1)
    out = pd.DataFrame({'cid': s['cid'].values, 't': s['t'].values, 'etype': etype})
    for j, a in enumerate(OTHER_AXES):
        out[a] = np.abs(self_v[:, j] - part_v[:, j])
    return out[valid]


def robust_f_per_axis(df, axes, floor=SCALE_FLOOR, floor_rel=0.0, return_scale=False):
    """per (cid, axis) full-history robust_z = clip((val−med)/max(MAD,floor_a), ±Z)。n<K_MIN は f=0。
    floor_a = MAD 下限。floor_rel>0 なら軸ごと floor_a = floor_rel·(その軸の全体 MAD)
    (各軸の固有スケールに比例＝低スケール軸を黙らせず clip 飽和だけ防ぐ)。else 絶対 floor。"""
    f = pd.DataFrame(index=df.index)
    scale = {}
    for a in axes:
        med = df.groupby('cid')[a].transform('median')
        mad = df.groupby('cid')[a].transform(lambda x: np.median(np.abs(x - np.median(x))) * MAD_C)
        n = df.groupby('cid')[a].transform('size')
        gm = float(np.median(np.abs(df[a] - np.median(df[a]))) * MAD_C)  # 全体 MAD
        scale[a] = gm
        floor_a = max(floor_rel * gm, SCALE_FLOOR) if floor_rel > 0 else floor
        z = (df[a] - med) / mad.clip(lower=floor_a)
        z = z.clip(-Z_CLIP, Z_CLIP)
        z = z.where(n >= K_MIN, 0.0)
        f[a] = z
    return (f, scale) if return_scale else f


def build_event_arrays(self_df, self_f, enc_df, enc_f):
    """per (seed,cid) に time 順の F 行列 (n_events × 7, 触らない軸は NaN) を作る。"""
    n_ax = len(AXES)
    # self: SELF 軸に f、OTHER は NaN
    S = pd.DataFrame({'seed': self_df['seed'].values, 'cid': self_df['cid'].values,
                      't': self_df['t'].values})
    for j, a in enumerate(AXES):
        S[j] = self_f[a].values if a in SELF_AXES else np.nan
    # enc: OTHER 軸に f、SELF は NaN
    E = pd.DataFrame({'seed': enc_df['seed'].values, 'cid': enc_df['cid'].values,
                      't': enc_df['t'].values})
    for j, a in enumerate(AXES):
        E[j] = enc_f[a].values if a in OTHER_AXES else np.nan
    allev = pd.concat([S, E], ignore_index=True).sort_values(['seed', 'cid', 't'])
    arrays = {}
    for (seed, cid), sub in allev.groupby(['seed', 'cid']):
        arrays[(seed, cid)] = sub[list(range(n_ax))].values.astype(np.float64)
    return arrays


def propagate(F, alpha, lam):
    """1 CID の event 列 F (n×7, NaN=触らない) を (α,λ) で伝播。
    返り値: 最終 rate, 系列中の最大 log10|rate| (swing 振幅), died flag。"""
    r = np.ones(len(AXES))
    maxabs = 1.0
    died = False
    for row in F:
        r = 1.0 + (r - 1.0) * lam            # 全軸 decay
        m = ~np.isnan(row)
        if m.any():
            r[m] = r[m] * np.clip(1.0 + alpha * row[m], 0.1, None)
        cur = np.max(np.abs(r))
        if not np.isfinite(cur):
            died = True; maxabs = np.inf; break
        if cur > maxabs:
            maxabs = cur
        if maxabs > OVERFLOW:
            died = True; break
    maxlog10 = np.inf if died else float(np.log10(max(maxabs, 1.0)))
    return r, maxlog10, died


def _build_arrays_with_floor(self_df, enc_df, floor=SCALE_FLOOR, floor_rel=0.0):
    self_f = robust_f_per_axis(self_df, SELF_AXES, floor=floor, floor_rel=floor_rel)
    enc_f = robust_f_per_axis(enc_df, OTHER_AXES, floor=floor, floor_rel=floor_rel)
    return build_event_arrays(self_df, self_f, enc_df, enc_f)


def _metrics(arrays, alpha, lam):
    finals = []; swings = []; deaths = 0; stress = 0
    for F in arrays.values():
        r, mlog, died = propagate(F, alpha, lam)
        swings.append(mlog)
        if died or mlog > DEAD_LOG10:
            deaths += 1
        else:
            finals.append(r)
            if mlog > STRESS_LOG10:
                stress += 1
    n = len(arrays)
    finals = np.array(finals) if finals else np.zeros((0, len(AXES)))
    sw = np.array(swings, float); fsw = sw[np.isfinite(sw)]
    out = dict(dead=deaths / n, stress=stress / n,
               sw50=float(np.percentile(fsw, 50)) if len(fsw) else np.inf,
               sw99=float(np.percentile(fsw, 99)) if len(fsw) else np.inf)
    if len(finals) > 3:
        logr = np.log10(np.clip(np.abs(finals), 1e-12, 1e12))
        prof = logr - logr.mean(axis=1, keepdims=True)
        out['diversity'] = float(prof.std(axis=0).mean())
        dom = np.argmax(logr, axis=1)
        counts = np.bincount(dom, minlength=len(AXES)) / len(dom)
        out['dom_entropy'] = float(-np.sum([c * np.log2(c) for c in counts if c > 0]))
        sl = logr[:, SELF_IDX].mean(1); ol = logr[:, OTHER_IDX].mean(1)
        out['sep'] = float(pearsonr(sl, ol)[0]) if sl.std() > 0 and ol.std() > 0 else np.nan
    else:
        out.update(diversity=np.nan, dom_entropy=np.nan, sep=np.nan)
    return out


def main_floorsweep(seeds):
    """MAD floor を sweep。裾(sw99/stress/dead)を潰しつつ個性(dom_entropy/diversity)を殺さない値を探す。
    live 起点 α=0.5、λ∈{1.0,0.99} で測る。"""
    print(f'=== M5 MAD floor sweep — seeds={seeds} (新 run なし、live 前の技術線) ===\n')
    sps, eps = [], []
    for seed in seeds:
        st = load_state(seed)
        sv = self_axis_values(st); sv['seed'] = seed
        ev = encounter_axis_values(seed, st); ev['seed'] = seed
        sps.append(sv); eps.append(ev)
    self_df = pd.concat(sps, ignore_index=True)
    enc_df = pd.concat(eps, ignore_index=True)
    _, sscale = robust_f_per_axis(self_df, SELF_AXES, return_scale=True)
    _, oscale = robust_f_per_axis(enc_df, OTHER_AXES, return_scale=True)
    print('  値の全体 MAD (floor の目安): SELF ' +
          ', '.join(f'{a}={sscale[a]:.3f}' for a in SELF_AXES))
    print('                               OTHER ' +
          ', '.join(f'{a}={oscale[a]:.3f}' for a in OTHER_AXES))
    print(f'  self events={len(self_df)}, encounter={len(enc_df)}\n')

    ALPHA = 0.5
    grid = {}
    # 軸ごと固有スケールに比例した floor (floor_rel · 全体 MAD)。低スケール軸を黙らせない。
    RELS = [0.0, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 50.0]
    print('  per-axis 相対 floor (floor_rel · その軸の全体 MAD):')
    print(f'{"rel":>6s} {"λ":>5s} {"dead%":>6s} {"stress%":>8s} {"sw_p50":>7s} {"sw_p99":>8s} '
          f'{"divers":>7s} {"domEntr":>8s} {"sep":>6s}')
    for rel in RELS:
        arrays = _build_arrays_with_floor(self_df, enc_df, floor=SCALE_FLOOR, floor_rel=rel)
        for lam in [1.0, 0.99]:
            m = _metrics(arrays, ALPHA, lam)
            grid[f'rel{rel}_l{lam}'] = dict(floor_rel=rel, alpha=ALPHA, lam=lam, **m)
            tag = 'none' if rel == 0 else f'{rel:.0f}x'
            print(f'{tag:>6s} {lam:>5.2f} {100*m["dead"]:>5.1f}% {100*m["stress"]:>7.1f}% '
                  f'{m["sw50"]:>7.2f} {m["sw99"]:>8.2f} {m["diversity"]:>7.2f} '
                  f'{m["dom_entropy"]:>8.2f} {m["sep"]:>6.2f}')
    (OUT / 'mad_floor_sweep.json').write_text(json.dumps(
        {'seeds': seeds, 'alpha': ALPHA, 'value_scale': {'SELF': sscale, 'OTHER': oscale},
         'floor_rels': RELS, 'grid': grid}, indent=2, ensure_ascii=False))
    print(f'\n保存: {OUT/"mad_floor_sweep.json"}')
    print('  狙い: sw_p99 を θ 生存域 (低い) に、dom_entropy/divers は維持 (個性を殺さない)')
    print('=== floor 当たり付け 完了 ===')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    seeds = [int(s) for s in args] if args else list(range(24))
    if '--floorsweep' in sys.argv:
        main_floorsweep(seeds)
        return
    print(f'=== M5 種類分け+衰退 post-process — seeds={seeds} (新 run なし) ===\n')

    sps, eps = [], []
    for seed in seeds:
        st = load_state(seed)
        sv = self_axis_values(st); sv['seed'] = seed
        ev = encounter_axis_values(seed, st); ev['seed'] = seed
        sps.append(sv); eps.append(ev)
    self_df = pd.concat(sps, ignore_index=True)
    enc_df = pd.concat(eps, ignore_index=True)
    print(f'  self events={len(self_df)}, encounter events={len(enc_df)} '
          f'(E3={int((enc_df.etype=="E3_contact").sum())}, ing={int((enc_df.etype=="ingestion").sum())})')

    # robust_z f を per cid-axis で precompute (α,λ 非依存)
    self_f = robust_f_per_axis(self_df, SELF_AXES)
    enc_f = robust_f_per_axis(enc_df, OTHER_AXES)
    arrays = build_event_arrays(self_df, self_f, enc_df, enc_f)
    print(f'  CIDs (seed,cid) total: {len(arrays)}\n')

    grid = {}
    print('  swing振幅 = 系列中の最大 log10(rate)。stress=>1e6, dead(inf)=>1e300。')
    print(f'{"α":>5s} {"λ":>5s} {"dead%":>6s} {"stress%":>8s} {"swing_p50":>9s} {"swing_p99":>9s} '
          f'{"self/oth":>9s} {"sep":>7s} {"divers":>7s} {"dom=SELF%":>9s} {"domEntr":>8s}')
    for alpha in ALPHAS:
        for lam in LAMBDAS:
            finals = []; swings = []; deaths = 0; stress = 0
            for key, F in arrays.items():
                r, mlog, died = propagate(F, alpha, lam)
                swings.append(mlog)
                if died or mlog > DEAD_LOG10:
                    deaths += 1
                else:
                    finals.append(r)
                    if mlog > STRESS_LOG10:
                        stress += 1
            finals = np.array(finals) if finals else np.zeros((0, len(AXES)))
            swings = np.array(swings, dtype=float)
            n = len(arrays)
            death_frac = deaths / n
            stress_frac = stress / n
            finite_sw = swings[np.isfinite(swings)]
            sw_p50 = float(np.percentile(finite_sw, 50)) if len(finite_sw) else float('inf')
            sw_p99 = float(np.percentile(finite_sw, 99)) if len(finite_sw) else float('inf')
            if len(finals) > 3:
                logr = np.log10(np.clip(np.abs(finals), 1e-12, 1e12))  # 表示安定化
                # ① 別軸に効くか: SELF vs OTHER の log-rate を CID 間で相関 (低=独立)
                self_log = logr[:, SELF_IDX].mean(axis=1)
                other_log = logr[:, OTHER_IDX].mean(axis=1)
                sep = float(pearsonr(self_log, other_log)[0]) if self_log.std() > 0 and other_log.std() > 0 else float('nan')
                # 自己/出会い の swing 大きさ比 (1 付近 = commensurate、別軸で埋もれない)
                so = float(np.median(np.abs(logr[:, SELF_IDX])) / max(np.median(np.abs(logr[:, OTHER_IDX])), 1e-9))
                # ② 個性: CID 内中心化した log プロファイルの軸別 CID 間 std (bounded)
                prof = logr - logr.mean(axis=1, keepdims=True)
                diversity = float(prof.std(axis=0).mean())
                # 支配軸 (argmax) の分布: SELF が dom の割合 + entropy (個性の散らばり)
                dom = np.argmax(logr, axis=1)
                dom_self = float(np.mean(np.isin(dom, SELF_IDX)))
                counts = np.bincount(dom, minlength=len(AXES)) / len(dom)
                dom_entropy = float(-np.sum([c*np.log2(c) for c in counts if c > 0]))
            else:
                sep = so = diversity = dom_self = dom_entropy = float('nan')
            grid[f'a{alpha}_l{lam}'] = dict(
                alpha=alpha, lam=lam, death_frac=death_frac, stress_frac=stress_frac,
                swing_p50=sw_p50, swing_p99=sw_p99, self_over_other=so, sep_corr=sep,
                diversity=diversity, dominant_is_self_frac=dom_self,
                dominant_axis_entropy=dom_entropy, n_survived=len(finals))
            print(f'{alpha:>5.1f} {lam:>5.2f} {100*death_frac:>5.1f}% {100*stress_frac:>7.1f}% '
                  f'{sw_p50:>9.2f} {sw_p99:>9.2f} {so:>9.2f} {sep:>7.2f} {diversity:>7.2f} '
                  f'{100*dom_self:>8.0f}% {dom_entropy:>8.2f}')

    (OUT / 'typesplit_decay.json').write_text(json.dumps(
        {'seeds': seeds, 'axis_partition': {'SELF': SELF_AXES, 'OTHER': OTHER_AXES},
         'grid': grid, 'params': dict(K_MIN=K_MIN, Z_CLIP=Z_CLIP, STRESS_LOG10=STRESS_LOG10,
                                      DEAD_LOG10=DEAD_LOG10, alphas=ALPHAS, lambdas=LAMBDAS)},
        indent=2, ensure_ascii=False))
    print(f'\n保存: {OUT/"typesplit_decay.json"}')
    print('  ③ dead% = rate が inf に発散 (記録が死ぬ域の代理、θ NaN の上流)')
    print('  ① sep≈0 = 自己軸と他者軸が独立 / self/oth≈1 = 別軸で埋もれない (累積 bound 不要)')
    print('  ② divers 高・domEntr 高 = 個性が分かれる (どの軸が伸びるかが CID で違う)')
    print('=== 完了 (live は α,λ 確定後) ===')


if __name__ == '__main__':
    main()
