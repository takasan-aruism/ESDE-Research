# Cognition — AI 向け要約 (最重要・最複雑)

*原本*: docs/ESDE_Cognition_Report_Final.md (1271 行)
*要約時点*: v9.9 完了前 (2026-04-11)
*対象読者*: 未来の Claude

> **重要**: このフェーズは大量の失敗を含み、それが設計の進化を駆動した。却下された方針を必ず読んで、同じ失敗を繰り返さないこと。物理層への介入は誤りという結論はここで確定した。

---

## このフェーズが答えた問い

Ecology から継承: **semantic structure は物理トポロジー内で emergence できるか?** → Yes, but 2 層 (physics + virtual) 必要。virtual layer は **位相周波数の organization** (spatial ではなく θ-space での grouping) として実現された。

---

## 用語集 (最小必須)

- **concept island**: 空間局所的かつ位相的に一貫した node 集合。persistence ≈ 0.07-0.08
- **erosion_depth**: 概念領域の深さ hops 単位で外界の影響がどこまで浸透するか。飽和値 3–6 hops
- **core_preservation**: 深部 node (depth≥3) が初期位相を保つ割合。ほぼ 0
- **whirlpool metric**: cluster identity を spatial center proximity で追跡 (node-set overlap が完全代謝で破綻するため)
- **R+ (resonance>0)**: cycle 存在の指標。R=0 (acyclic) vs R>0 (cycle)
- **M3 (encapsulation)**: density_ratio≥1.5 かつ seen_count≥3 を同時達成
- **Π (Proliferation Drive)**: void 場から link birth を駆動する状態依存的な大局制御量
- **V_i (Fertile Void)**: snap 時に沈殿する potential 場、isolated 領域で長生き
- **budget=1**: virtual layer の総エネルギー。分配の 0-sum ゲーム
- **labels (v7.x)**: R>0 motif から born する **位相周波数グループ**。spatial cluster ではなく θ-space 上の organization

---

## v3.x 観察フェーズ — 確定事項

**v3.0–3.1: 空間同一性の普遍性**
- Semantic injection (2 concepts, 10k nodes) → k\*=4 不変
- Checkerboard observer-concept mapping (r0→A, r1→B, r2→A, r3→B) が 100/100 seeds で一致
- Concept island は spatially stable だが topologically fragile (B_persist ≈ 7-8%)
- Merge=0, split=0: concepts は並列存在するが相互作用なし

**v3.2–3.4: Mediation paradigm**
- Direct A↔B bridge は phase_delta=π/2 → cos(Δθ)≈0 → 物理的に不可能
- Mediator C (intermediate phase) で tripartite structure emerges (85% seeds)
- 相互作用は entropy 保持しながら diffusion ~27k events で activate

**v3.5–3.9: Transport saturation と絶対限界**
- v3.6: **Paradigm shift** — 静的 bridge は fiction、semantic influence は dynamic transport flow (depth=2.25 hops)
- v3.7: erosion_depth 3–6 hops が物理上限、core_pres ≈ 0 でも macro 崩壊なし
- v3.8: 8× pressure amplification → diffusion 8 倍だが penetration depth 不変。**Transport saturation 確認** — 概念領域は bounded membrane (透過率 up でも侵入深度 up なし)
- v3.9: **Collapse threshold = 128× amplification** (2/10 seeds で k\*≠4)。64× 以下は unanimous k\*=4。Deep core は structurally empty

---

## v4.x 試行 — ★ 失敗の記録 (繰り返さないため必読)

### v4.2 Adaptive Dynamics → **Universal collapse at wave 6**
- Mechanism: plasticity=1.3 (rewiring), hardening_bonus=0.15
- 全 9 run wave 6 で崩壊。Rewiring は damage の 10-30% 程度、hardening は次 wave 到達前に 7× 速く decay
- **失敗理由**: Link starvation は phase transition、parameter tuning では解決不可

### v4.3 Encapsulation → **encapsulation = 0/555 windows**
- Steady pressure (no waves) で cluster は ubiquitous (66% windows)
- DR≥1.5 が 13/14 seeds で発生するが、cluster identity が持続できず
- **失敗理由**: size 3-5 node clusters は 200-step window 間に完全再構成、node-set overlap (≥50%) では tracking 不可
- Gemini の診断: 「水の分子を追跡して whirlpool を測ろうとしている」

### v4.4 Whirlpool Metric → **persistence/density 非共起**
- Center proximity tracking で seen_count≥3 達成 (8/10 seeds)
- **発見**: persistent clusters は low-DR、high-DR clusters は transient — 異なる populations
- 持続性と密度が同時に出現しないため M3 失敗

### v4.5a/b–v4.7 Latent boost 戦線 → **5 実験で同じ失敗に収束**
- v4.5a: incorporation 0/453 contact events
- v4.5b: resonance-biased boost で first deformation (62.5% node replacement)、incorporation 依然 0
- v4.6: Jaccard relaxed lifespan = strict (binary 0/1、中間状態なし)
- v4.7: per-step accretion (6,552 boosts!) でも incorporation=0
- **失敗理由 (根本)**: temporal bottleneck は解決したが **spatial mismatch** が致命的 — boost が accumulate する node pair と次窓の cluster boundary nodes が異なる位置
- **決定的結論**: Latent-boost architecture は mobile 3–5 node clusters と incompatible

### v4.8 Terrain Genesis → **cooling 不発**
- cooling_factor = 1/(1 + strength × density) で dense regions 保護予定
- **失敗理由**: Local link density too low (S≥0.20 で most nodes 0–1 links) → cooling function は 1.0 に張り付き

### v4.8b Chemical Valence → **初の M3 成功、ただし bubble-crash-depletion**
- Z-state coupling (Z=0 inert に decay penalty、Z=3 compound に restoration)
- **Project 初成果**: M3 達成 (2 windows)、relaxed_lifespan=10、max_size=10–11、gamma motifs 検出、cooling activated
- **失敗の芽**: Bubble-crash-depletion 3-phase lifecycle (4600→8400→1100 links)
- **失敗理由**: Static compound_restore=0.5 は high-density で強すぎ (bubble)、low-density で弱すぎ (depletion)

### v4.8c Axiomatic Parameter Discovery → **初の自動発見成功、bubble は残存**
- State-dependent viscosity α(t) で α 最大 100 倍可変
- **成果**: 両 seed が restore≈0.514, inert_penalty≈0.018 に収束 — **ESDE 初の system-discovered parameter**
- **失敗残存**: Bubble-crash cycle persistence (viscosity 応答が 10× 遅い)

### v4.9 P1–P6 History layer & Void → **All fail on timescale mismatch**
- h_age, h_res, h_str (maturation/rigidity/brittleness) → renewal なし (stagnation)
- Fertile Void V_i 生成、しかし decay too fast (λ=0.05 → 92.3% loss/50 steps)
- **失敗根因 (3 度目の同一パターン)**: intermediary field decay exceeds target response time

### v4.9 P7/P8 Generative Dynamics → ★ **初の renewal cycle 成功**
- **Paradigm shift**: 確率的 P(link) を deterministic T_ij > E_ij に変更
- T_ij = tanh(V_i+V_j) × (Π/Π_max) × cos((θ_i−θ_j)/2)、E_ij = tanh(max(deg)/(1+Π))
- **Degree-zero threshold bypass**: 両 node isolated → E_ij=0 → V>0 で T_ij>E_ij guaranteed
- **結果**: gen_births=5,155 (P2-6 は 0)、post-trough recovery 901→1383 (+54%)
- **成功の鍵**: Phase geometry (cos θ) が RNG を置換、semantic phase が structural generation に初参入

---

## v5.x — Circulation 失敗: 「選択なき循環は洗濯機」

**v5.0**: 4 loop fixes で links 安定化
**v5.1**: E↔V direct coupling 試行
- Run 1: radiation = 1−exp(−Π) → 99.7% E drained → instant death
- Run 2: 修正版で 27k births/window、cycle ゼロ
- **決定的発見 (Taka 直接発言)**:

> 「選択なき循環は洗濯機」

energy は flow するが structure 形成なし。Genesis の教訓: selection が先、quantity は後。

---

## v6.x Recurrence Architecture — 物理層への介入は誤り

**v6.0–6.1**: Genesis selection filter 復活、R+ echo deposits で scar 蓄積。reformation は p_link_birth=0.007 sparse sampling で fail (~3%/window hit rate)

**Critical realization (Taka 直接発言)**:

> 「物理層は床。床の上に建てる」

Physics layer (固定 p_link_birth, latent_refresh, decay_rate) 内に circulation/memory を implement するのは根本的に誤り。Parameters は biology で dynamic に regulate されるべき。**この発言以降、物理層への介入は禁則となった**。

---

## v7.x Virtual Layer & Budget=1 paradigm

**v7.0–7.2 World Induction**:
- R>0 motifs から labels birth、位相 torque で virtual energy 独立維持
- corr(R+,vE)=0.17 と弱いが、virtual layer が physical layer 独立に 225 labels sustain
- **30:1 structural amplification ratio**

**v7.3 Metabolism Model (budget=1, zero-sum)**:
- 「増減不要。物理的安定 = 1。それを label 間で分配」(Taka)
- **結果**: 1120 labels born → **9 survived (0.8% survival, 97% compression)**
- **生存法則**: late arrival (w100+) + low R+ window (born in calm, R+≈8.7 vs mean 19.5) + 5-node = survival
- **★ Critical finding**: **Labels are NOT spatial clusters — they are phase-frequency groups**
  - Internal node distance 40–60 hops (scattered across grid)
  - 22% of label nodes have no links
  - R>0 cycles は label 内 (intra) ではなく label 間 (inter) の boundary で形成
  - Label territories overlap (non-separable)

**v7.4 Scale validation (N=5000→10000, 12 seeds)**:
- 全 12 seeds 同一均衡 (links 5701±100, stress 0.986±0.011)
- **R+≈8 は N に scale しない (N 独立)**
- 「**Complexity は N からではなくルールから born**」

---

## v9.x への橋渡し (なぜ Subject Layer アプローチに至ったか)

v7.3-v7.4 で確立:
1. 動的平衡は self-regulating (stress intensity ≈1.0 via EMA、seed/N 独立)
2. Virtual layer は位相周波数の organization (spatial ではなく θ-space)
3. Label 間 boundary が構造的相互作用の場 (R>0 は inter-label bridges)
4. Budget=1 では label 単体の複雑性に limit (1120→9 compression)

**未解決問い → Primitive (v9.x) で取り組む**:
- Label set から単体では不可能な emergent behavior を trigger する条件
- Label を「作用する主体」より先に「世界を見ている主体」として定義する (v9.4 Perception Field)
- Subject (cid) を label から分離して観察主体化する (v9.8a 以降)

---

## 原本を読むべきタイミング

- v3.x detailed mechanics (transport saturation の数値、erosion_depth 確度)
- v4.2–v4.7 failed architectures のパラメータと elimination logic 詳細
- v4.8b chemical valence の bubble-crash-depletion dynamics 再現
- v7.3 label birth law (1120→9) の selection pressure 詳細
- 「物理層は床」発言の前後の Triad 議論の流れ
