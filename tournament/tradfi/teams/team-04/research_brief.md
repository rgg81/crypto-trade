# team-04 research brief — t04-xs-momentum-12-1-v1 (FINAL SPEC for QE)

Family (approved): **Cross-sectional momentum, 12-1 class** — plain CS momentum, registered in
`registry.jsonl` after the redraw round. This brief is the single, complete, unambiguous
specification the QE implements in `strategy.py`. Nothing here is left to QE judgment.

## 1. Economic mechanism

Relative winners over a ~12-month horizon keep winning: firm-level information diffuses
slowly and performance-chasing flows reinforce relative drift (Jegadeesh-Titman lineage).
On this panel (65 US mega-cap single-stock perps, 2010-2024), the anomaly's classic
"skip the last month" refinement adds nothing — short-horizon reversal is weak in modern
large caps — so the final signal is the plain trailing 252-day return (skip=0; margin
documented in exp-010/exp-024). The mechanism, expected regime behavior, and falsifier are
unchanged from the registration.

## 2. FINAL SPECIFICATION (exact; no degrees of freedom)

Interface: `build_raw_weights(pn, aux) -> pd.DataFrame` per the charter. `pn` keys used:
`close` ONLY. `aux` is UNUSED (no vix, no sector_map; `seed` unused — the strategy is
deterministic; rank ties are broken by `method="first"` i.e. panel column order).
Derive tickers from `pn['close'].columns` at runtime. No file I/O, no network, no
subprocess, numpy/pandas only.

Transform order (daily, same-bar decisions; the engine applies the `.shift(1)`):

1. **Signal** — let `close` be the raw close panel (dates x tickers) and
   `C = close.ffill()` (causal forward-fill; past values only):

   `mom[t, i] = C[t, i] / C[t - 252 rows, i] - 1.0`     (skip = 0, formation = 252 rows)

   Implemented as `mom = C / C.shift(252) - 1.0`. Rows are panel trading days.
2. **Eligibility** — name i is eligible at t iff `close[t, i]` is not NaN (a real bar
   today) AND `mom[t, i]` is finite (implies >= 252 panel rows since the name's first bar).
   Ineligible names take no weight at t (0), and are excluded from ranking.
3. **Rank** — among eligible names: `rank = mom.where(elig).rank(axis=1, method="first")`
   ascending (rank 1 = worst momentum). `N[t]` = number of eligible names at t.
4. **Hysteresis membership** (stateful loop over rows, state = previous day's long/short
   member sets, both initialized EMPTY at the first panel row):
   - `n_in[t] = floor(0.20 * N[t])`, `n_stay[t] = floor(0.35 * N[t])`.
   - If `n_in[t] < 5` or `N[t] <= 0`: row is FLAT (all zeros) and BOTH member sets reset
     to empty; continue to next row.
   - Long set at t: names with `rank > N - n_in` (fresh entry) UNION names that were long
     members at t-1 AND have `rank > N - n_stay` (retained). Only names with a finite rank
     at t can be members (a member with no bar today drops out).
   - Short set at t: names with `rank <= n_in` UNION prior short members with
     `rank <= n_stay`. Same finite-rank requirement.
   - A name qualifying for BOTH sets at t is removed from BOTH.
   - If after the above either side has fewer than 5 members: row is FLAT and both member
     sets reset to empty. Otherwise the sets become the new state.
5. **Weights** — `+1.0 / n_long` for each long member, `-1.0 / n_short` for each short
   member, `0.0` elsewhere. Return the full dates x tickers float DataFrame (zeros where
   flat — the engine treats NaN and 0 identically here, but emit 0.0 for cleanliness).

Fixed parameters (chosen values with plateau evidence in §3):

| parameter | value | swept range | evidence |
|---|---|---|---|
| formation | 252 rows | 126 / 189 / 252 | exp-001..009, exp-022 (see FLAG §4) |
| skip | 0 rows | 0 / 10 / 21 | exp-010/011 (grid), exp-024 (final arch.) |
| tail fraction q_in | 0.20 | 0.15 / 0.20 / 0.25 / 0.30 / 0.40 | exp-001..009, 019, 020 |
| stay fraction q_stay | 0.35 | (q_in + 0.15 band) | exp-015 vs exp-014/016/021 |
| min names per side | 5 | fixed a priori | charter breadth floor |
| weighting | equal-weight tails | rank-linear, vol-scaled tested | exp-012/013 (both worse) |

## 3. Expected IS metrics (evaluator output, exp-023 confirmation run)

From `te.run_is` on the exact spec above (QE's `team-run` must reproduce these):

- **Sharpe 0.5245 @1x cost, 0.4713 @2x cost** (monthly-summed, sqrt-12-annualized)
- maxDD **-0.2335** (1x), -0.2394 (2x); total return +174.9% over IS; n_months 174
- annual turnover **8.48** (vs ~26 without hysteresis — the overlay is load-bearing)
- breadth: median **12 long / 12 short**; mean gross 1.0; mean net ~0 (dollar-balanced)
- regime Sharpe: bull **+0.75**, bear **-1.14**, chop **+0.47**
- yearly Sharpe (1x): 2011 -0.31, 2012 0.51, 2013 1.54, 2014 1.17, 2015 0.67, 2016 0.56,
  2017 0.26, 2018 0.47, 2019 -0.33, 2020 0.95, 2021 1.28, 2022 0.80, 2023 -0.02, 2024 0.78
  (11 of 14 full years positive)

## 4. Honest flags (report as-is; do not gate away)

- **Bear-regime exposure (-1.14)**: the family's documented momentum-crash profile. The
  engine's 63d vol-target and net cap damp it; we do NOT add regime gates (bear-gated
  overlays are RESERVED; regime-switching books are not our family). Documented, accepted.
- **Formation-axis sensitivity**: on the final architecture F=189 scores 0.249 vs 0.525
  at F=252 (exp-022) — the formation axis is a gradient, not a flat plateau. F=252 is kept
  because it is the canonical 12-month formation, pre-registered as the family's central
  case at registration time (before any data was read), and the daily-recompute grid
  (exp-001..009) shows the same monotone preference for 252 at every tail width.
- **Skip=0 vs registration phrasing**: the registration's mechanism summary described the
  classic ~1-month skip. The skip was swept with pre-registered hypotheses (exp-010: the
  skip hypothesis was FALSIFIED — skip=0 0.516 vs skip=21 0.433 daily; exp-024 confirms on
  the final architecture: 0.395 skip=21 vs 0.525 skip=0). Mechanism class is unchanged
  (cross-sectional ranking of trailing ~12-month returns); skip is a swept parameter
  inside the registered family, decided by ledgered evidence, not silently.
- Tail-width plateau is genuine: q_in 0.20 -> 0.525, 0.25 -> 0.508, falloff at 0.15
  (0.460) and 0.30+ (<=0.30 daily). Overlay choice is phase-free by design: hold-21d
  showed rebalance-phase luck (exp-021: phase sweep mean 0.532, std 0.084, min 0.353);
  hysteresis matches the phase-agnostic mean without a calendar anchor.

## 5. QE implementation notes

- Stateful membership loop over rows is required (numpy loop over 3646 rows is fine).
- Do NOT read files, do NOT import beyond numpy/pandas/stdlib-math, no randomness.
- Truncated-replay equivalence holds by construction: state at t depends only on rows
  <= t. Confirm with the harness; the ffill and shift are the only lookback operators.
- Emit weights on the full panel grid (index = pn['close'].index, columns =
  pn['close'].columns), float dtype, zeros when flat.
- Include a future-corruption self-check in test_strategy.py (perturb rows > T, assert
  weights at <= T unchanged) and a determinism check (two calls, identical output).
- Reference implementation to translate (do not import from it):
  `out/scratch/scratch_explore_f.py` — `hysteresis_weights(252, 0, 0.20, 0.35)`.
