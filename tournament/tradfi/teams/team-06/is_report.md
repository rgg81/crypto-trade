# team-06 IS report — CANONICAL (post-team-run)

STATUS: CANONICAL. All Part-B numbers below are the frozen-spec `strategy.py` output produced by
`cli.py team-run --team team-06` and read from `out/is_metrics.json` (@1× and @2× cost). The QE
implemented `strategy.py` from the frozen spec (research_brief.md §P7); team-run reproduces the
QR scratch results exp-038 (@1×) and exp-040 (@2×) **bit-for-bit** (same evaluator, same inputs):
Sharpe +0.7388 @1× / +0.6393 @2×, maxDD −0.2298, ann. turnover 18.13×, breadth 22/27, total
return +3.443. Leak-proofing harness (`cli.py audit --team team-06`): PASS on all five checks
(static-scan, determinism, truncated-replay, future-corruption, same-bar; 11 truncation cuts).
The QR-authored Part A (retired sector-pairs family) is preserved verbatim.

## Part A — t06-sector-pairs-coint-v1: FALSIFIED (retired family)

Sector-pairs cointegration stat-arb produced **zero positive configurations in 18 pre-registered
backtests** (Sharpe@1× −1.11..−0.16). Decisive forensics: best breadth-valid book at ZERO cost
= −0.098 (gross alpha absent, exp-021); sign-flip diagnostic also negative (−0.326, exp-022) —
no unconditional edge in either spread direction on this Tech/Semi-heavy secular-divergence
universe. All three pre-registered falsifier prongs fired; the family was retired and the
single documented pivot exercised (reg-024). Details: research_brief.md §8, ledger exp-003..023.

## Part B — t06-vix-regime-books-v1 (pivot, family #7): SELECTED STRATEGY

Mechanism: calm VIX state → cross-sectional 12-1 momentum book; deep-stress VIX state
(trailing 504d percentile ≥ 0.85, hysteresis exit at 0.70) → 10d cross-sectional reversal book;
EMA(halflife 3) smoothing on the composite. Full frozen spec: research_brief.md §P7.

### Selected configuration (COMBO B, exp-038 / exp-040)

| Metric | @1× cost | @2× cost |
|---|---|---|
| Net IS Sharpe (monthly, √12) | **0.739** | **0.639** |
| Max drawdown | −0.230 | −0.234 |
| Annual turnover | 18.1× | 18.1× |
| Median names long / short | 22 / 27 | 22 / 27 |
| Total return (2010→2024H1) | +3.44 | +2.55 |
| Regime Sharpe bull / bear / chop | +0.63 / +0.41 / +1.28 | +0.55 / +0.17 / +1.19 |

Breadth floor (≥5/side): passed with 4×+ margin. Selection by the pre-registered rule
max min(Sharpe@1×, @2×): COMBO B 0.639 > COMBO A 0.631; lower-turnover tiebreak also → B.

### The switch is load-bearing (family-fidelity evidence)

| Book | Sharpe@1× | bear-regime Sharpe |
|---|---|---|
| Unconditional momentum (REF, exp-025) | +0.49 | −1.75 |
| Unconditional reversal (REF, exp-026) | −0.79 | −0.16 |
| Conditional composite (exp-038) | **+0.74** | **+0.41** |

The composite exceeds the best unconditional ingredient by +0.25 Sharpe (pre-registered
fidelity margin: +0.10) and removes the momentum-crash bear signature entirely. The alpha
claim is the state-conditionality, not either inner book — consistent with the registered
family mechanism (regime-conditional BOOK, not a VIX exposure gate).

### Robustness / plateau (research_brief.md §P6 table)

Deep-stress thresholds dominate loose ones (0.85/0.7 → +0.67 raw vs 0.7/0.5 → +0.16); EMA-3
smoothing cuts turnover ~60% and raises net Sharpe; percentile state beats absolute VIX levels;
252d/504d percentile windows both positive (756d weak). Sampled one-step neighbours of the
selected point retain 79–101% of its Sharpe with the same sign. Caveat disclosed: the 40-line
experiment cap was reached, so not every neighbour of COMBO B itself was run; the sampled
surface in the selected region is smooth and everywhere-positive.

### Experiment accounting

Ledger: 40 / 40 lines (3 registrations, 1 census, 31 material backtests, 5 diagnostics across
both families). Every line appended before its result was read. Pre-registered predictions
confirmed: banded pairs book breadth failure (exp-005), pairs chop-best regime, momentum bear
crash (exp-025), composite > references (exp-027+).
