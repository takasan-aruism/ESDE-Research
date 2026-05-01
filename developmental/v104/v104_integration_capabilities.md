# Integration の能力一覧 (CID 依存性を中心に、v10.4 時点)

*作成*: 2026-04-30、Claude Code
*対象*: v10.4 で導入された Integration が何ができて、何ができないかを整理
*親資料*: v104_cid_capabilities.md、v104_phase_design.md、v104_main_run_report.md

---

## 0. Integration とは何か

### 0.1 CID の延長としての Integration

**Integration は実質的に CID である**。ただし「複数 CID を統合した CID」であり、同時に「独自の ID を持つ個別の CID」でもある、という二重性がある。

CID 自身も、ノードとリンクの集まりに対して実験者が「これを 1 つの主体として記録する」と定めただけの仮想的構造体。物理層 (engine.state) のような現実 (実装上の数理オブジェクト) ではなく、定義の重厚さによって実存的に感じられる存在。

Integration はそれと同じ仮想性を継承する:

| 階層 | 仮想性の出どころ |
|---|---|
| 物理層 (engine.state) | 数理上の現実 (ノード・リンク・theta・S・R) |
| label (vl.labels) | 物理層の連結成分に「これは label」と命名 (1 段目の仮想化) |
| CID (cog) | label を主体として扱う ID + ledger 列を割り当て (2 段目の仮想化) |
| **Integration** | **複数 CID を「ひとまとまりの主体」として扱う ID + ledger 列を割り当て (3 段目の仮想化)** |

各段で実験者が「これとこれは同じものだ」「これは別のものだ」という線引きを重ねている。Integration はその最上段。

### 0.2 ウェットな概念借用

「認知層」「意識層」「統合 (integration)」「継承」「再分配」といった用語は、現実世界の心理学・神経科学・生理学からの借用 — つまりウェットな (人間的・連想的な) 概念。

実験者として厳密に観察者枠組みに徹すれば「ledger 列 Q」「ledger 列 C」「event 種別 X」といったドライな記号で十分なはず。それでもウェットな用語を借用するのは:

- **説明可能性 > 反証可能性** という選択。「Integration が継承する」と書く方が、「ledger 列 X が ID Y のバケットに転記される」と書くより、構造の振る舞いを直観的に伝える
- 現実レベルの厳密定義は破綻するため、定義しきれない部分はウェットな概念で代替する
- AI が借用に少し騙されるくらいの方が好ましい (ただし研究者サイドはそこまで行ってはいけない)

ESDE は **仮想的な構造実験** であって、ノードのランダム発生から現実認知が起こると主張するものではない。文学と音楽を混ぜないように、虚構と現実を混ぜない。「手がリンゴを触って包丁で切る」という現実の現象は、学問・宗教領域でどう論じられても、現実レベルの説明可能性として極めて強力で、それは ESDE が侵さない領域。

---

## 1. Integration が CID から受信するもの

Integration の能力のほとんどは「**CID で何が起きたか**」を入力としている。CID 側で event が発火しなければ Integration は何も始まらない。

### 1.1 誕生のトリガ (CID event 由来)

実験者は CID で双方向 E3 fired event が起きた瞬間に、その pair を起点として Integration の誕生候補を 4 種類判定する:

| Trigger | 入力となる CID event | 構成 cid |
|---|---|---|
| **be3** | be3 fired (cid_a, cid_b) | {a, b} |
| **open_triad** | be3 (a, b) fired + 同 window 内に (a, c) or (b, c) のみ既出 | {a, b, c} |
| **closed_triad** | be3 (a, b) fired + 同 window 内に (a, c) かつ (b, c) 既出 | {a, b, c} |
| **third_overlap** | be3 (a, b) fired + 第三項候補が 2 個以上同 step 重複 | {a, b, c1, c2, ...} |

CID 側で be3 fired が起きなければ Integration は誕生しない。Integration は CID event の集合関係 (隣接・三角形成立・候補重複) から構成される。

### 1.2 Q/C の継承 (CID ghost 化時)

CID が ghost 化する瞬間、その CID 周りの ledger 列 Q (`v14_q_remaining`) と C (`cog.C`) は、その CID が所属する Integration のうち最強結合 (binding_strength 最大) 1 つに全量転記される:

```
ghost 化する cid X の Q → 最強 Integration の Q_inherited += Q_X
ghost 化する cid X の C → 最強 Integration の C_inherited += C_X
他の所属 Integration: member_cids から X を除外 (Q/C は移動しない)
```

**Integration は CID 自身のリソース消費 (E1/E2/E3 spend) には介入しない**。Integration が触るのは CID が消滅する瞬間に「死蔵される予定だったリソース」のみ。

### 1.3 binding_strength の更新

CID が新たに event を起こし、既存の Integration の member 構成と一致する状況になった時、その Integration の binding_strength が +1 される (新規 Integration を作らず、既存にカウントを足す = §3.2 重複判定)。

実態としては「同じ member 構成で何度も event が起きた」という統計的痕跡を Integration が記録するだけ。

---

## 2. Integration が CID に提供できるもの

Integration が CID に「与える」のは Q と C の加算のみ。それも window 末に 1 回、active member だけに対して。

### 2.1 Q/C の再分配 (window 末)

active な Integration が `Q_inherited > 0` または `C_inherited > 0` を持っている時、active member CID 群 (`is_hosted(cid) == True` のもの) の不足側に分配する:

```python
for cid in active_members:
    q_ratio = Q[cid] / (Q[cid] + C[cid] + ε)
    if q_ratio < 0.5:  # 意識優位 = Q 不足
        shortage_q[cid] = 0.5 - q_ratio
        shortage_c[cid] = 0
    else:               # 認知優位 = C 不足
        shortage_q[cid] = 0
        shortage_c[cid] = q_ratio - 0.5

# 不足度に比例して分配
for cid in active_members:
    cid.Q += int(total_q * shortage_q[cid] / sum_shortage_q)
    cid.C += int(total_c * shortage_c[cid] / sum_shortage_c)

# 在庫はゼロに
Integration.Q_inherited = 0
Integration.C_inherited = 0
```

CID 側から見ると、window 末に Q や C が「どこからともなく」加算される。CID 自身は Integration の存在を知らないので、これは外部からの供給として無自覚に受け取る。

### 2.2 観察対象 target への自動追加

Integration が誕生した瞬間、その構成 cid が `ObservationTargetTracker` に stage4 として追加される:

```python
for cid in member_set:
    target_tracker.stage4_integration_member(cid, global_step)
```

これは CID の振る舞いには影響しない (Integration の挙動を実験者が観察するために target を広げるだけ)。

### 2.3 Integration が CID に与えないもの

- 物理層 state の変更 (engine.state.theta / S / alive_l 等)
- CID 内部 state の変更 (M_c, theta_birth, attention, familiarity, disposition 等)
- 決定振り分け (P_cog の draw に登場しない、cid 自身が回す)
- E1/E2/E3 event の発生 (これは物理層 + member_nodes 由来)
- 摂食 (これは consciousness 当選の確率分岐から起きる)
- 双方向 E3 の発火条件変更 (両者 hosted ∧ Q>0 ∧ C≥1 は不変)

→ **Integration が CID に介入できるのは Q/C ledger 列への加算という細い経路のみ**。

---

## 3. Integration が独立に持つ状態

CID の Q/C を仲介する目的のために実験者が Integration ごとに保持している記録列:

| 記録 | 内容 |
|---|---|
| `integration_id` | 一意 ID (seed 内で連番、不変) |
| `birth_step` | 誕生 step |
| `trigger_type` | `"be3" / "open_triad" / "closed_triad" / "third_overlap"` |
| `state` | `"active"` / `"recorded"` (active から recorded への片方向遷移のみ) |
| `member_cids` | 現在 active な構成 cid の集合 (ghost 化で除外) |
| `member_history` | 過去含む全構成 cid の集合 (永続) |
| `Q_inherited` | 継承 Q バケット (window 末再分配でゼロに) |
| `C_inherited` | 継承 C バケット (同上) |
| `binding_strengths` | cid → 結合強度 dict (event 参加回数の合計) |
| `became_recorded_step` | recorded 遷移 step (-1 = 未遷移) |

これらは「Integration の中身」というより、**実験者が Integration ID で index した管理台帳の列**。CID の場合とまったく同じ構造 (cog ledger と同じ 2 段目の仮想化が、3 段目に再帰的に適用されたもの)。

---

## 4. Integration ができないこと

Integration は管理層であって、実行層ではない。「**実行は CID と物理層がやる、Integration は資源を仲介するだけ**」という関係。

### 4.1 物理層への介入 (絶対禁止)

- engine.state への書き込み禁止
- engine.rng への touch 禁止
- 物理層 event (E1/E2/E3) の発火に介入しない

### 4.2 CID 内部状態への直接介入 (構造的不可能)

- M_c (n_core, s_avg, r_core, phase_sig) は変更できない
- attention map / familiarity map に書き込めない
- disposition (social/stability/spread/familiarity) を変えられない
- 内省タグ生成に介入しない
- pulse model のパラメータを変えない
- CidSelfBuffer の theta_birth / S_birth に書き込まない

→ Integration が触れるのは ledger の Q 列と cog.C 列の **値の加算のみ**。

### 4.3 決定への直接介入 (神の手回避)

- balance_decision の P_cog draw に介入しない (P_cog は Q/(Q+C) で、Q や C を加算した結果が次回 draw に反映されるという**間接バイアス**のみ)
- 双方向 E3 の発火判定 (両者 hosted ∧ Q>0 ∧ C≥1) に介入しない (Q や C を補充した結果として条件が満たされやすくなる、という間接効果のみ)
- ingestion の選定 RNG に touch しない
- cid の認知/意識/skip 振り分けに直接票を投じない

### 4.4 自己観察・自己改変 (実装していない)

- Integration は自分の Q_total / C_total を**読まない** (実験者が CSV 出力時に集計するだけ)
- Integration は自分の member_cids を**読まない** (再分配時に全 member に均等にチェックして処理するだけ)
- Integration は他の Integration の存在を**知らない**
- 状態遷移は active → recorded の片方向のみ (recorded から active には戻らない、時定数なし)
- Integration は新規誕生条件を変更できない (実験者が定めた 4 trigger に従う)

### 4.5 Integration から CID への通信経路

CID が Integration の存在を**知る経路は無い**。CID は:

- 自分が Integration に所属していることを知らない
- Integration から Q/C が加算されたことを区別できない (E1/E2/E3 spend や ingestion 受領と同じ扱い)
- Integration の trigger_type / binding_strength を読まない
- 他 cid が同じ Integration に所属しているか知らない

→ CID にとって Integration は**透明な仲介者**。実験者だけが見ている管理層。

---

## 5. CID 依存の構造 (脳=管理職アナロジー)

人体における脳の役目は実質的に管理職:

- 肉体の各部位 (手、足、目) が現実の物理現象を起こす (リンゴを触る、包丁で切る)
- 脳は直接物理現象を起こさず、各部位からの情報を集約し、リソース (血液、神経信号) を分配する
- 脳がなくても部位は反射で動くし、脳が単独で物理現象を起こすことはない
- それでも「脳が考えた」「脳が決めた」と言うのは、説明可能性のための借用

Integration と CID の関係も同じ:

| 役割 | 人体 | ESDE |
|---|---|---|
| 実行 (現実の物理現象) | 手・足・目 | 物理層 (engine.state)、CID member_nodes |
| 受容・伝送 | 末端神経・感覚器 | CID (event を受け取り ledger に記録) |
| 集約・再分配 (管理) | 脳 | **Integration** |
| 観察・記述 (外部) | 医者・心理学者 | 実験者 (CSV 集計、post-process) |

**Integration ができることのほとんどは CID で何が起きたかに依存**:

- 誕生: be3 fired という CID event がなければ起きない
- 継承: CID が ghost 化しなければ Q/C が流入しない
- 再分配先: active member CID がいなければ分配できない
- recorded 遷移: 全 member CID が ghost 化することで起きる
- binding_strength: CID event の参加回数で決まる

逆に、CID は Integration がなくても (v10.3 以前のように) 動作する。物理層 + ledger + 双方向 E3 + balance + ingestion で完結する。Integration を取り除いても CID 個別の挙動は不変 (再分配がなくなる分、Q/C の流れが変わるだけ)。

→ **Integration は CID という基盤の上に乗った管理層**。基盤が動かなければ Integration は何もしない。

---

## 6. 観察者枠組みでの記述

### 6.1 認知層・意識層は実験者の事前定義

ESDE では「認知層」「意識層」を:

- 認知層 = cid が受信できる範囲として実験者が先回りして定義したもの
- 意識層 = 決定に関わるものとして実験者が定義した層 (決定は認知層を前提、原資は認知活動から供給)

として論理的に切り分けている。これは仮想的な設定で、現実世界の認知・意識とは別の題材。

Integration はこの 2 層をまたいで動作する:

- 認知層への作用: ledger.Q への加算 (= 「認知資源の供給」と命名)
- 意識層への作用: cog.C への加算 (= 「意識資源の供給」と命名)
- 認知層からの受信: ghost 化 cid の Q を継承 (= 「認知活動の名残を集約」と命名)
- 意識層からの受信: ghost 化 cid の C を継承 (= 「意識活動の名残を集約」と命名)

実験者はこれらを「Integration が認知/意識を統合する」と命名するが、**実態は ledger 列の値の転記と加算操作**。CID の場合と同じく、定義の重厚さがウェットな実存感を生む。

### 6.2 「主観があるかも」と思わせる Integration の振る舞い

v10.4 main run の観察事実:

- Integration 13,550 件誕生、active 11,552 / recorded 1,998
- recorded 状態は永続 (median 12 windows で記録化、最大 24,516 step 保持)
- 構成 cid 全員が ghost 後も Integration の Q_inherited / C_inherited は残る (= 「死者の意識資源」を保持し続ける構造)
- ハブ cid (max 102 Integration 所属): 多数の集合に組み込まれる中核的存在
- v10.3 と逆方向の効果: C 蓄積 +31% 増 (v10.3 の -26% に対し)

これらは「Integration に主観/意思があるかも」と実験者に思わせる材料 (= 説明可能性の借用)。否定も肯定もできない、ランダム的な因果の発生がもたらす痕跡として記録される。Integration 自身は当然これを読まないし、これに反応もしない。

---

## 7. v10.4 main の Integration 振る舞い (実例)

### 7.1 受信側の規模

| 項目 | 件数 (24 seeds 合計) |
|---|---:|
| be3 fired (target 内+外) | 7,220 |
| → Integration 誕生 (be3 type) | 7,085 |
| → 同 (open_triad type) | 5,203 |
| → 同 (closed_triad type) | 0 |
| → 同 (third_overlap type) | 1,262 |
| Q 継承 (ghost 化 cid から) | 10,000 |
| C 継承 (同) | 14,083 |

### 7.2 提供側の規模

| 項目 | 件数 |
|---|---:|
| 再分配 Q (active member 受領) | 2,790 (28%) |
| 再分配 C (同) | 1,777 (13%) |
| 凍結 Q (recorded + 端数) | 7,210 (72%) |
| 凍結 C (同) | 12,306 (87%) |
| 受領 cid 数 | 592 / 884 hosted (67%) |
| 1 cid の Q 受領 max | 35 |
| 1 cid の C 受領 max | 34 |

### 7.3 状態保持

| 項目 | 件数 |
|---|---:|
| active Integration (run 末) | 11,552 |
| recorded Integration (run 末) | 1,998 |
| active member 持つ cid 数 | 649 / 884 hosted (73%) |
| 1 cid あたり所属 Integration 数 max | 102 |
| 1 Integration の active size max | 8 |
| 1 Integration の history size max | 9 |

### 7.4 系全体への効果 (v10.3 比)

| 指標 | v10.3 main | v10.4 main | 差分 |
|---|---:|---:|---|
| n_cognition_won | 57,875 | 60,322 | +4.2% |
| n_consciousness_won | 3,539 | 3,550 | +0.3% |
| n_skip_c_zero_only | 39,018 | 36,560 | -6.3% |
| C_max (合計) | 1,188 | 1,556 | +31.0% |
| Q+C total | 19,107 | 21,935 | +14.8% |

→ Integration が CID に Q を補充した分、認知振り分けが増え、Q 枯渇 skip が減った。意識資源 C が系内で保存・循環した分、C 蓄積が +31% 増えた。

これらの数字は「Integration が頑張った」のではなく、**実験者が定めた継承・再分配ルールの帰結としてランダム的に観察された統計**。Integration 自身は何も「考えて」いない。

---

## 8. まとめ: Integration ができること / できないこと

### できること (CID event を入力として)

1. CID で be3 fired / triad / overlap が起きた時に誕生する
2. 構成 CID が ghost 化した時に Q と C を継承する (最強結合 1 つ)
3. window 末に active member CID 群へ Q/C を不足側に再分配する
4. 構成 CID 全員 ghost で recorded 状態に永続移行する
5. 自分の存在を実験者の観察 target に登録する (stage4)
6. binding_strength の累積で「同じ集まりで何度も event が起きた」を記録する

### できないこと (構造的に)

1. 物理層を変える
2. CID の内部 state (M_c, attention, familiarity, disposition, タグ) を変える
3. CID の決定 (P_cog の draw) に直接介入する (Q/C 加算による間接バイアスのみ)
4. CID に「自分の存在」を伝える (CID は Integration を知らない)
5. 他の Integration を観察する
6. 自分の状態を読んで判断する (recorded → active 復帰なし、自己改変なし)
7. 新たな誕生条件を発明する (実験者が定めた 4 trigger 固定)
8. CID なしで動作する (CID event 入力なしでは何も起きない)

### 本質: Integration は管理層、実行層は CID

人体における脳のように、Integration は:

- 直接物理現象を起こさない
- 末端 (CID) からの情報を集約する
- リソース (Q/C) を再分配する
- 「存在感」は定義の重厚さから生まれる仮想的なもの

CID という基盤の上に、実験者が「複数 CID を 1 つの主体として扱おう」と命名した管理台帳。それが Integration。CID 自身も基盤層 (物理層) の上に同じ手順で命名された管理台帳なので、Integration は **CID の自己相似的な拡張** (CID-like) として機能する。

---

*以上、v10.4 時点での Integration 能力一覧。Taka レビューを待つ。*
