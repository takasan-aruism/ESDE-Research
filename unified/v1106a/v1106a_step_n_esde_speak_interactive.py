#!/usr/bin/env python3
"""v1106a Step N — ESDE 対話 1 サイクル生成 (B-3)

任意の CID 状態を入力 → ESDE が選ぶ word 確率分布を返す。

接続式 (案 Y):
  CID 48d vec → cid_atom_sim top-K atom (CID 由来の atom 重み)
              → 案 Y: Σ_a p(a) × cos_sim(atom_centroid_48d, word_raw_48d)
              → word 確率分布

入力モード:
  1. 実在 CID 指定: --seed N --cid M
  2. ランダム選択: --random [--seed N]
  3. 任意物理量から構築: --lifespan X --n_core Y --familiarity Z [...]
     (build_cid_vector を簡易再現、欠損値は 0 埋め)

出力:
  - 標準出力: top-K word 確率 + top atom 候補
  - --out PATH: CSV ファイルに保存

使用例:
  python3 v1106a_step_n_esde_speak_interactive.py --seed 0 --cid 198
  python3 v1106a_step_n_esde_speak_interactive.py --random --seed 5
  python3 v1106a_step_n_esde_speak_interactive.py --random --topk 20

注: v106 build_cid_vector は 10 種類の物理量から 48d vec を作る複雑な処理。
本スクリプトは簡易再現として「直接 48d vec 指定」または「実在 CID 流用」のみ対応。
完全な物理量 → 48d 変換は v106_post_process.py 経由が筋。
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1103_MAIN = REPO / 'unified/v1103/outputs/main'
V106_MAIN = REPO / 'developmental/v106/outputs/main'
MAPPER_DIR = REPO / 'language/lexicon/data/mapper_output'


def get_axes_order():
    """v106 axes_metadata 順序 (CID と atom 共通の 48 軸)"""
    am = json.load(open(V106_MAIN / 'axes_metadata.json'))
    axes = []
    for axis in am['axes_order']:
        for lvl in axis['level_names']:
            axes.append(f'{axis["name"]}.{lvl}')
    return axes


def load_resources(axes):
    """atom centroids + per (atom, word) cos_sim 事前計算"""
    ac = pd.read_parquet(V1103_MAIN / 'atom_centroids_48d_raw.parquet')
    atom_to_centroid = {row['atom']: np.array([row[ax] for ax in axes], dtype=np.float64)
                         for _, row in ac.iterrows()}

    # per atom: list of (word, raw_48d) + cos_sim(centroid, word)
    atom_to_word_sims = {}  # atom → list of (word, cos_sim, raw_48d)
    for fp in sorted(MAPPER_DIR.glob('*_a1.jsonl')):
        atom = fp.stem.replace('_a1', '').replace('_', '.', 1)
        if atom not in atom_to_centroid:
            continue
        centroid = atom_to_centroid[atom]
        cn = np.linalg.norm(centroid)
        if cn == 0:
            continue
        words_vecs = []
        with open(fp) as f:
            for line in f:
                r = json.loads(line)
                if r.get('status') != 'OK':
                    continue
                rs = r.get('raw_scores')
                if not isinstance(rs, dict):
                    continue
                vec = np.array([rs.get(ax, 0.0) for ax in axes], dtype=np.float64)
                wn = np.linalg.norm(vec)
                if wn == 0:
                    continue
                sim = float(np.dot(centroid, vec) / (cn * wn))
                words_vecs.append((r['word'], sim, vec))
        atom_to_word_sims[atom] = words_vecs
    return atom_to_centroid, atom_to_word_sims


def load_cid_vec(seed, cid):
    """実在 CID 48d vec を読み込み"""
    fp = V106_MAIN / f'cid_structure_profile_seed{seed}.csv'
    df = pd.read_csv(fp)
    row = df[df['cid'] == cid]
    if len(row) == 0:
        raise ValueError(f'CID {cid} not found in seed {seed}')
    dim_cols = [f'dim_{i}' for i in range(48)]
    return row.iloc[0][dim_cols].values.astype(np.float64)


def compute_cid_atom_sim(cid_vec, atom_to_centroid, axes):
    """CID 48d vec と各 atom centroid の cos_sim
    注: v106 では atom_profiles (normalized mean) を使うが、ここでは v1103
        atom_centroids_48d_raw (raw mean) を使う。両者は概ね方向一致 (cos_sim 0.83)。
        差は探索用途では許容。
    """
    cn = np.linalg.norm(cid_vec)
    sims = {}
    for atom, centroid in atom_to_centroid.items():
        an = np.linalg.norm(centroid)
        if an > 0 and cn > 0:
            sims[atom] = float(np.dot(cid_vec, centroid) / (cn * an))
        else:
            sims[atom] = 0.0
    return sims


def select_atom_distribution(cid_atom_sim, k=10):
    """CID → 上位 K atom の正規化確率分布"""
    sorted_atoms = sorted(cid_atom_sim.items(), key=lambda x: -x[1])[:k]
    # 負の sim は 0 に clip、正規化
    raw = [max(s, 0.0) for _, s in sorted_atoms]
    total = sum(raw)
    if total <= 0:
        # 均等
        return [(a, 1.0/len(sorted_atoms)) for a, _ in sorted_atoms]
    return [(a, r/total) for (a, _), r in zip(sorted_atoms, raw)]


def compute_word_distribution(atom_probs, atom_to_word_sims):
    """案 Y: score(word) = Σ p(a) × cos_sim(a, word)"""
    word_score = defaultdict(float)
    for atom, p in atom_probs:
        if atom not in atom_to_word_sims:
            continue
        for word, sim, _ in atom_to_word_sims[atom]:
            word_score[word] += p * max(sim, 0.0)
    total = sum(word_score.values())
    if total <= 0:
        return {}
    return {w: s/total for w, s in word_score.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=None, help='CID seed (0-23)')
    ap.add_argument('--cid', type=int, default=None, help='CID id (実在 CID)')
    ap.add_argument('--random', action='store_true', help='ランダム CID 選択')
    ap.add_argument('--topk', type=int, default=15, help='出力する top word 数')
    ap.add_argument('--atom_topk', type=int, default=10, help='採用する atom 数 (CID→atom)')
    ap.add_argument('--out', type=str, default=None, help='出力 CSV パス')
    args = ap.parse_args()

    print('=== v1106a Step N — ESDE 対話 1 サイクル ===\n')

    axes = get_axes_order()

    # CID 選択
    if args.random:
        seed = args.seed if args.seed is not None else int(np.random.randint(24))
        fp = V106_MAIN / f'cid_structure_profile_seed{seed}.csv'
        df = pd.read_csv(fp, usecols=['cid'])
        cid = int(np.random.choice(df['cid'].values))
        print(f'[ランダム選択] seed={seed}, cid={cid}')
    elif args.seed is not None and args.cid is not None:
        seed, cid = args.seed, args.cid
        print(f'[指定] seed={seed}, cid={cid}')
    else:
        print('ERROR: --seed N --cid M または --random を指定してください')
        return

    # CID 物理量を表示
    fp = V106_MAIN / f'cid_structure_profile_seed{seed}.csv'
    cid_df = pd.read_csv(fp)
    cid_row = cid_df[cid_df['cid'] == cid]
    if len(cid_row) == 0:
        print(f'ERROR: cid {cid} not found in seed {seed}')
        return

    # per_subject から物理量 (オプション)
    psub = REPO / f'developmental/v105/diag_v105_main/subjects/per_subject_seed{seed}.csv'
    if psub.exists():
        pdf = pd.read_csv(psub)
        prow = pdf[pdf['cognitive_id'] == cid]
        if len(prow) > 0:
            r = prow.iloc[0]
            print(f'\n[CID 物理量]')
            for c in ['n_alphas_currently', 'last_familiarity_max', 'current_stability',
                       'current_familiarity', 'current_social', 'current_spread',
                       'C_at_run_end', 'final_state']:
                if c in r.index:
                    v = r[c]
                    if isinstance(v, float):
                        print(f'  {c:30s} {v:.4f}')
                    else:
                        print(f'  {c:30s} {v}')

    # CID 48d vec
    cid_vec = load_cid_vec(seed, cid)
    print(f'\n[CID 48d vec]')
    print(f'  norm: {np.linalg.norm(cid_vec):.4f}')
    # 軸別に強い軸 top-5
    pairs = sorted(zip(axes, cid_vec), key=lambda x: -x[1])[:5]
    print(f'  top 5 軸: {[(a, round(v,3)) for a,v in pairs]}')

    # リソース読み込み
    print('\n[リソース読み込み中...]')
    t0 = time.time()
    atom_to_centroid, atom_to_word_sims = load_resources(axes)
    print(f'  loaded {len(atom_to_centroid)} atoms, {sum(len(v) for v in atom_to_word_sims.values()):,} (atom, word) pairs '
          f'({time.time()-t0:.1f}s)')

    # CID → atom sim
    cid_atom_sim = compute_cid_atom_sim(cid_vec, atom_to_centroid, axes)
    atom_probs = select_atom_distribution(cid_atom_sim, k=args.atom_topk)

    print(f'\n[ESDE が想起する atom top-{args.atom_topk}]')
    for atom, p in atom_probs:
        raw_sim = cid_atom_sim[atom]
        print(f'  {atom:25s} p={p:.4f} (cos_sim={raw_sim:+.4f})')

    # word 分布生成
    word_probs = compute_word_distribution(atom_probs, atom_to_word_sims)
    sorted_words = sorted(word_probs.items(), key=lambda x: -x[1])

    print(f'\n[ESDE の発話: top-{args.topk} word]')
    for i, (w, p) in enumerate(sorted_words[:args.topk], 1):
        print(f'  {i:2}. {w:25s} p={p:.4f}')

    # 出力 CSV (オプション)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame([{'rank': i+1, 'word': w, 'probability': p}
                            for i, (w, p) in enumerate(sorted_words[:args.topk])])
        df.to_csv(out_path, index=False, float_format='%.6f')
        print(f'\nwrote {out_path}')

    print(f'\n--- 統計 ---')
    print(f'  total unique words: {len(word_probs):,}')
    print(f'  max_prob: {sorted_words[0][1]:.4f}')
    entropy = -sum(p * np.log(p) for p in word_probs.values() if p > 0)
    print(f'  entropy: {entropy:.4f}')


if __name__ == '__main__':
    main()
