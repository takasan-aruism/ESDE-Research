#!/bin/bash
# ESDE v9.0 — Self-Referential Feedback Loop
# Phase 1: died_share_sum → EMA → torque modulation
# A=0.3 local wave, JOBS=24

SEEDS=$(python3 -c "
import random; random.seed(0)
base = [42, 123, 456, 789, 2024, 7, 314, 999, 55, 1337, 8888, 31415]
extra = random.sample(range(10000, 99999), 36)
print(' '.join(str(s) for s in base + extra))
")

WINDOWS=200
JOBS=24
AMP=0.3
OUTDIR="diag_v90_feedback_A${AMP}"

echo "============================================"
echo "  ESDE v9.0 — Self-Referential Feedback Loop"
echo "  A=${AMP} mode=x_coordinate"
echo "  gamma=0.1  clamp=[0.8, 1.2]  warmup=20"
echo "  Seeds: 48  Jobs: $JOBS"
echo "  Windows: $WINDOWS"
echo "  Start: $(date)"
echo "============================================"

mkdir -p $OUTDIR
parallel -j $JOBS --ungroup \
    env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    python esde_v90_calibrate.py \
        --seed {1} --windows $WINDOWS \
        --local-amp $AMP \
        --output $OUTDIR \
    ::: $SEEDS

echo ""
echo "============================================"
echo "  Done: $(date)"
echo "  Output: $OUTDIR/"
echo "============================================"
