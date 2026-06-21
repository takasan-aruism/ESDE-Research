# 課題#1 下準備2 — 全326 atom cosine を捨てずに出す（サンプル確認のみ）報告

## 自己規律宣言（Code A）
① 過去引用済: m30（sim は N×326 で計算され rank_1 以外は捨てている、`run_seed_step10:256-262 / cosine_similarity:258 / argmax:261`）、#30（気まぐれ指標禁止）、m20（build_step10_table / build_step10_cid_vector / atom_profiles_cache slot_keys 整合）。
② Taka 逐語（原文）: 「各時点で計算され捨てられている全 326 atom の cosine を捨てずに出力して実物を見るだけ」「演算・指標・閾値・濃度・spike・Δ・位相化・分布の計算は一切しない」「取れることを確認するのが目的」「サンプルを数行、実数で報告に貼る」。
③ 成否判定は Taka（success/fail 置かない、観察事実のみ）。
④ 集約語なし。

*作成*: 2026-06-17、Code A。*コード*: `m31_full_cosine_probe.py`。*出力*: `full_cosine_probe/`。**新しい計算は足していない**（argmax で潰す前の sim をそのまま保存しただけ）。濃度/spike/Δ/分布/エントロピー/閾値/判定は**していない**。

---

## 1. 全326（valid 325）atom cosine が (cid,t) 単位で取れる（確認）

- `build_step10_table(0)` → 各行 `build_step10_cid_vector`（48次元）→ `cosine_similarity(vecs, atom_profiles[valid])`（= `run_seed_step10:258` と同一）で **(62,906 行 × 325 valid atom)** の cosine 行列を取得し、**argmax で潰す前にそのまま parquet 保存**。
- 列 = `cid, t, <325 atom 名>`。各セル = その (cid,t) の CID 48次元ベクトルと当該 atom profile の cosine。
- → m30 で「計算され捨てている」と確認した全 atom cosine は**再計算で実物として取れる**（出力に無いだけ）。

## 2. コスト実測（step10 seed0）

| 項目 | 値 |
|---|---|
| 行数 (cid,t) | 62,906 |
| atom 列 | 325 (valid) |
| build_table | 0.4s |
| build_vecs | 2.2s |
| cosine | 0.11s |
| save | 0.8s |
| **計** | **3.5s** |
| **全量 parquet** | **121.3 MB** |

**概算（Taka が範囲を決める用）**: 4 粒度 × 24 seed なら **~11.6 GB / 計算 ~6 分**（粒度で行数が違うので粗概算。event/pulse は step10 より行少、window は更に少）。

## 3. サンプル実数（ある (cid,t) で 326 atom がそれぞれどれくらい立っているか）

rank 上位だけでなく、複数 atom が同時にどの cosine 値で並んでいるかが見える形で 3 行:

**cid 41 / t 13870** — min 0.0608 / mean 0.2495 / max 0.5215
- 上位8: PER.sound 0.5215, PRP.deep 0.4946, PRP.clear 0.4606, TIM.moment 0.4522, CHG.advance 0.4467, LOG.effect 0.4387, EXS.presence 0.4301, COM.silence 0.4271
- 中位(160-162位): PRP.light 0.246, COM.speak 0.246, EXS.spirit 0.2436
- 下位3: COG.unlearned 0.0729, SOC.individual 0.0688, WLD.unskilled 0.0608

**cid 107 / t 23680** — min 0.0168 / mean 0.1617 / max 0.4655
- 上位8: EXS.being 0.4655, FND.timeless 0.4586, EXS.nonbeing 0.4055, PER.sound 0.395, TIM.moment 0.3924, PRP.clear 0.3857, PER.hear 0.3565, PER.see 0.3423
- 中位(160-162位): BOD.hand 0.1626, ECO.currency 0.1618, WLD.outer_realm 0.1602
- 下位3: PER.numb 0.0251, COG.mindless 0.0215, COM.muteness 0.0168

**cid 178 / t 23720** — min 0.0172 / mean 0.1631 / max 0.4506
- 上位8: EXS.being 0.4506, PER.sound 0.4035, EXS.nonbeing 0.3918, TIM.moment 0.3803, PRP.clear 0.3745, LOG.reason 0.3724, PER.hear 0.3631, PER.see 0.3468
- 中位(160-162位): VAL.falsehood 0.1549, STA.peace 0.1542, WLD.religion 0.1538
- 下位3: COG.mindless 0.0244, PER.numb 0.0233, COM.muteness 0.0172

→ 観察事実（解釈なし）: 1 つの (cid,t) で 325 atom が **0.02〜0.52 の幅で同時に値を持つ**（rank_1 はその最大値）。複数 atom が並んで立っている実物がそのまま取れる。**「濃度」「集中」等の計算・判定はしていない**（数値を貼っただけ）。

## 4. やらなかったこと（明示）
濃度・spike・Δ・分布・エントロピー・集中度・閾値・「大きい/小さい」判定・atom×atom 網・CID 投影・センター接続・effect_size・位相化は**一切していない**。「こう読めば濃度になる」も書かない。

## 5. 一方向保証 + 出力の扱い
読む=frozen（v106 trajectory コード / atom_profiles_cache / v105 diag logs）、書く=`full_cosine_probe/` のみ。grep: physics/inject/ledger 書込 **0 件**。
**全量 parquet（121MB）はリポジトリ肥大回避のため commit しない**（ローカル + `m31` 再 run ~3.5s で再生成可）。commit するのは code + `sample_rows.json` + `cost.json` + 本 md。

---

*以上 課題#1 下準備2（Code A、2026-06-17）。argmax 前の全 326(valid325) cosine を step10 seed0 で実物保存＝(cid,t)単位で取れることを確認。cost 3.5s / 121MB(全量), 4粒度×24seed 概算 ~11.6GB/~6分。サンプル: 1つの(cid,t)で 325 atom が 0.02〜0.52 の幅で同時に値を持つ実物を貼付。濃度/判定/次手段は書かない。判定は Taka。*
