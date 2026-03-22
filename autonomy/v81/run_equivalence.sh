#!/bin/bash
# ESDE v8.1 — Equivalence Test (Fidelity + Speed)
#
# Run A: Uncompressed baseline, 500 windows
# Run B: Compressed at w50, 500 windows
# Same seed (123), same N, same steps.
#
# PRIMARY: Behavioral fidelity (links, R+, label survival)
# SECONDARY: Speed (sec/win comparison pre/post compression)
# NOTE: Speed improvement at N=5000 is modest (~2-5%).
#       The main purpose is validating compression correctness.

SEED=123
WINDOWS=500
OUTPUT="equivalence_test"

echo "============================================"
echo "  ESDE v8.1 — Equivalence Test"
echo "  Seed=$SEED  Windows=$WINDOWS"
echo "  Output: $OUTPUT/"
echo "  Start: $(date)"
echo "============================================"

mkdir -p $OUTPUT

echo ""
echo "  === RUN A: Uncompressed Baseline ==="
echo ""
time python esde_v81_calibrate.py \
    --seed $SEED --windows $WINDOWS \
    --output $OUTPUT \
    2>&1 | tee $OUTPUT/run_a.log

echo ""
echo "  === RUN B: Compressed (macro-node at w50) ==="
echo ""
time python esde_v81_calibrate.py \
    --seed $SEED --windows $WINDOWS \
    --compress --compress-at 50 --compress-min-age 10 \
    --output $OUTPUT \
    2>&1 | tee $OUTPUT/run_b.log

echo ""
echo "============================================"
echo "  Both runs complete: $(date)"
echo "  Compare CSV and JSON in $OUTPUT/"
echo "============================================"
