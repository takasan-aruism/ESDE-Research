#!/bin/bash
# ESDE v7.4 — Multi-seed parallel runner
# USAGE: bash run_parallel.sh
#
# Runs 6 seeds in parallel on Ryzen.
# Monitor: bash monitor.sh (in another terminal)

SEEDS="42 123 456 789 2024 7"
WINDOWS=200
N=10000
OUTPUT="calibration_v74"
JOBS=6

echo "============================================"
echo "  ESDE v7.4 — Large-Scale Autonomy"
echo "  N=$N  windows=$WINDOWS  seeds: $SEEDS"
echo "  Parallel jobs: $JOBS"
echo "  Output: $OUTPUT/"
echo "  Start: $(date)"
echo "============================================"

mkdir -p $OUTPUT

parallel -j $JOBS --ungroup \
    python esde_v74_calibrate.py \
        --seed {1} --windows $WINDOWS --N $N \
        --output $OUTPUT \
    ::: $SEEDS

echo ""
echo "  All seeds complete: $(date)"
echo "  Results in: $OUTPUT/"
ls -la $OUTPUT/*.csv
