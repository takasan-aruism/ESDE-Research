#!/usr/bin/env python3
"""v1103 Step C — 段 4-b 連想 + 段 4-c 48 次元密度 + 段 4-d 確率分布

設計書 §2.3-2.7 + GPT 監査 7 点 + §5.1 (raw/norm 両方並列):

段 4-b 連想を辿る:
  起点 atom (v1102 primary table atom_top1) →
  - 離散リンク: Constitution Couple 6 件 (proposals.json B_COUPLE)
  - 連続地形: A1 48 次元近傍 top-k (raw/norm 両方並列)
  単一 48 次元空間内、MiniLM 等異種空間経由なし

段 4-c 48 次元密度 (4 種並列、GPT 監査 1):
  - raw 密度
  - quality-weighted 密度 (focus_rate 重み)
  - constitution-adjusted 密度 (Monitor caution flag)
  - receiver-conditioned 密度 (受け手構造別、自然に出る)
  multi-k sensitivity (GPT 監査 2): k=5/10/20

段 4-d 確率分布出力 (GPT 監査 7):
  response_atom_distribution = 自然言語応答でなく候補確率分布
  argmax 取らない、Aruism 対称性 (100% を作らない)

入出力:
  入力: v1102 primary_table.parquet + atom_centroids_48d_raw/norm.parquet
        + proposals.json + atom_quality.parquet
  出力: response_atom_distribution.parquet (per cell × candidate atom × weight)
        + density_summary.parquet (per cell 4 種密度の指標)
"""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1102_MAIN = REPO_ROOT / 'unified/v1102/outputs/main'
V1103_MAIN = REPO_ROOT / 'unified/v1103/outputs/main'

K_VALUES = [5, 10, 20]  # multi-k sensitivity (GPT 監査 2)


def load_inputs():
    pt = pd.read_parquet(V1102_MAIN / 'primary_table.parquet')
    cent_raw = pd.read_parquet(V1103_MAIN / 'atom_centroids_48d_raw.parquet')
    cent_norm = pd.read_parquet(V1103_MAIN / 'atom_centroids_48d_normalized.parquet')
    qual = pd.read_parquet(V1103_MAIN / 'atom_quality.parquet')
    with open(V1103_MAIN / 'proposals.json') as f:
        prop = json.load(f)
    return pt, cent_raw, cent_norm, qual, prop


def build_centroid_matrix(cent_df: pd.DataFrame) -> tuple[np.ndarray, list[str], list[str]]:
    atoms = cent_df['atom'].tolist()
    axis_cols = [c for c in cent_df.columns if c not in ('atom', 'n_words')]
    M = cent_df[axis_cols].to_numpy(dtype=np.float64)
    return M, atoms, axis_cols


def build_couple_map(proposals: dict) -> dict[str, list[str]]:
    """B_COUPLE のみ抽出 (離散リンク)、双方向リンク"""
    cm = {}
    for p in proposals['proposals']:
        if p.get('pattern') == 'B_COUPLE':
            a, b = p['atom_a'], p['atom_b']
            cm.setdefault(a, []).append(b)
            cm.setdefault(b, []).append(a)
    return cm


def nearest_atoms(start_atom: str, M: np.ndarray, atoms: list[str], k: int) -> list[tuple[str, float]]:
    """start_atom を起点に cosine sim 上位 k atom を返す (自己除外)"""
    if start_atom not in atoms:
        return []
    idx = atoms.index(start_atom)
    sims = cosine_similarity(M[idx:idx+1], M)[0]
    # 自己除外
    sims[idx] = -np.inf
    top = np.argsort(sims)[-k:][::-1]
    return [(atoms[i], float(sims[i])) for i in top]


def quality_weight(atom: str, qual: pd.DataFrame) -> float:
    """品質重み = focus_rate_mean (高いほど信頼)"""
    row = qual[qual['atom'] == atom]
    if len(row) == 0:
        return 0.5  # 不在は中立扱い
    return float(row['focus_rate_mean'].iloc[0])


def is_monitor(atom: str, monitor_atoms: set) -> bool:
    return atom in monitor_atoms


def density_metrics(candidates: list[tuple[str, float]], M: np.ndarray,
                     atoms: list[str], qual: pd.DataFrame,
                     monitor_atoms: set) -> dict:
    """4 種密度指標を算出"""
    if not candidates:
        return dict(raw_density=np.nan, qweighted_density=np.nan,
                     const_adjusted_density=np.nan, n_candidates=0,
                     mean_pairwise_sim=np.nan, n_monitor=0)
    cand_atoms = [c[0] for c in candidates]
    cand_sims = [c[1] for c in candidates]
    # candidate centroids
    idxs = [atoms.index(a) for a in cand_atoms if a in atoms]
    if not idxs:
        return dict(raw_density=np.nan, qweighted_density=np.nan,
                     const_adjusted_density=np.nan, n_candidates=0,
                     mean_pairwise_sim=np.nan, n_monitor=0)
    sub = M[idxs]
    # raw 密度 = candidate centroid の平均ペア cosine sim (高=集中)
    if len(idxs) >= 2:
        pair = cosine_similarity(sub, sub)
        # 対角除く mean
        mask = ~np.eye(len(idxs), dtype=bool)
        raw_density = float(pair[mask].mean())
    else:
        raw_density = 1.0  # 単独は完全集中扱い
    # quality-weighted: focus_rate で重み
    weights = np.array([quality_weight(a, qual) for a in cand_atoms[:len(idxs)]])
    if weights.sum() > 0 and len(idxs) >= 2:
        # 重み付きペアsim
        w_pair = weights[:, None] * weights[None, :]
        np.fill_diagonal(w_pair, 0)
        qweighted = float((pair * w_pair).sum() / max(w_pair.sum(), 1e-9))
    else:
        qweighted = raw_density
    # constitution-adjusted: Monitor 該当を 0.5 で減点 (削除でなく重み軽減、GPT 監査 4)
    monitor_mask = np.array([0.5 if is_monitor(a, monitor_atoms) else 1.0 for a in cand_atoms[:len(idxs)]])
    n_mon = int((monitor_mask == 0.5).sum())
    if len(idxs) >= 2:
        m_pair = monitor_mask[:, None] * monitor_mask[None, :]
        np.fill_diagonal(m_pair, 0)
        const_adj = float((pair * m_pair).sum() / max(m_pair.sum(), 1e-9))
    else:
        const_adj = raw_density
    return dict(
        raw_density=raw_density,
        qweighted_density=qweighted,
        const_adjusted_density=const_adj,
        n_candidates=len(cand_atoms),
        mean_pairwise_sim=raw_density,
        n_monitor=n_mon,
    )


def main():
    t0 = time.time()
    print('=== v1103 Step C — 段 4-b/4-c/4-d ===')
    pt, cent_raw, cent_norm, qual, prop = load_inputs()
    print(f'primary_table: {len(pt)} cells, atom_centroids: {len(cent_raw)} atoms')

    M_raw, atoms_raw, _ = build_centroid_matrix(cent_raw)
    M_norm, atoms_norm, _ = build_centroid_matrix(cent_norm)
    couple_map = build_couple_map(prop)
    print(f'Couple links: {len(couple_map)} starting atoms')

    monitor_atoms = set()
    for p in prop['proposals']:
        if p.get('pattern') == 'MONITOR':
            monitor_atoms.add(p['atom_a'])
            monitor_atoms.add(p['atom_b'])
    print(f'Monitor atoms (caution flag、削除でなく重み軽減): {len(monitor_atoms)} = {sorted(monitor_atoms)[:5]}...')

    # 起点 = v1102 primary table の atom_top1_name (per cell)
    start_cells = pt[['receiver_bin', 'change_metric_type', 'n_records',
                       'atom_top1_name', 'conscious_frac']].copy()
    start_cells = start_cells.dropna(subset=['atom_top1_name'])
    print(f'starting cells (non-null atom_top1): {len(start_cells)}')

    rows_dist = []
    rows_density = []

    for _, cell in start_cells.iterrows():
        start_atom = cell['atom_top1_name']
        rbin = cell['receiver_bin']
        mt = cell['change_metric_type']

        # per (sim_basis=raw/norm) × per k
        for sim_basis, M, atoms in [('raw', M_raw, atoms_raw),
                                      ('norm', M_norm, atoms_norm)]:
            for k in K_VALUES:
                # 段 4-b: 連想先 = Couple ∪ 48 次元近傍 top-k
                couple_links = [(a, 1.0) for a in couple_map.get(start_atom, [])]
                near = nearest_atoms(start_atom, M, atoms, k=k)
                # 統合 (重複は max sim)
                combined = {}
                for a, s in couple_links + near:
                    if a not in combined or combined[a] < s:
                        combined[a] = s
                candidates = sorted(combined.items(), key=lambda x: -x[1])

                # 段 4-c: 4 種密度
                dm = density_metrics(candidates, M, atoms, qual, monitor_atoms)

                # 段 4-d: 候補確率分布 (sim を正規化、Aruism 対称性 100% 作らない)
                if candidates:
                    sims_arr = np.array([s for _, s in candidates])
                    # softmax with temperature (100% を作らない、最大値はsmaxで近づくが厳密 1 にならない)
                    exp_s = np.exp(sims_arr / 0.1)  # temperature 0.1
                    probs = exp_s / exp_s.sum()
                    for (atom, sim), prob in zip(candidates, probs):
                        rows_dist.append({
                            'receiver_bin': rbin,
                            'change_metric_type': mt,
                            'start_atom': start_atom,
                            'sim_basis': sim_basis,
                            'k': k,
                            'candidate_atom': atom,
                            'cosine_sim': sim,
                            'response_prob': float(prob),
                            'is_couple_link': atom in couple_map.get(start_atom, []),
                            'is_monitor': atom in monitor_atoms,
                            'quality_focus_rate': quality_weight(atom, qual),
                            'n_records_source_cell': int(cell['n_records']),
                        })

                rows_density.append({
                    'receiver_bin': rbin,
                    'change_metric_type': mt,
                    'start_atom': start_atom,
                    'sim_basis': sim_basis,
                    'k': k,
                    'n_records_source_cell': int(cell['n_records']),
                    'conscious_frac': float(cell['conscious_frac']),
                    **dm,
                })

    df_dist = pd.DataFrame(rows_dist)
    df_density = pd.DataFrame(rows_density)
    df_dist.to_parquet(V1103_MAIN / 'response_atom_distribution.parquet', index=False)
    df_density.to_parquet(V1103_MAIN / 'density_summary.parquet', index=False)

    elapsed = time.time() - t0
    print(f'\n=== 出力 (elapsed {elapsed:.1f}s) ===')
    print(f'response_atom_distribution: {len(df_dist):,} rows')
    print(f'density_summary: {len(df_density):,} rows')
    print(f'\n=== Aruism 対称性確認 (response_prob 最大値、100% 未満であること) ===')
    print(f'max prob: {df_dist["response_prob"].max():.4f}')
    print(f'n rows prob >= 0.999: {(df_dist["response_prob"] >= 0.999).sum()}')
    print(f'\n=== 4 種密度サマリ (24 cells) ===')
    print(df_density.groupby(['sim_basis', 'k'])[['raw_density','qweighted_density','const_adjusted_density','n_candidates','n_monitor']].mean().round(4).to_string())


if __name__ == '__main__':
    main()
