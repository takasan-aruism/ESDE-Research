#!/usr/bin/env python3
"""v12 Taka案 課題#1 — 一致率の時間更新で「何が拾えるか」(dump のみ)

## 自己規律 (Code A)
①過去引用: #30(接地・Ghost二役=死後もスロットが観測者/食料の二役、死は大変化のはず)、m19(4粒度の
  per-(cid,t) rank_1_atom+rank_1_sim 在: event~50step/pulse/step10 10step/window 500step)、
  source_events の birth_step/host_lost_step/reaped_step/final_state(step単位 死判定)。
②Taka逐語(原文): 「ESDE Atom にどんな多様性が生まれ、センターが拾えるか」「誕生/Q奪取/Integration は
  個性的イベントのはず」「閾値を決めない・網を組まない・センター接続しない・CID投影しない」
  「大きく見る/安く見るの両方を Taka が見られる形」.
③判定はTaka(success/fail置かない) ④集約語なし.

## 範囲: 4粒度の一致率時系列から「どんな変化が拾えるか」を観察事実で出すだけ。
  閾値を決めない・網を組まない・センター接続しない・CID投影しない。物理書込ゼロ.
## 一方向: 読=frozen(v106 trajectory/source_events), 書=cid_trajectory_probe/ のみ.
"""
import sys, json, time
from pathlib import Path
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

REPO = Path('/home/takasan/esde/ESDE-Research')
TRAJ = REPO / 'developmental/v106/outputs/main'
SE_DIR = REPO / 'developmental/v107/outputs/main'
OUT_DIR = REPO / 'unified/v1201/cid_trajectory_probe'
OUT_DIR.mkdir(parents=True, exist_ok=True)
SEEDS = list(range(24))
GRAINS = {'event': ('event_trajectory', 'event_cid_alignment'),
          'pulse': ('pulse_trajectory', 'pulse_cid_alignment'),
          'step10': ('step10_trajectory', 'step10_cid_alignment'),
          'window': ('window_trajectory', 'window_cid_alignment')}


def death_info(seed):
    """source_events から per-cid の birth/host_lost/reaped step + final_state (step単位 死判定)。"""
    se = pd.read_parquet(SE_DIR / f'source_events_seed{seed}.parquet')
    d = se.groupby('source_cid').agg(birth_step=('birth_step', 'first'),
                                     host_lost_step=('host_lost_step', 'first'),
                                     reaped_step=('reaped_step', 'first'),
                                     final_state=('final_state', 'first')).reset_index()
    d = d.rename(columns={'source_cid': 'cognitive_id'})
    return d


TIME_COL = {'event': 't', 'pulse': 't', 'step10': 't', 'window': 'step_at_window_end'}


def load_grain(grain, seed):
    sub, fn = GRAINS[grain]
    p = TRAJ / sub / f'{fn}_seed{seed}.csv'
    if not p.exists():
        return None
    df = pd.read_csv(p)
    tc = TIME_COL[grain]
    if tc != 't':
        df = df.rename(columns={tc: 't'})   # 時間列を 't' に標準化 (window=step_at_window_end)
    df['seed'] = seed
    return df


def process_grain(grain):
    t0 = time.time()
    dsim_alive, dsim_ghost = [], []
    sw_alive = [0, 0]; sw_ghost = [0, 0]   # [switch, total]
    trans_dsim = []                         # alive→ghost 遷移の Δsim
    bd_incl, bd_excl = [], []               # 生死含む/除く Δsim
    top_rows = []                           # 大跳ね候補 (|dsim| 上位)
    n_rows = 0
    for seed in SEEDS:
        df = load_grain(grain, seed)
        if df is None or df.empty:
            continue
        df = df.sort_values(['cognitive_id', 't']).reset_index(drop=True)
        di = death_info(seed)
        df = df.merge(di, on='cognitive_id', how='left')
        g = df.groupby('cognitive_id')
        df['dsim'] = g['rank_1_sim'].diff()
        df['t_prev'] = g['t'].shift()
        df['switch'] = (g['rank_1_atom'].shift() != df['rank_1_atom']) & df['t_prev'].notna()
        # Ghost 判定 (#30): host_lost_step 以降を ghost (死後スロット), それ未満 alive
        hl = df['host_lost_step']
        df['is_ghost'] = hl.notna() & (df['t'] >= hl)
        # alive→ghost 遷移行 (前 alive, 当 ghost)
        df['prev_ghost'] = g['is_ghost'].shift()
        df['is_transition'] = (df['is_ghost']) & (df['prev_ghost'] == False)
        # 生死行 (誕生=最初の行 / 死=host_lost or reaped 近傍)
        df['is_birth'] = df['t_prev'].isna()
        rb = df['reaped_step']
        df['is_death'] = ((hl.notna() & (df['t'] >= hl) & (df['t_prev'] < hl)) |
                          (rb.notna() & (df['t'] >= rb) & (df['t_prev'] < rb)))
        d = df.dropna(subset=['dsim'])
        n_rows += len(df)
        dsim_alive.append(d.loc[~d['is_ghost'], 'dsim'].values)
        dsim_ghost.append(d.loc[d['is_ghost'], 'dsim'].values)
        sw = d[~d['is_ghost']]; sw_alive[0] += int(sw['switch'].sum()); sw_alive[1] += len(sw)
        swg = d[d['is_ghost']]; sw_ghost[0] += int(swg['switch'].sum()); sw_ghost[1] += len(swg)
        trans_dsim.append(d.loc[d['is_transition'], 'dsim'].values)
        bd_incl.append(d['dsim'].values)
        bd_excl.append(d.loc[~(d['is_birth'] | d['is_death']), 'dsim'].values)
        # 大跳ね候補: |dsim| 上位 (seed ごと上位200を貯め最後に再選抜)
        dd = d.reindex(d['dsim'].abs().sort_values(ascending=False).index).head(200)
        cols = ['seed', 'cognitive_id', 't', 't_prev', 'dsim', 'rank_1_sim', 'rank_1_atom',
                'is_ghost', 'is_transition', 'is_birth', 'is_death']
        if 'source' in dd.columns:
            cols.append('source')
        top_rows.append(dd[cols])
    A = np.concatenate(dsim_alive) if dsim_alive else np.array([])
    G = np.concatenate(dsim_ghost) if dsim_ghost else np.array([])
    T = np.concatenate(trans_dsim) if trans_dsim else np.array([])
    BI = np.concatenate(bd_incl) if bd_incl else np.array([])
    BE = np.concatenate(bd_excl) if bd_excl else np.array([])
    top = pd.concat(top_rows, ignore_index=True) if top_rows else pd.DataFrame()
    top = top.reindex(top['dsim'].abs().sort_values(ascending=False).index).head(300) if len(top) else top

    def q(x):
        if len(x) == 0:
            return {}
        return {f'p{p}': round(float(np.percentile(x, p)), 4) for p in [1, 5, 25, 50, 75, 95, 99]}
    rep = {
        'grain': grain, 'n_rows': int(n_rows),
        'dsim_alive': {'n': int(len(A)), 'abs_mean': round(float(np.abs(A).mean()), 4) if len(A) else None, **q(A)},
        'dsim_ghost': {'n': int(len(G)), 'abs_mean': round(float(np.abs(G).mean()), 4) if len(G) else None, **q(G)},
        'atom_switch_rate_alive': round(sw_alive[0] / max(sw_alive[1], 1), 4),
        'atom_switch_rate_ghost': round(sw_ghost[0] / max(sw_ghost[1], 1), 4),
        'transition_dsim': {'n': int(len(T)), 'abs_mean': round(float(np.abs(T).mean()), 4) if len(T) else None, **q(T)},
        'dsim_birthdeath_incl': {'n': int(len(BI)), 'abs_mean': round(float(np.abs(BI).mean()), 4) if len(BI) else None},
        'dsim_birthdeath_excl': {'n': int(len(BE)), 'abs_mean': round(float(np.abs(BE).mean()), 4) if len(BE) else None},
        'elapsed_s': round(time.time() - t0, 1),
    }
    # 大跳ね×演算イベント対応 (event は source 内蔵, 他は source_events を (cid, t_prev<ts<=t) で join)
    if len(top):
        if 'source' not in top.columns:
            top['source'] = _join_events(top)
        top.to_parquet(OUT_DIR / f'top_jumps_{grain}.parquet', index=False)
        # source 種別の集計 (上位300 の大跳ねに居た演算イベント)
        rep['top_jump_source_counts'] = _src_counts(top['source'])
        rep['top_jump_ghost_frac'] = round(float(top['is_ghost'].mean()), 3)
        rep['top_jump_birthdeath_frac'] = round(float((top['is_birth'] | top['is_death']).mean()), 3)
    return rep


def _join_events(top):
    out = []
    cache = {}
    for r in top.itertuples():
        if r.seed not in cache:
            cache[r.seed] = pd.read_parquet(SE_DIR / f'source_events_seed{r.seed}.parquet')
        se = cache[r.seed]
        tp = -1 if pd.isna(r.t_prev) else r.t_prev
        m = se[(se.source_cid == r.cognitive_id) & (se.timestamp > tp) & (se.timestamp <= r.t)]
        out.append('|'.join(sorted(m.event_source_type.unique())) if len(m) else 'none')
    return out


def _src_counts(s):
    from collections import Counter
    c = Counter()
    for v in s.fillna('none'):
        for tok in str(v).split('|'):
            c[tok] += 1
    return dict(c.most_common())


def main():
    grains = sys.argv[1:] if len(sys.argv) > 1 else list(GRAINS)
    reps = []
    for grain in grains:
        rep = process_grain(grain)
        reps.append(rep)
        print(f"--- {grain} (n_rows={rep['n_rows']}, {rep['elapsed_s']}s) ---")
        print(f"  Δsim alive: |mean|={rep['dsim_alive']['abs_mean']} p50={rep['dsim_alive'].get('p50')} p95={rep['dsim_alive'].get('p95')} p99={rep['dsim_alive'].get('p99')} (n={rep['dsim_alive']['n']})")
        print(f"  Δsim ghost: |mean|={rep['dsim_ghost']['abs_mean']} p95={rep['dsim_ghost'].get('p95')} (n={rep['dsim_ghost']['n']})")
        print(f"  atom切替率 alive={rep['atom_switch_rate_alive']} ghost={rep['atom_switch_rate_ghost']}")
        print(f"  遷移(alive→ghost) Δsim: |mean|={rep['transition_dsim']['abs_mean']} (n={rep['transition_dsim']['n']})")
        print(f"  生死 incl |mean|={rep['dsim_birthdeath_incl']['abs_mean']} / excl |mean|={rep['dsim_birthdeath_excl']['abs_mean']}")
        if 'top_jump_source_counts' in rep:
            print(f"  大跳ね上位300 の演算イベント: {rep['top_jump_source_counts']}")
            print(f"    うち ghost={rep['top_jump_ghost_frac']} birth/death={rep['top_jump_birthdeath_frac']}")
        print()
    (OUT_DIR / 'probe_summary.json').write_text(json.dumps(reps, indent=2, ensure_ascii=False))
    print('保存: cid_trajectory_probe/probe_summary.json + top_jumps_*.parquet')


if __name__ == '__main__':
    main()
