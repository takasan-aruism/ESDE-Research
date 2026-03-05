"""
ESDE Genesis v0.3 — GenesisLogger
====================================
Tracks: Resonant Mass, Crystal Count (lifetime>100), Loop Spectrum,
plus standard metrics (energy, links, entropy, components).

Designed by: Gemini | Audited by: GPT | Implemented by: Claude
"""

import numpy as np
import json
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from collections import defaultdict

from genesis_state import GenesisState


@dataclass
class CrystalRecord:
    """Lifecycle of a connected component."""
    cid: int
    birth: int
    death: Optional[int] = None
    max_size: int = 0
    peak_resonant_mass: float = 0.0
    is_crystal: bool = False  # survived > 100 steps


class GenesisLogger:
    """Read-only observer. Never modifies state."""

    CRYSTAL_LIFETIME_THRESHOLD = 100

    def __init__(self):
        self.log: List[dict] = []
        self.crystals: Dict[int, CrystalRecord] = {}
        self._next_cid = 0
        self._active: Dict[frozenset, int] = {}
        self.snapshots: List[dict] = []

    def observe(self, state: GenesisState, event: str = ""):
        """Record one step."""
        step = state.step

        # Basic stats
        total_e = sum(state.E[i] for i in state.alive_n)
        n_nodes = len(state.alive_n)
        n_links = len(state.alive_l)

        # Resonant Mass: sum of S_ij where R_ij > 0
        resonant_mass = sum(
            state.S[k] for k in state.alive_l if state.R.get(k, 0) > 0
        )

        # Loop Spectrum — filled when cycle_data is passed
        loop_spectrum = self._last_loop_spectrum.copy() if hasattr(self, '_last_loop_spectrum') else {"3": 0, "4": 0, "5": 0}

        # Entropy
        entropy = self._entropy(state)

        # Components
        comps = state.connected_components()
        n_comps = len(comps)
        largest = max(len(c) for c in comps) if comps else 0

        # Triangle count (from resonance cache — links with R > 0)
        n_resonant_links = sum(1 for k in state.alive_l if state.R.get(k, 0) > 0)

        record = {
            "step": step,
            "total_energy": round(total_e, 4),
            "active_nodes": n_nodes,
            "active_links": n_links,
            "resonant_links": n_resonant_links,
            "resonant_mass": round(resonant_mass, 4),
            "entropy": round(entropy, 4),
            "n_components": n_comps,
            "largest_component": largest,
            "loop_spectrum": loop_spectrum,
            "event": event,
        }
        self.log.append(record)

        # Track crystal lifecycles
        self._track_crystals(state, comps, step)

    def observe_loops(self, cycle_counts: dict):
        """Update cached loop spectrum when resonance is recalculated."""
        self._last_loop_spectrum = {str(k): v for k, v in cycle_counts.items() if isinstance(k, int)}
        if self.log:
            self.log[-1]["loop_spectrum"] = self._last_loop_spectrum.copy()

    def take_snapshot(self, state: GenesisState, label: str = ""):
        s = state.snapshot()
        s["label"] = label
        self.snapshots.append(s)

    # ---- Crystal Tracking ----

    def _track_crystals(self, state: GenesisState, comps: List[Set[int]], step: int):
        cur = {}
        for comp in comps:
            if len(comp) < 2:
                continue
            fc = frozenset(comp)
            # Compute resonant mass of this component
            rm = 0.0
            for k in state.alive_l:
                if k[0] in comp or k[1] in comp:
                    if state.R.get(k, 0) > 0:
                        rm += state.S[k]
            cur[fc] = rm

        # Deaths
        dead = [k for k in self._active if k not in cur]
        for k in dead:
            cid = self._active[k]
            self.crystals[cid].death = step
            lifetime = step - self.crystals[cid].birth
            if lifetime >= self.CRYSTAL_LIFETIME_THRESHOLD:
                self.crystals[cid].is_crystal = True
            del self._active[k]

        # Births / updates
        for fc, rm in cur.items():
            if fc not in self._active:
                cid = self._next_cid
                self._next_cid += 1
                self.crystals[cid] = CrystalRecord(
                    cid=cid, birth=step, max_size=len(fc),
                    peak_resonant_mass=rm)
                self._active[fc] = cid
            else:
                cid = self._active[fc]
                r = self.crystals[cid]
                r.max_size = max(r.max_size, len(fc))
                r.peak_resonant_mass = max(r.peak_resonant_mass, rm)

    def _entropy(self, state: GenesisState) -> float:
        alive_e = [state.E[i] for i in state.alive_n if state.E[i] > state.EXTINCTION]
        if len(alive_e) < 2:
            return 0.0
        h, _ = np.histogram(alive_e, bins=20, range=(0., 1.))
        h = h[h > 0]
        p = h / h.sum()
        return float(-np.sum(p * np.log2(p + 1e-12)))

    # ---- KPI Computation ----

    def compute_kpis(self, quiet_start: int) -> dict:
        ql = [r for r in self.log if r["step"] >= quiet_start]
        if not ql:
            return {}

        def half_life(key):
            v0 = ql[0].get(key, 0)
            if v0 <= 0:
                return len(ql)
            for i, r in enumerate(ql):
                if r.get(key, 0) <= v0 / 2.0:
                    return i
            return len(ql)

        # Crystal count
        final_step = self.log[-1]["step"] if self.log else 0
        crystal_count = sum(
            1 for c in self.crystals.values()
            if c.max_size > 3 and (c.is_crystal or (c.death is None and final_step - c.birth >= 100))
        )
        structures_alive = sum(1 for c in self.crystals.values() if c.death is None)

        return {
            "energy_half_life": half_life("total_energy"),
            "link_half_life": half_life("active_links"),
            "resonant_mass_half_life": half_life("resonant_mass"),
            "peak_energy": round(ql[0].get("total_energy", 0), 2),
            "peak_links": ql[0].get("active_links", 0),
            "peak_resonant_mass": round(ql[0].get("resonant_mass", 0), 4),
            "crystal_count": crystal_count,
            "structures_alive": structures_alive,
            "total_structures_born": len(self.crystals),
        }

    # ---- Timeseries ----

    def get_timeseries(self) -> dict:
        return {
            "step": [r["step"] for r in self.log],
            "total_energy": [r["total_energy"] for r in self.log],
            "active_nodes": [r["active_nodes"] for r in self.log],
            "active_links": [r["active_links"] for r in self.log],
            "resonant_links": [r["resonant_links"] for r in self.log],
            "resonant_mass": [r["resonant_mass"] for r in self.log],
            "entropy": [r["entropy"] for r in self.log],
            "n_components": [r["n_components"] for r in self.log],
            "largest_component": [r["largest_component"] for r in self.log],
            "loops_3": [r.get("loop_spectrum", {}).get("3", 0) for r in self.log],
            "loops_4": [r.get("loop_spectrum", {}).get("4", 0) for r in self.log],
            "loops_5": [r.get("loop_spectrum", {}).get("5", 0) for r in self.log],
        }

    # ---- Export ----

    def export_json(self, path: str):
        data = {
            "log": self.log,
            "crystals": {
                str(cid): {
                    "birth": c.birth, "death": c.death,
                    "max_size": c.max_size,
                    "peak_resonant_mass": round(c.peak_resonant_mass, 4),
                    "is_crystal": c.is_crystal,
                }
                for cid, c in self.crystals.items()
            }
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Log: {path}")
