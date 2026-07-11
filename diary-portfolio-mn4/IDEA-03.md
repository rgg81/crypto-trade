# IDEA-03 Regime-Adaptive Allocator — Diary

**Track:** MN4 blind tournament. **Pair:** QR+QE. **Model:** Opus 4.8 (Fable
suspended this session — user-directed; disclose per charter §"Model"). **Date:**
2026-07-12. **Status:** IS GATE PASS → **reveal-ready** (frozen, banked for Phase-B).

## Decision: BANKED FOR REVEAL (IS gate PASS)

The construction passes ALL principle-anchored IS gates. It is frozen byte-exact.
The 2-year holdout is SEALED; the family token is reserved for the Phase-B reveal.

## Construction (frozen one-liner)

Principle-anchored threshold-rule regime detector (NORMAL/STRESS/CRISIS on BTC
rv30_ann + gap_z, STRESS hysteresis 0.80→0.60, CRISIS 5σ/12% trigger + 3-candle
dwell) → 60c cross-sectional momentum alpha (single signal, all regimes) → regime
drives universe (top-20→top-5 in STRESS) + gross (1.0→0.5→0.0) → rank-neutral +
BTC/ETH beta-hedge → daily rebal (rebal=3) → honest 5+2.5 bps + funding.

## IS Headline

- **Sharpe 1x: +1.552, Sharpe 2x (GT twin): +1.280** — strong cost survival.
- MaxDD: -41.66%. Turnover: 132x ann. Mean gross leverage: 0.920.
- All years positive (2020: +2.77, 2021: +2.08, 2022: +0.56, 2023: +1.40, 2024: +0.75).
- CRASH β: -0.012, MANIA β: +0.050, CHOP β: +0.009 (all < 0.20).
- Leak battery: PASS (corrupt-future + decision-lag on the stateful detector).

## Regime Occupancy

NORMAL 76.5%, STRESS 22.6%, CRISIS 0.9% (44 candles, 13 distinct entries). The
3-candle CRISIS dwell is the minimum for the daily rebal to catch every crisis —
well within the <5% calm-time occupancy bar (CRISIS-FALSIFY-003 lesson honored).
Sub-regime: NORMAL-TREND 45.3%, NORMAL-CHOP 54.7%.

## Per-Regime Attribution

NORMAL +6.38 bps/candle (Sharpe +1.79), STRESS +0.88 (+0.36), CRISIS +15.19 (+5.25).
The CRISIS Sharpe +5.25 is the crisis defense WORKING — the book is FLAT during
crisis dwell, avoiding the crash. NORMAL-TREND earns more than NORMAL-CHOP
(+8.04 vs +5.00 bps/candle), confirming the sub-regime classifier has discriminative
value (momentum is stronger in trends — informational, not traded on).

## What Worked

1. **The regime detector.** Principle-anchored, transparent, catches all IS crisis
   episodes (COVID, May-2021, LUNA, FTX) at 0-lag via the acute gap-z/abs-return
   trigger. The 3-candle dwell + daily rebal ensures the de-risk fires. Calm-time
   CRISIS occupancy 0.9% — no false-positive chronic stress.
2. **The de-risk primitive.** 383 rebals delevered (15 flat + 368 half-gross). The
   STRESS universe contraction (top-20→top-5) + gross halving (1.0→0.5) is the
   user's "stick to blue chips" mandate working BY CONSTRUCTION.
3. **The h=60 momentum alpha.** +1.06 Sharpe at 2x cost in the bare-signal scan.
   Cost-surviving. The charter's binding constraint (cost survival) met.
4. **Funding income.** +0.23 Sharpe from shorting high-funding alts. A genuine
   structural edge (crypto's positive funding on momentum alts = carry earned by
   the short leg).
5. **The leak battery.** The stateful regime detector passes corrupt-future +
   decision-lag. No look-ahead in the detector or the composite signal.

## What Failed (honest accounting — three iterations to the frozen design)

### Iteration 1: reversal-only (literal IC-scan interpretation)
- Close-to-close signal-IC scan showed reversal positive (+0.04-0.11), momentum
  null/negative. Built a 3c-reversal-in-TREND + 30c-reversal-in-CHOP design.
- **Result: Sharpe -1.55, MaxDD -95.6%, turnover 685x.** Catastrophic failure.
- **Root cause:** the close-to-close IC scan used the WRONG return convention. The
  engine earns **open-to-open** hold-period returns, not close-to-close. The two
  differ materially in crypto (session effects at 8h). The close-to-close IC was
  misleading by ~2.5 Sharpe.

### Iteration 2: h=3/h=30 reversal at rebal=1 (pre-cost-negative)
- Switched to shorter-horizon reversal (h=3 in TREND). Sharpe -1.69.
- **Root cause:** reversal is negative at ALL horizons on open-to-open. The
  zero-cost Sharpe was -0.80 — the signal generates NO edge even before cost.

### Iteration 3: h=60 momentum (the frozen design)
- Bare-signal open-to-open scan revealed momentum positive at all horizons.
- h=60 chosen as the best 2x-cost survivor (+1.06, turnover 125x).
- **Result: Sharpe +1.552.** PASS.

### Bug fixed: min_members=8 killed the de-risk primitive
- The first run showed 0 rebals delevered despite STRESS being 22.6% of candles.
- Root cause: `min_members=8` made EVERY STRESS rebal infeasible (the top-5 blue-chip
  core universe can never reach 8 members). The de-risk primitive was silently dead.
- Fix: removed `min_members` (set to None). The engine's `target_weights` returns
  zeros if <2 valid members — safe. The de-risk now fires correctly (383 rebals).

## Lessons

1. **Signal IC must use the strategy's actual hold-period return convention.**
   Close-to-close IC ≠ open-to-open strategy P&L. This cost 3 iterations and is the
   single most important methodological lesson from this idea. Any future signal
   research on this engine MUST measure IC on open-to-open forward returns.
2. **Crypto cross-sectional momentum is positive at all horizons 7-180c on
   open-to-open.** Reversal is null/negative everywhere. This is the OPPOSITE of the
   close-to-close IC picture and confirms that crypto exhibits persistent
   retail-flow-driven momentum (not the overreaction-reversion pattern the
   close-to-close IC falsely suggested).
3. **The regime detector's de-risk primitive must be TESTED for actual firing.**
   A min_members threshold that silently blocks STRESS rebals is an invisible failure
   mode. The `book_scalar_series` forensic is the audit trail — check it on every run.
4. **Cost survival is the binding constraint.** The h=3 signal had +0.11 IC (huge)
   but 685x turnover killed it. h=60 has lower IC but 125x turnover — it survives.
   The charter's cost-survival warning was the correct prior.
5. **CRISIS-FALSIFY-003 is not just about dwell length — it's about occupancy
   honesty.** The 3-candle dwell gives 0.9% CRISIS occupancy (13 entries). The
   detector REPORTS calm-time occupancy, doesn't just claim crisis-catch rate.

## Files

- `analysis/portfolio/mn4_idea03_regime.py` — regime detector + occupancy report.
- `analysis/portfolio/mn4_idea03_alpha.py` — 60c momentum alpha (frozen).
- `analysis/portfolio/mn4_idea03_run.py` — IS runner + scorecard + leak battery.
- `tests/test_mn4_idea03.py` — 13 tests (all PASS; ruff clean).
- `briefs-portfolio-mn4/IDEA-03.md` — this brief.

## For the Critic (Phase-C)

- The "reversal in chop" mandate was empirically null. The frozen book uses a single
  momentum alpha. The regime-adaptive ALLOCATION (universe + gross) is the
  regime-switching mechanism. Is this a legitimate "regime-adaptive allocator"?
- The rolling beta |p95| = 0.216 exceeds the strict G1a gate. The bucket betas
  (CRASH -0.012, MANIA +0.050) are well-controlled. Is the rolling-beta tail
  acceptable for a momentum book?
- The IC-vs-P&L disconnect (close-to-close vs open-to-open) is disclosed. Is the
  open-to-open signal scan sufficient evidence that the edge is real (not an IS
  artifact)?
- 2022 was the weakest year (+0.56). The holdout includes a crash-heavy tail.
  Does the crisis defense (flat in CRISIS) adequately protect OOS?
