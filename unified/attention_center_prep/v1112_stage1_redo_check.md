# v1112 Stage 1 作り直し — Code A 認識確認

date: 2026-06-03
from: Code A (Claude Code, Opus 4.7)
to: Web Claude / Taka
status: 指示受領、実装前の認識確認 (実装には未着手)

---

## 0. 全体認識 (最重要)

Web Claude / Taka 指示を、以下の通り認識した:

### 0.1 前回 v1112 Stage 1 の位置づけ

- 前回結果は **不成立でも兆しでもない**
- 主指標 (total_cooc / N_rcid) が位相ずらし (bin shift = 列 rotate) と数学的に独立だった = **位相ずらし対照を測れる道具ではなかった**
- 想定したもの (共鳴 CID = 同 phase 同期が偶然でないか) を、想定した道具で測れていなかった
- → 「不成立」でも「揃った」でもなく、**「測っていない」**
- 事後に diagonal で拾った (1)+(3) の 3/3 も、最初から diagonal で測る設計でなかったので **結果として残さない (兆しとも呼ばない)**

### 0.2 大前提 (Taka 規律として明文化)

**測定器が壊れているものを結果と呼ばない。** 曖昧にすると:

1. 壊れた測定の数字を結果として扱い
2. それを説明し
3. 次をその説明に合わせ
4. 本来の目的 (共鳴 CID が立つか) からズレ
5. 数字をいじる流れ = **ループ** に入る

ループ問題を解く作業が、測定器の放置でループに飲まれる。

→ **結果と呼ぶ前に「想定したものを、想定した道具で測れているか」を確認する。**
具体的には: 測ろうとしている処置 (位相ずらし) に対して、**主指標が反応することを、結果を読む前に確認する**。shift して値が動かない指標で shift の効果は測れない。

これは「失敗を反転して成功にしろ」ではない。壊れた測定は反転対象ですらない。組み直して測るだけ。

### 0.3 今回の位置づけ

- 「測り直し」ではなく「**測定器を組み直して、まだ測れていないものを初めて測る**」
- 新ステージではない、Stage 1 の作り直し
- 出口条件は Stage 1 の 3 条件 (1)+(2)+(3) のまま、Stage 2 / 意味 / 学習 / 書き戻しは入れない

---

## 1. 直す 3 点 (測定器の組み直し) と具体実装案

### 1.1 主指標を diagonal (近傍含む) に

#### 認識

- 共鳴の核心 = **両系が*同じ* phase 帯で同時に立つ** = cooc 行列の **対角**
- 主指標 = `diagonal_mass = Σ_i M[i, i]` + **近傍** `Σ_i Σ_{|d|≤δ} M[i, (i+d) mod 64]`
- δ は phase 離散化誤差 (5.6° / bin) の吸収のため、数 bin 程度

#### 具体実装案

```python
def diagonal_mass(M, delta=0):
    """対角 + 近傍 ±delta bin の mass"""
    n = M.shape[0]
    s = 0
    for i in range(n):
        for d in range(-delta, delta + 1):
            s += M[i, (i + d) % n]
    return float(s)

# 複数の delta で測る (固定値を置かない)
indicators = {
    'diag_d0': diagonal_mass(M, delta=0),   # 純対角
    'diag_d1': diagonal_mass(M, delta=1),   # ±1 bin (~11° 範囲)
    'diag_d3': diagonal_mass(M, delta=3),   # ±3 bin (~33° 範囲)
}
```

- δ=0 と δ=1, δ=3 の複数 δ で測り、Active vs Phase Shifted の **大小** を見る
- どの δ でも Active が大ならロバスト、δ 依存なら脆い
- factor は置かない (Phase Shifted との対照相対のみ)

#### total_cooc / N_rcid / max_cooc は判定に使わない

- 記録 (parquet に残す) はしてよい (Code A 設計欠陥の証拠として)
- 出口判定には使わない

### 1.2 同 seed 並走排除 (汚染を消す)

#### 認識

- 前回 OTHER_SEED_FIXED=100 で、atom=100 のとき atom と Other が **同 seed 並走** だった
- 「異なる系の共鳴」でなく「ほぼ同型の系の自己相関」を測っていた疑い
- atom=100 で diagonal が一番強かった (442) = +64% (v1110) と同じ匂い
- → 異系共鳴の証拠ではなく、汚染

#### 具体実装案

```python
ATOM_SEEDS = [42, 100, 200]  # 維持 (v1111d 互換)
OTHER_SEED_FIXED = 999       # ATOM_SEEDS のどれとも重複しない
```

- Other=999 固定 → 全 atom で同じ Other 系、atom 間の比較が成立
- atom=42, 100, 200 のどれとも別 seed → 同 seed 並走の構造的排除

(別案: Other = atom + 1000 のような atom 依存生成も可能だが、Web Claude 提案の「Other=999 固定」が条件最小なので採用)

### 1.3 self 床を乱数 phase に (慣性でなく無関係な相手を床に)

#### 認識

- 前回 self_loop = time-shifted 自己 cooc は、Atom の phase 慣性 (1 window では大きく動かない) で対角が高くなる
- 「self では立たず」が、慣性のせいで成立しなかった (2/3 不成立の本当の原因)
- 甘い対照だった

#### 具体実装案

```python
def random_phase_occupancy(state_seed, n_bins=64):
    """state 由来の乱数 phase 分布"""
    rng = np.random.RandomState(state_seed)
    occ = rng.random(n_bins)  # [0, 1) の一様分布
    return occ

# self 床 = Atom occupancy × 乱数 phase 分布 の cooc
# 各 window で異なる乱数 seed (atom seed + window index の関数)
for w in range(WINDOWS):
    atom.step_window(steps=WINDOW_STEPS)
    occ_a = list(atom.virtual.occupancy)
    # state 由来乱数: atom seed と window index から生成、再現可能
    state_seed = atom_seed * 100003 + w * 7919
    occ_rand = random_phase_occupancy(state_seed)
    observer_self.observe(occ_a, occ_rand)
```

- 「Atom の慣性」でなく「本当に無関係な相手」を床にする
- 乱数 seed は state 由来 (atom_seed と window から生成) で **再現可能**
- これで「self では立たない」が **本来の意味** (無関係な相手とは同期しない) で測れる

---

## 2. 実装前の測定器点検 (§1、必須手順)

実装後、本実行前に Code A が以下を確認:

### 2.1 主指標 diagonal が bin shift で動くか

```python
# ダミー行列で診断
import numpy as np
M = np.random.randint(0, 10, (64, 64))
M_shifted = np.roll(M, 32, axis=1)  # Phase Shifted と同じ操作

d_orig = diagonal_mass(M, delta=0)
d_shift = diagonal_mass(M_shifted, delta=0)

assert d_orig != d_shift, "主指標が shift 不変 — 測定器が壊れている、止める"
print(f"diagonal 原行列={d_orig}, shift 後={d_shift}, 差={d_orig - d_shift}")
```

- 差が出れば OK (主指標が shift に sensitive)
- 同じ値なら赤信号 (前回 total_cooc と同じ罠)、本実行に進まない

### 2.2 同 seed 並走がないか

```python
assert OTHER_SEED_FIXED not in ATOM_SEEDS, "Other が atom と同 seed = 汚染、止める"
```

### 2.3 乱数床が時系列で変わるか

```python
# window ごとに違う乱数を使うか確認
seeds_used = [atom_seed * 100003 + w * 7919 for w in range(WINDOWS)]
assert len(set(seeds_used)) == WINDOWS, "window 間で乱数 seed が重複"
```

これら 3 つを **本実行 (Pool 起動) の前に** 実行、結果を Web Claude に報告。

---

## 3. Web Claude コードチェック手順 (§2、Taka 指示)

Code A は実装後、以下を Web Claude に提示:

1. `unified/attention_center_prep/v1112_stage1_redo.py` (実装本体)
2. 測定器点検結果 (§2 の 3 項目の実行ログ)
3. 認識確認回答 (本ファイル)

Web Claude がコードを **実際に view して** 以下を確認:

- 主指標が diagonal (近傍含む) で、shift 不変な量 (total_cooc 等) を主指標にしていないか
- Other seed が atom と別 seed で、同 seed 並走 (atom=100 × Other=100) が起きていないか
- self 床が乱数 phase との cooc になっているか (time-shifted でないか)
- node ID 排他 (phase 空間のみ)、第三 ESDE が state なし観察体・書き戻しなし、が保たれているか

**Web Claude OK 後に本実行**。報告自己点検 (前回 ATOM_SEEDS は気づいたが指標独立性は見逃した) だけに頼らない。

v1111e で Web Claude が実際にコードを view して番号コピーを見つけた手順を、**今回は最初から組み込む**。

---

## 4. 不変 (前回 Stage 1 のまま、変えない)

- 第三 ESDE = state なし観察体 (ResonanceObserver、両系 read-only、書き戻しなし)
- node ID 排他 (phase 空間 64 bin のみ)
- 案 3+4 (Kuramoto 同期 + 確率累積)
- 過去標準スケール (500 step × 30 window、自然進化、注入なし)
- 3 条件 (Active Pair / Self Loop / Phase Shifted)
- factor なし、大小のみ、3 atom 共通で揃うか
- 出口一点 = 共鳴 CID が (1) 両系で立ち (2) self では立たず (3) 位相ずらしより明確に多いか
- Stage 2 / 意味 / 学習 / 書き戻し / 会話 入れない

---

## 5. 報告の言葉縛り (crown 防止)

- 出ても「**ループの外に独立軸が立つ候補が観察された**」まで
- 「Unified 完成」「第三 ESDE 成立」「共鳴 CID 形成」「同期した」とは書かない
- 不成立 (測れた上での) なら「Stage 1 不成立として記録、共鳴 CID 候補は観察されなかった」

---

## 6. やる順 (再確認)

| # | ステップ | 待ち |
|---|---|---|
| 1 | **本ファイル (認識確認) を Web Claude / Taka に提示** | **← 今ここ** |
| 2 | OK 後、測定器を組み直す (主指標 diagonal、Other=999、self 床乱数) | Web Claude / Taka OK 後 |
| 3 | 測定器点検 (§2 の 3 項目): diagonal が shift で動くか / 同 seed なし / 乱数 seed 多様 | Code A 自身で確認 |
| 4 | Web Claude コードチェック: 実装コードを Web Claude が view、§3 の 4 点確認 | Web Claude OK 後 |
| 5 | 本実行 (Pool(9) 1 Wave、推定 2.4 時間) | コードチェック OK 後 |
| 6 | 3 条件で diagonal_mass を取る、Active が Phase Shifted / self (乱数床) を明確に上回るか、3 atom で揃うか | |
| 7 | 観察事実のみ記録 (判定置かない)、揃えば Stage 2 へ、揃わねば「測れた上での不成立」として記録 | Web Claude 機能設計 → Taka 主題評価 |

---

## 7. 確認 5 点

| # | 確認項目 | Code A 認識 |
|---|---|---|
| 1 | **測定器の点検 (最優先)**: 主指標 diagonal が位相ずらし (bin shift) で値が動くか。shift 不変な量 (total_cooc 等) を主指標にしていないか | ✓ §2.1 で ダミー行列の roll テスト実装、本実行前に確認 |
| 2 | 主指標 diagonal: `Σ M[i,i]` + 近傍 ±δ。total_cooc/N_rcid は判定に使わない (記録のみ) | ✓ §1.1 で複数 δ (0, 1, 3) で測る、total_cooc は parquet 記録のみ判定外 |
| 3 | 同 seed 並走排除: Other が atom=[42,100,200] のどれとも別 seed か。atom=100 × Other=100 が起きないか | ✓ §1.2 で OTHER_SEED_FIXED=999、§2.2 で assert |
| 4 | self 床: 乱数 phase 分布との cooc (time-shifted でない)。乱数 seed は state 由来で再現可能か | ✓ §1.3 で `atom_seed * 100003 + w * 7919` 由来の乱数 phase、再現可能 |
| 5 | 不変: node ID 排他 (phase 空間のみ) / state なし観察体 / 書き戻しなし / 案 3+4 / 過去標準スケール / factor なし大小比較。**Web Claude コードチェック (§3) を本実行前に受けること** | ✓ §4 で不変項目維持、§3 で Web Claude コードチェック手順明文化 |

---

## 8. 一文サマリ

v1112 Stage 1 作り直し認識確認 (2026-06-03 Code A → Web Claude / Taka) — 前回位置づけ (不成立でも兆しでもない主指標 total_cooc/N_rcid が位相ずらしと数学的に独立 = 測れていない、diagonal で拾った (1)+(3) も結果に残さない兆しと呼ばない) 大前提 (測定器壊れているもの結果と呼ばない曖昧にすると壊れた数字説明し次をそれに合わせ目的からズレ数字いじりループ入る結果と呼ぶ前に処置に主指標が反応するか確認 shift で動かない指標で shift 測れない失敗反転でなく組み直すだけ) 今回位置づけ (測り直しでなく測定器組み直してまだ測っていないもの初めて測る新ステージでない Stage 1 作り直し出口 3 条件不変) 直す 3 点 ① 主指標 diagonal `Σ M[i,i]` + 近傍 ±δ 複数 δ (0,1,3) で測り Active vs Phase Shifted 大小 factor なし total_cooc/N_rcid 判定外記録のみ ② Other=999 固定 ATOM_SEEDS=[42,100,200] のどれとも別 seed atom=100 × Other=100 同 seed 並走排除 ③ self 床 = 乱数 phase 分布との cooc `atom_seed * 100003 + w * 7919` 由来再現可能 時間 shift 慣性床でなく無関係相手床、実装前測定器点検 (ダミー行列 np.roll で主指標 diagonal が値変わるか確認 同 seed なし assert 乱数 seed window 間で多様) 本実行前 Web Claude コードチェック (実装コード view して主指標 diagonal / Other 別 seed / self 床乱数 / node ID 排他 state なし書き戻しなし確認 v1111e 番号コピー見つけた手順最初から組み込む) 不変 (state なし観察体 read-only 書き戻しなし node ID 排他 phase 64 bin 案 3+4 過去標準 500×30 自然進化注入なし 3 条件 factor なし大小 3 atom 揃うか 出口一点 共鳴 CID 両系で立ち self で立たず位相ずらしより多いか Stage 2 意味学習書き戻し入れない) 報告言葉縛り (Unified 完成第三 ESDE 成立同期した書かない出ても「ループの外に独立軸が立つ候補が観察された」まで) やる順 (本ファイル提示 → OK 後組み直し → 測定器点検 → Web Claude コードチェック → 本実行 → 観察 → Web Claude 機能設計 → Taka 主題評価) 書込み unified/attention_center_prep/ 配下のみ。

---

## 9. Code A 自己評価

- 前回失敗の原因認識: ✓ 集計指標が処置と数学的に独立 (盲点 11 [[code-a-blind-spots]] 追加済み)
- 直す 3 点の理解: ✓ 主指標 / Other seed / self 床
- 実装前手順の理解: ✓ 測定器点検 → Web Claude コードチェック → 本実行
- 言葉縛りの理解: ✓ 「兆し」「成立」書かない

**Web Claude / Taka の認識確認 OK を待ちます。OK 後に実装に進みます。**
