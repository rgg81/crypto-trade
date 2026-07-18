# Critic audit — team-04 (t04-ts-trend-v2, redraw) — VERDICT: PASS

- **HARNESS: PASS.** All six checks PASS on rerun, zero violations; byte-identical to frozen
  `out/harness.json`.
- **SCAN+GREP: CLEAN.** `strategy.py` reads `pn["close"]` only; scratch clean; `globals()` in
  `test_strategy.py:144` is a benign manual test runner; no prohibited access.
- **SHAS: CLEAN.** sources_sha256 match; net_is.csv SHA match; `reported` equals
  is_metrics.json; tree matches freeze commit d2ed4f7b.
- **LEDGER: CLEAN.** 12/40 entries, evaluator-stamped, monotone (18:59:41→19:16:14); e12 is
  post-team-run adjudication forensics, explicitly no-tuning, logged before freeze (19:19:11).
- **FAMILY FIDELITY: CONFIRMED, one documented deviation.** Approved `t04-ts-trend-v2`; the
  implementation is pure per-name multi-horizon TS trend, no cross-sectional operation
  (explicitly differentiated from t03). **Known and adjudicated code/spec deviation:**
  `strategy.py` step 7 accumulates the horizon-presence counter as bool frames (`cnt +
  present` = logical OR), so `cnt` saturates at 1 and the signal is the SUM over available
  horizons, not the docstring's NaN-skipping MEAN. This was caught by the team's own forensics
  (ledgered e12: sum-semantics rebuild bit-identical to the frozen code; official 1.609/1.316
  reproduced exactly; mean variant is a plateau member at 1.624/1.336), disclosed in
  `is_report.md` §3 with the orchestrator's ruling (frozen code canonical), and marked in the
  brief's §8 adjudication note. The frozen artifacts ARE the frozen code's output — no
  reproduction or integrity issue; the residual defect is only a stale docstring inside the
  frozen file, which cannot be edited post-freeze. No action required.
- **ARTIFACT CONSISTENCY: CLEAN.** All official numbers match `out/is_metrics.json`
  (1.609/1.316, −37.3/−44.0%, 790.4/475.5%, 125.43, 18/17, funding +0.0651, costs
  0.3561/0.7121, regime table exact). Breadth floor met. Chop-bleed at 2× (−0.235) stated
  plainly. All auxiliary numbers marked SCRATCH with ledger ids.
- **OVERFIT SMELL (informational):** low. Selection landed in a statistical-tie cluster
  resolved by pre-registered tie-breakers (fewest changes from defaults → turnover →
  worst-regime), and e11 verified the pick is not a 2020-21 artifact within its cluster.
  Front-loaded edge disclosed (+2.643 vs +0.773 halves; forward expectation ~0.7–0.8 stated).
