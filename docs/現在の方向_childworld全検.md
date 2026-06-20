# 現在やろうとしていること — child-world 全検と CID 個性の検出（2026-06-21 時点）

*作成*: 2026-06-21、Code A
*目的*: 「今 ESDE で何をやろうとしているか」を新スレッド/3AI が一読で掴むための現況資料。判定は Taka。
*第一参照*: `docs/ESDE_技術仕様書.md`（現行技術仕様）/ `docs/ai_summaries/07_unified_summary_addendum_v13_childworld.md`（v13 詳細）/ `unified/v13_childworld/`（全データ）。

---

## 1. 一言で

**「CID（観察対象）の誕生時の形が、それ自身の小さな世界（child-world）をどう変えるか」を観察し、CID に個性（その CID 固有の系の振る舞い）があるかを、交絡を排した統計で検出しようとしている。**

直近の主戦場は Atom 空間（v12）から **child-world（v13）** に移った。両者は無関係 ―― v12 は「CID を Atom 326 の意味空間で読む」、v13 は「CID の誕生形態を物理 param に写して小さな ESDE を実際に回す」。

## 2. なぜ child-world か（v9.13 方針との整合）

- child-world は **物理層を一切いじらない**（v9.13「物理を支配しない・記憶を読む」の枠内）。CID の誕生時形態 M_c を**読んで**子系の初期 param に写すだけ。child engine は in-memory で親物理に書き戻さない（一方向）。
- ＝「CID をいじって物理に効かせる」逸脱A でも「異なる系の対応関係」逸脱B でもない。各 child は独立な同系内動学（過去の失敗フレームを踏まない）。

## 3. ここまで分かったこと（v13 の確定事実・判定なし）

1. **4 knob テスト（N/plb/K_sync/初期θ ← B_gen/S_avg/r_core/phase_sig）で系は実際に変わる**。pairing を見る置換検定で `K_sync→sync_order`・`plb→link/label_density` が両 ratio p<0.005。ただしこれは「knob が物理 param を直接動かす」manipulation check。
2. **「CID 個性が効かない（real≒shuffle）」は統計の罠だった**。署名の mean/std 対照は shuffle で構造上不変＝pairing を見ない。検定を pairing 基準にすると個性は検出される。
3. **像が保持して見えた相関の多くは run 長の交絡**（`life→n_labels` は観測窓を寿命に同期させた副作用、交絡を外すと消える）。
4. **写像は K_sync 100%・θ 84% で個性を伝えている**。弱いのは N（源 B_gen が n_core にほぼ連動して均質）と plb（設計幅 ±15% が狭い）の 2 点だけ。

## 4. 次にやること（確定した方向）

### (b) 全検 — 全 CID 値を全物理 param に取り込み、系がどう変わるか
- その後 **n_core 跨ぎ**（n_core=2,3,4,5）に拡張。母集団 85 CID（2:54/3:3/4:11/5:17）。
- まず「回るか」を見る（seed≈12・全跨ぎ・2ratio で ~12h の見積もり）。

### 譲れない一点（Taka）= 「10 全て取り込む選定に合理性があるか」
これを **3AI 合議**（GPT 監査・Gemini 設計・Web Claude 統合）＋Taka で確定する。合議を空中戦にしないため判断材料は調査済（`cw_fulltest_selection_material.md`）:
- CID 値は実質 **~5-14 独立軸**（pooled の低次元は n_core 産物・stratum 内はもっと高い・M_c4 すら共線で phase_sig 以外は stratum 依存）。
- 物理 param も **~6-7 独立軸**（状態変数 L/θ/S/E/R/Z で束ねられる）。
- ＝「10/25 全部繋ぐ」は冗長で交絡を孕む。合理的全検は「独立 CID 軸 → 独立物理軸」の対応。
- **knob 数はコストを増やさない**（driver は CID×対照×seed）。膨らむのは n_core 跨ぎと seed 数。

## 5. 設計上の必須要件（v13 監査で確定した「やり方」）

次の全検 run は以下を満たす（過去の交絡を繰り返さないため）:
1. **比較は pairing 基準**（knob→署名の paired 相関 + 多数置換 null の perm-p/CI）。署名 mean/std の real-vs-shuffle 対照は単独では使わない（pairing 盲目）。
2. **観測窓を揃える**（示量署名 n_labels を異なる run 長で cid 間比較しない。共通窓スナップショット or 示強量 or 定常後）。
3. **対照を対称に**（canon も run 長可変。全対照を同一観測窓に）。
4. **seed ≈12**（sync_order/link_density は ~10-14 seed で SE が cid 間信号の 1/4 を切る）。
5. **過剰精度をやめ perm-p/CI を付す**。manipulation check と CID 創発を報告で区別。
6. 選定（独立代表）は **n_core ごとにやり直す**（共線構造が stratum で変わる）。

## 6. やらないこと / 留保
- 「CID 個性が原理的に効かない」とまだ結論しない（pairing 検定で有意が出ている）。
- 選定確定・実行は 3AI 合議＋Taka の前にやらない。写像を「正しい一つ」に決めない。
- 親物理書き戻し / crown（「自我」「会話」「Unified 成立」等）。
- 「5000 ノード」は親 v918 main の N であって child の目標ではない（child は N≈110-354 の小規模で設計どおり）。

---

*以上、現在の方向（Code A、2026-06-21）。要約: child-world で CID の個性を交絡なく検出する段に入っており、次は全検だが「全部繋ぐ合理性」を 3AI 合議で詰める。判定は Taka。*
