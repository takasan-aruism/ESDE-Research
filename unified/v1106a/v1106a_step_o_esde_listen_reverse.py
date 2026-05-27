#!/usr/bin/env python3
"""v1106a Step O — ESDE 逆引き (C-6): word → atom → CID 候補

人間が word を投げると ESDE 側の整合 CID 状態を推定。
B-3 の逆向き処理。

接続式 (逆方向):
  word(s) 入力
    → 各 word を含む atom 群 + word の raw_scores 48d norm でスコア化
    → atom 確率分布 (合算 + 正規化)
    → 各 atom について cid_atom_sim_matrix の sim 値取得
    → atom 確率で重み付けて CID スコア合算
    → top-K CID 候補 + 物理量

実装方針:
  word_atom_score = ||word_raw_48d||  (atom 内の word の "強さ")
  → 全 atom の word 強度を合算正規化 → P(atom | word)

  cid_score = Σ_a P(atom) × max(cid_atom_sim, 0)
  → 全 CID で計算、top-K 返す

入力モード:
  - 単一 word: --word "smell"
  - 複数 word: --words smell incense perfume
  - 自然文 (簡易 tokenize): --text "I smell the fragrant incense"

出力:
  - 標準出力: top atom 候補 + top CID 候補 + 各 CID の物理量
  - --out PATH: CSV 保存
"""
from __future__ import annotations
import argparse, json, re, time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1103_MAIN = REPO / 'unified/v1103/outputs/main'
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V105_SUB = REPO / 'developmental/v105/diag_v105_main/subjects'
MAPPER_DIR = REPO / 'language/lexicon/data/mapper_output'

# 簡易 stopwords (英語、基本のみ)
STOPWORDS = set("""
a an the and or but of in on at to for with by from is are was were be been being
this that these those i you he she it we they me him her us them my your his
its our their as if then so do does did has have had not no yes
""".split())


def get_axes_order():
    am = json.load(open(V106_MAIN / 'axes_metadata.json'))
    axes = []
    for axis in am['axes_order']:
        for lvl in axis['level_names']:
            axes.append(f'{axis["name"]}.{lvl}')
    return axes


def load_word_atom_lookup(axes):
    """word → {atom: raw_48d_vec} の lookup
    + atom → centroid (再生成検証用)
    """
    word_to_atom_vec = defaultdict(dict)  # word → atom → 48d vec
    for fp in sorted(MAPPER_DIR.glob('*_a1.jsonl')):
        atom = fp.stem.replace('_a1', '').replace('_', '.', 1)
        with open(fp) as f:
            for line in f:
                r = json.loads(line)
                if r.get('status') != 'OK':
                    continue
                rs = r.get('raw_scores')
                if not isinstance(rs, dict):
                    continue
                vec = np.array([rs.get(ax, 0.0) for ax in axes], dtype=np.float64)
                word_to_atom_vec[r['word']][atom] = vec
    return word_to_atom_vec


def tokenize(text):
    """簡易 tokenize: 小文字、空白分割、stopwords 除外、英字のみ"""
    words = re.findall(r"[a-zA-Z][a-zA-Z\-']*", text.lower())
    return [w for w in words if w not in STOPWORDS]


def word_to_atom_distribution(words, word_to_atom_vec):
    """入力 word(s) → P(atom) 分布
    各 word について、含む atom 群の word raw_scores の L2 norm を計算
    word 横断で合算、正規化
    """
    atom_score = defaultdict(float)
    matched_words = []
    unmatched = []
    for w in words:
        if w not in word_to_atom_vec:
            unmatched.append(w)
            continue
        matched_words.append(w)
        for atom, vec in word_to_atom_vec[w].items():
            atom_score[atom] += float(np.linalg.norm(vec))
    total = sum(atom_score.values())
    if total <= 0:
        return {}, matched_words, unmatched
    return {a: s / total for a, s in atom_score.items()}, matched_words, unmatched


def atom_to_cid_candidates(atom_probs, seeds=None):
    """atom 確率分布 → top-K CID 候補 (全 seed 横断、または指定 seed)
    cid_atom_sim_matrix から sim 値を取得、atom 確率で重み付けて CID スコア合算
    """
    if seeds is None:
        seeds = list(range(24))
    cid_results = []
    for sd in seeds:
        fp = V106_MAIN / f'cid_atom_sim_matrix_seed{sd}.parquet'
        if not fp.exists():
            continue
        sim_df = pd.read_parquet(fp)
        cid_scores = np.zeros(len(sim_df))
        for atom, p in atom_probs.items():
            if atom in sim_df.columns:
                sims = sim_df[atom].values.astype(np.float64)
                cid_scores += p * np.clip(sims, 0, None)
        for i, cid in enumerate(sim_df['cid'].values):
            cid_results.append((sd, int(cid), float(cid_scores[i])))
    cid_results.sort(key=lambda x: -x[2])
    return cid_results


def get_cid_properties(seed, cid):
    """per_subject から CID 物理量を取得"""
    fp = V105_SUB / f'per_subject_seed{seed}.csv'
    if not fp.exists():
        return {}
    df = pd.read_csv(fp)
    row = df[df['cognitive_id'] == cid]
    if len(row) == 0:
        return {}
    r = row.iloc[0]
    out = {}
    for c in ['n_alphas_currently', 'last_familiarity_max', 'current_stability',
              'current_familiarity', 'current_social', 'current_spread',
              'C_at_run_end', 'final_state']:
        if c in r.index:
            out[c] = r[c]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--word', type=str, default=None, help='単一 word 入力')
    ap.add_argument('--words', type=str, nargs='+', default=None, help='複数 word 入力')
    ap.add_argument('--text', type=str, default=None, help='自然文入力 (簡易 tokenize)')
    ap.add_argument('--atom_topk', type=int, default=10, help='出力する atom 数')
    ap.add_argument('--cid_topk', type=int, default=10, help='出力する CID 数')
    ap.add_argument('--seeds', type=int, nargs='+', default=None,
                     help='検索対象 seed (省略時は全 24 seed)')
    ap.add_argument('--out', type=str, default=None, help='出力 CSV プレフィックス')
    args = ap.parse_args()

    # 入力 word 確定
    if args.text:
        words = tokenize(args.text)
        print(f'[自然文 tokenize] "{args.text}" → {words}')
    elif args.words:
        words = [w.lower() for w in args.words]
        print(f'[複数 word 入力] {words}')
    elif args.word:
        words = [args.word.lower()]
        print(f'[単一 word 入力] {words}')
    else:
        print('ERROR: --word / --words / --text のいずれかを指定してください')
        return

    print('=== v1106a Step O — ESDE 逆引き 1 サイクル ===\n')

    axes = get_axes_order()

    print('[リソース読み込み中...]')
    t0 = time.time()
    word_to_atom_vec = load_word_atom_lookup(axes)
    print(f'  loaded {len(word_to_atom_vec):,} unique words ({time.time()-t0:.1f}s)')

    # word → atom 分布
    atom_probs, matched, unmatched = word_to_atom_distribution(words, word_to_atom_vec)
    if not atom_probs:
        print(f'\nERROR: 入力 word が mapper_output に 1 つも見つからない')
        if unmatched:
            print(f'  unmatched words: {unmatched}')
        return

    print(f'\n[マッチング状況]')
    print(f'  matched ({len(matched)}): {matched}')
    if unmatched:
        print(f'  unmatched ({len(unmatched)}): {unmatched}')

    sorted_atoms = sorted(atom_probs.items(), key=lambda x: -x[1])
    print(f'\n[word → atom 候補 top-{args.atom_topk}]')
    for atom, p in sorted_atoms[:args.atom_topk]:
        n_word = len(word_to_atom_vec.get(matched[0], {})) if matched else 0
        print(f'  {atom:25s} p={p:.4f}')

    # atom → CID
    print(f'\n[atom → CID 候補計算中...]')
    cid_candidates = atom_to_cid_candidates(dict(sorted_atoms[:args.atom_topk]),
                                              seeds=args.seeds)
    print(f'  total CID candidates: {len(cid_candidates):,}')

    print(f'\n[CID 候補 top-{args.cid_topk}]')
    print(f'  {"rank":4s} {"seed":4s} {"cid":4s} {"score":7s}  | properties')
    for rank, (sd, cid, score) in enumerate(cid_candidates[:args.cid_topk], 1):
        props = get_cid_properties(sd, cid)
        prop_str = ', '.join([
            f'n_a={int(props.get("n_alphas_currently", -1)) if not pd.isna(props.get("n_alphas_currently", np.nan)) else "?"}',
            f'fam={props.get("last_familiarity_max", float("nan")):.1f}',
            f'stb={props.get("current_stability", float("nan")):.2f}',
            f'soc={props.get("current_social", float("nan")):.2f}',
            f'spr={props.get("current_spread", float("nan")):.2f}',
            f'state={props.get("final_state", "?")}',
        ])
        print(f'  {rank:4d} {sd:4d} {cid:4d} {score:7.4f}  | {prop_str}')

    # CID 物理量の集約傾向 (top-K 全体)
    if args.cid_topk >= 5:
        print(f'\n[top-{args.cid_topk} CID 物理量集約]')
        all_props = [get_cid_properties(sd, cid)
                      for sd, cid, _ in cid_candidates[:args.cid_topk]]
        for key in ['n_alphas_currently', 'last_familiarity_max',
                    'current_stability', 'current_social', 'current_spread']:
            vals = [p.get(key, np.nan) for p in all_props if not pd.isna(p.get(key, np.nan))]
            if vals:
                print(f'  {key:30s} mean={np.mean(vals):.3f} median={np.median(vals):.3f} '
                      f'min={min(vals):.3f} max={max(vals):.3f} (n={len(vals)})')

        # final_state の分布
        states = [p.get('final_state') for p in all_props if p.get('final_state')]
        if states:
            from collections import Counter
            sc = Counter(states)
            print(f'  final_state 分布: {dict(sc)}')

    # 出力 CSV
    if args.out:
        prefix = Path(args.out)
        prefix.parent.mkdir(parents=True, exist_ok=True)

        # atom 候補
        atom_df = pd.DataFrame([{'rank': i+1, 'atom': a, 'probability': p}
                                  for i, (a, p) in enumerate(sorted_atoms[:args.atom_topk])])
        atom_out = prefix.with_suffix('.atoms.csv')
        atom_df.to_csv(atom_out, index=False, float_format='%.6f')

        # CID 候補
        cid_rows = []
        for rank, (sd, cid, score) in enumerate(cid_candidates[:args.cid_topk], 1):
            props = get_cid_properties(sd, cid)
            row = {'rank': rank, 'seed': sd, 'cid': cid, 'score': score}
            row.update(props)
            cid_rows.append(row)
        cid_df = pd.DataFrame(cid_rows)
        cid_out = prefix.with_suffix('.cids.csv')
        cid_df.to_csv(cid_out, index=False, float_format='%.6f')

        print(f'\nwrote {atom_out.name}, {cid_out.name}')


if __name__ == '__main__':
    main()
