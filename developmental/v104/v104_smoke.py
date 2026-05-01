#!/usr/bin/env python3
"""ESDE v10.4 smoke wrapper.

実装指示書 §12.1: smoke (動作確認)
  N=5000、tracking 10、1 seed
  確認項目:
    - Integration が誕生するか
    - Integration の Q/C 継承が動くか
    - Integration の再分配が動くか
    - 全 logger が出力されるか
    - 物理層が v10.3 baseline と bit-identical か

USAGE:
  python v104_smoke.py [--seed 0]
"""
import argparse
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from v104_memory_readout import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="v10.4 smoke run")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--maturation-windows", type=int, default=20)
    parser.add_argument("--tracking-windows", type=int, default=10)
    parser.add_argument("--window-steps", type=int, default=500)
    parser.add_argument("--tag", type=str, default="smoke")
    parser.add_argument("--N", type=int, default=None)
    args = parser.parse_args()

    run(seed=args.seed,
        maturation_windows=args.maturation_windows,
        tracking_windows=args.tracking_windows,
        window_steps=args.window_steps,
        tag=args.tag,
        disable_e3=False,
        be3_shadow_audit=False,
        N=args.N)
