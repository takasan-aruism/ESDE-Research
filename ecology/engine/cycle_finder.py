"""
ESDE Genesis — Cycle Finder Accelerator
=========================================
Import this module to replace GenesisState.find_all_cycles with C extension.
Falls back to Python if C extension is not built.

Usage: Add 'import cycle_finder' at the top of your script.
No other changes needed.
"""

from collections import defaultdict
from genesis_state import GenesisState

_ACTIVE = False

try:
    from _cycle_finder import find_all_cycles_c

    def _build_adjacency(state):
        """Convert GenesisState neighbor structure to flat C-friendly arrays."""
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
        """Drop-in replacement using C extension. Same input/output contract."""
        adj_flat, adj_off, adj_sz = _build_adjacency(self)
        edges = list(self.alive_l)
        return find_all_cycles_c(adj_flat, adj_off, adj_sz,
                                 edges, self.n_nodes, max_length)

    # Monkey-patch
    GenesisState._python_find_all_cycles = GenesisState.find_all_cycles
    GenesisState.find_all_cycles = _fast_find_all_cycles
    _ACTIVE = True
    print("  [cycle_finder] C extension loaded")

except ImportError:
    print("  [cycle_finder] C extension not found — using Python (build with: python build_cycle_finder.py)")


def is_active():
    """Check if C extension is loaded."""
    return _ACTIVE
