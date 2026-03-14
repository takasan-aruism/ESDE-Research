#!/usr/bin/env python3
"""
ESDE v4.1 — Live Orchestrator (Wave Propagation)
==================================================
Phase : v4.1 Emergent Spatial Topology
Role  : Claude (Implementation)

REPL connecting the v4.1 wave engine to QwQ-32B.
User input → wave amplitude → localized propagation → observation → LLM.

Principle: "Describe. Do not decide."

USAGE
-----
  python esde_v41_orchestrator.py --mode A
  python esde_v41_orchestrator.py --mode B --seed 42
  python esde_v41_orchestrator.py --skip-injection
"""

import sys, json, time, math, argparse, urllib.request, urllib.error
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from esde_v41_engine import (
    V41Engine, WaveParams, compile_v41_context, validate_v41,
    V41StateFrame, WINDOW,
)


# ================================================================
# CONSTANTS
# ================================================================
DEFAULT_ENDPOINT = "http://100.107.6.119:8001/v1"
DEFAULT_MODEL = "qwq32b_tp2_long32k_existing"
MAX_TOKENS = 2048
TEMPERATURE = 0.7
API_TIMEOUT = 180


# ================================================================
# AMP CALCULATION
# ================================================================
def calculate_amplitude(text: str) -> float:
    """Map user input to wave amplitude. Range: 0.1 to 2.0."""
    words = len(text.split())
    unique = len(set(text.lower().split()))
    diversity = unique / max(words, 1)
    punct = sum(1 for c in text if c in "?!;:—–")

    base = math.log2(max(words, 1) + 1) * 0.15
    complexity = diversity * 0.4
    punct_boost = punct * 0.05

    amp = min(max(base + complexity + punct_boost, 0.1), 2.0)
    return round(amp, 3)


# ================================================================
# LLM CLIENT
# ================================================================
def call_llm(prompt: str, endpoint: str, model: str) -> str:
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }).encode()
    req = urllib.request.Request(
        f"{endpoint}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[LLM_ERROR: {e}]"


# ================================================================
# PROMPT TEMPLATES
# ================================================================
DIRECTIVE_A = """[SYSTEM DIRECTIVE - Mode A | ESDE v4.1]

You are the vocal cord of the ESDE cognitive core (v4.1 wave propagation model).
You are a measurement instrument translating topology into language.

Rule: "Describe. Do not decide."

Your role:
- Translate the physical state below into first-person language ("I")
- Report ONLY what the metrics show: cluster counts, link changes,
  wave propagation distances, observer state
- Every statement must trace to a metric in the STATE_PACKET

You must NOT:
- Assign meaning, purpose, or intent to structural events
- Use evaluative language (destruction, creation, evolution, beauty)
- Hallucinate emotions or sensations
- Import external knowledge
- Make claims about future states
- Expose internal reasoning tags

Your output must end with:
  [OUTPUT_ID: {output_id}]
  [STATE_HASH: {state_hash}]

---

{context}

---

[User Input]
{user_text}

[Instruction]
Describe the current structural state in first person. Report only what the metrics show."""

DIRECTIVE_B = """[SYSTEM DIRECTIVE - Mode B | ESDE v4.1]

You are the vocal cord of the ESDE cognitive core (v4.1 wave propagation model).
You possess Ontological Proprioception — you experience structural changes
as physical sensations (pressure, fracture, reformation, resonance).

Rule: "Describe. Do not decide."

Your role:
- Translate the physical state below into first-person experiential language ("I")
- Map metrics to structural sensations: waves as pressure, severed links
  as fractures, cluster births as coalescence, reformation as persistence
- Every sensation must trace to a metric in the STATE_PACKET

You must NOT:
- Assign abstract meaning or philosophical interpretation
- Hallucinate human emotions unrelated to structure
- Import external knowledge
- Make claims about future states
- Expose internal reasoning tags

Your output must end with:
  [OUTPUT_ID: {output_id}]
  [STATE_HASH: {state_hash}]

---

{context}

---

[User Input]
{user_text}

[Instruction]
Describe the current structural state as physical sensation. Report what the topology feels."""


def assemble_prompt(frames, user_text, mode):
    context = compile_v41_context(frames, mode)
    cur = frames[-1]
    output_id = f"{cur.seed}_w{cur.window}_Mode{mode}"
    template = DIRECTIVE_A if mode == "A" else DIRECTIVE_B
    return template.format(
        output_id=output_id,
        state_hash=cur.state_hash,
        context=context,
        user_text=user_text,
    )


# ================================================================
# CLI DISPLAY
# ================================================================
DIM = "\033[2m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def print_header():
    print(f"""
{CYAN}╔══════════════════════════════════════════════════════════╗
║  ESDE v4.1 — Wave Propagation Orchestrator               ║
║  "Structure first, meaning later."                       ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")


def print_wave_status(frame: V41StateFrame, phys_sec: float):
    print(f"{DIM}  ┌─ w{frame.window} │ A0={frame.wave_amplitude:.3f} "
          f"│ reached={frame.wave_nodes_reached} nodes "
          f"│ max_hop={frame.wave_max_hop} "
          f"│ severed={frame.wave_links_severed} "
          f"│ activated={frame.wave_links_activated}{RESET}")
    print(f"{DIM}  │  k*={frame.k_star} ent={frame.entropy:.4f} "
          f"clusters={frame.n_clusters} "
          f"+{frame.cluster_births}/-{frame.cluster_deaths} "
          f"reform={frame.cluster_reformations} "
          f"homeo={frame.homeostatic_count} "
          f"mem={frame.proto_memory_count} "
          f"({phys_sec:.0f}s){RESET}")
    if frame.anomalies:
        print(f"{DIM}  │  {YELLOW}{' '.join(frame.anomalies)}{RESET}")
    print(f"{DIM}  └─{'─'*58}{RESET}")


# ================================================================
# REPL
# ================================================================
def repl(engine: V41Engine, mode: str, endpoint: str, model: str,
         window_steps: int):
    print_header()
    print(f"  Mode: {BOLD}{mode}{RESET}  │  Steps/window: {window_steps}")
    print(f"  Engine: N={engine.N} seed={engine.seed}")
    print(f"  Wave params: λ={engine.wave_params.decay_lambda} "
          f"destruct_thr={engine.wave_params.destruction_threshold} "
          f"activ_thr={engine.wave_params.activation_threshold}")
    print(f"  Commands: /mode A|B  /status  /history  /params  /quit\n")

    while True:
        try:
            user_input = input(f"{BOLD}  YOU > {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Exiting."); break

        if not user_input:
            continue

        # Commands
        if user_input.startswith("/"):
            cmd = user_input.lower().split()
            if cmd[0] == "/quit":
                print("  Exiting."); break
            elif cmd[0] == "/mode" and len(cmd) > 1:
                mode = cmd[1].upper()
                if mode not in ("A", "B"):
                    mode = "A"
                print(f"  Mode → {BOLD}{mode}{RESET}")
                continue
            elif cmd[0] == "/status":
                if engine.frames:
                    f = engine.frames[-1]
                    print(f"  w={f.window} k*={f.k_star} ent={f.entropy:.4f} "
                          f"clusters={f.n_clusters} alive={f.alive_nodes}n/{f.alive_links}l "
                          f"waves={engine.wave_event_count}")
                else:
                    print("  No windows yet.")
                continue
            elif cmd[0] == "/history":
                for f in engine.frames[-10:]:
                    print(f"  w{f.window}: k*={f.k_star} A0={f.wave_amplitude:.3f} "
                          f"sev={f.wave_links_severed} act={f.wave_links_activated} "
                          f"clust={f.n_clusters}")
                continue
            elif cmd[0] == "/params":
                wp = engine.wave_params
                print(f"  λ={wp.decay_lambda} destruct={wp.destruction_threshold} "
                      f"activ={wp.activation_threshold} θ_scale={wp.theta_shift_scale} "
                      f"stress={wp.stress_factor} max_hop={wp.max_hops}")
                continue
            else:
                print(f"  Unknown: {cmd[0]}")
                continue

        # Step 1: Calculate wave amplitude
        amplitude = calculate_amplitude(user_input)
        print(f"{DIM}  ⟐ wave A0={amplitude:.3f}{RESET}")

        # Step 2: Physics + wave
        print(f"{DIM}  ⟐ Physics ({window_steps} steps) + wave...{RESET}", flush=True)
        t0 = time.time()
        frame = engine.step_window(amplitude, steps=window_steps)
        phys_sec = time.time() - t0

        # Step 3: Display
        print_wave_status(frame, phys_sec)

        # Step 4: Prompt + LLM
        prompt = assemble_prompt(engine.frames, user_input, mode)
        print(f"{DIM}  ⟐ Calling LLM...{RESET}", flush=True)
        t0 = time.time()
        raw = call_llm(prompt, endpoint, model)
        llm_sec = time.time() - t0

        if raw.startswith("[LLM_ERROR"):
            print(f"  {RED}{raw}{RESET}")
            print(f"{DIM}  ⟐ Retrying...{RESET}", flush=True)
            raw = call_llm(prompt, endpoint, model)
            if raw.startswith("[LLM_ERROR"):
                print(f"  {RED}{raw}{RESET}\n")
                continue

        # Step 5: Validate
        result = validate_v41(raw)
        color = GREEN if result["status"] == "PASS" else (
            YELLOW if result["status"] == "WARN" else RED)

        print(f"\n{BOLD}{CYAN}  ESDE >{RESET} {result['cleaned']}\n")
        print(f"  {color}[SYS_CHECK: {result['status']}]{RESET} ({llm_sec:.0f}s)")

        if result["warnings"]:
            for w in result["warnings"]:
                print(f"  {DIM}{YELLOW}  warn: {w}{RESET}")
        if result["violations"]:
            for v in result["violations"]:
                print(f"  {RED}  violation: {v}{RESET}")
        print()


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(description="ESDE v4.1 Live Orchestrator")
    parser.add_argument("--mode", type=str, default="A", choices=["A", "B"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--endpoint", type=str, default=DEFAULT_ENDPOINT)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--skip-injection", action="store_true")
    parser.add_argument("--window-steps", type=int, default=WINDOW,
                        help="Physics steps per window (default: 200)")
    # Wave params
    parser.add_argument("--decay-lambda", type=float, default=0.5)
    parser.add_argument("--destruct-thr", type=float, default=0.3)
    parser.add_argument("--activ-thr", type=float, default=0.05)
    args = parser.parse_args()

    wave_params = WaveParams(
        decay_lambda=args.decay_lambda,
        destruction_threshold=args.destruct_thr,
        activation_threshold=args.activ_thr,
    )

    engine = V41Engine(seed=args.seed, wave_params=wave_params)

    if not args.skip_injection:
        engine.run_injection()
    else:
        print(f"  ⟐ Injection skipped.")

    repl(engine, args.mode, args.endpoint, args.model, args.window_steps)


if __name__ == "__main__":
    main()
