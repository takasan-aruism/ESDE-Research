#!/bin/bash
# ESDE v8.4 — Local Wave Amplitude Sanity Sweep
# GPT Audit Condition A: safety confirmation before production
#
# A = 0.1 / 0.2 / 0.3 × 3 seeds
# + baseline (no local wave) × 3 seeds
# T=N/A (static gradient, no temporal wave)
# 200 windows

SEEDS="42 123 456"
WINDOWS=200
AMPS="0.1 0.2 0.3"

echo "============================================"
echo "  ESDE v8.4 — Local Wave Sanity Sweep"
echo "  Amplitudes: $AMPS"
echo "  Seeds: $SEEDS"
echo "  Windows: $WINDOWS"
echo "  Mode: x_coordinate (grid side=71)"
echo "  Start: $(date)"
echo "============================================"

# Baseline (no local wave)
echo ""
echo "  === Baseline (no local wave) ==="
OUTDIR="sanity_v84_baseline"
mkdir -p $OUTDIR
for SEED in $SEEDS; do
    echo "  seed=$SEED ..."
    python esde_v84_calibrate.py \
        --seed $SEED --windows $WINDOWS \
        --output $OUTDIR \
        2>&1 | tail -3
done

# Local wave runs
for AMP in $AMPS; do
    echo ""
    echo "  === Local Wave A=${AMP} ==="
    OUTDIR="sanity_v84_local_A${AMP}"
    mkdir -p $OUTDIR
    for SEED in $SEEDS; do
        echo "  seed=$SEED A=$AMP ..."
        python esde_v84_calibrate.py \
            --seed $SEED --windows $WINDOWS \
            --local-amp $AMP \
            --output $OUTDIR \
            2>&1 | tail -3
    done
done

echo ""
echo "============================================"
echo "  v8.4 Sanity sweep done: $(date)"
echo ""
echo "  Outputs:"
echo "    sanity_v84_baseline/"
echo "    sanity_v84_local_A0.1/"
echo "    sanity_v84_local_A0.2/"
echo "    sanity_v84_local_A0.3/"
echo ""
echo "  Quick check (seed=42, last window):"
echo "  for d in sanity_v84_*; do"
echo "    echo \$d; tail -1 \$d/*seed42*.csv | cut -d, -f1,3,17,38,39,40"
echo "  done"
echo "============================================"
