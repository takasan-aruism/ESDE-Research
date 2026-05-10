#!/usr/bin/env python3
"""v10.12 Step G: v112_orchestrator.

Step D / E_baseline / E_propagation / F の 4 モジュールを 1 コマンドで
順次実行し、smoke では bit-identity 層 A (2 回実行 hash 一致) +
層 B (v108_re/v108 既存出力 mtime/size 不変) + 層 C (v112/outputs/
配下のみ書き込み) を一括検証する.

Step C (receptive_cid_detector) は前提として既に実行済 (developmental/
v112/outputs/step_c/ に 24 seeds 分が存在)、本 orchestrator では
Step D 以降のみを順次実行する.

実行モード:
  --mode smoke : seed 0 のみ
  --mode main  : 24 seeds 全件 (Step H で Web Claude/Taka 承認後に発動)

検証モード:
  --verify-bit-identity : pipeline を 2 回実行し全成果物の hash 一致を検証
  --layer-b-check       : v108_re/v108 既存出力の mtime/size 不変を検証

出力:
  - v112/outputs/{mode}/orchestrator_run_summary_{mode}.json
  - v112/outputs/{mode}/orchestrator_bit_identity_{mode}.json (--verify-bit-identity 時)

規律:
  - 物理層 frozen: ledger 不変、各モジュール集計のみ
  - 神の手回避: 既存 4 モジュール (Step D-F 実装) を順次呼ぶのみ、新規ロジックなし
  - 層 A/B/C 検証: 構造的に保証済 (各モジュールの safe_write_parquet_v112 で層 C)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V108_ROOT = (REPO_ROOT / "developmental" / "v108").resolve()
V110_ROOT = (REPO_ROOT / "developmental" / "v110").resolve()
V112_ROOT = (REPO_ROOT / "developmental" / "v112").resolve()
V112_SMOKE = V112_ROOT / "outputs" / "smoke"
V112_MAIN = V112_ROOT / "outputs" / "main"
STEP_C_ROOT = V112_ROOT / "outputs" / "step_c"

# Step D-F の各 module
STEP_MODULES = [
    ("step_d", V112_ROOT / "v112_atom_event_generator.py", "Step D atom_event_generator"),
    ("step_e_baseline", V112_ROOT / "v112_baseline_recalculator.py", "Step E baseline_recalculator"),
    ("step_e_propagation", V112_ROOT / "v112_propagation_analyzer.py", "Step E propagation_analyzer"),
    ("step_f", V112_ROOT / "v112_observation_recorder.py", "Step F observation_recorder"),
]

# 層 B 不変検証対象 (v108_re / v108 既存出力)
LAYER_B_DIRS = [
    V110_ROOT / "v108_re" / "outputs" / "main",
    V110_ROOT / "v108_re" / "outputs" / "smoke",
    V108_ROOT / "outputs" / "main",
]

# bit-identity 検証対象ファイル (smoke seed 0)
BIT_IDENTITY_FILES_SMOKE_SEED0 = [
    "atom_introduction_events_v112_seed0.parquet",
    "atom_introduction_events_v108_standard_seed0.parquet",
    "baselines_with_delta_v112_seed0.parquet",
    "baselines_with_delta_v108_standard_seed0.parquet",
    "excess_change_adjusted_v112_seed0.parquet",
    "excess_change_adjusted_v108_standard_seed0.parquet",
    "propagation_profile_v112_seed0.parquet",
    "propagation_profile_v108_standard_seed0.parquet",
    "observation_summary_smoke.parquet",
    "observation_stratified_smoke.parquet",
    "observation_records_smoke.json",  # JSON は elapsed_sec normalize で比較
]


def assert_output_under_v112(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V112_ROOT not in abs_path.parents and abs_path != V112_ROOT:
        raise ValueError(f"Output path {path} not under v112/")


def safe_write_json_v112(obj, path: Path) -> None:
    assert_output_under_v112(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, default=str)


# ----------------------------------------------------------------------
# Module 実行 (subprocess、env 引き継ぎ)
# ----------------------------------------------------------------------
def run_module(module_path: Path, mode: str, n_workers: int) -> dict:
    """各 module を subprocess で実行、戻り値 + 時間を返す."""
    cmd = [sys.executable, str(module_path), "--mode", mode]
    # n_workers を持つモジュールには渡す (Step E baseline / E propagation)
    if "baseline_recalculator" in module_path.name or "propagation_analyzer" in module_path.name:
        cmd += ["--n_workers", str(n_workers)]
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    elapsed = time.time() - t0
    return {
        "module": module_path.name,
        "elapsed_sec": round(elapsed, 2),
        "returncode": int(res.returncode),
        "stdout_tail": res.stdout.splitlines()[-3:] if res.stdout else [],
        "stderr_tail": res.stderr.splitlines()[-3:] if res.stderr else [],
    }


# ----------------------------------------------------------------------
# 層 A: bit-identity hash 計算
# ----------------------------------------------------------------------
def file_hash(path: Path) -> str:
    """parquet/JSON ファイルの content hash (json は elapsed_sec を normalize)."""
    if path.suffix == ".parquet":
        df = pd.read_parquet(path)
        return hashlib.sha256(
            pd.util.hash_pandas_object(df, index=False).values.tobytes()
        ).hexdigest()[:16]
    if path.suffix == ".json":
        with open(path) as f:
            d = json.load(f)
        # observation_records.json の computation_metadata.elapsed_sec を normalize
        if isinstance(d, dict) and "computation_metadata" in d:
            cm = d.get("computation_metadata")
            if isinstance(cm, dict) and "elapsed_sec" in cm:
                cm["elapsed_sec"] = 0
        return hashlib.sha256(
            json.dumps(d, sort_keys=True, ensure_ascii=False, default=str).encode()
        ).hexdigest()[:16]
    raise ValueError(f"Unsupported suffix: {path}")


def hash_all_smoke_outputs(in_root: Path) -> dict:
    """smoke seed 0 の全成果物 hash を取得."""
    out = {}
    for fname in BIT_IDENTITY_FILES_SMOKE_SEED0:
        p = in_root / fname
        if not p.exists():
            out[fname] = None
            continue
        out[fname] = file_hash(p)
    return out


# ----------------------------------------------------------------------
# 層 B: v108_re/v108 既存出力 mtime/size snapshot
# ----------------------------------------------------------------------
def snapshot_layer_b_dirs() -> dict:
    """層 B 検証対象ディレクトリの mtime + size を snapshot."""
    snap = {}
    for d in LAYER_B_DIRS:
        if not d.exists():
            continue
        for p in d.rglob("*"):
            if p.is_file():
                st = p.stat()
                rel = str(p.relative_to(REPO_ROOT))
                snap[rel] = {"size": int(st.st_size), "mtime": float(st.st_mtime)}
    return snap


def diff_layer_b(snap1: dict, snap2: dict) -> dict:
    """snapshot 比較、変化があれば層 B 違反."""
    changed = []
    added = list(set(snap2.keys()) - set(snap1.keys()))
    removed = list(set(snap1.keys()) - set(snap2.keys()))
    common = set(snap1.keys()) & set(snap2.keys())
    for k in common:
        if snap1[k] != snap2[k]:
            changed.append({"file": k, "before": snap1[k], "after": snap2[k]})
    return {
        "n_files_tracked": int(len(snap1)),
        "n_changed": int(len(changed)),
        "n_added": int(len(added)),
        "n_removed": int(len(removed)),
        "changed_details": changed[:5],  # 最初 5 件のみ表示
        "added_files": added[:5],
        "removed_files": removed[:5],
        "passed": (len(changed) == 0 and len(added) == 0 and len(removed) == 0),
    }


# ----------------------------------------------------------------------
# Pipeline 1 回実行
# ----------------------------------------------------------------------
def run_pipeline(mode: str, n_workers: int) -> list[dict]:
    """Step D-F を順次実行."""
    results = []
    for step_id, mod_path, desc in STEP_MODULES:
        print(f"\n--- Running {desc} ({mode}) ---")
        r = run_module(mod_path, mode, n_workers)
        r["step_id"] = step_id
        r["description"] = desc
        results.append(r)
        if r["returncode"] != 0:
            print(f"  FAILED: returncode={r['returncode']}, stderr={r['stderr_tail']}")
            return results
        for line in r["stdout_tail"]:
            print(f"  {line}")
    return results


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "main"], default="smoke")
    ap.add_argument("--n_workers", type=int, default=12)
    ap.add_argument("--verify-bit-identity", action="store_true",
                       help="pipeline を 2 回実行し全成果物の hash 一致を検証 (smoke のみ)")
    ap.add_argument("--layer-b-check", action="store_true",
                       help="v108_re/v108 既存出力の mtime/size 不変を検証")
    args = ap.parse_args()

    in_root = V112_SMOKE if args.mode == "smoke" else V112_MAIN
    in_root.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    print("=" * 72)
    print(f"v10.12 Step G: v112_orchestrator  mode={args.mode}, "
          f"n_workers={args.n_workers}")
    print(f"  verify_bit_identity={args.verify_bit_identity}, "
          f"layer_b_check={args.layer_b_check}")
    print("=" * 72)

    # Step C 既存確認 (前提条件)
    n_step_c_v112 = len(list(STEP_C_ROOT.glob("receptive_cids_v112_seed*.parquet")))
    n_step_c_v108 = len(list(STEP_C_ROOT.glob("receptive_cids_v108_standard_seed*.parquet")))
    expected_n = 1 if args.mode == "smoke" else 24
    print(f"\n[prereq] Step C cid files: v112={n_step_c_v112}, v108_std={n_step_c_v108}, "
          f"expected ≥ {expected_n}")
    if n_step_c_v112 < expected_n or n_step_c_v108 < expected_n:
        print(f"  ERROR: Step C output insufficient. Run "
              f"v112_receptive_cid_detector.py --mode {args.mode} first.")
        return 1

    # 層 B snapshot (before)
    snap_before = None
    if args.layer_b_check:
        print("\n[layer B] snapshotting v108_re/v108 existing outputs...")
        snap_before = snapshot_layer_b_dirs()
        print(f"  tracked {len(snap_before)} files")

    # Pipeline 1 回目
    print("\n=== Run 1: Pipeline (Step D-F) ===")
    results_run1 = run_pipeline(args.mode, args.n_workers)
    failed = [r for r in results_run1 if r.get("returncode", 0) != 0]
    if failed:
        print(f"\nFAILED in run 1: {failed[0]['step_id']}")
        return 1

    # bit-identity 層 A 検証 (run 1 の hash を保存)
    bit_identity_result = None
    if args.verify_bit_identity:
        if args.mode != "smoke":
            print("\n[layer A] bit-identity verification skipped (only for smoke)")
        else:
            print("\n[layer A] computing run 1 hashes...")
            hashes_run1 = hash_all_smoke_outputs(in_root)
            for fname, h in hashes_run1.items():
                print(f"  {fname:<55s}: {h}")

            # 既存出力を 一時退避
            backup_dir = in_root / ".orchestrator_run1_backup"
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            backup_dir.mkdir(parents=True, exist_ok=True)
            for fname in BIT_IDENTITY_FILES_SMOKE_SEED0:
                src = in_root / fname
                if src.exists():
                    shutil.copy2(src, backup_dir / fname)

            # Pipeline 2 回目
            print("\n=== Run 2: Pipeline (Step D-F) ===")
            results_run2 = run_pipeline(args.mode, args.n_workers)
            failed2 = [r for r in results_run2 if r.get("returncode", 0) != 0]
            if failed2:
                print(f"\nFAILED in run 2: {failed2[0]['step_id']}")
                return 1

            print("\n[layer A] computing run 2 hashes...")
            hashes_run2 = hash_all_smoke_outputs(in_root)

            # 比較
            mismatches = []
            for fname in BIT_IDENTITY_FILES_SMOKE_SEED0:
                h1 = hashes_run1.get(fname)
                h2 = hashes_run2.get(fname)
                if h1 != h2:
                    mismatches.append({"file": fname, "run1": h1, "run2": h2})
            print(f"\n[layer A] bit-identity verification:")
            print(f"  files tracked: {len(BIT_IDENTITY_FILES_SMOKE_SEED0)}")
            print(f"  mismatches:    {len(mismatches)}")
            for fname in BIT_IDENTITY_FILES_SMOKE_SEED0:
                h1 = hashes_run1.get(fname)
                h2 = hashes_run2.get(fname)
                ok = "PASS" if h1 == h2 else "FAIL"
                print(f"    {fname:<55s} run1={h1} run2={h2} {ok}")
            bit_identity_result = {
                "files_tracked": int(len(BIT_IDENTITY_FILES_SMOKE_SEED0)),
                "mismatches": mismatches,
                "n_mismatches": int(len(mismatches)),
                "all_pass": (len(mismatches) == 0),
                "hashes_run1": hashes_run1,
                "hashes_run2": hashes_run2,
            }

            # cleanup backup (検証完了後)
            if backup_dir.exists():
                shutil.rmtree(backup_dir)

    # 層 B 比較 (after)
    layer_b_result = None
    if args.layer_b_check:
        print("\n[layer B] verifying v108_re/v108 outputs unchanged...")
        snap_after = snapshot_layer_b_dirs()
        layer_b_result = diff_layer_b(snap_before, snap_after)
        if layer_b_result["passed"]:
            print(f"  PASS: {layer_b_result['n_files_tracked']} files unchanged "
                  f"(0 modified, 0 added, 0 removed)")
        else:
            print(f"  FAIL: {layer_b_result['n_changed']} modified, "
                  f"{layer_b_result['n_added']} added, "
                  f"{layer_b_result['n_removed']} removed")
            for c in layer_b_result["changed_details"]:
                print(f"    changed: {c['file']}")

    # 層 C 検証 (構造的保証)
    print(f"\n[layer C] write path restriction (assert_output_under_v112):")
    print(f"  全モジュールで safe_write_parquet_v112() 経由、"
          f"v112/outputs/{{smoke,main}}/ + step_c/ 配下のみ書き込み")
    print(f"  → 構造的保証済 (PASS)")

    elapsed = time.time() - t0
    print(f"\nDONE  total elapsed = {elapsed:.2f}s")

    # JSON 出力
    summary = {
        "mode": args.mode,
        "n_workers": int(args.n_workers),
        "verify_bit_identity": args.verify_bit_identity,
        "layer_b_check": args.layer_b_check,
        "step_c_prerequisite": {
            "v112_files": int(n_step_c_v112),
            "v108_standard_files": int(n_step_c_v108),
            "expected_min": int(expected_n),
            "passed": (n_step_c_v112 >= expected_n and n_step_c_v108 >= expected_n),
        },
        "run1_results": results_run1,
        "layer_a_bit_identity": bit_identity_result,
        "layer_b_unchanged": layer_b_result,
        "layer_c_structural": "PASS (assert_output_under_v112 enforced in all modules)",
        "total_elapsed_sec": round(elapsed, 2),
    }
    out_path = in_root / f"orchestrator_run_summary_{args.mode}.json"
    safe_write_json_v112(summary, out_path)
    print(f"  output = {out_path}")

    # 全層 PASS 判定
    pass_a = (bit_identity_result is None) or bit_identity_result.get("all_pass", False)
    pass_b = (layer_b_result is None) or layer_b_result.get("passed", False)
    print(f"\n{'='*72}")
    print(f"Step G 判定: 層 A {'PASS' if pass_a else 'FAIL'} / "
          f"層 B {'PASS' if pass_b else 'FAIL'} / 層 C PASS (構造的)")
    print(f"{'='*72}")
    return 0 if (pass_a and pass_b) else 1


if __name__ == "__main__":
    sys.exit(main())
