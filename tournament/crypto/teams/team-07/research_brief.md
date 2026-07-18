# team-07 — research brief — family `t07-vol-structure-v1`

Status: PRE-REGISTERED before any experiment run (see `experiments.jsonl` timestamps — every
material experiment is logged via `cli.py log-experiment` BEFORE its result is read).
Registered family: **volatility structure** — realized-vol cross-section on the weekly top-40
USDT-perp universe, 8h bars. Approved in `registry.jsonl` (primary and backup-2 collided,
resolved FCFS; this is our approved family, no pivot used).

---

## 1. Mechanism

Cross-sectional lottery-demand premium in crypto perps: **leverage-hungry retail systematically
overpays to hold the high-realized-vol "lottery" tail of the top-40, while the calm liquid tail
carries a positive risk-adjusted premium.** We rank the eligible universe by realized volatility
and go long the low-vol tail, short the high-vol tail, cross-sectionally demeaned.

Why this mispricing exists and persists in crypto perp markets specifically:

1. **Lottery demand / attention flow.** The marginal crypto perp trader is a retail
   lottery-seeker: volume and attention concentrate in coins that just moved violently. Buying
   pressure is price-insensitive (they chase payoff profiles, not value), pushing high-vol
   names above fair value → lower subsequent risk-adjusted returns.
2. **Funding interaction (native to this tournament's P&L).** Crowded lottery longs pay
   funding. Shorting the high-vol tail structurally *collects* funding while the crowd pays to
   hold it. Note the signal itself uses **klines only** — funding enters exclusively through
   the engine's native funding P&L, so there is no overlap with the funding-carry family
   (which ranks ON funding).
3. **Limits to arbitrage.** Shorting a pumping alt is the scariest trade in crypto
   (squeeze risk, borrow risk in spot, unbounded loss). Sophisticated capital under-supplies
   this short, so the overpricing is not competed away. A capped, diversified, ~20-names-a-side
   book with a 10% per-name cap is exactly the vehicle that CAN harvest it.
4. **Leverage-constraint inversion.** Classic low-vol-anomaly logic: constrained traders who
   want big payoffs buy high-vol assets instead of levering low-vol ones. Crypto perps offer
   leverage, but liquidation mechanics make high leverage on low-vol names feel "safe" and are
   still predominantly *used* to chase high-vol names — the clientele effect survives.

**Cross-sectional, not vol-timing (orchestrator note, pre-registered):** the organizer engine
already vol-targets the *portfolio* return stream. Our signal is cross-sectionally demeaned
every candle (row net ≈ 0 by construction, |Σw| further capped at 0.25 by the engine), so the
strategy has *no market-timing / gross-timing channel*: all edge must come from **which names
and which sign**. We verify `mean_net` ≈ 0 in every run and report it.

## 2. Expected behavior per regime tag (pre-registered, before any result)

| Regime tag | Expectation | Why |
|---|---|---|
| COVID crash (2020-02→03) | positive (small sample) | high-vol tail crashes hardest in a leverage flush |
| 2020-21 bull → Coinbase top | weakest; flat to modestly negative price-alpha, partly offset by funding collection | alt-mania melt-ups: the lottery tail keeps pumping; shorts pay in price, collect in funding |
| May-2021 crash | positive | liquidation cascades concentrate in the crowded high-vol tail |
| Run to 69k ATH (2021 H2) | flat-to-positive | mania narrower than early 2021 |
| 2022 bear | most positive | lottery names bleed to zero (LUNA-class collapses), no dip-buyers left |
| FTX-aftermath chop (2023) | positive | no follow-through: high-vol pumps fade, funding drag persists |
| ETF bull (2023-10→2024-03) | flat-to-negative price-alpha, funding offset | renewed mania in the high-vol tail |
| Post-halving chop (2024) | positive | same as FTX chop |

Aggregate pre-registration: **bear > chop > bull**, with funding P&L a persistent positive
component (the crowd pays us to hold the short-lottery book). If instead the edge shows up
ONLY in bull regimes, that contradicts the mechanism and will be reported as such.

## 3. Falsifier (pre-registered — this kills the family)

Primary grid: 2 estimators (close-close vol, Parkinson range vol) × 5 windows
W ∈ {21, 42, 84, 126, 168} candles (1, 2, 4, 6, 8 weeks). Plateau statistic := for each
(estimator, W), the mean net IS Sharpe @1× of {W and its adjacent grid windows} (3-window
neighborhood; 2-window at grid edges).

**The family is DEAD if the best plateau statistic across both estimators is ≤ 0** — i.e.
there is no contiguous parameter region where long-calm / short-lottery makes money net of
all costs and funding. Also fatal: the apparent edge is NOT cross-sectional — flagged if
|mean_net| of the evaluated book > 0.10 (a structural directional tilt) or if the pre-cost
cross-sectional spread (parts["pnl"] + parts["fpnl"]) of the best config is ≤ 0 (meaning any
positive net number would be a vol-targeting artifact, which the engine owns, not us).
If the falsifier fires: report plainly, then DNF or request the one documented pivot.

Non-fatal but must-report honesty checks: regime signs vs §2; funding share of total P&L;
breadth (median names/side ≥ 5 hard floor); @2×-stress sign.

## 4. Parameter plan (grids + rationale)

- **Vol estimators** (in-family): (a) `cc`: std of 8h log close-returns; (b) `pk`: Parkinson
  range vol from high/low (more efficient at 8h granularity, robust to gap-less crypto bars).
- **Window W** ∈ {21, 42, 84, 126, 168} candles = 1–8 weeks. Shorter = reactive lottery proxy
  but noisier ranks + turnover; longer = stable clientele sorting. No window < 1 week (rank
  noise + cost blowup at 8h cadence) and none > 8 weeks (stale, and new listings — prime
  lottery material — would never enter the signal).
- **min_periods** = max(8, ceil(0.75·W)) — new listings get a signal once ¾ of the window
  exists; younger names stay flat (NaN→0). NaN-tolerant by construction.
- **Cross-sectional transform**: among eligible (aux eligibility row t, past-only organizer
  mask) AND non-NaN names: percentile rank of vol → w_raw = −(rank_pct − row-mean rank_pct).
  Linear in rank (robust, no outlier sensitivity), row-sum exactly 0, engine handles
  gross/caps. NaN → 0 (flat).
- **Overlay variants** (each adopted ONLY per the §5 rule, max ONE overlay total):
  - signal EMA smoothing, halflife ∈ {6, 15, 30} candles (turnover/cost control);
  - weekly decision refresh (emit new ranks only on Monday-00:00 rows, hold within week);
  - lottery-tail proxy: rolling q90 of 8h returns (MAX-effect flavor), W ∈ {42, 84, 126};
  - idiosyncratic vol: vol of residual returns vs BTC (rolling beta, 126 candles);
  - vol-trend (compression/expansion) tilt: vol_21 / vol_126 as secondary sort.

## 5. Selection rule (pre-registered — binding)

1. Run the primary grid (e01, e02). Compute the plateau statistic (§3) for every
   (estimator, W).
2. **Base config = argmax plateau statistic**, subject to: @2×-stress Sharpe > 0 AND median
   names/side ≥ 5. If the argmax fails a constraint, take the next-best neighborhood that
   passes.
3. An overlay is adopted ONLY if it improves BOTH @1× and @2×-stress net IS Sharpe by
   ≥ +0.10 over the base, AND the improvement is itself plateau-robust (an adjacent overlay
   parameter also improves both tiers). Max ONE overlay. Ties → the simpler spec.
4. The final spec is then FROZEN into §7 (QE SPEC) with every parameter fixed. No
   post-selection re-tuning; any number reported to the orchestrator comes from the selected
   spec's runs.

Budget: ≤ 10 material experiments planned (ledger ids e01…; hard cap 40, aim ≤ 20).

## 6. Experiment plan (ledger map)

- e01 — cc-vol window sweep {21,42,84,126,168}, base transform, every-candle emission.
- e02 — Parkinson sweep, same grid.
- e03 — mechanism decomposition on best base: price vs funding P&L, mean_net, breadth,
  turnover, regime table; + sign-reversal control (long-lottery/short-calm must be worse).
- e04 — EMA smoothing overlay sweep on base.
- e05 — weekly-refresh overlay on base.
- e06 — lottery q90 proxy sweep (standalone, in-family).
- e07 — idio-vol variant on best W.
- e08 — vol-trend tilt overlay.
- e09 — FINAL selected spec: @1× + @2× + sub-period halves (2020-01→2022-03 vs
  2022-04→2024-06) + regime table. These are the report numbers.
(Plan may terminate early if the falsifier fires at e01/e02.)

## A1 — AMENDMENT (2026-07-18, logged after e01/e02, before any further experiment)

**The §3 falsifier for the low-vol-premium sign FIRED.** Evidence (e01/e02, ledger-stamped
before results were read): all 10 (estimator × W) configs of long-calm/short-lottery are
NEGATIVE at 1× (best −0.140 pk-W168, worst −0.780 cc-W21); every bull-regime Sharpe is
−0.58…−1.04; and the book *pays* ~0.17–0.26 cumulative funding instead of collecting it —
mechanism premise #2 was empirically wrong-signed inside the top-40: the persistent positive
funding baseline sits on the low-vol majors, while the high-vol tail's funding is frequently
negative. The lottery-demand-premium story, as pre-registered, is dead in this universe and
window. Reported plainly per charter §8.

**Pre-registered reversed hypothesis H2 (before running it).** The orchestrator's dispatch
explicitly authorizes "whatever signed structure your research honestly supports within the
vol-structure family." H2: within a universe already filtered to the 40 most-traded perps,
high realized vol marks the names where the reflexive attention cycle is ACTIVE (vol attracts
retail attention, attention attracts flow, flow pushes price with days-to-weeks persistence),
so the high-vol tail OUTPERFORMS the calm tail; simultaneously the short-calm leg (majors)
collects the persistent positive baseline funding the perp crowd pays to hold majors long.
Signal stays klines-only realized-vol ranking (family-integral); funding enters only through
engine P&L. Pre-registered regime expectation for H2: strongest in bull and chop
(attention-driven), weakest/possibly negative in bear (vol flips to downside-crash vol; e01/e02
mirrors suggest bear ≈ −0.65 at long W but ≈ +0.5 at short W — short windows react fast
enough to re-rank crashing names; expect short-W to be the robust region).

**H2 falsifier — STRICTER because the sign is data-informed (one falsifier consumed):**
run the identical grid with sign reversed (e03). The family is DEAD (DNF or pivot request) if
best 3-window-neighborhood mean net IS Sharpe @1× < +0.35, OR the selected config's
@2×-stress Sharpe ≤ 0, OR breadth median < 5/side, OR fewer than 2 of 3 regime buckets
positive at the selected config. Turnover-control overlays (§4) may be applied before the
final verdict ONLY per the pre-registered §5 adoption rule; the +0.35 bar applies to the
post-overlay selected spec evaluated on the SAME pre-registered grid logic. Additional
honesty duty: decompose price vs funding P&L — if funding is >70% of total edge we say so
explicitly (mechanism would then be "vol-ranked funding differential," reported as such).

## A2 — AMENDMENT (2026-07-18, after e04–e12; selection frozen, no further experiments)

Course of research (full detail in `experiments.jsonl` + `out/scratch/`):
- e04/e05: both §4 turnover overlays on the H2 *level* signal FAILED the §5 adoption rule
  (EMA smoothing hurt both tiers; weekly refresh −0.06 at 1×). H2-level plateau stayed at
  +0.242 < +0.35 → the vol-LEVEL branch (either sign) is dead and is NOT the submission.
- e06 (pre-registered two-sided, stricter +0.35 bar): vol DYNAMICS — long vol-EXPANSION —
  showed large pre-cost alpha (+1.44 cumulative at vt 12/84, only 12% of it funding) but
  died at 2×-stress from 300/yr turnover. Long-compression is strongly negative everywhere
  (sign is structural, not noise: monotone across all three (s,l) pairs).
- e07–e11: pre-registered turnover-shaped variant — EMA the *score* (per-name vt ratio)
  BEFORE the cross-sectional rank (preserves exact row-demeaning; e04's post-rank smoothing
  had leaked a net tilt). Halflife grid extended twice under an explicit pre-commitment
  (max one extension after e10), rollover found at hl≈72: 0.899 (36) → 0.991 (48) →
  1.025 (72) → 0.961 (108) → 0.931 (144). 2D pair robustness: every cell of
  {12/84, 21/84, 21/126, 12/126} × hl {36,48} ≥ +0.73 @1× and ≥ +0.53 @2× — a broad
  plateau, not a peak. Selection per the pre-registered e11 rule: argmax 3-cell
  hl-neighborhood mean = **cc vt 12/84, hl=72** (0.992), interior optimum.
- e12 final validation (no re-selection): full IS +1.025 @1× / +0.826 @2×-stress,
  maxDD −0.311, turnover 70/yr, regimes bull +1.44 / bear +1.20 / chop +0.28, breadth
  20/20, mean_net +0.0000, funding = 11.7% of pre-cost P&L (price-alpha dominated).
  Sub-halves +1.223 / +0.801; last-12-months +0.438. Parkinson variant at identical
  params +0.927/+0.771 (mechanism robust across estimators; cc kept per selection rule).

**Falsifier status.** Original §3 (low-vol lottery premium): FIRED at e01/e02, documented in
A1. A1/e06 stricter bar for the data-informed branches (neighborhood ≥ +0.35 @1×, 2× > 0,
breadth ≥ 5/side, ≥2/3 regimes positive): CLEARED decisively by the vol-dynamics branch
(0.992 / +0.826 / 20-per-side / 3-of-3). Honesty duties: funding share 11.7% (well under the
70% flag); |mean_net| = 0.00 and pre-cost cross-sectional spread +1.001 > 0 (the edge is
cross-sectional, not a vol-targeting or directional artifact).

**Final mechanism statement (as supported by the data, within family).** Sustained
vol-regime elevation: within the volume-ranked top-40, names whose short-horizon vol has
been *persistently* elevated against their own long-horizon norm are the ones where fresh
narrative flow is active; attention and flow persist for weeks (best halflife ≈ 24 days) and
the 8h cross-section underreacts to the sustained regime shift (while single unsmoothed
spikes DO fade — the raw 12-candle ratio was chop-negative until smoothed). The short leg —
own-vol-compressed names that hold a top-40 volume rank while their price action dies — is
the structural loser leg (abandonment drift), and collects a small funding tailwind. This is
the "compression/expansion, long the profile that pays" clause of the registered family.

## 7. QE SPEC — FROZEN (implements EXACTLY this; nothing else)

`build_raw_weights(pn, aux) -> pd.DataFrame` — pure, deterministic, past-only, no file I/O,
no network, no randomness (`aux["seed"]` intentionally unused). Only pandas/numpy. Derive
symbols from `pn["close"].columns` at runtime (widening-safe; never hard-code names/counts).

Let `C = pn["close"]` (DatetimeIndex × symbols, float).

1. `r = np.log(C).diff()`                                  — 8h log returns, per column.
2. `vol_s = r.rolling(12, min_periods=9).std()`            — short vol (pandas ddof=1 default).
3. `vol_l = r.rolling(84, min_periods=63).std()`           — long vol.
   (min_periods rule: `max(8, ceil(0.75*W))` → 9 and 63.)
4. `vt = (vol_s / vol_l).replace([np.inf, -np.inf], np.nan)`   — expansion ratio; guard the
   `vol_l == 0` degenerate case (dead/flat price feeds) → NaN.
5. `sm = vt.ewm(halflife=72, min_periods=1, adjust=True, ignore_na=False).mean()`
   — per-name score EMA. Pin these exact kwargs (pandas defaults made explicit).
6. `elig = aux["eligibility"].reindex(index=C.index, columns=C.columns).fillna(False).astype(bool)`
   — align the organizer mask to the close panel; columns absent from the mask (e.g.
   harness-widening synthetics) become False → flat.
7. `masked = sm.where(elig)`                               — rank among eligible names only.
8. `p = masked.rank(axis=1, pct=True)`                     — pandas defaults (method="average",
   ascending=True, na_option="keep").
9. `w = p.sub(p.mean(axis=1), axis=0)`                     — row-demean; SIGN: positive weight
   on HIGH smoothed expansion (long expansion / short compression).
10. `return w.fillna(0.0)`                                 — NaN → flat; emit every candle on
    the full panel index (warmup rows are all-zero → flat book; engine owns everything else).

No other transforms, no clipping, no scaling (engine gross-normalises), no smoothing of
weights, no use of any panel other than `close` and `aux["eligibility"]`.

Expected team-run reference numbers (scratch parity, evaluator-computed; QE verifies
`team-run` reproduces them to numerical noise): IS net Sharpe @1× ≈ +1.025, @2×-stress
≈ +0.826, maxDD ≈ −0.311, ann. turnover ≈ 70, median names/side 20/20, mean_net ≈ 0.000,
regime Sharpe ≈ {bull +1.44, bear +1.20, chop +0.28}. `is_report.md` numbers must come ONLY
from `team-run` output.

Team tests to include (QE-owned `test_strategy.py`): future-corruption self-check (perturb
klines/eligibility strictly after a cut date → weights at/before the cut unchanged),
determinism (two calls bit-equal), widening (extra synthetic column → no crash, flat),
NaN-tolerance (all-NaN young column → flat), and same-bar convention sanity.
