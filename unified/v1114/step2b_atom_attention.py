#!/usr/bin/env python3
"""v1114 Step 2-B Atom 経由の注意 (押し込まず、注意を向ける)

## 観察対象注釈ブロック (実装着手前に明示、Code A 自己強制ハードル)

### 観察対象の本質
- 同じ系内 (Center 単体、Atom なし) の Step 2-A の percept に
  **8 番目 trigger 'atom_resonance_<atom>' を追加** (Atom 手置き → cid_atom_sim_matrix → top-k cid)
- Atom を ESDE に押し込まない (= engine.state 触らない、physics.inject 呼ばない)
- 「注意を向ける」だけ (= percept レコードに 8 番目 trigger として記録)

### Taka 釘 3 点 (2026-06-09)
釘 (1) 人工性留保:
  - cid_atom_sim_matrix は「4 月の手定義投影 (48 軸) を 6 月 cid に再適用するだけ」
  - 再生成で本物になったと読まない、CID→48次元は手定義投影と明示
  - resources の 留保: 48 次元は両端で人工 (LLM 判定 + Web Claude 手定義)

釘 (2) 位置づけ正確 (crown 禁止):
  - 「Atom 手置き → 共鳴 CID → percept 8 番目 trigger」の **配管確認まで**
  - 応答 (CID 群の dynamics) は **Step 3 以降**、本実装では扱わない
  - 入力テキスト → Atom の知覚は **無い** (Atom 手置き、LLM 経由は穴として残す)

釘 (3) 規律:
  - 既存スキーマ互換 (Step 2-A の percept 形式と同じ records)
  - 共鳴 CID は cid_atom_sim_matrix の lookup のみ (z で切らない・合成しない)
  - k は単純固定 (TOP_K = 5)、明示
  - engine.state 触らない・inject 呼ばない (γ との区別: 発火させずに観察)
  - 「向いた」を観察事実として記録 (判定・crown しない)

### 過去資産流用
- v106_post_process.py の per-axis cid vector builders (temporal/scale/epistemological/...) を import
- atom_centroids_48d (v1103 で生成、unified/v1103/outputs/main/atom_centroids_48d_normalized.parquet)
- Step 2-A の attention_records.json (Center 観察基盤 443 records)
- v105-today output (per_subject_seed0.csv + per_subject_audit_seed0.csv)

### Atom→ESDE 注入経路は **無い**
- 実機調査確認 (2026-06-09): physics.inject は全て node ID 経路、Atom 経由 source_event 無い
- 「新規の橋」は作らない (= Taka の線、神の手回避)
- 代わりに「注意を向ける」(本実装) で対応

### 残さないもの (Step 2-A 継続)
- node ID / 座標 / 不透明 float / 判定数値 (z) / 設計パラメータ / 差・有意差 / 近似擦り替え

### γ (押し込み) との区別
- (γ): cid_atom_sim_matrix → top-k cid → physics.inject (= pulse 発火、物理介入)
- 本実装: cid_atom_sim_matrix → top-k cid → percept 8 番目 trigger (観察のみ、物理触らず)
"""
import os, sys, json
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import pandas as pd

REPO = Path('/home/takasan/esde/ESDE-Research')
sys.path.insert(0, str(REPO / 'developmental/v106'))

OUT_DIR = REPO / 'unified/v1114/run_step2b'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 入力ソース
STEP2A_RECORDS_PATH = REPO / 'unified/v1114/run_step2a/attention_records.json'
V105_TODAY_DIR = Path('/tmp/v105_step2a_seed0_main/diag_v105_step2a_seed0')
PER_SUBJECT_PATH = V105_TODAY_DIR / 'subjects/per_subject_seed0.csv'
PER_SUBJECT_AUDIT_PATH = V105_TODAY_DIR / 'audit/per_subject_audit_seed0.csv'
ATOM_CENTROIDS_PATH = REPO / 'unified/v1103/outputs/main/atom_centroids_48d_normalized.parquet'

# 構成 (釘 3 遵守: k 単純固定)
TOP_K = 5  # 各 Atom 入力に対して top-k 共鳴 CID を引く (固定、明示)
TEST_ATOMS = [
    'WLD.science',
    'COG.understand',
    'ACT.build',
    'FND.spaceless',
    'EMO.calm',
]  # Atom 手置き (テスト用、LLM 経由は穴として残す)


def load_v106_builders():
    """v106_post_process.py の per-axis cid vector builders を import (関数のみ流用)"""
    import v106_post_process as v106pp
    return v106pp


def build_cid_vectors_from_v105today():
    """v105-today output (per_subject + audit) から 280 cid × 48 次元 vector を構築

    釘 (1) 人工性留保: CID → 48 次元は手定義投影 (v106 の per-axis builders、4 月設計)
                       これを 6 月 cid に再適用するだけ、本物になったと読まない。
    """
    v106pp = load_v106_builders()

    df_subj = pd.read_csv(PER_SUBJECT_PATH)
    df_audit = pd.read_csv(PER_SUBJECT_AUDIT_PATH)
    audit_cols = [
        'cid', 'n_core_member', 'v14_q0', 'v14_q_remaining', 'v14_q_spent',
        'v14_q_exhausted', 'v14_virtual_attention_entries', 'v14_virtual_attention_sum',
        'v14_virtual_familiarity_entries', 'v14_virtual_familiarity_sum',
    ]
    df_audit = df_audit[[c for c in audit_cols if c in df_audit.columns]].copy()
    df = df_subj.merge(
        df_audit, how='left', left_on='cognitive_id', right_on='cid', suffixes=('', '_audit')
    )
    df['seed'] = 0
    df['lifespan_steps'] = df.apply(v106pp.calc_lifespan, axis=1)

    seed_max = v106pp.compute_seed_max(df)

    cid_list = []
    vec_list = []
    for _, row in df.iterrows():
        cid = int(row['cognitive_id'])
        try:
            vec = v106pp.build_cid_vector(row, seed_max)
        except RuntimeError as e:
            print(f'  cid={cid} skip: {e}')
            continue
        cid_list.append(cid)
        vec_list.append(vec)

    cid_vectors = np.array(vec_list, dtype=np.float32)
    print(f'cid vectors: {cid_vectors.shape} (= {len(cid_list)} cids × 48 dims)')
    return cid_list, cid_vectors


def compute_cid_atom_sim_matrix(cid_list, cid_vectors):
    """atom_centroids_48d × cid_vectors の cosine sim matrix"""
    centroids_df = pd.read_parquet(ATOM_CENTROIDS_PATH)
    atom_names = centroids_df['atom'].tolist()
    atom_cols = [c for c in centroids_df.columns if c not in ('atom', 'n_words')]
    atom_matrix = centroids_df[atom_cols].values.astype(np.float32)  # (325, 48)
    print(f'atom centroids: {atom_matrix.shape} (= {len(atom_names)} atoms × 48 dims)')

    # cosine sim
    cid_norm = np.linalg.norm(cid_vectors, axis=1, keepdims=True)
    cid_norm[cid_norm < 1e-9] = 1.0
    cid_unit = cid_vectors / cid_norm
    atom_norm = np.linalg.norm(atom_matrix, axis=1, keepdims=True)
    atom_norm[atom_norm < 1e-9] = 1.0
    atom_unit = atom_matrix / atom_norm

    sim_matrix = cid_unit @ atom_unit.T  # (280, 325)
    print(f'sim matrix: {sim_matrix.shape}')

    # parquet 化 (Step 2-A スキーマ互換、v106 cid_atom_sim_matrix と同形式)
    out_df = pd.DataFrame(sim_matrix, columns=atom_names)
    out_df.insert(0, 'cid', cid_list)
    out_df.insert(0, 'seed', 0)
    out_path = OUT_DIR / 'cid_atom_sim_matrix_v105today.parquet'
    out_df.to_parquet(out_path, index=False)
    print(f'保存: {out_path.relative_to(REPO)}')
    return out_df, atom_names


def get_top_k_resonant_cids(sim_df, atom_name, allowed_cids, k=TOP_K):
    """Atom スコア順に top-k cid を取得、ただし allowed_cids (Center 知覚済み) に絞る (修正 A)

    釘 3: lookup のみ、合成しない
    修正 A (2026-06-09): atom が指す cid は Center が知覚できる cid 集合に絞る
    """
    if atom_name not in sim_df.columns:
        return []
    df = sim_df[sim_df['cid'].isin(allowed_cids)][['cid', atom_name]].copy()
    sorted_df = df.sort_values(atom_name, ascending=False).head(k)
    return [(int(row['cid']), float(row[atom_name])) for _, row in sorted_df.iterrows()]


def build_atom_resonance_records(sim_df, atom_names_input, start_order, cid_percept_map):
    """各 Atom 入力に対して top-k 共鳴 CID を引いて percept レコードを生成

    修正 B (2026-06-09): atom_resonance レコードを既存スキーマに揃える
    - 共鳴 cid の percept (n_core/C/Q/lifespan/pulse_reactivity/familiarity_n/familiarity_sizes)
      を point/neighborhood に乗せる (cid_percept_map から取得)
    - atom_name は別キー 'atom_via' で由来として添える
    - rank_in_topk は記号 ('top1'..'top5') で記録
    - raw cosine_sim は落とす (両端人工投影の連続値、percept でない)

    釘 3 遵守: trigger=atom_resonance_<atom>、k 固定 5、lookup のみ
    """
    records = []
    order = start_order
    allowed_cids = set(cid_percept_map.keys())  # Center が知覚した cid 集合
    for atom_name in atom_names_input:
        top_k = get_top_k_resonant_cids(sim_df, atom_name, allowed_cids, k=TOP_K)
        for rank, (cid, _sim_val) in enumerate(top_k):
            percept = cid_percept_map.get(cid)
            if percept is None:
                continue  # 念のため (allowed_cids で絞ってあるので発生しない)
            record = {
                'order': order,
                'cid': cid,
                'trigger': f'atom_resonance_{atom_name}',
                'point': dict(percept['point']),  # Step 2-A 形式 (n_core/lifespan/pulse_reactivity/C/Q_remaining)
                'neighborhood': dict(percept['neighborhood']),  # familiarity_n + familiarity_sizes
                'atom_via': atom_name,  # 由来 (記号)
                'rank_in_topk': f'top{rank + 1}',  # 記号 (top1..top5)
            }
            records.append(record)
            order += 1
    return records


def build_cid_percept_map(step2a_records):
    """Step 2-A records から cid → 最新 percept (point/neighborhood) のマップを構築

    修正 A 補助: Center が知覚した cid 集合とその percept を取得
    同じ cid が複数 record に登場する場合、最新 (最大 order) を採用
    """
    cid_percept = {}
    for r in step2a_records:
        cid = int(r['cid'])
        # 最新 order を優先 (order は通し番号、後勝ち)
        if cid not in cid_percept or r['order'] > cid_percept[cid]['_order']:
            cid_percept[cid] = {
                'point': r['point'],
                'neighborhood': r['neighborhood'],
                '_order': r['order'],
            }
    # _order を落として返す
    return {cid: {'point': v['point'], 'neighborhood': v['neighborhood']}
            for cid, v in cid_percept.items()}


def main():
    print('=== v1114 Step 2-B Atom 経由の注意 (押し込まず、注意を向ける) ===\n')
    print(f'  入力 Step 2-A records: {STEP2A_RECORDS_PATH}')
    print(f'  入力 per_subject: {PER_SUBJECT_PATH}')
    print(f'  入力 atom_centroids: {ATOM_CENTROIDS_PATH}')
    print(f'  TEST_ATOMS (手置き): {TEST_ATOMS}')
    print(f'  TOP_K = {TOP_K} (固定、明示)')
    print(f'  釘 (1) 人工性留保 / (2) 配管確認まで / (3) 観察のみ\n')

    # === Step 2-A の percept レコード読み込み ===
    if not STEP2A_RECORDS_PATH.exists():
        print(f'ERROR: Step 2-A records not found: {STEP2A_RECORDS_PATH}')
        sys.exit(1)
    with open(STEP2A_RECORDS_PATH) as f:
        step2a_records = json.load(f)
    print(f'Step 2-A records: {len(step2a_records)}')

    # === 修正 A: Step 2-A records から Center が知覚した cid → percept マップ構築 ===
    cid_percept_map = build_cid_percept_map(step2a_records)
    print(f'Center が知覚した unique cid: {len(cid_percept_map)} (= atom の lookup 範囲)')

    # === v105-today output から 48 次元 vector 構築 ===
    print('\n=== cid vector 構築 (v106 builders、4 月手定義投影を 6 月 cid に再適用) ===')
    cid_list, cid_vectors = build_cid_vectors_from_v105today()

    # === cid_atom_sim_matrix 生成 ===
    print('\n=== cid_atom_sim_matrix 計算 ===')
    sim_df, atom_names = compute_cid_atom_sim_matrix(cid_list, cid_vectors)

    # === 修正 A 確認: sim_df の cid と Center 知覚 cid の重なり ===
    sim_cids = set(int(c) for c in sim_df['cid'].values)
    center_cids = set(cid_percept_map.keys())
    overlap = sim_cids & center_cids
    print(f'\n修正 A 確認:')
    print(f'  sim_matrix の cid 数: {len(sim_cids)} (v106 が cid_vector を作れた集合)')
    print(f'  Center 知覚 cid 数: {len(center_cids)} (Step 2-A records の unique cid)')
    print(f'  両者の重なり: {len(overlap)} ← atom 経由で引ける cid 範囲 (Center が必ず知覚済み)')

    # === TEST_ATOMS で top-k 共鳴 CID 抽出 + 8 番目 trigger レコード生成 ===
    print('\n=== Atom 手置き → top-k 共鳴 CID (Center 知覚済みに絞る) → 8 番目 trigger ===')
    atom_records = build_atom_resonance_records(
        sim_df, TEST_ATOMS, start_order=len(step2a_records),
        cid_percept_map=cid_percept_map,
    )

    print(f'\natom_resonance records: {len(atom_records)}')
    print(f'引き金別:')
    trig_dist = Counter(r['trigger'] for r in atom_records)
    for trig, cnt in trig_dist.most_common():
        print(f'  {trig}: {cnt}')

    # 共鳴 CID の cid + 主要 percept (cosine_sim は出力しない、percept のみ)
    print(f'\n各 Atom の top-5 共鳴 CID とその percept:')
    for atom_name in TEST_ATOMS:
        if atom_name not in sim_df.columns:
            print(f'  {atom_name}: (Atom 不在、atom_centroids に無し)')
            continue
        records_for_atom = [r for r in atom_records if r['trigger'] == f'atom_resonance_{atom_name}']
        if not records_for_atom:
            print(f'  {atom_name}: top-k 抽出失敗 (Center 知覚と重なりなし)')
            continue
        print(f'  {atom_name}:')
        for r in records_for_atom:
            p = r['point']
            n = r['neighborhood']
            print(f'    {r["rank_in_topk"]} cid={r["cid"]}: n_core={p.get("n_core")} lifespan={p.get("lifespan")} '
                  f'pulse={p.get("pulse_reactivity")} C={p.get("C")} Q={p.get("Q_remaining")} '
                  f'fam_n={n.get("familiarity_n")} fam_sizes={n.get("familiarity_sizes")}')

    # === Step 2-A records + 8 番目 trigger records を結合して出力 ===
    combined_records = step2a_records + atom_records
    print(f'\n結合 records 総数: {len(combined_records)} (Step 2-A {len(step2a_records)} + atom_resonance {len(atom_records)})')

    out_records_path = OUT_DIR / 'attention_records.json'
    out_records_path.write_text(json.dumps(combined_records, indent=2, ensure_ascii=False))
    print(f'保存: {out_records_path.relative_to(REPO)}')

    summary = {
        'design': 'v1114_step2b_atom_attention',
        'note': '釘 3 点遵守: (1) cid_atom_sim_matrix は 4 月手定義投影を 6 月 cid に再適用するだけ、人工性は消えない (本物にならない). (2) 位置づけ = 配管確認まで、応答 (CID 群 dynamics) は Step 3、入力テキスト→Atom は LLM 経由の穴. (3) 観察のみ・engine.state 触らず・inject 呼ばず・8 番目 trigger は既存スキーマ互換.',
        'top_k': TOP_K,
        'test_atoms': TEST_ATOMS,
        'step2a_records_count': len(step2a_records),
        'atom_resonance_records_count': len(atom_records),
        'combined_records_count': len(combined_records),
        'cid_vectors_shape': list(cid_vectors.shape),
        'sim_matrix_shape': [int(sim_df.shape[0]), int(sim_df.shape[1] - 2)],  # (cid, atoms)
        'v105_today_dir': str(V105_TODAY_DIR),
        'atom_centroids_path': str(ATOM_CENTROIDS_PATH.relative_to(REPO)),
    }
    summary_path = OUT_DIR / 'summary.json'
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'保存: {summary_path.relative_to(REPO)}')

    print(f'\n=== Step 2-B 完了 ===')
    print(f'観察事実: Atom 手置き → cid_atom_sim_matrix lookup → top-{TOP_K} 共鳴 CID を percept に追加')
    print(f'差は測らず、crown せず (配管確認のみ、応答 dynamics は Step 3)')


if __name__ == '__main__':
    main()
