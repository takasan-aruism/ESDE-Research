# v1108a Step A — Code A 認識確認

**Date**: 2026-05-29
**Author**: Code A (実装担当)
**Status**: Step A 認識確認、**実装制約 1 件あり (Web Claude / Taka 確認必須)**
**親**: v1108a 設計書草案 (Web Claude、2026-05-29)

---

## 0. 受領内容認識

### 0.1 主題
v1108a — 時間軸を跨いだ Atom 遷移結合の観察 (Gemini 推奨方向、問いの形 A 点検)
- 観察 1: ΔC_ij (Atom 遷移結合カーネル)
- 観察 2: ρ_FH (Familiarity-Entropy 連動曲率)
- 観察 3: 時間軸シャッフル baseline
- 観察 4: Gemini 予測 1/2 検証

### 0.2 設計書冒頭予防規律 11 件 (受領)
- 6 段階目ミス予防 (実験設計を疑う) 4 件
- 5 段階目ミス予防 (他 AI 提案実環境照合) 3 件
- 4 段階目以前 4 件
- Gemini 言葉遣い予防 (内的文法/シンタックス/自発的 削除)

### 0.3 Code A への一言 (受領)
> 「わからんことは言えよな」

→ 本 §1 で **実装制約を隠さず提示**。

---

## 1. 実装制約事前提出 (「わからんことは言えよな」原則)

### 1.1 重大制約: Step H 自己対話に **turn 間 Atom 確率分布全体が記録されていない**

実環境照合結果 (Code A 実測):

| データソース | turn 数 | event 数 | atom_probs 全体 |
|---|---:|---:|---|
| **Step P** (Code A 介在 6 turn 対話) | 13 (T0-T12) | **1 event のみ** | **✓ あり** (各 turn の top-10 atom + 確率) |
| **Step H** (681 CID × 40 turn 自己対話) | 40 | **681 events** | **✗ なし** (top_atom 1 個のみ記録) |

設計書 §2.1 の指標:
```
C_{ij} = <P_t(A_i) * P_{t+1}(A_j)>  (event 平均)
```

→ **「P_t(A_i) (turn t の Atom i の確率)」が Step H には記録されていない**。Step P は 1 event のみ。

### 1.2 影響

| 観察 | 影響 |
|---|---|
| 観察 1 ΔC_ij | **計算不能** (現状)、または重大な情報損失付きで簡易版 |
| 観察 2 ρ_FH (familiarity 連動) | **計算可** (familiarity は Step H に記録あり、エントロピーは top_atom のみだと degenerate) |
| 観察 3 shuffle baseline | 観察 1 が計算不能なら同じく不能 |
| 観察 4 予測 1/2 | 観察 1 依存、同じく影響 |

### 1.3 解決案 4 つ (Web Claude / Taka 判断要)

#### 案 A: Step H 自己対話を atom_probs 記録版で再実行 (Code A 推奨)
- 既存 `v1106b_step_h_observation_4_main.py` を修正、`top_atom` の代わりに `atom_probs` 全体 (top-10 atom + 確率) を記録
- 実行時間: 元 32.5 秒 + atom_probs 保存で 1-2 分以内予想
- 出力: `unified/v1108a/outputs/main/self_dialogue_with_atom_probs.parquet`
- 物理層 frozen 維持 (v1108a 配下のみ書込み、v1106b は read-only)
- **Step P と同じ精度** (top-10 atom + 確率)

#### 案 B: Step P 6 turn のみで計算 (統計的に弱い)
- event 数 1 のみ、ΔC_ij の shuffle baseline 統計が不安定
- Gemini 予測 1 (社会的 vs 孤立の τ 比較) は input 1 つしかなく検証不能

#### 案 C: Step H 既存データで top_atom 1 個 × top_atom 1 個の簡易版 ΔC_ij
- 各 turn の top_atom が確率 1.0 と仮定 (情報損失大)
- 326 × 326 ペア中、実際に出現する組み合わせは極めて疎 (681 events × 40 turn = 27,240 ペア)
- 統計的に意味のある ΔC_ij は限定的

#### 案 D: 観察対象を変更 (Atom 遷移でなく CID 遷移)
- Step H には turn ごとの `cid` が記録されている
- CID ペア (cid_t → cid_{t+1}) の遷移カーネル ΔC_ij を計算
- v1106b 観察 2 (循環構造 attractor) との接続が深い
- 「Atom 遷移」(Gemini 案) から「CID 遷移」(Code A 案) へのシフトで本主題趣旨が変わる可能性

### 1.4 Code A 推奨

**案 A** を推奨:
- Gemini 案の主旨「Atom 遷移カーネル」を保持
- top-10 atom + 確率で実質的な確率分布として使える (Step P の精度と同等)
- 物理層 frozen 維持 (新規 main run でなく、Step H の出力フォーマット拡張)
- 実装軽量 (1-2 分)
- bit-identity 検証は v1108a 内で完結

### 1.5 Web Claude / Taka 判断要

| 判断 | 案 |
|---|---|
| 1 | 案 A 採用、Step H 再実行で atom_probs 記録 |
| 2 | 案 B 採用、Step P 6 turn のみ (検証統計的に弱い) |
| 3 | 案 C 採用、top_atom のみで簡易版 (情報損失大) |
| 4 | 案 D 採用、Atom 遷移を CID 遷移に置き換え (主題趣旨変更) |
| 5 | 他案、Web Claude / Taka 提示 |

---

## 2. データ取り違え防止 §0.7

| データ | パス | 状態 |
|---|---|---|
| v1106b dialogue_code_a_chat | `unified/v1106a/outputs/main/dialogue_code_a_chat.json` | frozen ✓ |
| v1106b 自己対話 (top_atom) | `unified/v1106b/outputs/main/observation_4_self_dialogue.parquet` | frozen ✓ |
| v106 cid_atom_sim_matrix | (24 seeds) | frozen ✓ |
| v1106a 案 Y word 分布 | `unified/v1106a/outputs/main/observation_Y_word_distributions.parquet` | frozen ✓ |
| v1106b 案 E 選定 CID | `unified/v1106b/outputs/main/env_check_selected_cids.parquet` | frozen ✓ |

全 frozen 確認。書込みは `unified/v1108a/outputs/main/` 配下のみ。

---

## 3. 計算量事前確認は不要 (受領、Taka 判断 4)

想定: v1106b 2 分、v1107 約 1 分実績ベース。案 A 採用なら Step H 再実行込みで 2-5 分程度。

---

## 4. 規律遵守確認

| 規律 | 遵守確認 |
|---|---|
| 絶対格言 15 件 | ✓ |
| 6 段階目ミス予防 (実験設計を疑う) | ✓ §1 で実装制約事前提出 |
| 5 段階目ミス予防 | ✓ Gemini 案数式を Code A 実測で確認 |
| 4 段階目以前予防 | ✓ §1.2 で集約関数情報損失明示 (Step H top_atom = 確率 1.0 の degenerate 化) |
| Gemini 言葉遣い予防 | ✓ §0.2 で受領、本文書で確定的呼称回避 |
| 物理層 frozen | ✓ 案 A でも v1108a 配下のみ書込み |
| ボツも構造事実 | ✓ Web Claude 設計書 §3 で構造ラベル 8 通り事前確定 |
| わからんことは言えよな | ✓ §1 で実装制約事前提出 |

---

## 5. Step 分解 (案 A 採用前提)

| Step | 内容 |
|---|---|
| A | 本文書、認識確認 + 案 A 推奨 |
| B | 環境準備 + Step H 再実行版実装 (atom_probs 記録) |
| C | 観察 1 (ΔC_ij Atom ペア結合カーネル) |
| D | 観察 2 (ρ_FH Familiarity-Entropy 連動) |
| E | 観察 3 (時間軸シャッフル baseline) |
| F | 観察 4 (Gemini 予測 1/2 検証) |
| G | bit-identity 3 層検証 |
| H | 観察事実最終報告 + 構造ラベル 8 通り判定 |

---

## 6. Web Claude / Taka への確認

| 項目 | Code A 提案 | 確認待ち |
|---|---|---|
| 案 A 採用 (Step H atom_probs 記録版再実行) | 推奨 | Web Claude / Taka 判断 |
| Step P 6 turn を補助観察として併用 | OK | 確認待ち |
| 案 D (CID 遷移に置き換え) を補助で実施するか | 主題趣旨変更含む | 確認待ち |

---

**Step A end. 実装制約 1 件提示、Web Claude / Taka 判断後に Step B 進行。**
