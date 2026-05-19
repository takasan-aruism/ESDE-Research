#!/usr/bin/env python3
"""v1102 Step E — bit-identity 3 層検証 (v1101a 同型)

層 A: Step B/C smoke 再実行 → parquet hash 一致
層 B: v10.6/v10.7/v10.5/v11.0.1.a main outputs 不変
層 C: 段階 2 scripts 書込みパスが unified/v1102/ 配下のみ

出力: unified/v1102/v1102_step_e_bit_identity_report.json
"""
from __future__ import annotations
import hashlib, json, re, subprocess, sys, time
from pathlib import Path

REPO_ROOT = Path("/home/takasan/esde/ESDE-Research")
V106_MAIN = REPO_ROOT / "developmental/v106/outputs/main"
V107_MAIN = REPO_ROOT / "developmental/v107/outputs/main"
V112_MAIN = REPO_ROOT / "developmental/v112/outputs/main"
V105_INTEGRATION = REPO_ROOT / "developmental/v105/diag_v105_main/integration"
V1101A_MAIN = REPO_ROOT / "unified/v1101a/outputs/main"
V1102_DIR = REPO_ROOT / "unified/v1102"
V1102_SMOKE = V1102_DIR / "outputs/smoke"

LAYER_A_SMOKE = ["primary_table.parquet"]
LAYER_A_STEPS = [
    ("v1102_step_b_primary_table.py", ["--seeds", "0", "--smoke-or-main", "smoke"]),
]
V1102_SCRIPTS = [
    "v1102_step_b_primary_table.py",
    "v1102_step_c_outstanding_extraction.py",
    "v1102_step_d_graph.py",
]

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
ALLOWED_V1102_TOKENS = ("V1102_OUT","V1102_MAIN","V1102_SMOKE","V1102_DIR","V1102_ROOT",
                        "OUT_MAIN","OUT_SMOKE","OUT_DIR","out_dir","out_path","src_dir","out")


def file_sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def snapshot_dir(root):
    snap = {}
    for p in root.rglob("*"):
        if p.is_file():
            st = p.stat()
            snap[str(p.relative_to(root))] = (st.st_size, st.st_mtime_ns)
    return snap


def layer_a_check():
    result = {"parquet_hash_match": {}, "rerun_times_sec": {}}
    pre = {f: file_sha256(V1102_SMOKE / f) if (V1102_SMOKE / f).exists() else None
           for f in LAYER_A_SMOKE}
    for script, args in LAYER_A_STEPS:
        t0 = time.time()
        subprocess.run([sys.executable, str(V1102_DIR / script)] + args,
                       capture_output=True, text=True, check=True, cwd=str(REPO_ROOT))
        result["rerun_times_sec"][script] = round(time.time() - t0, 2)
    post = {f: file_sha256(V1102_SMOKE / f) for f in LAYER_A_SMOKE}
    for f in LAYER_A_SMOKE:
        result["parquet_hash_match"][f] = (pre.get(f) is not None and pre[f] == post[f])
    result["all_parquet_match"] = all(result["parquet_hash_match"].values())
    return result


def layer_b_check(pre):
    result = {}
    for label, root in [("v106_main", V106_MAIN), ("v107_main", V107_MAIN),
                         ("v112_main", V112_MAIN), ("v105_integration", V105_INTEGRATION),
                         ("v1101a_main", V1101A_MAIN)]:
        post = snapshot_dir(root)
        added = set(post.keys()) - set(pre[label].keys())
        removed = set(pre[label].keys()) - set(post.keys())
        modified = [f for f in pre[label].keys() & post.keys() if pre[label][f] != post[f]]
        result[label] = {
            "n_files_pre": len(pre[label]), "n_files_post": len(post),
            "n_added": len(added), "n_removed": len(removed), "n_modified": len(modified),
            "pass": (len(added)==0 and len(removed)==0 and len(modified)==0),
        }
    result["all_pass"] = all(result[k]["pass"] for k in
                              ("v106_main","v107_main","v112_main","v105_integration","v1101a_main"))
    return result


def _is_under(expr):
    return any(c in expr for c in ALLOWED_V1102_TOKENS)


def layer_c_check():
    findings = []
    for script in V1102_SCRIPTS:
        text = (V1102_DIR / script).read_text(encoding="utf-8")
        for method, pat in ARG_WRITE_PATTERNS:
            for m in pat.finditer(text):
                t = m.group(1).strip()
                findings.append({"script": script, "method": method, "captured": t,
                                  "under_v1102": _is_under(t)})
        for method, pat in RECEIVER_WRITE_PATTERNS:
            for m in pat.finditer(text):
                r = m.group(1).strip()
                findings.append({"script": script, "method": method, "captured": r,
                                  "under_v1102": _is_under(r)})
    return {"n_write_calls": len(findings),
            "all_under_v1102": all(f["under_v1102"] for f in findings),
            "findings": findings}


def main():
    print("[G-v1102] snapshotting v10.x + v1101a main outputs ...")
    pre = {
        "v106_main": snapshot_dir(V106_MAIN),
        "v107_main": snapshot_dir(V107_MAIN),
        "v112_main": snapshot_dir(V112_MAIN),
        "v105_integration": snapshot_dir(V105_INTEGRATION),
        "v1101a_main": snapshot_dir(V1101A_MAIN),
    }
    for k, v in pre.items():
        print(f"  {k}: {len(v)} files")

    print("[A] layer A: re-run Step B smoke, parquet hash match")
    la = layer_a_check()
    print(f"  all_parquet_match={la['all_parquet_match']}, rerun={la['rerun_times_sec']}")

    print("[B] layer B: v10.x + v1101a main outputs frozen")
    lb = layer_b_check(pre)
    for k in pre.keys():
        v = lb[k]
        print(f"  {k}: pre={v['n_files_pre']} post={v['n_files_post']} "
              f"add={v['n_added']} rem={v['n_removed']} mod={v['n_modified']} pass={v['pass']}")
    print(f"  layer_b.all_pass={lb['all_pass']}")

    print("[C] layer C: v1102 script writes under unified/v1102/")
    lc = layer_c_check()
    print(f"  n_write_calls={lc['n_write_calls']}, all_under_v1102={lc['all_under_v1102']}")

    all_pass = la['all_parquet_match'] and lb['all_pass'] and lc['all_under_v1102']
    report = {
        "version": "v11.0.2 (v1102) Step E",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "layer_a": la, "layer_b": lb, "layer_c": lc,
        "all_layers_pass": all_pass,
    }
    out = V1102_DIR / "v1102_step_e_bit_identity_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReport: {out}")
    print(f"all_layers_pass = {all_pass}")


if __name__ == "__main__":
    main()
