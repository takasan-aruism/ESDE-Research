#!/usr/bin/env python3
"""v1106b Step D — 観察 1 main run: familiarity 軌跡 (24 seeds × 681 CID × 15 turn)

Step C smoke と同接続式、全 24 seeds で実行。
構造ラベル付与 (Taka 指示反映):
- ghost_bin_low_n / seed_with_low_ghost_total
- stuck_at_turn / oscillation_at_turn / rollback_20pct

入力 / 出力: Step C と同パターン (smoke → main へ)
出力:
- unified/v1106b/outputs/main/observation_1_familiarity_trajectory.parquet (全 turn 履歴)
- unified/v1106b/outputs/main/observation_1_summary.parquet (per start_cid 集計)
- unified/v1106b/outputs/main/observation_1_aggregate.parquet (final_state × fam_bin 集計)
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

N_TURN = 15
ATOM_TOPK = 10
WORD_TOPK_FOR_LOOP = 15
STUCK_K = 3
OSCILLATION_W = 5
OSCILLATION_UNIQUE_MAX = 2


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


def atom_to_cid_top1(atom_probs, sim_df):
    scores = np.zeros(len(sim_df))
    for atom, p in atom_probs.items():
        if atom in sim_df.columns:
            sims = sim_df[atom].values.astype(np.float64)
            scores += p * np.clip(sims, 0, None)
    cids = sim_df['cid'].values
    order = np.argsort(-scores)
    return int(cids[order[0]]), float(scores[order[0]])


def self_dialogue(seed, start_cid, n_turn, atom_to_centroid, atom_to_word_sims,
                    word_to_atom_vec, sim_df, props_df, cid_vecs):
    history = []
    current_cid = start_cid
    stuck_at = None
    oscillation_at = None
    cid_track = []
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
        next_cid, _ = atom_to_cid_top1(atom_probs2, sim_df)
        current_cid = next_cid
    for h in history:
        h['stuck_at_turn'] = stuck_at
        h['oscillation_at_turn'] = oscillation_at
    return history


def main():
    V1106B_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106b Step D — 観察 1 main run (24 seeds × 681 CID × 15 turn) ===\n')
    t0 = time.time()

    axes, atom_to_centroid, atom_to_word_sims, word_to_atom_vec = load_resources()

    sel = pd.read_parquet(V1106B_MAIN / 'env_check_selected_cids.parquet')
    print(f'\n[2] 選定 CID: {len(sel)} (seeds: {sel["seed"].nunique()})')

    # seed 別 ghost 合計 (構造ラベル用)
    ghost_per_seed = sel[sel['final_state'] == 'ghost'].groupby('seed').size().to_dict()
    seed_low_ghost = {sd for sd in range(24) if ghost_per_seed.get(sd, 0) < 5}
    print(f'  seed_with_low_ghost_total (ghost < 5): {sorted(seed_low_ghost)}')

    # bin 別 per_seed CID 数 (ghost_bin_low_n 判定用)
    bin_per_seed = sel.groupby(['seed', 'final_state', 'fam_bin'],
                                 observed=True).size().to_dict()

    print(f'\n[3] 自己対話 (top-1, N={N_TURN} turn) for each seed')
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
            hist = self_dialogue(sd, start_cid, N_TURN,
                                  atom_to_centroid, atom_to_word_sims, word_to_atom_vec,
                                  sim_df, props_df, cid_vecs)
            # 構造ラベル追加
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
    out1 = V1106B_MAIN / 'observation_1_familiarity_trajectory.parquet'
    hist_df.to_parquet(out1, index=False)
    print(f'\n  wrote {out1.name} ({len(hist_df):,} rows)')

    # per start_cid 集計
    print('\n[4] per start_cid 集計')
    summary = []
    for (sd, start_cid), grp in hist_df.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn')
        fam_vals = grp_sorted['last_familiarity_max'].tolist()
        valid_fam = [f for f in fam_vals if f is not None]
        start_fam = fam_vals[0] if fam_vals else None
        end_fam = fam_vals[-1] if fam_vals else None
        min_fam = min(valid_fam) if valid_fam else None
        rollback = (start_fam is not None and min_fam is not None
                     and min_fam < start_fam * 0.8)
        n_unique_cid = grp_sorted['cid'].nunique()
        summary.append({
            'seed': sd, 'start_cid': start_cid,
            'start_final_state': grp_sorted['start_final_state'].iloc[0],
            'start_fam_bin': grp_sorted['start_fam_bin'].iloc[0],
            'start_familiarity': start_fam,
            'end_familiarity': end_fam,
            'min_familiarity': min_fam,
            'rollback_20pct': rollback,
            'n_unique_cid_visited': n_unique_cid,
            'n_turns_recorded': len(fam_vals),
            'stuck_at_turn': grp_sorted['stuck_at_turn'].iloc[0],
            'oscillation_at_turn': grp_sorted['oscillation_at_turn'].iloc[0],
            'seed_with_low_ghost_total': grp_sorted['seed_with_low_ghost_total'].iloc[0],
            'ghost_bin_low_n': grp_sorted['ghost_bin_low_n'].iloc[0],
        })
    summary_df = pd.DataFrame(summary)
    out2 = V1106B_MAIN / 'observation_1_summary.parquet'
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
        n_unique_cid_mean=('n_unique_cid_visited', 'mean'),
        stuck_rate=('stuck_at_turn', lambda x: x.notna().mean()),
        oscillation_rate=('oscillation_at_turn', lambda x: x.notna().mean()),
        stuck_at_turn_median=('stuck_at_turn', 'median'),
        oscillation_at_turn_median=('oscillation_at_turn', 'median'),
    ).round(3).reset_index()
    out3 = V1106B_MAIN / 'observation_1_aggregate.parquet'
    agg.to_parquet(out3, index=False)
    print(f'  wrote {out3.name}')

    print(f'\n=== Step D 完了、elapsed {time.time()-t0:.1f}s ===\n')

    # サマリ
    print('--- 全体集計 ---')
    print(f'  n_start_cids: {len(summary_df)}')
    print(f'  rollback (20%+): {valid["rollback_20pct"].sum()}/{len(valid)} '
          f'({valid["rollback_20pct"].mean()*100:.1f}%)')
    print(f'  start_fam mean: {valid["start_familiarity"].mean():.2f}, '
          f'end_fam mean: {valid["end_familiarity"].mean():.2f}, '
          f'min_fam mean: {valid["min_familiarity"].mean():.2f}')
    print(f'  stuck 検出: {summary_df["stuck_at_turn"].notna().sum()}/{len(summary_df)} '
          f'({summary_df["stuck_at_turn"].notna().mean()*100:.1f}%)')
    print(f'  oscillation 検出: {summary_df["oscillation_at_turn"].notna().sum()}/{len(summary_df)} '
          f'({summary_df["oscillation_at_turn"].notna().mean()*100:.1f}%)')
    print(f'  unique CID visited mean: {summary_df["n_unique_cid_visited"].mean():.2f}')

    print('\n--- start_final_state × start_fam_bin 別 ---')
    print(agg.to_string(index=False))

    # 構造ラベル別集計
    print('\n--- ghost_bin_low_n vs その他 ---')
    if 'ghost_bin_low_n' in summary_df.columns:
        for label_val in [False, True]:
            sub = valid[valid['ghost_bin_low_n'] == label_val]
            if len(sub) > 0:
                print(f'  ghost_bin_low_n={label_val}: n={len(sub)}, '
                      f'rollback_rate={sub["rollback_20pct"].mean():.3f}, '
                      f'min_fam_mean={sub["min_familiarity"].mean():.2f}')

    print('\n--- seed_with_low_ghost_total vs その他 ---')
    for label_val in [False, True]:
        sub = valid[valid['seed_with_low_ghost_total'] == label_val]
        if len(sub) > 0:
            print(f'  seed_with_low_ghost_total={label_val}: n={len(sub)}, '
                  f'rollback_rate={sub["rollback_20pct"].mean():.3f}')


if __name__ == '__main__':
    main()
