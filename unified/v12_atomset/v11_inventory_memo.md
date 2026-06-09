# v11 棚卸しメモ (v1100 → v1114) — 実コード突合せ + v12 への接続

date: 2026-06-10
from: Code A (Claude Code, Opus 4.7)
to: Web Claude (Phase Result 一本化用素材) / Taka
status: 二本目 (smoke 待ち時間並行)、Web Claude v11 全体 Phase Result の土台

---

## 0. 一文サマリ (v11 → v12)

v11.0.0 (v1100) Language↔Genesis 接続事前調査 → v11.0.1 (v1101) Atom 的隆盛の統計的観察 → v11.0.1.a (v1101a) ESDE スケール注意機構 → v11.0.2 (v1102) 受け手構造×時間スケール 2 次元観察 → v11.0.3 (v1103) 段 4-c 48 次元密度点検 + `atom_centroids_48d` Code A 生成 → v11.0.4 (v1104) + v11.0.4a CID/IID 内部動作点検 (4 つの非対称性 #L30-L33 確定) → v11.0.5 (v1105/v1105a) 段 4-b/4-c 統合点検 + 役割表 + 応答候補絞り込み → v11.0.6-9 (v1106-v1109b) 全主題が loop に収束 (#L67) → 注意センター ESDE 本丸転換 (`07_addendum_v1105_to_attention_center.md`) → v1110-v1113 4 連続失敗 (異なる系の対応関係発想) → v1114 注意センター実装 Step 1+1b+2-A+2-B 完了 (familiarity_sizes 93.9% 解消、percept 配管確立) → **v12 Atomset 機構 (着手中、本書時点で M1 smoke 進行)**。

---

## 1. 主題系譜表 (v1100 - v1114、実コード確認済)

| Phase | バージョン | 主題 | 出口 / 結論 | outputs 規模 |
|---|---|---|---|---|
| v1100 | v11.0.0 | Language ↔ Genesis 接続事前調査 (6 候補) | Phase Result 未作成と判断 (Taka 2026-05-20)、両系の文脈非依存性は独立 atom を捕捉し Jaccard 0 | - |
| v1101 | v11.0.1 | Atom 的隆盛の統計的観察、一点を捉える観察 | 核心発見: 観察単位ごとに dominant atom が割れる、単一の答えがない (Atom 5 分裂) | 10 files |
| v1101a | v11.0.1.a | ESDE スケール注意機構 (像の差分 = 変化) | 段階 1: 意識優位時の注意候補波及が認知優位の 1.54-1.78 倍、段階 2: 波及増加は注意の動き、概念修正「注意の揺れと意識は別物」 | **131 files (大規模)** |
| v1102 | v11.0.2 | 条件が応答を変える: 受け手構造 × 時間スケール 2 次元観察 | CID 構成 node 数で応答 atom 像が階層的に反転、研究手法アップデート「際立ちの掬い取り」初本格適用 (47 records の極小構造を救う、#L14/L15/L16) | 3 files |
| v1103 | v11.0.3 | 段 4-c の点検: 48 次元密度の偏りは応答 Atom を絞れるか | 段 4-c は機構として動いた、ESDE と地続き (#L17)、決定機構が Aruism 内 (max_prob 0.7972)、会話への道が原理的に通った (慎重に言える)。**`atom_centroids_48d.parquet` を Code A が生成 (= v12 で流用)** | 6 files |
| v1104 | v11.0.4 | CID/IID 内部動作点検 段階 1 | 棚卸し 24 項目 → 8 → 4 項目に絞り込み (1.1/1.6/1.7/2.6)、Step H 初版 + H-3/H-4 再調査 (shuffle 種別で lift 0→0.17、scope-filter で r 0.157→0.42-0.48) | 13 files |
| v1104a | v11.0.4a | CID/IID 内部動作点検 段階 2 (scope × 層化) | 4 つの非対称性 #L30-L33 確定 (scope 別 chain 構造 / 粒度依存 trajectory-density 優劣逆転 / B 指標 scope 別 pattern / CID 100% self-loop が trajectory 構造的消失) | 7 files |
| v1105 | v11.0.5 | 段 4-b/4-c 統合点検、役割表まで | 5 役割 (候補保持 / 連想・踏み台 / 即時応答揺れ / 重要性 emit / 統合判断) を scope × 粒度に割り当てる役割表 (GPT 提案) | 4 files |
| v1105a | v11.0.5.a | 役割表を使って応答候補を絞る試行 (問いの形 B 切替、v1101 以来初) | (詳細は addendum 1 参照) | - |
| v1106 | v11.0.6 | Genesis 応答 Atom × Synapse 強度接続点検 | #L41 Synapse v3 weight=1.0 普遍化 | 7 files |
| v1106a/b | v11.0.6.a/b | mapper_output ベース新規 Synapse 接続 / 対話構造点検 | v1106b で **対話 loop が最初に顕在化** | - |
| v1107a/b/c | - | (詳細は addendum 1 参照、loop 関連) | - | 4 files (v1107c) |
| v1108a/b | - | 時間軸 + category 軸 (#L56-L60) | (詳細は addendum 1 参照) | 29 files |
| v1109/v1109b | - | 重み蓄積機構で loop 過剰化 0.964 (#L61-L64)、Grammar Exploration | 出口 A 0/5 (#L65 loop の幻 + CSG 撤回 + #L66 end_match loop 隠蔽 + **#L67 全主題が loop に収束 = 本期間最重要構造事実**) | 22 files |
| (注意センター転換) | - | #L67 受け 4 段階の外部接続フロー → 第 4 段階で「ループを崩す」は方向違いと判明 → Taka 本丸再確認 → 注意センター ESDE | Code A 技術的可能性 11 問すべて実現可能 (addendum 1 §11) | - |
| v1110-v1111e | - | Atom/Center/Other 3 instance pipe、別系注入 | **4 連続失敗** (番号コピー / step_window 呼び忘れ等) — 異なる系の対応関係発想の罠 | - |
| v1112 Stage 1 main/redo | - | 別系 occupancy phase 空間 cooc | 主指標 total_cooc が bin shift と数学的独立 / krandom 床で Stage 1 不成立 (測れた上での) | - |
| v1113 案 A/B | - | 別系 CID 特性 cosine | 案 A `engine.cog` 仮定で FAIL、案 B 完走するが per-seed 網羅で n_core=2 群 CV=0.086 = 背景由来 | - |
| **v1114 注意センター ESDE** | - | Step 1 (内部注意 287 records) + Step 1b (cid + 3 軸 383 records) + Step 2-A (生きた Center 443 records、familiarity_sizes 93.9%) + Step 2-B (Atom 経由注意、押し込まず) | 配管確認完了、formation_relation / lifecycle_phase は v105 hook で 100% 退化 (既知バグ保留)、応答 dynamics は Step 3 以降 | - |
| **v12 Atomset 機構 (現役、着手中)** | v12.0 | A 静的素質 + B 動的成長、頻度駆動 (Web Claude 設計書 2026-06-10) | M1 smoke 進行中 (本書時点)。M1 label に 2 key 追加 → M2 頻度集計 → M3 torque 接続 → M4 あり/なし比較 | - |

---

## 2. 残った資産 (v12 で流用)

### 2.1 atom 関連 (v12 Atomset の核心資産)

| 資産 | 場所 | v12 での使い方 |
|---|---|---|
| **`atom_centroids_48d_normalized.parquet`** (325 atoms × 48) | `unified/v1103/outputs/main/` | M2 で誕生時 rank_1 計算用 cosine sim の atom 側 |
| **`atom_centroids_48d_raw.parquet`** | 同上 | normalize 前 (raw_scores) 版、参考用 |
| **`cid_atom_sim_matrix_seed{N}.parquet`** (228 × 326、24 seeds) | `developmental/v106/outputs/main/` | v918 既存 baseline での cid × atom sim (古い baseline、v12 では参考のみ) |
| **`cid_atom_sim_matrix_v105today.parquet`** (228 × 325) | `unified/v1114/run_step2b/` | Step 2-B で再生成、v105-today baseline の cid sim (v12 では新規 main run で取り直し) |
| **v106 per-axis cid vector builders** (temporal/scale/.../value_generation) | `developmental/v106/v106_post_process.py:274-422` | M2 で誕生時 cid_vector 構築の素材 (v12 で関数だけ import) |
| **`esde_dictionary.json`** (326 atom + 10 axes + 48 sub-levels) | `language/atoms/` | atom 名 / sub-level 定義の正本 |
| **A1 mapper_output `*_a1.jsonl`** (325 atom × 単語、QwQ-32B 判定) | `language/lexicon/data/mapper_output/` | atom_centroids 生成の入力源 (再生成時) |

### 2.2 hook 経路 (v12 で流用)

| 資産 | 場所 | v12 での使い方 |
|---|---|---|
| **`apply_torque_only` の `cog_factor` 経路** (v9.7 既存、現在不使用) | `primitive/v910/virtual_layer_v9.py:432-441` | M3 で `atomset_factor` を乗算する雛形 |
| **Step 2-A monkey-patch 経路** (V82Engine + SubjectLayer + IntegrationManager + realizer.step) | `unified/v1114/step2a_live_observer.py` | M1 で再利用 (engine 捕捉 + 生きた run) |
| **v105_memory_readout.run() (案 b-1)** | `developmental/v105/v105_memory_readout.py` | M1 直接呼び (新規 main run、過去 output 不変) |

### 2.3 過去資産観察ベース (atom × cid の前例、v12 で再発明回避)

| 資産 | 場所 | v12 への含意 |
|---|---|---|
| atom_profiles_cache.npz (v1101a) | `unified/v1101a/` | CID に atom 由来属性を持たせる発想の前例 |
| observation_1_atom_profiles.parquet (v1108b) | `unified/v1108b/outputs/main/` | 325 atom × CID profile (静的) |
| v106 event_source_atom_distribution_seed{N}.csv | `developmental/v106/outputs/main/` | event 種別 × atom 分布 (= 「Atom 的因子の頻度」の前例) |
| v106 pulse_trajectory rank_1_atom | `developmental/v106/v106_pulse_trajectory.py:374` | per-pulse の dominant atom (= 頻度の Atom 変換の前例) |

---

## 3. 捨てたもの (v11 期で不採用 / 失敗 / 撤回)

### 3.1 4 連続失敗の枠組み (v1110-v1113)

「異なる系の対応関係を測る」発想 = 構造的失敗、`[[index-observation-target]]` で禁止リストに記録:

- **v1111c/d 番号コピー欠陥**: 別系の node ID を inject (Other は別 seed で無意味)
- **v1111e step_window 呼び忘れ**: Other.virtual.labels が空のまま注入
- **v1112 Stage 1 main**: total_cooc が bin shift と数学的独立 (測れない指標)
- **v1112 Stage 1 redo**: 一様乱数 self 床が実機 sparse occ と閾値挙動桁違い (krandom 床は PASS したが Stage 1 不成立)
- **v1113 案 A**: `engine.cog` 仮定で AttributeError (SubjectLayer は run() 内ローカル変数、Explore agent 結果を実機検証せず)
- **v1113 案 B**: per-seed 網羅で n_core=2 群 CV=0.086 = 背景由来 (= 異なる seed の系は独立な動学、対応関係はそもそも存在しない)

### 3.2 撤回された主題 / 仮説

- **#L61-L64 重み蓄積機構で loop 過剰化 0.964**: v1109 で confidence 高めに記録したが、過剰化として #L65/#L66 で撤回
- **CSG (Constrained Set Grammar)**: v1109b で撤回 (#L65 loop の幻)
- **end_match loop**: v1109b で loop 隠蔽として認識 (#L66)
- **48 次元の「測定」解釈**: v1103 留保 #L18 で「両端で人工 (LLM 判定 + Web Claude 手定義)、測定でなく定義/判定」と確定

### 3.3 V12 で踏まない罠 (Code A 自己強制ハードル、`feedback_code_a_blind_spots.md`)

- #1 配管の足の数 2 本誤認 (3 instance pipe を入口/出口で読む)
- #9 多 engine pipe で step_window 呼び忘れ
- #11 集計指標が処置と数学的独立
- #12 null 設計を自身 shuffle にすると「皆同じだから似てる」を引き算できない
- #13 集団平均の罠 (per-x / 層別なし)

→ v12 では cid_atom_sim_matrix の 326 次元を「合成指標」に畳まない (Atomset 設計書 §4.1 規律)。

---

## 4. v12 で流用する資産 (整理、設計書 §3 と整合)

| 資産 | v12 での具体的用途 |
|---|---|
| atom_centroids_48d_normalized (325 atoms × 48) | M2 で誕生時 cid 特性から 48 次元 cid_vector を build → atom_centroids との cosine → rank_1 atom を atomset_seed に設定 |
| v106 build_cid_vector (per-axis builders) | M2 で生きた run 中の cid 特性 (per_subject + audit) から 48 次元 vector を構築する関数 |
| v9.7 cog_factor 経路 (apply_torque_only) | M3 で `atomset_factor = 1.0 + atomset_bonus` を torque_mag に乗算する 1 行追加経路 |
| Step 2-A monkey-patch (SubjectLayer/IntegrationManager/realizer.step) | M1-M4 で v105 main run の per-10step hook + 内部 state 捕捉 |
| Step 2-A familiarity_sizes 取得経路 (cog.familiarity[cid].keys() + v11_m_c[partner]['n_core']) | M2 で frequency 集計時に per-cid context 取得 (= 補助情報) |

---

## 5. 正直な現在地 (本書時点、Code A 状況)

### 5.1 完了したもの

- v1100 - v1104a: Phase Result 完成 (5 本)、`07_unified_summary.md` 本体に反映
- v1105 - 注意センター転換: addendum 1 (`07_unified_summary_addendum_v1105_to_attention_center.md`)
- v1110 - v1114 Step 1+1b: addendum 2 (`07_unified_summary_addendum_2_attention_center_internal.md`、Code A 作成)
- v1114 Step 2-A (生きた Center 観察基盤): 443 records, familiarity_sizes 93.9%
- v1114 Step 2-B (Atom 経由注意、配管確認): 修正 A+B 反映済み

### 5.2 進行中

- **v12 Atomset M1 smoke (本書時点で実行中、推定 12-15 分)**: label に atomset_seed/bonus 追加 + 完走 + 発散なし確認
- v12 Atomset 設計書 (Web Claude 2026-06-10) 受領済み、M1-M4 段取り確定

### 5.3 保留 / 未完

- formation_relation / lifecycle_phase (Step 2-A の percept 軸): v105 hook で 100% 退化 (既知バグ保留、Step 1b は取れてた)
- §3 自己擦り込み (Step 2-A 設計外): Taka 判断待ち (Center が注意で何を *する* かのフォーク)
- 入力テキスト → Atom (LLM 経由の穴): Atom 手置きで代用中

### 5.4 v12 への接続

Atomset 機構 v12 (Web Claude 設計書):
- A 静的素質 + B 動的成長 (頻度駆動) + C torque 接続
- Frozenset (apply_torque_only) と同レイヤー、物理層触らず
- 新規 main run、過去 output 不変 (新世代 ESDE)
- 判断基準は一本「CID の個性化を促進するか」

→ **v1114 Step 2-B (Atom 経由注意の配管確認) で確立した「Atom と CID の橋」を、v12 で動学に接続**。Step 2-B では Atom 手置きで CID を引く配管のみ、v12 で CID 内に Atomset として組み込み、torque を通じて振る舞いに影響させる。

---

## 6. Web Claude Phase Result 一本化への素材

本書を素材として、Web Claude が v11 全体 Phase Result を以下の構成で書ける見込み:

1. ひとことサマリ (v11 → v12)
2. 主題系譜 (本書 §1 表)
3. 確定観察 / 留保番号一覧 (#L14 - #L67)
4. 残った資産・捨てたもの (本書 §2-3)
5. v12 への接続 (本書 §4-5)

詳細データは git history + 各 v110x/outputs/ + 各 phase_design.md / step_*_observation_final.md に存在、本書はその index。

---

*以上、Code A による v11 (v1101-v1114) 棚卸しメモ (2026-06-10、smoke 待ち時間並行作業)。Web Claude Phase Result 一本化の素材としても利用可。v12 着手の現在地と流用資産を明示。*
