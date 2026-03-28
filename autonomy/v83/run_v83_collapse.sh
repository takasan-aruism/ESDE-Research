#!/bin/bash
# ESDE v8.3 — Collapse Threshold Sweep
# T=100 fixed, A = 0.5 / 0.7 / 1.0
# 3 seeds (sanity first, mass test later if needed)
# A=0.3 already exists in diag_v83_wave_A0.3_T100
#
# GPT directive: 「動的崩壊がどのように起こるかを追う」
# Not "does it break" but "HOW does it break"

SEEDS="42 123 456"
WINDOWS=200
PERIOD=100
AMPS="0.5 0.7 1.0"

echo "============================================"
echo "  ESDE v8.3 — Collapse Threshold Sweep"
echo "  T=${PERIOD} fixed"
echo "  A = 0.5 / 0.7 / 1.0"
echo "  (A=0.3 = existing diag_v83_wave_A0.3_T100)"
echo "  Seeds: $SEEDS"
echo "  Windows: $WINDOWS"
echo "  Start: $(date)"
echo "============================================"

for AMP in $AMPS; do
    OUTDIR="diag_v83_wave_A${AMP}_T${PERIOD}"
    echo ""
    echo "  === A=${AMP} T=${PERIOD} ==="
    mkdir -p $OUTDIR
    parallel -j 3 --ungroup \
        env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
        python esde_v83_calibrate.py \
            --seed {1} --windows $WINDOWS \
            --wave-amp $AMP --wave-period $PERIOD \
            --output $OUTDIR \
        ::: $SEEDS
    echo "  A=${AMP} done: $(date)"
done

echo ""
echo "============================================"
echo "  Collapse sweep done: $(date)"
echo ""
echo "  Outputs:"
echo "    diag_v83_wave_A0.3_T100/  (existing)"
echo "    diag_v83_wave_A0.5_T100/"
echo "    diag_v83_wave_A0.7_T100/"
echo "    diag_v83_wave_A1.0_T100/"
echo ""
echo "  Analyze:"
echo "  python analyze_v83_collapse.py"
echo "============================================"
