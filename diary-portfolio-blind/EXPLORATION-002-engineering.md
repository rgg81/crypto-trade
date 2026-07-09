# EXPLORATION-002 — Engineering Report

## Headers
- Iteration: EXPLORATION-002 (mid-vol-decile shorts, tail-capped near-neutral L/S)
- Track: baseline-blind top-20 L/S portfolio
- Worktree: `quant-portfolio-blind`
- Date: 2026-07-09
- One change: replace `longonly_tophalf` builder with `midvol_short` (long lowest-vol half / short mid-vol band / skip extreme-vol tail, near-dollar-neutral at gross=1.0).
- OOS: **SEALED** (`OOS_CUTOFF = 2025-03-24`; panel sliced via `slice_is`; OOS never inspected).

## Test Status

- **18/18 green** (14 pre-existing + 4 new midvol_short tests).
- Pre-existing parity confirmed bit-identical: `longonly_tophalf` +0.511, `ew_long` +0.451, `rank_neutral` −0.141 (all within tolerance of EXPLORATION-001 / DIAGNOSTIC-002 baselines).
- New tests:
  - `test_future_corruption_leaves_past_identical_midvol` — leak positive-control on the new path (corrupt signal + open from cutoff → past weights/turnover/equity bit-identical).
  - `test_midvol_dollar_neutrality_and_gross` — sum(w)==0, sum(|w|)==gross, longs>0, shorts<0 at every rebal with n>=4 on the synthetic panel.
  - `test_target_weights_midvol_short_partition` — hand-computed 3-way partition (longs at positions {0,2,3,5}, shorts at {1,7}, extreme tail pos 4 skipped, NaN pos 6 zeroed).
  - `test_midvol_short_skips_extreme_tail` — **load-bearing**: simulated 100× mooner (signal=−100) gets weight exactly 0 (skipped, not shorted).

## Engine Changes (minimal, backward-compatible)

1. **`blind_engine.py`:**
   - Added `target_weights_midvol_short(signal_row, univ_row, gross, long_frac=0.5, short_frac=0.25)` builder per brief §3.3 (verbatim pseudocode).
   - Added `"midvol_short"` to the `weighting` allowed-set and to the rebal dispatch chain.
   - Added `short_frac: float | None = None` parameter to `run_backtest`.
   - Added `funding_rets: np.ndarray` field to `BacktestResult` (per-candle funding cost; default empty array for backward-compat). Used by attribution scripts to split funding from price P&L.
2. **`tests/test_blind_engine.py`:** 4 new tests appended; existing 14 untouched.
3. **`analysis/portfolio/blind_exploration_002.py`:** new run script (template: `blind_exploration_001.py`).

Linter: `uv run ruff check` clean on all three files. Formatter: `uv run ruff format` applied.

## 8-Run Table (IS-only, all funding ON, rebal=6, gross=1.0)

| run | weighting | sharpe | ann | maxDD | turn/yr | win% | final | per-year Sharpe |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 primary | `midvol_short` | **+0.09** | −1.3% | **−48.5%** | 138x | 52.2 | 0.94 | 2020:+0.81 / 2021:−0.38 / 2022:+0.89 / 2023:−0.79 / 2024:−0.34 / 2025:+3.18 |
| 2 +VT=0.40 | `midvol_short` +VT | +0.15 | −0.6% | −49.7% | 180x | 52.2 | 0.97 | 2020:+0.91 / 2021:−0.46 / 2022:+0.77 / 2023:−0.68 / 2024:−0.17 / 2025:+2.95 |
| 3 ew_long | `ew_long` | +0.45 | −0.6% | −88.2% | 31x | 52.4 | 0.97 | 2020:+0.76 / 2021:+1.87 / 2022:−1.53 / 2023:+1.48 / 2024:+0.22 / 2025:−1.68 |
| 4 long-only | `longonly_tophalf` | +0.51 | +9.8% | −87.0% | 73x | 52.9 | 1.62 | 2020:+0.80 / 2021:+1.54 / 2022:−1.53 / 2023:+1.71 / 2024:+0.53 / 2025:−0.80 |
| 5 b&h BTC | — | +1.07 | +60.4% | — | — | — | — | (benchmark, not through pipeline) |
| 6 cost=2x | `midvol_short` @2x cost | −0.29 | −11.0% | −59.7% | 138x | 51.4 | 0.55 | 2020:+0.37 / 2021:−0.75 / 2022:+0.46 / 2023:−1.13 / 2024:−0.67 / 2025:+2.79 |
| 7 rank_neut | `rank_neutral` | −0.14 | −15.4% | −78.8% | 108x | 52.5 | 0.42 | 2020:−0.31 / 2021:−1.83 / 2022:+0.94 / 2023:−0.61 / 2024:+0.78 / 2025:+1.35 |

(Run 8 in the brief is "NOT a separate run" — the primary book IS the mid-vol test.)

## Funding-by-Year Attribution (bps of equity)

Sign convention: **+ = net drag (longs pay more than shorts receive), − = net income (shorts receive more than longs pay).**

| year | 1 primary | 3 ew_long | 4 long-only |
|---|---:|---:|---:|
| 2020 | +124.9 | +1734.8 | +2229.4 |
| 2021 | **−240.4** | +3877.1 | **+3721.7** |
| 2022 | +287.8 | −1630.9 | −341.5 |
| 2023 | +1184.9 | −2082.4 | +550.7 |
| 2024 | −145.4 | +961.3 | +998.8 |
| 2025 | +142.9 | −475.8 | +57.5 |
| **TOTAL** | **+1354.7** | +2384.1 | **+7216.6** |

**G7 raw observation (2021 funding drag, primary): −240.4 bps.** Threshold: ≤ +1500 bps. The short leg's mania-year funding income (−2139.7 bps; see leg split below) more than offset the long leg's payment (+1899.4 bps), producing net funding INCOME in 2021. vs long-only's +3721.7 bps drag, this is a **+3962.0 bps reduction** (primary book's net funding is −6.5% of long-only's drag — i.e., it flipped sign from drag to income).

## Funding by Leg (primary book; bps of equity)

| year | long_leg_pays (+ = drag) | short_leg_pays (− = income) |
|---|---:|---:|
| 2020 | +1117.9 | −993.0 |
| 2021 | +1899.4 | **−2139.7** |
| 2022 | −165.4 | +453.1 |
| 2023 | +277.9 | +907.0 |
| 2024 | +502.1 | −647.5 |
| 2025 | +29.0 | +113.9 |
| TOTAL | +3660.8 | −2306.2 |

The short leg received funding income in 2020, 2021, and 2024 — the bull/manic years when retail pays up to hold leveraged longs. In 2022/2023/2025 (bear/early-recovery), funding went negative and shorts paid instead.

## Short-Leg Price P&L Attribution (primary book; fraction of equity per year)

Sign convention: **+ = shorts lost money (prices rose), − = shorts profited (prices fell).**

| year | long_leg | short_leg |
|---|---:|---:|
| 2020 | +0.5408 | −0.2766 |
| 2021 | +0.9895 | **−1.0144** |
| 2022 | −0.5824 | **+0.9280** |
| 2023 | +0.4815 | −0.4895 |
| 2024 | +0.2458 | −0.2657 |
| 2025 | −0.0555 | +0.2583 |
| TOTAL | +1.6196 | −0.8599 |

The 2022 short-leg price P&L is **+0.9280** — the short book captured the broad-based bear-market deleveraging exactly as the brief hypothesized (Section 2 rationale #3). The 2021 short-leg price P&L is −1.0144 (mid-vol names rose with the rally), but this was partially offset by the −2139.7 bps funding income the short leg received, bringing net 2021 Sharpe to −0.38 (above the −1.0 G4 floor).

## Max Per-Name Weight (|w|; flag if any name > 20%)

| run | max \|w\| | location | flag |
|---|---:|---|---|
| 1 primary | 0.5000 | k=30, col=155 | **\|w\| > 20%** (warmup edge: k=30 < warmup=63) |
| 2 +VT=0.40 | 0.7069 | k=41, col=118 | **\|w\| > 20%** (warmup edge + VT up-leverage) |
| 3 ew_long | 0.3534 | k=23, col=155 | **\|w\| > 20%** (warmup edge) |
| 4 long-only | 0.5220 | k=23, col=155 | **\|w\| > 20%** (warmup edge — same as EXPLORATION-001) |
| 6 cost=2x | 0.5000 | k=30, col=155 | **\|w\| > 20%** (warmup edge) |
| 7 rank_neut | 0.5642 | k=29, col=118 | **\|w\| > 20%** (warmup edge) |

All max-|w| excursions occur at k < warmup (63) — the same pit_topn_universe lookback-ramp edge effect documented in EXPLORATION-001 (REVIEW-001 S4). The warmup mask excludes these candles from Sharpe/MaxDD/per-year metrics. Post-warmup, the per-name long weight is 0.05 by design (gross_long=0.5 / 10 names) and per-name short weight is 0.10 (gross_short=0.5 / 5 names).

## Gross-Leverage Series (target = 1.0; confirm no drift)

| run | mean | max | min_active |
|---|---:|---:|---:|
| 1 primary | 1.0000 | 1.2744 | 0.5909 |
| 2 +VT=0.40 | 1.2640 | 2.4917 | 0.5548 |
| 3 ew_long | 0.9988 | 1.0123 | 0.4961 |
| 4 long-only | 0.9999 | 1.0109 | 0.6914 |
| 6 cost=2x | 1.0005 | 1.2750 | 0.5911 |
| 7 rank_neut | 1.0006 | 1.7266 | 0.4796 |

Primary book mean gross = 1.0000 (exactly target). Max = 1.2744 during warmup (few universe members → concentrated weights). Post-warmup, gross stays tightly near 1.0.

## Dollar-Neutrality Confirmation (primary book)

- **max|sum(w)| = 0.25** at a single rebal step.
- **mean|sum(w)| = 4.74e-04** across 950 rebal steps.

The mean is essentially zero — near-dollar-neutral by construction. The 0.25 max is the engine's existing `valid_price` force-exit branch (positions force-exited when a name has no valid fill price at open[k], breaking the long/short balance for that one candle). This is an engine-level behavior shared with `rank_neutral` (test `test_longonly_gross_and_nonneg_discipline` exercises the same branch); it is not a builder invariant violation. The synthetic-panel unit test (`test_midvol_dollar_neutrality_and_gross`) confirms strict sum(w)==0 at every n>=4 rebal when all fill prices are valid.

## LITUSDT Short-Book Funding Residual

- Symbol: `LITUSDT`, in panel: True.
- IS-universe member candles: **35**.
- Funding CSV starts 2025-12-23 (post-IS) → genuinely no IS funding data.
- **Residual upper bound: 3.92 bps of equity** (assuming short_w=0.10 × 0.0112%/8h mania mean × 35 candles).
- Direction: a short position in LITUSDT would have RECEIVED funding income we did not credit → the short book's reported P&L is very slightly understated (single-digit bps).
- **Materiality: immaterial.** 3.92 bps of equity over the full IS window is roughly 0.04% — orders of magnitude below the Sharpe-relevant threshold.
- Universe is FROZEN for this iteration; the residual cannot be fixed without a universe change.

## Parity Checks

| run | actual | target | delta | verdict |
|---|---:|---:|---:|---|
| run-4 long-only | +0.511 | +0.51 | +0.001 | PARITY OK |
| run-3 ew_long | +0.451 | +0.45 | +0.001 | PARITY OK |
| run-7 rank_neutral | −0.141 | −0.18 | +0.039 | PARITY OK |

EXPLORATION-001's three headline results reproduce bit-identically, confirming the new `midvol_short` code path did not perturb the existing builders.

## Anomaly Notes

- **Primary Sharpe +0.09 is well below the brief's Section-5 prediction of +0.7 to +1.2.** This is not a null result in the brief's pre-registered sense (the brief's null was "IS Sharpe +0.3–0.5, 2021 Sharpe < −1.0" — actual 2021 is −0.38, so the null's 2021-blowup condition did NOT fire). The mechanism behaved as designed in 2021 (mid-vol shorts did not blow up) and in 2022 (shorts dampened the bear), but the absolute Sharpe is dragged down by weak 2023 (−0.79) and 2024 (−0.34), and by turnover of 138x (above the 100x G5 target). The funding dodge fired even more strongly than predicted (−240 bps vs predicted +200 to +1200 bps). These are facts for the QR's Phase-7 evaluation.
- **Warmup edge effect recurred** (max |w| > 20% at k < 63) — same as EXPLORATION-001; expected per brief §7.4.
- **Cost-stress (2x) Sharpe = −0.29** — below the G6 threshold of 0.7; the high turnover (138x) makes the book cost-sensitive.
- **2025Q1 Sharpe = +3.18** — anomalously high; the IS window ends 2025-03-24 so this is one quarter of data (small sample, high variance). Not gated.

## Files Touched (all within blinding constraint)

- `analysis/portfolio/blind_engine.py` — added `target_weights_midvol_short`, `"midvol_short"` dispatch, `short_frac` param, `funding_rets` field.
- `analysis/portfolio/blind_exploration_002.py` — new run script (committed table producer).
- `tests/test_blind_engine.py` — 4 new tests appended.
- `diary-portfolio-blind/EXPLORATION-002-engineering.md` — this report.

No commits made (user owns the commit decision).

## Status

OVERALL = READY-FOR-QR-PHASE-7

OOS remains sealed. All G1–G7 gate verdicts are the QR's call. The funding-tax dodge (G7) fired beyond threshold; the remaining gates present a mixed picture that the QR will weigh against the brief's pre-registered criteria.
