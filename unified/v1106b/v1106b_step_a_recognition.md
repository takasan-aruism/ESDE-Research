# v1106b Step A — Code A 認識確認

**Date**: 2026-05-28
**Author**: Code A (実装担当)
**Status**: Step A 認識確認、Web Claude 確認待ち
**親**: Code A 設計書草案 (`v1106b_phase_design_draft.md`) + Web Claude 確認文書 (Taka 承認 + 追加提案 4 件)

---

## 0. Code A 受領内容の認識

### 0.1 Taka 承認内容
- Code A 設計書草案 (4 観察、A-J Step 構成、問いの形 A、範囲限定) → **OK**
- Web Claude 追加提案 4 件 (Step F.5 / v1107 接続記述 / Taka 直感メモ接続議題 / 自己対話停止条件提示) → **OK**
- §4.1 Taka 確認事項 5 件 → **すべて Code A 提案で承認**

### 0.2 Web Claude 追加提案の組み込み認識

| 提案 | 組み込み内容 |
|---|---|
| 1 (Step F.5 追加) | Step F 完了後 G 前に Web Claude へ観察 4 実装方針報告 |
| 2 (v1107 接続記述) | 観察 4 結果は v1107 主題判断材料として記述 (Phase Result で議題化、確定でなく) |
| 3 (Taka 直感メモ接続議題) | #L49 候補確定時に Taka 直感メモ (主体性複数 / 応答時間が系を変化) 接続を議題化 |
| 4 (自己対話停止条件) | 本文書 §3 で Code A 実装方針を提示 |

### 0.3 Step 分解 (F.5 追加後)

| Step | 内容 |
|---|---|
| **A** | **認識確認 (本文書)** |
| B | 環境準備 (リソース load 確認、開始 CID 選定) |
| C | 観察 1 smoke (1 seed のみ) → pause + Web Claude 報告 |
| D | 観察 1 main (24 seeds × 多数 CID × N turn) |
| E | 観察 2 (循環構造、観察 1 データ再集計) |
| F | 観察 3 (高/低 cos_sim event 特性) |
| **F.5 (新規)** | **観察 4 実装方針報告 → Web Claude 確認** |
| G | 観察 4 smoke (1 seed のみ) → pause + Web Claude 報告 |
| H | 観察 4 main (24 seeds 自己対話) |
| I | bit-identity 検証 (3 層、Step C-H 再実行 hash 一致) |
| J | 観察事実最終報告 (Code A → Web Claude Phase Result 着手) |

---

## 1. データ取り違え防止 §0.7 必須確認

v1106 §22.5 継承の必須確認 5 件:

### 1.1 データ所在 (実環境照合)

| データ | パス | 状態 |
|---|---|---|
| cid_atom_sim_matrix | `developmental/v106/outputs/main/cid_atom_sim_matrix_seed{N}.parquet` (24 files) | 存在確認 ✓ |
| cid_structure_profile | `developmental/v106/outputs/main/cid_structure_profile_seed{N}.csv` (24 files) | 存在確認 ✓ |
| mapper_output | `language/lexicon/data/mapper_output/*_a1.jsonl` (325 files) | 存在確認 ✓ |
| atom_centroids_48d_raw | `unified/v1103/outputs/main/atom_centroids_48d_raw.parquet` (325 atoms) | 存在確認 ✓ |
| verification_a_alignment | `unified/v1106a/outputs/main/verification_a_cid_word_alignment.parquet` (3,300 events) | 存在確認 ✓ |
| per_subject (CID 物理量) | `developmental/v105/diag_v105_main/subjects/per_subject_seed{N}.csv` (24 files) | 存在確認 ✓ |
| axes_metadata | `developmental/v106/outputs/main/axes_metadata.json` | 存在確認 ✓ |

### 1.2 timestamp 確認 (frozen 確認)

| データ | timestamp | 凍結状態 |
|---|---|---|
| v106 (cid_atom_sim_matrix / cid_structure_profile) | 旧 main run | frozen ✓ |
| v1103 atom_centroids | v1103 実行時 | frozen ✓ |
| mapper_output | 2026-02-21〜23 (LLM 1 億トークン 8 日間) | frozen ✓ |
| v1106a verification_a | 2026-05-27 (Step L 実行) | frozen ✓ |
| v105 per_subject | 旧 main run | frozen ✓ |

→ **全データ frozen、v1106b 実行で書き換わらない**。

### 1.3 生成方法 (各データの Taka 過去評価との整合)

| データ | 生成方法 | 整合性 |
|---|---|---|
| cid_atom_sim_matrix | v106_post_process.py で cosine_similarity(cid_vec, atom_profiles_normalized_mean) | v106 として確立 ✓ |
| atom_centroids_48d_raw | v1103 で mapper_output raw_scores の atom 内 word mean | v1103 として確立 ✓ |
| mapper_output | LLM Qwen32B が word × 48 軸を 0-10 整数で判定 (1 億 tokens / 8 日間) | Taka 評価「最新」✓ |
| verification_a | v1106a Step L で CID 48d × word 加重 48d centroid cos_sim 計算 | Step L で確立 ✓ |

### 1.4 古い実装との並存

- v1106b は v1106a Step K-P 実装 (案 Y) をそのまま正式化
- 古い案 X / 案 Z-1 は v1106b で使わない (参照のみ可、計算には使わない)
- v1106 Synapse v3 は v1106b で使わない
- → **古い実装との並存なし**

### 1.5 出力上書き防止

- v1106b 出力は `unified/v1106b/outputs/main/` 配下のみ
- 既存 v1106a 出力は上書きしない (別ディレクトリ)
- bit-identity 検証 (Step I) で書込みパス機械的確認

→ **データ取り違え防止規律 §0.7 すべて確認、問題なし**。

---

## 2. 新規実装方針の確認 (Web Claude 追加提案 4 反映)

### 2.1 自己対話の停止条件 (観察 4)

**Code A 提案**:

| 条件 | 採用 | 動作 |
|---|---|---|
| N turn 到達 (デフォルト) | ✓ | 必ず N turn 到達で終了、最大 turn 数を保証 |
| 同 CID 連続 K 回 (K=3) | ラベル付与のみ | 中断はせず継続、`stuck_at_turn` フィールドに記録 |
| CID 振動収束 (直近 W=5 turn の unique CID ≤ 2) | ラベル付与のみ | 中断はせず継続、`oscillation_at_turn` に記録 |

→ **強制中断はせず、N turn 完走 + 状態ラベル記録**で構造観察に活かす。

**理由**:
- T10 のような同 CID 固定や T4↔T12 のような循環は **観察対象そのもの**
- 中断すると振動・収束パターンが捕捉できなくなる
- N turn 完走で固定/振動/拡散の判別可能なデータが残る

### 2.2 top-1 vs sampling の使い分け

**Code A 提案**:

| 観察 | next CID 選択方式 | 理由 |
|---|---|---|
| 観察 1 (familiarity 軌跡) | top-1 | 再現性確保、軌跡パターンの統計集約 |
| 観察 2 (循環構造) | top-1 | 同上 (観察 1 データ再集計) |
| 観察 3 (高/低 cos_sim event) | N/A | event 単位の静的分析 |
| 観察 4 (自己対話) | top-3 sampling (確率重み) | 多様性確保、振動性も観察 |

→ 観察 1/2 で **構造の骨格** を把握、観察 4 で **振動性込みの実態** を把握。

### 2.3 Code A 介在なし保証 (観察 4)

**Code A 提案実装方針**:

```python
# 観察 4 自己対話バッチ実行 (擬似コード)
def self_dialogue_loop(seed, start_cid, n_turn, top_k=3, sampling=True):
    history = [{'turn': 0, 'cid': start_cid, ...}]
    current_cid = start_cid
    for t in range(1, n_turn + 1):
        # ESDE 発話
        cid_vec = get_cid_vec(seed, current_cid)
        word_probs, atom_probs = cid_to_words(cid_vec)

        # ESDE 自身の発話を取って次 CID を決める (人間応答なし)
        # top-3 word を「ESDE の応答」として扱う
        top_words = [w for w, p in word_probs[:top_k]]

        # 逆引き
        atom_probs2, _, _ = words_to_atom_probs(top_words, word_to_atom_vec)
        cid_candidates = atom_to_cid_candidates(atom_probs2, seeds=[seed], topk=5)

        # 次 CID: top-1 (sampling=False) or top-3 sampling (sampling=True)
        if sampling:
            scores = np.array([s for _, _, s in cid_candidates])
            probs = scores / scores.sum()
            idx = np.random.choice(len(scores), p=probs)
            next_seed, next_cid, _ = cid_candidates[idx]
        else:
            next_seed, next_cid, _ = cid_candidates[0]

        history.append({'turn': t, 'cid': next_cid, ...})
        current_cid = next_cid
    return history
```

→ **人間入力 (response 引数) 不要、スクリプト内で完結**。Code A は実行コードを起動するだけで、内容に介在しない。

### 2.4 v1107 接続記述の組み込み

設計書 §3.2 と §5 に Web Claude 追加提案 2 通りの記述を追加:

> 観察 4 (ESDE 自己対話純粋構造) の結果は v1107 以降の主題判断材料として活用される可能性 (Taka 構想「1 seed 常時 main run、cid 時系列増殖、マーカー = 注目」との接続)。本主題では構造事実観察に留め、解釈は Phase Result で議題化。

留保 #L49 候補 (familiarity 巻き戻り構造特性) の説明に Web Claude 追加提案 3 通りの記述を追加:

> #L49 が確定した場合、Taka 直感メモ (主体性複数 / 応答時間が系を変化) との接続を Phase Result で議題化。確定でなく議題として残す (Taka 規律「ESDE らしさの確定は待て」)。

---

## 3. 想定実行時間 (Code A 試算)

| Step | 内容 | 想定時間 |
|---|---|---|
| B 環境準備 | リソース load + 開始 CID 選定 (各 final_state × familiarity bin で計 40 CID/seed) | 数秒 |
| C 観察 1 smoke | 1 seed × 40 CID × 15 turn = 600 turn | 1-2 分 |
| D 観察 1 main | 24 seeds × 40 CID × 15 turn = 14,400 turn | 10-20 分 |
| E 観察 2 | 観察 1 データ再集計 (attractor 検出) | 数秒 |
| F 観察 3 | verification_a 3,300 events 上位/下位 5% 抽出 + 集計 | 数秒 |
| F.5 観察 4 実装方針報告 | Web Claude 確認 | 待ち |
| G 観察 4 smoke | 1 seed × 40 CID × 40 turn = 1,600 turn | 2-5 分 |
| H 観察 4 main | 24 seeds × 40 CID × 40 turn = 38,400 turn | 20-40 分 |
| I bit-identity 検証 | 3 層 (Step C-H 再実行 hash 一致 / 物理層 frozen / 書込みパス) | 30-60 分 (Step C-H 再実行含む) |
| J 観察事実最終報告 | Code A まとめ | 待ち |

**合計実装実行時間**: 60-120 分 (Step I 再実行含む)

### 3.1 計算量根拠

- 1 turn の処理: cid_vec → atom_probs (325 atom × 48 cos) → word_probs (各 atom の word に重み付け) → 逆引き (word → atom → cid_candidates)
- 1 turn あたり ~0.1 秒 (Step P 実測ベース)
- 観察 1: 14,400 turn × 0.1s ≈ 24 分
- 観察 4: 38,400 turn × 0.1s ≈ 64 分

実装で reduce (リソース load を 1 回、cos_sim 行列を pre-compute 等) すれば短縮可能。

---

## 4. 確認要請 (Web Claude 判断仰ぐ事項)

### 4.1 中断判断基準

予想外の結果が出た場合の中断方針:

| 予想外 | Code A 案 |
|---|---|
| 観察 1 で familiarity 巻き戻りが全く起こらない (Step P 1 事例が特異だった) | 中断せず完走、Phase Result で「特異事例」として記録 |
| 観察 4 で全 CID が即座に同 CID 固定 (1-2 turn で停止状態) | 中断せず完走 (停止条件は記録のみ)、Phase Result で「固定優位」として記録 |
| Step I bit-identity 違反 (Step C-H 再実行で hash 不一致) | **中断、Web Claude 報告**、原因究明後に再実行 |
| 物理層 frozen 違反 (v106/v1103/mapper_output に書き込み発生) | **即時中断、Web Claude 報告**、書込み箇所特定 |

### 4.2 留保候補と実観察事実が異なる場合の Phase Result 記述方針

#L49-#L52 候補は **予測**。実観察事実と異なる場合:

- 候補と異なる構造が観察された → そのまま観察事実として記録 (留保番号は Web Claude 再採番)
- 候補は妥当 → そのまま観察事実 + 候補番号で確定
- どちらでも判断つかない → 「観察事実 + 留保候補保留」として Phase Result 議題化

→ **Code A は予測に固執せず、実観察事実を優先**。Web Claude が Phase Result で採番。

### 4.3 観察 1 開始 CID 選定方針

各 seed で 40 CID を以下の方針で選定:

| final_state | familiarity bin | per-seed CID 数 |
|---|---|---|
| hosted (生存中) | low (familiarity < 10) | 5 |
| hosted | mid (10-50) | 5 |
| hosted | high (≥50) | 5 |
| ghost (消滅進行中) | low | 5 |
| ghost | mid | 5 |
| ghost | high | 5 |
| reaped (消滅済) | low | 5 |
| reaped | mid (任意) | 5 |

→ 24 seeds × 40 CID = **960 開始 CID** で観察 1/2、観察 4 で同 CID 群を使う。

→ 実 CID 数が 40 未満の bin がある場合は全 CID 採用 + 次の bin で補填。

---

## 5. Code A から Web Claude への確認

| 項目 | Code A 提案 | Web Claude 確認待ち |
|---|---|---|
| 自己対話停止条件 (§2.1) | 中断せず N turn 完走、状態ラベル記録のみ | 採用 OK か |
| top-1 vs sampling 使い分け (§2.2) | 観察 1/2=top-1、観察 4=top-3 sampling | 採用 OK か |
| Code A 介在なし保証 (§2.3) | 擬似コード方針、人間 input なし | 実装方針 OK か |
| 想定実行時間 (§3) | 観察 1=10-20 分、観察 4=20-40 分、I=30-60 分 | 妥当か |
| 中断判断基準 (§4.1) | bit-identity 違反 / 物理層 frozen 違反のみ即時中断 | 採用 OK か |
| 開始 CID 選定方針 (§4.3) | 3 final_state × 8 bin = 40 CID/seed | 採用 OK か |

---

## 6. Code A から Taka への確認 (任意)

| 項目 | Code A 提案 |
|---|---|
| 観察 1 開始 CID 数 | 40 CID/seed × 24 seeds = 960 CID |
| 観察 4 turn 数 | 40 turn (収束パターン捕捉のため) |
| 観察期間中の Taka 確認頻度 | smoke 後 (Step C / Step G) で必ず pause、main 後 (Step D / Step H) は Code A 自走 |

→ Code A 自走を許可するか、main 後も pause するかは Taka 判断領域。

---

## 7. 規律遵守確認

| 規律 | 遵守確認 |
|---|---|
| 絶対格言 #5 軸増やさない | ✓ 既存軸 (Step M-P) の精度向上 |
| 絶対格言 #6 出口固定 | ✓ §0.2 で範囲外明示 |
| 絶対格言 #11 概念単位を雑に扱わない | ✓ 観察 1-4 別レイヤー |
| 絶対格言 #12 judgment 回避 | ✓ 「価値」「優れた」書かない |
| データ取り違え防止 §0.7 | ✓ §1 で 5 件確認 |
| 留保番号統一管理 | ✓ Code A は候補扱い、Web Claude 採番 |
| 概念定義 vs 実装段階の区別 | ✓ Atom 326/325 区別を Phase Result でも継続 |
| smoke 後 pause | ✓ Step C / Step G で pause |
| 資料作成後 push | ✓ 本文書も push 予定 |
| 24 seeds 1 バッチ | ✓ Step D / Step H 共通 |
| smoke seed 0 を絶対視しない | ✓ main 結果で再確認 |
| 物理層 frozen | ✓ v106 / v1103 / mapper_output / v1106a 全 frozen |

---

## 8. 一文サマリ

v1106b Step A 認識確認として、Code A 設計書草案 + Web Claude 確認文書 (Taka 承認 + 追加提案 4 件) を全 OK で受領、Step F.5 (観察 4 実装方針報告) を組み込んだ A-J 10 Step 構成、データ取り違え防止 §0.7 必須確認 5 件すべて確認 (データ所在 / timestamp frozen / 生成方法 / 古い実装並存なし / 出力上書き防止)、新規実装方針 4 件 (自己対話停止条件 = 中断せず N turn 完走 + 状態ラベル記録 / top-1 vs sampling = 観察 1/2 top-1 + 観察 4 top-3 sampling / Code A 介在なし保証 = スクリプト内完結 / v1107 接続記述 + Taka 直感メモ接続議題 = 設計書 §3.2/§5/#L49 説明に追加) を Code A 提案、想定実行時間 (観察 1 main 10-20 分 / 観察 4 main 20-40 分 / bit-identity 30-60 分、合計 60-120 分) を試算、確認要請 3 件 (中断判断基準 = bit-identity/物理層 frozen 違反のみ即時中断 / 留保候補と実観察事実差異時 = Code A 予測固執せず実観察優先 / 観察 1 開始 CID 選定 = 3 final_state × 8 bin で 40 CID/seed × 24 seeds = 960 CID) を提示、規律遵守 12 件 (絶対格言 + データ取り違え防止 + 留保番号統一管理 + 概念定義実装段階区別 + smoke pause + push + 24 seeds + smoke 絶対視回避 + 物理層 frozen) すべて確認、Web Claude 確認待ち事項 6 件 + Taka 任意確認事項 3 件、Web Claude 確認後に Step B 環境準備へ進行。

---

**Step A 認識確認 end.**
