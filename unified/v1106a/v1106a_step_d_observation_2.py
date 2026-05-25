#!/usr/bin/env python3
"""v1106a Step D — 観察 2: mapper_output と s7 確率の整合

設計書 §2.3 通り、各 event × 系列 × 案 で alignment 指標計算:
- top1_atom_top1_score (案 X: raw_scores_max / 案 Z-1: normalized_scores_max)
- top1_atom_mean_score
- top1_atom_n_word_links
- top5_atom_top1_score_mean
- atom_word_rank_correlation (top5 atom の prob 順位 vs top1 score 順位 Spearman)

入力 (read-only):
  - unified/v1105a/outputs/main/trial_step4_distributions.parquet (s7 PC events)
  - language/lexicon/data/mapper_output/*_a1.jsonl

出力:
  - unified/v1106a/outputs/main/observation_2_mapper_alignment.parquet
    (per (seed, event_id, series_id, formula) で alignment 指標)
"""
from __future__ import annotations
import json, os, time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

REPO = Path('/home/takasan/esde/ESDE-Research')
V1105A_MAIN = REPO / 'unified/v1105a/outputs/main'
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'
MAPPER_DIR = REPO / 'language/lexicon/data/mapper_output'


def load_atom_to_words_sorted() -> dict:
    """atom → list of (word, raw_max, norm_max)、raw_max 降順 sort 済"""
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
        # raw_max 降順 sort
        entries.sort(key=lambda x: -x[1])
        if entries:
            a2w[atom] = entries
    return a2w


def main():
    V1106A_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106a Step D 観察 2: mapper_output と s7 整合 ===')
    t0 = time.time()

    # (1) atom → words lookup (raw_max 降順)
    print('[1] atom → words lookup 構築 (raw_max 降順)')
    a2w = load_atom_to_words_sorted()
    print(f'  atoms: {len(a2w)}')

    # (2) v1105a 7 系列 PC events
    print('\n[2] v1105a PC events 読み込み')
    dist = pd.read_parquet(V1105A_MAIN / 'trial_step4_distributions.parquet')
    pc = dist[dist['structural_label'] == 'distribution_valid'].copy()
    print(f'  PC rows: {len(pc):,}')

    # (3) per (event, series) × formula alignment 計算
    print('\n[3] alignment 計算 (案 X: raw_max / 案 Z-1: norm_max)')
    out_rows = []
    grouped = pc.groupby(['seed', 'event_id', 'series_id'])
    n_grp = len(grouped)
    cnt = 0
    for (sd, eid, sid), grp in grouped:
        cnt += 1
        if cnt % 5000 == 0:
            print(f'  processed {cnt:,}/{n_grp:,}, elapsed {time.time()-t0:.1f}s')

        grp_sorted = grp.sort_values('probability', ascending=False)
        if len(grp_sorted) == 0:
            continue
        top1_atom = grp_sorted.iloc[0]['candidate_atom']
        top5_atoms = grp_sorted.head(5)['candidate_atom'].tolist()
        top5_probs = grp_sorted.head(5)['probability'].tolist()

        for formula in ['X', 'Z1']:
            # top1 atom の top1 word, mean, n_links (案ごとに sort key 異なる)
            if top1_atom in a2w:
                words = a2w[top1_atom]
                if formula == 'X':
                    # raw_max 降順 sort 済、top1 は先頭
                    top1_score = words[0][1]  # raw_max
                    mean_score = float(np.mean([w[1] for w in words]))
                else:  # Z1
                    # norm_max 降順で sort
                    norm_sorted = sorted(words, key=lambda x: -x[2])
                    top1_score = norm_sorted[0][2]
                    mean_score = float(np.mean([w[2] for w in words]))
                n_links = len(words)
            else:
                top1_score = np.nan
                mean_score = np.nan
                n_links = 0

            # top5 atom の top1 score 平均
            top5_scores = []
            for a in top5_atoms:
                if a in a2w and a2w[a]:
                    if formula == 'X':
                        top5_scores.append(a2w[a][0][1])
                    else:
                        top5_scores.append(max(w[2] for w in a2w[a]))
            top5_score_mean = float(np.mean(top5_scores)) if top5_scores else np.nan

            # rank correlation: top5 atom の prob 順位 vs top1 score 順位 Spearman
            rank_corr = np.nan
            if len(top5_atoms) >= 3 and len(top5_scores) == len(top5_atoms):
                valid = [(p, s) for p, s in zip(top5_probs, top5_scores)
                         if not np.isnan(s)]
                if len(valid) >= 3 and len(set(s for _, s in valid)) > 1 and \
                   len(set(p for p, _ in valid)) > 1:
                    prob_arr = [p for p, _ in valid]
                    score_arr = [s for _, s in valid]
                    rho, _ = spearmanr(prob_arr, score_arr)
                    if not np.isnan(rho):
                        rank_corr = float(rho)

            out_rows.append({
                'seed': sd, 'event_id': eid, 'series_id': sid, 'formula': formula,
                'top1_atom': top1_atom,
                'top1_atom_top1_score': float(top1_score) if not np.isnan(top1_score) else np.nan,
                'top1_atom_mean_score': mean_score,
                'top1_atom_n_word_links': n_links,
                'top5_atom_top1_score_mean': top5_score_mean,
                'atom_word_rank_correlation': rank_corr,
                'n_atoms_top5': len(top5_atoms),
            })

    df = pd.DataFrame(out_rows).sort_values(
        ['seed', 'event_id', 'series_id', 'formula']).reset_index(drop=True)
    out = V1106A_MAIN / 'observation_2_mapper_alignment.parquet'
    df.to_parquet(out, index=False)
    print(f'\nwrote {out.name} ({len(df):,} rows, elapsed {time.time()-t0:.1f}s)')

    # --- サマリ ---
    cols = ['top1_atom_top1_score', 'top1_atom_mean_score', 'top1_atom_n_word_links',
            'top5_atom_top1_score_mean', 'atom_word_rank_correlation']
    print('\n--- formula × series_id 別 alignment mean ---')
    print(df.groupby(['formula', 'series_id'])[cols].mean().round(4).to_string())

    print('\n--- atom_word_rank_correlation 分布 (formula 別) ---')
    for formula in ['X', 'Z1']:
        sub = df[df['formula'] == formula]['atom_word_rank_correlation'].dropna()
        if len(sub) > 0:
            print(f'  {formula}: n={len(sub):,}, mean={sub.mean():.4f}, '
                  f'median={sub.median():.4f}, positive_rate={(sub>0).mean():.4f}, '
                  f'>0.5={(sub>0.5).mean():.4f}, <-0.5={(sub<-0.5).mean():.4f}')


if __name__ == '__main__':
    main()
