# v12 Atomset M3 smoke — bonus を torque に接続 (Frozenset cog_factor の口)

日付: 2026-06-11 / seed 0 / smoke (mat=2 + track=3, window_steps=500)

## 何をしたか

M2 で育てた `atomset_bonus` を `atomset_factor = 1.0 + GAIN * bonus` として
`label["torque_factor"]` に書き込み、torque に接続した。

接続点 (`primitive/v910/virtual_layer_v9.py`、`step()` 行 747 / `apply_torque_only()` 行 432):

```python
cog_factor = label.get("torque_factor", 1.0)
torque_mag = energy * rigidity_factor * self._torque_multiplier * cog_factor
```

この `cog_factor` の口 (= 設計書 §3.3、Frozenset の cog_factor 経路 = v9.7 cognitive feedback)
に `atomset_factor` を流した。v105 の NOTE 通り `torque_factor` を設定しない状態は v9.6 と
同一挙動なので、ここに値を書くこと自体が設計済みの接続口を使うことに相当する。

- bonus 育成 (k=0.5, C0=10.0) は **M2 と byte 単位で同一**。M2 で「頻度集計は物理に無害
  (6 ファイル bit-identity)」が確定済なので、本 M3 で出る diff は **torque 接続のみに由来** する。
- 物理層 (`genesis_physics`、イベント発生) は不可侵。VirtualLayer 内 torque のみ操作。
- 飽和係数 GAIN を **0→小→中** で段階的にかけ、各段で発散を確認してから上げた。

| 条件 | GAIN | atomset_factor 上限 |
|------|------|------|
| off    | 0.0 | 1.0 (制御群) |
| small  | 0.5 | 1.0 + 0.5·bonus |
| medium | 1.0 | 1.0 + 1.0·bonus (設計書 nominal) |

## 結果 (3 条件、各 ~12 分、発散ゼロ)

### (A) 制御群: off は M2 baseline と bit-identity ✓

GAIN=0 では `atomset_factor=1.0` を **明示設定しても** torque は変わらない。6 ファイル全一致:

| ファイル | rows × cols | 一致 |
|---|---|---|
| per_subject | 25 × 152 | ✓ |
| link_life | 104987 × 8 | ✓ |
| link_snap | 9328 × 4 | ✓ |
| label_member | 28 × 6 | ✓ |
| audit_event | 119 × 15 | ✓ |
| audit_subj | 25 × 14 | ✓ |

→ 配線は gated。off で無害 = 「torque 接続コードが正しく `factor=1.0` で no-op になる」ことの証明。

### (B) small / medium は off と diff が出る ✓ (= torque 効果)

GAIN>0 で全 6 ファイルが population ごと変化 (CID 数 off=18 → small=16 → medium=18、
link/audit も連動)。torque が theta を変えた結果、形成・存続する CID 構成が変わった。

**diff が torque 由来である切り分けの根拠** (集計値だけに頼らない):
- w=1 (まだ bonus が無い最初の window) の torque は **3 条件で完全一致** (torque_total=3.7752, events=154)。
- diff は **w=2 で factor>1 が初めて乗った瞬間から始まる**。
- bonus 育成は M2 で物理無害が確定済。
- → 「factor が乗った所からだけ diff が出る」ので、diff = torque 接続の因果足跡。

### (C) 全条件で発散なし + cog_factor が線形に乗っている ✓

| 条件 | 発散 | 観測最大 factor | factor>1 label | Σtorque_total | 所要 |
|---|---|---|---|---|---|
| off    | なし | 1.0000 | 0 | 16.47 | 721s |
| small  | なし | 1.1905 | 9 | 18.43 | 711s |
| medium | なし | 1.3837 | 11 | 18.63 | 714s |

- `theta` は全条件で範囲内 (|theta|>100 / NaN なし)。GAIN を中まで上げても発散しない。
- `Σtorque_total` が GAIN とともに単調増 (16.47 ≤ 18.43 ≤ 18.63)。cog_factor は torque_mag に
  線形に効く multiplier なので、これは「bonus が torque に実際に乗っている」感応指標
  (集計値が処置に鈍感になる罠を回避: cog_factor は構造保存変換ではない)。

## 訂正・追補 (2026-06-11、Web Claude view + 機構監査を受けて)

本報告の (B) を「population まるごと変化 (CID 数 18→16→18)」で見出しにしたのは粗い (CID 数は
個性化/寡占/安定化を区別しない集計量)。機構と妥当性の精査・私の実験方法の問題抽出は
**`m3_investigation_and_method_audit.md`** に分離した。要点:
- θ→S→ハード閾値 (S<0.007 死 / S≥0.20 island / R>0 seed / share<thr cull、化学ゲート cos(dθ)≥0.7)
  のカスケードで微小 θ 差が CID 数まで分岐する (コード trace + link `(1335,2701)` 寿命 44→108 step で実証)。
- CID 数変化は **唯一の入口 cog_factor の下流**。off≡M2 bit-identity がそれを証明 (隔離は崩れていない)。
- 妥当に言えるのは技術的 PASS まで。個性化 vs 寡占は seed 0・bonus 未 tag で判定不可。

## 留保 (smoke seed 0 を絶対視しない)

- diff は「population まるごと変化」として現れ、局所的な位相整合量としては測っていない。
  カオス系で theta への torque はカスケードするため当然だが、**diff の向き・大きさ・
  「個性化に良いか」は seed 0 smoke では判定不可**。24 seeds main で確認するまで判定保留。
- 本 smoke が確立したのは定性的事実のみ: **(1) 接続が live で因果的、(2) off で無害 (制御群)、
  (3) 中 GAIN でも非発散**。これは 24 seeds main の前提を満たす。

## 規律

- 判定数値 (GAIN, k, C0, event_count) は **CID の観察レコード (per_subject / label parquet) に
  不記載**。GAIN は実験条件 (knob) として summary.json / compare.json にのみ条件名で記載。
- 物理層不可侵、VirtualLayer 内 torque のみ。
- 人工性留保 (cid_atom_sim_matrix は LLM 判定+手定義投影、本物にならない) 継続。

## ファイル

- `m3_smoke.py` — torque 接続実装 (GAIN を argv で off/small/medium)
- `m3_compare.py` — 制御群 bit-identity + diff + 発散の検証
- `run_m3_smoke/{off,small,medium}/summary.json` — 各条件の出口
- `run_m3_smoke/compare.json` — 総合判定

## 次

**24 seeds main は未着手** ([[feedback-smoke-then-pause]] 遵守)。本 smoke 報告を Web Claude view に
渡し、承認を得てから main に進む。
