# v12 Atomset STEP 3 — 時間局所 membership 土台調査（実装前・dump と在/無のみ）

## 自己規律宣言（Code A）
① 過去引用済: STEP 2 報告 `m18`（main↔common 0.96＝出来事が網を方向づけてない）、`v106_step10_trajectory.py`（build_step10_cid_vector + cosine_similarity）、STEP 3 cid_align で確認した `atom_profiles_cache.npz` の slot_keys 整合（アルファベット順 v1103 でなくこれが cid-vector 整合）、`build_step10_table` の入力（v105 diag logs）。
② Taka 逐語（原文）: 「全部読んで変える系なら何やったって変化しないに決まってる。時間の概念をいれるならそれが Step なり Window なり、何 Step にするか、等の問題。そこで残るデータと比較されるデータ、消えるデータがただあるだけ」「Atom が接続されたことが意味になっていない／センターはなぜそれを受け取ったのか」「この調査は dump と在/無のみ。演算・網形成はしない」。
③ 成否判定は Taka（success/fail/Full/Partial/Failure を置かない、観察事実のみ）。
④ 集約語なし。

*作成*: 2026-06-16、Code A。*この STEP*: 時間局所 membership が現データから組めるか dump と在/無のみ。演算・網形成・実装はしていない。

---

## 0. 一文（観察事実）

時間局所の CID×atom 一致は **在る**（4 粒度: event/pulse/step10/window、per-(cid,t) 時系列）。ただし出力は **rank_1（top-1）のみ**で top-5 ではない。top-5（D1=5）が要るなら **再計算で組める**（必要な v105 diag logs と slot_keys 整合の `atom_profiles_cache.npz` が全て在る）。粒度・rank1 か top5 再計算かを Web Claude が突き合わせて決めてから実装。

---

## 1. 在るもの: 時間局所 CID×atom 一致の時系列（4 粒度）

`developmental/v106/outputs/main/{event,pulse,step10,window}_trajectory/` に per-(cid,t) の atom 一致時系列が在る。

| 粒度 | ファイル例 | seed0 行数 | cid0 の t 点数 | t 間隔 | membership 列 |
|---|---|---|---|---|---|
| event | `event_trajectory/event_cid_alignment_seed0.csv` | 15,687 | 591 | 中央 50 step | **rank_1_atom + rank_1_sim のみ** |
| step10 | `step10_trajectory/step10_cid_alignment_seed0.csv` | 62,906 | 2,500 | 10 step | **rank_1 のみ** |
| pulse | `pulse_trajectory/pulse_cid_alignment_seed0.csv` | （在） | — | ~pulse 周期 | rank_1 のみ |
| window | `window_trajectory/window_cid_alignment_seed0.csv` | （在） | — | 500 step | rank_1 のみ |

**列（event/step10 共通）**: `seed, cognitive_id, t, (source,) window, lifespan_so_far, n_core_member, C_at_window_end, Q_remaining_at_window_end, R_familiarity, cumulative_n_alphas/betas/ingestions (step10 は cumulative_pulse_count も), rank_1_atom, rank_1_sim, top_category`。

→ 観察事実: 「ある時点で CID がどの atom にどれだけ寄っているか」は **rank_1（1位 atom + その一致率）として per-(cid,t) で残っている**。同じ CID0 が t=0 で TIM.appear 0.517 等、時点ごとに記録されている。**top-k=5（D1）と全 atom の sim ベクトルは出力に無い。**

## 2. top-5 時間局所 membership は再計算で組めるか → 組める（土台確認）

rank_1 でなく top-5（D1=5・sim 重み）が要る場合、trajectory の **state 列から 48 次元 cid-vector を再計算 →`atom_profiles_cache` と cosine → top-5** で組める。土台:
- **再計算の入力（v105 diag logs）全て在**: pulse_log / per_subject / per_subject_audit / c_trajectory / alpha_lifecycle / beta_lifecycle / ingestion_events / per_event_audit（seed0 で全 8 在確認）。→ `build_step10_table(seed)` で全入力付きの per-(cid,t) 表を再生成可能。
- **`build_step10_cid_vector` + `atom_profiles_cache.npz` 在**: STEP 3 で確認した通り cache は slot_keys 順＝cid-vector 整合（アルファベット順 v1103 を使うと scramble、これは使わない）。cosine の軸整合 OK。

→ 観察事実: top-5 時間局所 membership は **現データから再計算で組める**（再 run 不要、frozen の v105 logs と v106 cache から post-process）。

## 3. 実装時の留意点（事実、判断は Web Claude/Taka）
- 粒度の選択肢: event（~50step・591点/cid）/ step10（10step・2500点）/ pulse / window（500step）。Taka 逐語「何 Step にするか、等の問題」。
- event_trajectory は `cumulative_pulse_count` 列が無い（step10 は在）。top-5 再計算で pulse 由来軸（ontological informational/lawfulness/experience）が要るなら step10 系か build_step10_table 再生成が要る。
- source_event(s,t) の辺形成では s と **target c の両方**の t 時点 membership が要る。trajectory は各 t で**生存 CID のみ**行を持つ。target c が t で trajectory に在るかの被覆は実装時に要確認（在/無を出す）。

## 4. やらなかったこと（明示）
演算・網形成・実装・CID 投影・low-dim 埋め込み・effect_size・cid pool 確定・Taka 案（326次元一致率の時間変動を直接見る別ルート）は**していない**。本 STEP は dump と在/無のみ。

## 5. 一方向保証
読んだのは frozen（v106 trajectory outputs / v105 diag logs / atom_profiles_cache）。書込なし（本 STEP は調査のみ、parquet も書いていない）。

---

*以上 STEP 3 土台調査（Code A、2026-06-16）。時間局所 CID×atom 一致は在(4粒度: event50step/step10/pulse/window500step, per-(cid,t))だが出力は rank_1 のみ。top-5(D1) は再計算で組める(v105 logs 全在・atom_profiles_cache slot_keys整合 在)。粒度と rank1/top5 を Web Claude が決めてから実装。演算・網形成なし。判定は Taka。*
