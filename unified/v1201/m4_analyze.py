#!/usr/bin/env python3
"""v12 M4 — first-divergence + per-CID 機構監査の解析

off vs small の計装出力から:
 (1) θ md5 を step で diff → θ が最初に分岐する step を確定
 (2) その直前の vl.step の bonus 対象 (factor>1) label territory を出し、
     M3 で特定済の first-divergence link (1335,2701) の node が territory に属すか確認
 (3) per-cid: bonus 対象か否か × 運命 (state/寿命/coherence/θdrift)、matched cid を off/small 比較
 (4) 多様性 (bonus 対象 vs 非対象、survivor) + 消えた CID の死因
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path('/home/takasan/esde/ESDE-Research/unified/v1201')
RUN = ROOT / 'run_m4'
OUT = RUN / 'analysis.json'
FIRST_DIV_LINK = (1335, 2701)  # M3 audit で特定
DIAG = {c: Path(f'/tmp/v12_m4_{c}_seed0/diag_v105_v12_m4_{c}_seed0') for c in ('off', 'small')}
M3DIAG = {c: Path(f'/tmp/v12_m3_smoke_{c}_seed0/diag_v105_v12_m3_smoke_{c}_seed0') for c in ('off', 'small')}

report = {}

# ── 0. 計装が read-only (m4 ≡ m3) の sanity ──
print('=== (0) 計装 read-only sanity: m4 off per_subject ≡ m3 off ===')
try:
    a = pd.read_csv(DIAG['off'] / 'subjects/per_subject_seed0.csv')
    b = pd.read_csv(M3DIAG['off'] / 'subjects/per_subject_seed0.csv')
    same = a.shape == b.shape and (a.fillna(-9).astype(str).values == b.fillna(-9).astype(str).values).all()
    print(f'  m4 off shape {a.shape} vs m3 off {b.shape}: {"✓ 一致 (計装は無害)" if same else "✗ 不一致"}')
    report['m4_eq_m3_off'] = bool(same)
except Exception as e:
    print(f'  skip: {e}'); report['m4_eq_m3_off'] = None

# ── 1. θ first-divergence step ──
print('\n=== (1) θ md5 first-divergence (off vs small) ===')
co = pd.read_csv(RUN / 'off/theta_checksums.csv')
cs = pd.read_csv(RUN / 'small/theta_checksums.csv')
m = min(len(co), len(cs))
first_step = None
for i in range(m):
    if co.iloc[i]['theta_md5'] != cs.iloc[i]['theta_md5']:
        first_step = int(co.iloc[i]['step']); break
total = len(co)
# window 推定: maturation 2*500 + tracking window k*500
print(f'  off steps={len(co)}, small steps={len(cs)}')
if first_step is not None:
    win = first_step / 500.0
    print(f'  最初に θ が分岐する step = {first_step} (≈ window {win:.2f}; mat=2×500 後 tracking)')
else:
    print(f'  共通 {m} step すべて θ md5 一致 (分岐なし?)')
report['theta_first_divergence_step'] = first_step
report['theta_steps_total'] = total

# ── 2. 分岐直前の bonus territory & first-divergence link ──
print('\n=== (2) bonus 対象 territory と first-divergence link 照合 ===')
snap_s = json.loads((RUN / 'small/label_window_snapshot.json').read_text())
# factor>1 が初めて出る window
windows = sorted(int(w) for w in snap_s.keys())
first_factor_win = None
for w in windows:
    if any(e['factor'] > 1.0 for e in snap_s[str(w)]):
        first_factor_win = w; break
print(f'  small で factor>1 が初出する vl.step window = {first_factor_win}')
territory_union = set()
bonus_labels_info = []
if first_factor_win is not None:
    for e in snap_s[str(first_factor_win)]:
        if e['factor'] > 1.0:
            territory_union |= set(e['nodes'])
            bonus_labels_info.append({'lid': e['lid'], 'cid': e['cid'],
                                      'factor': round(e['factor'], 4), 'n_nodes': len(e['nodes'])})
    print(f'  その window の bonus 対象 label: {bonus_labels_info}')
    print(f'  bonus territory node 数 (union): {len(territory_union)}')
n1, n2 = FIRST_DIV_LINK
in1, in2 = n1 in territory_union, n2 in territory_union
print(f'  first-divergence link {FIRST_DIV_LINK}: node {n1}∈territory={in1}, node {n2}∈territory={in2}')
# territory に隣接する link か (どちらか一方でも territory なら torque の波及先)
verdict_link = '両 node とも bonus territory' if (in1 and in2) else \
               ('片 node が bonus territory (gravity 波及先)' if (in1 or in2) else '両 node とも territory 外')
print(f'  → first-divergence link は: {verdict_link}')
report['first_factor_window'] = first_factor_win
report['bonus_labels_at_first_factor'] = bonus_labels_info
report['firstdiv_link_in_territory'] = {'node1': int(n1), 'in1': bool(in1),
                                        'node2': int(n2), 'in2': bool(in2), 'verdict': verdict_link}

# ── 3. per-cid: bonus 対象 × 運命 (matched cid を off/small 比較) ──
print('\n=== (3) per-cid: bonus 対象 × 運命 (matched cid) ===')
def load_fate(c):
    df = pd.read_csv(DIAG[c] / 'subjects/per_subject_seed0.csv')
    df = df.set_index('cognitive_id')
    end = 5
    out = {}
    for cid, r in df.iterrows():
        last = r['host_lost_window'] if pd.notna(r['host_lost_window']) else end
        out[int(cid)] = {
            'state': r['final_state'], 'life': float(last - r['birth_window']),
            'coher': round(float(r.get('v18_v_unified_concentration_final', np.nan)), 4),
            'drift': round(float(r.get('v18_theta_distance_from_birth_final', np.nan)), 4),
            'famil': round(float(r.get('last_familiarity_max', np.nan)), 2),
        }
    return out
fate = {c: load_fate(c) for c in ('off', 'small')}
tags = {c: pd.read_csv(RUN / f'{c}/cid_bonus_tags.csv') for c in ('off', 'small')}
bonus_cids = {c: set(tags[c]['cid'].astype(int).tolist()) for c in ('off', 'small')}
print(f'  bonus 対象 cid: off={sorted(bonus_cids["off"])}')
print(f'                 small={sorted(bonus_cids["small"])}')
matched = sorted(set(fate['off']) & set(fate['small']))
rows = []
for cid in matched:
    bt = cid in bonus_cids['small']
    fo, fs = fate['off'][cid], fate['small'][cid]
    rows.append({'cid': cid, 'bonus_target': bt,
                 'off_state': fo['state'], 'small_state': fs['state'],
                 'off_life': fo['life'], 'small_life': fs['life'],
                 'off_coher': fo['coher'], 'small_coher': fs['coher'],
                 'd_life': fs['life'] - fo['life'], 'd_coher': round(fs['coher'] - fo['coher'], 4)})
mdf = pd.DataFrame(rows)
print(mdf.to_string(index=False))
# bonus 対象 vs 非対象で寿命変化 (small-off) が系統的に違うか
for grp, sub in mdf.groupby('bonus_target'):
    print(f'  bonus_target={grp}: n={len(sub)}, Δlife mean={sub["d_life"].mean():.2f}, '
          f'Δcoher mean={sub["d_coher"].mean():.4f}, '
          f'生存↑={(sub["d_life"]>0).sum()} 生存↓={(sub["d_life"]<0).sum()}')
report['matched_percid'] = mdf.to_dict(orient='records')
report['bonus_target_cids_small'] = sorted(bonus_cids['small'])

# ── 4. 死因 + 多様性 (bonus 対象 vs 非対象) ──
print('\n=== (4) 死因 + 多様性 ===')
death = {}
for c in ('off', 'small'):
    df = pd.read_csv(DIAG[c] / 'subjects/per_subject_seed0.csv').set_index('cognitive_id')
    ghosts = df[df['final_state'] == 'ghost']
    bt_ghost = sum(1 for cid in ghosts.index if int(cid) in bonus_cids[c])
    nbt_ghost = len(ghosts) - bt_ghost
    hosted = df[df['final_state'] == 'hosted']
    bt_host = sum(1 for cid in hosted.index if int(cid) in bonus_cids[c])
    death[c] = {
        'n': len(df), 'hosted': len(hosted), 'ghost': len(ghosts),
        'ghost_bonus_target': bt_ghost, 'ghost_nonbonus': nbt_ghost,
        'hosted_bonus_target': bt_host,
        'ghost_dur_mean': round(float(ghosts['ghost_duration_steps'].mean()), 1) if len(ghosts) else None,
    }
    print(f'  {c}: born={len(df)} hosted={len(hosted)} ghost={len(ghosts)} '
          f'(ghost のうち bonus 対象={bt_ghost}, 非対象={nbt_ghost}); hosted のうち bonus 対象={bt_host}')
report['death_cause'] = death

OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str))
print(f'\n保存: {OUT}')
