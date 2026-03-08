# ESDE: Observer Physics

**From Static Graphs to Self-Observing Worlds**

*Project: ESDE (Endogenous Stochastic Differential Equation) Framework*
*Team: Gemini (Architect) / GPT (Audit) / Claude (Implementation)*
*Last updated: March 9, 2026*

---

## What We Are Trying to Do

We are building a minimal computational universe from first principles to test a specific claim: that persistent, self-sustaining structure can emerge from nothing more than local energy exchange rules on a graph, without being designed in.

The ESDE framework proposes that physical law is not arbitrary — that the parameters governing a universe converge toward configurations that maximize structural self-explanation. Genesis is the experimental sandbox where we test this. We start with 200 nodes, zero energy, zero connections, and a handful of simple rules. Then we inject energy, step back, and watch.

The central question across all versions has been: **What is the minimum set of local rules that produces durable, cyclic, self-renewing structure?**

This is not a simulation of known physics, chemistry, or biology. It is a search for the structural skeleton beneath all three — the conditions under which "things that persist" emerge from "things that happen."

---

## The Three Roles

The project operates as a three-agent collaboration:

- **Gemini (Architect)** designs each version's physics, mechanisms, and experimental conditions.
- **GPT (Audit)** reviews designs before implementation, identifies risks, mandates ablation controls, and specifies success criteria.
- **Claude (Implementation)** builds the code, runs experiments, reports results without editorializing, and flags discrepancies between prediction and observation.

No agent has unilateral authority. Design must be audited before implementation. Results are reported honestly regardless of whether they confirm hypotheses.

---

## Project Phases

The project progresses through stages, each building on the last:

```
Genesis  — Can an observer emerge? (COMPLETE)
  ↓
Ecology  — How do multiple observers interact? (IN PROGRESS)
  ↓
Concept  — Can observers form shared representations? (FUTURE)
  ↓
Language — Can structural concepts become communicable? (FUTURE)
```

---

## The Stack

Each version added one layer. Nothing was removed.

```
v0.3  Resonance       Closed paths decay slower (topology → persistence)
v0.4  Phase           Local oscillation inside loops (persistence → rhythm)
v0.5  Chemistry       State transitions gated by physics (rhythm → reaction)
v0.6  Patches         Background energy + exothermic decay + ghost links
v0.7  Controller      Adaptive parameter tuning (Axiom X)
v0.8  Dual Layer      Latent field enables link birth in quiet
v0.9  Auto-Growth     Loop participation strengthens links via latent cost
v1.0  Alignment       Growth-zone bias concentrates seeding near strong topology
─── characterization (no new mechanics) ───
v1.0s Bias Sweep      Map cycle rate × explainability across bias strength
v1.1  Noise Tolerance Identify safe bands and collapse cliffs for 3 noise knobs
v1.2  Ridge Map       2D heatmap locates the operating envelope
v1.3  Refinement      Fine grid confirms ridge is a band, not a point
v1.4  Validation      Long-run: 30/30 seeds cycle, η > 1.4, zero collapse
─── diversification ───
v1.5  Differentiation Observe: 2 cycle types, 1.8 islands, 60% coexistence
v1.6  Yield Asymmetry Energy bias shifts frequency, not type count (still 2)
v1.7  Topography      Fertility field creates niches but not new paths (still 2)
v1.8  Intrusion       Boundary perturbation + measurement instrumentation fixes
v1.8-O C′ Reframing   Contextual labels: 27 signatures, 58% drift, 5+ C′ types
─── adaptive observation (no new mechanics) ───
v1.8-O2 Raw Logging   Full context tuples for post-hoc k-selection
v1.9  Axiom X Observer k*=2 (low noise) → k*=4 (high noise); J increases with intrusion
v1.9c k=3 Tightened    Island Scale bins revised; k=3 wins 48% of windows
v1.9d Reproducibility  150 runs: k=3→k=4 transition reproducible across plb/seed
v1.9e-f Diagnostics   Margin analysis, switch causes, stability rule comparison
v1.9g  Observer Frozen hyst_0.01 adopted; k*=4 universal; 120 runs, 100% agree
─── scale expansion (no new mechanics) ───
Scale N=1000      Observer holds k=4 but agree drops to 60% at rate=0.001
Scale N=2000      Agree 70%; switch rate peaks; None ratio peaks — worst point
Scale N=5000      Agree recovers to 80%; None ratio returns to N=1000 level
Scale N=10000     rate=0.002: 100% agree; rate=0.001: 70% (marginal regime)
═══ GENESIS COMPLETE ═══
─── ecology (no new physics, observation only) ───
Eco v2.1  Region Observer    2x2 partition; local k* more stable than global
Eco v2.2  Temporal Tracking  Persistence streaks, divergence ratio 40–68%
          engine_accel       link_strength_sum O(N)→O(deg); 1.8–3.7× speedup
```

Each layer addresses a specific structural barrier identified by observation. No layer was added speculatively — every addition was driven by a measured failure mode.

---

## What the System Does Now

Starting from 200 disconnected, empty nodes:

1. **Injection** floods the system with energy and random connections
2. **Resonance** identifies closed loops and protects their links from decay
3. **Phase dynamics** synchronize oscillators within loops
4. **Chemistry** converts compatible neighbors into compounds when energy, topology, and phase align
5. **Decay** destroys everything that isn't topologically protected
6. When injection stops and the **quiet phase** begins:
   - Links decay but are continuously reborn from the **latent field**, modulated by local fertility
   - Newborn links participate in loops and **grow stronger** by consuming latent potential
   - Some links reach reaction threshold (S > 0.3), with peak observed strength of 0.74
   - Background micro-injection seeds A/B states, biased toward active growth zones
   - **Boundary intrusion** gradually shifts connectivity across island borders
   - When a strong link connects an A/B node to a C node with sufficient energy and phase sync, **reactions occur**
   - C nodes eventually decay back to Dust, releasing energy
   - Dust nodes get re-seeded, re-linked, and react again
   - **Individual nodes complete full transformation cycles**: C → Dust → A → C
   - Multiple **active islands** coexist (mean 1.8, up to 9 simultaneously)
   - **58% of cycles involve structural context drift** — a node begins its cycle in one topological environment and completes it in another

The system metabolizes, coexists in parallel domains, and **differentiates** — not by having different chemical reactions, but by executing the same reactions in structurally distinct environments. There are 2 chemical elements but 27 observed structural cycle signatures.

The system also **selects its own observation resolution.** An Axiom X postprocessor with hysteresis (T=0.01) evaluates 5 levels of structural context labeling per window and commits to the resolution that maximizes diversity without over-fragmenting. The observer universally selects **k=4** (resonance position + boundary status + island scale + intrusion exposure) as the optimal resolution.

---

## Key Findings (Summary)

1. **Metabolic cycles emerge** from mechanism stacking without being programmed (v0.9)
2. **The metabolic regime occupies a characterizable band** in parameter space, robust along energy/latent axes but fragile along connectivity (v1.0–v1.4)
3. **Diversity does not require expanding the ontology** — 2 elements produce 27 structural cycle signatures because structure and chemistry are orthogonal dimensions (v1.5–v1.8-O)
4. **The observer resolution converges to a stable fixed point** — k=4 is universally preferred, confirmed by hysteresis stabilization (v1.9g)
5. **Observer physics is scale-stable** — k=4 persists from N=200 to N=10,000; rate=0.002 achieves 100% agreement at largest scale (Scale expansion)
6. **Genesis is complete** — all five completion criteria satisfied (Genesis completion)
7. **The global observer is a lossy compression** of richer local structure — regional observers are more stable than their aggregate, and divergence is the default state (Ecology)

Detailed experimental data is in the phase-specific reports: **ESDE_Genesis_Report.md** and **ESDE_Ecology_Report.md**.

---

## Governance

- Explainability over complexity: ontological additions reduce, not increase, explanatory power
- Minimum viable change: observe → diagnose → minimal change → re-verify
- No research jumps: Genesis → Ecology → Concept → Language, in order
- Null results are valid scientific findings
- AI agents do not defer to each other; facts and observations take precedence
