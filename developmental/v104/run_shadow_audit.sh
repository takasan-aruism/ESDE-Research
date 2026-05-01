#!/bin/bash
# v10.4 shadow audit launcher: 24 seeds × 50 windows in parallel
# Writes to diag_v104_shadow/ and per-seed logs to run_logs_shadow/
set -e

cd "$(dirname "$0")"
mkdir -p run_logs_shadow

SEEDS_START=${1:-0}
SEEDS_END=${2:-23}
PARALLEL_JOBS=${3:-8}

echo "v10.4 shadow audit: seeds [$SEEDS_START..$SEEDS_END], -j$PARALLEL_JOBS"
seq "$SEEDS_START" "$SEEDS_END" | parallel -j"$PARALLEL_JOBS" \
    "python3 v104_shadow_audit.py --seed {} --tag shadow > run_logs_shadow/seed{}.log 2>&1; \
     echo \"seed={} exit=\$?\""
echo "v10.4 shadow audit done."
