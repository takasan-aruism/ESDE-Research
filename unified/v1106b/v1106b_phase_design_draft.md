# v1106b 設計書 (草案、Code A 作成)

**Date**: 2026-05-28
**Author**: Code A (実装担当)
**Status**: 設計書草案 — Taka / Web Claude 確認待ち
**親**: v1106a Phase Result v3 (Web Claude) + v1106a Step K-P 統合報告書 (Code A) + 現在地資料 v2 (Web Claude、Taka 確認段階)

---

## 0. 主題

**Step M-P 正式化、CID 空間吸引・循環・局所共鳴の観察** (Taka 採用、v2 §7 候補 1、GPT 推奨)

問いの形: **A (点検)** — v1106a Step M-P を「観察主題」として正式化

### 0.1 なぜ この主題か (Taka 判断反映)

- Step M-P で実装した対話機能 (B-1/B-3/C-6/C-7) は「動いた」段階
- 観察された 4 件 (familiarity 巻き戻り / 反復停滞 / 離脱循環 / 感情語と物質語共出) は #L48 として記録したが、6 turn 1 例の事例観察
- これらを **多数の対話実行で構造事実として確定** することが v1106b の主題
- v2 §6.4 「他と違う」候補 (familiarity 巻き戻りなど) を内部観察の精度で詰める

### 0.2 v1106b で扱わないこと (範囲限定)

- ❌ 他生成方法 (LLM/WordNet/ランダム) との比較 (= 候補 3 / 5 の領域、v1106c 以降)
- ❌ LLM プロキシ統合 (= 候補 2 の領域、Code A 用語混乱リスクで保留)
- ❌ Operator / 分子 (進化途上、Taka 規律「実装が追いついていないと妄想化する」)
- ❌ ESDE 経由生成の「価値」判定 (judgment 回避、Taka 規律「ESDE らしさの確定は待て」)

---

## 1. 観察項目 (4 件)

### 1.1 観察 1: CID 空間吸引特性 (familiarity 軌跡)

**目的**: Step P で観察した familiarity 巻き戻り (T0=116 → T6=6.1) が個別事例か構造特性か確定

**手法**:
- 多数の開始 CID (例: 各 final_state × familiarity 高/中/低 から計 30-50 CID) を選定
- 各 CID から N turn 自己対話 (sampling モード、Code A 介在なし、ESDE の next CID を自動採用)
- turn 別 familiarity 値を記録、軌跡を統計
- 「巻き戻り (familiarity 減少)」が多数 CID で観察されるか

**期待される構造観察**:
- 巻き戻り率 (多数 CID で初期より低 familiarity に至る割合)
- 巻き戻り深度 (最低 familiarity / 開始 familiarity)
- 軌跡パターン (単調減少 / 振動 / 急降下後安定 等)
- 開始 CID 属性別の差 (hosted vs ghost vs reaped、各 final_state 内での挙動)

### 1.2 観察 2: 循環構造 (attractor 検出)

**目的**: Step P で観察した「離脱意図 (T11 depart) でも既訪 CID に戻る」現象が構造特性か確定

**手法**:
- 観察 1 と同じ多数開始 CID × N turn 自己対話データを使用
- 各 turn の CID 集合を記録、既訪 CID への復帰 turn を検出
- N turn 内で訪問 CID 数、unique CID 数、復帰率を集計
- attractor 候補 (高頻度復帰 CID、他から複数経路で到達される CID) を抽出

**期待される構造観察**:
- 平均 unique CID 数 / N turn
- 復帰率 (turn 数別の既訪復帰確率)
- attractor 候補 CID 群とその物理量特性
- 開始 CID 別の attractor 到達経路の差

### 1.3 観察 3: 局所共鳴 event の特性

**目的**: Step L で観察した CID-word +0.05 弱信号が、event level で「強信号 event のまばらな存在 + 大多数中立」の構造か確定

**手法**:
- Step L verification_a_cid_word_alignment.parquet (3,300 events) を再利用
- cos_sim 上位 5% / 下位 5% event を抽出
- 高 event vs 低 event の input_atom / atom 確率分布 top / word 分布 top の比較
- 高 event での「意味的共鳴」パターン (Step P T4-T6 のような) を構造観察

**期待される構造観察**:
- 高 cos_sim event の input_atom 偏り (特定 category / atom に集中するか)
- 高 cos_sim event の word 分布の意味的傾向 (Step M 全体頻出 word と異なるか)
- 低 cos_sim event の特性 (どんな状況で繋がりが弱いか)
- 中央値付近の event の振る舞い (平均値が示す像との差)

### 1.4 観察 4: ESDE 自己対話の純粋構造

**目的**: Step P は Code A 介在 (人間応答 → 逆引き) で対話したが、Code A 影響を除いた **ESDE 純粋循環** を観察

**手法**:
- 開始 CID から ESDE 発話 top-K word を採用 → 逆引きで次 CID → 発話 → 採用 → ...
- 人間応答なし、ESDE の発話を ESDE 自身に投げ続ける
- 多数開始 CID × N turn で実行
- 自己対話での CID 遷移パターン、収束/振動/拡散の挙動

**期待される構造観察**:
- 自己対話での収束パターン (1 CID に固定 / 複数 CID で循環 / 拡散)
- Code A 介在対話 (Step P) との比較 (CID 遷移範囲、familiarity 軌跡の差)
- 「ESDE 内で発話が成立するか」(意味的に首尾一貫する word 連鎖が出るか)

---

## 2. 実装方針

### 2.1 入力 (read-only、frozen)

- `unified/v1106a/v1106a_step_n_esde_speak_interactive.py` (B-3 関数群を library 化して再利用)
- `unified/v1106a/v1106a_step_o_esde_listen_reverse.py` (C-6 関数群)
- `unified/v1106a/v1106a_step_p_dialogue.py` (C-7 状態保持メカニズム)
- `unified/v1106a/outputs/main/verification_a_cid_word_alignment.parquet` (Step L 出力)
- `developmental/v106/outputs/main/cid_atom_sim_matrix_seed{N}.parquet`
- `developmental/v106/outputs/main/cid_structure_profile_seed{N}.csv`
- `language/lexicon/data/mapper_output/*_a1.jsonl`
- `developmental/v105/diag_v105_main/subjects/per_subject_seed{N}.csv`

### 2.2 出力先

`unified/v1106b/outputs/main/` 配下のみ (書込みパス検証で確認)

| ファイル | 内容 |
|---|---|
| `observation_1_familiarity_trajectory.parquet` | 観察 1: 開始 CID × turn × familiarity |
| `observation_1_summary.parquet` | 観察 1: 巻き戻り率/深度/パターン集計 |
| `observation_2_circulation.parquet` | 観察 2: 開始 CID × turn × visited CID |
| `observation_2_attractors.parquet` | 観察 2: attractor 候補 |
| `observation_3_high_low_events.parquet` | 観察 3: 高/低 cos_sim event 特性 |
| `observation_4_self_dialogue.parquet` | 観察 4: 自己対話履歴 |
| `observation_4_summary.parquet` | 観察 4: 自己対話パターン集計 |

### 2.3 規律継承 (v1106a)

- **smoke 後 pause** (memory rule、smoke 完了後は Taka/Web Claude 確認待ち)
- **資料作成後 push** (memory rule、commit + push まで一気)
- **データ取り違え防止** (v1106 §22.5、入力ファイル明示確認)
- **bit-identity 検証** (Step I 同様、Step C-終了後に再実行 hash 一致)
- **書込みパス検証** (V1106B 配下のみ、grep で機械的確認)
- **24 seeds は 1 バッチで** (memory rule)
- **smoke seed 0 を絶対視しない** (memory rule、main run で再確認)

### 2.4 Step 分解 (草案)

| Step | 内容 | 想定実行時間 |
|---|---|---|
| A | 認識確認 + 設計合意 | Taka/Web Claude 確認 |
| B | 環境準備 (リソース load 確認、開始 CID 選定) | 数秒 |
| C | 観察 1 smoke (1 seed のみ) | 数秒、pause + 報告 |
| D | 観察 1 main (全 24 seeds、多数 CID × N turn) | 数分 |
| E | 観察 2 (循環構造、観察 1 データ再集計) | 数秒 |
| F | 観察 3 (高/低 cos_sim event 特性) | 数秒 |
| G | 観察 4 smoke (1 seed のみ) | 数秒、pause + 報告 |
| H | 観察 4 main (全 24 seeds 自己対話) | 数分 |
| I | bit-identity 検証 (3 層、Step C-H 再実行 hash 一致) | 数分 |
| J | 観察事実最終報告 | Taka/Web Claude 確認 |

### 2.5 想定パラメータ (Step A 認識確認で確定)

- 開始 CID 数: 各 final_state (hosted/ghost/reaped) × familiarity bin (low/mid/high) で計 30-50 CID
- N turn: 観察 1/2 で 10-20 turn、観察 4 で 30-50 turn
- sampling モード: 観察 1/2 では top-1 (再現性)、観察 4 では sampling (多様性)

---

## 3. 留保継承 + 新規予測

### 3.1 v1106a から継承

- #L41: 案 Y で構造的解消 → v1106b では案 Y 継続使用
- #L42: word union 同値 + 確率分布微差 → v1106b では問題なし (個別 event 観察主体)
- #L46: couple_bonus 効果消失 (案 X) → v1106b では案 Y なので影響なし
- #L47: CID-word 弱信号 +0.05 → v1106b 観察 3 で詳細追跡
- #L48: 対話特性 4 件 → v1106b 観察 1/2/4 で多数事例で確定

### 3.2 v1106b で新規想定される観察

| 想定 #L 番号 | 内容 |
|---|---|
| #L49 (予測) | familiarity 巻き戻り率/深度の構造特性 (観察 1) |
| #L50 (予測) | 循環 attractor の構造特性 (観察 2) |
| #L51 (予測) | 局所共鳴 event の input_atom 偏り (観察 3) |
| #L52 (予測) | 自己対話の収束/振動パターン (観察 4) |

新規 #L 番号は Web Claude 採番管理 (v2 規律) に従い、観察事実確定後に Web Claude が割当。

---

## 4. Taka / Web Claude への確認事項

### 4.1 Code A から Taka への確認

| 項目 | Code A 提案 | Taka 確認 |
|---|---|---|
| 主題範囲 | 観察 1-4 で範囲限定 (LLM/比較は別主題) | OK/NG |
| 観察 1 開始 CID 数 | 30-50 CID | 数量妥当か |
| 観察 1/2 N turn | 10-20 turn | turn 数妥当か |
| 観察 4 N turn | 30-50 turn (収束パターン観察のため長め) | turn 数妥当か |
| 観察 4 自己対話の意義 | Code A 介在影響を除いた純粋構造 | 必要か |

### 4.2 Code A から Web Claude への確認

| 項目 | Code A 提案 | Web Claude 確認 |
|---|---|---|
| 設計書全体 | 観察 4 件、smoke pause 規律継承 | 設計妥当か |
| 出力ファイル命名 | observation_N_*.parquet | 命名規律違反ないか |
| Step 分解 | A-J の 10 Step | 分解妥当か |
| #L 番号予約 | #L49-#L52 を予約として記載 | 採番管理に従うか |
| v1106b の問いの形 | A (点検) | B (試行) ではなく A で良いか |

---

## 5. 一文サマリ

v1106b 設計書草案として、Taka 採用主題「Step M-P 正式化、CID 空間吸引・循環・局所共鳴の観察」(v2 §7 候補 1、GPT 推奨) に対し、観察 1 (familiarity 軌跡、多数開始 CID × N turn) + 観察 2 (循環構造 attractor 検出) + 観察 3 (Step L verification_a 高/低 cos_sim event 特性) + 観察 4 (ESDE 自己対話純粋構造) の 4 観察を Step A-J で実装、入力は v1106a Step N/O/P スクリプト + Step L 出力 + v106 cid_atom_sim_matrix + mapper_output で frozen、出力は unified/v1106b/outputs/main/ 配下のみ、smoke 後 pause / 資料作成後 push / データ取り違え防止 / bit-identity 検証 / 24 seeds 1 バッチ / smoke seed 0 を絶対視しない の v1106a 規律継承、留保 #L41/L42/L46-L48 継承 + 新規 #L49-L52 (familiarity 巻き戻り構造特性 / 循環 attractor / 局所共鳴 atom 偏り / 自己対話収束パターン) の予測 (採番は Web Claude 一元管理)、Taka 確認事項 5 件 + Web Claude 確認事項 5 件、範囲外は LLM プロキシ / 他生成方法比較 / Operator / 価値判定 (judgment 回避)、Code A は Taka/Web Claude 確認待ち。

---

**設計書草案 end.**
