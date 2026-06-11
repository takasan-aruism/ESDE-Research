# v12 Atomset M5 — センサー(入力)/応答(出力)経路と「口」の接続性（調査）

日付: 2026-06-12 / **調査のみ。** Taka 出口の釘刺し: Atom の系はセンサー入力・応答出力の経路に**地続き**でなければ孤立した二つの系。
Unified の目的＝会話できる ESDE（人間入力→センサー→ESDE 内部→Genesis で揺れ/注意→応答→人間）。
→ 口の選択に**第4評価軸④**を追加: ①個性化 ②shuffle で本物か ③θ NaN ＋ **④その口が入力/出力経路に繋がるか**。
（着手前は私もこの経路を把握しておらず＝実コードで調べた。過去研究は財産。）

---

## 0. 結論（先に・正直に）

- **会話パイプラインの「通貨」は E（エネルギー）・θ（位相）・link・phase_sig。** 入力も出力もこの 4 つで動いている（実コードで確定）。
- **入力（センサー）の実体＝`physics.inject(state, target_nodes)` ただ一本**。書く先は **E / link(S,alive_l) / alive_n**。**θ は inject では書かない**（semantic_pressure が θ+L を書くが global・休眠）。狙う相手は **phase_sig 一致**で選ぶ（`exp(-λ·d(label.phase_sig, theme_phase))`）。
- **応答（出力）の実体＝位相励起分布** `exc[CID]=Σ_n E[n]·exp(-λ·d(phase_sig, θ[n]))`（v1111d）。読む先は **E / θ / phase_sig**。
- **→ ④ で 15 の口を採点すると、E・L・θ が地続き、Z/F/H は孤立**（個性化が出ても出口が無い＝Taka が避けたい「二つの系」）。
- **最大の正直な穴**: 言語→Atom→target_nodes の橋は**未実装**（atom_centroids は frozen data として在るが消費コードゼロ）。live→人間の応答合成も無し。**会話パイプラインは未完**。ただし「inject(E/L) を phase 一致で撃つ」「位相励起で読む」**部品は実在し走っている**ので、経験を**繋がる通貨（E/θ/L）に載せれば**橋が後で挿さる場所に置ける。

---

## 1. センサー（入力）経路 — 実コードで何が在るか

| 機構 | file:line | engine に書く先 | 相手選択 | 成熟度 |
|---|---|---|---|---|
| **physics.inject**（本命・唯一の実入力） | `genesis_physics.py:240-246` | **E[n]+0.6 / alive_n / S(link)+0.3 / alive_l** | target_nodes（per-CID/per-node） | **本走・実証**（stage3, v1111c-e 72 run） |
| 相手の撃ち方（addressing） | `v1111c.py:120-141` | — | `w=exp(-λ·d(label.phase_sig, theme_phase))` → top-K label の core node | 本走 |
| semantic_pressure（環境） | `v43_engine.py:374` | **θ nudge + latent(L)** | global（0.5% node/window）休眠 | stage4 で条件化のみ |
| stage2 external loop | `stage2_step_cde:103` | **書かない**（engine の外部 attr に append） | — | stub |
| **言語→Atom→engine 橋** | （存在しない） | — | — | **未実装（aspirational）** |

要点: **入力は E と link を書く**。θ は inject では書かない（θ を動かすのは torque か semantic_pressure）。**撃つ相手は phase_sig 一致で決まる**。

## 2. 応答（出力）経路 — 実コードで何が在るか

| 機構 | file:line | engine から読む先 | 出力の形 | 成熟度 |
|---|---|---|---|---|
| **位相励起分布**（最も応答らしい） | `v1111d.py:132-148` | **E / θ / label.phase_sig** | per-CID 励起分布 `Σ_n E[n]·exp(-λ·d(phase_sig,θ[n]))` | 本走（24 seeds） |
| 位相一致重み | `v1111c.py:120-128` | phase_sig / θ / E | per-CID 重み分布 | 本走 |
| v1103 応答 atom 分布 | `v1103_step_c` | atom_centroids（live でない） | per-atom 応答確率 | 本走（データ） |
| v1114 内部注意 | `v1114/step1` | source_events（post-hoc） | per-CID alert | 本走（post-hoc） |
| stage2 telemetry | `stage2_step_cde:47` | alive_n/l 数 | 計数（応答でない） | 本走 |

要点: **出力は E・θ・phase_sig を読む**。**live engine→人間の応答合成は未実装**（v1111 は過去 run の offline 解析）。

---

## 3. ④ 接続性マップ — 15 の口のうちどれが地続きか

会話の通貨＝**E / θ / link / phase_sig**。各口を「入力が書くか・出力が読むか」で採点:

| 口 | 入力(inject/pressure)が書くか | 出力(励起)が読むか | ④ 評価 | 種類分けとの相性 |
|---|---|---|---|---|
| **E energy** | ✅ inject の本体 | ✅ 励起の E | **★★★ 両端に地続き** | **SELF 経験（自己存続）に最適** |
| **L link** | ✅ inject が link 生成 | ◐ link→E 流れ→θ 経由 | **★★ 入力側に地続き** | **OTHER 経験（他者と結合）に最適** |
| **T torque(θ)** | ◐ semantic_pressure(休眠) | ✅ 励起の θ + addressing | **★★ 出力/addressing に地続き**（＝v9.7 の口） | どちらも可だが神の手リスク最大 |
| **P θ nudge** | ◐ pressure(global,休眠) | ✅ θ | ★ 出力側（global で per-CID 弱い） | 揺らぎ |
| F fertility | ✗ 直接入力なし | ◐ 間接(link 再生) | ☆ 弱い | — |
| H hardening | ✗ | ◐ 間接(link) | ☆ 弱い | — |
| Z chemistry | ✗ | ✗ | **☆ 孤立（④ 不成立）** | — |

### 読み（Taka の ④ への答え）
- **E が最強の候補**: inject の本体（＝入力が書く通貨そのもの）かつ励起出力が読む。経験が E を育てれば「**入力が入る口・経験が育てる口・応答が読む口が同一**」＝Atom の系と会話の系が**一つ**になる。しかも E は「燃料/存続」で θ より神の手リスクが低い（v9.7 は θ）。
- **L が OTHER 経験の出口**: inject は link も作る。OTHER 経験（関係）→ link 生成は「関係を物理で表現」かつ入力経路と地続き。
- **θ(torque)は出力/addressing と地続きだが v9.7 の口**＝個性化は出るが神の手リスク最大。比較対照として残す（slight 限定＋shuffle）。
- **Z/F/H は会話の通貨に触れない＝④ 不成立**。個性化が出ても出口が無いので**優先度を下げる**（Taka 指示通り）。

### 会話に繋がる種類分け（M-split-connected）＝有力な第一候補
- **SELF 経験（自己の動き）→ E（自分の node energy/存続）** ＝入力が書く通貨・出力が読む通貨・自己軸。
- **OTHER 経験（関係）→ L（他者との link）** ＝入力が作る通貨・関係軸。
- これなら **経験が育てる口（E,L）＝入力が入る口（inject の E,L）＝応答が読む口（励起の E、link→θ）** が全部同じ系。**Atom の系と会話の系が一つ。**

---

## 4. 並行試行 substrate（④ を評価軸に追加、繋がる口を優先）

| 方法 | 経験→口 | ④ 接続性 | 残す理由 |
|---|---|---|---|
| **M-E** | 経験集約 → E inject | ★★★ 入力本体＋出力読取 | 第一候補（会話と一体） |
| **M-split-conn** | SELF→E、OTHER→L | ★★★/★★ | 種類分け＋会話一体（有力） |
| **M-T** | 経験集約 → torque(θ) | ★★ 出力/addressing（v9.7 口） | 比較対照・slight 限定 |
| M-L | OTHER → link のみ | ★★ 入力側 | 関係単独 |
| ~~M-Z/F/H~~ | — | ☆ 孤立 | **④ 不成立で優先度下げ** |

各方法 × **shuffle 対照** × seeds。評価軸 **①個性化 ②shuffle で本物 ③θ NaN ④接続性**（その口の量が inject に書かれ／励起に読まれるか＝実コードで判定済、上表）。

---

## 5. 正直な穴と次

- **未実装の穴（財産化すべき課題）**: ①言語→Atom→target_nodes 橋（atom_centroids→theme_phase/target の変換コードがゼロ）②live engine→人間の応答合成。**これが無いと「人間と会話」までは届かない**。ただし橋は **phase_sig addressing の上流**に挿さる場所が決まっており、下流（inject E/L・励起読取）は実在。
- **→ 経験を E/L（と比較で θ）に載せる**のは、橋が未完でも「会話の通貨に地続きの場所」に Atom の系を置くこと＝Taka の「会話に繋がる形で Atom を作る」を満たす。
- **次（実装、Taka 承認後）**: 並行試行 substrate を組む。**M-E / M-split-conn を第一群、M-T を対照**、M-Z/F/H は落とす。④ は実コードで判定済（E/L/θ が地続き）なので、試行では ①②③ を計装し、④ は「育てた量＝inject が書く量／励起が読む量か」で各 run にタグ付け。
- **2AI 論点（Taka 判断）**: GPT に「E を経験で育てると、inject 入力と経験が同じ E を奪い合う＝入力と経験が干渉しないか（信号の混線）」、Gemini に「SELF→E / OTHER→L の対応は ESDE の存在/関係階層と橋の addressing(phase_sig) に整合するか」。

## ファイル
- 参照: `m5_port_inventory_and_plan.md`（15 口・v9.7 境界）、`m5_typesplit_decay_report.md`（経験計算）
- 実コード: `genesis_physics.py:240`（inject=入力）、`v1111c.py:120`（phase addressing）、`v1111d.py:132`（励起=出力）、
  `v43_engine.py:374`（semantic_pressure）、`stage3_step_b2_smoke.py:199`（inject 実証）
