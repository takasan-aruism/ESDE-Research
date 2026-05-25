#!/usr/bin/env python3
"""v1106a Step I — bit-identity 3 層検証

層 A: v1106a Step C-H 再実行で hash 一致 (9 ファイル)
層 B: v10.5/6/7 + v112 + v1101a-v1106 + language (synapse / mapper_output / a1_batch) 全 frozen
層 C: v1106a scripts の書込みパスが unified/v1106a/ 配下のみ
"""
from __future__ import annotations
import hashlib, json, re, subprocess, sys, time
from pathlib import Path

REPO_ROOT = Path("/home/takasan/esde/ESDE-Research")
V105_SAL = REPO_ROOT / "developmental/v105/diag_v105_main/salience"
V105_INT = REPO_ROOT / "developmental/v105/diag_v105_main/integration"
V106_DEV = REPO_ROOT / "developmental/v106/outputs/main"
V107_DEV = REPO_ROOT / "developmental/v107/outputs/main"
V112_DEV = REPO_ROOT / "developmental/v112/outputs/main"
V1101A_MAIN = REPO_ROOT / "unified/v1101a/outputs/main"
V1102_MAIN = REPO_ROOT / "unified/v1102/outputs/main"
V1103_MAIN = REPO_ROOT / "unified/v1103/outputs/main"
V1104_MAIN = REPO_ROOT / "unified/v1104/outputs/main"
V1104A_MAIN = REPO_ROOT / "unified/v1104a/outputs/main"
V1105_MAIN = REPO_ROOT / "unified/v1105/outputs/main"
V1105A_MAIN = REPO_ROOT / "unified/v1105a/outputs/main"
V1106_MAIN = REPO_ROOT / "unified/v1106/outputs/main"
SYNAPSE_DIR = REPO_ROOT / "language/synapse"
MAPPER_DIR = REPO_ROOT / "language/lexicon/data/mapper_output"
A1BATCH_DIR = REPO_ROOT / "language/atoms/a1_batch"
V1106A_DIR = REPO_ROOT / "unified/v1106a"
V1106A_MAIN = V1106A_DIR / "outputs/main"

LAYER_A_FILES = [
    "observation_1_word_distributions.parquet",
    "observation_1_labels.parquet",
    "observation_2_mapper_alignment.parquet",
    "observation_3_expansion.parquet",
    "observation_3_summary.parquet",
    "observation_4_layer_jaccard.parquet",
    "observation_4_series_comparison.parquet",
    "observation_5_L41_resolution.parquet",
    "observation_6_L42_resolution.parquet",
]
LAYER_A_RERUN = [
    ("v1106a_step_c_observation_1.py", []),
    ("v1106a_step_d_observation_2.py", []),
    ("v1106a_step_e_observation_3.py", []),
    ("v1106a_step_f_observation_4.py", []),
    ("v1106a_step_g_observation_5.py", []),
    ("v1106a_step_h_observation_6.py", []),
]
V1106A_SCRIPTS = [
    "v1106a_step_b_env_check.py",
    "v1106a_step_c_observation_1.py",
    "v1106a_step_d_observation_2.py",
    "v1106a_step_e_observation_3.py",
    "v1106a_step_f_observation_4.py",
    "v1106a_step_g_observation_5.py",
    "v1106a_step_h_observation_6.py",
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
ALLOWED_V1106A = ("V1106A", "OUT_MAIN", "OUT_DIR", "out_path", "out", "out1", "out2")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def snap(root):
    s = {}
    for p in root.rglob("*"):
        if p.is_file():
            st = p.stat()
            s[str(p.relative_to(root))] = (st.st_size, st.st_mtime_ns)
    return s


def layer_a():
    r = {"hash_match": {}, "rerun_sec": {}}
    pre = {f: sha(V1106A_MAIN / f) for f in LAYER_A_FILES if (V1106A_MAIN / f).exists()}
    for script, args in LAYER_A_RERUN:
        t = time.time()
        subprocess.run([sys.executable, str(V1106A_DIR / script)] + args,
                       capture_output=True, check=True, cwd=str(REPO_ROOT))
        r["rerun_sec"][script] = round(time.time() - t, 2)
    post = {f: sha(V1106A_MAIN / f) for f in LAYER_A_FILES}
    for f in LAYER_A_FILES:
        r["hash_match"][f] = pre.get(f) == post[f]
    r["all_match"] = all(r["hash_match"].values())
    return r


def layer_b(pre):
    r = {}
    for label, root in [
        ("v105_sal", V105_SAL), ("v105_int", V105_INT),
        ("v106", V106_DEV), ("v107", V107_DEV), ("v112", V112_DEV),
        ("v1101a", V1101A_MAIN), ("v1102", V1102_MAIN),
        ("v1103", V1103_MAIN), ("v1104", V1104_MAIN),
        ("v1104a", V1104A_MAIN), ("v1105", V1105_MAIN),
        ("v1105a", V1105A_MAIN), ("v1106", V1106_MAIN),
        ("language_synapse", SYNAPSE_DIR),
        ("language_mapper_output", MAPPER_DIR),
        ("language_atoms_a1_batch", A1BATCH_DIR),
    ]:
        post = snap(root)
        added = set(post) - set(pre[label])
        removed = set(pre[label]) - set(post)
        modified = [f for f in pre[label].keys() & post.keys() if pre[label][f] != post[f]]
        r[label] = {"pre": len(pre[label]), "post": len(post),
                    "add": len(added), "rem": len(removed), "mod": len(modified),
                    "pass": len(added) == 0 and len(removed) == 0 and len(modified) == 0}
    r["all_pass"] = all(r[k]["pass"] for k in pre)
    return r


def _under(expr):
    return any(c in expr for c in ALLOWED_V1106A)


def layer_c():
    f = []
    for s in V1106A_SCRIPTS:
        text = (V1106A_DIR / s).read_text()
        for m, pat in ARG_WRITE_PATTERNS:
            for x in pat.finditer(text):
                t = x.group(1).strip()
                f.append({"script": s, "method": m, "captured": t, "under": _under(t)})
        for m, pat in RECEIVER_WRITE_PATTERNS:
            for x in pat.finditer(text):
                rcv = x.group(1).strip()
                f.append({"script": s, "method": m, "captured": rcv, "under": _under(rcv)})
    return {"n": len(f), "all_under": all(x["under"] for x in f), "findings": f}


def main():
    print("[v1106a-I] snapshot pre")
    pre = {
        "v105_sal": snap(V105_SAL), "v105_int": snap(V105_INT),
        "v106": snap(V106_DEV), "v107": snap(V107_DEV), "v112": snap(V112_DEV),
        "v1101a": snap(V1101A_MAIN), "v1102": snap(V1102_MAIN),
        "v1103": snap(V1103_MAIN), "v1104": snap(V1104_MAIN),
        "v1104a": snap(V1104A_MAIN), "v1105": snap(V1105_MAIN),
        "v1105a": snap(V1105A_MAIN), "v1106": snap(V1106_MAIN),
        "language_synapse": snap(SYNAPSE_DIR),
        "language_mapper_output": snap(MAPPER_DIR),
        "language_atoms_a1_batch": snap(A1BATCH_DIR),
    }
    for k, v in pre.items():
        print(f"  {k}: {len(v)} files")

    print("[A] re-run Step C-H, hash match")
    la = layer_a()
    for f, ok in la['hash_match'].items():
        print(f"  {f}: {ok}")
    print(f"  all_match={la['all_match']}, rerun={la['rerun_sec']}")

    print("[B] all outputs frozen (v1106 まで + Synapse v3 + mapper_output + a1_batch)")
    lb = layer_b(pre)
    for k in pre:
        v = lb[k]; print(f"  {k}: pre={v['pre']} post={v['post']} a={v['add']} r={v['rem']} m={v['mod']} pass={v['pass']}")
    print(f"  all_pass={lb['all_pass']}")

    print("[C] write paths under unified/v1106a/")
    lc = layer_c()
    print(f"  n={lc['n']}, all_under={lc['all_under']}")
    if not lc['all_under']:
        for x in lc['findings']:
            if not x['under']:
                print(f"  VIOLATION: {x}")

    all_pass = la['all_match'] and lb['all_pass'] and lc['all_under']
    report = {"version": "v11.0.6a (v1106a) Step I",
              "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "layer_a": la, "layer_b": lb, "layer_c": lc,
              "all_layers_pass": all_pass}
    out = V1106A_DIR / "v1106a_step_i_bit_identity_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReport: {out}")
    print(f"all_layers_pass = {all_pass}")


if __name__ == "__main__":
    main()
