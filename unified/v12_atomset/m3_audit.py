#!/usr/bin/env python3
"""v12 M3 — first-divergence 監査 + per-CID 個性化/寡占 判定 (既存出力のみ、再 run なし)

GPT/Web Claude 指摘の検証:
- CID 数でなく「残った CID 間の差」「消えた CID の死因」で個性化 vs 寡占を判定する。
- 分岐前は同一世界なので、誕生が一致する CID (matched) の「その後の運命」を off/small/medium で
  並べて比較する (final_state / 寿命 / phase coherence / territory / θ drift)。
- 最終行比較でなく first-divergence を追う (audit_event / link_life の共通 prefix を整列)。
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

DIAG = {c: Path(f'/tmp/v12_m3_smoke_{c}_seed0/diag_v105_v12_m3_smoke_{c}_seed0')
        for c in ('off', 'small', 'medium')}
OUT = Path('/home/takasan/esde/ESDE-Research/unified/v12_atomset/run_m3_smoke/audit.json')

def load_subj(c):
    return pd.read_csv(DIAG[c] / 'subjects/per_subject_seed0.csv')

def lifespan(row):
    b = row['birth_window']
    h = row['host_lost_window']
    end = 5  # mat2+track3 = total 5 windows
    last = h if pd.notna(h) else end
    return last - b

report = {}

# ── 1. birth / death / ghost 分離 ──
print('=== (1) birth/death/ghost 分離 (count でなく内訳) ===')
counts = {}
for c in ('off', 'small', 'medium'):
    df = load_subj(c)
    n = len(df)
    hosted = int((df['final_state'] == 'hosted').sum())
    ghost = int((df['final_state'] == 'ghost').sum())
    ghost_dur = df.loc[df['final_state'] == 'ghost', 'ghost_duration_steps']
    counts[c] = {
        'n_cid_total_born': n, 'hosted_at_end': hosted, 'ghosted': ghost,
        'ghost_dur_mean': round(float(ghost_dur.mean()), 1) if len(ghost_dur) else None,
        'ghost_dur_max': int(ghost_dur.max()) if len(ghost_dur) else None,
    }
    print(f'  {c:7s}: born={n}, hosted={hosted}, ghost={ghost}, '
          f'ghost_dur mean={counts[c]["ghost_dur_mean"]} max={counts[c]["ghost_dur_max"]}')
report['birth_death_split'] = counts

# ── 2. matched CID (分岐前に誕生、3 条件共通) の運命比較 ──
print('\n=== (2) matched CID の運命 (誕生一致 → その後が torque で変わったか) ===')
subj = {c: load_subj(c).set_index('cognitive_id') for c in ('off', 'small', 'medium')}
common = sorted(set(subj['off'].index) & set(subj['small'].index) & set(subj['medium'].index))
print(f'  3 条件共通 CID (分岐前誕生): {common}')
report['matched_cids'] = common

FATE_COLS = {
    'birth_window': 'birth_w', 'host_lost_window': 'hostlost_w', 'final_state': 'state',
    'v11_m_c_n_core': 'n_core', 'v18_v_unified_concentration_final': 'coherence',
    'v18_theta_distance_from_birth_final': 'theta_drift', 'last_familiarity_max': 'famil',
    'last_n_partners': 'partners', 'v10_pulse_count': 'pulses', 'C_at_run_end': 'C',
}
matched_rows = []
for cid in common:
    rec = {'cid': cid}
    for c in ('off', 'small', 'medium'):
        r = subj[c].loc[cid]
        rec[f'{c}_state'] = r['final_state']
        rec[f'{c}_life'] = lifespan(r)
        rec[f'{c}_coher'] = round(float(r.get('v18_v_unified_concentration_final', np.nan)), 4)
        rec[f'{c}_famil'] = round(float(r.get('last_familiarity_max', np.nan)), 3)
        rec[f'{c}_pulses'] = int(r.get('v10_pulse_count', 0)) if pd.notna(r.get('v10_pulse_count')) else 0
    matched_rows.append(rec)
mdf = pd.DataFrame(matched_rows)
# fate が条件間で変わった matched CID を強調
changed = []
for _, r in mdf.iterrows():
    states = {r['off_state'], r['small_state'], r['medium_state']}
    lives = {r['off_life'], r['small_life'], r['medium_life']}
    if len(states) > 1 or len(lives) > 1:
        changed.append(int(r['cid']))
print(mdf.to_string(index=False))
print(f'\n  → 運命 (state/寿命) が条件間で変わった matched CID: {changed}')
report['matched_fate_changed'] = changed
report['matched_table'] = mdf.to_dict(orient='records')

# ── 3. 多様性指標 (残った CID 間の差) ──
print('\n=== (3) CID 間多様性 (個性化なら多様性維持/増、寡占なら少数支配・多様性減) ===')
div = {}
for c in ('off', 'small', 'medium'):
    df = load_subj(c)
    lifes = df.apply(lifespan, axis=1)
    coher = df['v18_v_unified_concentration_final'].dropna()
    famil = df['last_familiarity_max'].dropna()
    pulses = df['v10_pulse_count'].dropna()
    div[c] = {
        'n_cid': len(df),
        'life_mean': round(float(lifes.mean()), 2), 'life_std': round(float(lifes.std()), 2),
        'coher_mean': round(float(coher.mean()), 4), 'coher_std': round(float(coher.std()), 4),
        'famil_mean': round(float(famil.mean()), 3), 'famil_std': round(float(famil.std()), 3),
        'pulse_mean': round(float(pulses.mean()), 1), 'pulse_max': int(pulses.max()) if len(pulses) else 0,
        'pulse_gini': None,
    }
    # pulse の Gini (寡占度: 少数 CID が活動を独占しているか)
    pv = np.sort(pulses.values.astype(float))
    if len(pv) and pv.sum() > 0:
        nn = len(pv); cum = np.cumsum(pv)
        gini = (nn + 1 - 2 * (cum.sum() / cum[-1])) / nn
        div[c]['pulse_gini'] = round(float(gini), 4)
    d = div[c]
    print(f'  {c:7s}: n={d["n_cid"]} | life {d["life_mean"]}±{d["life_std"]} | '
          f'coher {d["coher_mean"]}±{d["coher_std"]} | famil {d["famil_mean"]}±{d["famil_std"]} | '
          f'pulse mean={d["pulse_mean"]} max={d["pulse_max"]} gini={d["pulse_gini"]}')
report['diversity'] = div

# ── 4. first-divergence (audit_event / link_life の共通 prefix) ──
print('\n=== (4) first-divergence 追跡 (最終行でなく分岐点) ===')
fd = {}
for other in ('small', 'medium'):
    ev_o = pd.read_csv(DIAG['off'] / 'audit/per_event_audit_seed0.csv')
    ev_x = pd.read_csv(DIAG[other] / 'audit/per_event_audit_seed0.csv')
    cols = ['window', 'step', 'cid', 'v14_event_type', 'link_id']
    n = min(len(ev_o), len(ev_x))
    first = None
    for i in range(n):
        a = tuple(ev_o.iloc[i][cols]); b = tuple(ev_x.iloc[i][cols])
        if a != b:
            first = {'row': i, 'off': [str(x) for x in a], other: [str(x) for x in b]}
            break
    # link_life: birth_step 昇順で整列、最初に差が出る link
    ll_o = pd.read_csv(DIAG['off'] / 'persistence/link_life_log_seed0.csv')
    ll_x = pd.read_csv(DIAG[other] / 'persistence/link_life_log_seed0.csv')
    keyc = ['link_id', 'birth_step', 'death_step', 'lifetime_steps']
    so = ll_o[keyc].sort_values(['birth_step', 'link_id']).reset_index(drop=True)
    sx = ll_x[keyc].sort_values(['birth_step', 'link_id']).reset_index(drop=True)
    m = min(len(so), len(sx))
    first_link = None
    for i in range(m):
        if not so.iloc[i].equals(sx.iloc[i]):
            first_link = {'row': i, 'off': so.iloc[i].to_dict(), other: sx.iloc[i].to_dict()}
            for k in ('off', other):
                first_link[k] = {kk: (int(vv) if isinstance(vv, (np.integer,)) else str(vv))
                                 for kk, vv in first_link[k].items()}
            break
    fd[other] = {'first_audit_event': first, 'first_link_divergence': first_link,
                 'audit_identical_rows': (first['row'] if first else n)}
    print(f'  off vs {other}:')
    print(f'    audit_event 共通 prefix {fd[other]["audit_identical_rows"]} 行、最初の差: {first}')
    print(f'    link_life 最初の差 (birth_step 整列): {first_link}')
report['first_divergence'] = fd

OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str))
print(f'\n保存: {OUT}')
