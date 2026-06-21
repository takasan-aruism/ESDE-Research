# v12 Projection Audit + match×surprise/M4b 調査報告（設計書 §9-A/B/C、実装に入らず事実のみ）

日付: 2026-06-11 / 対象: M4 (seed 0、off/small) の CID / `m4_projection_audit.py` + v106 実コード照合
指示: Atomset 選択性 設計書 統合確定版（2026-06-11 Web Claude）§9。**調査のみ、M5 実装に入らない。**

---

## 0. 結論（先に）

- **M4 の「bonus がほぼ全 CID に届く」直接原因は、明確に*記帳側*。** 現コード（私の `per_chunk_observe`）に **match gate が一切ない**——event 種別も内容も問わず、event があれば必ずその CID の seed bonus を +1 する。投影がどうであれこの挙動は変わらない（コードで自明）。
- **投影側の疑いは「半分当たり・半分外れ」。** CID ベクトル自身は潰れていない（**有効ランク 5–7**、Gemini の「実効自由度 ≤4」は**外れ**を実測確認）。**cosine が大きさを消す疑いも外れ**（‖V‖ の CV は 2–3%＝消すべき大きさ差が元々ほぼ無い）。**だが atom への射影は潰れている**（margin≈0.09、profile ほぼ平坦 entropy 5.67、v106 full では 25 CID が **2 atom** に集中）。
- **ただし動態の bonus 対象を実決定するのは v106 本体でなく簡易版**（scale+phase）で、そちらは **6 atom に分かれており v106 より良い**。→ 現挙動の犯人は投影でなく記帳。
- **【重大な壁】提案の `match = similarity(event_atoms, cid_atomset)` は現状*計算できない*。** event 自身に独立の atom が無く、唯一の atom 化経路（v106 `event_source_atom_distribution`）は **event 時の source CID 自身を投影して作る**＝`match ≈ similarity(その CID の atom, その CID の atomset) ≈ 1` で**循環・退化**。非循環な「出会った構造」は **相手 CID（contact/ingestion のみ）** だけ。
- **surprise（個体内対比）は match さえ定義できれば per-CID で計算可能**（M2 頻度経路の拡張）。
- **M4b（3–6 seed 再現）は即実行可能**（`SEED` を argv 化する 1 行）。

---

## A. Projection Audit（§9-A）

### A.1 実式（実コードで確定、推測なし）

v106 `build_cid_vector`（`developmental/v106/v106_post_process.py:486`）= 10 軸を連結した 48 次元：

| 軸 | dim | 入力 | 種別 |
|---|---|---|---|
| temporal | 7 | lifespan_steps | gradient bucket |
| scale | 6 | n_core_member | one-hot |
| epistemological | 5 | last_familiarity_max | gradient bucket |
| ontological | 5 | q_remaining/q0, virt_fam, n_alphas, n_core, C | 単体正規化(Σ=1) |
| interconnection | 5 | n_alphas_currently | gradient bucket |
| resonance | 4 | C_at_run_end | gradient bucket |
| symmetry | 5 | v99_drift_* | 単体正規化(Σ=1) |
| lawfulness | 4 | pulse_count/lifespan | gradient bucket |
| experience | 3 | ingestion/ghost/normal/major | 単体正規化(Σ=1) |
| value_generation | 4 | q_spent, n_observed, β受領, n_betas | 単体正規化(Σ=1) |

- **phase_sig は入力に無い**（実コードで確認）。Web Claude の疑い的中＝**v106 本体は phase_sig 不使用**。M2-M4 の簡易版 `compute_rank_1_atom` だけが phase_sig を入れている（本体と簡易版は別物、初版/Gemini の混同点）。
- atom 一致は `cosine_similarity(cid_vecs, atom_profiles)`（`:808`）＝**大きさを捨て方向のみ**。

### A.2 測定結果（M4 CID に適用）

| 指標 | off (25 CID) | small (16 CID) | 解釈 |
|---|---|---|---|
| 有効ランク | **6.89** | **5.04** | cid_vec は潰れていない（≤4 は外れ） |
| 数値ランク | 23 | 15 | |
| active 軸 | temporal/scale/epist/ontol/intercon/lawful/exp/valgen | 同（intercon 落ち） | 7-8 軸が動く |
| **near-constant 軸** | resonance, symmetry | resonance, symmetry, interconnection | 長期/統合系の軸が smoke で未分化 |
| ‖V‖ CV | **0.033** | **0.020** | 大きさほぼ一定→cosine は何も捨てていない |
| CID 間 cosine 距離 mean / min | 0.179 / **0.0002** | 0.228 / **−0.0** | 全体は散るが一部ペアは方向ほぼ一致 |
| **atom margin(top1−top2)** | **0.089** | 0.094 | 1 位 atom が 2 位とほぼ並ぶ＝弱い |
| atom profile entropy | **5.67** | 5.66 | 325 atom にほぼ平坦（max≈5.78） |
| **v106 top1 distinct atom** | **2** (PRP.new×21, EXS.being×4) | **2** (PRP.new×11, EXS.being×5) | 射影が 2 atom に集中＝潰れ |
| top3 Jaccard | 0.48 | 0.47 | CID 同士が top3 の半分を共有 |
| **簡易版(動態) distinct atom** | **6** | **6** | 動態で実使用、こちらは分かれている |

### A.3 判定（投影側 vs 記帳側）

1. **現挙動（near-universal）の犯人＝記帳側、確定。** match gate が無い（§A.4）ので、投影が 2 atom でも 6 atom でも、event があれば全員 bonus。投影品質と無関係。
2. **投影側の疑いは層で分けると：**
   - cid_vec 自体：**健全**（有効ランク 5–7、大きさ差ほぼ無し）。Gemini の「4 次元で潰れ」＆「cosine が大きさを消す」は**両方外れ**。
   - **atom への射影：弱い**（margin 0.09、entropy ほぼ平坦、v106 で 2 atom）。325 atom_centroids が CID の動く方向を張れておらず、ほぼ全 CID が PRP.new に最近接。
   - **ただし動態が使うのは簡易版（6 atom）で v106 本体ではない**。→ **現状の bonus 対象決定に投影は実害を与えていない**（6 種に分かれている）。
3. **→ いま直すべきは記帳側（match gate を入れる）。** 投影（atom 射影の弱さ）は「将来 match gate を atom 経由で作るなら効いてくる」二次問題。

### A.4 記帳条件（§9-A-3、実コードで確認）

私の `m4_first_divergence.py` / `m3_smoke.py` の `per_chunk_observe`：
```python
event_cids = births | deaths | alpha | beta | pulse | c_conv   # ほぼ全 event 種
for cid in event_cids:
    if label.atomset_seed is None: continue   # 失敗 0 件＝実質常に通る
    label.event_count += 1                     # ← 内容を問わず +1 (match gate なし)
    bonus = k*ec/(ec+C0); label.torque_factor = 1 + gain*bonus
```
**match 判定は一切無い。** bonus 対象 = 「seed を持つ（常に）」かつ「event を持つ（ほぼ常に）」＝ near-universal は当然の帰結。M4 の観察（全 19 CID 対象）はこの設計の直接の写し。

### A.5 留保（smoke スケール）

resonance/symmetry/interconnection が near-constant なのは **5 window smoke で長期/統合量が未分化**だから。本走（長尺）では分化が増え atom 分離も改善し得る。→ **atom 射影の弱さが「smoke が短い」由来か「atom_centroids が CID 方向を張れない」本質か**は、本走 CID で再 audit して切り分けるべき（今回は smoke のみ）。

---

## B. match × surprise の計算可能性（§9-B）

### B.1 イベント自身に atom 構成は無い（Explore + 実コード確認）

- v107 の event 行は `(source_cid, timestamp, event_type)` + その CID の pre-event 状態のみ。**per-event の atom/ベクトルは無い**（`v107_event_aggregator.py`）。
- v106 `event_source_atom_distribution`（event 種別×atom 分布）は存在するが、**`build_event_cid_vector(source_cid, t)` で source CID 自身を投影して rank_1 を取る**（`v106_event_trajectory.py:271,281,312`）。
- **∴ 提案 `match = similarity(event_atoms, cid_atomset)` は退化**：event_atoms が source CID 自身の atom なので `≈ similarity(self_atom, self_atomset) ≈ 1`、全 event が match＝今と同じ near-universal に戻る。**これが match 定義の核心の未解決問題（設計書 §9 指定の「正直に報告」点）。**

### B.2 非循環な「出会った構造」は相手 CID のみ（限定的）

- contact(E3)/ingestion は**相手（partner / ghost_cid）が特定可能**（`ingestion_events_seed*.csv` の `ghost_cid`、E3 audit の link 相手）。
  → `match = similarity(partner_cid_atomset, self_cid_atomset)`＝「出会った相手に自分が響くか」は**意味があり計算可能**。
- **だが pulse / α / β / c_conv / birth / death は自己 event で外部相手が無い**→ partner-match は定義できない（これらは match=対象外にする等、設計判断が要る）。
- いずれにせよ partner_cid_atomset も A.3 の「atom 射影が弱い」を経由するので、atom 経由でなく **cid_vec 直接の類似度**（有効ランク 5–7 を活かす）を検討する余地（A.3-2 と整合）。

### B.3 surprise は match さえ決まれば計算可能

- per-CID の「過去の一致率」= M2/M4 で既に持つ per-CID `event_count` を **per-window の matched-event 数**に拡張すれば算出可能（rolling rate）。M2 頻度経路の自然な拡張。
- ただし **match の定義（B.1/B.2）が決まらないと matched 数が定義できない**＝surprise は match に依存。

---

## C. M4b（少数 seed 再現）の即実行性（§9-C）

- `m4_first_divergence.py` は `SEED = 0` ハードコード（41 行）、`CONDITION` のみ argv。**`SEED` を argv 化する 1 行で 3–6 seed 実行可能**。
- 計装（per-CID tag / θ checksum / territory snapshot）はそのまま流用可。
- コスト: 1 seed ≈ 12 分。現設計のまま（off/small or 現設計のみ）。**即実行可能、壁なし。**

---

## D. 設計判断への含意（実装はしない、材料のみ）

1. **必須の最小変更は記帳側の match gate**（投影は現状実害なし、6 atom に分かれている）。
2. **だが提案 `match=similarity(event_atoms, cid_atomset)` は退化**（B.1）。採るなら **match を「相手 CID との類似」に再定義**（contact/ingestion 限定）か、**event 種別→代表 atom 分布 vs cid_atomset**（ただし種別代表も source CID 投影由来なら循環に注意）。
3. **match を atom 経由にするなら atom 射影の弱さ（A.2）が効く**→ atom を介さず **cid_vec（または簡易版 seed）直接**で match を測る方が分離が良い可能性。
4. **投影を強化するなら**（将来 atom 経由 match を採る場合）：phase_sig を本体に入れる（簡易版が 6 atom で勝っている事実が示唆）／near-constant 軸を本走 CID で再評価／325 atom が CID 方向を張れているか本走で再 audit。

→ **次の判断は Web Claude へ。** 焦点は「match を何に対して測るか（atom 退化を避ける）」と「記帳側修正を M5 で一つだけ・強度据え置き・rank_1 シャッフル対照付き」。M5 実装は判断後。

## ファイル
- `m4_projection_audit.py` / `run_m4/projection_audit.json`
- 参照: `m4_report.md`（M4 機構監査）、`m3_investigation_and_method_audit.md`
