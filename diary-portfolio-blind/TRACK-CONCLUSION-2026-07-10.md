# TRACK CONCLUSION — baseline-blind top-20 L/S (v1), 2026-07-10

**Ended by user decision, 2026-07-10: "for now this experiment should end. Too much data leak."**
A successor track (baseline-blind, MARKET-NEUTRAL mandate, fresh namespaces) starts immediately;
see ORCHESTRATOR_BRIEF_MN.md.

## Why it ends
Cumulative epistemic leakage on this instantiation's data:
- The original OOS window (2025-03-24→) was revealed once for /005 (FAIL), then — at explicit
  user instruction — revealed AGAIN for the current books (BURNED-REVEAL-2026-07-10.md), making
  it design-contaminated in both directions.
- Two full IS redesign cycles ran on the same IS window post-reveal (cumulative n_eff ≈ 17–23).
- The reveal also showed the phase-honest L1 edge ≈ −0.2 on 2025-26 and the IS crash alpha not
  persisting — informational, but enough to end the line honestly rather than forward-test a
  book whose recent-regime evidence is negative.

## Final state
- **Forward paper-trade: DISARMED before T0** (systemd timer `blind-paper-l1.timer` disabled
  2026-07-10; T0 was 2026-07-15 — ZERO forward candles ever accrued under EITHER protocol
  version; nothing abandoned mid-flight). PROTOCOL-ENSEMBLE-L1-FORWARD is RETIRED unexecuted.
- No deployment. No live orders were ever placed (paper-only architecture).

## What survives (reusable assets for the successor and any future track)
1. **blind_engine.py + 55-test leak/parity suite** — signal-agnostic, realistic-cost, leak-safe
   L/S engine with risk-control plumbing (gross/short scalars, DD brake, short-exclusion).
2. **The recompute forward-validation architecture** (growing-panel re-run, append-invariance,
   integrity pinning, tamper-evident weekly commits) — blind_paper_l1.py.
3. **Methodology, hard-won:** rebal-PHASE is a first-order robustness axis (sweep all offsets;
   phase-agnostic mean is the honest level; 21/21-positive deltas beat any single-phase
   headline); staggered-tranche ensembles clip timing tails (maxDD −37%→−19% IS) but do NOT
   create edge; holdings-correlation ≠ return-stream-correlation; principle-anchored gates
   (preserve-not-improve, relative-to-reference) vs absolute floors derived from lucky draws;
   stateful gates must be calibrated in-loop; analytic cost twins are inexact on fixed-share
   engines; market-only bucket rules (no strategy-P&L selection); pre-registration + adversarial
   Critic + falsification arms WORK — they caught every major error this phase.
4. **Data-pipeline fixes:** fetch --all poisoning by PENDING_TRADING symbols (tolerant per-symbol
   fetch), the 4.5-month panel-starvation discovery (CONFIRMATION-005's −73% maxDD was largely a
   DATA ARTIFACT — /005 on complete data: +0.139/−27.6%, FAIL survives via the Sharpe floor),
   live-feed-scoped staleness guards.
5. **Committed evidence:** phase_sweep_is.csv, /006-/007 briefs + reviews + engineering reports,
   the mania market-rule (blind_mania_rule.py), both protocol versions, the burned-reveal record.

## Verdict on the research line
The OHLCV-8h volume-top-20 cross-section (vol_low family), even with phase-honest measurement,
regime-targeted risk controls, and tranche ensembling, shows no durable deployable edge:
IS strength was substantially phase luck; the crash-insurance mechanism decayed out-of-sample;
the mania fix works but its regime is too rare to carry a book. Documented honestly; closed.
