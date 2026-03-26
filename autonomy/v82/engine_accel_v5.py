#!/usr/bin/env python3
"""
ESDE engine_accel v5 — L dict sharding + latent_refresh sampling fix
=====================================================================
Two changes that work together:

1. L dict → ShardedLatentDict (per-node shards)
2. latent_refresh: instead of list(L.keys()) every step,
   pick random nodes then sample within their shards.

PROBLEM:
  _fast_realization_step line 112:
    l_keys = list(state.L.keys())   ← 7M entries, 50x/window
  This single line dominates runtime at w100+.

FIX:
  Pick random alive nodes → sample within their L shards.
  Never build the full key list. Each shard is ~1000 entries.

RESULT INTEGRITY:
  latent_refresh is stochastic noise injection. The exact
  set of 500 keys refreshed per step does not need to be
  identical — the distribution matters, not the specific keys.
  Same physics, same birth/death logic.

USAGE:
  import engine_accel        # v1/v2
  import engine_accel_v3     # v3
  import engine_accel_v5     # v5 (this file)
"""

import numpy as np
from genesis_state import GenesisState
from realization import RealizationOperator


# ================================================================
# ShardedLatentDict
# ================================================================
class ShardedLatentDict:
    """Dict-like object backed by per-node shards.
    
    Key: (a, b) where a < b.
    Storage: shards[a][b] = value.
    """
    
    __slots__ = ('shards', '_len')
    
    def __init__(self):
        self.shards = {}
        self._len = 0
    
    def __contains__(self, key):
        a, b = key
        shard = self.shards.get(a)
        return shard is not None and b in shard
    
    def __getitem__(self, key):
        a, b = key
        return self.shards[a][b]
    
    def __setitem__(self, key, value):
        a, b = key
        shard = self.shards.get(a)
        if shard is None:
            shard = {}
            self.shards[a] = shard
        if b not in shard:
            self._len += 1
        shard[b] = value
    
    def __delitem__(self, key):
        a, b = key
        shard = self.shards.get(a)
        if shard is not None and b in shard:
            del shard[b]
            self._len -= 1
            if not shard:
                del self.shards[a]
    
    def __len__(self):
        return self._len
    
    def get(self, key, default=None):
        a, b = key
        shard = self.shards.get(a)
        if shard is None:
            return default
        return shard.get(b, default)
    
    def keys(self):
        for a, shard in self.shards.items():
            for b in shard:
                yield (a, b)
    
    def __iter__(self):
        return self.keys()
    
    def items(self):
        for a, shard in self.shards.items():
            for b, v in shard.items():
                yield (a, b), v
    
    def values(self):
        for shard in self.shards.values():
            yield from shard.values()
    
    def pop(self, key, *args):
        a, b = key
        shard = self.shards.get(a)
        if shard is None:
            if args:
                return args[0]
            raise KeyError(key)
        if b in shard:
            self._len -= 1
            val = shard.pop(b)
            if not shard:
                del self.shards[a]
            return val
        if args:
            return args[0]
        raise KeyError(key)


# ================================================================
# PATCH 1: Replace state.L with ShardedLatentDict
# ================================================================
_original_init = GenesisState.__init__

def _patched_init(self, *args, **kwargs):
    _original_init(self, *args, **kwargs)
    old_L = self.L
    new_L = ShardedLatentDict()
    if isinstance(old_L, dict):
        for k, v in old_L.items():
            new_L[k] = v
    self.L = new_L

GenesisState.__init__ = _patched_init


# ================================================================
# PATCH 2: get_latent — shard-direct (override v3)
# ================================================================
def _sharded_get_latent(self, a, b):
    if a > b:
        a, b = b, a
    shards = self.L.shards
    shard = shards.get(a)
    if shard is not None:
        val = shard.get(b)
        if val is not None:
            return val
    val = self._latent_rng.random()
    if shard is None:
        shard = {}
        shards[a] = shard
    shard[b] = val
    self.L._len += 1
    return val

GenesisState.get_latent = _sharded_get_latent


# ================================================================
# PATCH 3: set_latent — shard-direct (override v3)
# ================================================================
def _sharded_set_latent(self, a, b, val):
    if a > b:
        a, b = b, a
    val = max(0.0, min(1.0, val))
    shards = self.L.shards
    shard = shards.get(a)
    if shard is None:
        shard = {}
        shards[a] = shard
        self.L._len += 1
    elif b not in shard:
        self.L._len += 1
    shard[b] = val

GenesisState.set_latent = _sharded_set_latent


# ================================================================
# PATCH 4: Replace _fast_realization_step to avoid list(L.keys())
# ================================================================
# The original (engine_accel.py L99-140) does:
#   A. l_keys = list(state.L.keys())   ← 7M entries per step!
#      pick 500 random, refresh them
#   B. For each alive node, pick 3 random candidates, try realize
#
# We replace A with shard-based sampling. B is unchanged.

def _v5_realization_step(self, state):
    """Realizer step with shard-based latent refresh.
    
    Part A: Pick random nodes, sample their shards, refresh.
            Never builds the full key list.
    Part B: Same as engine_accel (random candidate realization).
    """
    if not self.params.enabled:
        return 0
    
    p = self.params
    self.realized_this_step = 0
    
    alive_list = list(state.alive_n)
    n_alive = len(alive_list)
    if n_alive < 2:
        return 0
    
    # ── A. Latent refresh via shard sampling ──
    # Pick ~20 random nodes, refresh ~25 entries from each shard ≈ 500 total
    shards = state.L.shards
    if shards:
        shard_nodes = list(shards.keys())
        n_shards = len(shard_nodes)
        if n_shards > 0:
            n_nodes_to_sample = min(20, n_shards)
            sampled_node_idx = state._latent_rng.choice(
                n_shards, n_nodes_to_sample, replace=False)
            
            noise_raw = np.abs(state._latent_rng.randn(500))
            noise_i = 0
            
            for idx in sampled_node_idx:
                node_a = shard_nodes[idx]
                shard = shards[node_a]
                if not shard:
                    continue
                shard_keys = list(shard.keys())
                n_pick = min(25, len(shard_keys))
                if n_pick == 0:
                    continue
                pick_idx = state._latent_rng.choice(
                    len(shard_keys), n_pick, replace=False)
                for pi in pick_idx:
                    if noise_i >= 500:
                        break
                    b = shard_keys[pi]
                    f_avg = (state.F[node_a] + state.F[b]) / 2.0
                    eff_rate = p.latent_refresh_rate * f_avg
                    shard[b] = min(1.0, shard[b] + noise_raw[noise_i] * eff_rate)
                    noise_i += 1
    
    # ── B. Realization (unchanged from engine_accel) ──
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

RealizationOperator.step = _v5_realization_step


# ================================================================
# REPORT
# ================================================================
print(f"  [engine_accel_v5] L dict -> ShardedLatentDict")
print(f"  [engine_accel_v5] get_latent/set_latent -> shard-direct")
print(f"  [engine_accel_v5] RealizationOperator.step -> shard-based refresh")
