#!/usr/bin/env python3
"""v1106b Step I — bit-identity 3 層検証

LAYER A: Step C-H 再実行で出力 hash 一致 (smoke + main)
LAYER B: 物理層 frozen 確認 (v106/v1103/mapper_output/v105/v1106a 全 read-only)
LAYER C: v1106b スクリプト書込みパスが unified/v1106b/ 配下のみ
"""
from __future__ import annotations
import hashlib, json, re, subprocess, sys, time
from pathlib import Path

REPO = Path('/home/takasan/esde/ESDE-Research')
V105_SUB = REPO / 'developmental/v105/diag_v105_main/subjects'
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V1103_MAIN = REPO / 'unified/v1103/outputs/main'
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'
V1106B_DIR = REPO / 'unified/v1106b'
V1106B_MAIN = V1106B_DIR / 'outputs/main'
MAPPER_DIR = REPO / 'language/lexicon/data/mapper_output'

LAYER_A_FILES = [
    'env_check_cid_props.parquet',
    'env_check_bin_counts.parquet',
    'env_check_selected_cids.parquet',
    'env_check_underfill.parquet',
    'observation_1_familiarity_trajectory_smoke.parquet',
    'observation_1_smoke_per_seed_bin_counts.parquet',
    'observation_1_familiarity_trajectory.parquet',
    'observation_1_summary.parquet',
    'observation_1_aggregate.parquet',
    'observation_2_circulation.parquet',
    'observation_2_attractors.parquet',
    'observation_2_aggregate.parquet',
    'observation_3_high_low_events.parquet',
    'observation_3_input_atom_bias.parquet',
    'observation_3_word_distribution.parquet',
    'observation_4_self_dialogue_smoke.parquet',
    'observation_4_smoke_compare_top1.parquet',
    'observation_4_self_dialogue.parquet',
    'observation_4_summary.parquet',
    'observation_4_aggregate.parquet',
    'observation_4_vs_top1_compare.parquet',
]
LAYER_A_RERUN = [
    'v1106b_step_b_env_check.py',
    'v1106b_step_c_observation_1_smoke.py',
    'v1106b_step_d_observation_1_main.py',
    'v1106b_step_e_observation_2_circulation.py',
    'v1106b_step_f_observation_3_local_resonance.py',
    'v1106b_step_g_observation_4_smoke.py',
    'v1106b_step_h_observation_4_main.py',
]
V1106B_SCRIPTS = LAYER_A_RERUN[:]  # LAYER C check 対象

ARG_WRITE_PATTERNS = [
    ('to_parquet', re.compile(r'\.to_parquet\(\s*([^,)]+)')),
    ('to_csv', re.compile(r'\.to_csv\(\s*([^,)]+)')),
    ('to_json', re.compile(r'\.to_json\(\s*([^,)]+)')),
    ('write_html', re.compile(r'\.write_html\(\s*([^,)]+)')),
    ('open_w', re.compile(r"open\(\s*([^,)]+),\s*['\"]w")),
]
RECEIVER_WRITE_PATTERNS = [
    ('write_text', re.compile(r'(\w+)\.write_text\(')),
    ('write_bytes', re.compile(r'(\w+)\.write_bytes\(')),
]
ALLOWED_V1106B = ('V1106B', 'OUT', 'out_path', 'out', 'out1', 'out2', 'out3', 'out4',
                    'prefix', 'V1106B_MAIN', 'V1106B_DIR')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def snap(root):
    s = {}
    for p in root.rglob('*'):
        if p.is_file():
            st = p.stat()
            s[str(p.relative_to(root))] = (st.st_size, st.st_mtime_ns)
    return s


def layer_a():
    """Step C-H 再実行で hash 一致確認"""
    r = {'hash_match': {}, 'rerun_sec': {}}
    pre = {f: sha(V1106B_MAIN / f) for f in LAYER_A_FILES if (V1106B_MAIN / f).exists()}
    print(f'  pre-hash 取得: {len(pre)} files')
    for script in LAYER_A_RERUN:
        t = time.time()
        sp = V1106B_DIR / script
        if not sp.exists():
            print(f'  WARN: {script} not found')
            continue
        result = subprocess.run([sys.executable, str(sp)],
                                  capture_output=True, check=True, cwd=str(REPO))
        r['rerun_sec'][script] = round(time.time() - t, 2)
        print(f'  rerun {script}: {r["rerun_sec"][script]}s')
    post = {f: sha(V1106B_MAIN / f) for f in LAYER_A_FILES if (V1106B_MAIN / f).exists()}
    for f in LAYER_A_FILES:
        if f in pre and f in post:
            r['hash_match'][f] = pre[f] == post[f]
        else:
            r['hash_match'][f] = False
    r['all_match'] = all(r['hash_match'].values()) and len(r['hash_match']) > 0
    return r


def layer_b(pre):
    """物理層 frozen 確認"""
    r = {}
    targets = [
        ('v105_subjects', V105_SUB),
        ('v106_main', V106_MAIN),
        ('v1103_main', V1103_MAIN),
        ('v1106a_main', V1106A_MAIN),
        ('mapper_output', MAPPER_DIR),
    ]
    for label, root in targets:
        post = snap(root)
        added = set(post) - set(pre[label])
        removed = set(pre[label]) - set(post)
        modified = [f for f in pre[label].keys() & post.keys() if pre[label][f] != post[f]]
        r[label] = {
            'pre': len(pre[label]), 'post': len(post),
            'add': len(added), 'rem': len(removed), 'mod': len(modified),
            'pass': len(added) == 0 and len(removed) == 0 and len(modified) == 0,
        }
    r['all_pass'] = all(r[k]['pass'] for k, _ in targets)
    return r


def _under(expr):
    return any(c in expr for c in ALLOWED_V1106B)


def layer_c():
    """v1106b スクリプトの書込みパス検証"""
    findings = []
    for s in V1106B_SCRIPTS:
        sp = V1106B_DIR / s
        if not sp.exists():
            continue
        text = sp.read_text()
        for m, pat in ARG_WRITE_PATTERNS:
            for x in pat.finditer(text):
                t = x.group(1).strip()
                findings.append({
                    'script': s, 'method': m, 'captured': t,
                    'under_v1106b': _under(t),
                })
        for m, pat in RECEIVER_WRITE_PATTERNS:
            for x in pat.finditer(text):
                rcv = x.group(1).strip()
                findings.append({
                    'script': s, 'method': m, 'captured': rcv,
                    'under_v1106b': _under(rcv),
                })
    return {
        'n': len(findings),
        'all_under_v1106b': all(f['under_v1106b'] for f in findings),
        'findings': findings,
    }


def main():
    print('=== v1106b Step I — bit-identity 3 層検証 ===\n')
    t0 = time.time()

    print('[pre-snapshot] 物理層 + v1106a の snapshot 取得')
    pre = {
        'v105_subjects': snap(V105_SUB),
        'v106_main': snap(V106_MAIN),
        'v1103_main': snap(V1103_MAIN),
        'v1106a_main': snap(V1106A_MAIN),
        'mapper_output': snap(MAPPER_DIR),
    }
    for k, v in pre.items():
        print(f'  {k}: {len(v)} files')

    print('\n[LAYER A] Step B-H 再実行 + hash 一致確認')
    la = layer_a()
    for f, ok in la['hash_match'].items():
        marker = '✓' if ok else '✗'
        print(f'  {marker} {f}: {ok}')
    print(f'  all_match: {la["all_match"]}')
    print(f'  rerun times: {la["rerun_sec"]}')

    print('\n[LAYER B] 物理層 frozen 確認')
    lb = layer_b(pre)
    for k in pre:
        v = lb[k]
        marker = '✓' if v['pass'] else '✗'
        print(f"  {marker} {k}: pre={v['pre']} post={v['post']} "
              f"a={v['add']} r={v['rem']} m={v['mod']} pass={v['pass']}")
    print(f'  all_pass: {lb["all_pass"]}')

    print('\n[LAYER C] v1106b スクリプト書込みパス検証')
    lc = layer_c()
    print(f'  n={lc["n"]}, all_under_v1106b={lc["all_under_v1106b"]}')
    if not lc['all_under_v1106b']:
        for f in lc['findings']:
            if not f['under_v1106b']:
                print(f"  VIOLATION: {f}")

    all_pass = la['all_match'] and lb['all_pass'] and lc['all_under_v1106b']
    report = {
        'version': 'v11.0.6b Step I',
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'elapsed_sec': round(time.time() - t0, 2),
        'layer_a': la,
        'layer_b': lb,
        'layer_c': lc,
        'all_layers_pass': all_pass,
    }
    out = V1106B_DIR / 'v1106b_step_i_bit_identity_report.json'
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f'\nReport: {out.name}')
    print(f'all_layers_pass = {all_pass}')
    print(f'elapsed: {time.time()-t0:.1f}s')


if __name__ == '__main__':
    main()
