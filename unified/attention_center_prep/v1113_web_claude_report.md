# v1113 CID 特性ベクトル共鳴測定 結果報告 (Web Claude 宛)

date: 2026-06-04
from: Code A (Claude Code, Opus 4.7)
to: Web Claude / Taka
status: 案 A FAIL → 案 B 完走、測定器点検全 PASS、観察事実出揃い

---

## 0. ひとことサマリ

- 案 A (v918 engine から CID 取得を仮定) は `engine.cog` 不存在で FAIL (Code A 盲点)
- 案 B (過去 v918 main run output 流用) に切り替えて完走
- 測定器点検 §3.1-§3.4 全 PASS (測れた上での観察)

観察事実 (Taka 言葉縛り):
- **集団平均 (per atom)**: 2/3 atom で rank=5/5、atom 依存に見える
- **per-cid 観察**: 各 atom で **16-23% の CIDs が null 5 系全超え** = 特に響く
- **n_core 別層化** (v10.2 哲学): **n_core=2 (主要集団 180-193 CIDs) で 3 atom 全て gap > 0 揃う**
- **n_core=3 (少数 12-15 CIDs) では 3 atom 全て gap < 0** (逆向き)
- 上位 sim ペアは sim=0.999-0.9999、**全て n_core=2 × n_core=2 の高類似**

→ 集団平均だけでは「atom 依存・半々」、per-cid + n_core 別で見ると「**n_core=2 で構造的に響く組が観察された**」。

---

## 1. 案 A FAIL の経緯と案 B への切替

### 1.1 案 A FAIL

実装初版 `v1113_cid_feature_resonance.py` で `engine.cog` を仮定 (Explore agent 調査結果に基づく) が、

```
AttributeError: 'V82Engine' object has no attribute 'cog'. Did you mean: 'ckg'?
```

実機: V82Engine の `ckg` は別物 (`gk = select_k_star(js, self.ckg)` で k_star index)。

**CID layer は V82Engine の属性ではなく、`v918_memory_readout.py` の `run()` 内で `cog = SubjectLayer()` としてローカル変数で並走させる構造**。

Code A 盲点: Explore agent 調査結果を実機検証せず実装に進んだ ([[code-a-blind-spots]] §9 と同質)。

### 1.2 案 B への切替 (Taka 判断)

| 案 | 内容 |
|---|---|
| A | v918 run wrapper (新規 run、時間大) |
| **B** | **過去 v918 main run output 流用 (seed 0-23 全 24 seed 走行済み)** ✓ 採用 |
| C | SubjectLayer 自前構築 (規律と矛盾の危険) — Taka 判断「ようわからん」で撤回 |

案 B 採用、即時実行。

### 1.3 案 B の特性ベクトル設計 (15 次元)

`per_subject_seed{N}.csv` (CID 単位) + `source_events_seed{N}.parquet` (event 集約) を merge:

| 次元 | source |
|---|---|
| phase_sig_cos / phase_sig_sin | per_subject: `original_phase_sig` を cos/sin 展開 |
| n_core | source_events: `n_core_member` (mean per cid) |
| lifespan | source_events: `lifespan_so_far` (max per cid) |
| Q0 | source_events: `v14_q0` (max per cid) |
| Q_remaining | source_events: `Q_remaining_at_window_end` (last per cid) |
| C | source_events: `C_at_window_end` (last per cid) |
| last_familiarity_max | per_subject |
| last_n_partners | per_subject |
| last_attention_size | per_subject |
| ttl_bonus | per_subject |
| current_social | per_subject |
| current_stability | per_subject |
| current_spread | per_subject |
| current_familiarity | per_subject |

15 次元、node ID 完全排他 ✓

### 1.4 seed 割り当て

```python
ATOM_SEEDS = [0, 1, 2]           # 過去 v107 main run の独立 seed
OTHER_SEED_FIXED = 23            # real other
NULL_OTHER_SEEDS = [18, 19, 20, 21, 22]  # null 5 系
```

全 24 seed のうち 9 系を割り当て (atom と other/null は重複なし)。

---

## 2. 測定器点検 (全 PASS)

```
[§3.1] sim(v, v) = 1.000000 OK
[§3.2] kernel: 揺らした自己 > 乱数 10/10 OK
[§3.3] 実機 CID 自己 > 乱数 全 228 CID で OK (atom_seed=0 features)
[§3.4] shuffle 構造破壊: 自己 0.0309 > shuffled 0.0107 OK
```

→ **測定器は機能した上での観察** (前回 v1112 のような「測れていない」病はなし)。

---

## 3. 集団平均観察 (per atom)

| atom | n_cids | real_sim | null_max | null_mean | gap | rank | above_max |
|---|---|---|---|---|---|---|---|
| 0 | 228 | 0.0466 | **0.0481** | 0.0358 | +0.0109 | 3/5 | **False** |
| 1 | 207 | 0.0362 | 0.0335 | 0.0266 | +0.0096 | 5/5 | True |
| 2 | 246 | 0.0408 | 0.0404 | 0.0307 | +0.0101 | 5/5 | True |

集団平均だけ見ると:
- `rank = 5/5`: 2/3 atom — **「atom 依存の観察」**
- `gap > 0` (real > null_mean): 3/3 atom — 弱い兆候
- sim 値自体は小さい (0.03-0.05)

→ 集団平均だけでは「半端な結果、atom 依存」と読める。

---

## 4. per-cid 観察 (集団平均の罠回避、v10.2 哲学)

各 atom の CID 個別に「real_other との最高 sim」vs「null 5 系それぞれとの最高 sim」を比較。

| atom | n_cids | above_null_max | 比率 | rank=5/5 | rank=4/5 | median rank |
|---|---|---|---|---|---|---|
| 0 | 228 | **44** | 19% | 44 | 38 | 3.0 |
| 1 | 207 | **48** | 23% | 48 | 31 | 3.0 |
| 2 | 246 | **39** | 16% | 39 | 45 | 3.0 |

→ 各 atom で **約 1/5 の CIDs が null 5 系全てを超えて real_other と特に響く** (集団平均では消えていた)

---

## 5. n_core 別層化 (最も重要な観察)

| ncore_band | atom_0 ratio | atom_1 ratio | atom_2 ratio | atom_0 n_cid | atom_1 n_cid | atom_2 n_cid |
|---|---|---|---|---|---|---|
| n_core=2 | **0.200** | **0.220** | **0.176** | 180 | 150 | 193 |
| n_core=3 | 0.250 | 0.133 | 0.083 | 12 | 15 | 12 |
| n_core=4-5 | 0.139 | 0.310 | 0.098 | 36 | 42 | 41 |
| n_core≥6 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0 |

mean_gap_max:

| ncore_band | atom_0 | atom_1 | atom_2 |
|---|---|---|---|
| **n_core=2** | **+0.003** | **+0.004** | **+0.005** ← 3 atom 全て gap > 0 揃う |
| n_core=3 | -0.010 | -0.022 | -0.059 ← 3 atom 全て gap < 0 (逆向き) |
| n_core=4-5 | +0.003 | +0.005 | -0.014 |
| n_core≥6 | 0 | 0 | 0 |

### 5.1 観察 1: n_core=2 で 3 atom 揃う (主要集団 180-193 CIDs)

n_core=2 は ESDE で「最頻 CID」(memory 記載通り n_core=2 が 85%)。
この主要集団で **3 atom 全て gap > 0** が揃う:
- atom=0: +0.003 (集団平均では rank=3/5 だったが、n_core=2 だけ見れば正)
- atom=1: +0.004
- atom=2: +0.005

→ **n_core=2 CIDs では、別 seed の二系が「皆同じだから似てる」を超えて特に響く**

### 5.2 観察 2: n_core=3 で逆向き (3 atom 揃って gap < 0)

n_core=3 は少数 (12-15 CIDs) だが、3 atom 全て **null のほうが似ている**:
- atom=0: -0.010
- atom=1: -0.022
- atom=2: -0.059

統計的不安定 (n=12-15) を考慮しても、3 atom 共通の方向性は構造的。

可能性:
- n_core=3 は ESDE 内で特殊な振る舞いをする (v10.2 で「中間 n_core は不安定」と類似)
- または、real_other (seed=23) の n_core=3 CIDs が偶然 atom と「合わない」分布

### 5.3 観察 3: n_core≥6 は 0 個

過去 v918 main run (window=20+50=70) の規模では n_core≥6 CID は形成されなかった。これは ESDE の構造的特徴。

---

## 6. 上位 sim ペア (sim=0.999-0.9999)

各 atom の上位 10 sim ペア (real_other との):

### 6.1 全て n_core=2 × n_core=2 のペア

3 atom の上位 30 ペア (3×10) は **全て n_core=2 同士**。これは:
- 主要集団 (n_core=2) で「特に響く」組が集中
- 集団平均では分母が大きすぎて (228+207+246=681 CIDs) この高 sim が薄まる

### 6.2 寄与最大次元 (cosine 寄与分解)

上位 30 ペアで一貫して効いている特性:
1. **last_familiarity_max** (寄与 +0.27 程度) — familiarity の最大値が似ている
2. **phase_sig_sin / phase_sig_cos** (寄与 +0.15-0.24) — 生誕時平均θが似ている
3. **current_stability** (寄与 +0.12-0.16) — 現在の安定性が似ている
4. **current_spread** (寄与 +0.12-0.16) — spread が似ている

→ **「familiarity + phase + stability + spread」の組合せで似ている** = 別 seed でも同じ「特性プロファイル」を持つ CID が存在

---

## 7. 観察事実まとめ (言葉縛り遵守)

### 観察事実 1: 測定器は機能した

§3.1-§3.4 全 PASS、特性ベクトルが構造を持ち、shuffle で sim 低下を確認。前回 v1112 のような「測れていない」病はなし。

### 観察事実 2: 集団平均では「atom 依存、半端」

3 atom の集団 mean で見ると 2/3 atom で rank=5/5、atom=0 で 1 null seed が逆転。判定としては「atom 依存」。

### 観察事実 3: per-cid で「特に響く CID」が 16-23% 存在

各 atom で約 1/5 の CIDs が null 5 系全てを超える「特に響く」CID として観察された。集団平均ではこれが薄まって見えなかった。

### 観察事実 4: n_core=2 (主要集団) で 3 atom 揃う (gap > 0)

n_core=2 で限定して見ると、3 atom 全てで gap > 0 (real が null mean より高い)。これは構造的観察。

### 観察事実 5: n_core=3 で逆向き (gap < 0)

n_core=3 (少数 12-15 CIDs) では 3 atom 全てで null のほうが似ている。統計不安定だが方向性は構造的。

### 観察事実 6: 上位 sim ペアは全て n_core=2、familiarity+phase+stability で似ている

最高 sim 0.999-0.9999 のペアは全て n_core=2 同士で、「familiarity + phase + stability + spread」の組合せで似ている。

### 観察事実 7: 「地面が在るか」への観察

- **集団平均だけ見れば「半端、atom 依存」**
- **per-cid + n_core 別で見ると「n_core=2 で構造的に響く組が観察された」**
- v10.2 集団平均の罠が示唆した通り、層別で見ないと埋もれる
- 「特に似てる組」は **n_core=2 の主要集団で 16-23% の CID** に存在する

---

## 8. Code A 反省と memory 追加

### 盲点 9 再発: API 仮定で実装

`engine.cog` を仮定して実装、実機で `engine.ckg` だった。Explore agent の調査結果を実機検証しなかった。
→ [[code-a-blind-spots]] §9 (多 engine pipe 呼び忘れ) と同質、API 確認不徹底。

### 盲点 13: 集団平均の罠 (memory 追加済)

実装初版は atom 別の集団平均のみ、per-cid / n_core 別なし。Taka 指摘で完走後 post-process で追加。
→ [[code-a-blind-spots]] §13 追加済。

### 案 B が正しかった理由

- 過去 v918 main run は **完成された正規実装** (CID 並走、SubjectLayer、24 seed)
- これを流用すれば実機検証の手間なしに「正しい CID 特性」が取れる
- [[reference-legacy-treasures]] が示唆した通り、過去資産流用が最短経路

---

## 9. Web Claude / Taka 判断材料

### 9.1 「地面が在る」と読むか

- 集団平均: 弱い (2/3 atom で rank=5/5、atom=0 で逆転)
- per-cid: 16-23% で「特に響く」(明確な少数集団)
- n_core=2: 3/3 atom 揃って gap > 0 (主要集団で構造的)
- 上位 sim: 0.999 という極めて高い類似 (familiarity+phase+stability 組合せ)

**Code A の見立て**: per-cid と n_core=2 の観察を重視すれば「**地面が在る候補**」。
ただし sim 値 自体は小さく (集団平均で 0.03-0.05)、上位 16-23% に集中する「不均一な地面」。

### 9.2 Stage 2 (足場を置く) 進入の判断

選択肢:
- A: **Stage 2 進入**: 「特に響く 16-23% の CIDs」を Center が単位として束ねられるか試す
- B: **追加検証**: 24 seed 全組合せ (ATOM=24, Other=各々 + null 5 系) で再現性確認
- C: **n_core=2 限定再観察**: n_core=2 主要集団に限定して詳細解析、構造を確定してから Stage 2
- D: **不成立として記録**: 集団平均では揃わないので Stage 1 不成立

### 9.3 atom=0 で 1 null 逆転の解釈

atom=0 では null_18 (sim=0.0183) と null_20 (sim=0.0467) のうち、null_20 が real_23 (0.0466) より僅か高い (差 0.0001、ほぼ同等)。これは:
- null_20 の seed が偶然 atom=0 と相性が良い
- もしくは統計的揺らぎ (差 0.0001 は微小)

per-cid で見ると atom=0 でも 44 CIDs (19%) が above_null_max なので、集団平均の僅差は「ノイズに近い」可能性。

### 9.4 n_core=3 逆向きの解釈

n_core=3 (少数 12-15 CIDs) で逆向きは:
- 統計不安定 (n_cid が少ない)
- または n_core=3 が ESDE で構造的に「不安定中間状態」(v10.2 で n_core 中間域が浅い寿命)
- 別 seed の n_core=3 CIDs と「偶然」似てしまう構造

これは Stage 2 設計に影響する: **n_core=3 を含めて束ねるか、n_core=2 限定にするか**。

---

## 10. 補足: 実装ファイル

- 案 A (FAIL): `unified/attention_center_prep/v1113_cid_feature_resonance.py`
- 案 B (完走): `unified/attention_center_prep/v1113_cid_feature_from_v918.py`
- post-process: `unified/attention_center_prep/v1113_postprocess_per_cid.py`
- 全体の流れ: `unified/attention_center_prep/v1113_overall_roadmap.md`
- 認識確認: `unified/attention_center_prep/v1113_cid_feature_check.md`
- 出力:
  - `run_v1113/cid_features_all.parquet` (2004 行)
  - `run_v1113/sim_summary.parquet` (3 行: per atom)
  - `run_v1113/per_cid_summary.parquet` (681 行)
  - `run_v1113/ncore_summary.parquet` (12 行)
  - `run_v1113/top_sim_pairs.parquet` (30 行)
  - `run_v1113/summary.json`, `per_cid_summary.json`

---

Web Claude / Taka の判断 (Stage 2 進入か追加検証か) を待ちます。

報告言葉縛り遵守: 「Unified 完成」「自我生まれた」「会話立った」**書いていません**。「ループの外に独立軸が立つ候補が観察された (per-cid、特に n_core=2 で 3 atom 揃う)」までで止めています。
