# iter-011 BRIEF — pivot toward a MULTI-FACTOR market-neutral book

**Date:** 2026-07-01 · **Track:** portfolio-tradfi · **Role:** Quant Researcher
**Cadence:** EXPLORATION / research + probe (IS-only, `< OOS_CUTOFF 2025-03-24`; **OOS HIDDEN** — no `--confirm`, no OOS number computed)
**Raised bar (user):** net **IS Sharpe ≥ 0.50 AND positive EVERY calendar year 2010-2025**.
**Base:** iter-006 momentum book, net **+0.28** (bull +0.30 / bear −0.24 / chop +0.51).
**Sources of truth:** `analysis/portfolio/tradfi/iter_011_probe.py` (all numbers below). Reproduce: `uv run python analysis/portfolio/tradfi/iter_011_probe.py`.

---

## Part A — the momentum book's per-year table (IS-only) and which years are negative

iter-006 (the +0.28 book), per calendar year, vol-targeted net (monthly-Sharpe / total return %):

| year | Sharpe | ret% | | year | Sharpe | ret% |
|---|---|---|---|---|---|---|
| 2010 | **−0.32** | **−6.2** | | 2018 | +0.42 | +3.9 |
| 2011 | +0.94 | +10.9 | | 2019 | **−0.71** | **−9.6** |
| 2012 | +0.57 | +9.1 | | 2020 | +0.30 | +2.7 |
| 2013 | **−1.28** | **−15.6** | | 2021 | +1.76 | +39.7 |
| 2014 | +0.89 | +16.9 | | 2022 | +0.40 | +1.5 |
| 2015 | +1.34 | +15.6 | | 2023 | **−0.09** | **−2.3** |
| 2016 | **−0.56** | **−5.8** | | 2024 | +0.09 | +0.5 |
| 2017 | **−0.45** | **−9.1** | | 2025 (partial) | +2.23 | +2.6 |

**NEGATIVE years (6 of 16): 2010, 2013, 2016, 2017, 2019, 2023.** Diagnosing them, they are **two different failure modes**, not one:
- **Momentum-CRASH / sharp-cross-sectional-reversal years — 2016, 2023** (and 2010 partially): the losers snap back hard (Feb-2016 reversal + the Nov-2016 post-election value rotation; the 2023 narrow mega-cap-AI melt-up that punished the sector-relative shorts). These are the classic Daniel-Moskowitz momentum crashes.
- **LOW-DISPERSION melt-up years — 2013, 2017, 2019**: a low-vol, low-cross-sectional-dispersion grind-up (S&P +30% in 2013 with historically low dispersion) where a *market-neutral* cross-sectional book has almost nothing to grab and bleeds cost/noise.

This distinction is the crux of the whole task: **a value-shaped diversifier can fix the crash years; NOTHING cross-sectional-market-neutral reliably fixes the low-dispersion years** (in a low-dispersion year every cross-sectional factor earns ≈0 simultaneously — see Part D, 2013 was negative for MOM, BAB, IVOL *and* STR at once).

---

## Part B — research summary (multi-factor market-neutral construction), cited

- **Combining low-correlated factors raises Sharpe AND smooths years.** Value and momentum are **negatively correlated (≈ −0.2)**; AQR's canonical result is that an equal-weight value+momentum combo delivers a Sharpe ~**1.23** vs either alone, precisely because each factor's bad years differ ([AQR, "Value and Momentum Everywhere" / *Understanding Factor Investing*](https://funds.aqr.com/Insights/Strategies/Understanding-Factor-Investing)). A 4-factor set (value, momentum, quality, low-vol) has **average pairwise correlation ≈ 0.08**, cutting portfolio vol ~60% vs the market and roughly doubling Sharpe ([AQR multi-factor](https://funds.aqr.com/Insights/Strategies/Multi-Factor); [Alpha Architect, multi-factor long-short across regimes](https://alphaarchitect.com/multi-factor-long-short-portfolios/)).
- **The factor zoo that actually diversifies momentum:** VALUE, QUALITY/profitability (Asness-Frazzini-Pedersen QMJ), LOW-VOL/BAB, size, investment (the Fama-French 5-factor spine + momentum). **BAB** (Frazzini-Pedersen): long leveraged low-beta / short high-beta, rescaled to β=1 each side, US Sharpe **~0.75** 1926-2009 (>momentum) — but it relies on a **broad-market low-beta tail** and a leverage model ([Frazzini-Pedersen 2014](https://pages.stern.nyu.edu/~lpederse/papers/BettingAgainstBeta.pdf)).
- **Short-term (1-month) reversal is a price-only, PIT-trivial momentum diversifier:** negatively correlated with momentum, far less crash-prone, and **more powerful in industry-relative form** ([Da-Liu-Schaumburg, "Industry classification, industry momentum and short-term reversal"](https://www.sciencedirect.com/science/article/abs/pii/S1544612322001490); [NY Fed, "Decomposing Short-Term Return Reversal"](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr513.pdf)).
- **Realistic Sharpe of a well-built market-neutral book:** a single factor ≈ 0.3-0.75; a **well-diversified multi-factor market-neutral book ≈ 0.8-1.3** gross of heavy costs, on a **broad universe** (hundreds-to-thousands of names with real value/beta/size dispersion). The Sharpe comes as much from **breadth × low factor correlation** (Grinold-Kahn: IR = IC×√breadth) as from any single signal.

---

## Part C — DATA-feasibility verdict (the crux — honest)

**Price/volume-only orthogonal factors on OUR universe: mostly DEAD (see Part D).** BAB and low-idio-vol are **signal-negative gross of cost** here (BAB gross −0.67, IVOL gross −0.68) — this is NOT a cost artifact. The reason is the **universe**: our 69 Binance stock-perps are **mega-cap growth**, 57% Tech+Semi, with **no genuine low-beta tail** (beta p10 ≈ 0.53, median ≈ 0.96, p90 ≈ 1.51). The low-vol/BAB premium lives in the broad market's defensive/junk spread, which we structurally do not have. Short-term reversal is **cost-killed** (1-week reversal is gross-positive +0.15 but net −1.02; 1-month is signal-weak). The **one** price-only orthogonal, positive-EV sleeve that survives is **long-term (3y-1y) reversal — a De Bondt-Thaler VALUE PROXY** (net +0.21, gross +0.26, corr to momentum +0.01).

**Fundamentals for value/quality:**
- `yfinance` gives only a handful of recent quarters + a **current** snapshot. Using today's fundamentals for 2010-2020 history is **LOOK-AHEAD — forbidden.** Not usable for PIT value/quality.
- **SEC EDGAR XBRL `companyfacts` API** is the free, PIT-clean path: every 10-K/10-Q fact for 10,000+ CIKs, **no key, no rate limit, back to ~2009 (XBRL mandate)**, timestamped by **filing date** (the correct PIT availability date) ([SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)). The catch: raw XBRL is a **"minefield — thousands of overlapping concept names, dimensional facts, fiscal-calendar drift"** ([StockFit XBRL-to-JSON](https://developer.stockfit.io/blog/xbrl-to-json-backtesting)). A usable value/quality sleeve needs: CIK↔ticker map, concept normalization (a curated tag whitelist per metric — `Assets`, `StockholdersEquity`, `NetIncomeLoss`, `Revenues`, `LiabilitiesAndStockholdersEquity`…), fiscal-period dedup, and **lag each fact to its filing date + a safety buffer** (~2-3 engineer-days for ~69 CIKs to a leak-safe quarterly panel).

**Honest verdict — can we hit ≥0.50 AND positive-every-year with free data?**
- **Price-only, current 69-name universe: NO.** Best achievable ≈ **+0.33 with 11/16 positive years** (Part D). The two remaining negatives (2013, 2017, 2019 low-dispersion) are **structural**: a market-neutral cross-sectional book cannot manufacture return in a low-dispersion melt-up. **16/16 positive years is likely unattainable for a purely market-neutral book on this universe** — even world-class multi-factor books have down years.
- **With a SEC-EDGAR value+quality build: MAYBE on the Sharpe, still doubtful on 16/16.** Value/quality are the correct crash-year diversifiers and are PIT-feasible free — but on a **mega-cap-growth** universe fundamental value dispersion is compressed (all expensive names), so the price-proxy (LT-reversal) may already capture most of the *available* value premium here; the marginal lift from true fundamentals is real but uncertain. Quality adds a defensive sleeve but also does not earn in low-dispersion years.
- **The genuinely different lever is UNIVERSE BREADTH.** The literature's ~1.0 Sharpe market-neutral books run on **hundreds-to-thousands** of names with real dispersion. Our 69 concentrated growth names cap breadth and kill BAB/low-vol/size. A broad-universe expansion (free daily data exists) is a bigger, higher-payoff data program than EDGAR.

---

## Part D — prototype results (`iter_011_probe.py`, IS-only, leak self-check PASS)

**Standalone price-only sleeves** (same band + 15% vol-target + 6bps cost; net IS Sharpe):

| sleeve | net | gross | corr→MOM | regimes (bull/bear/chop) | verdict |
|---|---|---|---|---|---|
| MOM (iter-006) | +0.28 | — | +1.00 | +0.30/−0.24/+0.51 | the base |
| STR1 1-mo reversal | −0.75 | −0.27 | −0.09 | −0.98/+0.17/−0.01 | dead (signal-weak; momentum-persistent universe) |
| STR1W 1-wk reversal | −1.02 | +0.15 | −0.14 | −1.23/−0.40/−0.35 | **cost-killed** (gross+, net−) |
| BAB low-beta | −0.69 | −0.67 | +0.02 | −0.89/**+1.49**/−0.79 | dead gross (no low-beta tail) |
| IVOL low idio-vol | −0.72 | −0.68 | +0.11 | −0.90/+0.23/−0.31 | dead gross |
| **LTR 3y-1y (value proxy)** | **+0.21** | **+0.26** | **+0.01** | **+0.13/+0.71/+0.24** | **the one survivor — orthogonal, +EV, all-regime +** |

Naively stacking MOM with the negative-EV sleeves is catastrophic (MOM+STR1+BAB+IVOL → **−0.77**, 2/16 years) — no weighting scheme rescues negative-EV sleeves.

**The recommended build — MOM + w·LTR** (equal-weight signal blend → one band → one vol-target; weight basin):

| w | net | +yrs | worst yr | maxDD |
|---|---|---|---|---|
| 0.3 | +0.34 | 11/16 | 2019 −0.91 | −40% |
| **0.5 (pre-reg)** | **+0.33** | **11/16** | 2017 −1.11 | −49% |
| 0.7 | +0.33 | 10/16 | 2017 −1.48 | −54% |
| 1.0 | +0.30 | 10/16 | 2017 −1.78 | −60% |

Broad basin (0.3-0.7 all ≈ +0.33) → not a knife-edge. **Per-year effect of MOM+0.5·LTR on the 6 bad years:** 2013 −1.28→**+0.46 FIXED**, 2016 −0.56→**+1.02 FIXED**, 2023 −0.09→**+0.37 FIXED**; 2017 −0.45→−1.11 *worse*, 2019 −0.71→−0.96 *worse*, 2010 unchanged (LTR 3y warm-up, no breadth pre-2013). **corr(MOM,LTR) = +0.01 full IS / −0.12 in the bad years** — genuine diversification. Cost: maxDD −29%→−49% (LTR is more drawdown-prone) and a few good years trimmed (2018, 2020, 2025). **Result: net +0.28→+0.33, positive years 10/16→11/16 — a real but partial win. Target NOT reached.**

---

## Recommended iter-011 (precise spec) + roadmap

**iter-011 = add the LONG-TERM-REVERSAL (value-proxy) sleeve to the momentum book.** This is the one genuine, PIT-trivial, orthogonal price-only diversifier, and it does exactly what multi-factor theory predicts — it earns in the momentum-crash years.

Spec (leak-safe, same machinery, no new data):
```
rvol      = close.pct_change().rolling(63).std()
ltr_raw   = gross_norm( sector_neutralize( -(close.shift(252)/close.shift(756) - 1)/rvol, SECTOR_MAP ) )
mom_raw   = gross_norm( iter006.crash_braked_raw(pn) )          # UNCHANGED base
raw       = (mom_raw + 0.5 * ltr_raw) / 1.5                     # w = 0.5 pre-registered (basin 0.3-0.7)
net, w    = iter003.banded_net(raw, ret_fwd, delta=0.005)       # band + vol-target UNCHANGED
```
Identities to pre-register: `w=0` reproduces iter-006 bit-for-bit; the LTR `skip=252` guarantees no overlap with the 12-1m momentum long leg. Warm-up ~3yr → 2010-2012 fall back toward pure momentum (leak-safe, honest).

**Roadmap to the target (in expected-payoff order):**
1. **iter-011 (this):** LTR value-proxy sleeve → +0.33, 11/16. Ship the real diversification win; be honest it is not the target.
2. **iter-012 — UNIVERSE BREADTH (highest payoff):** expand to a broad free-daily-data universe (Russell-1000-scale) to resurrect BAB/low-vol/size and multiply breadth. This is what separates our +0.33 from the literature's ~1.0. Bigger data program; free data exists.
3. **iter-013 — SEC-EDGAR PIT value+quality:** `companyfacts` ingestion (filing-date-lagged), book-to-market + QMJ-style profitability/leverage sleeves. The textbook crash-year diversifiers; ~2-3 eng-days for the ingestion.
4. Only after 2-3: revisit factor-timing / risk-parity weighting across the enlarged sleeve set.

## Pre-registered criteria + failure mode
- **Promote iter-011 → new base iff:** net > +0.28 (beat the momentum base) AND positive-years ≥ 10/16 (no worse than base) AND the 3 momentum-crash years (2013/2016/2023) flip positive AND corr(MOM,LTR) ≤ +0.2 (genuine diversification) AND leak self-check PASS. *(Predicted: net +0.33, 11/16, all three flip, corr +0.01 — expected PASS.)*
- **Raised-bar target (net ≥ 0.50 AND 16/16):** **NOT expected at iter-011** — pre-registered as a multi-iteration goal requiring the universe-breadth + fundamentals build (steps 2-3). Do not tune LTR's weight/window to chase 16/16 — that is overfitting to the revealed bad years; the basin sweep is the anti-overfit guard.
- **Failure mode (abandon LTR):** if MOM+LTR does NOT flip 2013/2016/2023 positive, or net ≤ +0.28, or corr > +0.2, LTR is not the diversifier the theory promises on this universe → drop it and jump straight to the universe-breadth program (step 2).
