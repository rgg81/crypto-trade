# REVIEW-001 — Critic Integrity Audit of EXPLORATION-001 (baseline-blind top-20 L/S track)

**Reviewer:** Quant Critic (read-only, tools: Read/Glob/Grep). **Date:** 2026-07-09.
**Scope:** Result INTEGRITY only. The QR owns the MERGE verdict (G1–G6). The Critic owns
"are these numbers trustworthy." (Persisted by orchestrator — Critic cannot write files.)

## OVERALL INTEGRITY VERDICT: CONDITIONAL-PASS

The headline numbers (+0.56 Sharpe, −87% MaxDD, +7216bps funding drag, parity with
DIAGNOSTIC-002 −0.18) are **trustworthy in direction and approximate magnitude**. The primary
book's metrics are clean. However, there is **one confirmed silent funding-accounting bug**
(SHIBUSDT symbol mismatch) that biases the G2 apples-to-apples comparison, **two coverage gaps
in the leak positive-controls** (funding + universe paths untested), and **one statistical
caveat** (the +0.054 G2 delta is inside noise). None change the qualitative finding (long-only
pays a real funding tax; the low-vol tilt does not meaningfully beat EW). They must be fixed
before any CONFIRMATION-style belief, and the SHIB fix is a prerequisite for any short-book work.

## Per-Area Findings (ranked by severity)

### [S1 — MEDIUM/HIGH] Silent funding symbol mismatch: SHIBUSDT klines vs 1000SHIBUSDT funding
**The bug (confirmed by direct file inspection).**
- `data/SHIBUSDT/8h.csv` EXISTS (klines start 2021-05-10).
- `data/funding_rates/SHIBUSDT.csv` DOES NOT EXIST.
- `data/funding_rates/1000SHIBUSDT.csv` EXISTS (Binance lists the perp under the 1000x-scaled
  symbol for sub-$1 coins; the RATE is scale-invariant).
- `blind_funding.py`: `p = FR_DIR / f"{s}.csv"` looks up the panel symbol verbatim. For
  `s="SHIBUSDT"` the file is absent → `except` swallows it → column stays `np.zeros` →
  `fund[:, ~present] = np.nan` → engine masks via `np.isfinite(f)` → **zero funding cost on
  every SHIB position**.

**Why it matters.** SHIB entered the PIT top-20 within ~10 candles of its 2021-05-10 listing.
The EW-top-20 benchmark (run 3) holds SHIB long; the rank-neutral L/S (run 6) shorts SHIB.
Sampled `1000SHIBUSDT.csv`: May-2021 −0.0075 (shorts pay longs ~0.75%/8h), Oct-2021 +0.0005 to
+0.0014 (longs pay). At 5% EW weight, +0.001/8h ≈ 5.5%/yr drag from SHIB alone. Cumulative EW
understatement ~100–300 bps over IS. **The primary book does NOT hold SHIB** (high-vol →
excluded from `longonly_tophalf`), so primary's +7216 bps funding is clean; the EW number is
mis-stated → the +0.054 Sharpe delta is unreliable in its second decimal.

**Failure scenario if uncaught.** A future short-book EXPLORATION shorts high-vol names. Every
1000x-scaled perp (SHIB, and historically BONK/PEPE/FLOKI under unscaled symbols) silently pays
zero funding → systematic subsidy to the short leg inflating reported short-side alpha. Compounds
with every new low-price listing.

**Required fix (blocking for EXPLORATION-002).** Symbol-resolution map in `load_funding`:
```python
_FUNDING_SYMBOL_MAP = {"SHIBUSDT": "1000SHIBUSDT", "BONKUSDT": "1000BONKUSDT", ...}
lookup = _FUNDING_SYMBOL_MAP.get(s, s)
p = FR_DIR / f"{lookup}.csv"
if not p.exists(): p = FR_DIR / f"{s}.csv"  # fallback
```
After `load_funding`, assert every IS universe member has `present[j]` — fail loud if any is NaN.

### [S2 — MEDIUM] Funding path has ZERO positive-control test coverage
`grep funding tests/test_blind_engine.py` → no matches. Both leak positive-controls use default
`funding_enable=False`. Bucketing, sign, alignment verified by MANUAL review only — correct today
but unprotected against future regressions. Confirmed correct now:
- Bucketing `k = searchsorted(grid, ft, "left") - 1`: for `ft = grid[k+1]` returns bucket k ✓
  (right-closed `(grid[k], grid[k+1]]` = hold window open[k]→open[k+1]).
- `<= T-2` bound: candle T-1 has no `open[T]` (engine `break`s); excluding it is correct ✓.
- Sign: `cost_fund = (w_eff * f).sum(); r = gross_pnl - cost_fund`. Long(w>0)×pos→drag ✓;
  Short(w<0)×pos→gain ✓.
- Multi-cadence: `np.add.at` accumulates all settlements in a hold; 4h/1h handled exactly ✓.
**Required fix.** 3 new tests: (a) settlement at `fundingTime=open_time[k+1]` bucketed to k;
(b) synthetic long with `f=+0.001` → `cost_fund>0`, equity < f=0 case; (c) corrupt future funding
→ past weights/turnover/equity bit-identical.

### [S3 — MEDIUM] The +0.054 G2 Sharpe delta is inside noise
IS = 5727 candles, rebal=6 → ~954 rebal decisions. Naive Sharpe SE ≈ `sqrt((1+0.5·S²)/N) ≈ 0.034`,
but 8h hold-period returns overlap (6-candle holds → serial correlation) → effective N ~6× smaller
→ SE ≈ 0.05–0.08. Observed +0.054 is ~1 sigma. **Primary does not meaningfully beat EW-top-20.**
Stats caveat, not a bug. QR may MERGE on other grounds (funding-tax finding is the real signal)
but must NOT claim a "+0.054 edge."

### [S4 — LOW] k=23 warmup edge: max per-name weight 0.52
Real but non-driving. `pit_topn_universe` lookback=30/min_periods=10 → first ~10–30 candles have
few valid members → 50–100% per-name weight. Equity at k=23 ≈ 1.0, immaterial to a 5727-candle
curve. **The −87% MaxDD is a 2022 regime event (Luna/3AC/FTX; majors −70–90%), NOT this artifact.**
The brief's predicted −35% to −50% was too optimistic. **Fix (recommended):** warmup mask — skip
first `max(lookback,30)` candles in `_metrics`, or start equity at `equity[30]=1.0`.

### [S5 — LOW] Funding docstring imprecise
`blind_funding.py`: "every settlement ... known by open[k]" is technically wrong (rate finalized
near settle time, not open[k]). **Not a leak** — funding is a COST applied to a held position, not
a decision input; decision (weights from `signal[k-1]`) doesn't consult funding. Reword to:
"funding[k] is the actual settled cost of holding over candle k; not a decision input, so its
timing doesn't create look-ahead."

### [S6 — LOW] Production universe path not covered by leak positive-control
Leak tests pass a FIXED `univ`. Production `pit_topn_universe` uses `quote_volume.rolling(30).rank`
— past-only by construction, so leak-safe, but the automated proof doesn't cover it. Add a test
that corrupts future `quote_volume` and asserts past universe membership bit-identical.

## Leak-Safety Verdict (mandatory positive-control review)
The two leak tests are **meaningful for what they test** (corrupt signal+fill forward; assert
weights/turnover/equity bit-identical). Catches signal look-ahead, fill-price look-ahead,
vol-target look-ahead, equity-compounding leaks. **No path where future data leaks into a
DECISION was found** — all signal/universe/vol-target use strictly trailing windows. Funding
"leak" concern is moot (funding is a cost, not a decision).

## Cost Realism & Apples-to-Apples
- Taker 5bps + slip 2.5bps one-way — fair for top-20 liquid perps at research AUM.
- Turnover `mean(|w_tgt−w_eff|)×1095`, zeros included — correct (73x primary, 31x EW).
- Cost `turn × cost_side` one-way — correct (not double-counting round-trip).
- EW through identical pipeline — YES, except SHIB funding asymmetry (S1) → G2 delta unreliable.

## Pre-Registration / No-Tuning-on-Result
Brief FROZEN (Section 0). `rebal=6` inherited from DIAGNOSTIC-002 sanity (mild selection, not on
this iteration's gates); `long_frac=0.5` parameter-free; cost honest Binance rates; signal_window=12
from IC screen; vol_target=0.40 standard Carver. **No parameter chosen with hindsight to pass a
gate.** OOS is the real arbiter (sealed). ✓

## Survivorship / Selection
- All coins with ≥200 candles loaded (delisted-with-klines included; list-and-delisted-before-download missing — standard Binance-vision limit).
- PIT top-20 by trailing $-volume, re-ranked — no look-ahead, but adverse-selected (pump→enter→dump). Punishes shorts; mitigated on long-low-vol side. 289 IS members = high churn.
- 1000x-scaling data issue (S1) = silent selection: kline-symbol ≠ funding-symbol coins get free funding.

## Path Forward for EXPLORATION-002 (constructive)
Verified finding is economically sharp: **long-only pays ~12%/yr funding tax (pro-cyclical, +37%
in 2021); dollar-neutral dodges it but eats short tails (−1.83 in 2021).** Three axes, each a
different family than "drop the short book":
1. **Mid-vol-decile shorts (tail-capped L/S)** [risk-primitive/weighting] — short ranks 11–15 only,
   never 16–20 (lottery mooners). Long bottom-10. Principled cutoff (IC monotone midpoint), pre-registerable.
2. **Signal-proportional weighting + short-vol-floor cap** [weighting] — `w ∝ |signal|`; zero-out
   names above 90th cross-sectional-vol pctile before proportional weighting. Continuous tail-cap.
3. **Regime-aware gross scalar (defensive, NOT a signal gate)** [risk-primitive] — IC is positive in
   mania (+0.068 in 2021), do NOT flatten; scale GROSS by BTC-90d-realized-vol pctile OR
   cross-sectional-dispersion pctile, de-risk when both legs adverse (the 2022 correlated deleveraging
   → −87% MaxDD). Addresses G3/G4 without touching the signal.
**Prerequisite for all three:** fix SHIB symbol-resolution (S1) before any short-book EXPLORATION.
