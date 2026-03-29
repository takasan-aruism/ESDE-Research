#!/bin/bash
# ESDE v8.4 — Local Wave 48-Seed Mass Test
# A=0.3, 200 windows, JOBS=24

SEEDS=$(python3 -c "
import random; random.seed(0)
base = [42, 123, 456, 789, 2024, 7, 314, 999, 55, 1337, 8888, 31415]
extra = random.sample(range(10000, 99999), 36)
print(' '.join(str(s) for s in base + extra))
")

WINDOWS=200
JOBS=24
AMP=0.3
OUTDIR="diag_v84_local_A${AMP}"

echo "============================================"
echo "  ESDE v8.4 — Local Wave Mass Test"
echo "  A=${AMP} mode=x_coordinate"
echo "  Seeds: 48  Jobs: $JOBS"
echo "  Windows: $WINDOWS"
echo "  Start: $(date)"
echo "============================================"

mkdir -p $OUTDIR
parallel -j $JOBS --ungroup \
    env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    python esde_v84_calibrate.py \
        --seed {1} --windows $WINDOWS \
        --local-amp $AMP \
        --output $OUTDIR \
    ::: $SEEDS

echo ""
echo "============================================"
echo "  Done: $(date)"
echo "  Output: $OUTDIR/"
echo "============================================"
