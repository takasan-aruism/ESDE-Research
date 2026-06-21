# v12 Atomset STEP 4 — event 下流帰結(delta)で辺を重み付け + 対照 A/B 報告

## 自己規律宣言（Code A）
① 過去引用済: STEP3 `m20`(time-local 辺ロジック)・`m22`(時間版でも rare↔common 0.925=event は出入り判定だけ)・`m23`(delta は per-(event,target_cid)・hop±1)、`v107_baseline_constructor` 読了（delta=target c の*単独状態*の event 後窓 drift・pairwise でない）、v108（familiarity が atom 識別・波及経由）、揺れの幅＝点推定にしない。
② Taka 逐語（原文）: 「意味のある信号は状態変化であって atom 同士の共起ではない」「下がること自体は目的でない＝ランダム化でも下がる、対照との差が要る」「全部読んで変える系なら何やったって変化しないに決まってる」。
③ 成否判定は Taka（success/fail/Full/Partial/Failure 置かない、観察事実のみ）。
④ 集約語なし。

*作成*: 2026-06-16、Code A。*コード*: `m24_step4_build_drift_network.py`、`m25_step4_gate.py`。*出力*: `timelocal_delta/`（283M、24 seed）。

---

## 【後日訂正・m29 懐疑監査】
GATE **E「main↔sim_matrix共起 負相関」は cross-builder 交絡**（edges=build_step10、cooc=sim_matrix の build_cid_vector、run-end でも membership 0.97/5 しか重ならない）＝「再描画でない」の負相関は builder 差込み。一方 **A/B/C（Main↔ctrlA/ctrlB/rare↔common）は全て build_step10 内で交絡なし＝核心（Rfam≈均等≈shuffle、C 疎で退化）は保持**。ctrlB shuffle は per-(event,path) 内で正しい（m29 監査D）。

## 0. 一文（観察事実）

target の使い方を「均等」から「event 後の drift で重み付け／選別」に替え（辺ロジック不変）、対照 A（均等）/B（drift を target 間 shuffle）込みで 24 seed 形成（物理ゼロ）。drift 量は **C（v1 指示、|Δ|>0 が 1% と疎）** と **Rfam（Code A 追加、69% と密、v108 整合）**。GATE 観察: **Rfam は Main≈ctrlA(均等,0.93-0.97)≈ctrlB(shuffle,0.94-0.97)＝drift 重み付けが均等とも shuffle とも区別されない**。**C は ctrlA と離れる(0.22-0.30)が網が退化(131-200 対/18-22 node)・shuffle 対照(B)が seed 間で不一致(0.61/0.87/0.89)**。判定は Taka。

---

## 1. 実装（STEP3 から変えた一点 + data が正した2点）

- **変えた一点**: event の実 target を均等に使うのをやめ、`edge_weight = (wi×wj) × d_norm(e,c)`、`d_norm = max(|delta| − baseline_med, 0)`、`d_norm=0` は drop。辺ロジック（cross-CID・time-local top5・(path×channel×n_core×window)層別・i≠j・無向）は STEP3 不変。
- **data が正した2点（報告明記）**:
  - **D4 baseline**: 設計の per-(event,path) は不可（hop=−1 の path は baseline 種別 `unrelated_baseline` 等 5 種で実 path と別＝(event,path) 0% 重複）。hop=−1 は同 event_id を全共有 → baseline_med を **per-event_id** で引くよう補正。
  - **D2 疎性**: `delta_C_medium`（v1 指示）は |Δ|>0 が **1%**（疎）。`delta_R_familiarity_medium` は **69%**（密）。→ **v1 は C のまま（勝手に変えない）**、密な Rfam を **Code A 追加の secondary**（ラベル明示、判定は Taka）として併産。
- **対照**: A=均等（STEP3 そのもの）、B=d_norm を同 (event,path) 内で target 間 shuffle。
- 24 seed: ctrlA ~2,400 対 / C main ~130-210 対(1% moved) / Rfam main ~2,200-2,400 対(69-74% moved)。

## 2. GATE 観察（判定しない。量= C(v1) / Rfam(Code A 追加)。seed0/1/2）

| 量 | A: Main↔ctrlA(均等) | B: Main↔ctrlB(shuffle) | C: rare↔common | E: ↔共起 | main 対数 |
|---|---|---|---|---|---|
| **C** s0/s1/s2 | 0.22 / 0.28 / 0.30 | 0.61 / 0.89 / 0.87 | 0.60 / 0.89 / 0.84 | −0.73〜−0.81 | 131 / 182 / 200 |
| **Rfam** s0/s1/s2 | 0.93 / 0.94 / 0.97 | 0.94 / 0.95 / 0.97 | 0.90 / 0.88 / 0.87 | −0.22 | 2297 / 2369 / 2169 |

（参考: STEP2 静的 rare↔common 0.96 / STEP3 time-local 0.925。Main 新規対は両量とも 0%＝ctrlA の部分集合。）

### 観察事実（各項、判定しない）
- **A（drift で結ぶ atom が変わるか）**: **Rfam は ctrlA とほぼ同じ（0.93-0.97）**＝drift 重み付けしても均等と同じ網。**C は ctrlA と離れる（0.22-0.30）**＝C-drift は別の小部分集合を選ぶ。
- **B（特定 target の drift が効くか＝Main vs shuffle）**: **Rfam は Main≈shuffle（0.94-0.97）**＝どの target が動いたかは効かず、drift 分布だけが効く（69% が動くので重みがほぼ一様）。**C は seed 間で不一致（0.61/0.89/0.87）**＝特定 target 効果が安定しない。
- **C（rare↔common）**: **C は下がる（0.96→0.60-0.89）**が、Taka 留保「下げ幅だけでは何も言えない＝対照差が要る」に照らすと、C の B 対照（shuffle）が不一致なので「event が形作った」とは言えない。**Rfam は下がらない（0.87-0.90, ≒STEP3）**。
- **D（センター拾う基準=時間集中）**: C の Main は maxwin_share=1.000（各対が 1 窓に集中）だが**これは C が疎すぎて各対が 1 回しか出ないため**（spike でなく退化）。Rfam は 0.50（ctrlA 0.42 よりやや集中）。
- **E（再描画/幅/whiteout）**: 両量とも sim_matrix 共起と**負相関**（C −0.7〜−0.8 / Rfam −0.22）＝静的共起の再描画でない。C は層数 4-6・node 18-22（退化）、Rfam は層数 23-28・node 78-85。

## 3. 留保（報告に明記）
- **C の疎性で退化**: C は 1% しか動かず Main が 131-200 対・18-22 node＝GATE の結論（A 低・rare↔common 低）は退化に強く依存し、信頼できない。
- **Rfam は密すぎて一様化**: 69% が動くため drift 重みがほぼ flat＝均等(ctrlA)とも shuffle(ctrlB)とも区別されない（A・B とも 0.93+）。
- **窓遅延＝因果候補**: drift は event 後 1000step の target 状態変化で、*この* event 由来とは限らない（v107 自身が候補扱い）。「event が辺を形作った」とは書かない＝「event 後に動いた target で辺を重み付けた」。
- **solo 状態**: delta は target 単独の状態、pairwise でない。
- **support escape しない**: atom 候補の台は sim_matrix top-5 のまま、新 atom は持ち込めない。
- **baseline 補正**: per-event_id（per-event×path は data 上不可）。
- **Rfam は Code A 追加**: v1 指示は C。Rfam は密性のための追加で、採否・D2 の最終決定は Taka。

## 4. やらなかったこと（明示）
CID 投影・low-dim 埋め込み・GATE を超える effect_size・cid pool 確定・Taka 案（CID 自身の 326次元一致率 spike 直接ルート）は**していない**。

## 5. 一方向保証
読む=frozen（baselines_with_delta / relation_paths / source_events / v105 diag logs / atom_profiles_cache）、書く=`timelocal_delta/` のみ。grep: physics/inject/ledger 書込 **0 件**（build・GATE 両方）。

**出力の扱い**: 283M。code+gate+coverage+report+**seed0 サンプル（全版: ctrlA/main_C/main_Rfam/ctrlB/common）** のみ commit、seed1-23 はローカル+再生成可（`m24` 再 run ~13分）。

---

*以上 STEP 4 drift（Code A、2026-06-16）。drift 重み付け+対照A/B。GATE: Rfam(密) は Main≈均等≈shuffle(0.93+)=drift が区別を生まない、C(疎v1) は均等と離れる(0.22-0.30)が網退化(131-200対)+shuffle対照不一致(0.61/0.89/0.87)で特定target効果不安定。rare↔common は C で下がる(0.96→0.6-0.89)が対照差が伴わない。両量とも静的共起と負相関(再描画でない)。留保: C疎性退化/Rfam一様化/窓遅延=因果候補/solo状態/Rfam は Code A追加。判定は Taka。*
