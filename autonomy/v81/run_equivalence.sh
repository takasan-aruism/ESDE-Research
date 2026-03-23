#!/bin/bash
# ESDE v8.1c — Equivalence Test (Fidelity + Speed)
#
# Run A: Uncompressed baseline
# Run B: Compressed at w50
# Run C: Compressed at w100
# Same seed, same N, same steps. All parallel.
#
# GPT audit recommendation: compare w50 vs w100 compression timing.
# Compression target: virtual claim (frozenset), not physical structure.

SEED=123
WINDOWS=500
OUTPUT="equivalence_test"

echo "============================================"
echo "  ESDE v8.1c — Equivalence Test"
echo "  Seed=$SEED  Windows=$WINDOWS"
echo "  Run A: uncompressed"
echo "  Run B: compress at w50"
echo "  Run C: compress at w100"
echo "  Output: $OUTPUT/"
echo "  Start: $(date)"
echo "============================================"

mkdir -p $OUTPUT

echo ""
echo "  === Running A, B, C in parallel ==="
echo ""

python esde_v81_calibrate.py \
    --seed $SEED --windows $WINDOWS \
    --output $OUTPUT \
    2>&1 | tee $OUTPUT/run_a.log &
PID_A=$!

python esde_v81_calibrate.py \
    --seed $SEED --windows $WINDOWS \
    --compress --compress-at 50 --compress-min-age 10 \
    --output $OUTPUT \
    2>&1 | tee $OUTPUT/run_b.log &
PID_B=$!

python esde_v81_calibrate.py \
    --seed $SEED --windows $WINDOWS \
    --compress --compress-at 100 --compress-min-age 10 \
    --output $OUTPUT \
    2>&1 | tee $OUTPUT/run_c.log &
PID_C=$!

wait $PID_A $PID_B $PID_C

echo ""
echo "============================================"
echo "  All runs complete: $(date)"
echo "  Compare CSV and JSON in $OUTPUT/"
echo "============================================"
