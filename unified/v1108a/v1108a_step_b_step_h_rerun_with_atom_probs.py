#!/usr/bin/env python3
"""v1108a Step B — Step H 自己対話を atom_probs 記録版で再実行

Code A 案 A (Taka 承認 2026-05-30): Step H と同パラメータで自己対話を再実行し、
各 turn で atom_probs (top-10 atom + 確率) を記録する。

物理層 frozen 規律厳密維持:
- v1106b は read-only (元ファイル変更なし)
- 新規ファイルは unified/v1108a/ 配下のみ
- 入力データ (v1106b env_check_selected_cids 等) は read-only

Step H と同じ設定:
- 681 CID × 40 turn × top-3 sampling (rng_seed=42)
- 同じ atom_to_centroid / atom_to_word_sims / sim_df / cid_vecs

追加:
- 各 turn で atom_probs (atom_top1〜top10、prob_top1〜top10) を記録
- cos_sim score 上位 10 atom + 確率

出力:
- unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet
- unified/v1108a/outputs/main/step_b_summary.parquet
"""
from __future__ import annotations
import json, time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V1103_MAIN = REPO / 'unified/v1103/outputs/main'
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V105_SUB = REPO / 'developmental/v105/diag_v105_main/subjects'
V1106B_MAIN = REPO / 'unified/v1106b/outputs/main'
V1108A_MAIN = REPO / 'unified/v1108a/outputs/main'
MAPPER_DIR = REPO / 'language/lexicon/data/mapper_output'

N_TURN = 40
ATOM_TOPK = 10
WORD_TOPK_FOR_LOOP = 15
CID_TOPK = 5
SAMPLING_K = 3
STUCK_K = 3
OSCILLATION_W = 5
OSCILLATION_UNIQUE_MAX = 2
RNG_SEED = 42


def get_axes():
    am = json.load(open(V106_MAIN / 'axes_metadata.json'))
    return [f'{ax["name"]}.{lvl}' for ax in am['axes_order'] for lvl in ax['level_names']]


def load_resources():
    axes = get_axes()
    print('[1] リソース読み込み')
    t0 = time.time()
    ac = pd.read_parquet(V1103_MAIN / 'atom_centroids_48d_raw.parquet')
    atom_to_centroid = {row['atom']: np.array([row[ax] for ax in axes], dtype=np.float64)
                         for _, row in ac.iterrows()}
    atom_to_word_sims = {}
    word_to_atom_vec = defaultdict(dict)
    for fp in sorted(MAPPER_DIR.glob('*_a1.jsonl')):
        atom = fp.stem.replace('_a1', '').replace('_', '.', 1)
        if atom not in atom_to_centroid:
            continue
        centroid = atom_to_centroid[atom]
        cn = np.linalg.norm(centroid)
        if cn == 0:
            continue
        wlist = []
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
                wlist.append((r['word'], sim, vec))
                word_to_atom_vec[r['word']][atom] = vec
        atom_to_word_sims[atom] = wlist
    print(f'  loaded {len(atom_to_centroid)} atoms, {len(word_to_atom_vec):,} words '
          f'({time.time()-t0:.1f}s)')
    return axes, atom_to_centroid, atom_to_word_sims, dict(word_to_atom_vec)


def load_seed_cid_vecs(seed):
    fp = V106_MAIN / f'cid_structure_profile_seed{seed}.csv'
    df = pd.read_csv(fp)
    return {int(r['cid']): r[[f'dim_{i}' for i in range(48)]].values.astype(np.float64)
            for _, r in df.iterrows()}


def load_seed_cid_atom_sim(seed):
    return pd.read_parquet(V106_MAIN / f'cid_atom_sim_matrix_seed{seed}.parquet')


def load_seed_props(seed):
    fp = V105_SUB / f'per_subject_seed{seed}.csv'
    df = pd.read_csv(fp, usecols=['cognitive_id', 'final_state',
                                    'last_familiarity_max', 'n_alphas_currently'])
    return df.set_index('cognitive_id')


def cid_to_word_top(cid_vec, atom_to_centroid, atom_to_word_sims, k_atom, k_word):
    cn = np.linalg.norm(cid_vec)
    sims = {}
    for atom, c in atom_to_centroid.items():
        an = np.linalg.norm(c)
        if an > 0 and cn > 0:
            sims[atom] = float(np.dot(cid_vec, c) / (cn * an))
        else:
            sims[atom] = 0.0
    sorted_a = sorted(sims.items(), key=lambda x: -x[1])[:k_atom]
    raw = [max(s, 0.0) for _, s in sorted_a]
    total = sum(raw)
    if total <= 0:
        atom_probs = [(a, 1.0/len(sorted_a)) for a, _ in sorted_a]
    else:
        atom_probs = [(a, r/total) for (a, _), r in zip(sorted_a, raw)]
    word_score = defaultdict(float)
    for atom, p in atom_probs:
        for word, sim, _ in atom_to_word_sims.get(atom, []):
            word_score[word] += p * max(sim, 0.0)
    total_w = sum(word_score.values())
    if total_w <= 0:
        return [], atom_probs
    words = sorted(word_score.items(), key=lambda x: -x[1])[:k_word]
    return [(w, p/total_w) for w, p in words], atom_probs


def words_to_atoms(words, word_to_atom_vec):
    atom_score = defaultdict(float)
    for w in words:
        if w not in word_to_atom_vec:
            continue
        for atom, vec in word_to_atom_vec[w].items():
            atom_score[atom] += float(np.linalg.norm(vec))
    total = sum(atom_score.values())
    if total <= 0:
        return {}
    return {a: s/total for a, s in atom_score.items()}


def atom_to_cid_topK(atom_probs, sim_df, k):
    scores = np.zeros(len(sim_df))
    for atom, p in atom_probs.items():
        if atom in sim_df.columns:
            sims = sim_df[atom].values.astype(np.float64)
            scores += p * np.clip(sims, 0, None)
    cids = sim_df['cid'].values
    order = np.argsort(-scores)
    return [(int(cids[i]), float(scores[i])) for i in order[:k]]


def self_dialogue_with_atom_probs(seed, start_cid, n_turn, atom_to_centroid,
                                     atom_to_word_sims, word_to_atom_vec, sim_df,
                                     props_df, cid_vecs, rng):
    """top-3 sampling 自己対話、atom_probs (top-10) 記録版"""
    history = []
    current_cid = start_cid
    cid_track = []
    stuck_at = None
    oscillation_at = None
    same_cid_run = 0
    prev_cid = None
    for t in range(n_turn + 1):
        if current_cid not in cid_vecs:
            break
        cid_vec = cid_vecs[current_cid]
        prop = props_df.loc[current_cid] if current_cid in props_df.index else None
        if prop is not None:
            fam = prop.get('last_familiarity_max')
            n_alphas = prop.get('n_alphas_currently')
            final_state = prop.get('final_state')
            if hasattr(fam, 'item'):
                fam = fam.item() if not pd.isna(fam) else None
            if hasattr(n_alphas, 'item'):
                n_alphas = n_alphas.item() if not pd.isna(n_alphas) else None
        else:
            fam = n_alphas = final_state = None
        words_top, atoms_top = cid_to_word_top(cid_vec, atom_to_centroid,
                                                  atom_to_word_sims,
                                                  ATOM_TOPK, WORD_TOPK_FOR_LOOP)
        top_word = words_top[0][0] if words_top else None

        record = {
            'seed': seed, 'start_cid': start_cid, 'turn': t,
            'cid': current_cid,
            'last_familiarity_max': fam,
            'n_alphas_currently': n_alphas,
            'final_state': final_state,
            'top_word': top_word,
        }
        # atom_probs top-10 を 20 列で記録
        for rank in range(ATOM_TOPK):
            if rank < len(atoms_top):
                record[f'atom_top{rank+1}'] = atoms_top[rank][0]
                record[f'prob_top{rank+1}'] = float(atoms_top[rank][1])
            else:
                record[f'atom_top{rank+1}'] = None
                record[f'prob_top{rank+1}'] = 0.0
        history.append(record)

        if prev_cid == current_cid:
            same_cid_run += 1
        else:
            same_cid_run = 1
        if same_cid_run >= STUCK_K and stuck_at is None:
            stuck_at = t
        cid_track.append(current_cid)
        if len(cid_track) >= OSCILLATION_W:
            recent = cid_track[-OSCILLATION_W:]
            if len(set(recent)) <= OSCILLATION_UNIQUE_MAX and oscillation_at is None:
                oscillation_at = t
        prev_cid = current_cid
        if t >= n_turn or not words_top:
            break
        top_words = [w for w, _ in words_top]
        atom_probs2 = words_to_atoms(top_words, word_to_atom_vec)
        if not atom_probs2:
            break
        cid_candidates = atom_to_cid_topK(atom_probs2, sim_df, k=CID_TOPK)
        if not cid_candidates:
            break
        top_k = cid_candidates[:SAMPLING_K]
        scores = np.array([s for _, s in top_k])
        if scores.sum() > 0:
            probs = scores / scores.sum()
        else:
            probs = np.ones(len(top_k)) / len(top_k)
        idx = rng.choice(len(top_k), p=probs)
        next_cid, _ = top_k[idx]
        current_cid = next_cid
    for h in history:
        h['stuck_at_turn'] = stuck_at
        h['oscillation_at_turn'] = oscillation_at
    return history


def main():
    V1108A_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1108a Step B — Step H 再実行 (atom_probs 記録版) ===\n')
    t0 = time.time()

    axes, atom_to_centroid, atom_to_word_sims, word_to_atom_vec = load_resources()

    sel = pd.read_parquet(V1106B_MAIN / 'env_check_selected_cids.parquet')
    print(f'\n[2] 選定 CID (v1106b 案 E): {len(sel)} ({sel["seed"].nunique()} seeds)')

    print(f'\n[3] 自己対話 sampling (top-{SAMPLING_K}, N={N_TURN}, rng_seed={RNG_SEED})')
    rng = np.random.default_rng(RNG_SEED)
    all_hist = []
    for sd in range(24):
        seed_sel = sel[sel['seed'] == sd]
        if len(seed_sel) == 0:
            continue
        ts = time.time()
        sim_df = load_seed_cid_atom_sim(sd)
        cid_vecs = load_seed_cid_vecs(sd)
        props_df = load_seed_props(sd)
        for _, row in seed_sel.iterrows():
            start_cid = int(row['cid'])
            hist = self_dialogue_with_atom_probs(
                sd, start_cid, N_TURN,
                atom_to_centroid, atom_to_word_sims, word_to_atom_vec,
                sim_df, props_df, cid_vecs, rng)
            for h in hist:
                h['start_final_state'] = row['final_state']
                h['start_fam_bin'] = row['fam_bin']
            all_hist.extend(hist)
        print(f'  seed={sd} done ({len(seed_sel)} CID, {time.time()-ts:.1f}s)')

    hist_df = pd.DataFrame(all_hist)
    out1 = V1108A_MAIN / 'self_dialogue_with_atom_probs.parquet'
    hist_df.to_parquet(out1, index=False)
    print(f'\n  wrote {out1.name} ({len(hist_df):,} rows)')

    # 整合性確認: v1106b Step H 出力と top_atom / familiarity が一致するか
    print('\n[4] v1106b Step H との整合性確認 (top_atom が atom_top1 と一致)')
    v1106b_h = pd.read_parquet(V1106B_MAIN / 'observation_4_self_dialogue.parquet')
    merged = hist_df.merge(
        v1106b_h[['seed', 'start_cid', 'turn', 'top_atom', 'last_familiarity_max']],
        on=['seed', 'start_cid', 'turn'],
        suffixes=('_new', '_v1106b')
    )
    match_atom = (merged['atom_top1'] == merged['top_atom']).sum()
    match_fam = (merged['last_familiarity_max_new'] == merged['last_familiarity_max_v1106b']).sum()
    total = len(merged)
    print(f'  matched rows: {total:,}')
    print(f'  atom_top1 == v1106b top_atom: {match_atom:,}/{total:,} ({match_atom/total*100:.2f}%)')
    print(f'  familiarity match: {match_fam:,}/{total:,} ({match_fam/total*100:.2f}%)')

    sum_df = pd.DataFrame([{
        'n_rows': len(hist_df),
        'n_events': hist_df[['seed', 'start_cid']].drop_duplicates().shape[0],
        'n_turns_per_event_mean': float(hist_df.groupby(['seed', 'start_cid']).size().mean()),
        'integrity_atom_top1_match_rate': float(match_atom / total),
        'integrity_familiarity_match_rate': float(match_fam / total),
        'elapsed_sec': round(time.time() - t0, 2),
    }])
    out2 = V1108A_MAIN / 'step_b_summary.parquet'
    sum_df.to_parquet(out2, index=False)

    print(f'\n=== Step B 完了、elapsed {time.time()-t0:.1f}s ===')


if __name__ == '__main__':
    main()
