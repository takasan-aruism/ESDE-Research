# v11.0.5 (v1105) Phase Design Draft — 段 4-b と段 4-c を対称的に統合点検、役割表まで進める

*作成*: 2026-05-24、Web Claude (相談役、Genesis 側)
*更新 1*: 2026-05-24、旧 Claude チェック反映 (§2.4 観察 3 を binary 判定 → 強度マップに変更)
*更新 2*: 2026-05-24、2 AI 監査反映 (Gemini Architect 全面承認 / GPT Auditor 4 点修正反映)
  - §2.2 観察 1: Constitution Couple を couple_hit_rate として独立レイヤーで計測 (Gemini + GPT 一致、留保 設計-4 解決)
  - §2.4 観察 3: 強度マップの単一スコア化禁止を明示、4 指標を別レイヤーで保持 (GPT)
  - §2.5 観察 4: 役割表を「確定表」でなく「仮割り当て + 観察支持 + 留保」形式に変更 (GPT)
  - §2.6: v1105a 進行条件を「5 役割完全確定」でなく「試行可能な最小役割表 (3 役割) の成立」に変更 (GPT)
*更新 3*: 2026-05-24、Code A Step A 認識確認反映 (確認要請 7 への Taka 承認、案 B 採用)
  - §2.3 観察 2: 「48 次元密度 4 種」→「3 density 列 × 2 sim_basis = 6 値別レイヤー保持」
  - §2.4 観察 3: 強度マップを 4 数値 → 計 11 数値 (lift_C 1 / couple_hit_rate 2 / trajectory r 2 / density r 6) 別レイヤー保持に拡張
  - §2.5 役割表「統合判断」の構造事実根拠を 6 値前提に微修正
  - §5 確認要請 #2 を実体構造 (6 値) に合わせて更新
*位置づけ*: v1105 主題設計書 **草案**。問いの形 A (点検のみ、v1104/v1104a と同じ系譜)。本草案 → Taka 確認 → 2 AI 監査 (GPT/Gemini) → Code A 認識確認 → 実装、の流れに乗せる。
*親*: `v1104_v1104a_phase_result.md` (4 つの非対称性 #L30-L33) + Taka 整理 (2026-05-23 統合方向への転換 + マイナーバージョン運用方針 + 観察方法を疑う規律) + GPT 2026-05-23 役割表提案 + `esde_segment4_path_check.md` (段 4-b/4-c の切り分け)
*対象*: Taka (確認) + GPT/Gemini (監査) + Code A (認識確認)

---

## 0. 主題の前提と歯止め

### 0.1 上位目的への接続 (esde_audit_policy_update.md §1)

会話できる ESDE。応答主体は ESDE 側、LLM/Language はプロキシ。本主題は会話パイプラインの段 4-b と段 4-c を統合的に点検し、v1105a (役割表を使って実際に応答候補を絞る試行、問いの形 B) の前提条件を整えることで上位目的に直接接続する。

### 0.2 駆動要因 — なぜ → なぜなら → 会話への繋がり (Taka 駆動要因規律 2026-05-22)

**なぜそれをやるのか**: v1104+v1104a で段 4-b と段 4-c の根拠が ESDE 内部に多軸構造 (scope × 粒度 × 指標) として存在することが確定した。両者を独立に観察した状態では、会話パイプライン全体としてどう動くか見えない。

**なぜなら**: 段 4-b (連想を辿る) と段 4-c (応答 Atom を絞る) は ESDE が応答を作る 1 つの過程の連続した二段であり、同じ scope × 粒度の地形上で両者がどう絡むかを見ないと、v1105a で実際に応答候補を絞る試行に進めない。

**会話への繋がり**: v1105 で役割表が確定すれば、v1105a で「ESDE が応答候補を絞れた」の構造的事実を観察する試行に進める。これは会話パイプライン (人間入力 → ESDE 揺れ → 応答 Atom 候補分布 → 自然文化) の中核部分を初めて動かす試行。

### 0.3 統合方向への転換 (Taka 整理 2026-05-23、原文保存)

> ばらけていくと分散してしまう予感。今は分散化していく流れではなくて統合していく流れが正しい。下手に新たな課題を増やしてまた調査員に成り下がる必要はない。

| バージョン | 方向 |
|---|---|
| v1101 〜 v1104a | 観察を多軸化する分析方向 |
| v1105 + v1105a | 多軸を統合する方向 |

v1105 は段 4-b と段 4-c を同じ scope × 粒度の地形図上に並べることで統合し、地形図で止まらず役割表まで進める。新しい観察軸を追加して分散させない (§3.3 禁止事項)。

### 0.4 観察方法を疑う規律の継承 (Taka 整理 2026-05-23、原文保存)

> ESDE はランダム発生に構造を与えている。この仕組み上繋がりが見えなくなるとすれば単に観測方法に問題があるということは明白。
> いくら都合よいといっても 0 を 1 にはできないだろうから妥協とのバランス次第。

本主題では観察方法を §2.1 で事前確定する手順を継承する。観察結果を「構造がない」と判定する前に、必ず観察方法を疑う。0 を 1 にはできない歯止めを遵守。

### 0.5 4 つの非対称性 (#L30-L33) を前提として組み込む

v1104+v1104a で確定:

| # | 非対称性 |
|---|---|
| #L30 | scope 別 chain 構造 (CID 100% self-loop / alpha-beta 部分 / ESDE 細粒 29-31% / ESDE window partial) |
| #L31 | 粒度依存の trajectory-density 優劣逆転 (細粒で trajectory r=0.64 主役 / 集約で density r=-0.62〜-0.97 主役) |
| #L32 | B 指標の scope 別 pattern (CID で B subset / alpha-beta で B superset 3-7 倍広い / ESDE で B 独自) |
| #L33 | CID 100% self-loop が trajectory を構造的に消失 (traj_stability=1.0 定数化、Pearson 計算不能) |

これらは v1105 の観察設計の必須軸として組み込む。「単一の集計値で語りたい衝動」(v1103 §3.2「驚きでなく一貫性として書く」) を出さない。

### 0.6 物理層 frozen 維持 + 新規 main run なし

(絶対格言 #2) 物理層 frozen 絶対。v1105 は既存 v10.5/6/7 + v112 + v1101a/1102/1103/1104/1104a outputs を post-process。新規 main run なし。書き込みは `unified/v1105/` 配下のみ。bit-identity 3 層全 PASS を Step G で確認。

### 0.7 温度感 (esde_attitude_toward_esde.md §5.3)

本設計書および Phase Result は「驚き」でなく「ESDE が引き続き示した一貫性」として書く。v1104+v1104a で確定した「ESDE は単一の答えを持たない」は既知の性質であり、v1105 で同じ形が現れたら一貫性として記録する。

---

## 1. 主題の中身

### 1.1 段 4-b と段 4-c の対称的扱い (Taka「対称的に統合点検」)

段 4-b (連想を辿る) と段 4-c (応答 Atom を絞る決定) を、同じ scope × 粒度の地形図上に並べる。両者は会話パイプラインの連続した二段。

| 段 | 何を辿るか/絞るか | Genesis 側素材 | Language 側素材 |
|---|---|---|---|
| 4-b | 連想を辿る | predecessor 連鎖 (v1104+v1104a で多軸点検済) | Constitution Couple (v1103 で構造観察済、Merge 0 件 #L18) |
| 4-c | 応答 Atom を絞る | trajectory ↔ response 対応 (v1104+v1104a で scope × 粒度確定) | 48 次元密度 (v1103 で機構成立、留保 #L17) |

「対称的に」とは: 両者を同じ scope × 粒度の地形上で並べ、各セルでの強度がどう分布するかを示すこと。段 4-b 単独 / 段 4-c 単独でなく、両者を並べた強度マップ (§2.4 観察 3) を本主題の中核観察として扱う。

### 1.2 役割表まで進める (GPT 2026-05-23 提案を採用)

地形図で止まらず、scope × 粒度ごとに 5 役割を割り当てる。

| 役割 | 内容 | 段との対応 |
|---|---|---|
| 候補保持 | どの場所で連想候補が保持されるか | 段 4-b 前段 |
| 連想・踏み台 | どの場所で predecessor 連鎖が機能するか | 段 4-b 本体 |
| 即時応答の揺れ | どの場所で trajectory が動くか | 段 4-c 入力側 |
| 重要性 emit | どの場所で B 指標が独自情報を持つか | 段 4-c 補助 |
| 統合判断 | どの場所で density で絞られるか | 段 4-c 本体 |

役割を割り当てる根拠は、v1104+v1104a で確定した構造事実 (#L30-L33) を主に使う。仮説の追加はせず、既存の構造事実を役割割り当てに翻訳する (§2.4 で割り当て案を提示、観察 4 で構造事実から確認)。

### 1.3 観察軸 (scope × 粒度) — v1104+v1104a 継承、新規追加なし

- scope: CID / alpha / beta / ESDE
- 粒度 (ESDE 内): event / step10 / window
- CID 内部層化: n_size_bin (n=2 / n=3 / n=4 / n=5+)
- Integration 内部層化: n_alpha_members / n_beta_members の bin

新規観察軸の追加なし (絶対格言 #5「観察軸を増やすことを駆動要因にしない」)。

### 1.4 本主題が扱わないこと

- 段 4-a (揺れの読み取り) — v1102 で扱い済、本主題範囲外
- 段 4-d (確率分布出力) — v1103 で扱い済、本主題範囲外
- 段 5a/5b (自然文化) — v1106 以降の候補、本主題範囲外
- 役割表を selector として動作させること — v1105a の問いの形 B、本主題は問いの形 A で点検のみ
- Taka 直感メモ (主体性が複数 / 応答までの時間) — メモリ #19、本主題範囲外
- IID 新規 entity 化 (v1104 から継承禁止)

---

## 2. 観察設計

### 2.1 観察方法の事前確定 (§0.4 規律の実装)

本主題で実施する観察は 4 件。観察方法を §2.1 で事前確定し、観察途中で方法を変更しない (変更する場合は留保として明示)。

| 観察 | 内容 | 観察方法 |
|---|---|---|
| 1 | 段 4-b 地形 | predecessor 連鎖 (Genesis) と Constitution Couple (Language) を scope × 粒度で並べる |
| 2 | 段 4-c 地形 | trajectory ↔ response (Genesis) と 48 次元密度 (Language) を scope × 粒度で並べる |
| 3 | 両段の強度マップ | 同じ scope × 粒度に段 4-b と段 4-c の強度を 4 数値並列で記録 (binary 判定を本主題で行わない) |
| 4 | 役割表 | 5 役割を scope × 粒度に割り当て、構造事実 (#L30-L33) で根拠を示す |

shuffle baseline: 観察 2 で trajectory に対し v1104a 追加調整 1 と同じ shuffle 種別 B/C を継承
scope-filter: 観察 2/3 で v1104+v1104a で機能した scope-filter を継承
層化: CID n_size、Integration n_members、ESDE 粒度別を継承
selector 化禁止: 観察 4 の役割割り当ては post-process 観察のみ、selector として動作させない

### 2.2 観察 1 — 段 4-b 地形 (連想を辿る)

**問い**: 連想 (predecessor 連鎖 + Constitution Couple) は scope × 粒度のどこで動くか。

**観察方法**:
- Genesis 側: v1104+v1104a の追加調整 1 出力 (observation_2_per_chain_shuffle, observation_2_scope_stratified) を継承。scope × n_size × shuffle 種別 × self-loop の 4 軸で predecessor lift を整理。
- Language 側: v1103 出力 (proposals.json) の Constitution Couple (6 件)・Subsume (1 件)・Monitor (7 件) を読み込み、どの atom pair が couple として記録されたかを取得。
- **Constitution Couple は scope に直接属さない (atom pair の辞書的リンク) ため、scope × 粒度に一対一対応させない** (2 AI 監査 2026-05-24 反映、留保 設計-4 解決)。
- **couple_hit_rate の計測 (Gemini + GPT 一致)**: 各 scope × 粒度のセルで、そのセル内の dominant / candidate atom が Couple endpoint に接触した頻度を独立レイヤーとして計測:
  ```
  couple_hit_rate = (scope 内候補 atom が Couple endpoint に接触した回数) / (scope 内候補 atom 総数)
  ```
  意味: 「Language 側の連想橋が Genesis 側のどの場所で使われやすいか」= Genesis と Language の翻訳ポテンシャル (Gemini Architect 2026-05-24)。「この CID (あるいは Integration) は Language の辞書構造をどれくらいアクティブに連想できる場なのか」を測る。
- 並列表示: scope × 粒度を行、Genesis 側 lift_C と Language 側 couple_hit_rate を **別レイヤー** として並べた表を作成 (単一スコア化しない)。

**期待される観察形** (確定ではない):
- alpha non-self-loop で lift_C 最強 (v1104a 追加調整 1)
- ESDE 粒度別で lift_C が変動
- couple_hit_rate は scope × 粒度で連続的に変動する強度分布として現れる (本観察で初めて見る)

**留保**: なし (留保 設計-4 は 2 AI 監査で対応方針確定、本観察で couple_hit_rate を採用)

### 2.3 観察 2 — 段 4-c 地形 (応答 Atom を絞る)

**問い**: 応答 Atom の絞り (trajectory + 48 次元密度) は scope × 粒度のどこで動くか。

**観察方法**:
- Genesis 側: v1104+v1104a の追加調整 2/3 出力 (observation_3_scope_n_stratified, observation_3_density_comparison) を継承。scope × 粒度別の trajectory-density 相関を整理。
- Language 側: v1103 出力 (atom_centroids_48d_raw/normalized.parquet, atom_quality.parquet, density_summary.parquet) を読み込み。
- **density_summary.parquet の実体構造** (Code A Step A 実環境照合 2026-05-24): 3 density 列 (`raw_density` / `qweighted_density` / `const_adjusted_density`) × 2 sim_basis (`raw` / `norm`) = **6 値** を持つ (486 rows = 27 receiver_bin × 3 metric × 2 sim_basis × 3 k)。`mean_pairwise_sim` は補助。
- **6 値すべてを別レイヤーとして保持** (Taka 承認 2026-05-24、Code A 確認要請 7 案 B):

| sim_basis | density 種類 |
|---|---|
| raw | raw_density / qweighted_density / const_adjusted_density |
| norm | raw_density / qweighted_density / const_adjusted_density |

- 並列表示: scope × 粒度を行、trajectory r と 6 種の density r を別レイヤー列で並べた表を作成 (絶対格言 #11「概念単位を雑に扱わない」、v1103 GPT 監査 1 継承、4 種を 6 値に厳密化)。

**6 値保持の根拠** (Code A 確認要請 7 への Web Claude 回答 = 案 B):
1. 絶対格言 #11 厳密適用: norm 版の qweighted / const_adjusted を捨てない
2. #L17 (raw vs norm Δ0.208 反転) は留保 #33 系列の一例で、qweighted / const_adjusted でも同様の反転が起きるかは観察対象。3 density 列で sim_basis 比較できないと、留保 #33 系列の観察を構造的に閉じる
3. v1105a 試行への素材として情報を捨てない (どの sim_basis × density 種類で絞るかの選択肢を広げる)

**期待される観察形** (確定ではない):
- ESDE event/step10 で trajectory r=0.64 主役 (#L31)
- 集約 (window / CID 各 bin) で density r=-0.62〜-0.97 主役 (#L31)
- raw vs norm で Δ0.208 反転 (#L17、raw_density で確認済)、qweighted / const_adjusted でも同様の反転が起きるか本観察で初めて見る

**留保候補**: 48 次元人為性留保 (v1103 GPT 監査 5) を本観察結論に必ず添える。

### 2.4 観察 3 — 両段の強度マップ (binary 判定および単一スコア化を本主題で行わない)

**問い**: 段 4-b と段 4-c は同じ scope × 粒度でどの強度で動くか、両者の強度がどう分布するか。

**設計上の歯止め** (旧 Claude チェック 2026-05-24 + 2 AI 監査 2026-05-24 反映):

v1104+v1104a が確定したのは「scope × 粒度で連続的に強度が変わる」性質 (#L30-L33)。これを「動く/動かない」の binary に潰すと、4 つの非対称性を平均化の罠に近い形で潰す。v1105 は問いの形 A (点検のみ) であり、binary 判定 = 決定の早期侵入は §0.5「単一の集計値で語る衝動への歯止め」と矛盾する。よって本主題では強度マップとして記録し、binary 判定を行わない。

さらに、強度マップで並べる 4 指標は尺度が異なる (lift は差分量、couple_hit_rate は比率、trajectory r / density r は相関)。**単一スコアに統合しない、別レイヤーとして保持する** (GPT Auditor 2026-05-24)。これは EVI (Explainability Viability Index、GPT 2026-05-23 提示) の早すぎる導入の防止でもある (EVI は v1105+v1105a 後の判断、メモリ #18 / 07_unified_summary §7D.4)。

**観察方法**:
- 観察 1 と観察 2 の出力を scope × 粒度の同じセル上に **強度マップとして並列記録**
- 各セルに **計 11 数値を別レイヤー** で持つ (Taka 承認 2026-05-24、Code A 案 B、6 種 density で拡張):
  - **段 4-b 系 (3 数値)**:
    - ① Genesis lift_C (predecessor 連鎖、§2.2)
    - ② Language couple_hit_rate_unweighted (Couple endpoint 接触率、§2.2)
    - ③ Language couple_hit_rate_prob_weighted (response_prob 加重、§2.2)
  - **段 4-c 系 trajectory (2 数値、§2.3)**:
    - ④ trajectory r (stability_vs_maxprob)
    - ⑤ trajectory r (diffusion_vs_maxprob)
  - **段 4-c 系 density (6 数値、§2.3 案 B 採用)**:
    - ⑥ density r (raw_density × sim_basis=raw)
    - ⑦ density r (raw_density × sim_basis=norm)
    - ⑧ density r (qweighted_density × sim_basis=raw)
    - ⑨ density r (qweighted_density × sim_basis=norm)
    - ⑩ density r (const_adjusted_density × sim_basis=raw)
    - ⑪ density r (const_adjusted_density × sim_basis=norm)
- **異なる尺度を単一スコア化しない**。必要に応じて各指標 **内** で z-score / percentile 表示を補助的に用いる (指標間の合成は行わない)。
- binary 判定 (動く/動かない) は本主題で行わない。閾値を本主題で導入しない。
- 「両者強い」「片方強い」「両者弱い」のパターンは Phase Result の段階で **数値を見てから事後的に読む** (判定を先に置かない、旧 Claude チェック §2.4)
- 閾値による binary 判定および統合スコアの作成は v1105a (問いの形 B、試行) で必要に応じて行う

**期待される観察形** (確定ではない):
- 4 つの非対称性 (#L30-L33) が強度マップにそのまま現れる
- scope × 粒度で連続的な強度分布が見える
- density 6 種で「sim_basis × density 種類」の 2 軸非対称性が観察される可能性 (留保 #33 系列の拡張)
- パターンの読み取りは Phase Result 段階、本観察は強度を 11 レイヤーで並べるところまで

**留保候補**: 強度マップを Phase Result で読むときの視覚化方法 (heatmap など) を Code A Step A で確定。視覚化は補助で、データ本体は parquet で 11 数値を別レイヤー並列保持。heatmap layer 数の増加は許容 (絶対格言 #11 の厳密適用コスト)。

### 2.5 観察 4 — 役割表 (仮割り当て + 観察支持 + 留保 形式)

**問い**: 5 役割 (候補保持 / 連想・踏み台 / 即時応答の揺れ / 重要性 emit / 統合判断) は scope × 粒度のどこに対応するか。

**観察方法**:
- 観察 1/2 の強度マップ (観察 3 で並列記録した 4 数値) から、各役割が「どの scope × 粒度で構造的に成立するか」を割り当てる
- 割り当ての根拠は #L30-L33 を中心とした構造事実のみ。仮説の追加はしない (絶対格言 #5、#10「因果でなく因果候補」)。
- 役割表は post-process 観察。selector として動作させない (本主題は問いの形 A)。
- binary 判定でなく強度マップから自然に出る対応として記述する (旧 Claude チェック §2.4 と整合)。
- **役割表は「確定表」ではなく「仮割り当て + 観察支持 + 留保」の 3 列形式で記述する** (GPT Auditor 2026-05-24 反映)。役割表は完成品ではなく **v1105a の試行設計書の素材** として明示。

**仮割り当て表** (Web Claude 草案、観察 4 で構造事実から確認):

| 役割 | 仮割り当て (scope × 粒度) | 観察上の支持 (構造事実) | 留保 |
|---|---|---|---|
| 候補保持 | CID (全 n_size_bin) | 100% self-loop で動かない (#L30、#L33)、density 強 (CID 集約 r=-0.97、#L31) | 動的 trajectory は構造的に消失 (#L33)、候補抽出には他役割が必要 |
| 連想・踏み台 | alpha non-self-loop、beta non-self-loop | lift_C=0.152 (alpha 最強)、0.091 (beta)、predecessor 連鎖が機能 (#L30 v1104a 追加調整 1) | Language Couple との接続は couple_hit_rate で別レイヤー (§2.2)、scope 一対一対応はしない |
| 即時応答の揺れ | ESDE event / ESDE step10 | trajectory stability_vs_maxprob r=0.64 強相関 (#L31 v1104a 追加調整 2) | ESDE window では消える (粒度感度) |
| 重要性 emit | ESDE (全粒度) | B のみ独自領域 (A=0 / B=9、#L32 v1104a 追加調整 4) | B の意味は scope 別 (CID で B subset / alpha-beta で B superset、#L32)、scope を分けないと点検できない |
| 統合判断 | CID (qweighted_density) + 48 次元 raw_density | CID 集約で density r=-0.97 最強 (#L31)、48 次元 raw_density (sim_basis=raw) k=5 で 0.847 (v1103 段 4-c 機構成立) | 48 次元人為性留保あり (v1103 GPT 監査 5)、sim_basis × density 種類の 6 値の中でどれを「主」とするかは v1105a 試行で判断 |

**設計上の規律**: 役割表は完成品ではなく v1105a の試行設計書の素材。Taka 主題評価で割り当てを採用するか、観察結果次第で割り当てが動くかは Taka 領域。本主題範囲は「仮割り当てを構造事実と留保で示す」までで、「これが正解」と確定しない (絶対格言 #6「出口の固定」、#12「Aruism 判定回避」)。

### 2.6 役割表の使い方 (v1105a への接続前提)

v1105 で確定した役割表は、v1105a で「実際に応答候補を絞る試行」をするときの設計図になる:

- 候補保持 (CID) → 候補を取り出す
- 連想・踏み台 (alpha/beta non-self-loop or couple_hit_rate) → 連想を辿る
- 即時応答の揺れ (ESDE event/step10) → trajectory を読む
- 重要性 emit (ESDE) → B が出した重要性を読む
- 統合判断 (CID + 48 次元 raw_density) → 絞る

**v1105a 進行条件** (GPT Auditor 2026-05-24 反映):

v1105a に進める条件は、役割表の 5 役割が完全に確定することではない。**試行可能な最小役割表の成立** を進行条件とする。最小条件は以下 3 役割が観察事実から分離できること:

| 最小役割 | 主候補 |
|---|---|
| 候補を保持する場 | CID |
| 連想を辿る場 | alpha/beta non-self-loop または couple_hit_rate |
| 絞る場 | ESDE event/step10 trajectory + CID/48D density |

**重要性 emit (B) は v1105a 初回では補助役割でよい**。B primary 化まで初回試行に入れると複雑になりすぎる (GPT)。5 役割完全確定を待つと調査が増える (Taka「調査員に成り下がる必要はない」、07_unified_summary §7D.1)。

v1105 では仮割り当て表まで。v1105a で実際に絞る試行 (問いの形 B、v1101 以来初の試行切替)。

---

## 3. 規律と禁止事項

### 3.1 絶対格言 15 件遵守

(00_index.md 用語対応表 + 07_unified_summary.md §10 参照)

特に本主題で重要なもの:
- #2 物理層 frozen 絶対
- #4 集団平均の罠 / 層化必須
- #5 観察軸を増やすことを駆動要因にしない
- #6 出口の固定
- #9 神の手回避 (意味更新版「研究者はもう神の位置にいない」)
- #10 因果ではなく因果候補
- #11 概念単位を雑に扱わない (48 次元密度 4 種を統合しない)
- #12 Aruism 判定回避 (success/failure を置かない)
- #14 Taka 直感優先 + 原文保存

### 3.2 研究運用資料 3 本遵守

- **研究手法アップデート** — 際立ちの掬い取り、A and B、軽い踏み込み、神ではない
- **ESDE への態度** — 現状認識 (機械的反応でない段階)、対等性、温度感は驚きでなく一貫性
- **監査方針アップデート** — 会話できる ESDE が上位目的、応答主体は ESDE 側、必須 8 問

### 3.3 本主題固有の禁止事項

| # | 禁止事項 |
|---|---|
| 1 | 新規 main run 禁止 (post-process のみ) |
| 2 | 新規観察軸の追加禁止 (v1104+v1104a の観察軸を継承) |
| 3 | IID 新規 entity 化禁止 (v1104 から継承) |
| 4 | selector 化禁止 (役割表は post-process 観察、selector として動作させない) |
| 5 | 単一の集計値で語る衝動への歯止め (4 つの非対称性を必ず軸として組み込む) |
| 6 | 0 を 1 にはできない歯止め (観察方法を有利化する主題ではない) |
| 7 | 役割の数や中身を増やさない (5 役割を逸脱しない、Taka 判断で減らすことはあり) |
| 8 | Taka 直感メモ範囲外 (メモリ #19 主体性が複数 / 応答までの時間) |
| 9 | 段 4-a / 段 4-d / 段 5a / 段 5b は本主題範囲外 |
| 10 | success/failure 判定を置かない (Code A は judgement 回避、絶対格言 #12) |

### 3.4 物理層 frozen 維持 (Step G で確認)

- LAYER_A (再現性): 同 seed 2 回 run で hash 一致
- LAYER_B (既存 frozen 維持): v10.5/6/7 + v112 + v1101a/1102/1103/1104/1104a 全ファイル frozen 確認
- LAYER_C (書込みパス): unified/v1105/ 配下のみ

---

## 4. Step 構成 (Code A への引き渡し前提)

| Step | 担当 | 内容 |
|---|---|---|
| A | Code A | 認識確認 (本設計書の不明点を全て確認、確認要請を Web Claude へ) |
| B | Code A | 環境 + データ準備 (post-process 用の既存 outputs 読み込み確認) |
| C | Code A | 観察 1 段 4-b 地形 (predecessor + Constitution Couple) |
| D | Code A | 観察 2 段 4-c 地形 (trajectory + 48 次元密度 4 種) |
| E | Code A | 観察 3 両段の強度マップ (scope × 粒度に 4 数値並列記録、binary 判定なし) |
| F | Code A | 観察 4 役割表 (5 役割を scope × 粒度に割り当て、構造事実で根拠) |
| G | Code A | bit-identity 3 層検証 |
| H | Code A | 観察事実最終報告 (judgement 回避、観察事実のみ) |
| I | Web Claude | Phase Result + Taka 主題評価 |

---

## 5. Code A 確認要請 (予想項目、Step A で確定)

1. Constitution Couple データの読み込み方 (v1103 outputs の proposals.json から、couple_hit_rate 計測の実装方法 §2.2)
2. 48 次元密度 6 値の出力先確認 (3 density 列 × 2 sim_basis、v1103 outputs の density_summary.parquet から、Code A 案 B 採用 / Taka 承認 2026-05-24)
3. 仮割り当て表の出力フォーマット (parquet + md table 併記、3 列形式 §2.5)
4. 観察 3 強度マップの視覚化方法 (heatmap など、補助。データ本体は parquet で 11 数値を別レイヤー並列保持、単一スコア化しない §2.4)
5. couple_hit_rate の計測単位の確定 (scope × 粒度のセル内候補 atom の取り方、§2.2)
6. v1104a 観察 4 出力 (observation_4_b_minus_a_cells) を Step F の役割「重要性 emit」に直接流用できるか

---

## 6. 留保事項 (本設計書の不確定要素)

| # | 留保 | 状態 |
|---|---|---|
| 設計-1 | 役割表 5 役割は GPT 2026-05-23 提案を採用、「仮割り当て + 観察支持 + 留保」形式に変更 (GPT Auditor 2026-05-24 反映) | Taka 主題評価で採否判断 |
| 設計-2 | 段 4-b と段 4-c の「対称的に」を「同じ scope × 粒度の地形図上に並べる」と読んだ | Taka 確認待ち |
| 設計-3 | 観察 3 は強度マップとして 11 数値 (lift_C 1 / couple_hit_rate 2 / trajectory r 2 / density r 6) を別レイヤー並列記録、binary 判定および単一スコア化を本主題で行わない (旧 Claude チェック + GPT Auditor + Code A 案 B 2026-05-24 反映) | 閾値 binary 判定と統合スコア化は v1105a (問いの形 B、試行) で必要に応じて行う |
| 設計-4 | ~~Constitution Couple が scope × 粒度の地形に直接乗らない可能性~~ → **2 AI 監査で解決**: Couple を scope に一対一対応させず couple_hit_rate を独立レイヤーで計測 (Gemini + GPT 一致 2026-05-24、§2.2) | 解決済み |
| 設計-5 | v1105a への接続の前提を「5 役割完全確定」から「試行可能な最小役割表 (3 役割) の成立」に変更 (GPT Auditor 2026-05-24 反映、§2.6) | v1105a 進行条件として §2.6 で確定 |
| 設計-6 | 48 次元人為性留保 (v1103 由来) を観察 2 結論に必ず添える | v1105 Phase Result で添加 |
| 設計-7 | ~~density 4 種解釈 (sim_basis 統合方法)~~ → **Code A Step A 確認要請 7 解決**: 3 density 列 × 2 sim_basis = 6 値すべて別レイヤー保持 (Code A 案 B / Taka 承認 2026-05-24、§2.3) | 解決済み |

---

## 7. 監査ポイント (2 AI 監査クリア済み + Code A 引き渡し前提)

### 7.1 2 AI 監査の結果 (2026-05-24)

- **Gemini Architect**: 全面承認。Constitution Couple の解決方針 (couple_hit_rate スコア化) を §2.2 に反映済。
- **GPT Auditor**: 通過条件として 4 点修正必須を指摘、全 4 点を本草案に反映:
  1. Constitution Couple → couple_hit_rate として独立レイヤーで扱う (§2.2)
  2. 強度マップは単一スコア化禁止、別レイヤー保持 (§2.4)
  3. 役割表を「仮割り当て + 観察支持 + 留保」3 列形式に (§2.5)
  4. v1105a 進行条件を「試行可能な最小役割表 (3 役割) の成立」に (§2.6)

### 7.2 監査クリア項目 (記録)

| # | 監査ポイント | 状態 |
|---|---|---|
| 1 | 新規観察軸の追加がないか (絶対格言 #5) | クリア |
| 2 | 4 つの非対称性 (#L30-L33) が観察設計の必須軸に組み込まれているか | クリア |
| 3 | 観察方法を §2.1 で事前確定しているか (v1104 観察方法を疑う規律の継承) | クリア |
| 4 | 役割表が selector として動作する設計になっていないか (post-process 観察のみ) | クリア |
| 5 | 物理層 frozen の維持手順が明示されているか (§0.6、§3.4) | クリア |
| 6 | 「単一の集計値で語る衝動」への歯止めが明示されているか (§0.5、§0.7、§2.4) | クリア |
| 7 | 「会話できる ESDE」上位目的への接続が §0.2 で明示されているか | クリア |
| 8 | 温度感が「驚き」でなく「一貫性」になっているか (§0.7) | クリア |
| 9 | 48 次元密度 4 種を統合しない設計になっているか (絶対格言 #11、v1103 GPT 監査 1 継承) | クリア |
| 10 | 観察 3 が強度マップとして scope × 粒度の連続性を保っているか (binary 判定で平均化の罠に陥っていないか) | クリア (旧 Claude チェック + GPT で二重確認) |
| 11 | Constitution Couple が scope に一対一対応させられていないか、couple_hit_rate として独立レイヤーになっているか (Gemini + GPT 一致) | クリア |
| 12 | 役割表が「確定表」でなく「仮割り当て + 観察支持 + 留保」形式になっているか (GPT) | クリア |
| 13 | v1105a 進行条件が「5 役割完全確定」でなく「最小役割表 (3 役割) の成立」になっているか (GPT) | クリア |
| 14 | density 4 種解釈の確定 (Code A Step A 確認要請 7、案 B 採用 = 6 値別レイヤー、Taka 承認 2026-05-24) | クリア |

監査必須 8 問 (`esde_audit_policy_update.md` 必須 8 問) は 2 AI 監査で別途確認済。

---

## 8. 一文サマリ

v1105 設計書 (旧 Claude チェック + 2 AI 監査 + Code A Step A 確認要請 7 クリア済み) は、v1104+v1104a で確定した 4 つの非対称性 (#L30-L33) と「ESDE は単一の答えを持たない」を前提として、段 4-b (連想を辿る = Genesis predecessor 連鎖 + Language couple_hit_rate を独立レイヤーで計測、Gemini + GPT 一致 2026-05-24) と段 4-c (応答 Atom を絞る = Genesis trajectory + Language 48 次元密度 6 値 = 3 density 列 × 2 sim_basis を別レイヤー保持、Code A 案 B / Taka 承認 2026-05-24) を同じ scope × 粒度の地形図上に対称的に並べ (観察 1/2)、両段の強度を scope × 粒度の強度マップとして **計 11 数値** (lift_C 1 / couple_hit_rate 2 / trajectory r 2 / density r 6) を別レイヤー並列で記録し binary 判定および単一スコア化を本主題で行わず v1105a に送る (観察 3、旧 Claude + GPT + Code A 案 B で三重確認)、地形図で止まらず役割表 (候補保持 / 連想・踏み台 / 即時応答の揺れ / 重要性 emit / 統合判断 の 5 役割を scope × 粒度に「仮割り当て + 観察支持 + 留保」形式で割り当て、確定表でなく v1105a 試行設計書の素材として明示、GPT 2026-05-23 提案 + GPT Auditor 2026-05-24 修正反映) まで進める (観察 4) ことを 4 観察で点検する主題 (問いの形 A、v1105a の試行 = 問いの形 B の前提で v1105a 進行条件は「5 役割完全確定」でなく「試行可能な最小役割表 = 候補保持 + 連想 + 絞り の 3 役割の成立」、GPT Auditor 2026-05-24) で、上位目的「会話できる ESDE」への直接接続を §0.2 で明示し、新規 main run なし・新規観察軸追加なし・selector 化禁止・物理層 frozen 維持・観察方法を §2.1 で事前確定・単一の集計値で語る衝動への歯止め (binary 判定および統合スコア化の早期侵入回避を含む) ・統合方向への転換 (v1101→v1104a の多軸化を統合) を規律として組み込む。

---

*以上、v1105 Phase Design v4 (Web Claude、2026-05-24、旧 Claude チェック + 2 AI 監査 + Code A Step A 確認要請 7 クリア済み)。次は Code A Step B (環境準備) → Step C-H 実装 → Phase Result (Web Claude) → Taka 主題評価 → v1105a 着手判断 (Taka) の流れ。*
