#!/bin/bash
# Quick sanity: 3 seeds, baseline vs compressed
# ~30 min total. Check if label count matches.

SEEDS="42 123 789"
WINDOWS=200
OUTPUT_B="sanity_baseline"
OUTPUT_C="sanity_compressed"

mkdir -p $OUTPUT_B $OUTPUT_C

echo "=== Baseline (3 seeds) ==="
parallel -j 3 python esde_v81_calibrate.py \
    --seed {1} --windows $WINDOWS --output $OUTPUT_B ::: $SEEDS

echo "=== Compressed (3 seeds) ==="
parallel -j 3 python esde_v81_calibrate.py \
    --seed {1} --windows $WINDOWS --compress --compress-at 50 \
    --output $OUTPUT_C ::: $SEEDS

echo "=== Quick comparison ==="
python3 -c "
import csv, glob, numpy as np
for label, d in [('Baseline', '$OUTPUT_B'), ('Compressed', '$OUTPUT_C')]:
    labels = []
    links = []
    for f in sorted(glob.glob(f'{d}/*.csv')):
        rows = list(csv.DictReader(open(f)))
        sl = rows[100:200]
        labels.append(np.mean([float(r['v_labels']) for r in sl]))
        links.append(np.mean([float(r['alive_links']) for r in sl]))
    print(f'{label}: labels={np.mean(labels):.1f} links={np.mean(links):.0f}')
"
echo "=== Done ==="
