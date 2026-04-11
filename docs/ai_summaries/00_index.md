# ESDE 研究史 — AI 向け超要約 (Index)

*作成日*: 2026-04-11 (v9.9 Long Run 進行中)
*対象読者*: ESDE-Research に新規に関わる Claude (新スレッド初見)

---

## このディレクトリの目的

ESDE 研究の各フェーズ (Genesis / Ecology / Autonomy / Cognition / Primitive) と哲学的コア (概念理解) を、未来の Claude が **context に乗せても暴走しない最小サイズ** に圧縮したもの。

各原本 (200-1300 行) の要点だけを抽出し、却下された方針 (失敗の記録) を必ず残してある。**未来の Claude が同じ失敗を繰り返さないため**。

---

## ⚠️ 警告

- これは**要約**であり原本ではない。設計の詳細や個別実験の数値が必要な場合は必ず原本 (`docs/ESDE_*_Report.md` および `docs/概念理解.md`) を参照すること。
- **要約は v9.9 時点のもの**。v9.10 以降の実装・発見は反映されていない。新しい知見が出たら本要約を更新するか、別途追記ファイルを作ること。
- **推測補完していない**。原本にあることだけ抽出している。「書いてないこと」を埋めようとしないこと。
- 概念理解.md からの引用は **必ず引用形式 (>) で残してある**。Taka の発言を勝手に言い換えないこと。

---

## 推奨読書順序

```
00_index.md (このファイル)
  ↓
06_concept_core.md      ← まず哲学コアと絶対ルールを把握
  ↓
01_genesis_summary.md   ← 物理層 (床) の確立
  ↓
02_ecology_summary.md   ← observer 複数性
  ↓
03_autonomy_summary.md  ← label 自律性、5-node 転換点
  ↓
04_cognition_summary.md ← ★ 失敗の記録 (最重要)
  ↓
05_primitive_summary.md ← v9.x の現状 (現行フェーズ)
```

**急ぎなら**: `06_concept_core.md` と `05_primitive_summary.md` の 2 つだけ読めば現状作業に最低限着手できる。**ただし `04_cognition_summary.md` の「却下された方針」は時間を作って必ず読むこと**。

---

## ファイル一覧

| # | ファイル | 原本 | 内容 |
|---|---|---|---|
| 00 | `00_index.md` | (このファイル) | ナビゲーション |
| 01 | `01_genesis_summary.md` | ESDE_Genesis_Report.md (638 行) | 物理層の確立、5 Forces、観察者 k\*=4、N=10000 まで scale 不変 |
| 02 | `02_ecology_summary.md` | ESDE_Ecology_Report.md (242 行) | observer 複数性、global は lossy compression、long_drift がデフォルト |
| 03 | `03_autonomy_summary.md` | ESDE_Autonomy_Report.md (749 行) | label = 魂 (frozenset)、territory = 場、5-node 転換点、Lifecycle Instrumentation |
| 04 | `04_cognition_summary.md` | ESDE_Cognition_Report_Final.md (1271 行) | **★最重要・最複雑**。v3-v7 の試行錯誤、「物理層は床」結論、virtual layer の確立 |
| 05 | `05_primitive_summary.md` | ESDE_Primitive_Report.md (746 行) | 3 層構造、cid (v9.8a)、内省 tag (v9.8b)、information pickup (v9.8c)、内的基準軸 (v9.9) |
| 06 | `06_concept_core.md` | 概念理解.md (1305 行) | Aruism、3 層構造、絶対ルール、Taka 直接発言、戦国大名モデル、spatial vs structural |

---

## 最小限知っておくべき 5 項目

未来の Claude が要約を読む前に最低限把握すべきこと:

1. **物理層には介入しない**。Cognition v5.x で「選択なき循環は洗濯機」と確定。認知層は存在層に書き込むだけ、loop は閉じない。
2. **label = frozenset の魂**、解放しない。cid (v9.8a 以降) は label とは別の観察主体。
3. **観察者は複数**。global は lossy compression、local が真。
4. **5-node が転換点**。density independent な唯一のサイズ (Autonomy で確定)。
5. **数値解釈は analyzer 段階で**。一次出力 (per_window/per_subject CSV) は構造語のみ ("formed"/"unformed"/"tie"/"none")。

---

## このディレクトリの更新ポリシー

- **既存レポート (`docs/ESDE_*_Report.md`、`docs/概念理解.md`) は一切編集しない**。本ディレクトリの要約のみ追加・修正する。
- v9.10 以降に新しい確定事項が出たら、該当する要約ファイルに「v9.10 追記」セクションを加えるか、`07_v910_addendum.md` のような追記ファイルを作る。
- 要約の質に疑問がある時は、まず原本を読み直して照合すること。要約だけで判断しないこと。
- **Taka の承認なしに勝手に書き換えない**。新規追記は OK だが、既存要約の改変は Taka の確認を取る。
