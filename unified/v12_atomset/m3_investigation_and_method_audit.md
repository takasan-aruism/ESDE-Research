# v12 M3 — 調査報告 + 実験方法の検証 + 結果の妥当性

日付: 2026-06-11 / 対象: M3 smoke (seed 0、off/small/medium) / 補助: `m3_audit.py`, Explore による engine コード trace

Taka 指示: GPT/Web Claude view の指摘が実際どこまで正しいか調査、私 (Code A) の実験方法自体を再チェックして問題を抽出、それをドキュメント化し、今回の結果の妥当性を論じる。

---

## 0. 総括 (先に結論)

- GPT の主要 3 主張は **すべて正しい**。うち 1 つ (入口隔離) は GPT が「言い直し」で済ませた所を、私の制御群データで **証明済** にできる (GPT より強い)。GPT 主張 1 (閾値カスケード) はコードと既存データの両方で確認、ただし「θ→R 直結」ではなく「θ→flow/chemistry/sync→link 強度 S→ハード閾値」という機構の補正が要る。
- GPT の総合判定 (技術的 PASS / 生態学的 healthy は未判定 / main を止める異常なし) は妥当。
- 私の実験方法には **既知の自分の盲点を繰り返した問題が複数** あった (CID 数を主指標にした、confound した集計量を「clean な指標」と提示した、first-divergence を追わず最終行 shape 比較で済ませた、bonus 対象 CID を tag せず個性化判定の材料を残さなかった)。抽出して下記に列挙。
- 今回の結果が **妥当に主張できるのは** 「入口隔離・因果的 liveness・非発散・カスケード機構」まで。**妥当に主張できないのは** 「効果の符号 (個性化か寡占か)・seed 一般性・成熟相での挙動」。
- GPT の「弱い GAIN を先に、は順序が早い。次は現 seed の first-divergence 監査」は順序として正しい。次実験を設計済 (§5)。

---

## 1. GPT 主張の検証 (コード + データ)

### 主張 1: 「位相が少し変わるだけなら CID 数は同じはず」は誤り。ESDE は閾値だらけの履歴依存系で、θ の微小差が閾値を跨げば CID 数まで分岐する。

**検証結果: 正しい (機構の補正付き)。**

コード trace (`ecology/engine/`, `primitive/v910/`, Explore 確認) で判明した因果連鎖:

- θ は **R に直結しない**。R は link グラフのサイクル (topology) から決まる (`genesis_physics.py:172-197`、cycle 検出に θ は出てこない)。← GPT/私の素朴な「θ→R」像は不正確。
- θ は別経路で効く:
  - エネルギー流の位相係数 `0.5 + 0.5·γ·cos(θ_j−θ_i)` (`genesis_physics.py:157`)
  - Kuramoto 同期 `θ += K·Σ sin(θ_j−θ_i)` (同 106-136)
  - **化学反応ゲート `cos(dθ) < 0.7 → 反応ブロック`** (`chemistry.py:168`) ← θ に対する **直接のハード閾値**
- これらが link 強度 `S` を変える → `S` が **ハード閾値** を跨ぐ:
  - link 死: `S < 0.007` (`genesis_state.py:106`)
  - island 所属: `S >= 0.20` (`intrusion.py:23`、v105 では 0.20 で呼ぶ `v105_memory_readout.py:2517`)
  - label seed: `R > 0` (`virtual_layer_v9.py:528`)
  - label cull: `share < threshold_i` (同 892)
- label 誕生/死 = CID 誕生/死 (`v105_memory_readout.py:2534, 2580`)。

**データでの実証 (`m3_audit.py` §4):** off と small/medium の最初の分岐は link `(1335,2701)`。3 条件すべてで **同じ step 499 に誕生**、死は off=step543 (寿命44) vs small/medium=step607 (寿命108)。torque がこの link の寿命を 64 step 延ばした = `S<0.007` の到達 timing を後ろにずらした実例。これが island→label→CID へ波及する。

→ 「θ が少し変われば link の寿命が変わり、寿命が閾値跨ぎの timing を変え、CID 数まで分岐する」は **コードと実データの両方で確認**。Taka の元評価 (位相微小変化なら CID 数同一のはず) は誤りで、GPT が正しい。補正: 経路は θ→R ではなく θ→(flow/化学/同期)→S→閾値。

### 主張 2: 「CID 数が変わったから torque 経路に隔離されてない」は誤り。入口は torque だけ、CID 数変化はその下流、入口の隔離は成立。

**検証結果: 正しい。しかも私のデータで証明できる (GPT は言い直しで済ませた)。**

- コード: M3 が M2 から変えたのは `label["torque_factor"]` の値のみ。これは `virtual_layer_v9.py:432, 747` で `cog_factor = label.get("torque_factor", 1.0)` として読まれ `torque_mag` に乗るだけ。他の入口はない。
- 実証: **off (GAIN=0) ≡ M2 baseline が 6 ファイル bit-identity** (`compare.json`、per_subject 25×152 含む全 max_abs_diff=0)。さらに **w=1 の torque は 3 条件で完全一致** (torque_total=3.7752, events=154)。→ window 1 終了まで 3 条件は同一世界。分岐は最初に factor>1 が乗った瞬間から始まる。
- ∴ CID 数変化は **唯一の入口 (cog_factor) の下流** で起きたことが論理的に確定。隔離は崩れていない。

→ GPT 主張 2 は正しく、私の制御群がそれを **経験的に証明** している。

### 主張 (言い直し): 「θ への作用が主体の生死に届くほど実効性を持った」

**検証結果: 正しい。具体的に裏付け可能。**

- matched CID (分岐前誕生、3 条件共通の cid 0..18) の運命が hosted↔ghost で入れ替わる:
  - cid4: off=ghost(寿命3) → small/medium=hosted(寿命5) (torque が生かした)
  - cid3: off=hosted(寿命5) → small/medium=ghost(寿命3) (torque が殺した)
  - cid15: off=ghost(寿命1) → small=hosted(寿命3)
- → θ への torque 作用が、主体の host 喪失 (生死) に届いている。

### GPT 総合判定: 技術的 PASS / 生態学的 healthy 未判定 / main を止める異常なし

**検証結果: 3 点とも妥当。** §3 (妥当性) で詳述。

### GPT 「弱い GAIN を先に、は順序が早い。次は GAIN いじりでなく first-divergence 監査」

**検証結果: 順序として正しい。** 機構 (どの CID・どの link・なぜ) を現 seed で解明する前に GAIN を増やすと、未理解の集計量を条件数だけ増やすことになる。先に「何を測るべきか」を確定させる方が良い。私の元の「GAIN 0→小→中 ramp」は **発散安全確認としては正しかった** が、それを「科学的な次の一手」と混同していた。発散 ramp は済んだ。次は機構監査。

---

## 2. 実験方法の再チェック (私=Code A の問題抽出)

[[code-a-blind-spots]] と照合して、自分の M3 実験・報告で踏んだ問題を抽出する。

| # | 問題 | 詳細 | 関連盲点 |
|---|---|---|---|
| M1 | **CID 数を主指標にした** | smoke 報告の (B) を「population まるごと変化 (18→16→18)」で見出しにした。CID 数は個性化/寡占/安定化を区別しない粗い集計量。per-CID 運命・多様性を先に出すべきだった。 | 集団平均の罠 / 集計指標が処置と独立 |
| M2 | **confound した集計量を「clean な感応指標」と提示** | `Σtorque_total` 単調増 (16.47≤18.43≤18.63) を「cog_factor が乗っている証拠」とした。しかし母集団 (18/16/18 label)・event 数が条件間で違うので交絡。本当に clean な信号は w=1 一致 + w=2 onset の方で、そちらを過小評価していた。 | 集計指標が処置と独立 |
| M3 | **first-divergence を追わず最終行 shape 比較で済ませた** | `m3_compare.py` は最終出力の shape mismatch を「diff」とした。分岐前は同一世界なので共通 prefix を整列すれば最初の分岐点 (link `(1335,2701)` の寿命、audit row 2) を特定できた。`m3_audit.py` で是正済。 | (新規) 最終状態比較は分岐点を隠す |
| M4 | **bonus 対象 CID を tag していない** | どの CID が factor>1 を受けたかを記録していないため、「boost された CID が勝ったのか (寡占) / 周りが多様化したのか (個性化)」を現データで判定できない。次 run で要 tag (実験側 audit file に、CID 公式レコード外で)。 | (新規) 処置対象の識別子を残す |
| M5 | **報告が機構を説明せず誤読を誘発** | 「population 変化」とだけ書き θ→S→閾値カスケードを説明しなかったため、「位相微小変化なら CID 数同一のはず」という誤読の余地を残した (実際に発生)。報告は反証され得る誤読を先回りで潰すべき。 | 想定外を想定の範囲で説明しない |
| M6 | **warmup/成熟相・寿命分解能の限界を明記せず** | smoke 5 window は warmup (M frozen=1.0) 内、未成熟・高 churn 相。寿命は 1-5 window 刻みで分解能が粗い。この相の torque 効果しか見ていないと明記すべきだった。 | smoke 設定を本格判定に継承 |

**良かった点 (維持):**
- **off≡M2 制御群** を置いたこと。これが入口隔離・因果 liveness の load-bearing な証拠になった。
- **発散安全 ramp (0→小→中)**。中 GAIN (factor 1.38) でも非発散を段階確認できた。
- **判定数値を CID レコード外に保った** こと自体は規律遵守 (ただし M4 の通り、observational な「bonus 対象か否か」は実験側 audit に残すべきだった — これは判定数値ではない)。

---

## 3. 今回の M3 結果の妥当性

### 妥当に主張できること (V)

- **V1 入口隔離**: off≡M2 の 6 ファイル bit-identity (全 max_abs_diff=0) + コード上 cog_factor が唯一の入口。→「GAIN>0 の diff は torque 由来」は妥当。
- **V2 因果的 liveness**: 分岐 onset = 最初の factor>1 適用と一致 (w=1 torque 一致、link 1335,2701 寿命 44→108 が step499 境界直後)。→「bonus が torque に実際に乗り動態に届く」は妥当。
- **V3 非発散・有界**: θ 範囲内、完走、GAIN=1.0 (max factor 1.38) まで。engine 自身の torque feedback M は warmup で 1.0 固定 = 暴走経路なし。→「異常なし、main を止める理由なし」は妥当。
- **V4 機構**: θ→{flow, Kuramoto, 化学ゲート cos(dθ)≥0.7}→S→ハード閾値→island/label/CID。コード trace + link 寿命データで確認。→「CID 数変化は下流」「微小 θ が CID 数を動かす」は妥当。

### 妥当に主張できないこと (I) — ここを超えて語ると過剰主張

- **I1 効果の符号**: torque は CID の生死を **再分配** する (cid4 生存↔cid3 死)。一様な強化でも弱化でもない。系統的方向は示せていない。
- **I2 個性化 vs 寡占**: 予備的に diversity を見ると — 平均寿命 off2.44→medium2.94 (延長)、pulse Gini off0.238→medium0.173 (より平等=寡占的でない方向)、平均 coherence 0.670→0.603 (微減)。**寡占よりむしろ安定化/平準化に傾く兆候**だが、seed 0・N=16-25・高分散・bonus 対象未 tag のため **判定不可**。母集団が条件間で違う集計量での比較 (M2 と同じ交絡) でもある。
- **I3 seed 一般性**: seed 0 のみ。[[smoke-seed0-not-absolute]] (v10.12 で 4/7 metric の符号反転実観測) より、符号は seed で反転し得る。
- **I4 成熟相**: 全 smoke が warmup (<20 window) 内。成熟相の attractor は未観測。寿命 1-5 window では効果の分解能も粗い。
- **I5 集計量の交絡**: CID 数・Σtorque_total・diversity std は条件間で母集団が違うため effect の clean な測定にならない。matched-CID 運命比較 (同一 CID の運命差) の方が clean だが、それは「再分配がある」までしか言えない。

### 妥当性の一行まとめ

> M3 smoke は **「Atomset→torque の配線が、隔離された唯一の入口を通じて、非発散のまま、主体の生死に届く実効性を持つ」ことを妥当に示した (技術的 PASS)。「その効果が個性化か寡占か、どの seed でも同じか」は妥当には言えない (生態学的判定は次段)。** GPT の総合判定と一致。

---

## 4. GPT はどこまで正しかったか — 採点

| GPT の主張 | 判定 | 根拠 |
|---|---|---|
| 「位相微小変化なら CID 数同一」は誤り (閾値カスケード) | **正しい** (機構補正付: θ→R 直結でなく θ→S→閾値) | コード trace + link 1335,2701 寿命 44→108 |
| 「CID 数変化=隔離崩れ」は誤り (入口は torque のみ、下流) | **正しい** (私の制御群で証明可、GPT より強く言える) | off≡M2 6 ファイル bit-identity + w=1 一致 |
| 言い直し「θ 作用が主体の生死に届いた」 | **正しい** | matched CID の hosted↔ghost 入替 |
| 総合: 技術 PASS / 生態 未判定 / main 止めない | **妥当** | §3 V1-V4, I1-I5 |
| 「弱い GAIN 先行は順序が早い、次は first-divergence 監査」 | **妥当** | 機構解明前の条件追加は未理解集計量の増殖 |

GPT の誤り・過不足: 実質的な誤りなし。唯一の不足は「θ→R」的な素朴機構像を明示補正していない点 (実機構は θ→flow/化学/同期→S)。これは私 (Code A) も同様に素朴だったので相殺。

---

## 5. 次の一手 (GPT 案を採用・設計)

GAIN いじり・複数 seed の前に、**現 seed (0) で first-divergence + per-CID 機構監査** を 1 本の計装 re-run で行う。

捕捉する観察 (すべて実験側 audit file = `/tmp` or `run_m3_smoke/` に置き、CID 公式レコードには入れない):
1. **per-step θ checksum** (off と small) → θ が最初に分岐する step を確定 (vl.step 境界の直後のはず)。
2. **bonus 対象 tag**: どの cid が factor>1 を受けたか、最終 event_count・factor、そして **first-divergence link `(1335,2701)` の node が bonus 対象 label の territory に属すか** を確認 (M4 のギャップ解消)。
3. **per-cid 分離**: birth / death / ghost化 / reap を別々に集計、寿命・share・V_unified coherence (`v18_v_unified_concentration_final`)・θ drift。
4. **多様性**: 残った CID 間の差 (分散・寿命) + 消えた CID の死因 (cull share 不足 / host 喪失)。
5. 判定は **CID 数でなく「残った CID 間の差」「消えた CID の死因」** で個性化 vs 寡占を論じる。

これが健全に終わってから **複数 seed か GAIN 追加** に進む ([[24seeds-single-batch]] / [[smoke-seed0-not-absolute]] 遵守、main は Web Claude view 承認後)。

---

## 付録: 使用データ・スクリプト

- `m3_audit.py` / `run_m3_smoke/audit.json` — birth/death/ghost 分離、matched CID 運命、多様性、first-divergence
- `m3_compare.py` / `run_m3_smoke/compare.json` — off≡M2 制御群 + 効果 + 発散
- Explore agent による engine コード trace (θ→R/S/閾値、warmup=20、chemistry gate 0.7)
- 既存出力: `/tmp/v12_m3_smoke_{off,small,medium}_seed0/diag_v105_*/` (per_subject / audit / persistence / link_life)
