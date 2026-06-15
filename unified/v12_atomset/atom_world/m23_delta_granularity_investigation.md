# v12 Atomset — baselines_with_delta の粒度調査（実装前・dump と在/無のみ）

## 自己規律宣言（Code A）
① 過去引用済: relation_paths_seed0（851,154 行・event_id join, m15）、source_events gated（rare 1,700 event）、STEP3 time-local 報告 m22（過渡 membership 支配の可能性・対照未実施で「出来事が動かした」未確定）。
② Taka 逐語（原文・Web Claude 経由）: 「baselines_with_delta で delta が per (event, target_cid) 粒度で取れるか。取れなければ『どの c が動いたか』が使えず案が成立しない＝そこで止めて Taka に再run 要否を上げる（勝手に進めない）」「取れると私が bash で確認後、delta-絞り版＋対照A/B を実装」。
③ 成否判定は Taka（success/fail 置かない、観察事実のみ）。
④ 集約語なし。

*作成*: 2026-06-16、Code A。*この STEP*: dump と在/無のみ。実装はしていない（delta-絞り版・対照 A/B は Web Claude の bash 確認後）。

---

## 0. 結論（観察事実）

delta は **per-(event, target_cid) で取れる**。`baselines_with_delta_seed{N}.parquet` は各 event×target に 5 量×3 窓の delta を持ち、さらに **`hop_distance` で「実辺」と「baseline 対照」が分かれている**（内蔵対照）。→ 「どの c が動いたか」は使える。**案は成立、止めない。** 実装は Web Claude の bash 確認後。

---

## 1. 粒度（dump）

`baselines_with_delta_seed0.parquet`: 1,763,031 行 × 26 列。キー列 = `event_id, source_cid, timestamp, target_cid, relation_path_type, relation_strength, hop_distance, seed`。

**delta 列（5 量 × 3 窓 = 15 列）**: `delta_{R_familiarity, Q, C, n_alphas, n_observed}_{immediate, short, medium}`。加えて `n_pulses_in_window_{immediate,short,medium}`。
→ **各 (event_id, target_cid) に、その target c の state 変化が immediate/short/medium 窓で付いている**。

## 2. 実辺 vs baseline 対照（hop_distance で分離）

| hop_distance | 行数 | 意味 |
|---|---|---|
| **+1** | 851,154 | **実辺**（relation_paths と同一＝実際に到達した target）。relation_paths の全キーがここに在（787,276/787,276 一致）。 |
| **−1** | 911,877 | **baseline 対照**（relation_paths に無い target＝比較用コントロール）。 |

→ 観察事実: baselines_with_delta は「実 target の delta」＋「baseline target の delta」を**両方**持つ。「c が動いた」を baseline 対照と比べて定義する材料が**内蔵**されている（delta-絞りの閾値を baseline 分布から取れる）。

## 3. gated（rare）event の被覆と per-target 差（dump）

- gated（ingestion/alpha/beta）event 1,700 件の baselines 被覆: **100%**。
- gated の実辺 (event, target) 行数: 206,323。
- per-target で delta は異なる（同一 event の familiarity target 例）:

| target_cid | delta_C_medium | delta_R_familiarity_medium | delta_n_observed_medium |
|---|---|---|---|
| 0 | +35.0 | −0.034 | 0 |
| 10 | +19.0 | +0.709 | 0 |
| 19 | −22.0 | +1.002 | 6 |
| 126 | −5.0 | 0.000 | 0 |

→ 観察事実: 同じ event でも target c ごとに動き方が違う（C が +35 の c もあれば −22 の c もある）＝**「どの c が動いたか」で辺を絞れる**。

## 4. 実装前に Web Claude が判断する点（事実、提案しない）
- どの delta 量（R_familiarity/Q/C/n_alphas/n_observed）・どの窓（immediate/short/medium）で「動いた」を定義するか。
- 「動いた」の閾値を baseline（hop=−1）分布からどう取るか。
- 重複キー: (event,target,path) は完全一意でない（実辺内で 127,756 重複行＝relation_paths 自体の重複由来）。dedup 方針。
- 対照 A/B の中身（design 未記載分）。

## 5. やらなかったこと（明示）
delta-絞り版の実装・対照 A/B・GATE は**していない**。本 STEP は dump と在/無のみ。

## 6. 一方向保証
読んだのは frozen（baselines_with_delta / relation_paths / source_events）。書込なし（調査のみ、parquet も書いていない）。

---

*以上（Code A、2026-06-16）。delta は per-(event, target_cid) で取れる（5量×3窓）。hop_distance で実辺(+1, 851k)と baseline対照(−1, 912k)が分離＝内蔵対照。gated 100%被覆、per-target で delta 異なる＝「どの c が動いたか」使える＝案成立、止めない。実装(delta-絞り+対照A/B)は Web Claude の bash 確認後。判定は Taka。*
