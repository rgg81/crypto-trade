# Iteration 161 Research Brief

**Type**: EXPLOITATION (infrastructure — DSR integration into reports)
**Model Track**: codebase enhancement, no strategy change
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Iter 160 added DSR helper functions to `backtest_report.py`. Iter 160's
diary Next Ideas #2 called for wiring DSR into `iteration_report.py`'s
`SplitMetrics` and `comparison.csv` output so every future backtest
automatically reports DSR alongside Sharpe.

## Scope

**ADD**:
- `dsr` field to `SplitMetrics` dataclass
- `n_trials` optional parameter to `_compute_metrics()` and
  `generate_iteration_reports()` (default: 1 → no deflation)
- Compute DSR using daily returns from `to_daily_returns_series()`
- Include `dsr` in `comparison.csv` metrics
- Print DSR alongside Sharpe in report summary

**DO NOT CHANGE**:
- `BacktestSummary` dataclass
- Existing metric semantics
- Default behavior for existing callers (n_trials=1 → DSR reduces to
  SR/SE, which is interpretable per-iteration but doesn't penalize)

## Design Decisions

### Default `n_trials=1`

- Keeps backward compatibility: existing callers get a computed DSR but
  without multi-testing penalty.
- Users who want the full iteration-count penalty set `n_trials` explicitly.
- DSR at N=1 reduces to `Sharpe / SE(Sharpe)` — still informative as a
  "raw t-stat" view.

### DSR in comparison.csv

- Added after calmar_ratio, before total_net_pnl.
- Same format as other float metrics.
- Ratio column: OOS_dsr / IS_dsr (comparable trajectory).

## Checklist Categories

- **H (Overfitting Audit)**: wires the DSR metric added in iter 160
  into the automatic report pipeline.

## Success Criteria

- All new unit tests pass
- Existing `test_backtest_report.py` tests still pass (13 tests)
- `ruff check` clean
- No regressions in existing backtest report generation

## No Merge Decision Expected

This is a pure infrastructure iteration. Codebase gains automatic DSR
reporting; BASELINE remains v0.152. MERGE iff tests pass.
