# v12 M5 — 全チャネル × over-drive × field 結果（cid/atom 特異な個性化は出ず）

日付: 2026-06-13 / 3 バッチ（全チャネル gate / over-drive+link / field）計 ~80 run。`m5_substrate_atom.py`。
判定: (1)corr 3seed 一貫正 (2)shuffle で消える (3)θ slight、＋ atom-level η²（per-Atom 文化の正しい粒度）。

---

## 0. 結論（先に・正直に）

- **どのチャネルも「文化が cid/atom 特異に dynamics を変え、構造的 baseline を超える個性化」を出せなかった。** torque（力学・over-drive 含む）/ lambda（出力）/ link（接続グラフ）/ field（世界＝入力地形）/ multi（合成）、全て。
- **θ は全 run で死なず（slight 維持、over-drive st10 でも）。** 機構・配線は健全。
- **核心の所見（η² baseline）**: cids は文化が無くても atom で強くクラスタする（baseline η²(degree)=0.62, η²(exc)=0.10）。理由＝atom は誕生時 n_core+phase_sig から付与＝**同 atom の cid は構造が似て dynamics も似る（文化でなく構造の偽の足場）**。文化を載せても η² は baseline を超えない。
- **→ ボトルネックはチャネル（効かせ方）でなく、経験シグナルそのもの（何を測るか）か、ESDE のカオス頑健性、の可能性。** 効かせ口は出尽くした。

---

## 1. #1 torque over-drive 閾値探索（cid 特異性が出始める strength）

| strength | corr_C(経験,Δexc) 3seed | mean | θ破綻 | Δlinks% |
|---|---|---|---|---|
| st=1 | −0.31 / +0.23 / +0.27 | +0.06 | 0 | −3.6 |
| st=3 | +0.54 / −0.05 / +0.03 | +0.17 | 0 | −5.2 |
| st=10 | −0.11 / +0.18 / +0.25 | +0.11 | 0 | −1.9 |

- **閾値は現れず**。corr は全 strength で mixed（3 seed 一貫正にならない）。over-drive しても θ 撹乱に対し cid 特異性が立ち上がらない。θ は st10 でも死なず（slight 頑健、神の手にならない範囲）。

## 2. #4 link 接続グラフ（誰と繋がるかが文化で変わるか）

| metric | corr_C(経験, Δ) | corr_F(shuffle) |
|---|---|---|
| degree | +0.19 / +0.12 / nan | +0.21 |
| n_partner_cids | +0.03 / +0.21 / nan | +0.06 |
| exc | +0.21 / +0.22 / nan | +0.24 |

- 接続グラフ（degree）は弱く動くが **corr_F(shuffle) ≈ corr_C ＝ cid 特異でない**（shuffle で消えない）。文化は「誰と繋がるか」を cid 特異には変えていない。

## 3. field（世界経由：文化が入力地形を偏らせる）

| cond/st | exc_std | deg_std | partner_std | survival | θ破綻 |
|---|---|---|---|---|---|
| B(st1) control | 23.0 | 1.58 | 0.09 | 44.3 | 0 |
| D(st1) field | 23.3 | 1.64 | 0.17 | 43.7 | 0 |
| E(st1) shuffle | 26.9 | 1.66 | 0.18 | 48.0 | 0 |
| D(st3) field | 26.9 | 1.47 | 0.18 | 49.0 | 0 |
| E(st3) shuffle | 27.1 | 1.56 | 0.14 | 44.7 | 0 |

- D(field) は B(control) をほぼ超えず、E(shuffle) も同程度＝**世界経由でも cid 特異の個性化は出ない**。
- 一つだけ気になる: η²(partner) field_st1 D=0.258 vs E=0.034（D≫E）だが、st3 で 0.117 vs 0.153 と反転＝**strength 横断で非頑健＝ノイズ**。

## 4. atom-level η²（per-Atom 文化の正しい粒度、baseline 対照）

per-Atom 文化は atom 群の性質＝cid-level でなく atom-level で見るべき（cids は atom 内で似る）。

| 条件 | η²(exc) | η²(degree) | η²(partner) |
|---|---|---|---|
| **baseline A（文化なし）** | **0.100** | **0.624** | — |
| field D real | 0.076 | 0.630 | 0.258 |
| field E shuffle | 0.041 | 0.547 | 0.034 |
| torque C real | 0.075 | 0.433 | 0.510 |
| torque F shuffle | 0.129 | 0.478 | 0.422 |
| link C real | 0.088 | 0.551 | 0.076 |

- **baseline で既に η²(degree)=0.62, η²(exc)=0.10＝文化なしでも atom クラスタは強い**（atom=構造の関数＝偽の足場）。
- 文化を載せた各条件の η² は **baseline を超えない**（むしろ同等〜下）。real vs shuffle も方向が一貫しない。
- → **文化は atom-level の個性化を baseline 以上に作っていない。** クラスタは文化でなく構造由来。

## 5. perception / gravity（今回外した理由・正直）

- **gravity**: `step()` 内で `gravity_factors` を算出・消費（local 変数、`virtual_layer_v9.py:715→764`）＝hook の外から綺麗に挟めない。かつ `grav_mag ∝ torque_mag ∝ torque_factor`＝torque チャネルに構造的に従属。→ 別チャネルとして無効化不可・冗長。
- **perception**: `p_capture`（`v105:2014`）は run ループ深部＋「capture_rng touch 禁止」規律。cog.attention/familiarity を書いても v105 の per-step 更新/decay に流される（前回 no-op）。clean な per-Atom 化は v105 source 改変が要る（決定論・frozen に影響）。
- → no-op を出すのを避け、今回は外して正直報告。やるなら v105 を編集する別 round。

---

## 6. 含意（Taka 判断、選択は閉じない）

効かせ口（チャネル）は exhaustive に試し、**どれも cid/atom 特異な個性化を baseline 超えで出さない**。残る大きな分岐:

1. **シグナル側を疑う**: 経験が測っている量（cid_vec movement → per-Atom 集約）が cid を区別する情報を担っていない可能性。atom 割当（rank_1 = n_core+phase_sig）が粗く構造的＝文化の器として弱い。**「何を経験とするか」を作り直す**（例: atom を構造でなく経験履歴で動的に付与／cid 固有の経験指標を直接）。
2. **ESDE のカオス頑健性を所見として受容**: 緩い文化は cid 特異に dynamics を変えられない＝「考える時間/カオス系」の性質。文化は読取層（lambda）でしか現れない、を結論とする（生物: 同 DNA+文化差は解釈/出力差として現れる）。
3. **perception を v105 編集で本実装**して受け取り方（→dynamics）を唯一未検証の口として撃つ。
4. **粒度の見直し**: per-Atom が「群」で cid 特異を消すなら、cid 固有 + 文化共有の二層（筋1）に戻す検討。

機構・slight・θ は全て健全。負の結果だが堅い（多チャネル×over-drive×baseline/shuffle 対照で再現）。

## ファイル
- `run_m5_atom/{torque_st*,lambda,link_st1,field_st*}/{A-F}/seed{0-2}/`、`m5_substrate_atom.py`
- 参照: `m5_interference_and_subject.md`（主体）、`m5_channel_investigation.md`（口）
