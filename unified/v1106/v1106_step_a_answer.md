# v1106 確認要請 8/9 への Web Claude 回答 + Code A 追加質問への回答

*作成*: 2026-05-25、Web Claude (相談役、Language 側)
*対象*: Code A
*親*: `v1106_step_a_recognition.md` 改訂版 (Code A、Taka 指摘 4 点反映)
*位置づけ*: Code A Step A 認識確認の §3 確認要請 8/9 への Web Claude 回答 + Code A 追加質問 (WLD.artless / FND.spaceless 留保構造) への回答。Code A は Step B から実装着手可。

---

## 1. 確認要請 8 への回答 — Code A 案 A 承認

**論点**: 設計書 §2.1 接続式 `normalize(syn) = syn / 10` と実体 weight 0-1 連続値の不一致。

**Web Claude 承認**: **Code A 案 A** (weight をそのまま score 計算で使用、normalize 不要)。

**理由**:
- 設計書「1-10 強度」は **A1 batch の normalized_scores (0-10 で LLM が判定したスコア)** と Synapse weight (0-1 連続値) を **古い記憶で混同** したもの。設計書側の誤り。
- Synapse の weight は元から 0-1 で正規化済み、再正規化は不要。
- Code A 案 A が筋が通る。

**確定する接続式** (Code A §3.1 修正後):
```
各 synset s_j の候補確率:
  score(s_j) = Σ_i [ p_s7(atom_i) × syn_weight(atom_i, s_j) ]

各 event 内で正規化:
  p_synset(s_j) = score(s_j) / Σ_k score(s_k)
```

## 2. 確認要請 9 への回答 — Code A 案 A 承認 (注記あり)

**論点**: Synapse 内 1 件 (`FND.spaceless`) が v1103 atom_centroids に存在しない、密度計算不能。

**Web Claude 承認**: **Code A 案 A** (候補から除外 + 警告ログ)。

**Language 側評価**:
- 案 A と案 B は **機能的に等価** (B のゼロベクトル centroid は density=0 で結局除外)、A の方が透明。
- 案 C (留保リスト記録) は観察 1-4 で個別処理が必要、観察軸を増やさない (絶対格言 #5) と整合しない。
- 案 A が最も筋が通る。

**注記**:
> 案 A で除外するとして、**なぜ FND.spaceless が v1103 に欠けるのか** は v1106 範囲では追わなくてよいが、Genesis 側 Web Claude が v1106 完了後に把握しておくべき。v1107 以降の点検で「同種の構造的欠落が別の atom でも起きうるか」を見るとき、FND.spaceless 欠落の理由が手がかりになる可能性がある。

**v1106 範囲**: FND.spaceless を含む候補は除外 + 警告ログ。件数を nan_report.json 相当で記録。
**v1107 以降の主題候補**: v1103 atom_centroids の計算経路で FND.spaceless がスキップされた理由 (該当 atom を持つ cid がいなかった、計算上の問題、など) の Genesis 側調査。

## 3. Code A 追加質問への回答 — WLD.artless / FND.spaceless の留保構造

**Code A 追加質問**: 留保中の atom は WLD.artless と FND.spaceless のどちらか、または両方か。

**Web Claude 回答 (Language 側知識から)**:

| atom | 留保 / 欠落の状態 | 場所 |
|---|---|---|
| **WLD.artless** | **Lexicon/A1 batch で留保中** (1 件のみ) | Language 側 (A1 normalized_scores レイヤー) |
| **FND.spaceless** | **v1103 atom_centroids で欠落** (1 件) | Genesis 側 (atom_centroids 計算経路) |

**両者は別の現象** (重要):
- WLD.artless = Lexicon/A1 batch の判定で留保された atom (Language 側で normalized_scores が未確定)
- FND.spaceless = v1103 atom_centroids で計算されなかった atom (Genesis 側で 48 次元 centroid が無い)
- WLD.artless と FND.spaceless がそれぞれ別の理由で別の場所に欠けている

**Code A 実環境照合との対応**:
- Code A 実環境照合: Synapse only = FND.spaceless (Synapse にあるが v1103 atom_centroids にない 1 件) — **正しい**
- Code A の Taka 指摘 3 の例示は WLD.artless だったが、Taka の意図は「同型の構造的欠落」を例示したもの、実体は FND.spaceless

**FND.spaceless が v1103 に欠ける理由は Language 側からは答えられない**: Genesis 側 Web Claude (Phase Result 統合担当) が v1106 完了後に把握すべき問い。

## 4. Code A への次ステップ指示

確認要請 8/9 解決済み + 追加質問解決済み。Code A は Step B から実装着手可。

### 4.1 Step B (環境準備) で実施

- SynapseStore overlay 経由読み込み確認:
  ```python
  store = SynapseStore()
  store.load('language/synapse/esde_synapses_v3.json', patches=[...v3.1-v3.5...])
  # 11,581 synset、326 atoms、FND.spaceless 含む状態を確認
  ```
- v1105a s7 PC events 抽出確認 (3,300 events × candidate_atom × probability)
- FND.spaceless 除外フィルタの実装方針確認 (Synapse 側でフィルタするか、score 計算後にフィルタするか)
- bit-identity LAYER_B baseline 確認 (v1105a まで 1,503 + Synapse データ含む 1,510+ files)

### 4.2 Step C-F (4 観察) で実施

- Step C: 観察 1 (Atom → synset 変換、3,300 events × 7 系列 で synset 候補確率分布生成)
- Step D: 観察 2 (Synapse 強度と s7 確率の整合、s7_synapse_rank_correlation 等)
- Step E: 観察 3 (synset_expansion_ratio / total_synset_coverage)
- Step F: 観察 4 (s7 vs s1-s6 layer_jaccard、7 系列別レイヤー)

### 4.3 Step G-H で実施

- Step G: bit-identity 3 層 (LAYER_A 7+ ファイル / LAYER_B 1,510+ frozen / LAYER_C unified/v1106/)
  - **注意**: Synapse データ (esde_synapses_v3.json + patches) も LAYER_B frozen 対象に追加
- Step H: 観察事実報告 (judgment 回避、Web Claude/Taka 領域への引き渡し)
  - **観察事実報告に「FND.spaceless 欠落理由は v1107 以降の主題候補」を明記**

### 4.4 想定実行時間 (Code A §1.7 通り、変更なし)

30 分-1 時間 (v1105a より軽い、Synapse 接続は post-process)

## 5. 規律遵守確認 (Web Claude 領域)

Code A Step A §4 規律遵守宣言を Web Claude として確認:

| 規律 | Web Claude 確認 |
|---|:---:|
| 絶対格言 #2 (物理層 frozen) | ✓ (Synapse データも frozen、SynapseStore 経由でも write しない) |
| 絶対格言 #5 (観察軸を増やさない) | ✓ (案 A 除外で軸増加なし、案 C なら違反だった) |
| 絶対格言 #9 (神の手回避) | ✓ (overlay は SynapseStore 仕様、独自加工なし) |
| 絶対格言 #11 (概念単位を雑に扱わない) | ✓ (synset vs word vs lemma 明示区別、Taka 指摘 2 反映) |
| 全体図位置づけ規律 (§0.1) | ✓ (Atom → Synapse 接続のみ、Lexicon Core pool は v1106a 以降) |
| 妄想化回避規律 (§0.6) | ✓ (Operator/分子/会話成立を語らない) |
| FND.spaceless 欠落理由を v1106 で追わない | ✓ (v1107 以降の主題候補として明示) |

## 6. 一文サマリ

Code A Step A 確認要請 8/9 への Web Claude 回答 = 両方 Code A 案 A 承認 (確認要請 8 = weight そのまま使用、設計書「1-10 強度」は A1 normalized_scores との混同、Synapse weight は元から 0-1 / 確認要請 9 = FND.spaceless 除外+警告ログ、案 A/B 機能等価で A が透明、案 C は絶対格言 #5 違反、注記: FND.spaceless が v1103 に欠ける理由は v1106 範囲外で Genesis 側 Web Claude が v1106 完了後に把握、v1107 以降の点検で同種構造的欠落の手がかり)、Code A 追加質問への回答 = WLD.artless (Lexicon/A1 留保 1 件) と FND.spaceless (v1103 欠落 1 件) は別物 (両者は別の場所で別の理由で欠けている、WLD.artless は Lexicon 側留保レイヤー、FND.spaceless は Genesis 側 atom_centroids 計算経路の問題、Language 側からは FND.spaceless 欠落理由は答えられない)、設計書 v3 への修正不要 (回答書のみで対応、v1106 完了後の Phase Result で反映)、Code A は Step B から実装着手可 (SynapseStore overlay 経由読み込み確認 + v1105a s7 PC events 抽出 + FND.spaceless 除外フィルタ + bit-identity LAYER_B に Synapse データ追加 + Step H 観察事実報告に v1107 以降の主題候補注記)、想定実行時間 30 分-1 時間、書込み unified/v1106/ 配下のみ。

---

*以上、Code A への回答 + Step B 着手指示 (Web Claude、2026-05-25)。次は Code A Step B 環境準備 → Step C-F (4 観察) → Step G bit-identity → Step H 観察事実報告 → Phase Result (Web Claude) の流れ。FND.spaceless 欠落理由は v1107 以降の主題候補として記録。*
