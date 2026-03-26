#!/bin/bash
# ESDE v8.2 — α Sensitivity Test
# GPT audit recommendation: α=0.05 で trio が残るか消えるかを判定
#
# Case A: trio が大きく減る → Past 強度に依存した副産物
# Case B: trio がかなり残る → 構造的パターン
#
# Baseline only (compressed 不要 — GPT指示)

SEEDS=$(python3 -c "
import random; random.seed(0)
base = [42, 123, 456, 789, 2024, 7, 314, 999, 55, 1337, 8888, 31415]
extra = random.sample(range(10000, 99999), 36)
print(' '.join(str(s) for s in base + extra))
")

WINDOWS=200
JOBS=24
ALPHA=0.05
BETA=0.10

echo "============================================"
echo "  ESDE v8.2 — α Sensitivity Test"
echo "  α=${ALPHA} (baseline: 0.10)"
echo "  β=${BETA}  (unchanged)"
echo "  N=5000  steps=50  windows=$WINDOWS"
echo "  Seeds: 48  Jobs: $JOBS"
echo "  Start: $(date)"
echo "============================================"

OUTPUT="diag_v82_alpha${ALPHA}"
mkdir -p $OUTPUT

parallel -j $JOBS --ungroup \
    env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    python esde_v82_calibrate.py \
        --seed {1} --windows $WINDOWS \
        --maturation-alpha $ALPHA \
        --rigidity-beta $BETA \
        --output $OUTPUT \
    ::: $SEEDS

echo ""
echo "============================================"
echo "  Done: $(date)"
echo "  Output: $OUTPUT/"
echo ""
echo "  Compare with baseline:"
echo "  python analyze_trio_audit.py --dir $OUTPUT"
echo "  python analyze_trio_genesis.py --dir $OUTPUT"
echo ""
echo "  Then compare trio counts:"
echo "    baseline (α=0.10): diag_v82_baseline"
echo "    test     (α=0.05): $OUTPUT"
echo "============================================"
