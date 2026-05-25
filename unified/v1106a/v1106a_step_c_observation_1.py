#!/usr/bin/env python3
"""v1106a Step C — 観察 1: Atom → word 変換 (案 X + 案 Z-1 並列、7 系列)

設計書 v3 §2.2 + Web Claude 確認要請 11 案 Z-1 採用、接続式:
  案 X (主軸): score = Σ p_s7(atom) × (raw_scores_max(atom, word) / 10)
  案 Z-1 (補助): score = Σ p_s7(atom) × normalized_scores_max(atom, word)

各 event × 系列 × 案 で正規化、構造ラベル付与 (v1106 §1.1 継承)。

入力 (read-only):
  - unified/v1105a/outputs/main/trial_step4_distributions.parquet (s7 PC events)
  - language/lexicon/data/mapper_output/*_a1.jsonl (325 atom × LLM 1 億トークン判定)

出力:
  - unified/v1106a/outputs/main/observation_1_word_distributions.parquet
    (per (seed, event_id, series_id, formula, candidate_word) で probability)
  - unified/v1106a/outputs/main/observation_1_labels.parquet
    (per (seed, event_id, series_id, formula) で構造ラベル + 集計指標)
"""
from __future__ import annotations
import json, os, time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1105A_MAIN = REPO / 'unified/v1105a/outputs/main'
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'
MAPPER_DIR = REPO / 'language/lexicon/data/mapper_output'

MAX_PROB_THRESH = 0.999


def load_atom_to_words() -> dict:
    """atom → list of (word, raw_max, norm_max) lookup
    status=OK のみ (raw_scores 持ち)"""
    a2w = {}
    for fp in sorted(MAPPER_DIR.glob('*_a1.jsonl')):
        atom = fp.stem.replace('_a1', '').replace('_', '.', 1)
        entries = []
        with open(fp) as f:
            for line in f:
                d = json.loads(line)
                if d.get('status') != 'OK':
                    continue
                if 'raw_scores' not in d or 'normalized_scores' not in d:
                    continue
                raw_max = max(d['raw_scores'].values())
                norm_max = max(d['normalized_scores'].values())
                entries.append((d['word'], float(raw_max), float(norm_max)))
        if entries:
            a2w[atom] = entries
    return a2w


def assign_label(n_after: int, max_prob: float, entropy: float) -> str:
    if n_after == 0:
        return 'word_candidate_empty'
    if max_prob >= MAX_PROB_THRESH:
        return 'word_distribution_degenerate'
    if max_prob < MAX_PROB_THRESH and entropy > 0:
        return 'word_distribution_valid'
    return 'word_candidate_empty'


def compute_distribution(atoms_probs: dict, atom_to_words: dict, formula: str) -> dict:
    """formula = 'X' (raw_scores_max / 10) or 'Z1' (normalized_scores_max)"""
    score = defaultdict(float)
    for atom, p in atoms_probs.items():
        if atom not in atom_to_words:
            continue
        for word, raw_max, norm_max in atom_to_words[atom]:
            if formula == 'X':
                weight = raw_max / 10.0
            else:  # Z1
                weight = norm_max
            score[word] += p * weight
    total = sum(score.values())
    if total <= 0:
        return {}
    return {w: s / total for w, s in score.items()}


def main():
    V1106A_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106a Step C 観察 1: Atom → word 変換 (案 X + 案 Z-1) ===')
    t0 = time.time()

    # (1) atom → words lookup
    print('[1] atom → words lookup 構築')
    a2w = load_atom_to_words()
    n_words_per_atom = [len(v) for v in a2w.values()]
    print(f'  atoms with words: {len(a2w)}')
    print(f'  words per atom: mean={np.mean(n_words_per_atom):.1f}, '
          f'max={max(n_words_per_atom)}, min={min(n_words_per_atom)}')
    print(f'  unique words: {len(set(w for ws in a2w.values() for w, _, _ in ws))}')

    # (2) v1105a 7 系列 PC events
    print('\n[2] v1105a 7 系列 PC events 読み込み')
    dist = pd.read_parquet(V1105A_MAIN / 'trial_step4_distributions.parquet')
    pc = dist[dist['structural_label'] == 'distribution_valid'].copy()
    print(f'  PC rows: {len(pc):,}, events: {pc["event_id"].nunique()}, '
          f'series: {pc["series_id"].nunique()}')

    # (3) per (event, series) × 案 X/Z-1 で接続式適用
    print('\n[3] 接続式適用 (案 X + 案 Z-1 並列)')
    out_rows = []
    label_rows = []
    grouped = pc.groupby(['seed', 'event_id', 'series_id'])
    n_grp = len(grouped)
    cnt = 0

    for (sd, eid, sid), grp in grouped:
        cnt += 1
        if cnt % 5000 == 0:
            print(f'  processed {cnt:,}/{n_grp:,}, elapsed {time.time()-t0:.1f}s')

        input_atom = grp['input_atom'].iloc[0]
        cand_dict = dict(zip(grp['candidate_atom'], grp['probability']))

        for formula in ['X', 'Z1']:
            word_probs = compute_distribution(cand_dict, a2w, formula)
            if not word_probs:
                label_rows.append({
                    'seed': sd, 'event_id': eid, 'series_id': sid,
                    'formula': formula, 'input_atom': input_atom,
                    'n_words_after': 0, 'word_max_prob': np.nan,
                    'word_entropy': np.nan,
                    'structural_label': 'word_candidate_empty',
                })
                continue

            probs_arr = np.array(list(word_probs.values()))
            max_p = float(probs_arr.max())
            p_nz = probs_arr[probs_arr > 0]
            ent = float(-np.sum(p_nz * np.log(p_nz))) if len(p_nz) > 0 else 0.0
            label = assign_label(len(word_probs), max_p, ent)

            label_rows.append({
                'seed': sd, 'event_id': eid, 'series_id': sid,
                'formula': formula, 'input_atom': input_atom,
                'n_words_after': len(word_probs),
                'word_max_prob': max_p,
                'word_entropy': ent,
                'structural_label': label,
            })
            for word, p in word_probs.items():
                out_rows.append({
                    'seed': sd, 'event_id': eid, 'series_id': sid,
                    'formula': formula, 'input_atom': input_atom,
                    'candidate_word': word,
                    'probability': p,
                })

    df_dist = pd.DataFrame(out_rows).sort_values(
        ['seed', 'event_id', 'series_id', 'formula', 'candidate_word']).reset_index(drop=True)
    df_labels = pd.DataFrame(label_rows).sort_values(
        ['seed', 'event_id', 'series_id', 'formula']).reset_index(drop=True)

    out1 = V1106A_MAIN / 'observation_1_word_distributions.parquet'
    df_dist.to_parquet(out1, index=False)
    print(f'\nwrote {out1.name} ({len(df_dist):,} rows)')

    out2 = V1106A_MAIN / 'observation_1_labels.parquet'
    df_labels.to_parquet(out2, index=False)
    print(f'wrote {out2.name} ({len(df_labels):,} rows = {df_labels["event_id"].nunique()} events × 7 系列 × 2 案)')

    print(f'\n=== Step C 完了、elapsed {time.time()-t0:.1f}s ===')

    # --- サマリ ---
    print('\n--- formula × series_id × structural_label 件数 ---')
    pv = df_labels.groupby(['formula', 'series_id', 'structural_label']).size().unstack(fill_value=0)
    print(pv.to_string())

    print('\n--- 全体集計 ---')
    for formula in ['X', 'Z1']:
        sub = df_labels[df_labels['formula'] == formula]
        print(f'\nformula {formula}:')
        for lbl in ['word_candidate_empty', 'word_distribution_degenerate', 'word_distribution_valid']:
            n = (sub['structural_label'] == lbl).sum()
            print(f'  {lbl}: {n:,} ({100*n/len(sub):.2f}%)')

    print('\n--- word 候補数 (word_distribution_valid のみ、formula × series) ---')
    v = df_labels[df_labels['structural_label'] == 'word_distribution_valid']
    print(v.groupby(['formula', 'series_id']).agg(
        n_words_mean=('n_words_after', 'mean'),
        n_words_median=('n_words_after', 'median'),
        n_words_max=('n_words_after', 'max'),
        max_prob_mean=('word_max_prob', 'mean'),
        max_prob_median=('word_max_prob', 'median'),
        entropy_mean=('word_entropy', 'mean'),
    ).round(4).to_string())


if __name__ == '__main__':
    main()
