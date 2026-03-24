#!/bin/bash
# ESDE v8.2 — 48-Seed Diagnosis
# v8.1d verification + Phase A observation in one run
# Batch 1: baseline (no compression)
# Batch 2: compressed (v8.1d, w50)
# Both output O/H/V phase space data

SEEDS=$(python3 -c "
import random; random.seed(0)
base = [42, 123, 456, 789, 2024, 7, 314, 999, 55, 1337, 8888, 31415]
extra = random.sample(range(10000, 99999), 36)
print(' '.join(str(s) for s in base + extra))
")

WINDOWS=200
JOBS=48

echo "============================================"
echo "  ESDE v8.2 — 48-Seed Diagnosis"
echo "  v8.1d verification + Phase A observation"
echo "  N=5000  steps=50  windows=$WINDOWS"
echo "  Seeds: 48  Jobs: $JOBS"
echo "  Start: $(date)"
echo "============================================"

echo ""
echo "  === BATCH 1: Baseline ==="
echo ""
mkdir -p diag_v82_baseline
parallel -j $JOBS --ungroup \
    python esde_v82_calibrate.py \
        --seed {1} --windows $WINDOWS \
        --output diag_v82_baseline \
    ::: $SEEDS

echo ""
echo "  Batch 1 done: $(date)"
echo ""
echo "  === BATCH 2: Compressed (v8.1d, w50) ==="
echo ""
mkdir -p diag_v82_compressed
parallel -j $JOBS --ungroup \
    python esde_v82_calibrate.py \
        --seed {1} --windows $WINDOWS \
        --compress --compress-at 50 --compress-min-age 10 \
        --output diag_v82_compressed \
    ::: $SEEDS

echo ""
echo "============================================"
echo "  Both batches done: $(date)"
echo "  Analyze with:"
echo "  python analyze_v82.py --baseline diag_v82_baseline --compressed diag_v82_compressed"
echo "============================================"
