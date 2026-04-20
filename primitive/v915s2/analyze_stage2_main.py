#!/usr/bin/env python3
"""Aggregation analysis for v9.15 段階 2 main run → feeds v915s2_stage2_result.md.

Output: テキスト形式でコンソールに表を出力。
"""
from __future__ import annotations
import csv, glob, json, statistics
from collections import Counter, defaultdict
from pathlib import Path

V915S2_DIR = Path('/home/takasan/esde/ESDE-Research/primitive/v915s2/diag_v915s2_main')
V915_DIR   = Path('/home/takasan/esde/ESDE-Research/primitive/v915/diag_v915_main')


def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def _to_int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _to_float(v, default=None):
    if v is None or v == '' or v == 'unformed':
        return default
    try:
        return float(v)
    except ValueError:
        return default


def _to_bool(v):
    s = str(v).lower()
    return s in ('true', '1', 'yes')


def bucket_n_core(nc):
    if nc is None or nc == '' or nc == 'unformed':
        return 'unformed'
    try:
        nc = int(nc)
    except (TypeError, ValueError):
        return 'unformed'
    if nc <= 4:
        return str(nc)
    return '5+'


def pct(values, p):
    if not values:
        return None
    s = sorted(values)
    if p == 50:
        return statistics.median(s)
    if p == 0:
        return s[0]
    if p == 100:
        return s[-1]
    idx = int(round(p / 100.0 * (len(s) - 1)))
    return s[idx]


def describe_stats(values):
    """Return dict with n/mean/median/p25/p75/min/max/sum."""
    vals = [v for v in values if v is not None]
    n = len(vals)
    if n == 0:
        return {'n': 0, 'mean': None, 'median': None,
                'p25': None, 'p75': None, 'min': None, 'max': None, 'sum': 0}
    return {
        'n': n,
        'mean': statistics.fmean(vals),
        'median': statistics.median(vals),
        'p25': pct(vals, 25),
        'p75': pct(vals, 75),
        'min': min(vals), 'max': max(vals), 'sum': sum(vals),
    }


# =================================================================
# 1. Load stage-2 per_subject rows
# =================================================================
stage2_rows = []
for f in sorted(V915S2_DIR.glob('subjects/per_subject_seed*.csv')):
    seed = int(f.stem.replace('per_subject_seed', ''))
    for r in load_csv(f):
        r['_seed'] = seed
        stage2_rows.append(r)

print(f"# stage 2 per_subject total rows: {len(stage2_rows)}")
print(f"# seeds: {sorted({r['_seed'] for r in stage2_rows})}")

# =================================================================
# 2. Stage-1 per_subject rows (参考値比較用)
# =================================================================
stage1_rows = []
for f in sorted(V915_DIR.glob('subjects/per_subject_seed*.csv')):
    seed = int(f.stem.replace('per_subject_seed', ''))
    for r in load_csv(f):
        r['_seed'] = seed
        stage1_rows.append(r)
print(f"# stage 1 per_subject total rows: {len(stage1_rows)}")


# =================================================================
# 3. Fetch 数分布 (全体、n_core バケット別)
# =================================================================
def fetch_stats_per_subject(rows):
    all_fc = [_to_int(r['v915_fetch_count']) for r in rows]
    by_nc = defaultdict(list)
    for r in rows:
        b = bucket_n_core(r.get('v11_m_c_n_core') or r.get('n_core_member') or r.get('n_core'))
        by_nc[b].append(_to_int(r['v915_fetch_count']))
    return all_fc, dict(by_nc)


s2_all_fc, s2_fc_by_nc = fetch_stats_per_subject(stage2_rows)
s1_all_fc, s1_fc_by_nc = fetch_stats_per_subject(stage1_rows)

print("\n## 2.1 Fetch count distribution (per_subject, stage 2)")
d = describe_stats(s2_all_fc)
print(f"  n={d['n']}, mean={d['mean']:.2f}, median={d['median']}, p25={d['p25']}, p75={d['p75']}, min={d['min']}, max={d['max']}, sum={d['sum']}")
print("  by n_core bucket:")
for b in sorted(s2_fc_by_nc.keys()):
    ds = describe_stats(s2_fc_by_nc[b])
    print(f"    {b}: n={ds['n']}, mean={ds['mean']:.2f}, median={ds['median']}, p25={ds['p25']}, p75={ds['p75']}, min={ds['min']}, max={ds['max']}, sum={ds['sum']}")

print("\n## 2.1 (参考) Fetch count distribution (per_subject, stage 1)")
d = describe_stats(s1_all_fc)
print(f"  n={d['n']}, mean={d['mean']:.2f}, median={d['median']}, p25={d['p25']}, p75={d['p75']}, min={d['min']}, max={d['max']}, sum={d['sum']}")
print("  by n_core bucket:")
for b in sorted(s1_fc_by_nc.keys()):
    ds = describe_stats(s1_fc_by_nc[b])
    print(f"    {b}: n={ds['n']}, mean={ds['mean']:.2f}, median={ds['median']}, p25={ds['p25']}, p75={ds['p75']}, min={ds['min']}, max={ds['max']}, sum={ds['sum']}")


# =================================================================
# 4. event 種別ごとの Fetch 発火数
# =================================================================
print("\n## 2.2 event 種別ごとの Fetch 発火 (stage 2、per_subject 合算)")
for col in ['v915_fetch_count_e1','v915_fetch_count_e2','v915_fetch_count_e3']:
    vals = [_to_int(r[col]) for r in stage2_rows]
    ds = describe_stats(vals)
    print(f"  {col}: n={ds['n']}, mean={ds['mean']:.3f}, median={ds['median']}, p75={ds['p75']}, max={ds['max']}, sum={ds['sum']}")

print("\n## 2.2 event 種別ごとの Fetch 発火 (stage 2、n_core バケット別)")
for b in ['2', '3', '4', '5+']:
    subset = [r for r in stage2_rows if bucket_n_core(r.get('v11_m_c_n_core') or r.get('n_core_member') or r.get('n_core')) == b]
    if not subset: continue
    print(f"  n_core {b} (n_cids={len(subset)}):")
    for col in ['v915_fetch_count_e1','v915_fetch_count_e2','v915_fetch_count_e3']:
        vals = [_to_int(r[col]) for r in subset]
        ds = describe_stats(vals)
        print(f"    {col}: mean={ds['mean']:.3f}, median={ds['median']}, max={ds['max']}, sum={ds['sum']}")


# =================================================================
# 5. 不一致観察
# =================================================================
print("\n## 2.3 any_mismatch_ever の分布 (stage 2)")
counts = Counter(_to_bool(r['v915_any_mismatch_ever']) for r in stage2_rows)
print(f"  True: {counts[True]} / {len(stage2_rows)} ({counts[True]/len(stage2_rows)*100:.1f}%)")
print(f"  False: {counts[False]} / {len(stage2_rows)} ({counts[False]/len(stage2_rows)*100:.1f}%)")

print("\n## 2.3 mismatch_count_total の分布 (stage 2)")
vals = [_to_int(r['v915_mismatch_count_total']) for r in stage2_rows]
ds = describe_stats(vals)
print(f"  n={ds['n']}, mean={ds['mean']:.3f}, median={ds['median']}, p75={ds['p75']}, max={ds['max']}, sum={ds['sum']}")

print("\n## 2.3 mismatch_count_e1/e2/e3 の分布 (stage 2)")
for col in ['v915_mismatch_count_e1','v915_mismatch_count_e2','v915_mismatch_count_e3']:
    vals = [_to_int(r[col]) for r in stage2_rows]
    ds = describe_stats(vals)
    print(f"  {col}: mean={ds['mean']:.3f}, median={ds['median']}, max={ds['max']}, sum={ds['sum']}")


# =================================================================
# 6. Self-Divergence final
# =================================================================
print("\n## 2.4 divergence_norm_final 分布 (stage 2)")
vals = [v for v in (_to_float(r['v915_divergence_norm_final']) for r in stage2_rows) if v is not None]
ds = describe_stats(vals)
print(f"  n={ds['n']}, mean={ds['mean']:.4f}, median={ds['median']:.4f}, p25={ds['p25']:.4f}, p75={ds['p75']:.4f}, max={ds['max']:.4f}")
print("  by n_core bucket:")
for b in ['2', '3', '4', '5+']:
    subset = [r for r in stage2_rows if bucket_n_core(r.get('v11_m_c_n_core') or r.get('n_core_member') or r.get('n_core')) == b]
    vals = [v for v in (_to_float(r['v915_divergence_norm_final']) for r in subset) if v is not None]
    if not vals: continue
    ds = describe_stats(vals)
    print(f"    {b}: n={ds['n']}, mean={ds['mean']:.4f}, median={ds['median']:.4f}, max={ds['max']:.4f}")

print("\n## 2.4 (参考) divergence_norm_final 分布 (stage 1)")
vals = [v for v in (_to_float(r['v915_divergence_norm_final']) for r in stage1_rows) if v is not None]
if vals:
    ds = describe_stats(vals)
    print(f"  n={ds['n']}, mean={ds['mean']:.4f}, median={ds['median']:.4f}, p75={ds['p75']:.4f}, max={ds['max']:.4f}")


# =================================================================
# 7. event 種別 × mismatch 率
# =================================================================
print("\n## 3.1 event 種別 × mismatch 率 (stage 2、全 cid 合算)")
for e in ('e1', 'e2', 'e3'):
    fc_col = f'v915_fetch_count_{e}'
    mm_col = f'v915_mismatch_count_{e}'
    tot_fc = sum(_to_int(r[fc_col]) for r in stage2_rows)
    tot_mm = sum(_to_int(r[mm_col]) for r in stage2_rows)
    rate = (tot_mm / tot_fc) if tot_fc > 0 else None
    print(f"  {e.upper()}: fetch_count={tot_fc}, mismatch_count={tot_mm}, mismatch_ratio={'{:.4f}'.format(rate) if rate is not None else 'n/a'}")


# =================================================================
# 8. divergence_log で event 種別ごとの theta_diff_norm 平均 (24 seeds 合算)
# =================================================================
print("\n## 3.2 event 種別ごとの theta_diff_norm (divergence_log、24 seeds 合算)")
by_event = defaultdict(list)
for f in sorted(V915S2_DIR.glob('selfread/divergence_log_seed*.csv')):
    for r in load_csv(f):
        et = r.get('event_type_coarse')
        v = _to_float(r['theta_diff_norm'])
        if et and v is not None:
            by_event[et].append(v)
for et in sorted(by_event.keys()):
    ds = describe_stats(by_event[et])
    print(f"  {et}: n={ds['n']}, mean={ds['mean']:.4f}, median={ds['median']:.4f}, p25={ds['p25']:.4f}, p75={ds['p75']:.4f}, max={ds['max']:.4f}")


# =================================================================
# 9. v9.14 shadow_pulse_count との相関
# =================================================================
print("\n## 4. v14_shadow_pulse_count と v915_fetch_count の cid 単位対応")
audit_by_cid = {}
for f in sorted(V915S2_DIR.glob('audit/per_subject_audit_seed*.csv')):
    seed = int(f.stem.replace('per_subject_audit_seed', ''))
    for r in load_csv(f):
        audit_by_cid[(seed, int(r['cid']))] = r

matched = 0
pairs = []
for r in stage2_rows:
    key = (r['_seed'], int(r.get('cognitive_id') or r.get('cid')))
    au = audit_by_cid.get(key)
    if au is None:
        continue
    sp = _to_int(au.get('v14_shadow_pulse_count'), 0)
    fc = _to_int(r['v915_fetch_count'], 0)
    pairs.append((sp, fc))
    matched += 1

print(f"  matched cids: {matched} / {len(stage2_rows)}")

if pairs:
    eq = sum(1 for sp, fc in pairs if sp == fc)
    lt = sum(1 for sp, fc in pairs if sp < fc)
    gt = sum(1 for sp, fc in pairs if sp > fc)
    print(f"  v14_shadow_pulse_count == v915_fetch_count: {eq} ({eq/len(pairs)*100:.1f}%)")
    print(f"  < : {lt} ({lt/len(pairs)*100:.1f}%)")
    print(f"  > : {gt} ({gt/len(pairs)*100:.1f}%)")

    # simple Pearson-like correlation
    xs = [sp for sp, _ in pairs]
    ys = [fc for _, fc in pairs]
    mx = sum(xs)/len(xs)
    my = sum(ys)/len(ys)
    num = sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    dx = sum((x-mx)**2 for x in xs) ** 0.5
    dy = sum((y-my)**2 for y in ys) ** 0.5
    r_val = num / (dx * dy) if dx > 0 and dy > 0 else None
    print(f"  Pearson r = {r_val:.4f}" if r_val is not None else "  Pearson r = n/a")


# =================================================================
# 10. Seed 別分散分析
# =================================================================
print("\n## 5. Seed 別分散 (n_core バケット × seed の Fetch 平均)")
by_seed_bucket = defaultdict(list)
for r in stage2_rows:
    b = bucket_n_core(r.get('v11_m_c_n_core') or r.get('n_core_member') or r.get('n_core'))
    by_seed_bucket[(r['_seed'], b)].append(_to_int(r['v915_fetch_count']))

means_per_bucket = defaultdict(dict)
for (s, b), vals in by_seed_bucket.items():
    means_per_bucket[b][s] = statistics.fmean(vals) if vals else 0

print("  n_core bucket × seed (fetch_count 平均):")
for b in sorted(means_per_bucket.keys()):
    seeds = sorted(means_per_bucket[b].keys())
    vs = [means_per_bucket[b][s] for s in seeds]
    if len(vs) > 1:
        mu = statistics.fmean(vs)
        sigma = statistics.stdev(vs) if len(vs) > 1 else 0
        cv = sigma / mu if mu else 0
        print(f"    {b}: n_seeds={len(vs)}, mean_across_seeds={mu:.2f}, stdev={sigma:.2f}, CV={cv:.3f}, min={min(vs):.2f}, max={max(vs):.2f}")

# same for divergence_norm_final
print("  n_core bucket × seed (divergence_norm_final 平均):")
by_seed_bucket_div = defaultdict(list)
for r in stage2_rows:
    b = bucket_n_core(r.get('v11_m_c_n_core') or r.get('n_core_member') or r.get('n_core'))
    v = _to_float(r['v915_divergence_norm_final'])
    if v is not None:
        by_seed_bucket_div[(r['_seed'], b)].append(v)
means_per_bucket = defaultdict(dict)
for (s, b), vals in by_seed_bucket_div.items():
    means_per_bucket[b][s] = statistics.fmean(vals) if vals else 0
for b in sorted(means_per_bucket.keys()):
    seeds = sorted(means_per_bucket[b].keys())
    vs = [means_per_bucket[b][s] for s in seeds]
    if len(vs) > 1:
        mu = statistics.fmean(vs)
        sigma = statistics.stdev(vs) if len(vs) > 1 else 0
        cv = sigma / mu if mu else 0
        print(f"    {b}: n_seeds={len(vs)}, mean={mu:.4f}, stdev={sigma:.4f}, CV={cv:.3f}, min={min(vs):.4f}, max={max(vs):.4f}")


# =================================================================
# 11. Per-event audit event 種別合計 (24 seeds 合算)
# =================================================================
print("\n## 参考: per_event_audit 24 seeds event 種別集計")
event_counter = Counter()
for f in sorted(V915S2_DIR.glob('audit/per_event_audit_seed*.csv')):
    for r in load_csv(f):
        event_counter[r['v14_event_type']] += 1
for et in ('E1_death', 'E1_birth', 'E2_rise', 'E2_fall', 'E3_contact'):
    print(f"  {et}: {event_counter.get(et, 0)}")
print(f"  total: {sum(event_counter.values())}")


# =================================================================
# 12. subject 行の schema 確認
# =================================================================
print("\n## schema (stage 2 per_subject 列の末尾)")
if stage2_rows:
    cols = list(stage2_rows[0].keys())
    v915_cols = [c for c in cols if c.startswith('v915_')]
    print(f"  v915_ 列数: {len(v915_cols)}")
    for c in v915_cols:
        print(f"    {c}")
