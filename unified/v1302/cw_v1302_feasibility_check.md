# v1302 §8 実装可否チェック資料（Code A → Web Claude / Taka）
**動的版を実装する前の可否ゲート。child run / smoke / 実装は実行ゼロ。read-only 点検＋最小 probe のみ。合意ゲート前で停止。**

*点検実施*: 2026-06-22、Code A。指示書 = `v1302 §8 実装可否チェック 指示書`（Web Claude, 2026-06-21）。判定（success/fail）は置かない。

---

## 自己規律宣言（4点）

**① 過去引用明記**
`v1302_instruction.md`（動的3チャネル plb(t)←Q_remaining / K_sync(t)←R_familiarity / decay_link(t)←n_core_member、N←B_gen・初期θ←phase_sig 静的、decay_node frozen、子寿命=親寿命、time-shuffle null、率正規化軌跡署名）／step-0 実装 `cw_step0.py`（**plb は `V82Engine(plb=...)` の構築時引数**で渡し、走行中更新したのは K_sync/decay_rate_node/decay_rate_link＝plb は走行中更新を試していなかった）／step-0 端末確認（K_sync/decay の10step毎更新 alive=1.0 非破綻・step_window 10step 刻み可・N 構築時固定）／§16（smoke 後停止、本書は smoke *前*の可否点検）／#30（写像＝サンプラー）／#33（同情報を2 param に当てない）。

**② Taka 逐語（原文）**
「子ESDEの物理法則そのものが親ESDEのCIDに合わせて変化していく系」「誕生時固定の値に関しては変更不要でいいや」「親10ステップで子供物理更新」「子ESDEを本来的に長生きさせる理由はそれほどない」「統計調査では不十分で、グラフを用いる、動的な傾向をみるための指標を用意する」「いいんじゃないかな。進めて」。本書はその実装の*可否ゲート*（チェック→合意→実装 の合意前）。

**③ 判定は Taka**（success/fail を置かない、可否＝観察事実のみ記録）。

**④ 集約語禁止。crown 禁止。**

---

## 観察対象注釈ブロック

- 読＝frozen：engine ソース（`autonomy/v82/esde_v82_engine.py` / `cognition/.../v43/esde_v43_engine.py` / `ecology/engine/realization.py` / `autonomy/v82/engine_accel_v5.py`）、`cw_step0.py`、birth-fixed `primitive/v918/diag_v918_main/subjects/per_subject_seed0.csv`、driver `developmental/v106/outputs/main/step10_trajectory/`。
- 書＝本資料（`cw_v1302_feasibility_check.md`）＋ probe スクリプト（`probe_runtime_params.py`、stdout のみ・データファイル非生成）。
- **child の実験 run（real/time-shuffle/canon・smoke・署名生成・Mantel/order-effect・親軌跡駆動）は一切走らせていない。** 親 physics/inject/ledger/state 非書込。
- probe 粒度 = step-0 端末と同等：engine を import し param を runtime セット、数十〜数百 step を走らせて反映と alive を見るだけ。署名計算・Mantel・実験データ生成なし、ファイル非生成。

---

## 結論サマリ（各項目：可 / 不可 / 要設計変更）

| # | 点検項目 | 判定 | 要点 |
|---|---|---|---|
| 1 | **plb 走行中書き換え（最優先ブロッカー）** | **可** | `eng.realizer.params.p_link_birth` は frozen でない dataclass、step が毎回読む。probe で反映実証。**§2 の「2本に落とす」帰結は不要** |
| 2 | 4可変/3駆動の照合 | **可（整合）** | 物理的可変は plb/K_sync/decay_node/decay_link の4本。decay_node frozen は設計判断（clean ドライバ無し）で物理不能ではない＝「4可変・駆動3」で整合 |
| 3 | K_sync(t)/decay_link(t) の3ドライバ写像再確認 | **可** | 10step刻みで `tanh` transform 更新、alive=200 非破綻（probe 再確認） |
| 4 | 10step駆動＋子寿命=親寿命 | **可** | `step_window(10)` を親軌跡点ぶん反復、終端で停止可。child run 長は親CIDごと可変（軌跡pts×10） |
| 5 | window毎の軌跡署名 | **可** | step-0 の創発人口統計を window 単位ループ内で記録するだけ（終端1点→時系列化は構造変更小） |
| 6 | ドライバ実在・解像度・欠損 | **可** | `Q_remaining_at_window_end`/`R_familiarity`/`n_core_member` 実在・10step解像度・n2/4/5 欠損なし |
| 7 | CID軌跡内 z 標準化 | **可** | 各CIDの軌跡内 mean/std で z 化、軌跡長可変でも per-CID 完結ゆえ問題なし |
| 8 | コスト見積（smoke 実時間） | **可** | smoke n2（K=10/seed=1/54CID）= 808,720 child-steps、Pool24 で実時間 数分（下記） |
| 9 | 軌跡距離3案の出力形 | **確認のみ（確定せず）** | 終端/per-window/DTW いずれも「CID×window×署名次元」の3階テンソルで足りる |

**不可・要差し戻しは無し。** 指示書の動的3チャネルはそのまま実装可能。最大の前提だった「plb は走行中書けないかもしれない（→2本に縮退）」は **probe で否定（書ける）** され、Q_remaining→plb(t) を含む3本が成立する。

---

## §1 項目詳細

### 項目1【最優先・ブロッカー候補】plb 走行中書き換え → **可**

**コード構造（read-only 追跡）**
- `esde_v43_engine.py:469` で `self.realizer = RealizationOperator(RealizationParams(enabled=True, p_link_birth=plb, ...))`。
- `realization.py`：`RealizationParams` は **素の `@dataclass`（frozen ではない）**。`RealizationOperator.step()` は毎 step `p = self.params` → `p_realize = p.p_link_birth * l_ij`（`engine_accel_v5.py:206,263`）で**毎回読み直す**。
- ⇒ runtime パス **`eng.realizer.params.p_link_birth = X`** が次 step の realization に効く。step-0 が plb を構築時引数でしか渡さなかったのは*実装の都合*で、走行中書込が物理的に不能だったわけではない。

**probe 実測**（`probe_runtime_params.py`、N=200・seed11、ファイル非生成）
```
[plb] 書換前: p_link_birth=0.007 active_links=128 alive_n=200
[plb] runtime set -> 0.05
[plb] 高plb 4window: 新規 active link=241 active_total=340 alive_n=200
[plb] 低plb(0.001) 4window: 新規 active link=5 active_total=9 alive_n=154
[plb] => 反映判定: 高plb新規(241) vs 低plb新規(5)  alive非破綻=True
```
高 plb で新規リンク 241、低 plb で 5＝**走行中の plb 値が realization に明確に反映**。alive 非破綻。

**caveat（観察・判定しない）**: 極端な低 plb（0.001）では link 飢餓で alive_n が 200→154 に減少（ノード死）。ただし指示書 transform `base·(1+0.3·tanh)` は plb を 0.007±30%＝約 0.0049〜0.0091 に閉じ込めるので、probe で見たような極端値には到達しない（飢餓崩壊は実駆動レンジ外）。

### 項目2 4可変/3駆動 → **可（整合）**
物理的に走行中書き換え可能なのは **plb / K_sync / decay_rate_node / decay_rate_link の4本**（plb は項目1 で実証、他3本は step-0 既証＋probe 再確認）。指示書が decay_node を frozen にしているのは「clean なドライバが無い」設計判断で、書込自体は可（probe で `eng2.physics.params.decay_rate_node` set 後 alive=200 確認）。⇒「4本可変・駆動は設計上3本・decay_node は意図的に駆動から外す」で矛盾なし。N・初期θ は誕生時固定（走行中変更しない・できない＝整合）。

### 項目3 K_sync/decay_link の3ドライバ写像 → **可**
`eng.physics.params.K_sync` / `eng.physics.params.decay_rate_link` を10step刻みで `tanh` transform 更新。probe：
```
upd0: K_sync=0.0772 decay_link=0.0386 alive_n=200
upd1: K_sync=0.1000 decay_link=0.0500 alive_n=200
upd2: K_sync=0.1228 decay_link=0.0614 alive_n=200
```
非破綻。step-0 端末既証を本指示の写像形で再確認。

### 項目4 10step駆動＋子寿命=親寿命 → **可**
`step_window(steps=10)` を親軌跡の各10step点でループし、軌跡終端（親死）で停止する構造が組める。child run 長 = 親CIDの軌跡点数×10 step で可変。誕生時 N←B_gen / 初期θ←phase_sig は run 開始時に一度だけ設定（step-0 と同形、line 96/106）。

### 項目5 window毎の軌跡署名 → **可**
step-0 は終端1点で `n_labels/mean_size/std_size/share_gini/mean_age` を計算（`worker()` 末尾）。これを駆動ループの各 window で呼び record するだけ＝時系列化。率正規化（各 window で「その時点生存の label」統計）も同関数を生存集合に当てるだけ。`lifecycle_events` は累積なので軌跡では差分 or 除外（ドライバ直写し禁止§5 に整合する範囲で要選別＝実装時 Web Claude 確認）。

### 項目6 ドライバ実在・解像度・欠損 → **可**
`developmental/v106/outputs/main/step10_trajectory/step10_cid_alignment_seed0.csv`（62,906行・17列・228 CID・各CID 46〜2500点・10step解像度）に：
- **`Q_remaining_at_window_end`**（→plb）✓ / **`R_familiarity`**（→K_sync）✓ / **`n_core_member`**（→decay_link）✓ 実在・populated。
- 除外対象も同居：`C_at_window_end`（Q の鏡）/`cumulative_*`（年齢代理）/`rank_1_sim`（Atom 由来）→ 指示書通り使わない。
- **birth-fixed（v918）↔ driver（v106）の CID 接合 = 228/228 完全一致**（traj-only=0, birth-only=0）。誕生時 M_c/B_gen/phase_sig（v918）と時間ドライバ（v106）は同一 CID 母集団で結合可能。
- **注記（交絡注意・#11）**: trajectory の `n_core_member` は*時間変化する駆動量*であり、層別ラベル `v11_m_c_n_core`（誕生時固定 n2=54/n4=11/n5=17）とは**別物**。層別はラベル、駆動は軌跡値で行う（decay_link を n_core_member(t) で駆動しつつ、集計は birth-fixed 層で層化）。v106 の n_core_member 終端値の分布（n2=180/n5=21/n4=15/n3=12）はラベル分布と一致しない＝両者を取り違えないこと。

### 項目7 CID軌跡内 z 標準化 → **可**
z は各 CID の軌跡内 mean/std で計算（軌跡の形を効かせる）。CID ごとに軌跡長が違っても per-CID 完結ゆえ実装可。軌跡が短い CID（min 46点）でも std 定義可。

### 項目8 コスト見積（実時間）→ **可（smoke は Pool24 で数分）**
- 計測：N=200 child で **約 352 steps/sec/child**（単スレ、`step_window(10)`×200回=2000step を 5.67s）。
- smoke 想定（K=10・seed=1・**n2 全54CID**）：child/CID = real(1)+time-shuffle(10)=11体、child run 長 = 軌跡点数×10。n2 軌跡点 sum=7,352 → **総 child-steps = 808,720**。
  - 単スレ ≈ 38 分 / **Pool24 ≈ 1.6 分**（純計算。実際は inject 起動・署名計算・スケジューラ overhead で数分レンジ）。
- shuffle 無料技（行列置換）は **使えない**：time-shuffle も子の再 run が要る（real 1 + shuffle K=10 ＝11倍）。それでも n2 smoke は実時間内。
- 全層・K 拡張時の参考：real 82CID 全層の child-steps（real のみ）は n2 の点数比から概算で十数万 step ×（1+K）。K と全層拡張は smoke 結果を見て承認後（指示書 §8.3）。

### 項目9 軌跡距離3案の出力形（確定しない）→ **確認のみ**
- 署名軌跡を **CID × window × 署名次元（5）** の3階テンソルで保持すれば3案すべて賄える：
  - **終端**：最終 window のベクトルのみ（real vs shuffle centroid 距離）。
  - **per-window Euclidean**：window 整列後に各 window 距離を平均（軌跡長は real と同CID shuffle で同一ゆえ整列可）。
  - **DTW**：window 系列を時間伸縮対応づけ（長さ可変でも対応可、信号あれば採用）。
- 距離はここで**確定しない**（smoke 後に最適化、指示書 §6/§8.9）。出力形だけ確認＝可。

---

## §2 不可時の帰結（該当なし）
全項目「可」のため §2 の差し戻し（plb→2本縮退、署名 cadence 粗化、コスト削減、ドライバ差替）はいずれも**発動不要**。特に最大懸念だった plb は probe で書込可と実証され、動的3チャネルが原案のまま成立する。

---

## §3 合意待ち事項（実装前に Web Claude / Taka へ）
1. **項目5 の `lifecycle_events` 系の扱い**：累積量を軌跡署名に入れるとドライバ直写し/run長トートロジー側に寄る。差分化 or 除外を実装時に確定したい（§5 直写し禁止との整合）。
2. **N の代表値**：コスト計測は N=200 で実施。実 child N=B_gen×10 は CID ごと可変。n2 の実 N 分布での再概算が要るか（おおむね同オーダー想定）。
3. これらは*実装に進む合意*の確認であって、可否自体は上表の通り全可。

**本資料は合意ゲート前。child run / smoke / 実装は未実行。次段（smoke K=10/seed=1/n2）は Taka / Web Claude の承認後に着手する。**

---

## 一文サマリ
v1302 §8 可否点検（Code A, 2026-06-22、child run/smoke/実装ゼロ・read-only＋最小 probe）── **全9項目「可」、差し戻しなし**。最大ブロッカー候補だった **plb 走行中書き換えは `eng.realizer.params.p_link_birth`（非frozen dataclass・step が毎回読む）で可能と probe 実証**（高plb→新規link241 / 低plb→5・alive非破綻）ゆえ動的3チャネル（plb←Q_remaining / K_sync←R_familiarity / decay_link←n_core_member）が原案のまま成立。ドライバ3列は v106 step10_trajectory に実在・10step解像度・欠損なし、birth-fixed(v918)↔driver(v106) CID 接合 228/228。10step駆動＋子寿命=親寿命・window毎軌跡署名・CID軌跡内 z 標準化いずれも実装可。コストは smoke(K=10/seed=1/n2 54CID=808,720 child-steps)が Pool24 で実時間数分（shuffle 無料技は使えず null ごと再 run だが n2 smoke は収まる）。軌跡距離3案は CID×window×署名 の3階テンソルで賄え、確定は smoke 後。合意待ち＝lifecycle系の署名扱い/実N再概算のみ。**合意ゲート前で停止、判定は Taka。**
