#!/usr/bin/env python3
"""v1104 Step H-4 bit-identity 再検証

Step H-3 を拡張し、観察 3 再調査 4 件出力 (4 parquet) も決定論的であることを確認。
層 A: Step B-E + Step H-3 + Step H-4 再実行 → parquet hash 一致
層 B: v10.5 / v10.6 / v10.7 / v11.0.1a / v11.0.2 / v11.0.3 main outputs 全 frozen
層 C: 段階 2 + 再調査 scripts 書込みパス unified/v1104/ 配下のみ
"""
from __future__ import annotations
import hashlib, json, re, subprocess, sys, time
from pathlib import Path

REPO_ROOT = Path("/home/takasan/esde/ESDE-Research")
V105_SAL = REPO_ROOT / "developmental/v105/diag_v105_main/salience"
V105_INT = REPO_ROOT / "developmental/v105/diag_v105_main/integration"
V106_MAIN = REPO_ROOT / "developmental/v106/outputs/main"
V107_MAIN = REPO_ROOT / "developmental/v107/outputs/main"
V112_MAIN = REPO_ROOT / "developmental/v112/outputs/main"
V1101A_MAIN = REPO_ROOT / "unified/v1101a/outputs/main"
V1102_MAIN = REPO_ROOT / "unified/v1102/outputs/main"
V1103_MAIN = REPO_ROOT / "unified/v1103/outputs/main"
V1104_DIR = REPO_ROOT / "unified/v1104"
V1104_MAIN = V1104_DIR / "outputs/main"

LAYER_A_FILES = [
    # 既存 Step B-E
    "observation_1_cid_integration.parquet",
    "observation_2_predecessor_chain.parquet",
    "observation_3_trajectory_response.parquet",
    "observation_4_b_overlap.parquet",
    # Step H-3 観察 2 再調査
    "observation_2_restratified.parquet",
    "observation_2_shuffle_variants.parquet",
    "cid_sim_matrix_distribution.parquet",
    "observation_2_resolution.parquet",
    "observation_2_self_loop_split.parquet",
    # Step H-4 観察 3 再調査
    "observation_3_stratified.parquet",
    "observation_3_weighted.parquet",
    "observation_3_alt_metrics.parquet",
    "observation_3_shuffle_baseline.parquet",
]
LAYER_A_RERUN = [
    ("v1104_step_b_observation_1.py", ["--seeds", "0..23"]),
    ("v1104_step_c_observation_2.py", ["--seeds", "0..23"]),
    ("v1104_step_d_observation_3.py", ["--seeds", "0..23"]),
    ("v1104_step_e_observation_4.py", []),
    ("v1104_step_h3_reinvestigation.py", ["--seeds", "0..23"]),
    ("v1104_step_h4_reinvestigation.py", ["--seeds", "0..23"]),
]
V1104_SCRIPTS = [
    "v1104_step_b_observation_1.py",
    "v1104_step_c_observation_2.py",
    "v1104_step_d_observation_3.py",
    "v1104_step_e_observation_4.py",
    "v1104_step_f_graph.py",
    "v1104_step_h3_reinvestigation.py",
    "v1104_step_h3_graph.py",
    "v1104_step_h4_reinvestigation.py",
    "v1104_step_h4_graph.py",
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
ALLOWED_V1104 = ("V1104", "OUT_MAIN", "OUT_DIR", "out_path", "out", "V1104_DIR", "V1104_MAIN")


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def snap(root):
    s = {}
    for p in root.rglob("*"):
        if p.is_file():
            st = p.stat()
            s[str(p.relative_to(root))] = (st.st_size, st.st_mtime_ns)
    return s


def layer_a():
    r = {"hash_match": {}, "rerun_sec": {}}
    pre = {f: sha(V1104_MAIN / f) for f in LAYER_A_FILES if (V1104_MAIN / f).exists()}
    for script, args in LAYER_A_RERUN:
        t = time.time()
        subprocess.run([sys.executable, str(V1104_DIR / script)] + args,
                       capture_output=True, check=True, cwd=str(REPO_ROOT))
        r["rerun_sec"][script] = round(time.time() - t, 2)
    post = {f: sha(V1104_MAIN / f) for f in LAYER_A_FILES}
    for f in LAYER_A_FILES:
        r["hash_match"][f] = pre.get(f) == post[f]
    r["all_match"] = all(r["hash_match"].values())
    return r


def layer_b(pre):
    r = {}
    for label, root in [("v105_sal", V105_SAL), ("v105_int", V105_INT),
                         ("v106", V106_MAIN), ("v107", V107_MAIN), ("v112", V112_MAIN),
                         ("v1101a", V1101A_MAIN), ("v1102", V1102_MAIN), ("v1103", V1103_MAIN)]:
        post = snap(root)
        added = set(post) - set(pre[label])
        removed = set(pre[label]) - set(post)
        modified = [f for f in pre[label].keys() & post.keys() if pre[label][f] != post[f]]
        r[label] = {"pre": len(pre[label]), "post": len(post),
                     "add": len(added), "rem": len(removed), "mod": len(modified),
                     "pass": len(added)==0 and len(removed)==0 and len(modified)==0}
    r["all_pass"] = all(r[k]["pass"] for k in pre)
    return r


def _under(expr): return any(c in expr for c in ALLOWED_V1104)


def layer_c():
    f = []
    for s in V1104_SCRIPTS:
        text = (V1104_DIR / s).read_text()
        for m, pat in ARG_WRITE_PATTERNS:
            for x in pat.finditer(text):
                t = x.group(1).strip()
                f.append({"script": s, "method": m, "captured": t, "under": _under(t)})
        for m, pat in RECEIVER_WRITE_PATTERNS:
            for x in pat.finditer(text):
                r = x.group(1).strip()
                f.append({"script": s, "method": m, "captured": r, "under": _under(r)})
    return {"n": len(f), "all_under": all(x["under"] for x in f), "findings": f}


def main():
    print("[v1104-H4] snapshot pre")
    pre = {"v105_sal": snap(V105_SAL), "v105_int": snap(V105_INT),
            "v106": snap(V106_MAIN), "v107": snap(V107_MAIN), "v112": snap(V112_MAIN),
            "v1101a": snap(V1101A_MAIN), "v1102": snap(V1102_MAIN), "v1103": snap(V1103_MAIN)}
    for k, v in pre.items():
        print(f"  {k}: {len(v)} files")

    print("[A] re-run Step B-E + Step H-3 + Step H-4, hash match")
    la = layer_a()
    for f, ok in la['hash_match'].items():
        print(f"  {f}: {ok}")
    print(f"  all_match={la['all_match']}, rerun={la['rerun_sec']}")

    print("[B] all outputs frozen")
    lb = layer_b(pre)
    for k in pre:
        v = lb[k]; print(f"  {k}: pre={v['pre']} post={v['post']} a={v['add']} r={v['rem']} m={v['mod']} pass={v['pass']}")
    print(f"  all_pass={lb['all_pass']}")

    print("[C] write paths under unified/v1104/")
    lc = layer_c()
    print(f"  n={lc['n']}, all_under={lc['all_under']}")

    all_pass = la['all_match'] and lb['all_pass'] and lc['all_under']
    report = {"version": "v11.0.4 (v1104) Step H-4",
              "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "layer_a": la, "layer_b": lb, "layer_c": lc,
              "all_layers_pass": all_pass}
    out = V1104_DIR / "v1104_step_h4_bit_identity_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReport: {out}")
    print(f"all_layers_pass = {all_pass}")


if __name__ == "__main__":
    main()
