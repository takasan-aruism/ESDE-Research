"""
ESDE Engine Accelerator
========================
Import this module to optimize hot paths. No physics changes.

Optimizations:
  1. link_strength_sum: O(all_links) → O(degree)  [verified exact match]
  2. _exclusion: uses neighbors instead of full scan [verified]
  3. cycle_finder: C extension for find_all_cycles  [verified exact match]
  4. latent refresh: batch noise generation          [same RNG sequence]

Usage: import engine_accel  (at top of script, after sys.path setup)
"""

import numpy as np
from genesis_state import GenesisState
from genesis_physics import GenesisPhysics
from realization import RealizationOperator


# ================================================================
# 1. link_strength_sum — O(links) → O(degree)
# ================================================================
def _fast_link_strength_sum(self, nid):
    t = 0.0
    for nb in self.neighbors(nid):
        k = self.key(nid, nb)
        if k in self.alive_l:
            t += self.S[k]
    return t

GenesisState.link_strength_sum = _fast_link_strength_sum


# ================================================================
# 2. _exclusion — O(N * links) → O(N * degree)
# ================================================================
def _fast_exclusion(self, state):
    for i in list(state.alive_n):
        total = state.link_strength_sum(i)
        if total <= state.c_max:
            continue
        conn = []
        for nb in state.neighbors(i):
            k = state.key(i, nb)
            if k in state.alive_l:
                conn.append((k, state.S[k]))
        conn.sort(key=lambda x: (x[1], x[0]))
        cur = total
        for k, s in conn:
            if cur <= state.c_max:
                break
            cur -= s
            state.kill_link(k)

GenesisPhysics._exclusion = _fast_exclusion


# ================================================================
# 3. C cycle finder (optional — falls back silently if not built)
# ================================================================
_has_c_cycles = False
try:
    from _cycle_finder import find_all_cycles_c

    def _build_adjacency(state):
        n = state.n_nodes
        if state._nbr_dirty:
            state._rebuild_nbr()
        adj_flat = []
        adj_off = [0] * n
        adj_sz = [0] * n
        offset = 0
        for i in range(n):
            nbrs = state._nbr.get(i, [])
            adj_off[i] = offset
            adj_sz[i] = len(nbrs)
            adj_flat.extend(nbrs)
            offset += len(nbrs)
        return adj_flat, adj_off, adj_sz

    def _fast_find_all_cycles(self, max_length=5):
        adj_flat, adj_off, adj_sz = _build_adjacency(self)
        edges = list(self.alive_l)
        return find_all_cycles_c(adj_flat, adj_off, adj_sz,
                                 edges, self.n_nodes, max_length)

    GenesisState.find_all_cycles = _fast_find_all_cycles
    _has_c_cycles = True
except ImportError:
    pass


# ================================================================
# 4. Latent refresh — batch noise generation (same RNG sequence)
# ================================================================
_original_realization_step = RealizationOperator.step

def _fast_realization_step(self, state):
    """Same logic as original, but batch-generates randn values."""
    if not self.params.enabled:
        return 0

    p = self.params
    self.realized_this_step = 0
    alive_list = list(state.alive_n)
    n_alive = len(alive_list)
    if n_alive < 2:
        return 0

    # A. Latent Refresh — batch noise (same RNG sequence as original)
    l_keys = list(state.L.keys())
    if l_keys:
        n_refresh = min(len(l_keys), 500)
        refresh_idx = state._latent_rng.choice(len(l_keys), n_refresh, replace=False)
        # Batch: generate all noise at once instead of per-key randn()
        noise_raw = np.abs(state._latent_rng.randn(n_refresh))
        for ii, idx in enumerate(refresh_idx):
            k = l_keys[idx]
            f_avg = (state.F[k[0]] + state.F[k[1]]) / 2.0
            eff_rate = p.latent_refresh_rate * f_avg
            state.L[k] = min(1.0, state.L[k] + noise_raw[ii] * eff_rate)

    # B. Realization — unchanged logic (preserves RNG sequence exactly)
    k_samples = min(3, n_alive - 1)
    alive_arr = np.array(alive_list)

    for i in alive_list:
        candidates = state.rng.choice(alive_arr, size=k_samples + 1, replace=False)
        for j in candidates:
            j = int(j)
            if j == i:
                continue
            link_key = state.key(i, j)
            if link_key in state.alive_l:
                continue

            l_ij = state.get_latent(i, j)
            p_realize = p.p_link_birth * l_ij
            if state.rng.random() < p_realize:
                state.add_link(i, j, p.latent_to_active_threshold)
                state.set_latent(i, j, l_ij - p.latent_to_active_threshold)
                self.realized_this_step += 1

    return self.realized_this_step

RealizationOperator.step = _fast_realization_step


# ================================================================
# Status
# ================================================================
_accel_list = ["link_strength_sum", "exclusion", "latent_refresh"]
if _has_c_cycles:
    _accel_list.append("cycle_finder(C)")
print(f"  [engine_accel] Loaded: {', '.join(_accel_list)}")
