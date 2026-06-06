# v1114 Step 2 — 生きた Center に進むための実装ベース提案 (Code A)

date: 2026-06-06
from: Code A (Claude Code, Opus 4.7)
to: Taka / Web Claude (相談役)
status: 実装提案 (着手前、Taka 判断材料)

---

## 0. 全体俯瞰 — Taka 整理「Center が今できていないこと」5 点と本提案の対応

| # | できていないこと (Taka 指摘) | 本提案で解決される段階 |
|---|---|---|
| 1 | 生きていない (post-process で見てるだけ) | **§1 生きた骨格** — V82Engine を実際に走らせ、自前 loop で per-N-step 観察 |
| 2 | 拾った結果を何にも戻していない / 使っていない | **§3 Δstate 自己擦り込み** — alert 時に Center 自身の state に擦り込み (phase 帯対応、node ID 不使用) |
| 3 | 外部 (Atom / 別系) を一切見ていない | **§5 段階分け** — Step 3 で Atom 並走 + 外部注意擦り込み (現段階では Step 2 範囲外) |
| 4 | lifecycle_phase が半分以上 unknown | **§4** — 生きた run なら cog.born_at[cid] を直接参照、source_events の attribution エラー無関係 |
| 5 | 周辺の大きさ (familiarity 相手の n_core) が取れない | **§4** — 生きた run なら cog.familiarity[cid].keys() で相手 cid 集合 → 各相手 cid の n_core を取得 |

→ Step 2 (生きた Center 単体 + 自己擦り込み) で **4 つ** が解決、Step 3 で **外部 (Atom 並走)** が解決。

---

## 1. 生きた Center の最小骨格

### 1.1 構造 (過去開発物の流用、新規発明なし)

```python
# v918 main run の正規実装を組み合わせる
from esde_v82_engine import V82Engine, V82EncapsulationParams, V82_N
from virtual_layer_v9 import VirtualLayer as VirtualLayerV9
# SubjectLayer は v918_memory_readout.py 内 class、import 可能

def build_center(seed=0):
    encap = V82EncapsulationParams(stress_enabled=True, virtual_enabled=True)
    engine = V82Engine(seed=seed, N=V82_N, encap_params=encap)
    engine.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8, 1.2))
    engine.virtual.torque_order = "age"
    engine.virtual.deviation_enabled = True
    engine.virtual.semantic_gravity_enabled = True
    engine.run_injection()  # Genesis 起動 (300 step injection)
    # SubjectLayer 構築 + cog 並走パイプ
    cog = SubjectLayer()
    # cog と engine の連携 (v918 run() のパターン)
    return engine, cog
```

### 1.2 自前 window loop (per-N-step 観察)

```python
WINDOW_STEPS = 500
WINDOWS = 30
N_PER_CHUNK = 10  # per-10step 観察粒度

engine, cog = build_center(seed=0)
for w in range(WINDOWS):
    for chunk in range(WINDOW_STEPS // N_PER_CHUNK):  # = 50 chunks/window
        engine.step_window(steps=N_PER_CHUNK)  # 10 step 進める
        # cog ライフサイクル更新 (v918 main loop と同等)
        update_cog_lifecycle(engine, cog, current_window=w, current_step=...)
        # per-10step メトリック取得 (Center の動学を観察)
        metrics = collect_metrics(engine, cog)
        # 注意発火判定 (EWMA + z-score、内部)
        alerts = check_alerts(metrics, running_stats)
        for alert in alerts:
            record = build_record(order, alert, engine, cog, current_step)
            records.append(record)
```

### 1.3 実装上の難所と対応

| 難所 | 対応 |
|---|---|
| v918_memory_readout.py の run() が 3153 行で密結合 | run() 全体を呼ぶのでなく、SubjectLayer / cog 更新ロジックの **必要部分だけ** を抜き出して自前 loop に組み込む (依存最小化) |
| cog ライフサイクル (label birth / death / pickup / reap) の更新タイミング | v918 run() の main loop を参考に、per-window で `cog.update_lifecycle(...)` 相当を呼ぶ |
| step_window が per-window 単位 (500 step 一気に進める) | `engine.step_window(steps=N_PER_CHUNK)` で 10 step ずつ進める — engine_accel 経由なので per-step physics は機能、observation だけ自前で挿入 |
| V_unified などのメトリック計算 | v918 unity_metrics.py / theta_distance.py を直接 import、per-10step で計算 |

---

## 2. リアルタイム per-N-step 観察 — Step 1b との対応

### 2.1 Step 1b → Step 2 の置き換え

| Step 1b (post-process) | Step 2 (生きた run) |
|---|---|
| 既存 source_events.parquet を per-10step に bin | engine 動学中に per-10step で計算 |
| event 種別 (pulse / α_formation / β_formation / c_conversion / ingestion) を集計 | engine + cog から **直接** event を取り出す (発火タイミングがリアルタイム) |
| cid_birth / cid_death を per_subject から構築 | cog.born_at[cid] / cog.host_lost_at[cid] が更新された瞬間に直接捕捉 |
| EWMA + z-score | 同じロジック (実装は変えない) |

### 2.2 metric の取り出し方 (実装上)

```python
# per-10step 観察 (engine 走行中)
def collect_metrics_per_chunk(engine, cog):
    # 1. V_unified (v918_unity_metrics)
    v_unified = compute_v_unified(engine.state.theta, engine.state.alive_n)
    # 2. source_event 5 種の発生数 (直近 chunk で)
    events_this_chunk = collect_recent_events(engine, cog, chunk_window=N_PER_CHUNK)
    # 3. CID 誕生数 / 死亡数 (cog.born_at / host_lost_at の delta)
    n_births = count_new_births(cog, since_last_chunk)
    n_deaths = count_new_deaths(cog, since_last_chunk)
    return {...}
```

### 2.3 7 種引き金は Step 1b と同じ (独立監視、合成しない)

`pulse` / `ingestion` / `alpha_formation` / `beta_formation` / `c_conversion` / `cid_birth` / `cid_death`

各々に独立 EWMA + z-score。レコードに残るのは記号のみ (Taka 念押し (a) 厳格遵守)。

---

## 3. 拾った結果を「使う」 — Δstate 自己擦り込み (本 Step 2 の核心)

### 3.1 設計 (前回提案 案 B の継承)

alert 発火時、Center 自身の Δstate (= 直前 N step の state 差分) を、Center 自身の state に **phase 帯対応**で擦り込む。

```python
def record_state_snapshot(engine, snapshot_buffer):
    """毎 chunk で state スナップショットを記録"""
    snapshot = {
        'theta': engine.state.theta.copy(),
        'E': engine.state.E.copy() if hasattr(engine.state, 'E') else None,
    }
    snapshot_buffer.append(snapshot)
    if len(snapshot_buffer) > MAX_BUFFER:
        snapshot_buffer.pop(0)

def apply_self_writeback(engine, snapshot_buffer, alert, gain=0.05):
    """alert 時に Δstate を phase 帯対応で擦り込み"""
    if len(snapshot_buffer) < 2:
        return
    state_now = snapshot_buffer[-1]
    state_prev = snapshot_buffer[-2]  # 1 chunk 前 (= 10 step 前)
    delta_theta = circular_diff(state_now['theta'], state_prev['theta'])
    # phase 帯対応で擦り込み: 各 node の theta_now に近い phase 帯の node 集合に
    # delta_theta * gain を加算 (node ID 不使用、phase 距離のみ)
    for node_idx in range(len(engine.state.theta)):
        # この node の theta_now に近い phase を持つ全 node に Δ を擦り込む
        # gain は alert 強度に比例 (z スコアでなく、alert 発生数等の記号的指標で量を決める)
        engine.state.theta[node_idx] += gain * weighted_delta(...)
```

### 3.2 phase 帯対応の正確性 (v1110-v1113 の轍を踏まない)

- ❌ **node ID コピー** (v1111c/d 番号コピー欠陥):
  - 別系の node ID をそのまま使う → 系を跨ぐと無意味
- ❌ **node ID 経由の擦り込み**:
  - 同じ node ID の state を上書き → ID 依存
- ✓ **本提案の phase 帯対応**:
  - theta 値 (連続) で対応、node ID は使わない
  - 「擦り込む対象 = 似た phase を持つ node 集合」(構造的対応)
  - 過去成功事例: v43 semantic_pressure (全 node に θ ランダム摂動 + 近傍 latent_boost) と同系統 = 「外部影響を構造的に擦り込む」確立パターン

### 3.3 擦り込み量 (gain) の決め方

- 初期: 小さい値 (例: gain = 0.05) で「動学を壊さない」最小擦り込み
- alert 強度に比例: 強い alert (= z 大) で gain 大
- ただし z 値はレコードに残さない (Taka 念押し (a))、gain は内部のみ
- 上限: gain ≤ 0.5 程度 (engine の動学が破壊されない範囲、要実機検証)

### 3.4 出口 (Step 2 の観察、差は測らない)

- 擦り込み **あり** / **なし** の Center 動学を比較し、**Center の state に変化が起きるか** を観察
- ただし「変化の大きさ」を有意差で測らない (Taka 念押し (b))
- 「擦り込みなしより動学が広がる」「擦り込みでパターンが現れる」程度の **分布の形** で記録
- crown 禁止: 「自我」「会話」と書かない、観察事実のみ

---

## 4. lifecycle_phase / 周辺の大きさ の自動解消 (Step 1b 残課題の生きた run での扱い)

### 4.1 lifecycle_phase

| Step 1b (post-process) | Step 2 (生きた run) |
|---|---|
| source_events の attribution エラーで `age < 0` 多数 → 221/383 が "unknown" | cog.born_at[cid] が「真の誕生 step」を持つ (v918 birth() で 1 回設定、不変) |
| per_subject 経由で +19 window オフセット問題 | cog.born_at をリアルタイムに参照 = オフセット不要 |
| 修正後も attribution エラー残存 | 生きた run では attribution エラーが構造的に発生しない |

→ Step 2 で **lifecycle_phase の "unknown" 率が大幅減** (= 死亡確定 CID のみが "unknown") する見込み。

### 4.2 周辺の大きさ (familiarity 相手の n_core list)

| Step 1b | Step 2 (生きた run) |
|---|---|
| v918 output に `cog.familiarity[cid].keys()` の dump 経路なし → Step 1b で落とす | engine 走行中に `cog.familiarity[cid]` (dict) を直接読める |

実装:
```python
def get_neighborhood_sizes(cog, cid):
    """familiarity 相手 cid の n_core list を取得"""
    fam_dict = cog.familiarity.get(cid, {})
    partner_cids = list(fam_dict.keys())  # 相手 cid 集合
    sizes = []
    for partner_cid in partner_cids:
        partner_buf = cog.v915_buffers.get(partner_cid)
        if partner_buf is not None:
            sizes.append(partner_buf.n_core)
    return sizes  # 例: [2, 2, 5] = hub の周辺に bulk が 2 つと hub が 1 つ
```

→ Step 2 のレコードに `neighborhood.familiarity_sizes: [2, 2, 5]` が入る (Web Claude 設計の元案を完全再現)。

---

## 5. 外部 (Atom / 別系) — 段階分け (Step 3 以降、Step 2 範囲外)

| Step | 内容 |
|---|---|
| Step 2 | Center **単体**、内部注意 + 自己擦り込み |
| Step 3 | Center + **Atom 並走** (別 V82Engine instance、別 seed)、Atom Δstate を Center に phase 帯対応で擦り込み |
| Step 4+ | 入力 → Center → 応答 (会話の芽) |

Step 2 完了後に Step 3 設計に進む。本提案では Step 2 範囲のみ。

---

## 6. 規律 + 過去成功事例との照合 (実装ファイル冒頭の観察対象注釈ブロック)

実装ファイル (`unified/v1114/step2_self_writeback.py`) の冒頭に必須:

```
### 観察対象の本質
- 同じ系内 (Center ESDE 単体、Atom なし) ← Step 3 の Atom 並走でも「Center 自身の動学変化」が観察対象
- 過去成功事例の照合:
  - v9.18 V_unified / theta_distance (動的平衡指標)
  - v10.7 source_event 5 種 (引き金分類)
  - v9.11 SubjectLayer (familiarity、CID lifecycle)
  - v43 semantic_pressure (外部影響を全 node に擦り込みパターン、本提案 §3 が踏襲)
- 過去失敗パターン回避:
  - v1110-v1113 = 異なる系の対応関係発想で 4 連続失敗
  - 本実装は Center 単体、cid id は認知 ID (node ID でない)
  - 擦り込みは phase 帯対応 (node ID コピーでない、v1111c/d の轍を踏まない)

### 残さないもの (Step 1b と同じ規律)
- node ID / 座標 (phase_sig / θ value そのもの) / 不透明 float ベクトル / 判定数値 (z) / 差・有意差
- 近似擦り替え (Taka 規律「すり替えない」)

### 残すもの (Step 1b + 解消された 2 軸)
- cid (認知 ID)
- trigger (記号 7 種)
- point: n_core / lifespan / lifecycle_phase / formation_relation / pulse_reactivity / C / Q_remaining
- neighborhood: familiarity_n + **familiarity_sizes** (= 周辺の大きさ list、生きた run で取得可能に)
- (Step 2 のみ追加) writeback: 擦り込み が起きたか (記号 yes/no)、擦り込み回数 (実数)
```

---

## 7. 実装の難所と最初のマイルストーン

### 7.1 難所 (現実的なリスク)

| 難所 | リスク | 対応案 |
|---|---|---|
| v918 run() の主要 logic を抜き出す | cog 更新タイミングの微妙な順序が動学に影響、v918 と異なる動学になる可能性 | v918 main run と同じ seed=0 で **bit-identity 検証** (label birth 順 / cog 状態を比較)、3 桁 step 一致するまで debug |
| step_window(steps=10) の per-step physics が正常動作するか | engine_accel が per-step 物理を持つ前提だが、per-window 用最適化が干渉する可能性 | smoke (1 window = 50 chunks) で各 chunk の state snapshot を取り、step_window(500) 一気と動学が一致するか検証 |
| 自己擦り込みで動学が暴走する | gain が大きいと state が発散 (theta が範囲外、energy が枯渇) | gain を 0.0 (擦り込みなし) で smoke、徐々に上げる (0.01, 0.05, 0.1)。発散したら即停止 |
| lifecycle_phase の "unknown" 率が逆に増える可能性 | 生きた run でも CID が tracking 終了時点で生存中なら "unknown" (これは正しい) | Step 1b と比較して "unknown" 率が下がれば成功 |

### 7.2 最初のマイルストーン (smoke 段階)

| マイルストーン | 内容 | 出口 |
|---|---|---|
| M1: 生きた骨格動く | engine + 自前 loop で 30 windows × 500 step 完走、cog 状態が更新される | step_window で alive_n / alive_l が変動する |
| M2: Step 1b と同じ percept が出る (擦り込みなし) | gain=0.0 で 7 種引き金独立監視、レコード生成 | Step 1b と類似の分布 (rank=1 一致でなく傾向一致) |
| M3: familiarity_sizes が入る | レコード neighborhood に list が入る | 全 record で list 取得可、unknown 率 < Step 1b |
| M4: 自己擦り込み開始 (gain=0.05) | alert 時に Δstate 擦り込み | engine 発散せず、record に writeback フィールド入り |
| M5: 擦り込みあり/なしの比較観察 | 擦り込みあり/なしを別 run、レコード分布の **形** を比較 (差は測らない) | 擦り込みで動学に変化が起きる (or 起きない) を観察事実として記録 |

各 M で smoke 結果を Taka に報告、判断後に次に進む。

---

## 8. Taka 判断材料

### 8.1 GO/NO-GO 判断ポイント

| 判断 | 内容 |
|---|---|
| **§1 生きた骨格** | v918 主要 logic 抜き出しで進めて良いか / v918 run() 直接呼び方が良いか |
| **§3 擦り込みの gain 範囲** | 0.0 / 0.01 / 0.05 / 0.1 の探索範囲で良いか / 別の単位 (V_unified を保つ範囲) で決めるか |
| **§3.4 擦り込みあり/なしの比較** | これは「差を測る」に該当するか / 「分布の形が違う」を「差なし」と読む解釈で良いか |
| **§5 Step 3 への進み方** | Step 2 完了後に Step 3 設計 (Atom 並走) に進む順序で良いか |

### 8.2 実装規模感

| マイルストーン | 推定コード行数 | 実装時間 |
|---|---|---|
| M1-M2 (骨格 + Step 1b 再現) | 400-500 行 | 半日-1 日 |
| M3 (familiarity_sizes 解消) | +50 行 | 数時間 |
| M4-M5 (擦り込み実装 + 比較観察) | +200 行 | 半日 |

合計 ~700 行、~2 日の見積もり (v1114 Step 1b が ~280 行参考)。

### 8.3 規律の継続

- 観察対象注釈ブロック (.py 冒頭)
- 実機 API 確認 (擦り込み前に cog.familiarity / cog.born_at の参照方法を grep + smoke 確認)
- 判定と記録の分離 (z はレコードに残さない)
- 取れないなら落とす・すり替えない
- 報告は「観察事実」+「分布の形」、差を測らない
- crown 禁止

### 8.4 Web Claude の関与

- 設計 view (実装着手前): Taka 判断
- コード view (実装後、本実行前): 前回 Step 1b で再投入された手順を踏襲
- ただし Web Claude OK は「実装ミスチェック」に限定、観察対象の妥当性は Code A が責任 (Code A 循環構造の認識 #423)

---

## 9. 一文サマリ

v1114 Step 2 (生きた Center) 実装提案 (2026-06-06 Code A → Taka / Web Claude、Step 1b 完了確認後の次フェーズ提案、Taka 整理「Center が今できていないこと」5 点 = 生きていない / 結果を使っていない / 外部見ていない / lifecycle_phase 半分 unknown / 周辺の大きさ取れない、への対応) — 提案核心 (§1 生きた骨格 = V82Engine + 自前 loop + cog 並走 + v918 主要 logic 抜き出し、§2 リアルタイム per-N-step 観察 = Step 1b と同じ 7 種引き金独立監視ロジックを生きた run に置換、§3 拾った結果を使う = alert 時に Δstate を Center 自身に phase 帯対応で擦り込み node ID 不使用 v43 semantic_pressure パターン踏襲 v1110-v1113 番号コピーの轍踏まない、§4 lifecycle_phase 解消 = cog.born_at[cid] 直接参照で +19 window オフセット問題消失 attribution エラー無関係 + 周辺の大きさ解消 = cog.familiarity[cid].keys() 直接読み相手 n_core list 取得可、§5 外部 = Atom 並走は Step 3 で本提案範囲外)、実装規律継続 (観察対象注釈ブロック / 実機 API 確認 / 判定と記録分離 / 取れないなら落とす / 記号 + 構造 / 差測らない / crown 禁止)、最初のマイルストーン M1-M5 (M1 骨格動く / M2 擦り込みなしで Step 1b 再現 / M3 familiarity_sizes 入る / M4 擦り込み開始 gain=0.05 / M5 擦り込みあり/なしの分布の形比較)、実装規模 ~700 行 ~2 日見積もり、Taka 判断材料 (骨格抜き出し方 / gain 範囲 / 擦り込み比較の差を測らない解釈 / Step 3 順序)、Web Claude 関与 (設計 view + コード view、観察対象妥当性は Code A 責任)、書込み unified/v1114/ 配下のみ。

---

*以上、Step 2 (生きた Center) 実装提案。Taka 整理 5 点のうち 4 点が Step 2 で解決、外部 (Atom) は Step 3 で。生きた骨格 + Δstate 自己擦り込み + familiarity_sizes / lifecycle_phase 解消が Step 2 範囲。実装規律は Step 1b 継続、新規発明なし、過去成功事例の組み合わせ。Taka 判断 + Web Claude 設計 view 後に実装着手。*
