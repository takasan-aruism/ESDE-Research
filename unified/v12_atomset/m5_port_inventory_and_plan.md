# v12 Atomset M5 — 経験を効かせる「口」の棚卸し + 過去資産 + 並行試行設計（調査）

日付: 2026-06-11 / **調査のみ（実装まだ）。** Taka 指示: 二択に絞らず、何ができるかを広げて報告。
守るのは目的だけ: ①個性化が起きるか ②観察が汚れず「本当に育った」か分かるか ③記録が死なないか（θ NaN）。
無印 ESDE の厳密な frozen/bit-identity は Atomset（言語系の特異処理・Unified）にはかけない。

---

## 0. 最重要の発見 — 経験→torque は v9.7「認知→存在介入」そのもの（再確認すべき境界）

実コード・実ドキュメントで確定:
- M3 の接続（`atomset_bonus → label["torque_factor"] → torque_mag`、`virtual_layer_v9.py:432` の cog_factor の口）は、**v9.7 の z-score torque modulation（`v97_feedback.py:547`、social disposition の z → torque_factor）と構造的に同一**。
- v9.7 は**正式撤回**され、ドキュメントに「**将来の Claude は v9.7 的介入を再導入してはならない**」（`05_primitive_summary.md:148`）、「認知層から θ への介入は入れない」（`09_esde_system_structure.md:79,965`）と明記。
- **なぜ失敗したか（数値発散ではない）**:
  1. **「cid 概念の純粋性を損なう」**（`05_primitive_summary.md:145`）＝認知由来の量を物理に戻すと、個性化が「本物」か「フィードバックの自己言及（反射型）」か分からなくなる＝**観察の汚染**。
  2. **Taka の v9.13 原則**（2026-04-16、`08_concept_core.md:154` / `05:522`）: 「**認知層は物理層を支配しない。効果は劇的ではなく、統計的に多少の差が出る程度。**」劇的な効果を期待する設計は**神の手**に近づく。比喩「健康に気をつけても寿命は 10倍100倍変わらない、統計的に多少差が出る程度」。

### Taka の 3 つの guard は v9.7 教訓そのもの（整合）
| Taka の guard | v9.7 教訓での対応 |
|---|---|
| ②観察が汚れず「本当に育った」か | **cid 純粋性の汚染**＝反射型フィードバックの自己言及。**→ shuffle 対照が必須の防御** |
| ③記録が死なない（θ NaN） | 数値の一線（v9.7 自体は tanh で有界＝発散せず） |
| （新）効果は劇的でなく統計的 | **v9.13 原則そのもの**。**M5 の 10²¹⁴ 裾＝「劇的/神の手」失敗モード** |

### 含意（設計の北極星）
- **Unified の「結果出したもん勝ち」は v9.7 の*禁止*を解除する**（cognition→physics を試してよい）。**だが v9.13 の「効果は統計的に多少の差」は guard として生きる**——これは Taka 自身の原則で、Atomset でも「本物の個性化＝slight」を狙う指針。
- **過度に振らせる（Taka「揺らして波及を観察」）は*観察のための耐震テスト***。建物が住むのは mild な領域。**over-drive で破壊点・波及構造を見る／実regime は slight**、の二段で矛盾しない。
- **→ 1 つ確認したい論点（Taka へ）**: Unified の relaxation は v9.7 の*禁止*だけ解くのか、それとも v9.13「slight statistical」guard も外すのか。私の読みは「**禁止は解く・slight guard は残す（over-drive は観察用）**」。

---

## 1. 経験を効かせられる「口」の棚卸し（実コード、15 ポート）

全て**物理/存在層**（認知層 Q/C/familiarity は書込禁止の被観測面）。per-CID で直接狙えるもの＝経験を個体別に効かせられる。

### per-CID 直接アドレス可能（経験を個体別に効かせられる＝本命群）
| 口 | 効かせる先 | 呼び方 (file:line) | 層 | 性格 |
|---|---|---|---|---|
| **T torque (cog_factor)** | θ 回転（位相を phase_sig へ） | `virtual_layer_v9.py:432` `label["torque_factor"]` | 存在 | **v9.7/M3 の道**。自己の「向き」を効かせる |
| **E energy inject** | node E（活性） | `genesis_physics.py:232` `inject(state,target_nodes)` | 存在 | 自己の「燃料/存続」 |
| **L latent boost** | link 誕生確率 L_ij | `realization.py:76` / `set_latent(i,j,+)` | 存在 | **関係（他者との結合）を作る** |
| **F fertility** | latent 補充率（link 再生） | `realization.py:50` `state.F[n]` | 存在 | 自己周りの結合再生力 |
| **H boundary hardening** | 境界 link 保護（存続） | `v43:319` hardening dict | 存在 | 自己の「殻」を守る |
| **Z chemistry** | 化学状態 Z（合成段階） | `chemistry.py:70` `state.Z[n]` | 存在 | 自己の成熟段階 |
| **P theta nudge** | θ 確率摂動 | `v43:374` pressure | 存在 | 自己の「揺らぎ」 |

### global（per-CID は topology 経由で間接）
beta/R 共鳴減衰、cycle_weights、K_sync（同期結合）、gamma/flow、decay_rate、c_max。

### 新ポートを足す余地（言語系特異処理）
torque_multiplier の per-CID override、physics.inject の per-CID semantic zone、per-CID-local 共鳴/予算。Unified なので追加は可。

### 種類分けと口の自然対応（(B) を具体化＝新しい試行候補）
M5 の SELF/OTHER 軸分割は、口にも自然に割れる:
- **SELF 経験（自己の動き）→ 自己存続系の口**: E（燃料）/ F（再生）/ H（殻）/ decay。
- **OTHER 経験（関係）→ 関係系の口**: L（他者と結合）/ H 境界 / intrusion（外への結合）。
- **T torque（θ）は v9.7 の道**＝最も「神の手」リスクが高い口。**含めるが slight 限定 + shuffle 対照必須**。

---

## 2. 過去資産は使えるか

### (a) 5 パターン性格（v10.4、`v106_post_process.py:510`）— **使える（独立ラベルとして検証に）**
- core/near_core(自己寄り＝強い核 5,5,5) / capture/bridge/peripheral（他者寄り＝捕獲型 2,5,5・橋渡し 2,4,5）。size-3 α の n_core 三つ組で live 分類。
- **これは「自己寄り↔他者寄り」が ESDE の実在する性格構造であることの過去検証**＝M5 の SELF/OTHER 軸分割の裏付け。
- **流用**: 経験で育った OTHER 軸が capture/bridge 所属と相関するか、SELF 軸が strong-core と相関するかを見る＝**「経験が本物の性格を追えているか」の独立検証**（guard ② を補強、shuffle と別系統の確証）。

### (b) disposition 4 軸（v9.8b、`v98b_introspection.py:853`）— **教訓が直接効く + 代替信号**
- social（n_partners）/ stability（構造サイズ CV の逆）/ spread（attention entropy）/ familiarity（平均親密度）。
- **観察専用、torque/action へ feedback 禁止**（`v98b:10,105` 「torque/action への feedback はしない」「NEVER fed back」）＝**まさに v9.7 と同じ禁則**。Atomset はこれを*あえて破る*ので、**disposition 観察専用化の理由＝guard ② の出所**を常に意識。
- **流用**: social ≈ OTHER 信号の代替/比較。経験信号と disposition の一致を見れば「経験が既知の性格指標と整合するか」が分かる。

### (c) v9.7 失敗（§0）— **境界の教訓そのもの**。再現しないための shuffle 対照 + slight 限定。

---

## 3. 並行試行の土台（選ばず全部試す）

**実現可能**: 24 seeds の `multiprocessing.Pool` パターンで、(方法 × shuffle × seed) を並行 smoke。経験計算（robust_z + 種類分け + 衰退 + floor 10×）は共通、**口の接続だけ差し替え**。

### 試行する「方法」（広く、過去資産由来も含む）
| 方法 | 接続 | 由来 |
|---|---|---|
| **M-T** torque scalar | 経験集約 → torque_factor（θ） | M3/v9.7 の道（既知、対照基準） |
| **M-E** energy | 経験集約 → node E inject | 自己存続 |
| **M-split** 種類別物理 | SELF経験→E/F/decay、OTHER経験→L/H | (B) 種類分けを物理まで貫通（§1） |
| **M-L** relational link | OTHER経験 → link 誕生/強度 | 関係を物理で表現 |
| （拡張）M-multi | 複数口の合成 | 結果次第 |

各方法 × **shuffle 対照**（経験を cid 間でランダム入替）× seeds。

### guard を測る（守るのは目的）
1. **①個性化**: 結果の動態（lifespan / coherence / 構造 / 5パターン所属）で CID が分かれるか（per-CID、n_core 別層化）。
2. **②汚染なし（shuffle 対照）**: real で個性化、shuffle で消える/弱まる＝**本物**。shuffle でも同じに出る＝v9.7 の反射型自己言及（偽）。**+ 5パターン/disposition との独立一致**で二重確認。
3. **③記録が死なない**: θ NaN 監視 + **効果が slight か（v9.13）**＝効果量が「統計的に多少」レベルか、神の手（劇的）になっていないか。over-drive は観察用に別途。

### θ への影響を slight に保つ（v9.7 を再発させない技術）
α を θ 耐性で決める（0.5 以下から）+ floor 10× + 衰退 + **効果量を監視**（cohens_d 等が「劇的」でない範囲）。over-drive 版は破壊点観察用に分離。

---

## 4. 2AI に並行で聞く価値がある論点（Taka 判断）

- **GPT（監査視点）**: 「経験→物理は v9.7 と同型。Unified relaxation は禁止だけ解き、v9.13『効果は statistical slight』guard は残す——この線引きで shuffle 対照と効果量監視は十分か。反射型自己言及を検出する対照設計に穴はないか。」
- **Gemini（設計視点）**: 「種類分け（SELF/OTHER 経験）を物理の口（自己存続系 vs 関係系）に対応させる M-split は、ESDE の階層（存在/関係）と整合するか。5 パターン（自己寄り/他者寄り）の過去構造と接続できるか。」

---

## 5. 確定・次

- **確定（調査）**: 口は 15、per-CID 本命 7（T/E/L/F/H/Z/P）。経験→torque は v9.7 と同型で、guard は v9.7 教訓そのもの（汚染→shuffle、神の手→slight+floor、θ NaN→監視）。過去資産は 5パターン（独立検証）と disposition（教訓+代替信号）が使える。並行試行は Pool で実現可能。
- **次（実装、Taka 承認後）**: 並行試行 substrate を組む（M-T/M-E/M-split/M-L × shuffle × smoke seeds、3 guard 計装、θ 監視）。**選ばず、結果が出た方法を採る。**
- **Taka に 1 点確認**: §0 の「Unified relaxation は v9.7 の*禁止*を解くが、v9.13『slight statistical』guard は残す（over-drive は観察用）」——この読みで合っているか。合っていれば substrate を組む。

## ファイル
- 参照: `m5_typesplit_decay_report.md`（種類分け+衰退+floor）、`m5_formula_selection_report.md`（robust_z）
- 実コード: `virtual_layer_v9.py:432`（torque 口）、`genesis_physics.py:232`（inject）、`realization.py:50,76`（L/F）、
  `v97_feedback.py:547`（v9.7 原型）、`v98b_introspection.py:853`（disposition）、`v106_post_process.py:510`（5 パターン）
