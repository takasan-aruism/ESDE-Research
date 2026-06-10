#!/usr/bin/env python3
"""v12 Atomset M3 — torque 接続の効果検証 (bit-identity 制御 + diff 確認)

3 条件 (off / small / medium) の出力を比較し、M3 smoke 出口を判定する:

  (A) 制御群: GAIN=off は M2 baseline と bit-identity (= 配線が gated、off で無害)
      → torque_factor=1.0 を明示設定しても torque は変わらないことを 6 ファイルで確認
  (B) torque 効果: GAIN=small / medium は off と diff が出る
      → bonus が cog_factor の口を通って torque_mag に乗り、位相を揃える力が変わった証拠
      → M2 で「頻度集計は物理に無害 (bit 一致)」が確定済なので、ここで出る diff は
        torque 接続のみに由来する (切り分け成立)
  (C) 発散なし: 全条件で theta_diverged=False、run 完走

判定数値 (GAIN) は CID レコードに残さない。本 script は実験者側の検証で、
出力は run_m3_smoke/compare.json (実験ログ)。
"""
import os, sys, json
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
RUN_DIR = REPO / 'unified/v12_atomset/run_m3_smoke'

# 比較対象ファイル (M2 bit-identity 検証と同一の 6 種)
PER_SUBJECT = 'subjects/per_subject_seed0.csv'
EXTRA_FILES = [
    ('persistence/link_life_log_seed0.csv', 'link_life'),
    ('persistence/link_snapshot_log_seed0.csv', 'link_snap'),
    ('persistence/label_member_persistence_seed0.csv', 'label_member'),
    ('audit/per_event_audit_seed0.csv', 'audit_event'),
    ('audit/per_subject_audit_seed0.csv', 'audit_subj'),
]

DIAG = {
    'm2':     Path('/tmp/v12_m2_smoke_seed0/diag_v105_v12_m2_smoke_seed0'),
    'off':    Path('/tmp/v12_m3_smoke_off_seed0/diag_v105_v12_m3_smoke_off_seed0'),
    'small':  Path('/tmp/v12_m3_smoke_small_seed0/diag_v105_v12_m3_smoke_small_seed0'),
    'medium': Path('/tmp/v12_m3_smoke_medium_seed0/diag_v105_v12_m3_smoke_medium_seed0'),
}


def compare_csv(p1, p2):
    """2 CSV を全 column 比較、bit-identity / diff を評価"""
    if not p1.exists() or not p2.exists():
        return {'ok': False, 'reason': f'missing: {p1.exists()=} {p2.exists()=}'}
    df1 = pd.read_csv(p1)
    df2 = pd.read_csv(p2)
    if df1.shape != df2.shape:
        return {'ok': False, 'shape_mismatch': True,
                'shape1': list(df1.shape), 'shape2': list(df2.shape),
                'reason': f'shape mismatch: {df1.shape} vs {df2.shape}'}
    n_rows = len(df1)
    all_ok = True
    n_mismatch_cols = 0
    max_diff_overall = 0.0
    for col in df1.columns:
        s1, s2 = df1[col], df2[col]
        if s1.dtype == object or s2.dtype == object:
            n_match = int((s1.astype(str).fillna('') == s2.astype(str).fillna('')).sum())
            if n_match != n_rows:
                all_ok = False
                n_mismatch_cols += 1
        else:
            v1 = s1.values.astype(float); v2 = s2.values.astype(float)
            mask = ~(np.isnan(v1) & np.isnan(v2))
            if mask.sum() == 0:
                continue
            diff = np.abs(v1[mask] - v2[mask])
            diff = diff[~np.isnan(diff)]
            md = float(diff.max()) if len(diff) else 0.0
            max_diff_overall = max(max_diff_overall, md)
            if md > 0:
                all_ok = False
                n_mismatch_cols += 1
    return {'ok': all_ok, 'n_rows': n_rows, 'n_cols': len(df1.columns),
            'n_mismatch_cols': n_mismatch_cols, 'max_diff_overall': max_diff_overall}


def compare_all_files(base_label, base_dir, other_label, other_dir):
    """6 ファイル全比較。bit-identity (全 ok) か diff か。"""
    files = [(PER_SUBJECT, 'per_subject')] + [(rp, nm) for rp, nm in EXTRA_FILES]
    out = {}
    for relpath, name in files:
        out[name] = compare_csv(base_dir / relpath, other_dir / relpath)
    all_ok = all(r.get('ok') for r in out.values())
    any_diff = any((not r.get('ok')) for r in out.values())
    return {'all_bit_identical': bool(all_ok), 'any_diff': bool(any_diff), 'files': out}


def load_summary(cond):
    p = RUN_DIR / cond / 'summary.json'
    return json.loads(p.read_text()) if p.exists() else None


def main():
    print('=== v12 M3 torque 接続 効果検証 ===\n')
    results = {}

    # === (A) 制御群: off vs M2 baseline → bit-identity 期待 ===
    print('--- (A) 制御群: GAIN=off vs M2 baseline (6 ファイル) ---')
    ctrl = compare_all_files('m2', DIAG['m2'], 'off', DIAG['off'])
    results['control_off_vs_m2'] = ctrl
    for name, r in ctrl['files'].items():
        if r.get('ok'):
            print(f'  ✓ {name}: {r["n_rows"]} rows × {r["n_cols"]} cols 全一致')
        elif r.get('shape_mismatch'):
            print(f'  ✗ {name}: shape {r["shape1"]} vs {r["shape2"]}')
        elif 'reason' in r:
            print(f'  ? {name}: {r["reason"]}')
        else:
            print(f'  ✗ {name}: {r["n_mismatch_cols"]} cols diff, max={r["max_diff_overall"]:.3e}')
    print(f'  → {"✓ off は M2 と bit-identity (制御群成立、配線 gated)" if ctrl["all_bit_identical"] else "✗ off が M2 と不一致 (制御群崩れ、要 debug)"}\n')

    # === (B) torque 効果: small / medium vs off → diff 期待 ===
    for cond in ('small', 'medium'):
        print(f'--- (B) torque 効果: GAIN={cond} vs off (6 ファイル) ---')
        cmp = compare_all_files('off', DIAG['off'], cond, DIAG[cond])
        results[f'effect_{cond}_vs_off'] = cmp
        for name, r in cmp['files'].items():
            if r.get('ok'):
                print(f'  = {name}: 一致 ({r["n_rows"]} rows)')
            elif r.get('shape_mismatch'):
                print(f'  Δ {name}: shape diverged {r["shape1"]} vs {r["shape2"]} (population 変化)')
            elif 'reason' in r:
                print(f'  ? {name}: {r["reason"]}')
            else:
                print(f'  Δ {name}: {r["n_mismatch_cols"]} cols diff, max={r["max_diff_overall"]:.3e}')
        verdict = 'torque 由来の diff あり (効果確認)' if cmp['any_diff'] else 'diff なし (torque が乗っていない疑い)'
        print(f'  → {"✓" if cmp["any_diff"] else "✗"} {verdict}\n')

    # === (C) 発散なし + instrumentation (summary から) ===
    print('--- (C) 発散チェック + torque 接続 instrumentation ---')
    instr = {}
    for cond in ('off', 'small', 'medium'):
        s = load_summary(cond)
        if s is None:
            print(f'  {cond}: summary 不在')
            continue
        instr[cond] = {
            'theta_diverged': s.get('theta_diverged'),
            'gain': s.get('torque_gain'),
            'max_atomset_factor': s.get('max_atomset_factor'),
            'labels_factor_gt1': s.get('labels_factor_gt1'),
            'windows_with_active_factor': s.get('windows_with_active_factor'),
            'torque_total_sum': s.get('torque_total_sum'),
            'bonus_max': s.get('bonus_max'),
            'duration_sec': s.get('duration_sec'),
        }
        d = instr[cond]
        print(f'  {cond:7s} GAIN={d["gain"]}: 発散={"✗発散" if d["theta_diverged"] else "✓なし"}, '
              f'max_factor={d["max_atomset_factor"]}, factor>1 label={d["labels_factor_gt1"]}, '
              f'Σtorque_total={d["torque_total_sum"]}, {d["duration_sec"]}s')
    results['instrumentation'] = instr

    # torque_total が GAIN とともに単調増 (cog_factor は線形 multiplier、感応指標) を確認
    try:
        tt = {c: instr[c]['torque_total_sum'] for c in ('off', 'small', 'medium')}
        mono = tt['off'] <= tt['small'] <= tt['medium']
        print(f'\n  Σtorque_total: off={tt["off"]} ≤ small={tt["small"]} ≤ medium={tt["medium"]} '
              f'→ {"✓ GAIN とともに増 (cog_factor が torque_mag に線形に乗っている)" if mono else "△ 単調でない (population 変化の交絡、要注意)"}')
        results['torque_total_monotonic'] = bool(mono)
    except Exception as e:
        print(f'  torque_total 比較 skip: {e}')

    # === 総合判定 ===
    ctrl_ok = results['control_off_vs_m2']['all_bit_identical']
    small_diff = results['effect_small_vs_off']['any_diff']
    medium_diff = results['effect_medium_vs_off']['any_diff']
    no_diverge = all(not v.get('theta_diverged') for v in instr.values())
    verdict_ok = ctrl_ok and small_diff and medium_diff and no_diverge

    print('\n' + '=' * 60)
    print('M3 smoke 総合判定')
    print('=' * 60)
    print(f'  (A) off ≡ M2 baseline (制御群): {"✓" if ctrl_ok else "✗"}')
    print(f'  (B) small/medium ≠ off (torque 効果): small={"✓" if small_diff else "✗"} medium={"✓" if medium_diff else "✗"}')
    print(f'  (C) 全条件で発散なし: {"✓" if no_diverge else "✗"}')
    print(f'  → M3 smoke: {"✓ 健全 (24 seeds main の前提を満たす)" if verdict_ok else "✗ 要確認"}')

    results['verdict'] = {
        'control_off_eq_m2': bool(ctrl_ok),
        'effect_small': bool(small_diff),
        'effect_medium': bool(medium_diff),
        'no_divergence': bool(no_diverge),
        'm3_smoke_healthy': bool(verdict_ok),
    }
    (RUN_DIR / 'compare.json').write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f'\n保存: {RUN_DIR / "compare.json"}')


if __name__ == '__main__':
    main()
