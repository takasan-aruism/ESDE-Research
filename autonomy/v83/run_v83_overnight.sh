#!/bin/bash
# ESDE v8.3 — Overnight Run
# 1. A=0.5 T=100 48-seed mass test (~1.5h)
# 2. 500-win baseline 48-seed (~3.5h)
# Total: ~5 hours

SEEDS=$(python3 -c "
import random; random.seed(0)
base = [42, 123, 456, 789, 2024, 7, 314, 999, 55, 1337, 8888, 31415]
extra = random.sample(range(10000, 99999), 36)
print(' '.join(str(s) for s in base + extra))
")

JOBS=24

echo "============================================"
echo "  ESDE v8.3 — Overnight Run"
echo "  Part 1: A=0.5 T=100 48-seed (200 win)"
echo "  Part 2: Baseline 48-seed (500 win)"
echo "  Start: $(date)"
echo "============================================"

# ── Part 1: A=0.5 T=100 mass test ──
echo ""
echo "  === Part 1: A=0.5 T=100 (200 win) ==="
OUTDIR1="diag_v83_wave_A0.5_T100"
mkdir -p $OUTDIR1
parallel -j $JOBS --ungroup \
    env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    python esde_v83_calibrate.py \
        --seed {1} --windows 200 \
        --wave-amp 0.5 --wave-period 100 \
        --output $OUTDIR1 \
    ::: $SEEDS
echo "  Part 1 done: $(date)"

# ── Part 2: 500-win baseline ──
echo ""
echo "  === Part 2: Baseline (500 win, no wave) ==="
OUTDIR2="diag_v83_baseline_500win"
mkdir -p $OUTDIR2
parallel -j $JOBS --ungroup \
    env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    python esde_v83_calibrate.py \
        --seed {1} --windows 500 \
        --output $OUTDIR2 \
    ::: $SEEDS
echo "  Part 2 done: $(date)"

echo ""
echo "============================================"
echo "  All done: $(date)"
echo ""
echo "  Outputs:"
echo "    $OUTDIR1/  (A=0.5 T=100, 200 win)"
echo "    $OUTDIR2/  (baseline, 500 win)"
echo ""
echo "  Analyze:"
echo "    python analyze_v83_collapse.py"
echo "    python analyze_v83_wave.py --baseline $OUTDIR2"
echo "============================================"
