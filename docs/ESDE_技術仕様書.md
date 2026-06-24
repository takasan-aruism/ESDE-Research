# ESDE 技術仕様書（Genesis 系・現行）

*版*: 1.1（2026-06-18 作成、Code A / 2026-06-25 フロンティア網羅追記、Claude Code）
*出典*: `docs/ai_summaries/`（00_index 〜 11、約14,000行）を一本化。詳細数値は各原典（`docs/ESDE_*_Report.md` / `primitive/v9XX/*.md` / `developmental/v10X/*.md` / `unified/v1NNN/*.md`）に遡れる。
*対象範囲*: 現役の **Genesis 系**（物理層→cid→α/β が emergent する「上昇」アプローチ）。Language 系（326 Atoms×48軸、2026-03 凍結）は §10 に substrate として収録。
*射程の時点*: 認知層 v9.18 / Developmental v10.0–v10.13a / Unified v1100–v1114（注意センター Step1 確立, 2026-06-05）+ フロンティア v12 Atomset（v1201）・v13 child-world（v1301/v1302、2026-06-23）+ v1303 設計（§17）。

---

## 0. この文書について

### 0.1 目的
ESDE が「何が・何を・どう行っているか」を**一本の線**として記録した正式な技術仕様書。過去の全試験を寄せ集めると数多の情報で混乱するため、現役 Genesis 系を芯に、機構・データ構造・パラメータ・ファイル所在を一箇所に集約する。「あれがない・これがない」を避けるための完結した reference。

### 0.2 観察者枠組み（この文書全体を貫く前提・必読）
ESDE は**虚構の構造実験**であり、現実の人間の認知・意識とは混ぜない（「文学と音楽を混ぜない」）。本書で「認知層」「意識層」「CID」「Q」「C」と書くものは、**cid が持つ内部状態ではなく、実験者が cid の周りに記録している量・観測事象に付けた命名**である。したがって本書は一貫して:

- cid を主語に擬人化しない（「cid が見る/感じる/選ぶ/意識する」と書かない）。
- 「実験者が記録する量」「cid の挙動が観察される」「Q と名付けた ledger 列」と書く。
- 効果は設計上「統計的にわずか」であり、**神の手（god's hand）ではない**。

### 0.3 現行 / 凍結 / 廃止の区別（先に明示）
- **現役 (LIVE)**: 物理層 `ecology/engine/` + エンジン `autonomy/v82` + 存在層 `primitive/v910` + 認知層 entrypoint `primitive/v918/v918_memory_readout.py` + 後処理 `developmental/v107+` + 注意センター `unified/v1114` + フロンティア `unified/v1201`（v12 Atomset / 一致率）・`unified/v1301`・`unified/v1302`（v13 child-world、最新、§17）。
- **凍結 (FROZEN)**: Language 系（`language/`、2026-03 凍結）。ただし atom profile の供給源として現役後処理に接続（§10）。
- **廃止 (DEPRECATED, コードは残すが再実装しない)**: `autonomy/v90` 旧 VirtualLayer、`S≥0.20` 閾値、path B、torque_factor（v9.7 認知→θ介入）、stress_decay、「loop collapse」方向、v1110–v1113 の「異系対応」枠組み（§15）。

---

## 1. ESDE とは何か

### 1.1 一文定義
ESDE は「**構造が、なにもないところから自分で立ち上がりうるか**」を完全な答えとして示そうとする数学的実験系。その法則形が **Aruism**、その数学的展開が **ESDE**。

### 1.2 Aruism（構造が先、意味が後）
反復過程 **定義 → 反転 → 非対称 → 連動 → 階層 → 命名 → 次の定義** そのものを「存在」と呼ぶ。帰結する運用原則:
- **存在の対称性/対等性**: 存在 A が B を認識するなら B も同時に A を認識する。一方向の認識は Aruism 違反（→ E3 が「双方向 2 単位消費」である根拠）。
- **ある / ない / 本当のない**: 「ある」が最も根源の前提、「ない」は「ある」の上に立つ存在の一形態、「本当のない」は不可知。ESDE は「他者がいない/接触がない」も存在の一形態として記録しうる。
- **誤りの価値の反転**: 「間違って作られたもの」も役割を持ちうる。不利な機構も削除せず休眠保持する根拠（§15）。

### 1.3 2 系統
| 系統 | テーマ | 方向 | 状態 |
|---|---|---|---|
| **Genesis 系**（本書） | 物理層 → cid → α/β-Integration、4層+Layer5 | 物理から認知が emergent する「上昇」 | **現役** |
| **Language 系**（§10） | Atom / Synapse / Lexicon v2 / Phase 7-10 | テキスト → 意味座標への「下降」 | **2026-03 凍結** |
- 両系の中間言語が **Atom**（326 個 × 48 軸）。Genesis 側が作る cid 48 次元ベクトルと Language 側の atom 48 次元 profile を同レイアウトで cosine 比較できる（§10.3）。

### 1.4 当面の目標 ―「会話できる ESDE」
最終目標ではないが、現フェーズの上位目的は「**ひとまず会話できる ESDE**」。定義は「自然文を吐く LLM」ではなく、**応答の方向を作る主体が ESDE 側にある**こと:
```
人間入力 → ESDE 内部入力化 → Genesis 側で揺れ・注意・応答構造が発生
  → 応答 Atom 候補分布を生成 → Language/Lexicon/LLM プロキシで自然文化
  → 人間へ返答 → 次入力で再び ESDE へ（ループ）
```
LLM が主応答を作り ESDE が事後説明に堕ちる構成は目標からの逸脱。監査の第一基準は「この実験/設計/実装は会話できる ESDE に近づくか」（§11.7）。

### 1.5 観察者枠組みの精緻化（§0.2 の根拠）
- **認知層** = 実験者が先回りして定義した「cid が受信できるものの範囲」。定義できないことはやらない。
- **意識層** = 実験者が「決定に関わる」と定義した層。決定は認知層を前提に発生し、意識層の原資は認知活動がもたらす（Q→C 転化）。
- これは**論理学的な構造定義**（仮想的設定）であって、現実の認知・意識ではない。AI は借用語に多少騙されてよいが、**実験者は決して騙されてはならない**（実体は「ledger 列の値の転記」）。

### 1.6 目的の現在の言語化 ―「存在＝同期」（2026-06 セッション）
§1.4「会話できる ESDE」の上位にある、目的そのものの言語化。判定でなく研究者（Taka）の枠組みの保存（出典 `docs/ai_summaries/esde_direction_memo_existence_sync.md`、`docs/仕様書/v1303_phase_design.md`）。
- **存在＝多くの系の同期**: ある存在を扱う際に**同期する系が多いほど、私たちはそれは存在する、と感覚的に理解する**（原文趣旨）。幼児が「りんご」を視覚・触覚・温度・音・発話の多系の重なりで覚えるように、一致率（§10.3）は ESDE が外部構造と**何系で同期するか**の測定。**多次元＝存在らしさ**。
- **一致率 0.5-0.6 頭打ちの解釈**: 同期できる系が言語 1 本だから。物理条件を ESDE の射程に加える＝同期できる系を増やす＝頭打ちを破る筋（「言語で詰まったから物理に逃げる」ではなく、存在＝多系の同期だから系を増やすのが本筋という論理的帰結）。
- **CID＝偏り検出器**: 「親子」は比喩で、本質は「**通常 ESDE と異なる系を自動で作り出す仕組み**」（§17.3-17.5）。親 CID の偏りを拾う＝方向を持った ESDE の進化（ただのランダムでない）。
- **直接アクセス全滅＝因果律の自然な防衛＝堅牢性**: 外部から物理を直接書く経路は全滅した（§17.4 v1302 #CW1-4）。だから「**系自身が条件を決める**仕組み」を作る＝**神の手の逆**。
- **AI 過去案（足す）vs 構想（取り出す）**: AI 案は「ESDE に何かを足す」（Atom 取込・K_sync 接続・topology 移植）で全て弾かれた。構想は「ESDE から何かを取り出す」（多様性を生む物理条件を系自身に探させる／read-back）＝ESDE が自然にやる方向に乗る。名付けは後から来る（自然現象が出来上がって人間が名付ける、アベコベでない）。

---

## 2. アーキテクチャ（層モデル）

### 2.1 層の一覧
上位層は下位層を操作しない。同じ frozenset（「魂」）が、経験の差で別の個性を生む。

| 層 | 比喩 | 実体／エンティティ | 実験者が記録する量 | 介入規律 |
|---|---|---|---|---|
| **物理層 (Layer 1)** | 波 | nodes / links / 位相 θ（動的平衡）。`engine.state` (GenesisState) | θ・S・R 分布、node 共鳴 R_ij | 上位から介入を**受けない**（frozen） |
| **存在層 (Layer 2)** | 粒子 | label（「魂」）= frozenset + phase_sig。cid もここに棲む | member_nodes（固定）、share | 物理層へ **torque（微小）のみ**。frozenset は解放しない |
| **認知層 (Layer 3)** | 過程 | 波と粒子の間の過程。CidSelfBuffer、Q | φ・attention・familiarity・B_Gen・M_c・capture・disposition | **観察のみ・介入なし**。存在層への効果は統計的にわずか |
| **意識層 (Layer 4)** | ― | 認知層を検証する層。資源 C | C（conscious_layer） | 物理/存在/認知層に介入しない。認知の穴を埋める |
| **Layer 5: Integration** | 統合 | cid 集合の仮想化。α=観察軸 / β=会計単位 | 集約 Q/C、IID 所属 | 認知/意識層に bias、物理層には介入しない（「国家は地震を防げない」） |
| (Layer 6: SEED 統合) | ― | 未実装・将来 | ― | ― |

### 2.2 介入規律（一方向）
```
物理層 ←(θ torque, 微小・M≈0.993)― 存在層 ―(観察のみ)→ 認知層 ―(認知のみ)→ 意識層
```
**物理層に書き込むのは存在層の torque だけ**。認知層・意識層・Integration・後処理はすべて物理層に対し read-only。この一方向性は **bit-identity 5 段連続（v9.15→…→v9.18, 5,224 cid で max abs diff 0.0）** で構造的に実証済（§11.1）。

### 2.3 エネルギー保存的結合（Q→C）
```
物理層 (5 力, θ空間)
  └ 確率的イベント (label 化は約7%, 93%は未使用原資)
存在層 (label/cid) ── 認知への橋
認知層 (Q 消費, 見たものをそのまま理解, 時間とともに劣化)
   ↓ Q を 1 消費 → 意識層が 1 獲得（エネルギー保存的; Q は消えず意識の原資になる）
意識層 (認知の穴を埋め, 後から育つ) ⇒ (認知 + 意識が一つの仕事 = 統合)
```
- **エネルギー概念は認知層以上にのみ存在**。物理層・存在層に Q/C はない。摂食・消費は認知層特異の現象。

### 2.4 同型反復の系譜（仮想化の繰り返し）
```
ノード →(link)→ 閉路 →(共鳴)→ 持続構造(Genesis) →(phase_sig)→ label(Autonomy)
      →(経験)→ cid(Primitive v9.8) →(E3)→ α-Integration(v10.4) →(α集合の意図的統合)→ β-Integration(v10.5)
      →(将来)→ SEED 統合(Layer 6)
```

### 2.5 死の二階層
| 階層 | 条件 | 状態 |
|---|---|---|
| 存在層の死 | label 死（detach） | **ghost** 化（「魂が抜けた容器」） |
| 認知層の死 | 残 Q = 0 | ghost 消滅 |
- ghost は原資（Q）を持つ限り残る。固定 TTL（`GHOST_TTL=10` windows）は **v10.1 で撤廃**（神の手回避）し、Q ベースの死に置換。ghost = **不均一な資源地形**（「石油」）で、残 Q は死前の活動量を反映。

---

## 3. 物理層 (Layer 1: Physics) ― frozen

ecology/engine/ の凍結コア。N=5000 ノードが 71×71 トーラス上（4近傍）で動的平衡を保つ。**二重トポロジ**（トーラス格子 + 長距離ランダム link、平均 link ≈2700、ρ≈0.022%、平均次数 ≈1.1）であり「局所格子ダイナミクス」と単純化してはならない。

### 3.1 GenesisState（状態変数）
| 変数 | スコープ | 意味 | 範囲 |
|---|---|---|---|
| θ[i] | node | 位相 | [0,2π) |
| ω[i] | node | 固有振動数（固定） | [0.05,0.3] |
| E[i] | node | エネルギー | [0,1] |
| Z[i] | node | 化学状態 0=Dust,1=A,2=B,3=C | ― |
| F[i] | node | 肥沃度（固定地形） | 平均1.0 |
| S[k] | link | 強度 | [0,1] |
| R[k] | link | 共鳴（閉路参加数） | [0,5] |
| L[i,j] | node-pair | 潜在ポテンシャル（疎） | [0,1] |
| age_r[k] | link | 連続 R>0 step 数（v9.13） | int≥0 |
- 消滅: node E<0.007 死、link S<0.007 死。`ecology/engine/genesis_state.py`。

### 3.2 5 力 / 7 オペレータ（per-step 固定実行順）
「5 力」= **位相回転 → 流れ＋同期 → 共鳴 → 減衰 → 排他**（Genesis の確定した物理法則）。実装上は 1 step で次の固定順に評価（`genesis_physics.py` 他）:

1. **Realization（link 誕生）**: 各 alive node から 3 node サンプル。P(birth)=p_link_birth×L[i,j]。誕生で S+=0.07, L−=0.07。潜在補充 L += |N(0,1)|×0.003×F_avg（500 pair/step）。age_r=0 初期化。`realization.py`
2. **物理 Pre-Chemistry**: θ[i] += ω[i] + K_sync·Σ_j sin(θ[j]−θ[i])（K_sync=0.1）。flow_ij = 0.1·S[k]·(E[j]−E[i])·(0.5+0.5cosΔθ)。E[i] += Σflow（clamp[0,1]）。位相同期が高いほど流れが効率化。
3. **Chemistry**: 合成 A+B→C+C（S≥0.3, E≥0.26, cosΔθ≥0.7）/ 自触媒 C+A→C+C / 減衰 C→Dust（E<0.2, 放出0.17）。**3 条件（強 link・エネルギー・位相整合）が同時に揃わないと反応ゼロ**。`chemistry.py`
4. **物理 Resonance（10 step ごと）**: 長さ 3–5 の閉路探索。R[k] += Σweight（L=3→1.0, L=4→0.5, L=5→0.25）、R=min(R,5.0)。続けて age_r 更新（R>0 で +1, 否なら 0）。R_ij = link (i,j) の閉路参加数。
5. **Auto-Growth**: R>0 link のみ ΔS=min(0.03·R[k], L[i,j], 1−S[k])、S+=ΔS, L−=ΔS。閉路が link を太らせる。`autogrowth.py`
6. **Boundary Intrusion**: island（S≥0.30 連結成分）の境界 node が P(swap)=0.002/step で島内 S−δ・島外 S+δ（δ=0.02）。`intrusion.py`
7. **Decay+Exclusion**: E*=(1−0.005)。S*=(1−0.05/(1+R[k]))（**共鳴が減衰を抑制**）。排他: node ΣS>1.0 で最弱 link を kill。消滅 E<0.007 / S<0.007。
8. **背景注入（減衰後）**: 各 alive node が P=0.003 で E+0.3。成長スコアで重み付け（BIAS=0.7）。Z=0 node の 50% を A か B に分化。

> 物理の核心知見: **トポロジが熱力学に先行**（閉路＝エネルギー容器、閉路構造は開路の 2.9–7× 長寿）。位相同期は閉路内で強い（3-loop r≈0.88）。観測解像度 k\*=4 がスケール不変（N=200〜10,000）。

### 3.3 frozen パラメータ（`ecology/engine/v19g_canon.py`）
| パラメータ | 値 | パラメータ | 値 |
|---|---|---|---|
| N | 5000 | K_sync | 0.1 |
| p_link_birth | 0.007 | NODE_DECAY | 0.005 |
| latent_refresh_rate | 0.003 | link_decay_rate | 0.05 |
| latent_to_active_threshold | 0.07 | BETA(resonance) | 1.0 |
| auto_growth_rate | 0.03 | C_MAX(exclusion) | 1.0 |
| intrusion_rate | 0.002 | EXTINCTION | 0.007 |
| BIAS | 0.7 | bg_injection_prob | 0.003 |
| E_thr(chemistry) | 0.26 | exothermic_release | 0.17 |
- 減衰抑制式: `effective_decay = base / (1 + β × R_ij)`（β=BETA=1.0）。

### 3.4 公式外部注入インターフェース `physics.inject`
- `ecology/engine/genesis_physics.py:232` `physics.inject(state, target_nodes=...)`。**Genesis/Atom 系への唯一の公式書込チャネル**。
- パラメータ: inject_amount=0.6（line 53）, inject_prob=0.15（line 54）, radius=8（link 半径）。注意センターから Atom 系への書込（§8, §11.7 stage3）で使用。

### 3.5 物理層 frozen 規律
新機構は物理層を一切書き換えない。出力は新規 dir に限定し、`assert_output_under_v10X` 等でパス侵入を防ぐ。検証は **bit-identity 3 層**（§11.1）。

### 3.6 環境要因（背景摂動・node/link 層、CID 層直接は無し）
物理層期の「環境要因」は 3 機構として実体化（CID 層への直接環境要因は今も無く、link/node 経由で間接）:
- **semantic_pressure**（node 層、`cognition/semantic_injection/v4_pipeline/v43/esde_v43_engine.py:374`、pressure_prob=0.005 / latent_boost=0.05、島内部は shield）: `autonomy/v82/esde_v82_engine.py:226` で **無条件呼出＝全 run で常時稼働**（24seed main 含む）。位相帯=構造摂動の実機構で、外部入力（§10.5）・注意センターの土台。
- **stress_decay**（link 層、`esde_v82_engine.py:58`、stress_intensity = current_links/link_ema の好不況）: `stress_enabled` で ON/OFF。既定 True だが **v918 main run は OFF**（:1535）、実験（stage4 B3 / 注意センター build_center）で再点火。**廃止ではない**。
- **External Wave**（外部 energy 波、`autonomy/esde_v83_calibrate.py`、wave_amplitude/period）: autonomy v8.3 の「外部を取り込む」環境要因。現行 run 未接続の**レガシー**（amplitude=0 既定）。「外部取り込み」系譜は注意センター（physics.inject + 位相帯擦り込み）へ継承。

---

## 4. 存在層 (Layer 2: Existence) ― 旧称「仮想層」

`primitive/v910/virtual_layer_v9.py`（**現役**、kwargs 版）。`autonomy/v90/virtual_layer_v9.py` は旧版で使わない。

### 4.1 label / frozenset / phase_sig
- **label** = 存在層に棲む「魂」。`nodes` が `frozenset(cluster_nodes)`（誕生時固定、解放しない）。`phase_sig` = 誕生時の平均 θ = `atan2(Σsin θ, Σcos θ)`。`share` = 所有 link / 全 link。
- **member_nodes は凍結**。ゆえに v9.18 の coverage_ratio=1.0 は構造的帰結。phase_sig は torque の標的かつ addressing 基準でもある。

### 4.2 persistence-based birth（誕生条件、v9.13）
誕生に絶対閾値はない（神の手回避）。手順:
1. 各 link の **age_r**（連続 R>0 step 数）を追跡。
2. **age_r ≥ τ** の link のみ残す（τ ∈ {50, 100}）。
3. 残存 link の連結成分（size≥2）→ label。
4. 既存 label と 50% 以上重なる成分は除外。
- これは旧 `S≥0.20`（島閾値）と path B（R>0 pair を即 label 化）を**置換・廃止**したもの（R=0 link の「見かけ構造」混入を解消、§15）。

### 4.3 torque（唯一の物理書込）+ Feedback Loop
- torque = rigidity·share·cos(θ[n] − phase_sig)、rigidity = 1/(1+0.10·age)。θ[n] += torque·feedback_multiplier。
- Feedback Loop: turnover_ratio = EMA(died_share/total_share)、feedback_multiplier = clamp(1+0.10·(ratio−1), 0.8, 1.2)、最初の 20 window は warmup（M=1.0）。**正味の変調 M≈0.993（微小・非支配）**。
- パラメータ: feedback_gamma=0.10, feedback_clamp=[0.8,1.2], rigidity_beta=0.10, torque_order="age"（年齢順に逐次処理＝「神の設計」、同時性撹乱を避ける）。

### 4.4 share / cull（成熟・相対閾値）
- 死（cull）は相対閾値: `share < base_threshold / (1 + maturation_alpha × age)`、base_threshold = fair_share × 0.5、maturation_alpha = 0.10（年寄りほど死ににくい）。
- n_core（構成 node 数, = label/cid のサイズ）の実測分布は n=2 が約 62.6%（多数派・「普通」）、n=5 が情報豊富・長寿・hub 化しやすい。**集団平均でなく n_core 別層化で観る**（§9.5, §11.4）。

---

## 5. 認知層 (Layer 3: Cognition)

主実装は `primitive/v918/v918_memory_readout.py`（**現役 entrypoint**, v9.11→v9.18 の copy 系譜）。認知層の各機構は「実験者が cid 周りに記録する量」であり、cid 自身はこれらを使って次 step の挙動を変えない（観察のみ）。

### 5.1 CID とライフサイクル
- **cid (cognitive id)** = 観察対象の識別子（int、`CidView` dataclass で object 化）。label とは独立に発番。同じ frozenset が複数 cid を host しうる（「魂は frozenset で固定、cid は経験で異なる」）。
- 遷移: **hosted**（label 健在）→ label 死で **ghost**（cid は残る）→ 残 Q=0 で **reaped**（registry から削除）。host_lost_step / reaped_step を実験者が記録。
- **重要**: cid の「記憶」は既に物理層の中にある。欠けていたのは「記憶を作る機構」ではなく「**物理状態を記憶として読む機能**」。member node の θ 分布と member link の S/R 分布が毎 step 変わる＝「その cid がどんな世界を経験したか」の物理的痕跡。

### 5.2 pulse model（観察タイミング、v9.10）
- **pulse** = Layer A の固定観察タイミング。`cumulative_step % 50 == cid % 50`（cid ごとに分散・決定論）。PULSE_INTERVAL=50。Cold Start: 最初の 3 pulse は "unformed"、4 つ目以降 "active"。
- **MAD-DT (Mean Absolute Delta — Dynamic Threshold)**: theta = mean(|Δx|) を cid 履歴（K=20 window）から自動算出し固定閾値を置換。R(主観的驚き) = Δx_current/(theta+ε)、ε=1e-6。R>+1.0 で gain タグ、R<−1.0 で loss タグ。**固定閾値には二度と戻さない**（v9.8b の social=0.1 等は廃止）。
- 注意: pulse は disposition 更新のみを行う観察機。Q 消費は認知/意識側の責務（v10.8 訂正、Web Claude が繰り返した誤解）。

### 5.3 Cognitive Capture（v9.11）
- **B_Gen（Genesis Budget, cid 固有・誕生時固定）**: ρ=links_total/C(N,2); Pbirth=(1/C(N,n_core))·ρ^(n−1)·r_core^(n−1)·S_avg^(n−1); **B_Gen = −log10(Pbirth)**。誕生確率の桁＝「ほぼ一意のパスワード＋認知燃料」。帯: n=2→≈12, n=3→≈20, n=4→≈28, n=5→≈35, n=6-8→42-62。**B_Gen は capture に直接入れない**（M_c 経由の間接のみ。直入れすると n_core 帯が支配する／GPT 監査訂正）。
- **M_c（Memory Core, 誕生時固定 4 要素）**: (n_core, S_avg, r_core, phase_sig)。「自己定義」。次元の呪い回避のため 4 要素で固定。
- **E_t（Experience, pulse ごと抽出 4 要素）**: (n_local, s_avg_local, r_local, theta_avg_local)。
- **Δ（重み付き L1・差分分解, cosine ではない）**: Δ = 0.25·(|n_core−n_local|/86 + |S_avg−s_avg_local|/1.0 + |r_core−r_local|/1.0 + circular_diff(phase_sig, theta_avg_local)/π)。NORM_N=86, NORM_S=NORM_R=1.0, 各軸重み 0.25。Δ は i.i.d.（時間で蓄積しない／v9.12 で確認）。
- **p_capture = 0.9 · exp(−2.724 · Δ)**（Variant A）。P_MAX=0.9, λ=2.724。capture_rng=`np.random.default_rng(seed ^ 0xC0FFEE)`（engine.rng と完全分離）。

### 5.4 Q（認知資源）と E1/E2/E3 spend
- **Q** = 認知活動の燃料。Q0 = floor(B_Gen)（誕生時固定、減るのみ）。n_core=2→Q0≈11-12, =5+→≈33-34。
- **承認イベント 3 種**（core-local・物理事実のみ、拡張は要協議）:
  - **E1**（core link 死/誕: E1_death / E1_birth）
  - **E2**（core link の R が 0 境界を跨ぐ: E2_rise / E2_fall。rise=fall は対称、fall の Δ は rise の 2.8×＝崩壊の方が情報多い）
  - **E3_contact**（異なる 2 cid の member node が同一 alive link で初めて繋がる第一 step。両 cid が 1 ずつ消費＝**対称 2 単位**）。
- 各イベントで spend packet 実行: E_t 読取 → Δ 計算 → virtual_attention/familiarity 更新（減衰なし・累積のみ）→ **Q_remaining −= 1**（負にしない）。Q 枯渇後はイベントを記録するが spend しない（「実効的な死」）。
- **E3 が認知資源消費を駆動**: E3 は全イベントの 70–90%。E3 を無効化すると n=5+ でも枯渇 0%（ablation 実証）＝「ESDE は社会系」。一方向発火（ghost 相手）main tracking-50 で 77%、両方向 23%。

### 5.5 CidSelfBuffer（自己読み, v9.15）+ 観察サンプリング（v9.16）
- **CidSelfBuffer** = cid が自分の構造を独立領域に展開し、必要時に自分で読む B 領域のメモリ。engine と共有しない。誕生時固定（theta_birth, S_birth, Q0, member_nodes）+ 最新 Fetch（theta_current, S_current）+ 3 点（any_mismatch_ever, mismatch_count_total, last_mismatch_step）。
- Fetch は **イベント駆動**（E1/E2/E3 を trigger、固定 50 step は研究者視点なので廃した）。各 node を match/mismatch/missing の 3 値で判定。
- **観察サンプリング（age_factor 比例, v9.16）**: `age_factor = Q_remaining / Q0` ∈ [0,1]; `n_observed = round(n_core × age_factor)`; ハッシュ由来の独立 RNG で n_observed 個の member node を選び判定、残りは **missing**。「何であるか」= B_Gen（自己読みで不変）、「どれだけ歳か」= Q_remaining（唯一動く量）の二段認識。
- 結果（24 seed×tracking50）: node-cell match 0.00% / mismatch 23.22% / missing 76.78%; Q 枯渇 cid 34.26%。missing% は age_factor で代数的に決まる（[0,0.2)→99.27%, [0.8,1.0)→6.37%）＝観察でなく必然。

### 5.6 他者読み + 接触体（v9.17）
- **read_other_on_e3_contact**: E3 接触時、相手の **visible_ratio = other.Q_remaining/other.Q0**（＝相手の age_factor）に比例して相手の M_c 特徴（10 個）を round(10·visible_ratio) 個サンプル、残りは missing。「相手が崩れていれば、こちらが若くても読めない」。読むのは M_c 不変量のみ（state は取らない）。
- **接触体 X（v9.17）**: cid の上に立つ新存在（暫定名 X）を「**器として**」導入（状態・動学・機能なし、記録専用）。trigger は E3_contact のみ、同一性は構成 cid の frozenset。物理層を一切変えない（v5–v7 の「取り込み」失敗を回避）。
- **InteractionLog（A 側外部記録）**: E3 発火を frozenset で記録。canonical 順序 dedup（observer_cid<partner_cid）でペアあたり ≤1 行。

### 5.7 A/B 分離規律（v9.15）
- **A（研究者観察）**: Python が state を読み CSV に書く。主語＝研究者。
- **B（cid 主体）**: cid が自分の構造を独立媒体（CidSelfBuffer）に展開し自分で読む。主語＝cid。
- **四重保証**: ファイル分離（B は A を import しない）/ クラス・メソッド境界（`_a_observer_*` read-only API）/ メモリ領域分離 / 命名規約（B: `read_own_state`/`read_on_event`; A: `compute_*`/`track_*`）。B を「層」と呼ばない（A 世界と B 世界は別ドメイン）。
- **サイコロの比喩**: 研究者は「次の目は 1/6」としか言えない。サイコロ自身は「私は 1」と言える。研究者は **いつ cid が自分を読むか予測できない**ことが「研究者主観の封印」の具体的意味。**ランダム性は論理の柱で、切る方向は取らない**。

---

## 6. 意識層 (Layer 4: Consciousness) ― 機構実装は v10.2

### 6.1 C（意識資源）と Q→C 転化
- **C**（`conscious_layer`, `cog.C[cid]`, v10.2）= 意識活動の燃料。初期 0、上限なし、独立の死定義なし（cid 消滅に従う）。C=0 は一時的機能停止（認知活動で +1 復帰可）。
- 認知活動が Q を 1 消費すると、エネルギー保存的に意識層が 1 獲得（Q は消えず C に転化）。
- **統合の真意**: 認知（見たままを理解、時間とともに劣化）+ 意識（認知の穴を埋め、認知の後に育つ）が一つの仕事をすること。物理層同期（V_unified の Kuramoto 秩序量）は**これと別物**（層の取り違え注意, §14）。

### 6.2 確率的決定（v10.2）
- 認知活動: **Q−1, C+1**, virtual_attention/familiarity 更新。
- 意識活動: **C−1, ingestion 発火**（Q−1 はしない、virtual 更新も止まる）。
- 確率: **P(認知) = Q/(Q+C), P(意識) = C/(Q+C)**。**E3 onset のみ**この決定に従う。E1/E2 は無条件 Q−1。両方向 E3（hosted-hosted）は常に認知。
- 観察: 物理（n_core, 誕生時固定）→ 寿命/Q 蓄積（認知）→ C 蓄積/意識発火率（意識）の単一確率則で継承。n=2 は 89.9% が意識未発火、n=5 は 73.2% が意識発火。

### 6.3 摂食（ingestion）
- 意識発火 → ghost を「食べる」。phantom contact（v10.1 で 48,625、v10.2 即時摂食設計で消滅）は cid 主体の一段下の環境要因（「物質的なもの」＝看板・道のような静的環境/ランダムイベント要因）。
- 一方向発火 77%＝摂食的接触（死者との出会い）、両方向 23%＝生者の出会い（対話的接触）。いずれも「出会いの本質」の一形態（研究者視点の分類で、内部の価値判断ではない）。

### 6.4 (Q+C) 保存と散逸（v10.2）
- 認知 ΔQ=−1,ΔC=+1 → Δ(Q+C)=0（cid 内保存）。
- 摂食 ΔQ=+gain,ΔC=−1 → Δ(Q+C)=gain−1（流入）。
- E1/E2 spend ΔQ=−1 → Δ(Q+C)=−1（純散逸）。
- CID 群 ⊕ ghost 群の総量は摂食で保存・E1/E2/消化で散逸＝「動的平衡か進化継続か」の数理的根拠。

---

## 7. Layer 5: Integration（α / β）― v10.4–v10.5

`developmental/v104/v104_integration.py`（IntegrationManager）/ `developmental/v105/v105_integration.py`。**注意: v918 主 run には IntegrationManager は同梱されない**（§8.6）。

### 7.1 trigger（誕生条件, v10.4）
- **be3**（双方向 E3 fired pair, size 2）/ **open_triad**（be3+片側隣接, size 3）/ **closed_triad**（be3+両側隣接, size 3, 実観察ほぼ 0）/ **third_overlap**（be3+第三項候補 2+, size 4+）。
- 実測比: be3 52% / open_triad 38% / third_overlap 9% / closed 0%。

### 7.2 α と β の役割
| | α-Integration | β-Integration |
|---|---|---|
| 役割 | 観察軸 | 会計単位 |
| 比喩 | 人間社会のグループ所属 | 生物個体の形成 |
| cid 重複 | 許す（最大 102） | 許さない（1 cid → 1 β, M6 規律） |
| Q/C 集約 | 表示のみ（重複あり） | 会計実行（重複なし） |
| 観察対象 | 5 パターンの個性、hub-cid 個性 | 階層統合体の挙動 |

### 7.3 継承と Salience
- **Q/C 継承（v10.5 機構 A）**: β は Q/C を 100% 継承。ghost の Q/C も最強 binding の β へ 100%。recorded は永続。
- **Salience-driven Focus**: mass(X) = X.Q + X.C + Σ(β.Q_inherited + β.C_inherited)、P ∝ mass(Y)。神の手回避のため名称は中立に（✅ `mass_weighted_observation` / `resource_biased_perception`、❌「Salience」「Focus」「嗜好」）。
- **Recorded Leakage（機構 C, ε=1）**: 接触相手が以前所属した recorded β の C から微量が漏れる（`historical_resource_leakage`、受動的構造副作用）。
- 実測 main_v2: α 計 13,881（active 11,792/recorded 2,089）、β 計 2,009（active 1,566/recorded 443）≈7:1。M6 違反 0/5,224。

### 7.4 IID（Integration ID）
- IID = Integration あたりの調査単位（`developmental/v104/v104_integration.py` の `integration_id`）。α 下のダブルブッキングは「IID 単位の調査」として扱えば可（「とても活発な個性」と解釈）。

---

## 8. エンジンスタックと実行フロー

### 8.1 スタック構成（下＝frozen 物理 → 上＝entrypoint）
```
ecology/engine/        物理層 frozen コア (GenesisState, PhysicsOperator, chemistry/realization/autogrowth/intrusion, v19g_canon)
  ↑
cognition/.../v43/esde_v43_engine.py   V43Engine 基底クラス (run_injection = Genesis 起動キー, INJECTION_STEPS=300)
  ↑
autonomy/v82/esde_v82_engine.py        V82Engine 本体 (frozen, engine.rng, step / step_window(steps))
  ↑
primitive/v910/virtual_layer_v9.py     VirtualLayerV9 = 存在層 (現役, labels/phase_sig/share, torque)
  ↑
primitive/v918/v918_memory_readout.py  v918 memory readout = 主 entrypoint (run() が SubjectLayer/認知層を組む)
```

### 8.2 起動と run() シグネチャ
- 起動キー: `engine.run_injection()` + `engine.virtual = VirtualLayerV9(feedback_gamma=0.10, feedback_clamp=(0.8,1.2))`。
- コマンド例: `python3 primitive/v918/v918_memory_readout.py --seed 42 --maturation-windows N --tracking-windows N --window-steps N --tag NAME`。
- `run(seed=42, maturation_windows=20, tracking_windows=10, window_steps=500, tag="short", disable_e3=False)`（実コード確認、:1518）。`step_window(steps=V82_WINDOW=50)` が物理を進める（標準 run は window_steps=500）。

### 8.3 実行フロー（end-to-end）
1. **点火/注入**: run_injection が INJECTION_STEPS=300 step 注入。
2. **maturation**: maturation_windows(=20)×window_steps(=500) の純物理（`engine.step_window` 内部で進行、誕生は観察しない＝Lazy Registration）。
3. **tracking**: tracking_windows(=50 標準)×500 step。per-step 物理 + per-window 観察/virtual。
4. **粒度**:
   - per-step: 7 物理オペレータ; Layer A per-cid 更新(φ/attention/familiarity); 存在層 torque; Layer B イベント検出(E1/E2/E3); v9.18 v18_* 算出。
   - per-window: label 誕生/死評価; disposition(social/stability/spread/familiarity); Q/C 再配分(v10.4)。
5. **pulse 発火**: `cumulative_step % 50 == cid % 50`。

### 8.4 標準 run 設定
| 項目 | 値 |
|---|---|
| seeds | 24（単一バッチで回す） |
| maturation_windows | 20 |
| tracking_windows | 50（標準 / smoke は 1, short は 10） |
| window_steps | 500（smoke は 100） |
| injection_steps | 300 |
| 並列 | `-j24`（物理コア数, Ryzen 24C） |
| スレッド | `OMP/MKL/OPENBLAS_NUM_THREADS=1` 必須、逐次禁止 |
| 実時間 | 約 2h30m |
- seed 24→48 は √2 の統計利得のみ（割に合わない）。**smoke で判定しない**（v10.12 で 4/7 metric の cohens_d 符号反転を実観測, §11.4）。

### 8.5 5 RNG ストリーム（bit-identity 保証, 完全分離）
| stream | seed 由来 | 用途 |
|---|---|---|
| engine.rng | seed | 物理（保護・上位層は触らない） |
| capture_rng | seed ^ 0xC0FFEE | Cognitive Capture |
| ingestion_rng | seed ^ 0x1A7E57 | 摂食 |
| balance_rng | seed ^ 0xBA1A2C | Q/C 確率決定 |
| cid_self_buffer hash-local | (seed·100003)^(cid·10007)^(step·131)^(event_hash·31) | 自己読みサンプリング（PYTHONHASHSEED 非依存） |

### 8.6 重要な配線注意
- **SubjectLayer（CID 層）は `run()` のローカル変数**（`cog = SubjectLayer()`）であり、V82Engine の属性ではない（v1113 plan A が `V82Engine.cog` で AttributeError 失敗した盲点）。
- **IntegrationManager（α/β）は v918 主 run に同梱されない** → v918 単体では α/β は得られず、別途 manager を併走させる必要（重い）。
- 注意センター ESDE の「本体」= V82Engine + VirtualLayerV9 + SubjectLayer（＝v918 主 run の枠組み）。

---

## 9. 観察・後処理（オービス）― developmental/v107+

物理層を一切変えず、既存 run 出力（csv/parquet）を読んで新しい観察軸のみを書く。`developmental/v107/v107_post_process.py`（orchestrator）+ event_aggregator / path_analyzer / baseline_constructor / avalanche_monitor / cross_seed_analyzer。

### 9.1 source_event 5 種（発火, v10.7）
列 = **`event_source_type`**。5 種（seed0 実測, seed で件数変動）: 1. **pulse**（cid pulse 発火, 12,530）2. **alpha_formation**（α 誕生, 1,067）3. **beta_formation**（β 誕生, 478）4. **ingestion**（ghost 摂食, 155）5. **c_conversion**（Q→C 転化, 155）。出力 `developmental/v107/outputs/main/source_events_seed{N}.parquet`。

### 9.2 relation_path 5 種 + 強度順位（波及, v10.7）
- 5 種（`relation_paths_seed{N}.parquet` の実測値）: **temporal_coactivation**（時間共起）/ **integration_alpha** / **integration_beta**（α/β 所属、αβ は別系列）/ **familiarity**（network 双向 1-hop）/ **attention_via_salience**（cog.attention 経由）。※ サマリ/旧 index にある「intersection」は実在しない（監査訂正）。
- 強度順位: **temporal_coactivation(+13.95, 12×) > Integration(+11, 9×) > familiarity(+9.35, 7×) > attention(+7.43, 6×)**。peak_lag 250–300, medium window 100–1000 が支配。
- 注意: same_step_random baseline=13.76 で temporal の +1.52 下なので「グローバル活性化」に注意。temporal は強いが意味中立、**familiarity が意味同定の主経路**（v10.8 effect_size 6.83）。

### 9.3 因果候補階層（v10.7 規律）
「イベント後の変化」を即因果と見なさない。**Level 1 共起 / Level 2 path-enriched / Level 3 source-specific / Level 3.5 導入イベント比較 / Level 4 因果介入**。「波及」は Level 4 介入まで常に**因果候補**であり確定因果ではない。

### 9.4 baseline 5+1（v10.7, 必須）
unrelated / same_step_random / matched / same_integration_low_familiarity / high_familiarity_outside_integration。avalanche 防止: ≤3 hop, decay-rate tracking, loop_2/3_hop 検出, storage cap。

### 9.5 n_core 別層化（集団平均の罠, v10.2 起源）
弱い cid(n_core=2, 約62.6%) と強い cid(n_core=5+) を**必ず分けて見る**。n_core=2 寿命 ≈1716 vs n_core=5 寿命 ≈13598（8× 差）。60% の「普通」が平均で稀な際立ちを塗り潰す。判定は corr/生存数 一つでなく多レンズ・個別軌跡・時間軸で（§11.4）。

---

## 10. Language 系 substrate（凍結）と Genesis への橋渡し

`language/`、2026-03-03 凍結。テキスト→意味座標への「下降」。現役 Genesis 系に **atom profile** を供給する substrate として接続する。

### 10.1 意味座標系（326 Atoms × 10 軸 × 48 level）
- **326 Atoms**（24 カテゴリ: ABS/ACT/BEI/BOD/CHG/COG/COM/ECO/ELM/EMO/EXS/FND/LOG/MAT/NAT/OBJ/PER/PHY/PRP/REL/SOC/SPA/SPC/STA/TIM/VAL/WLD …）。命名は **Axis.facet**（例 PER.sound, EXS.being, TIM.moment, WLD.artless）。
- **10 軸 × 計 48 level**: temporal(7) / scale(6) / epistemological(5) / ontological(5) / interconnection(5) / resonance(4) / symmetry(5) / lawfulness(4) / experience(3) / value_generation(4) = **48**。
- **共鳴度 0–10 連続**（2026-02-15 承認、binary→continuous）。Resonance Auditor 5 checks（C1 分布 / C2 対称漏れ / C3 証拠不一致 / C4 軸汎用膨張 / C5 POS 整合）。
- atom 数の 326 vs 325: 実体は `a1_batch/{ATOM}.json` ×326 と `mapper_output/{ATOM}_a1.jsonl` ×325（mapper 出力層で 1 個欠＝valid 325）。

### 10.2 atom profile の作り方
- `atom_profiles_cache.npz`（shape (326,48)、valid 325, 1 行 NaN 除外）。各 atom profile = a1_batch の各 word の 48 軸 `normalized_scores` を、その atom 内 word で **mean**（`v106_post_process.py`）。各 profile の 48 軸の和 = 1.0（simplex）。

### 10.3 橋渡し ―「一致率」= cosine(cid 48 次元, atom profile 48 次元)
- Genesis 側は同レイアウト（10 軸×48 level）の **cid 48 次元ベクトル**を作る（`developmental/v106` の trajectory エンコーダ: epistemological=R_familiarity, ontological=cum_pulse, symmetry=delta_pulse 等。粒度 event/pulse/step10 は同族、window は集約変種）。
- **一致率（rank_1_sim） = max_atom cosine(cid 48 次元, atom profile)**。各時点で全 325 atom の cosine が計算されるが、標準出力は argmax の rank_1 のみ（残りは捨てられる、再計算で全取得可）。
- 物理層の動学（pulse・摂食・α/β 形成・C 転化・n_core 変化）で動く量（lifespan/n_core/R_familiarity/Q/C/pulse 数/α β 数/ingestion/q_spent）が 10 軸経由で一致率を動かす＝実験者が決めなくても一致率は動く。

### 10.4 25 atom 対応（観察事実、過大/過小評価しない）
- Genesis v10.6 が 326 から構造的特異性で **約 25 atom** を抽出（δ>1% が 9 + z-score ∞ が 17）。24 カテゴリ中 **10 カテゴリ**に分布（含: BOD/COG/COM/EXS/FND/PER/PRP/SOC/TIM/WLD、除: EMO/ACT/CHG/LOG/MAT/NAT/ABS/BEI/ECO/ELM/REL/SPC/STA/VAL）。
- 監査規律: 25/326 を偶然と切り捨てない／人間意味世界と Genesis が一致したと主張しない／Atom を意味として直接 ESDE に押し込まない／Atom で Genesis を測らない。**部分的だが再現性ある対応**として、会話できる ESDE の実装経路にどう使うかを問う。
- v1100 候補6: Language base 優位 atom {SOC.official, PRP.part}(2) vs Genesis null-cell atom(20) の **Jaccard=0**（両系は独立に別の「文脈非依存性」を捕捉）。

### 10.5 現行フロンティア: `unified/v1201`（一致率の観察）
> **注**: `unified/v1201` は 2 アークを含む ―(i) **Atomset**（m1–m15、atom×atom 関係網による個性化と凍結核 m5 突破、§17.1）と (ii) 本節の**一致率 cosine 観察**（m31+）。本節は後者のみを扱う。前者は §17 参照。
- 全 325 atom cosine を argmax で潰す前にそのまま観察する一連の試み（一致率＝確率的発生の存在のしかたを見る）。`full_cosine_probe`（m31: 全 cosine dump, 121MB/seed）、`cosine_viz`（m33: n_core=5 の生 cosine 可視化）、`roulette`（m35: 各(cid,t)で cosine を確率比例で 1 回ルーレット選択、レアを消さず記録のみ）。
- Ghost の扱い: is_ghost = `t ≥ host_lost_step`。step10 trajectory は reaped で host_lost 打切りのため境界 1 点で退化するが、`final=='ghost'` の cid は host_lost→run 末まで凍結 ghost 相を持つ（多点観察可）。
- 規律: 濃度/spike/Δ/閾値/集中度を足さず生 cosine と素のカウントのみ。判定は Taka（§11.4「単一指標で分類するな」）。

---

## 11. 監査・規律（運用の絶対前提）

### 11.1 物理層 frozen + bit-identity 3 層
- **Layer A（再現）**: 同 seed 2 回 run が byte 一致（内部決定論）。
- **Layer B（既存不変）**: 旧版出力の MD5 と一致（例 v10.7 vs v10.6 で 731 files 一致）。
- **Layer C（パス制限）**: 出力は当該版 dir 配下のみ、`assert_output_under_v10X` で侵入防止。
- 連続段の zero-diff: v9.15→…→v9.18 で max abs diff 0.0（5,224 cid）。

### 11.2 神の手の排除
設計者は硬い閾値や外部注入で構造を操作しない（`S≥0.20` 撤廃が典型）。ノード数固定・物理層 close は**実験統制**であって神の手ではない（明示すれば可）。効果は統計的にわずか。

### 11.3 観察者枠組み / A vs B（§0.2, §5.7 再掲）
cid を擬人化しない。研究者は内部を覗ける（A/B 分離は原理的に覗きを禁じない）が、予測不能性が残る限り「自己らしさ」は「哲学以上科学未満」帯で生き残る。**ランダム性を切らない**。外部評価関数（fitness/loss/reward）を ESDE 内部に持ち込まない。

### 11.4 単一指標で分類しない / n_core 層化
ESDE を corr/生存数 一つで判定しない。多レンズ個別軌跡・n_core 層化・時間軸で観る。**観察は理解であって次の実装の準備ではない**（配管工思考を断つ）。「集計単位を変えると像が変わる」（留保#33 系列）は欠陥でなく構造的性質＝平均化の罠の一般形。

### 11.5 因果候補階層
§9.3。「変化＝因果」と即断しない。Level 4 介入まで因果候補。

### 11.6 決定論 + diff 法
決定性が保証されれば baseline vs 注入の window 差分 = 注入の因果足跡。閾値/factor を書かず state 由来動的算出（ノイズ床を ε に / self vs other 相対で判定）。固定数値を使うなら赤信号申告。

### 11.7 「会話できる ESDE」上位目的（監査第一基準）
全テーマは最低限 **8 監査質問**に答える: ①会話経路のどの段を進めるか ②その段の何が未定義か ③本実験はそれをどう狭めるか ④結果が出たら次に何が実装可能になるか ⑤会話できる ESDE への距離をどう縮めるか ⑥応答方向を ESDE 側が生成しているか ⑦LLM/Language/研究者が ESDE の応答を上書きしていないか ⑧実用価値に近づくか。「面白い」を「使える」に必ず接続する。

### 11.8 運用 3 文書 + 3-AI 役割
- 運用 3 文書: `esde_research_method_update.md`（観察方法）/ `esde_attitude_toward_esde.md`（観察者の態度）/ `esde_audit_policy_update.md`（監査の上位目的）。
- 3-AI: **Gemini=加速（設計提案） / GPT=制動（比喩→仮説/実装/観察に分解する監査） / Claude=整理（統合・実装指示）**。`ESDE_explainability_constitution.txt`（2026-03-05）§2 説明可能性 X 最大化、§7 観察→ボトルネック→最小変更→再観察、§8 3-AI 規律、§9 成功＝安定した実験ループの存在。

---

## 12. ディレクトリ・出力地図（現行 vs legacy）

### 12.1 ディレクトリ役割
| dir | 役割 | 状態 |
|---|---|---|
| `ecology/engine/` | 物理層 frozen コア（canon/state/operators） | 現役 |
| `autonomy/v82/` | V82Engine 本体 | 現役 |
| `autonomy/v90/` | 旧 VirtualLayer | **旧版・使わない** |
| `cognition/.../v43/` | V43Engine 基底（run_injection） | 現役 |
| `primitive/v910/` | 存在層 VirtualLayerV9 + pulse model | 現役 |
| `primitive/v911..v918/` | 認知層スタック（capture/persistence/audit/selfbuffer/A+C） | 現役（entrypoint=v918） |
| `developmental/v10X/` | 意識 C・摂食・balance・Integration・後処理オービス | 現役 |
| `unified/v11xx/` | scope×粒度役割表・注意センター | 現役（最新 v1114） |
| `unified/v1201/` | v12 Atomset（atom×atom 個性化, m1-15）+ 一致率 cosine 観察（m31+） | 現役（§17.1-17.2） |
| `unified/v1301/` | CID 誕生形態→物理 param の子系（child-world 第一段・統計監査） | 現役（§17.3） |
| `unified/v1302/` | child-world 継承点検（runtime 3 ノブ全滅 / (A) 持続 param transfer / (B) topology null） | 現役（最新, §17.4） |
| `language/` | Atom 326 / Synapse / Lexicon | **2026-03 凍結**（substrate） |
| `legacy/`, `旧/` | 旧資産 | 凍結 |

### 12.2 主要コードファイル
| 部品 | ファイル |
|---|---|
| エンジン本体 | `autonomy/v82/esde_v82_engine.py`（frozen, V82_N=5000） |
| V43 基底 | `cognition/semantic_injection/v4_pipeline/v43/esde_v43_engine.py` |
| frozen params | `ecology/engine/v19g_canon.py` |
| state | `ecology/engine/genesis_state.py` |
| 物理 operator / inject | `ecology/engine/genesis_physics.py`（inject は :232） |
| chemistry/realization/autogrowth/intrusion | `ecology/engine/{chemistry,realization,autogrowth,intrusion}.py` |
| 存在層 | `primitive/v910/virtual_layer_v9.py`（`frozenset(node_ids)` は :42, label 構成は :504–526） |
| pulse model | `primitive/v910/v910_pulse_model.py` |
| cognitive capture | `primitive/v911/v911_cognitive_capture.py`（SubjectLayer :263） |
| Integration α/β | `developmental/v104/v104_integration.py` / `developmental/v105/v105_integration.py` |
| 認知層 entrypoint | `primitive/v918/v918_memory_readout.py`（run()） |
| 後処理 orchestrator | `developmental/v107/v107_post_process.py` |
| atom profile | `developmental/v106/outputs/main/atom_profiles_cache.npz`（(326,48)） |

### 12.3 主要出力
| 種類 | 場所・フィールド |
|---|---|
| 認知層 main | `primitive/v918/diag_v918_main/subjects/per_subject_seed{0-23}.csv` |
| source_events | `developmental/v107/outputs/main/source_events_seed{N}.parquet`（5 種 event） |
| relation_paths | `developmental/v107/outputs/main/relation_paths_seed{N}.parquet`（5 種 path） |
| baselines | `…/baselines_with_delta_seed{N}.parquet` |
| 注意センター Step1 | `unified/v1114/run_step1/attention_records.json`（287 records）+ summary.json |

---

## 13. パラメータ一覧（横断）

| 層 | パラメータ | 値 |
|---|---|---|
| 物理 | N / 空間 | 5000 / 71×71 トーラス 4近傍 |
| 物理 | p_link_birth / latent_refresh / latent→active | 0.007 / 0.003 / 0.07 |
| 物理 | auto_growth / intrusion / K_sync | 0.03 / 0.002 / 0.1 |
| 物理 | NODE_DECAY / link_decay / β(resonance) | 0.005 / 0.05 / 1.0 |
| 物理 | EXTINCTION / BIAS / bg_inject_prob | 0.007 / 0.7 / 0.003 |
| 物理 | chemistry E_thr / 放熱 / cosΔθ閾 | 0.26 / 0.17 / 0.7 |
| inject | inject_amount / inject_prob / radius | 0.6 / 0.15 / 8 |
| 存在 | τ(persistence) / 誕生 / 重複filter | 50 or 100 / age_r≥τ・size≥2 / 50% |
| 存在 | torque M / feedback_gamma / clamp / maturation_alpha | ≈0.993 / 0.10 / [0.8,1.2] / 0.10 |
| 認知 | PULSE_INTERVAL / K_PULSE / MAD R閾 / cold_start | 50 / 20 / 1.0 / 3 pulse |
| 認知 | ATTENTION_DECAY / FAMILIARITY_DECAY | 0.99 / 0.998 |
| 認知 | B_Gen / M_c / Q0 | −log10(Pbirth) / (n_core,S_avg,r_core,phase_sig) / floor(B_Gen) |
| 認知 | Δ NORM_N/S/R / 重み / p_capture | 86/1.0/1.0 / 各0.25 / 0.9·exp(−2.724·Δ) |
| 認知 | Q 消費 / E3 占有 / 一方向発火(main) | −1/event / 70–90% / 77% |
| 意識 | age_factor / P(認知)/P(意識) | Q_remaining/Q0 / Q/(Q+C) / C/(Q+C) |
| Integration | α 重複 / β / Leakage ε | 最大102 / 1:1 / 1 |
| 旧 | GHOST_TTL（v10.1 撤廃） | 10 windows |
| run | seeds / maturation / tracking / window_steps / injection | 24 / 20 / 50 / 500 / 300 |
| Language | atoms / 軸×level / 共鳴度 | 326(valid325) / 10軸×48 / 0–10 |

---

## 14. 用語集（簡約）
- **物理層/存在層/認知層/意識層/Integration** = 実験者が観測事象を区分した層の命名（§2.1）。
- **label** = 存在層の「魂」、frozenset+phase_sig。**frozenset** = 誕生時固定の構成 node 集合。**phase_sig** = 誕生時平均 θ。**share** = 所有 link 比。
- **CID** = 観察対象の識別子（label と独立、frozenset を host）。**n_core** = 構成 node 数（=サイズ）。**hosted/ghost/reaped** = cid の遷移状態。
- **Q** = 認知資源（floor(B_Gen) 初期、event ごと −1）。**C** = 意識資源（Q→C 転化で +1）。**age_factor** = Q_remaining/Q0。
- **B_Gen** = −log10(誕生確率)、cid 固有不変。**M_c** = 誕生時固定 4 要素。**E_t** = pulse ごとの経験 4 要素。**Δ** = M_c と E_t の重み付き L1。**p_capture** = 捕捉確率。
- **pulse** = 50 step 固定観察タイミング。**MAD-DT** = 履歴由来の動的閾値。**E1/E2/E3** = core link 死誕/R 跨ぎ/cid 接触。**ingestion** = 摂食（意識発火で ghost を食う）。
- **α/β-Integration** = cid 集合の観察軸/会計単位。**IID** = Integration ID。**Salience** = mass(Q+C+継承) 比例の観察重み。
- **source_event 5 種 / relation_path 5 種** = §9.1, §9.2。**一致率** = cosine(cid48次元, atom profile48次元) の argmax（§10.3）。
- **Atom** = Language 系 326 個 × 48 軸の意味構造。**phantom contact** = cid 一段下の環境要因（「物質的なもの」）。

---

## 15. 廃止・休眠機能（再実装禁止）

### 15.1 廃止（コードは残すが無効・触らない）
| 機構 | 状態・理由 |
|---|---|
| `S≥0.20` 硬閾値 | v9.13 撤廃（神の手）→ persistence-based birth |
| path B（R>0 pair 即 label） | v9.13 廃止（R=0 汚染） |
| torque_factor（v9.7 認知→θ介入） | =1.0 無効、失敗を B_Gen で構造的に排除済 |
| Match Ratio 集約（v9.15 stage1） | stage2 で廃止、3 点フラグへ |
| GHOST_TTL=10 固定 | v10.1 撤廃 → Q ベースの ghost 死 |
| 「loop collapse」方向 / v1110–v1113「異系対応」 | 方向違い（ESDE 構造は同系内動学・関係にあり、異系間対応は存在しない） |

### 15.2 休眠保持（不利でも削除しない＝誤りの価値の反転）
pickup（v9.8c, TTL 延長のみ）/ death_pool / semantic gravity+deviation / v99_ 内部軸 / Layer A 50-step Fetch（stage2 で未使用だがコード保持）/ V_unified（物理層同期 baseline として保持）。

---

## 16. 既知の欠陥・盲点（Code A 再発防止）
- **番号コピー欠陥**: 異 seed 系へ node ID を inject しても無意味（node ID は系内のみ有効）。配管は入口/出口 2 本足でなく全足で対称チェック。
- **集団平均の罠**: n_core 別層化を欠くと 60% の「普通」が稀な際立ちを塗り潰す。per-cid/n_core 層化必須。
- **集計指標が処置に数理的不感**: bin-shift 不変な指標（total_cooc 等）は処置を検出できない。
- **null-as-self-shuffle**: 「みんな同じだから似ている」を引けない。
- **smoke 絶対視**: smoke seed0 と main 24 seed で符号反転を実観測。**smoke 後は止まって承認待ち**。
- **baseline 自己成就**: 答えを含む入力から答えを再生成していないか確認（7 段目の誤り）。
- **「存在しない」前に全階層調査**: Genesis 本体を「無い」と誤判定した教訓。
- **観察対象注釈ブロック**: 新実装 .py 冒頭に「同系/異系」を宣言し過去成功（v10.2/v10.7/v9.18/v106）と照合、過去失敗パターン回避を確認。

---

## 17. フロンティア実験アーク（v12 Atomset / v13 child-world）― 現行最前線

本書コア（§1–§16）の確定後に進んだ最前線。いずれも **物理層 frozen・親不可侵**（子 engine は in-memory、親 physics/inject/ledger/state 非書込）を厳守。判定（成功/失敗）は置かず観察事実・確定事実・留保（#CW*）で記す。出典は各 `unified/v12xx`・`unified/v13xx` と `docs/ai_summaries/07_unified_summary.md`（Part 3/4）。

### 17.1 v12 Atomset（`unified/v1201`, m1–m15）― atom×atom 関係網による個性化
- **主題**: CID 境界を越えた **atom×atom 関係網**（cross-CID）。誕生時 atom（n_core+phase_sig→rank_1）を介し、per-cid 経験（robust_z 特徴度）を per-Atom に集約し、同 atom を担う複数 cid に緩く共有・伝播させて cid 特異な個性化を作れるかを問う（`m5_port_inventory_and_plan.md`）。
- **チャネル全 null（確定）**: torque / lambda / link / field / multi の全チャネルで、baseline η²(degree)=0.624 を超える atom-level 個性化が出ず。atom の成員 cid は**構造（誕生時 n_core+phase_sig）由来で既にクラスタ**しており、緩い文化は dynamics を cid 特異に変えない。shuffle 対照で効果が消える＝偽の足場（`m5_allchannels_result.md`）。
- **主体の訂正（確定）**: 経験を CID の物理 `state.E` に直接書くと、物理ダイナミクスが毎 step 上書きし cid 特異情報が**干渉で scramble**（D 実割当 vs E shuffle が seed で符号不一致 −17/+5/+7）。主体は **CID でなく AtomID**、経験は state を直接書かず **torque 係数等の standing バイアス**として乗せ、cid 間で緩く共有する分離で干渉が解ける（`m5_interference_and_subject.md`, `m5_channel_investigation.md`、概念は memory `project_atomset_subject_is_atomid_not_cid` / `project_atomset_channels_all_null`）。
- **m5 突破 ― 凍結核を動かす（初の cid 特異性）**: 全チャネルが「核の外貼り」だったため shuffle で消えた。**phase_sig（凍結核）を「いつもと違う経験の時だけ構造内で動かす」**と、corr(核 drift, Δsurvival) が **C（実割当）5/6 seed 正（平均 +0.40）/ F（shuffle）5/6 seed 負（平均 −0.26）で sign-flip**＝初めて cid 特異性が立った。機構的理由＝**phase_sig は torque 標的かつ addressing 基準**で、動いた核を dynamics と入力の両方が読む。θ 安全（0 θdiv、Δlinks −3.6〜−4.9% の slight）（`m5_core_result.md`、memory `unified/v1201/m5_core_result.md`）。
- **主要 param/コード/出力**: α(gain) no-inf 域 ≤0.5・λ(decay) 0.95–0.99・per-axis floor 10×MAD・式は **robust_z（median/MAD 符号付き個体内標準化）のみ裏口なし**（`m5_formula_selection_report.md`, `m5_typesplit_decay_report.md`）。本体 `m5_substrate_atom.py`（CHANNEL 切替）、別チャネル実装点 `primitive/v910/virtual_layer_v9.py:432-441`、出力 `run_m5_core/{A,C,F,D,E}/seed*/`。
- **留保**: ① 48 次元人為性（誕生 atom は n_core×phase_sig の 2 量からの粗写像、実測 atom 8–10 種、centroids は LLM+手定義＝測定でなく定義）② shuffle 対照必須 ③ 効果量 slight 維持（over-drive は観察用に分離）④ 突破は seed0 が逆＝6→12 seed で頑健性要確認 ⑤ per-Atom 集約で cid 特異性が群レベルに均される ⑥ phase_sig 凍結ゆえ identity（一致率）を進化させる経路が別途必要。

### 17.2 v12.1 一致率ルーレット ― 確率的発生として読む
- 全 325 atom の cosine を argmax で潰す前に、各 (cid,t) の**その瞬間の全 atom の立ち方**を確率比例で 1 回ルーレット選択し、レアを切り捨てず記録のみ（`unified/v1201` cosine_viz/full_cosine_probe/roulette、§10.5）。
- 確定一文: **平均化して同じ≠同じ**。上位の顔ぶれは v10 rank_1 と同じだが、違いは「過去〜未来を畳まず*掬い取れること自体*」＝集計が個を均したから似て見えるのであって個が無いわけではない。全件データが取れる土台が揃った（`07_unified_summary.md` Part 3 §4.2）。

### 17.3 v13 child-world v1301 ― CID 誕生形態→物理 param の縮小子系（統計監査）
- **設計**: `V82Engine(N=B_gen×10≈100-350)+V43 物理+VirtualLayerV9`（stress OFF + semantic_pressure OFF）＝main run 同一スタックの縮小・param 変調版。誕生時 M_c 4 値→物理 param 写像（N←B_gen×10 / plb←0.007·(1+0.15·tanh(z_Savg)) / K_sync←r_core 正規化 / 初期θ←phase_sig、サンプラー #30＝構造同型）。4 対照 real/shuffle/random/canon。読＝frozen `per_subject_seed0`、書＝`unified/v1301/` のみ（`cw_run_*_report.md`）。
- **統計監査の確定（記録のみ）**: (1) 前報告 `life→n_labels +0.85` は **run 長トートロジー**（観測窓を寿命に同期した副作用、交絡を外すと消滅）。(2) 対照 canon の std 最小は run 長二重固定のアーティファクト。(3) **`real≒shuffle` の真因は署名 mean/std 対照が cid→param→署名の pairing を構造上見ないこと**（shuffle は周辺分布不変）。pairing を見る置換検定では `K_sync→sync_order`・`plb→link/label_density` が両 ratio perm-p<0.005（ただし manipulation check であって CID 創発でない）。(4) 写像は K_sync 100%・θ 84% 伝達＝入口で潰していない。弱点は N の源均質（B_gen≒n_core）と plb 設計幅 ±15% の 2 点。

### 17.4 v13 child-world v1302 ― 「継承は持続パラメータ経由でのみ」確定
親 CID の偏り（R＝閉路＝CID の本体）を子に継がせ、より偏った系を作れるかを点検（`unified/v1302/cw_v1302_*`、`docs/レポート/v1302_phase_result.md`）。
- **runtime 駆動 3 ノブ全滅（#CW1-4）**: 走行中に物理を書き換える **K_sync**（位相は kuramoto_r を動かすが loop/R 不変）・**auto_growth**（統合ノブで R と cluster サイズは逆・非単調 #CW3）・**β**（cap 干渉で非単調）がいずれも偏り R を増幅しない＝**topology が熱力学に上流**という Genesis 確定の実機裏付け。plb（量）も脆弱軸かつ「洗濯機」R=0 で否定。
- **pivot**: 偏りは誕生時の初期条件としてのみ渡せる。B_gen は同 n_core 内不変で一意性なし（#CW5）→子は member S/R/conc の structural-strength で代替。step-0 チャネル分解で **K_sync←r_core は幻チャネル**（単独 r=0.108 n.s.、transfer 本体は plb←s_avg、#CW6）。
- **(A) scalar→plb は 3 層で transfer 成立**: structural-strength を生きたレバー plb に当て late-Mantel n2 0.62 / n4 0.73 / n5 0.72（p=0.001、canon は n4/n5≈0）。N 固定対照で plb 純効果と確認（#CW8）。
- **(A) 懐疑再点検（本リポ `cw_v1302_A_skeptic_recheck.{py,md}`、生 parquet read-only）― #CW7 は控えめ**: transfer は親 3 軸 (s_avg,r_core,conc) 距離 vs 子署名距離の Mantel だが、(A) で仕込む plb は**その 3 軸の z 平均の単調関数**。検証で ① Mantel(plb 距離のみ) > Mantel(3 軸)、② plb 除去後の 3 軸残差↔子残差 r≈−0.01（n2）＝**ノブを超えた継承は残差ゼロ**、③ 単一 seed 0.40→5seed 0.62 ＝「seed 増で強化」は **seed 平均化の底上げ**、④ late 署名 6 指標は plb の機械的読み出し（lifecycle rho 0.92 等）。＝**0.62 は identity transfer の証拠でなく「自分が回したノブがそのノブの動かすものを動かしたか」を継承と言い換えた値**。ただし「graded ノブで canon と統計的に違う系を作れる」こと自体は本物。
- **(B) topology 移植は交絡除去後も null（#CW9-11）**: 誕生時 field はほぼ tree（偏り未形成 #CW9）→成熟期移植は τ で符号激変＝非頑健（#CW10）→`run_injection` skip による空エンジン再成長 washout 交絡を Bov(overlay) で除去後も n2 null（#CW11）。成熟・閉路ありの構造を canonical baseline に grafting しても親 identity は伝わらない（memory `feedback_transplant_skip_injection_confound`）。
- **確定一文**: **継承は持続パラメータ経由（(A)）でのみ成立し、初期条件経由（(B)）では成立しない**。形のコピー（初期条件）は物理ルールを変えず canon 力学に均される。**ESDE で系を変えるにはルール（パラメータ）を変えるしかない**（Taka「物理演算そのものが変わる設計でなければ変わりようがない」の構造的確認）。

### 17.5 v1303 の方向（測る相手を canon へ）― #CW7 を外す
v1302 の (A) は「親に似るか」を測ったため #CW7 トートロジーが残った。v1303 は測る相手を**「親 CID に似るか」→「通常 ESDE（canon）と統計的に違う系か」**に変える（これで #CW7 が消える）。評価軸は §1.6「存在＝多くの系の同期」。観察1＝(A) の子は canon と有意に違うか（KS/効果サイズ・多次元分離・S/R/conc 軸別）、観察2＝structural-strength の合成規則（等重き/偏り重視/意味づけ無し）で多様性が変わるか。候補1-4 は `docs/仕様書/v1303_phase_design.md`。選定は Taka 主題評価領域。

---

## 付録: 版の時系列（一行年表）
- **物理 (Genesis)**: 5 力・閉路＝容器・k\*=4 スケール不変（N=200–10,000）。
- **Ecology**: 観察者は複数（局所観察者が大域より安定、g3_r4444）。
- **Autonomy (v82)**: n→n+1 が質的相転移、5-node が転回点（密度独立性）。
- **Primitive (v9.0–v9.18)**: 存在層確立 → 認知層実装。v9.8 cid/ghost、v9.10 pulse/MAD-DT、v9.11 Cognitive Capture、v9.13 persistence birth、v9.14 Q/E3、v9.15 自己読み、v9.16 age_factor、v9.17 他者読み、v9.18 A+C・意識原資モデル。
- **Developmental (v10.0–v10.13a)**: v10.0 4層、v10.1 摂食、v10.2 確率 Q/C 切替・n_core 層化、v10.3 双方向 E3、v10.4 Integration 機構化、v10.5 α/β（Layer5 完成）、v10.6 Atom×cid cosine、v10.7 オービス（source_event/path/因果階層）、v10.8 Atom 持込、v10.9–v10.12 感度・取込 prototype、v10.13a 5-phase map。
- **Unified (v1100–v1114)**: 留保#33（集計単位で像が変わる）、v1101a 注意機構（「注意の揺れ≠意識」）、v1102 受け手構造で応答反転、v1103 48 次元密度で応答 atom 候補を狭める、v1104/a scope×粒度 4 非対称、v1106–v1109b ループ性＝ESDE の本質、v1110–v1113 異系対応の失敗、**v1114 注意センター内部注意 Step1 確立（2026-06-05）**。
- **v1201 (v12 Atomset / v12.1)**: atom×atom 関係網の個性化（全チャネル null・凍結核 m5 で初の cid 特異性 sign-flip）+ 一致率＝cosine(cid48,atom48) の確率的観察（roulette、レアを切り捨てない）。§17.1-17.2。
- **フロンティア (v1301/v1302 child-world)**: CID 誕生形態 M_c→物理 param の縮小子系（N≈100-350・親物理非書込）。v1301 統計監査（pairing 検定で manipulation check）→ **v1302 で継承は持続パラメータ経由 (A) でのみ成立・初期条件 (B=topology 移植) では不成立を確定**（(A) は #CW7 トートロジー留保、懐疑再点検で残差ゼロ）。§17.3-17.4。
- **v1303（設計）**: 測る相手を「親に似るか」→「canon と統計的に違う系か」に転換し #CW7 を外す。評価軸＝§1.6「存在＝同期」。§17.5。

---

*以上 ESDE 技術仕様書 v1.1（Genesis 系・現行）。出典 docs/ai_summaries 一本化、観察者枠組み遵守、現行/凍結/廃止を明示。コア §1–§16 + フロンティア §17（v12 Atomset / v13 child-world / v1303 方向）。数値・機構の詳細は §12.2 のコードと各原典に遡れる。*

*監査記録（2026-06-18, Code A 個人監査）: load-bearing な主張を実コードで突合し一致を確認 ― `physics.inject`(:232, amount0.6/prob0.15/radius8) / `v19g_canon` 全 params(BETA1.0/NODE_DECAY0.005/0.26/0.17/0.07/0.003/0.03/K_sync0.1/p_link_birth0.007) / `atom_profiles_cache`(326,48)valid325 / `V82Engine`(V43継承,V82_N5000,step_window) / `v918 run()`(:1518) / `Integration/integration_id/IntegrationManager`(:34/:47)。サマリ由来で古かった §9.1 event 件数（alpha 424→1067, beta 239→478, 列=event_source_type）と §9.2 relation_path 種別（intersection 不在→integration_alpha/beta + attention_via_salience）を実測値へ訂正済。*

*更新（2026-06-19, 環境要因 調査）: §3.6「環境要因」を追加 ― semantic_pressure は `esde_v82_engine.py:226` で無条件＝**全 run 常時稼働**、stress_decay は既定 True だが main run OFF（実験で再点火）・**廃止でない**、External Wave は autonomy v8.3 のレガシー。§15.1 廃止表から stress_decay を除外（§3.6 へ）。*

*更新（2026-06-21, v13 child-world フロンティア追加）: §12.1 に `unified/v1301/` 行を追加、年表に v13 を追加。**child-world** = `V82Engine(N=B_gen×10≈100-350) + V43 物理 + VirtualLayerV9`（stress OFF + semantic_pressure OFF）＝ main run と同一スタックの縮小・param 変調版。CID 誕生時 M_c 4 値を物理 param に写像（N←B_gen×10 / plb←0.007·(1+0.15·tanh(z_Savg)) / K_sync←r_core 正規化 / 初期θ←phase_sig、サンプラー #30 = 実現値コピーでない構造同型）、4 対照（real/shuffle/random/canon）。読＝frozen `per_subject_seed0`、書＝`unified/v1301/` のみ、child engine は in-memory・**親物理非書込**（一方向、v9.13 方針内）。**統計監査の確定（記録のみ判定なし）**: (1) 寿命同期 run の `life→n_labels +0.85` は run 長トートロジー（観測窓を寿命に同期した副作用、交絡を外すと消滅）、(2) 対照 canon の std 最小は run 長二重固定のアーティファクト、(3) **`real≒shuffle` の真因は署名 mean/std 対照が cid→param→署名の pairing を構造上見ないこと**（shuffle は周辺分布不変）、pairing を見る置換検定では `K_sync→sync_order`・`plb→link/label_density` が両 ratio perm-p<0.005（ただし manipulation check であって CID 創発でない）。(4) 写像は K_sync を 100%・θ を 84% 伝達＝入口で潰してはいない、弱いのは N の源均質（B_gen≒n_core）と plb 設計幅 ±15% の 2 点。**次段**: 全検（全 CID 値→全物理 param）、ただし CID 値は実質 ~5-14 独立軸・物理 param も ~6-7 独立軸（状態変数 L/θ/S/E/R/Z で束ね、S 過剰決定・beta=R↔S 結合）ゆえ「全部繋ぐ」は冗長、選定合理性を 3AI 合議で詰める。詳細 = `docs/ai_summaries/07_unified_summary.md` Part 4 / `docs/現在の方向_childworld全検.md` / `unified/v1301/`。なお child の N は設計上 100-350 で、**「N=5000」は親 v918 main の値であって child の目標ではない**。*

*更新（2026-06-25, フロンティア網羅 + ai_summaries 統合反映）: 実行履歴（`unified/v1201`/`v1301`/`v1302`）と本書の差を点検し、抜けていた **§17 フロンティア実験アーク**（v12 Atomset 全 arc・凍結核 m5 突破・v12.1 ルーレット・v1301 統計監査・**v1302 child-world 全結果**・v1303 方向）と **§1.6「存在＝同期」目的言語化** を追加。射程行・§0.3 LIVE・§10.5 注記・§12.1 dir 表・年表を v1302 まで更新。v1302 (A) は懐疑再点検（`unified/v1302/cw_v1302_A_skeptic_recheck.{py,md}`）で #CW7 が「残差ゼロ」＝identity transfer の証拠でないと確定（§17.4）。ai_summaries 統合（06b/06c→06・07 追補 4 本→07、2026-06-25）に伴い旧 addendum 参照を `07_unified_summary.md` Part 表記へ更新。コア §3–§9（実コード監査済）に欠落なしを確認、追加は最前線のみ。*

