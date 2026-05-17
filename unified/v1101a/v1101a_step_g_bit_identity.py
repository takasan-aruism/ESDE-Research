#!/usr/bin/env python3
"""v1101a Step G — bit-identity 3 層検証 (v1101 step G 同型)

層 A: Step C/D/E を smoke seed 0 で再実行 → 既存 smoke 出力との hash 一致
      (main 24 seeds は Step C で 16 分かかるため smoke 代用、本主題 deterministic)
      Step F は main から HTML 再生成 → 構造比較 (plotly UUID 非決定性のため)
層 B: v10.5 / v10.6 / v10.7 main outputs の全 file mtime + size 不変
層 C: Step C-F の .py script の書き込みパス scan、unified/v1101a/ 配下のみ

出力: unified/v1101a/v1101a_step_g_bit_identity_report.json
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
V105_INTEGRATION = REPO_ROOT / "developmental/v105/diag_v105_main/integration"
V1101A_DIR = REPO_ROOT / "unified/v1101a"
V1101A_MAIN = V1101A_DIR / "outputs/main"
V1101A_SMOKE = V1101A_DIR / "outputs/smoke"
V1101A_OUT = V1101A_DIR / "outputs"

# 層 A: smoke seed 0 出力 (Step C/D/E)
LAYER_A_SMOKE_PARQUETS = [
    "attention_emit_seed0.parquet",
    "attention_propagation_seed0.parquet",
    "attention_causality_seed0.parquet",
]

LAYER_A_STEP_C_D_E = [
    ("v1101a_step_c_attention_emit.py", ["--seeds", "0", "--smoke-or-main", "smoke"]),
    ("v1101a_step_d_attention_propagation.py", ["--seeds", "0", "--smoke-or-main", "smoke"]),
    ("v1101a_step_e_attention_causality.py", ["--seeds", "0", "--smoke-or-main", "smoke"]),
]

# Step F は main データから HTML 生成
STEP_F_SCRIPT = "v1101a_step_f_graph_html.py"
STEP_F_HTML_MAIN = V1101A_OUT / "v1101a_observation.html"
STEP_F_HTML_TOPK = V1101A_OUT / "v1101a_topk_attention_candidates.html"

V1101A_SCRIPTS = [s for s, _ in LAYER_A_STEP_C_D_E] + [STEP_F_SCRIPT]


def file_sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# --- 層 A ---
def layer_a_check() -> dict:
    result = {"parquet_hash_match": {}, "html_structural": {}, "rerun_times_sec": {}}

    # Pre snapshot (smoke 既存出力)
    pre = {}
    for f in LAYER_A_SMOKE_PARQUETS:
        p = V1101A_SMOKE / f
        if not p.exists():
            print(f"  WARNING: pre snapshot missing {p}, treating as no-pre")
            pre[f] = None
        else:
            pre[f] = file_sha256(p)

    # Step F HTML 構造の pre snapshot
    pre_main_text = STEP_F_HTML_MAIN.read_text(encoding="utf-8")
    pre_topk_text = STEP_F_HTML_TOPK.read_text(encoding="utf-8")
    pre_n_div_main = pre_main_text.count("plotly-graph-div")
    pre_n_plot_main = pre_main_text.count("Plotly.newPlot")
    pre_n_div_topk = pre_topk_text.count("plotly-graph-div")
    pre_n_plot_topk = pre_topk_text.count("Plotly.newPlot")
    pre_main_size = STEP_F_HTML_MAIN.stat().st_size
    pre_topk_size = STEP_F_HTML_TOPK.stat().st_size

    # Re-run Step C/D/E smoke
    for script, args in LAYER_A_STEP_C_D_E:
        t0 = time.time()
        proc = subprocess.run(
            [sys.executable, str(V1101A_DIR / script)] + args,
            capture_output=True, text=True, check=True,
            cwd=str(REPO_ROOT),
        )
        result["rerun_times_sec"][script] = round(time.time() - t0, 2)

    # Re-hash and compare
    post = {f: file_sha256(V1101A_SMOKE / f) for f in LAYER_A_SMOKE_PARQUETS}
    for f in LAYER_A_SMOKE_PARQUETS:
        result["parquet_hash_match"][f] = (pre.get(f) is not None
                                            and pre[f] == post[f])

    # Re-run Step F (main から)
    t0 = time.time()
    subprocess.run(
        [sys.executable, str(V1101A_DIR / STEP_F_SCRIPT), "--src", "main"],
        capture_output=True, text=True, check=True,
        cwd=str(REPO_ROOT),
    )
    result["rerun_times_sec"][STEP_F_SCRIPT] = round(time.time() - t0, 2)

    post_main_text = STEP_F_HTML_MAIN.read_text(encoding="utf-8")
    post_topk_text = STEP_F_HTML_TOPK.read_text(encoding="utf-8")

    result["html_structural"] = {
        "main_plotly_graph_div_count_match": (
            pre_n_div_main == post_main_text.count("plotly-graph-div")),
        "main_Plotly_newPlot_count_match": (
            pre_n_plot_main == post_main_text.count("Plotly.newPlot")),
        "topk_plotly_graph_div_count_match": (
            pre_n_div_topk == post_topk_text.count("plotly-graph-div")),
        "topk_Plotly_newPlot_count_match": (
            pre_n_plot_topk == post_topk_text.count("Plotly.newPlot")),
        "main_size_pre_bytes": pre_main_size,
        "main_size_post_bytes": STEP_F_HTML_MAIN.stat().st_size,
        "main_size_diff_bytes": (STEP_F_HTML_MAIN.stat().st_size - pre_main_size),
        "topk_size_pre_bytes": pre_topk_size,
        "topk_size_post_bytes": STEP_F_HTML_TOPK.stat().st_size,
        "topk_size_diff_bytes": (STEP_F_HTML_TOPK.stat().st_size - pre_topk_size),
        "note": ("HTML byte-identity NOT guaranteed (plotly UUID div IDs random); "
                 "structural identity verified"),
    }

    result["all_parquet_match"] = all(result["parquet_hash_match"].values())
    return result


# --- 層 B ---
def snapshot_dir(root: Path) -> dict:
    snap = {}
    for p in root.rglob("*"):
        if p.is_file():
            st = p.stat()
            snap[str(p.relative_to(root))] = (st.st_size, st.st_mtime_ns)
    return snap


def layer_b_check(pre_snapshots: dict) -> dict:
    result = {}
    label_root = [
        ("v106_main", V106_MAIN),
        ("v107_main", V107_MAIN),
        ("v105_integration", V105_INTEGRATION),
    ]
    for label, root in label_root:
        post = snapshot_dir(root)
        pre = pre_snapshots[label]
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
    result["all_pass"] = all(result[k]["pass"]
                              for k in ("v106_main", "v107_main",
                                        "v105_integration"))
    return result


# --- 層 C ---
ARG_WRITE_PATTERNS = [
    ("to_parquet", re.compile(r"\.to_parquet\(\s*([^,)]+)")),
    ("to_csv",     re.compile(r"\.to_csv\(\s*([^,)]+)")),
    ("to_json",    re.compile(r"\.to_json\(\s*([^,)]+)")),
    ("write_html", re.compile(r"\.write_html\(\s*([^,)]+)")),
    ("open_w",     re.compile(r"open\(\s*([^,)]+),\s*['\"]w")),
]
RECEIVER_WRITE_PATTERNS = [
    ("write_text",  re.compile(r"(\w+)\.write_text\(")),
    ("write_bytes", re.compile(r"(\w+)\.write_bytes\(")),
]
ALLOWED_V1101A_TOKENS = (
    "V1101A_OUT", "V1101A_MAIN", "V1101A_SMOKE", "V1101A_DIR",
    "OUT_MAIN", "OUT_SMOKE", "out_dir", "src_dir",  # script-local constants
    "out_main", "out_topk", "out_path",
)


def _is_under_v1101a(expr: str) -> bool:
    return any(c in expr for c in ALLOWED_V1101A_TOKENS)


def layer_c_check() -> dict:
    findings = []
    for script in V1101A_SCRIPTS:
        sp = V1101A_DIR / script
        text = sp.read_text(encoding="utf-8")
        for method, pat in ARG_WRITE_PATTERNS:
            for m in pat.finditer(text):
                target = m.group(1).strip()
                findings.append({
                    "script": script,
                    "method": method,
                    "position": "arg",
                    "captured": target,
                    "structurally_under_v1101a": _is_under_v1101a(target),
                })
        for method, pat in RECEIVER_WRITE_PATTERNS:
            for m in pat.finditer(text):
                receiver = m.group(1).strip()
                findings.append({
                    "script": script,
                    "method": method,
                    "position": "receiver",
                    "captured": receiver,
                    "structurally_under_v1101a": _is_under_v1101a(receiver),
                })
    all_under = all(f["structurally_under_v1101a"] for f in findings)
    return {
        "n_write_calls": len(findings),
        "all_structurally_under_v1101a": all_under,
        "allowed_tokens": list(ALLOWED_V1101A_TOKENS),
        "findings": findings,
    }


def main():
    print("[G] snapshotting v10.x main / v105 integration outputs ...")
    pre = {
        "v106_main": snapshot_dir(V106_MAIN),
        "v107_main": snapshot_dir(V107_MAIN),
        "v105_integration": snapshot_dir(V105_INTEGRATION),
    }
    print(f"  v106 main: {len(pre['v106_main'])} files")
    print(f"  v107 main: {len(pre['v107_main'])} files")
    print(f"  v105 integration: {len(pre['v105_integration'])} files")

    print("[G-1] layer A: re-run Step C/D/E smoke + Step F, verify parquet hash + HTML structure")
    layer_a = layer_a_check()
    n_pass = sum(layer_a["parquet_hash_match"].values())
    n_total = len(layer_a["parquet_hash_match"])
    print(f"  parquet hash: {n_pass}/{n_total} match, all_parquet_match={layer_a['all_parquet_match']}")
    h = layer_a['html_structural']
    print(f"  HTML main: div={h['main_plotly_graph_div_count_match']}, plot={h['main_Plotly_newPlot_count_match']}")
    print(f"  HTML topk: div={h['topk_plotly_graph_div_count_match']}, plot={h['topk_Plotly_newPlot_count_match']}")

    print("[G-2] layer B: verify v10.x main + v105 integration unchanged after re-run")
    layer_b = layer_b_check(pre)
    for k in ("v106_main", "v107_main", "v105_integration"):
        v = layer_b[k]
        print(f"  {k}: pre={v['n_files_pre']} post={v['n_files_post']} added={v['n_added']} removed={v['n_removed']} modified={v['n_modified']} pass={v['pass']}")
    print(f"  layer_b.all_pass={layer_b['all_pass']}")

    print("[G-3] layer C: scan script writes for structural v1101a compliance")
    layer_c = layer_c_check()
    print(f"  n_write_calls={layer_c['n_write_calls']}, all_under_v1101a={layer_c['all_structurally_under_v1101a']}")

    all_pass = (
        layer_a["all_parquet_match"]
        and layer_a["html_structural"]["main_plotly_graph_div_count_match"]
        and layer_a["html_structural"]["main_Plotly_newPlot_count_match"]
        and layer_a["html_structural"]["topk_plotly_graph_div_count_match"]
        and layer_a["html_structural"]["topk_Plotly_newPlot_count_match"]
        and layer_b["all_pass"]
        and layer_c["all_structurally_under_v1101a"]
    )
    report = {
        "version": "v11.0.1.a (v1101a) Step G",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note_layer_a": ("Step C main 24 seeds は 16 分かかるため smoke seed 0 で "
                         "代用、本主題 post-process deterministic"),
        "layer_a": layer_a,
        "layer_b": layer_b,
        "layer_c": layer_c,
        "all_layers_pass": all_pass,
    }
    out_path = V1101A_DIR / "v1101a_step_g_bit_identity_report.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"\nReport written: {out_path}")
    print(f"all_layers_pass = {report['all_layers_pass']}")


if __name__ == "__main__":
    main()
