# ESDE Genesis v1.9g — N=1000 Scale Validation

## Observer Policy
Policy            : hyst_0.01
Hysteresis (k3↔4) : 0.01
Stability metric  : switches_per_100_windows (canonical)
Label function    : ctx_label (frozen, k=0..4)
No ontology expansion.

## Experimental Grid (N=1000)
plb   : [0.007]
rates : [0.001, 0.002]
seeds : [42, 123, 456, 789, 2024, 7, 314, 999, 55, 1337]
runs  : 2 configs aggregated

## Results Table
| N | plb | rate | k* | Agree | sw/100 | None ratio | Islands(mid) |
|---|-----|------|----|-------|--------|------------|--------------|
| 200 | 0.007 | 0.0005 | k=4 | 80% | 2.5 | 0.880 | 1.4 |
| 200 | 0.007 | 0.0010 | k=4 | 100% | 2.5 | 0.872 | 1.6 |
| 200 | 0.007 | 0.0020 | k=4 | 100% | 3.0 | 0.877 | 1.5 |
| 200 | 0.007 | 0.0050 | k=4 | 100% | 2.0 | 0.877 | 1.5 |
| 200 | 0.008 | 0.0005 | k=4 | 70% | 4.0 | 0.832 | 2.3 |
| 200 | 0.008 | 0.0010 | k=4 | 100% | 2.5 | 0.837 | 2.3 |
| 200 | 0.008 | 0.0020 | k=4 | 100% | 3.5 | 0.837 | 2.2 |
| 200 | 0.008 | 0.0050 | k=4 | 100% | 2.0 | 0.845 | 2.0 |
| 200 | 0.010 | 0.0005 | k=4 | 100% | 2.0 | 0.781 | 3.7 |
| 200 | 0.010 | 0.0010 | k=4 | 90% | 2.0 | 0.790 | 3.6 |
| 200 | 0.010 | 0.0020 | k=4 | 100% | 1.5 | 0.786 | 4.0 |
| 200 | 0.010 | 0.0050 | k=4 | 100% | 0.0 | 0.779 | 3.8 |
| 500 | 0.007 | 0.0005 | k=3 | 70% | 4.5 | 0.918 | 0.9 |
| 500 | 0.007 | 0.0010 | k=4 | 70% | 5.0 | 0.919 | 0.8 |
| 500 | 0.007 | 0.0020 | k=4 | 100% | 5.5 | 0.916 | 0.9 |
| 500 | 0.007 | 0.0050 | k=4 | 100% | 3.0 | 0.922 | 0.9 |
| 500 | 0.008 | 0.0005 | k=4 | 60% | 8.0 | 0.899 | 1.8 |
| 500 | 0.008 | 0.0010 | k=4 | 90% | 6.5 | 0.895 | 1.8 |
| 500 | 0.008 | 0.0020 | k=4 | 100% | 7.5 | 0.901 | 1.8 |
| 500 | 0.008 | 0.0050 | k=4 | 100% | 5.0 | 0.902 | 1.8 |
| 500 | 0.010 | 0.0005 | k=4 | 90% | 7.0 | 0.856 | 4.0 |
| 500 | 0.010 | 0.0010 | k=4 | 100% | 8.0 | 0.860 | 3.8 |
| 500 | 0.010 | 0.0020 | k=4 | 100% | 6.5 | 0.858 | 4.2 |
| 500 | 0.010 | 0.0050 | k=4 | 100% | 1.5 | 0.852 | 4.2 |
| 1000 | 0.007 | 0.0010 | k=4 | 60% | 6.5 | 0.934 | 0.9 |
| 1000 | 0.007 | 0.0020 | k=4 | 90% | 5.5 | 0.939 | 0.9 |

## Branch Interpretation
Branch C: k oscillates / agreement low at N=1000 — observer stability depends on system size.

## Audit Checklist
[AC-1] hyst_0.01 frozen as canonical     : YES
[AC-2] k-switch logged per run            : YES (SwitchEvent JSON)
[AC-3] Canonical stability metric used    : YES (switches_per_100_windows)
[AC-4] N=1000 without physics patches     : YES
[AC-5] Comparable output schema           : YES (identical to v19g_canon)
[AC-6] No ontology expansion              : YES
[AC-7] Grid subset only (plb/rate reduced): YES — 2 configs at N=1000
