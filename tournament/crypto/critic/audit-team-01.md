# Critic audit — team-01 (t01-funding-carry-xs-v1) — VERDICT: PASS

Batch 1 audit. Basis: charter + config + registry + journal (incl. §13 AMENDMENT #1 and data
amendments); evaluator source reviewed; harness independently rerun; sources independently
grepped (incl. out/scratch/ and non-.py files); SHAs recomputed; ledger/brief/report/provenance
read; team tests executed.

- **HARNESS: PASS.** Rerun `cli.py audit --team team-01`: all six checks PASS (scan,
  determinism, truncation ×12, corruption, same-bar, widening), zero violations. Rerun output
  byte-identical to the frozen `teams/team-01/out/harness.json` (snapshotted before rerun).
- **SCAN+GREP: CLEAN.** `strategy.py` imports numpy/pandas only; no prohibited paths, network
  tokens, obfuscation patterns, or cross-team references in any file (.py or .md).
  `out/scratch/carrylib.py` reaches data only via `te.load_is_panels()` (authorized scratch
  use); no holdout probing.
- **SHAS: CLEAN.** `submission.json` sources_sha256 (strategy.py, test_strategy.py) matches the
  tree exactly; `net_is.csv` SHA matches; `reported` block equals `out/is_metrics.json`
  verbatim; working tree matches freeze commit 8f328ad3.
- **LEDGER: CLEAN.** 12/40 entries, evaluator-stamped, monotone timestamps (18:35:30→18:44:10),
  hypothesis-before-result phrasing throughout, coherent grid narrative (e02 grid-edge → e03
  extension → e08/e09 neighbor mapping → e10 deep check → e11 ablation → e12 spec-equivalence).
  Freeze (19:07:28) postdates the last entry.
- **FAMILY FIDELITY: CONFIRMED.** Implemented mechanism (smoothed same-bar funding → negated
  centered pct-rank → inverse-vol → weight EWM) is exactly the approved
  `t01-funding-carry-xs-v1`. No drift into any other team's family.
- **ARTIFACT CONSISTENCY: CLEAN.** Every §1–§4 number in `is_report.md` exists in
  `out/is_metrics.json` (Sharpe 2.4067/1.7023, maxDD −24.16/−25.84%, turnover 188.36, funding
  +0.71347, costs 0.53143/1.06287, breadth 20/20). Breadth floor met at 4× margin. 2×-stress
  decay disclosed (chop ≈ +0.09 at 2×, stated plainly). Scratch-provenance numbers (§5–§6) all
  labeled with ledger ids (e10, e02/e03, e06, e11).
- **OVERFIT SMELL (informational, not a DQ):** low-moderate. The selected config sits at the
  freshest end of the smoothing grid (funding EWM halflife 2, weight span 2) reached after
  twice extending the L-grid downward — a fresh-edge pick, mitigated by explicit
  neighbor/boundary mapping (e08/e09) and turnover/stress tie-breaks. Funding P&L (+0.713)
  exceeds total 1× costs, but funding IS the registered family and the price-leg is
  independently decomposed (funding-off ≈ 1.51, ledgered e10). Monotone yearly decay 3.56→0.68
  is disclosed with an explicit "expect 0.5–1.5, not 2.4" forward statement — exemplary
  honesty. Note for the record: AMENDMENT #1 originated from this team's QE harness BLOCK
  report; it was variant-construction-only, journaled, applied uniformly — not a finding.
