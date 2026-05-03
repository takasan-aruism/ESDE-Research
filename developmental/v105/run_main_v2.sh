#!/bin/bash
# v10.5 main re-run (Leakage 修正版): 24 seeds × 50 windows、tag main_v2
set -e

cd "$(dirname "$0")"
mkdir -p run_logs_main_v2

SEEDS_START=${1:-0}
SEEDS_END=${2:-23}
PARALLEL_JOBS=${3:-8}

echo "v10.5 main_v2 (leakage fix): seeds [$SEEDS_START..$SEEDS_END], -j$PARALLEL_JOBS"
seq "$SEEDS_START" "$SEEDS_END" | parallel -j"$PARALLEL_JOBS" \
    "python3 v105_memory_readout.py --seed {} \
        --maturation-windows 20 --tracking-windows 50 \
        --window-steps 500 --tag main_v2 > run_logs_main_v2/seed{}.log 2>&1; \
     echo \"seed={} exit=\$?\""
echo "v10.5 main_v2 done."
