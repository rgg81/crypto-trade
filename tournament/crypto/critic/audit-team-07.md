# Critic audit — team-07 (t07-vol-structure-v1) — VERDICT: PASS

- **HARNESS: PASS.** All six checks PASS on rerun, zero violations; byte-identical to frozen
  `out/harness.json`.
- **SCAN+GREP: CLEAN.** Close-panel-only signal, numpy/pandas imports; scratch clean; no
  prohibited access.
- **SHAS: CLEAN.** All match; tree matches freeze commit fb869fae.
- **LEDGER: CLEAN.** 12/40 entries, evaluator-stamped, monotone (19:17:49→19:26:46), freeze
  19:35:38 after last entry.
- **FAMILY FIDELITY: CONFIRMED (two-stage falsifier verified).** Brief §3 pre-registered the
  lottery-premium falsifier; it FIRED at e01/e02 (all 10 configs negative, funding premise
  wrong-signed); brief §A1 ("logged after e01/e02, before any further experiment")
  pre-registered the reversed H2 AND the stricter bar (3-window-neighborhood ≥ +0.35 @1×,
  2× > 0, breadth, ≥2/3 regimes) BEFORE e03 ran, and the e03/e06 ledger hypotheses (stamped
  before results) independently carry the same stricter bar. The shipped mechanism — long
  sustained vol-expansion / short compression — is explicitly within menu family #6's own text
  ("rank by realized vol dynamics (compression/expansion), long the profile that pays"), so
  the branch change stays in-family. Level-branch failure at both signs documented (§A2).
- **ARTIFACT CONSISTENCY: CLEAN.** All §1–§2 numbers match `out/is_metrics.json`
  (1.0247/0.8260, −31.13/−32.80%, 70.47, 20/20, funding +0.1169, cost 0.1988/0.3976, regime
  table exact — 3/3 buckets positive both tiers). §4 scratch numbers labeled with ledger ids.
  Funding share (11.7% of pre-cost P&L) disclosed with the pre-committed >70% honesty rule
  unfired. Decay disclosed (halves +1.22/+0.80; last-12-months +0.44 flagged as the closest
  holdout analog).
- **OVERFIT SMELL (informational):** moderate-low. The score-EMA halflife grid was extended
  three times (e08→e10→e11) chasing a rising Sharpe until rollover; mitigants: each extension
  pre-committed a limit ("at most ONE further… then selection freezes", honored), the final
  hl=72 is an interior optimum (0.899→0.991→1.025→0.961→0.931), and selection used a 3-cell
  neighborhood mean — though the chosen point is also the profile peak. One falsifier was
  consumed by the data-informed sign change, handled with the raised bar. **Process note (not
  a team finding):** `is_report.md` §1 quotes an orchestrator remark ("turnover ~70/yr is the
  lowest in the field") — a cross-team aggregate conveyed pre-freeze; see cohort report.
