#!/usr/bin/env python3
"""v1103 Step E — bit-identity 3 層検証

層 A: Step B (atom_centroids) + Step C (density) 再実行 → parquet hash 一致
層 B: v10.x main + v1101a + v1102 + Language outputs 不変
層 C: 段 2 scripts 書込みパス unified/v1103/ 配下のみ
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
V1102_MAIN = REPO_ROOT / "unified/v1102/outputs/main"
LANGUAGE_MAPPER = REPO_ROOT / "language/lexicon/data/mapper_output"
V1103_DIR = REPO_ROOT / "unified/v1103"
V1103_MAIN = V1103_DIR / "outputs/main"

LAYER_A_FILES = [
    "atom_centroids_48d_raw.parquet",
    "atom_centroids_48d_normalized.parquet",
    "atom_quality.parquet",
    "response_atom_distribution.parquet",
    "density_summary.parquet",
]
LAYER_A_RERUN = [
    ("v1103_step_b_atom_centroids.py", []),
    ("v1103_step_c_density_distribution.py", []),
]

V1103_SCRIPTS = [
    "v1103_step_b_atom_centroids.py",
    "v1103_step_c_density_distribution.py",
    "v1103_step_d_graph.py",
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
ALLOWED_V1103_TOKENS = ("V1103_OUT", "V1103_MAIN", "V1103_DIR", "OUT_MAIN", "out_dir", "out_path", "out")


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
    pre = {f: sha(V1103_MAIN / f) for f in LAYER_A_FILES if (V1103_MAIN / f).exists()}
    for script, args in LAYER_A_RERUN:
        t = time.time()
        subprocess.run([sys.executable, str(V1103_DIR / script)] + args,
                       capture_output=True, check=True, cwd=str(REPO_ROOT))
        r["rerun_sec"][script] = round(time.time() - t, 2)
    post = {f: sha(V1103_MAIN / f) for f in LAYER_A_FILES}
    for f in LAYER_A_FILES:
        r["hash_match"][f] = (pre.get(f) is not None and pre[f] == post[f])
    r["all_match"] = all(r["hash_match"].values())
    return r


def layer_b(pre):
    r = {}
    for label, root in [("v106", V106_MAIN), ("v107", V107_MAIN),
                         ("v112", V112_MAIN), ("v105_integration", V105_INTEGRATION),
                         ("v1101a", V1101A_MAIN), ("v1102", V1102_MAIN),
                         ("language_mapper", LANGUAGE_MAPPER)]:
        post = snap(root)
        added = set(post) - set(pre[label])
        removed = set(pre[label]) - set(post)
        modified = [f for f in pre[label].keys() & post.keys() if pre[label][f] != post[f]]
        r[label] = {"pre": len(pre[label]), "post": len(post),
                     "add": len(added), "rem": len(removed), "mod": len(modified),
                     "pass": len(added)==0 and len(removed)==0 and len(modified)==0}
    r["all_pass"] = all(r[k]["pass"] for k in pre.keys())
    return r


def _under(expr): return any(c in expr for c in ALLOWED_V1103_TOKENS)


def layer_c():
    f = []
    for s in V1103_SCRIPTS:
        text = (V1103_DIR / s).read_text()
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
    print("[v1103-E] snapshot pre")
    pre = {"v106": snap(V106_MAIN), "v107": snap(V107_MAIN), "v112": snap(V112_MAIN),
            "v105_integration": snap(V105_INTEGRATION), "v1101a": snap(V1101A_MAIN),
            "v1102": snap(V1102_MAIN), "language_mapper": snap(LANGUAGE_MAPPER)}
    for k, v in pre.items():
        print(f"  {k}: {len(v)} files")

    print("[A] re-run Step B+C, hash match")
    la = layer_a()
    print(f"  all_match={la['all_match']}, rerun={la['rerun_sec']}")

    print("[B] all outputs frozen")
    lb = layer_b(pre)
    for k in pre:
        v = lb[k]; print(f"  {k}: pre={v['pre']} post={v['post']} a={v['add']} r={v['rem']} m={v['mod']} pass={v['pass']}")
    print(f"  all_pass={lb['all_pass']}")

    print("[C] write paths under unified/v1103/")
    lc = layer_c()
    print(f"  n={lc['n']}, all_under={lc['all_under']}")

    all_pass = la["all_match"] and lb["all_pass"] and lc["all_under"]
    report = {"version": "v11.0.3 (v1103) Step E",
              "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "layer_a": la, "layer_b": lb, "layer_c": lc,
              "all_layers_pass": all_pass}
    out = V1103_DIR / "v1103_step_e_bit_identity_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReport: {out}")
    print(f"all_layers_pass = {all_pass}")


if __name__ == "__main__":
    main()
