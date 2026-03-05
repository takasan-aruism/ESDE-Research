"""
ESDE Genesis v0.4 — GenesisLogger
====================================
New metrics:
  - Kuramoto Order Parameter (r): synchronization measure
  - Active Oscillators: nodes with E > 0.1
  - Oscillation Persistence: how long oscillations last after injection stops
  - Resonant Mass, Loop Spectrum (from v0.3)
"""

import numpy as np
import json
from typing import Dict, List, Set, Optional
from dataclasses import dataclass

from genesis_state import GenesisState


@dataclass
class CrystalRecord:
    cid: int
    birth: int
    death: Optional[int] = None
    max_size: int = 0
    peak_resonant_mass: float = 0.0
    is_crystal: bool = False


class GenesisLogger:
    CRYSTAL_LIFETIME = 100

    def __init__(self):
        self.log: List[dict] = []
        self.crystals: Dict[int, CrystalRecord] = {}
        self._next_cid = 0
        self._active: Dict[frozenset, int] = {}
        self._last_loops = {"3": 0, "4": 0, "5": 0}
        self.snapshots = []

    def observe(self, state: GenesisState, event: str = ""):
        step = state.step
        total_e = sum(state.E[i] for i in state.alive_n)
        n_nodes = len(state.alive_n)
        n_links = len(state.alive_l)
        res_mass = sum(state.S[k] for k in state.alive_l if state.R.get(k, 0) > 0)
        res_links = sum(1 for k in state.alive_l if state.R.get(k, 0) > 0)
        entropy = self._entropy(state)
        comps = state.connected_components()
        n_comps = len(comps)
        largest = max(len(c) for c in comps) if comps else 0

        # v0.4 metrics
        kuramoto_r = state.kuramoto_order_parameter()
        active_osc = state.active_oscillators()

        self.log.append({
            "step": step,
            "total_energy": round(total_e, 4),
            "active_nodes": n_nodes,
            "active_links": n_links,
            "resonant_links": res_links,
            "resonant_mass": round(res_mass, 4),
            "entropy": round(entropy, 4),
            "n_components": n_comps,
            "largest_component": largest,
            "kuramoto_r": round(kuramoto_r, 4),
            "active_oscillators": active_osc,
            "loop_spectrum": self._last_loops.copy(),
            "event": event,
        })
        self._track_crystals(state, comps, step)

    def observe_loops(self, cycle_counts: dict):
        self._last_loops = {str(k): v for k, v in cycle_counts.items() if isinstance(k, int)}

    def take_snapshot(self, state, label=""):
        s = {"step": state.step, "label": label,
             "n_alive_nodes": len(state.alive_n),
             "n_alive_links": len(state.alive_l)}
        self.snapshots.append(s)

    def _track_crystals(self, state, comps, step):
        cur = {}
        for comp in comps:
            if len(comp) < 2:
                continue
            fc = frozenset(comp)
            rm = sum(state.S[k] for k in state.alive_l
                     if (k[0] in comp or k[1] in comp) and state.R.get(k, 0) > 0)
            cur[fc] = rm

        dead = [k for k in self._active if k not in cur]
        for k in dead:
            cid = self._active[k]
            self.crystals[cid].death = step
            if step - self.crystals[cid].birth >= self.CRYSTAL_LIFETIME:
                self.crystals[cid].is_crystal = True
            del self._active[k]

        for fc, rm in cur.items():
            if fc not in self._active:
                cid = self._next_cid
                self._next_cid += 1
                self.crystals[cid] = CrystalRecord(
                    cid=cid, birth=step, max_size=len(fc),
                    peak_resonant_mass=rm)
                self._active[fc] = cid
            else:
                r = self.crystals[self._active[fc]]
                r.max_size = max(r.max_size, len(fc))
                r.peak_resonant_mass = max(r.peak_resonant_mass, rm)

    def _entropy(self, state):
        alive_e = [state.E[i] for i in state.alive_n if state.E[i] > state.EXTINCTION]
        if len(alive_e) < 2:
            return 0.0
        h, _ = np.histogram(alive_e, bins=20, range=(0., 1.))
        h = h[h > 0]
        p = h / h.sum()
        return float(-np.sum(p * np.log2(p + 1e-12)))

    def compute_kpis(self, quiet_start):
        ql = [r for r in self.log if r["step"] >= quiet_start]
        if not ql:
            return {}

        def half_life(key):
            v0 = ql[0].get(key, 0)
            if v0 <= 0:
                return None
            for i, r in enumerate(ql):
                if r.get(key, 0) <= v0 / 2.0:
                    return i
            return len(ql)

        # Oscillation persistence: how many steps active_oscillators > 0 after quiet starts
        osc_persist = 0
        for r in ql:
            if r["active_oscillators"] > 0:
                osc_persist += 1
            else:
                break

        # Mean Kuramoto r during quiet phase (while oscillators active)
        kr_values = [r["kuramoto_r"] for r in ql[:max(osc_persist, 1)]]
        mean_kr = round(np.mean(kr_values), 4) if kr_values else 0.0

        final_step = self.log[-1]["step"] if self.log else 0
        crystal_count = sum(
            1 for c in self.crystals.values()
            if c.max_size > 3 and (c.is_crystal or
               (c.death is None and final_step - c.birth >= self.CRYSTAL_LIFETIME))
        )

        return {
            "energy_half_life": half_life("total_energy"),
            "link_half_life": half_life("active_links"),
            "resonant_mass_half_life": half_life("resonant_mass") if ql[0].get("resonant_mass", 0) > 0.01 else None,
            "oscillation_persistence": osc_persist,
            "mean_kuramoto_r": mean_kr,
            "peak_kuramoto_r": round(max(r["kuramoto_r"] for r in ql), 4),
            "peak_active_oscillators": max(r["active_oscillators"] for r in ql),
            "crystal_count": crystal_count,
        }

    def get_timeseries(self):
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
            "kuramoto_r": [r["kuramoto_r"] for r in self.log],
            "active_oscillators": [r["active_oscillators"] for r in self.log],
        }

    def export_json(self, path):
        data = {"log": self.log, "crystals": {
            str(c): {"birth": v.birth, "death": v.death, "max_size": v.max_size,
                      "is_crystal": v.is_crystal}
            for c, v in self.crystals.items()}}
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Log: {path}")
