#!/bin/bash
# ESDE v8.3 — External Wave 48-Seed Mass Test
# A=0.3 × T=10/50/100
# Baseline = diag_v82_baseline (既存、再実行不要)

SEEDS=$(python3 -c "
import random; random.seed(0)
base = [42, 123, 456, 789, 2024, 7, 314, 999, 55, 1337, 8888, 31415]
extra = random.sample(range(10000, 99999), 36)
print(' '.join(str(s) for s in base + extra))
")

WINDOWS=200
JOBS=24
AMP=0.3

echo "============================================"
echo "  ESDE v8.3 — External Wave Mass Test"
echo "  A=${AMP}  T=10,50,100"
echo "  Seeds: 48  Jobs: $JOBS"
echo "  Windows: $WINDOWS"
echo "  Baseline: ../v82/diag_v82_baseline (既存)"
echo "  Start: $(date)"
echo "============================================"

for T in 10 50 100; do
    OUTDIR="diag_v83_wave_A${AMP}_T${T}"
    echo ""
    echo "  === Wave A=${AMP} T=${T} ==="
    mkdir -p $OUTDIR
    parallel -j $JOBS --ungroup \
        env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
        python esde_v83_calibrate.py \
            --seed {1} --windows $WINDOWS \
            --wave-amp $AMP --wave-period $T \
            --output $OUTDIR \
        ::: $SEEDS
    echo "  T=${T} done: $(date)"
done

echo ""
echo "============================================"
echo "  All done: $(date)"
echo ""
echo "  Outputs:"
echo "    diag_v83_wave_A0.3_T10/"
echo "    diag_v83_wave_A0.3_T50/"
echo "    diag_v83_wave_A0.3_T100/"
echo "  Baseline:"
echo "    ../v82/diag_v82_baseline/"
echo "============================================"
