#!/usr/bin/env python3
import sys
import json
import re
from collections import defaultdict
import statistics

def parse_line(line):
    """Parse a line into key-value pairs, returning a dictionary."""
    result = {}
    # Match key=value pairs where key is [A-Za-z_][A-Za-z0-9_]* and value is non-whitespace
    for match in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)=([^\s]+)', line):
        key = match.group(1)
        value = match.group(2)
        result[key] = value
    return result

def safe_float(value, default=0.0):
    """Safely convert a value to float, returning default if not possible."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def main():
    # Read input
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            lines = f.readlines()
    else:
        lines = sys.stdin.readlines()
    
    # Initialize counters
    total_lines = 0
    level_counts = defaultdict(int)
    latency_values = []
    route_counts = defaultdict(int)
    
    # Process lines
    for line in lines:
        line = line.strip()
        if not line:
            continue
        total_lines += 1
        parsed = parse_line(line)
        # Update level count
        level = parsed.get('level')
        if level:
            level_counts[level] += 1
        # Update latency
        latency_str = parsed.get('latency_ms')
        if latency_str is not None:
            latency = safe_float(latency_str)
            if latency != 0.0 or latency_str == "0":
                latency_values.append(latency)
        # Update route count
        route = parsed.get('route')
        if route:
            route_counts[route] += 1
    
    # Calculate statistics
    levels = dict(level_counts)
    avg_latency = sum(latency_values) / len(latency_values) if latency_values else 0
    p95_latency = 0
    if latency_values:
        latency_values.sort()
        if len(latency_values) > 1:
            # Calculate 95th percentile
            index = int(0.95 * (len(latency_values) - 1))
            p95_latency = latency_values[index]
        else:
            p95_latency = latency_values[0]
    # Top 3 routes
    top_routes = [route for route, count in sorted(route_counts.items(), key=lambda x: -x[1])[:3]]
    
    # Prepare output
    result = {
        "total_lines": total_lines,
        "levels": levels,
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": p95_latency,
        "top_routes": top_routes
    }
    
    # Print as compact JSON
    print(json.dumps(result))

if __name__ == "__main__":
    main()
