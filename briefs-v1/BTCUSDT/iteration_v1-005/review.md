# Phase 7.5 Critic Review — iter-v1/005 (BTCUSDT) — EXPLORATION screen

## Verdict: NEGATIVE — funding feature inverts, does not lift.

### Results (K=5 screen) vs prune-only anchor
| | IS Sharpe | OOS Sharpe | OOS/IS ratio | dispersion | IS net | OOS net | trades |
|---|---|---|---|---|---|---|---|
| iter-001 baseline (K=20) | −0.2793 | +0.6401 | −2.29 (inversion) | 49.46 | −12.02 | +9.07 | — |
| iter-004 prune-only (K=20) | −0.17 | +0.48 | −2.82 (inversion) | — | — | — | — |
| iter-005 prune+funding (K=5) | **−0.4322** | **+0.8521** | **−1.97 (inversion)** | 40.05 | −18.37 | +12.13 | 194/83 |

### Critic's literal read
The generalization-coherence gate (user directive, codified at iter-002) ranks a both-positive
profile with healthy OOS/IS ratio ABOVE a sign-inverted profile, regardless of raw OOS. iter-005
is inverted (IS −0.43, OOS +0.85, ratio −1.97) — structurally the iter-001 baseline artifact we
were told not to reward. The funding feature made **IS worse** than prune-only (−0.43 vs −0.17),
so it is not an additive edge. **NEGATIVE.** Do not advance to confirmation.

### Methodology PASS on results
- Honest-cost netting verified (net = pnl − fee − slippage; OOS net +12.13 on +0.85 Sharpe).
- IS/OOS split at 2025-03-24 honored; backtest ran full data.
- Funding feature provably trained: parquet column present (97% IS / 100% OOS coverage), override
  banner shows features=42, `available_feat_cols` keeps it. The importance-CSV omission is a
  reporting-list artifact (193-col canonical list), not a drop.

### Flags
- **Importance verifiability gap:** orthogonal override features do not appear in
  `feature_importance_*.csv` (writer keyed on V1_FEATURE_COLUMNS, not active columns). Fix before
  the next orthogonal screen so we can read learned-vs-ignored rank. (Task #130.)
- **K-confound:** no K=5 prune-only control; attribution of the IS drop to funding vs K is
  directionally clear (K-monotonic prune-only trend) but not isolated. Fine for a NEGATIVE screen.

## Proposed Backtest Changes (mandatory)
1. **iter-v1/006 — FE-driven orthogonal selection.** Stop mechanically swapping single features.
   Hand the full non-OHLCV family space (funding z30/z90, OI delta/divergence, basis_zscore_30,
   long_short_zscore_30, cross-BTC ratios) to the Feature Engineer for IS-only IC + redundancy +
   cluster-importance analysis; screen the highest-conviction single feature OR a small orthogonal
   cluster. Wire importance to active columns first.
2. **Pre-register the coherence guardrail in the iter-006 brief:** the screen is PROMISING only if
   the profile is both-positive (IS > 0 AND OOS > 0) with ratio ≥ 0.5 — an inverted profile is an
   automatic NEGATIVE no matter how high OOS prints.
3. **If iter-006/007 also invert:** that is decisive evidence BTC's edge is regime-driven and
   thin; report to the user before spending a K=20 confirmation, and consider whether BTC is the
   right first symbol vs a coin with a coherent IS edge.
