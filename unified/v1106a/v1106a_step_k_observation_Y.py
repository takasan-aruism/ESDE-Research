#!/usr/bin/env python3
"""v1106a Step K — 案 Y 実装: 48 axes 全部経由 cosine_sim 接続

Code A 自己反省 (2026-05-26): Step A 認識確認で案 Y 計算量を「50 倍 (4-8 時間)」と
過剰見積もりして除外推奨してしまった。実際は numpy 並列で数分以内、再評価により
案 Y こそが LLM 1 億トークン 48 axes 判定の本来の活用方法。Taka 判断「案 Y 実装に
進む」で本 Step 実装。

接続式 (案 Y):
  各 atom について 48 axes centroid を持つ (v1103 atom_centroids_48d_raw)
  各 word について 48 axes raw_scores を持つ (mapper_output)

  cos_sim(atom, word) = cosine_similarity(atom_centroid_48d, word_raw_scores_48d)

  各 event で:
    score(word_j) = Σ_i [p_s7(atom_i) × cos_sim(atom_i, word_j)]
    p_word(word_j) = score(word_j) / Σ_k score(word_k)

  (cos_sim は -1〜1、正規化後 0-1 確率分布)

入力 (read-only):
  - unified/v1105a/outputs/main/trial_step4_distributions.parquet (s7 PC events)
  - unified/v1103/outputs/main/atom_centroids_48d_raw.parquet (325 atom × 48 axes)
  - language/lexicon/data/mapper_output/*_a1.jsonl (atom × word × 48 axes raw_scores)
  - language/atoms/esde_dictionary.json (48 axes 順序確認)

出力:
  - unified/v1106a/outputs/main/observation_Y_word_distributions.parquet
  - unified/v1106a/outputs/main/observation_Y_labels.parquet
  - unified/v1106a/outputs/main/observation_Y_L41L42_comparison.parquet (vs 案 X / Z-1)
"""
from __future__ import annotations
import json, os, time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

REPO = Path('/home/takasan/esde/ESDE-Research')
V1103_MAIN = REPO / 'unified/v1103/outputs/main'
V1105A_MAIN = REPO / 'unified/v1105a/outputs/main'
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'
MAPPER_DIR = REPO / 'language/lexicon/data/mapper_output'

MAX_PROB_THRESH = 0.999

# 48 axes 順序 (esde_dictionary.json 由来、atom_centroids_48d と一致確認済)
AXES_ORDER = None
def get_axes_order():
    global AXES_ORDER
    if AXES_ORDER is None:
        d = json.load(open(REPO/'language/atoms/esde_dictionary.json'))
        AXES_ORDER = []
        for axis_id, axis_def in d['axes'].items():
            for level in axis_def['levels']:
                AXES_ORDER.append(f'{axis_id}.{level}')
    return AXES_ORDER


def cosine_sim_vec(v1, v2):
    """v1: (48,) v2: (48,) → scalar"""
    n1 = np.linalg.norm(v1); n2 = np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (n1 * n2))


def cosine_sim_batch(v_target, V_matrix):
    """v_target: (48,), V_matrix: (N, 48) → (N,) cosine similarities"""
    n_t = np.linalg.norm(v_target)
    norms_v = np.linalg.norm(V_matrix, axis=1)
    if n_t == 0:
        return np.zeros(len(V_matrix))
    dots = V_matrix @ v_target
    out = dots / (n_t * np.where(norms_v > 0, norms_v, 1.0))
    out = np.where(norms_v > 0, out, 0.0)
    return out


def assign_label(n_after: int, max_prob: float, entropy: float) -> str:
    if n_after == 0:
        return 'word_candidate_empty'
    if max_prob >= MAX_PROB_THRESH:
        return 'word_distribution_degenerate'
    if max_prob < MAX_PROB_THRESH and entropy > 0:
        return 'word_distribution_valid'
    return 'word_candidate_empty'


def main():
    V1106A_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106a Step K 案 Y 実装: 48 axes cosine_sim 接続 ===')
    t0 = time.time()

    axes = get_axes_order()
    print(f'48 axes 順序確定: {len(axes)} axes')

    # (1) atom_centroids_48d_raw を読み込み
    print('\n[1] atom_centroids_48d_raw 読み込み')
    ac = pd.read_parquet(V1103_MAIN / 'atom_centroids_48d_raw.parquet')
    atom_to_centroid = {}
    for _, row in ac.iterrows():
        atom = row['atom']
        vec = np.array([row[ax] for ax in axes], dtype=np.float64)
        atom_to_centroid[atom] = vec
    print(f'  atoms: {len(atom_to_centroid)}, vec dim: {len(axes)}')

    # (2) mapper_output から (atom, word, 48d vec) 抽出
    print('\n[2] mapper_output 抽出 + per (atom, word) cos_sim 事前計算')
    atom_to_word_sim = {}  # atom → list of (word, cos_sim)
    n_entries = 0
    n_atoms_processed = 0
    for fp in sorted(MAPPER_DIR.glob('*_a1.jsonl')):
        atom = fp.stem.replace('_a1', '').replace('_', '.', 1)
        if atom not in atom_to_centroid:
            continue
        centroid = atom_to_centroid[atom]
        word_vecs = []
        word_names = []
        with open(fp) as f:
            for line in f:
                d = json.loads(line)
                if d.get('status') != 'OK':
                    continue
                rs = d.get('raw_scores')
                if not isinstance(rs, dict):
                    continue
                vec = np.array([rs.get(ax, 0.0) for ax in axes], dtype=np.float64)
                word_vecs.append(vec)
                word_names.append(d['word'])
                n_entries += 1
        if not word_vecs:
            continue
        V = np.stack(word_vecs)  # (N, 48)
        sims = cosine_sim_batch(centroid, V)
        atom_to_word_sim[atom] = list(zip(word_names, sims.tolist()))
        n_atoms_processed += 1
    print(f'  atoms processed: {n_atoms_processed}')
    print(f'  total (atom, word) entries: {n_entries:,}')
    cs_all = np.array([s for ws in atom_to_word_sim.values() for _, s in ws])
    print(f'  cos_sim range: min={cs_all.min():.4f}, max={cs_all.max():.4f}, '
          f'mean={cs_all.mean():.4f}, median={np.median(cs_all):.4f}')
    print(f'  cos_sim distribution: '
          f'>=0.99 tied = {(cs_all >= 0.99).mean()*100:.2f}%, '
          f'>=0.95 = {(cs_all >= 0.95).mean()*100:.2f}%')

    # (3) v1105a 7 系列 PC events 読み込み
    print('\n[3] v1105a 7 系列 PC events 読み込み')
    dist = pd.read_parquet(V1105A_MAIN / 'trial_step4_distributions.parquet')
    pc = dist[dist['structural_label'] == 'distribution_valid'].copy()
    print(f'  PC rows: {len(pc):,}')

    # (4) per (event, series) で 案 Y 接続式適用
    print('\n[4] 案 Y 接続式適用')
    out_rows = []
    label_rows = []
    align_rows = []
    grouped = pc.groupby(['seed', 'event_id', 'series_id'])
    n_grp = len(grouped)
    cnt = 0
    for (sd, eid, sid), grp in grouped:
        cnt += 1
        if cnt % 5000 == 0:
            print(f'  processed {cnt:,}/{n_grp:,}, elapsed {time.time()-t0:.1f}s')

        input_atom = grp['input_atom'].iloc[0]
        cand_dict = dict(zip(grp['candidate_atom'], grp['probability']))

        # score(word) = Σ p_s7(atom) × cos_sim(atom, word)
        # ただし word は atom ごとに異なる、union を取る
        word_score = defaultdict(float)
        for atom, p in cand_dict.items():
            if atom not in atom_to_word_sim:
                continue
            for word, sim in atom_to_word_sim[atom]:
                # 負の sim は 0 に clip (確率正規化のため)
                word_score[word] += p * max(sim, 0.0)
        total = sum(word_score.values())
        if total <= 0:
            label_rows.append({
                'seed': sd, 'event_id': eid, 'series_id': sid,
                'input_atom': input_atom, 'n_words_after': 0,
                'word_max_prob': np.nan, 'word_entropy': np.nan,
                'structural_label': 'word_candidate_empty',
            })
            continue

        word_probs = {w: s / total for w, s in word_score.items()}
        probs_arr = np.array(list(word_probs.values()))
        max_p = float(probs_arr.max())
        p_nz = probs_arr[probs_arr > 0]
        ent = float(-np.sum(p_nz * np.log(p_nz))) if len(p_nz) > 0 else 0.0
        label = assign_label(len(word_probs), max_p, ent)

        label_rows.append({
            'seed': sd, 'event_id': eid, 'series_id': sid,
            'input_atom': input_atom,
            'n_words_after': len(word_probs),
            'word_max_prob': max_p,
            'word_entropy': ent,
            'structural_label': label,
        })

        # alignment for #L41 解消確認:
        # top1 atom (s7 で確率最大) が指す top1 word (cos_sim 最大) の cos_sim 値
        grp_sorted = grp.sort_values('probability', ascending=False)
        top1_atom = grp_sorted.iloc[0]['candidate_atom']
        top5_atoms = grp_sorted.head(5)['candidate_atom'].tolist()
        top5_probs = grp_sorted.head(5)['probability'].tolist()

        if top1_atom in atom_to_word_sim and atom_to_word_sim[top1_atom]:
            sims = [s for _, s in atom_to_word_sim[top1_atom]]
            top1_atom_top1_cos = max(sims)
            top1_atom_mean_cos = float(np.mean(sims))
            top1_atom_n_word = len(sims)
        else:
            top1_atom_top1_cos = np.nan
            top1_atom_mean_cos = np.nan
            top1_atom_n_word = 0

        top5_top1_cos = []
        for a in top5_atoms:
            if a in atom_to_word_sim and atom_to_word_sim[a]:
                top5_top1_cos.append(max(s for _, s in atom_to_word_sim[a]))
        top5_top1_cos_mean = float(np.mean(top5_top1_cos)) if top5_top1_cos else np.nan

        rank_corr = np.nan
        if len(top5_atoms) >= 3 and len(top5_top1_cos) == len(top5_atoms):
            if len(set(top5_top1_cos)) > 1 and len(set(top5_probs)) > 1:
                rho, _ = spearmanr(top5_probs, top5_top1_cos)
                if not np.isnan(rho):
                    rank_corr = float(rho)

        align_rows.append({
            'seed': sd, 'event_id': eid, 'series_id': sid,
            'top1_atom': top1_atom,
            'top1_atom_top1_cos_sim': top1_atom_top1_cos,
            'top1_atom_mean_cos_sim': top1_atom_mean_cos,
            'top1_atom_n_word_links': top1_atom_n_word,
            'top5_atom_top1_cos_sim_mean': top5_top1_cos_mean,
            'atom_word_rank_correlation_Y': rank_corr,
        })

        for word, p in word_probs.items():
            out_rows.append({
                'seed': sd, 'event_id': eid, 'series_id': sid,
                'input_atom': input_atom,
                'candidate_word': word,
                'probability': p,
            })

    df_dist = pd.DataFrame(out_rows).sort_values(
        ['seed', 'event_id', 'series_id', 'candidate_word']).reset_index(drop=True)
    df_labels = pd.DataFrame(label_rows).sort_values(
        ['seed', 'event_id', 'series_id']).reset_index(drop=True)
    df_align = pd.DataFrame(align_rows).sort_values(
        ['seed', 'event_id', 'series_id']).reset_index(drop=True)

    out_d = V1106A_MAIN / 'observation_Y_word_distributions.parquet'
    df_dist.to_parquet(out_d, index=False)
    out_l = V1106A_MAIN / 'observation_Y_labels.parquet'
    df_labels.to_parquet(out_l, index=False)
    out_a = V1106A_MAIN / 'observation_Y_alignment.parquet'
    df_align.to_parquet(out_a, index=False)
    print(f'\nwrote {out_d.name} ({len(df_dist):,} rows)')
    print(f'wrote {out_l.name} ({len(df_labels):,} rows)')
    print(f'wrote {out_a.name} ({len(df_align):,} rows)')

    print(f'\n=== Step K 完了、elapsed {time.time()-t0:.1f}s ===')

    # --- サマリ ---
    print('\n--- 案 Y 構造ラベル件数 ---')
    print(df_labels.groupby('structural_label').size().to_string())

    print('\n--- 案 Y 系列別 (valid のみ) ---')
    v = df_labels[df_labels['structural_label'] == 'word_distribution_valid']
    if len(v) > 0:
        s = v.groupby('series_id').agg(
            n_events=('event_id', 'count'),
            n_words_mean=('n_words_after', 'mean'),
            n_words_max=('n_words_after', 'max'),
            max_prob_mean=('word_max_prob', 'mean'),
            max_prob_median=('word_max_prob', 'median'),
            entropy_mean=('word_entropy', 'mean'),
        ).round(4)
        print(s.to_string())

    print('\n--- 案 Y alignment 系列別 (#L41 解消再評価) ---')
    a_summary = df_align.groupby('series_id').agg(
        top1_cos_mean=('top1_atom_top1_cos_sim', 'mean'),
        top1_cos_max=('top1_atom_top1_cos_sim', 'max'),
        top1_tied_99=('top1_atom_top1_cos_sim', lambda x: (x >= 0.99).mean()),
        rc_valid_rate=('atom_word_rank_correlation_Y',
                        lambda x: (~x.isna()).mean()),
        rc_mean=('atom_word_rank_correlation_Y', 'mean'),
        rc_positive_rate=('atom_word_rank_correlation_Y',
                           lambda x: (x > 0).mean()),
    ).round(4)
    print(a_summary.to_string())

    # 案 X / 案 Z-1 と直接対比
    print('\n--- 案 X / 案 Z-1 / 案 Y 直接対比 (s1 sample) ---')
    if len(df_align) > 0:
        s1 = df_align[df_align['series_id'] == 's1_raw_density_raw']
        print(f'  案 Y (cos_sim 48 axes):')
        print(f'    top1_cos mean: {s1["top1_atom_top1_cos_sim"].mean():.4f}')
        print(f'    top1_tied (>=0.99): {(s1["top1_atom_top1_cos_sim"] >= 0.99).mean()*100:.2f}%')
        print(f'    rc_valid_rate: {(~s1["atom_word_rank_correlation_Y"].isna()).mean():.4f}')
        rc_valid = s1["atom_word_rank_correlation_Y"].dropna()
        if len(rc_valid) > 0:
            print(f'    rc_mean: {rc_valid.mean():.4f}')
            print(f'    rc_positive_rate: {(rc_valid > 0).mean():.4f}')

    # 案 X/Z-1 比較表保存
    comparison_rows = []
    for sid in df_labels['series_id'].unique():
        v_sid = v[v['series_id'] == sid]
        a_sid = df_align[df_align['series_id'] == sid]
        if len(v_sid) == 0 or len(a_sid) == 0:
            continue
        rc_valid = a_sid['atom_word_rank_correlation_Y'].dropna()
        comparison_rows.append({
            'formula': 'Y',
            'series_id': sid,
            'n_events': len(v_sid),
            'n_words_mean': float(v_sid['n_words_after'].mean()),
            'max_prob_mean': float(v_sid['word_max_prob'].mean()),
            'entropy_mean': float(v_sid['word_entropy'].mean()),
            'top1_cos_mean': float(a_sid['top1_atom_top1_cos_sim'].mean()),
            'top1_tied_99_rate': float((a_sid['top1_atom_top1_cos_sim'] >= 0.99).mean()),
            'rc_valid_rate': float((~a_sid['atom_word_rank_correlation_Y'].isna()).mean()),
            'rc_mean': float(rc_valid.mean()) if len(rc_valid) > 0 else np.nan,
            'rc_positive_rate': float((rc_valid > 0).mean()) if len(rc_valid) > 0 else np.nan,
        })
    comp_df = pd.DataFrame(comparison_rows)
    out_c = V1106A_MAIN / 'observation_Y_L41L42_comparison.parquet'
    comp_df.to_parquet(out_c, index=False)
    print(f'\nwrote {out_c.name} ({len(comp_df)} rows)')


if __name__ == '__main__':
    main()
