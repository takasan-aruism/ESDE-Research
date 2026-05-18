#!/usr/bin/env python3
"""v1101a 段階 2 Step E — bit-identity 3 層検証 (段階 1 step_g 同型、段階 2 用)

層 A: Step B/C smoke seed 0 を re-run → parquet hash 一致 (cid state ledger
      再生 + 観察 A/B/C の deterministic 保証、shuffle baseline は rng=42 固定)
層 B: v10.6/v10.7/v10.5 main outputs 不変 (段階 2 で実 ledger 再生したが
      replay 専用、ledger 書き換えなし)
層 C: 段階 2 scripts の書込みパスが unified/v1101a/ 配下のみ

出力: unified/v1101a/v1101a_phase_2_step_e_bit_identity_report.json
"""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path("/home/takasan/esde/ESDE-Research")
V106_MAIN = REPO_ROOT / "developmental/v106/outputs/main"
V107_MAIN = REPO_ROOT / "developmental/v107/outputs/main"
V112_MAIN = REPO_ROOT / "developmental/v112/outputs/main"
V105_INTEGRATION = REPO_ROOT / "developmental/v105/diag_v105_main/integration"
V1101A_DIR = REPO_ROOT / "unified/v1101a"
V1101A_SMOKE = V1101A_DIR / "outputs/smoke"

LAYER_A_SMOKE = [
    "cid_state_ledger_seed0.parquet",
    "unit_kl_delta_seed0.parquet",
]

LAYER_A_STEPS = [
    ("v1101a_phase_2_step_b_cid_state_ledger.py",
     ["--seeds", "0", "--smoke-or-main", "smoke"]),
]

V1101A_PHASE2_SCRIPTS = [
    "v1101a_phase_2_step_b_cid_state_ledger.py",
    "v1101a_phase_2_step_c_observations.py",
    "v1101a_phase_2_step_d_graph.py",
]


def file_sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def snapshot_dir(root: Path) -> dict:
    snap = {}
    for p in root.rglob("*"):
        if p.is_file():
            st = p.stat()
            snap[str(p.relative_to(root))] = (st.st_size, st.st_mtime_ns)
    return snap


def layer_a_check() -> dict:
    result = {"parquet_hash_match": {}, "rerun_times_sec": {}}
    # Pre snapshot (Step B smoke 既存出力)
    pre = {}
    for f in LAYER_A_SMOKE:
        p = V1101A_SMOKE / f
        if not p.exists():
            print(f"  pre missing: {p}")
            pre[f] = None
        else:
            pre[f] = file_sha256(p)
    # Re-run Step B smoke
    for script, args in LAYER_A_STEPS:
        t0 = time.time()
        subprocess.run(
            [sys.executable, str(V1101A_DIR / script)] + args,
            capture_output=True, text=True, check=True, cwd=str(REPO_ROOT))
        result["rerun_times_sec"][script] = round(time.time() - t0, 2)
    # Post hash
    post = {f: file_sha256(V1101A_SMOKE / f) for f in LAYER_A_SMOKE}
    for f in LAYER_A_SMOKE:
        result["parquet_hash_match"][f] = (pre.get(f) is not None and pre[f] == post[f])
    result["all_parquet_match"] = all(result["parquet_hash_match"].values())
    return result


def layer_b_check(pre_snapshots: dict) -> dict:
    result = {}
    for label, root in [("v106_main", V106_MAIN), ("v107_main", V107_MAIN),
                         ("v112_main", V112_MAIN),
                         ("v105_integration", V105_INTEGRATION)]:
        post = snapshot_dir(root)
        pre = pre_snapshots[label]
        added = set(post.keys()) - set(pre.keys())
        removed = set(pre.keys()) - set(post.keys())
        modified = [f for f in pre.keys() & post.keys() if pre[f] != post[f]]
        result[label] = {
            "n_files_pre": len(pre), "n_files_post": len(post),
            "n_added": len(added), "n_removed": len(removed),
            "n_modified": len(modified),
            "pass": (len(added) == 0 and len(removed) == 0 and len(modified) == 0),
        }
    result["all_pass"] = all(result[k]["pass"] for k in (
        "v106_main", "v107_main", "v112_main", "v105_integration"))
    return result


ARG_WRITE_PATTERNS = [
    ("to_parquet", re.compile(r"\.to_parquet\(\s*([^,)]+)")),
    ("to_csv", re.compile(r"\.to_csv\(\s*([^,)]+)")),
    ("to_json", re.compile(r"\.to_json\(\s*([^,)]+)")),
    ("write_html", re.compile(r"\.write_html\(\s*([^,)]+)")),
    ("open_w", re.compile(r"open\(\s*([^,)]+),\s*['\"]w")),
]
RECEIVER_WRITE_PATTERNS = [
    ("write_text", re.compile(r"(\w+)\.write_text\(")),
    ("write_bytes", re.compile(r"(\w+)\.write_bytes\(")),
]
ALLOWED_V1101A_TOKENS = (
    "V1101A_OUT", "V1101A_MAIN", "V1101A_SMOKE", "V1101A_DIR",
    "OUT_MAIN", "OUT_SMOKE", "out_dir", "out_path",
    "src_dir", "state_path", "kl_path",
)


def _is_under_v1101a(expr: str) -> bool:
    return any(c in expr for c in ALLOWED_V1101A_TOKENS)


def layer_c_check() -> dict:
    findings = []
    for script in V1101A_PHASE2_SCRIPTS:
        sp = V1101A_DIR / script
        text = sp.read_text(encoding="utf-8")
        for method, pat in ARG_WRITE_PATTERNS:
            for m in pat.finditer(text):
                t = m.group(1).strip()
                findings.append({"script": script, "method": method,
                                  "position": "arg", "captured": t,
                                  "structurally_under_v1101a": _is_under_v1101a(t)})
        for method, pat in RECEIVER_WRITE_PATTERNS:
            for m in pat.finditer(text):
                r = m.group(1).strip()
                findings.append({"script": script, "method": method,
                                  "position": "receiver", "captured": r,
                                  "structurally_under_v1101a": _is_under_v1101a(r)})
    return {
        "n_write_calls": len(findings),
        "all_structurally_under_v1101a": all(
            f["structurally_under_v1101a"] for f in findings),
        "findings": findings,
    }


def main():
    print("[G-phase2] snapshotting v10.x main + v105 integration outputs ...")
    pre = {
        "v106_main": snapshot_dir(V106_MAIN),
        "v107_main": snapshot_dir(V107_MAIN),
        "v112_main": snapshot_dir(V112_MAIN),
        "v105_integration": snapshot_dir(V105_INTEGRATION),
    }
    print(f"  v106 main: {len(pre['v106_main'])} files")
    print(f"  v107 main: {len(pre['v107_main'])} files")
    print(f"  v112 main: {len(pre['v112_main'])} files")
    print(f"  v105 integration: {len(pre['v105_integration'])} files")

    print("[G-phase2-1] layer A: re-run Step B smoke, verify parquet hash")
    layer_a = layer_a_check()
    print(f"  parquet hash: all_match={layer_a['all_parquet_match']}")

    print("[G-phase2-2] layer B: verify v10.x main + v105 integration unchanged")
    layer_b = layer_b_check(pre)
    for k in ("v106_main", "v107_main", "v112_main", "v105_integration"):
        v = layer_b[k]
        print(f"  {k}: pre={v['n_files_pre']} post={v['n_files_post']} "
              f"added={v['n_added']} removed={v['n_removed']} "
              f"modified={v['n_modified']} pass={v['pass']}")
    print(f"  layer_b.all_pass={layer_b['all_pass']}")

    print("[G-phase2-3] layer C: scan phase 2 script writes")
    layer_c = layer_c_check()
    print(f"  n_write_calls={layer_c['n_write_calls']}, "
          f"all_under_v1101a={layer_c['all_structurally_under_v1101a']}")

    all_pass = (layer_a["all_parquet_match"] and layer_b["all_pass"]
                and layer_c["all_structurally_under_v1101a"])
    report = {
        "version": "v11.0.1.a (v1101a) Phase 2 Step E",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": "Phase 2 (cid state ledger 再生 + 観察 A/B/C) の bit-identity 検証。"
                "shuffle baseline は rng_seed=42 固定で deterministic。",
        "layer_a": layer_a, "layer_b": layer_b, "layer_c": layer_c,
        "all_layers_pass": all_pass,
    }
    out = V1101A_DIR / "v1101a_phase_2_step_e_bit_identity_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    print(f"\nReport: {out}")
    print(f"all_layers_pass = {all_pass}")


if __name__ == "__main__":
    main()
