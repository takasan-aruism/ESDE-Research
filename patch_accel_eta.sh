#!/bin/bash
# ================================================================
# ESDE Ecology — region_observer.py patch
# Adds: (1) engine_accel import + guard, (2) ETA display
# 
# Usage:
#   cd ~/esde/ESDE-Research/ecology/region_observer
#   bash patch_accel_eta.sh
#   # verify:
#   python region_observer.py --sanity
# ================================================================
set -euo pipefail

FILE="region_observer.py"

if [ ! -f "$FILE" ]; then
    echo "ERROR: $FILE not found. Run from ecology/region_observer/"
    exit 1
fi

# Backup
cp "$FILE" "${FILE}.bak.$(date +%s)"
echo "  Backup created."

# ================================================================
# PATCH 1: engine_accel import + assert guard
# Insert after sys.path.insert line
# ================================================================
# Check if already patched
if grep -q "import engine_accel" "$FILE"; then
    echo "  SKIP: engine_accel import already present."
else
    sed -i '/^sys\.path\.insert(0, str(_P/a \
\
# engine_accel: monkey-patch hot paths (MUST be before any engine use)\
import engine_accel\
from genesis_state import GenesisState as _GS\
assert getattr(_GS.link_strength_sum, "__name__", "") == "_fast_link_strength_sum", \\\
    "FATAL: engine_accel failed to patch link_strength_sum. Run will be 2-3x slower."\
del _GS' "$FILE"
    echo "  DONE: engine_accel import + guard added."
fi

# ================================================================
# PATCH 2: ETA display in quiet phase loop
# Add time tracking + progress print at each window boundary
# ================================================================
if grep -q "_eta_last_window" "$FILE"; then
    echo "  SKIP: ETA display already present."
else
    # 2a. Add ETA timer init before the quiet loop (after "region_k_seqs = ...")
    sed -i '/region_k_seqs = {r: \[\] for r in range(N_REGIONS)}/a \
\
    # ETA tracking\
    _eta_t0 = time.time()\
    _eta_last_window = 0\
    _eta_total_windows = quiet_steps // WINDOW' "$FILE"

    # 2b. Add ETA print inside the window observation block
    #     Insert right after "win_idx = (step + 1) // WINDOW"
    sed -i '/win_idx = (step + 1) \/\/ WINDOW$/a \
\
            # ETA display\
            _eta_elapsed = time.time() - _eta_t0\
            _eta_last_window = win_idx\
            if _eta_last_window > 0:\
                _eta_per_win = _eta_elapsed / _eta_last_window\
                _eta_remaining = _eta_per_win * (_eta_total_windows - _eta_last_window)\
                _eta_total_est = _eta_per_win * _eta_total_windows\
                if win_idx % 5 == 0 or win_idx == _eta_total_windows:\
                    print(f"    window {win_idx}/{_eta_total_windows}  "\
                          f"elapsed={_eta_elapsed:.0f}s  "\
                          f"ETA={_eta_remaining:.0f}s  "\
                          f"total~{_eta_total_est:.0f}s", flush=True)' "$FILE"

    echo "  DONE: ETA display added (prints every 5 windows + final)."
fi

# ================================================================
# VERIFY
# ================================================================
echo ""
echo "  Verification:"
grep -n "engine_accel" "$FILE" | head -5
echo "  ---"
grep -n "_eta_" "$FILE" | head -5
echo ""
echo "  Patch complete. Run: python region_observer.py --sanity"
