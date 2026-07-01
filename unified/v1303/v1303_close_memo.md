# v1303 クローズ memo（attention input side の確立）

*作成*: 2026-07-01、Code A（Taka 7 条件で判定）。**read-only・物理非書込・判定なし #12。これ以上 v1303 に試験を足さない。**

v1303 の目的＝**attention input side の確立**（emitter → selector-prototype → 分布読み → output schema 固定）。ESDE が自分の珍しさで注意候補を pull する所まで。投影・応答方向・子ESDE・Atom 接続は v1303 非対象（v1304+）。

## クローズ 7 条件（充足で v1303 を閉じる）

| # | 条件 | 充足 | 根拠 |
|---|---|---|---|
| 1 | emitter 群の棚卸し完了 | ✓ | Now(v1303f) / Archive persistence(v1303e) / B_Gen(v1303h) / dynamic rarity・link rarity(v1303i) |
| 2 | 重複・言い換え・退化列の整理完了 | ✓ | global θ(raw θ と 0.99)・within_cid θ(within_ncore と 0.988)・R_positive(98% 欠損)・C-Q 冗長 を不採用 |
| 3 | selector-prototype 実装完了（cutoff なし pull） | ✓ | v1303j Step A（珍しさ比例ルーレット 1 本引き・研究者 cutoff なし） |
| 4 | 単発 trajectory でなく per-t distribution を本体にする方針確定 | ✓ | v1303j Step B（single-draw は chance≈1/eligible 支配・marginal は露出時間支配・per-t を本体に） |
| 5 | 正式 eye(4) / 補助 eye(1) / 不採用 eye 決定 | ✓ | Taka + GPT 判断・`attention_eye_registry`（now_theta / archive_theta_percentile / link_rarity / bgen_static_prior + aux_peer_relative_theta） |
| 6 | attention output schema 固定 | ✓ | `v1303_final_attention_output_seed0.parquet`（t×cid×eye・p_select_given_eye_t 本体・366,605 行） |
| 7 | 投影・子ESDE・Atom 接続を次版 stub として明記 | ✓ | 本 memo §6 |

→ **7 条件充足で v1303 クローズ**。v1303k / Step C を作らない。

## v1303 で確定した事実（Step A/B の残す知見）
- 選択確率は正規化 salience で厳密（`p=clip(sal,0)/Σ`・RNG 不要）。many-RNG(N=200) は sampler 検証で corr_emp_exact 0.9999＝バグなし。
- per-t で目は distinct（now×peer 0.55 / now×link 0.48 / now×persist 0.43 / now×bgen −0.05）かつ全 eye が uniform と区別可（per-t KL>0）。
- 構造は「5 独立系」でなく **dynamic physical cluster（now/archive_θ/link/peer・per-t corr 0.43–0.77）+ static prior（bgen・直交）**。link は非θゆえ物理側の別軸。多系性は薄いが完全に θ だけでもない。軸数を成果に数えない。
- 命名訂正: persist_thetapct は duration lens でない（長 segment を過剰選択せず）→ `archive_theta_percentile`。
- 方法論の落とし穴 2 件を実証・記録: (A) single-draw 一致率は chance 支配 (B) marginal 分布相関は D 型平均化で潰れる。両方 per-t / exact で回避。

## §6. Projection stub（v1304 の接続要件・v1303 では作らない）
selector（何を注意候補として pull するか）と projection（注意→応答方向）を混ぜない。以下は設計視界に入れるのみ：
- **selected CID 分布を子ESDE に渡す候補**：per-t の `p_select`（cid×eye 分布）を子ESDE 生成・選別・再演算の入力に。
- **子ESDE 生成条件**：どの注意分布がどの内部環境/小世界を派生させるか（CID 由来の内部環境・外部 inject でない）。
- **子ESDE が読む input schema**：本 schema をそのまま渡せる形に。
- **Taka 存在論の接続点**：投影の本質は「一致率が上下してもセンターが反応し、その反応から現実を作り込む」（完全一致を追わない）。スコープ問題＝①観測空間を閉じ ②中で一致率 ③残差 ④残差が意味を持つなら閉じ方を更新（動的な統計）。**④再スコープの引き金も ESDE 自身の珍しさ/驚きから来る必要がある**（研究者が決めたら神の手が戻る・注意と再スコープを同じ機構で閉じる）。
- → **v1304 = attention projection / child-ESDE interface** で本体化。子ESDE はまだ、ただし遠くない。

## クローズ後の非対象（v1303 で作らない）
投影・応答方向・子ESDE・Atom 意味接続・内部環境・外部入力・cross-eye 合成 pull。すべて v1304+ の主題。
