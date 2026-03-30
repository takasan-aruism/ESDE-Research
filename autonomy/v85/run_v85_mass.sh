#!/bin/bash
# ESDE v8.5 — Label Tracking + Thaw Pressure 48-Seed Mass Test
# A=0.3, 200 windows, JOBS=24
# Includes: C-light, D-light, Stage 1 thaw logging

SEEDS=$(python3 -c "
import random; random.seed(0)
base = [42, 123, 456, 789, 2024, 7, 314, 999, 55, 1337, 8888, 31415]
extra = random.sample(range(10000, 99999), 36)
print(' '.join(str(s) for s in base + extra))
")

WINDOWS=200
JOBS=24
AMP=0.3
OUTDIR="diag_v85_tracking_A${AMP}"

echo "============================================"
echo "  ESDE v8.5 — Label Tracking + Thaw Pressure"
echo "  A=${AMP} mode=x_coordinate"
echo "  Seeds: 48  Jobs: $JOBS"
echo "  Windows: $WINDOWS"
echo "  Instrumentation: C-light + D-light + Stage 1 thaw"
echo "  Start: $(date)"
echo "============================================"

mkdir -p $OUTDIR
parallel -j $JOBS --ungroup \
    env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    python esde_v85_calibrate.py \
        --seed {1} --windows $WINDOWS \
        --local-amp $AMP \
        --output $OUTDIR \
    ::: $SEEDS

echo ""
echo "============================================"
echo "  Done: $(date)"
echo "  Output: $OUTDIR/"
echo "============================================"
