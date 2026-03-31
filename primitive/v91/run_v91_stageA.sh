#!/bin/bash
# ESDE v9.1 Stage A — Gamma Regime Sweep
# clamp=[0.8, 1.2] 固定。gamma を正負に振る。
# 8 conditions × 3 seeds = 24 runs, JOBS=24
# A=0.3 local wave

SEEDS="42 123 456"
WINDOWS=200
JOBS=24
AMP=0.3
CLAMP_LO=0.8
CLAMP_HI=1.2

# GPT修正: 0.3/-0.3 追加、2.0 は後回し
GAMMAS="0.0 0.1 0.3 0.5 1.0 -0.3 -0.5 -1.0"

echo "============================================"
echo "  ESDE v9.1 Stage A — Gamma Regime Sweep"
echo "  Gammas: $GAMMAS"
echo "  Clamp: [$CLAMP_LO, $CLAMP_HI] (fixed)"
echo "  Seeds: $SEEDS"
echo "  A=${AMP}  Windows: $WINDOWS"
echo "  Start: $(date)"
echo "============================================"

# Build all (gamma, seed) pairs
PAIRS=""
for G in $GAMMAS; do
    for S in $SEEDS; do
        PAIRS="$PAIRS $G:$S"
    done
done

# Run in parallel
echo "$PAIRS" | tr ' ' '\n' | parallel -j $JOBS --ungroup \
    'G={= s/:.*//; =}; S={= s/.*://; =}; \
     OUTDIR="diag_v91_stageA_g${G}"; \
     mkdir -p $OUTDIR; \
     env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
     python esde_v90_calibrate.py \
         --seed $S --windows '"$WINDOWS"' \
         --local-amp '"$AMP"' \
         --gamma $G \
         --clamp-lo '"$CLAMP_LO"' --clamp-hi '"$CLAMP_HI"' \
         --output $OUTDIR'

echo ""
echo "============================================"
echo "  Stage A done: $(date)"
echo "  Outputs: diag_v91_stageA_g*/"
echo ""
echo "  Sanity pass conditions:"
echo "    1. alive_links not collapsed"
echo "    2. labels_active not zero"
echo "    3. M not pure clamp lock"
echo "    4. survival by size shows directional diff"
echo "============================================"
