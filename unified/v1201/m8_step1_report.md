# v12 Atomset cid_align — STEP 1 報告: cid_align 最小構築 + m6 §4.2 の訂正

**指示書 v2 STEP 1**: v106 エンコーダ 6 軸 + seed_max offline で per-CID per-10step cid_align を構築。
**目的（指示書）**: 関門 STEP 2 にかける cid_align シグナルを作る。
**次接続**: STEP 2 で「生イベントカウントの遅延コピーか独立か」にかける。

*作成*: 2026-06-15、Code A。*コード*: `m7_step1_build_cid_align.py`。*出力*: `run_step1/cid_align_step1.parquet`。
*使ったエンコーダ*: `developmental/v106/v106_post_process.py:234-338` から逐語コピー（簡易 vec48 でない）。
**crown なし。観察事実のみ。判定は Taka。**

---

## 0. 一文結論 + 【要・Web Claude 判断】

cid_align を 24 seed・5224 CID・376,956 chunk-records で構築完了（物理書込ゼロ）。**ただし STEP 1 を実データで検証した結果、m6 §4.2 の「6 軸クリーン」は楽観的だった**——実際に v106 エンコーダで写るのは **4 軸 DIRECT（temporal/scale/interconnection/resonance）+ ontological 4/5 近似**で、**epistemological は写せない**（R_familiarity_pre が count でなく ratio）。境界を作り直すと「簡易 vec48 の罠」なので写さず flag。**この 5 軸（26 次元）で STEP 2 関門に進んでよいか、epistemological を別途扱うか、Web Claude 判断を要する。**

---

## 1. 構築結果（事実）

| 項目 | 値 |
|---|---|
| seed | 24（全て、smoke seed0 を絶対視しない規律） |
| CID 総数 | **5224**（seed×cid）＝**v106 cid_atom_sim_matrix の 5224 と一致**（クロスチェック成功） |
| chunk-records | 376,956（per-CID per-10step、event のある chunk のみ） |
| CID あたり chunk-records 中央値 | 21 |
| n_core 分布 | 2:3968 / 3:288 / 4:327 / 5:638 / 6:1 / 7:1 / 8:1 |
| 非ゼロ次元 | **26/48**（idx 0-31 のうち epistemological 5 と informational 1 を除く） |

更新式: `cid_align ← normalize(cid_align + α·f·exp_vec)`、α=0.3、f=robust_z（median/MAD、いつもと違う度）、K_MIN=3。

## 2. 軸ごとの写り（実データ検証、m6 §4.2 の訂正）

| v106 軸 | 入力 field | v107 で写るか | STEP 1 |
|---|---|---|---|
| temporal | lifespan_so_far | ✓ DIRECT | 使用（非ゼロ 100%） |
| scale | n_core_member | ✓ DIRECT | 使用（非ゼロ 100%） |
| interconnection | n_alphas_pre | ✓ DIRECT | 使用（非ゼロ 100%） |
| resonance | C_pre | ✓ DIRECT | 使用（非ゼロ 100%） |
| ontological | Q_pre/v14_q0・n_alphas_pre・n_core・C_pre | △ **4/5**（informational=v14_virtual_familiarity_entries が v107 に**無い**→0 で renormalize） | 使用（非ゼロ 100%、ただし 5 次元中 4 次元のみ非ゼロ） |
| **epistemological** | R_familiarity_pre | ✗ **写せない** | **未使用（非ゼロ 0%）** |
| symmetry/lawfulness/experience/value_gen | v99_drift 等 | ✗ field 無し | 未使用（0） |

**epistemological が写せない理由（実データ）**: `R_familiarity_pre` は範囲 **-5.79〜20・中央 -0.26 の ratio/z 値**。v106 `epistemological_vector` は **count の境界 [10,30,60,150]** を期待する（v106 では median 41 の familiarity 数）。ratio を食わせると 99% が level 0 に潰れ、軸として機能しない。境界を作り直すのは「簡易 vec48 の罠」（指示書 6・「v106 のものと一致するか」に反する）ので**写さず flag**。

**ontological が 4/5 の理由**: 5 sub-field 中 `v14_virtual_familiarity_entries`（informational）が v107 source_events に無い。残り 4（material=Q_pre/v14_q0、relational=n_alphas_pre/max、structural=n_core/7、semantic=C_pre/C_max）で renormalize。設計書が許す「豊かな近似（完全再現不可）」の範囲。informational 次元（idx 19）は常に 0。

## 3. 過去問題の参照結果（指示書 STEP 1 記載分）

- **birth_step バグ（教訓271）→ 補正不要と確認**: v107 の `birth_step + lifespan_so_far == timestamp`（中央偏差 **0.0**）で正しく、lifespan=1 は 2.96% のみ（出生直後の真の event）。**v107 source_events は補正済み**＝per_subject の birth_window バグの影響を受けていない。temporal 軸を lifespan_so_far から直接作って問題ない。
- **build_cid_vector live 不可（v1101a）→ offline で解消**: seed_max（n_alphas_max・C_max_seed）を v107 全ストリームの max から計算（`compute_seed_max`）。live で死んだ run-end 依存が offline で消える（Code A crux 確認）。
- **両端人為的投影（教訓269・認識の核）**: CID 側 48 次元は v106 変換規則の産物、下位 level 厳密でなくてよい。本 STEP は一致率を測っていない（行き先・往復は STEP 3-4）。

## 4. 物理書込ゼロ確認（grep 結果を貼る、指示書 厳守事項2）

```
物理書込 (state.theta/.E/.S/phase_sig/label.nodes への代入): 0 件
engine import (V82Engine/VirtualLayer/SubjectLayer/realizer): 0 件 (post-process のみ)
書込先: m7_step1_build_cid_align.py:229  out.to_parquet(...) のみ
```
→ v107 ログを読んで parquet を書くだけ。物理層に一切触れない（v9.13/v106/v1114 規律遵守）。

---

## 5. 【Web Claude 判断要】STEP 2 へ進む前の確認

1. **epistemological を写せない件**: (a) このまま 5 軸（26 次元、temporal/scale/ontological4-5/interconnection/resonance）で STEP 2 関門に進む、(b) R_familiarity_pre 用に別の（v106 でない）写し方を許可する＝簡易 vec48 の罠を承知で入れる、(c) 別の familiarity 系 field を探す（per_subject の last_n_partners は run-end で per-event でない）。**Code A 推奨 = (a)**。理由: STEP 2 は「cid_align が生イベントカウントの遅延コピーか」を見る関門で、26 次元あれば十分検定可能。epistemological 1 軸の有無は関門の結論を変えにくい。境界 reinvent は規律違反。
2. **ontological 4/5 近似の許容**: informational 欠落（idx 19 常時 0）を許容してよいか（設計書「豊かな近似」範囲と Code A は判断、最終は Web Claude/Taka）。

**この 2 点の確認後、STEP 2（関門・選択肢 C: per-CID 主 + 系全体副）へ。** STEP 1 は実装・実行済み、報告のみで pause。

---

*以上 STEP 1 完了（Code A、2026-06-15）。cid_align 24seed×5224CID 構築（v106 5224 と一致）、物理書込ゼロ。実データで m6 §4.2 を訂正: 4 軸 DIRECT + ontological 4/5、epistemological は ratio で写せず flag。birth_step 補正不要・seed_max offline 解消を確認。STEP 2 進行可否（epistemological 扱い）を Web Claude 判断待ち。crown なし。*
