<!-- ========================================================== -->
<!--  CODE A 編集指示                                           -->
<!-- ========================================================== -->
<!--                                                            -->
<!--  Target file: docs/ai_summaries/05b_primitive_summary_v912_addendum.md  -->
<!--  Action: 新規ファイル作成                                  -->
<!--                                                            -->
<!--  ファイルの中身は下の「----- FILE CONTENT BEGIN -----」    -->
<!--  から「----- FILE CONTENT END -----」までをコピーして      -->
<!--  貼り付ける。指示コメント (この <!-- --> ブロック) は      -->
<!--  実ファイルには含めない。                                  -->
<!--                                                            -->
<!--  Verification:                                             -->
<!--    - 既存の 05_primitive_summary.md は変更しない           -->
<!--    - 05b_ ファイルが正しく作成される                       -->
<!--                                                            -->
<!-- ========================================================== -->


<!-- ----- FILE CONTENT BEGIN ----- -->

# Primitive — v9.11 / v9.12 Addendum

*追記時点*: 2026-04-16 (v9.12 phase 完了)
*対象読者*: 未来の Claude
*親ファイル*: `05_primitive_summary.md` (v9.9 時点の要約)

> **このファイルの性質**: `05_primitive_summary.md` は v9.9 完了前に書かれた原本要約。
> v9.11 で認知捕捉機構 (B_Gen + capture) が確立し、v9.12 で audit が完了した。
> 本 addendum は 05 に対する v9.11-v9.12 追記。
> 05 と併せて読むこと。

---

## v9.11 — Cognitive Capture (事象捕捉フィルタの確立)

### 目的

cid が誕生時の構造 (M_c) と現在の環境 (E_t) を比較し、個体ごとに異なる確率で事象を捕捉する。物理層・存在層への介入なし。

### 核心概念

| 概念 | 定義 | タイミング |
|---|---|---|
| B_Gen | -log10(Pbirth)、cid の構造階層指標 | birth 時固定 |
| M_c | (n_core, S_avg, r_core, phase_sig) | birth 時固定 |
| E_t | (n_local, s_avg_local, r_local, θ_avg_local) | pulse 時抽出 |
| Δ | M_c vs E_t の Weighted L1 距離 (phase は circular) | pulse 時計算 |
| p_capture | 0.9 × exp(-2.724 × Δ) | pulse 時計算 |
| captured | 確率的判定 TRUE/FALSE/cold_start | pulse 時記録 |

### 設計決定 (GPT 補正反映)

1. B_Gen を capture に直接入力しない (n_core バンド支配が capture 差を飲み込むため)
2. phase は circular distance で扱う
3. similarity は Weighted L1 (コサインではない)
4. Variant A (指数減衰、p_max=0.9) を初手採用
5. 誤差各軸 (d_n/d_s/d_r/d_phase) を個別記録

### 4 層構造の確認

| 層 | 役割 | v9.11 での確立 |
|---|---|---|
| 物理層 | 生成基盤 | 不変 |
| 存在層 | θ torque のみ | 不変 |
| 認知層 | 観察・比較・捕捉 | B_Gen + capture で確立 |
| 意識層 (将来) | 認知の検証 | v10.x 以降 |

**B_Gen の導入で「認知層から θ への介入」誘惑が構造的に消滅**。認知層の権限を「観察」に閉じ込めた。

### 結果 (48 seeds short + 5 seeds long)

- capture_rate mean ≈ 0.38 (設計通り)
- 軸寄与: phase 39% + r 34% = 72%、n 14%、s 13%
- L06 長命群 (114 cids): capture_rate 0.307、n_core=5 が 61%、Δ mean 0.414
- B_Gen バンド短長一致、λ=2.724 運用妥当

---

## v9.12 — Audit Phase (実装変更ゼロ)

v9.12 は新機構の実装ゼロ、既存データの分析と設計文書化のみ。

### Phase 1: L06 個別時系列分析

**最重要発見: Δ は i.i.d.** — 自己相関 ≈ 0 (全 lag: 1, 2, 3, 5, 10)。pulse 間の乖離変動はほぼ独立。

事前仮説「M_c 固定 → 時間進行で E_t が乖離 → Δ が蓄積」は**否定**された。

**L06 capture 低下の再解釈**: 時間効果ではなく **n_core 構成効果**。L06 は n_core=5 が 61%、n_core=5 は構造的に Δ ≈ 0.43 で定常。

| n_core | Δ mean | capture_rate |
|---|---|---|
| 2 | 0.252 | 46.4% |
| 3 | 0.355 | 36.8% |
| 4 | 0.410 | 30.8% |
| 5 | 0.433 | 29.2% |

**window-level slope (-0.00032/win)** は生存バイアスで説明可能 (短命 cid 脱落 → 長命 cid 残存)。

**spike vs low**: Δ 上位 10% → capture 15.4%、Δ 下位 10% → capture 50.9%。乖離と capture の逆相関は明確。

**first diverge axis**: 全体では phase 最多 (43%) だが n_core=5 では n 軸最多 (46%)。n_core 別で逆転。

### Phase 2A: コード解析

**phase+r 72% 原因** (コード確定):

| 要因 | 影響軸 | メカニズム |
|---|---|---|
| NORM_N=86 過大 | d_n 圧縮 | n_core∈{2..5} に対し過大、d_n p50=0.23 |
| S_avg ≈ s_avg_local | d_s 圧縮 | 物理層リンク強度の定常性、d_s std=0.13 |
| r_core vs r_local 乖離 | d_r 拡大 | r_core 固定、r_local 変動大 |
| circular_diff 一様性 | d_phase 拡大 | phase_sig 固定、θ_avg_local 変動 |

d_r と d_phase は無相関 (r=0.008)。4 軸は実質独立。**B 仮説 (E_t 定義偏り) は否定**。

**n≥6 欠落の原因** (コード確定):

1. **S≥0.20 連結成分の接続性制約** (主因) — 定常状態で 6 ノード以上の連結成分が形成される確率が構造的に低い
2. **50% overlap フィルタ** (副因) — 大型島ほど既存ラベルと重複してブロック
3. **非空間的リンク形成** (背景) — 一様ランダムで空間クラスタリングなし
4. **stress OFF は存在層成熟の帰結**。副作用として S 分布揺らぎ減 → 大型島頻度低下

コードに明示的なサイズ上限は存在しない。n_core≤5 は動力学的・統計的な帰結。

### 却下された作業

- NORM_N sweep (原因確定済み、確認実験不要)
- E_t 妥当性 audit (B 仮説否定)

### Phase 4: 未決境界問題

Taka 発言「並列基準原理」と「構造と数式の分離統合」を設計原理として記録。認知/意識の境界に関する Q1-Q5 を未決問題としてリスト化。

詳細: `docs/v912_unresolved_boundary_questions.md`

---

## v9.13 への橋渡し

v9.12 の最大の帰結: **S≥0.20 hard threshold の撤去が次の進化の主題**。

### Taka 発言 (2026-04-16)

> Frozenset に関して、ぼちぼち S≥0.20 と向き合うタイミングがきたように思う。なぜなら本来的にこれは神の手だから。動的均衡の哲学がある以上どこかで切り捨てなければならない。後回しにするほど調整が大変になるに決まってるのでさっさとやるほうがいい。

### v9.13 構想

- Pbirth 式を birth probability として使う (構造 × 場 = 確率的 birth)
- S≥0.20 撤去、S_avg は Pbirth の連続因子として機能
- frozenset・budget=1・物理層不変は維持
- n≥6 の自然出現を期待
- 認知層の capture 機構 (v9.11) はそのまま載せる
- Gemini に architecture 設計を依頼済 (`v913_gemini_design_request.md`)

---

## retention への含意 (v9.13 以降の候補)

- Δ が i.i.d. → EMA(Δ) は smoothing にしかならず prediction には無力
- retention の価値は「将来予測」ではなく「**自分の構造的位置を知る**」 (= 主観的基準形成)
- v9.10 MAD-DT の capture 版が自然な設計方向
- ただし v9.13 は S≥0.20 撤去が主題。retention は v9.14 以降

---

## 原本を読むべきタイミング

- v9.11 B_Gen の Pbirth 式導出 (組み合わせ確率 + 物理条件)
- v9.11 capture probability の 3 variant (A/B/C) 比較
- v9.12 Phase 1 L06 時系列の数値詳細
- v9.12 Phase 2A コード解析の d_* 値域計算
- Taka 発言引用 (並列基準原理、構造と数式、S≥0.20 撤去)
- `ESDE_Primitive_Report.md` の v9.11-v9.12 追記部分
- `概念理解.md` の v9.11-v9.12 追記部分 (並列基準、教訓 66-73)

<!-- ----- FILE CONTENT END ----- -->
