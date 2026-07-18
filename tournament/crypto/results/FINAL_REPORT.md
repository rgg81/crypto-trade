# crypto-cup-01 — FINAL REPORT

**Winner: team-02 — `t02-breakout-channel-v2` — sealed-holdout net Sharpe +2.113 (funding on).**
Deploys to the 6-month tournament paper desk.

## The tournament

Ten independent teams (QR = Fable, QE = Opus each), one read-only Critic (Fable), one
orchestrator. Substrate: Binance USDT crypto perpetuals, weekly point-in-time top-40 by
trailing 7-day dollar volume (pure crypto — stablecoins/tokenized stocks/metals/indexes
excluded), 8h bars, organizer-owned execution (0.10/0.25 caps, shift(1) fill, 5 bps taker +
liquidity-scaled slippage, NATIVE per-event funding P&L, vol-target 1%/candle). IS
2020-01-01→2024-06-30 (frozen SHA-manifest snapshot, 209 symbols, 628 files, digest
`93cc37d3…`); holdout 2024-07-01→2026-06-30 sealed and run once per finalist; objective =
net Sharpe (monthly, √12).

## Stage-2 sealed holdout (24 months, funding on, full 430-symbol universe)

| rank | team | family | holdout | IS @1x | maxDD | sensitivities (nofund / 2×cost / 2×slip) |
|---|---|---|---|---|---|---|
| **1** | **team-02** | **breakout-channel** | **+2.113** | +2.069 | −26.1% | +1.562 / +1.939 / +2.074 |
| 2 | team-05 | taker-flow continuation | +1.551 | +1.501 | −35.5% | +0.935 / +1.261 / +1.488 |
| 3 | team-04 | TS-trend | +1.499 | +1.609 | −31.8% | +0.844 / +1.286 / +1.451 |
| 4 | team-01 | funding-carry XS | +0.152 | +2.407 | −38.9% | −1.521 / −0.434 / +0.023 |

NOISE FLOOR: 24 monthly points ⇒ Sharpe SE ≈ ±0.77. The team-05/team-04 gap (+0.05) is a
statistical tie; team-02's margin over both (+0.56/+0.61) is inside one SE but consistent
across every sensitivity. The locked rule (best canonical holdout Sharpe) decides.

All four finalists passed the Run-A causality gate (IS-row weights bit-identical to the
frozen Stage-1 book) and the eligibility mask-replay check. Every holdout invocation was
journaled before computing.

## The headline stories

1. **The IS leader collapsed — exactly as its own caveat predicted.** team-01's funding-carry
   book led Stage 1 at +2.407 but pre-registered an alpha-compression warning (yearly Sharpe
   3.56→0.68 by 2024H1; "expect 0.5–1.4, not 2.4"). Holdout delivered +0.152 — below even
   their floor. The decomposition is stark: funding leg still collects (+0.741 cum; the
   mechanical cash flow persists) but the crowding-unwind price leg inverted (no-funding
   Sharpe −1.521). Selection-on-IS risk, realized. This is the tournament working as designed.
2. **The winner came from a pivot.** team-02's registered OI-crowding fade died honestly
   (falsifier fired, gross-negative everywhere, both signs); their documented pivot to
   Donchian channel-position books produced the most regime-robust result in the field —
   IS +2.069 → holdout +2.113, near-zero generalization gap, robust to doubled costs and
   funding-off. Three of ten teams pivoted after honest falsifier kills (02, 08, 09); the
   winner is one of them.
3. **Continuation ruled the 8h cross-section.** Two teams (08, 09) independently falsified
   reversal/snap-back mechanisms with evidence-monotone continuation measurements; the four
   books that generalized best all monetize persistence through different constructions
   (channel position, taker flow, multi-horizon trend, volume-confirmed momentum).
4. **Funding was a tailwind for every finalist in holdout** (+0.57 to +0.74 cum) — the
   engine's per-event funding model (255 of ~395 symbols pay every 4h, not 8h) materially
   shaped net results; the old repo model would have dropped half those events.

## Field results (Stage 1, all Critic-PASSED 10/10)

| team | family | IS @1x | @2x | holdout expectation they pre-registered |
|---|---|---|---|---|
| 01 | funding-carry XS | +2.407 | +1.702 | 0.7–1.4 ("not 2.4") — actual +0.15, below floor |
| 02 | breakout-channel (pivot) | +2.069 | +1.821 | "nearer 1 than 2" — actual +2.11, above ceiling |
| 04 | TS-trend (redraw) | +1.609 | +1.316 | ~0.7–0.8 — actual +1.50, above |
| 05 | taker-flow (redraw) | +1.501 | +1.049 | 0.2–0.9 — actual +1.55, above ceiling |
| 10 | volume-confirmed momentum | +1.419 | +0.992 | (5th — missed the cut by 0.082, inside noise) |
| 03 | BTC-residual momentum | +1.304 | +0.927 | 0.5–0.9 |
| 06 | L/S-ratio contrarian | +1.176 | +0.744 | 0.8–1.2 (coverage-diluted board number) |
| 07 | vol-dynamics XS | +1.025 | +0.826 | 0.3–0.7 |
| 09 | trade-size composition (pivot) | +0.830 | +0.590 | momentum-correlated caveat on record |
| 08 | OI-price confirmation (pivot) | +0.460 | +0.205 | 0.4–0.9 (0.49× coverage dilution disclosed) |

## Integrity record

- 10/10 Critic PASS; zero BLOCK-PENDING-FIX rounds; zero disqualifications; no plagiarism.
- Harness reruns byte-identical for all ten; SHA-bound submissions unmutated; every ledger
  evaluator-stamped with coherent pre-registration ordering.
- 7 of 10 initial primary registrations collided on residual momentum (worse herding than
  tradfi-cup-01's 8/10); two-pass FCFS + one redraw round produced ten distinct mechanisms.
- Three honest falsifier kills → documented pivots (02: OI-fade; 08: short-horizon reversal;
  09: liquidation snap-back). Two judged family-boundary rulings (10: within-family CWMOM;
  09: ship-with-disclosure momentum overlap), both journaled at choice time.
- Two charter-§13 evaluator amendments, both variant-construction/integrity-check-only, both
  journaled, neither touching any scoring number: #1 harness funding windows aligned to the
  engine's jitter-snap semantics (found by team-01's QE — it false-failed honest same-bar
  funding strategies); #2 Run-A causality compare moved to IS-length scoring (1-ULP numpy
  reduction-order divergence on longer frames false-failed all four finalists whose raw
  weights were bit-identical; forensics in journal).
- Data amendments journaled from team EDA: OI panels thin before ~Dec-2021; L/S-ratio panels
  zero-corrupted through 2022.

## Honest caveats for the paper desk

1. **Holdout was one draw.** 24 monthly points, SE ±0.77 — team-02 vs teams 04/05 is within
   one SE. The locked rule decides; the paper desk is the next independent sample.
2. **The winner's book is short-tilted in breadth (13L/26S median in holdout) yet the field's
   most stress-robust** — its 2×-cost and 2×-slip Sharpes barely move. Expect paper
   performance nearer its recent-half run-rate (~+1.1) than +2.1.
3. **The regime-tag scorecard doesn't extend past IS** (holdout months are untagged) — the
   per-regime read on the winner comes from IS: bull +3.02 / bear +1.49 / chop +0.31, with
   chop the known weak weather.
4. Six of ten books were momentum-correlated; the holdout rewarded persistence. A
   chop-dominated paper window is the winner's declared weak regime — watch, don't patch.

## Process lessons (for cup-02)

- Registration herding is the norm (7/10 here, 8/10 in tradfi) — backups + redraw handle it;
  disclose FCFS position in the dispatch so late teams self-diversify (worked: 10's primary
  was uncontested).
- The falsifier-fires → documented-pivot path produced the WINNER. Honest kills are not
  consolation prizes; budget for them.
- Evaluator self-inconsistencies surface under team pressure (both amendments were found by
  team QEs hitting checks honestly. The BLOCK-report mechanism worked exactly as designed).
- Keep even aggregate cross-team facts out of pre-freeze team channels (one hygiene slip
  noted by the Critic, harmless here).
- ULP-determinism across frame lengths is a real hazard for bit-exact replay gates: pin the
  compare to identical-length frames from the start.
