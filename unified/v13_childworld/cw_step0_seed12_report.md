# v13 child-world step-0 seed=12 結果（記録のみ・判定なし）

## 自己規律宣言（Code A）
**① 過去引用**: step-0 指示書 / `cw_step0_feasibility_check.md`(§8) / `cw_step0_smoke_report.md`(seed=3 + コード懐疑再点検 バグ無し) / 4 knob 教訓(real≈shuffle は mean/std が pairing 盲目) / §16(smoke 後停止・集団平均の罠) / #29(観察方法を疑う) / #33。
**② Taka 逐語**: 「step 0（CID 値が子に情報を渡せているか）だけ固める」「6−7 に広げる…追加候補の妥当性も検証」「ノードごと…混ぜてよくない」「問題がなければ次に進む」。
**③ 判定は Taka**（success/fail 置かず観察事実のみ）。
**④ 集約語禁止・crown 禁止。**

## 観察対象注釈ブロック
同系内（child=親 seed0 CID の縮小版）。読=frozen。書=`unified/v13_childworld/` のみ。child in-memory、親非書込。*実行*: 2026-06-21、`cw_step0.py` CW_SEEDS=12、**1002 child（real 984 + canon 18）、run_len=35000、Pool24、5977s（1.66h）**。出力 = `cw_step0_signatures.parquet`(上書き) / `cw_step0_summary.json`。

---

## 1. 主結果（Mantel、seed=3 → seed=12 比較）
| stratum | Mantel(Mc) r/p | Mantel(6入力) r/p | seed=3 からの変化 |
|---|---|---|---|
| **n2 (54 CID)** | 0.490 / **0.001** | 0.602 / **0.001** | Mc 0.42→0.49・6in 0.55→0.60＝**強化**（最も母数大・頑健）|
| n4 (11 CID) | 0.329 / **0.026** | 0.478 / **0.002** | Mc 0.47→0.33・6in 0.60→0.48＝弱化（11 CID で smoke が過大評価、seed=12 が信頼値。なお有意）|
| n5 (17 CID) | 0.042 / 0.355 | 0.091 / 0.266 | 不変（null のまま）|

- **6入力 > Mc が全層・両 seed で一貫**（n2 0.60>0.49、n4 0.48>0.33、n5 0.09>0.04）= 非 M_c 軸（capture_rate, n_captured）を足すと親–子対応が増える。Taka「M_c 4値の外に clean な CID identity があるか／追加候補の妥当性」への観察＝**M_c の外にも対応に寄与する CID 情報がある**。
- **n4 の r 低下は小標本ノイズ**（11 CID・55 pair・null std≈0.16）。smoke を絶対視しない規律どおり seed=12 で補正された（§16）。n2（54 CID）が最も信頼できる。

## 2. signal/noise の正しい解釈（seed=3 0.91 → seed=12 0.71 の低下は「真値への収束」）
seed を増やすと cid 平均署名から seed 雑音が抜けて between(cid 平均距離) は**縮んで真の信号へ収束**、within(単一 seed 雑音) は不変。∴ S/N 低下は劣化でなく、seed=3 の 0.91 が**雑音で水増しされていた**ことを意味する。2 つの S/N を分けると:

| stratum | 単一 child 識別 S/N (between/within) | cid 平均識別 S/N (between/(within/√12)) |
|---|---|---|
| n2 | **0.71** | 2.47 |
| n4 | 1.04 | 3.59 |
| n5 | 0.95 | 3.30 |

→ **二つの事実を分けて記録（強引な一括りを避ける）**:
1. **単一 child では親を見分けられない**（S/N≤1）= 1 体の child 署名は seed 雑音に支配される。
2. **12 seed 平均すると cid 平均は分離する**（S/N 2.5–3.6）= Mantel が捉えているのはこの平均後の構造対応。
∴ **伝達は「構造として検出可（Mantel 有意, n2/n4）だが per-realization では弱い（多数 seed 平均で初めて見える）」**。§7-1 caveat「6 本は breadth であって層内 strength でない」と整合。

## 3. n5 の新事実（seed=12 で鮮明化、観察のみ・断定しない）
- n5 は **cid 平均識別 S/N=3.30** ＝ child は CID ごとに分離している（差は*ある*）。
- だが **Mantel(parent, child) r=0.04** ＝ その分離が**親 CID 距離（M_c/6入力）に沿っていない**。
- ＝ n5 は「child が変わらない」のでなく「**child は変わるが親 identity に沿って変わらない**」。seed=3 の「null」より鮮明な像。
- **候補要因（未確定・#29 観察方法を疑う）**: n5 は入力が縮退（B_gen≒一定 CV0.025／既調査 B_gen↔r_core=−0.94 共線）→ D_parent の構造が薄く・低ランクで、対応すべき親距離構造がそもそも乏しい可能性。または param→署名が n5 領域で非線形/seed×param 交互作用支配で距離順位が崩れる可能性。**断定しない**。次段で n5 の D_parent 共線を観察方法側から切り分ける。

## 4. 観察のまとめ（判定は Taka）
- **問い「CID 情報が child に伝わるか＝real が shuffle(=置換 null)より親に対応するか」**:
  - **n2（最良母数）: 構造として伝わる**（Mc r=0.49, 6in r=0.60, p=0.001、創発のみ次元でも生存=manipulation 連鎖でない[smoke 検証]）。
  - n4: 弱く伝わる（p≤0.026、小標本）。
  - n5: 親 identity には沿わない（child は変わるが）。
- **ただし magnitude は弱い**（単一 child では seed 雑音優位、多数 seed 平均で顕在化）。
- **M_c の外（capture_rate, n_captured）も対応に寄与**（6入力>Mc 一貫）。

## 5. 次段（Taka 承認待ち・勝手に進めない）
- n5 の null を観察方法から疑う: D_parent の共線（母集団側）を測り、「親が似ているから対応構造が薄い」のか「伝達が n5 で本当に起きない」のかを切り分け（#29）。
- per-realization が弱い件: step-0 の問い（伝達の有無）は n2/n4 で固まった。**出口2（物理設定→CID 系傾向マップ→メイン反映）に進むなら、磁気の弱さ＝多数 seed 平均前提**を設計に織り込む要。
- 選定確定・マップ作成・beta/Z 投入・Atom 接続はしない。

## やらないこと / 一方向
- やらない: 出口2 マップ作成、success/fail 判定、crown、承認前の次段実行。
- 一方向: 読=frozen。書=`unified/v13_childworld/` のみ。child in-memory、親非書込。

## 一文サマリ
step-0 seed=12（Code A、2026-06-21、判定なし）── 1002 child・1.66h。**n2（54 CID, 最良母数）で real 署名が親 CID 距離に構造対応（Mc r=0.49 / 6入力 r=0.60, p=0.001）・6入力>Mc 一貫（M_c 外の軸も寄与）**。n4 は弱く有意（r 低下は小標本で smoke 過大評価の補正）。**n5 は child が CID ごとに分離(S/N3.3)するのに親 identity に沿わない(Mantel r=0.04)＝「変わるが親に沿って変わらない」**（候補=入力縮退/共線、断定せず次段で切り分け）。signal/noise の seed3→12 低下は真値収束で、**単一 child では親を見分けられず(S/N≤1)・12seed 平均で cid 平均が分離(S/N2.5–3.6)＝伝達は構造として検出可だが per-realization は弱い**。コード懐疑再点検でバグ無し（前 report）。判定は Taka。
