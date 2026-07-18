# team-06 IS report — t06-ls-ratio-contrarian-v1

Strategy: fade per-coin positioning extremes in the Binance global long/short account
ratio (`ls_accounts`): per-coin rolling z of the log ratio (W=90 candles, min_periods=45,
clip ±3), fade sign, EMA span 3, centered cross-sectional rank over eligible names.
Frozen spec: research_brief.md §10. Harness: PASS (all six); team tests: 5 passed.

**Number provenance:** every number in §1, §3, §4, §5 is from `out/is_metrics.json` /
`out/net_is.csv` (team-run). Numbers explicitly labeled *[scratch, ledger eNN]* are from
the evaluator-API scratch runs recorded in `experiments.jsonl`; they exist because the
official window cannot express honest-window quantities (see §2).

## 1. Headline (official IS window 2020-01-01 → 2024-06-30, 54 monthly points)

| tier | net Sharpe | maxDD | ann. turnover | med names L/S | total return |
|---|---|---|---|---|---|
| 1× | **+1.1757** | −32.6% | 93.8 | 20 / 20 | +182.0% |
| 2×-stress | **+0.7437** | −40.1% | 93.8 | 20 / 20 | +78.9% |

Breadth floor (median ≥ 5 names/side): passed with wide margin (20/20).

## 2. DATA AMENDMENT — read before interpreting anything above (e01, ledgered)

The four positioning-ratio aux panels are **zero-corrupted through 2022**: only BTC has
data 2020-09 → 2021-11 (cross-sectionally useless), and in 2022 85–100% of eligible cells
are exact zeros in most months (missing 5-min archive rows summed to 0). Clean 40-name
coverage exists only from mid-Dec-2022. Consequences:

- **Honest window: 2023-01-13 → 2024-06-30 (~17.6 months).** Only 21 of the 54 official
  months carry a live book (18 honest-window months + 3 corrupt-coverage "island" months:
  2021-12 +12.7%, 2022-06 +4.3%, 2022-12 −1.0%). The other 33 months are structurally
  flat zeros.
- The official 54-month Sharpe is therefore **diluted ≈ 0.58×** versus the live run-rate:
  honest-window Sharpe ≈ 1.60 @1× / ≈ 0.77 @2× *[scratch, ledger e05/e09]*.
- The 2022 bear regime is untestable for this family on this substrate (pre-registered
  falsifier was re-anchored to the honest window BEFORE any signal experiment; brief §2/§11.1).

## 3. Per-regime Sharpe — with population caveat

Official regime buckets (computed over all 54 months, i.e. INCLUDING flat months):

| regime class | @1× | @2× | actually populated by live signal? |
|---|---|---|---|
| bull | 1.385 | 1.270 | partially — live only in ETF bull (2023-10 → 2024-03) |
| bear | 1.024 | 0.961 | **effectively no** — only 2 live months (2021-12, 2022-06), both corrupt-coverage islands; the rest zeros. Treat as anecdote, not evidence |
| chop | 0.952 | **0.113** | yes — FTX-aftermath chop (from 2023-01-13) + post-halving chop |

Honest-window regime split *[scratch, ledger e09]*: bull 4.23 (6 months) vs chop 0.52
(14 months); H1-2023 (post-FTX participation trough) +0.41 @1× / **−0.51 @2×**, H2
(ETF bull + post-halving) +2.92 @1× / +2.13 @2×. **The edge as measured is materially
bull/participation-concentrated**; the 2×-tier chop figure (0.113) is the weakest
honest number and is stated here deliberately. 12/18 honest-window months positive
(monthly values in out/net_is.csv).

## 4. Funding & costs

Total funding P&L **+0.0701** (both tiers; funding is not scaled by the stress multiplier)
vs total cost 0.2576 @1× / 0.5152 @2×. The pre-registered funding-tailwind property holds:
the fade side of the crowded book collects funding on net. Turnover 93.8×/yr is the
EMA-smoothed plateau-center config; the cost bridge from 1× to 2× (−0.26 of return,
Sharpe 1.18 → 0.74) is the honest measure of cost sensitivity.

## 5. Book shape

mean_gross 1.0, mean_net ≈ 0 (engine-capped, effectively market-neutral), 54 scored months,
maxDD −32.6% @1× occurring within the live window (flat months cannot draw down).

## 6. Honest expectations for the holdout (2024-07-01 → 2026-06-30)

- **Coverage reverses in our favor:** the ratio panels have full 40-name coverage from
  2023 onward, so all 24 holdout months should carry a live book — the effective forward
  sample is RICHER than IS (24 live months vs 18 honest + 3 junk). The IS→holdout
  comparison for this team is run-rate vs diluted-official: the right IS anchor for
  forward expectation is the honest-window rate, not the headline 1.18.
- **Run-rate expectation:** center ≈ +0.8 to +1.2 @1× — between the chop-only floor
  (≈ 0.5 *[scratch, e09]*) and the honest-window rate (≈ 1.60), because the holdout
  likely mixes high-participation and low-participation phases. @2× expect ≈ 0.4–0.8.
- **Surprise bands (24 monthly points, Sharpe SE ≈ 0.9):** anything in roughly
  [−0.7, +2.7] @1× is statistically compatible with the IS estimate; a negative holdout
  Sharpe alone would NOT falsify the mechanism at this sample size, and > +2.5 should be
  read as luck, not skill. Mechanism-consistent failure mode to watch: a prolonged
  retail-participation trough (2023-H1 analogue) → chop-floor behavior, weakest at 2×.
- Known unhedged exposure: no bear-regime evidence. If the holdout contains a 2022-style
  liquidation bear, this strategy's behavior there is genuinely unknown (islands hint
  positive but are data-quality-unreliable).

## 7. Falsifier status

NOT fired (pre-registered §7 of research_brief.md): the honest-window plateau
{45,90}×{1,3,6} is positive at 1× in every cell with no sign flips, and 2×-stress > 0
everywhere on the plateau *[scratch, e02–e05]*. Selection followed the pre-registered
plateau-center rule (a higher-point peak at W=45 was NOT selected). Ledger: 10/40
experiments, no resets.
