#!/bin/bash
# Monitor v8.0 mass run
OUTPUT="calibration_v80_mass"
while true; do
    clear
    echo "=== ESDE v8.0 Mass Run Monitor === $(date)"
    echo ""
    
    # Count completed (detail.json exists)
    DONE=$(ls $OUTPUT/*_detail.json 2>/dev/null | wc -l)
    TOTAL=48
    
    # Count running (status.txt exists)
    RUNNING=$(ls $OUTPUT/*_status.txt 2>/dev/null | wc -l)
    
    echo "  Completed: $DONE / $TOTAL"
    echo "  Running:   $RUNNING"
    echo ""
    
    # Show last line of each status file
    for f in $OUTPUT/*_status.txt; do
        [ -f "$f" ] && cat "$f"
    done 2>/dev/null | sort | tail -10
    
    echo ""
    echo "  CSV files: $(ls $OUTPUT/*.csv 2>/dev/null | wc -l)"
    echo "  JSON files: $(ls $OUTPUT/*_detail.json 2>/dev/null | wc -l)"
    
    sleep 15
done
