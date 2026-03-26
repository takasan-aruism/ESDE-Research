#!/usr/bin/env python3
"""
ESDE engine_accel v5 — L dict sharding for cache locality
============================================================
Replaces state.L (flat dict with millions of entries) with a
sharded dict-of-dicts keyed by the smaller node ID.

PROBLEM:
  state.L grows to 3M+ entries over 200 windows.
  At 48 parallel processes, hash tables exceed L3 cache.
  get_latent() degrades from 16s/win to 40s/win.

SOLUTION:
  L[(a,b)] → L_shards[a][b]  (where a < b, always)
  Each shard has ~1000 entries → fits in L1 cache (32KB).
  When processing node i, only L_shards[i] is touched.

RESULT INTEGRITY:
  Same values in same order. Only storage layout changes.
  Flat dict interface preserved for external code (keys(), etc).

USAGE:
  import engine_accel        # v1/v2
  import engine_accel_v3     # v3
  import engine_accel_v5     # v5 L sharding (this file)
"""

from genesis_state import GenesisState


class ShardedLatentDict:
    """Dict-like object backed by per-node shards.
    
    External interface: L[(a,b)] where a < b.
    Internal storage: shards[a][b] = value.
    
    keys(), __contains__, __getitem__, __setitem__, __len__
    all work as expected. keys() iterates all shards (slow,
    but only called once per step for latent_refresh).
    """
    
    __slots__ = ('shards', '_len')
    
    def __init__(self):
        self.shards = {}
        self._len = 0
    
    def __contains__(self, key):
        a, b = key
        shard = self.shards.get(a)
        if shard is None:
            return False
        return b in shard
    
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
        """Iterate all keys. Used by latent_refresh (once per step)."""
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
# PATCH: Replace state.L with ShardedLatentDict
# ================================================================

_original_init = GenesisState.__init__

def _patched_init(self, *args, **kwargs):
    _original_init(self, *args, **kwargs)
    # Migrate existing L entries (if any from init) to sharded dict
    old_L = self.L
    new_L = ShardedLatentDict()
    if isinstance(old_L, dict):
        for k, v in old_L.items():
            new_L[k] = v
    self.L = new_L

GenesisState.__init__ = _patched_init


# ================================================================
# PATCH: get_latent with shard-direct access
# ================================================================
# Override v3's _fast_get_latent with shard-aware version.
# Avoids going through ShardedLatentDict.__contains__ + __getitem__.

def _sharded_get_latent(self, a, b):
    if a > b:
        a, b = b, a
    shards = self.L.shards
    shard = shards.get(a)
    if shard is not None:
        val = shard.get(b)
        if val is not None:
            return val
    # Lazy init
    val = self._latent_rng.random()
    if shard is None:
        shard = {}
        shards[a] = shard
    shard[b] = val
    self.L._len += 1
    return val

GenesisState.get_latent = _sharded_get_latent


# ================================================================
# PATCH: set_latent with shard-direct access
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
# REPORT
# ================================================================
print(f"  [engine_accel_v5] L dict → ShardedLatentDict")
print(f"  [engine_accel_v5] get_latent/set_latent → shard-direct")
