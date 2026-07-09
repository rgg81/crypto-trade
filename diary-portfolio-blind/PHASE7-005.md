# PHASE7-005 — EXPLORATION-005 MERGE verdict + FROZEN CONFIRMATION interpretation map

**Date:** 2026-07-10. **IS Verdict: MERGE-TO-CONFIRMATION** (Critic REVIEW-005 PASS; G1–G6 all clear).

## EXPLORATION-005 = track's first MERGE candidate
Construction: vol_low mid-vol tail-capped neutral (`weighting="midvol_short"`, long lowest-vol half / short
mid-vol band / skip extreme-vol tail / near-dollar-neutral / gross=1.0 / funding ON) at **rebal=21 (weekly)**
— the ONE change vs EXPLORATION-002 (rebal 6→21; canonical weekly, pre-registered, NOT the IS-max). IS results:
Sharpe **+0.913**, maxDD **−33%**, turnover 55x, 2×-cost **+0.77**, **all 6 years positive** (min +0.35).
Funding dodge preserved (2021 −208bps net income). 33/33 tests green incl. leak@rebal=21. Critic: real,
selection-bias defensible-but-temper (OOS expectation +0.65–0.80 after multiple-testing haircut), /002 freeze
not breached.

## FROZEN CONFIRMATION interpretation map (pre-registered BEFORE any OOS look)
OOS window: 2025-03-24 → ~2026-07-08 (~15 months). Construction byte-identical (no tuning after OOS). Single
pass; evaluate the OOS portion (signal/universe use past-only warmup from IS). Decision tree:

| OOS outcome | verdict | action |
|---|---|---|
| Sharpe **≥ +0.60** AND no OOS year < 0 AND maxDD ≥ −50% | **DEPLOYABLE** (MERGE confirmed) | This is the track's deliverable. Write BASELINE, ready for live-paper / deployment planning. |
| Sharpe **∈ [+0.30, +0.60)** OR one OOS year slightly negative (≥ −0.5) | **PARTIAL** | Edge real but weaker OOS. Add the hysteresis complement (REVIEW-005 F1 intra-rebal drift), re-test. Possibly deployable with refinement. |
| Sharpe **< +0.30** OR any OOS year < −1.0 OR maxDD < −60% | **FAIL** (IS overfit) | Not deployable. Document the negative result honestly; the cadence scan was IS-fit. Conclude or pivot. |

Supplementary OOS observations (report, do not gate on unless noted):
- OOS maxDD: if deepens beyond −45%, flag the intra-rebal drift risk (REVIEW-005 F1) — hysteresis complement warranted even if Sharpe holds.
- OOS 2023-analog regime (chop): the weakest IS year (+0.35) — if the OOS window is choppy and breaks, that's the diagnostic.
- Per-OOS-year Sharpe + funding attribution + leg P&L (mirror the IS characterization).

**NO POST-HOC TUNING.** Whatever OOS shows, the construction stays frozen. If FAIL, it fails — no parameter
adjustment, no "try rebal=42 instead" (42 is IS-max; switching to it after seeing OOS would be mining). The only
permitted follow-on (if PARTIAL) is the pre-named hysteresis complement, registered as a NEW EXPLORATION.

## Why this is the right MERGE candidate (the arc)
4 prior NO-MERGE explorations mapped a cadence-dependent ceiling: the OHLCV-8h vol_low cross-sectional alpha is
real (+0.052 IC, stable, orthogonal) but was being eaten by 138x turnover at the unvalidated rebal=6 anchor.
The substrate lever (weekly rebalance) — named as highest-ROI by REVIEW-002/004, RISK-004, PHASE7-004, and the
skill itself, all BEFORE the result — lifted the EXPLORATION-002 construction from +0.09 to +0.91. First book to
clear +0.60 with every year positive, funding-neutral, −33% maxDD. The Critic cleared it for CONFIRMATION.

## Next step (pending user go-ahead + commit)
Reveal OOS once, evaluate against the frozen map above. This is the one-time irreversible OOS look.
