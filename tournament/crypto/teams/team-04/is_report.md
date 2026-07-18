# team-04 IS report — t04-ts-trend-v2 (per-name multi-horizon time-series trend)

All official numbers below are from `out/is_metrics.json` as produced by
`cli.py team-run --team team-04` (window 2020-01-01 → 2024-07-01 exclusive, 54 monthly
points). Auxiliary honesty diagnostics that do not exist in `is_metrics.json` are explicitly
marked SCRATCH with their experiment-ledger id (`experiments.jsonl`, evaluator-stamped).

## 1. Headline (official, out/is_metrics.json)

| Metric | 1x costs | 2x-stress (taker AND slippage doubled) |
|---|---|---|
| **Net IS Sharpe** (monthly, √12) | **+1.609** | **+1.316** |
| Max drawdown | −37.3% | −44.0% |
| Total return (vol-targeted stream) | +790.4% | +475.5% |
| Ann. turnover (Σ|Δw|·1095) | 125.43 | 125.43 |
| Total cost paid (pre-vol-target) | 0.3561 | 0.7121 |
| Total funding P&L (pre-vol-target) | +0.0651 | +0.0651 |
| Months | 54 | 54 |

Book shape (official): mean gross 0.815, mean net +0.019 (market-neutral-ish under the
0.25 net cap), median names long/short = **18 / 17** vs the ≥5/side floor — passed with
wide margin; the volume-ranked top-40 keeps genuine shorts alive in every regime.

## 2. Per-regime Sharpe (official)

| Regime | @1x | @2x |
|---|---|---|
| bull | +2.548 | +2.294 |
| bear | +1.020 | +0.773 |
| chop | +0.063 | −0.235 |

The chop-bleed thesis pre-registered in the brief (section 2) is confirmed and stated
plainly: the strategy earns its Sharpe in directional regimes (bull AND bear — it is not a
long-only bull artifact) and approximately breaks even in chop at 1x, bleeding mildly in
chop under 2x stress. The worst IS stretch is the FTX-aftermath chop (2023-02..04), which
is where the −37.3% maxDD lives.

Funding share: funding contributed +0.0651 (pre-vol-target) — a mild structural CREDIT
(collected mostly in chop/bear), contrary to the pre-registered drag expectation.
SCRATCH e12: canonical book funding-off Sharpe +1.556 vs +1.609 — funding is not
load-bearing.

## 3. Anchor-gap adjudication (spec owner statement)

Official team-run numbers sit ~1% below the brief's scratch anchors (+1.609 vs +1.624;
+1.316 vs +1.336) while every structural metric matches to rounding. Cause identified
exactly (SCRATCH e12, closed-loop):

- `strategy.py` step 7 accumulates the horizon-presence counter as BOOL frames
  (`cnt = present if cnt is None else cnt + present`); pandas/numpy bool addition is
  logical OR, so `cnt` saturates at 1 and `sig = num / cnt` becomes the **SUM over
  available horizons** rather than the NaN-skipping MEAN written in QE-SPEC step 7.
- Verified: an explicit sum-semantics rebuild in scratch is **bit-identical** to
  `strategy.py`'s output (max abs diff 0.0), and scoring it reproduces the official
  metrics exactly (+1.609 / +1.316, funding +0.0651, turnover 125.4).
- Why the effect is tiny: sum and mean differ per cell by a factor equal to the number of
  available horizons; the engine's gross-normalization absorbs that factor whenever it is
  uniform across the row (most candles), leaving only a mild tilt toward full-history
  names on mixed rows — hence identical structure and a 0.015 Sharpe drift, far inside
  the 54-month noise floor.

Ruling applied (orchestrator): the frozen `strategy.py` stands unmodified and its
sum-over-available-horizons semantics is CANONICAL; the brief's section 8 carries a
marked adjudication note recording the intended-mean vs implemented-sum deviation. Both
variants are members of the same robustness plateau (mean variant: +1.624/+1.336,
SCRATCH e10); nothing was tuned in response to this finding.

## 4. Pre-registered honesty caveat — front-loaded edge (mandatory)

The edge is front-loaded, family-wide (every plateau member shows the same shape,
SCRATCH e11). For the canonical book (SCRATCH e12):

- Split-half Sharpe: **+2.643** (2020-01..2022-03) vs **+0.773** (2022-04..2024-06).
- Calendar years: 2020 +2.756, 2021 +3.047, 2022 +0.399, 2023 +1.216, 2024H1 −0.100.

Trend was simply stronger in 2020-21 than in 2022-24 across the entire pre-registered
parameter space. e11 verified the selected config is the CLUSTER'S BEST on the recent
half — the tie-break did not launder a 2020-21 artifact — but a realistic forward
expectation is nearer the recent-half level (~+0.7…+0.8) than the 54-month aggregate
(+1.609). No recency-targeted tuning was attempted.

## 5. Falsifier status

DOES NOT FIRE. Pre-registered falsifier: Sharpe ≤ 0 across the 21-126-candle plateau, or
all positive P&L in the 2020-21 bull with 2022 bear + both chops jointly strongly
negative. Measured: plateau-wide positive Sharpe (e02-e09); official bear-tag +1.020,
calendar-2022 +0.399 (SCRATCH e12), chop +0.063 — a genuine two-sided trend harvest.

## 6. Ledger & harness

Experiments e01-e12 (12 of 40; e12 = adjudication forensics, no tuning). Harness: PASS
all six checks; `test_strategy.py` 5 passed. One pivot budget unused. No holdout contact.
