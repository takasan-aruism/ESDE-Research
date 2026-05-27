#!/usr/bin/env python3
"""v1106b Step H — 観察 4 main run: ESDE 自己対話 top-3 sampling (24 seeds × 681 CID × 40 turn)

Step G smoke の同設計を全 24 seeds に拡大。
構造ラベル付与 (Step D と同様):
- ghost_bin_low_n / seed_with_low_ghost_total
- stuck_at_turn / oscillation_at_turn / rollback_20pct

出力:
- unified/v1106b/outputs/main/observation_4_self_dialogue.parquet
- unified/v1106b/outputs/main/observation_4_summary.parquet
- unified/v1106b/outputs/main/observation_4_aggregate.parquet
- unified/v1106b/outputs/main/observation_4_vs_top1_compare.parquet
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
    V1106B_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106b Step H — 観察 4 main (top-3 sampling、24 seeds × 681 CID × 40 turn) ===\n')
    t0 = time.time()

    axes, atom_to_centroid, atom_to_word_sims, word_to_atom_vec = load_resources()

    sel = pd.read_parquet(V1106B_MAIN / 'env_check_selected_cids.parquet')
    print(f'\n[2] 選定 CID: {len(sel)} (seeds: {sel["seed"].nunique()})')

    # 構造ラベル準備 (Step D と同)
    ghost_per_seed = sel[sel['final_state'] == 'ghost'].groupby('seed').size().to_dict()
    seed_low_ghost = {sd for sd in range(24) if ghost_per_seed.get(sd, 0) < 5}
    bin_per_seed = sel.groupby(['seed', 'final_state', 'fam_bin'],
                                 observed=True).size().to_dict()

    print(f'\n[3] 自己対話 sampling (top-{SAMPLING_K}, N={N_TURN} turn, rng_seed={RNG_SEED})')
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
            hist = self_dialogue_sampling(sd, start_cid, N_TURN,
                                             atom_to_centroid, atom_to_word_sims,
                                             word_to_atom_vec,
                                             sim_df, props_df, cid_vecs, rng)
            fs = row['final_state']
            fb = row['fam_bin']
            n_in_bin = bin_per_seed.get((sd, fs, fb), 0)
            for h in hist:
                h['start_final_state'] = fs
                h['start_fam_bin'] = fb
                h['seed_with_low_ghost_total'] = sd in seed_low_ghost
                h['ghost_bin_low_n'] = (fs == 'ghost' and n_in_bin < 3)
            all_hist.extend(hist)
        print(f'  seed={sd} done ({len(seed_sel)} CID, {time.time()-ts:.1f}s)')

    hist_df = pd.DataFrame(all_hist)
    out1 = V1106B_MAIN / 'observation_4_self_dialogue.parquet'
    hist_df.to_parquet(out1, index=False)
    print(f'\n  wrote {out1.name} ({len(hist_df):,} rows)')

    # per start_cid 集計
    print('\n[4] per start_cid 集計')
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
        # 復帰 turn 検出
        seen = set()
        first_revisit = None
        for i, c in enumerate(cids):
            if c in seen and first_revisit is None:
                first_revisit = i
            seen.add(c)
        summary.append({
            'seed': sd, 'start_cid': start_cid,
            'start_final_state': grp_sorted['start_final_state'].iloc[0],
            'start_fam_bin': grp_sorted['start_fam_bin'].iloc[0],
            'start_familiarity': start_fam,
            'end_familiarity': end_fam,
            'min_familiarity': min_fam,
            'rollback_20pct': rollback,
            'n_unique_cid': len(set(cids)),
            'n_turn': len(cids),
            'first_revisit_turn': first_revisit,
            'stuck_at_turn': grp_sorted['stuck_at_turn'].iloc[0],
            'oscillation_at_turn': grp_sorted['oscillation_at_turn'].iloc[0],
            'seed_with_low_ghost_total': grp_sorted['seed_with_low_ghost_total'].iloc[0],
            'ghost_bin_low_n': grp_sorted['ghost_bin_low_n'].iloc[0],
        })
    summary_df = pd.DataFrame(summary)
    out2 = V1106B_MAIN / 'observation_4_summary.parquet'
    summary_df.to_parquet(out2, index=False)
    print(f'  wrote {out2.name} ({len(summary_df)} rows)')

    # final_state × fam_bin 集計
    print('\n[5] final_state × fam_bin 集計')
    valid = summary_df.dropna(subset=['start_familiarity', 'min_familiarity'])
    agg = valid.groupby(['start_final_state', 'start_fam_bin'], observed=True).agg(
        n_start=('start_cid', 'count'),
        rollback_rate=('rollback_20pct', 'mean'),
        start_fam_mean=('start_familiarity', 'mean'),
        end_fam_mean=('end_familiarity', 'mean'),
        min_fam_mean=('min_familiarity', 'mean'),
        n_unique_cid_mean=('n_unique_cid', 'mean'),
        stuck_rate=('stuck_at_turn', lambda x: x.notna().mean()),
        oscillation_rate=('oscillation_at_turn', lambda x: x.notna().mean()),
        first_revisit_turn_median=('first_revisit_turn', 'median'),
    ).round(3).reset_index()
    out3 = V1106B_MAIN / 'observation_4_aggregate.parquet'
    agg.to_parquet(out3, index=False)
    print(f'  wrote {out3.name}')

    # observation 1 (top-1) と比較
    print('\n[6] top-1 (Step D) vs top-3 sampling (Step H) 比較')
    top1_sum = pd.read_parquet(V1106B_MAIN / 'observation_1_summary.parquet')
    cmp = top1_sum.rename(columns={
        'min_familiarity': 'min_fam_top1',
        'rollback_20pct': 'rollback_top1',
        'n_unique_cid_visited': 'n_unique_cid_top1',
        'stuck_at_turn': 'stuck_top1',
    })[['seed', 'start_cid', 'start_familiarity', 'min_fam_top1', 'rollback_top1',
        'n_unique_cid_top1', 'stuck_top1']].merge(
        summary_df.rename(columns={
            'min_familiarity': 'min_fam_top3',
            'rollback_20pct': 'rollback_top3',
            'n_unique_cid': 'n_unique_cid_top3',
            'stuck_at_turn': 'stuck_top3',
        })[['seed', 'start_cid', 'min_fam_top3', 'rollback_top3',
            'n_unique_cid_top3', 'stuck_top3']],
        on=['seed', 'start_cid'], how='inner')
    out4 = V1106B_MAIN / 'observation_4_vs_top1_compare.parquet'
    cmp.to_parquet(out4, index=False)
    print(f'  wrote {out4.name}')

    print(f'\n=== Step H 完了、elapsed {time.time()-t0:.1f}s ===\n')

    # サマリ
    print('--- 観察 4 main 全体集計 (681 CID, N=40) ---')
    print(f'  rollback (20%+): {valid["rollback_20pct"].sum()}/{len(valid)} '
          f'({valid["rollback_20pct"].mean()*100:.1f}%)')
    print(f'  start_fam mean: {valid["start_familiarity"].mean():.2f}, '
          f'end_fam mean: {valid["end_familiarity"].mean():.2f}, '
          f'min_fam mean: {valid["min_familiarity"].mean():.2f}')
    print(f'  stuck 検出: {summary_df["stuck_at_turn"].notna().sum()}/{len(summary_df)} '
          f'({summary_df["stuck_at_turn"].notna().mean()*100:.1f}%)')
    print(f'  oscillation 検出: {summary_df["oscillation_at_turn"].notna().sum()}/{len(summary_df)} '
          f'({summary_df["oscillation_at_turn"].notna().mean()*100:.1f}%)')
    print(f'  unique CID per start mean: {summary_df["n_unique_cid"].mean():.2f}')
    print(f'  first revisit turn median: {summary_df["first_revisit_turn"].median():.0f}')

    print('\n--- start_final_state × start_fam_bin 別 ---')
    print(agg.to_string(index=False))

    # top-1 vs top-3 sampling 比較
    print('\n--- top-1 (Step D, N=15) vs top-3 sampling (Step H, N=40) 比較 ---')
    print(f'  unique CID mean: top-1 {cmp["n_unique_cid_top1"].mean():.2f}, '
          f'top-3 {cmp["n_unique_cid_top3"].mean():.2f} (差 {cmp["n_unique_cid_top3"].mean()-cmp["n_unique_cid_top1"].mean():+.2f})')
    print(f'  rollback 率: top-1 {cmp["rollback_top1"].mean()*100:.1f}%, '
          f'top-3 {cmp["rollback_top3"].mean()*100:.1f}%')
    diff = cmp.dropna(subset=['min_fam_top1', 'min_fam_top3'])
    if len(diff) > 0:
        d = diff['min_fam_top3'] - diff['min_fam_top1']
        print(f'  min_fam diff (top-3 - top-1): mean={d.mean():+.2f}, median={d.median():+.2f}')
        print(f'  top-3 で min_fam がより小さくなる事例: '
              f'{(d < 0).sum()}/{len(diff)} ({(d < 0).mean()*100:.1f}%)')


if __name__ == '__main__':
    main()
