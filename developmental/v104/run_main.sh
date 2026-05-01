#!/bin/bash
# v10.4 main launcher: 24 seeds × 50 windows in parallel
set -e

cd "$(dirname "$0")"
mkdir -p run_logs_main

SEEDS_START=${1:-0}
SEEDS_END=${2:-23}
PARALLEL_JOBS=${3:-8}

echo "v10.4 main: seeds [$SEEDS_START..$SEEDS_END], -j$PARALLEL_JOBS"
seq "$SEEDS_START" "$SEEDS_END" | parallel -j"$PARALLEL_JOBS" \
    "python3 v104_memory_readout.py --seed {} \
        --maturation-windows 20 --tracking-windows 50 \
        --window-steps 500 --tag main > run_logs_main/seed{}.log 2>&1; \
     echo \"seed={} exit=\$?\""
echo "v10.4 main done."
