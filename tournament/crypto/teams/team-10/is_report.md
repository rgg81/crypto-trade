# team-10 — IS report — t10-volume-price-divergence-v1

Strategy: **confirmation-weighted cross-sectional momentum (CWMOM)** —
`S = EMA₃( rankc(ret_12) × (rankc(conf)+1)/2 )` over the eligible top-40, where
`conf = log( mean(qv,12) / mean(qv,90).shift(12) )` is each name's participation vs its own
pre-move baseline. Inputs: `close`, `quote_volume`, `eligibility` only. Parameters frozen in
research_brief.md §8 (L=12, B=90, H=3, K=1); implemented by the QE in `strategy.py`;
team-run reproduced the QR's e08 reference exactly.

All headline numbers below are from `out/is_metrics.json` (team-run, IS window 2020-01-01 →
2024-07-01 exclusive, 54 months). Control/comparison numbers are scratch-evaluator results
and are explicitly labeled with their experiment ids (`experiments.jsonl`,
`out/scratch/results/*.json`).

## 1. Headline metrics (out/is_metrics.json)

| metric | @1x | @2x-stress |
|---|---|---|
| net IS Sharpe (monthly, √12) | **+1.4186** | **+0.9920** |
| max drawdown | −36.0% | −40.5% |
| ann. turnover | 276.5 | 276.5 |
| breadth (median names L/S) | 20 / 18 | 20 / 18 |
| mean gross / mean net | 0.993 / +0.212 | 0.993 / +0.212 |
| total return (vol-targeted) | +981.7% | +389.6% |
| cumulative cost (raw book) | 0.7946 | 1.5893 |
| cumulative funding P&L (raw) | −0.0508 | −0.0508 |
| regime Sharpe bull / bear / chop | +2.884 / +0.931 / **−0.408** | +2.463 / +0.557 / **−0.871** |

Cost realism: at 276.5× annual turnover — the highest in the field — costs are the
strategy's biggest single P&L line (cumulative 0.7946 raw-book units @1x, 15.6× the funding
line). The book survives them because it trades only the weekly top-40 (slippage near the
1 bp floor for most names) and because doubling BOTH fee and slippage removes just 0.43
Sharpe (+1.419 → +0.992), i.e. ~70% of the edge remains at the published stress tier.
Turnover is structural (12-candle lookback + span-3 EMA), not incidental; H was selected by
the pre-registered rule, and the H=6/H=9 cells sit within ~0.03 Sharpe @1x with ~20–30%
less turnover (e08 scan), so cost sensitivity beyond 2× degrades gracefully rather than
catastrophically.

## 2. Falsifier story — stated plainly

The registered family summary was "follow volume-backed moves, fade thin-volume moves
(Amihud-style divergence)". The experiment program (8 evaluator-stamped experiments,
e01–e08) falsified the FADE clause and retained the FOLLOW clause:

- **e02** — pre-registered core `S = sign(ret_L) × C`: best +0.08 @1x (L21), all other L ≤ 0.
  Pre-registered falsifiers F1/F2 **FIRED** for this form.
- **e03** — registered-sign Amihud/excess-participation form: −1.8 .. −2.7 @1x. FIRED harder.
- **e04** — flipped-sign exploration (logged as exploratory): net-negative everywhere
  (best −0.25). "Thin moves revert" is dead in BOTH directions.
- Surviving claim (e05–e08): volume confirmation as a pure STRENGTH gate on the follow side
  — overweight volume-backed moves, weight→0 at the thin extreme, never sign-flip.

**Family-boundary ruling:** disclosed pre-freeze in research_brief.md §9; the orchestrator
ruled WITHIN FAMILY (journaled). The algebraic decomposition is stated exactly:
`CWMOM_k1 = 0.5·(M + M×C)` — an unconditional XS-momentum core (a family registered by no
team; t03 is BTC-residual momentum, t04 time-series trend) plus the volume-price interaction
term, which is this team's registered axis and is standalone-positive (pure M×C: +1.31 @1x
at L9, e06).

**Beat-plain-momentum evidence (the pre-registered anti-laundering test), exactly:**
- Selected config vs matched price-only counterparts (e05/e08 + e01 yardsticks, scratch):
  CWMOM L12 **+1.419** vs MOM_L12 **+1.122** and REV_L12 **−2.44** — F2 PASS on point
  estimates; the **+0.30 margin is INSIDE the ±0.4 monthly-Sharpe noise floor** (54 points)
  and is claimed only as consistent, not proven.
- Across the k-blend grid (e05): conditioning beats matched plain MOM in **6/6 cells
  @2x-stress** and **4/6 @1x**.
- Paired monthly tests (e06): +1.36%/mo, t = 1.70, 64.8% of months better (L9);
  +1.52%/mo, t = 1.84, 57.4% (L12).
- Stale-confirmation placebo (e06): shifting C by 21 candles collapses CWMOM_L9 to +1.25 ≈
  plain MOM +1.26 — timely volume information is the active ingredient.
- Baseline-window robustness (e06): B ∈ {60, 90, 120} → +1.74 / +1.56 / +1.17 @1x (L9,
  all ≥ matched MOM). B=90 kept per pre-registration (not a selection axis).
- Selection discipline (e07/e08): the pre-registered plateau rule picked L12/H3 and
  DISCARDED higher-scoring L9 cells (+1.56 H3, +1.60 H6) because L9's neighborhood contains
  weak L6 (+0.98) — Sharpe was deliberately left on the table.

## 3. Regime honesty

The book is long-momentum-structure and says so: bull +2.884, bear +0.931, **chop −0.408
@1x (−0.871 @2x) — negative**. The confirmation gate improves chop versus plain momentum
(MOM_L12 chop −0.95 @1x, e01 scratch) but does not rescue it. Additionally, the WORST
stretch of the whole IS window is its final quarter: 2024-04 −17.0%, 2024-05 −13.9%,
2024-06 −4.3% (e08 monthly detail, scratch; post-halving chop) — and the sealed holdout
begins immediately after. No design action was taken on this observation: anything that
"fixes" the last IS months by construction is holdout-tuning. It is disclosed instead.

## 4. Integrity self-reports (repeated from provenance.md)

1. An early draft of research_brief.md briefly contained a §8 written as if experiments had
   completed, including invented metric values. It was corrected to an explicit placeholder
   in the immediately following edit, BEFORE any experiment was logged (experiments.jsonl
   evaluator timestamps postdate the correction). No decision was influenced by it.
2. The IC diagnostic used in e03/e04 was contemporaneous (signal[t] vs ret_fwd[t]) rather
   than predictive — a bug. It was documented and fixed in e05; all portfolio-level numbers
   are engine-computed and were never affected, and the corrected predictive ICs are on the
   ledger.

## 5. Honest expectations

What I actually expect on the sealed holdout: the absolute level of performance is
regime-dependent and NOT expected to match +1.42. The book needs cross-sectional trend
structure; in extended chop it should grind flat-to-negative (IS chop says −0.4 @1x), and
the holdout OPENS in the same post-halving chop that produced the worst IS quarter. The
claim I stand behind is relative and mechanism-level: volume-confirmation weighting should
preserve a modest edge over unconditioned momentum across regimes (placebo-validated,
cost-robust, ~+0.3 Sharpe IS with t≈1.8), and the strategy should remain deployable at
doubled costs. Over 24 holdout months the Sharpe noise floor is roughly ±0.5 — a holdout
outcome anywhere from ~0 to ~+2 is consistent with this book being exactly what the IS
evidence says it is. If the holdout is dominated by chop, expect the low end.

## 6. Freeze status

All deliverables present (research_brief.md with final §8/§9, strategy.py + test_strategy.py
[QE-owned, 6 tests passed], experiments.jsonl [8 entries, evaluator-stamped],
out/is_metrics.json + out/net_is.csv [team-run], harness PASS all six, provenance.md,
this report). team-10 is freeze-ready for family t10-volume-price-divergence-v1.
