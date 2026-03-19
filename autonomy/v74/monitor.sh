#!/bin/bash
# ESDE v7.4 — Live Monitor
# Run in a separate tmux pane while run_parallel.sh is running.
# USAGE: bash monitor.sh
#        bash monitor.sh calibration_v74   (custom output dir)

OUTPUT="${1:-calibration_v74}"

echo "  Monitoring $OUTPUT/ (Ctrl+C to stop)"
echo ""

while true; do
    clear
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  ESDE v7.4 — Live Status  $(date '+%H:%M:%S')                      ║"
    echo "╠══════════════════════════════════════════════════════════════╣"

    for f in $OUTPUT/*_status.txt; do
        if [ -f "$f" ]; then
            echo "║  $(cat $f)"
        fi
    done

    # Show completed seeds
    completed=$(ls $OUTPUT/v74_*_detail.json 2>/dev/null | wc -l)
    total=$(ls $OUTPUT/v74_*_status.txt 2>/dev/null | wc -l)
    running=$total
    echo "╠══════════════════════════════════════════════════════════════╣"
    echo "║  Completed: $completed  Running: $running                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"

    # Last lines from each CSV
    echo ""
    for f in $OUTPUT/v74_*.csv; do
        if [ -f "$f" ]; then
            seed=$(echo $f | grep -oP 'seed\K[0-9]+')
            last=$(tail -1 "$f" 2>/dev/null)
            if [ -n "$last" ]; then
                win=$(echo $last | cut -d',' -f1)
                links=$(echo $last | cut -d',' -f3)
                echo "  seed=$seed w=$win links=$links"
            fi
        fi
    done

    sleep 10
done
