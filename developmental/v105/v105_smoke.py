#!/usr/bin/env python3
"""ESDE v10.5 smoke wrapper.

実装指示書 §F.2 + §G: smoke (動作確認)
  N=5000、tracking 10、1 seed
  確認項目:
    - α-Integration が誕生するか
    - β-Integration が誕生し、cid 1 → β 1 規律が守られているか
    - β の Q/C 継承・再分配が動くか
    - Salience event log が記録されるか
    - Leakage event log が記録されるか
    - 全 logger が出力されるか
    - 物理層が v10.4 baseline と bit-identical か (engine.state, labels)
  M1-M6 判定基準:
    M1: target 比 ≤ 30%
    M2: events/step ≤ 15
    M3: CSV size ≤ 750 MB
    M4: wall ratio ≤ 1.5 (vs v10.4)
    M5: β 統合数 ≤ cid 半数 (β インフレ判定)
    M6: 1 cid → 1 β (例外なし、規律違反検知)

USAGE:
  python v105_smoke.py [--seed 0]
"""
import argparse
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from v105_memory_readout import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="v10.5 smoke run")
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
