#!/usr/bin/env python3
"""v1101 Step G — bit-identity 3 層検証

層 A: Step C/D/E 再実行 hash 一致 (deterministic 動作確認)
       (Step F HTML は plotly UUID 由来非決定性、構造比較のみ)
層 B: v10.6 / v10.8 / v10.12 main outputs の全 file mtime + size 不変確認
層 C: Step C-F の .py script の書き込みパス scan、unified/v1101/ 配下のみ確認

出力:
  unified/v1101/outputs/v1101_step_g_bit_identity_report.json
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

V106_MAIN = Path("/home/takasan/esde/ESDE-Research/developmental/v106/outputs/main")
V108_MAIN = Path("/home/takasan/esde/ESDE-Research/developmental/v108/outputs/main")
V112_MAIN = Path("/home/takasan/esde/ESDE-Research/developmental/v112/outputs/main")
V1101_DIR = Path("/home/takasan/esde/ESDE-Research/unified/v1101")
V1101_MAIN = V1101_DIR / "outputs" / "main"
V1101_OUT = V1101_DIR / "outputs"

LAYER_A_PARQUETS = [
    "observation_1_center_cids.parquet",
    "observation_1_random_cids.parquet",
    "observation_1_trajectory.parquet",
    "observation_1_summary.parquet",
    "observation_2_events.parquet",
    "observation_2_propagation.parquet",
    "observation_2_summary.parquet",
    "observation_3_cid_atom_distribution.parquet",
    "observation_3_integration_summary.parquet",
    "observation_3_esde_aggregate.parquet",
]
LAYER_A_SCRIPTS = [
    "v1101_step_c_observation_1.py",
    "v1101_step_d_observation_2.py",
    "v1101_step_e_observation_3.py",
]
STEP_F_SCRIPT = "v1101_step_f_graph_html.py"
STEP_F_HTML = V1101_OUT / "v1101_observation.html"

V1101_SCRIPTS = LAYER_A_SCRIPTS + [STEP_F_SCRIPT]


def file_sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# --- 層 A ---
def layer_a_check() -> dict:
    """Step C/D/E 再実行 hash 一致 + Step F HTML 構造比較."""
    result = {"parquet_hash_match": {}, "html_structural": {}, "rerun_times_sec": {}}
    # Pre snapshot
    pre = {f: file_sha256(V1101_MAIN / f) for f in LAYER_A_PARQUETS}
    pre_html_size = STEP_F_HTML.stat().st_size
    pre_html_text = STEP_F_HTML.read_text(encoding="utf-8")
    pre_n_div = pre_html_text.count("plotly-graph-div")
    pre_n_plot = pre_html_text.count("Plotly.newPlot")
    pre_n_h2 = pre_html_text.count("<h2>")

    # Re-run Step C/D/E
    for script in LAYER_A_SCRIPTS:
        t0 = time.time()
        proc = subprocess.run(
            [sys.executable, str(V1101_DIR / script)],
            capture_output=True, text=True, check=True,
            cwd="/home/takasan/esde/ESDE-Research",
        )
        result["rerun_times_sec"][script] = round(time.time() - t0, 2)

    # Re-hash and compare
    post = {f: file_sha256(V1101_MAIN / f) for f in LAYER_A_PARQUETS}
    for f in LAYER_A_PARQUETS:
        result["parquet_hash_match"][f] = (pre[f] == post[f])

    # Re-run Step F
    t0 = time.time()
    subprocess.run(
        [sys.executable, str(V1101_DIR / STEP_F_SCRIPT)],
        capture_output=True, text=True, check=True,
        cwd="/home/takasan/esde/ESDE-Research",
    )
    result["rerun_times_sec"][STEP_F_SCRIPT] = round(time.time() - t0, 2)

    post_html_text = STEP_F_HTML.read_text(encoding="utf-8")
    post_html_size = STEP_F_HTML.stat().st_size

    result["html_structural"] = {
        "plotly_graph_div_count_match": (pre_n_div == post_html_text.count("plotly-graph-div") == 5),
        "Plotly_newPlot_count_match": (pre_n_plot == post_html_text.count("Plotly.newPlot") == 5),
        "h2_section_count_match": (pre_n_h2 == post_html_text.count("<h2>") == 4),
        "size_pre_bytes": pre_html_size,
        "size_post_bytes": post_html_size,
        "size_diff_bytes": post_html_size - pre_html_size,
        "note": "HTML byte-identity NOT guaranteed (plotly UUID div IDs random); structural identity verified",
    }

    result["all_parquet_match"] = all(result["parquet_hash_match"].values())
    return result


# --- 層 B ---
def snapshot_dir(root: Path) -> dict:
    """root 以下の全 file の (size, mtime_ns) snapshot."""
    snap = {}
    for p in root.rglob("*"):
        if p.is_file():
            st = p.stat()
            snap[str(p.relative_to(root))] = (st.st_size, st.st_mtime_ns)
    return snap


def layer_b_check(pre_snapshots: dict) -> dict:
    """v10.x main outputs の不変確認."""
    result = {}
    for label, root in [("v106_main", V106_MAIN), ("v108_main", V108_MAIN), ("v112_main", V112_MAIN)]:
        post = snapshot_dir(root)
        pre = pre_snapshots[label]
        all_files = set(pre.keys()) | set(post.keys())
        added = set(post.keys()) - set(pre.keys())
        removed = set(pre.keys()) - set(post.keys())
        modified = [f for f in pre.keys() & post.keys() if pre[f] != post[f]]
        result[label] = {
            "n_files_pre": len(pre),
            "n_files_post": len(post),
            "n_added": len(added),
            "n_removed": len(removed),
            "n_modified": len(modified),
            "added_samples": sorted(list(added))[:5],
            "removed_samples": sorted(list(removed))[:5],
            "modified_samples": sorted(modified)[:5],
            "pass": (len(added) == 0 and len(removed) == 0 and len(modified) == 0),
        }
    result["all_pass"] = all(result[k]["pass"] for k in ("v106_main", "v108_main", "v112_main"))
    return result


# --- 層 C ---
# Arg-position patterns (path = first arg): DataFrame.to_*, fig.write_html(path)
ARG_WRITE_PATTERNS = [
    ("to_parquet", re.compile(r"\.to_parquet\(\s*([^,)]+)")),
    ("to_csv",     re.compile(r"\.to_csv\(\s*([^,)]+)")),
    ("to_json",    re.compile(r"\.to_json\(\s*([^,)]+)")),
    ("write_html", re.compile(r"\.write_html\(\s*([^,)]+)")),  # plotly fig.write_html
    ("open_w",     re.compile(r"open\(\s*([^,)]+),\s*['\"]w")),
]
# Receiver-position patterns (path = receiver, content = first arg): Path.write_text/write_bytes
RECEIVER_WRITE_PATTERNS = [
    ("write_text",  re.compile(r"(\w+)\.write_text\(")),
    ("write_bytes", re.compile(r"(\w+)\.write_bytes\(")),
]
ALLOWED_V1101_CONSTANTS = ("V1101_OUT", "V1101_MAIN", "HTML_OUT", "V1101_DIR")


def _is_under_v1101(expr: str) -> bool:
    return any(c in expr for c in ALLOWED_V1101_CONSTANTS)


def layer_c_check() -> dict:
    """script 内の書き込みパスを scan、unified/v1101/ 配下のみであることを確認."""
    findings = []
    for script in V1101_SCRIPTS:
        sp = V1101_DIR / script
        text = sp.read_text(encoding="utf-8")
        # Arg-position writes (path in first arg)
        for method, pat in ARG_WRITE_PATTERNS:
            for m in pat.finditer(text):
                target = m.group(1).strip()
                findings.append({
                    "script": script,
                    "method": method,
                    "position": "arg",
                    "captured": target,
                    "structurally_under_v1101": _is_under_v1101(target),
                })
        # Receiver-position writes (path is the receiver before the dot)
        for method, pat in RECEIVER_WRITE_PATTERNS:
            for m in pat.finditer(text):
                receiver = m.group(1).strip()
                findings.append({
                    "script": script,
                    "method": method,
                    "position": "receiver",
                    "captured": receiver,
                    "structurally_under_v1101": _is_under_v1101(receiver),
                })
    all_under_v1101 = all(f["structurally_under_v1101"] for f in findings)
    return {
        "n_write_calls": len(findings),
        "all_structurally_under_v1101": all_under_v1101,
        "allowed_constants": list(ALLOWED_V1101_CONSTANTS),
        "findings": findings,
    }


def main():
    print("[G] snapshotting v10.x main outputs ...")
    pre = {
        "v106_main": snapshot_dir(V106_MAIN),
        "v108_main": snapshot_dir(V108_MAIN),
        "v112_main": snapshot_dir(V112_MAIN),
    }
    print(f"  v106 main: {len(pre['v106_main'])} files")
    print(f"  v108 main: {len(pre['v108_main'])} files")
    print(f"  v112 main: {len(pre['v112_main'])} files")

    print("[G-1] layer A: re-run Step C/D/E/F and verify parquet hash + HTML structure")
    layer_a = layer_a_check()
    n_pass = sum(layer_a["parquet_hash_match"].values())
    n_total = len(layer_a["parquet_hash_match"])
    print(f"  parquet hash: {n_pass}/{n_total} match, all_parquet_match={layer_a['all_parquet_match']}")
    print(f"  HTML structural: divs={layer_a['html_structural']['plotly_graph_div_count_match']}, "
          f"plots={layer_a['html_structural']['Plotly_newPlot_count_match']}, "
          f"h2={layer_a['html_structural']['h2_section_count_match']}")

    print("[G-2] layer B: verify v10.x main outputs unchanged after re-run")
    layer_b = layer_b_check(pre)
    for k in ("v106_main", "v108_main", "v112_main"):
        v = layer_b[k]
        print(f"  {k}: pre={v['n_files_pre']} post={v['n_files_post']} added={v['n_added']} removed={v['n_removed']} modified={v['n_modified']} pass={v['pass']}")
    print(f"  layer_b.all_pass={layer_b['all_pass']}")

    print("[G-3] layer C: scan script writes for structural v1101 compliance")
    layer_c = layer_c_check()
    print(f"  n_write_calls={layer_c['n_write_calls']}, all_under_v1101={layer_c['all_structurally_under_v1101']}")

    report = {
        "version": "v11.0.1 (v1101) Step G",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "layer_a": layer_a,
        "layer_b": layer_b,
        "layer_c": layer_c,
        "all_layers_pass": (
            layer_a["all_parquet_match"]
            and layer_a["html_structural"]["plotly_graph_div_count_match"]
            and layer_a["html_structural"]["Plotly_newPlot_count_match"]
            and layer_a["html_structural"]["h2_section_count_match"]
            and layer_b["all_pass"]
            and layer_c["all_structurally_under_v1101"]
        ),
    }
    out_path = V1101_OUT / "v1101_step_g_bit_identity_report.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReport written: {out_path}")
    print(f"all_layers_pass = {report['all_layers_pass']}")


if __name__ == "__main__":
    main()
