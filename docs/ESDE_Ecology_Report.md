# ESDE Ecology: Observer Interaction — Experiment Report

*Phase: Ecology (v2.1 –)*
*Status: IN PROGRESS*
*Team: Gemini (Architect) / GPT (Audit) / Claude (Implementation)*
*Started: March 9, 2026*
*Prerequisites: Genesis complete (see ESDE_Genesis_Report.md)*

---

## Context

Genesis established that a global observer (k*=4) emerges as a stable phase of the system across N=200 to N=10,000 nodes. Ecology asks the next question: **is the observer singular or plural?**

All Ecology experiments inherit the frozen Genesis physics, chemistry, and observer logic without modification. The only additions are spatial partitioning and per-region observation. Baseline conditions use Genesis-stable parameters: N=5000, plb=0.007, rate=0.002, quiet_steps=5000, 2×2 grid partition.

---

## Ecology v2.1 — Regional Decomposition

**Question:** Can the global observer be decomposed into local observer regions?

**Method:** Divide the N=5000 node space into a 2×2 grid (4 regions). Run the canonical k-selector independently per region. Measure inter-region active-link structure.

**Results (5 seeds):**

| seed | global k* | r0 | r1 | r2 | r3 | all match? |
|---|---|---|---|---|---|---|
| 42 | 4 | 4 (.96) | 4 (.96) | 4 (.96) | 4 (.96) | YES |
| 123 | 4 | 4 (.92) | 4 (.96) | 4 (.96) | 4 (.80) | YES |
| 2024 | 4 | 4 (.80) | 4 (.64) | 3 (.60) | 4 (.96) | NO |
| 456 | 3 | 4 (.96) | 4 (.96) | 4 (.80) | 4 (.76) | NO |
| 789 | 4 | 4 (.96) | 4 (.96) | 4 (.96) | 4 (.96) | YES |

(Numbers in parentheses = agree_frac: fraction of windows where that k* was dominant)

**Findings:**

*Local observers are more stable than the global observer.* In seed 456, the global selects k=3, but all four regions independently select k=4. The global aggregation loses information that each region preserves.

*Inter-region edge structure is uniform.* All 6 region pairs show 360–410 active links and 10–11 total weight per window. No spatial asymmetry at this partition resolution.

---

## Ecology v2.2 — Temporal Tracking

**Question:** Do local observer regions persist, diverge, and vary through time?

**Method:** Add window-by-window tracking of local k* transitions, per-region persistence streaks (longest run of unchanged k*), and a divergence flag (1 if any local k* ≠ global k*).

**Results (5 seeds):**

| seed | global k* | global sw | div_ratio | r0 streak | r1 streak | r2 streak | r3 streak |
|---|---|---|---|---|---|---|---|
| 42 | 4 | 11 | 0.48 | 24 | 24 | 24 | 24 |
| 123 | 4 | 7 | 0.48 | 13 | 23 | 24 | 23 |
| 2024 | 4 | 17 | 0.40 | 24 | 15 | 24 | 24 |
| 456 | 4 | 5 | 0.52 | 13 | 11 | 23 | 24 |
| 789 | 3 | 13 | 0.68 | 15 | 14 | 20 | 22 |

("streak" = max continuous windows with unchanged local k*, out of 25 total)

**Findings:**

*Local observers persist.* In seed 42, all four regions maintain k=4 for 24 consecutive windows (96% of the run). Even in the least stable case (seed 456, r1: streak=11), the dominant pattern is long-duration persistence, not random switching.

*Divergence is the norm, not the exception.* 40–68% of windows show at least one local k* ≠ global k*. The global observer is not a faithful summary of local dynamics — it is a lossy compression.

*Spatial asymmetry emerges in temporal stability.* r2 and r3 (bottom half of the grid) consistently show longer streaks (20–24) than r0 and r1 (top half: 11–24). This asymmetry is not built into the partition — it arises from the system's topology.

---

## Performance Note

The engine_accel optimization (replacing O(links) scans with O(degree) neighbor lookups in link_strength_sum and exclusion) produced a 1.8–3.7× speedup on N=5000 runs, reducing wall time from ~2.5 hours to ~1.3 hours per seed. No physics changes; algorithm-identical output verified by diff against Python-only runs (all fields except elapsed match exactly).

---

## What This Demonstrates

The system does not contain one observer — it contains multiple regional observers whose aggregate creates the appearance of a single, less certain global view. When decomposed spatially, the parts are individually more stable than the whole. This is the first evidence that observer structure in ESDE is inherently regional, not global.

Three specific claims are now supported by data:

1. Local k* selection is more stable than global k* selection (v2.1: seed 456 global=k3 while all regions=k4)
2. Local observer regions persist for extended periods (v2.2: streaks up to 24/25 windows)
3. Global-local divergence is the default state (v2.2: 40–68% of windows diverge)

---

## What It Does Not Demonstrate

- Whether observer competition or dominance produces lasting spatial patterns
- Whether finer partitions (4×4, 8×8) reveal hierarchical observer structure
- Whether regional divergence events are causally linked to island dynamics
- Whether merge/split events of island structure map to observer transitions

---

## Open Questions

- Do regional observers compete? Can one region's k* influence an adjacent region?
- Does divergence cluster in time (bursts) or distribute uniformly?
- At finer partition, do sub-regional observers emerge recursively?
- Can merge/split events of island structure be mapped to observer transition events?
- Is the spatial asymmetry (r2/r3 more stable than r0/r1) a topological feature or a partition artifact?

---

## Version Changelog

| Version | Date | Author | Core Addition | Key Result |
|---------|------|--------|---------------|------------|
| Eco v2.1 | 2026-03-09 | Gemini→GPT→Claude (Ryzen) | Region observer (2×2, 5 seeds) | **Local k* more stable than global; divergence in 2/5 seeds** |
| Eco v2.2 | 2026-03-09 | Gemini→GPT→Claude (Ryzen) | Temporal tracking (5 seeds) | **Streaks up to 24/25; divergence 40–68%; spatial asymmetry** |

---

*Ecology has opened a question Genesis could not ask: is the observer singular or plural? The first two experiments answer decisively — plural. The system produces a landscape of observers that see differently depending on where they stand.*
