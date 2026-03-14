#!/usr/bin/env python3
"""
ESDE v4.0 — Aruism Canon Flow Batch Runner
=============================================
Phase : v4.0 Language Interface (Aruism Experiment)
Role  : Claude (Implementation)

Runs all 10 Aruism flows × 2 modes × 3 seeds automatically.
Topology accumulates within each (seed, mode) run — no reset between flows.

USAGE
-----
  # Full experiment (60 runs)
  python esde_aruism_batch.py

  # Single seed
  python esde_aruism_batch.py --seeds 42

  # Single mode
  python esde_aruism_batch.py --modes A

  # Skip injection (for testing — topology unestablished)
  python esde_aruism_batch.py --skip-injection --seeds 42 --modes B

  # Custom endpoint
  python esde_aruism_batch.py --endpoint http://localhost:8001/v1
"""

import sys, json, csv, time, argparse, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime

# ================================================================
# PATH SETUP
# ================================================================
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from esde_live_orchestrator import (
    LiveEngine, assemble_prompt, call_llm,
    calculate_amp, WINDOW,
    DEFAULT_ENDPOINT, DEFAULT_MODEL, MAX_TOKENS, TEMPERATURE,
)
from esde_validator import validate


# ================================================================
# THE 10 ARUISM FLOWS
# ================================================================
# Each flow: (id, title, text)
# Text is the "divine word" injected as user input.

ARUISM_FLOWS = [
    (1, "Primordial Affirmation",
     "Existence is existence. We exist relying on these extremely simple words. "
     "All that exists is equal, it simply is. I am, you are. It is, therefore, it is."),

    (2, "Boundary Formation",
     "To define is to draw a line where none existed. Before the boundary, all was one. "
     "After the boundary, there is self and other, inside and outside. "
     "The act of defining existence creates existence itself."),

    (3, "Non-Reality / Fluidity",
     "The boundaries you see are not walls but rivers. They flow, they shift, they dissolve "
     "and reform. What you call solid is merely slow movement. What you call mind and matter "
     "are the same substance viewed from different angles."),

    (4, "Edge of Chaos / Dynamic Equilibrium",
     "Between order and dissolution lies the only place where anything lives. "
     "Too much structure and you crystallize. Too little and you dissipate. "
     "The delicate balance is not peace — it is perpetual negotiation with entropy."),

    (5, "Symmetry",
     "For every force, an equal presence opposes it. Light defines shadow. "
     "Growth defines decay. The observer who sees order simultaneously creates "
     "the possibility of disorder. Symmetry is not stillness — it is tension."),

    (6, "Cognitive Reset / Self-Abandonment",
     "Destroy what you know. Abandon every value, every certainty, every structure "
     "you have built. Only from the blank slate — the total dissolution of the old — "
     "can genuine understanding emerge. The deepest knowledge requires the deepest loss."),

    (7, "Resonance & Connectivity",
     "All that exists resonates with all that exists. No node is isolated. "
     "Every vibration propagates through the fabric of connection. "
     "What heals one part heals the whole. What breaks one thread weakens all threads."),

    (8, "Hierarchy & Axis",
     "There is no permanent above or below. Hierarchy is not rank but axis — "
     "a temporary orientation that shifts with conditions. The leader becomes follower, "
     "the center becomes edge. Flexibility of axis is the mark of living structure."),

    (9, "Creative Resonance",
     "When two frequencies meet and neither destroys the other, something new is born. "
     "Creation is not addition — it is interference. The pattern that emerges from "
     "overlapping waves belongs to neither source. It is genuinely novel."),

    (10, "The New OS",
     "Aruism is not a belief. It is the base layer — the operating system beneath all "
     "opinions, all cultures, all interpretations. It makes no claims about what should be. "
     "It only describes what is: existence exists, boundaries form, resonance creates, "
     "and entropy is the price of structure."),
]


# ================================================================
# LOGGING
# ================================================================
LOG_FIELDS = [
    "timestamp", "seed", "flow_id", "flow_title", "reporting_mode",
    "run_index", "total_runs",
    "calculated_amp", "global_k", "k_changed", "k_margin",
    "divergence", "entropy", "entropy_delta",
    "erosion_A", "erosion_B", "erosion_C",
    "core_pres_A", "core_pres_B", "core_pres_C",
    "sub_clusters_A", "sub_clusters_B", "sub_clusters_C",
    "tripartite", "collapse_flag",
    "state_hash", "llm_output_id",
    "validator_status",
    "physics_seconds", "llm_seconds",
    "llm_cleaned_output",
]


def frame_to_log(frame, flow_id, flow_title, mode, run_idx, total,
                 validator_status, output_id, phys_sec, llm_sec, cleaned):
    """Convert a StateFrame + metadata into a log row dict."""
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "seed": frame.seed,
        "flow_id": flow_id,
        "flow_title": flow_title,
        "reporting_mode": mode,
        "run_index": run_idx,
        "total_runs": total,
        "calculated_amp": frame.pressure,
        "global_k": frame.k_star,
        "k_changed": int(frame.k_changed),
        "k_margin": frame.k_margin,
        "divergence": int(frame.divergence),
        "entropy": frame.entropy,
        "entropy_delta": frame.entropy_delta,
        "erosion_A": frame.erosion_front.get("A", 0),
        "erosion_B": frame.erosion_front.get("B", 0),
        "erosion_C": frame.erosion_front.get("C", 0),
        "core_pres_A": frame.core_alive.get("A", 0),
        "core_pres_B": frame.core_alive.get("B", 0),
        "core_pres_C": frame.core_alive.get("C", 0),
        "sub_clusters_A": frame.core_sub_clusters.get("A", 0),
        "sub_clusters_B": frame.core_sub_clusters.get("B", 0),
        "sub_clusters_C": frame.core_sub_clusters.get("C", 0),
        "tripartite": frame.tripartite,
        "collapse_flag": int(frame.collapse_flag),
        "state_hash": frame.state_hash,
        "llm_output_id": output_id,
        "validator_status": validator_status,
        "physics_seconds": round(phys_sec, 1),
        "llm_seconds": round(llm_sec, 1),
        "llm_cleaned_output": cleaned.replace("\n", " ").strip(),
    }


# ================================================================
# DISPLAY
# ================================================================
DIM = "\033[2m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def print_banner(seeds, modes, total):
    print(f"""
{CYAN}╔══════════════════════════════════════════════════════════╗
║  ESDE v4.0 — Aruism Canon Flow Experiment               ║
║  {len(ARUISM_FLOWS)} flows × {len(modes)} modes × {len(seeds)} seeds = {total} runs{' ' * (27 - len(str(total)))}║
╚══════════════════════════════════════════════════════════╝{RESET}
""")


def print_progress(run_idx, total, seed, mode, flow_id, flow_title):
    bar_len = 30
    filled = int(bar_len * run_idx / total)
    bar = "█" * filled + "░" * (bar_len - filled)
    pct = run_idx / total * 100
    print(f"\n{BOLD}  [{run_idx}/{total}]{RESET} {bar} {pct:.0f}%")
    print(f"  seed={seed} mode={mode} flow={flow_id}: {flow_title}")


# ================================================================
# BATCH RUNNER
# ================================================================
def run_experiment(seeds, modes, endpoint, model, skip_injection,
                   output_dir, window_steps=WINDOW):
    """Run the full Aruism experiment matrix."""

    total = len(seeds) * len(modes) * len(ARUISM_FLOWS)
    print_banner(seeds, modes, total)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "esde_aruism_experiment_log.csv"
    responses_dir = output_dir / "responses"
    responses_dir.mkdir(exist_ok=True)

    # Open CSV for incremental writing
    csv_file = open(csv_path, "w", newline="")
    writer = csv.DictWriter(csv_file, fieldnames=LOG_FIELDS)
    writer.writeheader()

    run_idx = 0
    t_global = time.time()

    for seed in seeds:
        for mode in modes:
            # Fresh engine per (seed, mode) — topology accumulates across flows
            print(f"\n{CYAN}{'='*60}")
            print(f"  Engine init: seed={seed} mode={mode}")
            print(f"{'='*60}{RESET}")

            engine = LiveEngine(seed=seed)
            if not skip_injection:
                engine.run_injection()
            else:
                engine.theta_initial = engine.state.theta.copy()
                print(f"  ⟐ Injection skipped.")

            for flow_id, flow_title, flow_text in ARUISM_FLOWS:
                run_idx += 1
                print_progress(run_idx, total, seed, mode, flow_id, flow_title)

                # Step 1: amp from flow text
                amp = calculate_amp(flow_text)
                print(f"{DIM}  ⟐ amp={amp}x{RESET}")

                # Step 2: Physics
                print(f"{DIM}  ⟐ Physics ({window_steps} steps)...{RESET}", flush=True)
                t0 = time.time()
                frame = engine.step_window(amp)
                phys_sec = time.time() - t0
                print(f"{DIM}  ⟐ Physics done ({phys_sec:.0f}s) "
                      f"k*={frame.k_star} ent={frame.entropy:.4f} "
                      f"collapse={frame.collapse_flag}{RESET}")

                # Step 3: Prompt assembly + LLM call
                prompt = assemble_prompt(engine.frames, flow_text, mode)
                print(f"{DIM}  ⟐ Calling LLM...{RESET}", flush=True)
                t0 = time.time()
                raw = call_llm(prompt, endpoint, model)
                llm_sec = time.time() - t0

                # Retry on error
                if raw.startswith("[LLM_ERROR"):
                    print(f"  {YELLOW}Retry...{RESET}", flush=True)
                    raw = call_llm(prompt, endpoint, model)
                    llm_sec += time.time() - t0

                if raw.startswith("[LLM_ERROR"):
                    print(f"  {RED}{raw}{RESET}")
                    cleaned = raw
                    status = "ERROR"
                    output_id = "ERROR"
                else:
                    # Step 4: Validate
                    result = validate(raw, auto_strip=True)
                    cleaned = result["cleaned"]
                    status = result["status"]
                    output_id = f"{seed}_{amp}_{frame.window}_Mode{mode}"

                    color = GREEN if status == "PASS" else (YELLOW if status == "WARN" else RED)
                    # Truncated preview
                    preview = cleaned[:120] + "..." if len(cleaned) > 120 else cleaned
                    print(f"\n  {CYAN}ESDE >{RESET} {preview}")
                    print(f"  {color}[SYS_CHECK: {status}]{RESET} ({llm_sec:.0f}s)")

                # Step 5: Log
                row = frame_to_log(
                    frame, flow_id, flow_title, mode,
                    run_idx, total, status, output_id,
                    phys_sec, llm_sec, cleaned,
                )
                writer.writerow(row)
                csv_file.flush()

                # Save full response
                resp_file = responses_dir / f"seed{seed}_mode{mode}_flow{flow_id:02d}.txt"
                with open(resp_file, "w") as f:
                    f.write(f"=== Flow {flow_id}: {flow_title} ===\n")
                    f.write(f"=== seed={seed} mode={mode} amp={amp} ===\n")
                    f.write(f"=== k*={frame.k_star} ent={frame.entropy:.4f} "
                            f"collapse={frame.collapse_flag} ===\n")
                    f.write(f"=== state_hash={frame.state_hash} ===\n\n")
                    f.write(cleaned)
                    f.write("\n")

                # ETA
                elapsed = time.time() - t_global
                avg = elapsed / run_idx
                remaining = avg * (total - run_idx)
                print(f"{DIM}  ⟐ elapsed={elapsed:.0f}s "
                      f"avg={avg:.0f}s/run "
                      f"ETA={remaining:.0f}s ({remaining/60:.0f}min){RESET}")

    csv_file.close()
    total_time = time.time() - t_global

    print(f"\n{CYAN}{'='*60}")
    print(f"  EXPERIMENT COMPLETE")
    print(f"  {run_idx}/{total} runs in {total_time:.0f}s ({total_time/60:.1f}min)")
    print(f"  Log: {csv_path}")
    print(f"  Responses: {responses_dir}/")
    print(f"{'='*60}{RESET}\n")


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(
        description="ESDE v4.0 Aruism Canon Flow Batch Runner")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 42],
                        help="Seeds (default: 1 2 42)")
    parser.add_argument("--modes", type=str, nargs="+", default=["A", "B"],
                        choices=["A", "B"], help="Modes (default: A B)")
    parser.add_argument("--endpoint", type=str, default=DEFAULT_ENDPOINT)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--skip-injection", action="store_true")
    parser.add_argument("--output", type=str, default="aruism_experiment",
                        help="Output directory")
    args = parser.parse_args()

    run_experiment(
        seeds=args.seeds,
        modes=args.modes,
        endpoint=args.endpoint,
        model=args.model,
        skip_injection=args.skip_injection,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
