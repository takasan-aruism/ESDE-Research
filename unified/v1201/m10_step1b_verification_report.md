# v12 Atomset cid_align — STEP 1 検証 + 作り直し報告（Web Claude 2 点の実コード回答）

**依頼（Web Claude 2026-06-15）**: STEP 1 報告の 2 点を実コードで示せ。(1) ontological informational を 0 にした件は cumulative_pulse_count で作れるのでは。(2) epistemological「写せない」の根拠（境界実値・v106/v107 の R_familiarity 同一性・生 count field の有無）。

*作成*: 2026-06-15、Code A。*結論*: **両点とも Web Claude が正しい。私の旧 STEP 1（m7）は誤ったエンコーダ（run-end 版）を使っていた。** trajectory 版で作り直し、40/48 次元（旧 26）に。判定は Taka。crown なし。

---

## 0. 一文結論

旧 STEP 1 は `v106_post_process.py`（**run-end 版**）のエンコーダを使った誤り。正しい参照は **trajectory 版**（`v106_pulse_trajectory.py` / `v106_step10_trajectory.py`、Web Claude がアップした版）。trajectory 版を **verbatim import** して作り直した結果、**ontological 5/5**・**epistemological も写る（v106 同様 degenerate）**で、非ゼロ **40/48 次元**（旧 26）。残る欠落は symmetry（pulse_log delta_* 要・flag）のみ。

---

## 1. 点(1) ontological informational — Web Claude 正しい（実コード）

| 証拠 | 実コード/データ |
|---|---|
| run-end 版（私が誤って読んだ） | `v106_post_process.py:309` informational = `v14_virtual_familiarity_entries`（v107 に無い） |
| **trajectory 版（正しい）** | `v106_pulse_trajectory.py:213` **informational = `cumulative_pulse_count` / cumulative_pulse_max** |
| v107 で作れるか | pulse event **12530 個**（per-CID 中央 20）→ 累積カウントで構築可 ✓ |

→ **ontological は 4/5 でなく 5/5**。作り直し版で `ontological idx[18:23] 非ゼロ 5/5` 確認。私の「informational は v107 に field 無い」は **run-end 版を見ていた誤り**。trajectory 版は pulse を数える＝作れる。

## 2. 点(2) epistemological「写せない」— Web Claude 正しい（私の誤り、実コード）

(i) **EPISTEMOLOGICAL_BOUNDARIES の実値**: `v106_post_process.py:297` = **`[10, 30, 60, 150]`**（本物確認）。

(ii) **v106 trajectory の epistemological 入力 = R_familiarity**: `v106_pulse_trajectory.py:205-207` `epistemological_vec(r_familiarity)` → `_gradient_distribute(R_familiarity, [10,30,60,150], 5)`。`build_step10_cid_vector:221` も `epistemological_vec(row.get("R_familiarity",0))`。
**v106 R_familiarity と v107 R_familiarity_pre は同一量**（実データ）:
| | min | med | max |
|---|---|---|---|
| v107 R_familiarity_pre | -5.787 | -0.260 | 20.000 |
| v105 pulse_log R_familiarity | -5.787 | -0.279 | 20.000 |
→ **完全同レンジ＝同一量**。

**∴ v106 trajectory も同じ R_familiarity を境界 [10,30,60,150] に通すので、v106 でも 99.97% が level 0 に潰れていた**（R_familiarity>10 は 0.03% のみ）。**＝epistemological が degenerate なのは v106 の挙動そのもので、「写せない」のでなく「写すと v106 同様 degenerate」が正しい。** 私の旧報告は **run-end 版の `epistemological_vector(last_familiarity_max)`（count, 中央 41, 境界とも整合）と取り違えた誤り**。trajectory 版は R_familiarity を verbatim で使う＝v107 で写る。

(iii) **生 count field の有無**: v107 source_events に R_familiarity_pre 以外の familiarity 量は無い。生 count（v106 run-end の last_familiarity_max）は per_subject の `last_n_partners` にあるが **run-end・per-event でない**ため per-event cid_align には使えない。**→ trajectory 版の方針（R_familiarity を verbatim、degenerate を許容）が v106 一致かつ唯一の per-event 整合解。**

→ 作り直し版で `epistemological idx[13:18] 非ゼロ 2/5`（level0 常時 + level1 が R_familiarity>10 の 0.65% で稀に点く）＝**v106 と同じ degenerate な写り**。

## 3. 作り直し STEP 1（trajectory エンコーダ verbatim）の結果

**コード**: `m9_step1b_build_cid_align.py`。**v106 trajectory エンコーダを verbatim import**（`from v106_pulse_trajectory import temporal_vec, ..., value_generation_vec`）＝bit-identity 保証（Web Claude が照合可能）。cumulative_* は v107 event を per-CID per-timestamp で累積。seed_max は v107 全ストリームから offline。

| 軸 | 入力（v107 由来） | 非ゼロ次元 |
|---|---|---|
| temporal | lifespan_so_far | 7/7 ✓ |
| scale | n_core_member | 6/6 ✓ |
| epistemological | R_familiarity_pre（verbatim） | 2/5（v106 同様 degenerate） |
| **ontological** | Q_remaining/q0, **cum_pulse**, cum_alpha, n_core/7, C_at_window_end | **5/5 ✓**（点1解決） |
| interconnection | cum_alpha | 5/5 ✓ |
| resonance | C_at_window_end | 4/4 ✓ |
| symmetry | delta_*（**v107 に無い**） | **0/5**（flag、下記） |
| lawfulness | pulse_density = cum_pulse/lifespan | 4/4 ✓ |
| experience | discovery=cum_ingest, comprehension=cum_pulse（creation=cum_q_spend=0） | 3/3（うち creation a42 は fallback[1/3] 由来 16.3% のみ＝実質 2/3） |
| value_generation | q_spent_so_far/q0, cum_ingest, cum_alpha, cum_beta | 4/4 ✓ |

**非ゼロ 40/48 次元**（旧 26）。q_spent_so_far = `v14_q0 - Q_remaining_at_window_end`（med 9）で構築。

**物理書込ゼロ**（grep: state.theta/.E/.S/phase_sig/label.nodes 代入 0 件、engine import 0 件、書込は to_parquet のみ）。

## 4. 残る 1 点と flag（判定は Taka/Web Claude）

- **symmetry（5 次元）は v105 pulse_log の delta_social/stability/spread/familiarity で構築可能**（実在確認済、v106 trajectory も pulse_log から取る）。ただし v107 source_events には無いため、**追加には pulse_log を join する判断が要る**（experience stream を v107 に閉じる設計から外れる小拡張）。**Code A 推奨**: STEP 2 関門は 40 次元で十分。symmetry は行き先（STEP 3）の偏り緩和に効くので、関門通過後・STEP 3 前に pulse_log join で 45/48 に上げる選択肢を提示（判定は Taka）。
- **experience creation（cum_q_spend_events）**は v107 に対応 event 種が無く、a42 は fallback[1/3] 由来 16.3% のみ＝実質欠落。q_spend を別ログから足すか保留かは Taka 判断。

---

## 5. 次接続

- 作り直しで cid_align は **40/48 次元**（ontological 5/5・epistemological 写る）。Web Claude 予測通り「行き先 Atom の偏り緩和」に寄与。
- **STEP 2 関門（準・循環性、選択肢 C）はこの 40 次元版で実施可**。symmetry 追加は関門通過後・STEP 3 前に判断。
- 出力: `run_step1b/cid_align_step1b.parquet`（24seed×5224CID×376956 records）。

**STEP 2 へ進んでよいか（+ symmetry を pulse_log join で追加するか）、Web Claude/Taka 判断待ち。** crown なし、判定は Taka。

---

*以上（Code A、2026-06-15）。Web Claude 2 点とも正しく、私の旧 STEP 1 は run-end 版エンコーダの取り違え。trajectory 版 verbatim で作り直し、ontological 5/5・epistemological 写る（degenerate=v106 挙動）・40/48 次元。symmetry は pulse_log join で追加可能（flag）。物理書込ゼロ。STEP 2 進行可否を判断待ち。*
