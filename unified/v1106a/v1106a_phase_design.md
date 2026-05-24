# v11.0.6.a (v1106a) Phase Design Draft — mapper_output (LLM 1 億トークン 8 日間判定) ベースの新規 Synapse 接続点検

### サブタイトル: v1106 で確定した #L41 (Synapse v3 weight=1.0 普遍化) が mapper_output (raw_scores 0-10 整数) で解消するか、Atom × word の 48 axes で接続が構造的に成立するか

*作成*: 2026-05-25、Web Claude (相談役、Genesis 側)
*位置づけ*: v1106a 主題設計書 **草案**。問いの形 A (点検、v1106 同主題段階 2、マイナーバージョン運用方針 = アルファベットは同じ主題の段階更新、v1101a/v1104a/v1105a と同型)。本草案 → Taka 確認 → Code A 認識確認 → 実装、の流れに乗せる (Gemini 監査は v1106 同様 Taka 確定で省略、GPT 監査は構造的変更が大きい場合に追加検討)。
*親*: `v1106_phase_result.md` (Web Claude、4 条件成立 + #L41-L43 + 案 Y 採用「v1106 は古い Synapse v3 接続の記録、v1106a で最新データ点検」、Taka 2026-05-25) + Step H §12 経緯 (古い Synapse v3 vs 最新 mapper_output 対比) + Language 側 GPT 整理 2026-05-24 (A1 batch = mapper_output、Lexicon 側成果物、語 × 48 スロット × 0-10 整数 + 0-1 確率) + Taka 整理 (2026-05-25 案 Y 採用 +「うっかりミスは仕方ない、記録に残して先に進む」+ ESDE LANGUAGE 時代の構造的背景)
*対象*: Taka (確認) + Code A (認識確認)

(本書は全 8 セクションで構成、要約のみ抜粋して以下に記載。詳細本文は Web Claude 設計書原文を保存)

---

(設計書 v3 原文を保存、全 8 章 = §0 主題の前提と歯止め (11 サブセクション) / §1 主題の中身 (5 サブセクション、接続式 §1.3 案 X/Y/Z 含む) / §2 観察設計 (8 サブセクション、6 観察 = 観察 1-4 v1106 継承 + 観察 5/6 = #L41/#L42 解消確認 新規) / §3 規律と禁止事項 / §4 Step 構成 A-K / §5 Code A 確認要請 (必須 5 + 追加 5 = 計 10 件) / §6 留保事項 / §7 監査ポイント / §8 一文サマリ)

新規規律「データ取り違え防止規律」(v1106 §22.5、本主題で初適用):
> 主題着手時に「データの所在 / timestamp / 生成方法 / Taka 過去評価の確認」を Code A Step A で必須化する。古い実装と新しい実装が並存する場合、必ず Taka に最新版を確認する。

接続式 (Web Claude 案、Code A Step A で確認、独自発明禁止):
- 案 X (主軸): word 単位接続、raw_scores_max(atom, word) = max over 48 axes of raw_scores
  score(word_j) = Σ_i [p_s7(atom_i) × raw_scores_max(atom_i, word_j) / 10]
- 案 Y (補助): axis 単位接続、48 axes 全部経由して word は最後に集約
- 案 Z (補助): normalized_scores 直接使用 (案 X の raw_scores を normalized_scores に置換)

6 観察:
- 観察 1: mapper_output ベースの Atom → word 変換が途切れず変換できるか
- 観察 2: mapper_output の raw_scores / normalized_scores が v1105a s7 確率分布と整合するか
- 観察 3: word 候補の広がり / 絞り
- 観察 4: s7 主軸 vs s1-s6 補助系列の違いが mapper_output 接続でどう出るか
- 観察 5 (新規対比): #L41 解消の確認 (raw_scores 0-10 整数で atom 間差別化が観察されるか)
- 観察 6 (新規対比): #L42 解消の確認 (s1-s6 集計値が同値にならないか)

v1106a 進行条件 6 点:
- 条件 1-4: v1106 継承 (word_pipeline_complete 存在 / distribution_valid 成立 / 候補爆発制御可能 / s7 主軸存在)
- 条件 5 (新規): #L41 解消観察 (atom 間差別化)
- 条件 6 (新規): #L42 解消観察 (s1-s6 差別化)
→ 4 + 5/6 解消で v1106b 進行、4 + 5/6 部分解消で v1107 検討、4 未成立で v1106c 再設計

Step 構成: A 認識確認 / B 環境準備 / C 観察 1 / D 観察 2 / E 観察 3 / F 観察 4 / G 観察 5 / H 観察 6 / I bit-identity + 集計 / J 観察事実報告 / K Phase Result (Web Claude)

Code A 確認要請 必須 5 件 (データ取り違え防止規律 §0.7 適用):
1. mapper_output データ所在 (325 atom × jsonl、約 126 MB)
2. mapper_output timestamp (2026-03-21 前後、Synapse v3 より新しい)
3. mapper_output 生成方法 (LLM QwQ-32B、1 億トークン、約 8 日間、48 axes × 0-10 整数)
4. Taka 過去評価との整合 (= A1 batch、「シナプスの新しいやつ」「10 段階評価」)
5. 古い実装との並存 (Synapse v3 frozen のまま放置)

Code A 確認要請 追加 5 件:
6. 接続式 §1.3 案 X/Y/Z の実装可能性 + Code A 推奨
7. mapper_output の atom_id ↔ v1103 atom_id mapping (FND.spaceless 等の欠落)
8. word_expansion_ratio / total_word_coverage 計算方法 (Lexicon 32,666 word カバレッジ)
9. v1106 outputs 参照可能性 (v1106 + v1106a 統合 Phase Result のため)
10. 想定実行時間 (mapper_output 126 MB + 48 axes 計算量、1-3 時間規模か)

---

*以上、v1106a Phase Design Draft (Web Claude、2026-05-25) の要約。詳細本文は別途参照。Code A Step A で必須確認 5 件 + 確認要請 5 件 = 計 10 件を実施。問いの形 A 継続、v1106 同主題段階 2、mapper_output ベース、データ取り違え防止規律 §0.7 を本主題で初適用、v1106 結果との対比で #L41/#L42/s7 #L40 が解消するか / 持続するかを構造事実として確認。*
