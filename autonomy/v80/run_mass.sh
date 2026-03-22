#!/bin/bash
# ESDE v8.0 — Mass Lifecycle Test
# 48 seeds, 48 parallel, N=5000, 50 steps, 200 windows
# ~2 hours wall time

SEEDS=$(python3 -c "
import random; random.seed(0)
base = [42, 123, 456, 789, 2024, 7, 314, 999, 55, 1337, 8888, 31415]
extra = random.sample(range(10000, 99999), 36)
print(' '.join(str(s) for s in base + extra))
")

WINDOWS=200
OUTPUT="calibration_v80_mass"
JOBS=48

echo "============================================"
echo "  ESDE v8.0 — Mass Lifecycle Test"
echo "  N=5000  steps=50  windows=$WINDOWS"
echo "  Seeds: 48"
echo "  Parallel jobs: $JOBS"
echo "  Output: $OUTPUT/"
echo "  Start: $(date)"
echo "============================================"

mkdir -p $OUTPUT

parallel -j $JOBS --ungroup \
    python esde_v80_calibrate.py \
        --seed {1} --windows $WINDOWS \
        --output $OUTPUT \
    ::: $SEEDS

echo "============================================"
echo "  Finished: $(date)"
echo "============================================"
