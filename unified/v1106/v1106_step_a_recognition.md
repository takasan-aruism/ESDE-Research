# v11.0.6 (v1106) Step A 認識確認 — Code A

*作成*: 2026-05-25、Code A
*改訂 1*: 2026-05-25、Taka 指摘 4 点反映 (overlay 必須 / synset vs word 単位 / atom 1 件ズレは FND.spaceless / Lexicon Core pool は別物)
*親*: `v1106_phase_design.md` (Web Claude 設計書、GPT 監査クリア + Taka 確定「Gemini 不要」)
*対象*: Web Claude (相談役) + Taka (主題判断者)
*位置づけ*: v1106 進行表 Step A (Code A 認識確認 + 実環境照合 + Web Claude/Taka 領域への確認要請 2 件)。判定は行わず、観察手順の実装可能性と確認要請に限定。

---

## 0. 一文サマリ

v1106 設計書 (Synapse 接続点検、問いの形 A 復帰、GPT 監査クリア) を Code A 受領、実環境照合の初版で SimpleSynapseLoader / SynapseStore overlay を経由せず esde_synapses_v3.json を直接読んでいた誤りを Taka 指摘で修正、改訂版で **SynapseStore + v3.1-v3.5 patches overlay 適用後の最新状態 (v3.5 凍結時点)** を照合: **11,581 synset** (overlay 適用、+82 add / -10 disable / 9 overwrite / 10 disable_wins)、**5,840 unique lemma** (synset と word は別単位、Lexicon 32,666 word とも別物、Taka 指摘 2 反映)、**326 atoms used**、v1103 atom_centroids 325 との差分 1 件は **FND.spaceless** (Synapse only、v1103 atom_centroids に存在せず 48 次元座標引けない、Taka 指摘 3 反映 = WLD.artless ではなく実体は FND.spaceless)、**1 synset → 1-7 atoms** (overlay で max=3 → max=7 に拡大、mean 1.93)、**1 atom → 13-181 synsets** (mean 68.4 = Synapse 逆引き、Lexicon Core pool atom → word 直接の ~100 word/atom とは別物、Taka 副次指摘反映)、**weight 連続値 0-1** (mean 0.52、設計書「1-10 強度」と不一致)、Web Claude/Taka 領域への確認要請 2 件提示: 確認要請 8 (接続式 §2.1 normalize(syn)=syn/10 と実体 weight 0-1 連続値の不一致、Code A 推奨案 A weight そのまま使用)、**確認要請 9 (新規、FND.spaceless 扱い方針) Code A 推奨案 A 候補から除外 + 警告ログ (centroid 不在で密度計算不能、観察 3 候補爆発回避にも貢献)、案 B ゼロベクトル centroid 仮定 (全 atom と直交、density 0、score=0 で実質除外)、案 C 留保リストとして記録のみ (候補に残すが各観察で個別扱い)**、§5-1〜7 への回答 (1: SynapseStore + esde_synapses_v3.json + patches v3.1-v3.5 overlay 必須 / 2: v1105a outputs main / 3: atom 1 件ズレ FND.spaceless 扱い確認要請 9 / 4: 接続式は確認要請 8 後に確定、計算量 ~10M synset ペア / 5: synset_expansion_ratio = n_synsets_after / n_candidates_after、total_synset_coverage = n_synsets_after / 11,581 (実体合わせ) / 6: 接続条件 4 点は Web Claude/Taka 領域 / 7: 想定 30 分-1 時間)、Step B-H 想定実行時間 + 規律遵守宣言 (絶対格言 #2/#6/#9/#11/#12 + 試行 ≠ 会話成立判定 + 妄想化回避 + Synapse データ frozen + 書込み unified/v1106/ 配下) を完了、確認要請 8/9 回答受領後に Step B から実装着手予定、書込み unified/v1106/ 配下のみ。

---

## 1. §5 Code A 確認要請 1-7 への認識 (Taka 指摘反映改訂版)

### 1.1 §5-1: Synapse データの所在と読み込み方 (Taka 指摘 1: overlay 必須)

**実環境照合結果 (改訂、SynapseStore overlay 経由)**:

| ファイル | 所在 | 役割 |
|---|---|---|
| `esde_synapses_v3.json` | `language/synapse/` (5.5 MB) | Base JSON、11,557 synset 初期状態 |
| `synapse_v3.1.json` 〜 `v3.5.json` + `v3.3_hotfix.json` | `language/synapse/patches/` | overlay patches (6 ファイル) |
| `store.py` (SynapseStore class) | `language/synapse/` | Overlay 適用ローダ (Phase 8 Sensor + Observation C + Phase 7 Engine 共通) |

**最新状態の正しい読み込み方** (Taka 指摘 1 反映、SynapseStore Spec v2.1):
```python
from language.synapse.store import SynapseStore
store = SynapseStore()
store.load('language/synapse/esde_synapses_v3.json', patches=[
    'language/synapse/patches/synapse_v3.1.json',
    'language/synapse/patches/synapse_v3.2.json',
    'language/synapse/patches/synapse_v3.3.json',
    'language/synapse/patches/synapse_v3.3_hotfix.json',
    'language/synapse/patches/synapse_v3.4.json',
    'language/synapse/patches/synapse_v3.5.json',
])
# overlay 後の synapses: 11,581 synset (+82 add - 10 disable + 9 overwrite + 10 disable_wins)
```

**Code A 初版の誤り**: esde_synapses_v3.json を直接読んでいた = **v3.5 凍結時点の最新ではない**。v1106 実装では SynapseStore 経由を必須とする。

### 1.2 Synapse 構造統計 (Taka 指摘 2 反映、synset 単位明示)

| 項目 | 値 | 注記 |
|---|---:|---|
| **synset 件数** (overlay 適用後) | **11,581** | lemma.pos.sense 形式 (WordNet synset)、設計書「約 2 万 word」≠ 実体 |
| **unique lemma 数** (Taka 指摘 2 概算) | **5,840** | synset / lemma 比 1.98 (1 lemma あたり ~2 synset) |
| **Lexicon 全 word 数** (Taka 指摘 2 比較) | 32,666 | Synapse とは別物、後段で Lexicon Core pool として接続 |
| atoms used | 326 | overlay 後も同じ |
| 1 synset → atoms | mean 1.93, median 2, **max 7** (overlay で 3 → 7 拡大) | min 1 |
| 1 atom → synsets (Synapse 逆引き) | mean **68.4**, max 181 | Taka 副次指摘: Lexicon Core pool atom → word 直接 ~100 word/atom と別物 |
| weight 連続値 | 0-1 (min 0.0065, max 1.0, mean 0.518) | 設計書「1-10 強度」と不一致 (確認要請 8) |
| rank | 1-3 (1 synset 内 atom 順位) | overlay 後も同じ |

**Patch overlay 効果**:
- edges_added: 82
- edges_disabled: 10 (tombstone)
- conflicts_overwrite: 9
- conflicts_disable_wins: 10

### 1.3 §5-2: v1105a s7 出力の読み込み方 (変更なし)

| ファイル | 所在 | 内容 |
|---|---|---|
| `trial_step4_distributions.parquet` | `unified/v1105a/outputs/main/` | 206,900 rows、構造ラベル付き 7 系列確率分布 |

s7 (48D raw_density k=5) pipeline_complete events 抽出:
```python
dist = pd.read_parquet('trial_step4_distributions.parquet')
s7_pc = dist[(dist['series_id'] == 's7_48d_raw_k5') &
              (dist['structural_label'] == 'distribution_valid')]
```

### 1.4 §5-3: atom_id ↔ Synapse atom_id mapping (Taka 指摘 3 反映)

**実環境照合結果 (改訂)**:

| 集合 | 件数 | 内容 |
|---|---:|---|
| v1103 atom_centroids_48d_raw | 325 | 48 次元 centroid 利用可能 |
| Synapse atoms used (overlay 後) | 326 | |
| 完全一致 | 325 | |
| **Synapse only (v1103 にない)** | **1 件 = `FND.spaceless`** | 51 synset が指し示す可能性あり (今回照合は **WLD.artless** 含む全 atom に対し centroids 存在確認、WLD.artless は v1103 にあり) |
| v1103 only (Synapse にない) | 0 件 | |

**Taka 指摘 3 への補足**: Taka が例示した「WLD.artless 留保中」は私の照合で **WLD.artless は v1103 atom_centroids にも Synapse にも両方存在** していた。**実体で 1 件ズレているのは `FND.spaceless`**。Taka の挙げた留保問題と同型の構造 (Lexicon/A1 で留保中の atom が Synapse のみに存在し v1103 centroid 引けない) で、対象が異なるだけ。

→ 確認要請 9 (新規) で FND.spaceless の扱い方針を確定する必要。WLD.artless が留保リストにあるかどうかは確認要請として Web Claude/Taka に確認。

### 1.5 §5-4: 接続式 §2.1 の妥当性 (確認要請 8、変更なし)

設計書 §2.1 の `normalize(syn) = syn / 10` は **実体 weight が 0-1 連続値であることと不一致**。詳細は §3 確認要請 8。

**計算量見積もり (改訂)**:
- pipeline_complete events: 3,300 × 7 系列 = 23,100 event-series
- per event-series: candidate atoms (mean ~6) × synsets per atom (mean 68) = ~408 synset 候補
- 合計 synset 候補計算: 23,100 × 408 ≈ **9.4M ペア** (動的計算可能、数十秒-数分)

### 1.6 §5-5: synset_expansion_ratio / total_synset_coverage (Taka 指摘 2 反映、word → synset 単位修正)

**Code A 実装方針** (改訂、単位修正):
- `synset_expansion_ratio` = n_synsets_after / n_candidates_after (per event-series)
- `total_synset_coverage` = n_synsets_after / **11,581 (synset 全体、overlay 後)**

設計書 §2.4 の「word_expansion_ratio」「total_word_coverage」「2 万 word」は実体 **synset 11,581** に再定義。設計書 §0.1 図の Synapse は単語マッピングだが、実体は synset (WordNet sense) 単位なので、v1106 内ではすべて synset 単位で記述する。

Lexicon Core pool (32,666 word、atom → word 直接) は v1106 では使わない (これは v1106a 以降の段 5a Atom → word で使う構造、Taka 副次指摘)。

### 1.7 §5-6: v1106a 接続条件 4 点の操作的閾値 (synset 単位修正)

**Code A 実装方針** (構造ラベル付与、v1105a §1.1 継承):

| ラベル (改訂) | 操作的条件 |
|---|---|
| `synset_candidate_empty` | n_synsets_after == 0 |
| `synset_distribution_degenerate` | synset_max_prob ≥ 0.999 OR synset_prob_ge_0.999_count > 0 |
| `synset_distribution_valid` | synset_max_prob < 0.999 AND synset_entropy > 0 |
| `synset_pipeline_complete` | synset_distribution_valid 達成 |

設計書 §2.7 v1106a 接続条件 4 点の「word_pipeline_complete」「word_distribution_valid」「word_expansion_ratio」は synset 単位に統一する。Web Claude/Taka 領域での判定基準は変わらない (3 条件以上 → v1106a、2 条件以下 → v1106b)。

### 1.8 §5-7: 想定実行時間 (変更なし)

| Step | 想定実行時間 |
|---|---:|
| B 環境準備 | < 1 分 |
| C 観察 1 (Atom → synset 変換) | 数分 |
| D 観察 2 (Synapse 強度と s7 確率の整合) | 数分 |
| E 観察 3 (synset_expansion_ratio / total_synset_coverage) | 数分 |
| F 観察 4 (s7 vs s1-s6 layer_jaccard) | 数分 |
| G bit-identity 3 層 | 数十分 |
| H 観察事実報告 | — |

合計想定 **30 分-1 時間**。

---

## 2. 実装可能性 (変更なし)

| Step | 実装可能性 |
|---|:---:|
| B | ✓ |
| C-F | ✓ (確認要請 8/9 後) |
| G | ✓ |
| H | ✓ |

---

## 3. 確認要請 (Web Claude/Taka 領域)

### 3.1 確認要請 8 — 接続式 §2.1 weight 処理

(初版から変更なし、再掲)

**論点**: 設計書 §2.1 接続式 `normalize(syn) = syn / 10` は実体 weight 0-1 連続値と不一致。

**Code A 推奨**: **案 A** (weight をそのまま score 計算で使用、normalize 不要)。

**修正後の接続式**:
```
各 synset s_j の候補確率:
  score(s_j) = Σ_i [ p_s7(atom_i) × syn_weight(atom_i, s_j) ]
  (weight は既に 0-1 範囲、normalize 不要)

各 event 内で正規化:
  p_synset(s_j) = score(s_j) / Σ_k score(s_k)
```

### 3.2 確認要請 9 (新規、Taka 指摘 3 反映) — FND.spaceless の扱い

**論点**: Synapse 内に 1 件 (`FND.spaceless`) が v1103 atom_centroids に存在しない。Synapse から FND.spaceless が出る synset (51 件) を含む word 候補計算で **48 次元 centroid を引けず density 計算不能**。

**実体**:
- FND.spaceless を指す synset: 51 件 (sample: prioritize.v.01, artistic.a.01, object.n.01, design.v.02, purpose.n.01)
- s7 PC 3,300 events の input atom 25 種に FND.spaceless が含まれるかは Step B 環境準備で確認 (含まれない場合は Step 2 連想で出てこない可能性高)

**Code A 案 3 つ**:

| 案 | 内容 | 利点 | 欠点 |
|---|---|---|---|
| **案 A (Code A 推奨)** | FND.spaceless を候補から除外、警告ログ記録 | 単純、density 計算不能を回避、候補爆発抑制効果 | Synapse の atom を 1 件捨てる |
| 案 B | ゼロベクトル centroid を仮定、density 計算 (全 atom と直交 → density 0 で実質除外) | 候補リストに残るが score=0 で結局除外、frozen 維持 | 計算上は処理可能、結果として除外と同じ |
| 案 C | 候補に残し各観察で個別扱い (留保リストとして記録) | 全情報保持 | 観察 1-4 で何度も個別処理が必要、複雑 |

**Code A 推奨**: **案 A** (除外 + 警告ログ)。FND.spaceless を含む結果は構造ラベル付与時に観察対象外、件数を nan_report.json に記録。

**追加質問** (Taka 指摘 3 への確認): 留保中の atom は WLD.artless と FND.spaceless のどちらか、または両方か。実環境照合では FND.spaceless のみが Synapse - v1103 差分だが、WLD.artless が将来留保候補となる可能性も含めて Web Claude/Taka に確認。

---

## 4. 規律遵守宣言 (Step A 範囲、改訂)

| 規律 | 遵守 |
|---|:---:|
| 絶対格言 #2 (物理層 frozen) | ✓ (Synapse データも read-only、SynapseStore 経由でも write しない) |
| 絶対格言 #5 (観察軸を増やさない) | ✓ (FND.spaceless 扱い案 A は除外で軸増加なし) |
| 絶対格言 #9 (神の手回避) | ✓ (overlay 適用は SynapseStore 仕様通り、独自加工なし) |
| 絶対格言 #11 (概念単位を雑に扱わない) | ✓ (synset vs word vs lemma を明示区別、Taka 指摘 2 反映) |
| 絶対格言 #12 (judgment 回避) | ✓ (success/failure 未使用、構造ラベルのみ) |
| 全体図位置づけ規律 (§0.1) | ✓ (Atom → Synapse 接続のみ、Lexicon Core pool は v1106a 以降) |
| 妄想化回避規律 (§0.6) | ✓ (Operator/分子/会話成立を語らない) |
| LLM プロキシ呼び出し禁止 | ✓ |
| Synapse データ frozen + overlay 仕様 | ✓ (SynapseStore 経由 + patches read-only) |
| 接続式独自発明禁止 | ✓ (案 A は実体合わせの微修正) |
| 書込みパス unified/v1106/ 配下 | ✓ |
| smoke 含めず | ✓ |

---

## 5. Step A 完了後の進行 (確認要請 8/9 への Web Claude/Taka 回答受領後)

1. **確認要請 8 回答**: 接続式 weight 処理確定 (Code A 推奨案 A = そのまま使用)
2. **確認要請 9 回答**: FND.spaceless 扱い確定 (Code A 推奨案 A = 除外 + 警告)
3. 回答受領後 Step B から順次実装:
   - Step B (環境準備、SynapseStore overlay 確認)
   - Step C-F (4 観察)
   - Step G (bit-identity 3 層)
   - Step H (観察事実報告)

---

## 6. 一文サマリ (再掲)

v1106 設計書 Step A 認識確認の初版で esde_synapses_v3.json 直接読みで v3.5 overlay 未経由・word vs synset 単位混同・atom 1 件ズレ未明示の 3 誤りを Taka 指摘で改訂、改訂版で SynapseStore + v3.1-v3.5 patches overlay 経由で正しく照合 (11,581 synset / 5,840 lemma / 326 atoms used / overlay +82 add - 10 disable / atoms per synset max 3 → 7 拡大 / weight 0-1 連続値 mean 0.518)、v1103 atom_centroids 325 と Synapse atoms 326 の差分 1 件は **FND.spaceless** (Taka 指摘 3 が例示した WLD.artless ではなく実体は FND.spaceless、Lexicon/A1 留保中の atom が Synapse のみ存在し v1103 centroid 引けない構造)、Lexicon Core pool 32,666 word (atom → word 直接) は v1106 範囲外で v1106a 以降の段 5a で使用 (Taka 副次指摘反映)、Web Claude/Taka 領域への確認要請 2 件 (8 接続式 weight 処理 = Code A 案 A そのまま使用、9 新規 FND.spaceless 扱い = Code A 案 A 除外+警告) 提示、§5-1〜7 への回答 + synset 単位への用語修正 (word_expansion_ratio → synset_expansion_ratio、total_word_coverage → total_synset_coverage、word_pipeline_complete → synset_pipeline_complete) + Step B-H 想定実行時間 (30 分-1 時間) + 規律遵守宣言 (絶対格言 #2/#5/#9/#11/#12 + 全体図位置づけ + 妄想化回避 + Synapse データ frozen + SynapseStore 仕様遵守) を完了、確認要請 8/9 回答受領後に Step B 着手予定、書込み unified/v1106/ 配下のみ。
