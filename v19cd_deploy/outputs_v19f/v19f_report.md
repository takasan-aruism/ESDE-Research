# ESDE Genesis v1.9f — Observer Stability Report

## Task 1: Margin Analysis

| Rate | Mean Margin | |m|<0.01 | |m|<0.02 | |m|<0.05 |
|------|-------------|---------|---------|---------|
| 0.0 | +0.0000 | 100.0% | 100.0% | 100.0% |
| 0.0005 | +0.0349 | 74.0% | 74.8% | 80.8% |
| 0.001 | +0.0648 | 57.4% | 59.4% | 64.7% |
| 0.002 | +0.1225 | 32.4% | 36.4% | 44.0% |
| 0.005 | +0.2587 | 7.6% | 9.2% | 18.0% |

Conclusion: rate=0.001 agreement drops because margin is near-zero (tight competition).

## Task 2: Switch Causes

3→4: 134 events
4→3: 123 events

## Task 3: Rule Comparison (rate=0.001)

| Rule | Agree% | Switch/100 | Dom k* |
|------|--------|-----------|--------|
| hyst_0.01 | 100.0% | 4.8 | k=4 |
| hyst_0.02 | 100.0% | 4.8 | k=4 |
| hyst_0.05 | 90.0% | 4.0 | k=4 |
| smooth_3 | 90.0% | 18.9 | k=4 |
| smooth_5 | 90.0% | 8.8 | k=4 |
| baseline | 70.0% | 30.9 | k=3 |

Best rule at rate=0.001: hyst_0.01 (agree=100.0%)

## Task 4: k=3 Info Density

None split probe: marginal (ΔH≈0 for most windows, confirmed in v1.9e).
Current 4-bin (None/WeakOnly/Mid/Strong) is optimal for N=200.
