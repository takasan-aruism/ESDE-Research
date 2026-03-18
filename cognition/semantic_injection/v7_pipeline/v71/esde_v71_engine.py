#!/usr/bin/env python3
"""
ESDE v7.1 — Genesis + World Induction
========================================
物理層: V43Engine（Genesis canon）そのまま。
仮想層: virtual_layer.py から import。

このファイルは薄いグルー。物理と仮想を繋ぐだけ。
"""

import sys
from pathlib import Path
from dataclasses import dataclass

# ================================================================
# PATH SETUP
# ================================================================
_SCRIPT_DIR = Path(__file__).resolve().parent      # v71/
_PIPELINE_DIR = _SCRIPT_DIR.parent                  # v7_pipeline/
_SEMANTIC_DIR = _PIPELINE_DIR.parent                # semantic_injection/
_V4_PIPELINE = _SEMANTIC_DIR / "v4_pipeline"        # v4_pipeline/
_V43_DIR = _V4_PIPELINE / "v43"
_V41_DIR = _V4_PIPELINE / "v41"
_REPO_ROOT = _SEMANTIC_DIR.parent.parent            # ESDE-Research/
_ENGINE_DIR = _REPO_ROOT / "ecology" / "engine"

for p in [str(_PIPELINE_DIR), str(_V43_DIR), str(_V41_DIR),
          str(_ENGINE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import engine_accel
assert hasattr(engine_accel, '_fast_link_strength_sum'), \
    "FATAL: engine_accel not loaded"

from esde_v43_engine import V43Engine, EncapsulationParams
from virtual_layer import VirtualLayer


# ================================================================
V71_WINDOW = 50


@dataclass
class V71EncapsulationParams(EncapsulationParams):
    """V43 params + virtual layer toggle."""
    virtual_enabled: bool = True


# ================================================================
class V71Engine(V43Engine):
    """
    V43（Genesis canon）+ VirtualLayer。

    物理層: V43 の step_window() を super() で呼ぶ。一切変更なし。
    仮想層: post-physics で VirtualLayer.step()。
    """

    def __init__(self, seed=42, N=5000, plb=0.007, rate=0.002,
                 encap_params=None):
        params = encap_params or V71EncapsulationParams()
        super().__init__(seed=seed, N=N, plb=plb, rate=rate,
                         encap_params=params)
        self.virtual = VirtualLayer()
        self.virtual_stats = {}

    def step_window(self, steps=V71_WINDOW):
        # V43 full physics + observation
        frame = super().step_window(steps=steps)

        # Virtual Layer (World B) — post-physics
        p = self.island_tracker.params
        if hasattr(p, 'virtual_enabled') and p.virtual_enabled:
            vs = self.virtual.step(
                self.state, frame.window,
                islands=self.island_tracker.islands,
                substrate=self.substrate)
            self.virtual_stats = vs
        else:
            self.virtual_stats = {}

        return frame