#!/usr/bin/env python3
"""v1106 Step C — 観察 1: Atom → synset 変換 (7 系列並列)

設計書 v1106 §2.2 + Web Claude 確認要請 8 案 A 採用:
  接続式: score(s_j) = Σ_i [ p_s7(atom_i) × syn_weight(atom_i, s_j) ]
  正規化: p_synset(s_j) = score(s_j) / Σ_k score(s_k)

実装:
- SynapseStore + v3.1-v3.5 patches overlay (再現性確保)
- v1105a trial_step4_distributions から 7 系列 PC events 抽出 (3,300 events × 7 系列)
- 各 (event, series) について atom → synset 接続、構造ラベル付与
- FND.spaceless は除外 (Web Claude 確認要請 9 案 A、防御的)

構造ラベル (v1105a §1.1 継承、Web Claude 確認要請 9 確定):
  synset_candidate_empty: n_synsets_after == 0
  synset_distribution_degenerate: synset_max_prob >= 0.999
  synset_distribution_valid: synset_max_prob < 0.999 AND entropy > 0
  synset_pipeline_complete: synset_distribution_valid 達成

入力 (read-only):
  - unified/v1105a/outputs/main/trial_step4_distributions.parquet
  - language/synapse/esde_synapses_v3.json + patches v3.1-v3.5

出力:
  - unified/v1106/outputs/main/observation_1_synset_distributions.parquet
    (per (seed, event_id, series_id, candidate_synset) で probability + メタ)
  - unified/v1106/outputs/main/observation_1_labels.parquet
    (per (seed, event_id, series_id) で構造ラベル + 集計指標)
  - unified/v1106/outputs/main/observation_1_excluded_fnd_spaceless.json
    (FND.spaceless 除外件数 + 警告ログ)
"""
from __future__ import annotations
import sys, json, time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
sys.path.insert(0, str(REPO / 'language'))
from synapse.store import SynapseStore

V1105A_MAIN = REPO / 'unified/v1105a/outputs/main'
V1106_MAIN = REPO / 'unified/v1106/outputs/main'
SYNAPSE_DIR = REPO / 'language/synapse'

MAX_PROB_THRESH = 0.999
EXCLUDED_ATOMS = {'FND.spaceless'}  # v1103 atom_centroids に無い、Web Claude 確認要請 9 案 A


def load_synapse_store() -> SynapseStore:
    """SynapseStore overlay (v3.1-v3.5)"""
    store = SynapseStore()
    store.load(
        str(SYNAPSE_DIR / 'esde_synapses_v3.json'),
        patches=[
            str(SYNAPSE_DIR / 'patches/synapse_v3.1.json'),
            str(SYNAPSE_DIR / 'patches/synapse_v3.2.json'),
            str(SYNAPSE_DIR / 'patches/synapse_v3.3.json'),
            str(SYNAPSE_DIR / 'patches/synapse_v3.3_hotfix.json'),
            str(SYNAPSE_DIR / 'patches/synapse_v3.4.json'),
            str(SYNAPSE_DIR / 'patches/synapse_v3.5.json'),
        ],
    )
    return store


def build_atom_to_synsets(store: SynapseStore) -> dict:
    """atom → list of (synset_id, weight) 逆引き lookup"""
    atom_to_synsets = defaultdict(list)
    n_excluded = 0
    for synset_id, edges in store.synapses.items():
        for e in edges:
            atom = e.get('concept_id')
            if atom in EXCLUDED_ATOMS:
                n_excluded += 1
                continue
            weight = e.get('weight', 0.0)
            atom_to_synsets[atom].append((synset_id, weight))
    return dict(atom_to_synsets), n_excluded


def compute_synset_distribution(atoms_probs: dict, atom_to_synsets: dict) -> dict:
    """接続式: score(s_j) = Σ p(atom_i) × syn_weight(atom_i, s_j)、正規化
    atoms_probs: {atom: p}
    return: {synset_id: probability}
    """
    score = defaultdict(float)
    for atom, p in atoms_probs.items():
        if atom not in atom_to_synsets:
            continue  # Synapse 未登録 atom (FND.spaceless は除外済、他は無関係)
        for synset_id, weight in atom_to_synsets[atom]:
            score[synset_id] += p * weight
    total = sum(score.values())
    if total <= 0:
        return {}
    return {sid: s / total for sid, s in score.items()}


def assign_label(n_after: int, max_prob: float, entropy: float) -> str:
    if n_after == 0:
        return 'synset_candidate_empty'
    if max_prob >= MAX_PROB_THRESH:
        return 'synset_distribution_degenerate'
    if max_prob < MAX_PROB_THRESH and entropy > 0:
        return 'synset_distribution_valid'
    return 'synset_candidate_empty'


def main():
    V1106_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106 Step C 観察 1: Atom → synset 変換 ===')
    t0 = time.time()

    # (1) Synapse overlay
    print('[1] SynapseStore overlay 読み込み')
    store = load_synapse_store()
    atom_to_synsets, n_excluded_edges = build_atom_to_synsets(store)
    print(f'  synsets: {len(store.synapses):,}')
    print(f'  atom → synsets lookup: {len(atom_to_synsets)} atoms')
    print(f'  excluded edges (FND.spaceless): {n_excluded_edges}')

    # (2) v1105a 7 系列 PC events 読み込み
    print('\n[2] v1105a 7 系列 PC events 読み込み')
    dist = pd.read_parquet(V1105A_MAIN / 'trial_step4_distributions.parquet')
    pc = dist[dist['structural_label'] == 'distribution_valid'].copy()
    print(f'  PC rows: {len(pc):,}, events: {pc["event_id"].nunique()}, '
          f'series: {pc["series_id"].nunique()}')

    # (3) per (seed, event, series) で接続式適用
    print('\n[3] 接続式適用 + 構造ラベル付与')
    out_rows = []
    label_rows = []
    excluded_input_atoms = []  # 入力 atom が FND.spaceless だった events
    grouped = pc.groupby(['seed', 'event_id', 'series_id'])
    n_grp = len(grouped)
    cnt = 0
    for (sd, eid, sid), grp in grouped:
        cnt += 1
        if cnt % 5000 == 0:
            print(f'  processed {cnt:,}/{n_grp:,}, elapsed {time.time()-t0:.1f}s')

        # input_atom (FND.spaceless 除外、防御的)
        input_atom = grp['input_atom'].iloc[0]
        if input_atom in EXCLUDED_ATOMS:
            excluded_input_atoms.append({'seed': sd, 'event_id': eid, 'series_id': sid,
                                          'input_atom': input_atom})
            continue

        # candidate atoms とその probability
        cand_dict = dict(zip(grp['candidate_atom'], grp['probability']))
        # FND.spaceless 候補を除外 (防御的)
        cand_dict = {a: p for a, p in cand_dict.items() if a not in EXCLUDED_ATOMS}
        if not cand_dict:
            label_rows.append({
                'seed': sd, 'event_id': eid, 'series_id': sid,
                'input_atom': input_atom,
                'n_synsets_after': 0,
                'synset_max_prob': np.nan,
                'synset_entropy': np.nan,
                'structural_label': 'synset_candidate_empty',
            })
            continue

        # 接続式適用
        synset_probs = compute_synset_distribution(cand_dict, atom_to_synsets)
        if not synset_probs:
            label_rows.append({
                'seed': sd, 'event_id': eid, 'series_id': sid,
                'input_atom': input_atom,
                'n_synsets_after': 0,
                'synset_max_prob': np.nan,
                'synset_entropy': np.nan,
                'structural_label': 'synset_candidate_empty',
            })
            continue

        # 構造ラベル
        probs_arr = np.array(list(synset_probs.values()))
        max_p = float(probs_arr.max())
        p_nz = probs_arr[probs_arr > 0]
        ent = float(-np.sum(p_nz * np.log(p_nz))) if len(p_nz) > 0 else 0.0
        label = assign_label(len(synset_probs), max_p, ent)

        label_rows.append({
            'seed': sd, 'event_id': eid, 'series_id': sid,
            'input_atom': input_atom,
            'n_synsets_after': len(synset_probs),
            'synset_max_prob': max_p,
            'synset_entropy': ent,
            'structural_label': label,
        })

        # per (synset) 出力 (LAYER_A 容量制御のため全件保存、後でフィルタ可)
        for synset_id, p in synset_probs.items():
            out_rows.append({
                'seed': sd, 'event_id': eid, 'series_id': sid,
                'input_atom': input_atom,
                'candidate_synset': synset_id,
                'probability': p,
            })

    df_dist = pd.DataFrame(out_rows).sort_values(
        ['seed', 'event_id', 'series_id', 'candidate_synset']).reset_index(drop=True)
    df_labels = pd.DataFrame(label_rows).sort_values(
        ['seed', 'event_id', 'series_id']).reset_index(drop=True)

    out1 = V1106_MAIN / 'observation_1_synset_distributions.parquet'
    df_dist.to_parquet(out1, index=False)
    print(f'\nwrote {out1.name} ({len(df_dist):,} rows)')

    out2 = V1106_MAIN / 'observation_1_labels.parquet'
    df_labels.to_parquet(out2, index=False)
    print(f'wrote {out2.name} ({len(df_labels):,} rows)')

    # 除外件数記録
    excluded_report = {
        'excluded_atoms': sorted(EXCLUDED_ATOMS),
        'n_excluded_synapse_edges': n_excluded_edges,
        'n_excluded_input_atom_events': len(excluded_input_atoms),
        'note': ('FND.spaceless は v1103 atom_centroids に存在しないため候補から除外。'
                  'Web Claude 確認要請 9 案 A 採用、Genesis 側 Web Claude が v1106 完了後に'
                  '欠落理由を把握すべき (v1107 以降の主題候補)。'),
    }
    out3 = V1106_MAIN / 'observation_1_excluded_fnd_spaceless.json'
    out3.write_text(json.dumps(excluded_report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'wrote {out3.name}')

    print(f'\n=== Step C 完了、elapsed {time.time()-t0:.1f}s ===')

    # --- サマリ ---
    print('\n--- series_id × structural_label 件数 ---')
    pv = df_labels.groupby(['series_id', 'structural_label']).size().unstack(fill_value=0)
    pv['total'] = pv.sum(axis=1)
    if 'synset_distribution_valid' in pv.columns:
        pv['valid_rate'] = (pv['synset_distribution_valid'] / pv['total']).round(4)
    print(pv.to_string())

    print('\n--- 全体集計 ---')
    print(f'total event-series: {len(df_labels):,}')
    for lbl in ['synset_candidate_empty', 'synset_distribution_degenerate',
                'synset_distribution_valid']:
        n = (df_labels['structural_label'] == lbl).sum()
        print(f'  {lbl}: {n:,} ({100*n/len(df_labels):.2f}%)')

    print('\n--- synset 候補数 (synset_distribution_valid のみ) ---')
    v = df_labels[df_labels['structural_label'] == 'synset_distribution_valid']
    if len(v) > 0:
        print(f'  n_synsets_after: mean={v["n_synsets_after"].mean():.1f}, '
              f'median={v["n_synsets_after"].median():.0f}, '
              f'max={v["n_synsets_after"].max()}, min={v["n_synsets_after"].min()}')
        print(f'  synset_max_prob: mean={v["synset_max_prob"].mean():.4f}, '
              f'median={v["synset_max_prob"].median():.4f}')
        print(f'  synset_entropy: mean={v["synset_entropy"].mean():.4f}')


if __name__ == '__main__':
    main()
