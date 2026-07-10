# DIAGNOSTIC-B — Cointegration pairs/basket stat-arb at 1h (MN track, Sketch B)

**Date:** 2026-07-10. **Role:** QR. **Script:** `analysis/portfolio/mn_diag_b_coint.py`
(committed spec = PLAN.md §2 Sketch B, FROZEN; run as registered, not adjusted).
**Data:** 1h klines per `1H-FETCH-REPORT.md` + 6 census names landed after the report
(FTM/FIL/GALA/GMT via the QE's remainder driver; NEAR/SAND fetched directly by QR — bulk,
month-incremental, 0 errors). **Trial ledger:** 1 cell (census, thresholds, windows, and
trading rules all frozen in the PLAN).

## VERDICT: SKETCH B IS DEAD

| # | Kill criterion (PLAN §2 Sketch B, verbatim) | Measured | Result |
|---|---|---|---|
| (a) | persistence ≤ 1.5× base rate (cointegration is window noise) | persist 0.125 vs base 0.120 → **ratio 1.04×** | **KILLED** |
| (b) | walk-forward post-cost convergence P&L ≤ 0 | **−88,039 bps** of gross over 2,418 trades (mean −36.4 bps/trade, t=−2.51) | **KILLED** |
| (c) | median qualifying-pair count per window < 8 | median 26.0/window | survives |

Two independent criteria fired, and the deeper one — (a) — is mechanism-level: a pair
qualifying (EG p<0.05 AND OU half-life ∈ [6h,7d]) in one 90d window carries essentially
ZERO information about qualifying in the next (12.5% conditional vs 12.0% unconditional).
Formation-window "cointegration" in this universe is window noise, exactly the failure the
PLAN pre-registered as the sketch's known killer. This is a clean kill, and a good outcome:
the census machinery answered the question decisively in one probe.

---

## 1. Census — QR's disclosed call (per 1H-FETCH-REPORT §2)

The registered text "top-30 by IS mean $-vol" is ambiguous. The fetch report's `census30`
used `nanmean` over alive candles, which ranks 33-candle late-2025 listings above 6-year
majors (7/30 names can appear in ≤2 of 24 formation windows) and includes 5 same-base
quote-variants (BTCUSDC/BTCBUSD/ETHUSDC/ETHBUSD/SOLUSDC). **QR call, fixed before any
result was computed:** top-30 by **TOTAL IS $-volume** (≡ mean over the full 6,576-candle
IS window), ex-stablecoin bases, ≥270-candle 8h history, **deduplicated by base asset**.
Rationale (also in the script docstring):

1. A census must span the quarterly windows through the WHOLE IS; mean-over-alive starves
   2020–22 (2–13 co-listed names) where most of the sample is.
2. Same-base quote-variants are the SAME underlying; their "cointegration" is a mechanical
   quote-currency basis. Including them inflates qualifying counts (kill-c) and persistence
   (kill-a) with degenerate untradeable pairs — i.e. biases the diagnostic TOWARD survival.
   Deduplication is the conservative choice.
3. Kill criteria were scored ONCE, on this census. No second census variant was run.

Census (rank order): BTC ETH SOL XRP DOGE BNB ADA 1000PEPE LINK 1000SHIB LTC AVAX ETC
MATIC DOT SUI BCH FTM FIL NEAR GMT EOS LUNA SAND GALA AXS WIF APE ATOM APT.
Theoretical pairs = 435 (matches PLAN). LUNA (UST collapse), MATIC (POL migration), EOS
(vote delist) are IN — delisting/structural death is part of the question, not censored.

## 2. Data + hole policy

- BTC 1h IS grid: 52,608 rows (2020-01-01 00:00 → 2025-12-31 23:00), 0 gaps, guard-passed
  (`mn_guard_grid`, step=1h). `mn_panel_health()` run first (8h panel OK; DEGRADED verdict
  = live-feed staleness only, irrelevant for an IS-only probe).
- The two upstream archive holes (2022-02-26→28, 72h; 2022-04-01→02, 48h) hit SOL, XRP,
  LTC, FTM, FIL, NEAR, LUNA, SAND (120h each) and GMT (48h; listed after the Feb hole).
  **Policy:** interior forward-fill ≤96h, flagged; fill never extends past a symbol's last
  raw-finite candle (no zombie prices after delist); trading DECISIONS skipped on
  hole-filled hours (frozen prices must not fabricate z-crossings); positions hold through.
  1,008 candle-values fabricated = 0.08% of the finite panel.
- Formation co-listing: ≥95% raw-finite AND 100% post-ffill coverage on both legs.
- 24 formation windows × 2160h (starts 2020-01-01 … 2025-09-01); trading window = next
  2160h block, w=23's truncated to 768h at the IS boundary. Everything strictly < 2026-01-01.

## 3. Formation census (DIAG-B step 1)

| | med | min | max |
|---|---|---|---|
| co-listed pairs/window | 312 | 3 (2020-Q1) | 406 |
| EG-pass (p<0.05)/window | 26 | 0 | 93 |
| **qualifying** (EG + HL band)/window | **26.0** | 0 | 93 |

- EG-pass rate 11.7% of co-listed pair-windows — only ~2.3× the 5% false-positive rate the
  test would produce on independent random walks, and the HL band barely bites (qualifying
  rate 11.6%; <1% of EG-passes fall outside [6h, 168h]).
- Qualifying half-life: p25=45h, med=57h (~2.4d), p75=71h (n=786 pair-windows) — the OU
  fits look economically sensible *within* the window; the problem is they don't survive it.
- Qualifying γ: med +0.95 (p5 +0.18, p95 +2.12; 2% negative). Low-γ tail matters below.
- Benign numerical footnote: statsmodels emitted divide-by-zero R² warnings in a handful of
  2025-window ADF internals (quantized low-price series); affected pairs yield NaN p →
  conservatively excluded.

## 4. Persistence (DIAG-B step 2 — the registered killer, measured directly)

Pooled over 23 window transitions, restricted to pairs co-listed in both windows:
P(qual w+1 | qual w) = 95/758 = **0.125**; unconditional base = 757/6304 = **0.120**;
**ratio 1.04×** (kill floor 1.5×). Per-transition detail is in the run log; the best single
transition (w15→16) re-qualifies 21/93, still only ~2× a base that window and the only one
above 1.5×. There is no sub-era where persistence works — 2020–22 transitions are mostly
0-for-N. **Formation-window cointegration in liquid crypto perps at 1h is not a stable
property of pairs; it is a property of windows.**

## 5. Walk-forward trading (DIAG-B step 3) — costs AND tails

2,418 trades, 23 trading windows, 346 distinct pairs. Exit mix: **52.0% stopped at |z|>4,
40.2% converged to z=0**, 7.7% expired at window end, 3 leg-death force-closes.
Holding: med 106h (p25 33h / p75 268h).

Per-trade P&L, bps of GROSS notional (fee = 15 bps/trade = 4 crossings at 7.5bps/side):

| stream | mean | median | t | win% | total |
|---|---|---|---|---|---|
| GROSS (price) | −24.20 | −208 | −1.67 | 44.4% | −58,520 |
| + funding | −21.41 | −207 | −1.48 | 44.5% | −51,769 |
| **NET (1× costs)** | **−36.41** | −222 | **−2.51** | 44.3% | **−88,039** |
| NET (2×-cost twin) | −51.41 | −237 | −3.55 | 44.1% | −124,309 |

**The strategy loses BEFORE costs.** Funding is a rounding error (+2.8 bps/trade). Costs
(36,270 bps total, 0.70× the gross loss) deepen the grave but are not the binding failure —
the registered "second question" (does 1h cost reality kill it?) is moot because the
convergence premise itself fails first.

### Tails (DIAG-D/E1 lesson: means AND tails)

- Net/trade: p1 −1,787 / p5 −1,043 / p25 −482 / med −222 / p75 +459 / p95 +1,061 bps.
- Bimodal by construction: converged trades earn +645 bps mean (n=973); stops lose −573 bps
  mean (n=1,257). **Stops are both more frequent AND nearly as large as wins — 97% of all
  losses come from stop exits.** The spread converges *sometimes* and blows out *more often*;
  this is not a convergence book with tail risk, it is a break book with occasional
  convergence.
- Worst-10 table is a structural-break gallery: 6 of 10 are WIF pairs entered 2024-06→08
  (meme decouple; γ as low as +0.05 — a "pair" that is really a naked WIF bet), plus
  AXS/LUNA 2021 and two 2025-09 AXS/APE legs. Exactly the LUNA/WIF-class narrative
  decoupling the PLAN named as the known killer.

### Regime buckets (entry-time label, frozen mn_regimes rules; occupancy 11.5/15.7/72.7%)

| bucket | n | mean net (bps) | t | win% | total |
|---|---|---|---|---|---|
| CRASH | 200 | +105.1 | +1.71 | 49.0% | +21,016 |
| MANIA | 514 | −36.3 | −1.37 | 43.6% | −18,652 |
| CHOP | 1,704 | −53.1 | −3.04 | 44.0% | −90,403 |

Mechanism-consistent texture: forced-liquidation dislocations in CRASH do mean-revert
(+105 bps, t=+1.71, n=200 — suggestive, not significant). But the book significantly LOSES
in the 73%-occupancy CHOP bucket — a stat-arb book that only works during crashes is a
crash bet wearing a convergence costume, the exact inversion of what this track needs.

### Per-year stability + contamination

Never a good year: best is 2022–23 (+14 to +21 bps mean, t<0.8); 2021 −165 (t=−1.47),
2024 −70 (t=−2.71), 2025 −80 (t=−2.28). Contamination twin (excluding 321 trades entered
2025-03→2025-12): mean −33.0 bps, t=−2.10, total −69,127 bps — **the kill does not depend
on the revealed sub-window.**

### Turnover / capacity color

105 trades/quarter, ~9.6 concurrent open trades on average, ~403 round-trips/year, implied
annual turnover ~84× of average gross — at 15 bps/round-trip this book burns ~12.6% of
gross annually in fees alone, so even a hypothetical positive-gross variant would need
>12.6%/yr of gross in convergence alpha before slippage-doubling. For the record; moot here.

## 6. Neutrality check (measured, not assumed)

- Realized trade-book hourly β_BTC = **−0.061** (se 0.003), β_ETH = −0.039 — small but
  significantly nonzero; the book is systematically SHORT the market (short-spread trades
  skew short the high-vol leg).
- Bucket-conditional β_BTC: CRASH **−0.140**, MANIA **−0.171** — G2's ±0.15 bound would
  already be violated in MANIA, at diagnostic stage, before any construction.
- Per-trade |net exposure|/gross: median 0.17, p90 0.54 (G3 bound 0.10). **EG hedge ratios
  are levels-regression ratios, not beta hedges — "beta-neutral by construction" is
  empirically FALSE for EG pairs.** Recorded as a general lesson for any future
  relative-value sketch: the cointegrating vector does not deliver the neutrality gate.

## 7. Lessons (for the track ledger)

1. **Persistence ratio 1.04× is the load-bearing number.** EG qualification at 90d/1h in
   top-liquidity crypto perps is ~89% non-repeatable — there is no stable cointegration
   structure to re-parameterize. This kills the family at the mechanism level, not the
   parameter level; a different z-threshold, half-life band, or window length would be
   re-arranging deck chairs on a signal that isn't there (and would be unledgered mining).
2. Stops = 97% of losses; break risk is not a tail on the convergence distribution, it IS
   the distribution's losing mode (52% of trades).
3. The only positive bucket is CRASH — noteworthy as mechanism texture (liquidation
   dislocations do revert) but unusable: it is the regime-bet shape this track exists to
   avoid, and n=200/t=1.71 is not evidence of an all-conditions book.
4. EG hedge ratios ≠ beta neutrality (β_MANIA −0.17, median |net exposure| 0.17×gross).
   Any future relative-value construction must hedge betas explicitly (mn_beta overlay),
   never trust the cointegrating vector.
5. Census-definition disclosure: total-IS-$-volume + base-dedup chosen a-priori and
   disclosed; the alternative (nanmean census with quote-variants) would have mechanically
   inflated both fired criteria toward survival — the kill is conservative.

## 8. Recommendation

**DEAD — do not re-register.** Both the statistical premise (persistence) and the economic
premise (post-cost, and even pre-cost, convergence P&L) failed on the registered spec;
per PLAN §6, Sketch B's lookbacks, thresholds and universe die with it. No adjust-and-
re-register path is proposed because criterion (a) leaves nothing to adjust toward.
Track state after this entry: family A banked (terminal), DIAG-D/E1 dead, **DIAG-B dead**,
DIAG-C pending OI backfill, DIAG-E Stage 2 pending the full 1h remainder fetch (per
1H-FETCH-REPORT §5 it should wait for the 361-name union; the remainder driver was at
~140/328 and healthy when this diagnostic ran).

**Reproducibility:** after a cosmetic lint/format pass on the script, a full re-run
reproduced the scored output bit-identically (modulo timing lines); raw scored log:
`diary-portfolio-mn/DIAGNOSTIC-B-run.log`.

*— QR, MN track, 2026-07-10. Kill criteria scored once, as registered; no post-hoc
re-gating. Not committed (per dispatch).*
