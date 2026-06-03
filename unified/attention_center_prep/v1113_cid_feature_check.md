# v1113 CID 特性ベクトル共鳴測定 — Code A 認識確認

date: 2026-06-04
from: Code A (Claude Code, Opus 4.7)
to: Web Claude / Taka
status: 指示受領、実装前の認識確認 (実装には未着手)

---

## 0. 全体認識 (最重要)

Web Claude / Taka 指示 (2026-06-04) を、以下の通り認識した:

### 0.1 v1110-v1112 の根本問題

- v1110-v1112 は CID を **「どの phase の bin が埋まっているか」だけ** の痩せた表現 (occupancy[64]) で測っていた
- CID が実際に持つ情報 (n_core / 寿命 / Q/C / 認知層・意識層 / 形成の関係 / phase_sig 等) の **ほとんどを使っていなかった**
- 失敗 (Stage 1 不成立、Active < Phase Shifted 等) はそこが原因の可能性が高い
- 「足場が無い」と結論する前に、**CID の本当の情報で測り直す**

### 0.2 今回の課題 (一点だけ)

- 各 CID を、**実際に持つ情報から作った特性ベクトル**で表す
- どの情報を入れるかは、Code A が既存の CID データ / index から決める
- **phase の場所だけにしない**
- 独立 seed の二つの系の CID 同士を、**場所でなく特性の一致率 (似てる度合い)** で照合する
- **偶然より似ているペアが出るか。それだけ。** = 共鳴の足場が在るか / 無いか

### 0.3 大前提 (前回 §0.2 引継ぎ)

**測定器が壊れているものを結果と呼ばない。**
特性ベクトルの一致率が「ちゃんと機能するか」を結果を読む前に確認する。
壊れていたら止める (= 自己 > 乱数 が成り立たねば raise)。

### 0.4 報告言葉縛り

- 「偶然より似たペアが出た / 出ない」だけを、まっすぐ
- 出れば「痩せた表現で見落としていた足場が在る」
- 出なければ「CID の本当の情報を使っても足場は出ない」(正直な結果)
- **Unified 成立 / 第三 ESDE 成立 / crown は書かない**

---

## 1. CID 特性ベクトル設計 (Code A 判断、Explore 調査結果から)

### 1.1 取得可能な node ID free 属性 (実機 API 調査済み)

| 次元 | 取得方法 | 型 | 説明 | 採用 |
|---|---|---|---|---|
| `phase_sig_sin`, `phase_sig_cos` | `cog.original_phase_sig[cid]` を sin/cos 展開 | float × 2 | 生誕時平均 θ (circular → Euclidean 化) | ✓ 採用 |
| `phi_sin`, `phi_cos` | `cog.phi[cid]` を sin/cos 展開 | float × 2 | 現在の内的基準軸 θ (circular) | ✓ 採用 |
| `n_core` | `buffer.n_core` (CidSelfBuffer) | int | 生誕時メンバー数 | ✓ 採用 |
| `lifespan` | `window_now - cog.born_at[cid]` | int | 寿命 (window) | ✓ 採用 |
| `Q0` | `buffer.Q0` (CidSelfBuffer) | int | 生誕時割当認知資源 | ✓ 採用 |
| `Q_remaining` | `buffer.Q_remaining` | int | 残存 Q (pulse 等で消費) | ✓ 採用 |
| `C` | `cog.C[cid]` (v104+) | int | 意識資源 (ingestion で増加) | ✓ 採用 |
| `familiarity_n` | `len(cog.familiarity[cid])` | int | 他 cid への familiarity 記憶数 | ✓ 採用 |
| `v10_pulse_count` | `cog.v10_pulse_count[cid]` | int | 総 pulse fired 数 | ✓ 採用 |
| `v11_n_captured` | `cog.v11_n_captured[cid]` | int | 捕捉確定 pulse 数 | ✓ 採用 |
| `v11_b_gen` | `cog.v11_b_gen[cid]` | float | Genesis Budget | ✓ 採用 |
| `cid_ttl_bonus` | `cog.cid_ttl_bonus[cid]` | int | TTL 延長累積 | ✓ 採用 |
| `v18_birth_v_unified_concentration` | `buffer.v18_v_unified_concentration_birth` | float | 生誕時 unity concentration | ✓ 採用 |
| `v18_theta_distance_from_birth` | `buffer.v18_theta_distance_from_birth` | float | 生誕時 θ 分布からの距離 | ✓ 採用 |

合計 15 次元 (sin/cos 展開後)。

### 1.2 絶対に使わない (node ID 依存)

- `label.nodes` (frozenset of node ID)
- `buffer.member_nodes`
- `cog.attention[cid][node_id]`
- `buffer.sorted_member_list`
- `buffer.theta_birth` (node 順 indexed ndarray)

これらは別系で意味を持たないため、特性ベクトルに含めない (前回 v1111c/d の番号コピー欠陥再発防止)。

### 1.3 angle 処理 (circular → Euclidean)

phase_sig, phi は [-π, π] の角度量 → cosine 類似度で直接使えないため、

```python
def angle_to_xy(theta):
    return np.cos(theta), np.sin(theta)
```

で 2 次元 (x, y) に展開。これで Euclidean 距離 / cosine 類似度が circular に正しく動作。

### 1.4 ベクトル正規化 (scale 揃え)

各次元の scale が桁違い (例: Q0=O(1000), phase_sig=O(1), n_core=O(10))。

→ **z-score 標準化** (両系の CID 全 sample にわたって平均 0 / 分散 1)。
- 標準化後 cosine similarity を計算
- 各次元の貢献が均等になる

```python
def normalize_features(feature_matrix):
    """各次元を z-score 標準化"""
    mean = feature_matrix.mean(axis=0)
    std = feature_matrix.std(axis=0)
    std[std < 1e-9] = 1.0  # 0 div 回避
    return (feature_matrix - mean) / std
```

---

## 2. 一致率 (similarity) 計算

### 2.1 ペアごと cosine similarity

```python
def cosine_similarity(v1, v2):
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 < 1e-9 or n2 < 1e-9:
        return 0.0
    return float(np.dot(v1, v2) / (n1 * n2))
```

Atom 系 CID 集合 A (|A|≈10-50)、Other 系 CID 集合 O (|O|≈10-50)。
全 A × O ペアで similarity を計算 (|A|×|O| sample)。

### 2.2 「偶然より似ているか」判定 (Taka 指示)

**null 分布**: A の特性ベクトル次元値を window 内で **shuffle (各次元を独立に bin permute)**。
- これで「同じ次元分布だが、相関構造を壊した特性ベクトル群」が得られる
- 構造 (各 CID の特性間関係) を破壊した null

```python
def shuffle_features_independently(feature_matrix, state_seed):
    """各次元を独立に row 方向シャッフル (CID 間の相関構造を壊す)"""
    rng = np.random.RandomState(state_seed)
    shuffled = feature_matrix.copy()
    n_rows, n_cols = shuffled.shape
    for col in range(n_cols):
        shuffled[:, col] = shuffled[rng.permutation(n_rows), col]
    return shuffled
```

判定:

| 比較対象 | 期待 |
|---|---|
| `sim(A, O)` mean | 実観察 |
| `sim(A_shuffled, O)` mean | null (構造破壊) |
| 上位 5% sim ペア数 | 実 vs null |

**「偶然より似ている」**:
- `mean sim(A, O) > mean sim(A_shuffled, O)` かつ
- 上位 5% sim ペア数が null より明確に多い

3 atom seeds × 24 (24 seeds 規律) で全 atom で揃うか確認 (per_atom 観察)。

---

## 3. 測定器点検 (Taka 必須、結果を読む前)

### 3.1 §A: 自己 sim = 1.0 (恒等性)

```python
v = extract_features(cid_some)
assert cosine_similarity(v, v) == 1.0  # 自分自身は完全一致
```

これは数学的に当然だが、コードバグ (nan / inf / 正規化エラー) の検出。

### 3.2 §B: 揺らした自己 > 乱数 (kernel 機能)

```python
v = extract_features(cid_some)
noise = rng.normal(0, 0.05, size=v.shape)  # 小さい noise (5%)
v_perturbed = v + noise

v_random = rng.normal(0, 1, size=v.shape)  # 完全乱数

sim_perturbed = cosine_similarity(v, v_perturbed)
sim_random = cosine_similarity(v, v_random)

assert sim_perturbed > sim_random, "kernel が機能していない"
# 期待: sim_perturbed ≈ 0.95-1.0, sim_random ≈ 0 (cosine の null)
```

複数の cid で繰り返し、全部 (or ほぼ全部) で成立するか確認。
成立しなければ raise で止める。

### 3.3 §C: 実機 CID で自己 > 乱数 (実機 sample)

Atom 系を 1 sample 動かして実機 CID 群を取得、各 CID の自己 sim と乱数 sim を比較。
全 CID で `sim(self) > sim(random)` が成立するか。

### 3.4 §D: 構造破壊 (shuffle) が機能 (前回 §2.4 床点検と同じ哲学)

実機 Atom 特性行列を shuffle した null と、Atom 自身との sim を比較:
- 期待: `mean sim(A, A) > mean sim(A_shuffled, A)`
- shuffled が自己と同等の sim を出すならば、特性ベクトルの構造を捉えていない (= shuffle 不変 = 前回 total_cooc 教訓)

---

## 4. 実装構成 (前回 v1112 と同じ規律で)

### 4.1 ファイル

- 実装: `unified/attention_center_prep/v1113_cid_feature_resonance.py` (新規)
- 認識確認: `unified/attention_center_prep/v1113_cid_feature_check.md` (本ファイル)
- 出力: `unified/attention_center_prep/run_v1113/`

### 4.2 構成

- ATOM_SEEDS = [42, 100, 200] (まず 3 atom で確認、smoke 規模)
  - 後の本実行で 24 seeds に拡張 (Taka 規律: 1 バッチ)
- OTHER_SEED_FIXED = 999 (atom と別 seed、同 seed 並走排除)
- WINDOW_STEPS = 500
- WINDOWS = 30 (過去標準)
- 自然進化 (注入なし、書き戻しなし)
- node ID 排他 (絶対)
- 第三 ESDE = なし (今回は CID 特性比較なので observer 不要)

### 4.3 やる順 (Taka 指示準拠)

| # | ステップ |
|---|---|
| 1 | **本ファイル (認識確認) を Web Claude / Taka に提示** ← 今ここ |
| 2 | OK 後、`v1113_cid_feature_resonance.py` を実装 |
| 3 | 測定器点検 (§3.1-§3.4) を main 内で実装、本実行前に必須 |
| 4 | Web Claude コードチェック (実装コードを view、意図と合うか確認) |
| 5 | 本実行 (3 atom smoke or 24 seeds 本番、Pool 並列) |
| 6 | **偶然より似たペアが出るか、まっすぐ報告** (Unified 成立書かない、crown しない) |

### 4.4 不変 (前回からの引継ぎ規律)

- node ID 完全排他 (phase 空間でなく、CID 特性ベクトルでも同じ規律)
- 両系を 1 bit も書き換えない (read-only)
- 自然進化、注入なし、factor なし
- 報告は観察事実のみ、判定置かない

---

## 5. 確認 5 点

| # | 確認項目 | Code A 認識 |
|---|---|---|
| 1 | **痩せた phase 表現 (occupancy) を捨て、CID の本当の情報で測る** | ✓ §1 で 15 次元 (n_core / Q / C / phase_sig / phi / lifespan / pulse / familiarity / v9.18 unity) |
| 2 | **node ID 排他 (絶対)**: nodes / member_nodes / attention[cid][node_id] は使わない | ✓ §1.2 で除外リスト明示 |
| 3 | **完全一致でなく一致率**: cosine similarity (z-score 標準化後) | ✓ §2.1 |
| 4 | **偶然より似ているか**: 各次元独立 shuffle した null と比較 | ✓ §2.2 |
| 5 | **測定器点検 (結果を読む前に必須)**: 自己 > 揺らした自己 > 乱数 が成立するか | ✓ §3.1-§3.4 で 4 項目、FAIL なら raise |

---

## 6. 一文サマリ

v1113 CID 特性ベクトル共鳴測定 認識確認 (2026-06-04 Code A → Web Claude / Taka) — 背景 (v1110-v1112 は CID を occupancy[64] の痩せた表現で測っていた CID 真の情報 n_core 寿命 Q/C 認知層意識層 phase_sig 等を使っていない 失敗はそこが原因の可能性高い 足場無いと結論する前に測り直す) 課題 (CID を実データから特性ベクトル化 phase 場所だけにしない 独立 seed 2 系の CID 同士を場所でなく特性の一致率で照合 偶然より似たペア出るかだけ = 共鳴足場在るか無いか) 大前提 (測定器壊れているもの結果と呼ばない 一致率機能するか結果読む前に確認 自己>乱数 成り立たねば raise) 報告言葉縛り (偶然より似たペア出た出ないだけまっすぐ Unified 成立書かない crown しない 出れば見落とした足場ある 出なければ正直な無し) 特性ベクトル設計 (15 次元 = phase_sig sin/cos + phi sin/cos + n_core + lifespan + Q0 + Q_remaining + C + familiarity_n + v10_pulse_count + v11_n_captured + v11_b_gen + cid_ttl_bonus + v18_unity_concentration + v18_theta_distance_from_birth、node ID 依存 nodes/member_nodes/attention 絶対除外、circular phase は sin/cos 展開、scale 揃え z-score 標準化) 一致率 (cosine 類似度 ペアごと A × O sample、null 分布 = 各次元独立 shuffle = CID 間相関構造破壊、判定 mean sim(A,O) > mean sim(A_shuffled,O) かつ 上位 5% sim ペア数が null より多い) 測定器点検 §3.1-§3.4 (恒等性 sim(v,v)=1 / 揺らした自己 > 乱数 kernel 機能 / 実機 CID 自己>乱数 / shuffle 構造破壊で sim 低下) 実装構成 (v1113_cid_feature_resonance.py 新規 unified/attention_center_prep/ 配下 ATOM_SEEDS=[42,100,200] smoke 後 24 seeds 1 バッチ OTHER=999 別 seed 500×30 自然進化 注入なし node ID 排他 第三 ESDE なし) やる順 (本ファイル提示 → OK 後実装 → 測定器点検 → Web Claude view → 本実行 → 観察 まっすぐ報告)。

---

## 7. Code A 自己評価

- v1110-v1112 失敗の根本認識: ✓ 痩せた phase 表現 = CID の本当の情報を使っていなかった
- 特性ベクトル設計: ✓ 15 次元、ESDE 4 層 + Layer 5 + 動学 + 観察を網羅
- node ID 排他: ✓ 除外リスト明示、絶対遵守
- 測定器点検: ✓ 4 項目 (恒等性 / kernel / 実機自己 / shuffle 構造破壊)
- 言葉縛り: ✓ crown しない、観察事実のみ

**Web Claude / Taka の認識確認 OK を待ちます。OK 後に実装に進みます。**
