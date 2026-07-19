# Top-40 V3 post-tournament research extension

This study preserves Top-40 V3 and its original candidates as immutable historical evidence while
allowing explicitly adaptive research on the revealed record through 2023-06-30. It is not a
continuation of the V3 competition and cannot alter a V3 nomination, rank, or result.

The extension has two candidate lineages:

- Team 06: the own-coin multi-horizon time-series-momentum candidate.
- Team 04 UTC: the grandfathered uncrowded-trend-carry candidate that actually received the V3
  validation probe. This is distinct from Team 04's unevaluated downside-risk mandate.

## Evidence boundary

| Layer | Inclusive dates | Permitted feedback |
| --- | --- | --- |
| Adaptive development | 2020-02-03 to 2023-06-30 | full artifacts and diagnostics |
| Historical qualifier | 2023-07-01 to 2024-06-30 | one pass/fail decision per frozen finalist |
| Historical final | 2024-07-01 to 2026-06-30 | one complete release after all passers finish |
| Live forward | from 2026-08-01 | no changes during the declared observation period |

The revealed V3 validation year is development data in this study. It must never again be called
holdout evidence for a modified candidate. The historical qualifier and final remain outcome-blind
only while their raw rows and strategy results are inaccessible to the research process.

Development execution is fixed to the existing V3 runner's `public` stage, whose hard-coded end is
`2023-07-01T00:00:00Z`. Candidate code is hash-archived before every material run. A finalist binds
the exact source archive, strategy, risk policy, evaluator, dependency lock, and data authority.

## Research discipline

- The complete twelve-candidate matrix is declared in `policy.json` before the first result.
- Every attempted development run is append-only and failures count.
- At most one finalist may be frozen per lineage.
- No candidate may enter the qualifier unless it passes every selection floor.
- Qualifier failure retires that lineage for these historical windows.
- Qualifier passers enter the final unchanged; repairs and replacements are forbidden.
- The final is run serially but disclosed simultaneously.
- Later access, accidental or deliberate, invalidates the affected sealed window before use.

## Economic selection rule

Selection emphasizes durable edge after realistic costs rather than maximum backtest Sharpe. A
finalist must pass the existing stitched performance core plus all of the following:

- annualized one-way turnover no greater than 30 times equity;
- gross arithmetic edge of at least 30 basis points per unit of one-way turnover;
- base fees and slippage consume no more than half of positive gross PnL;
- at least three of four calendar folds have positive base and doubled-cost return;
- worst fold net Sharpe is at least -0.50;
- at least three of four frozen regimes have positive Sharpe and the worst is at least -0.75.

These are feasibility floors, not an optimizer. Among passers, the fixed ranking in `policy.json`
prefers doubled-cost Sharpe, worst-fold Sharpe, gross edge density, lower turnover, and finally the
lexicographically smaller candidate ID.

Raw development runs remain in the V3 runner's organizer namespace. Canonical extension summaries,
the chained journal, finalist freezes, qualifier decisions, and final release live under this
extension's own tournament and report namespaces.
