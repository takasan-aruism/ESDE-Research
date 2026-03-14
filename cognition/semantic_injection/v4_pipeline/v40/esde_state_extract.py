#!/usr/bin/env python3
"""
ESDE v4.0 — State Extractor
============================
Phase : v4.0 Language Interface (Pipeline Stage 1)
Role  : Claude (Implementation)

Parses v3.9 output files (JSON summary + concept CSV + switch events)
and produces a list of ESDEStateFrame objects — one per observation window.

Input:  outputs_v39/seed_{seed}_amp{tag}.json
        outputs_v39/seed_{seed}_amp{tag}_concept.csv
        outputs_v39/seed_{seed}_amp{tag}_switches.json

Output: List[ESDEStateFrame] (in-memory), or JSON when run standalone.

USAGE
-----
  # Extract single run
  python esde_state_extract.py outputs_v39/seed_1_amp16p0.json

  # Extract all runs in directory
  python esde_state_extract.py --all outputs_v39/

  # Output as JSON
  python esde_state_extract.py outputs_v39/seed_1_amp16p0.json --json
"""

import json, csv, sys, argparse, hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional


# ================================================================
# STATE FRAME
# ================================================================
@dataclass
class ESDEStateFrame:
    """One observation window's complete state."""
    # Identity
    seed: int
    amp: float
    window: int
    n_windows: int

    # Ecology — observer
    k_star: int
    k_changed: bool
    k_prev: Optional[int]
    k_margin: float               # J(new) - J(old) at switch, else 0
    divergence: bool
    divergent_regions: list        # which r_i disagree with global
    regional_k: dict               # {"r0":4, "r1":4, ...}

    # Ecology — thermodynamics
    entropy: float
    entropy_delta: float           # vs previous window

    # Concept dynamics
    n_C: int                       # alive chemistry-3 nodes
    tripartite: int
    erosion_front: dict            # {"A": depth, "B": depth, "C": depth}
    core_alive: dict               # {"A": pres, "B": pres, "C": pres}

    # Deep-core topology
    core_k_var: dict               # {"A": var, ...}
    core_sub_clusters: dict        # {"A": n, ...}
    core_size: dict                # {"A": n, ...}
    core_mean_k: dict              # {"A": k, ...}

    # System health
    collapse_flag: bool
    pressure: float                # amp value

    # Anomaly flags (populated by extractor)
    anomalies: list = field(default_factory=list)

    # Traceability
    state_hash: str = ""

    def compute_hash(self):
        """Deterministic hash over all measurement fields (excludes anomalies/hash)."""
        payload = {
            "seed": self.seed, "amp": self.amp, "window": self.window,
            "k_star": self.k_star, "entropy": self.entropy,
            "erosion_front": self.erosion_front, "core_alive": self.core_alive,
            "core_k_var": self.core_k_var, "core_sub_clusters": self.core_sub_clusters,
            "tripartite": self.tripartite, "divergence": self.divergence,
            "collapse_flag": self.collapse_flag,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        self.state_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return self.state_hash


# ================================================================
# PARSER
# ================================================================
CONCEPTS = ["A", "B", "C"]


def _load_concept_csv(csv_path: Path) -> list[dict]:
    """Load per-window concept CSV. Returns list of row dicts."""
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # Normalize types
            row = {}
            for k, v in r.items():
                try:
                    row[k] = int(v)
                except ValueError:
                    try:
                        row[k] = float(v)
                    except ValueError:
                        row[k] = v
            rows.append(row)
    return rows


def _load_switches(sw_path: Path) -> dict:
    """Load switch events, keyed by window number."""
    if not sw_path.exists():
        return {}
    with open(sw_path) as f:
        events = json.load(f)
    by_window = {}
    for ev in events:
        w = ev.get("window", ev.get("win"))
        if w is not None:
            by_window[w] = ev
    return by_window


def extract_run(summary_path: Path) -> list[ESDEStateFrame]:
    """
    Extract all per-window StateFrames from a single v3.9 run.

    Expects:
      summary_path:  seed_N_ampXpY.json
      concept CSV:   seed_N_ampXpY_concept.csv  (same directory)
      switches:      seed_N_ampXpY_switches.json (same directory, optional)
    """
    with open(summary_path) as f:
        summary = json.load(f)

    seed = summary["seed"]
    amp = summary["amp"]
    n_windows = summary["n_windows"]

    # Derive sibling file paths
    stem = summary_path.stem  # e.g. seed_1_amp16p0
    parent = summary_path.parent
    concept_path = parent / f"{stem}_concept.csv"
    switch_path = parent / f"{stem}_switches.json"

    # Load per-window data
    if not concept_path.exists():
        print(f"  WARNING: {concept_path} not found, skipping", file=sys.stderr)
        return []

    concept_rows = _load_concept_csv(concept_path)
    switches = _load_switches(switch_path)

    # Build frames
    frames = []
    prev_entropy = None
    prev_k = None

    for row in concept_rows:
        wi = row["win"]

        # Observer
        gk = row["gk"]
        k_changed = False
        k_margin = 0.0
        sw = switches.get(wi)
        if sw:
            k_changed = True
            k_margin = sw.get("margin", 0.0)

        # Regional k — not in concept CSV, reconstruct from wlogs if available
        # For now we use div flag; full regional k requires wlog parsing
        div = bool(row.get("div", 0))

        # Entropy
        ent = row["ent"]
        ent_delta = round(ent - prev_entropy, 6) if prev_entropy is not None else 0.0

        # Erosion / core per concept
        erosion_front = {}
        core_alive = {}
        core_kv = {}
        core_sc = {}
        core_sz = {}
        core_mk = {}
        for cn in CONCEPTS:
            erosion_front[cn] = row.get(f"{cn}_erosion_d", 0)
            core_alive[cn] = row.get(f"{cn}_core_pres", 0.0)
            core_kv[cn] = row.get(f"{cn}_core_k_var", 0.0)
            core_sc[cn] = row.get(f"{cn}_sub_clust", 0)
            core_sz[cn] = row.get(f"{cn}_core_size", 0)
            core_mk[cn] = row.get(f"{cn}_core_mk", 0.0)

        # k*=0 means "not yet established" — treat as uninitialized
        k_established = gk > 0

        # Collapse: NOT inferred per-window. Set to False here;
        # only the run-level summary flag (backfilled below) is authoritative.
        collapse_this_window = False

        # Anomaly detection
        anomalies = []
        # Only flag real switches (both sides must be established k*)
        prev_established = prev_k is not None and prev_k > 0
        if k_changed and k_established and prev_established:
            anomalies.append(f"[SWITCH] k*: {prev_k}->{gk}")
        if div and (not frames or not frames[-1].divergence):
            anomalies.append("[DIVERGENCE_ONSET]")
        if not div and frames and frames[-1].divergence:
            anomalies.append("[DIVERGENCE_RESOLVED]")
        if frames:
            for cn in CONCEPTS:
                if erosion_front[cn] > frames[-1].erosion_front.get(cn, 0):
                    anomalies.append(f"[EROSION_ADVANCE] {cn}: {frames[-1].erosion_front[cn]}->{erosion_front[cn]}")
                if core_alive[cn] < 0.01 and frames[-1].core_alive.get(cn, 1.0) >= 0.01:
                    anomalies.append(f"[CORE_DISSOLVED] {cn}")
        if prev_entropy is not None and abs(ent_delta) > 0.03:
            anomalies.append(f"[ENTROPY_SPIKE] delta={ent_delta:+.4f}")

        frame = ESDEStateFrame(
            seed=seed, amp=amp, window=wi, n_windows=n_windows,
            k_star=gk, k_changed=k_changed, k_prev=prev_k,
            k_margin=round(k_margin, 6),
            divergence=div, divergent_regions=[], regional_k={},
            entropy=ent, entropy_delta=ent_delta,
            n_C=row.get("nC", 0), tripartite=row.get("tri", 0),
            erosion_front=erosion_front, core_alive=core_alive,
            core_k_var=core_kv, core_sub_clusters=core_sc,
            core_size=core_sz, core_mean_k=core_mk,
            collapse_flag=collapse_this_window,
            pressure=amp,
            anomalies=anomalies,
        )
        frame.compute_hash()
        frames.append(frame)

        prev_entropy = ent
        prev_k = gk

    # Collapse flag comes ONLY from run-level summary (authoritative source).
    # Per-window inference is unreliable due to observer warmup noise.
    if summary.get("collapse_flag") and frames:
        # Find the first window where dominant_k shifted away from 4
        # (working backwards from summary's global_dominant_k)
        run_dk = summary.get("global_dominant_k", 4)
        collapse_onset = None
        for f in frames:
            if f.k_star > 0 and f.k_star != 4:
                collapse_onset = f.window
                break
        # Mark final windows with collapse flag
        for f in frames[-5:]:
            f.collapse_flag = True
            if "[COLLAPSE_WARNING]" not in " ".join(f.anomalies):
                f.anomalies.append("[COLLAPSE_WARNING]")

    return frames


def extract_directory(dirpath: Path) -> dict:
    """Extract all runs in a directory. Returns {stem: [frames]}."""
    results = {}
    for jp in sorted(dirpath.rglob("seed_*.json")):
        if "_concept" in jp.name or "_switches" in jp.name:
            continue
        stem = jp.stem
        frames = extract_run(jp)
        if frames:
            results[stem] = frames
            print(f"  {stem}: {len(frames)} windows extracted")
    return results


# ================================================================
# CLI
# ================================================================
def main():
    parser = argparse.ArgumentParser(description="ESDE v4.0 State Extractor")
    parser.add_argument("path", help="JSON summary file or directory")
    parser.add_argument("--all", action="store_true", help="Process all runs in directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--out", type=str, default=None, help="Output file path")
    args = parser.parse_args()

    p = Path(args.path)

    if args.all or p.is_dir():
        all_frames = extract_directory(p)
        print(f"\n  Total: {len(all_frames)} runs, "
              f"{sum(len(v) for v in all_frames.values())} frames")
        if args.json:
            out = {k: [asdict(f) for f in v] for k, v in all_frames.items()}
            dest = args.out or "state_frames_all.json"
            with open(dest, "w") as f:
                json.dump(out, f, indent=2)
            print(f"  Written to {dest}")
    else:
        frames = extract_run(p)
        print(f"  {p.stem}: {len(frames)} windows extracted")
        if args.json:
            out = [asdict(f) for f in frames]
            dest = args.out or f"{p.stem}_frames.json"
            with open(dest, "w") as f:
                json.dump(out, f, indent=2)
            print(f"  Written to {dest}")
        else:
            for fr in frames:
                flags = " ".join(fr.anomalies) if fr.anomalies else ""
                print(f"  w{fr.window:2d}: k*={fr.k_star} ent={fr.entropy:.4f} "
                      f"erosion={fr.erosion_front} core={fr.core_alive} "
                      f"hash={fr.state_hash} {flags}")


if __name__ == "__main__":
    main()
