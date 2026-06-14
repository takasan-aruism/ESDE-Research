# v12 Atomset — cid_align 設計書 §4 チェック（Code A → 実装前）

**依頼**: Web Claude 設計書（2026-06-14）§4 を実コードで (1) 矛盾しないか (2) 実装可能か (3) 落ちは。**判定（機能した/会話に繋がる）は Taka 領域。本書は観察事実のみ返す。**

*作成*: 2026-06-15、Code A。*親*: Web Claude `v12 Atomset cid_align 設計書`、`cid_align_investigation.md`（prototype 実証済）。
*確認に使った実コード*: `developmental/v106/v106_post_process.py:274-420`（軸エンコーダ）、`developmental/v107/outputs/main/source_events_seed0.parquet`（実カラム）、`unified/v1103/outputs/main/atom_centroids_48d_raw|normalized.parquet`（両在る）、`unified/v1114/step1_internal_attention.py`、`cid_align_prototype.py`。

---

## 0. 一文結論

**§4 全項目クリア——矛盾なし・実装可能・核は prototype で実証済。** 最大の crux は「seed_max が offline で解ける」＝build_cid_vector が live で死んだ理由（run-end 依存）が offline では消える、これが §5 全体を成立させる。最大の落ちは「全てが post-process 観察＝live 会話ループは別物・未構築」を明示すること。

---

## 1. §4.1 矛盾しないか → **整合**

| 観点 | 実コード事実 | 判定 |
|---|---|---|
| 物理いじらない | 設計は θ/S/R/E/Frozenset/phase_sig 非書込、post-process のみ | v9.13/v106 と整合 ✓ |
| offline/post-process 構築物 | v1114 Step1 は実コードで post-process（v918 per_subject + v107 source_events を読み EWMA+z-score 発火、engine 内 live 変数でない） | v1114 と同型 ✓ |
| 観察ベース | v106 build_cid_vector も run-end snapshot の観察 | v106 と同型 ✓ |

**重要な明確化（設計書 §2.2 を実コードで裏取り）**: cid_align を **live engine 変数でなく offline 構築物**にする判断は正しい。理由＝build_cid_vector は run-end の seed_max / C_at_run_end に依存し live 不可（v1101a で判明）。**だが offline なら v107 全ストリームから seed_max を計算できる**（下 §2 crux）。よって「live で死んだものが offline で生きる」＝設計の向きは v1114/v106 の観察ベースに正しく戻っている。

---

## 2. §4.2 実装可能か → **YES（核は prototype で実証済、6 軸クリーン）**

### (a) 初期化: v106 軸エンコーダを v107 fields に offline 適用

**実コードで軸ごとに写像可否を確認**（`v106_post_process.py:274-420` の引数 × `source_events` 実カラム）:

| v106 軸エンコーダ | 必要入力 | v107 に在るか | 写せるか |
|---|---|---|---|
| temporal_vector(lifespan_steps) | lifespan | `lifespan_so_far` ✓ | ✓ |
| scale_vector(n_core) | n_core | `n_core_member` ✓ | ✓ |
| epistemological_vector(familiarity_max) | familiarity | `R_familiarity_pre` ✓(近似) | ✓ |
| interconnection_vector(n_alphas) | n_alphas | `n_alphas_pre` ✓ | ✓ |
| resonance_vector(c_value) | C | `C_pre` ✓ | ✓ |
| ontological_vector(row, **seed_max**) | row + seed_max | row 在 + **seed_max は offline 計算可** | ✓(下 crux) |
| symmetry_vector(row) | social/stability/spread/familiarity | **✗ 無い** | ✗ |
| lawfulness_vector(row, lifespan) | pulse 系 row | 部分 | △ |
| experience_vector(row) | ingestion/ghost row | 部分（event_source_type から導出可） | △ |
| value_generation_vector(row, **seed_max**) | row + seed_max | 部分 | △ |

→ **6 軸クリーン（temporal/scale/epistemological/interconnection/resonance/ontological）**、これは設計書 §2.2 が挙げた 6 個と一致。symmetry は v107 に field 無し（再現不可）、lawfulness/experience/value_gen は partial。**＝「豊かな近似」の実体は ~6/10 クリーン + 3 partial、symmetry 欠落。** 設計書の「完全再現不可」留保は正しい。

**crux（実装成立の鍵）**: ontological/value_generation が要る **seed_max は run-end maxima だが、offline なら v107 全ストリームの max を取れる**。live build_cid_vector が死んだのはこの run-end 依存——offline ではこれが解消する。**よって build_cid_vector の軸エンコーダ自体が offline で（seed_max を流して）動く**。prototype の簡易 vec48（grad one-hot 5 軸）を、この v106 本物エンコーダ 6 軸に差し替えるのが実装。

### (b) 測定: v1103 raw/norm cosine + density

- **atom_centroids_48d_raw.parquet + normalized.parquet 両方在る**（148KB / 181KB、v1103 で生成済）✓。prototype は normalized のみ使用 → **raw を足すのが実装**（潜在/顕在 D.92、Δ0.208 反転 #L17 を両並列で観察）。
- cosine ロジック: prototype が既に `AM @ align`（normalize 済の cosine）を実装。`v1103_step_c` の density（候補群の mean pairwise cosine）を流用 ✓。

### (c) 出口: cid_align 軌跡を v1114 Step1 の観察対象に足す

- v1114 Step1 は post-process で EWMA+z-score を event-type カウントに当てて発火。**cid_align の per-CID per-chunk 軌跡を「追加の観察シグナル」として EWMA に流し、珍しい変化（z 高）で発火**＝同じ機構の入力を一本足すだけ。実装可能 ✓。
- **ただし「拾える＝発火する」と「拾ったものが意味を持つ」は別**（下 §3 落ち）。

**実装スコープ（prototype からの差分）**: (a) 簡易 vec48 → v106 本物エンコーダ 6 軸（seed_max を offline 流す）、(b) normalized のみ → raw+norm 両方、(c) self-shuffle → 別 seed null + 経験順序 shuffle、(d) v1114 への cid_align シグナル接続。**新規発明ゼロ、全て既存資産の組み替え。**

---

## 3. §4.3 落ち（正直に）

1. **「豊かな近似」の上限 = 6/10 クリーン + 3 partial + symmetry 欠落**。symmetry（social/stability/spread）は v107 に無く再現不可。**Atom centroid は 48 軸全部の上に在るので、CID 側が 6 軸サブ空間に偏ると cosine が一部軸でしか効かない**＝行き先 atom が「symmetry 系 atom」に向かないバイアスが入りうる。→ どの軸が効いた cosine かを軸別に記録すべき（集約 cosine 一個で見ない、絶対格言 #4）。

2. **CID→atom 射影の平坦性（margin 0.09、projection_audit）**。一致率は鋭く discriminate しない——**だが prototype 実測で「行き先 atom」は cid 特異 84-87% かつ多様 27-28 種**。→ 実装は「一致率の鋭さ」を期待せず「行き先（どの atom 方向か）」を主指標に。設計書 §2.3 の方針通り。**落ち＝報告で「一致率が上がった」を個性化の証拠に使わない**（prototype で上がり量は non-cid-specific=generic sharpening と確定済）。

3. **【最大の落ち】全て post-process 観察＝live 会話ループは別物・未構築**。「Center が拾う」の実体は「cid_align を v1114 のログ解析にもう一本足し、z-score で発火させる」＝**ログの後処理**。設計書 §0/§2.6 の「会話パイプライン（Center 注意→応答→人間）に流れる」の **live ループはこの実装に含まれない**。この実装が出すのは「**logged data 上で Center が cid_align の個性化に発火できるか**」まで。「会話に流れる」は別の未構築 live pipeline。→ **報告で観察（post-process）と会話接続（live、未構築）の境界を明示**。これを混ぜると crown（「会話成立」）になる。設計書 §3/§6 が「判定は Taka・crown 禁止」と枠を嵌めているので逸脱はしないが、Code A 実装時にこの境界を .py 冒頭注釈に固定する。

4. **準・循環性（要検証）**: cid_align は v1114 が読むのと同じ v107 ログから計算する。**「Center が cid_align を拾う」が、v1114 が既に持つ入力（pulse/ingestion/alpha/beta カウント）の遅延コピーを拾っているだけなら自明**。→ cid_align が足す新情報は「**経験の累積積分（履歴）**」＝生イベントカウントに無い次元。実装時、cid_align シグナルが既存 v1114 入力と相関しすぎないか（独立な発火をするか）を相関で確認。相関が高ければ「拾った」は自明。

5. **null（自明性排除、v1113 盲点#12）**: prototype は self-shuffle（他人の経験を入れたら行き先違う＝自明）。→ 実装は **別 seed の経験ストリームを null**（v1113 #12: 「皆同じ」を別 seed で引く）+ **同一 CID で経験順序 shuffle**（accumulation/履歴が効くか vs 経験集合だけで決まるか＝素性 control）。両方 v107 から offline で組める ✓。

---

## 4. 総括（Taka へ）

- **§4.1 矛盾なし**: offline post-process は v9.13/v106/v1114 と整合。設計の向きは正しく観察ベースに戻っている。
- **§4.2 実装可能**: YES。crux=seed_max が offline で解け、v106 本物エンコーダ 6 軸が offline で動く（live で死んだ run-end 依存が消える）。raw/norm 両 centroid 在り。v1114 への接続は機構の入力一本追加。核は prototype で実証済。
- **§4.3 落ち 5 点**: (1) 近似 6/10・symmetry 欠落で軸バイアス→軸別記録、(2) 一致率は平坦・行き先を主指標、(3) **最大=全て post-process 観察、live 会話ループは未構築・境界明示必須**、(4) cid_align が既存 v1114 入力の遅延コピーでないか相関確認、(5) null は別 seed + 順序 shuffle。

**実装は合意後**。合意あれば prototype を上記 4 差分で本実装（v106 エンコーダ 6 軸 + raw/norm + 別 seed null + v1114 接続）、観察対象注釈を .py 冒頭に固定、grep で物理書込ゼロ確認。出てきたものは Web Claude が報告とコードのズレを疑ってチェック。判定は Taka。

---

*以上、§4 チェック完了（Code A、2026-06-15）。矛盾なし・実装可能（6 軸 offline、seed_max が crux）・落ち 5 点（最大＝post-process と live 会話の境界）。crown なし、判定は Taka。実装は合意後。*
