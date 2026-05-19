#!/usr/bin/env python3
"""v1103 Step B (実装 1) — atom_centroids_48d.csv 生成 (raw + normalized 両方並列)

§5.1 確定: ゼロの意味は raw/normalized 両方並列で観察 (留保 #33 系列同型)
§5.2 確定: Code A が *_a1.jsonl から生成

入力: language/lexicon/data/mapper_output/*_a1.jsonl × 325 Atom
   各 *_a1.jsonl の row: word, pos, atom, raw_scores (48 dict), normalized_scores
   (48 dict、ただし mean n_keys 47.06), focus_rate, status, ...

出力:
- atom_centroids_48d_raw.parquet: per Atom の raw_scores mean (48 軸)
- atom_centroids_48d_normalized.parquet: per Atom の normalized_scores mean (48 軸)
- atom_quality.parquet: per Atom の focus_rate / status 分布 / Nonzero 軸数 mean

書込み: unified/v1103/outputs/main/ 配下のみ (物理層 frozen)
"""
from __future__ import annotations
import json, glob, time
from pathlib import Path
import pandas as pd
import numpy as np

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
MAPPER_DIR = REPO_ROOT / 'language/lexicon/data/mapper_output'
OUT_MAIN = REPO_ROOT / 'unified/v1103/outputs/main'


def main():
    OUT_MAIN.mkdir(parents=True, exist_ok=True)
    files = sorted(MAPPER_DIR.glob('*_a1.jsonl'))
    print(f'=== v1103 Step B atom_centroids 生成 ===')
    print(f'input: {len(files)} *_a1.jsonl files')

    t0 = time.time()
    rows_raw, rows_norm, rows_qual = [], [], []
    all_axis_keys = None

    for fp in files:
        atom = fp.stem.replace('_a1', '').replace('_', '.', 1)
        words = []
        with open(fp) as f:
            for ln in f:
                try:
                    words.append(json.loads(ln))
                except json.JSONDecodeError:
                    pass
        if not words:
            continue

        # 軸キー抽出 (全 word の和集合)
        raw_keys = set()
        norm_keys = set()
        for w in words:
            if isinstance(w.get('raw_scores'), dict):
                raw_keys.update(w['raw_scores'].keys())
            if isinstance(w.get('normalized_scores'), dict):
                norm_keys.update(w['normalized_scores'].keys())
        union_keys = sorted(raw_keys | norm_keys)
        if all_axis_keys is None:
            all_axis_keys = union_keys

        # per Atom centroid (raw / normalized)
        raw_cent = {k: [] for k in union_keys}
        norm_cent = {k: [] for k in union_keys}
        focus_rates = []
        statuses = []
        nonzero_raw = []
        nonzero_norm = []

        for w in words:
            rs = w.get('raw_scores', {})
            ns = w.get('normalized_scores', {})
            for k in union_keys:
                if isinstance(rs, dict):
                    raw_cent[k].append(float(rs.get(k, 0.0)))
                if isinstance(ns, dict):
                    norm_cent[k].append(float(ns.get(k, 0.0)))
            focus_rates.append(float(w.get('focus_rate', 0.0)))
            statuses.append(w.get('status', '?'))
            if isinstance(rs, dict):
                nonzero_raw.append(sum(1 for v in rs.values() if v != 0))
            if isinstance(ns, dict):
                nonzero_norm.append(sum(1 for v in ns.values() if v != 0))

        # mean centroid
        raw_row = {'atom': atom, 'n_words': len(words)}
        norm_row = {'atom': atom, 'n_words': len(words)}
        for k in union_keys:
            raw_row[k] = float(np.mean(raw_cent[k])) if raw_cent[k] else 0.0
            norm_row[k] = float(np.mean(norm_cent[k])) if norm_cent[k] else 0.0
        rows_raw.append(raw_row)
        rows_norm.append(norm_row)

        # 品質統計
        from collections import Counter
        cstat = Counter(statuses)
        rows_qual.append({
            'atom': atom,
            'n_words': len(words),
            'focus_rate_mean': float(np.mean(focus_rates)) if focus_rates else 0.0,
            'focus_rate_std': float(np.std(focus_rates)) if focus_rates else 0.0,
            'nonzero_raw_mean': float(np.mean(nonzero_raw)) if nonzero_raw else 0.0,
            'nonzero_norm_mean': float(np.mean(nonzero_norm)) if nonzero_norm else 0.0,
            'n_OK': cstat.get('OK', 0),
            'n_Diffuse_Observation': cstat.get('Diffuse_Observation', 0),
            'n_Observation_Failed': cstat.get('Observation_Failed', 0),
            'frac_OK': cstat.get('OK', 0) / len(words),
        })

    df_raw = pd.DataFrame(rows_raw)
    df_norm = pd.DataFrame(rows_norm)
    df_qual = pd.DataFrame(rows_qual)

    df_raw.to_parquet(OUT_MAIN / 'atom_centroids_48d_raw.parquet', index=False)
    df_norm.to_parquet(OUT_MAIN / 'atom_centroids_48d_normalized.parquet', index=False)
    df_qual.to_parquet(OUT_MAIN / 'atom_quality.parquet', index=False)

    elapsed = time.time() - t0
    print(f'生成完了 ({elapsed:.1f}s):')
    print(f'  atom_centroids_48d_raw.parquet: {len(df_raw)} atoms × {len(union_keys)} axes')
    print(f'  atom_centroids_48d_normalized.parquet: {len(df_norm)} atoms × {len(union_keys)} axes')
    print(f'  atom_quality.parquet: {len(df_qual)} atoms')
    print(f'\n品質統計サマリ (24 atoms sample):')
    print(df_qual[['atom','n_words','focus_rate_mean','nonzero_raw_mean','nonzero_norm_mean','frac_OK']].head(5).to_string(index=False))
    print(f'\n全 Atom 統計:')
    print(f'  n_words mean: {df_qual["n_words"].mean():.1f}')
    print(f'  focus_rate mean of mean: {df_qual["focus_rate_mean"].mean():.3f}')
    print(f'  nonzero_raw mean of mean: {df_qual["nonzero_raw_mean"].mean():.2f}/48')
    print(f'  nonzero_norm mean of mean: {df_qual["nonzero_norm_mean"].mean():.2f}/48')
    print(f'  frac_OK mean: {df_qual["frac_OK"].mean():.3f}')


if __name__ == '__main__':
    main()
