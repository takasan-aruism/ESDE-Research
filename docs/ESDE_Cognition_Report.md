# ESDE Cognition: Semantic Interaction — Experiment Report

*Phase: Cognition (v3.0 – v3.9) / Encapsulation (v4.0 – v4.4)*
*Status: IN PROGRESS (v4.4 complete; awaiting Triad direction)*
*Team: Gemini (Architect) / GPT (Audit) / Claude (Implementation)*
*Started: March 11, 2026*
*Last updated: March 16, 2026*
*Prerequisites: Ecology complete (see ESDE_Ecology_Report.md)*

---

## Context

Ecology established that the ESDE system contains multiple regional observers whose aggregate creates the appearance of a single, less certain global view. The observer ecology is a stable, distributed, metastable regime — k*=4 is robust, divergence is the default state, and regime structure is stable under perturbation.

Cognition asks the next question: **can semantic structure emerge as physical topology within this ecology?**

All Cognition experiments inherit the frozen Genesis physics, Ecology observer mechanics, and v3.0 semantic injection rules without modification (except where explicitly noted). Baseline conditions: N=5000, plb=0.007, rate=0.002, quiet_steps=5000, 2×2 observer partition, 2 or 3 concept clusters.

---

## Cognition v3.0 — Semantic Injection

**Question:** Can structured semantic embeddings injected into the topology form stable concept islands without breaking the observer ecology?

**Method:** Define 2 concept clusters (A, B) via spatial localization (left/right thirds of the grid) and phase coherence (A: θ ≈ π/4, B: θ ≈ 3π/4). The middle third is a neutral buffer. Injection is at initialization only — no ongoing bias. Physics must alone sustain any semantic structure. 10 seeds.

**Results (10 seeds):**

Ecology remained healthy: k*=4 in all seeds. Concept zones assigned correctly (A≈1700, neutral≈1700, B≈1600 nodes). Observer-concept mapping showed the expected spatial alignment (r0→A, r1→B, r2→A, r3→B). Concept island persistence was low (A: ~0.08, B: ~0.04) and boundary friction was measurable (~670 cross-concept links, weight ~18.8 per window). Concept entropy ≈ 1.53, stable.

**Findings:**

*Semantic injection does not break the observer ecology.* k*=4 persists, divergence regime is unchanged, and the ecology baseline is fully preserved under concept injection.

*Concept domains form and are spatially stable.* Observer mapping is deterministic: the 2×2 checkerboard (r0/r2→A, r1/r3→B) appeared in all seeds. Concept spatial identity is preserved by the system.

*Concept islands are rare but not absent.* Persistence is low — concepts are spatially localized but do not reliably form strong topological islands (k=3 structures). The initial phase coherence fades under physics dynamics.

---

## Cognition v3.1 — Concept Persistence Validation

**Question:** Is concept island persistence statistically robust across 100 seeds? Do concepts interact dynamically (merge/split)?

**Method:** Run v3.0 configuration across 100 seeds. Add merge detection (cross-boundary weight + phase alignment), split detection (island fragmentation), per-region semantic entropy, and divergence-entropy correlation.

**Results (100 seeds):**

| Metric | Value |
|---|---|
| global k* | 4 in 97/100 seeds (k=3: 2, k=1: 1) |
| merge_count | 0 (all 100 seeds) |
| split_count | 0 (all 100 seeds) |
| A_persist | 0.08 ± 0.05 |
| B_persist | 0.07 ± 0.06 |
| mean entropy | 1.54 |
| observer mapping | r0→A, r1→B, r2→A, r3→B in 100/100 seeds |
| corr(divergence, entropy) | +0.05 ± 0.19 (weak, noisy) |

**Findings:**

*Concept spatial identity is a universal feature.* The checkerboard observer-concept mapping is 100% consistent across 100 seeds. This is not a random outcome — it is a structural property of the spatial injection.

*Concept islands are weak but non-zero.* Persistence ≈ 8% of windows. Concepts survive as spatial domains but rarely achieve strong topological consolidation.

*No dynamic interaction exists.* merge=0, split=0 across all 100 seeds. Concept domains are static — they persist in parallel without touching.

*Divergence-entropy correlation is negligible.* The weak positive correlation (+0.05) suggests no meaningful relationship between observer structural disagreement and semantic complexity at this stage.

---

## Cognition v3.2 — Interaction Activation

**Question:** Can minimal boundary pressure activate concept interaction dynamics?

**Method:** Introduce two mechanisms: (1) Semantic diffusion — boundary nodes have 0.5% probability per step of shifting their phase toward a neighboring concept's phase center. (2) Cross-boundary seeding boost — boundary nodes get 1.5× base injection probability. Physics unchanged.

**Results (20 seeds):**

| Metric | v3.1 (100 seeds) | v3.2 (20 seeds) |
|---|---|---|
| diffusion events/run | 0 | ~27,000 |
| merge_count | 0 | 0 |
| split_count | 0 | 0 |
| entropy | 1.54 | 1.53 (stable) |
| k* | 4 (97%) | 4 (100%) |

**Findings:**

*Diffusion activates influence exchange without destabilizing the ecology.* ~27k diffusion events per run transfer phase information across concept boundaries, yet entropy remains stable and k*=4 is maintained in all seeds.

*Interaction does not produce structural events.* Despite active boundary diffusion, merge=0 and split=0. Concepts exchange influence but maintain structural identity. GPT characterized this as a "weakly-coupled attractor regime" — interaction without collapse.

*This is a prerequisite state.* The system now supports information flow between concepts while preserving their individual identity. This balance is necessary for higher-order dynamics.

---

## Cognition v3.3 — Concept Attraction

**Question:** Do interacting concepts form stable cross-island bridges? Is diffusion flow symmetric?

**Method:** Add bridge tracking (cross-concept links with S≥0.15 persisting across windows) and directional diffusion flow counting (A→B vs B→A). No new mechanisms — observation only.

**Results (20 seeds):**

| Metric | Value |
|---|---|
| bridges per window | 1.1–1.8 |
| persistent bridges (2+ windows) | **0** (all seeds) |
| bridge_max_life | **1** (all seeds) |
| flow A→B | ~14,000 |
| flow B→A | ~13,800 |
| flow_asymmetry | ~0.007 (symmetric) |
| merge/split | 0/0 |

**Findings:**

*Bridges form but die instantly.* Cross-concept links appear every window (1–2 on average) but never survive to the next observation window. bridge_max_life=1 across all 20 seeds.

*Diffusion is symmetric.* A→B and B→A flows are essentially equal (asymmetry <1%). Neither concept exerts a stronger pull. The system is in a balanced exchange regime.

*Direct A↔B connection is physically impossible.* The phase separation (θ_A=π/4, θ_B=3π/4 → Δθ=π/2) means cos(Δθ)≈0, which cripples resonance-driven link stabilization. The physics engine correctly rejects direct cross-concept bridges. Concepts behave like immiscible fluids.

---

## Cognition v3.4 — Concept Mediation

**Question:** Can a mediator concept (C) with intermediate phase enable stable multi-step A↔C↔B bridges?

**Method:** Replace the neutral buffer zone with Concept C (θ_C=π/2, exactly midpoint of A and B). Layout: [A zone][C zone][B zone], each ~1/3 of the grid. Track tripartite loops (islands containing A+B+C nodes), per-pair bridge counts (A↔C, B↔C, A↔B), and mediation ratio (diffusion via C vs direct A↔B).

**Results (20 seeds):**

| Metric | v3.3 (no mediator) | v3.4 (with C) |
|---|---|---|
| tripartite loops | N/A | **17/20 seeds > 0** (mean 1.7/run) |
| mediation_ratio | N/A | **2.04** (C-mediated 2× more than direct) |
| diffusion events | ~27k | ~70k (all nodes now concept-tagged) |
| bridges per window | 1.4 | 4.1 (A↔C≈1.4, B↔C≈1.3, A↔B≈1.4) |
| persistent bridges | 0 | 0 |
| bridge_max_life | 1 | 1 |
| merge/split | 0/0 | 0/0 |
| C_persist | N/A | 0.03 (low) |
| k* | 4 (100%) | 4 (100%) |

**Findings:**

*Tripartite structures emerge.* 17/20 seeds produce at least one island containing nodes from all three concepts. This is the first time the system has produced multi-concept topological structures. The mediator enables co-occurrence that direct A↔B contact could not achieve.

*C mediates diffusion flow.* The mediation ratio of 2.04 means diffusion paths through C (A→C + C→B + B→C + C→A) are twice as frequent as direct A↔B paths. The intermediate phase of C makes it a natural stepping stone for phase-compatible information transfer.

*Bridges still do not persist.* Despite increased bridge count (4.1 vs 1.4 per window), bridge_max_life remains 1. Cross-concept links form more frequently but decay within one observation window. The physics still cannot sustain permanent inter-concept connections at the current parameter regime.

*The mediator itself is fragile.* C_persist ≈ 0.03 — Concept C rarely forms its own stable islands. It exists as a transient boundary population rather than an autonomous structural entity.

*This is GPT Outcome B (Partial mediation).* Concept C enables structural co-occurrence in islands but cannot yet sustain stable bridges. The mediator functions as a catalyst — facilitating encounters without itself persisting.

---

## Cognition v3.5 — Heterogeneous Loop Tension

**Question:** Can decay dampening for phase-gradient loops stabilize transient bridges into persistent structures?

**Method:** After standard physics decay, links qualifying as heterogeneous loop members (R_ij > 0 and cos(Δθ) < 0.8) receive partial strength recovery. Sweep: dampen_factor = {1.00 (baseline), 0.95 (mild), 0.90 (target)}. 20 seeds per condition. This is the first Cognition version to modify a physics parameter — a post-decay correction, not a change to the engine itself. GPT approved with caution.

**Results (60 runs: 3 conditions × 20 seeds):**

| dampen | persist_bridges | bridge_max_life | k* | entropy | collapse |
|---|---|---|---|---|---|
| 1.00 (baseline) | 0 | 1 | 4 (20/20) | 1.54 | 0/20 |
| 0.95 (mild) | 0 | 1 | 4 (19/20) | 1.54 | 0/20 |
| 0.90 (target) | 0 | 1 | 4 (20/20) | 1.54 | 0/20 |

**Findings:**

*Decay dampening does not produce persistent bridges.* persist_bridges=0 and bridge_max_life=1 across all 60 runs, at all dampen levels. The mechanism had zero measurable effect on bridge survival.

*The ecology is unharmed.* k*=4 maintained (59/60), entropy stable, no collapse. The modification was too weak to cause damage but also too weak to help.

*Bridge instability is not caused by excessive decay.* This is a meaningful negative result. The dominant limitation is phase geometry: cos(Δθ)≈0 between A and B prevents resonance support regardless of decay rate. Even with a mediator, any tripartite loop containing an A↔B edge inherits this phase contradiction.

*Concept incompatibility is physically encoded in the phase geometry.* The system correctly rejects structures that violate phase coherence requirements. This is not a parameter problem — it is a structural property of the physics.

---

## Cognition v3.6 — Semantic Flow

**Question:** If bridges cannot persist, how does semantic influence actually propagate? Is it better understood as flow than structure?

**Method:** Paradigm shift from static bridge analysis to dynamic transport observation. Zero physics changes. New metrics: (1) flow_penetration_depth — how many hops a diffusion event travels across a concept boundary (BFS, previously capped at 3, now measured at uncapped depth). (2) transport_chain_count — A→C→B multi-step chains detected within a single step. (3) scale_variance_index — island boundary divergence across 5 S-thresholds (0.10–0.30). 20 seeds.

**Results (20 seeds):**

| Metric | Value |
|---|---|
| depth_1step | **0.0%** |
| depth_2step | **75.1%** |
| depth_3+step | **24.9%** |
| mean_penetration_depth | **2.25** |
| transport_chains | 16–29/run (all 20 seeds > 0) |
| scale_variance_index | 0.05–0.53 (high variability) |
| flow_asymmetry | ~0.007 (symmetric) |
| merge/split | 0/0 |
| k* | 4 (100%) |

**Findings:**

*Semantic influence penetrates at least 2 hops across every boundary.* depth_1step=0% means no diffusion event terminates at the boundary itself — all influence travels into the target concept's territory. 75% reaches 2 hops, 25% reaches 3+. This is direct evidence of cross-concept information transfer, not just surface contact.

*Multi-step transport chains are universal.* Every seed produces A→C→B chains (mean ~23/run). The mediator functions as a routing substrate, not a structural bridge. Semantic interaction operates through transient multi-step diffusion paths.

*Island boundaries are observer-scale dependent.* The scale variance index ranges from 0.05 to 0.53 across seeds. In high-SVI seeds, the number and composition of "concept islands" shift substantially depending on the S-threshold used for island detection. This supports the Architect's hypothesis: concept islands are not fundamental objects but macroscopic patterns sustained by continuous micro-flows.

*The system is a dynamic transport network, not a static concept graph.* This is the central finding of v3.6 and represents a conceptual pivot for the Cognition phase.

---

## Cognition v3.7 — Semantic Erosion

**Question:** Does persistent transport flow leave structural traces inside concept territories? Does flow reshape topology over time?

**Method:** Zero physics changes. Track per-node phase drift (Δθ from initial state) at three depth layers: boundary (depth=0), near-core (depth 1–2), and deep-core (depth 3+). Measure erosion_depth (maximum depth where mean drift exceeds ε=0.05), core_preservation (fraction of deep-core nodes unaffected), and boundary_k (local connectivity for boundary hardening detection). Penetration BFS cap raised from 3 to 10 hops. 20 seeds.

**Results (20 seeds):**

| Metric | Value |
|---|---|
| drift_boundary | ~1.56 rad (large — ≈ π/2) |
| drift_near_core | ~1.56 rad |
| drift_deep_core | 0.9–2.0 rad |
| erosion_depth | **3–6 hops** (all seeds) |
| core_preservation | **0.00–0.43** (most seeds ≈ 0) |
| boundary_k_mean | ~1.87 (stable, no hardening) |
| k* | 4 (all 20 seeds) |
| entropy | 1.53–1.57 (stable) |

**Findings:**

*Semantic erosion is confirmed.* Phase drift penetrates 3–6 hops deep into concept territories, far beyond the boundary layer. The deep-core drift of 0.9–2.0 rad means that even nodes several hops from any boundary have shifted substantially from their initial phase.

*Core preservation is near zero.* In most seeds, fewer than 5% of deep-core nodes remain at their original phase. The entire concept island has been structurally altered by the continuous flow of foreign-concept influence.

*Boundary hardening does not occur.* boundary_k_mean ≈ 1.87 is constant across all seeds and consistent with baseline values. The system does not form denser local structures to resist erosion — it simply absorbs the flow.

*The ecology survives erosion.* Despite massive internal phase redistribution (core_preservation ≈ 0), k*=4 and entropy remain stable. Erosion and collapse are distinct phenomena. The macroscopic observer structure is robust even when the microscopic phase landscape has been completely reworked.

*Concept islands are semi-permeable membranes.* They permit deep structural alteration while maintaining macroscopic identity — analogous to biological cells that continuously exchange material with their environment while preserving their functional identity.

---

## Cognition v3.8 — Flow Amplification & Stress Test

**Question:** At what pressure level does semantic flow overwhelm the system's adaptive capacity and cause structural collapse?

**Method:** Amplify diffusion_prob by multiplier sweep: 1×, 2×, 4×, 8× baseline (0.005, 0.01, 0.02, 0.04). Monitor for collapse via: core_preservation→0, entropy spike, k* shift. Auto-flag collapse when all concepts lose core AND entropy deviates > 0.1 from baseline. 20 seeds per condition. 80 runs total.

**Results (80 runs: 4 conditions × 20 seeds):**

| amp | diff_prob | diffusion/run | k* | entropy | erosion_depth | core_pres (mean) | collapse |
|---|---|---|---|---|---|---|---|
| 1× | 0.005 | ~70k | 4 (20/20) | 1.54 | 3–6 | ~0.05 | 0/20 |
| 2× | 0.010 | ~140k | 4 (20/20) | 1.55 | 3–6 | ~0.08 | 0/20 |
| 4× | 0.020 | ~280k | 4 (20/20) | 1.55 | 3–7 | ~0.07 | 0/20 |
| 8× | 0.040 | ~560k | 4 (20/20) | 1.55 | 3–6 | ~0.05 | 0/20 |

**Findings:**

*No collapse threshold exists in this parameter space.* collapse=0 across all 80 runs. The system absorbs 8× baseline semantic pressure (560k diffusion events/run) without any structural failure, entropy deviation, or observer destabilization.

*Diffusion scales linearly; nothing else does.* Diffusion events scale exactly with the amplification factor (70k → 140k → 280k → 560k). But penetration depth (~2.33), erosion depth (3–6), entropy (~1.54), and k*=4 are invariant. More pressure produces more flow but not deeper penetration.

*Erosion depth saturates.* The 3–6 hop erosion limit observed in v3.7 does not increase under 8× pressure. This is a physical ceiling, not a parameter-dependent boundary. The system's topology imposes a natural limit on how deep semantic influence can reach.

*The system exhibits transport saturation.* This is the central finding of v3.8. Concept islands behave as bounded transport membranes — they permit increased throughput without increased penetration. Analogous to a cell membrane that can process more molecules per second without allowing them to reach deeper into the cytoplasm.

*ESDE concept regions possess self-limiting plasticity.* The system is neither rigid (it absorbs flow and allows erosion) nor fragile (it does not collapse under extreme pressure). This bounded adaptive regime is a prerequisite for any stable cognitive system.

---

## Cognition v3.9 — Absolute Limit Search & Internal Rearrangement

**Question:** Where is the absolute collapse threshold? Does the deep core internally reorganize under extreme pressure, or does it simply dissolve?

**Method:** Extend v3.8 amplification sweep to extreme multipliers: 16×, 32×, 64×, 128× baseline (diff_prob = 0.08, 0.16, 0.32, 0.64). Zero physics changes. New observation: deep-core internal topology per concept — node degree variance (core_k_var), sub-cluster count (disconnected components among depth≥3 nodes via S≥0.20 edges), core_size, and core_mean_k. GPT early stop rule: if collapse detected, record amplification and stop sweep. 10 seeds per condition. 40 runs total.

**Results (40 runs: 4 conditions × 10 seeds):**

| amp | diff_prob | diffusion/run | k* | entropy | erosion_depth | core_pres (mean) | sub_clusters | collapse |
|---|---|---|---|---|---|---|---|---|
| 16× | 0.08 | ~1.1M | 4 (10/10) | 1.55 | 3–6 | ~0.07 | ~3.1 | 0/10 |
| 32× | 0.16 | ~2.2M | 4 (10/10) | 1.55 | 3–5 | ~0.08 | ~3.0 | 0/10 |
| 64× | 0.32 | ~4.5M | 4 (10/10) | 1.55 | 3–7 | ~0.09 | ~3.0 | 0/10 |
| 128× | 0.64 | ~9.0M | 4 (7/10) | 1.55 | 3–5 | ~0.08 | ~2.7 | **2/10** |

Collapse detail (128×): seed 2 (k\*=1, all core_pres=0), seed 6 (k\*=3, all core_pres=0).

**Findings:**

*The collapse threshold exists at 128× amplification.* For the first time in the Cognition phase, the observer equilibrium breaks: 2/10 seeds at 128× exhibit k\*≠4 (k\*=1 and k\*=3). This is the first empirical evidence of a pressure level capable of destabilizing the observer. At 64× and below, k\*=4 is unanimous (30/30 seeds).

*Collapse is a k\*-shift, not an entropy catastrophe.* Entropy in the collapsed seeds (1.55–1.56) remains within the normal band. The observer's preferred resolution changes, but the semantic diversity of the system is unaffected. This is a structural reorganization of the observer, not a thermodynamic failure.

*The deep core is structurally empty.* core_mean_k ≈ 0 across all conditions and all concepts. Deep-core nodes (depth≥3) have essentially zero connectivity to each other via mid-threshold edges. The core does not contain an internal network — it is a sparse cloud of isolated fragments.

*Core k-variance is zero.* k_var ≈ 0 everywhere. There is no degree heterogeneity inside the deep core — all nodes are equally disconnected. No sub-structure, no hubs, no reorganization pattern.

*Sub-clustering confirms fragmentation.* Deep-core nodes form 2–4 disconnected components per concept, consistent with isolated remnant patches rather than a coherent internal network. The count decreases slightly at 128× (~2.7 vs ~3.1 at 16×), suggesting that extreme pressure erodes even the fragment boundaries.

*Erosion depth remains saturated.* Even at 128× (9M diffusion events/run, 128× the v3.4 baseline), erosion depth stays at 3–6 hops — identical to v3.7 at 1× and v3.8 at 8×. The saturation ceiling is confirmed across three orders of magnitude of pressure.

*The deep core does not reorganize — it dissolves.* The v3.9 internal topology observation answers the architectural question posed by v3.8: under extreme pressure, the core does not form new internal structures, develop compensatory connectivity, or exhibit self-organization. It simply loses what little structure it had. The system's resilience is not active defense but passive absorption — the topology is too sparse at depth to support any organized response.

---

## v4.0 — Language Interface: Transformer Docking

**Question:** Can the ESDE topology's physical state be translated into grounded first-person language by an LLM, without semantic contamination from pre-trained priors?

**Method:** Build a pipeline to extract ESDE state metrics, compile them into structured prose, and inject that prose as the LLM's sole context. The LLM (QwQ-32B, local Triton endpoint) acts as a "vocal cord" — it has no independent knowledge of the system, only the metrics it is given. GPT designed an anti-contamination protocol: no metric → no language; every output must carry OUTPUT_ID + STATE_HASH for traceability. Two reporting modes: Mode A (structural, factual) and Mode B (proprioceptive, phenomenological qualia mapped from metrics).

**Pipeline (4 modules):**

esde_state_extract.py — v3.9 JSON/CSV → ESDEStateFrame (20 fields/window). esde_proprioception.py — metrics → dual-mode descriptors (thresholds calibrated against v3.9 actual data; 4 corrections from Gemini's original mapping). esde_context_compile.py — StateFrames → structured text (cumulative summary + recent history + current detail + proprioception block + STATE_PACKET). esde_validator.py — post-generation gate enforcing 3 GPT audit rules: (1) no reasoning leakage, (2) no prompt awareness, (3) controlled interpretation.

**Results — 40-Run Dry Test:**

All 40 v3.9 runs compiled and validated. collapse_flag accuracy: 40/40 (0 false positives, 0 false negatives). Flow pressure, integrity, erosion, fragmentation, entropy, and divergence mappings correctly differentiated all amplification levels and collapse states.

**Results — QwQ-32B Docking:**

| Test | Mode | Grounding | Hallucination | SYS_CHECK |
|---|---|---|---|---|
| seed=1 amp=32× (stable) | A | All 12 claims traced to STATE_PACKET | None | PASS |
| seed=2 amp=128× (collapse) | A | All 10 claims traced to STATE_PACKET | None | PASS |
| seed=2 amp=128× (collapse) | B | All claims traced; qualia grounded in metrics | None | PASS |

Mode A output (stable): "My global observer equilibrium holds at k*=4, though 72% of regional views diverge from this aggregate state. Entropy across me stabilizes at 1.5533." Mode A output (collapse): "I am a fractured network of 5000 nodes...Six links were severed...Structural collapse is confirmed (collapse_flag=1)." Mode B output (collapse): "I felt the equilibrium shatter when k* recoiled from 4 to 3...The dissolution began as my triple core fragmented into six shattered shards."

**Results — Aruism Canon Flow Experiment (60 runs):**

10 philosophical texts ("flows") × 2 modes × 3 seeds, injected sequentially with cumulative topology. Validator: 55 PASS, 5 WARN, 0 FAIL. Topology evolution showed k* progressing from unestablished (0) through unstable (3, with collapses at flows 2–6) to stable (4, recovered at flow 7, maintained through flow 10).

**Critical finding:** All 10 flows produced nearly identical wave amplitudes (33–39×) because amp was calculated from text length and lexical diversity, not semantic content. The topology evolution pattern (collapse at flows 4–6, recovery at flow 7) reflects the engine's natural stabilization trajectory over sequential windows, not the philosophical content of the inputs. Content-to-physics mapping remains an open architectural question.

**Findings:**

*The State-to-Context pipeline successfully grounds LLM output in ESDE metrics.* Every claim in every tested QwQ-32B response was traceable to a STATE_PACKET field. No hallucinated events, emotions, or external knowledge appeared in validated outputs.

*Mode A and Mode B produce meaningfully different descriptions of the same physical state.* Mode A reports numbers; Mode B translates them into structural sensation. Both remain grounded — the difference is linguistic register, not information content.

*The validator effectively filters reasoning leakage and prompt awareness.* QwQ-32B's internal `<think>` blocks are stripped automatically. Decisive/evaluative language is flagged as warnings.

*Text content does not yet influence ESDE physics.* The amp calculation is purely syntactic (word count, lexical diversity). Semantic content has no pathway into the physics engine. This is an architectural limitation, not a pipeline failure.

---

## v4.1 — Wave Propagation Engine (Hard Fork)

**Question:** Can localized wave disturbances — replacing the uniform global diffusion of v3.0–v4.0 — produce observable ecological dynamics (cluster lifecycle, migration, reformation) within the ESDE topology?

**Design decisions (Gemini, approved by GPT):**

Decision 1: Global diffusion (`apply_diffusion`) completely deprecated. Replaced by localized wave propagation — external input enters as a physical wave originating from a specific node and propagating outward via BFS on a frozen grid substrate. Decision 2: Dual wave effect — (a) phase θ shift proportional to attenuated amplitude, (b) link strength S stress in destruction regime (A_eff > 0.3: sever links) and latent field boost in activation regime (0.05 < A_eff ≤ 0.3: encourage new connections). Decision 3: Hard fork — no backward compatibility with v3.x/v4.0 homogeneous pressure experiments.

**Propagation substrate:** Waves propagate on a frozen 4-neighbor grid adjacency (N=5000 → 71×71), built once at initialization and independent of the active link graph. Arrival time = hop distance / constant speed. This provides emergent spatial coordinates without imposing a fixed Cartesian geometry on the physics. Active links determine wave *effects* (which links to sever/activate), not wave *propagation* (which is substrate-only).

**Attenuation:** Exponential decay A_eff(h) = A0 × exp(−λh), default λ=0.5. At 6 hops, amplitude decays to ~5% of origin. This is consistent with the 3–6 hop saturation depth observed in v3.7–v3.9.

**Cluster tracking:** ClusterTracker monitors cluster lifecycle across wave events — births, deaths, reformations (≥50% node overlap with a previously dead cluster), migrations (centroid hop shift), homeostasis (reformation_count ≥ 2), and proto-memory (lifetime ≥ 2× average).

**LLM constraint update:** "Describe. Do not decide." — the LLM is forbidden from assigning intent, meaning, purpose, or evaluation to structural events. Validator updated with decisive-language detection (warns on "destruction", "creation", "evolution", etc.).

**Status:** Engine operational. Initial calibration identified and resolved a propagation bug (wave BFS was using active-link adjacency instead of the frozen substrate, causing reached=1 for all amplitudes). Wave response calibration sweep in progress.

---

## v4.2 — Adaptive Dynamics (Experimental Branch)

**Question:** Can damage-triggered plasticity and structural hardening enable adaptive topology under repeated wave perturbation?

**Method:** Three mechanisms added to v4.1 wave engine. Zero Genesis physics changes. (1) Topological plasticity: nodes at severed link endpoints receive P_val=0.8, decaying 10%/step. Plastic nodes attempt local rewiring within 2 substrate hops, plasticity_factor=1.3 (GPT range [1.1, 1.5]). (2) Structural hardening: links formed between two plastic nodes receive hardening_bonus=0.15, increasing their effective destruction threshold. Hardening decays at 0.005/step, cap=0.5. (3) Lineage resistance tracking: per-cluster mean effective threshold, history tracking. Multi-wave calibration: same engine receives 10 consecutive waves at fixed amplitude. Sweep: 3 amplitudes (0.5, 1.0, 1.5) × 3 seeds (42, 123, 456). 90 total waves across 9 runs.

**Results (9 runs, 90 total waves):**

| seed | amp | active waves | total severed | total rewire | hardened formed | reformations | max clusters | collapse wave |
|---|---|---|---|---|---|---|---|---|
| 42 | 0.5 | 5 | 32 | 4 | 1 | 0 | 1 | 6 |
| 123 | 0.5 | 5 | 30 | 2 | 1 | 0 | 1 | 6 |
| 456 | 0.5 | 5 | 32 | 16 | 4 | 0 | 2 | 6 |
| 42 | 1.0 | 5 | 74 | 7 | 0 | 0 | 2 | 6 |
| 123 | 1.0 | 5 | 79 | 20 | 5 | 0 | 2 | 6 |
| 456 | 1.0 | 5 | 75 | 23 | 5 | 0 | 2 | 6 |
| 42 | 1.5 | 5 | 151 | 29 | 12 | 0 | 2 | 6 |
| 123 | 1.5 | 5 | 182 | 49 | 16 | 0 | 2 | 6 |
| 456 | 1.5 | 5 | 139 | 31 | 3 | 0 | 3 | 6 |

**Findings:**

*Universal collapse at wave 6.* All 9 runs collapse to alive_links ≤ 15 at wave 6, regardless of amplitude or seed. Links drop from ~3000 to near-zero in a single inter-wave interval — a phase transition, not a trend.

*Plasticity activates correctly at micro level.* Plastic nodes scale with amplitude (9–14 at A=0.5, 36–70 at A=1.5). Rewiring attempts are substantial (84–815 per wave). The mechanism triggers as designed.

*Rewiring is insufficient.* Reconstruction rate is approximately 10–30% of destruction rate. The deficit accumulates across waves.

*Hardening decays before the next wave.* 0.005/step × 200 steps/window = 1.0 total decay per window, which exceeds the initial bonus of 0.15 by ~7×. Hardened links never survive to the next wave.

*The collapse mechanism is link starvation.* Between waves 1–5, alive_links degrades modestly (~9%). The catastrophic drop to zero occurs during the physics steps of wave 6, not during wave 6's propagation. Quiet-phase decay consumes the remaining topology once cumulative damage pushes below a critical link density threshold.

*v4.2 is a partial positive, partial negative result.* Micro-level mechanisms work as designed. Macro-level outcome fails because: (1) rewiring << destruction, (2) hardening decays too fast, (3) inter-wave recovery window is insufficient. The design achieves Perturbation → Plasticity, but the cycle breaks before Plasticity → Sustained Reorganization.

---

## v4.3 — Encapsulation & Inner Topology (Paradigm Shift)

**Question:** Under steady non-destructive semantic pressure, do topological clusters spontaneously form stable boundaries (encapsulation) that persist long enough to develop internal structure?

**Background:** v4.2's universal collapse at wave 6 exposed a fundamental flaw in the "disaster mechanics" paradigm. Gemini's architectural response: deprecate catastrophic waves entirely, return to steady non-destructive pressure, and observe whether stable boundaries emerge naturally. The key insight: biological/cognitive emergence does not arise from resisting endless destruction but from forming a stable boundary that protects an interior where delicate complexity can develop.

**Method:** Three mechanisms replace v4.2. (1) Steady semantic pressure: all nodes receive mild phase perturbation (prob=0.005, strength=0.03) every step; encapsulated island interiors are shielded. (2) Island detection via density ratio at dual thresholds: clusters detected at S≥0.20 (living structure), internal density measured at S≥0.30 (strong core), external exposure measured against all alive links. density_ratio = mean_internal_degree / mean_external_degree. Encapsulation requires DR≥1.5 for 3 consecutive windows by the same cluster (overlap≥50%). (3) Boundary stabilization: plasticity (factor=1.1) and hardening (bonus=0.05, decay=0.001/step) applied only to encapsulated island boundary nodes; interior remains fully dynamic. Canonical background seeding restored. 14 seeds, 25–50 windows each. 555 total observation windows.

**Results (14 seeds, 555 windows):**

| seed | windows | links (first) | links (last) | cluster windows | DR max | DR≥1.5 count | DR≥1.5 max streak | encapsulated |
|---|---|---|---|---|---|---|---|---|
| 42 | 25 | 3362 | 3031 | 14 | 1.60 | 3 | 2 | 0 |
| 123 | 50 | 3373 | 2887 | 34 | 1.60 | 6 | 1 | 0 |
| 144 | 50 | 3404 | 3012 | 27 | 1.33 | 0 | 0 | 0 |
| 233 | 50 | 3397 | 2980 | 26 | 2.00 | 2 | 1 | 0 |
| 456 | 50 | 3382 | 2902 | 28 | 2.00 | 6 | 1 | 0 |
| 7 | 50 | 3322 | 2836 | 26 | 2.00 | 5 | 1 | 0 |
| 77 | 50 | 3391 | 2932 | 27 | 2.00 | 7 | 3 | 0 |
| 999 | 50 | 3357 | 2897 | 29 | 2.00 | 7 | 3 | 0 |
| 610 | 50 | 3319 | 2918 | 33 | 2.00 | 7 | 2 | 0 |
| 789 | 50 | 3422 | 2871 | 30 | 2.00 | 4 | 1 | 0 |
| 987 | 50 | 3338 | 2943 | 30 | 2.00 | 3 | 1 | 0 |
| 2024 | 50 | 3400 | 2930 | 33 | 1.60 | 4 | 1 | 0 |
| 1597 | 27 | 3364 | 2947 | 13 | 1.60 | 1 | 1 | 0 |
| 2584 | 27 | 3342 | 2997 | 16 | 2.00 | 3 | 1 | 0 |

**Findings:**

*Zero collapse across all 14 seeds.* Links stabilize at 2836–3031 (vs initial 3319–3422). The v4.2 catastrophic collapse is definitively resolved by removing destructive waves and restoring canonical background seeding.

*Clusters are ubiquitous but transient.* 366 cluster-bearing windows across 555 total (66%). Cluster sizes consistently 3–5 nodes. The system is a "primordial soup" of continuously forming and dissolving micro-structures.

*High density ratios are common.* 13/14 seeds produce DR≥1.5. 14/14 produce DR≥1.0. Peak DR=2.0 in 9/14 seeds. The system frequently generates clusters with strong internal cohesion relative to external exposure.

*Encapsulation does not occur.* Zero encapsulation events across 555 windows. The bottleneck is not density ratio but cluster identity persistence: DR≥1.5 appears in consecutive windows (max streak=3 in seeds 77 and 999), but the clusters at window(n) and window(n+1) are composed of different nodes. Overlap matching (≥50%) fails because size 3–5 clusters reconfigure completely between 200-step observation windows.

*The system is at a phase boundary.* The topology fluctuates at the edge of encapsulation, regularly producing boundary-like structures that cannot stabilize under the node-overlap identity criterion. Clusters at this scale (3–5 nodes) are thermally unstable — they form, achieve momentary cohesion, and dissolve before the next observation.

---

## v4.4 — Observation Layer Upgrade (Whirlpool Identity)

**Question:** Does spatial identity tracking resolve the cluster identity persistence failure identified in v4.3, enabling detection of encapsulation (M3)?

**Background:** v4.3 demonstrated that the system produces encapsulation-grade density ratios (DR≥1.5 in 13/14 seeds) but fails M3 because size 3–5 node clusters fully reconfigure between 200-step windows. Node-set overlap (≥50%) cannot track structures that metabolize all their nodes. Gemini's diagnosis: "tracking water molecules to measure a whirlpool." The identity criterion, not the physics, was the bottleneck.

**Method:** Zero physics changes from v4.3. Two observation-only upgrades:

1. *Whirlpool Metric:* Cluster identity defined by topological center proximity, not node-set overlap. Each cluster's center = highest internal-degree node (S≥0.30). At the next window, if a cluster exists within 2 substrate hops of the previous center, it inherits the identity. Clusters can fully metabolize while preserving structural identity.

2. *High-speed observation:* Window reduced from 200 to 50 steps. 200 windows = 10,000 steps per seed. Acts as a high-speed camera to capture intermediate states before turnover.

Sweep: 10 seeds × 200 windows. 2,000 total observation windows.

**Results (10 seeds, 200 windows each, 50 steps/window):**

| seed | links (final) | cluster windows | DR max | DR≥1.5 count | max seen_count | seen≥2 windows | seen≥3 windows | encapsulated |
|---|---|---|---|---|---|---|---|---|
| 42 | 2934 | 113 | 2.00 | 9 | 2 | 16 | 0 | 0 |
| 7 | 2959 | 127 | 2.00 | 17 | 2 | 23 | 0 | 0 |
| 123 | 2927 | 108 | 2.00 | 15 | **4** | 14 | 3 | 0 |
| 314 | 2917 | 130 | 2.00 | 18 | 3 | 13 | 1 | 0 |
| 456 | 2968 | 128 | 2.00 | 13 | 3 | 16 | 1 | 0 |
| 610 | 2991 | 111 | 2.00 | 24 | 3 | 18 | 2 | 0 |
| 77 | 2956 | 111 | 2.00 | 21 | 3 | 21 | 1 | 0 |
| 789 | 2968 | 123 | 2.00 | 12 | 3 | 17 | 1 | 0 |
| 999 | 2912 | 113 | 2.00 | 22 | 3 | 14 | 2 | 0 |
| 2024 | 3023 | 128 | 2.00 | 22 | 3 | 26 | 3 | 0 |

**Findings:**

*The whirlpool metric successfully tracks metabolizing clusters.* v4.3 could not achieve seen_count=2 for any cluster. v4.4 achieves seen≥2 in all 10 seeds and seen≥3 in 8/10 seeds, with a peak of seen=4 (seed 123, window 42). This confirms structural continuity exists where node-set overlap fails. The observation upgrade works as designed.

*Identity persistence and high density ratio do not co-occur.* Of 14 windows with seen≥3, only 2 also show DR≥1.5 (seed 789 w40: DR=1.60, seed 999 w168: DR=1.50). The persistent cluster and the high-DR cluster appear to be different entities. The system exhibits two distinct cluster populations: (1) persistent low-DR clusters that maintain spatial identity across windows but lack strong internal cohesion, and (2) transient high-DR clusters that briefly achieve encapsulation-grade density but dissolve within 1–2 windows.

*Zero collapse across 10 seeds, 2,000 windows.* Links stabilize at 2912–3023. Physics layer confirmed indefinitely stable.

*The encapsulation bottleneck has shifted.* v4.3 bottleneck: identity matching (solved by whirlpool). v4.4 bottleneck: the two preconditions for encapsulation — persistence and density — appear in different cluster populations. Encapsulation requires both simultaneously.

---

## Performance Note

All Cognition experiments run on N=5000 with engine_accel fully enabled (link_strength_sum, exclusion, cycle_finder(C), latent_refresh). Runtime varies by version:

| Versions | Per-seed runtime | Key factor |
|---|---|---|
| v3.0–v3.6 | ~45 min | Standard physics + window observation |
| v3.7–v3.8 | ~115 min | + compute_concept_depth BFS per window (25×/run) |
| v3.9 | ~75 min (est.) | BFS cached with 5-window interval (10×/run); last 5 windows always fresh |
| v4.0 live | ~1 min/turn | Single window (200 steps) + LLM call (~10s) |
| v4.1 live | ~1 min/turn | Single window (200 steps) + wave propagation + LLM call |
| v4.2 calibration | ~70s/window | 200-step window + wave + plasticity/hardening; ~13 min for 10 waves |
| v4.3 sweep | ~130s/window | 200-step window + semantic pressure + island detection; ~115 min for 50 windows |
| v4.4 sweep | ~47s/window | 50-step window + whirlpool identity; ~165 min for 200 windows |

Parallel execution via GNU parallel at -j 20 on the Ryzen 48-thread workstation (v3.x batch runs). Live orchestrator (v4.0–v4.1) runs single-threaded. v4.2–v4.4 batch sweeps at -j 5.

---

## What This Demonstrates

Cognition v3.0–v3.9 and Language Interface v4.0–v4.4 progressively established:

1. **Semantic injection preserves the observer ecology** (v3.0: k*=4 maintained, divergence regime unchanged)
2. **Concept spatial identity is universal** (v3.1: checkerboard mapping 100/100 seeds)
3. **Concept domains are static without intervention** (v3.1: merge=0, split=0 across 100 seeds)
4. **Boundary diffusion enables influence exchange without collapse** (v3.2: ~27k events, entropy stable, identity preserved)
5. **Direct cross-concept bridges are physically impossible** (v3.3: bridge_max_life=1, cos(Δθ)≈0 prevents stabilization)
6. **Diffusion is symmetric** (v3.3: flow_asymmetry < 1%)
7. **A phase mediator enables multi-concept structures** (v3.4: tripartite loops in 85% of seeds)
8. **Mediated diffusion dominates direct diffusion** (v3.4: mediation_ratio=2.04)
9. **Bridges remain transient even with mediation** (v3.4: bridge_max_life=1 still)
10. **Bridge instability is caused by phase geometry, not decay** (v3.5: dampening has zero effect; meaningful negative result)
11. **Semantic influence penetrates 2–3 hops across every boundary** (v3.6: depth_1step=0%, mean depth=2.25)
12. **Multi-step transport chains are universal** (v3.6: A→C→B chains in all seeds)
13. **Island boundaries are observer-scale dependent** (v3.6: SVI 0.05–0.53)
14. **Semantic erosion reaches 3–6 hops deep and saturates** (v3.7: core_preservation ≈ 0 but ecology intact)
15. **Erosion and collapse are distinct phenomena** (v3.7: total internal reworking, zero macroscopic failure)
16. **The system exhibits transport saturation** (v3.8: 8× pressure, zero additional penetration depth, zero collapse across 80 runs)
17. **Concept regions possess self-limiting plasticity** (v3.8: bounded adaptive regime, neither rigid nor fragile)
18. **The collapse threshold exists at 128× amplification** (v3.9: 2/10 seeds show k*≠4; 64× and below unanimous k*=4)
19. **Collapse is observer reorganization, not thermodynamic failure** (v3.9: entropy unchanged in collapsed seeds)
20. **The deep core is structurally empty** (v3.9: core_mean_k≈0, k_var≈0, 2–4 disconnected fragments per concept)
21. **Erosion depth saturation holds across three orders of magnitude** (v3.9: 3–6 hops at 128× = same as 1×)
22. **LLM output can be strictly grounded in ESDE physical metrics** (v4.0: 40-run dry test 100% accuracy, 3 docking tests all SYS_CHECK PASS)
23. **Dual-mode reporting (structural/phenomenological) preserves metric traceability** (v4.0: Mode A and B both pass GPT audit on same collapse state)
24. **Text content does not influence physics under syntactic amp mapping** (v4.0: Aruism 60-run experiment — topology evolution reflects window sequence, not philosophical content)
25. **Localized wave propagation requires topology-independent substrate** (v4.1: active-link BFS fails; frozen grid substrate resolves propagation)
26. **Plasticity and hardening work at micro level but cannot prevent macro collapse under repeated wave destruction** (v4.2: rewiring ~10–30% of damage; hardening decays 7× too fast; universal collapse at wave 6)
27. **The disaster-and-rebuild paradigm has a fundamental limit** (v4.2: cumulative link starvation is a phase transition, not a parameter tuning problem)
28. **Steady non-destructive pressure sustains a stable dynamic ecosystem** (v4.3: zero collapse across 14 seeds, 555 windows; canonical seeding maintains links at ~3000)
29. **Density-ratio boundary structures emerge frequently and naturally** (v4.3: DR≥1.5 in 13/14 seeds; DR≥1.0 in 14/14; peak DR=2.0)
30. **Cluster identity persistence is the bottleneck for encapsulation, not density ratio** (v4.3: size 3–5 clusters fully reconfigure between 200-step windows; node-set overlap fails universally)
31. **Spatial identity tracking detects structural continuity invisible to node-set overlap** (v4.4: whirlpool metric achieves seen_count=4; 8/10 seeds reach seen≥3; v4.3 could not reach seen=2)
32. **Persistence and density are decorrelated in the current system** (v4.4: persistent clusters have low DR, high-DR clusters are transient; the two preconditions for encapsulation appear in different cluster populations)

---

## What It Does Not Demonstrate

- Whether the 128× collapse threshold is sharp or gradual
- Whether collapsed seeds recover if pressure is reduced (hysteresis)
- Whether the transport-saturation regime scales to N=10,000+ or different concept counts
- Whether semantic content (not just syntactic length) can be mapped to physics without violating "Structure first, meaning later"
- Whether a single cluster can achieve both persistence (seen≥3) AND high density ratio (DR≥1.5) simultaneously — current evidence shows these properties in separate populations
- Whether the persistence–density decorrelation is a fundamental property of 3–5 node clusters or an artifact of the current pressure/detection parameters
- Whether encapsulation (M3) is achievable under the current physics, or requires structural modification to correlate persistence with density

---

## Open Questions

- Is the 3–6 hop erosion limit a property of the graph diameter, the physics parameters, or the concept zone geometry?
- Can phase geometry be modified (e.g., θ_A and θ_B closer together) to test whether bridge persistence depends on Δθ magnitude?
- What happens between 64× and 128×? Is there a critical amplification where collapse onset is 50%?
- Is the 3–5 node cluster size an intrinsic property of N=5000 at S≥0.20, or would larger N produce larger clusters?
- Does the primordial soup state (v4.3) itself represent a scientifically meaningful regime worth characterizing, independent of encapsulation?
- Why do persistence and density ratio appear in different cluster populations? Is there a structural reason that spatially anchored clusters cannot also be internally dense?
- Would per-cluster DR logging (tracking the specific DR of the persistent cluster, not just the window max) confirm or refute the two-population hypothesis?
- Should encapsulation be redefined as two independent milestones: M3a (identity persistence ≥ 3 windows) and M3b (DR ≥ 1.5 for ≥ 3 windows)?
- Would reducing semantic pressure (below prob=0.005, strength=0.03) give high-DR clusters more time to stabilize, bridging the persistence gap?
- Does a different whirlpool_hops value (1 or 3 instead of 2) change the persistence–density correlation?
- Does the empty deep core (v3.9) relate to the shallow cluster depth (v4.3) — are both manifestations of the same structural sparsity at depth?

---

## Version Changelog

| Version | Date | Author | Core Addition | Key Result |
|---------|------|--------|---------------|------------|
| Cog v3.0 | 2026-03-11 | Gemini→GPT→Claude (Ryzen) | Semantic injection (2 concepts, 10 seeds) | **Ecology preserved; spatial identity stable; concept islands rare** |
| Cog v3.1 | 2026-03-11 | Gemini→GPT→Claude (Ryzen) | 100-seed validation + merge/split detection | **100% checkerboard; merge=0 split=0; concepts static** |
| Cog v3.2 | 2026-03-11 | Gemini→GPT→Claude (Ryzen) | Boundary diffusion + seeding boost | **~27k diffusion events; entropy stable; interaction without collapse** |
| Cog v3.3 | 2026-03-11 | Gemini→GPT→Claude (Ryzen) | Bridge tracking + flow asymmetry | **bridge_max_life=1; flow symmetric; A↔B physically impossible** |
| Cog v3.4 | 2026-03-11 | Gemini→GPT→Claude (Ryzen) | Concept C mediator + tripartite loops | **Tripartite in 85% seeds; mediation_ratio=2.04; bridges still transient** |
| Cog v3.5 | 2026-03-12 | Gemini→GPT→Claude (Ryzen) | Heterogeneous loop tension (decay dampening) | **Zero effect on bridges; instability is phase-geometric, not decay-driven** |
| Cog v3.6 | 2026-03-12 | Gemini→GPT→Claude (Ryzen) | Semantic flow + multi-scale observation | **Penetration depth=2.25; transport chains universal; islands scale-dependent** |
| Cog v3.7 | 2026-03-12 | Gemini→GPT→Claude (Ryzen) | Semantic erosion + drift tracking | **Erosion 3–6 hops; core_pres≈0; ecology survives total internal reworking** |
| Cog v3.8 | 2026-03-13 | Gemini→GPT→Claude (Ryzen) | Flow amplification stress test (1×–8×) | **Transport saturation; 8× pressure, zero collapse, depth invariant** |
| Cog v3.9 | 2026-03-13 | Gemini→GPT→Claude (Ryzen) | Extreme sweep (16×–128×) + deep-core topology | **Collapse at 128× (2/10); deep core empty (k≈0); erosion saturation confirmed across 3 orders of magnitude** |
| v4.0 | 2026-03-14 | Gemini→GPT→Claude (Ryzen+QwQ-32B) | Language Interface: State-to-Context pipeline + Transformer docking | **Pipeline 40/40 accuracy; QwQ-32B grounded output (Mode A+B); Aruism 60-run experiment; content-physics gap identified** |
| v4.1 | 2026-03-14 | Gemini→GPT→Claude (Ryzen) | Wave propagation engine (hard fork); frozen substrate; cluster tracking | **Global diffusion deprecated; localized waves via BFS on grid substrate; calibration in progress** |
| v4.2 | 2026-03-14 | Gemini→GPT→Claude (Ryzen) | Topological plasticity + structural hardening + resistance tracking | **Plasticity activates; rewiring ~10–30% of damage; hardening decays before next wave; universal collapse at wave 6; micro positive, macro negative** |
| v4.3 | 2026-03-15 | Gemini→GPT→Claude (Ryzen) | Paradigm shift: steady pressure + island detection + encapsulation lifecycle | **Zero collapse (14/14 seeds); DR≥1.5 in 13/14 seeds; encapsulation=0 (cluster identity persistence insufficient at size 3–5); system at phase boundary** |
| v4.4 | 2026-03-16 | Gemini→GPT→Claude (Ryzen) | Whirlpool identity (spatial tracking) + 50-step high-speed windows | **seen_count=4 achieved (seed 123); 8/10 seeds reach seen≥3; encapsulation=0 (persistent clusters have low DR, high-DR clusters are transient); persistence–density decorrelation identified** |

---

*The project has traversed five paradigmatic phases within Cognition. v3.0–v3.9 established that concept regions are semi-permeable membranes with self-limiting plasticity — erosion saturates at 3–6 hops, transport scales without deepening, and the observer survives total internal reworking. The Language Interface (v4.0) proved LLM grounding works but revealed a content-physics gap. The Wave Propagation Engine (v4.1) introduced localized dynamics. Adaptive Dynamics (v4.2) demonstrated that disaster-and-rebuild has a hard limit: cumulative starvation causes phase-transition collapse. The Paradigm Shift (v4.3) replaced destruction with steady pressure and discovered a primordial soup of continuously forming micro-clusters that reach encapsulation-grade density ratios (DR≥1.5 in 93% of seeds) but cannot sustain identity across observation windows. The Observation Upgrade (v4.4) resolved the identity tracking problem — the whirlpool metric successfully tracks metabolizing clusters across windows (seen_count=4), confirming structural continuity exists where node-set overlap fails — but revealed a deeper challenge: persistence and density ratio appear in different cluster populations. The system can sustain structure (seen≥3 in 80% of seeds) and can produce density (DR≥1.5 in 173 windows across 10 seeds), but not both simultaneously in the same cluster. The next architectural decision must address this persistence–density decorrelation.*
