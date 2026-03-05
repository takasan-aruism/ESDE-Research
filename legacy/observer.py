"""
ESDE Genesis v0.1 — Observer Module
======================================
Read-only logging, KPI computation, visualization.
"""

import numpy as np
import json
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from collections import defaultdict

from universe import Universe


@dataclass
class StructureRecord:
    structure_id: int
    birth_step: int
    death_step: Optional[int] = None
    max_size: int = 0
    is_crystal: bool = False
    peak_density: float = 0.0
    cause_of_death: str = ""


class Observer:
    CRYSTAL_DENSITY_THRESHOLD = 0.5

    def __init__(self):
        self.global_log = []
        self.structures = {}
        self._next_sid = 0
        self._active = {}
        self.snapshots = []

    def observe(self, universe, event=""):
        step = universe.step_count
        total_e = sum(n.energy for n in universe.nodes.values())
        an = len(universe.active_nodes())
        al = len(universe.active_links())
        tc = universe.total_triangle_count()
        cc = self._clustering(universe)
        ent = self._entropy(universe)
        comps = universe.connected_components()
        nc = len(comps)
        lc = max(len(c) for c in comps) if comps else 0

        self.global_log.append({
            "step": step,
            "stats": {
                "total_energy": round(total_e, 4),
                "node_count_active": an,
                "link_count": al,
                "triangle_count": tc,
                "avg_clustering_coeff": round(cc, 4),
                "entropy": round(ent, 4),
                "n_components": nc,
                "largest_component": lc,
            },
            "event": event,
        })
        self._track(universe, comps, step)

    def take_snapshot(self, universe, label=""):
        s = universe.snapshot()
        s["label"] = label
        self.snapshots.append(s)

    def _track(self, universe, comps, step):
        cur = {}
        for comp in comps:
            if len(comp) < 2:
                continue
            fc = frozenset(comp)
            cur[fc] = universe.component_density(comp)

        dead = [k for k in self._active if k not in cur]
        for k in dead:
            self.structures[self._active[k]].death_step = step
            self.structures[self._active[k]].cause_of_death = "decay"
            del self._active[k]

        for fc, dens in cur.items():
            if fc not in self._active:
                sid = self._next_sid
                self._next_sid += 1
                self.structures[sid] = StructureRecord(
                    structure_id=sid, birth_step=step,
                    max_size=len(fc),
                    is_crystal=dens > self.CRYSTAL_DENSITY_THRESHOLD,
                    peak_density=dens)
                self._active[fc] = sid
            else:
                r = self.structures[self._active[fc]]
                r.max_size = max(r.max_size, len(fc))
                r.peak_density = max(r.peak_density, dens)
                if dens > self.CRYSTAL_DENSITY_THRESHOLD:
                    r.is_crystal = True

    def _entropy(self, universe):
        e = universe.get_energy_array()
        alive = e[e > universe.EXTINCTION_THRESHOLD]
        if len(alive) < 2:
            return 0.0
        h, _ = np.histogram(alive, bins=20, range=(0., 1.))
        h = h[h > 0]
        p = h / h.sum()
        return float(-np.sum(p * np.log2(p + 1e-12)))

    def _clustering(self, universe):
        coeffs = []
        for n in universe.active_nodes():
            nbrs = universe.neighbors(n.id)
            k = len(nbrs)
            if k < 2:
                coeffs.append(0.0)
                continue
            lb = 0
            for a in range(len(nbrs)):
                for b in range(a+1, len(nbrs)):
                    key = (min(nbrs[a], nbrs[b]), max(nbrs[a], nbrs[b]))
                    if key in universe.links and universe.links[key].alive:
                        lb += 1
            coeffs.append(lb / (k*(k-1)/2))
        return float(np.mean(coeffs)) if coeffs else 0.0

    def compute_kpis(self, quiet_start):
        ql = [r for r in self.global_log if r["step"] >= quiet_start]
        if not ql:
            return {"energy_half_life": 0, "link_half_life": 0, "triangle_half_life": 0}

        def half_life(key):
            v0 = ql[0]["stats"][key]
            if v0 <= 0:
                return len(ql)
            for i, r in enumerate(ql):
                if r["stats"][key] <= v0 / 2.0:
                    return i
            return len(ql)

        e0 = ql[0]["stats"]["total_energy"]
        l0 = ql[0]["stats"]["link_count"]
        t0 = ql[0]["stats"]["triangle_count"]

        fs = self.global_log[-1]["step"] if self.global_log else 0
        alive_s = [s for s in self.structures.values()
                   if s.death_step is None or s.death_step > fs - 10]

        return {
            "energy_half_life": half_life("total_energy"),
            "link_half_life": half_life("link_count"),
            "triangle_half_life": half_life("triangle_count"),
            "peak_energy_at_quiet": round(e0, 4),
            "peak_links_at_quiet": l0,
            "peak_triangles_at_quiet": t0,
            "diversity_unique_sizes": len(set(s.max_size for s in alive_s)),
            "crystal_count": sum(1 for s in alive_s if s.is_crystal),
            "total_structures_born": len(self.structures),
            "structures_still_alive": sum(
                1 for s in self.structures.values() if s.death_step is None),
        }

    def get_timeseries(self):
        return {
            "step": [r["step"] for r in self.global_log],
            "total_energy": [r["stats"]["total_energy"] for r in self.global_log],
            "active_nodes": [r["stats"]["node_count_active"] for r in self.global_log],
            "active_links": [r["stats"]["link_count"] for r in self.global_log],
            "triangle_count": [r["stats"]["triangle_count"] for r in self.global_log],
            "clustering": [r["stats"]["avg_clustering_coeff"] for r in self.global_log],
            "entropy": [r["stats"]["entropy"] for r in self.global_log],
            "n_components": [r["stats"]["n_components"] for r in self.global_log],
            "largest_component": [r["stats"]["largest_component"] for r in self.global_log],
        }

    def export_json(self, path):
        data = {
            "global_log": self.global_log,
            "structures": {
                sid: {"structure_id": s.structure_id, "birth_step": s.birth_step,
                      "death_step": s.death_step, "max_size": s.max_size,
                      "is_crystal": s.is_crystal,
                      "peak_density": round(s.peak_density, 4),
                      "cause_of_death": s.cause_of_death}
                for sid, s in self.structures.items()
            },
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Log: {path}")
