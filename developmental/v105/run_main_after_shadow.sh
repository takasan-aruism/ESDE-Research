#!/bin/bash
# Wait for shadow audit to finish, then immediately start main run.
set -e
cd "$(dirname "$0")"

echo "[chain] waiting for shadow audit to complete..."
# Wait until master log shows "shadow done."
while ! grep -q "v10.5 shadow done" run_shadow_master.log 2>/dev/null; do
    sleep 60
done
echo "[chain] shadow audit completed at $(date '+%F %T')"

# Quick sanity check: 24 exit=0 lines?
n_done=$(grep -c "^seed=.* exit=0" run_shadow_master.log || echo 0)
echo "[chain] shadow seeds with exit=0: $n_done / 24"

echo "[chain] starting main run at $(date '+%F %T')"
mkdir -p run_logs_main
seq 0 23 | parallel -j8 \
    "python3 v105_memory_readout.py --seed {} \
        --maturation-windows 20 --tracking-windows 50 \
        --window-steps 500 --tag main > run_logs_main/seed{}.log 2>&1; \
     echo \"seed={} exit=\$?\""
echo "[chain] v10.5 main done at $(date '+%F %T')."
