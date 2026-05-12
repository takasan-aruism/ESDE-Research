#!/usr/bin/env python3
"""v10.13.a Step B: 環境チェック + 層 B baseline 記録.

層 B 検証用に v107/v108/v109/v110/v111/v112 既存出力の mtime + size を snapshot.
Step I の bit-identity 検証で本 baseline と再比較し、~1,500 files の不変を確認.

入力確認:
  - developmental/v112/outputs/main/ (excess_change_adjusted, propagation_profile 等)
  - developmental/v107/outputs/main/ (source_events, excess_change)
  - developmental/v105/diag_v105_main_v2/ (ledger、long phase で再走査用)

出力:
  - developmental/v113a/outputs/main/layer_b_baseline.json
  - developmental/v113a/outputs/main/step_b_environment.json

規律:
  - 物理層 frozen (絶対格言 #2): 既存出力 read-only
  - 層 C (assert_output_under_v113a): v113a/ 配下のみ書き込み
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V113A_ROOT = (REPO_ROOT / "developmental" / "v113a").resolve()
V113A_OUT = V113A_ROOT / "outputs" / "main"

# 層 B 検証対象ディレクトリ
LAYER_B_DIRS = [
    REPO_ROOT / "developmental" / "v107" / "outputs" / "main",
    REPO_ROOT / "developmental" / "v108" / "outputs" / "main",
    REPO_ROOT / "developmental" / "v109" / "outputs" / "main",
    REPO_ROOT / "developmental" / "v110" / "outputs" / "main",
    REPO_ROOT / "developmental" / "v110" / "v108_re" / "outputs" / "main",
    REPO_ROOT / "developmental" / "v111" / "outputs" / "main",
    REPO_ROOT / "developmental" / "v112" / "outputs" / "main",
    REPO_ROOT / "developmental" / "v112" / "outputs" / "step_c",
]

# 主入力確認対象
REQUIRED_INPUTS = {
    "v112_excess_change_adjusted": [
        f"developmental/v112/outputs/main/excess_change_adjusted_v112_seed{n}.parquet"
        for n in range(24)
    ],
    "v112_excess_change_adjusted_v108_standard": [
        f"developmental/v112/outputs/main/excess_change_adjusted_v108_standard_seed{n}.parquet"
        for n in range(24)
    ],
    "v112_propagation_profile_v112": [
        f"developmental/v112/outputs/main/propagation_profile_v112_seed{n}.parquet"
        for n in range(24)
    ],
    "v112_propagation_profile_v108_standard": [
        f"developmental/v112/outputs/main/propagation_profile_v108_standard_seed{n}.parquet"
        for n in range(24)
    ],
    "v107_source_events": [
        f"developmental/v107/outputs/main/source_events_seed{n}.parquet"
        for n in range(24)
    ],
    "v107_excess_change": [
        f"developmental/v107/outputs/main/excess_change_seed{n}.parquet"
        for n in range(24)
    ],
}


def assert_output_under_v113a(path: Path) -> None:
    abs_path = Path(path).resolve()
    if V113A_ROOT not in abs_path.parents and abs_path != V113A_ROOT:
        raise ValueError(f"Output path {path} not under v113a/")


def safe_write_json_v113a(obj, path: Path) -> None:
    assert_output_under_v113a(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, default=str)


def snapshot_layer_b() -> dict:
    """層 B 検証対象の mtime + size を snapshot."""
    snap = {}
    for d in LAYER_B_DIRS:
        if not d.exists():
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file():
                st = p.stat()
                rel = str(p.relative_to(REPO_ROOT))
                snap[rel] = {"size": int(st.st_size), "mtime_ns": int(st.st_mtime_ns)}
    return snap


def check_required_inputs() -> dict:
    """主入力ファイルの存在確認."""
    out = {}
    for name, paths in REQUIRED_INPUTS.items():
        missing = []
        existing = 0
        for p in paths:
            full = REPO_ROOT / p
            if full.exists():
                existing += 1
            else:
                missing.append(p)
        out[name] = {
            "n_expected": len(paths),
            "n_existing": existing,
            "n_missing": len(missing),
            "missing": missing[:5],
            "all_present": len(missing) == 0,
        }
    return out


def main() -> int:
    t0 = time.time()
    print("=" * 72)
    print("v10.13.a Step B: 環境チェック + 層 B baseline 記録")
    print("=" * 72)

    V113A_OUT.mkdir(parents=True, exist_ok=True)
    print(f"\n[output dir] {V113A_OUT} created/verified")

    print(f"\n[input check] 主入力ファイル存在確認...")
    input_check = check_required_inputs()
    for name, info in input_check.items():
        status = "OK" if info["all_present"] else f"MISSING {info['n_missing']}"
        print(f"  {name:<50s} {info['n_existing']:>3d}/{info['n_expected']:<3d}  {status}")

    print(f"\n[layer B baseline] snapshotting ~1500 files...")
    snap = snapshot_layer_b()
    total_size = sum(f["size"] for f in snap.values())
    print(f"  tracked: {len(snap)} files, total size: {total_size / 1024 / 1024:.1f} MB")

    # ディレクトリ別内訳
    by_dir = {}
    for rel in snap.keys():
        top_dir = rel.split("/")[0] + "/" + rel.split("/")[1] if "/" in rel else rel
        by_dir.setdefault(top_dir, 0)
        by_dir[top_dir] += 1
    for d, n in sorted(by_dir.items()):
        print(f"    {d:<35s} {n:>4d} files")

    # snapshot hash (一括検証用)
    snap_json = json.dumps(snap, sort_keys=True)
    snap_hash = hashlib.sha256(snap_json.encode()).hexdigest()[:16]
    print(f"  layer_b_baseline hash: {snap_hash}")

    # 出力
    safe_write_json_v113a(snap, V113A_OUT / "layer_b_baseline.json")
    env_summary = {
        "step": "B",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "input_check": input_check,
        "layer_b": {
            "n_files": len(snap),
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "baseline_hash": snap_hash,
            "by_dir": by_dir,
        },
        "all_inputs_present": all(info["all_present"] for info in input_check.values()),
        "elapsed_sec": round(time.time() - t0, 2),
    }
    safe_write_json_v113a(env_summary, V113A_OUT / "step_b_environment.json")

    elapsed = time.time() - t0
    print(f"\nDONE  elapsed = {elapsed:.2f}s")
    print(f"  layer_b_baseline.json + step_b_environment.json written to {V113A_OUT}")

    if not env_summary["all_inputs_present"]:
        print(f"\nWARNING: 一部入力ファイル不在、Step C 着手前に確認必要")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
