#!/usr/bin/env python3
"""v1106a Step L 検証 A: CID 48d vec と word 分布加重 48d centroid の直接 cos_sim

目的:
  ユーザー指摘「単語群と atom に潜在的繋がりがあるはずなのに rc 無相関は変」
  → rc 指標は atom 間距離と atom 内 word 質の比較で本来の繋がり指標でない
  → CID (Genesis 物理量由来 48d) と word 分布 (案 Y) の 48 軸意味空間での
     直接整合性を測定

接続経路 (検証 A):
  CID (Genesis 系) → build_cid_vector → cid 48d (v106 cid_structure_profile)
  event word 分布 (案 Y) → Σ_w prob(w) × raw_scores(w) → weighted 48d centroid
  両者の cosine_similarity を計算 → 「CID 状態」と「word が指す意味中心」の整合

ランダムベースライン:
  - 同 seed 内 CID シャッフル (event の真の CID と無関係な CID を組み合わせ)
  - 全 seed クロス CID シャッフル (より厳しいベースライン)

期待:
  - 真の cos_sim > shuffled (有意差) → 潜在的繋がりあり (実装由来でなく構造由来)
  - 真の cos_sim ≈ shuffled → 実装が勝手に繋いでいるだけ (繋がりは説明力低い)

入力 (read-only):
  - unified/v1105a/outputs/main/trial_step2_associations.parquet (event ↔ CID マッピング)
  - unified/v1106a/outputs/main/observation_Y_word_distributions.parquet (案 Y word 分布)
  - developmental/v106/outputs/main/cid_structure_profile_seed{N}.csv (CID 48d, 24 seeds)
  - language/lexicon/data/mapper_output/*_a1.jsonl (word raw_scores 48d)
  - developmental/v106/outputs/main/axes_metadata.json (48 軸順序)

出力:
  - unified/v1106a/outputs/main/verification_a_cid_word_alignment.parquet
    (per event の cid_word_cos_sim + shuffled controls)
  - unified/v1106a/outputs/main/verification_a_summary.parquet (集約統計)
"""
from __future__ import annotations
import json, time
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
V105_MAIN = REPO / 'unified/v1105a/outputs/main'
V106_MAIN = REPO / 'developmental/v106/outputs/main'
V1106A_MAIN = REPO / 'unified/v1106a/outputs/main'
MAPPER_DIR = REPO / 'language/lexicon/data/mapper_output'

# v106 axes_metadata 順序 = CID 48d 順序 = mapper word raw_scores 順序
def get_axes_order():
    am = json.load(open(V106_MAIN/'axes_metadata.json'))
    axes = []
    for axis in am['axes_order']:
        for lvl in axis['level_names']:
            axes.append(f'{axis["name"]}.{lvl}')
    assert len(axes) == 48
    return axes


def main():
    V1106A_MAIN.mkdir(parents=True, exist_ok=True)
    print('=== v1106a Step L 検証 A: CID 48d × word 加重 48d の直接 cos_sim ===')
    t0 = time.time()

    AXES = get_axes_order()
    print(f'48 軸順序 (v106 axes_metadata): {AXES[:3]} ... {AXES[-3:]}')

    # (1) event ↔ CID マッピング
    print('\n[1] event ↔ CID マッピング読み込み')
    assoc = pd.read_parquet(V105_MAIN / 'trial_step2_associations.parquet',
                             columns=['seed', 'event_id', 'source_cid'])
    event_cid = assoc.drop_duplicates(['seed', 'event_id', 'source_cid'])
    print(f'  event-cid pairs: {len(event_cid):,}')
    # 1 event = 1 cid か確認
    mult = event_cid.groupby(['seed', 'event_id']).size()
    print(f'  events with multiple cids: {(mult > 1).sum()} / {len(mult)}')

    # (2) CID 48d vec (全 seed)
    print('\n[2] CID 48d vec 読み込み (24 seeds)')
    cid_vec = {}  # (seed, cid) → np.ndarray(48)
    dim_cols = [f'dim_{i}' for i in range(48)]
    for sd in range(24):
        fp = V106_MAIN / f'cid_structure_profile_seed{sd}.csv'
        if not fp.exists():
            continue
        df = pd.read_csv(fp, usecols=['seed', 'cid'] + dim_cols)
        for _, row in df.iterrows():
            cid_vec[(int(row['seed']), int(row['cid']))] = row[dim_cols].values.astype(np.float64)
    print(f'  CID 48d vec: {len(cid_vec):,}')

    # (3) word 48d raw_scores 読み込み (全 word の lookup)
    print('\n[3] word 48d raw_scores 読み込み')
    word_to_vec = {}  # word → np.ndarray(48) (atom が違う場合は最初の atom 採用)
    word_to_atom_vec = defaultdict(dict)  # word → atom → np.ndarray(48) (atom 別 lookup)
    for fp in sorted(MAPPER_DIR.glob('*_a1.jsonl')):
        atom = fp.stem.replace('_a1', '').replace('_', '.', 1)
        with open(fp) as f:
            for line in f:
                r = json.loads(line)
                if r.get('status') != 'OK': continue
                rs = r.get('raw_scores')
                if not isinstance(rs, dict): continue
                vec = np.array([rs.get(ax, 0.0) for ax in AXES], dtype=np.float64)
                word_to_atom_vec[r['word']][atom] = vec
    # word ↔ atom 多対多 (word が複数 atom に登場する場合あり、案 Y 出力には input_atom 別の分布)
    print(f'  unique words: {len(word_to_atom_vec)}')
    n_word_atom_pairs = sum(len(d) for d in word_to_atom_vec.values())
    print(f'  (word, atom) lookup pairs: {n_word_atom_pairs:,}')

    # (4) 案 Y word 分布 (s7 のみ)
    print('\n[4] 案 Y word 分布 (s7) 読み込み')
    dist_y = pd.read_parquet(V1106A_MAIN / 'observation_Y_word_distributions.parquet')
    s7 = dist_y[dist_y['series_id'] == 's7_48d_raw_k5']
    print(f'  s7 rows: {len(s7):,}, events: {s7.groupby(["seed","event_id"]).ngroups:,}')

    # (5) per event で word 加重 48d centroid 計算 + CID cos_sim
    print('\n[5] per event 計算 (cid 48d vs word weighted 48d centroid)')
    cid_lookup = event_cid.set_index(['seed', 'event_id'])['source_cid'].to_dict()

    out_rows = []
    n_grp = s7.groupby(['seed', 'event_id']).ngroups
    cnt = 0
    skipped = {'no_cid': 0, 'no_cid_vec': 0, 'no_word_vec': 0, 'zero_norm': 0}

    # event ごとに input_atom を取得 (word の atom 文脈に使う)
    iatom_lookup = s7.drop_duplicates(['seed', 'event_id'])[['seed','event_id','input_atom']].set_index(['seed','event_id'])['input_atom'].to_dict()

    for (sd, eid), grp in s7.groupby(['seed', 'event_id']):
        cnt += 1
        if cnt % 500 == 0:
            print(f'  processed {cnt:,}/{n_grp:,}, elapsed {time.time()-t0:.1f}s')

        # CID 取得
        if (sd, eid) not in cid_lookup:
            skipped['no_cid'] += 1
            continue
        cid = int(cid_lookup[(sd, eid)])
        if (sd, cid) not in cid_vec:
            skipped['no_cid_vec'] += 1
            continue
        cid_v = cid_vec[(sd, cid)]
        cid_norm = np.linalg.norm(cid_v)
        if cid_norm == 0:
            skipped['zero_norm'] += 1
            continue

        # word 加重 48d centroid 計算
        word_centroid = np.zeros(48)
        total_prob = 0.0
        n_word_used = 0
        for _, row in grp.iterrows():
            word = row['candidate_word']
            prob = row['probability']
            if word not in word_to_atom_vec: continue
            # 同 word の中で 1 atom 採用 (atom 別差は本検証では問わない、全 atom 平均)
            vecs = list(word_to_atom_vec[word].values())
            wv = np.mean(vecs, axis=0)  # word の atom 横断平均
            word_centroid += prob * wv
            total_prob += prob
            n_word_used += 1
        if n_word_used == 0 or total_prob == 0:
            skipped['no_word_vec'] += 1
            continue
        word_centroid /= total_prob
        wc_norm = np.linalg.norm(word_centroid)
        if wc_norm == 0:
            skipped['zero_norm'] += 1
            continue

        cs = float(np.dot(cid_v, word_centroid) / (cid_norm * wc_norm))

        out_rows.append({
            'seed': sd,
            'event_id': eid,
            'cid': cid,
            'input_atom': iatom_lookup[(sd, eid)],
            'n_words': n_word_used,
            'cid_word_cos_sim': cs,
            'cid_norm': float(cid_norm),
            'word_centroid_norm': float(wc_norm),
        })

    df = pd.DataFrame(out_rows)
    print(f'\n  processed: {len(df):,}, skipped: {skipped}')

    # (6) ベースライン: shuffled CID (同 seed 内)
    print('\n[6] Shuffled baseline (同 seed 内ランダム CID)')
    np.random.seed(42)
    shuffled_within = []
    shuffled_cross = []  # 全 seed × CID プールから無作為

    cid_pool = list(cid_vec.keys())  # (seed, cid)
    for _, r in df.iterrows():
        sd = int(r['seed'])
        # 同 seed CID プール
        seed_cids = [c for (s, c) in cid_pool if s == sd]
        # 真の cid と違う CID をランダム選択
        choices = [c for c in seed_cids if c != int(r['cid'])]
        if not choices:
            shuffled_within.append(np.nan)
            continue
        fake_cid = int(np.random.choice(choices))
        fake_v = cid_vec[(sd, fake_cid)]
        fnorm = np.linalg.norm(fake_v)
        if fnorm == 0:
            shuffled_within.append(np.nan)
            continue
        # word_centroid を r から再計算するのは重いので保存値が必要 — 再計算する
        # → 計算量考慮: 簡易化として word_centroid_norm から逆算は不能、
        #   ここでは事前計算した cos_sim と norm のみから shuffled cos_sim を計算するため、
        #   word_centroid 自体を memoize する必要あり。
        pass

    # 計算量問題: word_centroid は per event で再計算必要 → 事前 dict 保存して shuffle baseline
    print('  (word_centroid を事前保存して shuffle 再計算)')
    word_centroids_by_event = {}
    for (sd, eid), grp in s7.groupby(['seed', 'event_id']):
        wc = np.zeros(48)
        tp = 0.0
        for _, row in grp.iterrows():
            w = row['candidate_word']
            if w not in word_to_atom_vec: continue
            vecs = list(word_to_atom_vec[w].values())
            wv = np.mean(vecs, axis=0)
            wc += row['probability'] * wv
            tp += row['probability']
        if tp > 0:
            wc /= tp
        if np.linalg.norm(wc) > 0:
            word_centroids_by_event[(sd, eid)] = wc

    np.random.seed(42)
    shuf_rows = []
    cid_pool_by_seed = defaultdict(list)
    for (s, c) in cid_pool:
        cid_pool_by_seed[s].append(c)

    for r in df.itertuples():
        wc = word_centroids_by_event.get((int(r.seed), r.event_id))
        if wc is None: continue
        wc_n = np.linalg.norm(wc)
        sd = int(r.seed); true_cid = int(r.cid)

        # within-seed shuffle (10 回平均)
        rho_w = []
        seed_cids = [c for c in cid_pool_by_seed[sd] if c != true_cid]
        if seed_cids:
            for _ in range(10):
                fc = int(np.random.choice(seed_cids))
                fv = cid_vec[(sd, fc)]
                fn = np.linalg.norm(fv)
                if fn > 0:
                    rho_w.append(float(np.dot(fv, wc) / (fn * wc_n)))

        # cross-seed shuffle (別 seed の CID を 5 回)
        rho_c = []
        for _ in range(5):
            other_seeds = [s for s in range(24) if s != sd and cid_pool_by_seed[s]]
            if not other_seeds: break
            other_sd = int(np.random.choice(other_seeds))
            fc = int(np.random.choice(cid_pool_by_seed[other_sd]))
            fv = cid_vec[(other_sd, fc)]
            fn = np.linalg.norm(fv)
            if fn > 0:
                rho_c.append(float(np.dot(fv, wc) / (fn * wc_n)))

        shuf_rows.append({
            'seed': sd, 'event_id': r.event_id,
            'shuffled_within_seed_mean': float(np.mean(rho_w)) if rho_w else np.nan,
            'shuffled_cross_seed_mean': float(np.mean(rho_c)) if rho_c else np.nan,
        })

    shuf_df = pd.DataFrame(shuf_rows)
    df = df.merge(shuf_df, on=['seed', 'event_id'], how='left')

    # (7) 出力
    out_d = V1106A_MAIN / 'verification_a_cid_word_alignment.parquet'
    df.to_parquet(out_d, index=False)
    print(f'\nwrote {out_d.name} ({len(df):,} rows)')

    print(f'\n=== Step L 検証 A 完了、elapsed {time.time()-t0:.1f}s ===')

    # (8) サマリ
    print('\n--- 検証 A 結果サマリ ---')
    true_cs = df['cid_word_cos_sim'].dropna()
    shuf_w = df['shuffled_within_seed_mean'].dropna()
    shuf_c = df['shuffled_cross_seed_mean'].dropna()

    print(f'真の CID × word centroid cos_sim:')
    print(f'  n={len(true_cs)}, mean={true_cs.mean():.4f}, median={true_cs.median():.4f}, std={true_cs.std():.4f}')
    print(f'  min={true_cs.min():.4f}, max={true_cs.max():.4f}')
    print(f'  >=0.9: {(true_cs >= 0.9).mean()*100:.2f}%, >=0.8: {(true_cs >= 0.8).mean()*100:.2f}%, >=0.5: {(true_cs >= 0.5).mean()*100:.2f}%')

    print(f'\nShuffled within-seed (random CID 別 in same seed):')
    print(f'  n={len(shuf_w)}, mean={shuf_w.mean():.4f}, median={shuf_w.median():.4f}, std={shuf_w.std():.4f}')

    print(f'\nShuffled cross-seed (random CID from other seed):')
    print(f'  n={len(shuf_c)}, mean={shuf_c.mean():.4f}, median={shuf_c.median():.4f}, std={shuf_c.std():.4f}')

    print(f'\n--- 有意性指標 ---')
    diff_w = true_cs.mean() - shuf_w.mean()
    diff_c = true_cs.mean() - shuf_c.mean()
    print(f'  真 vs within-seed shuffle: diff={diff_w:+.4f} ({diff_w/shuf_w.std():.2f} σ)')
    print(f'  真 vs cross-seed shuffle:  diff={diff_c:+.4f} ({diff_c/shuf_c.std():.2f} σ)')

    # paired event-level
    paired = df.dropna(subset=['cid_word_cos_sim', 'shuffled_within_seed_mean'])
    if len(paired) > 0:
        diff_paired = paired['cid_word_cos_sim'] - paired['shuffled_within_seed_mean']
        print(f'\n  event-paired diff (true - within shuffle):')
        print(f'    mean={diff_paired.mean():+.4f}, std={diff_paired.std():.4f}')
        print(f'    >0 rate: {(diff_paired > 0).mean()*100:.2f}% (50% ならランダム)')

    # 集約 summary
    summary = pd.DataFrame([{
        'true_n': len(true_cs),
        'true_mean': float(true_cs.mean()), 'true_median': float(true_cs.median()),
        'true_std': float(true_cs.std()),
        'shuffled_within_mean': float(shuf_w.mean()), 'shuffled_within_std': float(shuf_w.std()),
        'shuffled_cross_mean': float(shuf_c.mean()), 'shuffled_cross_std': float(shuf_c.std()),
        'diff_within_sigma': float(diff_w/shuf_w.std()),
        'diff_cross_sigma': float(diff_c/shuf_c.std()),
        'paired_diff_mean': float(diff_paired.mean()) if len(paired) > 0 else np.nan,
        'paired_positive_rate': float((diff_paired > 0).mean()) if len(paired) > 0 else np.nan,
    }])
    out_s = V1106A_MAIN / 'verification_a_summary.parquet'
    summary.to_parquet(out_s, index=False)
    print(f'\nwrote {out_s.name}')


if __name__ == '__main__':
    main()
