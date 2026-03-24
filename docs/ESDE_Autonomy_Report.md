# ESDE Autonomy Report

*Phase: Autonomy (v8.0–)*
*Status: v8.1d — 48-seed根本原因特定完了。圧縮の「速いlabel」化修正済み。v8.2仕様確定。*
*Team: Taka (Director) / Claude (Implementation) / Gemini (Architecture) / GPT (Audit)*
*Started: March 21, 2026*
*Last updated: March 24, 2026*
*Prerequisites: Cognition complete (see ESDE_Cognition_Report_Final.md)*

---

## Cognition からの引き継ぎ

Cognition phase (v3.0–v7.4) で確立された事実:

| 事実 | 検証規模 |
|------|---------|
| 物理層は動的平衡を自律維持 (sI ≈ 1.0) | 12 seeds, N=10000 |
| R+ ≈ 8 は N にスケールしない | N=5000 vs N=10000 |
| label は位相周波数グループ（空間クラスタではない） | 空間分析, seed=42 |
| R>0 は label 間の境界に出現 | 空間分析, seed=42 |
| label 生存法則: 遅い + 静か + 5 ノード | 1120 born → 9 survived |
| 動的平衡は seed 非依存（普遍） | 12 seeds 全一致 |
| budget=1 は配分比率であってエネルギーではない | v7.3 実装分析 |
| N は重要でない。ルールが構造を生む | v7.4 スケーリング結果 |

## Cognition が残した問い

**中心課題:** budget=1 の仮想エネルギーから、label 単体では
ありえない存在（スケール 3）をどう生むか。

**進展 (v8.0-v8.1):** 認知的結合がスケール 3 の候補として浮上。
label は物理的に無関係な 5 ノードを「グループ」と主張し続ける。
この主張自体が物理層にない新しい種類の存在。

Genesis の precedent:
```
ノード (スケール 1) → リンク → サイクル (スケール 2)
  物理法則: plb, rate, K_sync, decay
  結果: k*=4 が自発的に出現（設計していない）
```

Autonomy で必要なこと:
```
label (スケール 2) → ??? → 新しい存在 (スケール 3)
  法則: 未定義
  物理的根拠: 観測データから導出すべき
```

## アーキテクチャ方針

**Taka 原文:** 「設計可能な数式はある程度物理的な根拠が伴えば許される」

**方向性候補:**
- label 間の位相干渉 → **niche isolation として確認済み**
- label 間の橋 → **未検証。lifecycle data で分析可能**
- ESDE NLP (Phase 8) との統一言語 → **構想段階**
- label 集合の法則化 → **E1-E6 として部分的に数式化**
- 認知的結合 → **仮説として提出。スケール 3 の候補**

---

## Version Changelog

| Version | Date | Author | Core Addition | Key Result |
|---------|------|--------|---------------|------------|
| v8.0 | 03-21 | Taka→Claude | Lifecycle logging | 48-seed 51,163 labels。niche isolation。認知的結合 |
| v8.1 | 03-22 | Gemini→GPT→Claude | Macro-node compression | Tripartite architecture |
| v8.1b | 03-22 | Claude (review) | E4 hardcoded 撤去 | Constitution §3 修正。frozen baseline 導入 |
| v8.1c | 03-23 | Claude (data fix) | S>=0.20 条件撤去 | 圧縮発動成功。物理 ±1%。仮想 -16% 問題 |
| v8.1d | 03-24 | Claude (root cause) | alive_n 除外撤去 | 「速い label」化。検証待ち |

---

## v8.0 — Lifecycle Instrumentation (48-Seed)

48 seeds × N=5000 × 50 steps × 200 windows。

**Niche Isolation（47/48 seed で再現）:**

| 指標 | 生存者 (560) | 死亡者 (50,603) | 比率 |
|------|-------------|----------------|------|
| nearest_label_dist | 0.213 | 0.084 | 2.5× |
| n_phase_neighbors | 1.66 | 31.71 | 0.05× |
| share_mean | 0.087 | 0.021 | 4.1× |

**サイズ生存率:** 5-node は 2-node の 32 倍（7.11% vs 0.22%）
**Carrying Capacity:** K = 12 ± 3.5
**認知的結合:** 5 ノードに物理的接続なし。label は frozenset で主張を維持。
**Coherence 撤回:** 4-seed の territory expansion 仮説は誤り。48-seed で逆転。

---

## 数式化（E1-E6）

| ID | 名称 | 式 / 値 | Status |
|----|------|---------|--------|
| E1 | 生存確率 | P = 0.027 / (1 + exp(-92×(d-0.034))) | PROVISIONAL |
| E2 | サイズ生存率 | S(5)=7.11%, S(2)=0.22% | SAFE |
| E3 | Carrying capacity | K = 12 ± 3.5 | QUARANTINED |
| E4 | Territory scaling | T(n) ≈ 1.4n + 1.2 | 参考値 |
| E5 | Coherence decay | surv:-0.008, dead:-0.028/win | QUARANTINED |
| E6 | Maturation contamination | w190-200 の 26.4% は偽生存 | PROVISIONAL |

---

## v8.1 圧縮 — 試行と根本原因特定

### 圧縮条件の修正履歴

| Version | 条件 | 結果 |
|---------|------|------|
| v8.1 | age>=10 + nodes>=3 + S>=0.20 | **圧縮ゼロ**。Gemini が 48-seed データを見ずに設計 |
| v8.1c | age>=10 + nodes>=3 | 圧縮発動。物理 ±1%。仮想 -16% |
| v8.1d | 同上 + alive_n 除外撤去 | 検証待ち |

### 48-Seed 根本原因診断

GPT 監査指示の 4 仮説:

| 仮説 | 結果 | 根拠 |
|------|------|------|
| A. share 固定が主因 | **否定** | top_share 7.2% 低下。奪っていない |
| B. timing が主因 | **否定** | 38/48 seed で同方向 |
| C. macro-node 存在が ecology を変える | **肯定** | regular -30.9%。niche 永久占有 |
| D. R+ 二次効果 | **否定** | +2.6% で自然変動内 |

### 根本原因

```
alive_n からノード除外 → 物理層がそのノード周辺を凍結
  → macro-node の territory が物理変動を受けない
    → 競争で負けない → niche を永久占有
      → regular label の生存枠 -30.9%
```

**本質:** 物理層は仮想層の「環境」。環境の一部を凍らせると仮想層が荒れた。
物理層自体は壊れない（links ±0.2%）。影響は仮想層にだけ出た。

### v8.1d の修正

macro-node を「強い label」から「速い label」に変更。

| 項目 | v8.1c | v8.1d |
|------|-------|-------|
| alive_n | ノード除外 | **残す** |
| share | frozen baseline | **通常 link count** |
| 物理変動 | 受けない | **受ける** |
| 死亡条件 | 特権的 | **通常 label と同一** |
| 違い | 内部リンクなし | 内部リンクなし（これだけ） |

---

## v8.2 仕様（確定済み、実装待ち）

### 概念（Taka の過去/未来再定義）

```
過去 = 位相空間で既に占有された領域（塗りつぶし）
未来 = まだ占有されていない領域（余白）
現在 = 可能性が現実へ変換される更新面
```

v4.9 は「記憶/予測」をリンクに載せた → リンクが消えた → 全部消えた。
v8.2 は「占有/余白」を位相空間に載せる → 位相空間は消えない。

### v4.9 history tensor の label 移植

| v4.9 (リンク → 失敗) | v8.2 (label) |
|----------------------|-------------|
| h_age (成熟) | death threshold 緩和 |
| h_res (硬直化) | torque 減衰 |
| h_str (脆性) | snap death |
| void field (作った → 消えた) | vacancy V[b]（観測するだけ） |

### 実装フェーズ

| Phase | 内容 | 依存 |
|-------|------|------|
| A | O/H/V ログ追加。ロジック変更なし | v8.1d 検証後 |
| B | vacancy birth filter + maturation + snap | Phase A データ |
| C | MacroNode 統合 | Phase B 安定後 |

---

## 認知的結合仮説

物理層: 5 ノードは無関係。仮想層: 5 ノードは「私のグループ」。
同じ 5 ノードに対する対称的記述。Aruism の存在の対称性。

---

## 設計上の教訓

1. 物理層は床。床に手を加えると仮想層が荒れる (v8.1c)
2. Gemini 設計は 48-seed データと突き合わせてから実装 (v8.1 S>=0.20)
3. 4 seed と 48 seed で解釈が逆転する (coherence)
4. share 固定は表面的原因。物理変動遮断が根本原因 (diagnosis)
5. macro-node は「速い label」。「強い label」にしてはいけない
6. v4.9 の失敗はタイミングの失敗。仮想層に移植すれば使える
7. void は作るものではなく観測するもの
8. 48 並列なら 3 seed も 48 seed も同じ時間。少数テストは不要

---

## Open Questions

1. v8.1d 検証: label 数 -16% は解消されるか？
2. v8.2 Phase A: occupancy/vacancy は label 生死と相関するか？
3. ターンオーバーの数式化は可能か？
4. label 間 R>0 橋の定量分析
5. P(M_k | M_i, M_j): stable unit 間の条件付き生成則
6. NLP 統一言語: 48 次元 ↔ label パラメータ

---

*v8.0 で生存法則を数式化。v8.1 で圧縮を導入し 3 回の修正を経て
「物理層を凍らせると仮想層が荒れる」という本質を発見した。
v8.1d で「速い label」に修正。v8.2 で Taka の過去/未来再定義を実装する。
v4.9 の失敗は無駄ではなかった。*
