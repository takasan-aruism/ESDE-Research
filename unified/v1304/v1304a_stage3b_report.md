# v1304a Stage 3b 報告 — 統計的やり直しで inconclusive を解消

*作成*: 2026-07-03、Code A。**Stage 3 smoke の統計不備を修正した本番。read-only・親へ feedback なし・物理非書込・判定なし #12。親 profile は v1303 final(seed0) のみ＝「親 seed0 に条件付けた結論」。**
*成果物*: `v1304a_stage3b.py` + `outputs/v1304a_stage3b_*`（liftcorr / drawmeans / tests・base0/base1）。R=20 draws × 3群 × M=30子 × 4eye × 2 base系列 = 14,400 child。

---

## 0. 結論（先に）
- **inconclusive は解消**。Stage 3 smoke の「(b)/(c) 寄り」は撤回済（統計不備）。本番の結論：
- **composition は親特異な集団構造乖離を出せる — ただし lift が転移チャネル s_avg と相関する目だけ。該当は `bgen_static_prior` のみ。**
  - bgen：parent−shuffle が両 base 系列で Holm 生存（link_density t−4.8/−5.2・p_holm 0.003/0.001）、**shuffle−canon は null**（p 0.17–0.93）＝真の親特異、符号一貫性 0.80–0.90。
  - 動的 salience 目（now_theta/archive/link_rarity）：parent−shuffle は Holm 生存ゼロ（now link_density t−0.25/−0.56）＝分離なし。
- **機構＝分離 ∝ corr(lift, s_avg)（仮説 支持）**：bgen だけ |corr|=0.55（強）で s_avg をずらせる。他は弱く分離せず。
- **重要な留保**：bgen は静的誕生 prior で、s_avg と相関するのは両者が同じ M_c 誕生量だから（誕生物理の関係）。＝**分離するのは静的 prior であって、センターが瞬間ごとに拾う動的 salience（θ/link）はチャネルに届いていない**。この読み替え（出口 a か・どの意味で a か）は Taka。

## 1. 修正した統計（Stage 3 smoke の不備の解消）
| 不備（Stage 3） | 修正（Stage 3b） |
|---|---|
| 単一 composition 抽選 | **R=20 回リサンプル**・分析単位＝draw（抽選分散を捕捉） |
| unpaired 過大 noise 床 | draw 内で engine seed を群間 matched＝**paired 差**を反復単位に |
| 多重比較未補正 | primary=**parent−shuffle** 事前固定・**Holm 補正**（24検定）・生 t/符号一貫性併記 |
| lift 定義依存を隠蔽 | **eligible-only=primary / alive=参考** の2定義併記（下表） |
| seed0 のみ | **base 2系列**（子側）で再現確認。親 profile は seed0 のみと明記 |

## 2. lift 定義依存の開示（corr(lift, s_avg)）
| eye | eligible(primary) | alive(参考) |
|---|---|---|
| now_theta | −0.164 | +0.070 |
| archive_theta_percentile | +0.260 | +0.288 |
| link_rarity | +0.042 | +0.289 |
| **bgen_static_prior** | **−0.545** | **−0.545** |
- 動的目の corr は定義で動く（link 0.04↔0.29）＝profile レベルの弱い関係は「robust に近い」止まり。**bgen だけ定義非依存に −0.55**（per-cid 定数ゆえ）＝分離を出す目の相関は頑健。

## 3. primary：parent−shuffle @ t_mid（Holm・両 base）
| eye / sig | base0 t (p_holm) | base1 t (p_holm) | 符号一貫 |
|---|---|---|---|
| **bgen link_density** | **−4.83 (0.003 ✓)** | **−5.16 (0.001 ✓)** | 0.90/0.80 |
| bgen n_labels | −3.42 (0.066) | **−5.38 (0.0008 ✓)** | 0.65/0.90 |
| bgen label_density | −3.42 (0.066) | **−5.38 (0.0008 ✓)** | 0.65/0.90 |
| now/archive/link（全 sig） | Holm 生存なし（\|t\|≤1.7・p_raw>0.10） | 同 | — |
- 要約：parent−shuffle 生 p<.05 ＝ base0 4/24・base1 3/24、**Holm<.05 ＝ base0 1/24・base1 3/24（全て bgen）**。

## 4. 親特異性の確定（bgen の 3対比）
| sig | parent−shuffle(親特異) | shuffle−canon(null床) |
|---|---|---|
| link_density | base0 t−4.83 p0.000 / base1 t−5.16 p0.000 | **t−0.09 p0.93 / t−1.06 p0.30（null）** |
| n_labels | t−3.42 p0.003 / t−5.38 p0.000 | t+0.86 p0.40 / t+1.42 p0.17（null） |
- **shuffle≈canon（composition 一般効果なし）なのに parent≠shuffle** → 効いているのは lift の量でなく **cid↔lift 対応**＝真の親特異。方向は一貫して負（parent の集団は link_density/n_labels が低い）。
- 機構的整合：bgen-lift は s_avg と −0.55 → 低 s_avg cid を多く構成 → 低 plb → 少リンク。bgen は lift の分散も最大（[0,2.16] std0.48）で、相関×分散の両方が揃う唯一の目。

## 5. 出口（設計 §3 に対応・判定は Taka）
- **(a) 親特異あり（bgen）**：composition は「注意が転移チャネルと相関する時」親特異な子集団を作る＝仮説「分離 ∝ corr(注意,チャネル)」が生存。→ composition を receiver contract の基礎にできる**素材**。
- **ただし動的 salience 目は (b)/(c)**：now_theta/archive/link_rarity はチャネル s_avg と相関せず分離しない＝「今のセンターの動的な濃淡は s_avg チャネル経由では子集団を分けない」。
- **統合的な読み（Taka 主題）**：分離を出したのは**静的誕生 prior**であり、その相関は誕生物理の関係。＝「センターの注意が子を形づくる」と言えるかは、(i) 静的 prior 経由でも a と読むか、(ii) 動的 salience が届く別チャネルを探すか、(iii) チャネル非依存に注意を効かせる別機構（feedback/動的統計）へ、の分岐。inconclusive でなく事実の上での分岐になった。

## 6. 実施範囲・規律
- 実施：R=20×3群×M30×4eye×2base＝14,400 child・paired・Holm・2定義 lift・2 seed系列。read-only・親へ feedback なし・物理非書込・分離幅に期待値置かず（v3.2）。
- 限界：親 profile は seed0 のみ（条件付き）。other-parent null は未実施（結果を見て・§2）。子側 N=150 固定・plb のみ per-cid（変数1本）。
- 判定（出口 a/b/c・composition 継続か別チャネル/feedback か）は Taka。

## 6b. 自己監査（2026-07-03・Code A）— コードバグなし・framing の過大読みを 3 点補正
Stage 3 で結論を過剰接続した反省から Stage 3b も敵対的に再監査。**コードバグ・設計読み違いは無し**（paired 設計＝draw 内で engine seed を群間 matched・群別に独立 plb、composition・lift 2定義・Holm・t検定・draw 独立性は正しい）。bgen 効果も本物・機構整合・2 base 再現（composition が plb を実際に −2.5% シフト＝corr(bgen-lift,plb)=−0.51 駆動、link_density は plb に敏感＝±15%→−0.17 ゆえ −2.5%→−0.015 と同オーダー同符号、少数 cid 依存でない＝effective count 35/45）。ただし結論を変えない範囲で **framing を 3 点補正**：
1. **効果量は小さい（有意 ≠ 大効果）**：固定 plb ペアの per-child 比較（n=24）は t−0.49（有意でない）。**t−4.8 の有意性は R=20×M=30 の平均化 power から**であり per-child 効果は小さくノイズ（std 0.062）に埋もれる。→「**小さいが robust**」と読む。
2. **「仮説 支持」→「1つの高 corr eye(bgen)で consistent」に降格**：高 corr eye は bgen 1個のみで graded な dose-response でなく閾値的 1 例。
3. **動的 eye の null は 45 制限 slice（注意の 20-26%）上の測定**：off-channel 74% と別チャネルは未検証。「動的 attention が子物理と無関係」でなく「45-slice が s_avg と相関しない」まで。

## 7. 一文サマリ
v1304a Stage 3b（統計やり直し・#12）── Stage 3 smoke の不備（単一抽選・unpaired 過大noise床・多重比較未補正・lift定義依存）を R=20 リサンプル×draw単位paired・primary=parent−shuffle事前固定+Holm・lift 2定義併記・base2系列で修正した結果、**inconclusive 解消＝composition は親特異な集団乖離を出せるが lift が転移チャネル s_avg と相関する目(bgen |corr|0.55)のみ**（bgen parent−shuffle link_density t−4.8/−5.2 両base Holm生存・shuffle−canon は null=真の親特異・符号一貫0.8–0.9、動的salience目 now/archive/link は corr弱く Holm生存ゼロ=分離なし）、機構は分離∝corr(注意,チャネル)で仮説支持、ただし**分離する bgen は静的誕生priorで s_avg との相関は誕生物理由来＝動的salience(θ/link)はチャネルに届かず**、出口は bgen で(a)素材/動的目で(b)(c)という事実上の分岐（静的prior経由でaと読むか・動的が届く別チャネル探すか・feedback へ)で判定はTaka、親profileはseed0条件付き・other-parent未実施。
