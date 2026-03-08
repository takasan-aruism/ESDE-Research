"""
ESDE Genesis v0.9 — Auto-Growth & Latent Cost
================================================
Links in loops grow stronger by consuming latent potential.
Exclusion provides competition (cost). Controller self-tunes.

Execution order per step:
  1. Background injection + seeding
  2. Realization (latent→active)
  3. Phase + Flow
  4. Chemistry
  5. Resonance (R_ij computed)
  6. Auto-Growth (S_ij += rate*R_ij, L_ij -= same)  ← NEW
  7. Decay + Exclusion

Primary: median S crosses 0.3 in quiet. Secondary: cycles > 0.

Designed: Gemini | Audited: GPT | Built: Claude
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import time
from collections import Counter, defaultdict

from genesis_state import GenesisState
from genesis_physics import GenesisPhysics, PhysicsParams
from genesis_logger import GenesisLogger
from chemistry import ChemistryEngine, ChemistryParams
from realization import RealizationOperator, RealizationParams
from autogrowth import AutoGrowthEngine, AutoGrowthParams
from controller import AdaptiveController

N_NODES = 200; C_MAX = 1.0
INJECTION_STEPS = 300; QUIET_STEPS = 2000
INJECT_INTERVAL = 3; SEED = 42
BETA = 1.0; NODE_DECAY = 0.005

STATE_NAMES = {0: "Dust", 1: "A", 2: "B", 3: "C"}
STRENGTH_BINS = [(0, 0.05), (0.05, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 1.01)]
BIN_LABELS = ["0-0.05", "0.05-0.1", "0.1-0.2", "0.2-0.3", "0.3+"]


class CycleTracker:
    def __init__(self):
        self.history = defaultdict(list)
        self.completed = []
    def record(self, state, step):
        for i in state.alive_n:
            z = int(state.Z[i])
            h = self.history[i]
            if not h or h[-1][1] != z:
                h.append((step, z))
    def detect_cycles(self):
        self.completed = []
        for nid, h in self.history.items():
            states = [s for _, s in h]
            for i in range(len(states) - 3):
                if states[i] == 3 and states[i+1] == 0 and states[i+2] in (1, 2):
                    for j in range(i+3, len(states)):
                        if states[j] == 3:
                            self.completed.append({
                                "node": nid,
                                "cycle": [STATE_NAMES[s] for s in states[i:j+1]],
                                "start": h[i][0], "end": h[j][0],
                            })
                            break
        return self.completed


def strength_histogram(state):
    strengths = [state.S[k] for k in state.alive_l]
    hist = {}
    for lo, hi in STRENGTH_BINS:
        hist[f"{lo}-{hi}"] = sum(1 for s in strengths if lo <= s < hi)
    return hist


def main():
    print("=" * 70)
    print("  ESDE Genesis v0.9 — Auto-Growth & Latent Cost")
    print("  'Can loop-participating links grow into usable connectivity?'")
    print("=" * 70)
    print(f"  Auto-growth: rate*R_ij, paid from L_ij")
    print(f"  Controller: 8 params, V = 100*median_S + 50*SPR + 10*cycles")
    print()

    state = GenesisState(n_nodes=N_NODES, c_max=C_MAX, seed=SEED)
    physics = GenesisPhysics(PhysicsParams(
        exclusion_enabled=True, resonance_enabled=True,
        phase_enabled=True, beta=BETA,
        decay_rate_node=NODE_DECAY, K_sync=0.1, alpha=0.0, gamma=1.0))
    chem = ChemistryEngine(ChemistryParams(enabled=True))
    realizer = RealizationOperator(RealizationParams(enabled=True))
    grower = AutoGrowthEngine(AutoGrowthParams(enabled=True))
    controller = AdaptiveController(window_size=200)
    logger = GenesisLogger()
    tracker = CycleTracker()

    t0 = time.time()
    o9_log = []
    prev_cycles = 0

    # ---- INJECTION ----
    print("  Injection Phase...")
    for step in range(INJECTION_STEPS):
        if step % INJECT_INTERVAL == 0:
            tgts = physics.inject(state)
            chem.seed_on_injection(state, tgts or [])
        physics.step_pre_chemistry(state)
        rxns = chem.step(state)
        cd = physics.step_resonance(state)
        if cd: logger.observe_loops(cd)
        grower.step(state)  # auto-growth during injection too
        physics.step_decay_exclusion(state)
        logger.observe(state, reactions=rxns)
        tracker.record(state, state.step - 1)

    print(f"    Done. C={sum(1 for i in state.alive_n if state.Z[i]==3)} L={len(state.alive_l)}")

    # ---- QUIET ----
    print(f"\n  Quiet Phase ({QUIET_STEPS} steps)...")
    w_realized = 0; w_growth_events = 0; w_latent_consumed = 0; w_prune = 0

    for step in range(QUIET_STEPS):
        # 1. Background injection
        bg_prob = controller.get_param("background_injection_prob")
        mask = state.rng.random(N_NODES) < bg_prob
        for i in range(N_NODES):
            if mask[i] and i in state.alive_n:
                state.E[i] = min(1.0, state.E[i] + 0.3)
                if state.Z[i] == 0 and state.rng.random() < 0.5:
                    state.Z[i] = 1 if state.rng.random() < 0.5 else 2

        # Sync params
        rp = realizer.params
        rp.p_link_birth = controller.get_param("p_link_birth")
        rp.latent_to_active_threshold = controller.get_param("latent_to_active_threshold")
        rp.latent_refresh_rate = controller.get_param("latent_refresh_rate")
        chem.params.E_thr = controller.get_param("reaction_energy_threshold")
        chem.params.exothermic_release = controller.get_param("exothermic_release_amount")
        state.EXTINCTION = controller.get_param("link_death_threshold")
        grower.params.auto_growth_rate = controller.get_param("auto_growth_rate")

        # 2. Realization
        pre_links = len(state.alive_l)
        n_real = realizer.step(state)
        w_realized += n_real

        # 3. Phase + Flow
        physics.step_pre_chemistry(state)

        # 4. Chemistry
        rxns = chem.step(state)

        # 5. Resonance
        cd = physics.step_resonance(state)
        if cd: logger.observe_loops(cd)

        # 6. Auto-Growth (AFTER resonance, BEFORE decay+exclusion)
        grower.step(state)
        w_growth_events += grower.growth_events
        w_latent_consumed += grower.latent_consumed

        # 7. Decay + Exclusion
        pre_exc = len(state.alive_l)
        physics.step_decay_exclusion(state)
        post_exc = len(state.alive_l)
        w_prune += max(0, pre_exc - post_exc)

        logger.observe(state, event="quiet", reactions=rxns)
        tracker.record(state, state.step - 1)

        # Window boundary
        if (step + 1) % controller.window_size == 0:
            # Metrics
            strengths = [state.S[k] for k in state.alive_l]
            med_s = float(np.median(strengths)) if strengths else 0.0
            loop_links = sum(1 for k in state.alive_l if state.R.get(k, 0) > 0)
            spr = loop_links / max(len(state.alive_l), 1)
            all_cyc = tracker.detect_cycles()
            new_cyc = len(all_cyc) - prev_cycles
            prev_cycles = len(all_cyc)

            hist = strength_histogram(state)
            sc = Counter(int(state.Z[i]) for i in state.alive_n)

            # Controller
            entry = controller.evaluate_and_adapt({
                "median_strength": med_s,
                "spr": spr,
                "cycles_window": new_cyc,
            })

            o9_entry = {
                "window": entry["window"],
                "V": entry["V"],
                "links": len(state.alive_l),
                "med_s": round(med_s, 5),
                "spr": round(spr, 4),
                "realized": w_realized,
                "growth_events": w_growth_events,
                "latent_consumed": round(w_latent_consumed, 3),
                "prune": w_prune,
                "loop_edges": loop_links,
                "cycles_new": new_cyc,
                "cycles_total": len(all_cyc),
                "n_C": sc.get(3, 0),
                "hist": hist,
                "latent_mass": round(state.latent_mass(), 1),
            }
            o9_log.append(o9_entry)

            w = entry["window"]
            s03 = hist.get("0.3-1.01", 0)
            print(f"    W{w:>2}: V={entry['V']:>7.1f} "
                  f"L={len(state.alive_l):>4} med={med_s:.4f} "
                  f"S>0.3={s03:>3} "
                  f"grow={w_growth_events:>4} "
                  f"loop={loop_links:>3} "
                  f"cyc={new_cyc} "
                  f"→{entry['param'][:12]}={entry['new']:.4f}"
                  f"{'(r)' if entry['rev'] else ''} "
                  f"({time.time()-t0:.0f}s)")

            w_realized = 0; w_growth_events = 0
            w_latent_consumed = 0; w_prune = 0

    all_cycles = tracker.detect_cycles()
    elapsed = time.time() - t0

    # ============================================================
    # RESULTS
    # ============================================================
    print(f"\n{'='*70}")
    print(f"  RESULTS — Auto-Growth & Latent Cost")
    print(f"{'='*70}")

    min_links = min(e["links"] for e in o9_log) if o9_log else 0
    max_med = max(e["med_s"] for e in o9_log) if o9_log else 0
    max_s03 = max(e["hist"].get("0.3-1.01", 0) for e in o9_log) if o9_log else 0

    print(f"\n  Cycles completed: {len(all_cycles)}")
    print(f"  Min active links: {min_links}")
    print(f"  Max median strength: {max_med:.5f}")
    print(f"  Max links S>0.3: {max_s03}")

    if min_links > 0:
        print(f"  ✓ Inert collapse prevented")
    if max_s03 > 0:
        print(f"  ✓ Usable connectivity achieved (S>0.3)")
    if len(all_cycles) > 0:
        print(f"  ✓ NODE-LEVEL CYCLES DETECTED")
        patterns = Counter(tuple(c["cycle"]) for c in all_cycles)
        for pat, count in patterns.most_common(10):
            print(f"    {' → '.join(pat)} : {count}")

    print(f"\n  Final Parameters:")
    for p in controller.params:
        print(f"    {p.name:<35} {p.value:.5f}")

    # ============================================================
    # PLOT
    # ============================================================
    fig, axes = plt.subplots(4, 2, figsize=(20, 22))
    fig.suptitle("ESDE Genesis v0.9 — Auto-Growth & Latent Cost\n"
                 "Can loop links grow into usable connectivity?",
                 fontsize=14, fontweight="bold", y=0.99)

    ws = [e["window"] for e in o9_log]

    ax = axes[0][0]
    ax.plot(ws, [e["links"] for e in o9_log], "o-", color="#2ecc71", ms=4)
    ax.axhline(y=0, color="red", linestyle=":", alpha=0.5)
    ax.set_title("Active Links"); ax.grid(True, alpha=0.2)

    ax = axes[0][1]
    ax.plot(ws, [e["med_s"] for e in o9_log], "o-", color="#3498db", ms=4, label="median S")
    ax.axhline(y=0.3, color="red", linestyle=":", alpha=0.5, label="reaction threshold")
    ax.set_title("Median Active Link Strength"); ax.legend(fontsize=8); ax.grid(True, alpha=0.2)

    ax = axes[1][0]
    # Strength histogram stacked
    for bi, bl in enumerate(BIN_LABELS):
        key = f"{STRENGTH_BINS[bi][0]}-{STRENGTH_BINS[bi][1]}"
        vals = [e["hist"].get(key, 0) for e in o9_log]
        ax.plot(ws, vals, ".-", label=bl, ms=3)
    ax.set_title("Strength Distribution"); ax.legend(fontsize=7); ax.grid(True, alpha=0.2)

    ax = axes[1][1]
    ax.plot(ws, [e["spr"] for e in o9_log], "o-", color="#1abc9c", ms=4)
    ax.set_title("Structural Persistence Ratio"); ax.grid(True, alpha=0.2)

    ax = axes[2][0]
    ax.plot(ws, [e["growth_events"] for e in o9_log], "o-", color="#f39c12", ms=4, label="growth")
    ax.plot(ws, [e["loop_edges"] for e in o9_log], "s-", color="#9b59b6", ms=4, label="loop edges")
    ax.set_title("Growth Events & Loop Edges"); ax.legend(fontsize=8); ax.grid(True, alpha=0.2)

    ax = axes[2][1]
    ax.plot(ws, [e["V"] for e in o9_log], "o-", color="#2ecc71", ms=4)
    ax.set_title("Vitality Score"); ax.grid(True, alpha=0.2)

    ax = axes[3][0]
    ax.plot(ws, [e["cycles_total"] for e in o9_log], "o-", color="#e67e22", ms=5)
    ax.set_title("Cumulative Cycles"); ax.grid(True, alpha=0.2)

    ax = axes[3][1]; ax.axis("off")
    txt = [f"Cycles: {len(all_cycles)}", f"Min Links: {min_links}",
           f"Max Median S: {max_med:.5f}", f"Max S>0.3: {max_s03}", "",
           "Final Params:"]
    for p in controller.params:
        txt.append(f"  {p.name[:28]}: {p.value:.4f}")
    ax.text(0.05, 0.95, "\n".join(txt), transform=ax.transAxes, fontsize=10,
            va="top", fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="lightyellow", edgecolor="gray", alpha=0.8))

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig("genesis_v09_autogrowth.png", dpi=150, bbox_inches="tight")
    print(f"\n  Plot: genesis_v09_autogrowth.png")

    controller.export_log("controller_v09_log.csv")
    with open("genesis_v09_o9_log.json", "w") as f:
        json.dump(o9_log, f, indent=2)
    with open("genesis_v09_cycles.json", "w") as f:
        json.dump(all_cycles, f, indent=2)

    print(f"  Elapsed: {elapsed:.0f}s | Seed: {SEED}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
