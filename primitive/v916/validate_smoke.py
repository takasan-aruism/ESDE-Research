"""
v9.16 Stage 3 Step 5 smoke 承認条件 12 項目の自動検査。

実行: python validate_smoke.py
前提: diag_v916_smoke/ と diag_v916_smoke_run2/ が存在、v915s2/v914 baseline も参照可。
"""
from __future__ import annotations

import csv
import hashlib
import os
import sys
from pathlib import Path
from collections import defaultdict


V916_DIR = Path(__file__).parent
RUN1 = V916_DIR / "diag_v916_smoke"
RUN2 = V916_DIR / "diag_v916_smoke_run2"
V914 = V916_DIR.parent / "v914" / "diag_v914_smoke"
V915S2 = V916_DIR.parent / "v915s2" / "diag_v915s2_smoke"


def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_csv(path: Path) -> tuple[list[str], list[dict]]:
    with open(path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_1_baseline_md5() -> tuple[bool, str]:
    """項目 1: v9.14 baseline 6 本 MD5 一致。"""
    targets = [
        ("aggregates", "per_window_seed0.csv"),
        ("pulse", "pulse_log_seed0.csv"),
        ("labels", "per_label_seed0.csv"),
        ("audit", "per_event_audit_seed0.csv"),
        ("audit", "per_subject_audit_seed0.csv"),
        ("audit", "run_level_audit_summary_seed0.csv"),
    ]
    results = []
    all_ok = True
    for sub, name in targets:
        p_v916 = RUN1 / sub / name
        p_v914 = V914 / sub / name
        if not p_v916.exists():
            results.append(f"  MISSING v916: {sub}/{name}")
            all_ok = False
            continue
        if not p_v914.exists():
            results.append(f"  MISSING v914 baseline: {sub}/{name}")
            all_ok = False
            continue
        m_v916 = md5(p_v916)
        m_v914 = md5(p_v914)
        ok = (m_v916 == m_v914)
        results.append(f"  {'OK' if ok else 'DIFF'}  {sub}/{name}")
        if not ok:
            results.append(f"       v916={m_v916}  v914={m_v914}")
            all_ok = False
    return all_ok, "\n".join(results)


def check_2_per_subject_v914_cols() -> tuple[bool, str]:
    """項目 2: per_subject CSV の v9.14 96 列 = v915s2 smoke と bit-identical
    (--ignore-prefix v915_)。"""
    p_v916 = RUN1 / "subjects" / "per_subject_seed0.csv"
    p_v915s2 = V915S2 / "subjects" / "per_subject_seed0.csv"
    if not p_v916.exists() or not p_v915s2.exists():
        return False, f"  MISSING {p_v916 if not p_v916.exists() else p_v915s2}"

    hdr_v916, rows_v916 = load_csv(p_v916)
    hdr_v915s2, rows_v915s2 = load_csv(p_v915s2)

    # v915_* を除いた非 v915 列が一致するか
    non_v915_v916 = [c for c in hdr_v916 if not c.startswith("v915_")]
    non_v915_v915s2 = [c for c in hdr_v915s2 if not c.startswith("v915_")]

    if non_v915_v916 != non_v915_v915s2:
        return False, (
            f"  v9.14 列順/名が段階 2 と不一致\n"
            f"  v916 non-v915 cols: {len(non_v915_v916)}\n"
            f"  v915s2 non-v915 cols: {len(non_v915_v915s2)}\n"
            f"  diff (v916 only): {set(non_v915_v916)-set(non_v915_v915s2)}\n"
            f"  diff (v915s2 only): {set(non_v915_v915s2)-set(non_v915_v916)}"
        )

    if len(rows_v916) != len(rows_v915s2):
        return False, f"  行数不一致 v916={len(rows_v916)} v915s2={len(rows_v915s2)}"

    diff_count = 0
    first_diff = None
    for i, (r1, r2) in enumerate(zip(rows_v916, rows_v915s2)):
        for c in non_v915_v916:
            if r1.get(c) != r2.get(c):
                diff_count += 1
                if first_diff is None:
                    first_diff = (i, c, r1.get(c), r2.get(c))
                break
    if diff_count > 0:
        return False, (
            f"  非 v915_* 列で差分 {diff_count} 行。"
            f"first_diff row={first_diff[0]} col={first_diff[1]} "
            f"v916={first_diff[2]!r} v915s2={first_diff[3]!r}"
        )
    return True, (
        f"  v9.14 {len(non_v915_v916)} 列すべて一致 "
        f"({len(rows_v916)} rows)"
    )


def check_3_v915_subject_cols() -> tuple[bool, str]:
    """項目 3: v915_* 列の存在 (段階 2 の 13 + 段階 3 の 7 = 20 列)。"""
    p = RUN1 / "subjects" / "per_subject_seed0.csv"
    hdr, _ = load_csv(p)
    expected = {
        # 段階 2 (13)
        "v915_fetch_count", "v915_last_fetch_step",
        "v915_divergence_norm_final", "v915_n_divergence_log",
        "v915_any_mismatch_ever", "v915_mismatch_count_total",
        "v915_last_mismatch_step",
        "v915_fetch_count_e1", "v915_fetch_count_e2", "v915_fetch_count_e3",
        "v915_mismatch_count_e1", "v915_mismatch_count_e2",
        "v915_mismatch_count_e3",
        # 段階 3 (7)
        "v915_avg_age_factor", "v915_min_age_factor",
        "v915_total_observed_count", "v915_total_missing_count",
        "v915_total_match_obs_count", "v915_total_mismatch_obs_count",
        "v915_final_missing_fraction",
    }
    found = {c for c in hdr if c.startswith("v915_")}
    missing = expected - found
    extra = found - expected
    if missing or extra:
        return False, (
            f"  missing={sorted(missing)} extra={sorted(extra)}"
        )
    return True, f"  20 列すべて存在"


def check_4_age_factor_range() -> tuple[bool, str]:
    """項目 4: age_factor が全 fetch で [0, 1]。"""
    p = RUN1 / "selfread" / "observation_log_seed0.csv"
    _, rows = load_csv(p)
    n_ok = 0
    for r in rows:
        af = float(r["age_factor"])
        if af < 0.0 or af > 1.0:
            return False, f"  OOR: row {n_ok+1}, age_factor={af}"
        n_ok += 1
    return True, f"  全 {n_ok} 行 age_factor ∈ [0, 1]"


def check_5_n_observed_range() -> tuple[bool, str]:
    """項目 5: 0 ≤ n_observed ≤ n_core。"""
    p = RUN1 / "selfread" / "observation_log_seed0.csv"
    _, rows = load_csv(p)
    for i, r in enumerate(rows):
        n_obs = int(r["n_observed"])
        n_core = int(r["n_core"])
        if n_obs < 0 or n_obs > n_core:
            return False, (
                f"  OOR at row {i}: n_observed={n_obs}, n_core={n_core}"
            )
    return True, f"  全 {len(rows)} 行で 0 ≤ n_observed ≤ n_core"


def check_6_n_observed_formula() -> tuple[bool, str]:
    """項目 6: n_observed == round(n_core * age_factor)。"""
    p = RUN1 / "selfread" / "observation_log_seed0.csv"
    _, rows = load_csv(p)
    for i, r in enumerate(rows):
        n_obs = int(r["n_observed"])
        n_core = int(r["n_core"])
        af = float(r["age_factor"])
        expected = int(round(n_core * af))
        expected = max(0, min(n_core, expected))
        if n_obs != expected:
            return False, (
                f"  formula mismatch at row {i}: "
                f"n_core={n_core} af={af} expected={expected} got={n_obs}"
            )
    return True, f"  全 {len(rows)} 行で n_observed == round(n_core * age_factor)"


def check_7_missing_flags_consistency() -> tuple[bool, str]:
    """項目 7: per_cid_self の total_missing_count が observation_log と整合。
    各 cid で: total_missing_count = sum(missing_count) across events。"""
    p_self = RUN1 / "selfread" / "per_cid_self_seed0.csv"
    p_obs = RUN1 / "selfread" / "observation_log_seed0.csv"
    _, self_rows = load_csv(p_self)
    _, obs_rows = load_csv(p_obs)

    per_cid_missing_sum = defaultdict(int)
    per_cid_obs_sum = defaultdict(int)
    for r in obs_rows:
        cid = int(r["cid_id"])
        per_cid_missing_sum[cid] += int(r["missing_count"])
        per_cid_obs_sum[cid] += int(r["n_observed"])

    mismatches = []
    checked = 0
    for r in self_rows:
        cid = int(r["cid_id"])
        total_missing = int(r["total_missing_count"])
        total_observed = int(r["total_observed_count"])
        exp_missing = per_cid_missing_sum.get(cid, 0)
        exp_obs = per_cid_obs_sum.get(cid, 0)
        if total_missing != exp_missing or total_observed != exp_obs:
            mismatches.append(
                f"cid={cid} self=(obs={total_observed},miss={total_missing}) "
                f"obslog=(obs={exp_obs},miss={exp_missing})"
            )
            if len(mismatches) >= 3:
                break
        checked += 1
    if mismatches:
        return False, "  \n  ".join(mismatches)
    return True, f"  {checked} cids で total_observed/missing が observation_log と一致"


def check_8_obs_count_split() -> tuple[bool, str]:
    """項目 8: total_match_obs_count + total_mismatch_obs_count == total_observed_count。"""
    p = RUN1 / "selfread" / "per_cid_self_seed0.csv"
    _, rows = load_csv(p)
    for i, r in enumerate(rows):
        m = int(r["total_match_obs_count"])
        mm = int(r["total_mismatch_obs_count"])
        obs = int(r["total_observed_count"])
        if m + mm != obs:
            return False, (
                f"  row {i} cid={r['cid_id']}: "
                f"match={m}+mismatch={mm}={m+mm} != observed={obs}"
            )
    return True, f"  {len(rows)} cids: match+mismatch == observed 全一致"


def check_9_determinism() -> tuple[bool, str]:
    """項目 9: 2 回連続 run の全 CSV で MD5 一致。"""
    diffs = []
    total = 0
    for root, _, files in os.walk(RUN1):
        for f in files:
            if not f.endswith(".csv"):
                continue
            rel = Path(root).relative_to(RUN1) / f
            p1 = RUN1 / rel
            p2 = RUN2 / rel
            if not p2.exists():
                diffs.append(f"  MISSING run2: {rel}")
                continue
            total += 1
            if md5(p1) != md5(p2):
                diffs.append(f"  DIFF: {rel}")
    if diffs:
        return False, "\n".join(diffs[:10])
    return True, f"  {total} CSV ファイル全 MD5 一致"


def check_10_time() -> tuple[bool, str]:
    """項目 10: 実行時間 ≤ 段階 2 smoke × 1.15。
    v915s2 smoke = 65m26.86s ≈ 3926.86s → threshold 4515.89s。"""
    log = V916_DIR / "logs" / "smoke_run1.out"
    if not log.exists():
        return False, f"  ログ無し: {log}"
    content = log.read_text()
    # sh 組み込み time 出力: "real 65m26.86s"
    import re
    m = re.search(r"real\s+(\d+)m([\d.]+)s", content)
    if not m:
        return False, "  time 出力を検出できませんでした"
    sec = int(m.group(1)) * 60 + float(m.group(2))
    threshold = 3926.86 * 1.15
    ok = sec <= threshold
    return ok, (
        f"  v916 smoke: {sec:.2f}s "
        f"(v915s2 {3926.86:.2f}s の {sec/3926.86:.1%}, "
        f"threshold +15% = {threshold:.2f}s)"
    )


def check_11_no_errors() -> tuple[bool, str]:
    """項目 11: エラー/例外ゼロ。"""
    log = V916_DIR / "logs" / "smoke_run1.out"
    content = log.read_text()
    bad_tokens = [
        "Traceback (most recent call last)",
        "Exception",
        "Error:",
        "assertionerror",
    ]
    hits = []
    lc = content.lower()
    for t in bad_tokens:
        if t.lower() in lc:
            hits.append(t)
    if hits:
        # 詳細な最初のエラー表示
        lines = content.splitlines()
        idx = next((i for i, L in enumerate(lines)
                    if any(t.lower() in L.lower() for t in bad_tokens)),
                   None)
        ctx = "\n".join(lines[max(0, idx-2):idx+8]) if idx is not None else ""
        return False, f"  エラー兆候 {hits}\n---\n{ctx}"
    return True, "  stderr にエラー兆候なし"


def check_12_observation_log() -> tuple[bool, str]:
    """項目 12: observation_log の行数が per_event_audit の event 数と整合
    (E3 contact は両 cid 記録のため、ledger event 数と observation_log 行数は
    1:1、per_event_audit の total event 数とは既に 1:1 のはず)。
    かつサイズ < 1 GB。"""
    p_obs = RUN1 / "selfread" / "observation_log_seed0.csv"
    p_audit = RUN1 / "audit" / "per_event_audit_seed0.csv"
    if not p_obs.exists():
        return False, "  observation_log 無し"
    if not p_audit.exists():
        return False, "  per_event_audit 無し"

    # サイズ
    size_gb = p_obs.stat().st_size / (1024**3)
    if size_gb >= 1.0:
        return False, f"  size {size_gb:.3f} GB >= 1 GB"

    # 行数比較
    with open(p_obs) as f:
        obs_rows = sum(1 for _ in f) - 1  # ヘッダを除く
    with open(p_audit) as f:
        audit_rows = sum(1 for _ in f) - 1

    # Layer B の event_emitter は E3 を両 cid 視点で 2 行 append している。
    # Layer C の Fetch も同じ 2 回呼ばれるので per_event_audit 行数と
    # observation_log 行数は同数になるはず。
    # ただし registry に未登録の cid (maturation 中未生成) は Fetch されないので
    # observation_log <= per_event_audit。
    if obs_rows > audit_rows:
        return False, (
            f"  observation_log 行数 {obs_rows} > per_event_audit {audit_rows}"
        )
    return True, (
        f"  obs_log={obs_rows} rows (<= audit={audit_rows}), "
        f"size={size_gb*1024:.1f} MB"
    )


def main() -> int:
    checks = [
        ("1. v9.14 baseline 6 本 MD5 一致", check_1_baseline_md5),
        ("2. per_subject v9.14 列 = 段階 2 bit-identical", check_2_per_subject_v914_cols),
        ("3. v915_* 列 20 列すべて存在", check_3_v915_subject_cols),
        ("4. age_factor ∈ [0, 1]", check_4_age_factor_range),
        ("5. 0 ≤ n_observed ≤ n_core", check_5_n_observed_range),
        ("6. n_observed == round(n_core × age_factor)", check_6_n_observed_formula),
        ("7. total_missing が observation_log と整合", check_7_missing_flags_consistency),
        ("8. match_obs + mismatch_obs == observed", check_8_obs_count_split),
        ("9. 決定論: 2 回連続 run で MD5 一致", check_9_determinism),
        ("10. 実行時間 ≤ 段階 2 smoke × 1.15", check_10_time),
        ("11. エラー・例外ゼロ", check_11_no_errors),
        ("12. observation_log 行数/サイズ健全", check_12_observation_log),
    ]
    n_pass = 0
    for name, fn in checks:
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, f"  EXCEPTION: {type(e).__name__}: {e}"
        sign = "PASS" if ok else "FAIL"
        print(f"[{sign}] {name}")
        for line in detail.splitlines():
            print(line)
        if ok:
            n_pass += 1
    print()
    print(f"{n_pass}/{len(checks)} checks passed.")
    return 0 if n_pass == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
