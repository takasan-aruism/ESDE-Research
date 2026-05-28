#!/usr/bin/env python3
"""v1107b Step G — bit-identity 3 層検証"""
from __future__ import annotations
import hashlib, json, re, subprocess, sys, time
from pathlib import Path

REPO = Path('/home/takasan/esde/ESDE-Research')
V105_SUB = REPO / 'developmental/v105/diag_v105_main/subjects'
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V1103_MAIN = REPO / 'unified/v1103/outputs/main'
V1105A_MAIN = REPO / 'unified/v1105a/outputs/main'
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'
V1106B_MAIN = REPO / 'unified/v1106b/outputs/main'
V1107B_DIR = REPO / 'unified/v1107b'
V1107B_MAIN = V1107B_DIR / 'outputs/main'
MAPPER_DIR = REPO / 'language/lexicon/data/mapper_output'

LAYER_A_FILES = [
    'env_check_summary.parquet', 'env_check_axes_meta.parquet',
    'axes_correlation_matrix.parquet',
    'observation_1_axis_clusters.parquet',
    'observation_1_hypothesis_purity.parquet', 'observation_1_summary.parquet',
    'observation_2_axis_contribution.parquet',
    'observation_2_category_scale_bias.parquet', 'observation_2_summary.parquet',
    'observation_3_axis_shuffle.parquet', 'observation_3_category_shuffle.parquet',
    'observation_3_summary.parquet',
    'observation_4_category_scale_map.parquet',
    'observation_4_scale_to_axes.parquet', 'observation_4_summary.parquet',
]
LAYER_A_RERUN = [
    'v1107b_step_b_env_check.py',
    'v1107b_step_c_observation_1.py',
    'v1107b_step_d_observation_2.py',
    'v1107b_step_e_observation_3.py',
    'v1107b_step_f_observation_4.py',
]
ALLOWED_V1107B = ('V1107B', 'OUT', 'out_path', 'out', 'out1', 'out2', 'out3', 'out4')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def snap(root):
    s = {}
    for p in root.rglob('*'):
        if p.is_file():
            st = p.stat()
            s[str(p.relative_to(root))] = (st.st_size, st.st_mtime_ns)
    return s


def main():
    print('=== v1107b Step G — bit-identity 3 層検証 ===\n')
    t0 = time.time()

    print('[pre-snap]')
    pre = {k: snap(p) for k, p in [
        ('v105_subjects', V105_SUB), ('v106_main', V106_MAIN),
        ('v1103_main', V1103_MAIN), ('v1105a_main', V1105A_MAIN),
        ('v1106a_main', V1106A_MAIN), ('v1106b_main', V1106B_MAIN),
        ('mapper_output', MAPPER_DIR),
    ]}

    # LAYER A
    print('\n[LAYER A] Step B-F 再実行 + hash 一致')
    pre_hash = {f: sha(V1107B_MAIN / f) for f in LAYER_A_FILES
                  if (V1107B_MAIN / f).exists()}
    rerun_sec = {}
    for script in LAYER_A_RERUN:
        t = time.time()
        subprocess.run([sys.executable, str(V1107B_DIR / script)],
                         capture_output=True, check=True, cwd=str(REPO))
        rerun_sec[script] = round(time.time() - t, 2)
        print(f'  {script}: {rerun_sec[script]}s')
    post_hash = {f: sha(V1107B_MAIN / f) for f in LAYER_A_FILES
                   if (V1107B_MAIN / f).exists()}
    hash_match = {f: pre_hash.get(f) == post_hash.get(f) for f in LAYER_A_FILES}
    all_match = all(hash_match.values()) and len(hash_match) > 0
    for f, ok in hash_match.items():
        print(f'  {"✓" if ok else "✗"} {f}')
    print(f'  all_match: {all_match}')

    # LAYER B
    print('\n[LAYER B] 物理層 frozen')
    layer_b = {}
    for k, _ in pre.items():
        post = snap({
            'v105_subjects': V105_SUB, 'v106_main': V106_MAIN,
            'v1103_main': V1103_MAIN, 'v1105a_main': V1105A_MAIN,
            'v1106a_main': V1106A_MAIN, 'v1106b_main': V1106B_MAIN,
            'mapper_output': MAPPER_DIR,
        }[k])
        added = set(post) - set(pre[k])
        removed = set(pre[k]) - set(post)
        modified = [f for f in pre[k].keys() & post.keys() if pre[k][f] != post[f]]
        passed = len(added) == 0 and len(removed) == 0 and len(modified) == 0
        layer_b[k] = {'add': len(added), 'rem': len(removed), 'mod': len(modified), 'pass': passed}
        print(f'  {"✓" if passed else "✗"} {k}: a={len(added)} r={len(removed)} m={len(modified)}')
    all_frozen = all(v['pass'] for v in layer_b.values())

    # LAYER C
    print('\n[LAYER C] 書込みパス')
    arg_patterns = [
        re.compile(r'\.to_parquet\(\s*([^,)]+)'),
        re.compile(r'\.to_csv\(\s*([^,)]+)'),
        re.compile(r'\.to_json\(\s*([^,)]+)'),
    ]
    findings = []
    for s in LAYER_A_RERUN:
        text = (V1107B_DIR / s).read_text()
        for pat in arg_patterns:
            for x in pat.finditer(text):
                t = x.group(1).strip()
                under = any(c in t for c in ALLOWED_V1107B)
                findings.append({'script': s, 'captured': t[:60], 'under': under})
    all_under = all(f['under'] for f in findings)
    print(f'  n={len(findings)}, all_under_v1107b={all_under}')

    all_pass = all_match and all_frozen and all_under
    report = {
        'version': 'v11.0.7b Step G',
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'elapsed_sec': round(time.time() - t0, 2),
        'layer_a': {'hash_match': hash_match, 'all_match': all_match, 'rerun_sec': rerun_sec},
        'layer_b': layer_b,
        'layer_c': {'n': len(findings), 'all_under': all_under},
        'all_layers_pass': all_pass,
    }
    out = V1107B_DIR / 'v1107b_step_g_bit_identity_report.json'
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f'\nall_layers_pass = {all_pass}')
    print(f'elapsed: {time.time()-t0:.1f}s')


if __name__ == '__main__':
    main()
