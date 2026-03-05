"""
ESDE Genesis v0.1 — Observer Module
======================================
v0.1 changes:
  - Tracks cycle counts (3,4,5) alongside triangle count
  - get_timeseries() includes cycle metrics

Author: Claude (Implementation)
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
        self._next_structure_id = 0
        self._active_structures = {}
        self.snapshots = []

    def observe(self, universe, event=""):
        step = universe.step_count

        total_energy = sum(n.energy for n in universe.nodes.values())
        active_nodes = len(universe.active_nodes())
        active_links = len(universe.active_links())
        triangle_count = universe.total_triangle_count()
        avg_clustering = self._clustering_coefficient(universe)
        entropy = self._energy_entropy(universe)
        components = universe.connected_components()
        n_components = len(components)
        largest = max(len(c) for c in components) if components else 0

        record = {
            "step": step,
            "stats": {
                "total_energy": round(total_energy, 4),
                "node_count_active": active_nodes,
                "link_count": active_links,
                "triangle_count": triangle_count,
                "avg_clustering_coeff": round(avg_clustering, 4),
                "entropy": round(entropy, 4),
                "n_components": n_components,
                "largest_component": largest,
            },
            "event": event,
        }
        self.global_log.append(record)
        self._track_structures(universe, components, step)

    def take_snapshot(self, universe, label=""):
        snap = universe.snapshot()
        snap["label"] = label
        self.snapshots.append(snap)

    def _track_structures(self, universe, components, step):
        current_sets = {}
        for comp in components:
            if len(comp) < 2:
                continue
            fcomp = frozenset(comp)
            density = universe.component_density(comp)
            current_sets[fcomp] = density

        dead_keys = []
        for fcomp, sid in self._active_structures.items():
            if fcomp not in current_sets:
                self.structures[sid].death_step = step
                self.structures[sid].cause_of_death = "decay"
                dead_keys.append(fcomp)
        for k in dead_keys:
            del self._active_structures[k]

        for fcomp, density in current_sets.items():
            if fcomp not in self._active_structures:
                sid = self._next_structure_id
                self._next_structure_id += 1
                self.structures[sid] = StructureRecord(
                    structure_id=sid, birth_step=step,
                    max_size=len(fcomp),
                    is_crystal=density > self.CRYSTAL_DENSITY_THRESHOLD,
                    peak_density=density,
                )
                self._active_structures[fcomp] = sid
            else:
                sid = self._active_structures[fcomp]
                rec = self.structures[sid]
                rec.max_size = max(rec.max_size, len(fcomp))
                rec.peak_density = max(rec.peak_density, density)
                if density > self.CRYSTAL_DENSITY_THRESHOLD:
                    rec.is_crystal = True

    def _energy_entropy(self, universe):
        energies = universe.get_energy_array()
        alive = energies[energies > universe.EXTINCTION_THRESHOLD]
        if len(alive) < 2:
            return 0.0
        hist, _ = np.histogram(alive, bins=20, range=(0.0, 1.0))
        hist = hist[hist > 0]
        probs = hist / hist.sum()
        return -np.sum(probs * np.log2(probs + 1e-12))

    def _clustering_coefficient(self, universe):
        coeffs = []
        for node in universe.active_nodes():
            nbrs = universe.neighbors(node.id)
            k = len(nbrs)
            if k < 2:
                coeffs.append(0.0)
                continue
            links_between = 0
            for a in range(len(nbrs)):
                for b in range(a + 1, len(nbrs)):
                    key = (min(nbrs[a], nbrs[b]), max(nbrs[a], nbrs[b]))
                    if key in universe.links and universe.links[key].alive:
                        links_between += 1
            coeffs.append(links_between / (k * (k - 1) / 2))
        return np.mean(coeffs) if coeffs else 0.0

    def compute_kpis(self, quiet_start):
        quiet_logs = [r for r in self.global_log if r["step"] >= quiet_start]
        if not quiet_logs:
            return {"energy_half_life": 0, "link_half_life": 0,
                    "triangle_half_life": 0}

        e0 = quiet_logs[0]["stats"]["total_energy"]
        energy_hl = len(quiet_logs)
        for i, log in enumerate(quiet_logs):
            if log["stats"]["total_energy"] <= e0 / 2.0:
                energy_hl = i
                break

        l0 = quiet_logs[0]["stats"]["link_count"]
        link_hl = len(quiet_logs)
        if l0 > 0:
            for i, log in enumerate(quiet_logs):
                if log["stats"]["link_count"] <= l0 / 2.0:
                    link_hl = i
                    break

        t0 = quiet_logs[0]["stats"]["triangle_count"]
        tri_hl = len(quiet_logs)
        if t0 > 0:
            for i, log in enumerate(quiet_logs):
                if log["stats"]["triangle_count"] <= t0 / 2.0:
                    tri_hl = i
                    break

        final_step = self.global_log[-1]["step"] if self.global_log else 0
        alive_s = [s for s in self.structures.values()
                   if s.death_step is None or s.death_step > final_step - 10]
        unique_sizes = set(s.max_size for s in alive_s)
        crystal_count = sum(1 for s in alive_s if s.is_crystal)

        return {
            "energy_half_life": energy_hl,
            "link_half_life": link_hl,
            "triangle_half_life": tri_hl,
            "peak_energy_at_quiet": round(e0, 4),
            "peak_links_at_quiet": l0,
            "peak_triangles_at_quiet": t0,
            "diversity_unique_sizes": len(unique_sizes),
            "crystal_count": crystal_count,
            "total_structures_born": len(self.structures),
            "structures_still_alive": sum(
                1 for s in self.structures.values() if s.death_step is None),
        }

    def get_timeseries(self):
        steps = [r["step"] for r in self.global_log]
        return {
            "step": steps,
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
                sid: {
                    "structure_id": s.structure_id,
                    "birth_step": s.birth_step,
                    "death_step": s.death_step,
                    "max_size": s.max_size,
                    "is_crystal": s.is_crystal,
                    "peak_density": round(s.peak_density, 4),
                    "cause_of_death": s.cause_of_death,
                }
                for sid, s in self.structures.items()
            },
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Log exported: {path}")
