# ESDE Genesis v1.9g — Canonical Freeze + Scale Transfer

## Observer Freeze Note
Policy: hyst_0.01
Hysteresis threshold: 0.01
Stability metric: switches_per_100_windows (canonical)
Label function: ctx_label(ctx, k) for k=0..4 (frozen)
k=3 bins: None / WeakOnly / Mid / Strong
k=4 adds: Intrusion exposure (0 / 1+)

## Results
Runs: 240 total (12 at N=200, 12 at N=500)

## N=200 vs N=500 Comparison
| N | Rate | k* | Agree | sw/100 | None ratio | Islands(mid) |
|---|------|----|----|--------|---------|---------|
| 200 | 0.0005 | k=4 | 80.0% | 2.5 | 0.880 | 1.4 |
| 200 | 0.001 | k=4 | 100.0% | 2.5 | 0.872 | 1.6 |
| 200 | 0.002 | k=4 | 100.0% | 3.0 | 0.877 | 1.5 |
| 200 | 0.005 | k=4 | 100.0% | 2.0 | 0.877 | 1.5 |
| 200 | 0.0005 | k=4 | 70.0% | 4.0 | 0.832 | 2.3 |
| 200 | 0.001 | k=4 | 100.0% | 2.5 | 0.837 | 2.3 |
| 200 | 0.002 | k=4 | 100.0% | 3.5 | 0.837 | 2.2 |
| 200 | 0.005 | k=4 | 100.0% | 2.0 | 0.845 | 2.0 |
| 200 | 0.0005 | k=4 | 100.0% | 2.0 | 0.781 | 3.7 |
| 200 | 0.001 | k=4 | 90.0% | 2.0 | 0.790 | 3.6 |
| 200 | 0.002 | k=4 | 100.0% | 1.5 | 0.786 | 4.0 |
| 200 | 0.005 | k=4 | 100.0% | 0.0 | 0.779 | 3.8 |
| 500 | 0.0005 | k=3 | 70.0% | 4.5 | 0.918 | 0.9 |
| 500 | 0.001 | k=4 | 70.0% | 5.0 | 0.919 | 0.8 |
| 500 | 0.002 | k=4 | 100.0% | 5.5 | 0.916 | 0.9 |
| 500 | 0.005 | k=4 | 100.0% | 3.0 | 0.922 | 0.9 |
| 500 | 0.0005 | k=4 | 60.0% | 8.0 | 0.899 | 1.8 |
| 500 | 0.001 | k=4 | 90.0% | 6.5 | 0.895 | 1.8 |
| 500 | 0.002 | k=4 | 100.0% | 7.5 | 0.901 | 1.8 |
| 500 | 0.005 | k=4 | 100.0% | 5.0 | 0.902 | 1.8 |
| 500 | 0.0005 | k=4 | 90.0% | 7.0 | 0.856 | 4.0 |
| 500 | 0.001 | k=4 | 100.0% | 8.0 | 0.860 | 3.8 |
| 500 | 0.002 | k=4 | 100.0% | 6.5 | 0.858 | 4.2 |
| 500 | 0.005 | k=4 | 100.0% | 1.5 | 0.852 | 4.2 |

## Interpretation
Branch 2: k=3 re-emerges at N=500

## Audit Checklist
[AC-1] hyst_0.01 frozen as canonical: YES (OBSERVER_POLICY constant)
[AC-2] k-switch logged: YES (SwitchEvent dataclass, per-run JSON)
[AC-3] Stability metric canonical: YES (switches_per_100_windows)
[AC-4] N=500 without theory patches: YES
[AC-5] Comparable outputs: YES (identical schema)
[AC-6] No ontology expansion: YES
