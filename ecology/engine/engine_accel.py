"""
Patch: Optimize link_strength_sum and exclusion to use neighbor cache.
Algorithm: identical. Output: identical. Speed: ~100-1000x for these functions.

Usage: import engine_accel (similar to cycle_finder)
"""
from genesis_state import GenesisState
from genesis_physics import GenesisPhysics


# ================================================================
# Fix 1: link_strength_sum — O(links) → O(degree)
# ================================================================
_original_link_strength_sum = GenesisState.link_strength_sum

def _fast_link_strength_sum(self, nid):
    t = 0.0
    for nb in self.neighbors(nid):
        k = self.key(nid, nb)
        if k in self.alive_l:
            t += self.S[k]
    return t

GenesisState.link_strength_sum = _fast_link_strength_sum


# ================================================================
# Fix 2: _exclusion — O(N * links) → O(N * degree)
# ================================================================
_original_exclusion = GenesisPhysics._exclusion

def _fast_exclusion(self, state):
    for i in list(state.alive_n):
        total = state.link_strength_sum(i)
        if total <= state.c_max:
            continue
        # Build conn using neighbors instead of scanning all alive_l
        conn = []
        for nb in state.neighbors(i):
            k = state.key(i, nb)
            if k in state.alive_l:
                conn.append((k, state.S[k]))
        conn.sort(key=lambda x: (x[1], x[0]))  # deterministic tiebreak by link key
        cur = total
        for k, s in conn:
            if cur <= state.c_max:
                break
            cur -= s
            state.kill_link(k)

GenesisPhysics._exclusion = _fast_exclusion

print("  [engine_accel] Optimized link_strength_sum + exclusion loaded")
