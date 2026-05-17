# v1101a 内課題 — Step E 因果候補集約の修正指示 (留保 #L5 対応)

*作成*: 2026-05-18、Web Claude (相談役)
*親*: `v1101a_phase_result.md` §3.1 / §6 留保 #L5 + Code A 追加調査 (relation_strength の path 別分布確認、2026-05-17) + Taka 判断 (2026-05-17)
*対象*: Code A
*位置づけ*: v11.0.1.a「ESDE スケール注意機構」段階 1 の **内部課題**。新バージョンを切らない。理由は §1 を参照。Step E (因果候補抽出) の集約ロジック修正で、留保 #L5 (Integration 経路 0 件) に対応する。

---

## 1. なぜ新バージョンを切らないか (Taka 判断 2026-05-17)

Taka 方針: 「枝分かれするかしないかの調査」を細かくバージョン化するとバージョン管理が情報量に押し潰される。Bug fix なのか主題級の課題なのかを調べる段階まではバージョンを与えない。調べた結果が「直せば済む」なら現バージョン内の課題、「主題級」なら初めてバージョンを切る。

本件は調べが済んでいる。Code A 追加調査で原因が「Step E の集約ロジックが path 別の relation_strength スケール差を無視していた」と判明した。新機構の発明でも ESDE の階層観の書き換えでもなく、本主題段階 1 で用いた観測器 (Step E の集約方式) の修正。したがって v1101a 内の課題として扱い、新バージョンを切らない。

---

## 2. 原因 (Code A 追加調査の確定事実)

relation_strength の値スケールが path 別に根本的に異なる:

| path | strength median | strength max | 性質 |
|---|---|---|---|
| integration_alpha | 1.000 | 1.000 (固定) | binary 接続有無 |
| integration_beta | 1.000 | 1.000 (固定) | binary 接続有無 |
| temporal_coactivation | 0.100 | 1.000 | 小スケール連続 |
| familiarity | 30.1 | 500 | 大スケール連続 |
| attention_via_salience | 33.0 | 124 | 大スケール連続 |

Step E の現方式 (path 別 strength の合計の argmax) では、1.0 固定の binary が 2 桁連続値に構造的に勝てない。因果候補 path 分布で integration_alpha/beta が全 24 seeds で 0 件になったのは、この不当比較の帰結。

検証: path 内で z-score 正規化してスケール差を除去して argmax を取ると、integration 経路が 29 source_cid (integration_alpha 15 + integration_beta 14) で因果候補として出現し、dominance が attention_via_salience → familiarity に逆転する (seed 0、24 seeds で同パターン想定)。

仮説 A (観測器の問題) と仮説 B (階層の役割分担 — integration の 1.0 固定 binary は「接続の有無」、salience/familiarity の連続値は「強度ある関係」で表す対象の種類が違う) は排他でなく **両方真**。詳細は Phase Result §3.1。

---

## 3. Taka 判断 — (iii) 両方併記

留保 #L5 への対応は Code A が提示した三択のうち **(iii) 両方併記** を Taka が採用:

- (i) Step E を z-score 正規化に置換 → 不採用 (仮説 B を無視する。binary と連続値の意味差は正規化で消えない)
- (ii) 現状維持 + 「integration は別レイヤー、causality 集約対象外」と明記 → 不採用 (仮説 A の発見 = 正規化すれば見えることを捨てる)
- **(iii) sum argmax (現方式) と z-score argmax (path 内正規化) の両方を出力** → **採用**。両仮説が真であることに正直で、「集約方式で因果の像が変わる」事実そのものを観察記録に残せる。v1101 留保 #33「集計単位による方向反転」と同型の対応。

---

## 4. Step E 修正の作業内容

### 4.1 修正対象

Step E の因果候補抽出スクリプト (`v1101a_step_e_*.py` 相当)。因果候補 path を決める argmax のロジック。

### 4.2 修正内容

因果候補 path を 1 つの方式で決めるのをやめ、**2 方式を並走させて両方を出力する**:

1. `causality_candidate_path_sum` — 現方式。path 別 relation_strength の合計の argmax。
2. `causality_candidate_path_zscore` — 新方式。path 内で relation_strength を z-score 正規化したうえで合計の argmax。path 別スケール差を除去する。

attention_emit ログ / causality 出力の per-record スキーマに、上記 2 列を併記する。現行の単一 `causality_candidate_path` 列は、`causality_candidate_path_sum` にリネームするか、互換のため残すかは Code A 判断 (どちらでも可、ただし下流の集計コードとの整合を確認すること)。

### 4.3 z-score 正規化の留意点

- 正規化は **path 内** (同じ relation_path_type の relation_strength 分布の中) で行う。path をまたいだ正規化ではない。
- integration_alpha / integration_beta は strength が 1.0 固定のため、path 内分散が 0 または極小になる。z-score が定義できない / 不安定になる場合の扱い (分散 0 のとき z-score を 0 とするか、別の正規化を当てるか) を Code A が決め、その扱いを観察事実報告に明記すること。これは神の手回避の観点で重要 — 分散 0 path の扱いは構造的に決め、ハンドチューニングしない (絶対格言 #9)。

### 4.4 出力と再集計

- Step E 出力を 2 方式併記で再生成。
- Step F のグラフ HTML に、因果候補 path 分布を sum 方式 / z-score 方式の 2 通りで表示する panel を追加する (v1101 留保 #33 を「集計単位で像が変わる」可視化として扱ったのと同じ趣旨)。
- Step G の bit-identity 検証を再実行 (本修正は v1101a 内の post-process 修正、v106/v107/v105 の main outputs は引き続き不変、書き込みは `unified/v1101a/` 配下のみであることを確認)。

### 4.5 範囲外

- 本修正は Step E (因果候補集約) のみ。注意 emit 本体 (Step C)・波及観察 (Step D)・qc_ratio は変更しない。
- v10.7 の relation_strength の **定義そのもの** (integration を 1.0 固定にした設計) は変更しない。これは v10.7 main outputs であり frozen 対象。本修正は v1101a 側の集約方式を変えるだけで、v10.7 の値には触れない。
- 段階 2 (時間軸付き観察) とは独立。本修正は段階 2 の判断を待たず実施してよい。

---

## 5. 進行

| Step | 内容 | 状態 |
|---|---|---|
| Step E 修正 | §4 の 2 方式併記実装 | Code A 着手可 |
| Step F 更新 | 因果候補 path 分布の 2 方式併記 panel 追加 | Step E 修正後 |
| Step G 再検証 | bit-identity 3 層、v10.x main outputs 不変確認 | Step F 更新後 |
| 観察事実報告 | 2 方式の因果候補 path 分布の比較を観察事実として記録 (judgement なし、絶対格言 #12)。z-score 方式で integration が因果候補としてどう振る舞うか、dominance がどう変わるかを記録 | Step G 後 |

観察事実報告は judgement を置かない。「z-score 方式で integration が N source_cid で出現した」「dominance が X → Y に変わった」を記録するに留め、「どちらの方式が正しい」の判定はしない。それは集計方式の選択の問題であり、v1101 留保 #33 と同じく「集計単位を変えると像が変わる」観察事実として両方残す。

Phase Result (`v1101a_phase_result.md`) は本修正を織り込み済 (§3.1 / §6 留保 #L5)。修正完了後、観察事実報告を受けて Phase Result §3.1 に z-score 方式の実測値 (現状 seed 0 の 29 source_cid を 24 seeds で確認した値) を追記する。

---

## 6. 一文サマリ

本書は v11.0.1.a「ESDE スケール注意機構」段階 1 の内部課題として、留保 #L5 (Integration 経路が因果候補として全 24 seeds で 0 件) への対応を Code A に指示するものであり、原因は Code A 追加調査で判明済 (relation_strength が integration は 1.0 固定 binary・salience/familiarity は 2 桁連続値とスケールが根本的に異なり、Step E の sum argmax がこれを不当比較していた)、Taka 判断 (iii) により Step E を sum argmax (現方式) と z-score argmax (path 内正規化) の 2 方式併記に修正し、Step F に 2 方式の因果候補 path 分布比較 panel を追加、Step G bit-identity 再検証、観察事実報告では judgement を置かず「集計方式で因果の像が変わる」を v1101 留保 #33 と同型の観察事実として両方記録する、原因が観測器の集約ロジックと判明したため新バージョンを切らず v1101a 内の課題として扱い (Taka のバージョン管理方針)、段階 2 とは独立で段階 2 判断を待たず実施可能、v10.7 relation_strength の定義自体 (frozen 対象) には触れず v1101a 側の集約方式のみ変更する。

---

*以上、v1101a 内課題 Step E 因果候補集約の修正指示 (Web Claude、2026-05-18)。新バージョンを切らない。Code A は段階 2 判断と独立に着手可。完了後 Phase Result §3.1 に実測値を追記。*
