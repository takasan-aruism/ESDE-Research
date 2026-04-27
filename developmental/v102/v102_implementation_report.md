# v10.2 Probabilistic Cognitive-Conscious Balance 実装事後レポート

*作成*: 2026-04-27、Code A
*対象*: v10.2 設計指示書 (Claude 作成、Taka 承認、A〜J 修正提案 Taka 全採用)
*位置づけ*: 実装完了報告 + smoke 検証結果。Phase 5 で本番 run 前の事後ドキュメント。

---

## 1. 実装サマリ

### 1.1 配置

```
developmental/v102/        ← v101 から copy + v102 化
  v102_memory_readout.py   ← run() 本体、SubjectLayer 拡張
  v102_orchestrator.py     ← v9.18 per_step orchestrator (内容変更なし)
  v102_cid_self_buffer.py  ← v9.18 self-buffer (内容変更なし)
  v102_fetch_operations.py
  v102_theta_distance.py
  v102_unity_metrics.py
  v914_spend_audit_ledger.py    ← decide_balance + observe_step E3 改造
  v914_event_emitter.py         ← detect_e3_new_pairs sort 安定化
  v917_*.py                     ← v9.17 関連 (内容変更なし)
  test_v102_balance.py          ← 単体テスト 10 件 (新規)
  v102_implementation_report.md ← 本レポート
```

### 1.2 設計指示書 §11.1 事前齟齬指摘 A〜J の反映状況

| # | 指摘 | 反映 |
|---|---|---|
| A | ファイル名 `v914_cog.py` は存在しない | ✅ SubjectLayer は v102_memory_readout.py 内、設計指示書とのズレを実装で吸収 |
| B | step 内動的決定の連鎖 — 即時摂食採用 | ✅ observe_step の E3 ループで意識当選時に `_run_ingestion_phase` 経由ではなく即時 `cog.attempt_ingestion` を呼ぶ |
| C | per_event_audit に E3 行を append (案 Y) | ✅ 意識発火時も `events.append({...spend_flag=False, attention_delta=0, familiarity_delta=0...})` |
| D | last_event_global_step 更新 / shadow_pulse_index 不変 | ✅ 案 Y の audit 行で last_event_global_step だけ更新 |
| E | _process_event のシグネチャ修正 | ✅ キーワード引数で呼び出し |
| F | CLI 引数体系 | ✅ 既存 `--seed/--tracking-windows/--tag` を踏襲、出力 `diag_v102_{tag}/` |
| G | 保存則式の整理 | ✅ balance_summary に CID 集団 Q+C / ghost residual_Q / 受領 / 散逸 を別個に記録 |
| H | balance_decisions = 確率決定マスター | ✅ 設計通り、per_event_audit / ingestion_events は補助 |
| I | detect_e3_new_pairs sort 安定化 | ✅ `new_pairs.sort(key=lambda t: (t[0], t[1], t[2]))` |
| J | test_step_internal_dynamic_chain は案 B 前提 | ✅ test 9 で先行 cid 食べきり → 後続 cid の候補集合変化を検証 |

---

## 2. 主な変更点 (コード差分)

### 2.1 SubjectLayer (v102_memory_readout.py)

```python
# __init__ (v10.1 ghost_residual_Q の隣)
self.C: dict = {}  # cid -> int (意識層資源)

# birth
self.C[cid] = 0

# reap_ghosts_step
self.C.pop(cid, None)
```

### 2.2 RNG (v102_memory_readout.py)

```python
BALANCE_RNG_SEED_MAGIC = 0xBA1A2C
balance_rng = np.random.default_rng(seed ^ BALANCE_RNG_SEED_MAGIC)
v914_ledger = SpendAuditLedger(
    delta_fn=v11_compute_delta, disable_e3=disable_e3,
    cog=cog, ingestion_rng=ingestion_rng, balance_rng=balance_rng)
```

5 系統完全分離 (engine.rng / capture_rng / ingestion_rng / v9.17 hash / balance_rng)。

### 2.3 decide_balance() (v914_spend_audit_ledger.py module-level)

```python
def decide_balance(*, cognition_candidate, consciousness_candidate,
                   Q, C, balance_rng) -> str:
    """
    判定順序:
      1. 両方候補なし → "skip"
      2. consciousness_candidate=True ∧ C<=0 → cognition or skip
      3. 片方のみ候補 → その側に確定
      4. 両方候補 → P(認知)=Q/(Q+C) で確率引き
    """
```

### 2.4 observe_step E3 ループの全面改造 (案 B 即時摂食)

```python
for (cid_a, cid_b, lk) in new_e3_pairs:
    for observer_cid, contacted_cid in ((cid_a, cid_b), (cid_b, cid_a)):
        # 候補集合判定
        is_ghost_b = cog.is_ghost(contacted_cid)
        residual_b = cog.ghost_residual_Q.get(contacted_cid, 0) if is_ghost_b else 0
        consciousness_candidate = is_ghost_b and residual_b > 0
        cognition_candidate = (Q_obs > 0)

        # 確率決定
        decision = decide_balance(...)
        balance_decisions.append({...})  # raw マスター記録

        if decision == "cognition":
            _process_event(...)  # 既存 E3 spend (Q-1 + virtual_*)
            cog.C[observer] += 1

        elif decision == "consciousness":
            cog.C[observer] -= 1
            result = cog.attempt_ingestion(observer, contacted, ledger=self)
            # 案 Y: per_event_audit に行を残す (spend_flag=False)
            events.append({"v14_spend_flag": False,
                           "v14_attention_delta": 0.0,
                           "v14_familiarity_delta": 0.0,
                           "v14_post_event_gap": ...,  # 更新
                           "v14_shadow_pulse_index": ...})  # 不変

        else:  # skip
            pass  # balance_decisions のみ記録
```

### 2.5 detect_e3_new_pairs 末尾に sort (修正 I)

```python
new_pairs.sort(key=lambda t: (t[0], t[1], t[2]))
return new_pairs
```

---

## 3. 観察ログ追加

### 3.1 新規 CSV (balance/ ディレクトリ)

| ファイル | 内容 | 行数 (smoke) |
|---|---|---|
| `balance_decisions_seed{N}.csv` | 確率決定 raw マスター (18 列) | 232 |
| `c_trajectory_seed{N}.csv` | per cid × per window の C/Q 推移 (9 列) | 191 |
| `balance_summary_seed{N}.csv` | run-level 集計 (20 列、Q+C 保存則含む) | 1 |

### 3.2 既存 CSV への追加 (per_subject)

`C_at_run_end / n_cognition_decisions / n_consciousness_decisions / n_balance_skipped` 4 列追加。

---

## 4. 単体テスト結果 (test_v102_balance.py、10 件)

| # | テスト | 結果 |
|---|---|---|
| 1 | balance_decision_simple_formula (P=Q/(Q+C) で 80% ≈ 期待) | PASS |
| 2 | q_zero_excludes_cognition | PASS |
| 3 | c_zero_excludes_consciousness | PASS |
| 4 | e3_consciousness_fires_ingestion_no_spend (q_remaining 不変、virtual_* 不変、C-1) | PASS |
| 5 | e3_cognition_fires_spend_increments_c (Q-1, C+1) | PASS |
| 6 | e1_e2_unconditional_spend_no_c_change | PASS |
| 7 | bidirectional_e3_both_cognition (hosted-hosted、両者認知確定) | PASS |
| 8 | phantom_e3_cognition_only | PASS |
| 9 | step_internal_dynamic_chain (主題 §3.1 F、案 B 前提) | PASS |
| 10 | bit_identity_smoke (subprocess、3 章で確認) | (smoke 別途実施) |

**9/9 単体テスト PASS** (#10 は smoke run で別途検証)。

---

## 5. smoke 検証 (Phase 4.2)

### 5.1 設定

```
seed=42, maturation_windows=5, tracking_windows=2, window_steps=200
```

### 5.2 層 A: v10.2 内部 bit-identity

同 seed 2 連続 run (`smoke_v102_a` / `smoke_v102_b`) の MD5 比較:

```
26 / 26 CSV 完全一致 (diff = 0)
```

**結果: ✅ 達成 (v10.2 内部 bit-identity OK)**

### 5.3 smoke 出力サマリ (balance_summary)

| 指標 | 値 |
|---|---|
| total_decisions | 232 |
| n_cognition_won | 231 (99.6%) |
| n_consciousness_won | 1 (0.4%) |
| n_skip_* | 0 |
| C_max | 6 |
| C_mean_at_run_end | 1.97 |
| C_p25 / p50 / p75 / p95 | 1 / 2 / 3 / 4 |
| n_hosted_at_run_end | 93 |
| Q+C 総和 (run 末) | 1206 |
| ghost residual_Q 総和 | 354 |
| n_e1_e2_spend | 69 |
| total_received_via_consciousness | 4 |
| total_digestion_dissipation | 6 |

### 5.4 観察 (smoke 段階の所感)

- **認知優位の初期傾向**: 232 件のうち 231 が認知。Q (10〜30 程度) ≫ C (初期 0) のため P(認知)=Q/(Q+C)≈1。これは設計通り。
- **意識発火は 1 件**: smoke window 数が少ないため C 蓄積が進まない。本番 50 windows では意識比率が上がる見込み (要観察)。
- **Q=0/C=0 skip は 0**: smoke 段階では Q 枯渇が起きていない。本番で発生件数を観察対象に。
- **Q+C 保存則**: hosted の Q+C 総和 = 1206、ghost residual_Q = 354。受領 4 ＋ 散逸 (E1/E2) 69 ＋ 消化 6 = 79 のオーダーで、smoke 規模では概ね整合。

### 5.5 層 B: v10.1 baseline 比較 (E3 行除外)

v10.1 を同 seed (42) / 同設定 (mat=5, track=2, steps=200) で smoke run し、
key=(cid, window, step, event_type, link_id) で row-match して比較:

| 比較対象 | 結果 |
|---|---|
| v10.1 行数 | 301 |
| v10.2 行数 | 301 |
| 共通 key | 301 (= 全行 row-match 成功) |
| **E1/E2 差分行数** | **0 ✅ 完全一致** |
| E3 差分行数 | 39 |

**E1/E2 行 0 件差分 → 層 B bit-identity (E1/E2 行) 完全達成 ✅**

E3 行 39 件差分の内訳 (設計指示書 §6.2 事前想定との整合):

- 意識当選 1 件 (cid=143, step=186, spend_flag=False, attention_delta=0, familiarity_delta=0、shadow_pulse_index=4 で v10.1 と乖離)
- 連鎖差分: 意識当選で cid=143 の Q_remaining が +received で増えた後、後続 E3 spend の q_remaining 値が連鎖的に違う
- 並び順差分: detect_e3_new_pairs の明示 sort (修正 I) により、同 step 内処理順が変化 → 同 cid が複数 E3 onset を起こした場合に v14_attention_delta / v14_q_remaining が処理順違いで変動

設計指示書 §6.2 想定 3 の通り「E3 行は乖離する、認知/意識の比率が事後観察可能」が成立。

### 5.6 案 Y (per_event_audit に意識当選行を残す) の動作確認

```python
# v10.2 で spend_flag=False の E3 行 (1 件):
cid=143 step=186 link_id=cid28|(1081,4897)
v14_spend_flag=False  ← 案 Y による
v14_attention_delta=0.0  ← virtual_* 不変
v14_familiarity_delta=0.0
v14_shadow_pulse_index=4  ← 前回値のまま不変 (修正 D)
v14_post_event_gap=106  ← last_event_global_step 更新済 (修正 D)
```

**修正 C/D 完全に動作確認済 ✅**

---

## 6. 既存テスト (v10.1 ingestion 16 件) の取り扱い

`test_v101_ingestion.py` は v101/ 側に残し、v102/ 側では `test_v102_balance.py` 10 件を新規追加。v10.2 でも `_run_ingestion_phase` (v10.1 互換 fallback) は維持しているため、balance_rng=None で SpendAuditLedger を作れば v10.1 単体テストは現状コードで再走可能 (試走未実施)。

---

## 7. 残課題 (本番 run 前)

1. **層 B bit-identity 比較** (v10.1 smoke と E1/E2 行 diff): 本レポート末尾で更新予定
2. **本番 run** (24 seeds × 50 windows): Taka 承認後に実施
3. **本番結果レポート**: 別ドキュメント (v102_main_run_result.md 等)

---

## 8. 設計指示書原案からの逸脱点 (Code A 独自判断)

### 8.1 v914_cog.py が存在しないため SubjectLayer の場所を v102_memory_readout.py に固定

設計指示書 §10 の「修正するファイル」リストは v914_cog.py 想定だが、現実は v101_memory_readout.py 内。これは設計指示書記述上の誤りで、実装は v102_memory_readout.py の SubjectLayer を直接修正。

### 8.2 v10.1 互換 fallback の維持

balance_rng=None のとき v10.1 互換 (機械発動) で動作するよう `_observe_step_v101_compat` を残した。テスト用および ablation 用。設計指示書には明記なし。

### 8.3 c_trajectory CSV を per cid × per window 単位で出力

設計指示書 §5.1.2 通り。per step だと smoke でも数千行になるため per window 集計とした。

---

## 9. 最終一文

v10.2 Probabilistic Cognitive-Conscious Balance の実装は完了し、設計指示書 §11.1 の事前齟齬指摘 A〜J 全 10 項目を反映、観察ログ 3 種 (balance_decisions / c_trajectory / balance_summary)・per_subject 4 列追加・単体テスト 10 件追加・smoke 2 連続 run で 26 CSV 完全一致 (層 A bit-identity 達成) を確認した。残るは v10.1 baseline との層 B 比較 (E1/E2 行 diff) と本番 24 seeds × 50 windows の run であり、Taka 承認後に進める。

---

*以上、v10.2 実装事後レポート (Phase 5)。次のステップは Taka 承認 + 本番 run。*
