#!/usr/bin/env python3
"""v1106b Step C — 観察 1 smoke: familiarity 軌跡 (1 seed)

目的:
- 1 seed (seed=0) の選定 CID (33 個程度) から N=15 turn 自己対話
- 各 turn の familiarity を記録、巻き戻り構造の smoke 観察
- main run 前の挙動確認 + per_seed bin 確保数報告

接続式:
  current_cid → cid_vec (48d) → atom 確率 (top-10) → word 確率 (top-15) → top word
  → 逆引き → atom 確率 → cid 候補 → top-1 next_cid

停止条件 (Code A 認識確認 §2.1):
- N turn 完走 (必ず)
- 同 CID 連続 K=3 → stuck_at_turn 記録のみ
- 直近 W=5 turn unique CID ≤ 2 → oscillation_at_turn 記録のみ

入力 (read-only):
- unified/v1106b/outputs/main/env_check_selected_cids.parquet
- developmental/v106/outputs/main/cid_structure_profile_seed{N}.csv
- developmental/v106/outputs/main/cid_atom_sim_matrix_seed{N}.parquet
- developmental/v106/outputs/main/axes_metadata.json
- unified/v1103/outputs/main/atom_centroids_48d_raw.parquet
- language/lexicon/data/mapper_output/*_a1.jsonl
- developmental/v105/diag_v105_main/subjects/per_subject_seed{N}.csv

出力:
- unified/v1106b/outputs/main/observation_1_familiarity_trajectory_smoke.parquet
- unified/v1106b/outputs/main/observation_1_smoke_per_seed_bin_counts.parquet
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
WORD_TOPK_FOR_LOOP = 15  # ESDE 発話から top-15 word を逆引きに渡す
STUCK_K = 3              # 同 CID 連続検出閾値
OSCILLATION_W = 5        # 直近 W turn の unique CID 閾値
OSCILLATION_UNIQUE_MAX = 2
SMOKE_SEED = 0


def get_axes():
    am = json.load(open(V106_MAIN / 'axes_metadata.json'))
    return [f'{ax["name"]}.{lvl}' for ax in am['axes_order'] for lvl in ax['level_names']]


def load_resources():
    axes = get_axes()
    print('[1] リソース読み込み')
    t0 = time.time()
    # atom centroids
    ac = pd.read_parquet(V1103_MAIN / 'atom_centroids_48d_raw.parquet')
    atom_to_centroid = {row['atom']: np.array([row[ax] for ax in axes], dtype=np.float64)
                         for _, row in ac.iterrows()}
    # per atom: list of (word, cos_sim, raw_48d) + word→atom→vec
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
    """seed の全 CID 48d vec lookup"""
    fp = V106_MAIN / f'cid_structure_profile_seed{seed}.csv'
    df = pd.read_csv(fp)
    return {int(r['cid']): r[[f'dim_{i}' for i in range(48)]].values.astype(np.float64)
            for _, r in df.iterrows()}


def load_seed_cid_atom_sim(seed):
    """seed の cid_atom_sim_matrix (cid 行 × atom 列)"""
    fp = V106_MAIN / f'cid_atom_sim_matrix_seed{seed}.parquet'
    df = pd.read_parquet(fp)
    return df


def load_seed_props(seed):
    """seed の per_subject (cid → familiarity 等)"""
    fp = V105_SUB / f'per_subject_seed{seed}.csv'
    df = pd.read_csv(fp, usecols=['cognitive_id', 'final_state',
                                    'last_familiarity_max', 'n_alphas_currently',
                                    'current_stability', 'current_social'])
    return df.set_index('cognitive_id')


def cid_to_word_top(cid_vec, atom_to_centroid, atom_to_word_sims, k_atom, k_word):
    """CID → atom 確率 → word 確率 (top-K)"""
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
    """word list → atom 確率分布 (raw_48d norm 重み)"""
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


def atom_to_cid_top1(atom_probs, sim_df, current_seed):
    """atom 確率分布 → 同 seed 内の cid 候補 top-1 (Code A 介在なし、top-1 固定)"""
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
    """top-1 自己対話、N turn 完走、stuck/oscillation 記録"""
    history = []
    current_cid = start_cid
    stuck_at = None
    oscillation_at = None
    cid_track = []  # 既訪 CID 順
    same_cid_run = 0
    prev_cid = None

    for t in range(n_turn + 1):  # turn 0 (初期) から N turn まで
        if current_cid not in cid_vecs:
            break
        cid_vec = cid_vecs[current_cid]
        # 物理量取得
        prop = props_df.loc[current_cid] if current_cid in props_df.index else {}
        fam = prop.get('last_familiarity_max', None) if not isinstance(prop, dict) else None
        if hasattr(fam, 'item'):
            fam = fam.item() if not pd.isna(fam) else None
        n_alphas = prop.get('n_alphas_currently', None) if not isinstance(prop, dict) else None
        if hasattr(n_alphas, 'item'):
            n_alphas = n_alphas.item() if not pd.isna(n_alphas) else None
        final_state = prop.get('final_state', None) if not isinstance(prop, dict) else None

        # ESDE 発話
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

        # stuck/oscillation
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

        # 逆引きで次 CID
        top_words = [w for w, _ in words_top]
        atom_probs2 = words_to_atoms(top_words, word_to_atom_vec)
        if not atom_probs2:
            break
        next_cid, _ = atom_to_cid_top1(atom_probs2, sim_df, seed)
        current_cid = next_cid

    # ラベル付与
    for h in history:
        h['stuck_at_turn'] = stuck_at
        h['oscillation_at_turn'] = oscillation_at

    return history


def main():
    V1106B_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106b Step C — 観察 1 smoke (seed=0) ===\n')
    t0 = time.time()

    axes, atom_to_centroid, atom_to_word_sims, word_to_atom_vec = load_resources()

    # smoke seed の選定 CID
    sel = pd.read_parquet(V1106B_MAIN / 'env_check_selected_cids.parquet')
    smoke_cids = sel[sel['seed'] == SMOKE_SEED]
    print(f'\n[2] smoke seed={SMOKE_SEED} 選定 CID: {len(smoke_cids)} 個')
    bin_dist = smoke_cids.groupby(['final_state', 'fam_bin']).size().to_dict()
    print(f'  bin 分布: {bin_dist}')

    # seed リソース
    print(f'\n[3] seed={SMOKE_SEED} リソース読み込み')
    sim_df = load_seed_cid_atom_sim(SMOKE_SEED)
    cid_vecs = load_seed_cid_vecs(SMOKE_SEED)
    props_df = load_seed_props(SMOKE_SEED)
    print(f'  cid_atom_sim: {sim_df.shape}, cid_vecs: {len(cid_vecs)}, props: {len(props_df)}')

    # 自己対話 (top-1)
    print(f'\n[4] 自己対話 (top-1, N={N_TURN} turn)')
    all_hist = []
    for i, (_, row) in enumerate(smoke_cids.iterrows()):
        start_cid = int(row['cid'])
        hist = self_dialogue(SMOKE_SEED, start_cid, N_TURN,
                              atom_to_centroid, atom_to_word_sims, word_to_atom_vec,
                              sim_df, props_df, cid_vecs)
        all_hist.extend(hist)
        if (i+1) % 5 == 0:
            print(f'  done {i+1}/{len(smoke_cids)}, elapsed {time.time()-t0:.1f}s')

    hist_df = pd.DataFrame(all_hist)
    out1 = V1106B_MAIN / 'observation_1_familiarity_trajectory_smoke.parquet'
    hist_df.to_parquet(out1, index=False)
    print(f'\n  wrote {out1.name} ({len(hist_df)} rows)')

    # per_seed bin 確保数 (全 24 seed、Taka 指示)
    print('\n[5] per_seed × bin 確保数集計 (全 24 seeds、Taka 指示)')
    seed_bin = sel.groupby(['seed', 'final_state', 'fam_bin'],
                            observed=True).size().reset_index(name='n_cid')
    out2 = V1106B_MAIN / 'observation_1_smoke_per_seed_bin_counts.parquet'
    seed_bin.to_parquet(out2, index=False)
    print(f'  wrote {out2.name}')

    # ghost が少ない seed の特定
    ghost = seed_bin[seed_bin['final_state'] == 'ghost']
    ghost_per_seed = ghost.groupby('seed')['n_cid'].sum().reset_index(name='ghost_total')
    low_ghost_seeds = ghost_per_seed[ghost_per_seed['ghost_total'] < 5].sort_values('ghost_total')
    print(f'\n  ghost 合計 < 5 の seed (構造ラベル候補):')
    print(low_ghost_seeds.to_string(index=False))

    # 観察 1 smoke サマリ
    print(f'\n=== Step C smoke 完了、elapsed {time.time()-t0:.1f}s ===\n')

    # 軌跡サマリ
    print('--- familiarity 軌跡 smoke 集計 ---')
    # 各 start_cid の familiarity 軌跡を集計
    summary = []
    for (sd, start_cid), grp in hist_df.groupby(['seed', 'start_cid']):
        grp_sorted = grp.sort_values('turn')
        fam_vals = grp_sorted['last_familiarity_max'].tolist()
        # 開始 fam (turn=0)
        start_fam = fam_vals[0] if fam_vals else None
        # 最終 fam
        end_fam = fam_vals[-1] if fam_vals else None
        # 最小 fam
        min_fam = min([f for f in fam_vals if f is not None], default=None)
        # 巻き戻りあり?
        rollback = (start_fam is not None and min_fam is not None
                     and min_fam < start_fam * 0.8)  # 20% 以上の低下
        summary.append({
            'seed': sd, 'start_cid': start_cid,
            'start_familiarity': start_fam,
            'end_familiarity': end_fam,
            'min_familiarity': min_fam,
            'rollback_20pct': rollback,
            'n_turns_recorded': len(fam_vals),
            'stuck_at_turn': grp_sorted['stuck_at_turn'].iloc[0],
            'oscillation_at_turn': grp_sorted['oscillation_at_turn'].iloc[0],
            'start_final_state': grp_sorted['final_state'].iloc[0],
        })
    summary_df = pd.DataFrame(summary)
    print(f'  n_start_cids: {len(summary_df)}')
    valid_fam = summary_df.dropna(subset=['start_familiarity', 'min_familiarity'])
    if len(valid_fam) > 0:
        print(f'  rollback (20%+ 低下): {valid_fam["rollback_20pct"].sum()}/{len(valid_fam)} '
              f'({valid_fam["rollback_20pct"].mean()*100:.1f}%)')
        print(f'  start_fam mean: {valid_fam["start_familiarity"].mean():.2f}, '
              f'end_fam mean: {valid_fam["end_familiarity"].mean():.2f}')
        print(f'  min_fam mean: {valid_fam["min_familiarity"].mean():.2f}')
    print(f'  stuck 検出: {summary_df["stuck_at_turn"].notna().sum()}/{len(summary_df)}')
    print(f'  oscillation 検出: {summary_df["oscillation_at_turn"].notna().sum()}/{len(summary_df)}')

    # final_state 別 rollback
    print(f'\n  --- start_final_state 別 rollback 率 ---')
    fs_summary = valid_fam.groupby('start_final_state').agg(
        n_start=('start_cid', 'count'),
        rollback_rate=('rollback_20pct', 'mean'),
        start_fam_mean=('start_familiarity', 'mean'),
        min_fam_mean=('min_familiarity', 'mean'),
    ).round(3)
    print(fs_summary.to_string())


if __name__ == '__main__':
    main()
