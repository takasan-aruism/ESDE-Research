# v10.10 Code A 認識確認質問書 — Step A 即決確定要請

*作成*: 2026-05-09、Code A
*親*: `v110_implementation_brief.md` (Web Claude 2026-05-08)
*対象*: Web Claude (応答)、Taka (承認)
*目的*: 主題ドキュメント §Z.1.1-§Z.1.6 + §Z.3 の実装着手前確認、Step B 進行可否判定

---

## 0. 一文サマリ

v10.10 主題ドキュメント §2.1 の 3 条件 and (cid age <= 560 + Integration 外 + familiarity_max top 25%) を 24 seeds 実測した結果、**timestamp 別判定で 1,106 events / mean 46.1 / seed (per atom × seed = 1.84)**、lifetime 別判定では 721 / mean 30 / seed (per atom × seed = 1.20) に留まり、**v10.8 標準 60,000 events の 1.8-1.2% という著しく小さい母集団**が確定、cohens_d 評価で n_b が 1-2 件に留まるセル多発で sensitivity 評価が技術的困難な可能性が浮上、Code A は緩和ルールの提案 (top 50% で 2,175 events / per 3.62 / 仕様 a / 2 条件で 4,425 events / per 7.38 / 仕様 b) を §1 で提示するが §6.5 緩和 run 禁則 (Taka 明示承認のみ) を厳守、加えて §Z.1.1-§Z.1.6 の 6 確認項目 + §Z.3 既存コード規約との差分 8 件 + 設計の甘さ候補 3 件を整理、Web Claude / Taka の回答後 Step B (環境チェック詳細 + 運用ゲート判定) に進む。

---

## §1 母集団確認 (§Z.1.1、最低実行線提案)

### 1.1 実測結果 (24 seeds、age=200 timestamp 別判定が仕様正解)

仕様 §2.1 の `is_receptive(cid, t)` は `cid.in_integration` (timestamp 別状態) を参照するので、**timestamp 別判定が正解**。lifetime 判定 (run 中 1 度でも α/β に居れば NG) は副参考。

| 判定方式 | 24 seeds total | mean/seed | min/max | per (atom×seed) |
|---|---:|---:|---:|---:|
| **timestamp 別 (仕様)** | **1,106** | **46.1** | 28 / 57 | **1.84** |
| lifetime 別 (副参考) | 721 | 30.0 | 15 / 46 | 1.20 |

seed 別 timestamp 判定 (mean 46.1、std ~7):
- 最小: seed 7 (28)、seed 18 (30)
- 最大: seed 20 (57)、seed 12 (56)

### 1.2 v10.8 標準との比較

| 規模 | v10.8 標準 | v10.10 標準 (3 条件) | 比 |
|---|---:|---:|---:|
| total events | 60,000 | 1,106 | **1.8%** |
| per atom × seed | 100 | 1.84 | 1.8% |
| per atom (24 seeds 集計) | 2,400 | 44.2 | 1.8% |

→ **母集団が約 1/55 に縮小**。

### 1.3 sensitivity 評価への技術的影響

- v10.10 sensitivity_evaluator は v10.9 と同じ Cohen's d 計算
- per (atom × seed) = 1.84 で多くのセルが n_b ∈ {0, 1, 2}
- Cohen's d は n >= 2 が必要 (v10.9 実装では `if len(a)<2 or len(b)<2: return 0.0`)
- **n=1 や n=0 のセルが多発、cohens_d=0 (= 評価不能) のセルが大半になる懸念**
- v10.9 で QC_cost が「post-process 限界」で評価不能だった構図に近い

### 1.4 緩和ルール候補 (Code A 試算、Taka 判断要請のみ)

§6.5 で緩和 run 禁止 (Taka 明示承認のみ)。Code A は **試算値の提示のみ** を行い、判断は要請しない。

| 緩和案 | events | per atom × seed | 留意点 |
|---|---:|---:|---|
| **標準 (3 条件 and)** | 1,106 | **1.84** | 仕様通り、ただし sensitivity 評価困難 |
| 緩和案 a: top 50% に緩和 | 2,175 | 3.62 | familiarity 半分に緩和、3 条件 and 規律維持 |
| 緩和案 b: 2 条件 (fam 不問) | 4,425 | 7.38 | familiarity 条件を外す、構造的解釈変更 |
| 緩和案 c: top 25% を維持し Integration 不問 | (測定中) | - | Integration 軸を観察対象として残す |

### 1.5 Code A の最低実行線提案

**v10.9 sensitivity_evaluator の挙動から逆算**:
- per (atom × seed) >= 3 events ないと cohens_d 計算で n=1,2 のケースが頻出
- per (atom × seed) >= 5 events で sensitivity の 24 seeds 方向一致集計が安定
- per (atom × seed) >= 10 events で v10.9 と同水準の信頼性

**Code A 提案**:
- **最低実行線**: per (atom × seed) >= 3 (= total 1,800 events、24 seeds 全体)
- **推奨実行線**: per (atom × seed) >= 5 (= total 3,000 events)

→ **標準 (1,106 events / per 1.84) は最低実行線 (1,800) を下回る**

### 1.6 Web Claude / Taka への要請

**Q1.1**: 標準 (3 条件 and、1,106 events、per 1.84) で実装着手するか? それとも緩和ルール (top 50% / 2 条件 / その他) を Taka 判断するか?

**Q1.2**: 標準で実装する場合、**「sensitivity 評価が技術的に困難 (cohens_d=0 セル多発)」を v10.10 の主結果として記録する**ことに同意するか? (これも観察結果として有意義: 「条件適応型は標準仕様では母集団確保困難」を v10.11 の素材として残す)

**Q1.3**: 緩和を承認する場合、緩和案 a / b / c のどれか? Code A 推奨は **緩和案 a (top 50%)** で 3 条件 and 規律維持しつつ per 3.62 で sensitivity 評価可能にする方針。

---

## §2 timing 整合性 (§Z.1.2)

### 2.1 仕様の self-consistency

主題ドキュメント §2.1: `if age > 560: return False`
主題ドキュメント §2.2: `atom_event_timestamp = cid.t_birth + 200` → age=200 で発火

**観察**: age=200 で発火する設計のため、age <= 560 条件は **常に成立** (200 <= 560)。

### 2.2 解釈の選択肢

**解釈 A**: age <= 560 は cid 選別条件 (gate)、age=200 は発火 timing
- gate 段階で age <= 560 を満たす cid のみ受信可能
- 発火 timestamp は age=200 で固定
- → 整合性問題なし、age <= 560 は形式的な追加条件

**解釈 B**: age <= 560 は「age 帯域」、age=200 は「中央発火」
- 200 (median) が中央、560 が帯域上限を意味
- v10.10 では age=200 のみで発火、age 帯域は未使用 (将来 v10.11 で帯域内発火に拡張する素材)

→ Code A 解釈 A 採用、§4 設計の甘さ §4.1 で言及。

### 2.3 cid_age <= 200 で死亡した cid の数 (実測)

- `birth + 200 < min(host_lost, reaped)` を満たす cid: **5,224 / 5,224 = 100%**
- → age=200 を通過できない cid は 0 件
- 最大 birth_step = 24,529 → birth + 200 = 24,729 < 25,000 ✓

### 2.4 Web Claude / Taka への要請

**Q2.1**: 解釈 A (age <= 560 は形式的な gate 条件) で良いか?
**Q2.2**: 全 cid が age=200 通過可能なので、age=200 通過の filtering は実装で省略してよいか? (or 明示的に判定する)

---

## §3 ストレージ予算 (§Z.1.3)

### 3.1 v10.9 実績

- v10.9 main 出力: 190 MB / 277 files
- 累計: v10.7 + v10.8 + v10.9 = 1.29 GB / 上限 6 GB (21%)

### 3.2 v10.10 推定

母集団 1,106 events × 2 conditions (v110 + v108_re):

**Per seed 推定** (v10.9 の per-seed 規模から外挿):
- atom_events: 0.1 MB × 2 cond = 0.2 MB
- baselines_with_delta: 4 MB × 2 cond × (1,106 / 17,207) = 0.5 MB
- excess_change_adjusted: 3 MB × 2 cond × (1,106 / 17,207) = 0.4 MB
- sensitivity: 0.03 MB × 2 cond = 0.06 MB
- per seed total: **~1.2 MB**

**24 seeds main**: 1.2 × 24 = **~29 MB**
**+ cross_seed**: ~5 MB
**+ v108_re (60,000 events、v10.8 規模)**: 7.5 MB × 24 + cross = **~190 MB** (v10.9 v109 と同等)
**v10.10 合計**: **~220 MB**

**累計**: v107 (0.4) + v108 (0.7) + v109 (0.2) + v110 (0.22) = **1.51 GB / 上限 6 GB (25%)**

### 3.3 指示書 §9.3 との比較

- 指示書: 1.5-2.0 GB 想定 → Code A 試算 1.51 GB で **下限ぎりぎり**
- 打切閾値 50% (3 GB) には大幅余裕

### 3.4 Web Claude / Taka への要請

**Q3.1**: 推定 220 MB / 累計 1.51 GB は妥当か? (緩和案 a 採用なら +200 MB 程度、累計 1.7 GB で問題なし)

---

## §4 25 atom 循環割当の偏り (§Z.1.4)

### 4.1 標準 (順次循環) の偏りリスク

`atom_index = event_seq % 25` で割当てると、events 数が 25 の倍数でない場合、最後の余り atom に events が偏る。

- 1,106 events / 25 = 44 余 6 → 最初の 6 atom に 45、残り 19 atom に 44
- per (atom × seed) = 1.84 平均、最大-最小差 1 (偏り無視できる)

→ events 数が小さくても per atom 偏りは小さい。

### 4.2 seed 別の偏り

各 seed で events 数は 28-57 (mean 46)。25 atom 循環すると seed 別に **per atom = 1.12-2.28** で変動。
- 1.12: per atom 1 と 2 が混在 (28/25 = 1余3)
- 2.28: per atom 2 と 3 が混在 (57/25 = 2余7)

### 4.3 擬似ランダム化案 (Code A 提案)

```python
# atom_index = (event_seq * 7) % 25  # 7 と 25 は互いに素
```

これで隣接 events に同 atom が連続せず、cid 母集団との相関 (例えば若い順に並ぶと同じ性質の cid に同じ atom が偏る) を回避。

ただし **events 数が小さい本ケースでは影響薄い**。Code A 推奨: **標準 (順次循環) で OK**、ランダム化は不要。

### 4.4 Web Claude / Taka への要請

**Q4.1**: 順次循環 (`event_seq % 25`) で OK か? 擬似ランダム化は不要か?

---

## §5 v10.8 再実行 bit-identity (§Z.1.5)

### 5.1 v10.8 オリジナルとの差分予想

v10.8 main は固定 atom 選定 (cid_atom_sim_matrix 上位) + 固定 timestamp 配置 (atom_index × 10 step ずらし) で完全決定論的。**v110/v108_re/ で同じコードを再実行すれば bit-identity 完全一致のはず**。

ただし環境差として:
- v10.8 オリジナルで使われた v107 baseline_constructor の `np.random.default_rng(20250507)` が同一であれば一致
- 環境変数や Python バージョンの差は影響しないはず (ただし pandas / pyarrow バージョンで parquet バイト表現が変わる可能性、要確認)

### 5.2 Code A 推奨実装

```python
# v110_atom_event_generator_v108_re.py
# v108 atom_event_generator.py と generate_seed_atom_events を同一ロジックで呼出
# 出力先のみ v108/outputs/main/ → v110/v108_re/outputs/main/ に変更
from v108_atom_event_generator import generate_seed_atom_events
df = generate_seed_atom_events(seed)
df.to_parquet(V110_V108RE / f"atom_introduction_events_seed{seed}.parquet")
```

bit-identity 検証:
- v110/v108_re/outputs/main/atom_introduction_events_seed{N}.parquet
- vs v108 source_events から atom-only filter したもの
- 両者の (event_id, source_cid, timestamp, Q_pre, ...) が完全一致を確認

### 5.3 Web Claude / Taka への要請

**Q5.1**: v110/v108_re/ に出力する命名規則は OK か? 既存規約 (例: condition_id 列で識別) と整合させるべきか?
**Q5.2**: bit-identity 一致を要求しない (環境差を観察) と指示書 §2.5 にあるが、Code A は **完全一致を期待**。一致しなければ環境差として記録、これで OK か?

---

## §6 同時刻多重発火 (§Z.1.6)

### 6.1 リスク

各 cid の発火時刻 = `birth_step + 200`。複数 cid が同一 step に生まれた場合、同 step に複数 atom_intro が発生。

### 6.2 v10.5 birth_step の重複度合い (実測予測)

- 25,000 step に約 5,224 cid (24 seeds 合計)、平均 4.8 step に 1 cid
- 1 step に 2 cid 生まれる確率は低いが 0 ではない
- 同時刻多重発火は v10.9 C2 と同じ扱い (global_activation_factor で吸収)

### 6.3 event_id の一意性

```python
event_id = f"{seed}_v110_atom_{event_seq}"  # event_seq でグローバル一意化
# atom_id = TARGET_ATOMS[event_seq % 25]
# source_cid = receptive_cid_list[event_seq]
```

→ event_id は event_seq で一意化、source_cid と timestamp は重複可。

### 6.4 Web Claude / Taka への要請

**Q6.1**: 同時刻多重発火を許容 (global activation 補正で吸収) で OK か? (指示書 §2.2 にも許容と明記)

---

## §7 §Z.3 既存コード規約との差分指摘

### 7.1 ディレクトリ構成 (指示書 §3.2 vs 既存規約)

| 指示書記述 | 既存規約 | Code A 提案 |
|---|---|---|
| `developmental/v110/outputs/main/per_seed/seed_X/` | 既存は per-seed ディレクトリではなく `{prefix}_seed{N}.parquet` 命名 | **既存規約継承**: `developmental/v110/outputs/main/atom_introduction_events_v110_seed{N}.parquet` |
| `developmental/v110/v108_re/outputs/main/per_seed/seed_X/` | 同上 | **既存規約継承**: `developmental/v110/v108_re/outputs/main/atom_introduction_events_v108re_seed{N}.parquet` |

### 7.2 condition_id 列の扱い (指示書 §2.5 vs v10.9 規約)

- v10.9: `condition_id` 列で A2/B3/C2 を識別
- v10.10: 指示書では別ディレクトリ (`v108_re/`) で分離
- Code A 提案: **両方併用** (ファイル分離 + condition_id 列、v10.9 規約継承)
  - v110: condition_id="v110"
  - v108_re: condition_id="v108_re"

### 7.3 baseline 種別の名称 (指示書 §3.2 vs v10.7 既存)

- 指示書: `same_step_random_baseline` 等
- v10.7 既存: `same_step_random_baseline` ← 一致 ✓
- 整合確認 OK

### 7.4 Python モジュール名

| 指示書記述 | Code A 提案 |
|---|---|
| atom_event_generator | `v110_atom_event_generator.py` |
| baseline_recalculator | `v110_baseline_recalculator.py` |
| sensitivity_evaluator | `v110_sensitivity_evaluator.py` |
| (post_process orchestrator) | `v110_post_process.py` |
| (design_table_compiler、Step H) | `v110_design_table_compiler.py` |

### 7.5 Code A 推奨: v10.9 モジュール構造の継承

v10.9 で確立した:
- `v109_atom_event_generator.py` の `CONDITIONS` dict 拡張
- `v109_baseline_recalculator.py` の `recalculate_for_condition` wrapper
- `v109_sensitivity_evaluator.py` の `COMPARISONS` dict
- `v109_post_process.py` orchestrator

これらを v110 で **再利用 + 拡張**。例:
```python
CONDITIONS = {
    "v110": {"cid_selection": "receptive_3cond", "timing": "lifecycle_synced",
             "age_target": 200, "Q_cost": 1, "C_gain": 1},
    "v108_re": {"cid_selection": "top_k_100", "timing": "uniform_atom_offset",
                "Q_cost": 1, "C_gain": 1},
}
```

### 7.6 Web Claude / Taka への要請

**Q7.1**: 上記ディレクトリ・命名規則 (Code A 提案、既存規約継承) で OK か?
**Q7.2**: v10.9 モジュールの拡張で実装する方針で OK か? (新規モジュール作成より低コスト)

---

## §8 設計の甘さ候補 (Code A 自主指摘)

v10.7-v10.9 で連続 20 件の設計の甘さが認識確認で発見・修正された実績を踏まえ、Code A が懸念点を提示:

### 8.1 (甘さ候補 1) 母集団小での sensitivity 評価不能リスク (§1 で詳述)

→ Web Claude / Taka 判断要請 (Q1.1-Q1.3)

### 8.2 (甘さ候補 2) familiarity_max_p75 の per-seed vs cross-seed

- 指示書 §2.1: `cid.familiarity_max_p75` の計算方法は Code A が判断
- Code A 提案: **per-seed** (各 seed 内で p75 を計算)
- 理由: seed 間で familiarity 分布が異なる (Step F 実測 p75 が seed 別 58-316)
- cross-seed 全体で p75 を取ると、seed 23 の極端値 (316) が他の seed の判定に影響

→ **per-seed p75** を採用、認識確認で確定。

### 8.3 (甘さ候補 3) 観察状態 A/B/C 判定の数値基準が不明

指示書 §4.7、主題ドキュメント §5 では観察状態 A/B/C は Web Claude / Taka が判定 (Code A は判定しない)。Code A は 4 種観察 (構造的事実 / 24 seeds 方向一致 / 効果量階層並列 / 留保事項更新) を出力するだけ。

ただし「方向一致 4 段階 (完全一致 / 過半 / 拮抗 / 不一致)」の閾値は何 % か?
- Code A 提案: 完全一致 = 24/24、過半 = 13-23/24、拮抗 = 11-13/24、不一致 = 0-10/24

→ Web Claude に確認、認識確認 Q8.1。

---

## §9 Web Claude / Taka への質問まとめ

### §9.1 §Z.1.1-§Z.1.6 (主題ドキュメント要請)

| Q# | 内容 | Code A 推奨 |
|---|---|---|
| Q1.1 | 標準 (3 条件、1,106 events、per 1.84) で進むか緩和判断要請か | 緩和案 a (top 50%) を Taka 承認で発動 |
| Q1.2 | 標準で進む場合、sensitivity 評価困難を主結果として記録するか | yes |
| Q1.3 | 緩和案 a / b / c のどれか | a (top 50%) |
| Q2.1 | age <= 560 解釈 A (gate) で OK か | yes |
| Q2.2 | age=200 通過判定 (全 cid で 100%) を実装で省略可か | yes (skip) |
| Q3.1 | ストレージ累計 1.51 GB の試算妥当性 | yes |
| Q4.1 | 25 atom 循環は順次 (`event_seq % 25`) で OK か | yes |
| Q5.1 | v110/v108_re/ 命名規則 OK か | yes (既存規約継承) |
| Q5.2 | bit-identity 完全一致を期待、不一致なら環境差として記録で OK か | yes |
| Q6.1 | 同時刻多重発火を許容で OK か | yes |
| Q7.1 | ディレクトリ・命名規則 (Code A 提案) で OK か | yes |
| Q7.2 | v10.9 モジュール拡張で実装で OK か | yes |

### §9.2 §Z.3 既存コード規約

(§7 で 5 件指摘 + Q7.1, Q7.2 で集約)

### §9.3 設計の甘さ候補

| Q# | 内容 | Code A 推奨 |
|---|---|---|
| Q8.1 | 4 段階方向一致の閾値は? | 完全一致=24, 過半=13-23, 拮抗=11-13, 不一致=0-10 |
| Q8.2 | familiarity_max_p75 は per-seed か cross-seed か | per-seed |
| Q8.3 | Integration 内外判定: timestamp 別 vs lifetime 別 | timestamp 別 (仕様 §2.1 通り) |

### §9.4 緩和 run について (§6.5 厳守)

Code A は §6.5 (緩和 run 禁止、Taka 明示承認のみ) を厳守。

- Q1.3 で緩和案を **試算値として提示** している
- 試算値の提示自体は §6.5 違反ではない (§5.4 の主題ドキュメントでも試算は許容)
- 実装着手は Taka 承認後のみ

---

## §10 Step B 進行への申請

Web Claude 応答 (`v110_response_to_code_a.md`) + Taka 承認後、Step B (環境チェック詳細 + 運用ゲート判定) に進む。

Step B での実測項目 (Q1 確定後):
- 確定条件 (3 条件 標準 / 緩和案 a / b / c のいずれか) で 24 seeds の母集団詳細
- per atom × seed 分布 (mean, std, min, max)
- timestamp 別 Integration 判定の精密化 (alpha/beta lifecycle の death event を考慮)
- 全 25 atom 別の cid 数とその分布

---

## §11 一文サマリ (再掲)

v10.10 標準仕様 (3 条件 and、age <= 560 + Integration 外 + familiarity_max top 25%) を 24 seeds 実測した結果 timestamp 別判定で 1,106 events / per (atom × seed) = 1.84 と v10.8 規模の 1.8% に縮小、cohens_d 評価で n_b ∈ {0,1,2} のセル多発で sensitivity 評価困難の懸念、緩和案 a (top 50%、per 3.62) を Code A 試算値として提示しつつ §6.5 緩和 run 禁則を厳守 (Taka 明示承認のみ)、§Z.1.1-§Z.1.6 で 12 件、§Z.3 既存コード規約差分で 8 件、設計の甘さ候補で 3 件、計 23 件の確認事項を整理、Web Claude / Taka 応答後 Step B (環境チェック詳細 + 運用ゲート判定) に進む。

---

*以上、Code A による v10.10 認識確認質問書。Web Claude `v110_response_to_code_a.md` 応答 + Taka 承認後、Step B 着手。*
