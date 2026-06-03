# v1112 Stage 1 — Code A 確認 5 点回答 (node ID 排他最優先)

**Date**: 2026-06-03
**Author**: Code A
**Status**: 確認回答 + 実装直前
**親**: Web Claude v1112 Stage 1 設計 + 2 AI 監査
**規律**: 機能で回答 / node ID 完全排他 / factor なし対照比較 / [[feedback-index-first]] 遵守

---

## 0. 全体結論

5 点すべて既存機構の組合せで実装可能、新規発明ほぼゼロ。**phase 空間 (64 bin) のみで共鳴検出、node ID は一切使わない**。第三 ESDE は **state なし軽量観察体** (独自 class、VirtualLayer の cull/cluster 機構は流用)。

---

## 1. 確認 1: node ID 排他 (最優先) ✓ 達成可能

### 1.1 共鳴検出の入出力

**入力 (両系から読むもの、phase 空間のみ)**:

| 取得元 | 形式 | 理由 |
|---|---|---|
| `atom.virtual.occupancy` | float[64] = 各 phase bin の label 占有 | bin = phase 空間 (0..2π を 64 等分)、両系で意味同じ |
| `other.virtual.occupancy` | float[64] | 同上 |

→ **両系で「同じ bin index = 同じ phase 帯」** という意味共有のみ。node ID も label ID も渡さない。

### 1.2 共鳴検出ロジック (phase 空間)

```python
# 両系で「同じ bin が同時に立っているか」を見る
def observe_cooccurrence(atom, other):
    occ_a = np.array(atom.virtual.occupancy)  # [64]
    occ_o = np.array(other.virtual.occupancy)  # [64]
    # 各系の閾値は state 由来 (mean occupancy)
    th_a = float(occ_a.mean())
    th_o = float(occ_o.mean())
    active_a = np.where(occ_a > th_a)[0]  # 立っている bin index
    active_o = np.where(occ_o > th_o)[0]
    # 両系で立っている bin ペア (= 同期候補)
    return [(a, b) for a in active_a for b in active_o]
```

- 渡るのは **bin index のみ** (0-63 の整数)
- 各系の node ID / label ID は worker 内で完全に閉じる、第三 ESDE には渡らない
- → **node ID 完全排他** ✓

### 1.3 v1111 の罠との違い

v1111 系列の番号コピー欠陥は「Atom の node ID を Other に inject」。v1112 では「両系の bin index (= phase 帯) の同時立ちを検出」だけで、node ID は系内で閉じる。**赤信号なし**。

---

## 2. 確認 2: 第三 ESDE 観察体 (state なし、書き戻さない)

### 2.1 実装

```python
class ResonanceObserver:
    """第三 ESDE = phase 空間で共鳴を観察、両系を 1 bit も書き換えない"""
    def __init__(self, n_bins=64):
        self.N_BINS = n_bins
        # 累積カウンタ (bin pair の同時立ち回数)
        self.cooc_count = np.zeros((n_bins, n_bins), dtype=np.int64)
        # 履歴 (確率累積用、直近 K step の同時立ち set)
        self.history = []
        # 共鳴 CID = 累積が床を超えた bin pair の集合
        self.rcid_pairs = set()
    
    def observe(self, occ_a, occ_o):
        """両系 occupancy を読んで cooccurrence を累積"""
        th_a = float(occ_a.mean())
        th_o = float(occ_o.mean())
        active_a = np.where(occ_a > th_a)[0]
        active_o = np.where(occ_o > th_o)[0]
        cooc = set()
        for a in active_a:
            for b in active_o:
                self.cooc_count[a, b] += 1
                cooc.add((a, b))
        self.history.append(cooc)
        # 履歴は K window 分だけ保持 (過去標準 K=10 程度、ですが state 由来で動的化検討)
        if len(self.history) > 10:
            self.history.pop(0)
    
    def total_cooc(self):
        return int(self.cooc_count.sum())  # N_rcid raw
    
    def E_rcid(self, occ_a_total, occ_o_total):
        """活動量 = cooc 加重 occupancy (現状は cooc_count.sum() で代用)"""
        return self.total_cooc()  # 簡素化
```

### 2.2 規律遵守確認

| 規律 | 確認 |
|---|---|
| state なし | ✓ GenesisState を持たない |
| VirtualLayer なし (loop しない) | ✓ step_window を呼ばない |
| 両系を書き換えない | ✓ atom.virtual / other.virtual は **read-only** |
| 第三 ESDE 自身が loop しない | ✓ observe() は累積するだけ、書き戻し経路なし |

---

## 3. 確認 3: 案 3+4 (Kuramoto 同期 + 確率累積)

### 3.1 案 3 (Kuramoto 同期、phase 空間)

`observe_cooccurrence` 自体が Kuramoto の簡素版:
- Atom の各 bin の活性度 = 「Atom の phase 分布の各帯への寄与」
- Other の各 bin の活性度 = 同
- 両系で **同じ bin** が同時に立つ = **両系が同じ phase 帯で同期している**
- → これは Kuramoto order parameter の「位相が同方向」と等価 (bin = 方向の離散化)

### 3.2 案 4 (確率累積、累積閾値 state 由来)

履歴と累積カウンタで「繰り返し同時に立った bin ペア」を弾き出す:

```python
def detect_rcid(self):
    """累積閾値超えの bin ペア = 共鳴 CID"""
    # 累積閾値は state 由来 (Phase Shifted の cooc_count を床に対照比較)
    # ここでは絶対値を返すだけ、3 条件の大小は main で
    nonzero = self.cooc_count[self.cooc_count > 0]
    if len(nonzero) == 0:
        return set(), 0
    # 床は対照比較で main 側で出すので、ここでは生の sum と nonzero count を返す
    return {tuple(p) for p in np.argwhere(self.cooc_count > 0)}, int(nonzero.sum())
```

**累積閾値 state 由来**:
- 単発の bin pair (cooc_count = 1) は弾く
- ですが「累積が何回以上で共鳴 CID」の閾値は Phase Shifted の cooc_count 分布を床にする
- → main で 3 条件比較時に「Active の cooc_count > Phase Shifted の cooc_count」を bin pair ごとに見る (factor なし)

### 3.3 単発を弾き繰り返しを束ねるか

`cooc_count[a, b]` は履歴累積。値が 1 = 1 回だけ同時立ち (偶然)、値が 5+ = 繰り返し同時立ち (構造)。Phase Shifted では値が低くとどまり、Active では高くなる **はず** (Gemini 予測)。

---

## 4. 確認 4: 3 条件 (Active / Self / Phase Shifted)

### 4.1 各条件の実装

| 条件 | 実装 |
|---|---|
| **Active Pair** | Atom seed = sa, Other seed = so で独立進化、ResonanceObserver で両系 occupancy を毎 window 観察 |
| **Self Loop** | Atom seed = sa のみ。「Other 役」も同じ atom engine の occupancy を使う = **完全同期**。**ですが Stage 1 の意図は「一系のみ」を見ること**、別実装が要る (§4.2) |
| **Phase Shifted** | Atom + Other 独立進化、ですが Other の occupancy を **bin shift** (= phase π ずらす) で使う = 位相破壊 |

### 4.2 Self Loop の実装案

Web Claude 設計「一系のみ (Other なし)、自己に対して共鳴検出」=

**Code A 案 (シンプル)**: Atom の occupancy を **time-shifted self** で使う:
```python
# Atom の前 window の occupancy を「Other 役」として観察
atom_occ_history = []  # 各 window の occupancy

for w in range(WINDOWS):
    atom.step_window()
    atom_occ_history.append(np.array(atom.virtual.occupancy))
    if w >= 1:  # 1 window 前と現在の cooc
        observer.observe(atom_occ_history[w-1], atom_occ_history[w])
```

これで「Atom 系内の時間的自己同期」= self loop の特徴を見る。

または **完全同期 (= Atom の occupancy を両側として)**:
```python
observer.observe(atom_occ, atom_occ)  # 完全同期 → cooc max
```

Web Claude 意図「立つなら同期でなく内部偏り」と整合するのは **time-shifted self** (Code A 推奨)。

### 4.3 Phase Shifted の実装

```python
# Other の occupancy を bin で π ずらす
shifted_occ_o = np.roll(occ_o, N_BINS // 2)  # 32 bin shift = π 位相反転
observer.observe(occ_a, shifted_occ_o)
```

- bin shift は phase 空間操作のみ (node ID 不要)
- π ずらせば「両系が完全に逆相」= 確実に非同期
- 必要なら別案: 時間軸 shift (Other の前 window occ を使う)

---

## 5. 確認 5: 対照比較 (factor なし、過去標準スケール)

### 5.1 比較指標

```python
N_rcid_active = observer_active.total_cooc()
N_rcid_self = observer_self.total_cooc()
N_rcid_shifted = observer_shifted.total_cooc()

# 大小判定 (factor なし)
active_gt_shifted = N_rcid_active > N_rcid_shifted  # 主役
active_gt_self = N_rcid_active > N_rcid_self
# 3 atom 共通で True なら Stage 1 出口 OK
```

- 絶対閾値・factor なし、3 条件の **大小のみ**
- 3 atom seeds で **大小が揃うか** が再現性指標 ([[code-a-blind-spots]] 単一 seed 絶対視しない)

### 5.2 過去標準スケール

```python
ATOM_SEEDS = [42, 100, 200]  # 3 atom (v1111f 直接比較、CPU 24 cores 整合)
WINDOW_STEPS = 500  # v9.18 標準
MATURATION_WINDOWS = 10
TRACKING_WINDOWS = 20
WINDOWS = 30
NATURAL_FIRE_START = 10  # v1111f 流用、自然発火開始 window
```

### 5.3 注入は不要 (Stage 1 では)

Web Claude §0 「書き戻しなし」、Stage 1 では injection なし、**両系を自然進化させて観察するだけ**。
→ v1111f より軽い (注入計算なし、3 instance のうち center 不要、Atom + Other の 2 instance で済む)。

---

## 6. 実装構成

### 6.1 Tasks

| condition | instance |
|---|---|
| **Active Pair** | atom (sa) + other (so)、独立進化、ResonanceObserver で両系観察 |
| **Self Loop** | atom (sa) のみ、time-shifted self で観察 |
| **Phase Shifted** | atom (sa) + other (so) 独立進化、Other occupancy を bin shift で観察 |

3 atom × 3 conditions × 3 Other (Active と Phase Shifted のみ) = **3 + 3×3 + 3×3 = 21 tasks**
または Other を集約: 3 atom × 3 conditions = 9 tasks (Other = 100 固定で smoke)

Code A 推奨: smoke で **3 atom × 3 conditions (Other=100 固定) = 9 tasks**、結果次第で Other 振り。

### 6.2 並列 + 時間

- 9 tasks Pool(9) で 1 Wave
- v1111f より軽い (2 instance × 30 windows × 500 step = 3.6 時間予想)
- 推定 **約 3.5-4 時間**

### 6.3 出力

- `cooc_matrix.parquet`: 各 task の cooc_count[64×64] (= 4096 cell × 9 task = 37k rows)
- `n_rcid_summary.parquet`: 各 task の N_rcid raw、phase_sig 分布
- `summary.json`: 3 条件比較結果、大小判定

---

## 7. 一文サマリ

v1112 Stage 1 Code A 確認 5 点回答 (2026-06-03、Web Claude Stage 1 設計、node ID 排他最優先) — (1) node ID 完全排他 ✓ phase 空間 (64 bin) のみで共鳴検出、両系から渡るのは bin index のみ node ID/label ID は系内に閉じる、v1111 番号コピー欠陥と異なり「bin index = 同じ phase 帯」の意味共有のみ赤信号なし / (2) 第三 ESDE = ResonanceObserver class、state なし、cooc_count[64×64] 累積カウンタ + 履歴、両系 occupancy を read-only で読み書き戻さず loop しない / (3) 案 3 Kuramoto = 両系の同 bin 同時立ち検出 (= 同 phase 帯で同期、Kuramoto order parameter 簡素版)、案 4 確率累積 = 履歴累積で繰り返し弾き出す、累積閾値は Phase Shifted を床にした state 由来対照比較 / (4) 3 条件 = Active Pair (独立 seed 二系同時) + Self Loop (Atom のみ time-shifted self で時間的自己同期) + Phase Shifted (同一 seed Other occupancy を bin shift で位相 π ずらし完全逆相)、bin shift は phase 空間操作のみ node ID 不要 / (5) 対照比較 = N_rcid raw の大小のみ factor なし 3 atom 共通で大小揃うか単一 seed 絶対視しない、過去標準スケール 500×30 自然進化 (注入なし Stage 1 書き戻しなし) v1111f より軽量、構成 3 atom × 3 conditions = 9 tasks Pool(9) 1 Wave 推定 3.5-4 時間、Code A 規律遵守 ([[feedback-index-first]] 実践 [[reference-legacy-treasures]] から phase 空間活用 / [[code-a-blind-spots]] node ID 排他で v1111 番号コピー欠陥再発防止)、書込み unified/attention_center_prep/ 配下のみ。

---

**確認回答 end. node ID 排他 ✓、state なし ✓、対照比較 factor なし ✓ → 実装に進む。**
