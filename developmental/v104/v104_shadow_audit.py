#!/usr/bin/env python3
"""ESDE v10.4 shadow audit wrapper.

実装指示書 §12.3: shadow audit (必須)
  N=5000、tracking 50、24 seeds
  C 消費・Q/C 継承・再分配は記録のみ、実消費しない (be3_shadow_audit=True)

USAGE:
  seq 0 23 | parallel -j8 python v104_shadow_audit.py --seed {} --tag shadow
"""
import argparse
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from v104_memory_readout import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="v10.4 shadow audit run")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--maturation-windows", type=int, default=20)
    parser.add_argument("--tracking-windows", type=int, default=50)
    parser.add_argument("--window-steps", type=int, default=500)
    parser.add_argument("--tag", type=str, default="shadow")
    parser.add_argument("--N", type=int, default=None)
    args = parser.parse_args()

    run(seed=args.seed,
        maturation_windows=args.maturation_windows,
        tracking_windows=args.tracking_windows,
        window_steps=args.window_steps,
        tag=args.tag,
        disable_e3=False,
        be3_shadow_audit=True,
        N=args.N)
