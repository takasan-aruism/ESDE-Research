# v1303g Step F — 注意センター Phase2前段：Comparator 4分類 dry候補 観察事実報告（判定なし）

*作成*: 2026-06-30、Code A。
*位置づけ*: 注意センター Phase2 前段（v1303g 設計・改善B'）の Step B〜F。v1303f 統合レコードを使い、Now-event に照合列を付け **4分類の候補軸が dry に組めるか**を見た。**4分類の本格判定はしない（候補定義まで）・(a)/(b) 判定しない（#12）。** 「Comparator が成立した／4分類できた／自律注意した」とは言わない。後処理のみ・物理非書込。判定は Web Claude / Taka。
*成果物*: `v1303g_comparator_dry.py` / `outputs/v1303g/v1303g_comparator_dry_seed0.parquet` / `v1303g_distributions.html` / Step A `v1303g_stepA_finding.md`。

---

## 0. 改善B'の経緯（Step A → Taka/GPT判断）
Step A 事前調査で literal 定義が degenerate（Familiar-Stable 92.1%/Novel-Random 0%）と判明し**実装前に報告** → Taka/GPT 判断で改善B'採用：(1)near_archive 除外（broad archive で 0.996 飽和・判別無効）、(2)Stable=θ帯（Atom は12%稀ゆえ補助降格）、(3)pulse を別 event_class に分離、(4)4分類は構造的イベント限定。Web Claude 独立検証で4象限分離を確認済。

## 1. event_class 構成（改善B'・pulse 分離）
| event_class | 件数 | 役割 |
|---|---|---|
| now_structural_event | 2,546 | birth/death/α/β/c_conversion（**4分類対象**） |
| now_pulse_event | 12,530 | pulse（**4分類に入れず別保持**・捨てず混ぜず・後段で pulse専用読み） |
| archive_persistence | 18,809 | stable-above-baseline segment（v1303f 継承） |

## 2. 観察 — 4分類 dry候補が組めたか
- **照合5列を別列で付与**（合成しない・#11）：`past_same`（再発）/ `near_archive`（記録列・Familiarに使わず）/ `theta_in_stability_band`（θ帯）/ `atom_changed`（補助降格）/ `bgen_stratum`。
- **4分類 dry候補軸**：`familiar_flag`=past_same / `stable_flag`=theta_in_stability_band / `dry_quadrant_candidate`（確定分類しない・列として付けるだけ）。
- **4象限 dry分布（構造的イベント2,546件）**：
  | 象限 | 件数 | 割合 |
  |---|---|---|
  | Familiar-Stable | 649 | 25.5% |
  | Familiar-Unstable | 1,087 | 42.7% |
  | Novel-Coherent | 460 | 18.1% |
  | Novel-Random | 350 | 13.7% |
  - **4象限すべてが立つ**（最大 42.7% < 85%・degenerate でない）＝照合列から4分類の候補軸が dry に引けた（出口a の向き・判定は委ねる）。

## 3. trigger別・n_core別・B_Gen層別（cid個別/層化・観察事実）
| trigger | n | Novel率 | Stable率 |
|---|---|---|---|
| cid_birth | 228 | **1.00** | 0.72 |
| cid_death | 191 | **1.00** | 0.49 |
| alpha_formation | 1,067 | 0.12 | 0.41 |
| beta_formation | 478 | 0.27 | 0.43 |
| c_conversion | 582 | 0.23 | 0.36 |
- **誕生/死は Novel率1.00**（過去同種なし＝素直に Novel・健全性OK）。α/β/c は再発ゆえ Familiar 寄り。誕生 Stable率0.72（誕生時 founding cycle＝高同期、v1303a「閉路で生まれ」と整合）。
- **n_core別 Novel率**：n2=0.63 / n3=0.35 / n4=0.14 / n5=0.09。長命な高n_core cid ほど構造的イベントが再発し Familiar 化（短命 n2 は初回イベントが多く Novel 寄り）。
- **B_Gen層別**：low=0.34 / high=0.09 Novel率（背景層別・差が出る・新発見扱いしない）。
- **補助列 atom_changed**：構造的イベントでの変化率 0.106（稀＝Stable判別に使わず補助に降格したのは妥当）。

## 4. 検証ゲート（全PASS・自己確認）
| ゲート | 内容 | 結果 |
|---|---|---|
| gate1_all4_quadrants_present | 4象限すべて存在 | **PASS** |
| gate2_not_degenerate(max<0.85) | 一象限に飽和しない | **PASS** |
| gate3_birth_is_novel | 誕生が Novel に素直（>95%） | **PASS** |
| gate4_pulse_segregated | pulse は別 event_class で4分類対象外 | **PASS** |
| gate5_familiar_is_past_same_only | Familiar=past_same のみ（near_archive 不使用） | **PASS** |
| gate6_no_composite | 合成スコア列なし（#11） | **PASS** |
| gate7_collation_cols_present | 構造的イベントに照合列が付く | **PASS** |

## 5. 言えること / 言えないこと
- **言える（観察事実）**：構造的 Now-event（birth/death/α/β/c）に照合列（past_same・θ帯・atom補助・B_Gen層別）を別列で付け、**4分類の候補軸（Familiar/Novel・Stable/Unstable）が dry に組めて4象限すべてが立った**（degenerate でない）。pulse は別 event_class に分離して保持。誕生は Novel に素直・n_core/B_Gen で分布差。
- **言わない**：「Comparator が成立した」「4分類できた（確定分類）」「CID が自律的に注意した」「注意センターが判断した」とは言わない。**dry＝候補軸を列で付けただけ・確定分類していない。** 閾値（past_same・θ帯・near_window=500）は研究者選択ゆえ `classification_threshold_tag` で明示（#CW7・将来内部化余地）。near_archive は今回 Familiar に使わなかったが Archive 概念は記録列として保持（将来分解で戻す）。(a)/(b) 判定は委ねる。

## 6. 規律遵守
- #11: 照合列を合成しない（別列）・4分類は分類であって合成でない・dryで確定分類しない。#4/D: cid個別/n_core別/B_Gen層別。#2/B: 後処理のみ・物理非書込。#12/J: 判定せず観察事実のみ・前段で止める（GPT・いきなり本体作らない）。F: 228宇宙統一。L: 「Comparator成立」と言わない・Atom意味解釈しない。
- **信頼問題の継続**：Step A で degenerate を実装前に捕捉し報告→改善B'採用→検証ゲートで4象限分離を機械確認してから完了（degenerate のまま「4分類できた」と進めない・想定外で先に進まない）。

## 7. 次段（Code A は判定しない・委ねる）
Web Claude 独立検証（4象限分布・誕生Novel・pulse分離・閾値タグの生データ再確認）→ Phase Result → Taka。Phase2本番候補：Comparator 本体（4分類の確定判定）・near_archive の分解で戻す（同cid過去同種/θ帯/residue/segment再入/Archive終端との近さ）・pulse専用読み・閾値の内部化（v1303e型）。

## 8. 一文サマリ
v1303g Phase2前段（v1303f統合レコード後処理・seed0・改善B'・判定なし#12）── Step A で literal 4分類定義が degenerate(Fam-St92.1%/Nov-Ra0%)と判明し実装前報告→Taka/GPT判断で**改善B'採用(near_archive除外[broad archiveで0.996飽和判別無効]・Stable=θ帯[Atom12%稀ゆえ補助降格]・pulse別event_class分離[捨てず混ぜず]・4分類は構造的イベント限定)**、Step B で構造的Now-event(2546)に照合列を別列付与(合成しない#11)し**4分類dry候補軸が組めて4象限すべて立つ(Familiar-Stable25.5/Familiar-Unstable42.7/Novel-Coherent18.1/Novel-Random13.7・degenerateでない)**、誕生/死Novel率1.00(過去同種なし=素直・健全性OK)・n_core別Novel率n2 0.63→n5 0.09(長命高n_coreほど再発でFamiliar化)・B_Gen層別low0.34/high0.09・atom_changed0.106(稀ゆえStable判別に使わず補助降格は妥当)、pulse(12530)は now_pulse_event に別保持(後段でpulse専用読み)、検証ゲート7項目全PASS、出口は「構造的イベントに照合列を付け4分類候補軸がdryに組めて4象限が立った+pulse別保持」まで(Comparator成立/4分類できた/自律注意とは言わない・dry=確定分類しない・閾値は研究者選択ゆえタグ明示で将来内部化余地・near_archiveは記録列で将来分解で戻す)、信頼問題継続(Step Aでdegenerateを実装前捕捉→改善→ゲートで確認してから完了)、判定はWeb Claude/Taka。
