#!/bin/bash
# ESDE v8.3 — External Wave Sanity Test
# 3 seeds × 3 periods + baseline (no wave)
# A=0.3 (±30% bg_prob modulation)
# 200 windows each
#
# Purpose: confirm wave modulation works,
#          check system doesn't crash or diverge,
#          eyeball label ecology response

SEEDS="42 123 456"
WINDOWS=200
AMP=0.3
PERIODS="10 50 100"

echo "============================================"
echo "  ESDE v8.3 — External Wave Sanity Test"
echo "  Seeds: $SEEDS"
echo "  Amplitude: $AMP"
echo "  Periods: $PERIODS"
echo "  Windows: $WINDOWS"
echo "  Start: $(date)"
echo "============================================"

# Baseline (no wave) for comparison
echo ""
echo "  === Baseline (no wave) ==="
mkdir -p sanity_wave_baseline
for SEED in $SEEDS; do
    echo "  seed=$SEED ..."
    python esde_v83_calibrate.py \
        --seed $SEED --windows $WINDOWS \
        --output sanity_wave_baseline \
        2>&1 | tail -3
done

# Wave runs
for T in $PERIODS; do
    echo ""
    echo "  === Wave A=${AMP} T=${T} ==="
    OUTDIR="sanity_wave_A${AMP}_T${T}"
    mkdir -p $OUTDIR
    for SEED in $SEEDS; do
        echo "  seed=$SEED T=$T ..."
        python esde_v83_calibrate.py \
            --seed $SEED --windows $WINDOWS \
            --wave-amp $AMP --wave-period $T \
            --output $OUTDIR \
            2>&1 | tail -3
    done
done

echo ""
echo "============================================"
echo "  v8.3 Sanity test done: $(date)"
echo ""
echo "  Check:"
echo "  1. All runs completed without crash"
echo "  2. CSV has bg_prob_effective column"
echo "  3. bg_prob_effective oscillates correctly:"
echo "     head -5 sanity_wave_A0.3_T50/*seed42*.csv"
echo ""
echo "  Quick comparison (last window):"
echo "  for d in sanity_wave_baseline sanity_wave_A0.3_T*; do"
echo "    echo \$d; tail -1 \$d/*seed42*.csv | cut -d, -f1,3,17,18; echo"
echo "  done"
echo "============================================"
