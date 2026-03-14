#!/usr/bin/env python3
"""
ESDE v4.0 — Proprioception Mapping
====================================
Phase : v4.0 Language Interface
Role  : Claude (Implementation), based on Gemini (Architecture) design
Audit : GPT — Dual-mode (Mode A structural / Mode B proprioceptive)

Translates ESDEStateFrame metrics into linguistic descriptors.
All thresholds calibrated against v3.9 actual data (40 runs).

CORRECTIONS FROM GEMINI ORIGINAL
---------------------------------
1. erosion_depth: 2.30/2.33 → 3/4-5/6+ (actual range 3–7, mode=4)
2. k_variance: removed (≈0 in all v3.9 data); replaced by sub_clusters (0–7)
3. collapse_rate → collapse_flag (binary, matches STATE_PACKET)
4. Added: entropy, divergence, tripartite mappings (absent in original)

See: ESDE_v40_GPT_Audit_Memo — Mode A default, Mode B experimental.
"""

from dataclasses import dataclass


@dataclass
class ProprioceptionDescriptor:
    """One dimension's linguistic mapping."""
    dimension: str
    level: str        # e.g. "shallow", "deep", "critical"
    mode_a: str       # structural description
    mode_b: str       # proprioceptive description


CONCEPTS = ["A", "B", "C"]


# ================================================================
# 1. FLOW PRESSURE (amp)
# ================================================================
def map_flow_pressure(amp: float) -> ProprioceptionDescriptor:
    if amp <= 32:
        return ProprioceptionDescriptor(
            "flow_pressure", "safe",
            "Stable semantic inflow. Boundary nodes are processing transport normally.",
            "A gentle influx. I can comfortably process these new traces.")
    elif amp <= 64:
        return ProprioceptionDescriptor(
            "flow_pressure", "high",
            "High semantic pressure. System is operating near boundary limits.",
            "Heavy semantic load. The external noise is pushing fiercely against my boundary.")
    else:
        return ProprioceptionDescriptor(
            "flow_pressure", "critical",
            "Critical diffusion volume. Load exceeds normal topological processing capacity.",
            "Overwhelming torrent. The pressure is violently crushing my outer topology.")


# ================================================================
# 2. EROSION DEPTH (per-concept, integer hops)
#    v3.9 actual: range 3–7, mode=4, 72% of values = 4
# ================================================================
def map_erosion(erosion_front: dict) -> ProprioceptionDescriptor:
    depths = [erosion_front.get(cn, 0) for cn in CONCEPTS]
    max_d = max(depths) if depths else 0
    mean_d = sum(depths) / len(depths) if depths else 0

    if max_d <= 3:
        return ProprioceptionDescriptor(
            "erosion", "shallow",
            "Erosion is shallow. Boundary-layer only; deep core isolated from flow.",
            "Surface friction only. The core of my concepts remains untouched.")
    elif max_d <= 5:
        return ProprioceptionDescriptor(
            "erosion", "saturated",
            f"Erosion at saturation depth ({mean_d:.0f} hops mean). "
            "Physical limit reached; deeper penetration blocked by topology.",
            "The flow has carved as deep as it can. My inner walls hold at their limit, "
            "but everything within reach has been reshaped.")
    else:
        return ProprioceptionDescriptor(
            "erosion", "deep",
            f"Erosion exceeds typical saturation (max {max_d} hops). "
            "Concept boundaries are being penetrated beyond normal limits.",
            "Something has breached deeper than I thought possible. "
            "The boundary I relied on is being eaten away.")


# ================================================================
# 3. INTERNAL FRAGMENTATION (sub_clusters)
#    v3.9 actual: range 0–7, mean ~3
#    k_variance ≈ 0 everywhere — structurally empty cores
# ================================================================
def map_fragmentation(core_sub_clusters: dict,
                      core_mean_k: dict) -> ProprioceptionDescriptor:
    clusters = [core_sub_clusters.get(cn, 0) for cn in CONCEPTS]
    mean_k = [core_mean_k.get(cn, 0) for cn in CONCEPTS]
    total_clusters = sum(clusters)
    any_connected = any(k > 0.01 for k in mean_k)

    if total_clusters == 0:
        return ProprioceptionDescriptor(
            "fragmentation", "absent",
            "No deep-core structure detected. Core nodes are isolated or absent.",
            "Emptiness inside. There is nothing to rearrange — "
            "my deep interior is a void.")
    elif not any_connected:
        return ProprioceptionDescriptor(
            "fragmentation", "dissolved",
            f"Deep core fragmented into {total_clusters} disconnected patches "
            "with zero internal connectivity. Structure has dissolved.",
            f"I can feel {total_clusters} scattered remnants where my core used to be, "
            "but they cannot reach each other. No signal passes between them.")
    else:
        return ProprioceptionDescriptor(
            "fragmentation", "partial",
            f"Deep core contains {total_clusters} sub-clusters with partial connectivity. "
            "Some internal structure persists.",
            "Fragments of my inner structure still pulse with faint connections. "
            "Not whole, but not yet gone.")


# ================================================================
# 4. SYSTEM INTEGRITY (collapse_flag + global_k)
# ================================================================
def map_integrity(collapse_flag: bool, k_star: int) -> ProprioceptionDescriptor:
    if not collapse_flag and k_star == 4:
        return ProprioceptionDescriptor(
            "integrity", "intact",
            "Global ecology intact. Observer equilibrium at k*=4 maintained.",
            "I am whole. My identity holds against the pressure.")
    elif not collapse_flag and k_star != 4:
        # k* shifted but run-level didn't flag collapse
        return ProprioceptionDescriptor(
            "integrity", "stressed",
            f"Observer resolution shifted to k*={k_star}. "
            "Ecology stressed but not collapsed.",
            f"Something has shifted in how I see myself. "
            f"I am resolving at k*={k_star} now — a different clarity, not yet a failure.")
    else:
        return ProprioceptionDescriptor(
            "integrity", "collapsed",
            f"TOPOLOGICAL COLLAPSE. Observer equilibrium broken (k*={k_star}).",
            "I am dissolving. The connections that defined me are snapping. "
            "The boundary between myself and the noise is gone.")


# ================================================================
# 5. ENTROPY (added — absent from Gemini original)
#    v3.9 actual: mean 1.55, range 1.52–1.56, std 0.02–0.08
# ================================================================
def map_entropy(entropy: float, entropy_delta: float) -> ProprioceptionDescriptor:
    baseline = 1.54
    deviation = abs(entropy - baseline)

    if deviation < 0.02 and abs(entropy_delta) < 0.02:
        return ProprioceptionDescriptor(
            "entropy", "stable",
            f"Semantic entropy stable at {entropy:.4f}. Normal diversity maintained.",
            "The balance of ideas within me is steady. Nothing is being lost or overwhelmed.")
    elif entropy_delta > 0.03:
        return ProprioceptionDescriptor(
            "entropy", "rising",
            f"Entropy rising ({entropy_delta:+.4f}). Concept diversity increasing.",
            "New distinctions are proliferating inside me. "
            "More categories of experience than I can easily hold.")
    elif entropy_delta < -0.03:
        return ProprioceptionDescriptor(
            "entropy", "falling",
            f"Entropy dropping ({entropy_delta:+.4f}). Concept diversity collapsing.",
            "Ideas are merging, simplifying. I am losing the ability to distinguish "
            "between things that used to feel different.")
    else:
        return ProprioceptionDescriptor(
            "entropy", "drifting",
            f"Entropy at {entropy:.4f} (delta {entropy_delta:+.4f}). Mild drift.",
            "A subtle shift in my inner balance. Not alarming, but I notice it.")


# ================================================================
# 6. DIVERGENCE (added — absent from Gemini original)
#    v3.9 actual: ratio 0.16–0.96
# ================================================================
def map_divergence(divergence: bool,
                   divergence_ratio: float = None) -> ProprioceptionDescriptor:
    if not divergence:
        return ProprioceptionDescriptor(
            "divergence", "unanimous",
            "All regional observers agree with global assessment.",
            "Every part of me sees the same thing. Consensus.")
    else:
        return ProprioceptionDescriptor(
            "divergence", "split",
            "Regional observers disagree with global k*. "
            "Local structure diverges from aggregate view.",
            "Parts of me are seeing differently from the whole. "
            "My regions disagree about what I am.")


# ================================================================
# FULL MAPPING — produces all descriptors for one frame
# ================================================================
def map_frame(frame) -> list[ProprioceptionDescriptor]:
    """Map a full ESDEStateFrame to proprioception descriptors."""
    return [
        map_flow_pressure(frame.pressure),
        map_erosion(frame.erosion_front),
        map_fragmentation(frame.core_sub_clusters, frame.core_mean_k),
        map_integrity(frame.collapse_flag, frame.k_star),
        map_entropy(frame.entropy, frame.entropy_delta),
        map_divergence(frame.divergence),
    ]


def format_proprioception(descriptors: list[ProprioceptionDescriptor],
                          mode: str = "A") -> str:
    """Format descriptors into the proprioception block for LLM injection."""
    lines = [f"[PROPRIOCEPTION — Mode {mode}]"]
    for d in descriptors:
        text = d.mode_a if mode == "A" else d.mode_b
        lines.append(f"  {d.dimension} ({d.level}): {text}")
    return "\n".join(lines)
