# ai_templates — Index

*配置先 (Ryzen)*: `docs/ai_templates/`
*対になるディレクトリ*: `docs/ai_summaries/` (フェーズ要約)
*対象読者*: 未来の Claude (相談役 / Code A / Code B)

---

## このディレクトリの目的

ESDE 研究のスレッドは高回転率で更新される (Claude 文脈制限のため)。各スレッドで設計書フォーマットを再発明すると、項目欠落・チェック漏れ・不変量逸脱の事故源になる。

本ディレクトリは **相談役 Claude が Code A / Code B に渡す書類の標準フォーマット** を保管する。新スレッドの相談役は本テンプレに従って書く。Code A/B は本テンプレに従って提出する。

---

## ⚠️ 警告

- **テンプレを勝手に書き換えない**。Taka 承認なしに既存テンプレを改変しない (ai_summaries と同ルール)。
- **足りない節があれば追記**して、相談役 Claude → Taka 承認 → テンプレ反映のフローで更新する。
- 各テンプレの末尾に「適用例」リンクが書いてある。**箱の中身に迷ったら実例を読む**。

---

## ファイル一覧

| # | ファイル | 用途 | 利用者 |
|---|---|---|---|
| 00 | `00_index.md` | (本ファイル) ナビ + 共通規律 + 体制判定 + 共通不変量 | 全員 |
| 01 | `01_design_template.md` | 設計書テンプレ (軽量/中量/重量) | 相談役 → Code A |
| 02 | `02_codecheck_request.md` | Code B チェック依頼書 | 相談役 / Code A → Code B |
| 03 | `03_codecheck_response.md` | Code B 承認/不承認レポート | Code B → 相談役 / Taka |
| 04 | `04_phase_summary.md` | Phase 完了報告書 | 相談役 → Taka |

---

## ESDE プロジェクト共通規律 (どの作業でも遵守)

### A. 絶対遵守ルール

1. **物理層への非干渉** — 認知層から物理層 (theta/S/R/E/Z) を変更しない。Cognition v5.x の「選択なき循環は洗濯機」結論を破らない。
2. **frozenset は解放しない** — label の魂は固定。動きは認知層内部状態から作る。
3. **既存科学オントロジーへの依存禁止** — 既知パターンへの翻訳は「ずれ」を招く。翻訳ではなく演繹。
4. **外部評価関数の禁止** — loss / reward / fitness は ESDE の外側にある。内部評価のみ。
5. **静的パラメータチューニングの禁止** — 動的平衡原則 (Axiom L)。固定値で結論を出さない。

### B. 3 層構造 (4 層構造移行中)

- 物理層 (波): 5 Forces、frozen
- 存在層 (粒子): label = frozenset + phase_sig + share、torque で物理層に微小影響のみ
- 認知層 (過程): cid、観察と差分のみ、物理層・存在層に介入しない
- 意識層 (将来): 認知層の解釈を検証のみ、どこにも介入しない (v10.x 以降)

### C. プロジェクト精神

- **結果出したもん勝ち** — 論文より実測。Null result も valid な結果。
- **48 seeds 標準** — 4 seeds の結論は 48 で覆る。本格 run は 48 seeds 必須。
- **OMP/MKL/OPENBLAS_NUM_THREADS=1** — numpy thread 競合防止。`JOBS=24` parallel が `JOBS=48` より速い。
- **Ryzen ground truth** — `/mnt/user-data/uploads/` の Taka upload ファイルが正、Claude の local 理解より優先。
- **Taka の概念発言は定義であって実装予測ではない** — 哲学的 framing を技術予測と混同しない。
- **忖度しない** — Taka は flattery を求めていない。誤りはそのまま指摘する。

---

## 体制判定基準 (どの設計書テンプレを使うか)

新規作業を Code A/B に流す前に、相談役 Claude が以下で判定する。**判定結果は設計書冒頭に明記**。Taka はそれを見て「もっと軽くていい」「もう少しチェック入れろ」と覆せる。

### 軽量 (Code A 実行のみ、Code B チェック省略)

該当条件 (いずれか):
- 既存出力データの集計 / 分析のみ (新規 run なし)
- 既存スクリプトの定数差し替え 1〜2 個で実行、結果は単独参考値
- 文書のみ (実装変更なし)

例:
- 既存 pulse_log_seed*.csv からの時系列抽出
- audit 用の使い捨てスクリプト (本実装に組み込まない)
- レポート / 文書草稿

体制: **相談役 Claude 設計 → Code A 実行 → 相談役 + Taka 読み合わせ**

### 中量 (Code A 実装 + Code B 軽量チェック)

該当条件 (いずれか):
- 既存ロジックを保持したまま定数 sweep
- 既存スクリプトのコピー + パラメータ系列を変える派生
- 出力 CSV に列追加するだけで、ロジック分岐を増やさない

例:
- NORM_N sweep run
- λ 再決定 audit
- 既存 SubjectLayer フィールド追加だけで内部処理は不変

体制: **相談役 Claude 設計 → Code A 実装 → Code B 軽量チェック (改変範囲のみ) → 本格 run**
Code B チェック内容: 「定数差し替え以外の改変がないこと」「不変量保持」のみ。集計再現性チェックは Code A の自己責任。

### 重量 (Code A 実装 + Code B 通常チェック)

該当条件 (いずれか):
- 新ロジック追加 (新メソッド、新ファイル)
- SubjectLayer / VirtualLayer / engine 周辺への構造的変更
- CSV スキーマ大幅変更
- 物理層 / 存在層に近い層の改変

例:
- v9.11 cognitive_capture 本実装
- 新しい認知層メソッドの追加
- 意識層 skeleton 実装

体制: **相談役 Claude 設計 → Taka 承認 → Code A 実装 → Code B 通常チェック (不変量 + 集計再現性 + 解釈妥当性) → smoke → Code B smoke チェック → 本格 run → Code B 結果チェック**

---

## 共通不変量 (どの Phase でも触らないもの)

新規作業の不変量チェックリストはこれをベースに作る。

### ファイル (1 バイトも変更しない)

- `ecology/engine/v19g_canon.py`
- `autonomy/v82/esde_v82_engine.py`
- `cognition/semantic_injection/v4_pipeline/v43/esde_v43_engine.py` (V43Engine 基底)
- `primitive/v910/virtual_layer_v9.py`
- `ecology/engine/genesis_state.py`, `genesis_physics.py`, `chemistry.py`, `realization.py`, `autogrowth.py`, `intrusion.py`

確認方法: `git log --all --oneline -- <file>` で不変ファイルへの commit が増えていないこと。

### 物理層オペレータ実行順序

```
realizer.step → physics.pre_chemistry → chem.step → physics.resonance
→ grower.step → autogrowth (R>0 リンク強化) → intruder.step
→ physics.decay_exclusion → background injection (BIAS + Z seeding)
```

この順序を変えない。新規物理操作を挿入しない。

### CSV 列保存

- v99_ 列 (v9.9 内的基準軸) は位置・値とも保存
- v10_ 列 (v9.10 pulse model) は位置・値とも保存
- 新規 v11_ / v12_ 列は **末尾に追加**、既存列の順序を崩さない

### 認知層から書き込まないもの

`engine.state.theta / S / R / E / Z`、`vl.labels[*].phase_sig / share / nodes` への書き込みは認知層から一切なし。
確認: `grep -E 'engine\.state\.(theta|S|R|E|Z)\s*=' <file>` で 0 ヒット、`grep -E '\.phase_sig\s*=|\.share\s*=' <file>` で 0 ヒット (cog 側コードに対して)。

### RNG 分離

`engine.state.rng` を認知層側で消費しない。新規 RNG が必要なら `np.random.default_rng(seed ^ <定数>)` で派生。
過去使用済 XOR 定数: `0xC0FFEE` (v9.11 capture)。

### per_window CSV bit identical

物理層・存在層への影響がない変更なら、smoke 時に v9.10 (または最新の baseline) と `diff` exit 0 でなければならない。

---

## テンプレ更新ポリシー

- 既存テンプレの改変は Taka 承認必須
- 新テンプレの追加は OK だが、用途が既存テンプレと重複しないこと
- 既存テンプレの末尾に「v9.x 追記」セクションを足すのは可
- フェーズ終了時に「このテンプレで困ったこと」があれば相談役 Claude が Taka に挙げる

---

## 一文サマリ

ai_templates は相談役 Claude / Code A / Code B が共有する標準フォーマット。スレッド回転で揺れない箱を作っておくことで、項目欠落・チェック漏れ・不変量逸脱を防ぐ。新作業は **体制判定 → 該当テンプレ選択 → 共通規律と共通不変量に従う**。
