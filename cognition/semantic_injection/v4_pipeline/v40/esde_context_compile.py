#!/usr/bin/env python3
"""
ESDE v4.0 — Context Compiler
==============================
Phase : v4.0 Language Interface (Pipeline Stage 2)
Role  : Claude (Implementation)

Converts a list of ESDEStateFrame objects into the structured text format
required for the Transformer prompt:
  1. STATE_PACKET   — deterministic, hashable metric block
  2. CONTEXT BLOCK  — cumulative summary + recent history + anomaly flags

Input:  List[ESDEStateFrame] (from esde_state_extract.py)
Output: Structured text string per run (or per window for streaming mode)

USAGE
-----
  # Compile a single run (all windows -> one context block at final window)
  python esde_context_compile.py outputs_v39/seed_1_amp16p0.json

  # Compile all runs in directory
  python esde_context_compile.py --all outputs_v39/

  # Compile context at specific window (streaming simulation)
  python esde_context_compile.py outputs_v39/seed_2_amp128p0.json --at-window 20

  # Write compiled outputs to directory
  python esde_context_compile.py --all outputs_v39/ --out compiled_v39/
"""

import json, sys, argparse, hashlib
from pathlib import Path
from dataclasses import asdict

# Import State Extractor (same directory)
from esde_state_extract import (
    ESDEStateFrame, extract_run, extract_directory, CONCEPTS
)

# Import Proprioception Mapping (Gemini design, Claude-calibrated)
from esde_proprioception import map_frame, format_proprioception


# ================================================================
# CONSTANTS
# ================================================================
HISTORY_DEPTH = 5        # recent windows to include in detail
STABLE_COMPRESS_THR = 3  # compress after N identical consecutive windows
ENTROPY_BASELINE = 1.54  # from v3.0–v3.8 established baseline


# ================================================================
# STATE PACKET (deterministic, for GPT validation gate)
# ================================================================
def build_state_packet(frame: ESDEStateFrame) -> str:
    """
    Deterministic metric block. This is the sole semantic authority
    for the LLM's output (per GPT anti-contamination protocol).
    """
    lines = [
        f"STATE_PACKET {{",
        f"  window: {frame.window}/{frame.n_windows}",
        f"  seed: {frame.seed}",
        f"  amp: {frame.amp}",
        f"  entropy: {frame.entropy:.4f}",
        f"  entropy_delta: {frame.entropy_delta:+.4f}",
        f"  global_k: {frame.k_star}",
        f"  k_changed: {frame.k_changed}",
        f"  k_margin: {frame.k_margin:.4f}",
        f"  divergence: {int(frame.divergence)}",
        f"  tripartite: {frame.tripartite}",
        f"  n_C: {frame.n_C}",
    ]
    for cn in CONCEPTS:
        lines.append(f"  {cn}_erosion_depth: {frame.erosion_front.get(cn, 0)}")
        lines.append(f"  {cn}_core_pres: {frame.core_alive.get(cn, 0.0):.4f}")
        lines.append(f"  {cn}_k_var: {frame.core_k_var.get(cn, 0.0):.4f}")
        lines.append(f"  {cn}_sub_clusters: {frame.core_sub_clusters.get(cn, 0)}")
        lines.append(f"  {cn}_core_size: {frame.core_size.get(cn, 0)}")
        lines.append(f"  {cn}_core_mean_k: {frame.core_mean_k.get(cn, 0.0):.2f}")
    lines.append(f"  collapse_flag: {int(frame.collapse_flag)}")
    lines.append(f"  state_hash: {frame.state_hash}")
    lines.append(f"}}")
    return "\n".join(lines)


# ================================================================
# CUMULATIVE SUMMARY
# ================================================================
def build_cumulative(frames: list[ESDEStateFrame]) -> str:
    """Compress full history into a one-paragraph summary."""
    if not frames:
        return "CUMULATIVE: No data."

    cur = frames[-1]
    n = len(frames)

    # k* stability — filter out k*=0 (uninitialized windows)
    k_vals = [f.k_star for f in frames]
    switches = []
    for i in range(1, len(k_vals)):
        # Skip transitions involving k*=0 (initialization artifact)
        if k_vals[i] == 0 or k_vals[i-1] == 0:
            continue
        if k_vals[i] != k_vals[i-1]:
            switches.append((frames[i].window, k_vals[i-1], k_vals[i]))

    # Current k* = last established (non-zero) value
    established_k = [k for k in k_vals if k > 0]
    cur_k = established_k[-1] if established_k else 0
    n_established = len(established_k)

    if not switches:
        k_desc = f"k*={cur_k} stable for {n_established} established windows."
    else:
        k_desc = (f"k*={cur_k} now. {len(switches)} switch(es): "
                  + ", ".join(f"w{w}: {a}->{b}" for w, a, b in switches) + ".")

    # Entropy trend
    ents = [f.entropy for f in frames]
    ent_mean = sum(ents) / len(ents)
    ent_range = max(ents) - min(ents)
    ent_desc = f"Entropy: {ent_mean:.4f} mean, range {ent_range:.4f}."

    # Erosion
    erosion_vals = {cn: [f.erosion_front.get(cn, 0) for f in frames] for cn in CONCEPTS}
    erosion_maxes = {cn: max(vals) for cn, vals in erosion_vals.items()}
    erosion_desc = "Erosion max: " + ", ".join(
        f"{cn}={erosion_maxes[cn]}" for cn in CONCEPTS) + "."

    # Divergence
    div_count = sum(1 for f in frames if f.divergence)
    div_ratio = div_count / n
    div_desc = f"Divergence: {div_count}/{n} windows ({div_ratio:.0%})."

    # Core status
    all_dissolved = all(
        frames[-1].core_alive.get(cn, 0) < 0.01 for cn in CONCEPTS
    )
    if all_dissolved:
        core_desc = "All concept cores dissolved."
    else:
        surviving = [cn for cn in CONCEPTS
                     if frames[-1].core_alive.get(cn, 0) >= 0.01]
        core_desc = f"Surviving cores: {', '.join(surviving)}."

    # Collapse
    collapsed = any(f.collapse_flag for f in frames)
    collapse_desc = ""
    if collapsed:
        first_collapse = next(f.window for f in frames if f.collapse_flag)
        collapse_desc = f" COLLAPSE detected at window {first_collapse}."

    return (f"CUMULATIVE: {k_desc} {ent_desc} {erosion_desc} "
            f"{div_desc} {core_desc}{collapse_desc}")


# ================================================================
# RECENT HISTORY (last N windows)
# ================================================================
def _arrow(delta: float) -> str:
    if delta > 0.005:
        return " ^"
    elif delta < -0.005:
        return " v"
    return ""


def build_recent_history(frames: list[ESDEStateFrame],
                         depth: int = HISTORY_DEPTH) -> str:
    """Last N windows as compact one-liners."""
    recent = frames[-depth:] if len(frames) >= depth else frames
    if not recent:
        return "RECENT HISTORY: No data."

    lines = [f"RECENT HISTORY (last {len(recent)} windows):"]
    for f in recent:
        erosion_str = " ".join(
            f"{cn}={f.erosion_front.get(cn, 0)}" for cn in CONCEPTS)
        core_str = " ".join(
            f"{cn}={f.core_alive.get(cn, 0):.2f}" for cn in CONCEPTS)
        ent_arrow = _arrow(f.entropy_delta)

        parts = [
            f"  w{f.window:2d}:",
            f"k*={f.k_star}",
            f"| div={int(f.divergence)}",
            f"| ent={f.entropy:.4f}{ent_arrow}",
            f"| erosion {erosion_str}",
            f"| core_pres {core_str}",
            f"| tri={f.tripartite}",
        ]

        # Deep-core detail (only when sub_clusters data is nonzero)
        has_deep = any(f.core_sub_clusters.get(cn, 0) > 0 for cn in CONCEPTS)
        if has_deep:
            frag_str = " ".join(
                f"{cn}:{f.core_sub_clusters.get(cn,0)}" for cn in CONCEPTS)
            parts.append(f"| [DEEP_CORE] fragments {frag_str}")

        # Anomalies
        if f.anomalies:
            parts.append(f"| {' '.join(f.anomalies)}")

        lines.append(" ".join(parts))

    return "\n".join(lines)


# ================================================================
# CURRENT FRAME DETAIL
# ================================================================
def build_current_detail(frame: ESDEStateFrame) -> str:
    """Expanded prose description of the current window."""
    lines = ["CURRENT FRAME DETAIL:"]

    # Observer
    if frame.divergence:
        obs = (f"Observer: k*={frame.k_star}, DIVERGENT "
               f"(regional disagreement). Margin={frame.k_margin:+.4f}.")
    elif frame.k_changed:
        obs = (f"Observer: k* SWITCHED to {frame.k_star} "
               f"(from {frame.k_prev}). Margin={frame.k_margin:+.4f}.")
    else:
        obs = (f"Observer: unanimous k*={frame.k_star}, all regions agree. "
               f"Margin comfortable ({frame.k_margin:+.4f}).")
    lines.append(f"  {obs}")

    # Concepts / erosion
    dissolved = [cn for cn in CONCEPTS if frame.core_alive.get(cn, 0) < 0.01]
    surviving = [cn for cn in CONCEPTS if frame.core_alive.get(cn, 0) >= 0.01]
    if len(dissolved) == 3:
        concept_str = "Concepts: all cores dissolved (pres ~ 0)."
    elif dissolved:
        concept_str = (f"Concepts: {', '.join(dissolved)} dissolved; "
                       f"{', '.join(surviving)} surviving.")
    else:
        concept_str = "Concepts: all cores intact."

    erosion_vals = [frame.erosion_front.get(cn, 0) for cn in CONCEPTS]
    erosion_range = f"{min(erosion_vals)}-{max(erosion_vals)}"
    lines.append(f"  {concept_str} Erosion front at {erosion_range} hops.")

    # Pressure / diffusion
    lines.append(f"  Pressure: {frame.amp}x baseline.")

    # Deep core
    all_empty = all(frame.core_mean_k.get(cn, 0) < 0.01 for cn in CONCEPTS)
    if all_empty:
        lines.append("  Deep core: structurally empty. No internal connectivity.")
    else:
        active = {cn: frame.core_mean_k.get(cn, 0) for cn in CONCEPTS
                  if frame.core_mean_k.get(cn, 0) >= 0.01}
        lines.append(f"  Deep core: partial connectivity in {active}.")

    # Collapse
    if frame.collapse_flag:
        lines.append("  >>> COLLAPSE STATE: observer equilibrium broken. <<<")

    return "\n".join(lines)


# ================================================================
# TRANSITIONS & ANOMALIES
# ================================================================
def build_transitions(frame: ESDEStateFrame) -> str:
    """Summarize anomaly flags for current window."""
    if not frame.anomalies:
        return "TRANSITIONS THIS WINDOW: none.\nANOMALIES THIS WINDOW: none."

    transitions = [a for a in frame.anomalies
                   if a.startswith("[SWITCH") or a.startswith("[DIVERGENCE")]
    anomalies = [a for a in frame.anomalies if a not in transitions]

    t_str = ", ".join(transitions) if transitions else "none"
    a_str = ", ".join(anomalies) if anomalies else "none"
    return f"TRANSITIONS THIS WINDOW: {t_str}\nANOMALIES THIS WINDOW: {a_str}"


# ================================================================
# FULL CONTEXT BLOCK
# ================================================================
def compile_context(frames: list[ESDEStateFrame],
                    at_window: int = None,
                    mode: str = "A") -> str:
    """
    Compile the full context block for LLM injection.

    mode: "A" (structural, default) or "B" (proprioceptive, experimental)

    If at_window is specified, only frames up to that window are used
    (for streaming / real-time mode). Otherwise, final window is used.
    """
    if not frames:
        return "[ERROR: No frames to compile]"

    if at_window is not None:
        frames = [f for f in frames if f.window <= at_window]
        if not frames:
            return f"[ERROR: No frames at or before window {at_window}]"

    cur = frames[-1]

    header = (f"=== ESDE CORE STATE "
              f"(window {cur.window}/{cur.n_windows}, "
              f"amp={cur.amp}x, seed={cur.seed}) ===")

    # Proprioception mapping
    descriptors = map_frame(cur)
    proprio_block = format_proprioception(descriptors, mode)

    sections = [
        header,
        "",
        build_cumulative(frames),
        "",
        build_recent_history(frames),
        "",
        build_current_detail(cur),
        "",
        proprio_block,
        "",
        build_transitions(cur),
        "",
        build_state_packet(cur),
    ]

    return "\n".join(sections)


# ================================================================
# BATCH COMPILE
# ================================================================
def compile_run_file(summary_path: Path, at_window: int = None,
                     mode: str = "A") -> str:
    """Extract + compile a single run."""
    frames = extract_run(summary_path)
    if not frames:
        return f"[ERROR: No frames extracted from {summary_path}]"
    return compile_context(frames, at_window, mode)


def compile_directory(dirpath: Path, outdir: Path = None,
                      mode: str = "A") -> dict:
    """Extract + compile all runs. Optionally write to files."""
    all_runs = extract_directory(dirpath)
    results = {}

    for stem, frames in all_runs.items():
        ctx = compile_context(frames, mode=mode)
        results[stem] = ctx

        if outdir:
            outdir.mkdir(parents=True, exist_ok=True)
            out_path = outdir / f"{stem}_context.txt"
            with open(out_path, "w") as f:
                f.write(ctx)

    return results


# ================================================================
# CLI
# ================================================================
def main():
    parser = argparse.ArgumentParser(description="ESDE v4.0 Context Compiler")
    parser.add_argument("path", help="JSON summary file or directory")
    parser.add_argument("--all", action="store_true",
                        help="Process all runs in directory")
    parser.add_argument("--at-window", type=int, default=None,
                        help="Compile context at specific window")
    parser.add_argument("--out", type=str, default=None,
                        help="Output directory for compiled files")
    parser.add_argument("--mode", type=str, default="A", choices=["A", "B"],
                        help="Mode A (structural, default) or B (proprioceptive)")
    args = parser.parse_args()

    p = Path(args.path)

    if args.all or p.is_dir():
        outdir = Path(args.out) if args.out else None
        results = compile_directory(p, outdir, mode=args.mode)
        print(f"\n  Compiled {len(results)} runs")
        if outdir:
            print(f"  Written to {outdir}/")
        else:
            # Print first and last for review
            keys = sorted(results.keys())
            if keys:
                print(f"\n{'='*72}")
                print(f"  SAMPLE: {keys[0]}")
                print(f"{'='*72}")
                print(results[keys[0]])
                if len(keys) > 1:
                    print(f"\n{'='*72}")
                    print(f"  SAMPLE: {keys[-1]}")
                    print(f"{'='*72}")
                    print(results[keys[-1]])
    else:
        ctx = compile_run_file(p, args.at_window, mode=args.mode)
        print(ctx)


if __name__ == "__main__":
    main()
