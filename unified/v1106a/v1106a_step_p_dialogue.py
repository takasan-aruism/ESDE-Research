#!/usr/bin/env python3
"""v1106a Step P — ESDE 連続対話 (C-7)

ESDE と人間 (Code A) の往復対話を 1 ターンずつ進める CLI。
状態 (現 CID) と履歴を JSON ファイルで保持。

ターン構造:
  T0: 初期 CID 設定 → ESDE 発話
  T1: 人間応答 (word 列) → 逆引き → 次 CID → ESDE 次発話
  T2: ...

使い方:
  # 初期化 (CID 指定 or ランダム)
  python3 v1106a_step_p_dialogue.py init --dlg my_chat --seed 0 --cid 198

  # 人間応答を投げて次ターンへ
  python3 v1106a_step_p_dialogue.py turn --dlg my_chat --response "I sense the fragrance"

  # 履歴表示
  python3 v1106a_step_p_dialogue.py show --dlg my_chat

入力 (read-only):
  - unified/v1103/outputs/main/atom_centroids_48d_raw.parquet
  - developmental/v106/outputs/main/cid_atom_sim_matrix_seed{N}.parquet
  - developmental/v106/outputs/main/axes_metadata.json
  - language/lexicon/data/mapper_output/*_a1.jsonl
  - developmental/v105/diag_v105_main/subjects/per_subject_seed{N}.csv

出力:
  - unified/v1106a/outputs/main/dialogue_{dlg_id}.json (履歴)
"""
from __future__ import annotations
import argparse, json, re, sys, time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1103_MAIN = REPO / 'unified/v1103/outputs/main'
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V105_SUB = REPO / 'developmental/v105/diag_v105_main/subjects'
MAPPER_DIR = REPO / 'language/lexicon/data/mapper_output'
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'

STOPWORDS = set("""
a an the and or but of in on at to for with by from is are was were be been being
this that these those i you he she it we they me him her us them my your his
its our their as if then so do does did has have had not no yes very just
""".split())


def get_axes():
    am = json.load(open(V106_MAIN / 'axes_metadata.json'))
    return [f'{ax["name"]}.{lvl}' for ax in am['axes_order'] for lvl in ax['level_names']]


_CACHE = {}

def load_resources():
    if 'loaded' in _CACHE:
        return _CACHE
    axes = get_axes()
    ac = pd.read_parquet(V1103_MAIN / 'atom_centroids_48d_raw.parquet')
    atom_to_centroid = {row['atom']: np.array([row[ax] for ax in axes], dtype=np.float64)
                         for _, row in ac.iterrows()}
    atom_to_word_sims = {}
    word_to_atom_vec = defaultdict(dict)
    for fp in sorted(MAPPER_DIR.glob('*_a1.jsonl')):
        atom = fp.stem.replace('_a1', '').replace('_', '.', 1)
        if atom not in atom_to_centroid: continue
        centroid = atom_to_centroid[atom]
        cn = np.linalg.norm(centroid)
        if cn == 0: continue
        wlist = []
        with open(fp) as f:
            for line in f:
                r = json.loads(line)
                if r.get('status') != 'OK': continue
                rs = r.get('raw_scores')
                if not isinstance(rs, dict): continue
                vec = np.array([rs.get(ax, 0.0) for ax in axes], dtype=np.float64)
                wn = np.linalg.norm(vec)
                if wn == 0: continue
                sim = float(np.dot(centroid, vec) / (cn * wn))
                wlist.append((r['word'], sim, vec))
                word_to_atom_vec[r['word']][atom] = vec
        atom_to_word_sims[atom] = wlist
    _CACHE.update({'axes': axes, 'atom_to_centroid': atom_to_centroid,
                    'atom_to_word_sims': atom_to_word_sims,
                    'word_to_atom_vec': dict(word_to_atom_vec), 'loaded': True})
    return _CACHE


def tokenize(text):
    words = re.findall(r"[a-zA-Z][a-zA-Z\-']*", text.lower())
    return [w for w in words if w not in STOPWORDS]


def get_cid_props(seed, cid):
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
            v = r[c]
            if isinstance(v, (np.floating, np.integer)):
                v = v.item()
            if isinstance(v, float) and np.isnan(v):
                v = None
            out[c] = v
    return out


def get_cid_vec(seed, cid):
    fp = V106_MAIN / f'cid_structure_profile_seed{seed}.csv'
    df = pd.read_csv(fp)
    row = df[df['cid'] == cid]
    if len(row) == 0:
        raise ValueError(f'CID {cid} not found in seed {seed}')
    return row.iloc[0][[f'dim_{i}' for i in range(48)]].values.astype(np.float64)


def cid_to_atom_probs(cid_vec, atom_to_centroid, k=10):
    cn = np.linalg.norm(cid_vec)
    sims = {}
    for atom, c in atom_to_centroid.items():
        an = np.linalg.norm(c)
        if an > 0 and cn > 0:
            sims[atom] = float(np.dot(cid_vec, c) / (cn * an))
        else:
            sims[atom] = 0.0
    sorted_a = sorted(sims.items(), key=lambda x: -x[1])[:k]
    raw = [max(s, 0.0) for _, s in sorted_a]
    total = sum(raw)
    if total <= 0:
        return [(a, 1.0/len(sorted_a)) for a, _ in sorted_a]
    return [(a, r/total) for (a, _), r in zip(sorted_a, raw)], sims


def cid_to_words(cid_vec, k=15, atom_topk=10):
    res = load_resources()
    atom_probs, _ = cid_to_atom_probs(cid_vec, res['atom_to_centroid'], k=atom_topk)
    word_score = defaultdict(float)
    for atom, p in atom_probs:
        for word, sim, _ in res['atom_to_word_sims'].get(atom, []):
            word_score[word] += p * max(sim, 0.0)
    total = sum(word_score.values())
    if total <= 0:
        return [], atom_probs
    words = sorted(word_score.items(), key=lambda x: -x[1])[:k]
    words = [(w, p/total) for w, p in words]
    return words, atom_probs


def words_to_atom_probs(words, word_to_atom_vec):
    atom_score = defaultdict(float)
    matched = []
    unmatched = []
    for w in words:
        if w not in word_to_atom_vec:
            unmatched.append(w); continue
        matched.append(w)
        for atom, vec in word_to_atom_vec[w].items():
            atom_score[atom] += float(np.linalg.norm(vec))
    total = sum(atom_score.values())
    if total <= 0:
        return {}, matched, unmatched
    return {a: s/total for a, s in atom_score.items()}, matched, unmatched


def atom_to_cid_candidates(atom_probs, seeds=None, topk=20):
    if seeds is None:
        seeds = list(range(24))
    results = []
    for sd in seeds:
        fp = V106_MAIN / f'cid_atom_sim_matrix_seed{sd}.parquet'
        if not fp.exists(): continue
        sim_df = pd.read_parquet(fp)
        scores = np.zeros(len(sim_df))
        for atom, p in atom_probs.items():
            if atom in sim_df.columns:
                sims = sim_df[atom].values.astype(np.float64)
                scores += p * np.clip(sims, 0, None)
        for i, cid in enumerate(sim_df['cid'].values):
            results.append((sd, int(cid), float(scores[i])))
    results.sort(key=lambda x: -x[2])
    return results[:topk]


def dialogue_path(dlg_id):
    V1106A_MAIN.mkdir(parents=True, exist_ok=True)
    return V1106A_MAIN / f'dialogue_{dlg_id}.json'


def load_dialogue(dlg_id):
    fp = dialogue_path(dlg_id)
    if not fp.exists():
        return None
    return json.loads(fp.read_text())


def save_dialogue(dlg_id, state):
    fp = dialogue_path(dlg_id)
    fp.write_text(json.dumps(state, indent=2, ensure_ascii=False, default=str))


def render_esde_turn(seed, cid):
    """ESDE 1 ターン: 現 CID から発話"""
    cid_vec = get_cid_vec(seed, cid)
    words, atom_probs = cid_to_words(cid_vec, k=15, atom_topk=10)
    props = get_cid_props(seed, cid)
    return {
        'seed': seed, 'cid': cid,
        'cid_vec_norm': float(np.linalg.norm(cid_vec)),
        'cid_props': props,
        'atom_probs': [{'atom': a, 'prob': float(p)} for a, p in atom_probs],
        'top_words': [{'word': w, 'prob': float(p)} for w, p in words],
    }


def cmd_init(args):
    res = load_resources()
    if args.cid is not None and args.seed is not None:
        seed, cid = args.seed, args.cid
    else:
        seed = args.seed if args.seed is not None else int(np.random.randint(24))
        fp = V106_MAIN / f'cid_structure_profile_seed{seed}.csv'
        df = pd.read_csv(fp, usecols=['cid'])
        cid = int(np.random.choice(df['cid'].values))
    turn = render_esde_turn(seed, cid)
    state = {
        'dialogue_id': args.dlg,
        'created_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'turns': [{'turn': 0, 'role': 'esde', **turn}],
    }
    save_dialogue(args.dlg, state)
    print_turn(0, state['turns'][0])


def cmd_turn(args):
    res = load_resources()
    state = load_dialogue(args.dlg)
    if state is None:
        print(f'ERROR: dialogue {args.dlg} not found. Run "init" first.')
        return
    turn_idx = len(state['turns'])
    response = args.response
    words = tokenize(response)
    if not words:
        print(f'ERROR: no valid words in response "{response}"')
        return

    atom_probs, matched, unmatched = words_to_atom_probs(
        words, res['word_to_atom_vec'])
    if not atom_probs:
        print(f'ERROR: no atoms found for words {words}')
        return

    sorted_atoms = sorted(atom_probs.items(), key=lambda x: -x[1])[:10]
    cid_candidates = atom_to_cid_candidates(dict(sorted_atoms),
                                              seeds=args.seeds, topk=15)
    if not cid_candidates:
        print(f'ERROR: no CID candidates')
        return

    # 次 CID: top-1 (デフォルト) または sampling
    if args.sample:
        scores = np.array([s for _, _, s in cid_candidates[:5]])
        probs = scores / scores.sum() if scores.sum() > 0 else None
        idx = int(np.random.choice(len(scores), p=probs))
        next_seed, next_cid, next_score = cid_candidates[idx]
    else:
        next_seed, next_cid, next_score = cid_candidates[0]

    # 人間ターンを記録
    human_turn = {
        'turn': turn_idx, 'role': 'human',
        'response': response,
        'tokens': words,
        'matched_words': matched,
        'unmatched_words': unmatched,
        'top_atoms': [{'atom': a, 'prob': float(p)} for a, p in sorted_atoms[:5]],
        'top_cid_candidates': [
            {'seed': s, 'cid': c, 'score': sc, 'props': get_cid_props(s, c)}
            for s, c, sc in cid_candidates[:5]
        ],
        'chosen_next': {'seed': next_seed, 'cid': next_cid, 'score': next_score,
                         'mode': 'sampling' if args.sample else 'top1'},
    }
    state['turns'].append(human_turn)
    print_turn(turn_idx, human_turn)

    # ESDE 次ターン
    esde_turn = render_esde_turn(next_seed, next_cid)
    esde_turn = {'turn': turn_idx + 1, 'role': 'esde', **esde_turn}
    state['turns'].append(esde_turn)
    save_dialogue(args.dlg, state)
    print_turn(turn_idx + 1, esde_turn)


def cmd_show(args):
    state = load_dialogue(args.dlg)
    if state is None:
        print(f'ERROR: dialogue {args.dlg} not found')
        return
    print(f'=== Dialogue {args.dlg} (created {state["created_at"]}) ===\n')
    for t in state['turns']:
        print_turn(t['turn'], t)


def print_turn(turn_idx, t):
    role = t['role']
    if role == 'esde':
        props = t.get('cid_props', {})
        prop_str = ', '.join([f'{k}={v}' for k, v in props.items() if v is not None])
        print(f'\n[T{turn_idx}] ESDE (seed={t["seed"]}, cid={t["cid"]}, vec_norm={t["cid_vec_norm"]:.2f})')
        print(f'         props: {prop_str}')
        atoms = ', '.join([f'{a["atom"]}({a["prob"]:.3f})' for a in t['atom_probs'][:5]])
        print(f'         atoms: {atoms}')
        words = ', '.join([f'{w["word"]}({w["prob"]:.3f})' for w in t['top_words'][:10]])
        print(f'         words: {words}')
    elif role == 'human':
        print(f'\n[T{turn_idx}] HUMAN: "{t["response"]}"')
        print(f'         tokens: {t["tokens"]}')
        if t.get('unmatched_words'):
            print(f'         unmatched: {t["unmatched_words"]}')
        atoms = ', '.join([f'{a["atom"]}({a["prob"]:.3f})' for a in t['top_atoms']])
        print(f'         top atoms: {atoms}')
        cn = t['chosen_next']
        print(f'         → next CID: seed={cn["seed"]}, cid={cn["cid"]}, score={cn["score"]:.4f} ({cn["mode"]})')


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)

    p_init = sub.add_parser('init')
    p_init.add_argument('--dlg', required=True)
    p_init.add_argument('--seed', type=int, default=None)
    p_init.add_argument('--cid', type=int, default=None)

    p_turn = sub.add_parser('turn')
    p_turn.add_argument('--dlg', required=True)
    p_turn.add_argument('--response', required=True)
    p_turn.add_argument('--seeds', type=int, nargs='+', default=None)
    p_turn.add_argument('--sample', action='store_true',
                         help='top-5 candidates から重み付きサンプル')

    p_show = sub.add_parser('show')
    p_show.add_argument('--dlg', required=True)

    args = ap.parse_args()
    {'init': cmd_init, 'turn': cmd_turn, 'show': cmd_show}[args.cmd](args)


if __name__ == '__main__':
    main()
