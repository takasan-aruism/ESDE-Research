# v1303g Step A 事前調査 — 4分類候補軸は literal 定義では degenerate・改善余地あり（実装前報告）

*作成*: 2026-06-30、Code A。read-only 後処理。**設計の4分類 literal 定義が degenerate（健全性NG）と事前調査で判明 → 実装前に報告し定義の判断を仰ぐ（一括しない）。** 構成的改善も提示。判定は Web Claude / Taka。

---

## 0. 結論（先に）
- **照合5列（近傍Archive・過去同種・θ近さ・Atom安定/変化・B_Gen層別）は全て v1303f統合+ledger から計算可能**（取得性OK）。
- **だが設計の literal な4分類候補定義は degenerate**：Familiar-Stable 92.1% / Novel-Random 0.0%。設計§2.4「一象限に偏れば定義見直し」・§1.4(b)「候補軸が引けない→定義見直し」に該当。
- 原因は**データ特性**（下記）。**構成的改善（near_archive除外・Stable=θ帯・pulse背景化）で4象限が分離する**ことも確認。定義変更は設計判断ゆえ報告。

## 1. literal 定義の degenerate（設計通りに組んだ結果）
| 象限 | 件数 | 割合 |
|---|---|---|
| Familiar-Stable | 13,892 | **92.1%** |
| Familiar-Unstable | 1,176 | 7.8% |
| Novel-Coherent | 8 | 0.1% |
| Novel-Random | 0 | **0.0%** |
- Familiar = past_same ∨ near_archive / Stable = ¬atom_changed ∨ θ近さ（設計 §1.3）。

## 2. degenerate の原因（データ特性・診断）
| 軸 | 飽和の理由 | 値 |
|---|---|---|
| **near_archive** | v1303e persistence(archive) が**寿命の約48%を覆う broad な区間**ゆえ ±500窓で誰でも near_archive | near_archive=**0.996** |
| **past_same** | now_event の **83%が pulse**で、各cidが多数 pulse を持つ＝再発が自明 | past_same=**0.931**（pulse 0.982） |
| **atom_changed** | event時点で rank_1_atom が変わるのは**稀（12%）**＝¬atom_changed(stable)が飽和 | atom_changed=**0.123** |
- → 3軸とも「ほぼ常に Familiar / ほぼ常に Stable」に飽和し、Novel・Unstable が立たない。**near_archive は broad archive ゆえ無意味・atom は変化稀ゆえ Stable 判別に無効・pulse 再発が Familiar を飽和**。

## 3. 構成的改善（4象限が分離するか・dry テスト）
| 定義 | Fam-Stable | Fam-Unstable | Novel-Coher | Novel-Rand |
|---|---|---|---|---|
| literal（設計） | 92.1% | 7.8% | 0.1% | 0.0% |
| **改善A**：Familiar=past_same のみ（near_archive除外）/ Stable=θ近さ（atom除外） | 35.9% | 57.2% | 3.5% | 3.3% |
| **改善B**：改善A ＋ **pulse除外（背景化）し構造的イベント(birth/death/α/β/c)のみ分類** | 25.5% | 42.7% | **18.1%** | **13.7%** |
- **改善B で4象限が実質的に分離**（Novel 32%）。理由：(1)near_archive は broad archive ゆえ判別に使えない→外す、(2)Stable は atom(稀)でなく **θ帯（now θ ≥ cid persistence閾値・40%で分離）**、(3)**pulse(83%・背景的に頻発)を分類対象から外し構造的イベントに絞る**。
- 健全性: literal では cid_birth すら Novel率1.3%（near_archive が誕生も Familiar 化）＝不自然。改善で誕生は素直に Novel 寄り。

## 4. 報告と判断要請（実装前・定義は設計territory）
照合列は組めるが、**4分類候補軸の literal 定義は degenerate（設計の(b)出口・見直し条件に該当）**。実装に進む前に定義の判断を仰ぐ：
1. **改善Bの定義で dry 4分類を実装する**か（near_archive除外・Stable=θ帯・pulse背景化＝4象限分離）。これは設計の literal 定義からの変更（Familiar/Stable の中身を変える）ゆえ Web Claude/Taka 承認が要る。
2. それとも **literal のまま実装し「degenerate（注意センターの4分類は現データでは Familiar-Stable に飽和）」を観察事実として報告**するか（dry の出口(b)＝定義見直しが必要、という結論）。
3. pulse の扱い（背景化して構造的イベントのみ分類 / pulse を別 event_class に / 含める）。

## 5. 規律
- read-only・物理非書込・#12 判定せず観察事実のみ・合成しない(#11・4分類は合成でなく分類のまま)・cid個別/n_core別/B_Gen層別・**結果を確定しにいかない・前段で止める**（GPT）。
- **信頼問題の継続**：事前調査で degenerate を捕捉し、degenerate のまま「4分類できた」と進めない（想定外で先に進まない）。改善案は提示するが定義変更は設計判断ゆえ報告。

## 6. 一文サマリ
v1303g Step A 事前調査（Code A, read-only）── Now-event への照合5列（近傍Archive・過去同種・θ近さ・Atom安定/変化・B_Gen層別）は全て v1303f統合+ledger から計算可能だが、**設計の literal な4分類候補軸は degenerate**（Familiar-Stable 92.1%/Novel-Random 0.0%・設計§2.4/§1.4(b)の見直し条件に該当）、原因は**データ特性**＝near_archive飽和(persistence archiveが寿命48%を覆うbroadさゆえ±500で誰でも近傍=0.996)・past_same飽和(now_eventの83%がpulseで再発自明=0.931)・atom_changed稀(12%でStable飽和)、構成的改善（near_archive除外・Stable=θ帯(atom除外)・pulse背景化し構造的イベントのみ）で**4象限が分離**(改善B: 25.5/42.7/18.1/13.7・Novel32%)を確認、実装前に定義の判断を仰ぐ（改善Bで実装 / literalのままdegenerate報告 / pulse扱い）＝定義変更は設計territoryゆえ報告・degenerateのまま「4分類できた」と進めない（信頼問題・前段で止める）、判定はWeb Claude/Taka。
