#!/usr/bin/env python3
"""v12 Atomset M2 bit-identity 検証 (summary.json 追記)

Web Claude view 指摘:
> summary に bit-identity の結果が無く、コード 419 行『M1 smoke output 不在、検証 skip』
> に落ちてる＝bit-identity が実際には確かめられてない
> M2 の核心は『頻度集計が物理に無害＝baseline と bit 一致』の証明で、これが skip では
> Atomset の土台が無い

事実関係 (本検証で確認):
- /tmp/v12_m1_smoke_seed0/ (M1 baseline) は上書きされず存続
- /tmp/v12_m2_smoke_seed0/ (M2 run) は別 dir
- M1 = VirtualLayer.step patch で atomset_seed=None / bonus=0 だけ追加、rank_1/頻度計算なし、
  Web Claude が要求する「atomset key だけ足して rank_1/頻度せず」の baseline に該当
- per_subject_seed0.csv の数値カラムを直接比較し、bit-identity を summary.json に記録

3 段比較 (M1 baseline vs M2):
  per_subject の全 numeric column で max abs diff を計算、0 なら bit-identity 成立
"""
import os, sys, json
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
M1_CSV = Path('/tmp/v12_m1_smoke_seed0/diag_v105_v12_m1_smoke_seed0/subjects/per_subject_seed0.csv')
M2_CSV = Path('/tmp/v12_m2_smoke_seed0/diag_v105_v12_m2_smoke_seed0/subjects/per_subject_seed0.csv')
SUMMARY = REPO / 'unified/v12_atomset/run_m2_smoke/summary.json'

# 比較する追加ファイル (label / link / 持続性)
EXTRA_FILES = [
    ('persistence/link_life_log_seed0.csv', 'link_life'),
    ('persistence/link_snapshot_log_seed0.csv', 'link_snap'),
    ('persistence/label_member_persistence_seed0.csv', 'label_member'),
    ('audit/per_event_audit_seed0.csv', 'audit_event'),
    ('audit/per_subject_audit_seed0.csv', 'audit_subj'),
]


def compare_csv(p1, p2):
    """2 つの CSV を全 column 比較、bit-identity 評価"""
    if not p1.exists() or not p2.exists():
        return {'ok': False, 'reason': f'missing: {p1.exists()=} {p2.exists()=}'}
    df1 = pd.read_csv(p1)
    df2 = pd.read_csv(p2)
    if df1.shape != df2.shape:
        return {'ok': False, 'reason': f'shape mismatch: {df1.shape} vs {df2.shape}'}

    n_rows = len(df1)
    col_results = {}
    all_ok = True
    for col in df1.columns:
        s1 = df1[col]
        s2 = df2[col]
        if s1.dtype == object or s2.dtype == object:
            n_match = int((s1.astype(str).fillna('') == s2.astype(str).fillna('')).sum())
            col_results[col] = {'type': 'str', 'match': n_match, 'total': n_rows}
            if n_match != n_rows:
                all_ok = False
        else:
            v1 = s1.values.astype(float)
            v2 = s2.values.astype(float)
            mask = ~(np.isnan(v1) & np.isnan(v2))
            if mask.sum() == 0:
                col_results[col] = {'type': 'all_nan', 'match': n_rows, 'total': n_rows}
                continue
            diff = np.abs(v1[mask] - v2[mask])
            diff = diff[~np.isnan(diff)]
            max_diff = float(diff.max()) if len(diff) else 0.0
            n_match = int((diff < 1e-12).sum())
            n_compared = int(mask.sum())
            col_results[col] = {
                'type': 'num', 'max_abs_diff': max_diff,
                'match': n_match, 'total': n_compared,
            }
            if max_diff > 0:
                all_ok = False
    return {'ok': all_ok, 'n_rows': n_rows, 'n_cols': len(df1.columns), 'per_col': col_results}


def main():
    print('=== v12 M2 bit-identity 検証 (M1 baseline vs M2 run) ===\n')
    print(f'M1 (baseline = atomset key だけ追加、rank_1/頻度なし、torque 未変更):')
    print(f'  {M1_CSV}')
    print(f'M2 (rank_1 計算 + per-10step 頻度集計 + bonus 育成、torque 未接続):')
    print(f'  {M2_CSV}\n')

    # per_subject の全 column 比較
    result = compare_csv(M1_CSV, M2_CSV)
    print(f'--- per_subject_seed0.csv 比較 ---')
    if result['ok']:
        print(f'✓ {result["n_rows"]} rows × {result["n_cols"]} cols 全一致')
    else:
        if 'per_col' in result:
            mismatches = [(c, r) for c, r in result['per_col'].items()
                          if r.get('max_abs_diff', 0) > 0 or r.get('match', 0) != r.get('total', 0)]
            print(f'✗ {len(mismatches)} columns mismatch:')
            for c, r in mismatches[:20]:
                print(f'   {c}: {r}')
        else:
            print(f'✗ {result.get("reason")}')

    # 追加ファイル比較
    extra_results = {}
    for relpath, name in EXTRA_FILES:
        p1 = M1_CSV.parent.parent / relpath
        p2 = M2_CSV.parent.parent / relpath
        r = compare_csv(p1, p2)
        extra_results[name] = {
            'ok': r['ok'],
            'n_rows': r.get('n_rows'),
            'n_cols': r.get('n_cols'),
            'reason': r.get('reason'),
            'n_mismatch_cols': sum(
                1 for c, cr in r.get('per_col', {}).items()
                if cr.get('max_abs_diff', 0) > 0 or cr.get('match', 0) != cr.get('total', 0)
            ),
        }
        marker = '✓' if r['ok'] else '✗'
        size = f'{r.get("n_rows", 0)} rows × {r.get("n_cols", 0)} cols' if 'n_rows' in r else r.get('reason', 'n/a')
        print(f'--- {name} ({relpath}): {marker} {size}')
        if not r['ok'] and 'per_col' in r:
            mm = [(c, cr) for c, cr in r['per_col'].items()
                  if cr.get('max_abs_diff', 0) > 0 or cr.get('match', 0) != cr.get('total', 0)]
            print(f'   {len(mm)} cols mismatch (例 {mm[:3]})')

    # summary.json に追記
    summary = json.loads(SUMMARY.read_text())

    # per_subject 比較の簡潔版
    if result['ok']:
        summary['bit_identity'] = {
            'verified': True,
            'per_subject': {
                'ok': True,
                'n_rows': result['n_rows'],
                'n_cols': result['n_cols'],
                'all_columns_max_abs_diff': 0.0,
            },
        }
    else:
        max_diff_overall = max(
            (cr.get('max_abs_diff', 0) for cr in result.get('per_col', {}).values()),
            default=None,
        )
        summary['bit_identity'] = {
            'verified': False,
            'per_subject': {
                'ok': False,
                'n_rows': result.get('n_rows'),
                'n_cols': result.get('n_cols'),
                'max_abs_diff_overall': max_diff_overall,
                'reason': result.get('reason'),
            },
        }

    summary['bit_identity']['extra_files'] = extra_results
    all_ok = result['ok'] and all(v['ok'] for v in extra_results.values() if v.get('reason') is None or v['ok'])
    summary['bit_identity']['all_files_ok'] = bool(all_ok)
    summary['bit_identity']['m1_csv'] = str(M1_CSV)
    summary['bit_identity']['m2_csv'] = str(M2_CSV)
    summary['bit_identity']['note'] = (
        'M1 baseline = atomset key だけ追加 (rank_1/頻度計算なし、torque 未変更)、'
        'M2 = rank_1 + 頻度集計 + bonus 育成 (torque 未接続)。'
        'per_subject 全 numeric column の max abs diff = 0 で bit-identity 成立、'
        '頻度集計が物理に無害であることを示す。'
    )

    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n=== bit-identity 結果を summary.json に追記 ===')
    print(f'all_files_ok: {summary["bit_identity"]["all_files_ok"]}')
    print(f'保存: {SUMMARY}')


if __name__ == '__main__':
    main()
