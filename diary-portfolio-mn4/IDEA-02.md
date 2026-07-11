# IDEA-02 — Meta-Labeled Breakout (diary, MN4 Phase A)

> Model: **Opus 4.8** (Fable rate-limited this session; user-directed).
> Frozen: 2026-07-12. No holdout read. No git commit (orchestrator commits).

## Decision: NO-MERGE — not reveal-ready

Six of seven principle-anchored IS gates pass; **G3 (maxDD ≥ −30%) fails by
50 bps (−30.5%)**. Per the freeze-then-reveal discipline (charter Phase A →
Phase B), no post-hoc throttle tightening is adopted. Token NOT spent; this
is a clean IS null on one gate, not a holdout failure.

## IS headline

| | filtered | unfiltered |
|---|---:|---:|
| Sharpe 1× | **+1.915** | +2.056 |
| Sharpe 2×-GT | **+1.429** | +1.752 |
| maxDD | **−30.5%** | −21.0% |
| turnover_ann | 109.7 | 107.2 |
| β_BTC mean (post-hedge) | +0.004 | — |
| CRASH β_BTC | +0.002 | — |
| CRASH net Sharpe | −3.12 | −1.54 |
| meta precision lift | **+5.90 pp** | (base 0.4794) |

## What worked

1. **The meta adds real precision.** Weighted-precision lift = +5.90 pp
   (0.5384 vs base 0.4794). The classifier learned something real about which
   breakouts pay. The hard-gate reference trio (θ = 0.55 / 0.60 / 0.65) is
   monotone — higher θ → higher precision → lower take-rate, exactly the
   precision/recall frontier you'd expect from a calibrated classifier.

2. **The meta improves the hard regimes.** Per-year Sharpe:
   - 2022 bear: filtered +0.14 vs unfiltered −0.06 (lift +0.20)
   - 2024-H1: filtered −0.48 vs unfiltered −1.03 (lift +0.55)
   - 2020: identical (no OOF coverage before 2021-07 → primary trades unfiltered).
   This is the GENERALIZATION the charter asks for — better in the bad regimes
   at the cost of some peak-regime alpha. Sharpe is the objective, not return.

3. **Cost-survival is robust.** 2×-GT Sharpe is +1.429 (75% of 1× Sharpe) — the
   book is genuinely cost-surviving, not a bid-ask-bounce artifact. Turnover
   is 110/yr one-way, far under the 300 gate.

4. **Neutrality by construction AND measurement.** β_BTC mean = +0.004
   post-hedge, β_ETH = +0.002, crash-bucket β = +0.002. The BTC leg of the
   hedge overlay does its job in every regime without an ETH leg.

5. **Leak battery is clean.** All 4 leak checks (corrupt-future, decision-lag,
   PIT membership, append-invariance) plus 2 unit tests pass. The OOF
   predictions are bit-identical across the append-invariance check — walk-
   forward + purge is implemented correctly.

## What failed

1. **G3 (maxDD ≥ −30%) fails by 50 bps.** The dd_brake (engage −15%, scale 0.30,
   release −7.5%) engages but the position drifts further before recovering.
   The filtered book's maxDD is also worse than the unfiltered book's (−30.5%
   vs −21.0%) — the continuous meta scaling can amplify gross leverage in
   periods where the meta is confidently wrong all at once.

2. **CRASH regime is the Achilles heel.** Filtered CRASH Sharpe = −3.12 vs
   unfiltered −1.54. The meta HURTS in crash. Root cause: the classifier was
   trained predominantly on chop/mania data (CRASH is only 13% of IS candles
   by mn_regimes frozen rules). In crash it keeps upside breakouts (which
   looked like continuations in training) that then fail. This is a genuine
   structural limitation of regime-agnostic meta-labeling on a primary whose
   failure mode is regime-conditional.

3. **2023 chop regression.** Filtered 2023 = +0.96 vs unfiltered +2.00. The
   meta attenuates some chop winners (continuous scaling zeros out signals
   it's uncertain about, and in chop the good breaks look similar to the bad
   ones to the classifier).

## Lessons (generalizable)

### L1 — Meta-labeling in a rank-neutral L/S framework is not the canonical event-driven framing
LdP's canonical hard take/skip is correct for EVENT-DRIVEN primaries (a
direction trade is emitted or not). For a rank-neutral L/S book it creates a
rank artifact: skipped names tie at signal=0 and the cross-section demeans
them into the opposite leg. The principled fix is **continuous confidence
scaling** (`signal × clip(2(p−0.5), 0, 1)`) — meta-as-refinement, not
meta-as-gate. The diagnostic was severe (Sharpe −0.23 → +1.92 from the fix
alone); future meta-labeling work on magnitude-aware books should adopt the
continuous scaling from the start. Documented in the brief as ruling R1.

### L2 — A regime-agnostic meta cannot fix a regime-conditional failure mode
The Donchian primary's worst regime is CRASH (Sharpe −1.54 unfiltered).
Training a single meta-classifier on all regimes teaches it the chop/mania
pattern (the dominant one) and it fails in crash. A regime-CONDITIONAL meta
(separate classifiers per mn_regimes bucket, or a CRASH feature given much
stronger weight) is the natural next step — but is out of scope for the
frozen Phase-A construction.

### L3 — maxDD is the binding constraint on this primary, not Sharpe
The unfiltered Donchian already clears Sharpe 1×/2×-GT/maxDD/neutrality gates.
The meta trades absolute Sharpe for generalization (better in bad regimes) —
but at the cost of maxDD amplification. The crisis throttle is the load-bearing
component for reveal-readiness on this family. A more aggressive throttle
(scale=0.10 or 0.0 instead of 0.30) is the obvious lever — but adopting it
post-hoc would be the very fitting-to-IS the charter §5 forbids.

## Leak battery (all PASS)

- **L1 corrupt-future**: corrupting `close[t+5:]` leaves don_score, all 14
  features, and the meta label on the clean prefix bit-identical.
- **L2 decision-lag**: don_score[t] from a panel truncated at row t equals
  don_score[t] from the full panel.
- **L3 PIT membership**: universe membership at row t depends only on
  quote_volume ≤ t.
- **L4 append-invariance**: 86,941 jointly-finite member cells are bit-identical
  between a full-IS run and a run with the last 3 months truncated. The walk-
  forward + 3-candle purge correctly isolates each month's training data.

Tests: `tests/test_mn4_idea02_leak.py` — 6/6 PASS, ~2 min wall.

## Cost coverage

ann_return (filtered) = +39.73%. Annual one-way turnover = 109.7. At 7.5 bps
one-way (5 + 2.5), annual cost drag ≈ 109.7 × 7.5 bps = 8.2%. Cost coverage
ratio = 39.73% / 8.2% ≈ 4.8× — the book comfortably clears cost. The 2×-GT
twin (Sharpe +1.429) confirms cost-survival under doubled fees.

## Path forward (NOT adopted — out of freeze scope; recorded for the Critic)

1. **Tighten the crisis throttle.** dd_brake scale 0.30 → 0.10 (or 0.0).
   Predicted effect (mechanical): maxDD compresses toward −15..−20%; Sharpe
   falls modestly because of re-entry turnover. Would likely clear G3.
   A candidate for a v2 construction if a Phase-A revision is sanctioned.
2. **Regime-conditional meta.** Train separate classifiers per mn_regimes
   bucket; or weight the loss function by inverse-regime-frequency so CRASH
   gets more learning signal. Predicted effect: CRASH Sharpe lifts toward 0;
   MANIA/CHOP unchanged.
3. **Add a CRASH-specific feature.** A trailing 30-candle cross-book correlation
   (ρ̄ from `mn3_crisis.c2_corr`) would let the meta detect "everything is
   falling together" and attenuate breakout signals in that state.
4. **Hard take/skip via NaN, not 0, for the cleanest LdP framing.** Replacing
   skipped signals with NaN (not 0) removes them from the rank book entirely.
   Requires a different engine call (the rank-neutral path treats NaN as
   "not a member"), and a min_members guard. Untested on this construction.

## Honest prior (set expectations)

This is the FIRST meta-labeling construction attempted in the baseline-blind
track (charter: "the strongest all-weather priors ... were NEVER tried in this
track"). A clean null on one gate (G3) is the methodology working — the
frozen-then-reveal discipline refused to tighten the throttle post-hoc. The
meta-precision-lift finding (+5.90 pp) and the regime-conditional failure
mode are themselves research outputs that the Critic can use across the
tournament.

## Files

- `analysis/portfolio/mn4_idea02_meta.py` — construction (Donchian, meta
  features, walk-forward OOF).
- `analysis/portfolio/mn4_idea02_backtest.py` — scorecard runner (filtered +
  unfiltered × 1× + 2×-GT, full IS gates).
- `tests/test_mn4_idea02_leak.py` — 4 leak checks + 2 unit tests (6/6 PASS).
- `briefs-portfolio-mn4/IDEA-02.md` — this brief.
- `diary-portfolio-mn4/IDEA-02.md` — this diary.

## Model disclosure

Opus 4.8 (Claude code-focused model). Fable was rate-limited this session;
user-directed to Opus 4.8 per the charter. No Fable artifacts were consumed
or produced.
