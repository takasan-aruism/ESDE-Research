# v12 M5 — core channel（凍結核を動かす）結果: 初の cid 特異性シグナル

日付: 2026-06-14 / 30 run (A/C/F/D/E × 6 seed)、0 errors、**0 θdiv**。`m5_substrate_atom.py` CHANNEL=core。
Taka 方向: 全チャネルが shuffle で消えた=核(phase_sig)凍結のまま外貼り。→ 核そのものを動かす(行き止まりを条件変えて越える=アリズム)。

---

## 0. 結論

- **初めて real > shuffle が出た（cid 特異性シグナル）。** 核(phase_sig)を「いつもと違う経験の時だけ・構造内で」動かすと、**「誰の経験か」が効く**。
- **`corr(核drift, Δsurvival)` が sign-flip**: real(C, 自分の経験で核動く)=**5/6 seed で正**、shuffle(F, 他人の経験)=**5/6 seed で負**。前チャネルは real≈shuffle(同符号)だった。
- **θ 安全**: 0 θdiv、Δlinks −3.6〜−4.9%(slight)。MAX_DRIFT 上限で核を動かしても θ 死なず。
- 構造的理由: phase_sig は **torque 標的 + addressing 基準**＝動いた核を dynamics/入力が両方読む → 外貼り(shuffleで消える)と違い、核が動けば「誰のか」が結果を変える。

---

## 1. ★核心: real(C) vs shuffle(F)、corr(核drift, Δsurvival)（入力なし、核drift だけ）

| seed | C (自分の経験で核動く) | F (他人の経験で核動く) | C>F |
|---|---|---|---|
| 0 | −0.02 | +0.34 | ✗ |
| 1 | +0.66 | −0.38 | ✓ |
| 2 | +0.44 | −0.85 | ✓ |
| 3 | +0.16 | −0.24 | ✓ |
| 4 | +0.49 | −0.18 | ✓ |
| 5 | +0.68 | −0.25 | ✓ |
| **平均** | **+0.40** | **−0.26** | **5/6** |

- **C(real) > 0 が 5/6、F(shuffle) < 0 が 5/6**。自分の経験で核が動いた cid は生存↑、他人の経験で動かされた cid は生存↓。
- corr(Δlife_C, Δlife_F)=+0.39（前チャネル +0.5〜0.6 より低い＝real と shuffle で動く cid が違う＝cid 特異）。

## 2. θ 安全（phase_sig=θ直結、特に監視）

| cond | θdiv | Δlinks% |
|---|---|---|
| C/D/F/E | 0/6 | −3.6〜−4.9 |

- 核を動かしても θ は死なない。MAX_DRIFT(=0.5rad×STRENGTH) が本質方向を保ち暴走を防いだ。

## 3. 生存・個性化（A基準）

| cond | 最終生存 | exc_std |
|---|---|---|
| A | 17.7 | 29.6 |
| C real | 18.0 | 24.1 |
| F shuffle | 21.5 | 26.8 |
| D real+入力 | 18.8 | **36.5** |
| E shuffle+入力 | 22.7 | 29.4 |

- **総生存は C<F**（real 核drift は総生存を増やさない＝差別化/選別圧、生存ブーストでない）。
- だが §1 の通り **WITHIN-cid では「自分の経験で動いた cid が生存」**（corr 符号が real と shuffle で逆）。
- D で exc_std 36.5（個性化↑、入力ループが核drift と合わさり出力分化が増える）。

## 4. 解釈（正直に）

- **これは行き止まりの突破。** 凍結核では shuffle が常に再現した（「誰のか」が効かない）。**核を動かすと real と shuffle が符号で分離**（5/6 seed）＝「その個体の経験だから効いた」が初めて成立。Taka の DNA 観（核はあるが発現に柔軟性、いつもと違う時だけ動く）が実装で機能した。
- **caveat**: (1) seed0 が逆（5/6 で 6/6 でない、要 seed 増で頑健性確認）。(2) 総生存は C<F＝核drift は生存を上げず差別化する（選別圧の側面）。cid 特異性は「誰が生き残るか」(own-experience-aligned cid)に出る。(3) 入力ループ(D/E)は弱め（+0.14 vs −0.02）＝核drift 単独(C/F)が最も鮮明、入力が希釈する可能性。

## 5. 次（Taka 判断）

1. **seed 増で sign-flip の頑健性確認**（6→12、5/6 が安定するか、seed0 の逆を理解）。
2. **核drift の調整**: MAX_DRIFT/THRESHOLD/DRIFT_RATE を sweep し、cid 特異性が最大化する帯を探す（over-drive、θ 監視つき）。
3. **総生存 C<F の意味**: 差別化(選別圧)を個性化として活かすか、生存も上げる調整があるか。
4. **入力ループの希釈**: なぜ C/F より D/E が弱いか（核drift と input addressing の干渉）。

機構・θ・対照・per-seed 全て健全。**初の cid 特異性、堅い兆し（5/6）。** 行き止まりを条件変えて越えた。

## ファイル
- `run_m5_core/core_st1/{A,C,F,D,E}/seed{0-5}/`、`m5_substrate_atom.py`(CHANNEL=core, update_phase_sig)
- 参照: `m5_computation_audit.md`(凍結核の問題)、`m5_allchannels_result.md`(凍結チャネル全 null)
