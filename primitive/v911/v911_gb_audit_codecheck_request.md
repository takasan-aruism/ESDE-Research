# Codecheck Request: v911_genesis_budget_measure.py

> レビュー対象: `primitive/v911/v911_genesis_budget_measure.py`
> 関連出力: `primitive/v911/v911_genesis_budget_audit.md`, `primitive/v911/v911_genesis_budget_raw.csv`
> 作成者: Claude Code (Opus 4.6)
> 日付: 2026-04-13

---

## 目的

v9.10 long run と同一のエンジン構成で label birth 時の B_gen = n_core × S_avg × r_core を計測する。

## 確認ポイント

### 1. エンジン構成の同一性
- V82Engine の初期化パラメータ (stress_enabled=False, virtual_enabled=True) が v910_pulse_model.py と一致しているか
- VirtualLayerV9 の設定 (feedback_gamma=0.10, torque_order="age", deviation_enabled=True, semantic_gravity_enabled=True) が一致しているか

### 2. Tracking フェーズの物理層ループ
- v910_pulse_model.py の tracking loop (L1250-1300) と同一の step 順序か
  - realizer → physics.pre_chem → chem → physics.resonance → grower → intruder → physics.decay_exclusion → background injection
- **既知の差異**: step_window() ではなく手動ループを使用。背景注入の growth bias (BIAS=0.7) の `_g_scores` 計算パスが v910_pulse_model.py からコピーされているが、v82_engine.step_window() 内部の実装と bit-identical かは未検証

### 3. B_gen 計測ロジック
- `measure_birth_stats()` の S_avg 計算: ラベル内ノード間の alive リンクのみを対象としているか
- r_core (Kuramoto order parameter) の計算: `|1/N Σ exp(iθ_j)|` が正しく実装されているか
- 計測タイミング: VL step 直後 (label が labels dict に追加された直後) で engine.state にアクセスしているか

### 4. 出力の妥当性
- n_core の分布が v910 long run の per_label CSV と概ね一致しているか (n_core=2 が 77〜80%)
- リンク数 (links_total) が v910 long run の per_window CSV と同程度か (≈2700)

### 5. レポートの解釈
- PI 試算のロジック: `clamp(α × B_gen, 10, 200)` の計算が正しいか
- 相関分析: corr(S_avg, r_core) = -0.269 の解釈 (交絡効果の説明) は妥当か

---

## レビューアへの依頼

上記 5 点について確認し、このドキュメント内に直接コメントを追記してください。
問題なければ `v911_gb_audit_codecheck_status_approved.md` を、
問題があれば `v911_gb_audit_codecheck_status_denied.md` を作成してください。
