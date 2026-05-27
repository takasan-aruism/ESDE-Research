#!/usr/bin/env python3
"""v1106b Step G — 観察 4 smoke: ESDE 自己対話 top-3 sampling (1 seed)

Step F.5 実装方針通り:
- top-3 sampling (top-5 候補から上位 3 を確率重みで選択)
- N=40 turn (Step C/D の 15 turn より長く、収束パターン捕捉)
- Code A 介在なし保証 (人間 input/動的判定なし、rng シード固定)
- 停止条件: 中断せず N turn 完走 + stuck/oscillation ラベル記録

smoke seed: 0 (Step C と同)
対象 CID: 33 (env_check_selected_cids の seed=0)

入力: Step C/D と同 (frozen)
出力:
- unified/v1106b/outputs/main/observation_4_self_dialogue_smoke.parquet (全 turn 履歴)
- unified/v1106b/outputs/main/observation_4_smoke_compare_top1.parquet (top-1 vs top-3 sampling 比較)
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
MAPPER_DIR = REPO / 'language/lexicon/data/mapper_output'

N_TURN = 40
ATOM_TOPK = 10
WORD_TOPK_FOR_LOOP = 15
CID_TOPK = 5     # cid_candidates 上位 5 取得
SAMPLING_K = 3   # top-3 sampling
STUCK_K = 3
OSCILLATION_W = 5
OSCILLATION_UNIQUE_MAX = 2
SMOKE_SEED = 0
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
                                    'last_familiarity_max', 'n_alphas_currently',
                                    'current_stability', 'current_social'])
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
    """atom 確率 → 同 seed cid 候補 top-K (sampling 用)"""
    scores = np.zeros(len(sim_df))
    for atom, p in atom_probs.items():
        if atom in sim_df.columns:
            sims = sim_df[atom].values.astype(np.float64)
            scores += p * np.clip(sims, 0, None)
    cids = sim_df['cid'].values
    order = np.argsort(-scores)
    return [(int(cids[i]), float(scores[i])) for i in order[:k]]


def self_dialogue_sampling(seed, start_cid, n_turn, atom_to_centroid,
                              atom_to_word_sims, word_to_atom_vec, sim_df,
                              props_df, cid_vecs, rng):
    """top-3 sampling 自己対話"""
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
        top_atom = atoms_top[0][0] if atoms_top else None

        history.append({
            'seed': seed, 'start_cid': start_cid, 'turn': t,
            'cid': current_cid,
            'last_familiarity_max': fam,
            'n_alphas_currently': n_alphas,
            'final_state': final_state,
            'top_atom': top_atom,
            'top_word': top_word,
        })

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

        # top-3 sampling
        top3 = cid_candidates[:SAMPLING_K]
        scores = np.array([s for _, s in top3])
        if scores.sum() > 0:
            probs = scores / scores.sum()
        else:
            probs = np.ones(len(top3)) / len(top3)
        idx = rng.choice(len(top3), p=probs)
        next_cid, _ = top3[idx]
        current_cid = next_cid

    for h in history:
        h['stuck_at_turn'] = stuck_at
        h['oscillation_at_turn'] = oscillation_at

    return history


def main():
    V1106B_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106b Step G — 観察 4 smoke (top-3 sampling、seed=0、N=40) ===\n')
    t0 = time.time()

    axes, atom_to_centroid, atom_to_word_sims, word_to_atom_vec = load_resources()

    sel = pd.read_parquet(V1106B_MAIN / 'env_check_selected_cids.parquet')
    smoke_cids = sel[sel['seed'] == SMOKE_SEED]
    print(f'\n[2] smoke seed={SMOKE_SEED} 選定 CID: {len(smoke_cids)} 個')

    print(f'\n[3] seed={SMOKE_SEED} リソース読み込み')
    sim_df = load_seed_cid_atom_sim(SMOKE_SEED)
    cid_vecs = load_seed_cid_vecs(SMOKE_SEED)
    props_df = load_seed_props(SMOKE_SEED)

    print(f'\n[4] 自己対話 sampling (top-3、N={N_TURN} turn、rng_seed={RNG_SEED})')
    rng = np.random.default_rng(RNG_SEED)
    all_hist = []
    for i, (_, row) in enumerate(smoke_cids.iterrows()):
        start_cid = int(row['cid'])
        hist = self_dialogue_sampling(SMOKE_SEED, start_cid, N_TURN,
                                         atom_to_centroid, atom_to_word_sims,
                                         word_to_atom_vec,
                                         sim_df, props_df, cid_vecs, rng)
        for h in hist:
            h['start_final_state'] = row['final_state']
            h['start_fam_bin'] = row['fam_bin']
        all_hist.extend(hist)
        if (i+1) % 5 == 0:
            print(f'  done {i+1}/{len(smoke_cids)}, elapsed {time.time()-t0:.1f}s')

    hist_df = pd.DataFrame(all_hist)
    out1 = V1106B_MAIN / 'observation_4_self_dialogue_smoke.parquet'
    hist_df.to_parquet(out1, index=False)
    print(f'\n  wrote {out1.name} ({len(hist_df)} rows)')

    # 集計
    print(f'\n=== Step G smoke 完了、elapsed {time.time()-t0:.1f}s ===\n')

    # per start_cid 集計
    summary = []
    for (sd, start_cid), grp in hist_df.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn')
        fam_vals = [f for f in grp_sorted['last_familiarity_max'].tolist() if f is not None]
        cids = grp_sorted['cid'].tolist()
        start_fam = fam_vals[0] if fam_vals else None
        end_fam = fam_vals[-1] if fam_vals else None
        min_fam = min(fam_vals) if fam_vals else None
        rollback = (start_fam is not None and min_fam is not None
                     and min_fam < start_fam * 0.8)
        summary.append({
            'seed': sd, 'start_cid': start_cid,
            'start_familiarity': start_fam,
            'end_familiarity': end_fam,
            'min_familiarity': min_fam,
            'rollback_20pct': rollback,
            'n_unique_cid': len(set(cids)),
            'n_turn': len(cids),
            'stuck_at_turn': grp_sorted['stuck_at_turn'].iloc[0],
            'oscillation_at_turn': grp_sorted['oscillation_at_turn'].iloc[0],
            'start_final_state': grp_sorted['start_final_state'].iloc[0],
        })
    summary_df = pd.DataFrame(summary)
    valid_fam = summary_df.dropna(subset=['start_familiarity', 'min_familiarity'])

    print('--- 観察 4 sampling smoke 集計 (seed=0、33 CID、N=40) ---')
    print(f'  n_start_cids: {len(summary_df)}')
    print(f'  rollback (20%+): {valid_fam["rollback_20pct"].sum()}/{len(valid_fam)} '
          f'({valid_fam["rollback_20pct"].mean()*100:.1f}%)')
    print(f'  start_fam mean: {valid_fam["start_familiarity"].mean():.2f}, '
          f'end_fam mean: {valid_fam["end_familiarity"].mean():.2f}, '
          f'min_fam mean: {valid_fam["min_familiarity"].mean():.2f}')
    print(f'  stuck 検出: {summary_df["stuck_at_turn"].notna().sum()}/{len(summary_df)} '
          f'({summary_df["stuck_at_turn"].notna().mean()*100:.1f}%)')
    print(f'  oscillation 検出: {summary_df["oscillation_at_turn"].notna().sum()}/{len(summary_df)} '
          f'({summary_df["oscillation_at_turn"].notna().mean()*100:.1f}%)')
    print(f'  unique CID per start: mean={summary_df["n_unique_cid"].mean():.2f}, '
          f'median={summary_df["n_unique_cid"].median():.0f}, '
          f'max={summary_df["n_unique_cid"].max()}')

    # top-1 (Step C smoke) との比較
    print('\n--- top-1 vs top-3 sampling 比較 (seed=0) ---')
    top1_smoke = pd.read_parquet(V1106B_MAIN / 'observation_1_familiarity_trajectory_smoke.parquet')
    top1_summary = []
    for (_, start_cid), grp in top1_smoke.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn')
        fam_vals = [f for f in grp_sorted['last_familiarity_max'].tolist() if f is not None]
        cids = grp_sorted['cid'].tolist()
        start_fam = fam_vals[0] if fam_vals else None
        min_fam = min(fam_vals) if fam_vals else None
        rollback = (start_fam is not None and min_fam is not None
                     and min_fam < start_fam * 0.8)
        top1_summary.append({
            'start_cid': start_cid, 'n_unique_cid_top1': len(set(cids)),
            'min_fam_top1': min_fam,
            'rollback_top1': rollback,
            'stuck_top1': grp_sorted['stuck_at_turn'].iloc[0],
        })
    top1_df = pd.DataFrame(top1_summary)

    compare = summary_df[['start_cid', 'n_unique_cid', 'min_familiarity',
                            'rollback_20pct', 'stuck_at_turn']].rename(columns={
        'n_unique_cid': 'n_unique_cid_top3sample',
        'min_familiarity': 'min_fam_top3sample',
        'rollback_20pct': 'rollback_top3sample',
        'stuck_at_turn': 'stuck_top3sample',
    }).merge(top1_df, on='start_cid', how='left')

    out2 = V1106B_MAIN / 'observation_4_smoke_compare_top1.parquet'
    compare.to_parquet(out2, index=False)
    print(f'  wrote {out2.name}')

    valid_cmp = compare.dropna(subset=['n_unique_cid_top1', 'n_unique_cid_top3sample'])
    print(f'\n  unique CID: top-1 mean={valid_cmp["n_unique_cid_top1"].mean():.2f} '
          f'(N=15)、top-3 sampling mean={valid_cmp["n_unique_cid_top3sample"].mean():.2f} (N=40)')
    print(f'  rollback 率: top-1 {valid_cmp["rollback_top1"].mean()*100:.1f}% '
          f'(N=15)、top-3 sampling {valid_cmp["rollback_top3sample"].mean()*100:.1f}% (N=40)')
    print(f'  stuck 検出: top-1 {valid_cmp["stuck_top1"].notna().sum()}/{len(valid_cmp)} '
          f'(N=15)、top-3 sampling {valid_cmp["stuck_top3sample"].notna().sum()}/{len(valid_cmp)} (N=40)')

    # min_fam の差
    valid_minfam = compare.dropna(subset=['min_fam_top1', 'min_fam_top3sample'])
    if len(valid_minfam) > 0:
        diff = valid_minfam['min_fam_top3sample'] - valid_minfam['min_fam_top1']
        print(f'  min_fam diff (top-3 - top-1): mean={diff.mean():.2f}, '
              f'median={diff.median():.2f}, std={diff.std():.2f}')
        print(f'  top-3 sampling で min_fam が小さくなる事例: '
              f'{(diff < 0).sum()}/{len(valid_minfam)} ({(diff < 0).mean()*100:.1f}%)')


if __name__ == '__main__':
    main()
