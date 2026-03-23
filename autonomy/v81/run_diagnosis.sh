#!/bin/bash
# ESDE v8.1c — 48-seed Compression Diagnosis
# Batch 1: 48 seeds uncompressed (baseline)
# Batch 2: 48 seeds compressed at w50
# ~2h per batch, 4h total

SEEDS=$(python3 -c "
import random; random.seed(0)
base = [42, 123, 456, 789, 2024, 7, 314, 999, 55, 1337, 8888, 31415]
extra = random.sample(range(10000, 99999), 36)
print(' '.join(str(s) for s in base + extra))
")

WINDOWS=200
JOBS=48

echo "============================================"
echo "  ESDE v8.1c — 48-Seed Compression Diagnosis"
echo "  N=5000  steps=50  windows=$WINDOWS"
echo "  Seeds: 48  Jobs: $JOBS"
echo "  Start: $(date)"
echo "============================================"

echo ""
echo "  === BATCH 1: Uncompressed Baseline ==="
echo ""
mkdir -p diag_baseline
parallel -j $JOBS --ungroup \
    python esde_v81_calibrate.py \
        --seed {1} --windows $WINDOWS \
        --output diag_baseline \
    ::: $SEEDS

echo ""
echo "  Batch 1 done: $(date)"
echo ""
echo "  === BATCH 2: Compressed at w50 ==="
echo ""
mkdir -p diag_compressed
parallel -j $JOBS --ungroup \
    python esde_v81_calibrate.py \
        --seed {1} --windows $WINDOWS \
        --compress --compress-at 50 --compress-min-age 10 \
        --output diag_compressed \
    ::: $SEEDS

echo ""
echo "============================================"
echo "  Both batches done: $(date)"
echo "============================================"
