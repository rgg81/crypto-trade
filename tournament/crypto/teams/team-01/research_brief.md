# team-01 research brief — t01-funding-carry-xs-v1

Family (approved in `registry.jsonl`): **cross-sectional funding-rate carry** — short the
coins the crowd pays to hold long, long the coins shorts pay for, smoothed to low turnover.

Status: PRE-REGISTRATION written BEFORE any experiment was logged or run. Results and the QE
SPEC are appended at the bottom after the ledgered experiments; nothing above the "RESULTS"
line is edited afterward except typo fixes.

---

## 1. Mechanism & economic rationale

Perpetual-swap funding is the market-clearing **price of leveraged positioning**. When longs
crowd a perp, its mark trades rich to index and funding goes positive: longs literally pay a
periodic fee to stay in the trade. Persistent positive funding therefore identifies coins
with crowded, paying long bases; persistent negative funding identifies coins with crowded or
capitulating shorts.

A cross-sectional tilt **against** the funding extremes earns two aligned streams:

1. **The carry itself, mechanically.** The evaluator charges `−w · funding` natively. A short
   weight on a positive-funding coin RECEIVES that funding every candle it is held. This leg
   is a cash flow, not a fitted pattern — it cannot be overfit; only the price leg can.
2. **The positioning-unwind price leg.** Crowded-long (high-funding) names sit above a dense
   band of long-liquidation triggers; small adverse moves cascade, so their forward returns
   are negatively skewed. Crowded-short (negative-funding) names are squeeze fuel in the other
   direction. The classic empirical finding in perp markets is that the funding cross-section
   negatively predicts the return cross-section at multi-day horizons.

Why the premium persists (limits to arbitrage): harvesting it requires holding the
uncomfortable side — short the hottest coin in a mania, long the most-hated coin in a
capitulation — with liquidation risk and negative-carry-of-attention. Retail perp flow is the
structural payer (they chase, they lever, they pay funding to do so); the fee is compensation
for warehousing their crowding risk. This is a flow-driven risk premium, not an anomaly that
closes when published — it has been published for years and funding dispersion has not
collapsed.

Why it fits THIS tournament substrate specifically: funding P&L is charged natively; funding
is strongly autocorrelated so smoothed signals turn over slowly (survives 5 bps + slippage per
side at 8h cadence); the signal is defined per-name from its own funding history, so it is
column-set agnostic and survives weekly top-40 churn and unseen holdout listings; and the
funding panel covers the FULL IS window (unlike OI/ratio aux, NaN pre-2020-09), so all nine
regime windows are testable.

## 2. Expected behavior per regime tag (pre-registered)

| Window | Tag | Expectation |
|---|---|---|
| 2020-01→02-14 pre-COVID grind | bull | small positive; modest funding dispersion |
| 2020-02-14→03-13 COVID crash | bear | positive but noisy: crowded longs wiped out, negative-funding names snap back; smoothing may lag the crash itself |
| 2020-03-13→2021-04-14 bull | bull | positive carry, price leg headwind during alt melt-ups; the Jan–Apr-2021 alt mania is the classic carry-crash risk window — expect the weakest stretch here |
| 2021-04-14→07-20 May-2021 crash | bear | strongly positive: the highest-funding names crash hardest |
| 2021-07-20→11-10 run to ATH | bull | modest positive; big carry collection, some price headwind |
| 2021-11-10→2022-11-21 macro bear | bear | positive: shorts crowd, negative funding on capitulating names pays the long leg; squeeze bounces help |
| 2022-11-21→2023-10-16 FTX-aftermath chop | chop | small positive; low funding dispersion → weak signal, low turnover |
| 2023-10-16→2024-03-14 ETF bull | bull | positive carry, meme-mania price headwind late (Feb–Mar 2024) |
| 2024-03-14→07-01 post-halving chop | chop | positive; froth cooling favors the short-crowded-longs leg |

Honest summary of the expectation: carry should be **all-weather positive on average** with
its known weak spot in violent alt melt-ups (short-leg price losses can exceed collected
funding for weeks at a time). It should NOT be a one-regime wonder — that is exactly what the
falsifier tests.

## 3. Falsifier (pre-registered, binding)

The family is DEAD and I report a negative result (and either pivot or submit best-honest) if,
for the plateau-selected configuration (selection rule §5, chosen before looking at holdout —
holdout is sealed anyway):

- **F1.** Net IS Sharpe @1× costs ≤ 0; or
- **F2.** The edge is a one-regime artifact: recomputing the monthly-sum Sharpe after
  EXCLUDING the single best regime window (of the nine) yields ≤ 0; or
- **F3.** The 2×-stress tier (cost AND slippage doubled) flips the sign: stress Sharpe ≤ 0.

Additional hard validity constraints (not falsifiers, but submission blockers to fix):
median names per side ≥ 5; strategy NaN-safe and column-set agnostic.

## 4. Signal construction space (fixed a priori)

All panels: candle × symbol, 8h grid. `fund` = `aux['funding']` (per-candle summed events,
same-bar). `close` = `pn['close']`. `elig` = `aux['eligibility']`.

Fixed pipeline skeleton (order of operations is part of the pre-registration):

1. **Listed-ness mask:** `fund_m = fund.where(close.notna())` — the funding panel is
   0.0-filled where a symbol never traded; ranking raw zeros would fake "neutral funding" for
   dead/unlisted names.
2. **Smoothing:** `sm = fund_m.rolling(L, min_periods=max(2, L//3)).mean()` (variant: EWM
   halflife L). L is the primary parameter.
3. **Tradable mask:** `sm = sm.where(elig & close.notna())` — rank only within the in-force
   top-40.
4. **Cross-sectional transform** (one of):
   - `rank`: percentile rank per row, centered on the row mean → linear L/S book, breadth
     ~20/side;
   - `topk`: equal-weight short the k highest-funding names, long the k lowest, k per side;
   - `z`: row z-score winsorized at ±2.5.
   Sign: **weight = −transform** (short high funding, long low/negative funding).
5. **Optional inverse-vol sizing:** divide by per-name realized vol (63-candle std of close
   returns, min_periods 21, same-bar) before normalization.
6. **Optional weight smoothing:** causal EWM (span S) over the weight rows, applied after
   masking, to cut turnover.
7. Hand raw signed weights to the engine (it re-masks, gross-normalizes, caps, lags, costs,
   charges funding, vol-targets).

## 5. Parameter grid & selection rule (pre-registered)

| Axis | Grid | Rationale |
|---|---|---|
| Smoothing window L (candles) | 7, 14, 21, 42, 63, 84, 126 | 2.3d → 6wk; funding autocorrelation horizon unknown a priori; costs favor longer |
| Smoother | rolling mean vs EWM halflife | responsiveness vs stability |
| Transform | rank / topk (k ∈ {5, 8, 10, 13}) / z | breadth-vs-concentration of the carry spread |
| Weight EWM span S | 1 (none), 3, 5, 9, 15 | turnover control |
| Inverse-vol sizing | off / on | risk allocation, not mechanism |

Budget: ≤ 14 ledgered experiments intended (hard tournament cap 40). Sweeps along one axis are
ONE ledgered experiment each (config lists the grid).

**Selection rule (locked before results):** greedy one-axis-at-a-time from the baseline
(L=21, mean, rank, S=1, vol-off), in the order L → smoother → transform → S → vol-sizing.
On each axis pick the **center of the widest contiguous plateau** whose Sharpe@1× is within
~10–15% of the axis maximum — never an isolated peak; explicit tie-breaks: lower annualized
turnover, then higher 2×-stress Sharpe. A step is adopted only if its plateau center beats the
incumbent by more than +0.10 Sharpe (below that = noise at 54 monthly points; keep the simpler
incumbent). Final candidate must re-verify: breadth ≥ 5/side, F2, F3, and a neighbor-perturb
check (each parameter ±1 grid step stays within ~15% of candidate Sharpe).

The Sharpe noise floor at 54 monthly points is ≈ 0.5 annualized — differences below ~0.3 are
statistically meaningless; the plateau rule exists to stop me from harvesting that noise.

## 6. Experiment plan (maps to `experiments.jsonl` ids)

- e01 — baseline sanity: L=21 mean, rank, S=1, vol-off. Headline + turnover + breadth.
- e02 — L sweep {7,14,21,42,63,84,126}, everything else baseline.
- e03 — smoother: EWM halflife at the L-plateau center vs rolling mean.
- e04 — transform: rank vs topk k∈{5,8,10,13} vs z, at chosen L/smoother.
- e05 — weight-smoothing span S sweep {1,3,5,9,15}.
- e06 — inverse-vol sizing on/off.
- e07 — final-candidate deep check: 2×-stress, funding-off attribution (carry vs price-leg
  split), 9-window regime table, exclude-best-window Sharpe (F2), split-half consistency.
- e08 — neighbor-perturbation plateau check on the final joint configuration.
- (reserve e09+ for surprises; hard stop at 14 unless something is genuinely broken.)

---

# RESULTS (appended after ledgered experiments — nothing above this line edited)

12 experiments logged (e01–e12, evaluator-stamped in `experiments.jsonl`; budget 12/40).
All scratch numbers below were computed with the evaluator's own `net_series`/`evaluate`
(1× and 2×-stress tiers) inside `out/scratch/carrylib.py`; the canonical numbers for
`is_report.md` will come from `team-run` after the QE builds `strategy.py`.

## Headline — selected configuration

Signal: funding EWM (halflife 2 candles) → centered cross-sectional percentile rank
(negated) → inverse-vol sizing (63-candle realized vol) → causal weight EWM (span 2).

| Metric (IS 2020-01-01 → 2024-06-30) | @1× | @2×-stress |
|---|---|---|
| Net Sharpe (monthly, √12) | **2.407** | **1.702** |
| Max drawdown | −0.242 | −0.258 |
| Ann. turnover | 188× | — |
| Median names long/short | 20 / 20 | — |
| Total funding P&L (raw-net units) | +0.713 | — |
| Total cost (raw-net units) | −0.531 | — |
| Monthly hit rate | 75.9% (54 months) | — |
| Price-leg-only Sharpe (funding P&L off) | 1.514 | — |

Attribution: BOTH legs contribute — the mechanical carry stream adds ≈ +0.9 Sharpe on top
of a positive price leg (crowding-unwind). This is exactly the pre-registered mechanism.

## Falsifier verdicts (pre-registered §3)

- **F1** net IS Sharpe @1× = 2.407 > 0 → PASS.
- **F2** Sharpe excluding the best regime window (COVID crash, +7.22) = **2.332** > 0 → PASS
  (edge is not a one-regime artifact; 8 of 9 windows positive).
- **F3** 2×-stress Sharpe = 1.702 > 0 → PASS.
- Breadth: 20/20 median names per side (floor 5) → PASS.

## Nine-window regime table (final config, @1×)

| Window | Tag | Sharpe | vs pre-registered expectation |
|---|---|---|---|
| 2020-01 pre-COVID | bull | +3.73 | better than expected |
| 2020-02 COVID crash | bear | +7.22 | better (fresh signal reacts fast; the L=21 baseline had −2.71 here — smoothing lag was real, as pre-registered) |
| 2020-03→2021-04 bull | bull | +3.75 | better (carry-crash risk absorbed by breadth + inverse-vol) |
| 2021-04 May crash | bear | +4.16 | as expected (strongly positive) |
| 2021-07→11 run to ATH | bull | +3.90 | as expected |
| 2021-11→2022-11 macro bear | bear | +1.49 | as expected (positive, thinner) |
| 2022-11→2023-10 FTX chop | chop | +1.18 | as expected (small positive) |
| 2023-10→2024-03 ETF bull | bull | +2.80 | better than expected |
| 2024-03→07 post-halving chop | chop | **−0.63** | worse — the ONLY negative window, and the most recent one |

Yearly Sharpe: 2020 = 3.56, 2021 = 3.32, 2022 = 2.44, 2023 = 1.35, 2024H1 = 0.68.
Split-half (2022-04 split): first half 3.49, second half 1.44.

## Honest generalization assessment

The alpha COMPRESSES over the sample: funding dispersion shrank after the 2022
deleveraging, and the yearly Sharpe declines monotonically. The last 3.5 IS months are
negative (−0.63). I expect holdout Sharpe well below the IS 2.4 — the right mental model is
the late-sample run-rate (≈ 0.7–1.4), not the full-IS number. The mechanical carry leg and
the all-weather window profile are why I still believe expectancy is positive out of sample.
This is reported plainly per charter §8.

## Experiment log summary (full detail in `experiments.jsonl` + `out/scratch/`)

- e01 baseline L=21/rank: 1.388 @1× — mechanism confirmed, but stale.
- e02 L sweep {7..126}: monotone — alpha lives in RECENT funding; L≥42 dead late-sample.
- e03 L ext {2,3,5} + stress: 1× max at L=2 (2.295); stress max at L=7 (1.38); plateau {2..7}.
- e04 EWM halflife {2,3,5,7,14}: at matched turnover EWM ≥ rolling mean on 1×/2×/h2.
- e05 weight-EWM span sweep on 3 bases: smoothing trades 1× for stress; freshest keeps best
  late-half Sharpe.
- e06 transform axis: centered rank DOMINATES top/bottom-k and winsorized z everywhere
  (carry premium is spread across the cross-section; concentration adds noise).
- e07 inverse-vol sizing: +0.34 Sharpe on the smoothed base (adopted); hurts the unsmoothed
  book's stress (interaction documented).
- e08 boundary + neighbors: L=1 raw-funding book fails stress (0.19/−0.79) at 736×/yr
  turnover → the fresh-signal trend does NOT extend to the boundary; plateau is real.
  vol_win axis flat (42/63/84 within 0.03).
- e09 joint (h,S) map: broad 7-cell plateau h∈{1,2}×S∈{1,2,3}(+{1,5}), all ≥ 2.29 @1×.
- e10 final deep check: table above; F1/F2/F3 pass.
- e11 vn ablation at final: vn off → 2.014/−0.424 maxDD/h2 0.64 → vn=on confirmed.
- e12 spec equivalence: standalone widening-safe implementation bit-identical
  (max |Δw| = 0.0; Sharpe 2.40675 @1×, 1.70226 @2×), widening smoke clean, pandas 3.0.0.

## Selection-rule application & documented deviations

1. **Grid extension (e03):** e02's optimum sat at the pre-registered grid edge (L=7), so I
   extended the L axis downward {2,3,5} — logged before running, same axis, same family.
2. **Axis order:** pre-registered L → smoother → transform → S → vol; actually executed
   L → smoother → S → transform → vol (S before transform). No selection consequence:
   rank won the transform axis under both bases tested.
3. **Plateau-center tie-break judgment:** the 4-cell center block of the (h,S) plateau is
   {(1,2),(1,3),(2,2),(2,3)}. The literal turnover-first tie-break picks (2,3)
   (turn 164); I selected **(2,2)** (turn 188) because it dominates (2,3) on 1× Sharpe
   (2.407 vs 2.288), 2×-stress (1.702 vs 1.675 — the stress maximum of the entire map),
   late-half Sharpe (1.44 vs 1.28), and maxDD, while giving up only 13% turnover. All four
   cells are far inside the ±0.3 noise band; I explicitly did NOT take the raw 1× peak
   ((1,3) = 2.452). Judgment documented here per discipline.

---

# QE SPEC — t01-funding-carry-xs-v1 (final, frozen by QR)

The QE implements EXACTLY this. No research, no re-tuning, no added parameters. The
reference implementation below was verified bit-identical to the ledgered final candidate
(e12) and produces, through the evaluator at 1×: **Sharpe 2.40675, maxDD −0.24155,
ann_turnover 188.36, total_return 37.666, 20/20 median names, mean_gross 0.99354,
mean_net 0.01883, funding P&L +0.71347, cost 0.53143, 54 months**; at 2×-stress:
**Sharpe 1.70226**. `team-run` must reproduce these to float precision; treat any deviation
as an implementation bug, not a tuning opportunity.

## strategy.py — reference implementation (verbatim)

```python
import numpy as np
import pandas as pd

HALFLIFE = 2.0        # candles — funding EWM halflife
MIN_FUND_OBS = 2      # min funding observations before a name gets a signal
VOL_WIN = 63          # candles — realized-vol window for inverse-vol sizing
VOL_MIN_PERIODS = 21  # min obs for the vol estimate (younger names stay flat)
WEIGHT_SPAN = 2       # causal EWM span over weight rows (turnover damping)


def build_raw_weights(pn, aux):
    close = pn["close"]
    cols, idx = close.columns, close.index

    # --- defensive alignment (widening-safe; no-op on the real panels) ---
    fund = aux["funding"].reindex(index=idx, columns=cols)
    elig = aux["eligibility"].reindex(index=idx, columns=cols)
    elig = elig.astype("boolean").fillna(False).astype(bool)

    alive = close.notna()          # listed-and-trading mask
    mask = elig & alive            # tradable: in-force top-40 AND alive

    # --- signal: smoothed same-bar funding (past-only: ewm over rows <= t) ---
    fund_m = fund.where(alive)     # funding panel is 0.0-filled where never listed
    sm = fund_m.ewm(halflife=HALFLIFE, min_periods=MIN_FUND_OBS,
                    adjust=True, ignore_na=False).mean()
    sm = sm.where(mask)

    # --- cross-sectional transform: centered percentile rank, negated ---
    r = sm.rank(axis=1, pct=True)            # ascending, average ties, NaN excluded
    w = -(r.sub(r.mean(axis=1), axis=0))     # short high funding, long low/negative

    # --- inverse-vol sizing ---
    vol = close.pct_change(fill_method=None).rolling(
        VOL_WIN, min_periods=VOL_MIN_PERIODS).std(ddof=1)
    w = w.div(vol.replace(0.0, np.nan))
    w = w.replace([np.inf, -np.inf], np.nan)

    # --- mask, flatten NaN, damp turnover, re-mask ---
    w = w.where(mask, 0.0).fillna(0.0)
    w = w.ewm(span=WEIGHT_SPAN, adjust=True, ignore_na=False).mean()
    w = w.where(mask, 0.0)
    return w
```

## Binding implementation notes

1. **Order of operations is load-bearing.** Mask → smooth → mask → rank → vol-divide →
   zero-fill → weight-EWM → re-mask. Do not reorder; the weight-EWM must run on the
   zero-filled masked book (its decay through zeros is intentional), and the final re-mask
   must NOT be followed by another fillna (there are no NaNs left; verified).
2. **Pandas semantics pinned** (venv has pandas 3.0.0 / numpy 2.2.6): `ewm(adjust=True,
   ignore_na=False)` (the defaults, stated explicitly); `rank(axis=1, pct=True)` default
   average-tie ascending; `pct_change(fill_method=None)`; `std(ddof=1)`. The
   `astype("boolean").fillna(False).astype(bool)` chain normalizes eligibility after a
   widening reindex (object/NaN-safe).
3. **NaN rules.** Funding is 0.0-filled by the engine where a symbol never traded — the
   `where(alive)` mask is what prevents dead/unlisted names from faking neutral funding.
   Names with < 2 funding candles, < 21 return observations, or zero/NaN vol are flat by
   construction. All-NaN synthetic columns produce all-zero weights (verified e12).
4. **Column-set agnostic:** every operation derives columns/index from `pn["close"]` at
   runtime; aux panels are reindexed onto them. No symbol literals anywhere.
5. **Determinism:** no randomness — `aux["seed"]` is intentionally unused. Pure function of
   its arguments; no I/O, no imports beyond numpy/pandas (stdlib math allowed; scipy and
   teamlib not needed).
6. **Same-bar legality:** row t uses funding/close/eligibility of rows ≤ t only (ewm/rolling
   are causal; rank is row-wise). The engine applies the `.shift(1)` decision lag itself —
   do NOT pre-shift anything.
7. **team tests (test_strategy.py)** must include at minimum: (a) future-corruption
   self-check — mutate pn/aux rows strictly after a cutoff T, assert weights on rows ≤ T
   are unchanged (np.allclose with tight atol); (b) determinism — two calls on copies are
   `.equals()`-identical; (c) widening — extra synthetic column in pn (and separately in
   aux) neither crashes nor changes real columns, per e12; (d) NaN tolerance — an all-NaN
   column stays all-zero in the output; (e) output shape/index/columns match `pn["close"]`.
8. **Expected `team-run` cross-check numbers** are listed at the top of this spec; the
   breadth floor (median 20/20 vs required 5) and both cost tiers must appear in
   `is_report.md` from `out/is_metrics.json` ONLY.
